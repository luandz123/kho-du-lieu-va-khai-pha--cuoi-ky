@chapter CHƯƠNG 4. KHAI PHÁ DỮ LIỆU: PHÂN CỤM NGƯỜI DÙNG VÀ GỢI Ý PHIM

Chương này trình bày hai bài toán khai phá trên dữ liệu đọc từ kho: phân cụm người dùng theo sở thích thể loại bằng K-Means (câu hỏi Q1) và gợi ý Top-5 phim bằng lọc cộng tác dựa trên sản phẩm (câu hỏi Q2). Với mỗi bài toán, báo cáo trình bày cách xây dựng dữ liệu đầu vào, thiết kế thực nghiệm, kết quả và diễn giải.

## 4.1. Phân cụm người dùng theo sở thích thể loại (Q1)

### 4.1.1. Xây dựng vector đặc trưng

Mỗi người dùng được biểu diễn bằng một vector 18 chiều, mỗi chiều ứng với một thể loại (sắp theo thứ tự chữ cái từ Action tới Western). Chỉ các lượt đánh giá **tích cực** (từ 4 sao trở lên) được sử dụng. Gọi P(u) là tập phim người dùng u đánh giá tích cực, G(i) là tập thể loại của phim i. Số lượt gắn thể loại g và vector tỷ lệ của u được tính như sau:

@eq C_{u,g} = \sum_{i \in P(u)} \mathbf{1}[\, g \in G(i)\,], \qquad p_{u,g} = \dfrac{C_{u,g}}{\sum_{g'=1}^{18} C_{u,g'}}

Mỗi vector có các thành phần không âm và tổng bằng 1, thể hiện **cơ cấu thể loại trong những phim người dùng yêu thích**. Việc dùng tỷ lệ thay vì số lượng tuyệt đối giúp so sánh được người dùng đánh giá ít với người dùng đánh giá nhiều. Ví dụ: nếu một người chấm 5 sao cho phim A (Action, Comedy), 4 sao cho phim B (Comedy) và 2 sao cho phim C (Drama), thì có 3 lượt gắn thể loại tích cực: Action 1, Comedy 2; vector của người này có p(Action) = 1/3, p(Comedy) = 2/3, các thể loại khác bằng 0. Phim C không được tính vì chỉ đạt 2 sao.

Có 2 người dùng không có lượt đánh giá nào từ 4 sao trở lên; vector của họ không xác định (chia cho 0), nên họ được gắn trạng thái “không đủ dữ liệu” và không tham gia phân cụm. Ma trận đầu vào cuối cùng có kích thước **6.038 × 18**. Tuổi, giới tính và nghề nghiệp **không** được đưa vào vector đặc trưng; chúng chỉ được ghép lại sau khi phân cụm để mô tả từng cụm, nhờ đó các cụm phản ánh thuần túy sở thích thể loại.

### 4.1.2. Thực nghiệm lựa chọn số cụm

Nhóm thử nghiệm 14 cấu hình: số cụm K từ 2 tới 8, mỗi giá trị chạy trên hai không gian dữ liệu là tỷ lệ gốc (raw) và dữ liệu chuẩn hóa bằng StandardScaler. Mọi cấu hình dùng `random_state = 42`, `n_init = 10`. Inertia và kích thước cụm được tính trên toàn bộ 6.038 người dùng; hệ số Silhouette được tính trên một mẫu cố định 2.000 người để giảm thời gian tính toán (độ phức tạp của Silhouette tăng theo bình phương số điểm). Kết quả được trình bày trong Bảng 4.1 và Hình 4.1.

@table Bảng 4.1. Kết quả 14 cấu hình K-Means
@widths 1.4,3.6,3,2.8,2.6,2.6
| K | Tiền xử lý | Inertia | Silhouette | Cụm nhỏ nhất | Cụm lớn nhất |
| 2 | Tỷ lệ gốc | 217,77 | 0,2233 | 2.798 | 3.240 |
| 3 | Tỷ lệ gốc | 181,02 | 0,2211 | 1.250 | 2.534 |
| **4** | **Tỷ lệ gốc** | **162,99** | **0,1860** | **760** | **2.478** |
| 5 | Tỷ lệ gốc | 152,14 | 0,1674 | 524 | 1.604 |
| 6 | Tỷ lệ gốc | 141,74 | 0,1723 | 103 | 1.902 |
| 7 | Tỷ lệ gốc | 132,01 | 0,1729 | 101 | 1.340 |
| 8 | Tỷ lệ gốc | 125,50 | 0,1721 | 101 | 1.308 |
| 2 | StandardScaler | 95.141,11 | 0,1472 | 2.360 | 3.678 |
| 3 | StandardScaler | 86.041,23 | 0,1398 | 1.475 | 2.642 |
| 4 | StandardScaler | 80.502,67 | 0,1238 | 460 | 1.982 |
| 5 | StandardScaler | 76.187,45 | 0,1199 | 350 | 2.336 |
| 6 | StandardScaler | 72.188,23 | 0,1302 | 100 | 2.335 |
| 7 | StandardScaler | 69.077,42 | 0,1055 | 97 | 1.970 |
| 8 | StandardScaler | 65.742,18 | 0,1018 | 5 | 1.960 |

@fig figures/kmeans_chon_k.png | Hình 4.1. Inertia và hệ số Silhouette theo số cụm K | 15.5

Từ kết quả thực nghiệm, nhóm có các nhận xét sau:

- **Về tiền xử lý:** dữ liệu tỷ lệ gốc cho Silhouette cao hơn StandardScaler ở mọi giá trị K. StandardScaler chia mỗi chiều cho độ lệch chuẩn, làm tăng trọng số của các thể loại hiếm (như Film-Noir, Documentary), dẫn tới các cụm rất nhỏ (cụm chỉ 5 người ở K = 8). Mặt khác, vì các thành phần của vector đã cùng thang đo [0, 1] nên việc chuẩn hóa là không cần thiết. Lưu ý inertia của hai không gian không so sánh trực tiếp được vì khác thang đo.
- **Về số cụm:** Silhouette cao nhất ở K = 2 (0,2233) và K = 3 (0,2211). Tuy nhiên, với K = 2 thuật toán chỉ tách thô người dùng thiên về Drama và người dùng thiên về Action/Comedy; với K = 3, nhóm Comedy và nhóm Action vẫn chưa được tách bạch. Từ K = 4, đường inertia bắt đầu giảm chậm lại (điểm khuỷu tay), và bốn cụm có ý nghĩa rõ ràng. Từ K = 6 trở đi xuất hiện các cụm nhỏ khoảng 100 người, khó diễn giải.

Vì vậy, nhóm chọn **K = 4 trên dữ liệu tỷ lệ gốc**. Đây là quyết định cân bằng giữa nhiều tiêu chí (elbow, kích thước cụm, khả năng diễn giải), không phải chỉ dựa vào Silhouette. Giá trị Silhouette 0,186 ở mức thấp cho thấy các nhóm sở thích có ranh giới không tuyệt đối mà chuyển tiếp liên tục; đây là đặc điểm thường gặp của dữ liệu hành vi người dùng.

### 4.1.3. Đánh giá độ ổn định

Để kiểm tra kết quả có phụ thuộc vào yếu tố ngẫu nhiên hay không, nhóm huấn luyện lại cấu hình đã chọn với hai hạt giống khác (0 và 7) và so sánh với kết quả gốc (hạt giống 42) bằng chỉ số ARI. Kết quả ARI đạt **0,9949** (so với hạt giống 0) và **0,9763** (so với hạt giống 7), rất gần 1. Như vậy, cách chia cụm gần như không đổi khi thay đổi khởi tạo, chứng tỏ cấu trúc bốn cụm là ổn định.

### 4.1.4. Kết quả và diễn giải bốn cụm

Hồ sơ của mỗi cụm là trung bình vector tỷ lệ thể loại của các người dùng trong cụm. Bảng 4.2 trình bày quy mô và các thể loại nổi bật; Hình 4.2 trình bày bản đồ nhiệt đầy đủ 4 cụm × 18 thể loại.

@table Bảng 4.2. Quy mô và thể loại nổi bật của bốn cụm (mô hình K = 4)
@widths 1.4,4.6,2,2.2,5.8
| Cụm | Tên mô tả | Số người | Tỷ lệ (%) | Thể loại nổi bật (tỷ lệ trung bình, %) |
| 0 | Đánh giá đa dạng | 2.478 | 41,0 | Drama 17,7; Comedy 16,2; Action 10,8; Thriller 9,7 |
| 1 | Thiên về Drama và tình cảm | 1.393 | 23,1 | Drama 34,3; Comedy 14,9; Romance 8,4; Thriller 8,2 |
| 2 | Thiên về hài (Comedy) | 760 | 12,6 | Comedy 36,0; Drama 16,3; Romance 11,4; Action 5,3 |
| 3 | Thiên về hành động, viễn tưởng | 1.407 | 23,3 | Action 20,1; Sci-Fi 13,6; Thriller 11,6; Drama 10,4 |

@fig ../../results/mining/cluster_genre_heatmap.png | Hình 4.2. Bản đồ nhiệt tỷ lệ thể loại trung bình của bốn cụm | 15.5

Có thể diễn giải bốn cụm như sau:

- **Cụm 0 – Đánh giá đa dạng (41,0%):** nhóm lớn nhất, sở thích trải đều trên các thể loại đại chúng, không thiên lệch mạnh về thể loại nào.
- **Cụm 1 – Drama và tình cảm (23,1%):** hơn một phần ba lượt yêu thích thuộc thể loại Drama, cao gần gấp đôi cụm 0.
- **Cụm 2 – Hài (12,6%):** Comedy chiếm 36% lượt yêu thích, đồng thời tỷ lệ Action rất thấp (5,3%).
- **Cụm 3 – Hành động, viễn tưởng (23,3%):** tập trung vào các thể loại kịch tính Action, Sci-Fi và Thriller.

Hình 4.3 chiếu dữ liệu xuống không gian hai chiều bằng phân tích thành phần chính (PCA) để minh họa. Hai thành phần đầu giải thích khoảng 60% phương sai; các cụm 1, 2, 3 nằm ở ba hướng khác nhau, còn cụm 0 nằm ở trung tâm, phù hợp với đặc điểm “đa dạng”. Phép chiếu PCA chỉ dùng để minh họa, không tham gia vào quá trình phân cụm.

@fig ../../results/mining/cluster_pca_2d.png | Hình 4.3. Phân bố người dùng của bốn cụm trên mặt phẳng hai thành phần chính | 13

### 4.1.5. Đặc điểm nhân khẩu học của các cụm

Sau khi phân cụm, nhóm ghép thông tin giới tính và tuổi để mô tả từng cụm, so sánh với mốc chung là toàn bộ 6.038 người được phân cụm (Bảng 4.3 và Hình 4.4).

@table Bảng 4.3. Cơ cấu nhân khẩu học của các cụm so với mốc chung (đơn vị: %)
@widths 4,2,2,2.6,2.6,2.4
| Nhóm | Nam | Nữ | Tuổi 25–34 | Dưới 18 | Từ 56 |
| Toàn bộ (mốc so sánh) | 71,7 | 28,3 | 34,7 | 3,7 | 6,3 |
| Cụm 0 – Đa dạng | 73,7 | 26,3 | 36,6 | 3,4 | 4,4 |
| Cụm 1 – Drama, tình cảm | 61,2 | 38,8 | 31,2 | 1,4 | 12,0 |
| Cụm 2 – Hài | 55,1 | 44,9 | 34,1 | 7,5 | 5,3 |
| Cụm 3 – Hành động, viễn tưởng | 87,4 | 12,6 | 35,3 | 4,3 | 4,4 |

@fig ../../results/mining/cluster_demographics.png | Hình 4.4. Cơ cấu giới tính và nhóm tuổi của từng cụm so với mốc chung | 13

Kết quả cho thấy những khác biệt rõ rệt, trả lời phần thứ hai của câu hỏi Q1:

- **Cụm 3** thiên mạnh về nam giới: 87,4% so với mốc 71,7%.
- **Cụm 1** có tỷ lệ nữ (38,8%) và tỷ lệ người từ 56 tuổi trở lên (12,0%) cao hơn hẳn mốc chung (28,3% và 6,3%).
- **Cụm 2** có tỷ lệ nữ cao nhất (44,9%) và tỷ lệ người dưới 18 tuổi cao gấp đôi mốc chung (7,5% so với 3,7%).
- **Cụm 0** có cơ cấu gần với mốc chung nhất, phù hợp với tính chất “đa dạng”.

Đây là các khác biệt mang tính **mô tả** trên dữ liệu lịch sử. Nhóm chưa thực hiện kiểm định thống kê và không suy luận quan hệ nhân quả (ví dụ “là nữ thì thích phim tình cảm”), cũng không kết luận sở thích của một người thay đổi theo tuổi, vì dữ liệu chỉ ghi nhận một thời điểm cho mỗi người dùng.

Kết quả phân cụm (6.040 dòng gán cụm, 72 dòng hồ sơ cụm × thể loại) được nạp vào schema `analytics` trong một giao dịch, sau khi kiểm tra khớp với dữ liệu hiện tại của kho, và được hiển thị trên dashboard Sở thích đã trình bày ở mục 3.4.3.

## 4.2. Gợi ý Top-5 phim (Q2)

### 4.2.1. Thiết kế thực nghiệm

**Chia dữ liệu theo thời gian.** Để tránh rò rỉ dữ liệu tương lai, toàn bộ 1.000.209 lượt đánh giá được chia theo hai mốc thời gian t₁ và t₂ là phân vị 70% và 85% của timestamp (Hình 4.5): tập **train** gồm các lượt trước hoặc tại t₁ (22/11/2000), tập **validation** từ sau t₁ tới t₂ (10/12/2000), tập **test** sau t₂. Các lượt có cùng timestamp luôn nằm cùng một phía.

@fig figures/chia_thoi_gian.png | Hình 4.5. Chia dữ liệu theo thời gian thành train, validation và test | 15.5

Quy trình sử dụng ba tập dữ liệu như sau: ở pha validation, mô hình chỉ học từ tập train và được đánh giá trên tập validation để chọn tham số; sau khi đã chốt tham số, mô hình được huấn luyện lại trên train + validation và đánh giá **đúng một lần** trên tập test. Kết quả test không được dùng để điều chỉnh mô hình.

**Người dùng được đánh giá.** Một người dùng được đưa vào đánh giá nếu có ít nhất 5 lượt đánh giá trong lịch sử huấn luyện (để mô hình có đủ thông tin) và có ít nhất 1 phim đánh giá tích cực trong giai đoạn đánh giá (để có đáp án). Phim “liên quan” T(u) là các phim người dùng đánh giá từ 4 sao trở lên trong giai đoạn đánh giá. Tập ứng viên của mỗi người là toàn bộ phim trong danh mục huấn luyện trừ các phim người đó đã đánh giá; nhóm không lấy mẫu âm. Bảng 4.4 tóm tắt quy mô các tập.

@table Bảng 4.4. Quy mô người dùng và phim trong hai pha đánh giá
@widths 9,3.5,3.5
| Nội dung | Validation | Test |
| Số lượt đánh giá dùng để huấn luyện | 700.148 | 850.177 |
| Số phim trong danh mục huấn luyện | 3.633 | 3.669 |
| Người dùng có hoạt động trong giai đoạn đánh giá | 1.352 | 1.512 |
| Bị loại do có dưới 5 lượt trong lịch sử huấn luyện | 849 | 332 |
| Bị loại do không có phim tích cực trong giai đoạn đánh giá | 32 | 26 |
| **Số người dùng được đánh giá** | **471** | **1.154** |
| Phim mới (chưa có trong danh mục huấn luyện) được đánh giá tích cực | 3 | 16 |

Phim mới xuất hiện lần đầu trong giai đoạn đánh giá không thể được gợi ý bởi cả hai mô hình (vấn đề khởi đầu lạnh – cold start), nhưng vẫn được giữ trong mẫu số của Recall để không làm kết quả đẹp hơn thực tế.

### 4.2.2. Mô hình item-based CF và mô hình cơ sở

**Item-based CF.** Ma trận đánh giá R được lưu dạng ma trận thưa (sparse) với mỗi hàng là một phim, mỗi cột là một người dùng, ô có giá trị là số sao, ô trống là 0 (biểu diễn “chưa có tương tác”, không phải “0 sao”). Ở pha test, ma trận có kích thước 3.669 × 5.715 với 850.177 ô khác 0, tức mật độ chỉ khoảng 4%. Mỗi hàng được chuẩn hóa về độ dài 1, khi đó tích vô hướng giữa hai hàng chính là độ tương tự cosine. Phép nhân ma trận được thực hiện theo từng lô 500 phim để tiết kiệm bộ nhớ. Với mỗi phim, chỉ giữ lại k láng giềng có độ tương tự dương lớn nhất (bỏ chính nó).

Điểm của phim ứng viên được tính theo công thức ở mục 1.3.2: cộng độ tương tự của ứng viên với mỗi phim hạt giống (phim người dùng đánh giá từ 4 sao) mà ứng viên nằm trong tập láng giềng. Ví dụ: hai phim có vector đánh giá (4, 0) và (4, 3) có độ tương tự cosine bằng 16 / (4 × 5) = 0,8. Nếu một phim ứng viên là láng giềng của hai phim hạt giống với độ tương tự 0,8 và 0,6, điểm của nó là 1,4. Khi hai phim có cùng điểm, phim phổ biến hơn được ưu tiên, sau đó tới mã phim nhỏ hơn. Nếu người dùng không có phim hạt giống hoặc có ít hơn 5 ứng viên có điểm dương, danh sách được bổ sung bằng các phim phổ biến nhất mà người đó chưa xem (cơ chế dự phòng – fallback).

**Popularity Baseline.** Mô hình cơ sở gợi ý 5 phim có nhiều lượt đánh giá nhất trong dữ liệu huấn luyện mà người dùng chưa đánh giá. Hai mô hình được đánh giá trên **cùng tập người dùng và cùng tập ứng viên**, bảo đảm so sánh công bằng.

### 4.2.3. Lựa chọn số láng giềng k trên tập validation

Nhóm thử ba giá trị k ∈ {20, 40, 80}. Tiêu chí chọn được chốt trước khi chạy: chọn k có Recall@5 trên validation cao nhất; nếu bằng nhau thì chọn k nhỏ hơn. Kết quả được trình bày trong Bảng 4.5 và Hình 4.6.

@table Bảng 4.5. Kết quả trên tập validation (471 người dùng)
@widths 4.5,3.5,3.5,2.5,2
| Mô hình | Precision@5 | Recall@5 | Số gợi ý đúng | Fallback |
| Popularity Baseline | 0,1699 | 0,0313 | 400 | – |
| Item-based CF, k = 20 | 0,1771 | 0,0286 | 417 | 0 |
| **Item-based CF, k = 40** | **0,1800** | **0,0301** | **424** | **0** |
| Item-based CF, k = 80 | 0,1843 | 0,0287 | 434 | 0 |

@fig figures/cf_validation.png | Hình 4.6. Precision@5 và Recall@5 trên tập validation | 15.5

Theo tiêu chí đã chốt, **k = 40** được chọn vì có Recall@5 cao nhất trong ba cấu hình CF (0,0301). Cấu hình k = 80 có Precision và số gợi ý đúng cao hơn nhưng Recall thấp hơn; nhóm giữ nguyên tiêu chí ban đầu thay vì đổi tiêu chí sau khi thấy kết quả.

Một kết quả đáng chú ý là trên tập validation, **Recall@5 của CF (0,0301) còn thấp hơn Popularity Baseline (0,0313)**, dù Precision cao hơn. Điều này không mâu thuẫn với việc CF có tổng số gợi ý đúng nhiều hơn: Recall được tính trung bình theo từng người với mẫu số là số phim liên quan của chính người đó, nên một gợi ý đúng cho người có ít phim liên quan đóng góp vào Recall nhiều hơn một gợi ý đúng cho người có nhiều phim liên quan. Tổng số gợi ý đúng cao hơn vì thế không bảo đảm Recall trung bình cao hơn. Nhóm giữ nguyên kết quả bất lợi này trong báo cáo thay vì bỏ qua.

### 4.2.4. Kết quả trên tập test

Sau khi chốt k = 40, mô hình được huấn luyện lại trên train + validation và đánh giá một lần trên tập test với 1.154 người dùng. Kết quả được trình bày trong Bảng 4.6 và Hình 4.7.

@table Bảng 4.6. Kết quả trên tập test (1.154 người dùng)
@widths 4.6,2.8,2.8,2.6,3.2
| Mô hình | Precision@5 | Recall@5 | Số gợi ý đúng | Người dùng fallback |
| Popularity Baseline | 0,2017 | 0,0271 | 1.164 | 0 |
| **Item-based CF, k = 40** | **0,2310** | **0,0353** | **1.333** | **2 (0,17%)** |

@fig figures/cf_test.png | Hình 4.7. So sánh item-based CF và Popularity Baseline trên tập test | 14

Trên tập test, item-based CF vượt Popularity Baseline ở cả hai chỉ số: Precision@5 cao hơn 14,5% (0,2310 so với 0,2017), Recall@5 cao hơn 30,2% (0,0353 so với 0,0271), với 169 gợi ý đúng nhiều hơn. Chỉ 2 trên 1.154 người dùng cần đến cơ chế dự phòng. Có thể diễn giải Precision@5 = 0,231 như sau: trung bình cứ 5 phim được gợi ý thì có khoảng 1,15 phim người dùng thực sự đánh giá từ 4 sao trở lên trong giai đoạn sau đó.

Giá trị Recall@5 thấp (khoảng 3,5%) là điều dễ hiểu: danh sách gợi ý chỉ có 5 phim trong khi nhiều người dùng đánh giá tích cực hàng chục phim trong giai đoạn test, nên dù gợi ý đúng cả 5 phim thì Recall vẫn nhỏ. Hơn nữa, mô hình phải chọn 5 phim trong khoảng 3.400 ứng viên mỗi người.

Cần lưu ý rằng kết quả trên là một lần đánh giá trên một cách chia dữ liệu; nhóm chưa thực hiện kiểm định ý nghĩa thống kê hay đánh giá trực tuyến với người dùng thật. Ngoài ra, tập người dùng được đánh giá ở pha validation và test khác nhau, nên không so sánh trực tiếp hai bảng kết quả để kết luận mô hình “tiến bộ theo thời gian”.

### 4.2.5. Công cụ gợi ý dòng lệnh

Mô hình được đóng gói thành công cụ dòng lệnh `mining.recommend`, đọc dữ liệu trực tiếp từ kho (tham số `--source dw`) và hỗ trợ hai chế độ:

- **Chế độ đánh giá (evaluation):** dùng đúng mô hình và mốc thời gian của pha test, để minh họa gợi ý trong điều kiện đánh giá.
- **Chế độ demo:** huấn luyện trên toàn bộ lịch sử để đưa ra gợi ý “thực tế” cho người dùng.

Ví dụ lệnh: `python -m mining.recommend --source dw --user-id <mã người dùng> --mode demo --top-n 5`. Kết quả gồm 5 phim với tên, thể loại, điểm xếp hạng và loại điểm (CF hoặc fallback). Nhóm đã kiểm tra ba trường hợp: người dùng có phim hạt giống (gợi ý bằng CF), người dùng phải dùng fallback và chế độ demo; cả ba đều trả đủ 5 phim, không trùng lặp và không chứa phim người dùng đã xem.

## 4.3. Thảo luận

Kết quả hai bài toán khai phá có thể được đối chiếu với nhau và với phần OLAP:

- Popularity Baseline đạt kết quả khá cao (Precision@5 = 0,20 trên test), phù hợp với nhận xét ở mục 3.3.2 rằng các phim được đánh giá nhiều nhất cũng thường được đánh giá cao. Item-based CF vẫn cải thiện được kết quả vì tận dụng thông tin cá nhân của từng người.
- Bốn cụm sở thích ở Q1 cho thấy người dùng có các khẩu vị khác biệt (Drama, Comedy, Action/Sci-Fi). Đây là lý do mô hình cá nhân hóa như CF có ưu thế hơn gợi ý chung cho mọi người.
- Cả hai bài toán đều đọc dữ liệu từ bốn khung nhìn chuẩn của kho; việc so sánh mã băm bảo đảm kết quả khai phá dựa trên đúng dữ liệu đã được đối soát ở chương 3.

## 4.4. Kết luận chương 4

Chương 4 đã trả lời hai câu hỏi khai phá. Với Q1, phân cụm K-Means (K = 4, dữ liệu tỷ lệ gốc) chia 6.038 người dùng thành bốn nhóm sở thích: đa dạng, Drama và tình cảm, hài, hành động và viễn tưởng; kết quả ổn định (ARI > 0,97) và có khác biệt rõ về cơ cấu giới tính, tuổi. Với Q2, item-based CF với 40 láng giềng đạt Precision@5 = 0,231 và Recall@5 = 0,0353 trên tập test, vượt Popularity Baseline ở cả hai chỉ số, trong một quy trình đánh giá chia theo thời gian, chọn tham số trên validation và chỉ dùng tập test một lần.
