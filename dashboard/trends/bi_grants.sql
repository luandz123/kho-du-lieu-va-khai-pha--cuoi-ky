-- Execute as authorized project owner, only against movielens_btl.
-- Existing role/credential preserved. No schema-wide SELECT or default privileges.
GRANT USAGE ON SCHEMA analytics TO movielens_bi_reader;
GRANT SELECT ON analytics.v_olap_time_rollup, analytics.v_olap_genre_quarter TO movielens_bi_reader;
