"""
Popularity Baseline Module for MovieLens 1M Q2 Recommendation (Step 9B).
According to Data Contract v2, Project Specifications, and Coordinator Instructions.

Implements:
- Popularity model fitting on Train partition (timestamp <= t1):
    Counts ALL ratings per movie_id (regardless of rating value), sorted by count DESC, movie_id ASC.
- Per-user Top-K recommendations:
    Excludes all movies rated by the user in the training history.
    Takes up to K items from the user's unranked candidate universe.
    No negative sampling, no validation popularity leakage, no Q1 cluster features.
- Validation evaluation on exact eligible cohort (471 users):
    Verified against cohort hash in split_manifest.json.
    Precision@5: hits / 5 (fixed denominator).
    Recall@5: hits / |Relevant_eval(u)| (full relevant count including novel items outside train).
    Macro-averaging: arithmetic mean across all 471 users.
- Export of evaluation summary to results/mining/baseline_popularity_validation.json.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mining.clustering import compute_file_sha256, verify_and_hash_input_tables
from mining.data_io import load_data
from mining.evaluation import (
    compute_macro_metrics,
    compute_user_metrics_at_k,
    get_eligible_eval_cohort,
)
from mining.split import (
    DEFAULT_OUTPUT_MANIFEST as DEFAULT_SPLIT_MANIFEST_PATH,
    hashlib_sha256_set,
    split_ratings_by_timestamp,
)

DEFAULT_BASELINE_OUTPUT = REPO_ROOT / "results" / "mining" / "baseline_popularity_validation.json"


def fit_popularity_model(train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fits popularity baseline model strictly from the training partition (timestamp <= t1).
    
    Rules:
    - Counts ALL ratings per movie_id (1..5 stars), not just positive ratings (>=4).
    - Sorts deterministically: rating_count DESC, movie_id ASC.
    """
    if "movie_id" not in train_df.columns:
        raise ValueError("train_df must contain 'movie_id' column")

    pop_df = (
        train_df.groupby("movie_id", as_index=False)
        .size()
        .rename(columns={"size": "rating_count"})
        .sort_values(by=["rating_count", "movie_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return pop_df


def recommend_for_user_popularity(
    user_train_history: Set[int],
    popularity_ranking: List[int],
    top_k: int = 5,
) -> List[int]:
    """
    Generates Top-K recommendation list for a single user using popularity ranking.
    
    Rules:
    - Excludes all items previously rated by the user in training history.
    - Selects up to top_k items.
    - If fewer than top_k items are available in the candidate universe, returns all available.
    """
    recommended: List[int] = []
    for mid in popularity_ranking:
        if mid not in user_train_history:
            recommended.append(mid)
            if len(recommended) == top_k:
                break
    return recommended


def run_popularity_validation_pipeline(
    ratings_df: pd.DataFrame,
    manifest_path: Path = DEFAULT_SPLIT_MANIFEST_PATH,
    top_k: int = 5,
    canonical_hashes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Executes complete Popularity Baseline evaluation pipeline on Validation set.
    """
    start_time = time.time()

    # 1. Load and verify split manifest
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing split manifest at: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        split_manifest = json.load(f)

    manifest_sha256 = compute_file_sha256(manifest_path)
    t1 = int(split_manifest["thresholds"]["t1"])
    t2 = int(split_manifest["thresholds"]["t2"])
    expected_cohort_hash = split_manifest["cohort_analysis"]["validation_phase"]["metrics"]["eligible_user_ids_hash"]
    expected_cohort_size = int(split_manifest["cohort_analysis"]["validation_phase"]["metrics"]["eligible_users_count"])

    # Verify canonical hashes against split manifest if provided
    manifest_canonical_hashes = split_manifest.get("canonical_hashes", {})
    if canonical_hashes is not None and manifest_canonical_hashes:
        for tbl_name, expected_h in manifest_canonical_hashes.items():
            actual_h = canonical_hashes.get(tbl_name)
            if actual_h and actual_h != expected_h:
                raise ValueError(
                    f"Runtime canonical hash drift for table '{tbl_name}': actual {actual_h} != expected {expected_h}"
                )

    # 2. Split dataset by verified thresholds
    splits = split_ratings_by_timestamp(ratings_df, t1, t2)
    train_df = splits["train"]
    val_df = splits["validation"]

    # Runtime split integrity checks against approved split_manifest
    expected_train_count = int(split_manifest["partitions"]["train"]["row_count"])
    expected_val_count = int(split_manifest["partitions"]["validation"]["row_count"])
    if len(ratings_df) == int(split_manifest.get("total_dataset_ratings", 1000209)):
        if len(train_df) != expected_train_count:
            raise ValueError(f"Train row count mismatch: got {len(train_df)}, expected {expected_train_count}")
        if len(val_df) != expected_val_count:
            raise ValueError(f"Validation row count mismatch: got {len(val_df)}, expected {expected_val_count}")

    # 3. Determine eligible evaluation cohort
    eligible_users, cohort_diag = get_eligible_eval_cohort(train_df, val_df, min_train_ratings=5, min_pos_rating=4)
    actual_cohort_hash = hashlib_sha256_set(eligible_users)

    if len(eligible_users) != expected_cohort_size:
        raise ValueError(f"Cohort size mismatch: got {len(eligible_users)}, expected {expected_cohort_size}")
    if actual_cohort_hash != expected_cohort_hash:
        raise ValueError(f"Cohort hash mismatch: got {actual_cohort_hash}, expected {expected_cohort_hash}")

    # 4. Fit Popularity model on Train
    popularity_df = fit_popularity_model(train_df)
    popularity_ranking = popularity_df["movie_id"].tolist()
    train_catalog = set(popularity_ranking)

    expected_train_catalog_size = int(split_manifest["partitions"]["train"]["unique_movies"])
    if len(ratings_df) == int(split_manifest.get("total_dataset_ratings", 1000209)):
        if len(train_catalog) != expected_train_catalog_size:
            raise ValueError(f"Train catalog size mismatch: got {len(train_catalog)}, expected {expected_train_catalog_size}")

    # 5. Extract user histories and validation positives
    train_history_map = train_df.groupby("user_id")["movie_id"].apply(set).to_dict()
    val_pos_df = val_df[val_df["rating"] >= 4]
    val_positives_map = val_pos_df.groupby("user_id")["movie_id"].apply(set).to_dict()

    # Calculate per-user candidate universe sizes (train_catalog - user_train_history)
    candidate_sizes = [len(train_catalog - train_history_map.get(uid, set())) for uid in eligible_users]
    min_candidate_size = min(candidate_sizes) if candidate_sizes else 0
    max_candidate_size = max(candidate_sizes) if candidate_sizes else 0

    # Runtime assertion for canonical MovieLens 1M validation cohort
    if len(ratings_df) == int(split_manifest.get("total_dataset_ratings", 1000209)):
        if min_candidate_size != 2193 or max_candidate_size != 3628:
            raise ValueError(
                f"Candidate universe min/max drift: got min={min_candidate_size}, max={max_candidate_size}, expected 2193/3628"
            )

    # 6. Generate recommendations and compute metrics per eligible user
    user_metrics: List[Dict[str, Any]] = []
    short_candidate_users_count = 0
    total_hits = 0

    sorted_cohort_users = sorted(eligible_users)
    for uid in sorted_cohort_users:
        user_hist = train_history_map.get(uid, set())
        candidate_universe = train_catalog - user_hist
        if len(candidate_universe) < top_k:
            short_candidate_users_count += 1

        recs = recommend_for_user_popularity(user_hist, popularity_ranking, top_k=top_k)

        # Integrity validations
        assert len(recs) == len(set(recs)), f"User {uid} received duplicate recommendations: {recs}"
        assert set(recs).issubset(train_catalog), f"User {uid} received items outside train catalog: {recs}"
        assert set(recs).isdisjoint(user_hist), f"User {uid} received items already in train history: {recs}"
        assert len(recs) <= top_k, f"User {uid} received more than {top_k} recommendations"

        user_positives = val_positives_map.get(uid, set())
        m = compute_user_metrics_at_k(recs, user_positives, k=top_k)
        total_hits += m["hits"]
        user_metrics.append(m)

    # 7. Aggregate macro metrics
    macro = compute_macro_metrics(user_metrics)
    runtime_sec = round(time.time() - start_time, 4)

    # 8. Compute Novel movie statistics and ratios
    eval_movies = set(val_df["movie_id"].unique())
    eval_pos_movies = set(val_pos_df["movie_id"].unique())
    cohort_pos_movies = set(
        val_pos_df[val_pos_df["user_id"].isin(eligible_users)]["movie_id"].unique()
    )

    novel_movies_all = eval_movies - train_catalog
    novel_pos_movies_all = eval_pos_movies - train_catalog
    novel_pos_movies_cohort = cohort_pos_movies - train_catalog

    total_eval_movies_count = len(eval_movies)
    total_eval_pos_movies_count = len(eval_pos_movies)
    total_cohort_pos_movies_count = len(cohort_pos_movies)

    total_active_eval_users = int(cohort_diag["total_active_eval_users"])
    excluded_count = total_active_eval_users - len(eligible_users)
    exclusion_rate = (excluded_count / total_active_eval_users * 100.0) if total_active_eval_users > 0 else 0.0

    # 9. Compute hashes
    code_hash = compute_file_sha256(Path(__file__).resolve())
    config_dict = {
        "evaluation_phase": "validation",
        "top_k": int(top_k),
        "training_cutoff_timestamp": t1,
        "evaluation_cutoff_timestamp": t2,
        "min_train_ratings": 5,
        "min_pos_rating": 4,
    }
    config_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode("utf-8")).hexdigest()

    effective_canonical_hashes = canonical_hashes or manifest_canonical_hashes

    results = {
        "contract_version": 2,
        "model_name": "popularity",
        "evaluation_phase": "validation",
        "top_k": int(top_k),
        "cutoff": int(top_k),
        "training_cutoff_timestamp": t1,
        "evaluation_cutoff_timestamp": t2,
        "thresholds": {
            "t1": t1,
            "t1_utc": split_manifest["thresholds"].get("t1_utc", "2000-11-22T03:06:26Z"),
            "t2": t2,
            "t2_utc": split_manifest["thresholds"].get("t2_utc", "2000-12-10T04:20:51Z"),
        },
        "canonical_hashes": effective_canonical_hashes,
        "provenance": {
            "split_manifest_path": "results/mining/split_manifest.json",
            "split_manifest_sha256": manifest_sha256,
            "baseline_code_sha256": code_hash,
            "config_hash": config_hash,
            "runtime_seconds": runtime_sec,
        },
        "cohort": {
            "evaluation_phase": "validation",
            "eligible_cohort_size": int(len(eligible_users)),
            "eligible_user_ids_hash": actual_cohort_hash,
            "total_active_eval_users": total_active_eval_users,
            "excluded_users_count": int(excluded_count),
            "exclusion_rate_percentage": round(exclusion_rate, 4),
            "excluded_insufficient_train_count": int(cohort_diag["excluded_insufficient_train_ratings"]),
            "excluded_no_positives_in_eval_count": int(cohort_diag["excluded_no_positives_in_eval"]),
            "candidate_universe_stats": {
                "formula": "train_catalog - user_train_history",
                "training_catalog_size": len(train_catalog),
                "min_candidates_per_user": int(min_candidate_size),
                "max_candidates_per_user": int(max_candidate_size),
            },
            "short_candidate_universe_users_count": int(short_candidate_users_count),
        },
        "novel_movies_breakdown": {
            "all_validation_novel_movies": {
                "count": int(len(novel_movies_all)),
                "denominator_total_validation_catalog": int(total_eval_movies_count),
                "ratio_percentage": round(len(novel_movies_all) / total_eval_movies_count * 100.0, 4),
            },
            "all_validation_novel_positive_movies": {
                "count": int(len(novel_pos_movies_all)),
                "denominator_total_validation_positive_movies": int(total_eval_pos_movies_count),
                "ratio_percentage": round(len(novel_pos_movies_all) / total_eval_pos_movies_count * 100.0, 4),
            },
            "eligible_cohort_novel_positive_movies": {
                "count": int(len(novel_pos_movies_cohort)),
                "denominator_total_cohort_positive_movies": int(total_cohort_pos_movies_count),
                "ratio_percentage": round(len(novel_pos_movies_cohort) / total_cohort_pos_movies_count * 100.0, 4),
                "movie_ids": sorted(list(map(int, novel_pos_movies_cohort))),
            },
        },
        "metrics": {
            "top_k": int(top_k),
            "total_evaluated_users": int(macro["total_users"]),
            "total_hits": int(total_hits),
            "macro_precision_at_5": round(macro["macro_precision"], 6),
            "macro_recall_at_5": round(macro["macro_recall"], 6),
            "macro_precision_at_5_percentage": round(macro["macro_precision"] * 100.0, 4),
            "macro_recall_at_5_percentage": round(macro["macro_recall"] * 100.0, 4),
        },
        "popularity_fit_summary": {
            "training_items_count": int(len(popularity_df)),
            "top_10_popular_movie_ids": popularity_ranking[:10],
            "top_10_popular_movie_counts": [int(c) for c in popularity_df["rating_count"].head(10).tolist()],
        },
    }
    return results


def main():
    parser = argparse.ArgumentParser(description="Popularity Baseline Evaluation for MovieLens 1M Q2 (Step 9B)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Input data source")
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT_MANIFEST_PATH, help="Path to split_manifest.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_BASELINE_OUTPUT, help="Path to output results JSON")
    parser.add_argument("--top-k", type=int, default=5, help="Recommendation cutoff K")
    args = parser.parse_args()

    print(f"=== Step 9B: Popularity Baseline Evaluation (Source: {args.source}, K={args.top_k}) ===")
    tables = load_data(source=args.source)
    canonical_hashes, source_hashes, g1_commit = verify_and_hash_input_tables(tables)
    ratings = tables["ratings"]

    results = run_popularity_validation_pipeline(
        ratings_df=ratings,
        manifest_path=args.split_manifest,
        top_k=args.top_k,
        canonical_hashes=canonical_hashes,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results written to: {args.output}")
    print(f"Cohort Size:      {results['metrics']['total_evaluated_users']} users")
    print(f"Total Hits:       {results['metrics']['total_hits']} hits")
    print(f"Macro-Precision@5: {results['metrics']['macro_precision_at_5']:.6f} ({results['metrics']['macro_precision_at_5_percentage']}%)")
    print(f"Macro-Recall@5:    {results['metrics']['macro_recall_at_5']:.6f} ({results['metrics']['macro_recall_at_5_percentage']}%)")
    print(f"Candidate Universe: min={results['cohort']['candidate_universe_stats']['min_candidates_per_user']}, max={results['cohort']['candidate_universe_stats']['max_candidates_per_user']}")
    print(f"Exclusion Rate:    {results['cohort']['exclusion_rate_percentage']}% ({results['cohort']['excluded_users_count']} / {results['cohort']['total_active_eval_users']})")
    print(f"Novel Positive in Cohort: {results['novel_movies_breakdown']['eligible_cohort_novel_positive_movies']['count']} movies (IDs: {results['novel_movies_breakdown']['eligible_cohort_novel_positive_movies']['movie_ids']})")


if __name__ == "__main__":
    main()
