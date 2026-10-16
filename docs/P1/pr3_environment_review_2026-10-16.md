# Rà PR3 và chuẩn bị kiểm nhận G1

Ngày16/10/2026, Asia/Bangkok. Phạm vi theo điều phối: chỉ rà môi trường/PR và lập checklist; không sửa code/config/duyệt/P2, không mở S04, commit/push/PR/merge. Không fetch/pull/stash/reset/chuyển nhánh.

## 1. Git và căn cứ diff thực tế

- Nhánh giữ **p1-s02-env**, HEAD **c53b92e2a4a3c25c275ea19c1ec9ebbfbc196c6b**.
- API PR3 vừa xác minh: OPEN, merged=false; head p1-s02-env/c53b92e..., base main/**ff87081add55137a0b8c8541d1a84e7ef8443d37**.
- PR: https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/3. Diff27 file; đã đối chiếu hashblob27 file ở commit HEAD với API PR file list, đều khớp. Đọc diff so base thật, không coi diff workingtree là diffPR.
- PR bao gồm code/config/test/requirements P1, báo cáo không bí mật và hồ sơP1 đến S02. Không sửa fileP2 trong diff.
- Các sửa STATE/DECISIONS/PROMPTS P1 và untracked S04/kế hoạch16/10 là workingtree cũ **ngoài head PR**; giữ nguyên trong lượt này. Hai file rà soát/checklist mới cũng chưa nằm trong PR.

## 2. Điểm đạt của PR3

- Không thấy .env thật/venv/raw/processed/dump/key/token hoặc dữ liệu theo user trong27 filePR và tracked inventory. Rà signature credentialURL/privatekey/token không phát hiện; đây là kiểm tra có giới hạn, không tuyên bố quét toàn lịch sử Git.
- Mẫu root/nested .env.example không chứa password/secret; secrets runtime tách khỏi source. Docker build context allowlist chỉ Dockerfile/config/init, không mang.env vào build.
- Requirements P1 khóa11 distribution, requirements gốc chỉincludeP1, không giả đã hợp nhấtP2. Khác patch3.12.14 P1/3.12.3 P2 được ghi, không nhận testMLP2 đã chạy trênP1.
- Checker SQL đặt readonly/timeout, chỉSELECT1/server_version; container nhận cấu hình qua stdin, không argvURI/log. Không tạoDB/bảng ở checker. Lỗi xuất nhãn, không rawexception.
- Compose tách metadata PostgreSQL/volume khỏi DW Windows, bind web127.0.0.1:8089, ghim6.1.0/driver 2.9.13/postgres 17.11; không thao tác down-v/reset.

## 3. Lỗi/rào cản và việc cần sửa theo lượt được giao riêng

### G1 profile CSV bị ignore — đã tái hiện

`git check-ignore --no-index -v results/eda/data_profile.csv` xác nhận `.gitignore` dòng 21:`*.csv` đang chặn tệp bắt buộc củaG1. Quy tắc này có từ **base G0**, không phải regression do dòng mới PR3. Canonical/source manifest JSON không bị chặn trong phép kiểm; handoff theo user vẫn bị chặn đúng chủ đích.

Đề nghị P1 được giao cho phép riêng `results/eda/data_profile.csv` sau khi kiểm chỉ là thống kê tổng hợp, kèm rà staged; không mở toàn bộCSV. P2 không tự sửa .gitignore P1. Lượt này **chưa sửa** quy tắc hoặc dùng force-add.

### Cần làm rõ trước tái lập máy khác

- `.venv` dựa runtime trong cache/bundle cá nhân. Đường dẫn này là bằng chứng máy P1, không là runtime chắc chắn có trên máy khác; cần hướng dẫn chọn Python 3.12 đã cài khi tạo môi trường sạch. Chưa kiểm rebuild/restore sạch trong lượt này.
- Superset checker hardcode tên container/port/phiên bản dự án hiện tại. Hợp với instanceP1, chưa là checker tổng quát cho mọi máy/projectname.
- Các nhãn trạng thái cũ trong đặc tả/hồ sơ là lịch sử; nên phân biệt rõ tại bàn giao/PR, không dùng chúng tự thay lời duyệt. Không sửa trạng thái trong lượt rà này.

Không phát hiện thêm lỗi chức năng tái hiện trong các phép kiểm nhẹ đã chạy. Điều đó không thay thế kiểm dựng mới, UI, DW hoặc testnghiệp vụ.

## 4. Kiểm tra mới ngày 16/10, không dùng báo cáo15/10 làm kết quả mới

| Kiểm tra | Kết quả mới | Cách thực hiện |
|---|---|---|
| Python/import | 3.12.14, đúng .venv,5 góiimportPASS | Chạy check_environment bằng .venv với-B, **không --report**, không ghi đè reportcũ |
| SQLWindows | SELECT1_PASS/server 17.11/exit 0 | Checkerreadonly dùng.env chỉ trong bộ nhớ; không in credential |
| Dependency | pipcheckPASS, không xung đột | python-mpipcheck |
| Superset | Web/metadata Exited255 khoảng4 giờ; init lịch sử exit 0 | dockerps chỉ đọc, **không khởi động**, không testSQLcontainer vì đang dừng |
| Ignore/tracked | ProfileCSV bị chặn; manifest JSON không bị chặn; không sensitive tracked theo pathcheck | gitcheck-ignore vàgitls-files chỉ đọc |
| Diff/API |27 blobPR khớpHEAD; không P2/data/secret signature | API GET và local diff base...HEAD, không fetch |

Thời điểm SQL mới: **2026-10-16T12:13:14.941270+00:00**, tức **19:13:14 Asia/Bangkok**. Bằng chứng mới được ghi trong ghi chú này và tooloutput của chat; không ghi đè results/warehouse/*.json ngày 15/10. Superset SQL/health15/10 chỉ là lịch sử; hôm nay dịch vụ dừng. Chưa xác minh UI login/DW view/role BI, rebuild image và tái lập máy sạch.

## 5. Thông tin P2 qua điều phối

Điều phối báo P2 xác nhận contract v2 tại 3A và tạo canonical/manifest3B, chưapush/PR G1, còn thiếu adapter/báo cáo. Nguồn là **báo cáo qua điều phối**, chưa được P1 kiểm bằngfile/PR; không ghi3B hoặcP2 APPROVED, không cập nhật trườngapprovalJSON/P2STATE. G1 chưa kiểm nhận, G3 chưa nhận, G2 chưa làm.

## 6. Thay đổi riêng của lượt này và điểm dừng

Chỉ tạo `docs/P1/g1_intake_checklist.md` và ghi chú rà soát này. Không sửa code/config/requirements/STATE/DECISIONS/REVIEWS/PROMPTS cũ hoặc tệpP2. Giữ nguyên3 filemodified và2 fileuntracked có sẵn. Khôngstaging/commit/push/PR/merge hoặc tải dữ liệu. S04 chưa mở.

Việc cần điều phối tiếp: P2 hoàn thiện/push G1 để có bằng chứng; xử lý phạm vi whitelistprofile CSV bằng lệnh riêng choP1; reviewPR3 và quyết định merge riêng. Sau đủ tiền đề mới giao P1 kiểm nhậnG1/S04; checklist này không thay phê duyệt.
