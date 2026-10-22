"""
Unit and regression tests for mining/recommend.py CLI and recommendation logic.
Verifies:
- User with multiple valid seeds receives CF recommendations.
- User with 0 seeds triggers popularity fallback with score_type='popularity_fallback'.
- Non-existent user triggers global popularity fallback.
- CLI argument validation (top_n > 0, valid modes).
- Separation of scores: CF scores are float, fallback scores are None.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

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
rec_mod = load_mining_module("mining.recommend", "mining/recommend.py")

recommend_movies = rec_mod.recommend_movies


@pytest.fixture
def synthetic_mock_tables():
    """Builds self-contained mock tables for fast unit testing."""
    movies_df = pd.DataFrame([
        {"movie_id": 1, "title": "Toy Story (1995)", "release_year": 1995},
        {"movie_id": 2, "title": "Jumanji (1995)", "release_year": 1995},
        {"movie_id": 3, "title": "Grumpier Old Men (1995)", "release_year": 1995},
        {"movie_id": 4, "title": "Waiting to Exhale (1995)", "release_year": 1995},
        {"movie_id": 5, "title": "Father of the Bride Part II (1995)", "release_year": 1995},
        {"movie_id": 6, "title": "Heat (1995)", "release_year": 1995},
        {"movie_id": 7, "title": "Sabrina (1995)", "release_year": 1995},
    ])
    movie_genres_df = pd.DataFrame([
        {"movie_id": 1, "genre_name": "Animation"},
        {"movie_id": 1, "genre_name": "Comedy"},
        {"movie_id": 2, "genre_name": "Adventure"},
        {"movie_id": 3, "genre_name": "Comedy"},
        {"movie_id": 4, "genre_name": "Comedy"},
        {"movie_id": 5, "genre_name": "Comedy"},
        {"movie_id": 6, "genre_name": "Action"},
        {"movie_id": 7, "genre_name": "Comedy"},
    ])
    ratings_df = pd.DataFrame([
        # User 1 has seeds (rating 5 on movie 1)
        {"user_id": 1, "movie_id": 1, "rating": 5, "timestamp": 100},
        {"user_id": 1, "movie_id": 2, "rating": 2, "timestamp": 200},
        # User 2 rates movies 1, 3, 4 positively
        {"user_id": 2, "movie_id": 1, "rating": 5, "timestamp": 100},
        {"user_id": 2, "movie_id": 3, "rating": 4, "timestamp": 200},
        {"user_id": 2, "movie_id": 4, "rating": 5, "timestamp": 300},
        # User 3 has NO seeds (all ratings < 4)
        {"user_id": 3, "movie_id": 1, "rating": 3, "timestamp": 100},
        {"user_id": 3, "movie_id": 2, "rating": 2, "timestamp": 200},
        # Other ratings for popularity
        {"user_id": 4, "movie_id": 5, "rating": 5, "timestamp": 100},
        {"user_id": 4, "movie_id": 6, "rating": 5, "timestamp": 200},
        {"user_id": 4, "movie_id": 7, "rating": 4, "timestamp": 300},
    ])
    return {
        "movies": movies_df,
        "movie_genres": movie_genres_df,
        "ratings": ratings_df,
    }


def test_recommend_active_user_with_seeds(synthetic_mock_tables):
    res = recommend_movies(
        user_id=1, top_n=3, mode="evaluation", tables=synthetic_mock_tables, skip_manifest_verification=True
    )
    assert res["user_id"] == 1
    assert res["user_status"] == "ACTIVE_CF_USER"
    assert res["seeds_count"] == 1
    assert len(res["recommendations"]) == 3
    # Excludes history: movies 1 and 2 must not be recommended
    rec_ids = [r["movie_id"] for r in res["recommendations"]]
    assert 1 not in rec_ids
    assert 2 not in rec_ids
    assert rec_ids[0] in [3, 4]  # High similarity from user 2 co-ratings
    assert res["recommendations"][0]["score_type"] == "cf"
    assert isinstance(res["recommendations"][0]["score"], float)
    assert res["model_construction"]["reconstruction_mode"] == "runtime_in_memory_fit"


def test_recommend_zero_seeds_user_triggers_fallback(synthetic_mock_tables):
    res = recommend_movies(
        user_id=3, top_n=3, mode="evaluation", tables=synthetic_mock_tables, skip_manifest_verification=True
    )
    assert res["user_id"] == 3
    assert res["user_status"] == "ZERO_SEEDS_USER"
    assert res["seeds_count"] == 0
    assert res["used_fallback"] is True
    assert len(res["recommendations"]) == 3
    # All items must be popularity_fallback
    for r in res["recommendations"]:
        assert r["score_type"] == "popularity_fallback"
        assert r["score"] is None
        assert "Popularity Fallback" in r["score_display"]


def test_recommend_non_existent_user(synthetic_mock_tables):
    res = recommend_movies(
        user_id=99999, top_n=3, mode="evaluation", tables=synthetic_mock_tables, skip_manifest_verification=True
    )
    assert res["user_id"] == 99999
    assert res["user_status"] == "NON_EXISTENT_USER"
    assert res["seeds_count"] == 0
    assert res["used_fallback"] is True
    assert len(res["recommendations"]) == 3
    for r in res["recommendations"]:
        assert r["score_type"] == "popularity_fallback"


def test_recommend_rejects_invalid_arguments(synthetic_mock_tables):
    with pytest.raises(ValueError, match="top_n must be positive"):
        recommend_movies(user_id=1, top_n=0, tables=synthetic_mock_tables, skip_manifest_verification=True)

    with pytest.raises(ValueError, match="mode must be 'evaluation' or 'demo'"):
        recommend_movies(user_id=1, mode="invalid_mode", tables=synthetic_mock_tables, skip_manifest_verification=True)


def test_recommend_evaluation_mode_rejects_corrupted_input_hash(tmp_path, synthetic_mock_tables, monkeypatch):
    """Verifies that evaluation mode strictly rejects execution when input data hash mismatches manifest."""
    dummy_receipt = tmp_path / "dummy_receipt.json"
    manifest_data = {
        "training_manifest": {
            "model_version": "item_based_cf_k40_eval_v1",
            "training_cutoff_timestamp": 976422051,
            "training_ratings_count": len(synthetic_mock_tables["ratings"]),
        },
        "frozen_configuration": {"neighbor_k": 40},
        "hashes": {
            "canonical_table_hashes": {
                "ratings": "expected_valid_ratings_sha256_hash",
            }
        },
    }
    dummy_receipt.write_text(json.dumps(manifest_data), encoding="utf-8")

    # Mock verify_and_hash_input_tables returning mismatched hash
    def mock_verify(tables, manifest_path=None):
        return {"ratings": "corrupted_tampered_ratings_sha256_hash"}, {}, "commit_123"

    monkeypatch.setattr(rec_mod, "verify_and_hash_input_tables", mock_verify)

    with pytest.raises(ValueError, match="Input data verification failed for table 'ratings'"):
        recommend_movies(
            user_id=1,
            mode="evaluation",
            tables=synthetic_mock_tables,
            receipt_path=dummy_receipt,
            skip_manifest_verification=False,
        )


def test_recommend_evaluation_mode_rejects_cutoff_ratings_count_mismatch(tmp_path, synthetic_mock_tables, monkeypatch):
    """Verifies that evaluation mode strictly rejects execution when active ratings count mismatches manifest."""
    dummy_receipt = tmp_path / "dummy_receipt.json"
    manifest_data = {
        "training_manifest": {
            "model_version": "item_based_cf_k40_eval_v1",
            "training_cutoff_timestamp": 976422051,
            "training_ratings_count": 999999,  # Mismatched expected count
        },
        "frozen_configuration": {"neighbor_k": 40},
        "hashes": {
            "canonical_table_hashes": {
                "ratings": "matching_hash",
            }
        },
    }
    dummy_receipt.write_text(json.dumps(manifest_data), encoding="utf-8")

    def mock_verify(tables, manifest_path=None):
        return {"ratings": "matching_hash"}, {}, "commit_123"

    monkeypatch.setattr(rec_mod, "verify_and_hash_input_tables", mock_verify)

    with pytest.raises(ValueError, match="Training ratings count mismatch under cutoff"):
        recommend_movies(
            user_id=1,
            mode="evaluation",
            tables=synthetic_mock_tables,
            receipt_path=dummy_receipt,
            skip_manifest_verification=False,
        )


def test_recommend_evaluation_mode_binds_model_identity_from_manifest(tmp_path, synthetic_mock_tables, monkeypatch):
    """Verifies that CLI evaluation mode takes model identity and cutoff strictly from receipt manifest."""
    dummy_receipt = tmp_path / "dummy_receipt.json"
    manifest_data = {
        "training_manifest": {
            "model_version": "item_based_cf_k40_eval_v1",
            "training_cutoff_timestamp": 976422051,
            "training_ratings_count": len(synthetic_mock_tables["ratings"]),
        },
        "frozen_configuration": {"neighbor_k": 40},
        "hashes": {
            "canonical_table_hashes": {
                "ratings": "matching_hash",
            }
        },
    }
    dummy_receipt.write_text(json.dumps(manifest_data), encoding="utf-8")

    def mock_verify(tables, manifest_path=None):
        return {"ratings": "matching_hash"}, {}, "commit_123"

    monkeypatch.setattr(rec_mod, "verify_and_hash_input_tables", mock_verify)

    res = recommend_movies(
        user_id=1,
        mode="evaluation",
        tables=synthetic_mock_tables,
        receipt_path=dummy_receipt,
        skip_manifest_verification=False,
    )
    assert res["model_version"] == "item_based_cf_k40_eval_v1"
    assert res["model_construction"]["reconstruction_mode"] == "runtime_in_memory_fit"
    assert res["manifest_metadata"]["integrity_verification"] == "PASSED_CANONICAL_HASHES_MATCH"


def test_recommend_demo_mode_has_distinct_manifest_and_offline_disclaimer(synthetic_mock_tables):
    """Verifies that demo mode carries DEMO identity and prohibits offline metric evaluation."""
    res = recommend_movies(
        user_id=1, mode="demo", tables=synthetic_mock_tables, skip_manifest_verification=True
    )
    assert res["model_version"] == "item_based_cf_k40_DEMO_full_history_v1"
    assert "offline_metrics_disclaimer" in res["manifest_metadata"]
    assert "NEVER be used to evaluate or publish offline metrics" in res["manifest_metadata"]["offline_metrics_disclaimer"]


def test_recommend_cli_smoke(tmp_path):
    """Smoke test running recommend.py via subprocess on real data."""
    script = REPO_ROOT / "mining" / "recommend.py"
    python_bin = sys.executable
    out_json = tmp_path / "rec.json"
    proc = subprocess.run(
        [
            python_bin,
            str(script),
            "--user-id",
            "1",
            "--top-n",
            "5",
            "--mode",
            "evaluation",
            "--output-json",
            str(out_json),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"CLI error: {proc.stderr}"
    assert out_json.exists()
    with open(out_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["user_id"] == 1
    assert len(data["recommendations"]) == 5
    assert data["model_version"] == "item_based_cf_k40_eval_v1"
    assert data["manifest_metadata"]["integrity_verification"] == "PASSED_CANONICAL_HASHES_MATCH"

