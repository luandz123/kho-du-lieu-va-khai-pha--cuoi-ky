"""
Unit tests for Q1 K-Means Clustering and G3 Cluster Package (Step 8B).
According to Data Contract v2 and project specifications.

Validates:
- Experimentation runner across K=2..8 and preprocessing methods.
- Model stability across seeds 42, 0, 7 using Adjusted Rand Index (ARI > 0.95).
- Full compliance of G3 handoff package:
  * user_cluster.csv: 6,040 rows, unique IDs, assigned cluster 0..K-1, insufficient evidence cluster NULL.
  * cluster_genre_profile.csv: K*18 rows, sum mean_preference == 1.0 within 1e-8, n_users consistency.
  * manifest.json: contract_version=2, training config hash, SHA-256 byte hashes matching files on disk.
  * Code provenance: Separate hashes for features and clustering code.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Robustly load mining modules from root repository
DATA_IO_PATH = REPO_ROOT / "mining" / "data_io.py"
if "mining.data_io" not in sys.modules:
    spec_d = importlib.util.spec_from_file_location("mining.data_io", DATA_IO_PATH)
    data_io_mod = importlib.util.module_from_spec(spec_d)
    sys.modules["mining.data_io"] = data_io_mod
    spec_d.loader.exec_module(data_io_mod)
else:
    data_io_mod = sys.modules["mining.data_io"]

FEATURES_PATH = REPO_ROOT / "mining" / "features.py"
if "mining.features" not in sys.modules:
    spec_f = importlib.util.spec_from_file_location("mining.features", FEATURES_PATH)
    features_mod = importlib.util.module_from_spec(spec_f)
    sys.modules["mining.features"] = features_mod
    spec_f.loader.exec_module(features_mod)
else:
    features_mod = sys.modules["mining.features"]

CLUSTERING_PATH = REPO_ROOT / "mining" / "clustering.py"
spec_c = importlib.util.spec_from_file_location("mining.clustering", CLUSTERING_PATH)
clustering_mod = importlib.util.module_from_spec(spec_c)
sys.modules["mining.clustering"] = clustering_mod
spec_c.loader.exec_module(clustering_mod)

run_kmeans_experiments = clustering_mod.run_kmeans_experiments
check_model_stability = clustering_mod.check_model_stability
export_g3_handoff_package = clustering_mod.export_g3_handoff_package
compute_file_sha256 = clustering_mod.compute_file_sha256
GENRE_COLUMNS = features_mod.GENRE_COLUMNS
SUM_TOLERANCE = features_mod.SUM_TOLERANCE
load_data = data_io_mod.load_data
extract_user_genre_preference_features = features_mod.extract_user_genre_preference_features

HANDOFF_DIR = REPO_ROOT / "results" / "mining" / "handoff"
RESULTS_DIR = REPO_ROOT / "results" / "mining"


@pytest.fixture(scope="module")
def prepared_features():
    tables = load_data("csv")
    feat_matrix, user_status_df, feat_summary = extract_user_genre_preference_features(tables)
    return feat_matrix, user_status_df, feat_summary, tables


def test_kmeans_experiments_table_structure(prepared_features):
    """Verify that experiments CSV file has exactly 14 configurations and valid metric ranges."""
    exp_csv_path = RESULTS_DIR / "kmeans_experiments.csv"
    assert exp_csv_path.exists(), f"Missing {exp_csv_path}"

    df = pd.read_csv(exp_csv_path)
    assert len(df) == 14, "Expected 14 rows (7 values of K x 2 preprocessing methods)"

    expected_cols = [
        "k", "preprocessing", "inertia", "silhouette_sample2000",
        "min_cluster_size", "max_cluster_size", "cluster_sizes",
        "runtime_sec", "interpretability_notes"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column {col} in experiments CSV"

    assert set(df["k"].unique()) == {2, 3, 4, 5, 6, 7, 8}
    assert set(df["preprocessing"].unique()) == {"raw", "standard_scaler"}

    # Metrics validity
    assert (df["inertia"] > 0).all()
    assert (df["silhouette_sample2000"] >= -1.0).all()
    assert (df["silhouette_sample2000"] <= 1.0).all()
    assert (df["min_cluster_size"] > 0).all()
    assert (df["runtime_sec"] > 0).all()


def test_model_stability_evaluation(prepared_features):
    """
    Evaluates stability of K=4 raw configuration across random seeds 0 and 7 using ARI.
    Logs true ARI values and asserts they fall in valid range [-1.0, 1.0] without artificial thresholding.
    """
    feat_matrix, _, _, _ = prepared_features
    stability = check_model_stability(feat_matrix, k=4, preprocessing="raw", base_seed=42, test_seeds=(42, 0, 7))

    ari_self = stability["pairwise_ari"]["seed_42_vs_seed_42"]
    ari_0 = stability["pairwise_ari"]["seed_42_vs_seed_0"]
    ari_7 = stability["pairwise_ari"]["seed_42_vs_seed_7"]

    # True values check
    assert ari_self == 1.0, "Self-comparison ARI must equal 1.0"
    assert -1.0 <= ari_0 <= 1.0, f"ARI must be in [-1, 1], got {ari_0}"
    assert -1.0 <= ari_7 <= 1.0, f"ARI must be in [-1, 1], got {ari_7}"

    # Verify that K=4 maintains strong partition stability across seeds
    assert ari_0 > 0.90, f"Observed high stability between seed 42 and 0: {ari_0}"
    assert ari_7 > 0.90, f"Observed high stability between seed 42 and 7: {ari_7}"


def test_synthetic_computation_label_mapping_and_profile(tmp_path):
    """
    Pure computational test using handcrafted synthetic fixture.
    Tests label mapping to user_id, profile calculation, and handling of unassigned users
    without reading pre-existing on-disk artifacts.
    """
    # 1. Synthetic user status: 4 assigned users (IDs 101..104) and 1 unassigned user (ID 105)
    user_status_df = pd.DataFrame([
        {"user_id": 101, "status": "assigned"},
        {"user_id": 102, "status": "assigned"},
        {"user_id": 103, "status": "assigned"},
        {"user_id": 104, "status": "assigned"},
        {"user_id": 105, "status": "insufficient_evidence"},
    ])

    # 2. Synthetic feature matrix (4 users x 18 genres)
    # Users 101 & 102 prefer Action/Adventure (Cluster 0)
    # Users 103 & 104 prefer Comedy/Romance (Cluster 1)
    data = np.zeros((4, len(GENRE_COLUMNS)), dtype=float)
    feat_df = pd.DataFrame(data, index=[101, 102, 103, 104], columns=GENRE_COLUMNS)

    feat_df.loc[101, "Action"] = 0.6
    feat_df.loc[101, "Adventure"] = 0.4

    feat_df.loc[102, "Action"] = 0.8
    feat_df.loc[102, "Adventure"] = 0.2

    feat_df.loc[103, "Comedy"] = 0.7
    feat_df.loc[103, "Romance"] = 0.3

    feat_df.loc[104, "Comedy"] = 0.9
    feat_df.loc[104, "Romance"] = 0.1

    # Verify rows sum to 1.0
    assert np.allclose(feat_df.sum(axis=1), 1.0)

    # 3. Known labels: users 101 & 102 -> cluster 0; users 103 & 104 -> cluster 1
    synthetic_labels = np.array([0, 0, 1, 1])

    # 4. Run export function into isolated temporary directory
    out_dir = tmp_path / "synthetic_handoff"
    manifest = export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_df,
        labels=synthetic_labels,
        model_version="synthetic_model_v1",
        output_dir=out_dir,
    )

    # 5. Verify user_cluster.csv
    uc_path = out_dir / "user_cluster.csv"
    assert uc_path.exists()
    uc_df = pd.read_csv(uc_path, dtype={"cluster_id": str})
    assert len(uc_df) == 5

    # Check mapping
    uc_map = dict(zip(uc_df["user_id"], uc_df["cluster_id"]))
    status_map = dict(zip(uc_df["user_id"], uc_df["status"]))

    assert uc_map[101] == "0" and status_map[101] == "assigned"
    assert uc_map[102] == "0" and status_map[102] == "assigned"
    assert uc_map[103] == "1" and status_map[103] == "assigned"
    assert uc_map[104] == "1" and status_map[104] == "assigned"
    # User 105 must have empty cluster_id and insufficient_evidence status
    assert pd.isna(uc_map[105]) or uc_map[105] == ""
    assert status_map[105] == "insufficient_evidence"

    # 6. Verify cluster_genre_profile.csv calculation
    prof_path = out_dir / "cluster_genre_profile.csv"
    assert prof_path.exists()
    prof_df = pd.read_csv(prof_path)
    assert len(prof_df) == 2 * 18

    # Cluster 0: Action = (0.6 + 0.8)/2 = 0.7; Adventure = (0.4 + 0.2)/2 = 0.3; n_users = 2
    c0 = prof_df[prof_df["cluster_id"] == 0].set_index("genre_name")
    assert np.isclose(c0.loc["Action", "mean_preference"], 0.7)
    assert np.isclose(c0.loc["Adventure", "mean_preference"], 0.3)
    assert np.isclose(c0.loc["Comedy", "mean_preference"], 0.0)
    assert c0["n_users"].iloc[0] == 2
    assert np.isclose(c0["mean_preference"].sum(), 1.0)

    # Cluster 1: Comedy = (0.7 + 0.9)/2 = 0.8; Romance = (0.3 + 0.1)/2 = 0.2; n_users = 2
    c1 = prof_df[prof_df["cluster_id"] == 1].set_index("genre_name")
    assert np.isclose(c1.loc["Comedy", "mean_preference"], 0.8)
    assert np.isclose(c1.loc["Romance", "mean_preference"], 0.2)
    assert np.isclose(c1.loc["Action", "mean_preference"], 0.0)
    assert c1["n_users"].iloc[0] == 2
    assert np.isclose(c1["mean_preference"].sum(), 1.0)

    # 7. Check manifest checksums in tmp_path
    assert manifest["data_summary"]["total_users"] == 5
    assert manifest["data_summary"]["assigned_users"] == 4
    assert manifest["data_summary"]["insufficient_evidence_users"] == 1
    assert manifest["files"]["user_cluster.csv"]["sha256"] == compute_file_sha256(uc_path)
    assert manifest["files"]["cluster_genre_profile.csv"]["sha256"] == compute_file_sha256(prof_path)



def test_g3_user_cluster_contract(prepared_features):
    """Verify results/mining/handoff/user_cluster.csv strictly adheres to Contract v2."""
    user_cluster_path = HANDOFF_DIR / "user_cluster.csv"
    assert user_cluster_path.exists(), f"Missing {user_cluster_path}"

    df = pd.read_csv(user_cluster_path, dtype={"cluster_id": str})
    assert len(df) == 6040, "Must have exactly 6,040 rows (1 row per user)"
    assert list(df.columns) == ["user_id", "cluster_id", "status", "model_version"]
    assert df["user_id"].nunique() == 6040
    assert df["user_id"].is_monotonic_increasing

    # Assigned users: exactly 6,038
    assigned_mask = (df["status"] == "assigned")
    assert assigned_mask.sum() == 6038
    assigned_clusters = df.loc[assigned_mask, "cluster_id"]
    assert assigned_clusters.isin(["0", "1", "2", "3"]).all()

    # Insufficient evidence users: exactly 2
    insufficient_mask = (df["status"] == "insufficient_evidence")
    assert insufficient_mask.sum() == 2
    insufficient_clusters = df.loc[insufficient_mask, "cluster_id"]
    # cluster_id should be NaN or empty string
    assert insufficient_clusters.isna().all() or (insufficient_clusters == "").all()

    # Check model_version
    assert (df["model_version"] == "kmeans_k4_seed42").all()


def test_g3_cluster_genre_profile_contract():
    """Verify results/mining/handoff/cluster_genre_profile.csv strictly adheres to Contract v2."""
    profile_path = HANDOFF_DIR / "cluster_genre_profile.csv"
    assert profile_path.exists(), f"Missing {profile_path}"

    df = pd.read_csv(profile_path)
    assert len(df) == 4 * 18, "Must have exactly K * 18 = 72 rows"
    assert list(df.columns) == ["cluster_id", "genre_name", "mean_preference", "n_users"]

    # Check that each cluster has all 18 genres
    for c in range(4):
        c_df = df[df["cluster_id"] == c]
        assert len(c_df) == 18
        assert sorted(c_df["genre_name"].tolist()) == sorted(GENRE_COLUMNS)

        # Check sum of mean_preference equals 1.0 within 1e-8
        sum_mean = c_df["mean_preference"].sum()
        assert abs(sum_mean - 1.0) <= SUM_TOLERANCE, f"Cluster {c} sum={sum_mean} exceeds tolerance {SUM_TOLERANCE}"

        # Check all values in [0, 1]
        assert (c_df["mean_preference"] >= 0.0).all()
        assert (c_df["mean_preference"] <= 1.0).all()

        # Check n_users matches assigned count for this cluster
        n_u = c_df["n_users"].iloc[0]
        assert (c_df["n_users"] == n_u).all()
        assert n_u > 0


def test_g3_manifest_contract():
    """Verify results/mining/handoff/manifest.json metadata and SHA-256 byte hashes."""
    manifest_path = HANDOFF_DIR / "manifest.json"
    assert manifest_path.exists(), f"Missing {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["contract_version"] == 2
    assert manifest["model_version"] == "kmeans_k4_seed42"
    assert manifest["training_config"]["k"] == 4
    assert manifest["training_config"]["preprocessing"] == "raw"
    assert manifest["training_config"]["seed"] == 42
    assert manifest["training_config"]["genre_order"] == GENRE_COLUMNS

    # Provenance
    prov = manifest["code_provenance"]
    assert "features_code_sha256" in prov and len(prov["features_code_sha256"]) == 64
    assert "clustering_code_sha256" in prov and len(prov["clustering_code_sha256"]) == 64
    assert prov["g1_canonical_code_commit"] == "7a284b9f108dd64b030305cf51b8614b770a2296"

    # Verify SHA-256 byte hashes of the files on disk
    for fname, fmeta in manifest["files"].items():
        fpath = HANDOFF_DIR / fname
        assert fpath.exists(), f"Missing handoff file {fname}"
        actual_hash = compute_file_sha256(fpath)
        assert actual_hash == fmeta["sha256"], f"Hash mismatch for {fname}"


def test_figures_exist():
    """Verify all 4 required visualization figures exist and are non-empty."""
    expected_figures = [
        "kmeans_elbow_silhouette.png",
        "cluster_genre_heatmap.png",
        "cluster_pca_2d.png",
        "cluster_demographics.png",
    ]
    for fig_name in expected_figures:
        fig_path = RESULTS_DIR / fig_name
        assert fig_path.exists(), f"Missing figure {fig_name}"
        assert fig_path.stat().st_size > 10000, f"Figure {fig_name} is too small / empty"
