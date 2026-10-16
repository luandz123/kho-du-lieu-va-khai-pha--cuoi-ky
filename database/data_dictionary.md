# Từ điển dữ liệu — S04 nháp v2

V2 kế thừa đủ 64 cột của v1, không đổi kiểu hoặc giao diện. Tập mã trong manifest PR #5 tại `a8d2615` xác nhận F/M, bảy nhãn tuổi, occupation 0..20, rating 1..5 và 18 genre. SHA metadata còn chờ P2 sửa không làm thay đổi miền hay checksum. Bảng và ràng buộc vẫn là thiết kế chưa áp dụng.

Ngày 16/10/2026. Thiết kế PostgreSQL 17, contract v2; chưa chạy DDL. SQL có thẩm quyền về khai báo tại [schema.sql](schema.sql); nguồn và phép biến đổi tại [source_to_target.md](source_to_target.md).

`NN` = NOT NULL, `Y` = cho phép NULL, `PK` = khóa chính (ngầm NN), `UQ` = duy nhất, `FK` = khóa ngoại. `G` = cột GENERATED STORED, không nhận giá trị nạp trực tiếp. Cột G không khai báo NN trong SQL nhưng biểu thức từ đầu vào NN luôn sinh giá trị khác NULL trong miền dữ liệu này. Không dùng ZIP, không lưu mật khẩu hoặc connection URI.

## Staging: giữ trường nguồn trước kiểm tra nghiệp vụ

Mỗi bảng có một dòng cho một dòng nguồn, không có dòng header. Số dòng nguồn bắt đầu từ 1 và duy nhất **trong từng tệp**. Đây là định vị lỗi, không phải ID nghiệp vụ. Đọc Latin-1, tách `::`, kiểm số trường trước nạp. Những trường text cho phép NULL để phát hiện lỗi; NULL/lỗi nghiệp vụ phải làm thất bại đối soát, không tự lọc bỏ. Không giữ cả dòng users nguyên bản vì có ZIP.

| Bảng.cột | Kiểu | Null | Khóa/ràng buộc | Nguồn, biến đổi và ý nghĩa |
|---|---|---|---|---|
| staging.users_raw.source_line | bigint | NN | PK, >0 | Vị trí dòng users.dat; truy vết cục bộ |
| staging.users_raw.user_id_raw | text | Y | — | UserID nguyên chuỗi trước ép kiểu |
| staging.users_raw.gender_raw | text | Y | — | Gender nguồn, không tự đổi nhãn |
| staging.users_raw.age_code_raw | text | Y | — | Age nguồn; chưa thay nhãn tại staging |
| staging.users_raw.occupation_raw | text | Y | — | Occupation nguồn; ZIP cột cuối bị loại có chủ đích |
| staging.movies_raw.source_line | bigint | NN | PK, >0 | Vị trí dòng movies.dat |
| staging.movies_raw.movie_id_raw | text | Y | — | MovieID nguyên chuỗi |
| staging.movies_raw.title_raw | text | Y | — | Title giữ nguyên, gồm năm trong ngoặc nếu có |
| staging.movies_raw.genres_raw | text | Y | — | Chuỗi genre nguồn, phân cách bên trong bằng `|` |
| staging.ratings_raw.source_line | bigint | NN | PK, >0 | Vị trí dòng ratings.dat; grain đánh giá nguồn |
| staging.ratings_raw.user_id_raw | text | Y | — | UserID nguồn |
| staging.ratings_raw.movie_id_raw | text | Y | — | MovieID nguồn |
| staging.ratings_raw.rating_raw | text | Y | — | Rating nguồn trước kiểm miền |
| staging.ratings_raw.timestamp_raw | text | Y | — | Giây Unix nguồn, không phải thời lượng xem |

## DW: dimension và bridge

| Bảng.cột | Kiểu | Null | Khóa/ràng buộc | Nguồn, biến đổi và ý nghĩa |
|---|---|---|---|---|
| dw.dim_user.user_key | integer identity ALWAYS | NN | PK | Sinh tại DW; không xuất làm user_id, có thể đổi khi full refresh |
| dw.dim_user.user_id | integer | NN | UQ, >0 | Ép kiểu UserID, giữ ID MovieLens gốc |
| dw.dim_user.gender | text | NN | F hoặc M | Giữ Gender nguồn |
| dw.dim_user.age_group | text | NN | Bảy nhãn contract | Age: 1→Under 18, 18→18-24, 25→25-34, 35→35-44, 45→45-49, 50→50-55, 56→56+; mã khác dừng |
| dw.dim_user.occupation | smallint | NN | 0..20 | Mã nghề nguồn, không gán nghĩa nghề mới; view cast integer |
| dw.dim_movie.movie_key | integer identity ALWAYS | NN | PK | Surrogate DW |
| dw.dim_movie.movie_id | integer | NN | UQ, >0 | MovieID gốc |
| dw.dim_movie.title | text | NN | — | Giữ nguyên chuỗi Title; không bỏ năm/trim chuỗi nguồn |
| dw.dim_movie.release_year | smallint | Y | 0..9999 khi có | Bốn chữ số trong ngoặc cuối Title, không khớp thì NULL; dù mẫu đã kiểm không có NULL, contract vẫn cho NULL |
| dw.dim_date.date_key | integer identity ALWAYS | NN | PK; UQ ghép với full_date | Surrogate DW, không dùng Unix timestamp làm khóa ngày |
| dw.dim_date.full_date | date | NN | UQ | Ngày UTC từ timestamp; sinh lịch liên tục từ ngày nhỏ nhất đến lớn nhất nguồn để hỗ trợ quý không có rating |
| dw.dim_date.calendar_year | smallint, G | Từ NN | EXTRACT YEAR | Năm lịch của full_date |
| dw.dim_date.quarter_number | smallint, G | Từ NN | 1..4 | Quý lịch, không phải quý tài chính |
| dw.dim_date.month_number | smallint, G | Từ NN | 1..12 | Tháng UTC |
| dw.dim_date.day_of_month | smallint, G | Từ NN | 1..31 | Ngày trong tháng |
| dw.dim_genre.genre_key | integer identity ALWAYS | NN | PK | Surrogate DW |
| dw.dim_genre.genre_name | text | NN | UQ | Tập tên genre nguồn; không tự đổi hoa/thường hoặc thêm genre |
| dw.bridge_movie_genre.movie_key | integer | NN | PK ghép; FK dim_movie.movie_key | Ánh xạ MovieID nguồn sang surrogate |
| dw.bridge_movie_genre.genre_key | integer | NN | PK ghép; FK dim_genre.genre_key | Một cặp phim–genre đúng một lần; không nhân bản phim trong dim_movie |

Không có dimension đạo diễn, diễn viên, phiên xem hoặc doanh thu. Tuổi/giới là thuộc tính lịch sử trong nguồn; không có SCD giả lập khi nguồn không cung cấp lịch sử thay đổi.

## DW: fact_rating

| Cột | Kiểu | Null | Khóa/ràng buộc | Nguồn, biến đổi và ý nghĩa |
|---|---|---|---|---|
| rating_key | bigint identity ALWAYS | NN | PK | Khóa kỹ thuật một đánh giá nguồn; không phải ID lượt xem |
| user_key | integer | NN | FK dim_user.user_key; UQ ghép movie_key | Tra cứu từ user_id gốc; không tìm thấy thì dừng |
| movie_key | integer | NN | FK dim_movie.movie_key; UQ ghép user_key | Tra cứu từ movie_id gốc |
| date_key | integer | NN | FK ghép rated_date → dim_date(date_key,full_date) | Tra cứu ngày UTC; FK ghép ngăn liên kết nhầm ngày |
| rating | smallint | NN | 1..5 | Số sao nguyên của nguồn; không phải lượt xem |
| rating_timestamp | bigint | NN | Epoch phải bằng rated_at | Giữ giây Unix nguồn, tên timestamp ở view |
| rated_at | timestamptz | NN | EXTRACT(EPOCH) = rating_timestamp | Cùng thời điểm với Unix; nạp từ chuyển đổi timezone-aware UTC |
| rated_date | date, G | Từ NN | Thành phần FK ghép | `(rated_at AT TIME ZONE 'UTC')::date`; không phụ thuộc timezone phiên |

UNIQUE(user_key,movie_key) dựa trên đối soát G1: duplicate_pairs=0 trên 1000209 dòng. Nếu nguồn tương lai có trùng, dừng và xin chính sách chung, không dùng UPSERT để mất đánh giá. FK không có ON DELETE CASCADE; không tự xóa lan truyền.

## Analytics: metadata kỹ thuật của gói cụm

`analytics.model_registry` là đề xuất cần review, hỗ trợ hai bảng kết quả được yêu cầu. Chỉ nhận metadata từ manifest đã kiểm; tên phiên bản không suy từ ngày chạy hay nhánh Git. Không chứa mô hình CF hoặc kết quả cá nhân Top 5.

| Cột | Kiểu | Null | Khóa/ràng buộc | Nguồn, biến đổi và ý nghĩa |
|---|---|---|---|---|
| model_version | text | NN | PK, không rỗng sau btrim | Chuỗi cố định từ manifest G3 và user_cluster.csv; không tự sửa/cắt chuỗi |
| contract_version | smallint | NN | =2 | Contract của gói |
| source_hashes | jsonb | NN | Object, đủ bốn tên tệp | SHA-256 users.dat/movies.dat/ratings.dat/README; giá trị hash và tập khóa phải kiểm trước nạp |
| canonical_hashes | jsonb | NN | Object, đủ bốn tên bảng | SHA-256 users/movies/movie_genres/ratings; phải khớp DW hiện tại |
| k | smallint | NN | 2..8 | K từ manifest, theo miền lựa chọn trong đặc tả Q1 |
| seed | integer | NN | — | Seed tái lập từ manifest |
| preprocessing | jsonb | NN | — | Đặc tả tiền xử lý, giữ nội dung manifest; kiểm cấu trúc trước nạp |
| genre_order | text[] | NN | Mảng một chiều, không rỗng/NULL | Thứ tự vector genre của mô hình; kiểm không lặp và đúng toàn bộ genre DW |
| libraries | jsonb | NN | Object | Tên thư viện và phiên bản thực dùng của P2; không thay bằng phiên bản máy P1 |
| training_config_hash | text | NN | 64 ký tự hex thường | Hash cấu hình mô hình từ gói; đối chiếu quy tắc tạo hash của P2 |
| model_created_at | timestamptz | NN | — | Thời điểm UTC trong manifest G3; không dùng thời điểm nạp thay thế |
| registered_at | timestamptz | NN | Default CURRENT_TIMESTAMP | Thời điểm P1 nhận gói, khác thời điểm huấn luyện |
| is_valid_for_dw | boolean | NN | Default false | Chỉ true sau đối soát cùng DW; refresh vô hiệu hóa |
| is_active | boolean | NN | Default false, active ⇒ valid; unique partial index | Tối đa một model active toàn hệ thống; cho phép chưa có active |

Registry không thay thế manifest gốc: gói và báo cáo kiểm nhận được lưu cục bộ ngoài Git; hồ sơ tổng hợp lưu đường dẫn, hash, count và trạng thái. Cấu trúc JSON không tự chứng minh giá trị hash đúng. Metadata cũ có thể giữ để kiểm toán sau refresh; kết quả đang dùng phải thuộc DW hiện hành.

## Analytics: hai bảng nhận kết quả

| Bảng.cột | Kiểu | Null | Khóa/ràng buộc | Nguồn, biến đổi và ý nghĩa |
|---|---|---|---|---|
| analytics.user_cluster.model_version | text | NN | PK ghép user_id; FK registry | Cùng phiên bản ở từng dòng CSV và manifest |
| analytics.user_cluster.user_id | integer | NN | PK ghép model_version; FK dim_user.user_id | ID nguồn; đúng một dòng cho mỗi user DW trong mỗi model |
| analytics.user_cluster.cluster_id | integer | Y | assigned: nguyên ≥0; thiếu bằng chứng: NULL | Phải <K qua kiểm gói; không dùng -1 thay NULL |
| analytics.user_cluster.status | text | NN | assigned hoặc insufficient_evidence | CHECK ghép với cluster_id; thiếu bằng chứng không tham gia trung bình cụm |
| analytics.cluster_genre_profile.model_version | text | NN | PK ghép cluster_id,genre_name; FK registry | Bổ sung từ manifest của **cùng gói**, vì CSV profile không có cột phiên bản |
| analytics.cluster_genre_profile.cluster_id | integer | NN | PK ghép, ≥0 | <K qua kiểm gói |
| analytics.cluster_genre_profile.genre_name | text | NN | PK ghép; FK dim_genre.genre_name | Giữ tên genre; đủ mọi genre cho mỗi cụm, kể cả giá trị 0 |
| analytics.cluster_genre_profile.mean_preference | double precision | NN | 0..1 | Trung bình tỷ lệ genre gốc của user assigned; tổng theo cụm =1 trong sai số tuyệt đối 1e-8 |
| analytics.cluster_genre_profile.n_users | integer | NN | ≥0 | Số user assigned trong cụm; giống nhau ở mọi genre và bằng count trong user_cluster |

DDL cho phép n_users=0 nhưng **không cho activate gói có cụm rỗng**: trung bình không xác định; trả P2 để xử lý/chốt mô hình. Không tự gán trung bình 0 hoặc chia cho 0. Mean phải hữu hạn; kiểm gói chặn NaN/Infinity trước SQL. Mọi kiểm liên bảng, K×genre, số user, mean và hash nằm trong quy trình trước activate, không ngụy tạo CHECK liên bảng.

## View và ý nghĩa NULL ở giao tiếp

Bốn view contract có cột theo đúng thứ tự [source_to_target.md](source_to_target.md). Integer DW nhỏ được cast integer ở view; timestamp trả bigint; rated_at trả text ISO 8601 UTC-Z. Chỉ release_year được NULL. View ratings không join bridge/genre nên vẫn một dòng mỗi đánh giá. Không ORDER BY ngầm: bên xuất phải sort theo contract trước hash.

Hai view nội bộ `analytics.v_active_user_cluster` và `analytics.v_active_cluster_genre_profile` lọc registry active AND valid. View user trả `user_id,cluster_id,status,model_version`; profile trả `cluster_id,genre_name,mean_preference,n_users,model_version`. Không có active thì rỗng; không gán phiên bản cũ làm mặc định. Khi BI nối hai view, luôn dùng cả model_version và cluster_id; khi nối demographics dùng user_id nguồn đúng khóa.
