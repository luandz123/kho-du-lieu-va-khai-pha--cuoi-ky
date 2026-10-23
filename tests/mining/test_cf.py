"""
Unit Tests and Hand-Calculated Fixtures for Item-Based Collaborative Filtering (Step 10A).
Validates:
- Cosine similarity computation on sparse representations (zero diagonal, positive similarities only).
- Nearest neighbor search with deterministic tie-breaking (similarity DESC, movie_id ASC).
- Scoring direction: sum of sim(i, j) for seed j where i in N_k(j).
- History filtering and recommendation tie-breaking (score DESC, train_pop DESC, movie_id ASC).
- Popularity fallback mechanism when CF candidates < 5.
- Fixed Precision@5 denominator (5) and Recall@5 denominator including novel items.
- Strict enforcement of top_n=5 recommendation cutoff.
- Integrity and reproducibility of results/mining/cf_validation_experiments.json artifact.
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

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

build_sparse_ratings_matrix = cf_mod.build_sparse_ratings_matrix
compute_item_cosine_similarities_top_k = cf_mod.compute_item_cosine_similarities_top_k
recommend_for_user_cf = cf_mod.recommend_for_user_cf
evaluate_cf_validation_pipeline = cf_mod.evaluate_cf_validation_pipeline
DEFAULT_CF_OUTPUT = cf_mod.DEFAULT_CF_OUTPUT

compute_user_metrics_at_k = eval_mod.compute_user_metrics_at_k
compute_macro_metrics = eval_mod.compute_macro_metrics


def test_hand_calculated_cosine_similarity_properties():
    """
    Hand-calculated fixture test for item cosine similarity:
    - M1: [3, 4] -> norm = 5
    - M2: [4, 3] -> norm = 5 -> dot product = 24 -> cosine = 24 / 25 = 0.96
    - M3: [0, 5] -> norm = 5 -> dot product with M1 = 20 -> cosine = 20 / 25 = 0.80
    - M4: [0, 0] -> zero vector -> no positive cosine
    
    Verifies:
    - Diagonal is zero (no self-similarity).
    - Only positive similarities (sim > 0) are retained.
    - Tie-breaking: similarity DESC, movie_id ASC.
    """
    # 4 movies, 2 users
    data = np.array([3, 4, 4, 3, 5], dtype=np.float32)
    rows = np.array([0, 0, 1, 1, 2], dtype=np.int32)
    cols = np.array([0, 1, 0, 1, 1], dtype=np.int32)
    R = csr_matrix((data, (rows, cols)), shape=(4, 2))

    idx_to_movie = {0: 10, 1: 20, 2: 30, 3: 40}
    neighbors_map = compute_item_cosine_similarities_top_k(R, idx_to_movie, max_k=5, batch_size=2)

    # Movie 10 neighbors: M20 (0.96), M30 (0.80). M10 self-sim is 0. M40 has 0 sim.
    m10_neighbors = neighbors_map[10]
    assert len(m10_neighbors) == 2
    assert m10_neighbors[0][0] == 20
    assert np.isclose(m10_neighbors[0][1], 0.96)
    assert m10_neighbors[1][0] == 30
    assert np.isclose(m10_neighbors[1][1], 0.80)

    # Movie 40 has 0 neighbors
    assert len(neighbors_map[40]) == 0


def test_hand_calculated_seed_top_k_direction_and_scoring():
    """
    Hand-calculated fixture test for seed-to-candidate scoring direction:
    Rule: Score(u, i) = sum_{j in Seed(u), i in N_k(j)} sim(i, j)
    
    Data:
    - User has seeds: {S1, S2}
    - N_k(S1) with k=2: [(M2, 0.9), (M3, 0.7)]   (M4 with 0.5 is cut off at k=2)
    - N_k(S2) with k=2: [(M3, 0.8), (M5, 0.6)]   (M2 with 0.4 is cut off at k=2)
    
    Candidate scores:
    - M2: gets 0.9 from S1; 0 from S2 (since M2 is NOT in N_2(S2)) -> total 0.9
    - M3: gets 0.7 from S1; 0.8 from S2 -> total 1.5
    - M5: gets 0.6 from S2 -> total 0.6
    
    History exclusion:
    - If user history contains M3: M3 is excluded.
    - Expected remaining order: [M2, M5].
    """
    top_neighbors_map = {
        100: [(2, 0.9), (3, 0.7), (4, 0.5)],   # Seed S1
        200: [(3, 0.8), (5, 0.6), (2, 0.4)],   # Seed S2
    }
    popularity_ranking = [2, 3, 4, 5, 6, 7]
    popularity_counts = {2: 100, 3: 100, 4: 100, 5: 100, 6: 100, 7: 100}

    # Case 1: user_train_history has {100, 200} (the seeds), candidate M3 is valid
    recs, details, used_fallback = recommend_for_user_cf(
        user_id=1,
        user_train_history={100, 200},
        user_train_seeds={100, 200},
        top_neighbors_map=top_neighbors_map,
        k=2,
        popularity_ranking=popularity_ranking,
        popularity_counts=popularity_counts,
        top_n=3,
    )
    # M3 (1.5) > M2 (0.9) > M5 (0.6)
    assert recs[:3] == [3, 2, 5]
    assert np.isclose(details[0]["score"], 1.5)
    assert np.isclose(details[1]["score"], 0.9)
    assert np.isclose(details[2]["score"], 0.6)
    assert not used_fallback

    # Case 2: user already rated M3 in train -> M3 is excluded
    recs_ex, details_ex, used_fb_ex = recommend_for_user_cf(
        user_id=1,
        user_train_history={100, 200, 3},
        user_train_seeds={100, 200},
        top_neighbors_map=top_neighbors_map,
        k=2,
        popularity_ranking=popularity_ranking,
        popularity_counts=popularity_counts,
        top_n=2,
    )
    assert recs_ex == [2, 5]
    assert 3 not in recs_ex


def test_hand_calculated_tie_breaking_and_popularity_fallback():
    """
    Hand-calculated fixture test for tie-breaking and fallback:
    1. Tie on score: M10 and M20 both have score 1.0.
       - Train pop: M20 has 50 ratings, M10 has 30 ratings -> M20 wins.
       - If train pop also ties: smaller movie_id wins.
    2. Fallback when fewer than 5 CF items have positive score:
       - Only 2 CF candidates available: [M20, M10].
       - Needs 3 fallback items from popularity ranking.
       - Verifies score_type='cf' for first 2, and score_type='popularity_fallback' for last 3.
       - Verifies used_fallback is True.
    """
    top_neighbors_map = {
        100: [(10, 1.0), (20, 1.0)],  # Tie on score 1.0
    }
    popularity_ranking = [20, 10, 30, 40, 50, 60]
    popularity_counts = {20: 50, 10: 30, 30: 20, 40: 15, 50: 10, 60: 5}

    recs, details, used_fallback = recommend_for_user_cf(
        user_id=1,
        user_train_history={100},
        user_train_seeds={100},
        top_neighbors_map=top_neighbors_map,
        k=10,
        popularity_ranking=popularity_ranking,
        popularity_counts=popularity_counts,
        top_n=5,
    )

    # 1. Tie breaking: M20 (pop 50) before M10 (pop 30)
    assert recs[:2] == [20, 10]
    assert details[0]["score_type"] == "cf"
    assert details[1]["score_type"] == "cf"

    # 2. Fallback items: M30, M40, M50
    assert recs[2:] == [30, 40, 50]
    assert details[2]["score_type"] == "popularity_fallback"
    assert details[3]["score_type"] == "popularity_fallback"
    assert details[4]["score_type"] == "popularity_fallback"
    assert used_fallback is True


def test_hand_calculated_recall_denominator_includes_novel_items():
    """
    Hand-calculated fixture test:
    - User recommended: [10, 20, 30, 40, 50]
    - User has positives in validation: {20, 9999} where 9999 is novel (outside train).
    - Hits: 1 (on 20).
    - Precision@5 = 1 / 5 = 0.20
    - Recall@5 = 1 / 2 = 0.50 (denominator strictly includes novel item 9999).
    """
    recs = [10, 20, 30, 40, 50]
    positives = {20, 9999}

    m = compute_user_metrics_at_k(recs, positives, k=5)
    assert m["hits"] == 1
    assert np.isclose(m["precision"], 0.20)
    assert np.isclose(m["recall"], 0.50)


def test_pipeline_strictly_rejects_non_top_5():
    """
    Regression test: evaluate_cf_validation_pipeline must reject top_n != 5 before processing.
    """
    empty_df = pd.DataFrame(columns=["user_id", "movie_id", "rating", "timestamp"])

    with pytest.raises(ValueError, match="top_n=5"):
        evaluate_cf_validation_pipeline(ratings_df=empty_df, top_n=10)

    with pytest.raises(ValueError, match="top_n=5"):
        evaluate_cf_validation_pipeline(ratings_df=empty_df, top_n=0)


def test_cli_rejects_non_top_5_without_touching_output(tmp_path):
    """
    Regression test: CLI must reject --top-k != 5 with nonzero exit code before loading data.
    """
    cf_script = REPO_ROOT / "mining" / "cf.py"
    out_file = tmp_path / "cf_out.json"

    proc = subprocess.run(
        [sys.executable, str(cf_script), "--top-k", "10", "--output", str(out_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert not out_file.exists()


def test_real_data_cf_validation_artifact():
    """
    Artifact verification test for results/mining/cf_validation_experiments.json:
    - Validates schema, metadata, provenance, experiments for k in {20, 40, 80}.
    - Verifies best k* is selected as 40.
    - Verifies exact reproducible metrics.
    """
    assert DEFAULT_CF_OUTPUT.exists(), f"Missing {DEFAULT_CF_OUTPUT}"
    with open(DEFAULT_CF_OUTPUT, "r", encoding="utf-8") as f:
        res = json.load(f)

    assert res["contract_version"] == 2
    assert res["model_name"] == "item_based_collaborative_filtering"
    assert res["evaluation_phase"] == "validation"
    assert res["recommendation_cutoff"] == 5
    assert res["training_cutoff_timestamp"] == 974862386
    assert res["evaluation_cutoff_timestamp"] == 976422051

    # Provenance and metadata
    prov = res["provenance"]
    assert "split_manifest_sha256" in prov
    assert "cf_code_sha256" in prov
    assert "cf_code_git_blob_sha1" in prov
    assert "code_provenance" in prov
    assert "config_hash" in prov
    assert prov["matrix_dtype"] == "float32"
    assert prov["batch_size"] == 500
    assert "timing_breakdown" in prov
    assert "matrix_fit_seconds" in prov["timing_breakdown"]
    assert "neighbor_build_seconds" in prov["timing_breakdown"]
    assert "pipeline_runtime_seconds" in prov["timing_breakdown"]
    assert "libraries" in prov
    assert prov["libraries"]["scipy"] == "1.14.1"
    assert "scikit_learn" in prov["libraries"]
    assert "source_hashes" in res
    assert "ratings.dat" in res["source_hashes"]

    # Cohort
    cohort = res["cohort"]
    assert cohort["eligible_cohort_size"] == 471
    assert cohort["eligible_user_ids_hash"] == "ba0f9648c46999712f4339a81f0b6c0cb45b4bd3bc5ad1184d8885e580fd101f"
    assert cohort["candidate_universe_stats"]["min_candidates_per_user"] == 2193
    assert cohort["candidate_universe_stats"]["max_candidates_per_user"] == 3628

    # Experiments
    exp = res["experiments"]
    assert "k_20" in exp
    assert "k_40" in exp
    assert "k_80" in exp

    # Distinction between top_n and neighbor_k
    assert exp["k_40"]["recommendation_top_n"] == 5
    assert exp["k_40"]["neighbor_k"] == 40

    # k=20
    assert np.isclose(exp["k_20"]["macro_precision_at_5"], 0.177070, atol=1e-5)
    assert np.isclose(exp["k_20"]["macro_recall_at_5"], 0.02856537, atol=1e-6)
    assert exp["k_20"]["total_hits"] == 417

    # k=40
    assert np.isclose(exp["k_40"]["macro_precision_at_5"], 0.180042, atol=1e-5)
    assert np.isclose(exp["k_40"]["macro_recall_at_5"], 0.03007556, atol=1e-6)
    assert exp["k_40"]["total_hits"] == 424

    # k=80
    assert np.isclose(exp["k_80"]["macro_precision_at_5"], 0.184289, atol=1e-5)
    assert np.isclose(exp["k_80"]["macro_recall_at_5"], 0.02866586, atol=1e-6)
    assert exp["k_80"]["total_hits"] == 434

    # Strictly unrounded recall comparison justifies k*=40
    assert exp["k_40"]["macro_recall_at_5_unrounded"] > exp["k_80"]["macro_recall_at_5_unrounded"]
    assert exp["k_80"]["macro_recall_at_5_unrounded"] > exp["k_20"]["macro_recall_at_5_unrounded"]

    # Best configuration: k=40 selected by unrounded recall
    best = res["best_configuration"]
    assert best["selected_k"] == 40
    assert best["metrics"]["macro_recall_at_5"] == exp["k_40"]["macro_recall_at_5"]
    assert best["unrounded_macro_recall_at_5"] == exp["k_40"]["macro_recall_at_5_unrounded"]

    # Baseline comparison
    comp = res["baseline_comparison"]
    assert comp["baseline_metrics"]["total_hits"] == 400
    assert comp["best_cf_metrics"]["total_hits"] == 424
    assert comp["best_cf_metrics"]["macro_precision_at_5"] > comp["baseline_metrics"]["macro_precision_at_5"]
    assert comp["best_cf_metrics"]["macro_recall_at_5"] < comp["baseline_metrics"]["macro_recall_at_5"]


def test_real_data_cf_code_provenance_and_newline_integrity():
    """
    Provenance regression test verifying exact hash match of mining/cf.py:
    - Verifies canonical LF SHA-256 and Git blob SHA-1 match artifact provenance.
    - Verifies cross-platform invariance under Windows CRLF line endings.
    - Verifies tamper detection (modified code produces mismatch).
    """
    import tempfile

    assert DEFAULT_CF_OUTPUT.exists(), f"Missing {DEFAULT_CF_OUTPUT}"
    with open(DEFAULT_CF_OUTPUT, "r", encoding="utf-8") as f:
        res = json.load(f)

    prov = res["provenance"]
    cf_path = REPO_ROOT / "mining" / "cf.py"
    compute_code_hashes = cf_mod.compute_code_hashes

    # 1. Exact match with active codebase (canonical LF SHA-256 & Git blob SHA-1)
    live_hashes = compute_code_hashes(cf_path)
    assert prov["cf_code_sha256"] == live_hashes["cf_code_sha256"], (
        f"Code SHA-256 drift: artifact {prov['cf_code_sha256']} != live {live_hashes['cf_code_sha256']}"
    )
    assert prov["cf_code_git_blob_sha1"] == live_hashes["cf_code_git_blob_sha1"], (
        f"Git blob SHA-1 drift: artifact {prov['cf_code_git_blob_sha1']} != live {live_hashes['cf_code_git_blob_sha1']}"
    )
    # Raw runtime hash records the original execution environment;
    # verify it is valid historical provenance, without forcing checkouts with different newlines to match.
    assert isinstance(prov["code_provenance"]["runtime_bytes_sha256"], str)
    assert len(prov["code_provenance"]["runtime_bytes_sha256"]) == 64
    if live_hashes["runtime_newline_format"] == prov["code_provenance"]["runtime_newline_format"]:
        assert prov["code_provenance"]["runtime_bytes_sha256"] == live_hashes["runtime_bytes_sha256"]

    # 2. Cross-platform CRLF normalization test
    orig_bytes = cf_path.read_bytes()
    crlf_bytes = orig_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(crlf_bytes)
        tmp_path = Path(tmp.name)

    try:
        crlf_hashes = compute_code_hashes(tmp_path)
        assert crlf_hashes["runtime_newline_format"] == "CRLF"
        # Canonical hashes MUST remain invariant across CRLF vs LF
        assert crlf_hashes["cf_code_sha256"] == live_hashes["cf_code_sha256"]
        assert crlf_hashes["cf_code_git_blob_sha1"] == live_hashes["cf_code_git_blob_sha1"]
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    # 3. Tamper detection test (modifying code detects change)
    tampered_bytes = orig_bytes + b"\n# audit tamper marker\n"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(tampered_bytes)
        tmp_tampered_path = Path(tmp.name)

    try:
        tampered_hashes = compute_code_hashes(tmp_tampered_path)
        assert tampered_hashes["cf_code_sha256"] != prov["cf_code_sha256"]
        assert tampered_hashes["cf_code_git_blob_sha1"] != prov["cf_code_git_blob_sha1"]
    finally:
        if tmp_tampered_path.exists():
            tmp_tampered_path.unlink()


def test_real_data_cf_timing_breakdown_isolation():
    """
    Verifies timing isolation between pure algorithm execution and CLI I/O:
    - pipeline_runtime_seconds strictly measures algorithmic execution.
    - cli_total_wall_seconds covers end-to-end execution including data loading and verification.
    - Loading and verification times are separated and non-zero when run via CLI.
    """
    assert DEFAULT_CF_OUTPUT.exists(), f"Missing {DEFAULT_CF_OUTPUT}"
    with open(DEFAULT_CF_OUTPUT, "r", encoding="utf-8") as f:
        res = json.load(f)

    timing = res["provenance"]["timing_breakdown"]
    assert "pipeline_runtime_seconds" in timing
    assert "matrix_fit_seconds" in timing
    assert "neighbor_build_seconds" in timing
    assert "evaluation_runtime_seconds" in timing
    assert "cli_total_wall_seconds" in timing
    assert "cli_data_loading_seconds" in timing
    assert "cli_verification_seconds" in timing

    # Pipeline runtime should be strictly positive and smaller than CLI wall time
    assert timing["pipeline_runtime_seconds"] > 0
    assert timing["cli_total_wall_seconds"] >= timing["pipeline_runtime_seconds"]
    assert timing["cli_data_loading_seconds"] > 0
    assert timing["cli_verification_seconds"] > 0

    # Explanation must document the boundary clearly
    assert "pure algorithm" in timing["explanation"].lower()
    assert "excludes disk data loading" in timing["explanation"].lower()

