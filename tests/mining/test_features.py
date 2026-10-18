"""
Unit tests for Q1 User Genre Preference Feature Engineering (Step 8A).
According to Data Contract v2 and project specifications.

Validates:
- Mathematical accuracy on a hand-calculated multi-genre fixture.
- Proper handling of users with insufficient evidence (0 positive ratings).
- Zero-division prevention and excluding empty vectors from training data.
- Extraction from canonical MovieLens 1M dataset:
  * 6,038 assigned users with normalized 18-genre vectors.
  * 2 insufficient evidence users with status='insufficient_evidence'.
  * Strict sum to 1.0 within 1e-8 tolerance.
  * Correct alphabetical order (A-Z) of 18 genres.
  * Absolute absence of demographic attributes in feature vectors.
- Reproducibility between raw and CSV sources.
"""

import importlib.util
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_IO_PATH = REPO_ROOT / "mining" / "data_io.py"
if "mining.data_io" not in sys.modules:
    spec_d = importlib.util.spec_from_file_location("mining.data_io", DATA_IO_PATH)
    data_io_mod = importlib.util.module_from_spec(spec_d)
    sys.modules["mining.data_io"] = data_io_mod
    spec_d.loader.exec_module(data_io_mod)
else:
    data_io_mod = sys.modules["mining.data_io"]

FEATURES_PATH = REPO_ROOT / "mining" / "features.py"
spec_f = importlib.util.spec_from_file_location("mining.features", FEATURES_PATH)
features_mod = importlib.util.module_from_spec(spec_f)
sys.modules["mining.features"] = features_mod
spec_f.loader.exec_module(features_mod)

GENRE_COLUMNS = features_mod.GENRE_COLUMNS
SUM_TOLERANCE = features_mod.SUM_TOLERANCE
extract_user_genre_preference_features = features_mod.extract_user_genre_preference_features
load_data = data_io_mod.load_data


# ---------------------------------------------------------------------------
# 1. HAND-CALCULATED FIXTURE TEST
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_toy_fixture():
    """
    Hand-calculated synthetic dataset:
    - 3 users:
      * User 1: Has positive ratings on multi-genre movies (M1: Animation|Children's|Comedy, M2: Adventure|Children's|Fantasy)
                and a negative rating on M3. Total positive genre associations = 6.
      * User 2: Has positive rating on single multi-genre movie (M3: Action|Crime|Thriller).
                Total positive genre associations = 3.
      * User 3: Only has ratings < 4 (ratings 1, 2, 3). Zero positive ratings.
                Status must be 'insufficient_evidence'.
    """
    users = pd.DataFrame({
        "user_id": [1, 2, 3],
        "gender": ["M", "F", "M"],
        "age_group": ["25-34", "18-24", "35-44"],
        "occupation": [4, 10, 7],
    })

    movies = pd.DataFrame({
        "movie_id": [101, 102, 103],
        "title": ["Toy Movie (1995)", "Adventure Movie (1995)", "Action Movie (1995)"],
        "release_year": [1995, 1995, 1995],
    })

    movie_genres = pd.DataFrame({
        "movie_id": [
            101, 101, 101,  # M1: Animation, Children's, Comedy
            102, 102, 102,  # M2: Adventure, Children's, Fantasy
            103, 103, 103,  # M3: Action, Crime, Thriller
        ],
        "genre_name": [
            "Animation", "Children's", "Comedy",
            "Adventure", "Children's", "Fantasy",
            "Action", "Crime", "Thriller",
        ],
    })

    ratings = pd.DataFrame({
        "user_id": [1, 1, 1, 2, 3, 3, 3],
        "movie_id": [101, 102, 103, 103, 101, 102, 103],
        "rating": [
            5,  # U1, M1 -> positive: Animation(1), Children's(1), Comedy(1)
            4,  # U1, M2 -> positive: Adventure(1), Children's(1), Fantasy(1)
            2,  # U1, M3 -> negative: IGNORED
            4,  # U2, M3 -> positive: Action(1), Crime(1), Thriller(1)
            1,  # U3, M1 -> negative: IGNORED
            2,  # U3, M2 -> negative: IGNORED
            3,  # U3, M3 -> negative: IGNORED
        ],
        "timestamp": [1000, 1001, 1002, 1003, 1004, 1005, 1006],
        "rated_at": [
            "2000-01-01T00:00:00Z", "2000-01-01T00:00:01Z", "2000-01-01T00:00:02Z",
            "2000-01-01T00:00:03Z", "2000-01-01T00:00:04Z", "2000-01-01T00:00:05Z",
            "2000-01-01T00:00:06Z",
        ],
    })

    return {
        "users": users,
        "movies": movies,
        "movie_genres": movie_genres,
        "ratings": ratings,
    }


def test_hand_calculated_synthetic_fixture(synthetic_toy_fixture):
    """Verify exact mathematical output against hand calculations."""
    feat_matrix, status_df, summary = extract_user_genre_preference_features(synthetic_toy_fixture)

    # 1. Shape and users count
    assert len(feat_matrix) == 2, "Only Users 1 and 2 should be in feature matrix"
    assert feat_matrix.shape == (2, 18), "Feature matrix must have exactly 18 genres"
    assert list(feat_matrix.columns) == GENRE_COLUMNS, "Columns must be exactly 18 genres in A-Z order"

    # 2. Check User 1 hand-calculated vector:
    # Total positive genre associations = 6:
    # Adventure: 1/6, Animation: 1/6, Children's: 2/6, Comedy: 1/6, Fantasy: 1/6. Others: 0.0.
    u1_vec = feat_matrix.loc[1]
    assert np.isclose(u1_vec["Adventure"], 1.0 / 6.0)
    assert np.isclose(u1_vec["Animation"], 1.0 / 6.0)
    assert np.isclose(u1_vec["Children's"], 2.0 / 6.0)
    assert np.isclose(u1_vec["Comedy"], 1.0 / 6.0)
    assert np.isclose(u1_vec["Fantasy"], 1.0 / 6.0)
    for g in GENRE_COLUMNS:
        if g not in ["Adventure", "Animation", "Children's", "Comedy", "Fantasy"]:
            assert u1_vec[g] == 0.0
    assert np.isclose(u1_vec.sum(), 1.0, atol=SUM_TOLERANCE)

    # 3. Check User 2 hand-calculated vector:
    # Total positive genre associations = 3:
    # Action: 1/3, Crime: 1/3, Thriller: 1/3. Others: 0.0.
    u2_vec = feat_matrix.loc[2]
    assert np.isclose(u2_vec["Action"], 1.0 / 3.0)
    assert np.isclose(u2_vec["Crime"], 1.0 / 3.0)
    assert np.isclose(u2_vec["Thriller"], 1.0 / 3.0)
    for g in GENRE_COLUMNS:
        if g not in ["Action", "Crime", "Thriller"]:
            assert u2_vec[g] == 0.0
    assert np.isclose(u2_vec.sum(), 1.0, atol=SUM_TOLERANCE)

    # 4. Check User 3 (insufficient evidence):
    assert 3 not in feat_matrix.index, "User 3 must not be in feature matrix"
    u3_status = status_df[status_df["user_id"] == 3].iloc[0]
    assert u3_status["status"] == "insufficient_evidence"
    assert u3_status["positive_ratings_count"] == 0
    assert u3_status["genre_association_count"] == 0


# ---------------------------------------------------------------------------
# 2. FULL MOVIELENS 1M DATASET TESTS
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def canonical_tables():
    return load_data("csv")


def test_full_dataset_feature_matrix_properties(canonical_tables):
    """
    Verify full dataset feature matrix satisfies all specifications of Data Contract v2:
    - 6,038 assigned users
    - 2 insufficient evidence users
    - Matrix dimensions: (6038, 18)
    - Row sums equal 1.0 within 1e-8
    - All values in [0, 1] and finite
    - Demographics strictly absent
    """
    feat_matrix, status_df, summary = extract_user_genre_preference_features(canonical_tables)

    # 1. Dimensionality, index, and absence of cluster_id/model_version
    assert feat_matrix.shape == (6038, 18), "Feature matrix shape must be (6038, 18)"
    assert list(feat_matrix.columns) == GENRE_COLUMNS
    assert feat_matrix.index.nunique() == 6038
    assert feat_matrix.index.name == "user_id"
    assert feat_matrix.index.is_monotonic_increasing, "User IDs must be strictly sorted to avoid key mismatch"
    assert "cluster_id" not in feat_matrix.columns, "8A feature matrix must not contain cluster_id"
    assert "model_version" not in feat_matrix.columns

    # 2. Verify demographics are not present in features
    for demo_col in ["gender", "age_group", "occupation", "zip_code"]:
        assert demo_col not in feat_matrix.columns

    # 3. Value ranges and finiteness
    assert (feat_matrix.values >= 0.0).all(), "Feature values must be >= 0"
    assert (feat_matrix.values <= 1.0).all(), "Feature values must be <= 1"
    assert np.isfinite(feat_matrix.values).all(), "Feature values must be finite"

    # 4. Sum to 1.0 within tolerance
    row_sums = feat_matrix.sum(axis=1)
    max_dev = (row_sums - 1.0).abs().max()
    assert max_dev <= SUM_TOLERANCE, f"Row sum deviation {max_dev} exceeds tolerance {SUM_TOLERANCE}"

    # 5. User statuses
    assert len(status_df) == 6040, "Status DataFrame must include all 6,040 users"
    assigned_count = (status_df["status"] == "assigned").sum()
    insufficient_count = (status_df["status"] == "insufficient_evidence").sum()
    assert assigned_count == 6038, "Expected exactly 6,038 assigned users"
    assert insufficient_count == 2, "Expected exactly 2 insufficient evidence users"

    # 6. Verify summary metadata
    assert summary["assigned_users_count"] == 6038
    assert summary["insufficient_evidence_users_count"] == 2
    assert summary["total_positive_ratings"] == 575281
    assert summary["total_genre_associations"] == 1206999


def test_zero_division_guard_edge_case():
    """Verify that a user with 0 ratings or only low ratings never causes ZeroDivisionError."""
    empty_ratings = pd.DataFrame(columns=["user_id", "movie_id", "rating", "timestamp", "rated_at"])
    users = pd.DataFrame({
        "user_id": [999], "gender": ["M"], "age_group": ["25-34"], "occupation": [1]
    })
    movies = pd.DataFrame({
        "movie_id": [1], "title": ["M (1995)"], "release_year": [1995]
    })
    movie_genres = pd.DataFrame({
        "movie_id": [1], "genre_name": ["Drama"]
    })

    tables = {
        "users": users, "movies": movies, "movie_genres": movie_genres, "ratings": empty_ratings
    }

    feat_matrix, status_df, summary = extract_user_genre_preference_features(tables)
    assert len(feat_matrix) == 0, "No assigned users when no positive ratings exist"
    assert len(status_df) == 1
    assert status_df.iloc[0]["status"] == "insufficient_evidence"
    assert summary["assigned_users_count"] == 0
    assert summary["insufficient_evidence_users_count"] == 1


def test_raw_csv_feature_extraction_equivalence():
    """Verify feature matrix extracted from raw vs csv is byte-for-byte identical."""
    raw_tables = load_data("raw")
    csv_tables = load_data("csv")

    feat_raw, status_raw, _ = extract_user_genre_preference_features(raw_tables)
    feat_csv, status_csv, _ = extract_user_genre_preference_features(csv_tables)

    # Values must match with high precision
    np.testing.assert_allclose(feat_raw.values, feat_csv.values, atol=1e-14)
    pd.testing.assert_frame_equal(feat_raw, feat_csv)
    pd.testing.assert_frame_equal(status_raw, status_csv)
