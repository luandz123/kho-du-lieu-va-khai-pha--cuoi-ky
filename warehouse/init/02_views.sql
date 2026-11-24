-- View phân tích cho dashboard bản nâng cấp (Superset đọc trực tiếp các view này).

-- 1. So sánh điểm MovieLens (người dùng 2000–2003) với điểm IMDb hiện tại.
CREATE OR REPLACE VIEW analytics.v_movielens_vs_imdb AS
WITH ml AS (
    SELECT movie_key, avg(rating)::numeric(3,2) AS ml_avg, count(*) AS ml_ratings
    FROM dw.fact_rating WHERE NOT is_deleted GROUP BY movie_key
), imdb AS (
    SELECT DISTINCT ON (movie_key) movie_key, imdb_rating, imdb_votes
    FROM dw.fact_imdb_rating_daily ORDER BY movie_key, date_key DESC
)
SELECT m.movie_id, m.title, m.year, ml.ml_avg, ml.ml_ratings,
       imdb.imdb_rating, imdb.imdb_votes,
       -- quy đổi thang 1–5 sang 1–10 để so sánh
       round(ml.ml_avg * 2 - imdb.imdb_rating, 2) AS gap_ml_minus_imdb
FROM dw.dim_movie m JOIN ml USING (movie_key) JOIN imdb USING (movie_key)
WHERE ml.ml_ratings >= 50;

-- 2. Phim "đang được quan tâm": lượt xem Wikipedia 7 ngày gần nhất so với 7 ngày trước đó.
CREATE OR REPLACE VIEW analytics.v_trending_movies AS
WITH last_day AS (SELECT max(full_date) AS d FROM dw.fact_pageviews_daily JOIN dw.dim_date USING (date_key)),
pv AS (
    SELECT p.movie_key,
           sum(p.views) FILTER (WHERE dd.full_date > l.d - 7) AS views_7d,
           sum(p.views) FILTER (WHERE dd.full_date <= l.d - 7 AND dd.full_date > l.d - 14) AS views_prev_7d
    FROM dw.fact_pageviews_daily p JOIN dw.dim_date dd USING (date_key) CROSS JOIN last_day l
    GROUP BY p.movie_key
)
SELECT m.movie_id, m.title, m.year, m.poster_url, pv.views_7d, pv.views_prev_7d,
       round(100.0 * (pv.views_7d - pv.views_prev_7d) / nullif(pv.views_prev_7d, 0), 1) AS growth_pct
FROM pv JOIN dw.dim_movie m USING (movie_key)
WHERE pv.views_7d IS NOT NULL;

-- 3. Lượt xem Wikipedia theo ngày và thể loại.
CREATE OR REPLACE VIEW analytics.v_pageviews_by_genre AS
SELECT dd.full_date, g.genre_name, sum(p.views) AS views
FROM dw.fact_pageviews_daily p
JOIN dw.dim_date dd USING (date_key)
JOIN dw.bridge_movie_genre b USING (movie_key)
JOIN dw.dim_genre g USING (genre_key)
GROUP BY 1, 2;

-- 4. Đạo diễn: số phim, điểm trung bình MovieLens, tổng lượt chấm.
CREATE OR REPLACE VIEW analytics.v_director_stats AS
SELECT d.director, count(DISTINCT m.movie_key) AS movies, count(*) AS ratings,
       avg(f.rating)::numeric(3,2) AS avg_rating
FROM dw.dim_movie m
CROSS JOIN LATERAL unnest(m.directors) AS d(director)
JOIN dw.fact_rating f ON f.movie_key = m.movie_key AND NOT f.is_deleted
GROUP BY d.director
HAVING count(DISTINCT m.movie_key) >= 3;

-- 5. Rating mới từ app (qua CDC) theo giờ – thấy dữ liệu thời gian thực đổ vào kho.
CREATE OR REPLACE VIEW analytics.v_app_ratings_hourly AS
SELECT date_trunc('hour', rated_at) AS hour, count(*) AS ratings,
       count(*) FILTER (WHERE is_deleted) AS deleted, avg(rating)::numeric(3,2) AS avg_rating
FROM dw.fact_rating f JOIN dw.dim_source s USING (source_key)
WHERE s.source_name = 'app'
GROUP BY 1;

-- 6. Giám sát pipeline.
CREATE OR REPLACE VIEW analytics.v_pipeline_runs AS
SELECT run_id, step, status, started_at, finished_at,
       extract(epoch FROM finished_at - started_at)::numeric(10,1) AS seconds, rows_in, rows_out, message
FROM etl.pipeline_run;

-- 7. Lịch sử phiên bản người dùng (SCD loại 2).
CREATE OR REPLACE VIEW analytics.v_user_versions AS
SELECT user_id, user_key, gender, age_group, occupation, valid_from, valid_to, is_current
FROM dw.dim_user
WHERE user_id IN (SELECT user_id FROM dw.dim_user GROUP BY user_id HAVING count(*) > 1);
