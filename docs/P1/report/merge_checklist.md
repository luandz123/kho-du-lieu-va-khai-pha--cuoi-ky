# Checklist ghép báo cáo chung — chuẩn bị cục bộ

Điều phối đã duyệt checklist và hai ảnh Sở thích bổ sung ngày24/10/2026. Checklist được công bố cùng phần hình bổ sung để nhóm sử dụng; các ô ghép báo cáo bên dưới vẫn là việc chưa thực hiện, không tự đánh dấu hoàn thành. Không thay đổi kết luận G4 hoặc ghép DOCX tổng.

Ngày 24/10/2026. **Điều phối đã duyệt checklist**. Chưa ghép báo cáo hoặc tạo DOCX tổng/slide. Công bố checklist và hình bổ sung theo lệnh riêng, chưa tự merge. Điều phối duyệt nội dung PR27 tại HEAD `d018921be66b12dc275933e1de9c2e755b74241a`; không tự merge hoặc thay HEAD này. Nếu có commit bổ sung sau review phải nêu riêng diff và xin review đúng phạm vi.

## 1. Gate và kiểm kê phần nhận

| Chương | Người viết | Đầu vào để ghép | Trạng thái hiện tại |
|---|---|---|---|
| 1 — Bài toán/phạm vi | P1 | [chapter_01.md](chapter_01.md), bản PR27 đã duyệt | Nội dung PR được điều phối duyệt, chưa tự merge |
| 2 — Cơ sở lý thuyết/phương pháp | P2 | File/commit/PR và lời review do P2/điều phối bàn giao | Chưa xác nhận gói chương đã được duyệt trong lượt này |
| 3 — Dữ liệu và DW | P1 | [chapter_03.md](chapter_03.md), bản PR27 đã duyệt | Như chương 1 |
| 4 — ETL/OLAP/dashboard | P1 | [chapter_04.md](chapter_04.md), bản PR27 đã duyệt | Như chương 1; ảnh mới phải review riêng trước khi thay hình |
| 5 — K-Means/CF/baseline/đánh giá | P2 | File/commit/PR, bảng và nguồn hình đã duyệt | Đang chờ bàn giao được xác nhận |
| 6 — Kết luận/giới hạn | P2 | File/commit/PR được duyệt, thống nhất trạng thái G4 | Đang chờ; không suy G4 đạt từ PR báo cáo |

- [ ] Nhận đủ sáu chương, kiểm đúng bản được review; ghi commit/file/hash và nguồn duyệt cho từng phần.
- [ ] Nhận các phụ lục và nguồn hình/bảng của P2; không tự sửa file P2 để ép khớp.
- [ ] Kiểm hai phần được duyệt trước ghép bản tổng; P1 quản lý bản tổng duy nhất.
- [ ] Xác minh trạng thái merge các PR thực tế; nội dung được duyệt khác PR MERGED.
- [ ] Điều phối nghiệm thu12B/G4 trước khóa kết luận tích hợp. Việc chuẩn bị checklist không mở G4.

## 2. Thuật ngữ, ký hiệu và phạm vi

- [ ] Rating = đánh giá; timestamp = thời điểm đánh giá UTC. Không đổi thành lượt xem, thời lượng, doanh thu hoặc nhu cầu hiện tại.
- [ ] Phân biệt phim danh mục 3.883 với phim có rating 3.706; user nguồn 6.040 với assigned 6.038 và insufficient 2.
- [ ] Q1: K-Means trên tỷ lệ genre tích cực; tuổi/giới dùng diễn giải sau phân cụm, không suy nhân quả hoặc thay đổi sở thích cùng người theo tuổi.
- [ ] Q2: item-based CF và Popularity Baseline; score là điểm xếp hạng, không phải sao dự đoán. Top 5 loại phim đã biết trong lịch sử được phép dùng.
- [ ] Phân biệt K=4 số cụm, k=40 số láng giềng, N=5 độ dài gợi ý; dùng nhất quán ở công thức/bảng/chú thích.
- [ ] Dùng đúng model_version của Q1/Q2; không đưa cụm toàn lịch sử Q1 vào đánh giá Q2.
- [ ] Giữ nhãn tuổi và trường/cột đúng contract2, ID nguồn khác surrogate; năm NULL đúng quy tắc trích cuối title.
- [ ] Mean dùng SUM/COUNT; rating duy nhất khác lượt gán genre; n_users lặp trên 18 genre không được cộng thành tổng user.
- [ ] Sharegenre dùng tổng lượt gán tất cả genre cùng quý; baseline Sở thích cố định6.038, không tự thu hẹp theo filter.

## 3. Chương 2 khác chương 5; tránh lặp phương pháp

- [ ] Chương 2 trình bày khái niệm/công thức/thuật toán và tài liệu tham khảo, ví dụ tính tay bằng fixture; không chép toàn bảng kết quả thực nghiệm.
- [ ] Chương 5 dẫn lại mục phương pháp chương 2, chỉ nêu cấu hình thực dùng, cách chọn, kết quả, so sánh và giải thích giới hạn.
- [ ] Chương 3 tập trung nguồn/EDA/contract/thiết kế; không lặp diễn giải mọi cụm ở chương 5.
- [ ] Chương 4 mô tả giao diện G3/BI và kiểm pipeline; lý do chọnK, profile và kết quảCF đặt ở chương 5.
- [ ] Nếu phát hiện khác thuật toán/metric giữa hai chương, lập bảng điểm lệch để chủ phần chốt; không sửa âm thầm receipt/cấu hình.

## 4. Validation, Test và demo; mức bằng chứng

- [ ] Validation chọnk = 20/40/80 theo quy tắc đã chốt; không lấy Test để điều chỉnh mô hình hoặc gọi validation là kết quả cuối.
- [ ] Metrics Test chép đúng [receipt chính thức](../../../results/mining/cf_test_evaluation_receipt.json), cùng cohort 1.154/candidate/cutoff; không chạy lại evaluator Test để viết hoặc ghép.
- [ ] Giữ độ chính xác trong receipt; nếu trình phần trăm ghi đúng đơn vị, không tự tính delta từ số đã làm tròn rồi thay receipt.
- [ ] Báo fallback và phim mới trong mẫu số Recall; không đặt điều kiện CF bắt buộc thắng baseline.
- [ ] Demo full-history khác evaluation theo cutoff; outputCLI không tự là phép đánh giá lại Test. Không đưa userID/history/gợi ý gắn người thật vào bản tổng.
- [ ] Ghi P1 đã kiểm trên môi trường nào, P2 đã báo/đã có artifact nào và phần nào được điều phối nghiệm thu. Không nâng thông tin P2 báo thành P1 kiểm độc lập.
- [ ] Hiện P2 báo G2 CONFIRMED trên Windows/Python 3.12.6/PostgreSQL 17.4; bằng chứng công bố chờ review theo ghi nhận hiện có. Không ghi đã kiểm Linux.
- [ ] Phân biệt thiết kế/kiểm tĩnh với thực thi; fixture với dữ liệu thật; API/SQL với ảnhUI; restore cùng máy với phục hồi máy mới.

## 5. Hình, bảng và nguồn dẫn

- [ ] Đánh số theo chương; đối chiếu mọi chỗ gọi hình/bảng với caption. Khi ghép không lặp số hoặc giữ tên tạm của phần viết khác.
- [ ] Mỗi bảng có phạm vi, đơn vị, mẫu số, filter và nguồn; mỗi hình có nguồn/instance/model/filter khi cần.
- [ ] Chọn ảnh rõ đã xem thật. Giữ ảnh lịch sử; ảnh chụp bổ sung24/10 trong `captures/20261024_preferences/` là hồ sơ mới, chưa thay hình PR27.
- [ ] Với ảnh Sở thích: toàn bộ assigned 6.038/baseline 6.038/insufficient 2; ca cụm 1/F/25–34 assigned 170, baseline 6.038/insufficient 2. Heatmap chỉ chịu cluster; không diễn giải profile đã tính lại theo nhân khẩu học.
- [ ] ERD giữ PK/FK/bridge và grain khi render; kiểm lại độ rõ của PNG/Word/PDF sau khi được giao ghép.
- [ ] QoQ giữ dấu âm/NULL, zero-fill trước LAG, ngưỡngprev ≥ 100 và quý biên; hạng1 âm ghi giảm ít nhất.
- [ ] Phân biệt count tổng O4 cấp quarter với year/month; không cộng các cấp hoặc genre thành tổng hệ thống.
- [ ] Kiểm hình không lộ credential, URI có mật khẩu, user-level output, account riêng tư hoặc rawlog. Chỉ dùng thống kê tổng hợp.

## 6. Tài liệu tham khảo và phụ lục

- [ ] Hợp nhất [references.md](references.md) với phần P2 sau duyệt; gộp mục trùng, thống nhất mã/cách dẫn, không tự áp mẫu chưa được yêu cầu.
- [ ] Nguồn dữ liệu/nghiên cứu gốc/tài liệu chính thức tách artifact nội bộ. Website cập nhật liên tục không giả thành snapshot đúng version đang chạy.
- [ ] Mọi kết quả đo dẫn [E01–E20](../report_evidence_index.md), run/artifact/receipt, không dùng tài liệu công cụ làm bằng chứng nhóm đã chạy.
- [ ] Chuyển run/hash/lệnh dài vào [phụ lục](appendix_sources.md), giữ code thực chạy chưa commit khác commit công bố/candidate.
- [ ] Không đưa dump, modelbinary, secret/configprivate hoặc dữ liệu cá nhân vào phụ lục/gói nộp.

## 7. Vị trí phải cập nhật sau G4

| Vị trí | Việc cập nhật sau nghiệm thu thật | Điều chưa được tự ghi |
|---|---|---|
| Chương1 mục1.5 | Candidate/phạm vi tái lập/nguồn nghiệm thu | Không tự đổi thành đã tích hợp hoàn tất |
| Chương 3 mục3.7 | Giới hạn adapter/DW/P2 và nguồn xác nhận | Không ghiLinux nếu không có bằng chứng |
| Chương 4 mục4.7–4.8 | Báo cáo12-P2, lỗi đã xử lý,12B/G4 và phạm vi môi trường | Không gán run/hash cũ cho commit nghiệm thu mới |
| Chương 5 do P2 viết | Cách dữ liệuDW được kiểm nhận và giới hạn thực nghiệm | Không thay metrics Test hoặc provenance đã chốt |
| Chương 6 do P2 viết | Ma trận Q1–Q3 và trạng thái hoàn thành cuối | Không suy hoàn thành từ riêng PR chương P1 |
| Phụ lục/README/checklist tích hợp | Commit ứng viên/commit nghiệm thu, receipt và lệnh thực | Không ghi thao tác chưa chạy thành đã chạy |
| Ảnh Sở thích/bảng scope | Chọn ảnh mới sau review, đánh số lại nếu thêm | Không sửa dashboard để che lệch hoặc ghi đè ảnh lịch sử |

## 8. Điều kiện trước ghép bản tổng

- [ ] Điều phối duyệt phần bổ sung/checklist/hình mới và giao ghép.
- [ ] Đủ hai phần được duyệt, danh mục nguồn/hình rõ và các ô G4 được cập nhật bằng bằng chứng thật.
- [ ] Khi được giao tạo DOCX/PDF: render và kiểm bố cục, bảng bị ngắt, font/công thức, liên kết, caption và số trang theo mẫu chính thức nếu có.
- [ ] Bản tổng được review riêng; không coi checklist hoàn tất là quyền tự nộp/merge/tag hoặc tạo slide.
