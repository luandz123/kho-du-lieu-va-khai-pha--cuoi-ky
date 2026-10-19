-- name: O1
-- Grain one system snapshot; unique fact denominator, no genre join; no filters.
SELECT * FROM analytics.v_olap_kpi;

-- name: O2
-- Grain movie; top10 count DESC, then mean DESC, then original movie_id ASC.
SELECT movie_id,title,rating_count,rating_sum,mean_rating
FROM analytics.v_olap_movie_metrics
ORDER BY rating_count DESC,mean_rating DESC,movie_id ASC LIMIT 10;

-- name: O3
-- Grain genre x age; nullable gender/genre-array/age-array filters. Weighted roll-up.
SELECT genre_name,age_group,sum(rating_count) AS rating_count,sum(rating_sum) AS rating_sum,
       sum(rating_sum)::numeric/NULLIF(sum(rating_count),0) AS mean_rating
FROM analytics.v_olap_genre_age_gender
WHERE (%(gender)s::text IS NULL OR gender=%(gender)s)
  AND (%(genres)s::text[] IS NULL OR genre_name=ANY(%(genres)s::text[]))
  AND (%(ages)s::text[] IS NULL OR age_group=ANY(%(ages)s::text[]))
GROUP BY genre_name,age_group ORDER BY genre_name,age_group;

-- name: O4
-- Grain year OR quarter OR month, unique fact counts; sum/count weighted mean.
SELECT * FROM analytics.v_olap_time_rollup
ORDER BY calendar_year,quarter_number NULLS FIRST,month_number NULLS FIRST;

-- name: O5
-- Grain genre x quarter; all genres/all demographics/full observed period.
-- Ranking: fixed previous_count>=100, excluding current/previous boundary quarters.
-- Share denominator stays ALL genre assignments of same quarter (no genre slice here).
WITH eligible AS (
 SELECT genre_name,quarter_start,row_number() OVER(PARTITION BY quarter_start
   ORDER BY qoq_pct DESC,rating_count DESC,genre_name ASC) AS growth_rank
 FROM analytics.v_olap_genre_quarter WHERE eligible_for_ranking
)
SELECT v.*,e.growth_rank FROM analytics.v_olap_genre_quarter v
LEFT JOIN eligible e USING(genre_name,quarter_start)
ORDER BY quarter_start,genre_name;

-- name: O6
-- Grain month x movie after combined filters. ANY selected genre via EXISTS avoids
-- double counting movies in two selected genres; mean denominator=unique selected ratings.
SELECT date_trunc('month',v.rated_date::timestamp)::date AS month_start,
       v.movie_id,v.title,sum(v.rating_count) AS rating_count,sum(v.rating_sum) AS rating_sum,
       sum(v.rating_sum)::numeric/NULLIF(sum(v.rating_count),0) AS mean_rating
FROM analytics.v_olap_movie_day_segment v
WHERE v.rated_date>=%(start_date)s::date AND v.rated_date<%(end_date)s::date
 AND (%(gender)s::text IS NULL OR v.gender=%(gender)s)
 AND (%(ages)s::text[] IS NULL OR v.age_group=ANY(%(ages)s::text[]))
 AND (%(genres)s::text[] IS NULL OR EXISTS (
  SELECT 1 FROM dw.bridge_movie_genre b JOIN dw.dim_genre g ON g.genre_key=b.genre_key
  WHERE b.movie_key=v.movie_key AND g.genre_name=ANY(%(genres)s::text[])))
GROUP BY month_start,v.movie_id,v.title ORDER BY month_start,rating_count DESC,v.movie_id;
