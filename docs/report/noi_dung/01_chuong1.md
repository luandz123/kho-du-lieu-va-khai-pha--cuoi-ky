@chapter CHƯƠNG 1. CƠ SỞ LÝ THUYẾT

Chương này trình bày các khái niệm nền tảng được sử dụng trong đề tài, gồm kho dữ liệu và mô hình chiều, quy trình ETL, các thao tác OLAP, thuật toán phân cụm K-Means, hệ gợi ý dựa trên lọc cộng tác và các chỉ số dùng để đánh giá kết quả khai phá.

## 1.1. Kho dữ liệu

### 1.1.1. Khái niệm và đặc trưng

Theo W. H. Inmon, kho dữ liệu là “một tập hợp dữ liệu hướng chủ đề, tích hợp, ổn định và có tính lịch sử, phục vụ cho quá trình ra quyết định” [4]. Bốn đặc trưng trong định nghĩa này có ý nghĩa cụ thể như sau:

- **Hướng chủ đề:** dữ liệu được tổ chức xoay quanh các chủ đề phân tích (ví dụ: hoạt động đánh giá phim) thay vì xoay quanh các chức năng nghiệp vụ hằng ngày.
- **Tích hợp:** dữ liệu từ nhiều nguồn được chuẩn hóa về cùng định dạng, cùng quy ước mã hóa và cùng đơn vị đo.
- **Ổn định:** dữ liệu sau khi nạp chủ yếu được đọc để phân tích, không bị cập nhật liên tục như trong hệ thống giao dịch.
- **Có tính lịch sử:** mỗi bản ghi gắn với một mốc thời gian, cho phép phân tích xu hướng qua các kỳ.

Khác với cơ sở dữ liệu tác nghiệp (OLTP) được tối ưu cho các thao tác ghi nhỏ và thường xuyên, kho dữ liệu được tối ưu cho các truy vấn tổng hợp trên khối lượng lớn bản ghi [5]. Một kiến trúc kho dữ liệu điển hình gồm ba tầng: tầng **staging** tiếp nhận dữ liệu thô từ nguồn, tầng **kho dữ liệu** lưu dữ liệu đã chuẩn hóa theo mô hình chiều, và tầng **phân tích** cung cấp các khung nhìn tổng hợp cho công cụ báo cáo. Đề tài áp dụng đúng kiến trúc ba tầng này.

### 1.1.2. Mô hình dữ liệu chiều

Mô hình dữ liệu chiều (dimensional modeling) do R. Kimball đề xuất tổ chức dữ liệu thành hai loại bảng [3]:

- **Bảng sự kiện (fact table)** lưu các phép đo của một quy trình nghiệp vụ. Mỗi dòng là một sự kiện, gồm các khóa ngoại trỏ tới bảng chiều và các thước đo dạng số (ví dụ: số sao đánh giá).
- **Bảng chiều (dimension table)** lưu ngữ cảnh mô tả sự kiện: ai, cái gì, khi nào. Các thuộc tính trong bảng chiều được dùng để lọc, nhóm và gắn nhãn kết quả phân tích.

Khái niệm quan trọng nhất khi thiết kế là **mức chi tiết (grain)** của bảng sự kiện, tức là câu trả lời cho câu hỏi “một dòng trong bảng sự kiện đại diện cho điều gì?”. Kimball nhấn mạnh grain phải được xác định trước khi chọn chiều và thước đo, vì mọi phép tổng hợp sau này đều phụ thuộc vào nó [3].

Khi bảng sự kiện ở trung tâm nối trực tiếp với các bảng chiều, ta có **lược đồ hình sao (star schema)**. Nếu bảng chiều tiếp tục được chuẩn hóa thành nhiều bảng con, ta có **lược đồ bông tuyết (snowflake schema)**. Lược đồ sao được ưa chuộng vì truy vấn đơn giản và hiệu năng tốt.

Một tình huống đặc biệt là quan hệ **nhiều – nhiều** giữa bảng chiều và sự kiện, chẳng hạn một bộ phim thuộc nhiều thể loại. Nếu lưu thể loại thành một cột trong bảng phim, ta không thể lọc theo từng thể loại; nếu nhân bản dòng sự kiện cho mỗi thể loại, tổng số sự kiện sẽ bị đếm lặp. Giải pháp chuẩn là dùng **bảng cầu nối (bridge table)** giữa chiều phim và chiều thể loại [3]. Khi đó, cần phân biệt rõ hai đại lượng: số sự kiện duy nhất (đếm trên bảng sự kiện) và số lượt gắn thể loại (đếm sau khi nối qua bảng cầu nối).

### 1.1.3. Quy trình ETL

ETL (Extract – Transform – Load) là quy trình đưa dữ liệu từ nguồn vào kho [3], [5]:

- **Extract (trích xuất):** đọc dữ liệu từ nguồn, kiểm tra tính toàn vẹn của tệp và ghi vào vùng staging ở dạng gần nguyên bản nhất.
- **Transform (biến đổi):** làm sạch, ép kiểu, ánh xạ mã (ví dụ: mã tuổi sang nhóm tuổi), chuẩn hóa thời gian và tra cứu khóa thay thế (surrogate key).
- **Load (nạp):** ghi dữ liệu vào bảng chiều trước, bảng cầu nối và bảng sự kiện sau để bảo đảm ràng buộc khóa ngoại.

Có hai chiến lược nạp chính: **nạp toàn bộ (full refresh)**, xóa và nạp lại toàn bộ dữ liệu ở mỗi lần chạy, và **nạp tăng dần (incremental load)**, chỉ nạp phần thay đổi. Với một bộ dữ liệu tĩnh như MovieLens 1M, nạp toàn bộ là lựa chọn hợp lý. Để bảo đảm kho không bao giờ ở trạng thái “nạp dở”, toàn bộ quá trình nạp nên được bao trong một **giao dịch (transaction)**: nếu bất kỳ bước kiểm tra nào thất bại, giao dịch bị hủy (ROLLBACK) và kho giữ nguyên trạng thái cũ [6].

Sau khi nạp, cần **đối soát (reconciliation)** dữ liệu giữa nguồn và đích. Chỉ so sánh số dòng là chưa đủ, vì hai bảng có cùng số dòng vẫn có thể khác nội dung. Đề tài đối soát đồng thời số dòng, tổng điểm, phân bố giá trị, khóa và mã băm SHA-256 của dữ liệu sau khi tuần tự hóa theo cùng một quy ước.

## 1.2. Xử lý phân tích trực tuyến (OLAP)

OLAP là thuật ngữ do E. F. Codd đưa ra để chỉ các công cụ cho phép người dùng phân tích dữ liệu đa chiều một cách linh hoạt và nhanh chóng [7]. Dữ liệu được hình dung như một khối lập phương (cube) với mỗi trục là một chiều phân tích, mỗi ô chứa giá trị tổng hợp. Các thao tác OLAP cơ bản gồm [5], [8]:

- **Roll-up (cuộn lên):** tổng hợp lên mức chi tiết thấp hơn theo phân cấp, ví dụ từ tháng lên quý, từ quý lên năm.
- **Drill-down (khoan xuống):** đi ngược lại, từ năm xuống quý, tháng hoặc tới từng bộ phim.
- **Slice (cắt lát):** cố định một giá trị trên một chiều, ví dụ chỉ xét người dùng nữ.
- **Dice (cắt khối):** chọn đồng thời một tập giá trị trên nhiều chiều, ví dụ người dùng nữ, nhóm tuổi 18–24, thể loại Comedy và Drama.
- **Pivot (xoay):** đổi vị trí các chiều giữa hàng và cột để quan sát dữ liệu từ góc nhìn khác.

Trong hệ quản trị quan hệ, các thao tác này được hiện thực bằng SQL (mô hình ROLAP). Toán tử `GROUPING SETS` do Gray và cộng sự đề xuất [8] cho phép tính nhiều mức tổng hợp trong một truy vấn duy nhất. Một nguyên tắc quan trọng khi tổng hợp là phân biệt thước đo **cộng được** (như số lượt, tổng điểm) và **không cộng được** (như điểm trung bình). Điểm trung bình của một nhóm lớn phải được tính bằng tổng điểm chia tổng số lượt, không được lấy trung bình cộng của các điểm trung bình nhóm con, vì các nhóm con có quy mô khác nhau.

Tăng trưởng so với quý trước (QoQ) của đại lượng *n* tại quý *t* được tính theo công thức:

@eq \mathrm{QoQ}_t = 100 \times \dfrac{n_t - n_{t-1}}{n_{t-1}}\ (\%)

Khi quý trước không có dữ liệu (nₜ₋₁ = 0) thì QoQ không xác định và cần được hiển thị là N/A thay vì một giá trị bất kỳ.

## 1.3. Khai phá dữ liệu

Khai phá dữ liệu là quá trình phát hiện các mẫu có ý nghĩa, mới và hữu ích từ khối lượng lớn dữ liệu [5]. Theo mô hình CRISP-DM [9], một dự án khai phá đi qua sáu pha: hiểu bài toán, hiểu dữ liệu, chuẩn bị dữ liệu, xây dựng mô hình, đánh giá và triển khai. Đề tài áp dụng hai nhóm kỹ thuật: phân cụm (học không giám sát) cho câu hỏi Q1 và hệ gợi ý cho câu hỏi Q2.

### 1.3.1. Phân cụm K-Means

Cho tập gồm N điểm dữ liệu (mỗi điểm là một vector trong không gian d chiều), thuật toán K-Means [10] chia các điểm vào K cụm C₁, C₂, …, Cₖ sao cho tổng bình phương khoảng cách từ mỗi điểm tới tâm cụm của nó là nhỏ nhất:

@eq J = \sum_{c=1}^{K} \sum_{x_u \in C_c} \| x_u - \mu_c \|^2, \qquad \mu_c = \dfrac{1}{|C_c|}\sum_{x_u \in C_c} x_u

Đại lượng J được gọi là **inertia** hay **SSE**. Thuật toán lặp lại hai bước cho tới khi hội tụ: gán mỗi điểm vào cụm có tâm gần nhất, sau đó cập nhật tâm cụm bằng trung bình các điểm trong cụm. Do kết quả phụ thuộc vào vị trí tâm khởi tạo, đề tài dùng phương pháp khởi tạo k-means++ [11] và chạy lại 10 lần với các khởi tạo khác nhau (tham số `n_init = 10`), giữ lời giải có inertia nhỏ nhất.

K-Means dùng khoảng cách Euclid nên nhạy với thang đo của các đặc trưng. Phương pháp chuẩn hóa **StandardScaler** biến đổi mỗi đặc trưng về trung bình 0 và độ lệch chuẩn 1; điều này làm thay đổi trọng số của từng chiều trong phép đo khoảng cách. Vì thế, đề tài thử nghiệm cả dữ liệu gốc và dữ liệu đã chuẩn hóa để so sánh.

Việc chọn số cụm K được dựa trên nhiều tiêu chí:

- **Phương pháp khuỷu tay (elbow):** vẽ inertia theo K và tìm điểm mà tốc độ giảm inertia chậm lại rõ rệt.
- **Hệ số Silhouette** [12]: với mỗi điểm u, gọi a(u) là khoảng cách trung bình tới các điểm cùng cụm, b(u) là khoảng cách trung bình nhỏ nhất tới các điểm của một cụm khác. Hệ số Silhouette của điểm u là:

@eq s(u) = \dfrac{b(u) - a(u)}{\max\{a(u),\, b(u)\}} \in [-1, 1]

Giá trị trung bình càng gần 1 thì các cụm càng tách biệt; giá trị gần 0 cho thấy các cụm chồng lấn nhau.

- **Chỉ số Rand hiệu chỉnh (ARI)** [13]: đo mức độ giống nhau giữa hai cách phân cụm trên cùng một tập điểm, đã loại trừ yếu tố trùng hợp ngẫu nhiên. ARI bằng 1 khi hai cách phân cụm trùng khớp hoàn toàn. Đề tài dùng ARI để kiểm tra độ ổn định của kết quả khi thay đổi hạt giống ngẫu nhiên (random seed).
- **Khả năng diễn giải:** các cụm phải có kích thước hợp lý và có ý nghĩa thực tế.

### 1.3.2. Hệ gợi ý và lọc cộng tác dựa trên sản phẩm

Hệ gợi ý (recommender system) là hệ thống dự đoán những sản phẩm mà người dùng có khả năng quan tâm [14]. Có ba hướng tiếp cận chính: gợi ý dựa trên nội dung (content-based), lọc cộng tác (collaborative filtering) và kết hợp (hybrid). Lọc cộng tác chỉ sử dụng ma trận tương tác giữa người dùng và sản phẩm, không cần thông tin mô tả sản phẩm, nên rất phù hợp với MovieLens.

Lọc cộng tác dựa trên sản phẩm (item-based CF) do Sarwar và cộng sự đề xuất [15] và được Amazon áp dụng ở quy mô lớn [16]. Ý tưởng chính: nếu một người dùng thích phim j, họ có khả năng thích các phim i “tương tự” j, trong đó độ tương tự được đo qua hành vi đánh giá của toàn bộ cộng đồng. Gọi R là ma trận đánh giá với mỗi hàng là một phim và mỗi cột là một người dùng; độ tương tự cosine giữa hai phim i và j là:

@eq \mathrm{sim}(i, j) = \dfrac{R_i \cdot R_j}{\|R_i\| \, \|R_j\|}

Với người dùng u, gọi S(u) là tập phim mà u đánh giá từ 4 sao trở lên (phim “hạt giống”), Nₖ(j) là tập k phim láng giềng có độ tương tự cao nhất với phim j. Điểm xếp hạng của một phim ứng viên i mà u chưa đánh giá được tính bằng:

@eq \mathrm{score}(u, i) = \sum_{j \in S(u)} \mathbf{1}[\, i \in N_k(j)\,] \cdot \mathrm{sim}(i, j)

Năm phim có điểm cao nhất được đưa ra làm gợi ý. Điểm này chỉ dùng để xếp hạng, không phải là số sao dự đoán.

Để đánh giá một mô hình gợi ý có thực sự hữu ích hay không, cần so sánh với một **mô hình cơ sở (baseline)**. Mô hình cơ sở phổ biến nhất là **Popularity Baseline**: gợi ý những phim được đánh giá nhiều nhất mà người dùng chưa xem. Nghiên cứu của Cremonesi và cộng sự cho thấy mô hình đơn giản này thường đạt kết quả khá cao trên bài toán Top-N [17], nên đây là mốc so sánh nghiêm túc.

### 1.3.3. Đánh giá hệ gợi ý Top-N

Với bài toán gợi ý danh sách N phim, các chỉ số thường dùng là Precision@N và Recall@N [17], [18]. Gọi L(u) là danh sách gợi ý cho người dùng u, T(u) là tập phim u thực sự đánh giá tích cực trong giai đoạn đánh giá, và h(u) = |L(u) ∩ T(u)| là số gợi ý đúng:

@eq \mathrm{Precision@5}(u) = \dfrac{h(u)}{5}, \qquad \mathrm{Recall@5}(u) = \dfrac{h(u)}{|T(u)|}

Kết quả chung là trung bình cộng của các giá trị trên tất cả người dùng được đánh giá (macro average), mỗi người có trọng số như nhau.

Một lỗi phương pháp thường gặp là **rò rỉ dữ liệu (data leakage)**: chia ngẫu nhiên các lượt đánh giá thành tập huấn luyện và tập kiểm tra khiến mô hình được “nhìn thấy” thông tin của tương lai. Campos và cộng sự [19] khuyến nghị chia dữ liệu theo thời gian: mọi đánh giá trong tập huấn luyện đều xảy ra trước mọi đánh giá trong tập kiểm tra. Đề tài áp dụng cách chia ba phần theo mốc thời gian: **train** để huấn luyện, **validation** để chọn tham số và **test** chỉ dùng một lần để báo cáo kết quả cuối cùng.

## 1.4. Công cụ sử dụng

@table Bảng 1.1. Công cụ và phiên bản sử dụng trong đề tài
@widths 4,3,9
| Công cụ | Phiên bản | Vai trò |
| PostgreSQL | 17 | Lưu trữ staging, kho dữ liệu, các khung nhìn OLAP và kết quả phân cụm |
| Python | 3.12 | Ngôn ngữ cho ETL, đối soát, khai phá dữ liệu và kiểm thử |
| pandas, NumPy, SciPy | 2.3 / 2.0 / 1.14 | Xử lý dữ liệu dạng bảng, ma trận thưa |
| scikit-learn | 1.5.2 | K-Means, StandardScaler, Silhouette, ARI, chuẩn hóa vector [20] |
| psycopg2 | 2.9 | Kết nối Python với PostgreSQL |
| Apache Superset | 6.1.0 | Xây dựng dashboard, chạy trong container Docker riêng [21] |
| pytest | 8.4 | Kiểm thử tự động |
| Git, GitHub | – | Quản lý mã nguồn, rà soát chéo qua pull request |

## 1.5. Kết luận chương 1

Chương 1 đã trình bày các cơ sở lý thuyết cần thiết cho đề tài. Về kho dữ liệu, mô hình chiều với lược đồ sao và bảng cầu nối cho phép xử lý đúng quan hệ phim – thể loại; quy trình ETL trong một giao dịch kèm đối soát đa chỉ số bảo đảm dữ liệu trong kho đúng và nhất quán. Về phân tích, các thao tác OLAP cùng nguyên tắc tính trung bình có trọng số và QoQ là nền tảng để trả lời câu hỏi Q3. Về khai phá, K-Means với các tiêu chí inertia, Silhouette và ARI được dùng cho câu hỏi Q1; item-based CF cùng Popularity Baseline và cách chia dữ liệu theo thời gian được dùng cho câu hỏi Q2. Chương tiếp theo áp dụng các kiến thức này để phân tích dữ liệu và thiết kế kho dữ liệu.
