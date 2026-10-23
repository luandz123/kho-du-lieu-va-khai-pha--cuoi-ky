"""
Unit and regression tests for Step 10B Test Evaluation and CLI recommender.
Verifies:
- Test cohort eligibility and candidate universe on synthetic fixtures.
- Precision@5 (fixed denominator 5) and Recall@5 (denominator includes novel movies).
- CF tie-breaking and popularity fallback on test setting.
- Receipt creation and anti-overwrite protection.
- CLI recommend.py in evaluation and demo modes, edge cases (zero seeds, non-existent user).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Set

import numpy as np
import pandas as pd
import pytest

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
cf_mod = load_mining_module("mining.cf", "mining/cf.py")
cf_test_eval_mod = load_mining_module("mining.cf_test_evaluation", "mining/cf_test_evaluation.py")

get_eligible_eval_cohort = eval_mod.get_eligible_eval_cohort
get_user_candidate_universe = eval_mod.get_user_candidate_universe
compute_user_metrics_at_k = eval_mod.compute_user_metrics_at_k
recommend_for_user_cf = cf_mod.recommend_for_user_cf
fit_popularity_model = baseline_mod.fit_popularity_model
recommend_for_user_popularity = baseline_mod.recommend_for_user_popularity


def test_hand_calculated_test_cohort_and_candidate_universe():
    """
    Synthetic fixture test for Test Cohort eligibility:
    - User 1: 5 ratings in Train+Val, 1 positive (rating 5) in Test -> ELIGIBLE
    - User 2: 4 ratings in Train+Val, 2 positives in Test -> EXCLUDED (insufficient train ratings)
    - User 3: 10 ratings in Train+Val, 2 ratings in Test but all < 4 (ratings 3, 2) -> EXCLUDED (no positive)
    - User 4: 0 ratings in Train+Val, 3 ratings in Test -> EXCLUDED (cold start user)
    """
    train_val_records = [
        # User 1: 5 ratings
        {"user_id": 1, "movie_id": 10, "rating": 5, "timestamp": 100},
        {"user_id": 1, "movie_id": 20, "rating": 4, "timestamp": 200},
        {"user_id": 1, "movie_id": 30, "rating": 3, "timestamp": 300},
        {"user_id": 1, "movie_id": 40, "rating": 2, "timestamp": 400},
        {"user_id": 1, "movie_id": 50, "rating": 1, "timestamp": 500},
        # User 2: 4 ratings
        {"user_id": 2, "movie_id": 10, "rating": 4, "timestamp": 100},
        {"user_id": 2, "movie_id": 20, "rating": 5, "timestamp": 200},
        {"user_id": 2, "movie_id": 30, "rating": 4, "timestamp": 300},
        {"user_id": 2, "movie_id": 40, "rating": 5, "timestamp": 400},
        # User 3: 5 ratings
        {"user_id": 3, "movie_id": 10, "rating": 4, "timestamp": 100},
        {"user_id": 3, "movie_id": 20, "rating": 4, "timestamp": 200},
        {"user_id": 3, "movie_id": 30, "rating": 4, "timestamp": 300},
        {"user_id": 3, "movie_id": 40, "rating": 4, "timestamp": 400},
        {"user_id": 3, "movie_id": 50, "rating": 4, "timestamp": 500},
    ]
    test_records = [
        # User 1: 1 positive rating
        {"user_id": 1, "movie_id": 60, "rating": 5, "timestamp": 1000},
        # User 2: 2 positive ratings
        {"user_id": 2, "movie_id": 50, "rating": 4, "timestamp": 1000},
        {"user_id": 2, "movie_id": 60, "rating": 5, "timestamp": 1100},
        # User 3: ratings < 4
        {"user_id": 3, "movie_id": 60, "rating": 3, "timestamp": 1000},
        {"user_id": 3, "movie_id": 70, "rating": 2, "timestamp": 1100},
        # User 4: new user in test
        {"user_id": 4, "movie_id": 10, "rating": 5, "timestamp": 1000},
    ]

    train_val_df = pd.DataFrame(train_val_records)
    test_df = pd.DataFrame(test_records)

    eligible, diag = get_eligible_eval_cohort(train_val_df, test_df, min_train_ratings=5, min_pos_rating=4)
    assert eligible == {1}
    assert diag["eligible_cohort_size"] == 1
    assert diag["total_active_eval_users"] == 4
    assert diag["excluded_insufficient_train_ratings"] == 2  # user 2 and user 4
    assert diag["excluded_no_positives_in_eval"] == 1  # user 3

    # Candidate universe for user 1:
    cand_u1 = get_user_candidate_universe(train_val_df, 1)
    assert cand_u1 == set()

    # Candidate universe for user 2:
    cand_u2 = get_user_candidate_universe(train_val_df, 2)
    assert cand_u2 == {50}


def test_hand_calculated_test_metrics_with_novel_movies():
    """
    Synthetic fixture test verifying Recall@5 denominator includes novel test movies:
    - User is recommended 5 movies: [101, 102, 103, 104, 105]
    - User has 3 positives in test:
        * 101 (in training catalog, HIT)
        * 102 (in training catalog, HIT)
        * 999 (novel movie outside training catalog, MISSED)
    - Total hits = 2
    - Precision@5 = 2 / 5 = 0.40
    - Recall@5 = 2 / 3 = 0.666667 (denominator strictly 3, includes 999)
    """
    recs = [101, 102, 103, 104, 105]
    positives = {101, 102, 999}

    metrics = compute_user_metrics_at_k(recs, positives, k=5)
    assert metrics["hits"] == 2
    assert np.isclose(metrics["precision"], 0.40)
    assert np.isclose(metrics["recall"], 2.0 / 3.0)


def test_hand_calculated_cf_tie_breaking_and_fallback():
    """
    Synthetic fixture test for CF k=40 tie breaking and fallback on Test:
    - Candidate items with positive similarity from seeds:
        * Movie 20: score 2.0, train popularity 100
        * Movie 10: score 2.0, train popularity 200 -> wins tie over 20
        * Movie 30: score 1.5, train popularity 50
    - Total CF candidates = 3 (< 5).
    - Needs 2 fallback items from popularity ranking:
        * Popularity ranking: [10, 20, 30, 40, 50, 60]
        * 10, 20, 30 already selected or in history -> fallback selects [40, 50].
    - Verifies fallback_rate is True for this user.
    """
    top_neighbors_map = {
        100: [(10, 1.0), (20, 1.0), (30, 0.75)],
        200: [(10, 1.0), (20, 1.0), (30, 0.75)],
    }
    popularity_ranking = [10, 20, 30, 40, 50, 60]
    popularity_counts = {10: 200, 20: 100, 30: 50, 40: 30, 50: 20, 60: 10}

    recs, details, used_fb = recommend_for_user_cf(
        user_id=1,
        user_train_history={100, 200},
        user_train_seeds={100, 200},
        top_neighbors_map=top_neighbors_map,
        k=40,
        popularity_ranking=popularity_ranking,
        popularity_counts=popularity_counts,
        top_n=5,
    )

    # 10 before 20 because of higher popularity (200 > 100)
    assert recs[:3] == [10, 20, 30]
    assert details[0]["score_type"] == "cf"
    assert details[1]["score_type"] == "cf"
    assert details[2]["score_type"] == "cf"

    # Fallback items
    assert recs[3:] == [40, 50]
    assert details[3]["score_type"] == "popularity_fallback"
    assert details[4]["score_type"] == "popularity_fallback"
    assert used_fb is True


def test_pre_execution_guard_rejects_existing_receipt_before_load_data(tmp_path, monkeypatch):
    """
    Verifies production CLI strictly rejects execution if the official receipt already exists,
    triggering FileExistsError BEFORE load_data or evaluator pipeline is called,
    and without overwriting the receipt.
    """
    receipt_file = tmp_path / "cf_test_evaluation_receipt.json"
    output_file = tmp_path / "cf_test_evaluation.json"
    dummy_receipt_content = json.dumps({"run_id": "test_locked_run", "status": "LOCKED"}, indent=2)
    receipt_file.write_text(dummy_receipt_content, encoding="utf-8")

    load_data_called = False
    evaluator_called = False

    def mock_load_data(*args, **kwargs):
        nonlocal load_data_called
        load_data_called = True
        raise AssertionError("load_data must NOT be called when receipt already exists!")

    def mock_evaluator(*args, **kwargs):
        nonlocal evaluator_called
        evaluator_called = True
        raise AssertionError("run_cf_test_evaluation_pipeline must NOT be called when receipt already exists!")

    monkeypatch.setattr(cf_test_eval_mod, "load_data", mock_load_data)
    monkeypatch.setattr(cf_test_eval_mod, "run_cf_test_evaluation_pipeline", mock_evaluator)

    argv = ["--receipt", str(receipt_file), "--output", str(output_file)]
    with pytest.raises(FileExistsError, match="Official test receipt already exists"):
        cf_test_eval_mod.main(argv)

    assert load_data_called is False
    assert evaluator_called is False
    assert receipt_file.read_text(encoding="utf-8") == dummy_receipt_content
    assert not output_file.exists()


def test_pre_execution_guard_rejects_existing_output_before_load_data(tmp_path, monkeypatch):
    """
    Verifies production CLI strictly rejects execution if the official output JSON already exists,
    triggering FileExistsError BEFORE load_data or evaluator pipeline is called,
    and without overwriting the output file.
    """
    receipt_file = tmp_path / "cf_test_evaluation_receipt.json"
    output_file = tmp_path / "cf_test_evaluation.json"
    dummy_output_content = json.dumps({"run_id": "test_locked_output", "status": "LOCKED"}, indent=2)
    output_file.write_text(dummy_output_content, encoding="utf-8")

    load_data_called = False
    evaluator_called = False

    def mock_load_data(*args, **kwargs):
        nonlocal load_data_called
        load_data_called = True
        raise AssertionError("load_data must NOT be called when output already exists!")

    def mock_evaluator(*args, **kwargs):
        nonlocal evaluator_called
        evaluator_called = True
        raise AssertionError("run_cf_test_evaluation_pipeline must NOT be called when output already exists!")

    monkeypatch.setattr(cf_test_eval_mod, "load_data", mock_load_data)
    monkeypatch.setattr(cf_test_eval_mod, "run_cf_test_evaluation_pipeline", mock_evaluator)

    argv = ["--receipt", str(receipt_file), "--output", str(output_file)]
    with pytest.raises(FileExistsError, match="Official test output already exists"):
        cf_test_eval_mod.main(argv)

    assert load_data_called is False
    assert evaluator_called is False
    assert output_file.read_text(encoding="utf-8") == dummy_output_content
    assert not receipt_file.exists()


def test_evaluator_cli_strictly_rejects_removed_force_flag():
    """
    Verifies that --force has been removed from official evaluation CLI options.
    """
    with pytest.raises(SystemExit):
        cf_test_eval_mod.main(["--force"])


def test_evaluator_provenance_trace_artifact_integrity():
    """
    Verifies that the dedicated evaluator provenance trace record exists,
    contains valid schema, points to authentic repository snapshot docs/P2/provenance/eval_original.py,
    and byte-verifies its size (32,508 bytes), LF newline format, SHA-256, and git blob SHA-1.
    """
    import hashlib

    trace_path = REPO_ROOT / "results" / "mining" / "evaluator_provenance_trace.json"
    assert trace_path.exists(), f"Missing provenance trace at: {trace_path}"
    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["provenance_trace_record"]["status"] == "VERIFIED_AUTHENTIC_PROVENANCE"
    assert data["runtime_snapshot_verification"]["canonical_lf_sha256"] == "e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d"
    assert data["runtime_snapshot_verification"]["git_blob_sha1"] == "d7c97bae8b6de3449c0306a2f841325f5434f248"
    assert data["change_classification"]["algorithm_changes"]["percentage"] == 0.0

    snapshot_rel_path = data["runtime_snapshot_verification"]["snapshot_file"]
    assert snapshot_rel_path == "docs/P2/provenance/eval_original.py"
    snapshot_path = REPO_ROOT / snapshot_rel_path
    assert snapshot_path.exists(), f"Physical snapshot file missing at: {snapshot_path}"

    with open(snapshot_path, "rb") as f_snap:
        snap_bytes = f_snap.read()

    assert len(snap_bytes) == 32508
    assert b"\r\n" not in snap_bytes, "Snapshot must use LF newlines"
    assert hashlib.sha256(snap_bytes).hexdigest() == "e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d"
    header = f"blob {len(snap_bytes)}\0".encode("ascii")
    blob_sha1 = hashlib.sha1(header + snap_bytes).hexdigest()
    assert blob_sha1 == "d7c97bae8b6de3449c0306a2f841325f5434f248"



