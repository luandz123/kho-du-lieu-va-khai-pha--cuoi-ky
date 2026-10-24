# Hồ sơ biên tập và checklist phần báo cáo P1

## Cập nhật hình được duyệt — 24/10/2026

Điều phối duyệt checklist ghép và ảnh Sở thích bổ sung. Chương4 bổ sung Hình4.3 (`all_kpis.jpg`) và Hình4.4 (`cluster1_F_25_34_top.jpg`), giữ nguyên byte ảnh gốc, không cắt/sửa số liệu. Caption ghi instance8089, ngày24/10 và filter toàn bộ/cụm1-F-25–34. Bảng4.4 giữ nguyên. Scope heatmap dẫn SQL profile, snapshot cấu hình API và reconciliation, không suy chỉ từ screenshot.

Nhật ký dịch vụ: lượt trước chỉ start đúng metadata/web8089 hiện hữu sau khi xác minh chúng dừng. SameID/volume,health200;8091/8092 giữ nguyên. Khảo sát log chưa xác minh nguyên nhân gốc dừng. Thông tin này thuộc hồ sơ biên tập, không chèn vào thân chương. Lượt công bố hình không khởi động instance hoặc gọi dashboard/pipeline/evaluator.

Đã có hai ảnh được điều phối duyệt; mục “chưa có ảnh rõ” và lần kết nối thất bại bên dưới là quan sát lịch sử trước khi khôi phục8089, không là trạng thái hiện hành. Ảnh thử/DOMlog/rawlog giữ cục bộ, không trong phần bổ sung. Manifest công bố chỉ có hai ảnh tại `captures/20261024_preferences/selected_manifest.json`.

Phần ghép sáu chương/DOCX/P2 vẫn chờ đúng tiền đề. PR27 được kiểm OPEN tại HEADd018921… trước bổ sung; dùng chính PR27, không mở PR trùng và không tự merge. HEAD mới và diff riêng sau mốc duyệt được xác minh khi push.

Ngày24/10/2026, phiên bản biên tập P1-v2. Nguồn giao việc: điều phối qua thông điệp người dùng đã chấp nhận nội dung chương1/3/4 và phụ lục, giao chỉnh rồi commit/push/mởPR phần chương. Đây là chấp nhận nội dung của điều phối, không là xác nhận G4 hoặc quyền tự merge.

## 1. Tách bản báo cáo khỏi hồ sơ công việc

- Thân chương giữ bài toán, phương pháp, thiết kế, kết quả, nguồn và giới hạn khoa học/môi trường. Bỏ banner trạng thái công việc, câu ghi đã xem ảnh, lời nhắc ảnh mờ và các bước review khỏi thân chương.
- Nhãn hình vẫn ghi nguồn, instance/filter cần thiết để hiểu nội dung. Chi tiết chất lượng ảnh, ảnh chưa chọn và việc cần làm nằm ở hồ sơ này, không trình thành kết quả thực nghiệm.
- Phụ lục giữ run/hash/commit/lệnh dài. Snapshot `draft_audit.json` và `image_review.json` của bản trước giữ nguyên, không sửa hash lịch sử để trỏ bản biên tập mới.
- Sơ đồ chương1 tách Q1/G3/analytics/BI khỏi Q2/split/CF/baseline/evaluation/CLI. Không đưa nhãn cụm Q1 vào đánh giá Q2.
- Bỏ khẳng định ngưỡng ranking đã được chọn trước khi xem kết quả. Bản báo cáo chỉ nói ngưỡng quý trước≥100 là quy tắc trong SQL/hồ sơ được đối soát; không suy thời điểm ra quyết định từ kết quả hiện có.

## 2. Git và bảo toàn

PR26 dàn ý đã được API xác minh MERGED tại `dad848eedcd11230559acfc01ee103be718289a2`. Main tại lúc tạo nhánh phần chương là commit này. Nhánh công bố mới `codex/p1-s13-chapters` tạo từ origin/main, không dùng HEAD nhánh dàn ý làm base mới.

Phần bản thảo và hồ sơ cục bộ được checkpoint có chọn lọc `b681f68` trên nhánh cũ, chuyển bằng cherry-pick `3c7157d` sang nhánh mới. Kế hoạch `docs/KE_HOACH_BTL_MOVIELENS.md` giữ untracked và giữ hash cũ; không reset/stash/ghi đè P2. Bản chấp nhận trước biên tập được giữ trong checkpoint và snapshot ignored cục bộ.

Các cập nhật OPEN/WAITING_REVIEW của PR26 trong hồ sơ cũ là lịch sử. Quan sát merge mới ghi riêng, không thay receipt/runtime report. PR phần chương chưa được merge; kết quả xuất bản được ghi sau xác minh.

## 3. Hình đã xem và việc chụp lại

Lượt viết trước đã xem7ảnh thật, ghi tại [image_review.json](image_review.json). Giữ nguyên file đó và ảnh lịch sử. Bản biên tập không tạo ảnh giả hoặc sửa dashboard để khớp số liệu.

| Hình / ứng viên | Quyết định biên tập | Phạm vi và giới hạn |
|---|---|---|
| Hình3.1 / rating_distribution.png | Giữ | Nhãn/cột rõ; dữ liệu tổng hợp |
| Hình3.2 / quarterly_activity.png | Giữ, bổ sung chú thích quý biên | Nguồn ảnh không đánh dấu cờ biên; thân bài/chú thích nêu2000Q2 và2003Q1 |
| Hình3.3 / ERD Mermaid | Giữ nguồn chỉnh sửa được | Quan hệ/PK/FK đối chiếu SQL; chưa render PNG mới |
| Hình4.1 / all_history_charts.jpg | Giữ làm ảnh Tổng quan | No filter, instance8089 lịch sử; một số tiêu đề đầu viewport bị cắt. Bảng4.1 xác định KPI |
| Hình4.2 / three_genres_qoq.jpg | Giữ để minh họa QoQ/filter | Animation/Horror/Western,2001Q1–2002Q2; chip quý thu gọn, cột phải bảng bị cắt; giá trị chính xác lấy artifact/bảng4.3 |
| Ba ảnh Sở thích cũ | Không dùng làm hình chính | Chữ mờ; dùng bảng4.4 và SQL/API reconciliation đã đối soát |

Ngày24/10 thử mở dashboard hiện hữu `http://127.0.0.1:8089/superset/dashboard/3/` bằng trình duyệt chỉ đọc: `net::ERR_CONNECTION_REFUSED`. Kiểm tra HTTP `/health` từ máy cũng không truy cập được. Không suy đoán nguyên nhân hoặc gán trạng thái container chỉ từ lỗi này. Không khởi động/recreate service, đổi quyền/config/filter lưu, dữ liệu hoặc chạy ETL. **Không có ảnh mới được chụp thành công** trong lượt biên tập.

Nếu có lượt chụp sau được giao, lưu ảnh mới vào thư mục riêng kèm instance, thời điểm, model_version, cluster/age/gender và scope; xem độ rõ, count, nhãn và thông tin riêng tư trước dùng. Không ghi đè ảnh cũ.

## 4. Checklist biên tập

- [x] Tách hai nhánh Q1/G3 và Q2/CLI.
- [x] Thân chương bỏ nhật ký review hình và banner trạng thái công việc.
- [x] Rà khoảng trắng, thuật ngữ, bảng/hình theo từng chương; không đổi số liệu/mẫu số/miền môi trường.
- [x] Chuẩn bị [references.md](references.md), tách nguồn ngoài và artifact nội bộ; Superset docs rolling/Next không được gọi là tài liệu version6.1.0.
- [x] Giữ bảng Sở thích đã đối soát khi ảnh rõ chưa có.
- [x] Hai ảnh Sở thích được điều phối duyệt: Hình4.3–4.4, ghi filter/model/instance trong caption và selected_manifest.json; giữ ảnh lịch sử.
- [ ] Xem lại kích thước/độ rõ hình khi ghép bản Word/PDF; hiện chưa tạo DOCX/slide.
- [ ] Điều phối review bằng chứng tích hợp P2 và nghiệm thu12B/G4. P2 báo G2CONFIRMED trên Windows3.12.6/PG17.4; không có xác minh Linux.
- [ ] Nhận phần chương2/5/6 của P2 đã được duyệt; chưa ghép trong PR này.
- [ ] Đối chiếu rubric/mẫu chính thức khi có; không tự đặt số trang/thể thức bắt buộc.

## 5. Kết quả kiểm công bố

Kiểm file, liên kết, bảng số liệu so với bản chấp nhận, số hiệu hình/bảng, JSON, hash nguồn/receipt và phạm vi Git được ghi trong `publication_audit.json`. Không chạy lại evaluator Test, ETL/G3/dump/restore. Không kiểm quyền runtime hoặc sức khỏe hệ thống rộng hơn lần thử HTTP chỉ đọc trên.

## 6. Quan sát công bố

Đã mở [PR27](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/27), OPEN/merged=false tại lúc kiểm. Commit nội dung `393322017890af82808851b1e2b8296a35fce7eb`, base `dad848eedcd11230559acfc01ee103be718289a2`. Commit hồ sơ tiếp theo chỉ ghi kết quả công bố, không thay chương, ảnh hoặc bằng chứng runtime. `publication_audit.json` là snapshot kiểm trước công bố; ledger mới trong `publication_remote_observation.json` ghi hash hồ sơ cập nhật, không sửa audit cũ. Chưa tự merge hoặc chốtG4.
