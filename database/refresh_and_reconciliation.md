# Full refresh, index và kế hoạch đối soát — S04 nháp v2

Kế thừa quy trình v1; không có lệnh nào trong tài liệu này được chạy. Cập nhật căn cứ PR #5 merge `a8d2615`, bốn canonical hash không đổi; metadata SHA còn P2 sửa không chặn thiết kế. Chưa có phép kiểm PostgreSQL DW thật.

Ngày 16/10/2026, **chỉ thiết kế, chưa kết nối PostgreSQL hoặc chạy SQL**. Chưa viết chương trình ETL. Ràng buộc và bảng dự kiến nằm tại [schema.sql](schema.sql).

## Index và mục đích

| Index/ràng buộc tạo index | Tác dụng dự kiến | Giới hạn |
|---|---|---|
| PK các dimension; UQ user_id/movie_id/full_date/genre_name | Tra lookup ID nguồn, chống trùng, hỗ trợ FK | Không cần index trùng cùng tiền tố |
| UQ dim_date(date_key,full_date) | Đích FK ghép chứng minh đúng ngày UTC | Dư thừa về duy nhất so với PK nhưng cần cho FK ghép |
| PK fact_rating(rating_key) | Định danh dòng DW | Không thay khóa nghiệp vụ |
| UQ fact(user_key,movie_key) | Chống trùng theo EDA, lọc lịch sử user | Tiền tố user đã có index; không thêm riêng user_key |
| ix_fact_rating_movie(movie_key) | Lọc/tổng hợp và kiểm FK theo phim | Hiệu quả thực cần EXPLAIN sau nạp |
| ix_fact_rating_date_movie(date_key,movie_key) | Roll-up ngày/quý và phim | Chưa là bằng chứng tối ưu hiệu năng |
| ix_fact_rating_rated_at(rated_at) | Lọc khoảng UTC | Có thể cân nhắc bỏ nếu workload không dùng, sau đo thực |
| PK bridge(movie_key,genre_key) | Chống lặp liên kết, tra thể loại của phim | Không ngăn nhiều genre cho cùng phim |
| ix_bridge_genre_movie(genre_key,movie_key) | Lọc từ genre đến phim/fact | Không dùng kết quả join này làm tổng rating toàn hệ thống |
| PK registry(model_version); uq_model_registry_one_active | Phiên bản duy nhất, tối đa một active | Có thể không có active; index không chứng minh gói đúng |
| PK user_cluster(model_version,user_id) | Một user mỗi phiên bản | Cần kiểm đủ cohort |
| ix_user_cluster_version_cluster(model_version,cluster_id) | Tổng hợp cụm theo phiên bản | Khi join profile phải dùng cả model_version |
| ix_user_cluster_source_user(user_id) | FK/lookup user qua các phiên bản | Không xuất danh sách cá nhân lên Git |
| PK profile(model_version,cluster_id,genre_name) | Chống trùng profile | K×genre và tổng mean cần kiểm riêng |
| ix_cluster_profile_genre(genre_name) | FK/tra cứu profile theo genre | Chưa đo chi phí/hiệu quả thực |

Staging chỉ có PK source_line, chưa thêm index trường raw text. Chưa đề xuất partition, materialized view hoặc index trên mọi cột. Đánh giá lại bằng kế hoạch truy vấn và số đo sau khi có dữ liệu; không hứa máy đủ mạnh/nhanh từ số lượng index.

## Tạo schema lần đầu, khác với refresh

SQL nháp có BEGIN/COMMIT, timezone UTC và guard đòi session `btl.target_database` khớp database dự án riêng đã được chốt, từ chối postgres/template0/template1. Không CREATE DATABASE/ROLE, không IF NOT EXISTS để che schema lệch, không DROP. Nếu schema đã tồn tại phải kiểm hiện trạng/migration riêng ở bước được giao; không chạy lại file như cơ chế refresh. Guard không thay quyền tối thiểu hoặc kiểm tra database thực tế.

## Full refresh dự kiến trong một transaction

1. Trước mở transaction: tải độc lập GroupLens vào thư mục cục bộ mới, đối chiếu bốn SHA-256 và số dòng nguồn với manifest G1 đã kiểm nhận; kiểm provenance và serializer. Không ghi manifest P2, không ghi đè raw có sẵn. Chưa nhận toàn bộ G1 thì chưa mở bước thực thi.
2. Kết nối đúng database dự án, đặt UTC; lấy khóa giao dịch chung cho refresh và nhận G3 (đề xuất advisory_xact_lock với cặp số cố định 20261027,1). Đặt lock_timeout/statement_timeout phù hợp khi thực thi; nếu không lấy được khóa thì dừng sạch. Không cho hai tác vụ refresh/activate cùng chạy.
3. Trong transaction, đặt mọi registry is_active=false/is_valid_for_dw=false. Dọn **danh sách tường minh**: analytics.user_cluster, analytics.cluster_genre_profile, dw.fact_rating, dw.bridge_movie_genre, dw.dim_user, dw.dim_movie, dw.dim_date, dw.dim_genre, staging.users_raw, staging.movies_raw, staging.ratings_raw; reset identity cho những bảng có identity. PostgreSQL TRUNCATE phải gồm cả bảng tham chiếu ngay cả khi rỗng. Không CASCADE, không tác động database/schema khác. Giữ model_registry làm metadata kiểm toán nhưng kết quả cũ bị xóa trong refresh toàn phần này.
4. Nạp ba staging từ ba tệp nguồn, bỏ ZIP ngay khi đọc; kiểm số trường, source_line, count, ép kiểu/miền/NULL và khóa trước chuyển DW. Tệp README chỉ kiểm nguồn/miền mã, không nạp thành bảng nghiệp vụ. Nếu lỗi, không tự deduplicate, đổi nhãn, bỏ dòng hoặc sửa nguồn.
5. Nạp dim_user, dim_movie, dim_genre; sinh dim_date **liên tục** từ ngày UTC nhỏ nhất đến lớn nhất ratings. Tra surrogate bằng ID/tên duy nhất, nạp bridge rồi fact. Có thể quy định sort ID nguồn để tái lập thứ tự nạp; không hứa surrogate bền qua refresh. Dữ liệu giao tiếp luôn dùng ID nguồn.
6. Trước COMMIT, đối soát bốn view trong cùng transaction: schema/thứ tự cột, row_count, tập khóa, FK, miền, timestamp↔UTC, năm/genre/tuổi, và SHA-256 byte CSV chuẩn. Bất kỳ sai khác nào ⇒ ROLLBACK toàn bộ, khôi phục cả DW và trạng thái model cũ. Chỉ count/tổng điểm bằng nhau chưa đủ.
7. COMMIT khi tất cả điều kiện đạt. Việc refresh thành công để analytics không active; muốn dùng lại gói G3 phải nạp/kiểm lại cùng canonical DW, dù nguồn không đổi. Không giữ một cờ active trỏ kết quả đã bị dọn.
8. Sau commit, tạo báo cáo G2 và manifest bốn view bằng ghi tệp tạm rồi thay tên trong thư mục đầu ra P1; CSV tùy chọn lưu ngoài Git. File và SQL không có transaction chung: nếu ghi báo cáo thất bại, ghi G2 chưa bàn giao, tạo lại từ DW, không tuyên bố đã rollback DB đã commit. Lưu dấu mốc và hash, không dữ liệu theo user hoặc credential.

### Làm rõ v2: connection, nạp lại và lỗi

Tại bước 3, danh sách dọn là **một thao tác TRUNCATE chung** cho toàn bộ bảng được liệt kê, không phát các TRUNCATE cha/con riêng để thử vượt FK. Registry không tham chiếu DW và không bị truncate. Khóa chung phải được mọi luồng ghi tuân thủ; advisory lock không tự ngăn tác vụ tùy ý ngoài quy trình.

Kiểm trước COMMIT phải dùng **cùng connection và transaction đang nạp** để đọc chính dữ liệu chưa commit qua bốn view. Không gọi adapter P2 bằng một connection mới ở thời điểm này: connection khác không chứng minh được dữ liệu đang nạp. P1 dùng cùng quy tắc canonical đã chốt để đối soát trong transaction; adapter P2 trên DW đã commit là kiểm G2 riêng. Không dùng tệp manifest cũ trên đĩa để bỏ qua kiểm snapshot hiện tại.

Nạp lại full refresh không nối tiếp bản cũ: dọn đúng phạm vi rồi nạp đủ snapshot. PK/UNIQUE chặn trùng ngay cả khi ETL có lỗi; không ON CONFLICT DO NOTHING, không bỏ dòng để làm count khớp. Hai lần nạp thành công phải có cùng bốn canonical hash/count; identity nội bộ không phải bằng chứng tương đương. Gây lỗi parse, trùng user–movie, FK, rating ngoài miền hoặc checksum sai phải trả lỗi và ROLLBACK cả staging/DW/cờ model trong transaction. Không commit theo chunk; COPY/batch có thể chia lô nhưng vẫn dùng cùng transaction. Ca kiểm rollback và chạy hai lần chỉ là kế hoạch, chưa thực thi.

Nếu mất kết nối đúng lúc COMMIT, kết quả có thể chưa xác định: không tự báo đã rollback hoặc nạp tiếp. Khi được giao thực thi, kiểm lại snapshot DW và trạng thái model bằng connection mới trước quyết định chạy lại; ghi lỗi đã lọc, không exception/URI thô. Kết quả kiểm trước commit, manifest và báo cáo sau commit phải ghi commit code/config/hash để truy vết, không giả định SQL và filesystem cùng giao dịch.

TRUNCATE lấy khóa mạnh; chỉ thực thi trong cửa sổ bảo trì của dự án, chấp nhận BI có thể chờ hoặc lỗi tùy isolation. Không hứa không gián đoạn. Transaction rollback bảo vệ lỗi nạp; SQL/schema/index thật, quyền, dung lượng và thời gian khóa chưa được kiểm chứng trong S04.

## Ma trận đối soát trước commit/G2

| Điều kiện | Giá trị tham chiếu đã kiểm nhận | Kiểm ở ETL/G2 và bằng chứng phải lưu |
|---|---|---|
| Ba nguồn và README | Bốn hash tại source_manifest | So byte nguồn độc lập; log tên tệp/hash/count/UTC và commit tham chiếu |
| Bốn bảng/view | users=6040, movies=3883, movie_genres=6408, ratings=1000209 | COUNT sau nạp và so schema/cột/thứ tự; manifest bốn bảng |
| Khóa | duplicate_pairs=0; ID user/movie, cặp movie–genre duy nhất | Kiểm trước nạp và UNIQUE/PK; lỗi trả mã khác 0 |
| FK và miền | orphan=0; rating ngoài 1..5=0 | Anti-join/NULL/domain checks + ràng buộc DB; không dùng inner join để âm thầm bỏ orphan |
| Năm/chuỗi | release_year khớp regex cuối title; contract cho NULL | Title nguyên vẹn, Latin-1→Unicode không mất ký tự; NULL biểu diễn ô rỗng |
| Ngày/UTC | 1000209 rated_at khớp epoch | Kiểm biên ngày/quý UTC; FK ghép, CHECK epoch; ISO Z đúng từng dòng |
| Genre | 18 genre; bridge 6408 dòng | Tập tên đúng nguồn, không lặp cặp; phim nhiều genre không tăng view ratings |
| Chuẩn hóa/hash | Bốn SHA-256 chuẩn trong README thiết kế | Serialize UTF-8 không BOM, LF, comma, CSV quote chuẩn, header đúng; int không .0; NULL rỗng; sort đúng contract; đối chiếu từng hash |
| Raw/csv/DW | Raw/csv đã kiểm; DW chưa có | Adapter sửa R1/R5/R6; kiểm trên PostgreSQL thật, không lấy fixture TEXT thay bằng chứng timestamptz |
| Refresh/rollback | Chưa kiểm thực thi | Chạy lại không tăng dòng; gây lỗi fixture có kiểm soát và chứng minh DB/model cũ nguyên vẹn trong môi trường thử được giao |

Số genre và count là snapshot đã đối soát, không tự sửa manifest kỳ vọng nếu nguồn mới khác. FK user/movie và unique rating đã đạt trong bằng chứng G1; tập mã/provenance R4 vẫn chờ sửa hồ sơ. Không đưa ID/lịch sử từng user vào báo cáo Git. Báo cáo S04 chỉ xác nhận thiết kế tĩnh; không ghi những phép kiểm tương lai là đã chạy.

## Nhận G3 và tránh trộn phiên bản

- Nhận **cả hai CSV và manifest cùng gói**. Kiểm header/order theo contract; hash byte CSV, row_count, contract=2, model_version cố định, source_hashes/canonical_hashes, seed, K, preprocessing, genre_order, libraries, training_config_hash và thời điểm UTC. Không nhận một CSV mới ghép một CSV cũ. Profile nhận model_version từ manifest đã kiểm, không suy từ tên thư mục.
- Khóa cùng giao dịch với refresh. Đối soát canonical bằng bốn view DW hiện tại trong snapshot được bảo vệ; manifest G2 trên đĩa đơn lẻ không đủ nếu DW đã đổi. Chưa khớp thì không nạp/activate. Không cập nhật model_version đã tồn tại bằng nội dung khác; gói trùng hoàn toàn có thể xác nhận idempotent sau đối chiếu metadata/hash, gói khác cần phiên bản mới từ P2.
- Mỗi user DW đúng một dòng; assigned có cluster_id nguyên 0..K-1, insufficient_evidence có NULL. Số user thiếu bằng chứng phải đúng quy tắc dữ liệu của model; con số 2 trong G1 chỉ là quan sát nguồn, không cố định cho mọi mô hình/phiên bản tương lai.
- Profile đúng K×18 dòng cho snapshot này, genre_order không lặp và bằng tập genre DW; có cả mean=0. n_users nhất quán mọi genre và bằng số assigned trong cụm, tổng n_users qua **mỗi cụm một lần** bằng tổng assigned. Không cộng n_users qua mọi dòng genre.
- Kiểm mean hữu hạn trong [0,1], tổng mỗi cụm lệch 1 tối đa 1e-8. Mean phải là trung bình tỷ lệ genre gốc của user assigned, không phải tâm sau scaling/normalization khác. Đối soát với bằng chứng/tỷ lệ gốc theo preprocessing do P2 bàn giao; thiếu đặc tả hoặc không tái lập được thì gói chờ, không activate. Cụm rỗng trả lại để chốt chính sách, không bịa mean.
- Nạp registry inactive/invalid và hai bảng cùng transaction. Sau khi kiểm toàn gói đạt, chuyển model cũ inactive, model mới valid+active, COMMIT. Bất cứ lỗi nào ROLLBACK cả gói, không thay active cũ. Index chặn hơn một active, CHECK chặn active chưa valid; kiểm liên bảng vẫn bắt buộc.
- BI chỉ dùng hai view active, nối cả model_version và cluster_id. Nếu không có active sau refresh, hiển thị chưa có kết quả hợp lệ; không lấy MAX(model_version) hoặc trộn dòng. Registry phục vụ kiểm toán; không coi tồn tại dòng là model đã được người dùng duyệt.

## Tổng hợp OLAP và ý nghĩa chỉ số

Điểm trung bình chung là SUM(rating)/COUNT(rating). Khi triển khai PostgreSQL phải chia kiểu numeric, ví dụ biểu thức `SUM(rating)::numeric / NULLIF(COUNT(*), 0)`, tránh chia nguyên và chia 0. Khi roll-up nhóm dùng tổng điểm và số đánh giá, không lấy trung bình đơn giản của các trung bình nhóm có mẫu khác nhau. Rating là đánh giá; timestamp là thời điểm đánh giá.

Genre là nhiều–nhiều. Chọn định nghĩa mặc định cho BI: **tỷ trọng gán genre** = số cặp đánh giá–genre của genre / tổng số cặp đánh giá–genre trong cùng bộ lọc. Tổng tỷ trọng =100%, nhưng mẫu số lớn hơn số đánh giá nếu có phim nhiều genre. Nếu dùng độ phủ genre = số đánh giá phim có genre / tổng đánh giá, tổng tỷ lệ có thể >100%; phải ghi nhãn khác. Không phân bổ 1/số genre vào mean_preference của P2 nếu preprocessing contract không quy định như vậy. OLAP và tỷ lệ genre của vector ML là hai định nghĩa riêng phải ghi rõ công thức.

Q3 tổng hợp COUNT fact theo quý lịch UTC trong thời kỳ dữ liệu; dùng dim_date để bù quý không có rating. Tăng trưởng=(n_quý_này−n_quý_trước)/n_quý_trước; quý trước=0 hoặc chưa có ⇒ NULL/không xác định, không chia 0. Quý đầu/cuối có thể không trọn kỳ (nguồn 25/04/2000–28/02/2003 UTC); biểu đồ phải ghi chú trước so sánh. Không suy nhu cầu hiện tại hoặc doanh thu. Q1 mô tả cơ cấu lịch sử, không suy cùng người đổi sở thích theo tuổi; Q2 Top 5 theo lịch sử, chưa có thuật toán trong S04.

## Phần còn chờ và tham khảo kỹ thuật

PR #5 sửa các phát hiện R1–R6 của [kiểm nhận G1 lịch sử](../docs/P1/g1_review_2026-10-16.md) đã merge. Điều phối báo 23/23 đạt, snapshot có log tương ứng, source/canonical hash không đổi; P2 còn sửa một trường SHA metadata. Xem [cập nhật v2](../docs/P1/s04_review_v2.md), không dùng trạng thái chờ sửa v1 để chặn thiết kế. G3 chưa được kiểm nhận. Chưa chốt tên database dự án/quyền ghi và read-only DW; chưa thực thi SQL/parser PostgreSQL, adapter/view DW thật, đo index/refresh/rollback hoặc cấu hình BI.

Quy tắc CHECK/FK và TRUNCATE được đối chiếu tài liệu PostgreSQL 17: [constraints](https://www.postgresql.org/docs/17/ddl-constraints.html), [TRUNCATE](https://www.postgresql.org/docs/17/sql-truncate.html), [generated columns](https://www.postgresql.org/docs/17/ddl-generated-columns.html), [formatting](https://www.postgresql.org/docs/17/functions-formatting.html). Đây là căn cứ thiết kế, không phải kết quả chạy SQL trên máy P1.
