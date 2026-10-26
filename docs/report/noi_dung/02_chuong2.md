@chapter CHƯƠNG 2. PHÂN TÍCH DỮ LIỆU VÀ THIẾT KẾ KHO DỮ LIỆU

Chương này mô tả bộ dữ liệu MovieLens 1M, các kết quả phân tích khám phá dữ liệu (EDA) có ảnh hưởng tới thiết kế, kiến trúc tổng thể của hệ thống và thiết kế chi tiết kho dữ liệu.

## 2.1. Bộ dữ liệu MovieLens 1M

### 2.1.1. Nguồn và cấu trúc dữ liệu

MovieLens là dự án nghiên cứu về hệ gợi ý của nhóm GroupLens tại Đại học Minnesota; các bộ dữ liệu của dự án được sử dụng rộng rãi trong nghiên cứu và giảng dạy [1]. Bộ MovieLens 1M [2] gồm ba tệp văn bản, mỗi dòng là một bản ghi, các trường được phân tách bởi chuỗi `::` và mã hóa theo Latin-1:

- `users.dat`: thông tin người dùng gồm mã người dùng, giới tính, mã nhóm tuổi, mã nghề nghiệp và mã bưu chính.
- `movies.dat`: thông tin phim gồm mã phim, tên phim kèm năm phát hành trong ngoặc, và danh sách thể loại phân tách bởi ký tự `|`.
- `ratings.dat`: các lượt đánh giá gồm mã người dùng, mã phim, số sao (1 đến 5) và thời điểm đánh giá dạng Unix timestamp (số giây tính từ 01/01/1970).

Để bảo đảm hai thành viên làm việc trên cùng một dữ liệu, mỗi máy tự tải bộ dữ liệu từ trang chính thức của GroupLens và kiểm tra mã băm SHA-256 của từng tệp theo một tệp kê khai (manifest) chung, thay vì chia sẻ dữ liệu qua Git. Sau khi đọc, dữ liệu được chuẩn hóa thành bốn bảng logic như trong Bảng 2.1.

@table Bảng 2.1. Quy mô các bảng dữ liệu sau chuẩn hóa
@widths 3.2,2.8,4,6
| Bảng | Số dòng | Khóa | Ý nghĩa |
| users | 6.040 | user_id | Hồ sơ người dùng |
| movies | 3.883 | movie_id | Danh mục phim |
| movie_genres | 6.408 | movie_id, genre_name | Cặp phim – thể loại sau khi tách chuỗi thể loại |
| ratings | 1.000.209 | user_id, movie_id | Lượt đánh giá |

Mã bưu chính không được sử dụng vì không phục vụ câu hỏi nghiên cứu nào. Mã nhóm tuổi được ánh xạ sang bảy nhãn: Under 18, 18-24, 25-34, 35-44, 45-49, 50-55 và 56+. Năm phát hành được tách từ cặp ngoặc cuối cùng trong tên phim. Thời điểm đánh giá được giữ cả hai dạng: Unix timestamp gốc và thời điểm theo giờ UTC.

### 2.1.2. Chất lượng dữ liệu

Kết quả kiểm tra chất lượng cho thấy dữ liệu MovieLens 1M khá sạch: không có giá trị thiếu ở các trường bắt buộc, mọi lượt đánh giá đều tham chiếu tới người dùng và phim có trong danh mục, số sao đều là số nguyên từ 1 đến 5, và **không có cặp (người dùng, phim) nào bị trùng**. Tuy vậy, nhóm không mặc định dữ liệu “sạch” mà đưa các điều kiện này thành ràng buộc trong kho dữ liệu, để mọi bất thường (nếu dữ liệu nguồn thay đổi) đều làm quá trình nạp thất bại thay vì bị bỏ qua.

## 2.2. Phân tích khám phá dữ liệu

### 2.2.1. Phân bố điểm đánh giá

Hình 2.1 cho thấy phân bố số sao lệch về phía điểm cao: mức 4 sao chiếm nhiều nhất với 348.971 lượt (34,9%), tiếp theo là 3 sao (26,1%) và 5 sao (22,6%); mức 1 sao chỉ chiếm 5,6%. Điểm trung bình toàn bộ dữ liệu là 3,58. Đặc điểm này là cơ sở để chọn ngưỡng **từ 4 sao trở lên** làm định nghĩa “đánh giá tích cực” trong cả hai bài toán khai phá: ngưỡng này đủ chặt để phản ánh sự yêu thích, đồng thời vẫn giữ được hơn một nửa số lượt đánh giá (57,5%).

@fig figures/phan_bo_sao.png | Hình 2.1. Phân bố số lượt đánh giá theo số sao | 12

### 2.2.2. Mức độ hoạt động của người dùng và phim

Mỗi người dùng trong bộ dữ liệu có ít nhất 20 lượt đánh giá. Số lượt đánh giá mỗi người có trung vị là 96 nhưng trung bình lên tới 165,6 và giá trị lớn nhất là 2.314, cho thấy phân bố lệch phải mạnh: một nhóm nhỏ người dùng rất tích cực đóng góp phần lớn dữ liệu. Tương tự, trong 3.706 phim có đánh giá, số lượt đánh giá mỗi phim có trung vị 123,5 trong khi phim được đánh giá nhiều nhất (American Beauty, 1999) có 3.428 lượt. Có **177 phim trong danh mục chưa từng được đánh giá**; vì vậy, kho dữ liệu cần phân biệt “số phim trong danh mục” (3.883) với “số phim có đánh giá” (3.706).

### 2.2.3. Đặc điểm nhân khẩu học

Hình 2.2 cho thấy người dùng nam chiếm 71,7% (4.331 người) và nhóm tuổi 25–34 đông nhất với 2.096 người (34,7%). Sự mất cân đối này cần được lưu ý khi mô tả các cụm người dùng ở chương 4: một cụm có tỷ lệ nam cao chưa chắc đã khác biệt, mà cần so sánh với tỷ lệ chung của toàn bộ người dùng.

@fig figures/nhan_khau_hoc.png | Hình 2.2. Phân bố người dùng theo nhóm tuổi và giới tính | 15

### 2.2.4. Thể loại phim

Dữ liệu có 18 thể loại. Drama (1.603 phim) và Comedy (1.200 phim) là hai thể loại phổ biến nhất, trong khi Film-Noir chỉ có 44 phim (Hình 2.3). Điểm đáng chú ý là **1.858 trong 3.883 phim (47,9%) thuộc từ hai thể loại trở lên**, có phim thuộc tới 6 thể loại. Đây là phát hiện quan trọng nhất đối với thiết kế: nếu nối trực tiếp bảng đánh giá với bảng thể loại rồi đếm, một lượt đánh giá cho phim thuộc ba thể loại sẽ bị đếm ba lần. Vì vậy, thiết kế kho dùng bảng cầu nối phim – thể loại và tách bạch hai đại lượng “số lượt đánh giá” và “số lượt gắn thể loại”.

@fig figures/phim_theo_the_loai.png | Hình 2.3. Số phim theo thể loại | 12

### 2.2.5. Phân bố theo thời gian

Các lượt đánh giá trải dài từ 25/04/2000 đến 28/02/2003 nhưng tập trung rất mạnh vào năm 2000: riêng quý 3 và quý 4 năm 2000 đã chiếm 77,1% tổng số lượt (Hình 2.4). Từ năm 2001, số lượt đánh giá mỗi quý giảm xuống chỉ còn vài nghìn tới vài chục nghìn. Hai quý đầu và cuối (2000Q2 và 2003Q1) không có dữ liệu trọn quý nên được đánh dấu là **quý biên** và loại khỏi việc xếp hạng tăng trưởng. Phân bố thời gian không đều này cũng ảnh hưởng trực tiếp tới cách chia dữ liệu huấn luyện và kiểm tra cho hệ gợi ý ở chương 4.

@fig figures/danh_gia_theo_quy.png | Hình 2.4. Số lượt đánh giá theo quý (giờ UTC) | 15

### 2.2.6. Tổng hợp các quyết định thiết kế rút ra từ EDA

@table Bảng 2.2. Kết quả khảo sát dữ liệu và quyết định thiết kế tương ứng
@widths 4.2,5,6.8
| Quan sát | Kết quả | Quyết định thiết kế |
| Cặp (người dùng, phim) trùng | 0 cặp | Ràng buộc UNIQUE trên bảng sự kiện |
| Miền giá trị số sao | Số nguyên 1..5 | Kiểu smallint, ràng buộc CHECK 1..5 |
| Phim nhiều thể loại | 1.858 phim, tối đa 6 thể loại | Bảng chiều thể loại và bảng cầu nối phim – thể loại |
| Phim chưa có đánh giá | 177 phim | Giữ đủ danh mục; tách KPI “phim trong danh mục” và “phim có đánh giá” |
| Người không có đánh giá ≥ 4 sao | 2 người | Gắn trạng thái “không đủ dữ liệu” trong bài toán phân cụm |
| Thời gian không đều, quý biên | 2000Q2 và 2003Q1 thiếu dữ liệu | Chuẩn hóa giờ UTC; đánh dấu quý biên trong phân tích QoQ |

## 2.3. Kiến trúc tổng thể của hệ thống

Hệ thống được tổ chức theo ba tầng như Hình 2.5. Ở **tầng dữ liệu**, dữ liệu MovieLens được trích xuất vào vùng staging, biến đổi và nạp vào kho dữ liệu theo lược đồ sao; kho cung cấp bốn khung nhìn (view) chuẩn làm giao diện dữ liệu chung cho phần khai phá. Ở **tầng phân tích và khai phá**, ba nhánh xử lý song song trả lời ba câu hỏi nghiên cứu: các truy vấn OLAP (Q3), phân cụm K-Means (Q1) và gợi ý Top-5 (Q2). Ở **tầng trình bày**, kết quả được hiển thị qua dashboard Apache Superset hoặc công cụ dòng lệnh.

@fig figures/kien_truc.png | Hình 2.5. Kiến trúc tổng thể của hệ thống | 15.5

Trong PostgreSQL, dữ liệu được chia thành ba schema có vai trò tách biệt:

- **staging:** ba bảng `users_raw`, `movies_raw`, `ratings_raw` lưu dữ liệu nguồn ở dạng văn bản kèm số thứ tự dòng trong tệp gốc, phục vụ truy vết lỗi.
- **dw:** bốn bảng chiều, một bảng cầu nối, một bảng sự kiện và bốn khung nhìn chuẩn cho phần khai phá.
- **analytics:** sáu khung nhìn OLAP và ba bảng lưu kết quả phân cụm để hiển thị trên dashboard.

Việc phần khai phá đọc dữ liệu qua bốn khung nhìn chuẩn thay vì đọc trực tiếp các bảng nội bộ giúp tách biệt hai phần: kho dữ liệu có thể thay đổi cấu trúc bên trong mà không ảnh hưởng tới mô hình, miễn là các khung nhìn giữ nguyên tên cột, kiểu dữ liệu và ý nghĩa.

## 2.4. Thiết kế kho dữ liệu

### 2.4.1. Quy trình nghiệp vụ và mức chi tiết

Theo phương pháp bốn bước của Kimball [3], nhóm lần lượt xác định:

- **Quy trình nghiệp vụ:** hoạt động người dùng đánh giá phim.
- **Mức chi tiết (grain):** **một dòng trong bảng sự kiện là một lượt đánh giá trong dữ liệu nguồn**, tức là một người dùng chấm điểm một bộ phim tại một thời điểm.
- **Các chiều:** người dùng (ai đánh giá), phim (đánh giá phim nào), ngày (đánh giá khi nào) và thể loại (phim thuộc thể loại gì).
- **Thước đo:** số sao đánh giá; số lượt đánh giá được tính bằng cách đếm dòng.

Việc chọn grain ở mức lượt đánh giá nguồn (thay vì mức lượt đánh giá × thể loại) bảo đảm tổng số dòng của bảng sự kiện luôn bằng đúng 1.000.209, và mọi phép tổng hợp toàn hệ thống đều chính xác mà không cần khử trùng lặp.

### 2.4.2. Lược đồ sao

Hình 2.6 trình bày lược đồ sao của kho dữ liệu. Bảng sự kiện `fact_rating` ở trung tâm nối với ba bảng chiều `dim_user`, `dim_movie`, `dim_date`. Chiều thể loại `dim_genre` liên kết với chiều phim qua bảng cầu nối `bridge_movie_genre`, không nối trực tiếp vào bảng sự kiện.

@fig figures/luoc_do_sao.png | Hình 2.6. Lược đồ sao của kho dữ liệu | 15.5

Mỗi bảng chiều có một **khóa thay thế (surrogate key)** dạng số nguyên tự tăng làm khóa chính, đồng thời giữ lại mã gốc của MovieLens (`user_id`, `movie_id`) với ràng buộc duy nhất. Khóa thay thế giúp kho độc lập với cách đánh mã của hệ thống nguồn, còn mã gốc cho phép đối chiếu với dữ liệu ban đầu và với phần khai phá. Bảng 2.3 mô tả chi tiết các bảng.

@table Bảng 2.3. Mô tả các bảng trong kho dữ liệu
@widths 3.8,3.6,8.6
| Bảng | Khóa chính | Thuộc tính và ràng buộc chính |
| dim_user | user_key | user_id duy nhất; gender ∈ {F, M}; age_group thuộc 7 nhãn; occupation 0..20 |
| dim_movie | movie_key | movie_id duy nhất; title; release_year (cho phép rỗng) |
| dim_date | date_key | full_date duy nhất; năm, quý, tháng, ngày là cột tính sẵn từ full_date |
| dim_genre | genre_key | genre_name duy nhất (18 giá trị) |
| bridge_movie_genre | (movie_key, genre_key) | Hai khóa ngoại tới dim_movie và dim_genre; mỗi cặp xuất hiện đúng một lần |
| fact_rating | rating_key | Khóa ngoại tới user, movie, date; rating 1..5; rating_timestamp và rated_at (UTC); UNIQUE (user_key, movie_key) |

### 2.4.3. Chiều thời gian

Bảng `dim_date` được sinh liên tục theo từng ngày từ ngày đánh giá sớm nhất tới muộn nhất (theo giờ UTC), kể cả những ngày không có lượt đánh giá nào. Nhờ đó, các báo cáo theo tháng hoặc quý vẫn hiển thị đầy đủ các kỳ có giá trị 0 thay vì bỏ trống. Các cột năm, quý, tháng, ngày được khai báo là cột sinh tự động (`GENERATED ALWAYS AS ... STORED`) từ cột `full_date`, nên không thể bị nhập sai lệch.

Toàn bộ thời gian được chuẩn hóa về giờ UTC. Nếu dùng múi giờ của máy chạy, một lượt đánh giá lúc 23 giờ UTC ngày cuối quý có thể bị tính sang quý sau khi chạy ở Việt Nam (UTC+7), khiến kết quả thay đổi theo máy. Để chặn lỗi này, bảng sự kiện có ràng buộc kiểm tra `rated_at` và `rating_timestamp` biểu diễn cùng một thời điểm, và dùng khóa ngoại kép `(date_key, rated_date)` tham chiếu tới `(date_key, full_date)`, bảo đảm mỗi lượt đánh giá trỏ đúng tới ngày UTC của nó.

### 2.4.4. Ràng buộc toàn vẹn và chỉ mục

Các quy tắc chất lượng phát hiện ở bước EDA được chuyển thành ràng buộc trong cơ sở dữ liệu: khóa chính, khóa ngoại, `NOT NULL`, `UNIQUE` cho cặp người dùng – phim, `CHECK` cho miền số sao, giới tính, nhóm tuổi và mã nghề nghiệp. Nhờ đó, dữ liệu vi phạm sẽ bị từ chối ngay khi nạp.

Ngoài các chỉ mục được tạo tự động bởi khóa chính và ràng buộc duy nhất, nhóm bổ sung bốn chỉ mục theo các đường truy cập phổ biến: `fact_rating(movie_key)` cho truy vấn theo phim; `fact_rating(date_key, movie_key)` và `fact_rating(rated_at)` cho truy vấn lọc theo thời gian; `bridge_movie_genre(genre_key, movie_key)` cho truy vấn đi từ thể loại sang phim.

Một đoạn định nghĩa bảng sự kiện trong tệp `database/schema.sql` như sau:

@code
CREATE TABLE dw.fact_rating (
    rating_key       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_key         integer NOT NULL REFERENCES dw.dim_user (user_key),
    movie_key        integer NOT NULL REFERENCES dw.dim_movie (movie_key),
    date_key         integer NOT NULL,
    rating           smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rating_timestamp bigint NOT NULL,
    rated_at         timestamptz NOT NULL,
    rated_date date GENERATED ALWAYS AS ((rated_at AT TIME ZONE 'UTC')::date) STORED,
    CONSTRAINT uq_fact_rating_user_movie UNIQUE (user_key, movie_key),
    CONSTRAINT ck_fact_rating_epoch
        CHECK (EXTRACT(EPOCH FROM rated_at) = rating_timestamp),
    CONSTRAINT fk_fact_rating_utc_day FOREIGN KEY (date_key, rated_date)
        REFERENCES dw.dim_date (date_key, full_date)
);
@endcode

## 2.5. Ánh xạ nguồn – đích

Bảng 2.4 tóm tắt cách mỗi trường nguồn được biến đổi trước khi vào kho dữ liệu.

@table Bảng 2.4. Ánh xạ dữ liệu từ nguồn vào kho
@widths 4.5,3.7,7.8
| Nguồn | Đích | Phép biến đổi và kiểm tra |
| users: id, giới tính, tuổi, nghề | dim_user | Ép kiểu số; ánh xạ mã tuổi sang 7 nhãn; giữ F/M và mã nghề; bỏ mã bưu chính |
| movies: id, tên phim | dim_movie | Giữ nguyên tên; tách năm trong ngoặc cuối, không khớp mẫu thì để rỗng |
| movies: thể loại | dim_genre, bridge | Tách chuỗi theo ký tự gạch đứng; kiểm tra tên thể loại hợp lệ và cặp không trùng |
| ratings: timestamp | dim_date, fact | Đổi Unix timestamp sang UTC; sinh lịch ngày liên tục |
| ratings: user, movie, rating | fact_rating | Tra đúng một khóa thay thế cho mỗi mã; kiểm tra miền 1..5 và tính duy nhất |

Mỗi phép tra khóa phải tìm thấy **đúng một** bản ghi tương ứng. Thiếu hoặc thừa đều được coi là lỗi và làm quá trình nạp dừng lại; nhóm không dùng phép nối trong (inner join) để âm thầm loại bỏ những dòng không khớp.

## 2.6. Bốn khung nhìn chuẩn cho phần khai phá

Kho dữ liệu cung cấp bốn khung nhìn `v_ml_users`, `v_ml_movies`, `v_ml_movie_genres` và `v_ml_ratings` với tên cột, kiểu dữ liệu và thứ tự cột cố định theo thỏa thuận giữa hai thành viên. Các khung nhìn trả về mã gốc của MovieLens thay vì khóa thay thế, nên mô hình khai phá không phụ thuộc vào lần nạp cụ thể của kho. Đặc biệt, khung nhìn `v_ml_ratings` **không nối với bảng thể loại**, nên mỗi lượt đánh giá chỉ xuất hiện đúng một lần; thông tin thể loại được lấy riêng từ `v_ml_movie_genres` khi cần.

Để kiểm chứng phần khai phá đọc dữ liệu từ kho cho kết quả giống hệt khi đọc trực tiếp từ tệp gốc, hai thành viên thống nhất một quy tắc xuất CSV chuẩn (UTF-8, xuống dòng LF, thứ tự cột và thứ tự dòng cố định, thời gian theo định dạng ISO 8601 UTC) và so sánh mã băm SHA-256 của bốn bảng. Kết quả cho thấy dữ liệu từ ba đường đọc (tệp gốc, CSV trung gian, kho dữ liệu) trùng khớp hoàn toàn.

## 2.7. Lưu trữ kết quả khai phá

Kết quả phân cụm của câu hỏi Q1 cần được hiển thị trên dashboard, nên được lưu vào schema `analytics` gồm ba bảng:

- `model_registry`: thông tin phiên bản mô hình (số cụm, hạt giống ngẫu nhiên, cách tiền xử lý, thư viện, mã băm dữ liệu đầu vào) và hai cờ trạng thái “đang dùng” (`is_active`) và “hợp lệ với dữ liệu hiện tại” (`is_valid_for_dw`).
- `user_cluster`: cụm của từng người dùng theo phiên bản mô hình; người không đủ dữ liệu có trạng thái `insufficient_evidence` và mã cụm rỗng.
- `cluster_genre_profile`: tỷ lệ trung bình của từng thể loại trong từng cụm.

Dashboard chỉ đọc qua hai khung nhìn lọc đúng phiên bản đang dùng và hợp lệ. Khi kho dữ liệu được nạp lại, mô hình cũ tự động bị đánh dấu không hợp lệ và chỉ được kích hoạt lại sau khi kiểm tra khớp với dữ liệu mới. Cơ chế này ngăn dashboard hiển thị kết quả phân cụm được tính từ một phiên bản dữ liệu khác.

## 2.8. Kết luận chương 2

Kết quả khảo sát cho thấy dữ liệu MovieLens 1M có chất lượng tốt nhưng có ba đặc điểm cần xử lý trong thiết kế: phim thuộc nhiều thể loại, phân bố thời gian không đều và phân bố người dùng lệch. Kho dữ liệu được thiết kế theo lược đồ sao với grain một lượt đánh giá, bảng cầu nối phim – thể loại, chiều thời gian chuẩn hóa UTC và hệ thống ràng buộc chặt chẽ. Bốn khung nhìn chuẩn và schema analytics là cầu nối giữa kho dữ liệu với phần khai phá và dashboard. Chương 3 trình bày việc hiện thực thiết kế này.
