# Chương 6. Kết luận, giới hạn và hướng phát triển

Kết luận dựa trên [chương 4 của P1](../../P1/report/chapter_04.md), [chương 5](chapter_05.md) và [ma trận nghiệm thu 12B](../../P1/integration_acceptance.md), không là một lượt thực nghiệm mới. Các kết quả rating mô tả hoạt động đánh giá lịch sử, không phải lượt xem, thời lượng xem hoặc doanh thu.

## 6.1. Trả lời các câu hỏi nghiên cứu

**Bảng 6.1. Câu trả lời Q1–Q3, bằng chứng và giới hạn.** Đơn vị và mẫu số nằm ở từng dòng; không cộng các đại lượng khác grain.

| Câu hỏi | Kết quả trong phạm vi đã kiểm | Bằng chứng | Giới hạn diễn giải |
|---|---|---|---|
| Q1 — Nhóm sở thích và cơ cấu tuổi/giới | 6.038 vector×18 genre, 4 cụm raw: đa dạng (2.478), Drama/tình cảm (1.393), Comedy (760), Action/Sci-Fi/Thriller (1.407); 2 người insufficient | Chương 5, bảng 5.1–5.4; E12–E13 | Quy mô mẫu số 6.038 assigned; genre là trung bình tỷ lệ gốc. Nhân khẩu học chỉ mô tả sau phân cụm, không nhân quả hoặc đại diện dân số |
| Q2 — Gợi ý Top-5 | CF k40 trong Test đã chốt có macro P@5=0.231023, R@5=0.03530289; baseline 0.201733 và 0.02712408, fallback CF 2/1.154 người | Chương 5, bảng 5.7–5.9; E14–E16, receipt chính thức | Cùng cohort 1.154; Precision mẫu số 5, Recall mẫu số relevant từng người. Recall validation CF vẫn thấp hơn baseline; chưa kiểm định thống kê hoặc online |
| Q3 — Biến động đánh giá theo quý/genre | Animation 2000Q4 từ 13.102 lên 20.068 lượt gắn genre, QoQ +53,17%; 2001Q1 còn 1.715, QoQ −91,45% dù hạng 1 trong tập đủ điều kiện | Chương 4, mục 4.4–4.5; E09–E11/E17, olap_findings.md | QoQ mẫu số quý trước; prev≥100, quý biên loại khỏi hạng. Hạng cao có thể là giảm; rating không là nhu cầu thị trường |

Nguồn: [chỉ mục E](../../P1/report_evidence_index.md), [kết quả OLAP](../../P1/olap_findings.md), [receipt Test](../../../results/mining/cf_test_evaluation_receipt.json). Số Q3 được rút gọn hai chữ số thập phân từ nguồn đã công bố; số Test chép nguyên receipt. Ba câu hỏi được trả lời theo hai hướng: Q1/Q3 mô tả snapshot, Q2 đánh giá xếp hạng với tương lai tách theo timestamp.

Q1 tạo được bốn profile thể loại được mô tả ở bảng 5.3. K=4 là quyết định đa tiêu chí; Silhouette mẫu 0,1860 không phải cao nhất. Độ ổn định ARI qua các seed đã kiểm bổ sung bằng chứng về tính nhất quán, không biến nhãn cụm thành chân lý về sở thích.

Q2 có đối chứng Popularity và quy tắc đánh giá tách bạch. K40 được chọn theo Recall validation chưa làm tròn trong lưới CF; Test được khóa và chỉ tham chiếu receipt. Kết quả Test CF cao hơn baseline ở cả hai metric là một quan sát có điều kiện. Không bỏ kết quả Recall validation bất lợi để đưa ra lời khẳng định vượt trội tổng quát. Phim mới ngoài catalog huấn luyện vẫn ở mẫu số Recall, giúp tránh làm metric đẹp hơn bằng cách xóa các relevant mà mô hình chưa thể gợi ý.

Q3 được giải bằng count, share và QoQ có mẫu số rõ ràng. Việc zero-fill trước LAG, xử lý mẫu số 0, quý biên và điều kiện quý trước ≥100 giúp bảng xếp hạng có nghĩa. Số đánh giá toàn hệ thống Q3/2000 là 324.864 và Q4/2000 là 446.574 theo chương 4; không cộng các genre để ra số này vì phim đa genre có thể đóng góp nhiều lượt gắn.

## 6.2. Đóng góp và phạm vi đã nghiệm thu

Đóng góp thứ nhất là luồng dữ liệu thống nhất từ nguồn đến bốn view contract, có đối soát count/hash và grain rating không bị nhân qua bridge. Các thành phần BI và khai phá dùng cùng dữ liệu logic nhưng giữ đúng mục đích từng phép đo. Full refresh, transaction, trạng thái model và đối soát gói giúp tránh dùng kết quả cụm không còn phù hợp snapshot DW.

Đóng góp thứ hai là hai quy trình khai phá có truy vết: Q1 xuất profile/nhãn cụm có version; Q2 có baseline, temporal split, cohort/candidate chung và receipt Test đóng băng. CLI tách evaluation khỏi demo toàn lịch sử. Đóng góp thứ ba là bằng chứng tích hợp độc lập trên hai máy Windows, với phạm vi khác nhau được ghi rõ thay vì quy toàn bộ phép kiểm về một môi trường.

**Bảng 6.2. Phạm vi tích hợp được nghiệm thu đến ngày 24/10/2026.** Đơn vị: mốc/quy trình; không phải bảng tỷ lệ pass trên mọi cấu hình. Mẫu/phạm vi kiểm ghi trong từng dòng.

| Mốc/phạm vi | Trạng thái hiện hành | Căn cứ và giới hạn |
|---|---|---|
| G2 / 12-P2 | Đã được điều phối nghiệm thu | P2 DW-only, bốn view tương đương raw/CSV/DW, Q1/G3 và ba ca CLI; candidate cố định |
| 12B / G4 | **ĐẠT trong phạm vi đã kiểm** | Nghiệm thu ngày 24/10/2026 theo phạm vi ma trận I01–I15; không suy mọi môi trường |
| P1 / Windows | Có bằng chứng tích hợp, BI và phục hồi theo ma trận I01–I15 | Python 3.12.14, PostgreSQL 17.11; Superset 6.1.0 ở môi trường/container riêng, không gọi là kiểm Linux độc lập |
| P2 / Windows 11 độc lập | Có bằng chứng tái lập DW/feature/G3/CLI | Python 3.12.6, PostgreSQL 17.4; không kiểm Superset/restore hoặc nạp analytics G3 trên P2 |
| G5 / gói nộp cuối | Chưa hoàn thành | Ngoài phạm vi nghiệm thu tích hợp G4 |

Nguồn: [ma trận I01–I16](../../P1/integration_acceptance.md), [môi trường P2](../../../results/mining/integration_p2/environment.json), [S13](../../agent/steps/P2/S13.md), [REVIEWS_P2](../../agent/REVIEWS_P2.md).

Candidate thực kiểm giữ nguyên `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. Commit merge hồ sơ và HEAD viết báo cáo không thay thế candidate hoặc các code hash của run lịch sử. Hai CSV G3 tái lập từ DW khớp fingerprint; không tuyên bố toàn bộ môi trường/manifest giống từng byte. pip check đạt chỉ nói không phát hiện xung đột dependency được khai báo.

## 6.3. Giới hạn dữ liệu và phương pháp

MovieLens là mẫu người tự tham gia với dữ liệu lịch sử; rating quan sát không đồng nghĩa bộ phim đã được xem đầy đủ và không có thời lượng xem. Thiếu rating cũng không chứng minh không thích. Khoảng UTC quan sát từ 25/04/2000 đến 28/02/2003 không đại diện nhu cầu hiện tại. Dữ liệu tuổi/giới là thuộc tính nguồn tĩnh, không theo dõi quá trình một người lớn tuổi lên và thay đổi sở thích. Do đó không suy quan hệ nhân quả hoặc khuyến nghị kinh doanh hiện tại từ cơ cấu cụm.

Feature Q1 đếm liên kết genre tích cực, nên phim nhiều genre đóng góp nhiều lượt liên kết. Chuẩn hóa giảm ảnh hưởng số lượng hoạt động nhưng vẫn bỏ qua thứ tự thời gian, độ tin cậy theo số đánh giá và mức khác biệt giữa 4/5 sao. Chỉ thử 14 cấu hình K-Means trong hai không gian; Silhouette trên mẫu cố định 2.000 không có khoảng tin cậy. Ổn định seed trên snapshot chưa chứng minh ổn định khi dữ liệu thay đổi; PCA không thay thế chỉ số toàn không gian.

Q2 dùng cosine trên ma trận thưa với ô chưa quan sát bằng 0, không có nội dung để xử lý item hoàn toàn mới. Cohort đòi ≥5 rating lịch sử và có relevant kỳ đánh giá, nên loại một phần đáng kể người ít hoạt động. Kết quả không phản ánh chất lượng cho toàn bộ 6.040 người hoặc cold start chưa có lịch sử. Top-N=5 thu hồi hữu hạn; Recall không là catalog coverage và chưa đo độ đa dạng, tính mới, công bằng hay mức hài lòng. Chưa có kiểm định ý nghĩa thống kê hoặc thực nghiệm online.

## 6.4. Giới hạn hạ tầng và khả năng tái lập

Tích hợp đã kiểm trên hai máy Windows với patch Python/PostgreSQL khác nhau. Không tuyên bố đã kiểm Linux, mọi dependency/version hoặc kết nối BI từ P2 sang P1. P2 tái dựng từ nguồn thay vì phục hồi toàn bộ hạ tầng P1. BI và restore thuộc P1 theo chương 4, gồm DW clone, metadata Superset và ZIP import bổ sung REST layout; đó là ba cơ chế khác nhau, không phải một backup toàn stack đã phục hồi trên máy mới. Quyền database-level của clone khác nguồn và PUBLIC TEMP còn là giới hạn đã công bố.

Hiệu năng hiện có là quan sát trong các lượt thực nghiệm cụ thể, chưa benchmark tải đồng thời toàn diện. Receipt/hash giúp truy vết và phát hiện thay đổi, không phải chữ ký số hoặc chứng minh tuyệt đối chưa từng có một lượt chạy khác. Hồ sơ lịch sử giữ nguyên; viết báo cáo không tạo thêm bằng chứng thực chạy.

## 6.5. Hướng phát triển

Các hướng sau là **đề xuất, chưa triển khai**: đánh giá thêm các cửa sổ thời gian/snapshot với tiêu chí định trước; báo cáo khoảng tin cậy trên kết quả đánh giá được phép trong một nghiên cứu mới; khảo sát độ ổn định profile theo dữ liệu; bổ sung thước đo đa dạng/catalog coverage và phương pháp hybrid cho item mới; kiểm phục hồi trên máy khác và tải đồng thời với cấu hình được khóa. Không thực hiện các đề xuất này bằng cách chạy lại hoặc tune lượt Test đã chốt của đồ án.

G4 ĐẠT trong phạm vi tích hợp đã kiểm; G5 và toàn bộ gói nộp chưa hoàn thành.
