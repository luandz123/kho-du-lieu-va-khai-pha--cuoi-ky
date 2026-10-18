# Công bố PR ETL/G2

## Trạng thái và nguồn review

Điều phối chấp nhận 6D cục bộ sau review code, chạy lại65/65 unit test và đối chiếu29artifact. Hai run **16421c84a7a244b5ad4b60f4ce4dfbc6** và **6501a547065246869b98b6ab6531190e** COMMITTED, cùng bundle/config/checks. Thông tin này có nguồn từ điều phối, không phải lời duyệt nguyên văn do agent tạo.

Code6D đã commit tại **4fa9cf17aa41e5ff84d4490886eeac27971e46f6** trên p1-s06-etl. Fetch xác nhận origin/main **52dd682920e0587f3a474fe284b9bf5635ab6aac** vẫn là base, không có thay đổi main mới và không cần merge thêm. Chưa push/mởPR ở thời điểm chốt mốc này; URLPR sẽ cập nhật sau xác minh. **Chưa merge, P2 chưa kiểm nhận G2.**

## Truy vết runtime và code công bố

- Checkpoint6A cfed2c848e196bee73fcb61ec5fd017cc9dbaf98; checkpoint6B d698d8eab4bd8fbf828ffa23e434ddf52ba9eebe; checkpoint6C/base runtime6D **c143f5d7081da041aad38c0a97c0a8ac0ef721cb**.
- Bundle working tree thực chạy **b858a879b6a0d03ef5b7b1533caf93d1c76f421b8171b5579f61ced840638422**. Commit công bố là mốc lưu code này sau khi chạy, không thay base_commit trong runreport.
- **Commit code làm căn cứ tái tạo: 4fa9cf17aa41e5ff84d4490886eeac27971e46f6.** Các commit hồ sơ công bố tiếp theo chỉ ghi trạng thái Git/PR, không đổi pipeline. Git blob LF của năm file bundle được đối chiếu riêng với file Windows và hash runtime trong ledger; không thay byte nguồn/CSV để ép khớp.
- Giữ reportPASS/FAIL6A–6D và [summary6D](../../results/warehouse/s06d_summary.json) nguyên vẹn. Ledger29artifact là snapshot lúc bàn giao; hồ sơ được sửa để công bố có hash mới trong [ledger công bố](g2_publication.json).
- So code Windows với Git blob theo LF sau khi phân biệt CRLF; không chuẩn hóa byte nguồn/canonical. Code/runtime/manifest và JSON không được gán commit mới như thể đã chạy ở commit đó.

## Nội dung và quyền truy cập

PR bao gồm toàn bộ checkpoint6A/B/C và6D: dimension/bridge/fact/fullrefresh nguyên tử, unit/fixture tự tạo, hậu kiểm, metadata/manifest và bằng chứng tổng hợp; không thêm DDL mới. Không raw/processed/CSV theo user/dump/.env/credential hoặc kế hoạch ngoài phạm vi. Filelist toànPR và kiểm thực tế được ghi trong ledger sau rà diff/base.

Rà trước push:65file P1,34JSON (trước ledger tự tham chiếu) và16Python hợp lệ;61blob thay đổi trong ba checkpoint đã quét chữ ký secret. Diffcheck đạt, helper refactor giữ quy tắc chuẩn hóa và guard lịch sử. Kế thừa bằng chứng65unit/fixture/adapter/hậu kiểm đã review; không ghi là vừa chạy lại các phép kiểm DB hoặc fullrefresh trong lượt công bố.

[Gói DW](dw_handoff.md), [manifest](../../results/warehouse/dw_manifest.json), [bàn giao6D](s06d_handoff.md) giữ hai run, bốn hash/count và số liệu thực. Adapter P2 tại P1 đã so raw/CSV/DW mọicell trên PostgreSQL thật, không thay việc P2 nhận G2.

`dedicated_read_only_account_verified=false`, `p2_intake_status=NOT_CONFIRMED`. Account đang kiểm có quyền quản trị/ghi dù session READONLY; không gửi credential này cho P2. Còn cần tài khoản chỉ đọc chuyên dụng và phương thức kết nối riêng được nhóm chốt, hoặc P2 tái tạo DW cục bộ từ nguồn chính thức theo hướng dẫn. Chưa tạo role/cấp quyền/mở PostgreSQL công khai/thay firewall hoặc kiểm remote P2 trong lượt công bố. Chưa OLAP/dashboard/G3.
