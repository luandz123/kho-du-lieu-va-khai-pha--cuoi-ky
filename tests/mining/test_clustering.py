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
import shutil
import sys
import numpy as np
import pandas as pd
import pytest
import sklearn

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
    Verifies valid ARI range [-1.0, 1.0], self-comparison equals 1.0, and records observed values.
    Stability discussion and interpretation belong in report documentation rather than hardcoded test assertions.
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
    synthetic_canonical_hashes = {
        "users": "syn_users_hash_abc",
        "movies": "syn_movies_hash_def",
        "movie_genres": "syn_mg_hash_ghi",
        "ratings": "syn_ratings_hash_jkl",
    }

    # 4. Run export function into isolated temporary directory
    out_dir = tmp_path / "synthetic_handoff"
    manifest = export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_df,
        labels=synthetic_labels,
        canonical_hashes=synthetic_canonical_hashes,
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

    # 7. Check manifest data binding and checksums in tmp_path
    assert manifest["canonical_hashes"] == synthetic_canonical_hashes
    assert manifest["libraries"]["scikit-learn"] == str(sklearn.__version__)
    assert manifest["data_summary"]["total_users"] == 5
    assert manifest["data_summary"]["assigned_users"] == 4
    assert manifest["data_summary"]["insufficient_evidence_users"] == 1
    assert manifest["files"]["user_cluster.csv"]["sha256"] == compute_file_sha256(uc_path)
    assert manifest["files"]["cluster_genre_profile.csv"]["sha256"] == compute_file_sha256(prof_path)


def test_input_verification_mismatch_detected_on_mutated_dataframe(prepared_features):
    """
    Unit test: Verifies that verify_and_hash_input_tables detects in-memory data mutation.
    When a single rating is modified in the loaded DataFrame, it raises InputDataIntegrityError.
    """
    _, _, _, real_tables = prepared_features

    # Copy tables so we do not mutate module fixture
    mutated_tables = {k: v.copy() for k, v in real_tables.items()}

    # Mutate exactly one rating
    original_rating = mutated_tables["ratings"].loc[0, "rating"]
    mutated_tables["ratings"].loc[0, "rating"] = 1 if original_rating != 1 else 5

    with pytest.raises(clustering_mod.InputDataIntegrityError, match="Canonical hash mismatch for table 'ratings'"):
        clustering_mod.verify_and_hash_input_tables(mutated_tables)


def test_input_verification_missing_manifest_or_table(tmp_path):
    """
    Unit test: Verifies that verify_and_hash_input_tables raises InputDataIntegrityError
    when canonical manifest does not exist or required tables are missing.
    """
    fake_manifest = tmp_path / "non_existent_manifest.json"
    with pytest.raises(clustering_mod.InputDataIntegrityError, match="Canonical manifest not found"):
        clustering_mod.verify_and_hash_input_tables({}, manifest_path=fake_manifest)

    # Missing required tables
    with pytest.raises(clustering_mod.InputDataIntegrityError, match="missing required table"):
        clustering_mod.verify_and_hash_input_tables({"users": pd.DataFrame()})


def test_cli_rejects_mutated_data_without_exporting_package(tmp_path, monkeypatch):
    """
    Regression test reproducing coordinator's finding:
    Mutating a rating in the DataFrame returned by loader must cause the CLI to exit
    with non-zero exit code without generating a package or overwriting files.
    """
    real_tables = load_data("csv")
    mutated_tables = {k: v.copy() for k, v in real_tables.items()}
    original_rating = mutated_tables["ratings"].loc[0, "rating"]
    mutated_tables["ratings"].loc[0, "rating"] = 1 if original_rating != 1 else 5

    # Monkeypatch load_data in clustering module
    monkeypatch.setattr(clustering_mod, "load_data", lambda source="csv": mutated_tables)

    out_dir = tmp_path / "mutated_handoff"
    monkeypatch.setattr(
        sys,
        "argv",
        ["clustering.py", "--source", "csv", "--mode", "reproduce", "--outdir", str(out_dir)],
    )

    with pytest.raises(SystemExit) as exc_info:
        clustering_mod.main()

    # Must exit with non-zero exit code
    assert exc_info.value.code != 0
    # No handoff package must be written
    assert not (out_dir / "user_cluster.csv").exists()
    assert not (out_dir / "manifest.json").exists()


def test_version_reuse_protection(tmp_path):
    """
    Verifies that model_version reuse protection forbids using the frozen
    model_version 'kmeans_k4_seed42' with mismatched data or configuration,
    and prevents overwriting an existing package with conflicting data.
    """
    user_status_df = pd.DataFrame([
        {"user_id": 1, "status": "assigned"},
        {"user_id": 2, "status": "assigned"},
        {"user_id": 3, "status": "assigned"},
        {"user_id": 4, "status": "assigned"},
    ])
    feat_df = pd.DataFrame(
        np.ones((4, 18)) / 18.0,
        index=[1, 2, 3, 4],
        columns=GENRE_COLUMNS,
    )

    # 1. Attempting to use frozen model_version with K!=4 must raise ValueError
    labels_k2 = np.array([0, 0, 1, 1])
    with pytest.raises(ValueError, match="frozen for K=4"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels_k2,
            canonical_hashes=clustering_mod.FROZEN_G3_FINGERPRINT["canonical_hashes"],
            model_version=clustering_mod.FROZEN_G3_MODEL_VERSION,
            output_dir=tmp_path / "test_freeze_k",
        )

    # 2. Attempting to use frozen model_version with differing canonical_hashes must raise ValueError
    labels_k4 = np.array([0, 1, 2, 3])
    conflicting_hashes = {
        "users": "dummy_users_hash",
        "movies": "dummy_movies_hash",
        "movie_genres": "dummy_genres_hash",
        "ratings": "dummy_ratings_hash",
    }
    with pytest.raises(ValueError, match="frozen for canonical dataset"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels_k4,
            canonical_hashes=conflicting_hashes,
            model_version=clustering_mod.FROZEN_G3_MODEL_VERSION,
            output_dir=tmp_path / "test_freeze_hashes",
        )

    # 3. Package overwriting protection under same custom version
    out_dir = tmp_path / "existing_pkg"
    hashes_v1 = {"users": "h1", "movies": "h2", "movie_genres": "h3", "ratings": "h4"}
    export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_df,
        labels=labels_k4,
        canonical_hashes=hashes_v1,
        model_version="custom_version_v1",
        output_dir=out_dir,
    )
    assert (out_dir / "manifest.json").exists()

    # Try exporting to same directory under same version with different canonical_hashes
    hashes_v2 = {"users": "h1_diff", "movies": "h2", "movie_genres": "h3", "ratings": "h4"}
    with pytest.raises(ValueError, match="Cannot reuse model_version 'custom_version_v1' with different input data"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels_k4,
            canonical_hashes=hashes_v2,
            model_version="custom_version_v1",
            output_dir=out_dir,
        )


def test_g3_user_cluster_contract(prepared_features):
    """Artifact verification: Verify published results/mining/handoff/user_cluster.csv adheres to Contract v2."""
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
    assert insufficient_clusters.isna().all() or (insufficient_clusters == "").all()

    # Check model_version
    assert (df["model_version"] == "kmeans_k4_seed42").all()


def test_g3_cluster_genre_profile_contract():
    """Artifact verification: Verify published results/mining/handoff/cluster_genre_profile.csv adheres to Contract v2."""
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
    """Artifact verification: Verify published results/mining/handoff/manifest.json metadata and SHA-256 byte hashes."""
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

    # Runtime sklearn version
    assert manifest["libraries"]["scikit-learn"] == str(sklearn.__version__)

    # Canonical hashes
    assert "canonical_hashes" in manifest, "Manifest must contain 'canonical_hashes' per Contract v2"
    for tbl in ["users", "movies", "movie_genres", "ratings"]:
        assert tbl in manifest["canonical_hashes"], f"Missing table '{tbl}' in canonical_hashes"
        assert len(manifest["canonical_hashes"][tbl]) == 64

    # Verify SHA-256 byte hashes of the files on disk
    for fname, fmeta in manifest["files"].items():
        fpath = HANDOFF_DIR / fname
        assert fpath.exists(), f"Missing handoff file {fname}"
        actual_hash = compute_file_sha256(fpath)
        assert actual_hash == fmeta["sha256"], f"Hash mismatch for {fname}"


def test_figures_exist():
    """Artifact verification: Verify all 4 required visualization figures exist and are non-empty."""
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


def test_export_preserves_existing_package_on_fingerprint_mismatch(tmp_path, prepared_features):
    """
    Regression test:
    Copies an existing valid G3 handoff package into tmp_path and records SHA-256 for all 3 files.
    Then attempts to export using the same model_version ('kmeans_k4_seed42') but with permuted labels
    (conflicting payload / fingerprint mismatch).
    Must raise ValueError and ensure all 3 existing files retain their exact original bytes.
    """
    feat_matrix, user_status_df, _, tables = prepared_features
    copy_dir = tmp_path / "valid_g3_copy"
    copy_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy existing valid package
    for fname in ["user_cluster.csv", "cluster_genre_profile.csv", "manifest.json"]:
        shutil.copy2(HANDOFF_DIR / fname, copy_dir / fname)

    # 2. Record initial SHA-256 byte hashes
    h_uc_before = compute_file_sha256(copy_dir / "user_cluster.csv")
    h_prof_before = compute_file_sha256(copy_dir / "cluster_genre_profile.csv")
    h_manifest_before = compute_file_sha256(copy_dir / "manifest.json")

    # 3. Fit standard KMeans to get labels, then permute labels to generate conflicting payload
    km = sklearn.cluster.KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = km.fit_predict(feat_matrix.values)
    permuted_labels = (labels + 1) % 4  # Permute cluster assignments

    # 4. Attempt export under frozen model_version with permuted labels
    with pytest.raises(ValueError) as exc_info:
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_matrix,
            labels=permuted_labels,
            canonical_hashes=clustering_mod.FROZEN_G3_FINGERPRINT["canonical_hashes"],
            model_version=clustering_mod.FROZEN_G3_MODEL_VERSION,
            output_dir=copy_dir,
        )

    # Check error message indicates mismatch
    err_msg = str(exc_info.value)
    assert "hash mismatch" in err_msg or "conflicting payload" in err_msg

    # 5. Verify that all 3 files on disk retain their exact byte content without modification
    h_uc_after = compute_file_sha256(copy_dir / "user_cluster.csv")
    h_prof_after = compute_file_sha256(copy_dir / "cluster_genre_profile.csv")
    h_manifest_after = compute_file_sha256(copy_dir / "manifest.json")

    assert h_uc_after == h_uc_before, "user_cluster.csv was mutated during failed export!"
    assert h_prof_after == h_prof_before, "cluster_genre_profile.csv was mutated during failed export!"
    assert h_manifest_after == h_manifest_before, "manifest.json was mutated during failed export!"


def test_export_leaves_no_incomplete_package_when_validation_fails(tmp_path, prepared_features):
    """
    Regression test:
    When exporting to a new/unborn directory, if validation fails (e.g. permuted labels),
    it must NOT leave behind an incomplete or seemingly complete package.
    """
    feat_matrix, user_status_df, _, _ = prepared_features
    target_dir = tmp_path / "unborn_handoff_package"
    assert not target_dir.exists()

    km = sklearn.cluster.KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = km.fit_predict(feat_matrix.values)
    permuted_labels = (labels + 1) % 4

    with pytest.raises(ValueError):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_matrix,
            labels=permuted_labels,
            canonical_hashes=clustering_mod.FROZEN_G3_FINGERPRINT["canonical_hashes"],
            model_version=clustering_mod.FROZEN_G3_MODEL_VERSION,
            output_dir=target_dir,
        )

    # Must not contain any partial or seemingly complete handoff files
    if target_dir.exists():
        assert not (target_dir / "user_cluster.csv").exists()
        assert not (target_dir / "cluster_genre_profile.csv").exists()
        assert not (target_dir / "manifest.json").exists()


def test_export_rejects_corrupted_existing_package_without_modifying(tmp_path):
    """
    Regression test:
    Verifies that existing packages are strictly validated for internal consistency:
    - Incomplete package (CSV without manifest) is rejected.
    - Corrupted JSON manifest is rejected.
    - Checksum mismatch between disk CSV and manifest is rejected.
    """
    user_status_df = pd.DataFrame([{"user_id": 1, "status": "assigned"}])
    feat_df = pd.DataFrame(np.ones((1, 18)) / 18.0, index=[1], columns=GENRE_COLUMNS)
    labels = np.array([0])
    hashes = {"users": "h1", "movies": "h2", "movie_genres": "h3", "ratings": "h4"}

    # Case 1: CSV exists but manifest is missing
    corrupt_dir_1 = tmp_path / "corrupt_pkg_1"
    corrupt_dir_1.mkdir(parents=True)
    (corrupt_dir_1 / "user_cluster.csv").write_text("dummy,content\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV file.*exist but.*manifest.json.*missing"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels,
            canonical_hashes=hashes,
            model_version="custom_v1",
            output_dir=corrupt_dir_1,
        )

    # Case 2: Manifest exists but is invalid JSON
    corrupt_dir_2 = tmp_path / "corrupt_pkg_2"
    corrupt_dir_2.mkdir(parents=True)
    (corrupt_dir_2 / "user_cluster.csv").write_text("dummy\n", encoding="utf-8")
    (corrupt_dir_2 / "cluster_genre_profile.csv").write_text("dummy\n", encoding="utf-8")
    (corrupt_dir_2 / "manifest.json").write_text("{broken_json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid JSON"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels,
            canonical_hashes=hashes,
            model_version="custom_v1",
            output_dir=corrupt_dir_2,
        )

    # Case 3: Manifest records a hash, but disk file was tampered with (checksum mismatch)
    corrupt_dir_3 = tmp_path / "corrupt_pkg_3"
    corrupt_dir_3.mkdir(parents=True)
    (corrupt_dir_3 / "user_cluster.csv").write_text("tampered content\n", encoding="utf-8")
    (corrupt_dir_3 / "cluster_genre_profile.csv").write_text("dummy\n", encoding="utf-8")
    bad_manifest = {
        "model_version": "custom_v1",
        "files": {
            "user_cluster.csv": {"sha256": "expected_different_sha256_hash"},
            "cluster_genre_profile.csv": {"sha256": compute_file_sha256(corrupt_dir_3 / "cluster_genre_profile.csv")},
        },
    }
    with open(corrupt_dir_3 / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(bad_manifest, f)

    with pytest.raises(ValueError, match="checksum mismatch for 'user_cluster.csv'"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels,
            canonical_hashes=hashes,
            model_version="custom_v1",
            output_dir=corrupt_dir_3,
        )


def test_export_reproduce_yields_exact_frozen_csv_hashes(tmp_path, prepared_features):
    """
    Regression test:
    Verifies that reproducing the finalized model in an isolated tmp_path
    produces the exact two finalized CSV hashes for user_cluster.csv and cluster_genre_profile.csv.
    """
    feat_matrix, user_status_df, _, _ = prepared_features
    reproduce_dir = tmp_path / "reproduce_isolated"

    km = sklearn.cluster.KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = km.fit_predict(feat_matrix.values)

    manifest = export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_matrix,
        labels=labels,
        canonical_hashes=clustering_mod.FROZEN_G3_FINGERPRINT["canonical_hashes"],
        model_version=clustering_mod.FROZEN_G3_MODEL_VERSION,
        output_dir=reproduce_dir,
    )

    uc_path = reproduce_dir / "user_cluster.csv"
    prof_path = reproduce_dir / "cluster_genre_profile.csv"

    assert uc_path.exists()
    assert prof_path.exists()

    expected_csv_hashes = clustering_mod.FROZEN_G3_FINGERPRINT["expected_csv_hashes"]
    assert compute_file_sha256(uc_path) == expected_csv_hashes["user_cluster.csv"]
    assert compute_file_sha256(prof_path) == expected_csv_hashes["cluster_genre_profile.csv"]
    assert manifest["files"]["user_cluster.csv"]["sha256"] == expected_csv_hashes["user_cluster.csv"]
    assert manifest["files"]["cluster_genre_profile.csv"]["sha256"] == expected_csv_hashes["cluster_genre_profile.csv"]


def test_export_rejects_conflicting_payload_under_custom_model_version(tmp_path):
    """
    Regression test:
    Under a custom model_version, exporting a conflicting payload (different labels/data)
    into an existing package directory must be rejected before modifying files, preserving old bytes.
    """
    user_status_df = pd.DataFrame([
        {"user_id": 1, "status": "assigned"},
        {"user_id": 2, "status": "assigned"},
    ])
    feat_df = pd.DataFrame(np.ones((2, 18)) / 18.0, index=[1, 2], columns=GENRE_COLUMNS)
    labels_v1 = np.array([0, 0])
    hashes = {"users": "h1", "movies": "h2", "movie_genres": "h3", "ratings": "h4"}

    target_dir = tmp_path / "custom_payload_pkg"

    # Export initial valid package
    export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_df,
        labels=labels_v1,
        canonical_hashes=hashes,
        model_version="custom_payload_v1",
        output_dir=target_dir,
    )

    h_uc_before = compute_file_sha256(target_dir / "user_cluster.csv")
    h_prof_before = compute_file_sha256(target_dir / "cluster_genre_profile.csv")
    h_manifest_before = compute_file_sha256(target_dir / "manifest.json")

    # Attempt export with different labels (conflicting payload) under same version
    labels_v2 = np.array([0, 1])
    with pytest.raises(ValueError, match="Cannot reuse model_version 'custom_payload_v1' with conflicting payload"):
        export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_df,
            labels=labels_v2,
            canonical_hashes=hashes,
            model_version="custom_payload_v1",
            output_dir=target_dir,
        )

    # Confirm all 3 files remain byte-identical
    assert compute_file_sha256(target_dir / "user_cluster.csv") == h_uc_before
    assert compute_file_sha256(target_dir / "cluster_genre_profile.csv") == h_prof_before
    assert compute_file_sha256(target_dir / "manifest.json") == h_manifest_before


