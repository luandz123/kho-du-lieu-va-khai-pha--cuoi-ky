# Bàn giao S05 — WAITING_REVIEW

Cập nhật công bố ngày **17/10/2026, Asia/Bangkok**: điều phối đã review code/đối chiếu bằng chứng, báo chạy lại 9/9 unit test đạt và chưa phát hiện lỗi code chặn PR. Đây là ghi nhận **review của điều phối**, không tạo lời duyệt nguyên văn của người dùng hoặc tự suy nghiệm thu G2. Được giao thêm một lượt load cùng phiên bản rồi commit/push/mở PR; chưa merge/6A. Cặp cùng phiên bản đã đạt, không sửa code giữa hai run.

Đã mở [PR #7 — S05](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/7), nhánh p1-s05-staging → main; **OPEN, chưa MERGED**. Push và 25 file/blob đã xác minh thực tế ở head mở 2417416. Công bố có 19/19 kiểm trước commit và 8/8 sau fetch; chưa kiểm ETL DW/G2, quyền BI hoặc phục hồi backup.

## Phạm vi và căn cứ

Theo lệnh điều phối Bước 5 sau PR #6 MERGED, merge c3e4f998b3d8a0248770aeefada7200471fb3037. Đã đọc STATE/S04, SQL/ERD/dictionary/mapping/refresh; đồng bộ main bằng fast-forward và tạo p1-s05-staging. Giữ kế hoạch untracked ngoài phạm vi. Không commit/push/mở PR, không sửa file P2 hoặc manifest/source.

Database điều phối chọn **movielens_btl**. Khảo sát mới: Windows PostgreSQL 17.11 tại 127.0.0.1:5432, kết nối thành công; target chưa tồn tại, role hiện có đủ quyền CREATE DATABASE. Dùng postgres chỉ làm kết nối quản trị để tạo target, không chứa bảng nghiệp vụ. Không đổi credential/quyền hoặc database có sẵn khác.

## File và cách chạy

- [etl/s05_staging.py](../../etl/s05_staging.py): inputs, bootstrap, load, catalog; [hướng dẫn PowerShell](../../etl/README.md).
- [test_s05_staging.py](../../tests/warehouse/test_s05_staging.py): unit fixtures; [check_s05_rollback.py](../../tests/warehouse/check_s05_rollback.py): integration rollback tách biệt.
- Dùng nguyên [database/schema.sql](../../database/schema.sql), không đổi mô hình/DDL được duyệt. Bằng chứng chi tiết trong [s05_summary.json](../../results/warehouse/s05_summary.json), liên kết từng run và hash code thực chạy.
- Hồ sơ S05/STATE/DECISIONS/REVIEWS/PROMPTS P1 cập nhật; code đã commit tại 7981844ed2f4b50ed0705db5c04562d7e8fcf028. Các run vẫn giữ HEAD nền/hash byte **đúng lúc chạy chưa commit**; không sửa báo cáo cũ để gán lại phiên bản.

## Kết quả thực tế

| Kiểm | Kết quả |
|---|---|
| Nguồn độc lập | Kiểm mới bốn hash và line_count khớp source_manifest; tái sử dụng bản P1 tự tải, sao chép vào raw cục bộ riêng; không ghi P2 |
| Bốn bảng canonical | users=6040, movies=3883, movie_genres=6408, ratings=1000209; cả bốn SHA-256 khớp canonical_manifest bằng adapter/serializer đã kiểm nhận |
| DDL/cấu trúc | Thực thi trên movielens_btl; catalog thực khớp 12 bảng/64 cột/9 FK/27 CHECK/8 index tường minh; 6 view gồm 4 contract + 2 active |
| View contract | Tên/thứ tự/kiểu được đọc từ PostgreSQL; rated_at=text UTC-Z, timestamp=bigint. View đã tồn tại nhưng rỗng, chưa nghiệm thu adapter DW/G2 |
| Cặp chứng minh chạy lại cùng phiên bản | 0f24c3a → f5f11bcd; code_sha256=04cb9c6082bbe6224d4c2e7e4d33f312140f25dce52c4a8fbc54d2aebdf8e92f, không sửa code giữa hai run |
| Count và nội dung của cặp này | Cả hai đều users_raw=6040, movies_raw=3883, ratings_raw=1000209; cùng ba retained_row_csv_sha256, mọi field/source_line khớp nguồn, chín target DW/analytics vẫn rỗng |
| Nội dung | So toàn bộ dòng/field với nguồn; giữ title, genre raw và thứ tự. 50 title có ký tự ngoài ASCII, 993 title chứa dấu phẩy được so chính xác. Nguồn này không có title chứa dấu quote; fixture quote/é/comma đã kiểm COPY |
| Rollback | Sau COPY users+movies của fixture, ratings malformed gây rollback; cả seed fixture phục hồi đúng, staging thật và DW/analytics không đổi; schema thử đã dọn |
| Unit tests | 9/9 đạt, chỉ fixture tự tạo, không database |
| Đích DW/analytics | Cả 4 dimension, bridge, fact và 3 bảng analytics đều 0 dòng |

Staging giữ các trường text nguyên nguồn và source_line, không ZIP, chưa tạo khóa surrogate hay transform/nạp DW. Việc parse canonical để đối soát đầu vào diễn ra trong bộ nhớ, không phải ETL vào dimension/fact.

### Thứ tự các run — dùng thời điểm bắt đầu trong báo cáo

| Thứ tự | Run | Bắt đầu UTC | Bắt đầu Asia/Bangkok | Giây | Code hash đầu | Vai trò bằng chứng |
|---|---|---|---|---:|---|---|
| 1 | c122ce2fb93946a09cc02d47f65a8973 | 16/10/2026 16:03:45.575768Z | 16/10/2026 23:03:45.575768+07 | 16.844 | b9cf2df | Lịch sử, khác phiên bản |
| 2 | 0f24c3af4b8941dda6cb4d4ce075957d | 16/10/2026 16:04:50.909826Z | 16/10/2026 23:04:50.909826+07 | 10.078 | 04cb9c6 | Cặp cùng phiên bản — A |
| 3 | f5f11bcd42314042b34bfa1ff66e1f56 | 17/10/2026 14:41:09.503758Z | 17/10/2026 21:41:09.503758+07 | 9.281 | 04cb9c6 | Cặp cùng phiên bản — B |

Summary dùng cùng thứ tự/thời điểm/thời gian trên. Run c122ce2 giữ nguyên, chỉ chứng minh lịch sử dữ liệu, không dùng chung với 0f24c3a để kết luận chạy lại cùng code. Chín báo cáo lịch sử (kể cả FAIL) giữ nguyên byte; run mới không ghi đè báo cáo cũ.

## Lỗi đã gặp và cách xử lý

1. Kiểm adapter ban đầu dừng vì hash script CRLF checkout khác LF của PR. Đã chứng minh khác đúng xuống dòng và dùng Git blob để kiểm phiên bản code; **không** thay hash nguồn/canonical, không sửa file P2. Báo cáo FAIL ban đầu giữ nguyên.
2. Lần bootstrap đầu đã tạo database mới, nhưng checker catalog gọi fetchone trong generator hai lần gây TypeError. Transaction chứa DDL được rollback; kiểm lại chỉ public và 0 user object, database nguồn gốc P1 giữ nguyên. Sửa checker, giữ nguyên SQL, thực thi/kiểm lại thành công. CREATE DATABASE nằm ngoài transaction DDL nên không tuyên bố database đã bị rollback/xóa.

Các lỗi này đã xử lý và không còn chặn S05; không xóa bằng chứng thất bại. Code/check hiện tại được unit, catalog và nạp lần hai kiểm thực tế. Không suy từ kiểm này rằng mọi tình huống mất điện/mất kết nối hoặc phục hồi dump đã được thử.

## Giới hạn và điểm cần duyệt

S05 **WAITING_REVIEW** phần PR, code đã được điều phối review, cặp chạy lại cùng phiên bản đạt theo giao việc ngày 17/10. Chưa nạp dimension/bridge/fact, chưa làm 6A/G2/OLAP/BI; chưa bật Superset, kiểm quyền BI hoặc phục hồi backup. CHECK đã tồn tại/validated và được lưu định nghĩa; chưa chạy toàn bộ ca vi phạm của mô hình DW khi chưa có dữ liệu DW. Được commit/push/mở PR, chưa được merge hoặc chuyển bước.

SHA source_code_commit trong metadata P2 còn lệch provenance; S05 lưu commit/hash adapter thực tế, không sửa P2 hoặc chặn kiểm đầu vào có byte canonical đã khớp. Thời gian hai lượt là số đo riêng trên P1, không phải benchmark hoặc cam kết hiệu năng máy bảo vệ. Báo cáo Git chỉ thống kê/hash; dữ liệu theo user, raw và buffer COPY giữ cục bộ.

## Năm ý bảo vệ

1. Staging là vùng giữ trường nguồn/truy vết lỗi; DW mới là mô hình phân tích có dimension, bridge và fact.
2. Timestamp là thời điểm đánh giá; S05 giữ chuỗi raw, không biến thành phiên xem hoặc thời lượng.
3. Hash kiểm đúng nguồn; so từng field/source_line kiểm đúng Extract/COPY, không chỉ so số dòng.
4. Một transaction cho ba staging bảo đảm lỗi cuối tệp không để users/movies mới đi cùng ratings cũ.
5. Refresh staging thay snapshot và PK source_line chống lặp; fixture tách biệt chứng minh rollback mà không sửa nguồn thật.

Nhánh p1-s05-staging; HEAD nền trước công bố c3e4f998b3d8a0248770aeefada7200471fb3037, commit nội dung S05 7981844ed2f4b50ed0705db5c04562d7e8fcf028. Đã commit trước fetch; origin/main vẫn c3e4f998, không cần merge. Kế hoạch untracked ngoài phạm vi giữ nguyên. Trạng thái push/PR cuối tại STATE_P1 và báo cáo công bố sau xác minh thật. Chưa merge, không tự chuyển 6A.
