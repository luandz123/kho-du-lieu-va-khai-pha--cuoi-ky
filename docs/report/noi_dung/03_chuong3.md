@chapter CHƯƠNG 3. XÂY DỰNG ETL, OLAP VÀ DASHBOARD

Chương này trình bày quá trình hiện thực kho dữ liệu: quy trình ETL và đối soát, sáu truy vấn OLAP cùng kết quả trả lời câu hỏi Q3, ba dashboard trên Apache Superset, cơ chế sao lưu phục hồi và kiểm thử.

## 3.1. Môi trường triển khai

Hệ thống được triển khai trên máy tính cá nhân chạy Windows. PostgreSQL 17 chạy trực tiếp trên máy, chứa cơ sở dữ liệu riêng của dự án. Mã ETL và khai phá viết bằng Python 3.12, chạy trong môi trường ảo (virtual environment) với các thư viện được ghim phiên bản trong tệp `requirements.txt`. Apache Superset 6.1.0 chạy trong container Docker riêng, có cơ sở dữ liệu metadata riêng, và kết nối tới kho dữ liệu bằng một tài khoản chỉ có quyền đọc. Thông tin kết nối và mật khẩu được lưu trong tệp `.env` cục bộ, không đưa lên Git.

Để kiểm tra khả năng tái lập, thành viên thứ hai đã dựng lại toàn bộ kho dữ liệu và chạy lại phần khai phá trên một máy Windows khác (Python 3.12.6, PostgreSQL 17.4) từ mã nguồn trên GitHub; kết quả bốn bảng dữ liệu và kết quả phân cụm trùng khớp hoàn toàn với máy thứ nhất.

## 3.2. Quy trình ETL

### 3.2.1. Tổng quan

Toàn bộ quy trình nạp được chạy bằng một lệnh duy nhất `python -m etl.run_etl refresh` và gồm sáu bước như Hình 3.1. Điểm quan trọng nhất là **cả sáu bước nằm trong một giao dịch duy nhất**: kho dữ liệu chỉ chuyển sang trạng thái mới khi mọi kiểm tra đều đạt; nếu có bất kỳ lỗi nào, toàn bộ thay đổi bị hủy và kho giữ nguyên dữ liệu cũ.

@fig figures/quy_trinh_etl.png | Hình 3.1. Quy trình ETL nạp toàn bộ trong một giao dịch | 15.5

### 3.2.2. Trích xuất và nạp vùng staging

Trước khi đọc, chương trình kiểm tra mã băm SHA-256 của ba tệp nguồn so với tệp kê khai. Mỗi dòng được giải mã Latin-1, tách theo chuỗi `::` và kiểm tra đủ số trường. Dữ liệu được nạp vào ba bảng staging bằng lệnh `COPY` của PostgreSQL ở dạng văn bản, kèm số thứ tự dòng trong tệp gốc (`source_line`). Nhờ giữ nguyên dạng văn bản, mọi lỗi ép kiểu hoặc sai miền giá trị đều được phát hiện ở bước biến đổi và có thể truy ngược về đúng dòng trong tệp nguồn.

### 3.2.3. Biến đổi và nạp kho dữ liệu

Các bảng được nạp theo thứ tự bảo đảm ràng buộc khóa ngoại:

- **Bốn bảng chiều:** `dim_user` (ánh xạ mã tuổi sang nhãn), `dim_movie` (tách năm phát hành), `dim_genre` (18 thể loại) và `dim_date` (lịch ngày liên tục theo UTC).
- **Bảng cầu nối:** tách chuỗi thể loại của từng phim, tra khóa phim và khóa thể loại, thu được 6.408 cặp.
- **Bảng sự kiện:** với mỗi lượt đánh giá, tra khóa người dùng, khóa phim và khóa ngày UTC, thu được 1.000.209 dòng. Bảng sự kiện **không nối với thể loại** trong quá trình nạp, nên số dòng luôn bằng số lượt đánh giá nguồn.

Trước khi nạp lại, chương trình xóa dữ liệu cũ theo một danh sách bảng được liệt kê tường minh (không dùng `DROP ... CASCADE`), đồng thời đánh dấu kết quả phân cụm hiện có là không còn hợp lệ.

### 3.2.4. Đối soát trước khi xác nhận giao dịch

Bước đối soát được thực hiện **trên chính kết nối đang mở giao dịch**, trước lệnh `COMMIT`. Đây là chi tiết kỹ thuật quan trọng: một kết nối khác không thể nhìn thấy dữ liệu chưa được xác nhận, nên việc kiểm tra bằng một chương trình bên ngoài sau khi nạp không thể ngăn dữ liệu sai được ghi vào kho. Các chỉ số được đối soát gồm: số dòng từng bảng, tổng điểm, phân bố số sao, số người dùng và số phim có đánh giá, mốc thời gian sớm nhất và muộn nhất, tính duy nhất của khóa và mã băm SHA-256 của bốn khung nhìn chuẩn. Kết quả đối soát được trình bày trong Bảng 3.1.

@table Bảng 3.1. Kết quả đối soát sau khi nạp kho dữ liệu
@widths 7,9
| Chỉ tiêu | Kết quả |
| Số người dùng / phim / cặp phim – thể loại | 6.040 / 3.883 / 6.408 |
| Số lượt đánh giá | 1.000.209 |
| Tổng điểm đánh giá | 3.582.313 |
| Người dùng / phim có đánh giá | 6.040 / 3.706 |
| Phân bố 1 → 5 sao | 56.174 / 107.557 / 261.197 / 348.971 / 226.310 |
| Khoảng thời gian (UTC) | 25/04/2000 23:05:32 – 28/02/2003 17:49:50 |
| Mã băm bốn khung nhìn chuẩn | Khớp với dữ liệu đọc trực tiếp từ tệp nguồn |

Quy trình được chạy hai lần liên tiếp trên cùng mã nguồn và cấu hình; cả hai lần đều cho kết quả đối soát giống hệt nhau. Nhóm cũng xây dựng các bộ dữ liệu thử nhỏ có lỗi cố ý (dòng sai định dạng, số sao ngoài miền, cặp trùng, thiếu khóa tham chiếu) để kiểm chứng rằng mỗi loại lỗi đều làm giao dịch bị hủy và dữ liệu cũ được giữ nguyên.

## 3.3. Sáu truy vấn OLAP

### 3.3.1. Tổng quan

Sáu truy vấn OLAP được xây dựng dưới dạng sáu khung nhìn trong schema `analytics` (tệp `database/views.sql`) và các câu truy vấn có tham số lọc (tệp `olap/queries.sql`). Bảng 3.2 tóm tắt nội dung và kết quả tiêu biểu.

@table Bảng 3.2. Sáu truy vấn OLAP và kết quả tiêu biểu
@widths 1.3,5.2,4,5.5
| Mã | Nội dung | Thao tác OLAP | Kết quả tiêu biểu |
| O1 | KPI tổng quan toàn hệ thống | Tổng hợp toàn bộ | 1.000.209 lượt; điểm trung bình 3,5816 |
| O2 | Top 10 phim theo số lượt đánh giá | Xếp hạng | American Beauty dẫn đầu với 3.428 lượt |
| O3 | Điểm trung bình theo thể loại × nhóm tuổi × giới tính | Slice, dice, pivot | 18 × 7 = 126 ô cho mỗi lát giới tính |
| O4 | Số lượt theo năm → quý → tháng | Roll-up, drill-down | 4 năm, 12 quý, 35 tháng; tổng mỗi cấp đều bằng 1.000.209 |
| O5 | Số lượt, tỷ trọng và QoQ theo thể loại × quý | Phân tích xu hướng | 18 × 12 = 216 ô; 156 ô đủ điều kiện xếp hạng |
| O6 | Lọc kết hợp thể loại, tuổi, giới, thời kỳ; chi tiết tháng × phim | Dice, drill-down | Comedy, tuổi 18–24, nửa cuối năm 2000: 53.541 lượt |

Mọi điểm trung bình trong các khung nhìn đều được tính bằng **tổng điểm chia tổng số lượt** và các khung nhìn lưu sẵn cả hai đại lượng này, để khi người dùng gộp nhiều nhóm lại, kết quả vẫn là trung bình có trọng số chính xác.

### 3.3.2. KPI tổng quan và Top 10 phim (O1, O2)

Truy vấn O1 cho thấy toàn bộ 6.040 người dùng và 3.706 trên 3.883 phim có ít nhất một lượt đánh giá, với điểm trung bình 3,5816. Truy vấn O2 xếp hạng phim theo số lượt đánh giá giảm dần, khi bằng nhau thì xét điểm trung bình giảm dần rồi mã phim tăng dần để kết quả luôn xác định. Kết quả được trình bày trong Bảng 3.3.

@table Bảng 3.3. Mười phim được đánh giá nhiều nhất (truy vấn O2)
@widths 1.2,8.6,3.2,3
| STT | Tên phim | Số lượt | Điểm TB |
| 1 | American Beauty (1999) | 3.428 | 4,32 |
| 2 | Star Wars: Episode IV – A New Hope (1977) | 2.991 | 4,45 |
| 3 | Star Wars: Episode V – The Empire Strikes Back (1980) | 2.990 | 4,29 |
| 4 | Star Wars: Episode VI – Return of the Jedi (1983) | 2.883 | 4,02 |
| 5 | Jurassic Park (1993) | 2.672 | 3,76 |
| 6 | Saving Private Ryan (1998) | 2.653 | 4,34 |
| 7 | Terminator 2: Judgment Day (1991) | 2.649 | 4,06 |
| 8 | Matrix, The (1999) | 2.590 | 4,32 |
| 9 | Back to the Future (1985) | 2.583 | 3,99 |
| 10 | Silence of the Lambs, The (1991) | 2.578 | 4,35 |

Mười phim này đều có điểm trung bình cao hơn mức chung 3,58, trong đó bộ ba Star Wars chiếm ba vị trí liền nhau. Điều này cho thấy các phim được nhiều người đánh giá thường cũng được đánh giá tốt, một đặc điểm giải thích vì sao gợi ý theo độ phổ biến là một mô hình cơ sở khá mạnh (xem chương 4).

### 3.3.3. Phân tích thể loại theo nhóm tuổi và giới tính (O3)

Khung nhìn O3 có grain thể loại × nhóm tuổi × giới tính. Vì một phim thuộc nhiều thể loại, mỗi lượt đánh giá đóng góp vào tất cả các thể loại của phim đó; đây là số lượt gắn thể loại chứ không phải số lượt đánh giá duy nhất. Từ khung nhìn này có thể thực hiện:

- **Slice:** cố định giới tính nữ (F) để xem điểm trung bình của 18 thể loại theo 7 nhóm tuổi.
- **Dice:** chọn đồng thời giới tính F, nhóm tuổi 18–24 và hai thể loại Comedy, Drama. Kết quả: Comedy có 19.136 lượt với điểm trung bình 3,42; Drama có 15.977 lượt với điểm trung bình 3,63. Như vậy, trong nhóm này Comedy được đánh giá nhiều hơn nhưng Drama được chấm điểm cao hơn.
- **Pivot:** xoay nhóm tuổi thành cột và thể loại thành hàng, tạo bảng 18 hàng × 7 cột để so sánh trực quan.

### 3.3.4. Roll-up và drill-down theo thời gian (O4)

Khung nhìn O4 dùng toán tử `GROUPING SETS` để tính đồng thời ba cấp tổng hợp năm, quý, tháng trong một truy vấn. Khung nhìn xuất phát từ bảng `dim_date` và nối trái (`LEFT JOIN`) với bảng sự kiện, nhờ đó các kỳ không có lượt đánh giá vẫn xuất hiện với giá trị 0:

@code
CREATE VIEW analytics.v_olap_time_rollup AS
SELECT CASE WHEN GROUPING(d.month_number) = 0 THEN 'month'
            WHEN GROUPING(d.quarter_number) = 0 THEN 'quarter'
            ELSE 'year' END AS time_level,
       d.calendar_year, d.quarter_number, d.month_number,
       count(f.rating_key) AS rating_count,
       COALESCE(sum(f.rating), 0) AS rating_sum,
       sum(f.rating)::numeric / NULLIF(count(f.rating_key), 0) AS mean_rating
FROM dw.dim_date d LEFT JOIN dw.fact_rating f ON f.date_key = d.date_key
GROUP BY GROUPING SETS ((d.calendar_year),
                        (d.calendar_year, d.quarter_number),
                        (d.calendar_year, d.quarter_number, d.month_number));
@endcode

Kết quả gồm 51 dòng (4 năm, 12 quý, 35 tháng). Tổng số lượt ở mỗi cấp đều bằng đúng 1.000.209; đây là một phép kiểm tra tính nhất quán của roll-up. Lưu ý không được cộng cả 51 dòng với nhau, vì mỗi lượt đánh giá có mặt ở cả ba cấp.

### 3.3.5. Trả lời câu hỏi Q3: xu hướng đánh giá theo thể loại và quý (O5)

Khung nhìn O5 tính cho mỗi thể loại g và mỗi quý t ba đại lượng: số lượt gắn thể loại n(g, t), tỷ trọng của thể loại trong quý và tăng trưởng QoQ. Để kết quả đúng, khung nhìn được xây dựng theo bốn nguyên tắc:

- **Lưới đầy đủ:** tạo đủ 18 thể loại × 12 quý (216 ô), những ô không có dữ liệu được điền 0 **trước khi** dùng hàm cửa sổ `LAG` để lấy giá trị quý trước. Nếu bỏ qua bước này, quý trước của một ô có thể bị lấy nhầm thành quý có dữ liệu gần nhất chứ không phải quý liền kề.
- **Mẫu số rõ ràng:** tỷ trọng = n(g, t) chia tổng lượt gắn của mọi thể loại trong cùng quý; QoQ có mẫu số là số lượt quý trước, nếu bằng 0 thì trả về rỗng (N/A).
- **Ngưỡng tin cậy:** chỉ xếp hạng tăng trưởng khi quý trước có ít nhất 100 lượt, tránh trường hợp tăng từ 2 lên 6 lượt được coi là “tăng 200%”.
- **Loại quý biên:** không xếp hạng các quý 2000Q2, 2003Q1 và quý ngay sau quý biên, vì chúng không chứa dữ liệu trọn quý.

Bảng 3.4 trình bày thể loại xếp hạng cao nhất về QoQ trong mỗi quý đủ điều kiện.

@table Bảng 3.4. Thể loại có QoQ cao nhất trong từng quý đủ điều kiện xếp hạng
@widths 2.2,2.8,2.6,2.6,2.6,3.2
| Quý | Thể loại | Quý trước | Quý này | QoQ (%) | Tỷ trọng (%) |
| 2000Q4 | Animation | 13.102 | 20.068 | +53,17 | 2,12 |
| 2001Q1 | Animation | 20.068 | 1.715 | −91,45 | 2,71 |
| 2001Q2 | Comedy | 11.975 | 5.812 | −51,47 | 19,92 |
| 2001Q3 | Western | 179 | 189 | +5,59 | 0,78 |
| 2001Q4 | Film-Noir | 159 | 151 | −5,03 | 0,93 |
| 2002Q1 | Horror | 514 | 697 | +35,60 | 4,39 |
| 2002Q2 | Musical | 306 | 268 | −12,42 | 2,20 |
| 2002Q3 | Thriller | 1.007 | 1.004 | −0,30 | 9,76 |
| 2002Q4 | Romance | 733 | 711 | −3,00 | 8,88 |

Từ kết quả này có thể rút ra các nhận xét trả lời câu hỏi Q3:

- Hoạt động đánh giá tăng mạnh trong năm 2000, đạt đỉnh ở quý 4 với 446.574 lượt, rồi giảm đột ngột còn 32.223 lượt ở quý 1 năm 2001 (giảm 92,8%) và tiếp tục giảm dần tới cuối giai đoạn. Do đó, phần lớn thể loại đều có QoQ âm từ năm 2001.
- Animation là thể loại tăng trưởng mạnh nhất quý 4 năm 2000 (+53,17%). Đáng chú ý, ở quý 1 năm 2001 Animation vẫn đứng hạng 1 dù QoQ là −91,45%: điều đó có nghĩa là Animation **giảm ít nhất** trong khi mọi thể loại khác đều giảm mạnh hơn. Nếu chỉ nhìn thứ hạng mà gọi đây là “thể loại tăng trưởng cao nhất” sẽ là một diễn giải sai.
- Trong các quý từ năm 2001, chỉ có Western (2001Q3) và Horror (2002Q1) đạt tăng trưởng dương. Western tăng từ một nền rất nhỏ (179 lên 189 lượt), nên mức tăng này ít ý nghĩa thống kê.
- Tỷ trọng cho thấy cơ cấu thể loại ổn định hơn nhiều so với số lượt tuyệt đối. Ví dụ ở quý 2 năm 2001, dù số lượt giảm 51,47%, Comedy vẫn chiếm 19,92% tổng lượt gắn thể loại; vì vậy khi phân tích xu hướng cần đọc đồng thời số lượt, QoQ và tỷ trọng.

Các kết quả trên mô tả **hoạt động gửi đánh giá trong bộ dữ liệu**. Sự sụt giảm sau năm 2000 nhiều khả năng phản ánh cách dữ liệu được thu thập (phần lớn người dùng tham gia trong năm 2000) chứ không phải sự thay đổi nhu cầu xem phim; vì vậy nhóm không suy rộng các con số này thành xu hướng thị trường.

### 3.3.6. Lọc kết hợp và chi tiết theo phim (O6)

Truy vấn O6 cho phép lọc đồng thời theo danh sách thể loại, nhóm tuổi, giới tính và khoảng thời gian, sau đó đi sâu tới từng tháng và từng phim. Khi chọn nhiều thể loại, truy vấn dùng điều kiện `EXISTS` trên bảng cầu nối thay vì phép nối, để một lượt đánh giá cho phim thuộc cả hai thể loại được chọn chỉ được đếm một lần. Với bộ lọc thể loại Comedy, nhóm tuổi 18–24, thời kỳ từ 01/07/2000 đến hết năm 2000, kết quả gồm 5.032 dòng tháng × phim, tổng cộng 53.541 lượt và tổng điểm 185.726 (điểm trung bình 3,47); con số này khớp với một truy vấn độc lập trực tiếp trên bảng sự kiện.

## 3.4. Dashboard trên Apache Superset

Ba dashboard được xây dựng trên Apache Superset, mỗi dashboard dùng các tập dữ liệu (dataset) được định nghĩa bằng SQL trên các khung nhìn của kho. Mỗi dataset được ghi rõ grain, thước đo và phạm vi tác động của từng bộ lọc.

### 3.4.1. Dashboard Tổng quan

Dashboard Tổng quan (Hình 3.2) hiển thị các KPI: tổng số lượt đánh giá, điểm trung bình, số người dùng và số phim có đánh giá, số phim trong danh mục, tổng điểm; bảng Top 10 phim và biểu đồ phân bố số sao. Bộ lọc thời gian được áp dụng trên dữ liệu đánh giá trước khi tổng hợp, nên mọi biểu đồ thay đổi theo khoảng thời gian được chọn; riêng KPI “phim trong danh mục” luôn là 3.883 vì không phụ thuộc thời gian.

@fig ../../dashboard/overview/evidence/all_history_charts.jpg | Hình 3.2. Dashboard Tổng quan trên toàn bộ giai đoạn dữ liệu | 15.5

### 3.4.2. Dashboard Xu hướng

Dashboard Xu hướng (Hình 3.3) trả lời câu hỏi Q3, gồm biểu đồ số lượt đánh giá theo quý của toàn hệ thống, biểu đồ QoQ và bảng tỷ trọng theo thể loại. Bộ lọc thể loại chỉ tác động lên các biểu đồ theo thể loại, không làm thay đổi biểu đồ tổng toàn hệ thống. Bộ lọc quý chỉ chọn các quý hiển thị sau khi QoQ đã được tính trên chuỗi đầy đủ, nên quý đầu tiên trong vùng chọn vẫn có giá trị QoQ chính xác.

@fig ../../dashboard/trends/evidence/three_genres_qoq.jpg | Hình 3.3. Dashboard Xu hướng với ba thể loại Animation, Horror, Western | 15.5

### 3.4.3. Dashboard Sở thích

Dashboard Sở thích (Hình 3.4) trình bày kết quả phân cụm của câu hỏi Q1: số người dùng trong mỗi cụm, bản đồ nhiệt (heatmap) tỷ lệ thể loại của từng cụm và cơ cấu giới tính, nhóm tuổi của mỗi cụm so với toàn bộ người dùng. Dữ liệu người dùng và dữ liệu hồ sơ cụm được tách thành hai dataset ở hai grain khác nhau (một dòng mỗi người dùng; một dòng mỗi cụm × thể loại) để tránh đếm lặp người dùng. Ví dụ, khi lọc cụm 1, giới tính nữ, nhóm tuổi 25–34, dashboard hiển thị 170 người dùng, trong khi các chỉ số mốc so sánh (6.038 người được phân cụm, 2 người không đủ dữ liệu) vẫn được giữ cố định.

@fig ../../docs/P1/report/captures/20261024_preferences/all_kpis.jpg | Hình 3.4. Dashboard Sở thích hiển thị kết quả phân cụm | 15.5

### 3.4.4. Kiểm tra tính đúng của dashboard

Mỗi dashboard được đối chiếu với các truy vấn SQL độc lập trên nhiều tổ hợp bộ lọc. Ví dụ với dashboard Tổng quan: toàn bộ giai đoạn cho 1.000.209 lượt, quý 3 năm 2000 cho 324.864 lượt, quý 1 năm 2001 cho 32.223 lượt, đều khớp với kết quả SQL. Superset kết nối tới kho bằng tài khoản `movielens_bi_reader` chỉ có quyền `SELECT` trên các khung nhìn cần thiết, không có quyền ghi hay quản trị.

## 3.5. Sao lưu và phục hồi

Nhóm đã kiểm thử ba cơ chế sao lưu, phục hồi tách biệt cho ba loại tài sản khác nhau (Bảng 3.5).

@table Bảng 3.5. Các cơ chế sao lưu và phục hồi đã kiểm thử
@widths 4,5.5,6.5
| Cơ chế | Đối tượng | Kết quả kiểm thử |
| pg_dump / pg_restore | Toàn bộ kho dữ liệu: bảng, khung nhìn, kết quả phân cụm | Phục hồi vào cơ sở dữ liệu mới; bốn mã băm, số liệu OLAP và trạng thái mô hình khớp bản gốc |
| Sao lưu metadata Superset | Cơ sở dữ liệu cấu hình của Superset | Phục hồi sang một instance Superset riêng; đăng nhập, kết nối, bố cục và bộ lọc hoạt động đúng |
| Xuất / nhập dashboard (ZIP) | Ba dashboard cùng dataset và biểu đồ | Nhập vào instance mới; bố cục được khôi phục bổ sung qua REST API |

## 3.6. Kiểm thử tự động

Mã nguồn đi kèm 225 ca kiểm thử tự động: 135 ca cho phần kho dữ liệu (ETL, đối soát, OLAP, nạp kết quả phân cụm, sao lưu phục hồi) và 90 ca cho phần khai phá (đọc dữ liệu, đặc trưng, phân cụm, chia dữ liệu, mô hình gợi ý, đánh giá). Phần lớn ca kiểm thử dùng bộ dữ liệu nhỏ tự tạo, trong đó có các trường hợp biên như phim nhiều thể loại, quý không có dữ liệu, quý trước bằng 0, hai nhóm có quy mô chênh lệch (để phát hiện lỗi lấy trung bình của trung bình) và các dòng dữ liệu lỗi cố ý.

## 3.7. Kết luận chương 3

Chương 3 đã hiện thực kho dữ liệu với quy trình ETL nạp toàn bộ trong một giao dịch, đối soát đầy đủ trước khi xác nhận và cho kết quả lặp lại giống hệt nhau qua nhiều lần chạy và trên hai máy khác nhau. Sáu truy vấn OLAP minh họa đầy đủ các thao tác roll-up, drill-down, slice, dice và pivot. Kết quả truy vấn O5 trả lời câu hỏi Q3: hoạt động đánh giá tập trung mạnh trong năm 2000 rồi giảm sâu, Animation là thể loại tăng mạnh nhất quý 4 năm 2000, và thứ hạng tăng trưởng phải luôn được đọc kèm dấu và giá trị tuyệt đối. Ba dashboard Superset được đối chiếu với SQL độc lập và truy cập kho bằng tài khoản chỉ đọc.
