@front LỜI NÓI ĐẦU

Trong những năm gần đây, dữ liệu đã trở thành một nguồn tài nguyên quan trọng của mọi tổ chức. Tuy nhiên, dữ liệu thô chỉ thực sự có giá trị khi được tổ chức lại một cách nhất quán để phục vụ phân tích, và khi các tri thức ẩn bên trong được khai thác bằng những phương pháp phù hợp. Môn học **Kho dữ liệu và Khai phá dữ liệu** trang bị cho sinh viên hai nhóm kiến thức bổ trợ cho nhau: xây dựng kho dữ liệu để tổng hợp, phân tích đa chiều (OLAP) và áp dụng các kỹ thuật khai phá để tìm ra các mẫu, các nhóm và các quy luật trong dữ liệu.

Với mong muốn vận dụng trọn vẹn cả hai nhóm kiến thức trên vào một bài toán thực tế, nhóm chúng em lựa chọn đề tài **“Xây dựng kho dữ liệu và khai phá dữ liệu đánh giá phim MovieLens 1M”**. Đề tài đi qua toàn bộ quy trình: từ khảo sát dữ liệu gốc, thiết kế lược đồ sao, xây dựng quy trình ETL có kiểm soát, viết các truy vấn OLAP, dựng dashboard trên Apache Superset, cho tới phân cụm người dùng bằng K-Means và xây dựng hệ gợi ý phim bằng lọc cộng tác dựa trên sản phẩm (item-based collaborative filtering).

Nhóm xin chân thành cảm ơn giảng viên phụ trách học phần đã truyền đạt kiến thức nền tảng và định hướng trong suốt quá trình học tập, giúp nhóm có cơ sở để hoàn thành đề tài này. Dù đã cố gắng thực hiện một cách cẩn thận, do thời gian và kinh nghiệm còn hạn chế nên báo cáo khó tránh khỏi thiếu sót. Nhóm rất mong nhận được những góp ý của thầy cô để đề tài được hoàn thiện hơn.

@lists

@front DANH MỤC CÁC TỪ VIẾT TẮT

@table Bảng 0.1. Các từ viết tắt sử dụng trong báo cáo
@widths 3,6.5,6.5
| Viết tắt | Tiếng Anh | Ý nghĩa |
| DW | Data Warehouse | Kho dữ liệu |
| ETL | Extract – Transform – Load | Trích xuất – Biến đổi – Nạp dữ liệu |
| OLAP | Online Analytical Processing | Xử lý phân tích trực tuyến |
| BI | Business Intelligence | Trí tuệ doanh nghiệp, báo cáo phân tích |
| EDA | Exploratory Data Analysis | Phân tích khám phá dữ liệu |
| CF | Collaborative Filtering | Lọc cộng tác |
| KPI | Key Performance Indicator | Chỉ số đo lường chính |
| QoQ | Quarter over Quarter | Tăng trưởng so với quý trước |
| SSE | Sum of Squared Errors | Tổng bình phương sai số (inertia) |
| ARI | Adjusted Rand Index | Chỉ số Rand hiệu chỉnh |
| PK / FK | Primary Key / Foreign Key | Khóa chính / Khóa ngoại |
| UTC | Coordinated Universal Time | Giờ phối hợp quốc tế |
| CLI | Command Line Interface | Giao diện dòng lệnh |

@body

@chapter MỞ ĐẦU

## 1. Lý do chọn đề tài

Các nền tảng xem phim, thương mại điện tử hay mạng xã hội đều ghi nhận một lượng rất lớn phản hồi của người dùng dưới dạng đánh giá, lượt thích hoặc bình luận. Dữ liệu này có thể được khai thác theo hai hướng. Hướng thứ nhất là **phân tích mô tả**: trả lời các câu hỏi như phim nào được đánh giá nhiều nhất, thể loại nào được ưa chuộng trong từng nhóm tuổi, hoạt động đánh giá biến động ra sao theo thời gian. Hướng thứ hai là **khai phá tri thức**: phát hiện các nhóm người dùng có sở thích tương đồng và dự đoán phim mà một người có thể quan tâm để đưa ra gợi ý.

Hai hướng trên đòi hỏi một nền dữ liệu chung, sạch và nhất quán. Nếu bộ phận báo cáo và bộ phận xây dựng mô hình tự xử lý dữ liệu theo những cách riêng, cùng một câu hỏi có thể cho ra hai con số khác nhau. Kho dữ liệu chính là lời giải cho vấn đề này: dữ liệu được làm sạch, chuẩn hóa và tổ chức theo mô hình chiều một lần, sau đó phục vụ đồng thời cho các truy vấn OLAP, dashboard và các thuật toán khai phá.

Bộ dữ liệu MovieLens 1M do nhóm nghiên cứu GroupLens (Đại học Minnesota) công bố [1], [2] là lựa chọn phù hợp cho mục đích học tập: dữ liệu có quy mô vừa đủ lớn (hơn một triệu lượt đánh giá), có đủ các chiều phân tích (người dùng, phim, thể loại, thời gian) và có đặc điểm thách thức về mặt thiết kế như một phim thuộc nhiều thể loại. Vì vậy, nhóm lựa chọn đề tài “Xây dựng kho dữ liệu và khai phá dữ liệu đánh giá phim MovieLens 1M” làm bài tập lớn cuối kỳ.

## 2. Mục tiêu và câu hỏi nghiên cứu

Mục tiêu chung của đề tài là xây dựng một hệ thống phân tích hoàn chỉnh từ dữ liệu gốc tới kết quả trực quan: dữ liệu được nạp vào kho có kiểm soát, được đối soát đầy đủ, sau đó dùng chung cho phân tích OLAP, dashboard và khai phá dữ liệu. Cụ thể, đề tài hướng tới trả lời ba câu hỏi nghiên cứu sau:

- **Q1 – Phân cụm:** Người dùng có thể được chia thành những nhóm sở thích thể loại nào, và cơ cấu tuổi, giới tính của các nhóm khác nhau ra sao?
- **Q2 – Gợi ý:** Có thể gợi ý 5 phim phù hợp cho một người dùng dựa trên lịch sử đánh giá như thế nào, và chất lượng gợi ý so với phương pháp gợi ý theo độ phổ biến ra sao?
- **Q3 – Xu hướng:** Số lượt đánh giá theo từng thể loại biến động như thế nào qua các quý trong giai đoạn dữ liệu được thu thập?

Bảng 0.2 tóm tắt phương pháp và sản phẩm tương ứng với từng câu hỏi.

@table Bảng 0.2. Câu hỏi nghiên cứu, phương pháp và sản phẩm
@widths 1.6,5.4,4.5,4.5
| Câu hỏi | Nội dung | Phương pháp | Sản phẩm |
| Q1 | Nhóm sở thích và cơ cấu tuổi, giới tính | Vector tỷ lệ thể loại từ đánh giá tích cực, phân cụm K-Means | Bốn cụm người dùng, dashboard Sở thích |
| Q2 | Gợi ý Top-5 phim | Item-based CF so sánh với Popularity Baseline, chia dữ liệu theo thời gian | Bảng đánh giá Precision@5, Recall@5; công cụ gợi ý dòng lệnh |
| Q3 | Biến động đánh giá theo thể loại và quý | Truy vấn OLAP: roll-up, drill-down, tăng trưởng QoQ, tỷ trọng | Sáu truy vấn OLAP, dashboard Xu hướng |

## 3. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu** gồm: (i) các kỹ thuật xây dựng kho dữ liệu theo mô hình chiều và quy trình ETL; (ii) các phép phân tích OLAP; (iii) thuật toán phân cụm K-Means và thuật toán lọc cộng tác dựa trên sản phẩm cùng phương pháp đánh giá hệ gợi ý.

**Phạm vi dữ liệu** là bộ MovieLens 1M gồm 6.040 người dùng, 3.883 phim và 1.000.209 lượt đánh giá trong khoảng từ 25/04/2000 đến 28/02/2003. Mỗi lượt đánh giá là số sao (từ 1 đến 5) mà một người dùng chấm cho một bộ phim tại một thời điểm. Dữ liệu không chứa lượt xem, thời lượng xem hay doanh thu, vì vậy mọi kết luận trong báo cáo đều được diễn đạt theo “số lượt đánh giá” và “điểm đánh giá”, không suy rộng sang hành vi xem phim hay nhu cầu thị trường hiện nay.

**Phạm vi công nghệ** gồm hệ quản trị cơ sở dữ liệu PostgreSQL cho kho dữ liệu, ngôn ngữ Python cho ETL và khai phá dữ liệu, và Apache Superset cho dashboard. Đề tài không bao gồm khai phá luật kết hợp, học sâu, xử lý dữ liệu luồng và nạp dữ liệu tăng dần.

## 4. Phương pháp thực hiện

Đề tài được thực hiện theo quy trình gồm các bước chính:

- Khảo sát và phân tích khám phá dữ liệu (EDA) để hiểu cấu trúc, chất lượng và đặc điểm phân bố của dữ liệu.
- Thiết kế kho dữ liệu theo phương pháp Kimball [3]: xác định quy trình nghiệp vụ, mức chi tiết (grain), các bảng chiều và bảng sự kiện.
- Xây dựng quy trình ETL bằng Python, nạp dữ liệu trong một giao dịch duy nhất và đối soát kết quả trước khi xác nhận.
- Viết sáu truy vấn OLAP và dựng ba dashboard trên Apache Superset.
- Xây dựng đặc trưng, thực nghiệm K-Means với nhiều cấu hình, xây dựng mô hình item-based CF và đánh giá trên dữ liệu chia theo thời gian.
- Kiểm thử tự động, đối chiếu kết quả giữa SQL, dashboard và mô hình; tổng hợp và diễn giải kết quả.

Mã nguồn được quản lý trên GitHub, mỗi chức năng được phát triển trên một nhánh riêng và hợp nhất qua pull request sau khi được rà soát chéo giữa hai thành viên.

## 5. Phân công công việc

@table Bảng 0.3. Phân công công việc trong nhóm
@widths 3.5,12.5
| Thành viên | Nội dung phụ trách |
| Thành viên 1 | Thiết kế kho dữ liệu (lược đồ, ràng buộc, chỉ mục); xây dựng ETL và đối soát; sáu truy vấn OLAP; ba dashboard Superset; sao lưu, phục hồi; tích hợp và tổng hợp báo cáo |
| Thành viên 2 | Khảo sát và phân tích khám phá dữ liệu; xây dựng đặc trưng; thực nghiệm K-Means; xây dựng item-based CF và Popularity Baseline; thiết kế giao thức đánh giá; công cụ gợi ý dòng lệnh |

Hai thành viên cùng thống nhất một “hợp đồng dữ liệu” chung (tên bảng, kiểu dữ liệu, thứ tự cột, quy ước thời gian) ngay từ đầu, nhờ đó phần kho dữ liệu và phần khai phá có thể phát triển song song mà vẫn khớp nhau khi tích hợp.

## 6. Bố cục báo cáo

Ngoài phần Mở đầu, Kết luận, Tài liệu tham khảo và Phụ lục, báo cáo gồm bốn chương:

- **Chương 1. Cơ sở lý thuyết:** trình bày các khái niệm về kho dữ liệu, mô hình chiều, ETL, OLAP, thuật toán K-Means, lọc cộng tác và các chỉ số đánh giá.
- **Chương 2. Phân tích dữ liệu và thiết kế kho dữ liệu:** mô tả bộ dữ liệu, kết quả phân tích khám phá, kiến trúc hệ thống và thiết kế chi tiết kho dữ liệu.
- **Chương 3. Xây dựng ETL, OLAP và dashboard:** trình bày quá trình nạp dữ liệu, đối soát, sáu truy vấn OLAP, kết quả trả lời câu hỏi Q3 và ba dashboard.
- **Chương 4. Khai phá dữ liệu:** trình bày thực nghiệm phân cụm người dùng (Q1) và hệ gợi ý phim (Q2) cùng các kết quả đánh giá.
