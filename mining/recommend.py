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
from mining.data_io import load_data

EVALUATION_CUTOFF_TIMESTAMP = 976422051  # t2


def recommend_movies(
    user_id: int,
    top_n: int = 5,
    mode: str = "evaluation",
    source: str = "csv",
    tables: Optional[Dict[str, pd.DataFrame]] = None,
) -> Dict[str, Any]:
    """
    Core inference function generating recommendations for a specific user.
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

    # Partition data based on mode
    if mode == "evaluation":
        model_version = "item_based_cf_k40_eval_frozen_v1"
        active_ratings = ratings_df[ratings_df["timestamp"] <= EVALUATION_CUTOFF_TIMESTAMP].copy()
        cutoff_note = f"Train+Validation history (timestamp <= {EVALUATION_CUTOFF_TIMESTAMP}, 2000-12-10 04:20:51 UTC)"
    else:
        model_version = "item_based_cf_k40_DEMO_full_history_v1"
        active_ratings = ratings_df.copy()
        cutoff_note = "Full dataset history (DEMO mode: not for offline evaluation metrics)"

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


def main():
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
    parser.add_argument("--output-json", type=Path, default=None, help="Optional path to export JSON output")
    args = parser.parse_args()

    result = recommend_movies(
        user_id=args.user_id,
        top_n=args.top_n,
        mode=args.mode,
        source=args.source,
    )

    print_recommendation_cli(result)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nJSON output saved to: {args.output_json}")


if __name__ == "__main__":
    main()
