"""
Unit tests and hand-calculated verification fixtures for Step 9A:
- Temporal Split logic, threshold determination, and boundary tie-handling.
- Cohort eligibility determination and exclusion accounting.
- Candidate universe construction (strictly un-sampled).
- Recommendation metrics: Precision@5, Recall@5 with novel items in denominator.
- Deterministic tie-breaking rules.
- Verification of results/mining/split_manifest.json.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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

load_data = data_io_mod.load_data
verify_and_hash_input_tables = clustering_mod.verify_and_hash_input_tables

compute_temporal_split_thresholds = split_mod.compute_temporal_split_thresholds
split_ratings_by_timestamp = split_mod.split_ratings_by_timestamp
generate_split_manifest = split_mod.generate_split_manifest
FROZEN_T1 = split_mod.FROZEN_T1
FROZEN_T2 = split_mod.FROZEN_T2
DEFAULT_OUTPUT_MANIFEST = split_mod.DEFAULT_OUTPUT_MANIFEST

get_eligible_eval_cohort = eval_mod.get_eligible_eval_cohort
get_user_candidate_universe = eval_mod.get_user_candidate_universe
rank_candidates = eval_mod.rank_candidates
compute_user_metrics_at_k = eval_mod.compute_user_metrics_at_k
compute_macro_metrics = eval_mod.compute_macro_metrics


def test_temporal_split_tie_handling_and_boundary_integrity():
    """
    Unit test with hand-calculated synthetic fixture:
    Verifies that all ratings sharing identical boundary timestamps stay on the same side,
    and that partitions are strictly non-overlapping and preserve all rows.
    """
    synthetic_records = [
        # Timestamps <= 100 (Train)
        {"user_id": 1, "movie_id": 1, "rating": 5, "timestamp": 80},
        {"user_id": 1, "movie_id": 2, "rating": 4, "timestamp": 90},
        {"user_id": 2, "movie_id": 1, "rating": 3, "timestamp": 100},  # Boundary t1
        {"user_id": 3, "movie_id": 2, "rating": 4, "timestamp": 100},  # Boundary t1 duplicate
        {"user_id": 4, "movie_id": 3, "rating": 5, "timestamp": 100},  # Boundary t1 duplicate
        # Timestamps between 101 and 200 (Validation)
        {"user_id": 2, "movie_id": 3, "rating": 4, "timestamp": 110},
        {"user_id": 3, "movie_id": 1, "rating": 5, "timestamp": 150},
        {"user_id": 4, "movie_id": 4, "rating": 2, "timestamp": 200},  # Boundary t2
        {"user_id": 5, "movie_id": 1, "rating": 4, "timestamp": 200},  # Boundary t2 duplicate
        # Timestamps > 200 (Test)
        {"user_id": 1, "movie_id": 4, "rating": 5, "timestamp": 210},
        {"user_id": 5, "movie_id": 2, "rating": 3, "timestamp": 250},
    ]
    df = pd.DataFrame(synthetic_records)
    t1 = 100
    t2 = 200

    parts = split_ratings_by_timestamp(df, t1, t2)
    train_df = parts["train"]
    val_df = parts["validation"]
    test_df = parts["test"]

    # 1. Total row count preserved
    assert len(train_df) + len(val_df) + len(test_df) == len(df) == 11

    # 2. Boundary tie-handling: All 3 records with timestamp=100 must be in Train
    assert len(train_df) == 5
    assert set(train_df["timestamp"]) == {80, 90, 100}
    assert (train_df["timestamp"] == 100).sum() == 3

    # 3. Boundary tie-handling: All 2 records with timestamp=200 must be in Validation
    assert len(val_df) == 4
    assert set(val_df["timestamp"]) == {110, 150, 200}
    assert (val_df["timestamp"] == 200).sum() == 2

    # 4. Test subset strictly > 200
    assert len(test_df) == 2
    assert set(test_df["timestamp"]) == {210, 250}

    # 5. Non-overlapping timestamps
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_real_data_temporal_split_properties():
    """
    Verification test on full canonical MovieLens 1M dataset:
    Verifies frozen thresholds (t1=974862386, t2=976422051), exact partition sizes,
    and row counts strictly summing to 1,000,209.
    """
    tables = load_data("csv")
    ratings = tables["ratings"]
    assert len(ratings) == 1000209

    t1, t2 = compute_temporal_split_thresholds(ratings, 0.70, 0.85)
    assert t1 == FROZEN_T1, f"Expected frozen t1={FROZEN_T1}, got {t1}"
    assert t2 == FROZEN_T2, f"Expected frozen t2={FROZEN_T2}, got {t2}"

    parts = split_ratings_by_timestamp(ratings, t1, t2)
    train_df = parts["train"]
    val_df = parts["validation"]
    test_df = parts["test"]

    # Exactly 700,148 / 150,029 / 150,032
    assert len(train_df) == 700148
    assert len(val_df) == 150029
    assert len(test_df) == 150032
    assert len(train_df) + len(val_df) + len(test_df) == 1000209

    # Strict partition isolation
    assert train_df["timestamp"].max() == 974862386
    assert val_df["timestamp"].min() == 974862390
    assert val_df["timestamp"].max() == 976422042
    assert test_df["timestamp"].min() == 976422054
    assert test_df["timestamp"].max() == 1046454590


def test_hand_calculated_evaluation_cohort():
    """
    Hand-calculated fixture test for user cohort eligibility:
    - User 1: 5 train ratings, 2 eval ratings (one 4-star) -> ELIGIBLE.
    - User 2: 4 train ratings (<5), 3 eval ratings (all 5-star) -> EXCLUDED (insufficient train).
    - User 3: 10 train ratings, 2 eval ratings (ratings 2 and 3) -> EXCLUDED (no positive eval).
    - User 4: 8 train ratings, 0 eval ratings -> EXCLUDED (inactive in eval).
    - User 5: 0 train ratings, 5 eval ratings -> EXCLUDED (cold user in train).
    """
    train_records = []
    # User 1: 5 ratings in train
    for m in range(1, 6):
        train_records.append({"user_id": 1, "movie_id": m, "rating": 4, "timestamp": 10})
    # User 2: 4 ratings in train (<5)
    for m in range(1, 5):
        train_records.append({"user_id": 2, "movie_id": m, "rating": 5, "timestamp": 10})
    # User 3: 10 ratings in train
    for m in range(1, 11):
        train_records.append({"user_id": 3, "movie_id": m, "rating": 4, "timestamp": 10})
    # User 4: 8 ratings in train
    for m in range(1, 9):
        train_records.append({"user_id": 4, "movie_id": m, "rating": 4, "timestamp": 10})

    train_df = pd.DataFrame(train_records)

    eval_records = [
        # User 1: 1 positive (rating 4), 1 non-positive (rating 3)
        {"user_id": 1, "movie_id": 101, "rating": 4, "timestamp": 50},
        {"user_id": 1, "movie_id": 102, "rating": 3, "timestamp": 50},
        # User 2: 3 positive ratings
        {"user_id": 2, "movie_id": 101, "rating": 5, "timestamp": 50},
        {"user_id": 2, "movie_id": 102, "rating": 5, "timestamp": 50},
        {"user_id": 2, "movie_id": 103, "rating": 5, "timestamp": 50},
        # User 3: 2 non-positive ratings (2 and 3)
        {"user_id": 3, "movie_id": 101, "rating": 2, "timestamp": 50},
        {"user_id": 3, "movie_id": 102, "rating": 3, "timestamp": 50},
        # User 5: cold-start user
        {"user_id": 5, "movie_id": 101, "rating": 5, "timestamp": 50},
    ]
    eval_df = pd.DataFrame(eval_records)

    eligible_users, diag = get_eligible_eval_cohort(train_df, eval_df, min_train_ratings=5, min_pos_rating=4)

    # Exactly User 1 must be eligible
    assert eligible_users == {1}
    assert diag["eligible_cohort_size"] == 1
    assert diag["total_active_eval_users"] == 4  # Users 1, 2, 3, 5
    assert diag["excluded_insufficient_train_ratings"] == 2  # Users 2, 5
    assert diag["excluded_no_positives_in_eval"] == 1  # User 3


def test_hand_calculated_candidate_universe_and_no_negative_sampling():
    """
    Hand-calculated fixture test for candidate universe:
    Catalog in train: {10, 20, 30, 40, 50}.
    User 1 rated {10, 20} in train.
    Candidate universe for User 1 MUST be exactly {30, 40, 50}.
    """
    train_records = [
        {"user_id": 1, "movie_id": 10, "rating": 4, "timestamp": 1},
        {"user_id": 1, "movie_id": 20, "rating": 5, "timestamp": 2},
        {"user_id": 2, "movie_id": 30, "rating": 4, "timestamp": 3},
        {"user_id": 3, "movie_id": 40, "rating": 3, "timestamp": 4},
        {"user_id": 4, "movie_id": 50, "rating": 5, "timestamp": 5},
    ]
    train_df = pd.DataFrame(train_records)

    cands = get_user_candidate_universe(train_df, user_id=1)
    assert cands == {30, 40, 50}
    # User's rated items strictly excluded
    assert 10 not in cands
    assert 20 not in cands


def test_hand_calculated_precision_and_recall_denominator():
    """
    Hand-calculated fixture test for Precision@5 and Recall@5:
    - User has positive items in eval: {30, 40, 999} where 999 is a NOVEL item (not in train).
      Total positive items = 3.
    - System recommends Top-5: [30, 50, 60, 70, 80] (hit on 30).
    - Precision@5 = 1 / 5 = 0.20
    - Recall@5 = 1 / 3 = 0.3333333333333333
    - When system only has 3 candidates to recommend: [30, 50, 60] (hit on 30)
      Precision@5 = 1 / 5 = 0.20 (denominator fixed to 5).
      Recall@5 = 1 / 3 = 0.3333333333333333
    """
    positives = {30, 40, 999}  # 999 is a cold-start item
    recommended_full = [30, 50, 60, 70, 80]

    metrics = compute_user_metrics_at_k(recommended_full, positives, k=5)
    assert metrics["hits"] == 1
    assert np.isclose(metrics["precision"], 0.20)
    assert np.isclose(metrics["recall"], 1.0 / 3.0)

    # When fewer than K items returned
    recommended_short = [30, 50, 60]
    metrics_short = compute_user_metrics_at_k(recommended_short, positives, k=5)
    assert metrics_short["hits"] == 1
    assert np.isclose(metrics_short["precision"], 0.20)  # Still divided by 5
    assert np.isclose(metrics_short["recall"], 1.0 / 3.0)


def test_hand_calculated_tie_breaking_rules():
    """
    Hand-calculated fixture test for deterministic tie-breaking:
    1. Score descending (-score)
    2. Training history popularity descending (-popularity)
    3. movie_id ascending (+movie_id)
    """
    scores = {
        10: 2.5,  # pop 50
        20: 2.5,  # pop 100
        30: 2.5,  # pop 100, id 30
        40: 2.5,  # pop 100, id 40
        50: 3.0,  # score 3.0 (highest score)
        60: 1.0,  # lowest score
    }
    popularity = {
        10: 50,
        20: 100,
        30: 100,
        40: 100,
        50: 10,
        60: 500,
    }
    ranked = rank_candidates(scores, popularity, top_k=5)

    # Expected order:
    # 1. movie 50 (score 3.0)
    # 2. movie 20, 30, 40 all have score 2.5 and pop 100 -> sorted by movie_id ASC: 20, 30, 40
    # 3. movie 10 (score 2.5, pop 50)
    assert ranked == [50, 20, 30, 40, 10]


def test_hand_calculated_relevant_outside_candidate_universe_and_macro_average():
    """
    Hand-calculated fixture test for:
    1. Positive items lying outside candidate universe (novel items in evaluation).
    2. Preservation of complete positive items in individual user Recall@5 denominator.
    3. Macro-averaging across the eligible cohort.
    
    Scenario:
    - User 1:
        Positive items in eval: {10, 20, 999} (3 items). Item 999 is novel (outside train catalog).
        Train history: {101, 102, 103, 104, 105}.
        Train catalog: {10, 20, 30, 40, 50, 101, 102, 103, 104, 105}.
        Candidate universe: {10, 20, 30, 40, 50} (Item 999 is strictly absent).
        Recommended Top-5: [10, 30, 40, 50, 60] (hit on 10).
        Precision@5 = 1 / 5 = 0.20
        Recall@5 = 1 / 3 = 0.3333333333333333 (denominator strictly includes 999).
    - User 2:
        Positive items in eval: {10, 20} (2 items, both in train catalog).
        Recommended Top-5: [10, 20, 30, 40, 50] (hits on 10, 20).
        Precision@5 = 2 / 5 = 0.40
        Recall@5 = 2 / 2 = 1.00
    - Cohort Macro-Averaging over {User 1, User 2}:
        Macro-Precision@5 = (0.20 + 0.40) / 2 = 0.30
        Macro-Recall@5 = (1/3 + 1.0) / 2 = 2/3 = 0.6666666666666666
    """
    train_records = [
        {"user_id": 1, "movie_id": 101, "rating": 5, "timestamp": 1},
        {"user_id": 1, "movie_id": 102, "rating": 5, "timestamp": 2},
        {"user_id": 1, "movie_id": 103, "rating": 4, "timestamp": 3},
        {"user_id": 1, "movie_id": 104, "rating": 4, "timestamp": 4},
        {"user_id": 1, "movie_id": 105, "rating": 5, "timestamp": 5},
        {"user_id": 2, "movie_id": 10, "rating": 4, "timestamp": 6},
        {"user_id": 2, "movie_id": 20, "rating": 4, "timestamp": 7},
        {"user_id": 2, "movie_id": 30, "rating": 4, "timestamp": 8},
        {"user_id": 2, "movie_id": 40, "rating": 4, "timestamp": 9},
        {"user_id": 2, "movie_id": 50, "rating": 4, "timestamp": 10},
    ]
    train_df = pd.DataFrame(train_records)

    # 1. Candidate universe for User 1 does NOT contain 999
    cands_u1 = get_user_candidate_universe(train_df, user_id=1)
    assert 999 not in cands_u1
    assert cands_u1 == {10, 20, 30, 40, 50}

    # 2. Metric calculation per user
    u1_recs = [10, 30, 40, 50, 60]
    u1_positives = {10, 20, 999}
    m1 = compute_user_metrics_at_k(u1_recs, u1_positives, k=5)
    assert m1["hits"] == 1
    assert np.isclose(m1["precision"], 0.20)
    assert np.isclose(m1["recall"], 1.0 / 3.0)

    u2_recs = [10, 20, 30, 40, 50]
    u2_positives = {10, 20}
    m2 = compute_user_metrics_at_k(u2_recs, u2_positives, k=5)
    assert m2["hits"] == 2
    assert np.isclose(m2["precision"], 0.40)
    assert np.isclose(m2["recall"], 1.00)

    # 3. Macro aggregation across cohort
    user_metrics_list = [m1, m2]
    macro = compute_macro_metrics(user_metrics_list)
    assert np.isclose(macro["macro_precision"], 0.30)
    assert np.isclose(macro["macro_recall"], 2.0 / 3.0)
    assert macro["total_users"] == 2


def test_split_manifest_contract_and_structure():
    """
    Artifact verification:
    Verifies results/mining/split_manifest.json adheres to contract v2,
    has correct partition counts, and contains cohort diagnostics.
    """
    assert DEFAULT_OUTPUT_MANIFEST.exists(), f"Missing {DEFAULT_OUTPUT_MANIFEST}"
    with open(DEFAULT_OUTPUT_MANIFEST, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["contract_version"] == 2
    assert meta["split_strategy"] == "temporal_global_quantiles"
    assert "quantile_method" in meta
    assert "epoch_conversion" in meta
    assert meta["boundary_operators"]["train"] == "timestamp <= t1"
    assert meta["boundary_operators"]["validation"] == "t1 < timestamp <= t2"
    assert meta["boundary_operators"]["test"] == "timestamp > t2"
    assert meta["total_dataset_ratings"] == 1000209
    assert meta["thresholds"]["t1"] == 974862386
    assert meta["thresholds"]["t2"] == 976422051

    # Partitions row counts
    parts = meta["partitions"]
    assert parts["train"]["row_count"] == 700148
    assert parts["validation"]["row_count"] == 150029
    assert parts["test"]["row_count"] == 150032

    # Validation cohort analysis
    val_cohort = meta["cohort_analysis"]["validation_phase"]["metrics"]
    assert val_cohort["total_active_users_in_eval"] == 1352
    assert val_cohort["eligible_users_count"] == 471
    assert val_cohort["excluded_insufficient_train_ratings_count"] == 849
    assert val_cohort["excluded_no_positives_in_eval_count"] == 32
    assert val_cohort["novel_movies_in_eval_count"] == 36
    assert val_cohort["novel_positive_movies_in_eval_count"] == 9
    assert val_cohort["novel_positive_movies_in_cohort_count"] == 3
    assert val_cohort["novel_positive_movies_in_cohort_ids"] == [192, 712, 1471]

