# Chương 2. Cơ sở lý thuyết và phương pháp

Chương này giải thích phương pháp; cấu hình và kết quả đo được trình bày ở [chương 5](chapter_05.md). Các ví dụ dưới đây là fixture tự tạo, không trích dữ liệu cá nhân MovieLens. Mã tài liệu P2-R được giải thích trong [danh mục tham khảo](references.md).

## 2.1. Kho dữ liệu, grain và mô hình chiều

Kho dữ liệu (DW) tổ chức dữ liệu đã chuẩn hóa để hỗ trợ truy vấn phân tích nhất quán. Trong dự án, staging là vùng tiếp nhận và kiểm tra nguồn; DW lưu các sự kiện đánh giá cùng chiều mô tả; analytics cung cấp các phép tổng hợp và kết quả mô hình đã kiểm. Grain phải được xác định trước khi chọn khóa và thước đo: nó diễn đạt một dòng fact đại diện sự kiện nào. Theo [Kimball, Fact Tables](https://www.kimballgroup.com/2008/11/fact-tables/) (P2-R01), thước đo phải phù hợp grain và các dimension cung cấp ngữ cảnh phân tích.

Ở đây grain fact là **một đánh giá nguồn**, có số sao và thời điểm gửi; không phải lượt xem. Dimension user, movie, date và genre mô tả ngữ cảnh. Một phim nhiều genre được biểu diễn bằng bridge movie–genre. Mô hình sao thuận tiện cho tổng hợp qua fact và dimension; quan hệ đa trị của genre đòi hỏi thêm bridge và định nghĩa mẫu số rõ ràng. Thiết kế cụ thể và ràng buộc của dự án được trình bày ở [chương 3, mục 3.3–3.6](../../P1/report/chapter_03.md), không phải một mô hình SCD/incremental đã triển khai đầy đủ.

Ví dụ fixture: một đánh giá 4 sao cho phim thuộc Action và Comedy là một dòng fact, nhưng khi nối bridge tạo hai lượt gắn genre. COUNT trên fact cho 1 đánh giá; COUNT sau nối bridge cho 2 lượt gắn genre. Hai đại lượng hợp lệ cho hai câu hỏi khác nhau, không được gọi cùng là tổng rating hệ thống. Điểm trung bình khi roll-up phải bằng tổng số sao chia tổng số đánh giá, không phải trung bình không trọng số của các điểm trung bình nhóm.

## 2.2. ETL theo lô, transaction và đối soát

ETL gồm trích xuất, biến đổi và nạp dữ liệu. Với snapshot cố định, dự án dùng full refresh theo lô: đọc nguồn theo contract, kiểm miền/khóa, ánh xạ dimension, nạp bridge và fact rồi đối soát trước commit. Count kiểm bảo toàn số dòng; canonical hash kiểm nội dung đã tuần tự hóa theo cùng schema, thứ tự cột, thứ tự dòng, UTC và quy tắc byte. Count bằng nhau riêng lẻ không chứng minh dữ liệu bằng nhau.

Transaction gom các thao tác thành đơn vị nguyên tử. BEGIN mở giao dịch, COMMIT xác nhận và ROLLBACK hủy thay đổi chưa commit; đây là cơ chế nền của PostgreSQL, không phải chỉ đặt tên trạng thái trong log. [PostgreSQL 17, Transactions](https://www.postgresql.org/docs/17/tutorial-transactions.html) (P2-R02). Trong dự án, lỗi đối soát phải ngăn công bố snapshot mới; kết quả cụm cũ bị vô hiệu hóa khi DW refresh và chỉ được kích hoạt sau đối soát gói G3. Phạm vi rollback/restore thực kiểm thuộc chương 4 và [ma trận I04–I08, I13–I14](../../P1/integration_acceptance.md). Không suy rằng mọi lỗi phần cứng hoặc mất kết nối lúc COMMIT đã được thử.

## 2.3. Các thao tác OLAP và ý nghĩa tổng hợp

OLAP phân tích dữ liệu theo nhiều chiều và cấp chi tiết. Trong phạm vi dự án, các thao tác được hiểu theo giao diện SQL/dashboard đã công bố, không hàm ý đã triển khai một máy chủ cube riêng:

- Roll-up tổng hợp từ tháng lên quý/năm; drill-down đi ngược về tháng/phim.
- Slice cố định một giá trị của chiều, chẳng hạn giới tính; dice chọn kết hợp các tập giá trị thể loại, tuổi và khoảng thời gian.
- Pivot đổi cách bố trí hàng/cột của cùng phép tổng hợp, không thay đổi grain hoặc mẫu số.

Các thao tác thực tế O1–O6 được dẫn ở [chương 4](../../P1/report/chapter_04.md) và [SQL OLAP](../../../olap/queries.sql). Với Q3, đặt n(g,q) là số lượt gắn genre g trong quý q. QoQ = 100 × [n(g,q) − n(g,q−1)] / n(g,q−1); mẫu số bằng 0 hoặc chưa có quý trước thì N/A. Lưới genre×quý phải điền 0 trước LAG để so đúng quý liền trước. Tỷ trọng genre dùng tổng lượt gắn tất cả genre cùng quý làm mẫu số; nó khác tỷ lệ trên tổng rating duy nhất. Ngưỡng quý trước ≥100 và loại quý biên là quy tắc thực nghiệm đã chốt, không phải một định luật OLAP.

## 2.4. Đặc trưng tỷ lệ genre và K-Means

### 2.4.1. Tạo vector sở thích từ đánh giá tích cực

Theo [mining/features.py](../../../mining/features.py), một đánh giá rating ≥4 được quy ước là tích cực. Đặt G(i) là tập genre của phim i và P(u) là tập phim được đánh giá tích cực trong lịch sử dùng cho Q1:

$$C_{u,g}=\sum_{i\in P(u)}\mathbf{1}[g\in G(i)],\quad S_u=\sum_{g=1}^{18}C_{u,g},\quad p_{u,g}=C_{u,g}/S_u\;(S_u>0).$$

Mỗi phim đa genre đóng góp 1 cho **từng** genre, rồi chuẩn hóa bằng tổng lượt gắn genre tích cực; không chia mỗi phim thành trọng số 1/|G(i)|. Vector có 18 chiều theo A–Z, không âm, tổng bằng 1 trong tolerance 10⁻⁸. Nếu S(u)=0 thì status là insufficient_evidence và cluster_id NULL; không đưa vector rỗng vào K-Means. Giới/tuổi/nghề không nằm trong feature.

**Bảng 2.1. Fixture tính tay vector genre.** Đơn vị: số sao, lượt gắn và tỷ lệ; mẫu số vector là 3 lượt gắn genre tích cực của một hồ sơ giả định.

| Phim ký hiệu tự tạo | Genre | Rating giả định | Đóng góp vào C |
|---|---|---:|---|
| A | Action, Comedy | 5 | Action +1, Comedy +1 |
| B | Comedy | 4 | Comedy +1 |
| C | Drama | 2 | Không cộng |

Nguồn: fixture do tác giả tạo theo features.py; không phải bản ghi thực. Kết quả: p(Action)=1/3, p(Comedy)=2/3, 16 chiều còn lại bằng 0. Đây là tỷ lệ liên kết genre từ đánh giá tích cực, không phải tỷ lệ thời gian xem. Feature Q1 dùng toàn lịch sử chỉ để mô tả; không đưa vào đánh giá thời gian Q2.

### 2.4.2. Hàm mục tiêu và tiền xử lý

K-Means phân  N vector vào K cụm và tối thiểu hóa tổng bình phương khoảng cách Euclidean đến tâm:

$$J=\sum_{c=1}^{K}\sum_{u\in C_c}\|x_u-\mu_c\|_2^2,\qquad \mu_c=|C_c|^{-1}\sum_{u\in C_c}x_u.$$

Đây là inertia/SSE. Thuật toán lặp gán điểm về tâm gần nhất và cập nhật tâm trung bình; khởi tạo ảnh hưởng nghiệm cục bộ. [scikit-learn 1.5.2, K-Means](https://scikit-learn.org/1.5/modules/clustering.html#k-means) (P2-R03). Dự án so sánh x=p nguyên tỷ lệ (raw) và z=(p−mean)/standard deviation theo genre. StandardScaler làm thay đổi trọng số khoảng cách; vì vậy không so trực tiếp độ lớn SSE giữa hai không gian để chọn bên tốt hơn. Profile sau phân cụm luôn là trung bình tỷ lệ **gốc** của người thuộc cụm.

### 2.4.3. Chỉ số đánh giá và độ ổn định

Với điểm u, a(u) là khoảng cách trung bình đến các điểm cùng cụm (không kể chính nó), b(u) là giá trị nhỏ nhất của khoảng cách trung bình đến từng cụm khác. Silhouette s(u)=[b(u)−a(u)]/max[a(u),b(u)], rồi lấy trung bình; cụm singleton dùng quy ước thư viện. Giá trị gần 0 thể hiện chồng lấn. [Tài liệu silhouette_score](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.silhouette_score.html) (P2-R04). Code dự án fit trên toàn bộ assigned nhưng tính Silhouette trên một mẫu cố định; khoảng cách trong chỉ số này cũng được tính trong mẫu, không gọi là Silhouette toàn tập.

ARI so sánh hai cách gán cụm trên cùng tập điểm, điều chỉnh sự đồng thuận ngẫu nhiên: ARI=(RI−E[RI])/(max(RI)−E[RI]). Nó bất biến với hoán vị nhãn cụm. [Tài liệu adjusted_rand_score](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.adjusted_rand_score.html) (P2-R05). Trong dự án, ARI đo ổn định giữa seed, không phải độ chính xác so với nhãn sở thích đúng. PCA hai chiều chỉ minh họa phép chiếu, không là không gian fit và không chứng minh các cụm tách biệt hoàn toàn.

## 2.5. Cosine item-based CF, baseline và fallback

Item-based CF khai thác quan hệ giữa các item từ ma trận đánh giá; nghiên cứu của Sarwar và cộng sự là cơ sở tiếp cận item–item, có xem xét cosine và các cách tổng hợp gợi ý. [Sarwar et al., WWW 2001](https://www.ra.ethz.ch/cdstore/www10/papers/pdf/p519.pdf) (P2-R06). Phiên bản dự án dưới đây là quy tắc xếp hạng riêng theo code, không sao chép công thức dự đoán sao của bài báo.

Ma trận R có hàng là phim, cột là người dùng trong lịch sử huấn luyện; ô quan sát chứa rating 1..5, ô chưa quan sát bằng 0. Số 0 là cách biểu diễn thiếu tương tác, không phải đánh giá 0 sao. Không trừ trung bình người dùng. Với hai hàng phim khác nhau:

$$sim(i,j)=\frac{R_i\cdot R_j}{\|R_i\|_2\|R_j\|_2}.$$

Đặt đường chéo 0, chỉ giữ sim>0; N_k(j) là tối đa neighbor_k láng giềng của **phim seed j**, xếp similarity giảm rồi movie_id tăng. Việc cắt top-k làm quan hệ láng giềng có thể không đối xứng dù cosine đối xứng. Đặt H(u) là toàn bộ phim đã đánh giá trong lịch sử được phép, S(u) là các phim rating ≥4 trong H(u). Điểm ứng viên i chưa nằm trong H(u) là:

$$score(u,i)=\sum_{j\in S(u)}\mathbf{1}[i\in N_k(j)]\,sim(i,j).$$

Công thức khớp [recommend_for_user_cf](../../../mining/cf.py): không nhân thêm số sao seed, không chia tổng similarity. Score là điểm xếp hạng tổng hợp, có thể lớn hơn 1; không phải trực tiếp một cosine hoặc sao dự đoán. Xếp theo score giảm, popularity huấn luyện giảm rồi movie_id tăng; xếp trước khi làm tròn score xuất ra.

Fixture tự tạo: hai hàng phim (4,0) và (4,3) có cosine 16/(4×5)=0,8. Nếu một ứng viên nằm trong láng giềng của hai seed với similarity 0,8 và 0,6 thì score=1,4. Ví dụ này minh họa công thức, không công bố gợi ý cho người dùng thực.

Popularity Baseline đếm **mọi** rating huấn luyện của phim, gồm cả rating dưới 4; hòa count thì movie_id tăng. Sau khi loại H(u), lấy Top-N=5. Nếu CF có dưới 5 ứng viên điểm dương, bổ sung từ cùng bảng popularity, loại lịch sử và mục đã chọn. Các dòng bổ sung mang score_type=popularity_fallback; score nội bộ None và CLI hiển thị N/A (Popularity Fallback). Không trộn số đếm popularity vào float score CF. Baseline là mô hình đối chứng độc lập; fallback là cơ chế hoàn thiện danh sách CF. [Nguồn: baseline.py, cf.py và recommend.py trong mining.]

## 2.6. Chia thời gian và đánh giá Top-5

Phân vị timestamp toàn cục ở mức 0,70 và 0,85 được nội suy tuyến tính rồi lấy int thành t₁,t₂. Train: t≤t₁; validation: t₁<t≤t₂; Test: t>t₂. Timestamp hòa giữ cùng phía. Validation chỉ học từ Train; sau chọn neighbor_k mới fit Train+Validation để đánh giá Test đóng băng. Q1 và demo toàn lịch sử không tham gia việc chọn cấu hình Q2. Đây là thiết kế giảm rò rỉ tương lai trong snapshot, không chứng minh hiệu quả triển khai trực tuyến.

Cohort gồm người có ≥5 rating trong lịch sử huấn luyện và ≥1 phim rating ≥4 trong kỳ đánh giá. Candidate universe I(u)=catalog huấn luyện trừ H(u), không negative sampling. Phim mới chưa có trong catalog huấn luyện không thể được CF/baseline đề xuất, nhưng phim tích cực mới vẫn nằm trong mẫu số Recall.

Đặt L₅(u) là danh sách gợi ý tối đa 5 phim, T(u) là toàn bộ phim tích cực kỳ đánh giá, h(u)=|L₅(u)∩T(u)|. Công thức thực thi ở [evaluation.py](../../../mining/evaluation.py):

$$P@5(u)=h(u)/5,\quad R@5(u)=h(u)/|T(u)|,$$
$$macro\ P@5=|U|^{-1}\sum_{u\in U}P@5(u),\quad macro\ R@5=|U|^{-1}\sum_{u\in U}R@5(u).$$

**Bảng 2.2. Định nghĩa và mẫu số chỉ số.**

| Chỉ số | Đơn vị | Mẫu số/phạm vi |
|---|---|---|
| Precision@5 | Tỷ lệ [0,1] | 5 vị trí cố định, cả khi trả thiếu |
| Recall@5 | Tỷ lệ [0,1] | Số phim tích cực của từng người trong kỳ, gồm phim mới |
| Macro | Trung bình tỷ lệ | Số người đủ điều kiện, mỗi người trọng số ngang nhau |
| Fallback rate | % người | Người có dùng ít nhất một mục fallback / cohort ×100 |
| Inertia | Tổng bình phương khoảng cách | Tổng trên toàn assigned trong không gian fit, không chia N |
| Silhouette | Không đơn vị | Trung bình trên mẫu cố định |
| ARI | Không đơn vị | Cặp điểm của cùng tập assigned ở hai lần gán nhãn |

Nguồn: code evaluation.py/clustering.py và P2-R03–R05. Precision/Recall dựa nguyên lý số đúng trên số đề xuất/số liên quan ([tài liệu precision](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.precision_score.html), [recall](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.recall_score.html), P2-R07–R08); macro trong dự án lấy trung bình **theo người**, không dùng trực tiếp macro theo nhãn của API phân loại.

Fixture tính tay: hồ sơ giả định A có 2 hits trong 5 gợi ý và 4 phim relevant (gồm 1 phim mới), nên P=0,4, R=0,5. Hồ sơ giả định B trả 3 gợi ý, có 1 hit và 2 relevant, nên P=0,2, R=0,5. Macro trên đúng hai hồ sơ giả định là P=0,3 và R=0,5; không đổi mẫu số Precision của B thành 3. Recall đo mức thu hồi relevant, **không phải catalog coverage**. Không kết luận tất cả phim chưa đánh giá là không thích hoặc mọi rating ≤3 là bằng chứng người dùng không quan tâm.
