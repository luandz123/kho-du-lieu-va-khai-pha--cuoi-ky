# Gói DW G2 — P1 / contract v2

**Cập nhật công bố:** điều phối chấp nhận6D cục bộ và giao PR ETL/G2; kết quả Git/commit code/PR được ghi sau xác minh tại [hồ sơ công bố](g2_publication.md). Chưa merge hoặc xác nhận P2 kiểm nhận. Manifest vẫn ghi run2 và version bundle thực chạy, không gán commit mới cho các run lịch sử.

## Phạm vi và trạng thái

Đây là gói metadata/hướng dẫn để review 6D và chuẩn bị G2. **Chưa có xác nhận P2 kiểm nhận G2**, chưa push/PR trong lượt này. Kết quả thực chạy, hai run cùng phiên bản, adapter và rollback được tổng hợp tại [bàn giao 6D](s06d_handoff.md) và [summary](../../results/warehouse/s06d_summary.json). Không suy việc bốn view đọc được thành đã tích hợp BI/OLAP/dashboard hoặc quyền đọc của máy P2.

Database dự án là **movielens_btl**, PostgreSQL 17.11 đã xác minh ở các mốc trước. Dùng schema/DDL S04 đã triển khai S05, không bootstrap hoặc đổi mô hình ở 6D. [DDL và bốn view](../../database/schema.sql), [ERD](../../database/erd.md), [từ điển](../../database/data_dictionary.md), [mapping](../../database/source_to_target.md), [contract v2](../shared/data_contract.md).

## Thành phần bàn giao

- [dw_manifest.json](../../results/warehouse/dw_manifest.json): contract_version, run_id, bốn canonical hash/count, tổng điểm/phân bố sao, min/max UTC, source hash, ETL version/code bundle và trạng thái model. Đây là manifest sau COMMIT gần nhất, không thay việc kiểm DW hiện tại.
- [etl/run_etl.py](../../etl/run_etl.py): full refresh chung một connection và transaction; [checker](../../tests/warehouse/check_warehouse.py) chỉ đọc tích hợp, không dựa vào run6C/surrogate cũ.
- Report hai run và fixture trong results/warehouse, index tại summary6D; hồ sơ S06 và hướng dẫn này. Report lịch sử nguyên vẹn, manifest gần nhất được thay tên nguyên tử sau commit.
- CSV đối chiếu chỉ nằm **cục bộ ngoài Git** ở `data/processed/p1_g2_<adapter_run_id>/`, đường dẫn cụ thể trong report adapter. Không đưa CSV/dump hoặc lịch sử user lên Git. P2 không cần chép toàn bộ raw/docs của máy P1.

## Tái tạo và hậu kiểm trên máy P1

PowerShell tại checkout P1, dùng môi trường đã thiết lập và nguồn tải độc lập đã khớp source_manifest:

```powershell
.\.venv\Scripts\Activate.ps1
python -X utf8 -m etl.run_etl refresh --env-file .env
python -X utf8 tests/warehouse/check_warehouse.py --env-file .env
```

Lệnh refresh có quyền ghi trong **đúng database dự án** theo lệnh giao6D: kiểm host/config/marker/catalog/nguồn trước ghi; advisory lock (20261027,1); vô hiệu hóa registry, **một TRUNCATE tường minh 11 bảng RESTART IDENTITY**, giữ metadata registry; nạp staging→dimension→bridge→fact rồi đối soát trước COMMIT cùng connection. Không CASCADE/DROP hoặc ghi bảng ngoài danh sách. BI có thể phải chờ khóa trong cửa sổ refresh. Không chạy nối tiếp CLI S05/6A/6B/6C để thay full refresh.

Sau refresh, mọi registry inactive/invalid và hai bảng kết quả cụm rỗng. Không dùng model cũ cho BI, kể cả khi nguồn/hash không đổi; gói G3 cần được kiểm/nạp riêng khi được giao. Surrogate có thể thay đổi: hợp đồng tương đương dựa trên ID nguồn/nội dung/hash, không dựa identity hoặc fingerprint vật lý cũ.

Checker tích hợp mở transaction READ ONLY / REPEATABLE READ, so nguồn/staging/DW, khóa, UTC, bốn hash và trạng thái sau refresh. Nó áp dụng trước khi nạp G3; khi được giao tích hợp model phải bổ sung kiểm model phù hợp, không tự bỏ guard. Không chạy lại các checker tiểu bước cũ đòi DW/fact/bridge rỗng.

## Quy tắc dữ liệu

| View | Cột theo đúng thứ tự |
|---|---|
| dw.v_ml_users | user_id, gender, age_group, occupation |
| dw.v_ml_movies | movie_id, title, release_year |
| dw.v_ml_movie_genres | movie_id, genre_name |
| dw.v_ml_ratings | user_id, movie_id, rating, timestamp, rated_at |

ID là ID MovieLens gốc; surrogate chỉ trong DW. Title giữ nguyên, năm không khớp regex cuối là NULL; CSV NULL rỗng, integer không `.0`. Timestamp là giây Unix, rated_at là chuỗi UTC-Z cùng thời điểm. Ratings không nối genre; một đánh giá nguồn một dòng, không phải lượt xem.

Serializer đã review của P2 giữ UTF-8 không BOM, LF, comma, header và CSV quote chuẩn. Caller sort users(user_id), movies(movie_id), movie_genres(movie_id,genre_name), ratings(user_id,movie_id,timestamp,rating). Hash trên byte CSV chuẩn, không trên file JSON hoặc chuỗi datetime phụ thuộc máy.

## Cách P2 nhận và kiểm G2

Sau khi điều phối giao công bố PR G2 và PR được merge, P2 bảo toàn checkout riêng rồi nhận đúng commit qua quy trình GitHub nhóm. Kiểm contract_version=2 và commit/code bundle/source/canonical hash của manifest cùng report; tải GroupLens độc lập nếu chưa có nguồn đúng hash, không chép toàn bộ thư mục máy P1.

Đối chiếu trực tiếp bốn view qua adapter `mining.data_io.load_dw_data(connection_or_engine=conn)` hiện có; không đổi ID hoặc nối genre vào ratings. Connection do người vận hành cấu hình cục bộ, không gửi mật khẩu/URI trong chat hoặc Git. Có thể dùng các biến `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` ở máy P2; **PGDATABASE phải là movielens_btl**, không dùng mặc định movielens_dw trong adapter khi không truyền connection. `PGHOST` phải là host PostgreSQL thực sự được nhóm cho phép; localhost trên máy P2 là máy P2, không phải máy Windows P1.

P1 đã được giao kiểm adapter trên PostgreSQL thật tại máy P1; kết quả cụ thể trong report adapter, không thay xác nhận của P2. **Session READ ONLY khác tài khoản chỉ có quyền đọc**. Lượt này không tạo role, cấp quyền, mở firewall hoặc public server. Quyền tài khoản đang dùng và khả năng P2 kết nối từ xa được báo riêng; nếu chưa có tài khoản/đường kết nối dành cho P2, đó là đầu vào còn thiếu cho bàn giao truy cập. Không yêu cầu người dùng gửi credential vào chat. CSV cục bộ tùy chọn dùng trao đổi riêng theo quy trình nhóm, không thay nghiệm thu cuối trên DW.

Kết quả cục bộ hiện tại: adapter run **c75f9cb0ceb04d74bfa36e140d812754 PASS**, mọi cell/schema/count/hash raw/CSV/DW khớp bốn bảng. Session readonly=on; account hiện tại có superuser và quyền ghi, **không phải tài khoản chỉ đọc chuyên dụng đã được xác minh**. P2 remote và lời xác nhận kiểm nhận vẫn chưa có. Xem [report adapter](../../results/warehouse/s06d_adapter_c75f9cb0ceb04d74bfa36e140d812754.json).

P2 kiểm schema/order, row_count, bốn canonical hash và tương đương raw/CSV/DW; sau đó gửi xác nhận gắn run_id/commit thật để điều phối ghi nhận. Trạng thái `p2_intake_status=NOT_CONFIRMED` không được tự đổi vì P1 đã chạy adapter thành công.

### Đầu vào truy cập còn thiếu và phương án DW cục bộ

Để đọc DW trên máy P1, nhóm cần chuẩn bị tài khoản chuyên dụng có SELECT bốn view/USAGE schema phù hợp và phương thức kết nối riêng được chốt (host, port, mạng riêng hoặc kênh truy cập được phép). Chưa tạo/cấp quyền, mở port công khai hay thay firewall trong lượt công bố; không chia sẻ credential quản trị đang dùng cho P2.

Phương án độc lập: P2 nhận đúng commit code sau PR được chốt, tải GroupLens độc lập và đối chiếu bốn SHA nguồn, tạo môi trường riêng từ requirements P1 và database dự án cục bộ theo hướng dẫnS05, áp dụng DDL đã duyệt lần đầu với guard đúng DB, rồi chạy fullrefresh/hậu kiểm. `.env` và credential do P2 nhập cục bộ; không chép venv hoặc dữ liệu từ máy P1. P1 chưa thực thi/chứng minh setup Linux trên máy P2. Mọi xác nhận phải ghi run_id/commit/hash thực từ máy đó. Hai phương án không chặn công bố code/metadata, nhưng chưa được coi là quyền truy cập hoặc G2 đã nhận.

## Transaction và công bố file

Mọi lỗi parse/mapping/FK/miền/trùng/checksum trước commit phải rollback cả dữ liệu cũ lẫn model flags. Fixture thử dùng dữ liệu/model tự tạo trong schema riêng, không sửa nguồn thật. Mất kết nối đúng lúc COMMIT được ghi chưa xác định, reconnect kiểm snapshot/model; nếu snapshot giống cũ/mới không phân biệt được thì vẫn không gán commit thành công. Ca mất kết nối được kiểm bằng unit mô phỏng, không cắt mạng thật.

SQL transaction không bao gồm filesystem. Sau COMMIT, report/manifest ghi file tạm rồi `os.replace`; nếu ghi thất bại, log DB đã commit nhưng G2 chưa bàn giao. Không báo DB đã rollback vì lỗi ghi file. Manifest cũ phải được kiểm run_id/report và DW hiện tại; không tự coi file trên đĩa là snapshot còn hợp lệ. Không tự chạy refresh lại để chữa lỗi xuất metadata khi chưa kiểm trạng thái.
