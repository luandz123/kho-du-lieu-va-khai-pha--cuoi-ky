-- Grain: cluster x genre in the single active+valid model. No user join.
-- Precomputed positive-rating preference, NOT recomputed by demographic filters.
SELECT cluster_id, genre_name, mean_preference, n_users, model_version,
       CASE cluster_id
         WHEN 0 THEN '0 · Đa dạng / cân bằng'
         WHEN 1 THEN '1 · Drama / tình cảm'
         WHEN 2 THEN '2 · Comedy'
         WHEN 3 THEN '3 · Action / Sci-Fi / Thriller' END AS cluster_label
FROM analytics.v_active_cluster_genre_profile
