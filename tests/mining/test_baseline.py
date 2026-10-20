"""
Unit Tests and Hand-Calculated Fixtures for Popularity Baseline (Step 9B).
Validates:
- Deterministic popularity ranking: count DESC, movie_id ASC.
- Exclusion of user training history.
- Handling of short candidate universe (< 5 items) with fixed Precision@5 denominator.
- Handling of novel positive items outside candidate universe in Recall@5 denominator.
- Macro-averaging across eligible evaluation cohort.
- Integrity of results/mining/baseline_popularity_validation.json artifact.
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

# Robustly load mining modules from repository root to prevent shadowing with tests/mining package
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def load_mining_module(mod_name: str, rel_path: str):
    full_path = REPO_ROOT / rel_path
    if mod_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(mod_name, full_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        return mod
    return sys.modules[mod_name]

data_io_mod = load_mining_module("mining.data_io", "mining/data_io.py")
features_mod = load_mining_module("mining.features", "mining/features.py")
clustering_mod = load_mining_module("mining.clustering", "mining/clustering.py")
split_mod = load_mining_module("mining.split", "mining/split.py")
eval_mod = load_mining_module("mining.evaluation", "mining/evaluation.py")
baseline_mod = load_mining_module("mining.baseline", "mining/baseline.py")

fit_popularity_model = baseline_mod.fit_popularity_model
recommend_for_user_popularity = baseline_mod.recommend_for_user_popularity
run_popularity_validation_pipeline = baseline_mod.run_popularity_validation_pipeline
DEFAULT_BASELINE_OUTPUT = baseline_mod.DEFAULT_BASELINE_OUTPUT

compute_user_metrics_at_k = eval_mod.compute_user_metrics_at_k
compute_macro_metrics = eval_mod.compute_macro_metrics


def test_hand_calculated_popularity_fit_and_ranking():
    """
    Hand-calculated fixture test for Popularity model fitting:
    - Verifies that ALL ratings (1..5) are counted, not just positive (>=4).
    - Verifies tie-breaking: count DESC, movie_id ASC.
    
    Data:
    - Movie 10: 4 ratings (ratings: 1, 1, 2, 3) -> count = 4 (even though 0 ratings >= 4!)
    - Movie 20: 3 ratings (ratings: 4, 5, 5) -> count = 3
    - Movie 30: 3 ratings (ratings: 5, 5, 5) -> count = 3 (tie with Movie 20, 20 < 30)
    - Movie 40: 1 rating (rating: 5) -> count = 1
    
    Expected ranking: [10, 20, 30, 40]
    """
    train_records = [
        {"user_id": 1, "movie_id": 10, "rating": 1, "timestamp": 1},
        {"user_id": 2, "movie_id": 10, "rating": 1, "timestamp": 2},
        {"user_id": 3, "movie_id": 10, "rating": 2, "timestamp": 3},
        {"user_id": 4, "movie_id": 10, "rating": 3, "timestamp": 4},
        {"user_id": 1, "movie_id": 20, "rating": 4, "timestamp": 5},
        {"user_id": 2, "movie_id": 20, "rating": 5, "timestamp": 6},
        {"user_id": 3, "movie_id": 20, "rating": 5, "timestamp": 7},
        {"user_id": 1, "movie_id": 30, "rating": 5, "timestamp": 8},
        {"user_id": 2, "movie_id": 30, "rating": 5, "timestamp": 9},
        {"user_id": 3, "movie_id": 30, "rating": 5, "timestamp": 10},
        {"user_id": 1, "movie_id": 40, "rating": 5, "timestamp": 11},
    ]
    train_df = pd.DataFrame(train_records)

    pop_df = fit_popularity_model(train_df)
    ranked_movies = pop_df["movie_id"].tolist()
    counts = pop_df["rating_count"].tolist()

    assert ranked_movies == [10, 20, 30, 40]
    assert counts == [4, 3, 3, 1]


def test_hand_calculated_user_recommendation_and_history_exclusion():
    """
    Hand-calculated fixture test for recommendation filtering:
    - Global ranking: [10, 20, 30, 40, 50, 60]
    - User train history: {10, 30}
    - Recommended Top-3: [20, 40, 50] (10 and 30 strictly excluded)
    """
    ranking = [10, 20, 30, 40, 50, 60]
    user_hist = {10, 30}

    recs = recommend_for_user_popularity(user_hist, ranking, top_k=3)
    assert recs == [20, 40, 50]
    assert 10 not in recs
    assert 30 not in recs


def test_hand_calculated_short_candidate_universe_and_novel_items():
    """
    Hand-calculated fixture test for edge cases:
    1. Short candidate list (<5 items): System returns all available items (2 items).
       Precision@5 denominator is STILL 5.
    2. Novel positive item outside train catalog:
       User has positive items in eval: {20, 999} where 999 is novel (outside train).
       Recommended: [20, 30] (hits on 20).
       Precision@5 = 1 / 5 = 0.20
       Recall@5 = 1 / 2 = 0.50 (denominator includes 999).
    """
    ranking = [10, 20, 30]
    user_hist = {10}  # Candidate universe: {20, 30} (only 2 items available)

    recs = recommend_for_user_popularity(user_hist, ranking, top_k=5)
    assert recs == [20, 30]
    assert len(recs) == 2  # Shorter than K=5

    positives = {20, 999}  # 999 is a novel item
    metrics = compute_user_metrics_at_k(recs, positives, k=5)
    assert metrics["hits"] == 1
    assert np.isclose(metrics["precision"], 0.20)  # 1 / 5
    assert np.isclose(metrics["recall"], 0.50)     # 1 / 2


def test_hand_calculated_pipeline_macro_metrics():
    """
    Hand-calculated fixture test for complete pipeline macro aggregation:
    - User 1:
        recs = [10, 20, 30, 40, 50]
        positives = {10, 60} (2 items)
        hits = 1 (on 10)
        precision = 1 / 5 = 0.20
        recall = 1 / 2 = 0.50
    - User 2:
        recs = [10, 20, 30, 40, 50]
        positives = {10, 20} (2 items)
        hits = 2 (on 10, 20)
        precision = 2 / 5 = 0.40
        recall = 2 / 2 = 1.00
    - Cohort Macro Aggregation:
        Macro-Precision@5 = (0.20 + 0.40) / 2 = 0.30
        Macro-Recall@5    = (0.50 + 1.00) / 2 = 0.75
    """
    u1_recs = [10, 20, 30, 40, 50]
    u1_pos = {10, 60}
    m1 = compute_user_metrics_at_k(u1_recs, u1_pos, k=5)

    u2_recs = [10, 20, 30, 40, 50]
    u2_pos = {10, 20}
    m2 = compute_user_metrics_at_k(u2_recs, u2_pos, k=5)

    macro = compute_macro_metrics([m1, m2])
    assert np.isclose(macro["macro_precision"], 0.30)
    assert np.isclose(macro["macro_recall"], 0.75)
    assert macro["total_users"] == 2


def test_real_data_popularity_baseline_artifact():
    """
    Artifact verification test for results/mining/baseline_popularity_validation.json:
    - Validates schema, metadata, candidate universe bounds, and exact macro metrics on canonical data.
    """
    assert DEFAULT_BASELINE_OUTPUT.exists(), f"Missing {DEFAULT_BASELINE_OUTPUT}"
    with open(DEFAULT_BASELINE_OUTPUT, "r", encoding="utf-8") as f:
        res = json.load(f)

    assert res["contract_version"] == 2
    assert res["model_name"] == "popularity"
    assert res["evaluation_phase"] == "validation"
    assert res["top_k"] == 5
    assert res["cutoff"] == 5
    assert res["training_cutoff_timestamp"] == 974862386
    assert res["evaluation_cutoff_timestamp"] == 976422051

    # Thresholds
    assert res["thresholds"]["t1"] == 974862386
    assert res["thresholds"]["t2"] == 976422051

    # Provenance and hashes
    assert "split_manifest_sha256" in res["provenance"]
    assert "baseline_code_sha256" in res["provenance"]
    assert "config_hash" in res["provenance"]
    assert "canonical_hashes" in res
    assert "users" in res["canonical_hashes"]
    assert "movies" in res["canonical_hashes"]
    assert "movie_genres" in res["canonical_hashes"]
    assert "ratings" in res["canonical_hashes"]

    # Cohort checks
    cohort = res["cohort"]
    assert cohort["eligible_cohort_size"] == 471
    assert cohort["total_active_eval_users"] == 1352
    assert cohort["excluded_users_count"] == 881
    assert np.isclose(cohort["exclusion_rate_percentage"], 65.1627, atol=1e-3)
    assert cohort["excluded_insufficient_train_count"] == 849
    assert cohort["excluded_no_positives_in_eval_count"] == 32
    assert cohort["short_candidate_universe_users_count"] == 0
    assert cohort["eligible_user_ids_hash"] == "ba0f9648c46999712f4339a81f0b6c0cb45b4bd3bc5ad1184d8885e580fd101f"

    # Per-user candidate universe bounds
    cand_stats = cohort["candidate_universe_stats"]
    assert cand_stats["training_catalog_size"] == 3633
    assert cand_stats["min_candidates_per_user"] == 2193
    assert cand_stats["max_candidates_per_user"] == 3628

    # Novel movies breakdown
    novel = res["novel_movies_breakdown"]
    assert novel["all_validation_novel_movies"]["count"] == 36
    assert novel["all_validation_novel_movies"]["denominator_total_validation_catalog"] == 3426

    assert novel["all_validation_novel_positive_movies"]["count"] == 9
    assert novel["all_validation_novel_positive_movies"]["denominator_total_validation_positive_movies"] == 3072

    assert novel["eligible_cohort_novel_positive_movies"]["count"] == 3
    assert novel["eligible_cohort_novel_positive_movies"]["denominator_total_cohort_positive_movies"] == 2445
    assert novel["eligible_cohort_novel_positive_movies"]["movie_ids"] == [192, 712, 1471]

    # Metrics on real MovieLens 1M
    metrics = res["metrics"]
    assert metrics["top_k"] == 5
    assert metrics["total_evaluated_users"] == 471
    assert metrics["total_hits"] == 400
    assert np.isclose(metrics["macro_precision_at_5"], 0.169851, atol=1e-5)
    assert np.isclose(metrics["macro_recall_at_5"], 0.031261, atol=1e-5)

    # Popularity items summary
    fit_summary = res["popularity_fit_summary"]
    assert fit_summary["training_items_count"] == 3633
    assert fit_summary["top_10_popular_movie_ids"] == [2858, 1196, 260, 1210, 589, 2028, 480, 1270, 608, 593]


def test_pipeline_strictly_rejects_non_top_5():
    """
    Regression test: run_popularity_validation_pipeline must reject any top_k != 5
    (including top_k=10 and top_k=0) before computing or generating results.
    """
    empty_df = pd.DataFrame(columns=["user_id", "movie_id", "rating", "timestamp"])

    with pytest.raises(ValueError, match="top_k=5"):
        run_popularity_validation_pipeline(ratings_df=empty_df, top_k=10)

    with pytest.raises(ValueError, match="top_k=5"):
        run_popularity_validation_pipeline(ratings_df=empty_df, top_k=0)

    with pytest.raises(ValueError, match="top_k=5"):
        run_popularity_validation_pipeline(ratings_df=empty_df, top_k=3)


def test_cli_rejects_non_top_5_without_touching_output(tmp_path):
    """
    Regression test: CLI must reject any --top-k != 5 with non-zero exit code
    before loading data and must not create or overwrite the output file.
    """
    baseline_script = REPO_ROOT / "mining" / "baseline.py"

    # Test top_k=10 on non-existent file: must fail with nonzero and not create file
    out_file_10 = tmp_path / "out_10.json"
    proc_10 = subprocess.run(
        [sys.executable, str(baseline_script), "--top-k", "10", "--output", str(out_file_10)],
        capture_output=True,
        text=True,
    )
    assert proc_10.returncode != 0
    assert not out_file_10.exists()
    assert "invalid choice" in proc_10.stderr or "top-k" in proc_10.stderr

    # Test top_k=0 on existing file: must fail with nonzero and preserve existing file content
    out_file_0 = tmp_path / "out_0.json"
    sentinel_content = '{"sentinel_preserved": true}'
    out_file_0.write_text(sentinel_content, encoding="utf-8")
    proc_0 = subprocess.run(
        [sys.executable, str(baseline_script), "--top-k", "0", "--output", str(out_file_0)],
        capture_output=True,
        text=True,
    )
    assert proc_0.returncode != 0
    assert out_file_0.read_text(encoding="utf-8") == sentinel_content
