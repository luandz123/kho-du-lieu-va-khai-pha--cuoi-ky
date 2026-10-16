# Ánh xạ nguồn và giao diện contract v2

Nháp P1-S04-draft-v2, kế thừa mapping v1, chưa triển khai pipeline/DDL. Căn cứ: contract v2, kiểm nhận kỹ thuật G1 head `9299268` và manifest PR #5 tại merge `a8d2615` có cùng bốn checksum. Không dựa vào câu “100% sạch”, không sửa file P2 hoặc manifest kỳ vọng.

## Nguồn → staging → DW

| Nguồn | Staging | Biến đổi/validation ở ETL tương lai | Đích |
|---|---|---|---|
| users.dat cột 1 | users_raw.user_id_raw | Parse integer, không NULL, duy nhất, đối chiếu tập ID | dim_user.user_id; user_key identity nội bộ |
| users.dat cột 2 | gender_raw | Giữ F/M theo contract | dim_user.gender |
| users.dat cột 3 | age_code_raw | 1→Under 18, 18→18-24, 25→25-34, 35→35-44, 45→45-49, 50→50-55, 56→56+ | dim_user.age_group |
| users.dat cột 4 | occupation_raw | Parse mã integer nguồn, miền 0..20; không suy nghề mới | dim_user.occupation |
| users.dat cột 5 | Không stage, không DW | ZIP không dùng; tệp gốc vẫn cục bộ để đối chiếu hash | Không có dimension ZIP |
| movies.dat cột 1 | movies_raw.movie_id_raw | Parse integer, duy nhất, không NULL | dim_movie.movie_id; movie_key identity |
| movies.dat cột 2 | title_raw | Latin-1→Unicode; giữ nguyên title; lấy bốn chữ số trong ngoặc cuối tiêu đề, không khớp→NULL | title, release_year |
| movies.dat cột 3 | genres_raw | Tách dấu `|`, giữ tên genre; kiểm cặp phim–genre không trùng | dim_genre + bridge_movie_genre |
| ratings.dat cột 1/2 | user_id_raw/movie_id_raw | Parse ID, kiểm FK nguồn tồn tại, tra surrogate duy nhất | fact_rating.user_key/movie_key |
| ratings.dat cột 3 | rating_raw | Parse số nguyên 1..5, không coi 0 là rating thiếu | fact_rating.rating |
| ratings.dat cột 4 | timestamp_raw | Parse int64 giây Unix; chuyển UTC cùng thời điểm, tách ngày UTC | fact_rating.rating_timestamp/rated_at/rated_date/date_key |
| Vị trí dòng nguồn | source_line | Đánh số từ 1 trong từng tệp; manifest/log xác định tệp và hash | Staging; truy vết lỗi cục bộ |

Staging giữ text nullable để nhận diện lỗi trước chuyển DW; kiểm số trường/NULL/parse và không tự bỏ dòng, deduplicate hoặc sửa dữ liệu. Không giữ raw_line chứa ZIP. Full refresh chỉ nhận một snapshot nguồn đã chốt. README nguồn cung cấp miền mã, không thành bảng nghiệp vụ.

Dim_date phủ liên tục ngày UTC từ min đến max quan sát; năm/quý/tháng/ngày sinh từ full_date. Không suy dữ liệu đầy đủ trong mọi quý. Surrogate có thể đổi khi refresh; giao tiếp luôn dùng ID nguồn.

## Bốn view bắt buộc

| View | Thứ tự cột | Kiểu SQL đầu ra |
|---|---|---|
| dw.v_ml_users | user_id, gender, age_group, occupation | INTEGER, TEXT, TEXT, INTEGER |
| dw.v_ml_movies | movie_id, title, release_year | INTEGER, TEXT, INTEGER nullable |
| dw.v_ml_movie_genres | movie_id, genre_name | INTEGER, TEXT |
| dw.v_ml_ratings | user_id, movie_id, rating, timestamp, rated_at | INTEGER, INTEGER, INTEGER, BIGINT, TEXT UTC-Z |

Alias SQL `"timestamp"` vẫn trả đúng tên cột timestamp. Fact giữ TIMESTAMPTZ; view dùng `to_char` sau chuyển UTC, xuất `YYYY-MM-DDTHH:MM:SSZ`. Đây là lựa chọn nháp cần duyệt. CHECK epoch không cho mất phần giây hoặc làm tròn nguồn để ép khớp.

View users/movies trả toàn bộ dimension nguồn; không inner join fact làm mất phim chưa được đánh giá. View ratings chỉ nối ngược hai dimension user/movie theo khóa duy nhất, không join bridge/genre/date/analytics. View movie_genres trả mỗi cặp nguồn một dòng.

View không hứa thứ tự hàng. Serializer phải ORDER BY theo contract: users(user_id), movies(movie_id), movie_genres(movie_id,genre_name), ratings(user_id,movie_id,timestamp,rating). CSV UTF-8 không BOM, LF, header, dấu phẩy, quote CSV chuẩn, NULL rỗng, integer không .0; SHA-256 tính trên byte CSV đã sort, không trên str(datetime) mặc định.

PR #5 đã bàn giao sửa R1/R5/R6 và bộ test 23/23 đạt theo điều phối/log P2; ghi chú yêu cầu sửa của v1 được thay bằng cập nhật này. Việc view trả TEXT và test fixture không thay nghiệm thu adapter DW thật. G2 phải kiểm raw/csv/DW tương đương trên PostgreSQL, cùng test TIMESTAMPTZ và timezone; chưa chạy ở S04.

### Năm NULL và tên phim

Ví dụ tổng hợp: `Example (2001)` giữ nguyên title và release_year=2001; `Example` giữ nguyên title và release_year=NULL. Không thay NULL bằng 0, năm hiện tại hoặc ngày đánh giá. Đưa NULL thành ô rỗng khi xuất canonical; client pandas phải dùng kiểu nullable integer để tránh `2001.0`. BI giữ nhóm năm chưa xác định riêng, không làm mất phim/rating khi lọc hoặc tổng hợp. Việc nguồn hiện tại có null_year=0 không cho phép đổi schema thành NOT NULL.

## Gói cụm → analytics

| Đầu vào contract | Đích/ánh xạ |
|---|---|
| user_cluster.csv: user_id, cluster_id, status, model_version | analytics.user_cluster; đọc CSV theo header tường minh, không phụ thuộc thứ tự cột vật lý SQL; FK user_id→dim_user.user_id |
| cluster_genre_profile.csv: cluster_id, genre_name, mean_preference, n_users | analytics.cluster_genre_profile; thêm model_version từ manifest của cùng gói, không đoán từ phiên bản active |
| manifest.json | model_registry: model_version/contract_version/source_hashes/canonical_hashes/K/seed/preprocessing/genre_order/libraries/training_config_hash/thời điểm UTC |
| Trạng thái P1 nội bộ | registered_at, is_valid_for_dw/is_active; không biến thành trường bắt buộc mới trong manifest P2 |

Hai CSV phải đúng header/order contract, đủ gói và khớp hash. Không truyền surrogate P1 cho P2. Các phiên bản được phân tách bằng PK; BI chỉ đọc hai view active và nối kèm model_version. Full refresh vô hiệu hóa kết quả, yêu cầu kiểm/nạp lại gói theo hash DW hiện tại. Không tự tạo model_version, K hoặc tên cụm. G3 chưa bắt buộc để review thiết kế, nhưng cần cho dashboard 11B.
