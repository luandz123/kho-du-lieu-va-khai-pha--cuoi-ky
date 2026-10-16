# Bàn giao S04 — thiết kế v2, điều phối chấp nhận ở mức thiết kế

Cập nhật công bố: nguồn ghi nhận **Điều phối chấp nhận S04 v2 ở mức thiết kế**, không phải lời duyệt nguyên văn của người dùng. Được commit/push/mở PR, chưa merge hoặc thực thi. Những nhãn WAITING_REVIEW/không commit ở mô tả lượt thiết kế dưới đây là lịch sử. Không thay định nghĩa DDL. 37/37 kiểm tĩnh là kết quả lượt v2, kiểm công bố và hash được ghi riêng, không tuyên bố chạy lại 37 kiểm.

Ngày 16/10/2026. Chỉ hoàn thiện thiết kế theo lệnh điều phối; chưa có schema/bảng/view nghiệp vụ được tạo bởi S04. V2 kế thừa sáu file database của v1, không khởi tạo lại hay thay bản khác. SQL chỉ cập nhật comment phiên bản/căn cứ, giữ nguyên định nghĩa DDL.

## Căn cứ và phân biệt bằng chứng

| Căn cứ | Đã xác minh ở lượt này | Giới hạn |
|---|---|---|
| PR #3 môi trường | API MERGED, merge 9846219eb0944e75e57f349e1bcfc88c7d1e8088 | Không chạy lại môi trường/SQL/Superset |
| PR #4 G1 | API MERGED, merge b71d439fa2cc3ee84c40f4a28dc6fe00c8326d42 | Đối soát nguồn độc lập trước đó thuộc bằng chứng 9299268 |
| PR #5 sửa G1 | API MERGED, head b73c8e2bc3bc98ff8576f75c02416cf2582bdc73, merge a8d2615df1e5aa522b2cceaaa073336d61013b83 | Chỉ đọc snapshot cố định, không pull vào checkout |
| Canonical/source manifest PR #5 | Bốn hash/count và hash nguồn giữ nguyên; code sets đã có; ba script hash khớp | Không tải/hash lại tệp nguồn hoặc tái tạo canonical ở lượt này |
| Test bản sửa | Đọc log P2: 23 passed in 158.31s; điều phối xác nhận kiểm độc lập 23/23 | Không gọi đây là P1 chạy test mới; DW thật chờ G2 |
| Một SHA metadata | source_code_commit khác provenance.original_commit_g1 và commit gốc thật 7a284b9f108dd64b030305cf51b8614b770a2296 | P2 đang sửa; không sửa chéo, không chặn thiết kế theo lệnh điều phối |

[Snapshot và hash các đầu vào](s04_inputs_pr5.json) giữ căn cứ tại PR #5. Không dùng source_code_commit sai để checkout code hoặc tuyên bố tái lập. Giữ nguyên báo cáo kiểm nhận cũ để truy vết R1–R6; trạng thái chờ sửa ở báo cáo cũ không thay cập nhật hiện hành này. Không tạo lời duyệt S04/G1/3B.

## File và cách xem

| File | Nội dung review |
|---|---|
| [database/README.md](../../database/README.md) | Điểm vào, căn cứ, checksum và quyết định |
| [schema.sql](../../database/schema.sql) | SQL nháp, chưa chạy: ba staging, sáu bảng DW, ba bảng analytics gồm hai kết quả + registry kỹ thuật; bốn view DW và hai view active nội bộ |
| [erd.md](../../database/erd.md) | Mermaid chỉnh sửa được, chín quan hệ FK, PK/FK và ví dụ đa genre |
| [data_dictionary.md](../../database/data_dictionary.md) | Đủ 64 cột: kiểu, null, khóa, nguồn, phép biến đổi và ý nghĩa |
| [source_to_target.md](../../database/source_to_target.md) | Mapping và kiểu/thứ tự bốn view, năm NULL, gói G3 |
| [refresh_and_reconciliation.md](../../database/refresh_and_reconciliation.md) | Index, thứ tự nạp, transaction/rollback/reload, kiểm G2/G3, công thức OLAP |
| [s04_design_checks_v2.json](s04_design_checks_v2.json) | Kiểm tĩnh mới và inventory SQL; phần chưa kiểm được liệt kê riêng |
| [S04.md](../agent/steps/P1/S04.md) | Tiền đề/lệnh/phiên bản/thay đổi/giới hạn; STATE/DECISIONS/REVIEWS/PROMPTS P1 cập nhật tương ứng |

Mở README và ERD trong trình xem Markdown; mở SQL để review văn bản. **Không chạy schema.sql ở lượt này.** Bằng chứng v1 s04_design_checks.json được giữ nguyên, không thay bằng kết quả v2.

## Quyết định chính, lý do và tác động

1. **Grain và khóa:** một dòng fact là một đánh giá nguồn; surrogate chỉ trong DW, view giữ ID MovieLens. UNIQUE(user_key,movie_key) dựa duplicate_pairs=0 đã kiểm trên 1000209 rating. Nguồn sau này có trùng thì dừng chốt chính sách, không tự UPSERT/bỏ dòng.
2. **Dim/bridge:** user/movie/date/genre, một bridge movie–genre. View ratings chỉ join user/movie theo khóa duy nhất, nên không nhân dòng bởi genre. View movies giữ cả phim chưa có rating; release_year nullable dù snapshot hiện tại không có năm NULL.
3. **Thời gian:** timestamp BIGINT giây Unix, rated_at TIMESTAMPTZ cùng thời điểm bằng CHECK epoch; rated_date UTC generated và FK ghép vào dim_date. View xuất TEXT ISO UTC-Z đúng contract, không phụ thuộc timezone client. Thứ tự hàng do serializer ORDER BY, không do view đảm bảo.
4. **Nạp lại:** full refresh một transaction trong database dự án riêng; danh sách truncate tường minh có bảng phụ thuộc analytics, nạp dimensions→bridge→fact, kiểm bốn hash/view trước commit bằng cùng connection. PK/UNIQUE chống trùng; lỗi rollback cả gói, không commit theo chunk. Nạp hai lần thành công phải bằng canonical/hash, không dựa surrogate.
5. **Phiên bản cụm:** hai bảng kết quả theo model_version, registry kỹ thuật kiểm active/valid. insufficient_evidence giữ cluster_id NULL và không tham gia mean; nhận đủ hai CSV + manifest trong một transaction. Không ghép hai phiên bản, không activate cụm rỗng/mean thiếu bằng chứng. Refresh vô hiệu hóa và yêu cầu kiểm/nạp lại kết quả cụm.

Vẫn cần review việc bổ sung registry/hai view nội bộ, UTC-Z ở giao diện và full refresh invalidation. Đây là phương án thiết kế, không quyết định nhóm đã duyệt. Tên database riêng/quyền ghi/role BI chỉ đọc sẽ chốt trước thực thi, không sử dụng database quản trị để nạp nghiệp vụ.

## Những cách tính phải giải thích rõ

Phim giả lập M có Action và Comedy, nhận hai đánh giá 4 và 2: fact có 2 dòng, SUM=6, mean=3. Join bridge cho 4 dòng gán genre; Action=2 và Comedy=2, không cộng thành 4 đánh giá duy nhất. Tổng toàn hệ thống lấy fact; khi cần tổng rating trong tập genre, dùng khóa rating duy nhất hoặc tập fact lọc tồn tại genre. Tỷ trọng gán genre mặc định: mỗi genre 2/4=50%; mẫu số là lượt gán. Mean roll-up dùng tổng điểm/tổng count có kiểu numeric, không trung bình các trung bình.

Năm không khớp bốn chữ số cuối title→NULL; không 0 hoặc năm hiện tại. Title giữ nguyên. NULL xuất ô rỗng, integer không .0, nhóm năm chưa xác định không bị loại khỏi KPI. Danh sách phim và rating không inner join bảng ngày theo release_year.

## Kiểm tra và giới hạn

**37/37 kiểm tra tĩnh mới đạt**: đối chiếu 12 bảng/64 cột, kiểu/null/PK/FK/index, cột/thứ tự/kiểu suy ra của bốn view với contract, ERD và dictionary. Chín FK có đích PK/UNIQUE và kiểu tương ứng; chín quan hệ 1:N trên ERD khớp FK; tám index tường minh dùng cột tồn tại và có mô tả. Đã đối chiếu miền mã/checksum mới với bằng chứng cũ, tính nhất quán của kế hoạch refresh, SQL v1 không đổi ngoài comment và file ngoài phạm vi giữ nguyên. Không coi kiểm cấu trúc văn bản là PostgreSQL parser hay chạy DDL. Inventory và từng kết quả lưu trong JSON v2.

Chưa kết nối DB, chưa tạo schema/bảng/view, chưa thử refresh/rollback/quyền/hiệu năng hoặc adapter DW. Canonical đúng trong báo cáo điều phối và bằng chứng cũ; đối soát ba mode trên DW thật thuộc G2. Một SHA metadata còn sửa không thay schema/checksum; G3/8A không là đầu vào phải đợi để hoàn thiện S04. Rubric giảng viên chưa xác minh, các tiêu chí chi tiết ở đây là tiêu chí thiết kế nội bộ.

## Git và bảo toàn

Nhánh **p1-s04-schema**, HEAD **aeb41d1fab5aa2760d69220e2eaefc401723eb0c**; main cục bộ vẫn b71d439. Giữ dirty tree đầu lượt; không commit/fetch/pull/merge/reset/stash/chuyển nhánh/push/PR. V1 checkpoint thuộc lượt trước. Bản sửa G1 được đọc qua snapshot remote, không chép sang thư mục P2. Bản kế hoạch untracked ngoài phạm vi và bằng chứng v1 giữ nguyên byte. Danh sách dirty/staged cuối lượt ghi trong JSON kiểm tĩnh v2; mọi thay đổi còn cục bộ.

## Năm ý bảo vệ

- Rating là đánh giá, không phải lượt xem; khóa nghiệp vụ được chốt bằng EDA thay vì giả định.
- Bridge biểu diễn một phim nhiều genre; tổng hệ thống lấy fact để tránh đếm lặp.
- SUM/COUNT có trọng số khi roll-up; năm thiếu là NULL có ý nghĩa, không tự điền.
- ID nguồn và UTC/serializer thống nhất giúp DW giao tiếp chính xác với máy P2.
- Transaction/rollback và model_version bảo vệ tính đầy đủ, không cho BI dùng gói cụm khác phiên bản hoặc khác DW.

**Thiết kế được điều phối chấp nhận. Công bố PR theo lệnh mới; dừng chờ review PR, chưa merge/triển khai hoặc tự sang S05.**
