"""
Evaluation Protocol and Metric Computation Module for MovieLens 1M Q2 Recommendation (Step 9A).
According to Data Contract v2, Project Specifications, and Coordinator Instructions.

Implements:
- Cohort eligibility determination (>=5 train ratings and >=1 rating >=4 in eval).
- Candidate universe construction (training catalog minus user's training history; NO negative sampling).
- Tie-breaking ranking rules: score DESC -> train popularity DESC -> movie_id ASC.
- Top-5 recommendation metrics:
    * Precision@5: hits / 5 (fixed denominator 5 even if <5 candidates returned).
    * Recall@5:    hits / |R_eval| (denominator includes novel/cold-start positive movies in eval).
    * Macro aggregation: unweighted arithmetic mean over all eligible cohort users.
- Explicit handling of edge cases (novel items, ties, <5 candidates, fallback reporting).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd


def get_eligible_eval_cohort(
    train_history_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    min_train_ratings: int = 5,
    min_pos_rating: int = 4,
) -> Tuple[Set[int], Dict[str, Any]]:
    """
    Identifies the eligible cohort of users for recommendation evaluation.
    
    Criteria (both must be satisfied):
    1. User has >= min_train_ratings (default 5) in the training history.
    2. User has >= 1 rating >= min_pos_rating (default 4) in the evaluation period.
    
    Returns:
    - Set of eligible user IDs.
    - Diagnostic dictionary breaking down exclusions and counts.
    """
    # 1. Training history counts per user
    train_counts = train_history_df.groupby("user_id").size()
    users_with_min_train = set(train_counts[train_counts >= min_train_ratings].index)

    # 2. Evaluation period positive ratings per user
    eval_active_users = set(eval_df["user_id"].unique())
    pos_mask = eval_df["rating"] >= min_pos_rating
    eval_pos_users = set(eval_df[pos_mask]["user_id"].unique())

    # 3. Eligible cohort intersection
    eligible_users = set(sorted(users_with_min_train.intersection(eval_pos_users)))

    # 4. Exclusion breakdowns
    excluded_insufficient_train = eval_active_users - users_with_min_train
    excluded_no_positives = (eval_active_users.intersection(users_with_min_train)) - eval_pos_users

    diagnostics = {
        "total_active_eval_users": len(eval_active_users),
        "eligible_cohort_size": len(eligible_users),
        "excluded_insufficient_train_ratings": len(excluded_insufficient_train),
        "excluded_no_positives_in_eval": len(excluded_no_positives),
        "min_train_ratings_required": min_train_ratings,
        "min_pos_rating_threshold": min_pos_rating,
    }
    return eligible_users, diagnostics


def get_user_candidate_universe(
    train_history_df: pd.DataFrame,
    user_id: int,
) -> Set[int]:
    """
    Constructs the un-sampled candidate movie universe for a specific user.
    
    Candidate universe definition:
        C(u) = { m in M_train | (u, m) not in R_train }
    where:
    - M_train is the set of all unique movies appearing in training history.
    - (u, m) in R_train represents all movies already rated by user u in training history.
    
    Strict constraints:
    - NO negative sampling: ranking is evaluated against all unrated training movies.
    - Novel movies introduced only during the evaluation period cannot be recommended.
    """
    train_catalog = set(train_history_df["movie_id"].unique())
    user_train_movies = set(train_history_df[train_history_df["user_id"] == user_id]["movie_id"].unique())
    candidate_universe = train_catalog - user_train_movies
    return candidate_universe


def rank_candidates(
    scores: Dict[int, float],
    train_popularity: Dict[int, int],
    top_k: int = 5,
) -> List[int]:
    """
    Ranks candidate movies using deterministic score and tie-breaking rules:
    1. Score descending (-score)
    2. Training history rating count / popularity descending (-train_popularity)
    3. movie_id ascending (+movie_id)
    
    Returns the ordered list of Top-K candidate movie IDs.
    """
    sorted_candidates = sorted(
        scores.keys(),
        key=lambda m: (-scores[m], -train_popularity.get(m, 0), int(m))
    )
    return sorted_candidates[:top_k]


def compute_user_metrics_at_k(
    recommended_movies: List[int],
    user_eval_positives: Set[int],
    k: int = 5,
) -> Dict[str, float]:
    """
    Computes Precision@K and Recall@K for an individual user.
    
    Definitions:
    - Top-K: First K items from recommended_movies (default K=5).
    - hits: Number of recommended Top-K items in user_eval_positives.
    - Precision@K = hits / K
        * Fixed denominator K=5 even if fewer than K candidates are returned.
    - Recall@K = hits / |user_eval_positives|
        * Denominator is the user's TOTAL positive items (rating >= 4) in the evaluation period.
        * Includes novel/cold-start items not in the training catalog.
    
    Raises ValueError if user_eval_positives is empty (eligible users must have >= 1 positive).
    """
    if len(user_eval_positives) == 0:
        raise ValueError("user_eval_positives cannot be empty for an eligible evaluation user")

    top_k_items = recommended_movies[:k]
    hits = len(set(top_k_items).intersection(user_eval_positives))

    precision = hits / float(k)
    recall = hits / float(len(user_eval_positives))

    return {
        "precision": float(precision),
        "recall": float(recall),
        "hits": int(hits),
        "k": int(k),
        "num_positives": int(len(user_eval_positives)),
        "num_recommended": int(len(top_k_items)),
    }


def compute_macro_metrics(
    user_metrics: List[Dict[str, float]],
) -> Dict[str, float]:
    """
    Computes macro-averaged Precision@K and Recall@K across all eligible users.
    
    Macro-averaging weights each user equally regardless of their activity level:
        Macro-Precision@K = (1 / |U|) * sum_{u} Precision@K(u)
        Macro-Recall@K    = (1 / |U|) * sum_{u} Recall@K(u)
    """
    if len(user_metrics) == 0:
        return {
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "total_users": 0,
        }

    precisions = [m["precision"] for m in user_metrics]
    recalls = [m["recall"] for m in user_metrics]

    return {
        "macro_precision": float(np.mean(precisions)),
        "macro_recall": float(np.mean(recalls)),
        "total_users": int(len(user_metrics)),
    }
