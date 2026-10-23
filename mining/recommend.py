"""
CLI Recommendation Engine for MovieLens 1M Q2 (Step 10B).
According to Data Contract v2, Project Specifications, and Coordinator Instructions.

Supports:
- Flags: --user-id, --top-n, --source (raw|csv|dw), --mode (evaluation|demo)
- Modes:
    * evaluation: Uses frozen model fitted strictly on Train+Validation (timestamp <= t2 = 976422051).
                  History and seeds are strictly bounded at t2. Does not compute test metrics.
    * demo: Fits model on full dataset history (timestamp <= max, 1,000,209 ratings).
            Distinct model_version marked clearly with DEMO. Does not export offline metrics.
- Output:
    * Valid seeds display (ratings >= 4 in history).
    * Top-N recommendations with Movie ID, Title, Genres, Score Type (cf vs popularity_fallback), and Score.
    * Clear explanation: CF score is a similarity-weighted ranking score, NOT a predicted star rating.
    * Distinct separation between similarity scores and popularity fallback (no mixing).
    * Robust handling of edge cases: user with many seeds, few seeds, zero seeds, and non-existent user.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mining.baseline import fit_popularity_model, recommend_for_user_popularity
from mining.cf import (
    build_sparse_ratings_matrix,
    compute_item_cosine_similarities_top_k,
    recommend_for_user_cf,
)
from mining.clustering import verify_and_hash_input_tables, InputDataIntegrityError
from mining.data_io import load_data

DEFAULT_TEST_RECEIPT = REPO_ROOT / "results" / "mining" / "cf_test_evaluation_receipt.json"
EVALUATION_CUTOFF_TIMESTAMP = 976422051  # t2


def load_evaluation_manifest(receipt_path: Path = DEFAULT_TEST_RECEIPT) -> Dict[str, Any]:
    """Loads official evaluation receipt manifest to enforce configuration and hash bindings."""
    if not receipt_path.exists():
        raise FileNotFoundError(
            f"Official evaluation receipt manifest not found at: {receipt_path}. "
            "Evaluation mode requires a verified receipt manifest."
        )
    with open(receipt_path, "r", encoding="utf-8") as f:
        return json.load(f)


def recommend_movies(
    user_id: int,
    top_n: int = 5,
    mode: str = "evaluation",
    source: str = "csv",
    tables: Optional[Dict[str, pd.DataFrame]] = None,
    receipt_path: Optional[Path] = None,
    skip_manifest_verification: bool = False,
    expected_model_version: Optional[str] = None,
    expected_cutoff_timestamp: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Core inference function generating recommendations for a specific user.
    Binds strictly to evaluation manifest in 'evaluation' mode.
    """
    if top_n <= 0:
        raise ValueError(f"top_n must be positive, got {top_n}")
    if mode not in ("evaluation", "demo"):
        raise ValueError(f"mode must be 'evaluation' or 'demo', got '{mode}'")

    if tables is None:
        tables = load_data(source=source)

    ratings_df = tables["ratings"]
    movies_df = tables["movies"]
    movie_genres_df = tables.get("movie_genres")

    # Map movie metadata for rich output
    movie_titles = dict(zip(movies_df["movie_id"], movies_df["title"]))
    movie_genres: Dict[int, List[str]] = {}
    if movie_genres_df is not None:
        for mid, grp in movie_genres_df.groupby("movie_id"):
            movie_genres[int(mid)] = grp["genre_name"].tolist()

    manifest_metadata: Dict[str, Any] = {}

    # Partition data and bind configuration based on mode
    if mode == "evaluation":
        if not skip_manifest_verification and top_n != 5:
            raise ValueError(
                f"In evaluation mode, recommendation_top_n is strictly frozen to 5 by official protocol, got {top_n}"
            )

        if not skip_manifest_verification:
            manifest_file = receipt_path or DEFAULT_TEST_RECEIPT
            manifest = load_evaluation_manifest(manifest_file)
            if not isinstance(manifest, dict):
                raise ValueError("Official evaluation receipt manifest must be a dictionary object.")

            # 1. Status check: must be OFFICIAL_COMPLETED
            status = manifest.get("status")
            if status != "OFFICIAL_COMPLETED":
                raise ValueError(
                    f"Evaluation receipt manifest status must be 'OFFICIAL_COMPLETED', got '{status}'"
                )

            # 2. Required sections check
            for section in ("training_manifest", "frozen_configuration", "hashes"):
                if section not in manifest or not isinstance(manifest[section], dict):
                    raise ValueError(f"Evaluation receipt manifest missing required section: '{section}'")

            tm = manifest["training_manifest"]
            fc = manifest["frozen_configuration"]
            hashes = manifest["hashes"]

            # 3. Training manifest checks (no default fallbacks)
            for req_tm in ("model_version", "training_cutoff_timestamp", "training_ratings_count"):
                if req_tm not in tm or tm[req_tm] is None:
                    raise ValueError(f"Evaluation receipt manifest missing required field '{req_tm}' in training_manifest")

            model_version = tm["model_version"]
            if model_version != "item_based_cf_k40_eval_v1":
                raise ValueError(
                    f"Evaluation manifest model_version mismatch: expected 'item_based_cf_k40_eval_v1', got '{model_version}'"
                )

            cutoff_timestamp = tm["training_cutoff_timestamp"]
            if cutoff_timestamp != EVALUATION_CUTOFF_TIMESTAMP:
                raise ValueError(
                    f"Evaluation manifest cutoff timestamp mismatch: expected {EVALUATION_CUTOFF_TIMESTAMP}, got {cutoff_timestamp}"
                )

            expected_ratings_count = tm["training_ratings_count"]
            if expected_ratings_count != 850177:
                raise ValueError(
                    f"Evaluation manifest training ratings count mismatch: expected 850177, got {expected_ratings_count}"
                )

            if tm.get("matrix_dtype") != "float32":
                raise ValueError(
                    f"Evaluation manifest matrix_dtype mismatch: expected 'float32', got '{tm.get('matrix_dtype')}'"
                )
            if tm.get("batch_size") != 500:
                raise ValueError(
                    f"Evaluation manifest batch_size mismatch: expected 500, got {tm.get('batch_size')}"
                )
            if tm.get("seed_rating_threshold") != 4:
                raise ValueError(
                    f"Evaluation manifest seed_rating_threshold mismatch: expected 4, got {tm.get('seed_rating_threshold')}"
                )

            # 4. Frozen configuration checks (no default fallbacks)
            for req_fc in ("neighbor_k", "recommendation_top_n", "matrix_dtype", "seed_rating_threshold"):
                if req_fc not in fc or fc[req_fc] is None:
                    raise ValueError(f"Evaluation receipt manifest missing required field '{req_fc}' in frozen_configuration")

            neighbor_k = fc["neighbor_k"]
            if neighbor_k != 40:
                raise ValueError(
                    f"Evaluation manifest frozen neighbor_k mismatch: expected 40, got {neighbor_k}"
                )

            frozen_top_n = fc["recommendation_top_n"]
            if frozen_top_n != 5:
                raise ValueError(
                    f"Evaluation manifest frozen recommendation_top_n mismatch: expected 5, got {frozen_top_n}"
                )

            if fc["matrix_dtype"] != "float32":
                raise ValueError(
                    f"Evaluation manifest frozen matrix_dtype mismatch: expected 'float32', got '{fc['matrix_dtype']}'"
                )

            if fc["seed_rating_threshold"] != 4:
                raise ValueError(
                    f"Evaluation manifest frozen seed_rating_threshold mismatch: expected 4, got {fc['seed_rating_threshold']}"
                )

            # 5. Hashes and canonical table hashes (no defaults)
            if "canonical_table_hashes" not in hashes or not isinstance(hashes["canonical_table_hashes"], dict):
                raise ValueError("Evaluation receipt manifest missing 'canonical_table_hashes' in hashes")

            expected_table_hashes = hashes["canonical_table_hashes"]
            required_canonical_tables = ("users", "movies", "movie_genres", "ratings")
            for tbl_name in required_canonical_tables:
                if tbl_name not in expected_table_hashes or not expected_table_hashes[tbl_name]:
                    raise ValueError(f"Evaluation receipt manifest missing canonical hash for table '{tbl_name}'")

            # 6. Verification of optional expected arguments (if provided by caller)
            if expected_model_version is not None and model_version != expected_model_version:
                raise ValueError(
                    f"Model identity mismatch: expected '{expected_model_version}', "
                    f"manifest defines '{model_version}'."
                )

            if expected_cutoff_timestamp is not None and cutoff_timestamp != expected_cutoff_timestamp:
                raise ValueError(
                    f"Training cutoff timestamp mismatch: expected {expected_cutoff_timestamp}, "
                    f"manifest defines {cutoff_timestamp}."
                )

            # 7. Verification of input data against manifest before fitting
            canonical_hashes, _, _ = verify_and_hash_input_tables(tables)
            for tbl_name in required_canonical_tables:
                actual_hash = canonical_hashes.get(tbl_name)
                expected_hash = expected_table_hashes[tbl_name]
                if actual_hash != expected_hash:
                    raise ValueError(
                        f"Input data verification failed for table '{tbl_name}': "
                        f"expected {expected_hash}, got {actual_hash}. "
                        "Input data does not match the official evaluation manifest."
                    )

            active_ratings = ratings_df[ratings_df["timestamp"] <= cutoff_timestamp].copy()
            if len(active_ratings) != expected_ratings_count:
                raise ValueError(
                    f"Training ratings count mismatch under cutoff {cutoff_timestamp}: "
                    f"expected {expected_ratings_count}, got {len(active_ratings)}."
                )

            # Extract libraries from manifest or official test output
            libraries = tm.get("libraries")
            if not libraries:
                eval_output_file = REPO_ROOT / "results" / "mining" / "cf_test_evaluation.json"
                if eval_output_file.exists():
                    try:
                        with open(eval_output_file, "r", encoding="utf-8") as f_eval:
                            eval_data = json.load(f_eval)
                            libraries = eval_data.get("model_manifest", {}).get("libraries", {})
                    except Exception:
                        pass

            cutoff_note = (
                f"Train+Validation history strictly bounded by official manifest "
                f"(timestamp <= {cutoff_timestamp}, {len(active_ratings):,} ratings)"
            )
            manifest_metadata = {
                "manifest_source": str(manifest_file),
                "run_id": manifest.get("run_id"),
                "status": manifest.get("status"),
                "integrity_verification": "PASSED_CANONICAL_HASHES_MATCH",
                "libraries": libraries or {},
            }
        else:
            # Synthetic / fixture bypass mode
            model_version = "item_based_cf_k40_eval_v1"
            if expected_model_version is not None and model_version != expected_model_version:
                raise ValueError(
                    f"Model identity mismatch: expected '{expected_model_version}', "
                    f"fixture defines '{model_version}'."
                )
            cutoff_timestamp = EVALUATION_CUTOFF_TIMESTAMP
            if expected_cutoff_timestamp is not None and cutoff_timestamp != expected_cutoff_timestamp:
                raise ValueError(
                    f"Training cutoff timestamp mismatch: expected {expected_cutoff_timestamp}, "
                    f"fixture defines {cutoff_timestamp}."
                )
            neighbor_k = 40
            active_ratings = ratings_df[ratings_df["timestamp"] <= cutoff_timestamp].copy()
            cutoff_note = f"Train+Validation history (timestamp <= {cutoff_timestamp}, fixture mode)"
            manifest_metadata = {
                "manifest_source": "SYNTHETIC_FIXTURE_BYPASS",
                "integrity_verification": "BYPASSED_FOR_TESTS",
                "libraries": {},
            }
    else:
        # demo mode: full dataset history
        model_version = "item_based_cf_k40_DEMO_full_history_v1"
        neighbor_k = 40
        active_ratings = ratings_df.copy()
        cutoff_note = "Full dataset history (DEMO mode: interactive exploration only; offline metrics forbidden)"
        manifest_metadata = {
            "demo_manifest": "DEMO_INTERACTIVE_V1",
            "total_ratings": len(active_ratings),
            "offline_metrics_disclaimer": "Demo mode uses full interaction history and must NEVER be used to evaluate or publish offline metrics.",
        }

    # Check user existence in active data
    all_known_users = set(ratings_df["user_id"].unique())
    user_in_dataset = user_id in all_known_users
    user_ratings = active_ratings[active_ratings["user_id"] == user_id]

    user_history = set(user_ratings["movie_id"].unique())
    user_seeds_df = user_ratings[user_ratings["rating"] >= 4].sort_values(by="rating", ascending=False)
    user_seeds = set(user_seeds_df["movie_id"].unique())

    # Build popularity model from active ratings for fallback & non-existent user
    pop_df = fit_popularity_model(active_ratings)
    popularity_ranking = pop_df["movie_id"].tolist()
    popularity_counts = dict(zip(pop_df["movie_id"], pop_df["rating_count"]))

    # Prepare seeds display list
    seeds_display: List[Dict[str, Any]] = []
    for _, row in user_seeds_df.iterrows():
        mid = int(row["movie_id"])
        seeds_display.append({
            "movie_id": mid,
            "title": movie_titles.get(mid, f"Movie {mid}"),
            "rating": int(row["rating"]),
            "genres": movie_genres.get(mid, []),
        })

    # Edge Case: User not in training history or has zero valid seeds
    if not user_in_dataset:
        user_status = "NON_EXISTENT_USER"
        status_message = (
            f"User {user_id} was not found in the dataset. "
            "Providing non-personalized recommendations based on training popularity ranking."
        )
        recs = recommend_for_user_popularity(
            user_train_history=set(),
            popularity_ranking=popularity_ranking,
            top_k=top_n,
        )
        rec_details = [
            {
                "movie_id": int(mid),
                "score": None,
                "score_type": "popularity_fallback",
            }
            for mid in recs
        ]
        used_fallback = True

    elif len(user_seeds) == 0:
        user_status = "ZERO_SEEDS_USER"
        status_message = (
            f"User {user_id} exists with {len(user_history)} ratings, but has 0 positive seeds (rating >= 4). "
            "Falling back to user's personalized popularity ranking (excluding history)."
        )
        recs = recommend_for_user_popularity(
            user_train_history=user_history,
            popularity_ranking=popularity_ranking,
            top_k=top_n,
        )
        rec_details = [
            {
                "movie_id": int(mid),
                "score": None,
                "score_type": "popularity_fallback",
            }
            for mid in recs
        ]
        used_fallback = True

    else:
        user_status = "ACTIVE_CF_USER"
        status_message = f"User {user_id} has {len(user_seeds)} valid seeds (rating >= 4) from {len(user_history)} rated movies."

        # Fit CF model
        R_sparse, movie_to_idx, idx_to_movie, user_to_idx, idx_to_user = build_sparse_ratings_matrix(active_ratings)
        top_neighbors_map = compute_item_cosine_similarities_top_k(
            R_sparse, idx_to_movie, max_k=40, batch_size=500
        )

        recs, rec_details, used_fallback = recommend_for_user_cf(
            user_id=user_id,
            user_train_history=user_history,
            user_train_seeds=user_seeds,
            top_neighbors_map=top_neighbors_map,
            k=40,
            popularity_ranking=popularity_ranking,
            popularity_counts=popularity_counts,
            top_n=top_n,
        )

    # Format final recommendation list with full metadata
    formatted_recs: List[Dict[str, Any]] = []
    for rank_idx, item in enumerate(rec_details, start=1):
        mid = item["movie_id"]
        formatted_recs.append({
            "rank": rank_idx,
            "movie_id": mid,
            "title": movie_titles.get(mid, f"Movie {mid}"),
            "genres": movie_genres.get(mid, []),
            "score_type": item["score_type"],
            "score": item["score"],
            "score_display": f"{item['score']:.4f}" if item["score"] is not None else "N/A (Popularity Fallback)",
        })

    result = {
        "model_version": model_version,
        "mode": mode,
        "cutoff_note": cutoff_note,
        "user_id": user_id,
        "user_status": user_status,
        "status_message": status_message,
        "history_count": len(user_history),
        "seeds_count": len(user_seeds),
        "seeds": seeds_display,
        "top_n": top_n,
        "used_fallback": used_fallback,
        "recommendations": formatted_recs,
        "model_construction": {
            "reconstruction_mode": "runtime_in_memory_fit",
            "model_binary_persistence": "none_git_excluded",
            "description": (
                "CLI dynamically constructs in-memory sparse ratings matrix and item similarity matrix "
                "from verified training ratings at runtime. Model binary is not persisted or loaded from disk, "
                "strictly complying with repository storage constraints."
            ),
        },
        "model_identity_mapping": {
            "evaluation_receipt_model": "item_based_cf_k40_eval_v1",
            "cli_runtime_model": model_version,
            "status": "UNIFIED_IDENTITY_MATCH" if model_version == "item_based_cf_k40_eval_v1" else "MAPPED_IDENTITY",
            "explanation": (
                "CLI strictly adopts the model identity defined in the official test evaluation receipt manifest "
                "('item_based_cf_k40_eval_v1'). No modifications have been made to historical test run metadata."
            ),
        },
        "manifest_metadata": manifest_metadata,
        "technical_notes": {
            "score_interpretation": (
                "CF score is a similarity-weighted ranking score (sum of cosine similarities from seed movies), "
                "NOT a predicted star rating (1-5 stars)."
            ),
            "fallback_handling": (
                "Popularity fallback items are distinctly labeled (score_type='popularity_fallback') and their "
                "rating counts are NEVER mixed with similarity float scores."
            ),
        },
    }
    return result


def print_recommendation_cli(result: Dict[str, Any]) -> None:
    """Pretty prints recommendation results to stdout."""
    mode_label = "OFFICIAL EVALUATION MODEL" if result["mode"] == "evaluation" else "*** DEMO MODE (FULL HISTORY) ***"
    print("=" * 80)
    print(f" MOVIELENS 1M - ITEM-BASED COLLABORATIVE FILTERING RECOMMENDER ({mode_label})")
    print("=" * 80)
    print(f"Model Version:   {result['model_version']}")
    print(f"Training Scope:  {result['cutoff_note']}")
    print(f"Target User ID:  {result['user_id']} ({result['user_status']})")
    print(f"User Summary:    {result['status_message']}")

    # Print Seeds
    seeds = result["seeds"]
    if seeds:
        print(f"\n--- User Seeds (Ratings >= 4, showing up to 5 of {len(seeds)} seeds) ---")
        for s in seeds[:5]:
            genres_str = ", ".join(s["genres"]) if s["genres"] else "Unknown"
            print(f"  * [Rating {s['rating']}/5] ID {s['movie_id']:>4}: {s['title']} ({genres_str})")
        if len(seeds) > 5:
            print(f"    ... and {len(seeds) - 5} additional positive seed movies.")

    # Print Recommendations
    print(f"\n--- Top-{result['top_n']} Recommended Movies ---")
    header = f"{'Rank':<5} {'ID':<6} {'Score Type':<21} {'Score':<10} {'Title (Genres)'}"
    print(header)
    print("-" * 80)
    for r in result["recommendations"]:
        genres_str = f" ({', '.join(r['genres'])})" if r["genres"] else ""
        title_full = f"{r['title']}{genres_str}"
        print(f"{r['rank']:<5} {r['movie_id']:<6} {r['score_type']:<21} {r['score_display']:<10} {title_full}")

    print("-" * 80)
    print(f"Technical Note:  {result['technical_notes']['score_interpretation']}")
    print(f"Fallback Note:   {result['technical_notes']['fallback_handling']}")
    print("=" * 80)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="MovieLens 1M Q2 Item-based Collaborative Filtering Recommender CLI (Step 10B)"
    )
    parser.add_argument("--user-id", type=int, required=True, help="User ID to generate recommendations for")
    parser.add_argument("--top-n", type=int, default=5, help="Number of recommendations to return (default: 5)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Input data source (default: csv)")
    parser.add_argument(
        "--mode",
        choices=["evaluation", "demo"],
        default="evaluation",
        help="Inference mode: 'evaluation' (frozen model <= t2) or 'demo' (full history). Default: evaluation",
    )
    parser.add_argument("--receipt", type=Path, default=DEFAULT_TEST_RECEIPT, help="Path to evaluation receipt manifest")
    parser.add_argument(
        "--model-version",
        type=str,
        default=None,
        help="Expected model version identity to verify against manifest (default: item_based_cf_k40_eval_v1)",
    )
    parser.add_argument("--output-json", type=Path, default=None, help="Optional path to export JSON output")
    args = parser.parse_args(argv)

    result = recommend_movies(
        user_id=args.user_id,
        top_n=args.top_n,
        mode=args.mode,
        source=args.source,
        receipt_path=args.receipt,
        expected_model_version=args.model_version,
    )

    print_recommendation_cli(result)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nJSON output saved to: {args.output_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
