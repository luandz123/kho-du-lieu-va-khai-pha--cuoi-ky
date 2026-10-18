"""
Feature Engineering Module for MovieLens 1M Q1 User Clustering (Step 8A).
According to Data Contract v2 and project specifications.

Extracts normalized 18-dimensional genre preference vectors from historical user ratings:
- Considers positive feedback (rating >= 4).
- For each positive rating, maps movie to all its constituent genres (multi-genre movies
  contribute 1 count to each genre).
- Aggregates genre counts per user: C_{u, g}.
- Normalizes by total positive genre associations: p_{u, g} = C_{u, g} / S_u, where S_u = sum_g C_{u, g}.
- Enforces exact 18 genres in alphabetical order (A-Z) per DEC-P2-007.
- Handles users without positive ratings (S_u == 0) as 'insufficient_evidence' (cluster_id = NULL),
  preventing division by zero and excluding empty vectors from training.
- Demographics (gender, age, occupation) are explicitly excluded from feature vectors.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path for direct CLI execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd

from mining.data_io import load_data, CANONICAL_MANIFEST_PATH

# 18 Standard Genres in strict Alphabetical Order per DEC-P2-007 and Contract v2
GENRE_COLUMNS: List[str] = [
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western",
]

DEFAULT_FEATURE_DIR = Path("data/features")
SUM_TOLERANCE: float = 1e-8


def extract_user_genre_preference_features(
    tables: Dict[str, pd.DataFrame],
    positive_threshold: int = 4,
    tolerance: float = SUM_TOLERANCE,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Extracts normalized user genre preference vectors from logical tables.

    Args:
        tables: Dictionary containing DataFrames for 'users', 'movies', 'movie_genres', 'ratings'.
        positive_threshold: Minimum rating score to consider positive (default: 4).
        tolerance: Numerical tolerance for vector sum == 1.0 (default: 1e-8).

    Returns:
        Tuple containing:
        - feature_matrix: pd.DataFrame of shape (N_assigned, 18), index=user_id, columns=GENRE_COLUMNS.
        - user_status_df: pd.DataFrame with columns ['user_id', 'status', 'positive_ratings_count',
          'genre_association_count'].
        - summary: Dict with extraction metadata and sanity check metrics.
    """
    users_df = tables["users"]
    movies_df = tables["movies"]
    genres_df = tables["movie_genres"]
    ratings_df = tables["ratings"]

    total_users_count = len(users_df)
    all_user_ids = sorted(users_df["user_id"].unique())

    # 1. Filter positive feedback (rating >= positive_threshold)
    pos_ratings = ratings_df[ratings_df["rating"] >= positive_threshold]
    total_pos_ratings = len(pos_ratings)

    # 2. Join positive ratings with movie_genres
    # Multi-genre movies expand naturally: 1 positive rating for a movie with M genres
    # produces M positive genre association events.
    pos_genres = pos_ratings[["user_id", "movie_id"]].merge(
        genres_df[["movie_id", "genre_name"]], on="movie_id", how="inner"
    )
    total_genre_associations = len(pos_genres)

    # 3. Aggregate genre counts per user
    user_genre_counts = (
        pos_genres.groupby(["user_id", "genre_name"])
        .size()
        .unstack(fill_value=0)
    )

    # Ensure all 18 genres are present as columns in exact A-Z order
    for g in GENRE_COLUMNS:
        if g not in user_genre_counts.columns:
            user_genre_counts[g] = 0
    user_genre_counts = user_genre_counts[GENRE_COLUMNS]

    # Calculate total positive genre associations per user S_u
    row_sums = user_genre_counts.sum(axis=1)

    # 4. Identify user status
    # Users with at least 1 positive rating -> assigned
    # Users with 0 positive ratings -> insufficient_evidence
    pos_uids = set(user_genre_counts.index[row_sums > 0])
    
    # Positive rating count and genre association count per user
    user_pos_rating_counts = pos_ratings.groupby("user_id").size().to_dict()
    row_sums_dict = row_sums.to_dict()

    status_records = []
    for uid in all_user_ids:
        pos_r_count = user_pos_rating_counts.get(uid, 0)
        genre_assoc_count = int(row_sums_dict.get(uid, 0))
        if uid in pos_uids:
            status = "assigned"
        else:
            status = "insufficient_evidence"
        status_records.append({
            "user_id": uid,
            "status": status,
            "positive_ratings_count": pos_r_count,
            "genre_association_count": genre_assoc_count,
        })

    user_status_df = pd.DataFrame(status_records)

    # 5. Build normalized feature matrix for assigned users ONLY
    assigned_counts = user_genre_counts.loc[user_genre_counts.index.isin(pos_uids)].sort_index()
    assigned_sums = assigned_counts.sum(axis=1)

    # Normalize: p_{u, g} = C_{u, g} / S_u
    feature_matrix = assigned_counts.div(assigned_sums, axis=0)
    feature_matrix.index.name = "user_id"

    # 6. Sanity and contract validation
    assigned_count = len(feature_matrix)
    insufficient_count = total_users_count - assigned_count

    if assigned_count > 0:
        # Check non-negativity and finite
        assert (feature_matrix.values >= 0.0).all(), "Feature values must be non-negative"
        assert (feature_matrix.values <= 1.0).all(), "Feature values must not exceed 1.0"
        assert np.isfinite(feature_matrix.values).all(), "Feature values must be finite (no NaN, no Inf)"

        # Check sum to 1.0 within tolerance
        calculated_sums = feature_matrix.sum(axis=1)
        max_sum_deviation = float((calculated_sums - 1.0).abs().max())
        assert max_sum_deviation <= tolerance, f"Row sum deviation {max_sum_deviation} exceeds tolerance {tolerance}"
    else:
        max_sum_deviation = 0.0

    # Check column order
    assert list(feature_matrix.columns) == GENRE_COLUMNS, "Columns must match GENRE_COLUMNS A-Z"

    summary = {
        "total_users": total_users_count,
        "assigned_users_count": assigned_count,
        "insufficient_evidence_users_count": insufficient_count,
        "total_positive_ratings": total_pos_ratings,
        "total_genre_associations": total_genre_associations,
        "feature_dimensions": len(GENRE_COLUMNS),
        "genre_columns": list(GENRE_COLUMNS),
        "positive_threshold": positive_threshold,
        "tolerance": tolerance,
        "max_sum_deviation": max_sum_deviation,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    return feature_matrix, user_status_df, summary


def build_and_save_features(
    source: str = "csv",
    output_dir: Path = DEFAULT_FEATURE_DIR,
) -> Dict[str, Any]:
    """
    Loads data via data_io adapter, computes user genre features, and saves them
    to local directory (ignored by Git).
    """
    tables = load_data(source=source)
    feature_matrix, user_status_df, summary = extract_user_genre_preference_features(tables)

    summary["data_source"] = source
    canonical_manifest_path = Path("results/eda/canonical_manifest.json")
    if canonical_manifest_path.exists():
        try:
            with open(canonical_manifest_path, "r", encoding="utf-8") as f:
                c_manifest = json.load(f)
            summary["canonical_hashes"] = c_manifest.get("canonical_hashes", {})
            summary["source_code_commit"] = c_manifest.get("source_code_commit", "")
        except Exception:
            pass

    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save local feature tables (git-ignored)
    matrix_csv_path = output_dir / "user_features.csv"
    matrix_parquet_path = output_dir / "user_features.parquet"
    status_csv_path = output_dir / "user_status.csv"
    summary_json_path = output_dir / "feature_summary.json"

    feature_matrix.to_csv(matrix_csv_path, index=True)
    parquet_exported = False
    try:
        feature_matrix.to_parquet(matrix_parquet_path, index=True)
        parquet_exported = True
    except Exception:
        parquet_exported = False
    summary["parquet_exported"] = parquet_exported

    user_status_df.to_csv(status_csv_path, index=False)
    
    # Compute SHA-256 of the generated local CSV for local verification
    with open(matrix_csv_path, "rb") as f:
        matrix_hash = hashlib.sha256(f.read()).hexdigest()
    summary["local_feature_matrix_csv_sha256"] = matrix_hash

    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def main():
    parser = argparse.ArgumentParser(description="MovieLens 1M Q1 Feature Engineering (Step 8A)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Input data source")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_FEATURE_DIR, help="Local output directory")
    args = parser.parse_args()

    print(f"=== Extracting Q1 User Genre Preference Features (Step 8A, Source: {args.source}) ===")
    summary = build_and_save_features(source=args.source, output_dir=args.outdir)
    print(f"Total Users: {summary['total_users']}")
    print(f"Assigned Users (status='assigned'): {summary['assigned_users_count']}")
    print(f"Insufficient Evidence Users: {summary['insufficient_evidence_users_count']}")
    print(f"Feature Dimensions: {summary['feature_dimensions']} genres (A-Z)")
    print(f"Max Sum Deviation from 1.0: {summary['max_sum_deviation']:.2e} (tolerance: {summary['tolerance']})")
    print("Features extracted and saved locally successfully.")


if __name__ == "__main__":
    main()
