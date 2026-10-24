# Ghi chú biên tập báo cáo P2 — 24/10/2026

Điều phối đã chấp nhận nội dung chính chương 2/5/6 và giao chỉnh biên tập, commit/push nhánh `codex/p2-s13-report`, mở PR vào main; không tự merge. Nguồn là thông điệp người dùng chuyển trong phiên này. Nội dung báo cáo được tách khỏi nhật ký review, trạng thái PR/bản thảo và việc còn chờ ghép.

## PCA tạm loại khỏi bản chính

Tạm bỏ Hình 5.2 và mọi tỷ lệ phương sai PCA khỏi các chương chính. Ảnh gốc [cluster_pca_2d.png](../../../results/mining/cluster_pca_2d.png) giữ nguyên: nhãn PC1 35,5% và PC2 24,9%, trong khi [clustering_interpretation.md](../clustering_interpretation.md) ghi 22,1% và 14,5%. Chưa xác minh được nguyên nhân khác biệt bằng bằng chứng công bố hiện có; không chọn một bộ tỷ lệ làm kết quả chính. Không sửa ảnh, artifact, metric hoặc chạy lại pipeline. Chương 2 vẫn giữ giải thích PCA chỉ minh họa phương pháp, không dùng để phân cụm.

## Biên tập nội dung và nguồn

- Sửa nhãn cohort ở bảng 5.6 thành “Có dưới 5 rating lịch sử”; số 849/332 giữ nguyên.
- Bỏ nhận định profile dễ diễn giải hơn cách chỉ đếm hoạt động vì chưa có thực nghiệm đối chứng hỗ trợ. Giữ mô tả bốn profile, Silhouette và ARI đã công bố.
- Giữ nguyên công thức, các bảng số liệu thực nghiệm, receipt và nguồn dẫn. Bảng 6.2 chỉ còn phạm vi G2/G4, hai máy và giới hạn G5; các hàng quản lý PR/bản thảo chuyển vào hồ sơ này.
- Heatmap nhãn dài sát số, hình nhân khẩu học rút gọn tên: tiếp tục dùng bảng 5.3/5.4 đọc chính và dẫn link ảnh nguồn. Không sửa artifact.
- Tài liệu cũ nhắc kmeans_experiments.csv nhưng Git không có file; bảng 5.1 dùng đủ 14 dòng experiments_summary JSON. ARI chính chỉ dùng hai cặp seed trong summary.

## Trạng thái và việc còn chờ ghép

G4 đã được điều phối nghiệm thu ngày 24/10/2026 trong phạm vi đã kiểm. PR30 đã merge tại `67fd9eb6b98211485b713c99e829291bc3b50f57`; sự kiện Git và lời nghiệm thu là hai căn cứ riêng. Candidate thực kiểm vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`.

G5 và toàn bộ gói nộp chưa hoàn thành. Khi ghép, P1 cần cập nhật các nhãn trạng thái lịch sử trong phần mình, thống nhất số bảng/hình/mã tham khảo, kiểm cỡ chữ Hình 5.1 và áp mẫu/rubric chính thức khi được cung cấp. P2 không sửa phần P1 hoặc tạo DOCX tổng trong PR này. Báo cáo hiện có 13 bảng và 1 hình nhúng (Hình 5.1); Hình 5.2 được tạm bỏ, không còn tham chiếu trong các chương chính.

Nội dung chính đã được chấp nhận; lượt chỉnh biên tập được giao công bố PR để điều phối review diff cuối. Không coi việc mở PR là nghiệm thu G5 hoặc cho phép tự merge. Hồ sơ S13/STATE_P2 ghi trạng thái công bố cụ thể; audit ghi kiểm tra tĩnh, không phải bằng chứng thực chạy mới.
