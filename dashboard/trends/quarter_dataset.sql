-- O4: exactly one row per UTC quarter. Never add year/month rollup rows.
SELECT calendar_year::text || ' Q' || quarter_number::text AS quarter_label,
       make_date(calendar_year,quarter_number*3-2,1) AS quarter_start,
       rating_count,rating_sum,mean_rating,
       make_date(calendar_year,quarter_number*3-2,1) IN
         (SELECT min(make_date(calendar_year,quarter_number*3-2,1)) FROM analytics.v_olap_time_rollup WHERE time_level='quarter')
       OR make_date(calendar_year,quarter_number*3-2,1) IN
         (SELECT max(make_date(calendar_year,quarter_number*3-2,1)) FROM analytics.v_olap_time_rollup WHERE time_level='quarter') AS is_boundary_partial
FROM analytics.v_olap_time_rollup WHERE time_level='quarter'
