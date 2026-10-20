"""
Clustering and Profiling Module for MovieLens 1M Q1 (Step 8B).
According to Data Contract v2 and project specifications.

Implements:
- K-Means experimentation (K=2..8 on raw and StandardScaler) with fixed 2,000-user Silhouette sample.
- Stability validation across random seeds (seed 42 vs 0 and 7) using Adjusted Rand Index (ARI).
- Interpretability and demographic profiling (strictly correlational, non-causal).
- Generation of visualization figures (Elbow/Silhouette, Genre Heatmap, PCA 2D, Demographics).
- Export of G3 cluster package to results/mining/handoff/ (user_cluster.csv, cluster_genre_profile.csv, manifest.json).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

import sys
# Ensure repository root is on sys.path for direct CLI execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mining.data_io import load_data, CANONICAL_MANIFEST_PATH, compute_canonical_hash
from mining.features import (
    GENRE_COLUMNS,
    SUM_TOLERANCE,
    extract_user_genre_preference_features,
)

DEFAULT_HANDOFF_DIR = REPO_ROOT / "results" / "mining" / "handoff"
DEFAULT_RESULTS_DIR = REPO_ROOT / "results" / "mining"
CANONICAL_PROCESSED_DIR = REPO_ROOT / "data" / "processed"

MODEL_VERSION = "kmeans_k4_seed42"
CHOSEN_K = 4
CHOSEN_PREPROCESSING = "raw"
CHOSEN_SEED = 42

CLUSTER_NAMES: Dict[int, str] = {
    0: "Nhóm người dùng đánh giá đa dạng / Cân bằng các thể loại",
    1: "Nhóm người dùng đánh giá tập trung Drama & Tình cảm",
    2: "Nhóm người dùng đánh giá tập trung Hài kịch (Comedy)",
    3: "Nhóm người dùng đánh giá tập trung Hành động, Viễn tưởng & Giật gân",
}

# Frozen fingerprint for the finalized G3 package (model_version="kmeans_k4_seed42")
FROZEN_G3_MODEL_VERSION = "kmeans_k4_seed42"
FROZEN_G3_FINGERPRINT: Dict[str, Any] = {
    "k": 4,
    "preprocessing": "raw",
    "seed": 42,
    "n_init": 10,
    "canonical_hashes": {
        "users": "7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f",
        "movies": "154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b",
        "movie_genres": "9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf",
        "ratings": "06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf",
    },
    "expected_csv_hashes": {
        "user_cluster.csv": "5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93",
        "cluster_genre_profile.csv": "59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d",
    },
}


class InputDataIntegrityError(Exception):
    """Raised when loaded input data fails canonical integrity checks or manifest mismatch."""
    pass


def verify_and_hash_input_tables(
    tables: Dict[str, pd.DataFrame],
    manifest_path: Path = CANONICAL_MANIFEST_PATH,
) -> Tuple[Dict[str, str], Dict[str, str], str]:
    """
    Serializes and hashes the four DataFrames actually loaded into memory,
    strictly according to Data Contract v2 serialization rules and sorting.
    Compares the calculated hashes against the canonical manifest.

    Returns:
        canonical_hashes: Dict[str, str] mapping table_name to verified SHA-256 hash.
        source_hashes: Dict[str, str] from canonical manifest for provenance.
        g1_code_commit: str from canonical manifest for provenance.

    Raises:
        InputDataIntegrityError: if manifest is missing, required tables are missing,
                                 or any table's canonical hash mismatches.
    """
    if not manifest_path.exists():
        raise InputDataIntegrityError(f"Canonical manifest not found at: {manifest_path}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            c_meta = json.load(f)
    except Exception as e:
        raise InputDataIntegrityError(f"Failed to read canonical manifest: {e}") from e

    expected_canonical_hashes = c_meta.get("canonical_hashes", {})
    source_hashes = c_meta.get("source_hashes", {})
    g1_code_commit = c_meta.get("source_code_commit", "")

    required_tables = ["users", "movies", "movie_genres", "ratings"]
    for tbl in required_tables:
        if tbl not in expected_canonical_hashes:
            raise InputDataIntegrityError(
                f"Canonical manifest at {manifest_path} is missing expected hash for '{tbl}'"
            )
        if tbl not in tables:
            raise InputDataIntegrityError(f"Loaded tables dict is missing required table '{tbl}'")

    actual_canonical_hashes: Dict[str, str] = {}
    for tbl in required_tables:
        df = tables[tbl]
        # Directly compute canonical hash from in-memory DataFrame
        actual_hash = compute_canonical_hash(tbl, df)
        expected_hash = expected_canonical_hashes[tbl]
        if actual_hash != expected_hash:
            raise InputDataIntegrityError(
                f"Canonical hash mismatch for table '{tbl}' in loaded data! "
                f"Actual in-memory hash={actual_hash} != Expected manifest hash={expected_hash}"
            )
        actual_canonical_hashes[tbl] = actual_hash

    return actual_canonical_hashes, source_hashes, g1_code_commit


def compute_file_sha256(filepath: Path) -> str:
    """Calculates SHA-256 byte hash of a local file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_kmeans_experiments(
    feat_matrix: pd.DataFrame,
    k_range: range = range(2, 9),
    random_state: int = CHOSEN_SEED,
    sample_size: int = 2000,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Runs K-Means clustering across K=2..8 on both raw and StandardScaler features.
    Computes inertia, silhouette score on a fixed subsample of users, and cluster sizes.
    Confirms all models are fitted on all assigned users; inertia is from full fit;
    only silhouette score uses the fixed reproducible 2,000-user sample.
    """
    X_raw = feat_matrix.values
    user_ids = feat_matrix.index.values
    n_users = len(user_ids)

    # 1. Fixed reproducible sample for Silhouette scoring
    actual_sample_size = min(sample_size, n_users)
    rng = np.random.RandomState(random_state)
    sample_indices = rng.choice(n_users, size=actual_sample_size, replace=False)
    sample_user_ids = user_ids[sample_indices]
    sample_hash = hashlib.sha256(
        ",".join(map(str, sorted(sample_user_ids))).encode("utf-8")
    ).hexdigest()

    user_order_hash = hashlib.sha256(
        ",".join(map(str, user_ids)).encode("utf-8")
    ).hexdigest()
    genre_order_hash = hashlib.sha256(
        ",".join(GENRE_COLUMNS).encode("utf-8")
    ).hexdigest()

    # 2. Preprocessing transformations
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    experiments: List[Dict[str, Any]] = []

    for prep_name, X_space in [("raw", X_raw), ("standard_scaler", X_scaled)]:
        for k in k_range:
            t0 = time.time()
            km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            labels = km.fit_predict(X_space)
            runtime = time.time() - t0

            # Silhouette score on fixed sample
            X_sample = X_space[sample_indices]
            labels_sample = labels[sample_indices]
            sil = float(silhouette_score(X_sample, labels_sample, metric="euclidean", random_state=random_state))

            counts = pd.Series(labels).value_counts().sort_index().to_dict()
            cluster_sizes = [counts[c] for c in range(k)]
            min_size = min(cluster_sizes)
            max_size = max(cluster_sizes)

            # Interpretability note (neutral scientific description)
            if prep_name == "standard_scaler" and min_size < 100:
                note = "StandardScaler chia theo độ lệch chuẩn làm tăng trọng số thể loại hiếm, tạo cụm quy mô nhỏ (<100 user)"
            elif prep_name == "raw" and k == 4:
                note = "Cấu hình đề xuất: Phân tách rõ 4 chủ đề thể loại, quy mô cân đối (12.6%-41.0%), độ ổn định cao (ARI>0.97)"
            elif prep_name == "raw" and k in [2, 3]:
                note = "Silhouette cao hơn (0.22) nhưng phân chia còn thô (chủ yếu tách Drama vs Action/Comedy)"
            elif prep_name == "raw" and k >= 6:
                note = "Bắt đầu phân mảnh thành các cụm phụ quy mô nhỏ (<200 user)"
            else:
                note = "Cấu hình so sánh thử nghiệm"

            experiments.append({
                "k": k,
                "preprocessing": prep_name,
                "inertia": round(float(km.inertia_), 4),
                "silhouette_sample2000": round(sil, 4),
                "min_cluster_size": min_size,
                "max_cluster_size": max_size,
                "cluster_sizes": str(cluster_sizes),
                "runtime_sec": round(runtime, 3),
                "interpretability_notes": note,
            })

    exp_df = pd.DataFrame(experiments)
    metadata = {
        "sample_size": actual_sample_size,
        "sample_hash": sample_hash,
        "total_assigned_users": n_users,
        "random_state": random_state,
        "n_init": 10,
        "user_order_hash": user_order_hash,
        "genre_order_hash": genre_order_hash,
    }
    return exp_df, metadata


def check_model_stability(
    feat_matrix: pd.DataFrame,
    k: int = CHOSEN_K,
    preprocessing: str = CHOSEN_PREPROCESSING,
    base_seed: int = CHOSEN_SEED,
    test_seeds: Tuple[int, ...] = (0, 7),
) -> Dict[str, Any]:
    """
    Evaluates stability of the selected K-Means configuration across different random seeds using ARI.
    """
    X = feat_matrix.values if preprocessing == "raw" else StandardScaler().fit_transform(feat_matrix.values)

    km_base = KMeans(n_clusters=k, random_state=base_seed, n_init=10).fit(X)
    labels_base = km_base.labels_

    stability_results: Dict[str, Any] = {
        "base_seed": base_seed,
        "k": k,
        "preprocessing": preprocessing,
        "pairwise_ari": {},
    }

    for seed in test_seeds:
        km_test = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(X)
        ari = float(adjusted_rand_score(labels_base, km_test.labels_))
        stability_results["pairwise_ari"][f"seed_{base_seed}_vs_seed_{seed}"] = round(ari, 4)

    return stability_results


def plot_elbow_and_silhouette(
    exp_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generates and saves the 2-panel Elbow and Silhouette comparison figure."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    raw_df = exp_df[exp_df["preprocessing"] == "raw"].sort_values("k")
    scaled_df = exp_df[exp_df["preprocessing"] == "standard_scaler"].sort_values("k")

    # Panel 1: Inertia (Elbow) - plotted on separate twin axes because scales differ
    ax1 = axes[0]
    l1 = ax1.plot(raw_df["k"], raw_df["inertia"], marker="o", color="#1f77b4", label="Raw (L1 simplex)")
    ax1.set_xlabel("Number of Clusters (K)")
    ax1.set_ylabel("Inertia (Raw SSE)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")

    ax1_twin = ax1.twinx()
    l2 = ax1_twin.plot(scaled_df["k"], scaled_df["inertia"], marker="s", color="#ff7f0e", linestyle="--", label="StandardScaler SSE")
    ax1_twin.set_ylabel("Inertia (StandardScaler SSE)", color="#ff7f0e")
    ax1_twin.tick_params(axis="y", labelcolor="#ff7f0e")

    # Combine legends
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper right")
    ax1.set_title("Elbow Curve (Inertia vs K - Heuristic Rate of Reduction)")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Panel 2: Silhouette Score
    ax2 = axes[1]
    ax2.plot(raw_df["k"], raw_df["silhouette_sample2000"], marker="o", color="#1f77b4", label="Raw (L1 simplex)")
    ax2.plot(scaled_df["k"], scaled_df["silhouette_sample2000"], marker="s", color="#ff7f0e", linestyle="--", label="StandardScaler")
    ax2.axvline(x=CHOSEN_K, color="red", linestyle=":", label=f"Selected K={CHOSEN_K}")
    ax2.set_xlabel("Number of Clusters (K)")
    ax2.set_ylabel("Silhouette Score (Fixed sample N=2000)")
    ax2.set_title("Silhouette Score vs K (Tradeoff with Interpretability & Stability)")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_cluster_genre_heatmap(
    cluster_profiles: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generates and saves heatmap of mean raw genre proportions per cluster."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Data matrix: K x 18
    data = cluster_profiles.values * 100.0  # Percentage
    im = ax.imshow(data, cmap="YlGnBu", aspect="auto")

    # Ticks & Labels
    ax.set_xticks(np.arange(len(GENRE_COLUMNS)))
    ax.set_yticks(np.arange(len(cluster_profiles.index)))
    ax.set_xticklabels(GENRE_COLUMNS, rotation=45, ha="right", fontsize=9)
    y_labels = [f"C{c}: {CLUSTER_NAMES.get(c, '')}" for c in cluster_profiles.index]
    ax.set_yticklabels(y_labels, fontsize=9)

    # Annotate values
    for i in range(len(cluster_profiles.index)):
        for j in range(len(GENRE_COLUMNS)):
            val = data[i, j]
            text_color = "white" if val > 20.0 else "black"
            ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=text_color, fontsize=8)

    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    cbar.ax.set_ylabel("Mean Genre Preference (%)", rotation=-90, va="bottom")
    ax.set_title(f"Cluster Genre Preference Profiles (K={len(cluster_profiles.index)}, Raw Proportions)", fontsize=13)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_pca_2d(
    feat_matrix: pd.DataFrame,
    labels: np.ndarray,
    output_path: Path,
) -> None:
    """Generates a 2D PCA projection scatter plot strictly for visualization illustration."""
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(feat_matrix.values)

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

    for c in sorted(np.unique(labels)):
        mask = (labels == c)
        c_name = CLUSTER_NAMES.get(c, f"C{c}")
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            c=colors[c % len(colors)],
            label=f"C{c} ({c_name[:20]}..., n={mask.sum()})",
            alpha=0.45,
            s=18,
            edgecolors="none",
        )

    var_ratio = pca.explained_variance_ratio_ * 100
    ax.set_xlabel(f"Principal Component 1 ({var_ratio[0]:.1f}% variance)")
    ax.set_ylabel(f"Principal Component 2 ({var_ratio[1]:.1f}% variance)")
    ax.set_title("2D PCA Projection of User Genre Preference Clusters (Visualization Only, Not Used for Clustering)", fontsize=11)
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_demographics_comparison(
    cluster_df: pd.DataFrame,
    users_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Generates bar charts comparing gender and age distribution per cluster vs population.
    Demographics baseline is strictly computed on the 6,038 assigned users.
    Descriptive correlation only; no causality inferred.
    """
    merged = cluster_df.merge(users_df, on="user_id", how="inner")
    clusters = sorted(merged["cluster_id"].unique())

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # 1. Gender distribution
    gender_cats = ["M", "F"]
    pop_gender = merged["gender"].value_counts(normalize=True).reindex(gender_cats, fill_value=0) * 100
    x = np.arange(len(clusters) + 1)
    width = 0.35

    m_shares = []
    f_shares = []
    for c in clusters:
        c_sub = merged[merged["cluster_id"] == c]
        g_shares = c_sub["gender"].value_counts(normalize=True).reindex(gender_cats, fill_value=0) * 100
        m_shares.append(g_shares["M"])
        f_shares.append(g_shares["F"])
    m_shares.append(pop_gender["M"])
    f_shares.append(pop_gender["F"])

    labels = [f"C{c}: {CLUSTER_NAMES.get(c, '')[:14]}..." for c in clusters] + ["Baseline (6,038 assigned)"]

    axes[0].bar(x - width/2, m_shares, width, label="Male (M)", color="#3470a3")
    axes[0].bar(x + width/2, f_shares, width, label="Female (F)", color="#e27c7c")
    axes[0].set_ylabel("Share (%)")
    axes[0].set_title("Gender Composition Across Clusters vs Baseline (Descriptive Post-Hoc Correlation)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=9)
    axes[0].legend(loc="upper right")
    axes[0].grid(axis="y", linestyle=":", alpha=0.6)

    # 2. Age group distribution
    age_groups = ["Under 18", "18-24", "25-34", "35-44", "45-49", "50-55", "56+"]
    pop_age = merged["age_group"].value_counts(normalize=True).reindex(age_groups, fill_value=0) * 100

    age_data = []
    for c in clusters:
        c_sub = merged[merged["cluster_id"] == c]
        age_shares = c_sub["age_group"].value_counts(normalize=True).reindex(age_groups, fill_value=0) * 100
        age_data.append(age_shares.values)
    age_data.append(pop_age.values)

    age_matrix = np.array(age_data)  # shape: (n_clusters + 1, 7)
    bottom = np.zeros(len(x))
    cmap = plt.get_cmap("tab10")

    for idx, ag in enumerate(age_groups):
        values = age_matrix[:, idx]
        axes[1].bar(x, values, width=0.55, bottom=bottom, label=ag, color=cmap(idx))
        bottom += values

    axes[1].set_ylabel("Cumulative Share (%)")
    axes[1].set_title("Age Group Composition Across Clusters vs Baseline (Descriptive Post-Hoc Correlation)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=9)
    axes[1].legend(loc="upper right", bbox_to_anchor=(1.15, 1.0), fontsize=9)
    axes[1].grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def export_g3_handoff_package(
    user_status_df: pd.DataFrame,
    feat_matrix: pd.DataFrame,
    labels: np.ndarray,
    canonical_hashes: Dict[str, str],
    model_version: str = MODEL_VERSION,
    output_dir: Path = DEFAULT_HANDOFF_DIR,
    source_hashes: Optional[Dict[str, str]] = None,
    g1_code_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Exports G3 cluster package strictly complying with Data Contract v2:
    - user_cluster.csv: (user_id, cluster_id, status, model_version)
    - cluster_genre_profile.csv: (cluster_id, genre_name, mean_preference, n_users)
    - manifest.json: Full contract v2 metadata, actual verified canonical_hashes, and checksums.

    Publication guarantees & limitations:
    - Pre-flight validation: Fully constructs DataFrames, serializes CSV bytes, and computes
      SHA-256 hashes in memory. Validates contract rules, frozen fingerprints, existing package
      internal consistency, and version anti-reuse BEFORE touching any target files.
      If validation fails at this stage, any existing package on disk remains completely untouched.
    - Publication semantics: Staged files are published sequentially via individual `os.replace` calls.
      On POSIX filesystems, each `os.replace` is atomic per file, but the sequence of three replacements
      is NOT an all-or-nothing multi-file transaction. An unhandled I/O failure or abrupt termination
      between replaces could leave the destination directory in an inconsistent/corrupted state.
    - Downstream receiver requirement: Consumers (Person 1 / Analytics) MUST verify the manifest and
      both CSV checksums before ingesting. If an inconsistent/corrupted package is detected, ingestion
      must abort immediately and a clean reproduction must be run into a new directory, preserving
      the faulty directory for diagnostic inspection. No transactional filesystem engine or power-loss
      rollback is implemented.
    """
    output_dir = Path(output_dir)
    assigned_user_ids = feat_matrix.index.values
    k_clusters = len(np.unique(labels))

    # 1. Static parameter and frozen fingerprint validation
    if model_version == FROZEN_G3_MODEL_VERSION:
        if k_clusters != FROZEN_G3_FINGERPRINT["k"]:
            raise ValueError(
                f"model_version '{FROZEN_G3_MODEL_VERSION}' is frozen for K={FROZEN_G3_FINGERPRINT['k']}, "
                f"but received K={k_clusters}"
            )
        if CHOSEN_PREPROCESSING != FROZEN_G3_FINGERPRINT["preprocessing"]:
            raise ValueError(
                f"model_version '{FROZEN_G3_MODEL_VERSION}' is frozen for preprocessing '{FROZEN_G3_FINGERPRINT['preprocessing']}', "
                f"but received '{CHOSEN_PREPROCESSING}'"
            )
        if CHOSEN_SEED != FROZEN_G3_FINGERPRINT["seed"]:
            raise ValueError(
                f"model_version '{FROZEN_G3_MODEL_VERSION}' is frozen for seed {FROZEN_G3_FINGERPRINT['seed']}, "
                f"but received seed {CHOSEN_SEED}"
            )
        expected_can_hashes = FROZEN_G3_FINGERPRINT["canonical_hashes"]
        for tbl, exp_h in expected_can_hashes.items():
            act_h = canonical_hashes.get(tbl)
            if act_h != exp_h:
                raise ValueError(
                    f"model_version '{FROZEN_G3_MODEL_VERSION}' is frozen for canonical dataset. "
                    f"Table '{tbl}' hash mismatch: actual={act_h} != expected={exp_h}"
                )

    # 2. Existing package consistency and anti-reuse check on disk (PRE-FLIGHT)
    manifest_path = output_dir / "manifest.json"
    user_cluster_csv_path = output_dir / "user_cluster.csv"
    profile_csv_path = output_dir / "cluster_genre_profile.csv"

    existing_manifest: Optional[Dict[str, Any]] = None
    has_manifest = manifest_path.exists()
    has_uc = user_cluster_csv_path.exists()
    has_prof = profile_csv_path.exists()

    if has_manifest or has_uc or has_prof:
        if not has_manifest:
            raise ValueError(
                f"Corrupted or incomplete existing handoff package at '{output_dir}': "
                f"CSV file(s) exist but 'manifest.json' is missing."
            )
        if not has_uc or not has_prof:
            raise ValueError(
                f"Corrupted or incomplete existing handoff package at '{output_dir}': "
                f"'manifest.json' exists but required CSV file(s) are missing."
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                existing_manifest = json.load(f)
        except Exception as e:
            raise ValueError(f"Corrupted existing manifest at '{manifest_path}': invalid JSON ({e})")

        if not isinstance(existing_manifest, dict) or "files" not in existing_manifest:
            raise ValueError(f"Corrupted existing manifest at '{manifest_path}': missing required 'files' dictionary")

        # Validate internal consistency of existing files on disk
        existing_files = existing_manifest.get("files", {})
        for expected_fname in ["user_cluster.csv", "cluster_genre_profile.csv"]:
            if expected_fname not in existing_files or "sha256" not in existing_files[expected_fname]:
                raise ValueError(
                    f"Corrupted existing manifest at '{manifest_path}': missing checksum entry for '{expected_fname}'"
                )
            expected_disk_hash = existing_files[expected_fname]["sha256"]
            actual_disk_hash = compute_file_sha256(output_dir / expected_fname)
            if actual_disk_hash != expected_disk_hash:
                raise ValueError(
                    f"Corrupted existing handoff package at '{output_dir}': "
                    f"checksum mismatch for '{expected_fname}' (disk={actual_disk_hash} != manifest={expected_disk_hash})"
                )

        # Anti-reuse validation for canonical_hashes under same model_version
        if existing_manifest.get("model_version") == model_version:
            existing_can = existing_manifest.get("canonical_hashes", {})
            if existing_can and existing_can != canonical_hashes:
                raise ValueError(
                    f"Cannot reuse model_version '{model_version}' with different input data. "
                    f"Existing package at '{output_dir}' has canonical_hashes={existing_can}, "
                    f"attempting to export with {canonical_hashes}"
                )

    # 3. Construct DataFrames in memory and strictly validate Data Contract v2
    label_map = dict(zip(assigned_user_ids, labels))

    user_cluster_records = []
    for _, row in user_status_df.sort_values("user_id").iterrows():
        uid = int(row["user_id"])
        status = row["status"]
        if status == "assigned":
            c_id: Optional[int] = int(label_map[uid])
        else:
            c_id = None
        user_cluster_records.append({
            "user_id": uid,
            "cluster_id": "" if c_id is None else str(c_id),
            "status": status,
            "model_version": model_version,
        })

    user_cluster_df = pd.DataFrame(user_cluster_records)

    # Validate user_cluster contract in memory
    if list(user_cluster_df.columns) != ["user_id", "cluster_id", "status", "model_version"]:
        raise ValueError("user_cluster DataFrame columns violate Data Contract v2")
    if len(user_cluster_df) != len(user_status_df):
        raise ValueError("User count mismatch in user_cluster DataFrame")
    assigned_mask = user_cluster_df["status"] == "assigned"
    valid_clusters = [str(c) for c in range(k_clusters)]
    if not user_cluster_df.loc[assigned_mask, "cluster_id"].isin(valid_clusters).all():
        raise ValueError("user_cluster DataFrame contains invalid cluster_id for assigned users")
    if not (user_cluster_df.loc[~assigned_mask, "cluster_id"] == "").all():
        raise ValueError("user_cluster DataFrame contains non-empty cluster_id for unassigned users")
    if not (user_cluster_df["model_version"] == model_version).all():
        raise ValueError("user_cluster DataFrame model_version mismatch")

    # Build cluster_genre_profile DataFrame in memory
    feat_df_with_cluster = feat_matrix.copy()
    feat_df_with_cluster["cluster_id"] = labels
    cluster_counts = pd.Series(labels).value_counts().to_dict()

    profile_records = []
    for c in range(k_clusters):
        c_features = feat_df_with_cluster[feat_df_with_cluster["cluster_id"] == c][GENRE_COLUMNS]
        mean_prefs = c_features.mean(axis=0)
        n_users_in_c = int(cluster_counts.get(c, 0))

        sum_mean = float(mean_prefs.sum())
        if abs(sum_mean - 1.0) > SUM_TOLERANCE:
            raise ValueError(f"Cluster {c} mean preference sum {sum_mean} exceeds tolerance {SUM_TOLERANCE}")

        for g in GENRE_COLUMNS:
            profile_records.append({
                "cluster_id": c,
                "genre_name": g,
                "mean_preference": float(mean_prefs[g]),
                "n_users": n_users_in_c,
            })

    profile_df = pd.DataFrame(profile_records)
    profile_df = profile_df.sort_values(["cluster_id", "genre_name"])

    # Validate cluster_genre_profile contract in memory
    if list(profile_df.columns) != ["cluster_id", "genre_name", "mean_preference", "n_users"]:
        raise ValueError("cluster_genre_profile DataFrame columns violate Data Contract v2")
    if len(profile_df) != k_clusters * len(GENRE_COLUMNS):
        raise ValueError(f"Profile row count mismatch: expected {k_clusters * len(GENRE_COLUMNS)}, got {len(profile_df)}")
    if not ((profile_df["mean_preference"] >= 0.0) & (profile_df["mean_preference"] <= 1.0)).all():
        raise ValueError("cluster_genre_profile contains mean_preference outside [0.0, 1.0]")

    # 4. In-memory CSV serialization and SHA-256 byte hashing
    user_cluster_bytes = user_cluster_df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    profile_bytes = profile_df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    user_cluster_sha256 = hashlib.sha256(user_cluster_bytes).hexdigest()
    profile_sha256 = hashlib.sha256(profile_bytes).hexdigest()

    # 5. Frozen fingerprint validation on serialized CSV bytes
    if model_version == FROZEN_G3_MODEL_VERSION:
        expected_csvs = FROZEN_G3_FINGERPRINT["expected_csv_hashes"]
        if user_cluster_sha256 != expected_csvs["user_cluster.csv"]:
            raise ValueError(
                f"user_cluster.csv hash mismatch for frozen model_version '{FROZEN_G3_MODEL_VERSION}': "
                f"actual={user_cluster_sha256} != expected={expected_csvs['user_cluster.csv']}"
            )
        if profile_sha256 != expected_csvs["cluster_genre_profile.csv"]:
            raise ValueError(
                f"cluster_genre_profile.csv hash mismatch for frozen model_version '{FROZEN_G3_MODEL_VERSION}': "
                f"actual={profile_sha256} != expected={expected_csvs['cluster_genre_profile.csv']}"
            )

    # 6. Anti-reuse check on payload against existing package on disk
    if existing_manifest is not None and existing_manifest.get("model_version") == model_version:
        existing_files = existing_manifest.get("files", {})
        existing_uc_hash = existing_files.get("user_cluster.csv", {}).get("sha256")
        existing_prof_hash = existing_files.get("cluster_genre_profile.csv", {}).get("sha256")
        if existing_uc_hash and existing_uc_hash != user_cluster_sha256:
            raise ValueError(
                f"Cannot reuse model_version '{model_version}' with conflicting payload in '{output_dir}': "
                f"new user_cluster.csv hash={user_cluster_sha256} != existing={existing_uc_hash}"
            )
        if existing_prof_hash and existing_prof_hash != profile_sha256:
            raise ValueError(
                f"Cannot reuse model_version '{model_version}' with conflicting payload in '{output_dir}': "
                f"new cluster_genre_profile.csv hash={profile_sha256} != existing={existing_prof_hash}"
            )

    # 7. Metadata and Manifest Preparation in memory
    if source_hashes is None:
        source_hashes = {}
        if CANONICAL_MANIFEST_PATH.exists():
            try:
                with open(CANONICAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
                    c_meta = json.load(f)
                source_hashes = c_meta.get("source_hashes", {})
                if g1_code_commit is None:
                    g1_code_commit = c_meta.get("source_code_commit", "")
            except Exception:
                pass

    features_code_path = REPO_ROOT / "mining" / "features.py"
    clustering_code_path = REPO_ROOT / "mining" / "clustering.py"
    features_code_sha256 = compute_file_sha256(features_code_path) if features_code_path.exists() else ""
    clustering_code_sha256 = compute_file_sha256(clustering_code_path) if clustering_code_path.exists() else ""

    total_users = len(user_cluster_df)
    assigned_count = (user_cluster_df["status"] == "assigned").sum()
    insufficient_count = (user_cluster_df["status"] == "insufficient_evidence").sum()

    user_order_hash = hashlib.sha256(",".join(map(str, assigned_user_ids)).encode("utf-8")).hexdigest()
    genre_order_hash = hashlib.sha256(",".join(GENRE_COLUMNS).encode("utf-8")).hexdigest()

    training_config = {
        "k": k_clusters,
        "preprocessing": CHOSEN_PREPROCESSING,
        "seed": CHOSEN_SEED,
        "n_init": 10,
        "genre_order": GENRE_COLUMNS,
        "genre_order_hash": genre_order_hash,
        "user_order_hash": user_order_hash,
        "total_assigned_users": int(assigned_count),
    }
    training_config_hash = hashlib.sha256(
        json.dumps(training_config, sort_keys=True).encode("utf-8")
    ).hexdigest()

    manifest: Dict[str, Any] = {
        "contract_version": 2,
        "model_version": model_version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": "KMeans",
        "training_config": training_config,
        "training_config_hash": training_config_hash,
        "libraries": {
            "scikit-learn": str(sklearn.__version__),
            "numpy": str(np.__version__),
            "pandas": str(pd.__version__),
            "python": sys.version.split()[0],
        },
        "canonical_hashes": canonical_hashes,
        "source_hashes": source_hashes or {},
        "code_provenance": {
            "g1_canonical_code_commit": g1_code_commit or "",
            "features_code_sha256": features_code_sha256,
            "clustering_code_sha256": clustering_code_sha256,
        },
        "data_summary": {
            "total_users": int(total_users),
            "assigned_users": int(assigned_count),
            "insufficient_evidence_users": int(insufficient_count),
            "num_clusters": k_clusters,
            "cluster_sizes": {int(k): int(v) for k, v in cluster_counts.items()},
        },
        "files": {
            "user_cluster.csv": {
                "row_count": len(user_cluster_df),
                "sha256": user_cluster_sha256,
            },
            "cluster_genre_profile.csv": {
                "row_count": len(profile_df),
                "sha256": profile_sha256,
            },
        },
    }

    manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")

    # 8. Atomic Publication via Temporary Staging Directory
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=output_dir, prefix=".staging_g3_handoff_") as staging_dir_str:
        staging_dir = Path(staging_dir_str)
        stage_uc = staging_dir / "user_cluster.csv"
        stage_prof = staging_dir / "cluster_genre_profile.csv"
        stage_manifest = staging_dir / "manifest.json"

        stage_uc.write_bytes(user_cluster_bytes)
        stage_prof.write_bytes(profile_bytes)
        stage_manifest.write_bytes(manifest_bytes)

        # Final sanity checks on staging files before replacing destination
        if compute_file_sha256(stage_uc) != user_cluster_sha256:
            raise RuntimeError("Staging user_cluster.csv corruption detected during publication")
        if compute_file_sha256(stage_prof) != profile_sha256:
            raise RuntimeError("Staging cluster_genre_profile.csv corruption detected during publication")

        # Sequential per-file atomic replacement:
        # Each os.replace is atomic per-file on POSIX filesystems.
        # Note: The 3-file sequence is not an all-or-nothing multi-file transaction.
        # An I/O error between replacements can leave an inconsistent state on disk,
        # which will be detected and rejected by pre-flight checksum checks on subsequent runs.
        os.replace(stage_uc, user_cluster_csv_path)
        os.replace(stage_prof, profile_csv_path)
        os.replace(stage_manifest, manifest_path)

    return manifest


def main():
    parser = argparse.ArgumentParser(description="MovieLens 1M Q1 Clustering & Profiling (Step 8B)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Input data source")
    parser.add_argument("--mode", choices=["reproduce", "explore", "all"], default="reproduce",
                        help="Execution mode: 'reproduce' (deterministic reproduction of chosen K=4 for P1), 'explore' (run full 14-experiment grid), 'all' (experiments, reproduction, and plots)")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_HANDOFF_DIR, help="Handoff output directory")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR, help="Results and figures directory")
    parser.add_argument("--skip-plots", action="store_true", help="Skip figure generation")
    args = parser.parse_args()

    print(f"=== Step 8B: K-Means Clustering & Profiling (Source: {args.source}, Mode: {args.mode}) ===")
    args.results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    tables = load_data(source=args.source)

    # 2. Verify and hash in-memory input DataFrames immediately after load_data
    try:
        canonical_hashes, source_hashes, g1_code_commit = verify_and_hash_input_tables(
            tables=tables,
            manifest_path=CANONICAL_MANIFEST_PATH,
        )
    except InputDataIntegrityError as e:
        print(f"FATAL: Input data integrity verification failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Extract features from verified tables
    feat_matrix, user_status_df, feat_summary = extract_user_genre_preference_features(tables)
    print(f"Features: {feat_matrix.shape[0]} assigned users, {len(user_status_df) - feat_matrix.shape[0]} insufficient evidence")

    # MODE: REPRODUCE (Deterministic reproduction of chosen K=4 model for P1 without exploring K)
    if args.mode == "reproduce":
        print(f"Reproducing chosen model: K={CHOSEN_K}, Preprocessing={CHOSEN_PREPROCESSING}, Seed={CHOSEN_SEED}, n_init=10...")
        km = KMeans(n_clusters=CHOSEN_K, random_state=CHOSEN_SEED, n_init=10)
        labels = km.fit_predict(feat_matrix.values)

        print("Exporting G3 handoff package...")
        handoff_manifest = export_g3_handoff_package(
            user_status_df=user_status_df,
            feat_matrix=feat_matrix,
            labels=labels,
            canonical_hashes=canonical_hashes,
            model_version=MODEL_VERSION,
            output_dir=args.outdir,
            source_hashes=source_hashes,
            g1_code_commit=g1_code_commit,
        )
        print(f"G3 Handoff package reproduced successfully at: {args.outdir}")
        print(f"Files: user_cluster.csv ({len(user_status_df)} rows), cluster_genre_profile.csv ({CHOSEN_K * 18} rows), manifest.json")
        return

    # MODE: EXPLORE or ALL
    print("Running K-Means experiments across 14 configurations (K=2..8 on raw and StandardScaler)...")
    exp_df, exp_meta = run_kmeans_experiments(feat_matrix)
    exp_csv_path = args.results_dir / "kmeans_experiments.csv"
    exp_df.to_csv(exp_csv_path, index=False)
    print(f"Saved experiments table (14 configs) to {exp_csv_path}")

    print(f"Evaluating chosen model stability across seeds (K={CHOSEN_K}, Preprocessing={CHOSEN_PREPROCESSING}, BaseSeed={CHOSEN_SEED})...")
    stability = check_model_stability(feat_matrix, k=CHOSEN_K, preprocessing=CHOSEN_PREPROCESSING)
    print(f"Stability ARI: {stability['pairwise_ari']}")

    # Fit chosen model
    km = KMeans(n_clusters=CHOSEN_K, random_state=CHOSEN_SEED, n_init=10)
    labels = km.fit_predict(feat_matrix.values)

    # Export G3 handoff package
    print("Exporting G3 handoff package...")
    handoff_manifest = export_g3_handoff_package(
        user_status_df=user_status_df,
        feat_matrix=feat_matrix,
        labels=labels,
        canonical_hashes=canonical_hashes,
        model_version=MODEL_VERSION,
        output_dir=args.outdir,
        source_hashes=source_hashes,
        g1_code_commit=g1_code_commit,
    )
    print(f"G3 Handoff package exported successfully to {args.outdir}")

    # Generate Figures
    if not args.skip_plots:
        print("Generating visual interpretation plots...")
        plot_elbow_and_silhouette(exp_df, args.results_dir / "kmeans_elbow_silhouette.png")

        df_w_c = feat_matrix.copy()
        df_w_c["cluster_id"] = labels
        profiles = df_w_c.groupby("cluster_id")[GENRE_COLUMNS].mean()
        plot_cluster_genre_heatmap(profiles, args.results_dir / "cluster_genre_heatmap.png")

        plot_pca_2d(feat_matrix, labels, args.results_dir / "cluster_pca_2d.png")

        plot_demographics_comparison(
            cluster_df=pd.DataFrame({"user_id": feat_matrix.index, "cluster_id": labels}),
            users_df=tables["users"],
            output_path=args.results_dir / "cluster_demographics.png",
        )
        print("Plots generated successfully in", args.results_dir)

    # Save summary JSON
    summary_path = args.results_dir / "clustering_summary.json"
    summary_data = {
        "chosen_k": CHOSEN_K,
        "chosen_preprocessing": CHOSEN_PREPROCESSING,
        "chosen_seed": CHOSEN_SEED,
        "model_version": MODEL_VERSION,
        "cluster_names": CLUSTER_NAMES,
        "stability_ari": stability["pairwise_ari"],
        "experiment_metadata": exp_meta,
        "experiments_summary": exp_df.to_dict(orient="records"),
        "handoff_manifest": handoff_manifest,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()

