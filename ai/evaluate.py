"""Đánh giá gợi ý hybrid theo ĐÚNG giao thức của bản cũ để so sánh công bằng:

  - Chia theo thời gian: t1 = 974862386, t2 = 976422051 (results/mining/split_manifest.json).
      Chọn α:  huấn luyện trên rating ≤ t1, đánh giá trên (t1, t2]
      Kiểm tra: huấn luyện trên rating ≤ t2, đánh giá trên > t2   (1.154 người dùng)
  - Người dùng được đánh giá: ≥ 5 rating khi huấn luyện và ≥ 1 rating ≥ 4 trong giai đoạn đánh giá.
  - Ứng viên: mọi phim trong tập huấn luyện trừ phim user đã chấm. Không lấy mẫu âm.
  - Chỉ số: Precision@5, Recall@5, trung bình theo người dùng (macro).

Thêm thí nghiệm cold-start: mỗi người dùng chỉ giữ 3 rating ≥ 4 SỚM NHẤT (giả lập người mới),
so sánh CF và hybrid trên cùng tập người dùng.

Chạy: python -m ai.evaluate        -> results/mining/hybrid_evaluation.json
"""
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2

from ai.hybrid import HybridRecommender
from mining.evaluation import compute_macro_metrics, compute_user_metrics_at_k, get_eligible_eval_cohort
from pipeline import config, lake
from transform.duck import connect

T1, T2 = 974862386, 976422051
ALPHAS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.3, 0.0]
OUT = Path("results/mining/hybrid_evaluation.json")


def load_ratings() -> pd.DataFrame:
    df = connect().execute(f"""
        SELECT user_id, movie_id, rating, epoch(rated_at)::BIGINT AS ts
        FROM read_parquet('{lake.path('silver', 'ratings', 'data.parquet')}')""").df()
    return df


def load_embeddings() -> dict[int, np.ndarray]:
    with psycopg2.connect(config.dw_dsn()) as conn, conn.cursor() as cur:
        cur.execute("SELECT m.movie_id, e.embedding::text FROM dw.movie_embedding e JOIN dw.dim_movie m USING (movie_key)")
        return {mid: np.array(json.loads(v), dtype=np.float32) for mid, v in cur.fetchall()}


def evaluate(model: HybridRecommender, train: pd.DataFrame, test: pd.DataFrame, alpha: float,
             history_override: dict[int, dict[int, int]] | None = None) -> dict:
    cohort, _ = get_eligible_eval_cohort(train, test)
    positives = test[test.rating >= 4].groupby("user_id")["movie_id"].apply(set).to_dict()
    history = train.groupby("user_id").apply(lambda g: dict(zip(g.movie_id, g.rating)), include_groups=False).to_dict()
    metrics = []
    for u in sorted(cohort):
        h = (history_override or history)[u]
        recs = model.recommend(h, alpha=alpha, top_n=5)
        metrics.append(compute_user_metrics_at_k([r.movie_id for r in recs], positives[u], k=5))
    m = compute_macro_metrics(metrics)
    return {"alpha": alpha, "users": len(cohort),
            "precision_at_5": round(m["macro_precision"], 6), "recall_at_5": round(m["macro_recall"], 6)}


def main():
    ratings = load_ratings()
    emb = load_embeddings()
    print(f"{len(ratings):,} rating, {len(emb):,} vector phim")

    # 1. Chọn α trên tập validation
    train_v, val = ratings[ratings.ts <= T1], ratings[(ratings.ts > T1) & (ratings.ts <= T2)]
    model_v = HybridRecommender(emb).fit(train_v)
    validation = []
    for a in ALPHAS:
        r = evaluate(model_v, train_v, val, a)
        validation.append(r)
        print("validation", r)
    best = max((r for r in validation if 0 < r["alpha"] < 1), key=lambda r: (r["recall_at_5"], r["alpha"]))
    best_alpha = best["alpha"]

    # 2. Kiểm tra trên tập test với α đã chốt
    train_t, test = ratings[ratings.ts <= T2], ratings[ratings.ts > T2]
    model_t = HybridRecommender(emb).fit(train_t)
    test_results = {name: evaluate(model_t, train_t, test, a)
                    for name, a in [("cf_only", 1.0), ("content_only", 0.0), ("hybrid", best_alpha)]}
    for k, v in test_results.items():
        print("test", k, v)

    # 3. Cold-start: chỉ giữ 3 rating ≥ 4 sớm nhất của mỗi người
    early = (train_t[train_t.rating >= 4].sort_values(["user_id", "ts", "movie_id"])
             .groupby("user_id").head(3))
    cold_hist = early.groupby("user_id").apply(lambda g: dict(zip(g.movie_id, g.rating)), include_groups=False).to_dict()
    cohort, _ = get_eligible_eval_cohort(train_t, test)
    cold_hist = {u: cold_hist.get(u, {}) for u in cohort}
    cold = {name: evaluate(model_t, train_t, test, a, history_override=cold_hist)
            for name, a in [("cf_only", 1.0), ("content_only", 0.0), ("hybrid", best_alpha)]}
    for k, v in cold.items():
        print("cold-start", k, v)

    OUT.write_text(json.dumps({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "temporal split t1/t2 giống bản cũ; macro P@5, R@5; ứng viên = catalog train trừ lịch sử",
        "embedding_model": "intfloat/multilingual-e5-small",
        "validation_alpha_grid": validation, "chosen_alpha": best_alpha,
        "test": test_results, "cold_start_3_ratings": cold,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("->", OUT)


if __name__ == "__main__":
    main()
