-- Independent source for S11C checks: no analytics view in the expected result.
-- Aggregate history only, no user-level evidence is exported.
SELECT date_trunc('quarter',f.rated_at AT TIME ZONE 'UTC')::date AS quarter_start,
       count(*) AS rating_count,sum(f.rating) AS rating_sum
FROM dw.fact_rating f GROUP BY 1 ORDER BY 1;

SELECT date_trunc('quarter',f.rated_at AT TIME ZONE 'UTC')::date AS quarter_start,
       g.genre_name,count(*) AS rating_count
FROM dw.fact_rating f JOIN dw.bridge_movie_genre b ON b.movie_key=f.movie_key
JOIN dw.dim_genre g ON g.genre_key=b.genre_key GROUP BY 1,2 ORDER BY 1,2;
