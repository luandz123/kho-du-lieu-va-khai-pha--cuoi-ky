# Quyết định P1

Phiên bản P1-S01-v1 ngày 15/10/2026. Không thay thế hồ sơ duyệt; đề xuất chưa phải quyết định nhóm đã duyệt.

| Mã | Nội dung và tác động | Trạng thái/căn cứ |
|---|---|---|
| P1-D01 | MovieLens1M/PostgreSQL/Python/6 OLAP/K-Means/CF+baseline+metric/3 Superset/report-slide; giới hạn Q1–Q3 | Ràng buộc Prompt chung, không mở rộng |
| P1-D02 | Checkout hiện tại; giữ bản cũ; S00 đã duyệt, S01 được giao | Xác minh local và “duyệt bước 0”; không phải duyệt S01 |
| P1-D03 | Contract2 nguyên quy ước, MD/JSON/workflow | WAITING_REVIEW, P1/P2 chưa xác nhận |
| P1-D04 | PostgreSQL 17.11 thay15/16 ghi trong nền; SQL/quyền kiểm lại | Đề xuất trình ở S00, cụ thể hóa S01 chờ chốt; không nhập lời duyệt bản cũ |
| P1-D05 | P1 Python 3.14/P2 Linux3.12.3; đề nghị dòng 3.12 chung tại G0 | WAITING_REVIEW; chưa chọn patch/pin hoặc cài P1; P2 tự báo, chưa test |
| P1-D06 | Kế thừa chọn lọc Superset6.1.0/8089, metadata riêng, giữ 8088/dịch vụ khác | WAITING_REVIEW; chưa copy/khởi động/chứng minh chạy hiện tại |
| P1-D07 | Nặng chạy lần lượt, thưa/theo lô, đo tài nguyên | WAITING_REVIEW; không tự đổi K/lọc phim/lấy mẫu Silhouette |
| P1-D08 | Lịch15–26/10, bảo vệ27/10; G0–G5; 12A→12-P2→12B và cụm trước CF | Lịch đề nghị S01 chờ duyệt; hạn bảo vệ là ràng buộc; không bỏ gate |
| P1-D09 | Hồ sơ chung cũ chỉ đọc, chưa ánh xạ/nhận APPROVED | Prompt chung; cần nhóm chốt cách kế thừa trước ánh xạ |
| P1-D10 | Không cần CF thắng baseline, không ngưỡng Silhouette buộc đạt; tính đúng/tái lập | Theo kế hoạch và lệnh S01; chi tiết acceptance chờ duyệt |
| P1-D11 | Remote có lịch sử, G0 qua nhánh/PR | Git local; kiểm quyền/remote thật khi G0 được giao; S01 không đẩy |
| P1-D12 | Rubric/checkout P2/máy bảo vệ chưa xác minh | Giới hạn bằng chứng, không biến tiêu chí nội bộ thành rubric |

Đổi giao diện cần phiên bản mới, chủ file xác nhận và nêu đầu ra phải chạy lại; không tự sửa hoặc tự duyệt bước cũ.

## Cập nhật tại G0 ngày15/10/2026

R-P1-01 duyệt P1-S01-v1; các nhãn đề xuất trong bảng là lịch sử. P1-D03 (phía P1), D04/D06/D07/D08 và phạm vi/nghiệm thu được duyệt; chưa đồng nghĩa runtime đã đạt. P1-D09 tiếp tục giữ hồ sơ cũ nguyên trạng; chưa có lựa chọn ánh xạ cụ thể để thi hành.

| Mã | Quyết định mới | Căn cứ và tác động |
|---|---|---|
| P1-D13 | Dòng Python3.12 chung, main mặc định | Người dùng “Duyệt” sau câu hỏi xác nhận. P1 còn3.14; cài/kiểm chứng3.12 thuộc setup, chưa chốt patch/pin tổng |
| P1-D14 | Nhánh mới không có codex/; G0 p1-g0-contract | Nguyên văn “các nhánh tạo sẽ không có codex đằng trước”. Thay quy ước tên của workflow nguồn; không tự đổi/xóa nhánh của P2 hoặc nhánh cũ |
| P1-D15 | Tám tệp nền G0 stage có chọn lọc; hồ sơ agent cập nhật cục bộ, chưa stage | Bootstrap tối thiểu; không git add .; commit/push/PR chờ Đẩy G0 |
| P1-D16 | P2 báo đã xong2/PR chờ duyệt, Python3.12.3 với các pin | numpy2.0.2/scipy1.14.1/scikit-learn1.5.2/pandas2.3.3/pytest8.4.2 là thông tin do người dùng chuyển, chưa kiểm PR hoặc chạy P1; không ghi requirements P2 |

Remote HEAD/fetch đã xác minh main/b7698b2, main...origin/main=0/0. Quyền đọc đạt; quyền ghi chưa thực kiểm. Không dùng quyền đọc để tuyên bố quyền push.

## Kết quả Đẩy G0

P1-D17, ngày15/10/2026: người dùng “Duyệt và đẩy g0” duyệt bộ G0/cấp quyền commit-push-PR. Commit5c31e80 thành công, push403 vì tài khoản GitHub hungvu205 thiếu quyền ghi repo luandz123/kho-du-lieu-va-khai-pha--cuoi-ky. Giữ commit/remote/nhánh, không tự đổi danh tính hoặc tạo fork. G0 APPROVED chức năng, công bố BLOCKED, PR/MERGED chưa có. Sau bổ sung quyền tiếp tục đúng commit theo quyền đẩy đã có; không cần xin lại duyệt mốc, merge vẫn riêng.

P1-D18, ngày15/10/2026: sau “đã vào push lại”, push5c31e80 thành công và mở PR#1 OPEN vào main. Blocker403 đã giải quyết; giữ nguyên commit/nhánh, không tạo fork/đổi remote. Dừng trước merge; P2 nhận main sau merge và xác nhận contract.

P1-D19, ngày15/10/2026: sau “đã merge”, xác minh GitHub PR#1 MERGED/eff54aee..., đồng bộ main bằng fast-forward, giữ nhánh G0 và hồ sơ cục bộ. Mốc nền sẵn sàng cho P2 pull/xác nhận contract; không tự sang bước2 hoặc gửi tin chat khác.

## S02-P1-v1 ngày15/10/2026

P1-D20: nhánh p1-s02-env không codex/, theo lệnh mới; chỉ setup sau S01 duyệt/G0 merge, chưa đẩy.

P1-D21: dùng Python3.12.14 bundled có sẵn để tạo venv, không cài toàn hệ thống hoặc đổi3.14; ghi base_prefix/cache dependency và nhu cầu tạo lại. P1 pins đã cài/import thực, requirements gốc chỉ include P1, chưa hợp nhất P2 hoặc nhận ML đã chạy.

P1-D22: kế thừa chọn lọc Superset6.1.0/8089, giữ metadata/volume/key/env hiện có. Sao chép secret.env cục bộ không đọc/in/hash; dùng docker start container cũ để tránh reset/recreate; config ghim6.1.0/postgres17.11, chưa rebuild máy sạch.

P1-D23: checker SQL readonly/timeout/SELECT1, .env chỉ đọc khi explicit; container nhận cấu hình qua stdin. Không raw exception/credential log; thiếu/failed là exit2/3. MetadataSQL/TCP không thay SQL Windows. Xác thực hiện lỗi, chờ user sửa, không đoán mật khẩu hoặc tạoDB.

P1-D24: nested.env.example được allowlist, secret.env vẫn ignore. Không có sensitive tracked nên không cần bỏ theo dõi; không sửa lịch sử Git. S02 giữ phạm vi chưa DW/ETL/mining/dashboard.

P1-D25: S02-v2 sau user báo đã sửa, cả host/container SELECT1_PASS17.11/exit0 theo.env thật. Khởi động lại hai container dự án đã dừng, giữ volume/key. Các lỗiSQL trước đã giải quyết; view/roleBI/UI/dashboard còn chưa nghiệm thu. Chờ duyệt S02, không tự chuyển bước/đẩy.

P1-D26: người dùng “duyệt và đẩy bước2” duyệt P1-S02-v2, cấp quyền commit/push/PR, không merge. Fetch trước đẩy thấy origin/main ff87081 đã gộp PR#2/P2, chỉ thêm file P2 không trùng; tích hợp nguyên vẹn sau commit phần P1, không sửa/chạy hoặc tự duyệt sản phẩm P2. Từ S02 đưa hồ sơ P1/tiền đề G0-S00-S01 vào Git để lưu dấu vết; giới hạn8tệp chỉ áp dụng bootstrap G0, không gom file môi trường/dữ liệu/bí mật.
