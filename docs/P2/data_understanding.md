# Báo Cáo Phân Tích & Thấu Hiểu Dữ Liệu (Data Understanding) - MovieLens 1M
**Vai trò**: Người 2 (P2 - Khai phá dữ liệu & EDA)  
**Hợp đồng dữ liệu**: Phiên bản 2 (`docs/shared/data_contract.md` & `docs/shared/data_contract.json`)  
**Mốc bàn giao**: G1 (EDA, Adapter và Canonical Manifest)  
**Thời điểm hoàn thiện**: 2026-10-16  

---

## 1. Tổng Quan Bộ Dữ Liệu & Quy Trình Khám Phá

Tài liệu này cung cấp kết quả khảo sát toàn diện bộ dữ liệu MovieLens 1M được cung cấp chính thức bởi phòng nghiên cứu GroupLens thuộc Đại học Minnesota. Phân tích này phục vụ trực tiếp cho việc xây dựng Kho dữ liệu (Person 1) và hai bài toán khai phá dữ liệu (Person 2):
1. **Câu hỏi 1 (Q1)**: Phân cụm người dùng theo xu hướng sở thích thể loại phim bằng K-Means (Bước 8).
2. **Câu hỏi 2 (Q2)**: Hệ thống gợi ý Top 5 phim cá nhân hóa bằng Item-based Collaborative Filtering, đối sánh với Popularity Baseline theo chia tập thời gian (Bước 9 & 10).

### Nguồn gốc & Tính toàn vẹn tệp gốc
* URL tải chính thức: `https://files.grouplens.org/datasets/movielens/ml-1m.zip`
* Ngày tải UTC: `2026-10-15T10:40:34Z`
* Lưu trữ cục bộ tại: `data/raw/ml-1m/` (được cách ly khỏi Git theo đúng chính sách bảo mật).
* Mã băm SHA-256 byte và số dòng tệp nguồn được quản lý tại `data/source_manifest.json`:
  * `users.dat`: 6,040 dòng, 134,368 bytes, SHA-256: `1dc3a95300cb19f7c10e027daf29b8cdf1d908dab65b5edfb45950aa389a10a3`
  * `movies.dat`: 3,883 dòng, 171,308 bytes, SHA-256: `0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9`
  * `ratings.dat`: 1,000,209 dòng, 24,594,131 bytes, SHA-256: `506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f`
  * `README`: 170 dòng, 5,577 bytes, SHA-256: `2d5ddce86ccbd247207456165827b4b9ddf27282bca93807d4c763e28414f133`

---

## 2. Giới Hạn Nghiệp Vụ Của Dữ Liệu Nguồn (Business & Data Boundaries)

Để đảm bảo tính trung thực học thuật và tránh suy diễn sai lệch, các giới hạn sau của tập dữ liệu MovieLens 1M được xác định và đóng băng:
1. **Rating là điểm đánh giá, KHÔNG PHẢI lượt xem**: Dữ liệu chỉ ghi nhận phản hồi chủ động của người dùng (1 đến 5 sao), không thể hiện số lần xem hay người dùng có xem trọn vẹn bộ phim hay không.
2. **Timestamp là thời điểm đánh giá, KHÔNG PHẢI thời lượng xem**: Dữ liệu chỉ lưu giây Unix thời điểm người dùng gửi đánh giá trên hệ thống, không có thông tin thời lượng xem phim (watch duration/runtime).
3. **Không có đạo diễn, diễn viên hay tóm tắt nội dung**: Thuộc tính của phim chỉ gồm `movie_id`, `title` (chứa năm phát hành) và `genres`. Không bổ sung dữ liệu bên ngoài về diễn viên hay đạo diễn.
4. **Không có tuổi chính xác**: Độ tuổi được thu thập dưới dạng 7 nhóm tuổi phân loại (Under 18, 18-24, 25-34, 35-44, 45-49, 50-55, 56+). Không có ngày sinh hay tuổi nguyên thủy cụ thể.
5. **Mã bưu điện (Zip-code) bị loại bỏ**: Tuân thủ quy định Hợp đồng dữ liệu v2, mã ZIP bị loại bỏ hoàn toàn do không đồng nhất và không phục vụ mục tiêu khai phá.

---

## 3. Khảo Sát Chi Tiết Bốn Bảng Logic Chuẩn Hóa

### 3.1. Bảng `users` (6,040 bản ghi)
* **Schema**: `users(user_id int, gender text, age_group text, occupation int)`
* **Khóa chính**: `user_id` (duy nhất 100%, từ 1 đến 6,040).
* **Phân bố giới tính**:
  * Nam (`M`): 4,331 người (71.71%)
  * Nữ (`F`): 1,709 người (28.29%)
* **Phân bố 7 nhóm tuổi chuẩn hóa**:
  * `Under 18`: 222 người (3.68%)
  * `18-24`: 1,103 người (18.26%)
  * `25-34`: 2,096 người (34.70%) — *Nhóm nhân khẩu học chiếm tỷ trọng lớn nhất*
  * `35-44`: 1,193 người (19.75%)
  * `45-49`: 550 người (9.11%)
  * `50-55`: 496 người (8.21%)
  * `56+`: 380 người (6.29%)
* **Nghề nghiệp (`occupation`)**: Gồm đủ 21 mã nguồn nguyên thủy (0..20) theo MovieLens README.
* **Thứ tự sắp xếp**: `user_id` tăng dần (ASC).

### 3.2. Bảng `movies` (3,883 bản ghi) & `movie_genres` (6,408 liên kết)
* **Schema `movies`**: `movies(movie_id int, title text, release_year int nullable)`
* **Schema `movie_genres`**: `movie_genres(movie_id int, genre_name text)`
* **Khóa chính**: `movie_id` trên `movies`; `(movie_id, genre_name)` trên `movie_genres`.
* **Trích xuất năm phát hành (`release_year`)**:
  * 100% tiêu đề phim khớp biểu thức chính quy tách 4 chữ số trong ngoặc ở cuối chuỗi: `\((\d{4})\)$`.
  * Không có phim nào bị thiếu năm hoặc trích xuất thất bại.
  * Khoảng năm phát hành: từ năm 1919 đến năm 2000.
* **18 Thể loại gốc MovieLens 1M**:
  * Theo quyết định `[DEC-P2-007]`, thứ tự thể loại cho các vector đặc trưng và hồ sơ cụm được chuẩn hóa theo bảng chữ cái A–Z (`genre_order`):
    `Action`, `Adventure`, `Animation`, `Children's`, `Comedy`, `Crime`, `Documentary`, `Drama`, `Fantasy`, `Film-Noir`, `Horror`, `Musical`, `Mystery`, `Romance`, `Sci-Fi`, `Thriller`, `War`, `Western`.
  * Phân bố tần suất thể loại trên danh mục phim:
    * `Drama`: 1,603 phim (41.3%)
    * `Comedy`: 1,200 phim (30.9%)
    * `Action`: 503 phim (13.0%)
    * `Thriller`: 492 phim (12.7%)
    * `Romance`: 471 phim (12.1%)
    * `Horror`: 343 phim (8.8%)
    * `Adventure`: 283 phim (7.3%)
    * `Sci-Fi`: 276 phim (7.1%)
    * `Children's`: 251 phim (6.5%)
    * `Crime`: 211 phim (5.4%)
    * `War`: 143 phim (3.7%)
    * `Documentary`: 127 phim (3.3%)
    * `Musical`: 114 phim (2.9%)
    * `Mystery`: 106 phim (2.7%)
    * `Animation`: 105 phim (2.7%)
    * `Fantasy`: 68 phim (1.8%)
    * `Western`: 68 phim (1.8%)
    * `Film-Noir`: 44 phim (1.1%)
* **Phim đa thể loại (Multi-genre Movies)**:
  * 2,025 phim chỉ thuộc 1 thể loại.
  * 1,858 phim thuộc từ 2 đến 6 thể loại (trung bình 1.65 thể loại/phim).
  * **Ràng buộc kiến trúc sống còn**: Bảng `ratings` tuyệt đối KHÔNG được nối (JOIN) với `movie_genres` vì sẽ làm nhân bản dòng từ 1,000,209 lên hàng triệu bản ghi, phá vỡ tính đúng đắn của độ đo và phép tính tổng.
* **Phim chưa từng được đánh giá (Unrated Movies)**:
  * Trong danh mục 3,883 phim, có **3,706 phim** xuất hiện ít nhất 1 lần trong bảng đánh giá và **177 phim** hoàn toàn chưa từng nhận được đánh giá nào.
* **Thứ tự sắp xếp**:
  * `movies`: `movie_id` tăng dần (ASC).
  * `movie_genres`: `movie_id` ASC, sau đó `genre_name` ASC.

### 3.3. Bảng `ratings` (1,000,209 bản ghi)
* **Schema**: `ratings(user_id int, movie_id int, rating int, timestamp int64, rated_at UTC)`
* **Kiểm tra tính duy nhất khóa nghiệp vụ**:
  * **0 bản ghi trùng lặp cặp `(user_id, movie_id)`**.
  * Toàn bộ 1,000,209 bản ghi đều ứng với một cặp người dùng - bộ phim duy nhất. Người dùng chỉ đánh giá mỗi phim tối đa 1 lần.
  * Đủ điều kiện để Người 1 tạo ràng buộc `UNIQUE (user_id, movie_id)` trong DW.
* **Kiểm tra khóa ngoại & Toàn vẹn tham chiếu**:
  * 100% `user_id` tồn tại trong bảng `users`.
  * 100% `movie_id` tồn tại trong bảng `movies`. Không có bản ghi mồ côi.
* **Miền giá trị đánh giá (Rating Scale 1..5)**:
  * 100% giá trị rating là số nguyên nằm trong `[1, 5]`.
  * 1 sao: 56,174 lượt (5.62%)
  * 2 sao: 107,557 lượt (10.75%)
  * 3 sao: 261,197 lượt (26.11%)
  * 4 sao: 348,971 lượt (34.89%) — *Tần suất cao nhất*
  * 5 sao: 226,310 lượt (22.63%)
  * **Điểm đánh giá trung bình toàn hệ thống**: **3.5816** (độ lệch chuẩn 1.1171). Tỷ lệ đánh giá tích cực (rating >= 4) đạt **57.52%** (575,281 lượt).
* **Thời gian & Biên độ thời gian (`timestamp` & `rated_at`)**:
  * `timestamp` (Unix epoch seconds): min = 956,703,932, max = 1,046,454,590.
  * `rated_at` (chuỗi UTC ISO 8601): từ `2000-04-25T23:05:32Z` đến `2003-02-28T17:49:50Z` (gần 3 năm).
  * Thứ tự sắp xếp: `user_id` ASC, `movie_id` ASC, `timestamp` ASC, `rating` ASC.

---

## 4. Thống Kê Hành Vi Người Dùng & Phát Hiện Quan Trọng Cho Khai Phá

### 4.1. Mức độ tích cực của người dùng (Ratings per User)
* Theo cam kết của GroupLens, mỗi người dùng trong MovieLens 1M có ít nhất 20 đánh giá.
* Thống kê phân vị:
  * Min: 20 đánh giá
  * Phân vị 25% ($Q_1$): 44.0 đánh giá
  * Trung vị (Median): 96.0 đánh giá
  * Trung bình (Mean): 165.60 đánh giá
  * Phân vị 75% ($Q_3$): 208.0 đánh giá
  * Phân vị 90%: 400.0 đánh giá
  * Phân vị 95%: 556.0 đánh giá
  * Phân vị 99%: 906.7 đánh giá (chính xác: 906.66)
  * Max: 2,314 đánh giá

### 4.2. Phát hiện 2 người dùng thiếu bằng chứng tích cực (Insufficient Evidence)
* Bài toán phân cụm K-Means (Bước 8) xây dựng vector sở thích dựa trên các phim có đánh giá tích cực (rating $\ge$ 4).
* Qua khảo sát, có chính xác **2 người dùng** trong toàn bộ tập dữ liệu không có bất kỳ đánh giá nào $\ge 4$ (toàn bộ đánh giá đều từ 1 đến 3 sao): một người dùng có 65 đánh giá (điểm tối đa 2 sao) và một người dùng có 51 đánh giá (điểm tối đa 3 sao). Để tuân thủ quy định bảo vệ dữ liệu người dùng, danh sách User ID cụ thể được lưu trữ trong hồ sơ kiểm chứng cục bộ và không đưa lên Git.
* **Xử lý theo Hợp đồng v2**: Hai người dùng này được gán trạng thái `status = 'insufficient_evidence'`, `cluster_id = NULL`, không chia cho 0 và không đưa vector rỗng vào K-Means. 6,038 người dùng còn lại có `status = 'assigned'`.

### 4.3. Xu hướng hoạt động theo quý UTC (Temporal Activity)
Phân bố số lượng đánh giá theo quý UTC cho thấy sự tập trung áp đảo trong năm đầu tiên (năm 2000):
* **2000-Q2**: 133,319 lượt (13.33%)
* **2000-Q3**: 324,864 lượt (32.48%)
* **2000-Q4**: 446,574 lượt (44.65%) — *Đỉnh điểm thu thập dữ liệu*
* **2001-Q1**: 32,223 lượt (3.22%)
* **2001-Q2**: 15,091 lượt (1.51%)
* **2001-Q3**: 12,296 lượt (1.23%)
* **2001-Q4**: 8,448 lượt (0.84%)
* **2002-Q1**: 8,166 lượt (0.82%)
* **2002-Q2**: 6,385 lượt (0.64%)
* **2002-Q3**: 5,309 lượt (0.53%)
* **2002-Q4**: 4,186 lượt (0.42%)
* **2003-Q1**: 3,348 lượt (0.33%)

> **Tác động tới Bước 9**: Hơn 90.46% dữ liệu được tạo ra trong năm 2000. Do đó, việc chia tập theo phân vị thời gian toàn cục (70% tại $t_1$ và 85% tại $t_2$) sẽ đặt các mốc chia $t_1$ và $t_2$ vào giai đoạn cuối năm 2000, đảm bảo tập Train có đủ lịch sử và tập Validation/Test phản ánh đúng các tương tác tiếp nối theo thời gian.

---

## 5. Bảng Hồ Sơ Dữ Liệu & Mã Băm Chuẩn Hóa (Checksums)

Toàn bộ chỉ số định lượng chi tiết đã được xuất vào tệp tổng hợp: `results/eda/data_profile.csv`.

Mã băm SHA-256 byte của 4 bảng CSV chuẩn tại `data/processed/` được ghi nhận tại `results/eda/canonical_manifest.json`:
* `users.csv`: `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` (6,040 dòng dữ liệu)
* `movies.csv`: `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` (3,883 dòng dữ liệu)
* `movie_genres.csv`: `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` (6,408 dòng dữ liệu)
* `ratings.csv`: `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` (1,000,209 dòng dữ liệu)

Các biểu đồ trực quan hóa được lưu tại:
* `results/eda/rating_distribution.png`: Phân bố điểm đánh giá 1..5 sao.
* `results/eda/quarterly_activity.png`: Hoạt động đánh giá theo quý UTC.
* `results/eda/user_ratings_distribution.png`: Tần suất đánh giá của người dùng.
* `results/eda/movie_ratings_distribution.png`: Số lượt đánh giá mỗi phim và Top 10 phim phổ biến.
* `results/eda/genre_distribution.png`: Phân bố 18 thể loại theo thứ tự A–Z.
* `results/eda/age_gender_distribution.png`: Cơ cấu nhân khẩu học theo nhóm tuổi và giới tính.

---

## 6. Hướng Dẫn Người 1 (P1) Tải Nguồn Độc Lập & Đối Soát Checksum

Để đảm bảo nguyên tắc độc lập và bảo mật, Người 1 không sao chép dữ liệu từ Người 2 mà tải trực tiếp từ GroupLens:
1. Tải gói dữ liệu gốc từ: `https://files.grouplens.org/datasets/movielens/ml-1m.zip`
2. Giải nén và tính SHA-256 byte của 4 tệp nguồn: `users.dat`, `movies.dat`, `ratings.dat`, `README`.
3. Đối chiếu trực tiếp với `data/source_manifest.json` do P2 bàn giao qua Git.
4. Chạy pipeline ETL để nạp vào PostgreSQL Staging và Data Warehouse (`dw.v_ml_*`).
5. Xuất thử 4 bảng DW và đối chiếu SHA-256 byte với `results/eda/canonical_manifest.json` của P2 trước khi chốt mốc G2.
