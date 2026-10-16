# ERD nháp S04

P1-S04-draft-v2, WAITING_REVIEW. Kế thừa nguyên mô hình v1; chỉ cập nhật căn cứ PR #5, không thêm quan hệ/cột. Ký hiệu `||--o{`: một hàng cha có thể có 0..N hàng con, mỗi con có đúng một cha. Tất cả FK trong SQL mặc định NO ACTION; không tự cascade xóa dữ liệu. Trong Mermaid, `text_array` biểu diễn SQL text[] và `double` biểu diễn double precision.

```mermaid
erDiagram
    DW_DIM_USER ||--o{ DW_FACT_RATING : user_key
    DW_DIM_MOVIE ||--o{ DW_FACT_RATING : movie_key
    DW_DIM_DATE ||--o{ DW_FACT_RATING : "date_key + UTC day"
    DW_DIM_MOVIE ||--o{ DW_BRIDGE_MOVIE_GENRE : movie_key
    DW_DIM_GENRE ||--o{ DW_BRIDGE_MOVIE_GENRE : genre_key
    DW_DIM_USER ||--o{ ANALYTICS_USER_CLUSTER : "original user_id"
    DW_DIM_GENRE ||--o{ ANALYTICS_CLUSTER_GENRE_PROFILE : "original genre_name"
    ANALYTICS_MODEL_REGISTRY ||--o{ ANALYTICS_USER_CLUSTER : model_version
    ANALYTICS_MODEL_REGISTRY ||--o{ ANALYTICS_CLUSTER_GENRE_PROFILE : model_version

    DW_DIM_USER {
        integer user_key PK
        integer user_id UK
        text gender
        text age_group
        smallint occupation
    }
    DW_DIM_MOVIE {
        integer movie_key PK
        integer movie_id UK
        text title
        smallint release_year "nullable"
    }
    DW_DIM_DATE {
        integer date_key PK
        date full_date UK
        smallint calendar_year "generated"
        smallint quarter_number "generated"
        smallint month_number "generated"
        smallint day_of_month "generated"
    }
    DW_DIM_GENRE {
        integer genre_key PK
        text genre_name UK
    }
    DW_BRIDGE_MOVIE_GENRE {
        integer movie_key PK,FK
        integer genre_key PK,FK
    }
    DW_FACT_RATING {
        bigint rating_key PK
        integer user_key FK "unique with movie_key"
        integer movie_key FK "unique with user_key"
        integer date_key FK
        smallint rating
        bigint rating_timestamp
        timestamptz rated_at
        date rated_date FK "generated UTC; composite FK with date_key"
    }
    ANALYTICS_MODEL_REGISTRY {
        text model_version PK
        smallint contract_version
        jsonb source_hashes
        jsonb canonical_hashes
        smallint k
        integer seed
        jsonb preprocessing
        text_array genre_order
        jsonb libraries
        text training_config_hash
        timestamptz model_created_at
        timestamptz registered_at
        boolean is_valid_for_dw
        boolean is_active "at most one true"
    }
    ANALYTICS_USER_CLUSTER {
        text model_version PK,FK
        integer user_id PK,FK
        integer cluster_id "nullable only for insufficient_evidence"
        text status
    }
    ANALYTICS_CLUSTER_GENRE_PROFILE {
        text model_version PK,FK
        integer cluster_id PK
        text genre_name PK,FK
        double mean_preference
        integer n_users
    }
```

Tên có tiền tố DW/ANALYTICS tương ứng schema viết thường trong SQL. FK ngày thực tế là `(date_key,rated_date) → dim_date(date_key,full_date)`; ERD chỉ có một đường quan hệ đó. UNIQUE fact `(user_key,movie_key)` không bao gồm thời điểm vì G1 đã đối soát không cặp user–movie lặp. Không suy mỗi người chỉ xem phim một lần.

Staging là lớp giữ trường nguồn, không có FK trực tiếp sang DW trước validation:

| Bảng staging | PK | Trường text nguồn |
|---|---|---|
| users_raw | source_line | user_id_raw, gender_raw, age_code_raw, occupation_raw |
| movies_raw | source_line | movie_id_raw, title_raw, genres_raw |
| ratings_raw | source_line | user_id_raw, movie_id_raw, rating_raw, timestamp_raw |

Hai bảng analytics là 0..N theo dimension khi giữ nhiều phiên bản; trong **một model_version** chỉ một hàng/user, và mỗi profile có một hàng/(cluster,genre). Không có FK trực tiếp user_cluster→cluster_genre_profile vì một cluster có nhiều genre; tính liên kết cluster/K được kiểm cả gói trước activate.

## Ví dụ tổng hợp, không phải dữ liệu người dùng thật

Giả sử phim M thuộc Action và Comedy. Bridge có hai hàng cho M. Hai đánh giá giả lập cho M là 4 và 2:

- Fact có hai hàng, tổng điểm 6, điểm trung bình 6/2=3.
- Join bridge để phân tích genre cho ra bốn hàng: Action count 2 và Comedy count 2. Tổng rating **duy nhất vẫn 2**, không cộng 2+2 thành 4.
- Tỷ trọng lượt gán genre trong tập ví dụ: Action 2/(2+2)=50%, Comedy 50%; mẫu số 4 lượt gắn, khác 2 rating duy nhất.
- View `dw.v_ml_ratings` không join bridge nên vẫn hai hàng; view `dw.v_ml_movie_genres` chỉ trả hai liên kết M–genre.

Bridge không giới hạn mỗi phim chỉ có hai genre; số liên kết phải khớp nguồn và manifest đã kiểm nhận. Biểu đồ trên không thêm director/actor hoặc dimension khác nguồn.
