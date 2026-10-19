-- Independent SQL reference for each interval. Use NULL bounds for full history.
-- Bind UTC-aware :start_utc and :end_utc (inclusive / exclusive).
WITH filtered AS (
 SELECT f.* FROM dw.fact_rating f
 WHERE (CAST(:start_utc AS timestamptz) IS NULL OR f.rated_at>=CAST(:start_utc AS timestamptz))
   AND (CAST(:end_utc AS timestamptz) IS NULL OR f.rated_at<CAST(:end_utc AS timestamptz))
)
SELECT count(*) AS rating_count,sum(rating) AS rating_sum,
 count(DISTINCT user_key) AS rated_users,count(DISTINCT movie_key) AS rated_movies,
 sum(rating)::numeric/nullif(count(*),0) AS weighted_mean FROM filtered;
-- The executed references and three interval parameters are recorded by reconcile.py
-- and evidence/reconciliation.json, including star GROUP BY and explicit three-key Top10.
SELECT count(*) AS fixed_catalog_movies FROM dw.dim_movie;
