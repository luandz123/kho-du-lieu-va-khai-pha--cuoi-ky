-- S11A dataset grain: one source user-movie rating. UTC timestamp is typed,
-- title join is one-to-one; no genre bridge. Superset filters before GROUP BY/LIMIT.
SELECT r.user_id,r.movie_id,m.title,r.rating,
       1::bigint AS rating_count,r.rating::bigint AS rating_sum,
       (r.rated_at::timestamptz AT TIME ZONE 'UTC') AS rated_at_utc
FROM dw.v_ml_ratings r JOIN dw.v_ml_movies m ON m.movie_id=r.movie_id
