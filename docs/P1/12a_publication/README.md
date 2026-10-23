# Công bố PR12A — gói tích hợp đã nghiệm thu kỹ thuật

Điều phối chấp nhận run `57c1e8e3d3f445c4b3eeddbfc3364709` và giao commit/push/PR, không merge/G4. Base PR24 `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02`, nhánh `codex/p1-s12a-integration`. Candidate cuối **chưa chọn**; sẽ là merge commit của PR12A sau khi được review và merge, không phải HEAD nhánh hoặc commit nền.

## Truy vết và tái lập

- [Phiếu gói tích hợp](../integration_candidate.md) chứa base, contract/config/source/package hashes, hai chu trình và giới hạn.
- [Runbook](../integration_runbook.md) theo thứ tự môi trường/tải nguồn → schema/staging/fullrefresh → kiểmDW/OLAP → MLquaDW → G3 → Superset8092, gồm lệnh DW-only cho P2.
- [Summary thực chạy](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json), [READONLY hậu kiểm](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/postflight.json) và [environment](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/environment.json) giữ nguyên byte sau nghiệm thu.
- Runtime bundleSHA `3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22`, code khi chạy chưa commit; dictionary từng module trong summary. Commit công bố được ghi riêng, không thay base/hash lịch sử.
- Test metric trong official_test_metrics_reference.json là kết quả tham chiếu từ receipt/report chính thức củaP2; không gọi lại evaluator hoặc mô tả là vừa đánh giá test từDW.

88 test mục tiêu và hai chu trình đã chạy thật trên Windows Python3.12.14, venv `tmp/s12a-venv`, Superset6.1.0 container riêng. DW-only helper `etl/recreate_integration_dw.py`: defaultplan-only đã chạy; apply riêng chưa chạy thêm trênP1, không tuyên bố Linux/P2 đã kiểm. P2 tự tải nguồn/sohash/dùnglocalcredential và gửi xác nhận thực; intakeG2 vẫn **NOT_CONFIRMED**.

## Kiểm công bố

Rà toàn diff thuộc P1, PythonAST/JSON/whitespace, secret/credentialURI/passwordhash, ignore và hash runtime/artifact; không chạy ETL/G3/dump/restore/evaluator hoặc tạo lại dịch vụ. Manifest công bố mới băm byte hiện tại của code/tài liệu. Ledger runtime cũ có thể chứa hash tài liệu lúc bàn giao trước review; giữ như lịch sử, không sửa cho khớp tài liệu vừa chốt.

Kiểm Git blob phân biệt LF/CRLF của code trên Windows; không chuẩn hóa byte nguồn/canonical/góiG3 hoặc sửa receipt. File/blob PR và toàn cây remote phải khớp GitHEAD cuối. Kết quả kiểm công bố/quan sátremote/filelist được ghi riêng trong thư mục này.

Không công bố env/SECRET_KEY/passwordhash/URIcredential/dump/backup/modelbinary/rawlog/user-level/CLIprivate. Kế hoạch untracked `docs/KE_HOACH_BTL_MOVIELENS.md` giữ ngoài commit. Code/table/viewcontract/metric/config P2 không sửa để công bố.

## Tài nguyên giữ và giới hạn

Giữ `movielens_btl_int_20261023_57c1e8e3`, source demo `movielens_btl`, clone `movielens_btl_restore_20261021_2856ed49`, backup và metadata/volume trước. 8092 giữ kết nối DBtíchhợp để review;8089 phục vụdemo;8091 dừng. Không đổi ACL/firewall hoặc tạo lại tài nguyên trong lượt công bố.

Giới hạn same-host Windows/PG17.11/Superset6.1.0; chưa tái lập môi trường tổng trênLinux/P2 hoặc fullstack mới. Giữ P2intakeG2NOT_CONFIRMED/G4chưa hoàn thành. Chức năng12A được điều phối chấp nhận, PR vẫn cần review/merge riêng, chưa candidate cuối.
