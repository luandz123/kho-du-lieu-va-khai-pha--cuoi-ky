"""
Unit tests for mining/data_io.py adapter according to Data Contract v2.

Validates:
- Logical schemas, column order, data types
- Source ID preservation and uniqueness
- UTC ISO 8601 formatting for rated_at
- Raw <-> CSV byte-level equivalence and SHA-256 manifest matching
- Multi-genre movies do not cause row multiplication in ratings
- DW view query interface and graceful connection error handling
"""

import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

import pandas as pd
import pytest

# Robustly load mining/data_io.py from repository root to prevent shadowing with tests/mining package
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_IO_PATH = REPO_ROOT / "mining" / "data_io.py"
spec = importlib.util.spec_from_file_location("mining.data_io", DATA_IO_PATH)
data_io = importlib.util.module_from_spec(spec)
sys.modules["mining.data_io"] = data_io
spec.loader.exec_module(data_io)

load_data = data_io.load_data
load_csv_data = data_io.load_csv_data
load_raw_data = data_io.load_raw_data
load_dw_data = data_io.load_dw_data
verify_raw_csv_equivalence = data_io.verify_raw_csv_equivalence
compute_canonical_hash = data_io.compute_canonical_hash
TABLE_SCHEMAS = data_io.TABLE_SCHEMAS
DWConnectionError = data_io.DWConnectionError
CANONICAL_MANIFEST_PATH = data_io.CANONICAL_MANIFEST_PATH



@pytest.fixture(scope="module")
def canonical_manifest():
    assert CANONICAL_MANIFEST_PATH.exists(), f"Missing {CANONICAL_MANIFEST_PATH}"
    with open(CANONICAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def csv_tables():
    return load_csv_data()


@pytest.fixture(scope="module")
def raw_tables():
    return load_raw_data()


def test_table_schemas_and_columns(csv_tables, raw_tables):
    """Verify that both raw and csv loaders yield identical schemas and column order."""
    for tbl, expected_cols in TABLE_SCHEMAS.items():
        assert tbl in csv_tables, f"Missing {tbl} in csv_tables"
        assert tbl in raw_tables, f"Missing {tbl} in raw_tables"

        csv_df = csv_tables[tbl]
        raw_df = raw_tables[tbl]

        assert list(csv_df.columns) == expected_cols, f"CSV {tbl} column mismatch"
        assert list(raw_df.columns) == expected_cols, f"RAW {tbl} column mismatch"
        assert len(csv_df) == len(raw_df), f"Row count mismatch in {tbl}"


def test_raw_csv_byte_equivalence(canonical_manifest):
    """Verify raw and csv sources produce identical serialized SHA-256 byte hashes."""
    report = verify_raw_csv_equivalence()
    assert report["overall_equivalence"] is True

    for tbl in ["users", "movies", "movie_genres", "ratings"]:
        info = report[tbl]
        assert info["equivalent"] is True
        assert info["hashes_match"] is True
        assert info["raw_hash"] == canonical_manifest["canonical_hashes"][tbl]
        assert info["csv_hash"] == canonical_manifest["canonical_hashes"][tbl]


def test_id_uniqueness_and_foreign_keys(csv_tables):
    """Verify primary keys and foreign key relationships."""
    users_df = csv_tables["users"]
    movies_df = csv_tables["movies"]
    genres_df = csv_tables["movie_genres"]
    ratings_df = csv_tables["ratings"]

    # Users PK uniqueness
    assert users_df["user_id"].is_unique
    assert len(users_df) == 6040

    # Movies PK uniqueness
    assert movies_df["movie_id"].is_unique
    assert len(movies_df) == 3883

    # Genres (movie_id, genre_name) uniqueness
    mg_pairs = set(zip(genres_df["movie_id"], genres_df["genre_name"]))
    assert len(mg_pairs) == len(genres_df)
    assert len(genres_df) == 6408

    # Foreign key: movie_genres.movie_id in movies.movie_id
    movie_id_set = set(movies_df["movie_id"])
    for mid in genres_df["movie_id"]:
        assert mid in movie_id_set

    # Ratings business key (user_id, movie_id) uniqueness
    rating_pairs = set(zip(ratings_df["user_id"], ratings_df["movie_id"]))
    assert len(rating_pairs) == len(ratings_df)
    assert len(ratings_df) == 1000209


def test_rated_at_utc_formatting(csv_tables):
    """Verify rated_at is ISO 8601 UTC ending with 'Z' and matches timestamp."""
    ratings_df = csv_tables["ratings"]
    sample = ratings_df.head(100)

    for _, row in sample.iterrows():
        rated_at = row["rated_at"]
        ts = row["timestamp"]
        assert rated_at.endswith("Z")
        # Check ISO parse
        dt = pd.to_datetime(rated_at)
        assert dt.timestamp() == ts


def test_multi_genre_movies_do_not_multiply_ratings(csv_tables):
    """
    Ensure movies with multiple genres have exactly 1 record per user rating.
    Ratings must NEVER be multiplied by genre count.
    """
    movies_df = csv_tables["movies"]
    genres_df = csv_tables["movie_genres"]
    ratings_df = csv_tables["ratings"]

    # Identify multi-genre movies
    genre_counts = genres_df.groupby("movie_id").size()
    multi_genre_ids = genre_counts[genre_counts > 1].index.tolist()
    assert len(multi_genre_ids) == 1858  # 1,858 movies have >1 genres in MovieLens 1M

    # Pick Toy Story (movie_id = 1, genres = Animation|Children's|Comedy -> 3 genres)
    toy_story_genres = genres_df[genres_df["movie_id"] == 1]
    assert len(toy_story_genres) == 3

    toy_story_ratings = ratings_df[ratings_df["movie_id"] == 1]
    assert len(toy_story_ratings) == 2077  # Exactly 2,077 ratings, NOT 3 * 2077 = 6231!

    # Check across 20 multi-genre movies: count of ratings must equal unique user_ids
    sample_multi_mids = multi_genre_ids[:20]
    for mid in sample_multi_mids:
        m_ratings = ratings_df[ratings_df["movie_id"] == mid]
        assert len(m_ratings) == m_ratings["user_id"].nunique(), (
            f"Movie {mid} has duplicate user ratings, indicating genre multiplication!"
        )


def test_dw_error_handling_when_offline():
    """Verify that load_data(source='dw') raises DWConnectionError gracefully when DW is offline."""
    with pytest.raises(DWConnectionError) as exc_info:
        load_data(source="dw")
    assert "DW connection" in str(exc_info.value) or "DW views" in str(exc_info.value)
    # Ensure no secrets or passwords are leaked in the error message
    assert "password" not in str(exc_info.value).lower()


def test_dw_mock_interface_with_connection():
    """
    Verify DW query interface using an in-memory SQLite database simulating DW views dw.v_ml_*.
    Ensures that when views exist, load_dw_data queries all 4 tables correctly.
    """
    # Create SQLite in-memory connection and attach mock views
    conn = sqlite3.connect(":memory:")
    conn.execute("ATTACH DATABASE ':memory:' AS dw")
    conn.execute("""
        CREATE TABLE dw.v_ml_users (
            user_id INT, gender TEXT, age_group TEXT, occupation INT
        )
    """)
    conn.execute("""
        CREATE TABLE dw.v_ml_movies (
            movie_id INT, title TEXT, release_year INT
        )
    """)
    conn.execute("""
        CREATE TABLE dw.v_ml_movie_genres (
            movie_id INT, genre_name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE dw.v_ml_ratings (
            user_id INT, movie_id INT, rating INT, timestamp BIGINT, rated_at TEXT
        )
    """)

    # Insert mock test data
    conn.execute("INSERT INTO dw.v_ml_users VALUES (1, 'F', 'Under 18', 10)")
    conn.execute("INSERT INTO dw.v_ml_movies VALUES (1, 'Toy Story (1995)', 1995)")
    conn.execute("INSERT INTO dw.v_ml_movie_genres VALUES (1, 'Animation'), (1, 'Comedy')")
    conn.execute("INSERT INTO dw.v_ml_ratings VALUES (1, 1, 5, 956703932, '2000-04-25T23:05:32Z')")
    conn.commit()

    # Query using load_dw_data with the mock connection
    dw_tables = load_dw_data(connection_or_engine=conn)

    assert "users" in dw_tables
    assert "movies" in dw_tables
    assert "movie_genres" in dw_tables
    assert "ratings" in dw_tables

    assert len(dw_tables["users"]) == 1
    assert len(dw_tables["movies"]) == 1
    assert len(dw_tables["movie_genres"]) == 2
    assert len(dw_tables["ratings"]) == 1

    # Verify column schemas
    for tbl, cols in TABLE_SCHEMAS.items():
        assert list(dw_tables[tbl].columns) == cols

    conn.close()

