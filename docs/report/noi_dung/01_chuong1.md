@chapter CHƯƠNG 1. CƠ SỞ LÝ THUYẾT

Chương này trình bày các khái niệm nền tảng được sử dụng trong đề tài, gồm kho dữ liệu và mô hình chiều, quy trình ETL, các thao tác OLAP, thuật toán phân cụm K-Means, hệ gợi ý dựa trên lọc cộng tác, các chỉ số dùng để đánh giá kết quả khai phá, và các thành phần của nền tảng dữ liệu hiện đại được dùng trong bản nâng cấp.

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

Có hai chiến lược nạp chính: **nạp toàn bộ (full refresh)**, xóa và nạp lại toàn bộ dữ liệu ở mỗi lần chạy, và **nạp tăng dần (incremental load)**, chỉ nạp phần thay đổi. Với một bộ dữ liệu tĩnh như MovieLens 1M, nạp toàn bộ là lựa chọn hợp lý; khi dữ liệu phát sinh liên tục, nạp tăng dần trở nên cần thiết (mục 1.4.4). Để bảo đảm kho không bao giờ ở trạng thái “nạp dở”, toàn bộ quá trình nạp nên được bao trong một **giao dịch (transaction)**: nếu bất kỳ bước kiểm tra nào thất bại, giao dịch bị hủy (ROLLBACK) và kho giữ nguyên trạng thái cũ [6].

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

## 1.4. Nền tảng dữ liệu hiện đại

Mục này trình bày các khái niệm được dùng trong bản nâng cấp ở chương 5, khi hệ thống phải tiếp nhận dữ liệu từ nhiều nguồn và cập nhật liên tục.

### 1.4.1. Thu thập dữ liệu thay đổi (CDC)

CDC (Change Data Capture) là kỹ thuật phát hiện và chuyển tiếp các thay đổi (thêm, sửa, xóa) trên cơ sở dữ liệu nguồn tới hệ thống đích [22]. Cách đơn giản nhất là định kỳ truy vấn các dòng có cột `updated_at` mới hơn lần đọc trước, nhưng cách này có ba nhược điểm: không thấy được các dòng đã bị xóa, có thể bỏ sót thay đổi xảy ra giữa hai lần quét, và tạo thêm tải truy vấn lên cơ sở dữ liệu nguồn.

**CDC dựa trên log** khắc phục các nhược điểm trên bằng cách đọc nhật ký giao dịch mà hệ quản trị vốn phải ghi. Trong PostgreSQL, đó là **WAL (Write-Ahead Log)**: mọi thay đổi được ghi vào WAL trước khi ghi vào bảng, để phục hồi khi hệ thống gặp sự cố [6]. Khi đặt `wal_level = logical`, WAL có thể được giải mã thành các thay đổi theo từng dòng; mỗi thay đổi có một vị trí **LSN (Log Sequence Number)** tăng dần, cho phép sắp đúng thứ tự. **Replication slot** giúp PostgreSQL ghi nhớ bên đọc đã đọc tới đâu, còn **publication** khai báo những bảng được phát thay đổi. Debezium [23] là công cụ mã nguồn mở phổ biến cho CDC dựa trên log; mỗi thay đổi được biểu diễn thành một sự kiện gồm loại thao tác (`op`), giá trị trước (`before`) và sau (`after`) của dòng, cùng thông tin nguồn như LSN.

### 1.4.2. Xử lý luồng sự kiện với Apache Kafka

Apache Kafka [24] là nền tảng truyền sự kiện phân tán. Sự kiện được ghi vào các **topic**; mỗi topic chia thành nhiều **partition**, trong mỗi partition các sự kiện giữ đúng thứ tự và được đánh số **offset** tăng dần. Bên đọc thuộc một **consumer group** và tự lưu (commit) offset đã xử lý. Kafka tách bên gửi khỏi bên nhận: làm vùng đệm khi bên nhận chậm, cho nhiều bên cùng đọc một luồng và cho phép đọc lại dữ liệu trong thời gian lưu giữ.

Thời điểm commit offset quyết định ngữ nghĩa xử lý [25]. Commit trước rồi xử lý có thể làm mất sự kiện khi bên đọc gặp sự cố (*at-most-once*). Xử lý xong rồi mới commit thì không mất nhưng có thể xử lý lặp (*at-least-once*). *Exactly-once* đòi hỏi giao dịch giữa các hệ thống; trong thực tế, hiệu quả tương đương thường đạt được bằng at-least-once kết hợp với thao tác ghi idempotent ở đích, tức là ghi lặp lại cùng một dữ liệu không làm thay đổi kết quả.

### 1.4.3. Data lake và kiến trúc medallion

Data lake là kho lưu trữ dữ liệu ở mọi định dạng (có cấu trúc, bán cấu trúc, phi cấu trúc) với chi phí thấp, thường trên hệ lưu trữ đối tượng theo chuẩn S3. Khác với kho dữ liệu có lược đồ chặt được áp đặt khi ghi (*schema-on-write*), data lake giữ dữ liệu ở dạng gốc và chỉ diễn giải lược đồ khi đọc (*schema-on-read*) [26]. Kiến trúc **medallion** tổ chức data lake thành ba tầng: **bronze** giữ dữ liệu thô đúng như nguồn gửi về, **silver** chứa dữ liệu đã làm sạch, chuẩn hóa và tích hợp, **gold** chứa dữ liệu đã tổng hợp hoặc định hình sẵn cho mục đích sử dụng [27]. Việc giữ tầng bronze cho phép xử lý lại toàn bộ khi phát hiện lỗi logic ở các tầng sau mà không cần lấy lại dữ liệu từ nguồn.

Ở các tầng silver và gold, dữ liệu thường được lưu bằng định dạng cột **Apache Parquet** [28]: chỉ đọc các cột cần dùng, nén hiệu quả, giữ kiểu dữ liệu và lưu thống kê min/max để bỏ qua các khối không liên quan. **DuckDB** [29] là cơ sở dữ liệu phân tích nhúng trong tiến trình, có thể truy vấn trực tiếp tệp CSV, JSON và Parquet trên S3 bằng SQL.

### 1.4.4. Nạp tăng dần và chiều thay đổi chậm

Nạp tăng dần chỉ xử lý phần dữ liệu thay đổi kể từ lần nạp trước. Mốc đã nạp được lưu trong một bảng **watermark**; mỗi lần chạy, hệ thống đọc các bản ghi mới hơn mốc này và ghi vào kho bằng thao tác **upsert** (thêm mới nếu chưa có, cập nhật nếu đã có theo khóa). Để không bỏ sót dữ liệu đến muộn, có thể đọc lùi một khoảng trước mốc; upsert theo khóa bảo đảm phần đọc chồng lấn không gây nhân đôi. Watermark phải được cập nhật trong cùng giao dịch với dữ liệu.

Khi thuộc tính của một bảng chiều thay đổi theo thời gian (ví dụ người dùng đổi nghề nghiệp), Kimball phân loại các cách xử lý thành các loại **SCD (Slowly Changing Dimension)** [3]. **SCD loại 1** ghi đè giá trị cũ, đơn giản nhưng mất lịch sử. **SCD loại 2** giữ lịch sử bằng cách thêm một dòng mới cho mỗi phiên bản, kèm khoảng hiệu lực (`valid_from`, `valid_to`) và cờ phiên bản hiện tại; khóa thay thế là bắt buộc vì một khóa tự nhiên có thể ứng với nhiều dòng. Mỗi sự kiện được gắn với phiên bản có hiệu lực tại thời điểm xảy ra sự kiện. Kimball cũng phân biệt bảng sự kiện **giao dịch** (một dòng cho mỗi sự kiện) với bảng **chụp nhanh định kỳ** (một dòng cho mỗi thực thể trong mỗi kỳ, ví dụ phim × ngày) [3].

### 1.4.5. Điều phối quy trình

Một quy trình dữ liệu gồm nhiều bước phụ thuộc nhau cần được chạy theo lịch, thử lại khi lỗi và lưu vết từng lần chạy. Apache Airflow [30] biểu diễn mỗi quy trình bằng một **DAG** (đồ thị có hướng không chu trình) gồm các **task** và quan hệ phụ thuộc giữa chúng. So với lịch chạy đơn giản như cron, Airflow cung cấp quản lý phụ thuộc, thử lại tự động, lịch sử chạy, nhật ký từng task và giao diện, API để kích hoạt thủ công. Để thử lại an toàn, mỗi task nên có tính idempotent.

### 1.4.6. Embedding và tìm kiếm ngữ nghĩa

Embedding là cách biểu diễn một đoạn văn bản bằng một vector số thực sao cho các văn bản có nghĩa gần nhau có vector gần nhau. Các mô hình embedding đa ngôn ngữ như multilingual-E5 [31] được huấn luyện trên dữ liệu nhiều ngôn ngữ, nên một câu tiếng Việt và một đoạn tiếng Anh cùng nghĩa cho vector gần nhau. Độ gần thường được đo bằng cosine như công thức ở mục 1.3.2. Phần mở rộng **pgvector** [32] bổ sung kiểu dữ liệu vector và phép tìm láng giềng gần nhất cho PostgreSQL; chỉ mục **HNSW** [33] tổ chức các vector thành đồ thị nhiều tầng để tìm láng giềng gần đúng rất nhanh.

Embedding cho phép xây dựng gợi ý **dựa trên nội dung**: điểm của một phim ứng viên là độ tương tự giữa vector của phim đó với hồ sơ sở thích của người dùng (ví dụ trung bình vector các phim người đó yêu thích). Mô hình **lai (hybrid)** kết hợp điểm lọc cộng tác và điểm nội dung, nhằm tận dụng ưu điểm của cả hai: lọc cộng tác mạnh khi có nhiều lịch sử, còn nội dung giúp gợi ý được phim mới chưa có đánh giá [14].

## 1.5. Công cụ sử dụng

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
| Docker Compose | – | Chạy toàn bộ dịch vụ của bản nâng cấp trên một máy |
| Debezium | 2.7.3 | CDC: đọc WAL của PostgreSQL, phát sự kiện thay đổi |
| Apache Kafka | 3.9.0 | Truyền sự kiện CDC và streaming (chế độ KRaft) |
| MinIO | – | Data lake theo chuẩn S3 |
| DuckDB | 1.2.2 | Biến đổi dữ liệu trên data lake bằng SQL |
| Apache Airflow | 2.10.4 | Điều phối ba DAG nạp dữ liệu |
| pgvector | 0.8.0 | Lưu vector phim, tìm kiếm theo cosine |
| sentence-transformers | 3.3.1 | Mô hình embedding multilingual-e5-small |
| Streamlit | 1.40.2 | Ứng dụng web xem phim, chấm điểm, gợi ý và theo dõi pipeline |

## 1.6. Kết luận chương 1

Chương 1 đã trình bày các cơ sở lý thuyết cần thiết cho đề tài. Về kho dữ liệu, mô hình chiều với lược đồ sao và bảng cầu nối cho phép xử lý đúng quan hệ phim – thể loại; quy trình ETL trong một giao dịch kèm đối soát đa chỉ số bảo đảm dữ liệu trong kho đúng và nhất quán. Về phân tích, các thao tác OLAP cùng nguyên tắc tính trung bình có trọng số và QoQ là nền tảng để trả lời câu hỏi Q3. Về khai phá, K-Means với các tiêu chí inertia, Silhouette và ARI được dùng cho câu hỏi Q1; item-based CF cùng Popularity Baseline và cách chia dữ liệu theo thời gian được dùng cho câu hỏi Q2. Ngoài ra, các khái niệm CDC dựa trên log, Kafka, data lake ba tầng, nạp tăng dần, SCD loại 2, điều phối bằng DAG và embedding là cơ sở cho bản nâng cấp ở chương 5. Chương tiếp theo áp dụng các kiến thức này để phân tích dữ liệu và thiết kế kho dữ liệu.
