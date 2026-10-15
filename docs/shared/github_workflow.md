# Quy trình GitHub chung

## Quyết định hiện hành P1-G0-v1

S01 đã duyệt theo R-P1-01; Python3.12 và main đã chốt. Người dùng chỉ thị nguyên văn “các nhánh tạo sẽ không có codex đằng trước”: tất cả ví dụ codex/ trong phần nguồn trích nguyên văn dưới đây được áp dụng bằng cách bỏ codex/. G0 dùng **p1-g0-contract**; các nhánh đã tồn tại của P2 không tự đổi tên/xóa. Quy định này ưu tiên hơn ví dụ trong nguồn Word.

Đã kiểm remote HEAD và fetch thành công: main/b7698b2, main...origin/main=0/0. Quyền đọc đạt, quyền push chưa kiểm chứng. Bộ G0 gồm8tệp nền, hồ sơ agent duy trì cục bộ. G0 WAITING_REVIEW, chưa commit/PR/MERGED; chờ Đẩy G0 mới commit/push/PR, merge sau xác nhận riêng. P2 xác nhận contract sau nhận commit main đã merge trước EDA.


Phiên bản P1-S01-v1, 15/10/2026, **WAITING_REVIEW**. Hợp đồng kèm: v2. Các quy ước nguồn sau được chép nguyên văn; không cấp quyền thực hiện G0 trong S01.

## 1. Quy ước nguồn

Dùng một repository GitHub chung do nhóm cung cấp URL và quyền truy cập. Tài liệu này chỉ hướng dẫn công việc tương lai, không tự tạo hay push repository hiện tại. Không đoán URL, tên tài khoản hoặc thêm token vào lệnh. Chọn private nếu phù hợp yêu cầu môn học; quyền phân phối dữ liệu vẫn phải theo điều khoản nguồn.

G0 do P1 làm sau bước 1 đã duyệt: đưa .gitignore, đặc tả, hợp đồng và hướng dẫn tối thiểu lên main làm mốc nền. Chỉ lần bootstrap khi remote thực sự rỗng mới push trực tiếp main; nếu remote đã có lịch sử, tạo nhánh và PR. P2 clone mốc nền vào thư mục mới, không clone đè workspace có file. Môi trường 2-P2 có thể chuẩn bị trước G0 ngoài checkout; sau clone chỉ chuyển có chọn lọc file thuộc P2, tạo lại .venv tại checkout nếu cần.

Mỗi mốc dùng nhánh mới từ main mới nhất, ví dụ codex/p1-s06-etl hoặc codex/p2-s08-clusters. Không dùng một nhánh kéo dài toàn dự án. Sau merge, giữ nhánh cũ, chuyển main và tạo nhánh mốc tiếp theo. Hai người dùng checkout riêng, không cùng sửa một working tree.

Đầu mỗi mốc: kiểm tra git status và git remote -v; khi working tree sạch, git fetch origin, chuyển main, git pull --ff-only origin main, rồi tạo nhánh mốc. Nếu còn thay đổi, commit đúng phần đang làm trên nhánh riêng trước; không reset --hard hoặc tự bỏ file. Các lệnh ở đây phải được điều chỉnh theo nhánh mặc định thực tế nếu nhóm không dùng main.

Kết thúc mốc đã duyệt: chạy kiểm tra liên quan, xem git diff, stage từng đường dẫn thuộc vai trò, xem git diff --cached và danh sách file; commit, push -u origin <nhánh_mốc>, mở PR vào main. Nội dung PR ghi thay đổi, cách chạy, kết quả kiểm tra, contract_version và đầu ra bàn giao. Ghi link PR và commit vào hồ sơ bước sau khi lệnh thành công; không tự ghi đã push khi lỗi xác thực.

Người còn lại review PR, kiểm tra giao diện và xác nhận trên GitHub hoặc qua yêu cầu rõ ràng trong chat. Chỉ merge sau xác nhận thật và kiểm tra đạt; dùng merge commit nhất quán để dễ theo dõi. Duyệt bước chức năng không tự động là quyền merge. Nếu công cụ không có quyền GitHub, chuẩn bị commit và hướng dẫn thao tác rồi chờ người dùng xác nhận kết quả thực tế.

Sau merge, bên nhận lấy main bằng fetch/pull; bên đang làm nhánh riêng có thể merge origin/main vào nhánh hiện tại khi working tree sạch. Không chép toàn bộ docs hoặc thư mục code từ máy kia đè vào checkout. Khi conflict, đọc hai thay đổi, giữ quyền sở hữu file, nhờ chủ file chốt phần chưa rõ; không dùng ours/theirs hàng loạt và không force-push.

Đưa lên Git: code, SQL, cấu hình mẫu không bí mật, requirements theo vai trò, tài liệu, test fixture tự tạo, manifest checksum và kết quả tổng hợp đã rà soát. Không dùng git add . thiếu kiểm tra. .gitignore phải loại .env và credential, .venv, cache, data/raw, data/processed, dump DB, metadata/volume Superset, mô hình lớn, dữ liệu theo user, gói bàn giao chứa user và file xuất có connection URI/mật khẩu.

P1 sở hữu requirements.txt tổng; P1 ghi docs/P1/requirements-p1.txt, P2 chỉ ghi docs/P2/requirements-p2.txt. Hai bên thống nhất Python ở G0, ghi thư viện đã kiểm chứng. P1 hợp nhất requirements ở 12A và P2 kiểm thử. Nếu cần đổi phiên bản ảnh hưởng nhau, mở PR ghi tác động, không sửa chéo file quyền sở hữu.

Dữ liệu nguồn mỗi máy tự tải từ GroupLens và so hash. File theo user và backup tái tạo cục bộ bằng script, không tự đăng lên GitHub kể cả Release/Artifact. Gói cụm P1 có thể tái tạo từ phiên bản code P2 đã merge; nếu nhóm có phương thức chia sẻ được phép, ghi đường dẫn và checksum trong hồ sơ. GitHub không phải kênh mặc định để phân phối MovieLens.
## 2. Quyền ghi tệp

| Vai trò | Phạm vi |
|---|---|
| P1 | database/, etl/, olap/, dashboard/, tests/warehouse/, results/warehouse/, results/olap/, docs/P1/, docs/shared/, docs/agent/steps/P1/ và docs/agent/*_P1.md |
| P1 sở hữu tệp chung | .gitignore, .env.example, requirements.txt, README.md, docs/project_spec.md, docs/acceptance.md, docs/report_outline.md, docs/slide_outline.md, docs/integration_checklist.md, docs/bao_cao_BTL.docx, docs/slide_BTL.pptx và docs/demo_script.md |
| P2 | mining/, tests/mining/, results/eda/, results/mining/, docs/P2/, docs/agent/steps/P2/ và docs/agent/*_P2.md; sở hữu data/source_manifest.json |
| Cục bộ từng máy | data/raw/, data/processed/, .venv/, .env; không commit dữ liệu/bí mật. P2 không ghi requirements.txt gốc hoặc trạng thái P1; P1 không ghi trạng thái P2 |

## 3. Các mốc và đồng bộ

| Mốc | Chủ trì và đầu ra | Hành động Git sau duyệt và lệnh Đẩy mốc |
|---|---|---|
| G0 | P1 sau S01: đặc tả/nghiệm thu/contract/workflow/nền tối thiểu | codex/p1-g0-contract → PR main vì checkout có lịch sử; không bootstrap thẳng main. P2 clone mốc nền vào thư mục mới |
| G1 | P2 sau 3: EDA/adapter/manifest | Nhánh mốc P2 → PR → review/merge được xác nhận; P1 nhận cho 4–6, P2 tiếp 8–10 |
| G2 | P1 sau 6D: DW/view/ETL/manifest | codex/p1-s06-etl → PR; P2 chạy G2-P2 sớm, P1 tiếp OLAP |
| G3 | P2 sau 8B rồi sau 10: cụm trước, CF sau | Nhánh riêng từng mốc, ví dụ codex/p2-s08-clusters; P1 nhận cụm cho 11B không chờ CF |
| G4 | P1 12A → P2 12 → P1 12B | codex/p1-s12a-integration → commit ứng viên → PR tái lập P2 → codex/p1-s12b-acceptance; duyệt/merge từng mốc, không chờ vòng |
| G5 | Hai bên 13/14, P1 ghép tổng | PR dàn ý codex/p1-s13-outline, chương codex/p1-s13-chapters, tổng codex/p1-s13-report; dàn ý slide bàn giao sớm, PR demo/tổng duyệt; tag cuối sau nghiệm thu và xác nhận |

PR P1 còn gồm codex/p1-s02-env, codex/p1-s04-schema, codex/p1-s05-staging, codex/p1-s07-olap và PR dashboard theo tiểu bước. Mỗi nhánh mới từ main mới nhất khi đủ tiền đề và được giao.

## 4. Áp dụng checkout này

P1 dùng `D:/kho-du-lieu-va-khai-pha--cuoi-ky`, remote cấu hình https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky.git, main/b7698b2. Đây là xác minh cấu hình local, chưa xác minh quyền mạng/push. G0 phải fetch/so sánh khi được giao; không allow-unrelated-histories hoặc force để ép ghép. S01 chỉ ghi tài liệu, chưa stage/commit/push/PR.

APPROVED chức năng khác MERGED. Duyệt kèm lệnh Đẩy mốc cho phép commit/push/PR đúng mốc; merge cần xác nhận cụ thể. Không tự tạo repository, đổi remote, xóa nhánh hoặc force-push. Ngoại lệ bootstrap rỗng không áp dụng checkout có lịch sử này.

Hồ sơ chung cũ tại `D:/BTL_Kho_Du_Lieu` chỉ đọc, chưa có quyết định ánh xạ. Không chép toàn bộ thư mục cũ hoặc P2 đè checkout này. Gói có user/dump/backup tái tạo cục bộ; nếu nhóm chọn kênh chia sẻ được phép thì ghi đường dẫn/checksum, không đính PR/Release/Artifact.
