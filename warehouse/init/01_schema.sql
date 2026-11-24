-- Kho dữ liệu bản nâng cấp: lược đồ sao, nạp tăng dần từ tầng gold của data lake.
--
-- Bảng chiều (dimension)            Bảng sự kiện (fact)
--   dim_user   (SCD loại 2)           fact_rating             transaction: 1 dòng = 1 lượt chấm điểm
--   dim_movie  (SCD loại 1)           fact_imdb_rating_daily  periodic snapshot: 1 phim x 1 ngày
--   dim_genre + bridge_movie_genre    fact_pageviews_daily    periodic snapshot: 1 phim x 1 ngày
--   dim_date, dim_source              fact_wiki_edit          transaction (streaming): 1 lần sửa bài Wikipedia

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA dw;
CREATE SCHEMA etl;
CREATE SCHEMA analytics;

-- ------------------------------------------------------------------ dimensions
CREATE TABLE dw.dim_date (
    date_key     integer PRIMARY KEY,               -- YYYYMMDD
    full_date    date NOT NULL UNIQUE,
    year         smallint NOT NULL,
    quarter      smallint NOT NULL,
    month        smallint NOT NULL,
    day          smallint NOT NULL,
    day_of_week  smallint NOT NULL,                 -- 1 = thứ Hai ... 7 = Chủ nhật
    is_weekend   boolean NOT NULL
);

INSERT INTO dw.dim_date
SELECT to_char(d, 'YYYYMMDD')::int, d, extract(year FROM d), extract(quarter FROM d),
       extract(month FROM d), extract(day FROM d), extract(isodow FROM d), extract(isodow FROM d) >= 6
FROM generate_series('1995-01-01'::date, '2030-12-31'::date, '1 day') AS d;

CREATE TABLE dw.dim_source (
    source_key   smallint PRIMARY KEY,
    source_name  text NOT NULL UNIQUE,
    description  text NOT NULL
);
INSERT INTO dw.dim_source VALUES
    (1, 'movielens', 'MovieLens 1M, rating lịch sử 2000–2003'),
    (2, 'app',       'App xem phim, rating mới qua CDC (Debezium)');

-- SCD loại 2: người dùng đổi nghề nghiệp / nhóm tuổi trên app -> thêm phiên bản mới, giữ phiên bản cũ.
-- Rating cũ vẫn trỏ về phiên bản đúng tại thời điểm chấm.
CREATE TABLE dw.dim_user (
    user_key     integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id      integer NOT NULL,                  -- khóa tự nhiên
    gender       char(1) NOT NULL,
    age_group    text NOT NULL,
    occupation   text NOT NULL,
    valid_from   timestamptz NOT NULL,
    valid_to     timestamptz,                       -- NULL = phiên bản hiện tại
    is_current   boolean NOT NULL DEFAULT true
);
CREATE UNIQUE INDEX ux_dim_user_current ON dw.dim_user (user_id) WHERE is_current;

-- SCD loại 1: thông tin phim (thời lượng, đạo diễn...) chỉ cần giá trị mới nhất, ghi đè.
CREATE TABLE dw.dim_movie (
    movie_key        integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movie_id         integer NOT NULL UNIQUE,
    title            text NOT NULL,
    year             smallint,
    imdb_id          text,
    imdb_match       text,                          -- links | title_year | NULL
    runtime_minutes  smallint,
    directors        text[],
    top_cast         text[],
    countries        text[],
    oscar_wins       smallint,
    enwiki_title     text,
    viwiki_title     text,
    poster_url       text,                          -- ảnh đại diện bài Wikipedia
    updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dw.dim_genre (
    genre_key   smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_name  text NOT NULL UNIQUE
);

CREATE TABLE dw.bridge_movie_genre (
    movie_key  integer NOT NULL REFERENCES dw.dim_movie,
    genre_key  smallint NOT NULL REFERENCES dw.dim_genre,
    PRIMARY KEY (movie_key, genre_key)
);

-- ------------------------------------------------------------------ facts
CREATE TABLE dw.fact_rating (
    user_id      integer NOT NULL,                  -- degenerate: khóa tự nhiên để upsert
    movie_id     integer NOT NULL,
    user_key     integer NOT NULL REFERENCES dw.dim_user,
    movie_key    integer NOT NULL REFERENCES dw.dim_movie,
    date_key     integer NOT NULL REFERENCES dw.dim_date,
    source_key   smallint NOT NULL REFERENCES dw.dim_source,
    rating       smallint NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_at     timestamptz NOT NULL,
    is_deleted   boolean NOT NULL DEFAULT false,    -- rating bị xóa trên app: xóa mềm
    changed_at   timestamptz NOT NULL,              -- thời điểm thay đổi ở nguồn (watermark)
    loaded_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, movie_id)
);
CREATE INDEX ix_fact_rating_movie ON dw.fact_rating (movie_key);
CREATE INDEX ix_fact_rating_date ON dw.fact_rating (date_key);
CREATE INDEX ix_fact_rating_source ON dw.fact_rating (source_key, rated_at);

CREATE TABLE dw.fact_imdb_rating_daily (
    movie_key    integer NOT NULL REFERENCES dw.dim_movie,
    date_key     integer NOT NULL REFERENCES dw.dim_date,
    imdb_rating  numeric(3,1) NOT NULL,
    imdb_votes   integer NOT NULL,
    votes_delta  integer,                           -- số vote tăng so với bản chụp trước
    PRIMARY KEY (movie_key, date_key)
);

CREATE TABLE dw.fact_pageviews_daily (
    movie_key  integer NOT NULL REFERENCES dw.dim_movie,
    date_key   integer NOT NULL REFERENCES dw.dim_date,
    views      integer NOT NULL,
    PRIMARY KEY (movie_key, date_key)
);

CREATE TABLE dw.fact_wiki_edit (
    event_id    text PRIMARY KEY,
    movie_key   integer NOT NULL REFERENCES dw.dim_movie,
    date_key    integer NOT NULL REFERENCES dw.dim_date,
    edited_at   timestamptz NOT NULL,
    wiki        text NOT NULL,
    is_bot      boolean NOT NULL,
    size_delta  integer
);

-- Vector mô tả phim cho tìm kiếm ngữ nghĩa (pgvector), 384 chiều = mô hình MiniLM đa ngôn ngữ.
CREATE TABLE dw.movie_embedding (
    movie_key  integer PRIMARY KEY REFERENCES dw.dim_movie,
    doc        text NOT NULL,
    embedding  vector(384) NOT NULL
);

-- ------------------------------------------------------------------ vận hành ETL
CREATE TABLE etl.watermark (
    name        text PRIMARY KEY,
    value       timestamptz NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE etl.pipeline_run (
    run_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    step         text NOT NULL,
    started_at   timestamptz NOT NULL,
    finished_at  timestamptz,
    rows_in      bigint,
    rows_out     bigint,
    status       text NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    message      text
);
