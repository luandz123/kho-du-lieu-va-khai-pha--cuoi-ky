-- P1 S07: six aggregate views, existing analytics schema only. No table/contract DDL.
-- O1 grain: system snapshot. Denominator: unique fact ratings; catalog counts separate.
CREATE VIEW analytics.v_olap_kpi AS
SELECT (SELECT count(*) FROM dw.dim_user) AS catalog_users,
       (SELECT count(*) FROM dw.dim_movie) AS catalog_movies,
       count(DISTINCT user_key) AS rated_users, count(DISTINCT movie_key) AS rated_movies,
       count(*) AS rating_count, sum(rating) AS rating_sum,
       sum(rating)::numeric / NULLIF(count(*),0) AS mean_rating
FROM dw.fact_rating;

-- O2 grain: rated movie. Mean denominator: this movie's source ratings.
CREATE VIEW analytics.v_olap_movie_metrics AS
SELECT m.movie_id,m.title,count(*) AS rating_count,sum(f.rating) AS rating_sum,
       sum(f.rating)::numeric / count(*) AS mean_rating
FROM dw.fact_rating f JOIN dw.dim_movie m ON m.movie_key=f.movie_key
GROUP BY m.movie_id,m.title;

-- O3 grain: genre x age label x gender. A multi-genre rating contributes to each genre.
-- Filter gender/genre/age before rolling up; SUM(score)/SUM(count), never mean(means).
CREATE VIEW analytics.v_olap_genre_age_gender AS
SELECT g.genre_name,u.age_group,u.gender,count(*) AS rating_count,sum(f.rating) AS rating_sum,
       sum(f.rating)::numeric / count(*) AS mean_rating
FROM dw.fact_rating f JOIN dw.dim_user u ON u.user_key=f.user_key
JOIN dw.bridge_movie_genre b ON b.movie_key=f.movie_key JOIN dw.dim_genre g ON g.genre_key=b.genre_key
GROUP BY g.genre_name,u.age_group,u.gender;

-- O4 grain: one calendar year/quarter/month at each level, unique ratings from fact.
-- UTC date dimension; LEFT JOIN counts f.rating_key, not calendar rows. Empty periods=0.
CREATE VIEW analytics.v_olap_time_rollup AS
SELECT CASE WHEN GROUPING(d.month_number)=0 THEN 'month'
            WHEN GROUPING(d.quarter_number)=0 THEN 'quarter' ELSE 'year' END AS time_level,
       d.calendar_year,d.quarter_number,d.month_number,
       count(f.rating_key) AS rating_count,COALESCE(sum(f.rating),0) AS rating_sum,
       sum(f.rating)::numeric / NULLIF(count(f.rating_key),0) AS mean_rating
FROM dw.dim_date d LEFT JOIN dw.fact_rating f ON f.date_key=d.date_key
GROUP BY GROUPING SETS ((d.calendar_year),(d.calendar_year,d.quarter_number),
                       (d.calendar_year,d.quarter_number,d.month_number));

-- O5 grain: complete genre x UTC quarter grid within observed fact bounds, no filters.
-- Share denominator=sum of rating-genre assignments in same quarter, NOT unique ratings.
-- Zero-fill BEFORE LAG. Edge quarter flag is observational, not a completeness claim.
CREATE VIEW analytics.v_olap_genre_quarter AS
WITH bounds AS (
 SELECT min(date_trunc('quarter',rated_at AT TIME ZONE 'UTC'))::date AS lo,
        max(date_trunc('quarter',rated_at AT TIME ZONE 'UTC'))::date AS hi FROM dw.fact_rating
), quarters AS (
 SELECT s::date AS quarter_start FROM bounds,
 generate_series(lo::timestamp,hi::timestamp,interval '3 months') s
), counts AS (
 SELECT g.genre_name,date_trunc('quarter',f.rated_at AT TIME ZONE 'UTC')::date AS quarter_start,
        count(*) AS rating_count,sum(f.rating) AS rating_sum
 FROM dw.fact_rating f JOIN dw.bridge_movie_genre b ON b.movie_key=f.movie_key
 JOIN dw.dim_genre g ON g.genre_key=b.genre_key GROUP BY 1,2
), system_counts AS (
 SELECT date_trunc('quarter',rated_at AT TIME ZONE 'UTC')::date AS quarter_start,
        count(*) AS system_rating_count FROM dw.fact_rating GROUP BY 1
), grid AS (
 SELECT g.genre_name,q.quarter_start,COALESCE(c.rating_count,0) AS rating_count,
        COALESCE(c.rating_sum,0) AS rating_sum,COALESCE(s.system_rating_count,0) AS system_rating_count,
        (q.quarter_start=b.lo OR q.quarter_start=b.hi) AS is_boundary_partial
 FROM dw.dim_genre g CROSS JOIN quarters q CROSS JOIN bounds b
 LEFT JOIN counts c USING(genre_name,quarter_start) LEFT JOIN system_counts s USING(quarter_start)
), lagged AS (
 SELECT *,lag(rating_count) OVER w AS previous_rating_count,
        lag(is_boundary_partial) OVER w AS previous_is_boundary_partial,
        sum(rating_count) OVER(PARTITION BY quarter_start) AS genre_assignment_total
 FROM grid WINDOW w AS(PARTITION BY genre_name ORDER BY quarter_start)
)
SELECT *,100::numeric*(rating_count-previous_rating_count)/NULLIF(previous_rating_count,0) AS qoq_pct,
       100::numeric*rating_count/NULLIF(genre_assignment_total,0) AS genre_share_pct,
       COALESCE(previous_rating_count>=100,false) AS passes_fixed_100_threshold,
       COALESCE(previous_rating_count>=100 AND NOT is_boundary_partial
                AND NOT previous_is_boundary_partial,false) AS eligible_for_ranking
FROM lagged;

-- O6 grain: UTC day x movie x age x gender, unique ratings (no bridge join).
-- Query filters genre via EXISTS, then period/age/gender and rolls up day to month/movie.
CREATE VIEW analytics.v_olap_movie_day_segment AS
SELECT d.full_date AS rated_date,m.movie_key,m.movie_id,m.title,u.age_group,u.gender,
       count(*) AS rating_count,sum(f.rating) AS rating_sum
FROM dw.fact_rating f JOIN dw.dim_date d ON d.date_key=f.date_key
JOIN dw.dim_movie m ON m.movie_key=f.movie_key JOIN dw.dim_user u ON u.user_key=f.user_key
GROUP BY d.full_date,m.movie_key,m.movie_id,m.title,u.age_group,u.gender;
