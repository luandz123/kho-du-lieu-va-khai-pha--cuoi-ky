-- Grain: one original user in the single active+valid model, including insufficient.
-- Window denominators are computed BEFORE outer native filters.
SELECT c.user_id, c.cluster_id, c.status, c.model_version, u.gender, u.age_group,
       CASE c.cluster_id
         WHEN 0 THEN '0 · Đa dạng / cân bằng'
         WHEN 1 THEN '1 · Drama / tình cảm'
         WHEN 2 THEN '2 · Comedy'
         WHEN 3 THEN '3 · Action / Sci-Fi / Thriller'
         ELSE 'Thiếu bằng chứng' END AS cluster_label,
       COUNT(*) FILTER (WHERE c.status='assigned') OVER () AS assigned_total,
       COUNT(*) FILTER (WHERE c.status='assigned') OVER (PARTITION BY c.cluster_id) AS original_cluster_n,
       COUNT(*) FILTER (WHERE c.status='assigned') OVER (PARTITION BY u.gender) AS baseline_gender_n,
       COUNT(*) FILTER (WHERE c.status='assigned') OVER (PARTITION BY u.age_group) AS baseline_age_n
FROM analytics.v_active_user_cluster c
JOIN dw.v_ml_users u USING (user_id)
