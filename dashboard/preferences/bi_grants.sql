-- Only these three additional view privileges; no table/schema-wide SELECT.
GRANT USAGE ON SCHEMA analytics, dw TO movielens_bi_reader;
GRANT SELECT ON analytics.v_active_user_cluster,
    analytics.v_active_cluster_genre_profile, dw.v_ml_users TO movielens_bi_reader;
