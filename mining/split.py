"""
Temporal Split Module for MovieLens 1M Q2 Recommendation (Step 9A).
According to Data Contract v2 and project specifications.

Implements:
- Global timestamp quantile-based threshold selection near 70% (t1) and 85% (t2).
- Non-overlapping, non-leaking temporal partitioning:
    * Train:      timestamp <= t1
    * Validation: t1 < timestamp <= t2
    * Test:       timestamp > t2
- Deterministic boundary handling ensuring records with identical timestamps stay on the same side.
- Manifest generation and serialization to results/mining/split_manifest.json.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mining.clustering import verify_and_hash_input_tables
from mining.data_io import CANONICAL_MANIFEST_PATH, load_data

DEFAULT_OUTPUT_MANIFEST = REPO_ROOT / "results" / "mining" / "split_manifest.json"

# Fixed global quantile targets
DEFAULT_Q1 = 0.70
DEFAULT_Q2 = 0.85

# Frozen canonical timestamp thresholds verified on MovieLens 1M canonical dataset
FROZEN_T1 = 974862386  # 2000-11-22T03:06:26Z (Train <= t1: 700,148 rows ~ 70.0002%)
FROZEN_T2 = 976422051  # 2000-12-10T04:20:51Z (Val (t1, t2]: 150,029 rows ~ 14.9998%, Test > t2: 150,032 rows ~ 15.0001%)


def compute_temporal_split_thresholds(
    ratings_df: pd.DataFrame,
    q1: float = DEFAULT_Q1,
    q2: float = DEFAULT_Q2,
) -> Tuple[int, int]:
    """
    Computes global integer Unix timestamp thresholds near q1 (default 70%) and q2 (default 85%).
    
    Guarantees:
    - Sorts timestamps and uses numpy.quantile to determine boundary timestamps.
    - Truncates to integer Unix seconds.
    - Strictly enforces t1 < t2.
    """
    if "timestamp" not in ratings_df.columns:
        raise ValueError("ratings_df must contain 'timestamp' column")
    if len(ratings_df) == 0:
        raise ValueError("ratings_df cannot be empty")
    if not (0.0 < q1 < q2 < 1.0):
        raise ValueError(f"Quantiles must satisfy 0 < q1 < q2 < 1, got q1={q1}, q2={q2}")

    ts = ratings_df["timestamp"].values
    t1 = int(np.quantile(ts, q1))
    t2 = int(np.quantile(ts, q2))

    if t1 >= t2:
        raise ValueError(f"Calculated thresholds violate t1 < t2: t1={t1}, t2={t2}")

    return t1, t2


def split_ratings_by_timestamp(
    ratings_df: pd.DataFrame,
    t1: int,
    t2: int,
) -> Dict[str, pd.DataFrame]:
    """
    Partitions ratings into Train, Validation, and Test subsets based on t1 and t2.
    
    Partition rules:
    - Train:      timestamp <= t1
    - Validation: t1 < timestamp <= t2
    - Test:       timestamp > t2
    
    All ratings sharing the exact same timestamp stay strictly on the same side.
    """
    if t1 >= t2:
        raise ValueError(f"Invalid thresholds: t1 ({t1}) must be strictly less than t2 ({t2})")

    train_mask = ratings_df["timestamp"] <= t1
    val_mask = (ratings_df["timestamp"] > t1) & (ratings_df["timestamp"] <= t2)
    test_mask = ratings_df["timestamp"] > t2

    train_df = ratings_df[train_mask].copy()
    val_df = ratings_df[val_mask].copy()
    test_df = ratings_df[test_mask].copy()

    # Verification assertions
    total_split = len(train_df) + len(val_df) + len(test_df)
    if total_split != len(ratings_df):
        raise RuntimeError(
            f"Row count mismatch during split: total={len(ratings_df)}, split sum={total_split}"
        )

    if len(train_df) > 0 and len(val_df) > 0:
        assert train_df["timestamp"].max() < val_df["timestamp"].min(), "Train and Validation timestamps overlap!"
    if len(val_df) > 0 and len(test_df) > 0:
        assert val_df["timestamp"].max() < test_df["timestamp"].min(), "Validation and Test timestamps overlap!"

    return {
        "train": train_df,
        "validation": val_df,
        "test": test_df,
    }


def compute_partition_metadata(
    df: pd.DataFrame,
    total_ratings: int,
) -> Dict[str, Any]:
    """Computes summary statistics for a rating partition."""
    count = len(df)
    pct = (count / total_ratings * 100.0) if total_ratings > 0 else 0.0
    if count == 0:
        return {
            "row_count": 0,
            "percentage": 0.0,
            "min_timestamp": None,
            "max_timestamp": None,
            "min_rated_at_utc": None,
            "max_rated_at_utc": None,
            "unique_users": 0,
            "unique_movies": 0,
        }

    min_ts = int(df["timestamp"].min())
    max_ts = int(df["timestamp"].max())
    min_utc = datetime.fromtimestamp(min_ts, timezone.utc).isoformat().replace("+00:00", "Z")
    max_utc = datetime.fromtimestamp(max_ts, timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "row_count": int(count),
        "percentage": round(pct, 4),
        "min_timestamp": min_ts,
        "max_timestamp": max_ts,
        "min_rated_at_utc": min_utc,
        "max_rated_at_utc": max_utc,
        "unique_users": int(df["user_id"].nunique()),
        "unique_movies": int(df["movie_id"].nunique()),
    }


def analyze_cohort_eligibility(
    train_history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    min_train_ratings: int = 5,
    min_pos_rating: int = 4,
) -> Dict[str, Any]:
    """
    Analyzes user cohort eligibility and cold-start movie statistics for evaluation.
    
    Cohort rules:
    - User has >= min_train_ratings in training history.
    - User has >= 1 rating >= min_pos_rating in evaluation period.
    """
    # Training history user activity
    train_counts = train_history_df.groupby("user_id").size()
    users_with_min_train = set(train_counts[train_counts >= min_train_ratings].index)

    # Evaluation period activity
    eval_active_users = set(eval_df["user_id"].unique())
    eval_pos_users = set(eval_df[eval_df["rating"] >= min_pos_rating]["user_id"].unique())

    # Eligible cohort: intersection
    eligible_users = users_with_min_train.intersection(eval_pos_users)

    # Exclusions breakdown
    excluded_insufficient_train = eval_active_users - users_with_min_train
    excluded_no_positives = (eval_active_users.intersection(users_with_min_train)) - eval_pos_users

    # Catalog & novel movies analysis
    train_movies = set(train_history_df["movie_id"].unique())
    eval_movies = set(eval_df["movie_id"].unique())
    eval_pos_movies = set(eval_df[eval_df["rating"] >= min_pos_rating]["movie_id"].unique())

    new_movies_in_eval = eval_movies - train_movies
    new_pos_movies_in_eval = eval_pos_movies - train_movies

    # Novel positive movies evaluated by users in the eligible cohort
    eval_cohort_pos_df = eval_df[
        (eval_df["user_id"].isin(eligible_users)) & (eval_df["rating"] >= min_pos_rating)
    ]
    new_pos_movies_in_cohort = set(eval_cohort_pos_df["movie_id"].unique()) - train_movies

    return {
        "total_active_users_in_eval": int(len(eval_active_users)),
        "eligible_users_count": int(len(eligible_users)),
        "eligible_user_ids_hash": hashlib_sha256_set(eligible_users),
        "excluded_insufficient_train_ratings_count": int(len(excluded_insufficient_train)),
        "excluded_no_positives_in_eval_count": int(len(excluded_no_positives)),
        "training_catalog_movies": int(len(train_movies)),
        "eval_catalog_movies": int(len(eval_movies)),
        "novel_movies_in_eval_count": int(len(new_movies_in_eval)),
        "novel_positive_movies_in_eval_count": int(len(new_pos_movies_in_eval)),
        "novel_positive_movies_in_cohort_count": int(len(new_pos_movies_in_cohort)),
        "novel_positive_movies_in_cohort_ids": sorted(list(map(int, new_pos_movies_in_cohort))),
    }


def hashlib_sha256_set(items: set) -> str:
    """Computes a deterministic SHA-256 hash over a sorted set of integers/strings."""
    sorted_str = ",".join(map(str, sorted(items)))
    import hashlib
    return hashlib.sha256(sorted_str.encode("utf-8")).hexdigest()


def generate_split_manifest(
    ratings_df: pd.DataFrame,
    canonical_hashes: Dict[str, str],
    t1: int = FROZEN_T1,
    t2: int = FROZEN_T2,
) -> Dict[str, Any]:
    """Generates complete Step 9A split manifest dictionary."""
    partitions = split_ratings_by_timestamp(ratings_df, t1, t2)
    total_ratings = len(ratings_df)

    train_meta = compute_partition_metadata(partitions["train"], total_ratings)
    val_meta = compute_partition_metadata(partitions["validation"], total_ratings)
    test_meta = compute_partition_metadata(partitions["test"], total_ratings)

    # Validation evaluation cohort (uses Train as history)
    val_cohort = analyze_cohort_eligibility(
        train_history_df=partitions["train"],
        eval_df=partitions["validation"],
    )

    # Final test evaluation cohort (uses Train + Validation as history)
    train_val_df = pd.concat([partitions["train"], partitions["validation"]], ignore_index=True)
    test_cohort = analyze_cohort_eligibility(
        train_history_df=train_val_df,
        eval_df=partitions["test"],
    )

    t1_utc = datetime.fromtimestamp(t1, timezone.utc).isoformat().replace("+00:00", "Z")
    t2_utc = datetime.fromtimestamp(t2, timezone.utc).isoformat().replace("+00:00", "Z")

    manifest = {
        "contract_version": 2,
        "split_strategy": "temporal_global_quantiles",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "quantile_targets": {
            "q1": DEFAULT_Q1,
            "q2": DEFAULT_Q2,
        },
        "quantile_method": "numpy.quantile(linear) / pandas.Series.quantile(interpolation='linear')",
        "epoch_conversion": "int(quantile_timestamp)",
        "boundary_operators": {
            "train": "timestamp <= t1",
            "validation": "t1 < timestamp <= t2",
            "test": "timestamp > t2",
        },
        "tie_handling": "All ratings sharing timestamp == t1 are assigned to train; all ratings sharing timestamp == t2 are assigned to validation",
        "thresholds": {
            "t1": int(t1),
            "t1_utc": t1_utc,
            "t2": int(t2),
            "t2_utc": t2_utc,
            "t1_exact_timestamp_ratings_count": int((ratings_df["timestamp"] == t1).sum()),
            "t2_exact_timestamp_ratings_count": int((ratings_df["timestamp"] == t2).sum()),
        },
        "canonical_hashes": canonical_hashes,
        "total_dataset_ratings": int(total_ratings),
        "partitions": {
            "train": train_meta,
            "validation": val_meta,
            "test": test_meta,
        },
        "cohort_analysis": {
            "validation_phase": {
                "training_history": "train (timestamp <= t1)",
                "evaluation_period": "validation (t1 < timestamp <= t2)",
                "metrics": val_cohort,
            },
            "test_phase": {
                "training_history": "train + validation (timestamp <= t2)",
                "evaluation_period": "test (timestamp > t2)",
                "metrics": test_cohort,
            },
        },
    }
    return manifest


def main():
    parser = argparse.ArgumentParser(description="MovieLens 1M Q2 Temporal Split (Step 9A)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Input data source")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_MANIFEST, help="Output manifest path")
    args = parser.parse_args()

    print(f"=== Step 9A: Q2 Temporal Split Generation (Source: {args.source}) ===")
    tables = load_data(source=args.source)
    canonical_hashes, source_hashes, g1_commit = verify_and_hash_input_tables(tables)
    ratings = tables["ratings"]

    # Compute and verify thresholds
    t1, t2 = compute_temporal_split_thresholds(ratings, DEFAULT_Q1, DEFAULT_Q2)
    if t1 != FROZEN_T1 or t2 != FROZEN_T2:
        print(f"WARNING: Computed thresholds ({t1}, {t2}) differ from frozen ({FROZEN_T1}, {FROZEN_T2})")

    manifest = generate_split_manifest(ratings, canonical_hashes, t1, t2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Split manifest successfully written to: {args.output}")
    print(f"Train:      {manifest['partitions']['train']['row_count']} rows ({manifest['partitions']['train']['percentage']}%)")
    print(f"Validation: {manifest['partitions']['validation']['row_count']} rows ({manifest['partitions']['validation']['percentage']}%)")
    print(f"Test:       {manifest['partitions']['test']['row_count']} rows ({manifest['partitions']['test']['percentage']}%)")
    print(f"Val eligible cohort: {manifest['cohort_analysis']['validation_phase']['metrics']['eligible_users_count']} users")


if __name__ == "__main__":
    main()
