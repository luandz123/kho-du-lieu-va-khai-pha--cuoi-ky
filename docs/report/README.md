# Báo cáo tổng hợp MovieLens 1M

Trạng thái: **Nội dung đã được điều phối duyệt ngày 25/10/2026; công bố chờ review PR**. G4 đã được điều phối nghiệm thu ngày 24/10/2026 trong phạm vi I01–I15 và giới hạn công bố; G5 chưa hoàn thành. Đây là lựa chọn trình bày học thuật của nhóm khi chưa có mẫu/rubric chính thức: A4, Times New Roman 12 pt, giãn dòng 1,15; tiêu đề, caption và lề nhất quán. Không đặt số trang thành yêu cầu chính thức.

## Đầu vào và sản phẩm

- P1: `../P1/report/chapter_01.md`, `chapter_03.md`, `chapter_04.md`, phụ lục và tài liệu tham khảo cùng thư mục; kế thừa phần đã duyệt tại HEAD d018921be66b12dc275933e1de9c2e755b74241a, bổ sung hình/checklist đã merge PR27 tại 03d9bc9932f7919c5eb5d04075f0235a1e0448fc. Dùng bản P1 đã cập nhật G4 cục bộ; không tạo lại hoặc ghi đè nguồn chương.
- P2: `../P2/report/chapter_02.md`, `chapter_05.md`, `chapter_06.md` và references; đúng HEAD được duyệt f090eff8b5a58242f8391469772cb3bd329f43f4, PR31 đã merge tại a2021a9f591c56222f5ae16e169f278bf3cec5a7. Agent không merge PR31.
- Candidate thực chạy giữ nguyên 4546d5bbd8f9130a420518b77dc3ad894bc7f42b. Commit nguồn chương, commit tài liệu và candidate thực nghiệm là các mốc khác nhau.
- `bao_cao_tong_hop.md`: nguồn ghép để review nội dung; liên kết tương đối trỏ nguồn thật.
- `bao_cao_tong_hop.docx`: bản chỉnh sửa với heading, số trang và ba trường TOC tự động (mục lục, danh mục hình, danh mục bảng).
- `bao_cao_tong_hop.pdf`: bản xuất từ cùng DOCX sau khi cập nhật trường bằng Word.
- `editorial_manifest.json`: hash đầu vào, ánh xạ mã tham khảo, các thay đổi biên tập đáng kể. Không thay số liệu/công thức/receipt; PCA bị loại khỏi bản chính, không đưa hình PCA vào tài liệu.
- `layout_review.json`: kết quả kiểm trang của bản xuất cuối; chỉ ghi PASS sau khi thực sự xem ảnh trang.

## Tái tạo tài liệu

Dùng Python có python-docx và Pillow (lần tạo này dùng runtime bundled của Codex, không sửa dependency môi trường demo). Script chạy offline, không kết nối PostgreSQL hoặc Superset.

```powershell
# Tại root repository; chọn đúng Python môi trường tài liệu
python docs/report/build_report.py
powershell -NoProfile -File docs/report/render_report.ps1
```

Script PowerShell cần Microsoft Word trên Windows, tạo một COM Application riêng và chỉ mở tệp báo cáo được sinh. Cập nhật fields/TOC, repaginate, cập nhật số trang rồi xuất PDF; không gắn hoặc đóng phiên Word của người dùng. Tái tạo ghi đè đúng các sản phẩm sinh tự động trong `docs/report/`; không dùng thao tác này trên bản Word đã biên tập tay nếu chưa bảo toàn chỉnh sửa.

Renderer `render_docx.py` của skill đã được thử nhưng không có LibreOffice trên PATH. Máy này không có LibreOffice bundled; không cài công cụ toàn hệ thống. Phương án đã dùng: Word native COM để cập nhật/hiển thị DOCX và xuất PDF, sau đó Poppler bundled để render từng trang PNG vào `tmp/s13/render/` (ignored). Không coi việc xuất PDF thành công là kết quả kiểm bố cục.

```powershell
# Có thể dùng Poppler đã có để render ở độ phân giải kiểm tra
pdftoppm -r 110 -png docs/report/bao_cao_tong_hop.pdf tmp/s13/render/page
```

Sau mỗi lần đổi nội dung hoặc bố cục, phải render lại và kiểm tất cả trang, đặc biệt bảng rộng, công thức, ERD, ảnh dashboard và số trang trong mục lục. Trong Word có thể chọn References → Update Table → Update entire table; không chuyển mục lục sang văn bản tĩnh.

## Kiểm biên tập và thông tin còn thiếu

Nguồn chương riêng và bằng chứng lịch sử được giữ nguyên. Gộp nguồn Sarwar, PostgreSQL Transactions và silhouette trùng giữa hai danh mục; ánh xạ P2-R về R chung trong manifest. Chương 2 giải thích phương pháp và fixture; chương 5 trình bày cấu hình/kết quả. Nhật ký PR/review không nằm trong thân sáu chương; mốc nguồn và runtime dài chuyển phụ lục/hồ sơ biên tập. Bảng 4.4 giữ số chính xác bên cạnh ảnh Sở thích; scope heatmap dẫn SQL/API, không suy riêng từ ảnh.

Theo trả lời của người dùng ngày 25/10/2026 “Cứ để trống”, bìa giữ nhãn và các dòng trống cho: tên trường, khoa/bộ môn, giảng viên, họ tên/MSSV hai thành viên, lớp/nhóm; không tự điền. Chưa xác nhận mẫu/rubric chính thức. Không tự lấy tên tài khoản Git làm họ tên sinh viên. Thời hạn bảo vệ được giữ 27/10/2026.

Giới hạn thực nghiệm không thay đổi: chỉ kiểm Windows P1/P2 với patch Python/PostgreSQL đã công bố; không kiểm Linux, Superset trên máy P2 hoặc phục hồi toàn stack trên máy mới. ZIP import cần bước layout REST; metadata restore và DW restore là hai cơ chế riêng; PUBLIC TEMP và ACL database clone giữ như hồ sơ.

Được giao commit/push/PR bản tổng ngày 25/10/2026; chưa nộp hoặc chốt G5. Slide được chuẩn bị nháp sau công bố. Việc tạo báo cáo không chạy ETL/G3/evaluator/dump/restore, không sửa metric, receipt, dữ liệu hoặc hệ thống demo.

## Chỉnh trước nộp ngày 25/10/2026

Bảng 5.5 dùng t₁/t₂; số giây Unix và UTC của hai ngưỡng giữ trong giải thích dưới bảng. Bảng 5.7 dùng sáu cột; ba số Recall chưa làm tròn chuyển nguyên giá trị sang phụ lục G, tránh ngắt chữ số và không đổi tiêu chí chọn k. Nguồn chương P2, metric và receipt không sửa. Bản 24/10 được bảo toàn tại review_history/ (metadata) và tmp/pre_submit_20261025/report_before/ (bản tài liệu cục bộ); đây là lịch sử, không ghi đè để gán thành kết quả mới.
