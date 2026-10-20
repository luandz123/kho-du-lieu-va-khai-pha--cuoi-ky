-- O5: one genre x UTC quarter. All windows/denominators precede display filters.
-- Approved view zero-fills before LAG; previous=0 -> NULL; threshold fixed at100.
WITH eligible AS (
 SELECT genre_name,quarter_start,
        row_number() OVER(PARTITION BY quarter_start ORDER BY qoq_pct DESC,rating_count DESC,genre_name ASC) AS growth_rank
 FROM analytics.v_olap_genre_quarter WHERE eligible_for_ranking
), full_series AS (
 SELECT v.*,e.growth_rank,
        extract(year FROM v.quarter_start)::int::text || ' Q' || extract(quarter FROM v.quarter_start)::int::text AS quarter_label
 FROM analytics.v_olap_genre_quarter v LEFT JOIN eligible e USING(genre_name,quarter_start)
)
SELECT *,CASE WHEN is_boundary_partial THEN 'Quý biên: thiếu quan sát'
              WHEN previous_is_boundary_partial THEN 'Quý trước là quý biên: không xếp hạng'
              WHEN NOT passes_fixed_100_threshold THEN 'Quý trước <100 hoặc chưa có: không xếp hạng'
              ELSE 'Đủ điều kiện xếp hạng (toàn bộ 18 genre)' END AS ranking_status,
       CASE WHEN growth_rank=1 AND qoq_pct<0 THEN 'Hạng 1: giảm ít nhất'
            WHEN growth_rank=1 THEN 'Hạng 1: tăng dương'
            WHEN growth_rank IS NULL THEN 'N/A: không xếp hạng'
            ELSE 'Đã xếp hạng' END AS rank_interpretation
FROM full_series
