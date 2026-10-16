"""
Comprehensive unit tests for Canonical Data Tables according to Data Contract v2.
Validates:
- Row counts, schemas, and columns
- Key uniqueness and integrity
- Foreign key validity
- Age group labels
- Sorting rules
- Rated_at UTC ISO 8601 formatting
- SHA-256 byte hashes matching results/eda/canonical_manifest.json
"""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import pytest

MANIFEST_PATH = Path("results/eda/canonical_manifest.json")
PROCESSED_DIR = Path("data/processed")

VALID_AGE_GROUPS = {
    "Under 18", "18-24", "25-34", "35-44", "45-49", "50-55", "56+"
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_PATH.exists(), f"Missing {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_canonical_manifest_structure(manifest):
    assert manifest.get("contract_version") == 2
    assert "canonical_hashes" in manifest
    assert "row_counts" in manifest
    assert "schemas" in manifest
    assert "source_code_sets" in manifest
    assert "provenance" in manifest

    for tbl in ["users", "movies", "movie_genres", "ratings"]:
        assert tbl in manifest["canonical_hashes"]
        assert tbl in manifest["row_counts"]
        assert tbl in manifest["schemas"]

    # Verify source code sets
    scs = manifest["source_code_sets"]
    assert scs["gender"] == ["F", "M"]
    assert len(scs["age_groups"]) == 7
    assert len(scs["occupations"]) == 21
    assert len(scs["genres"]) == 18
    assert scs["ratings"] == [1, 2, 3, 4, 5]

    # Verify provenance
    prov = manifest["provenance"]
    assert "original_generation_script" in prov
    assert Path(prov["original_generation_script"]).exists()
    assert "current_adapter_script" in prov
    assert Path(prov["current_adapter_script"]).exists()


def test_users_table(manifest):
    csv_path = PROCESSED_DIR / "users.csv"
    assert csv_path.exists()
    assert compute_sha256(csv_path) == manifest["canonical_hashes"]["users"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["user_id", "gender", "age_group", "occupation"]

        prev_uid = 0
        uids = set()
        count = 0
        for row in reader:
            count += 1
            uid = int(row[0])
            gender = row[1]
            age_group = row[2]
            occ = int(row[3])

            assert uid > prev_uid, "users must be sorted by user_id strictly ascending"
            prev_uid = uid
            assert uid not in uids
            uids.add(uid)

            assert gender in ("M", "F")
            assert age_group in VALID_AGE_GROUPS
            assert 0 <= occ <= 20

        assert count == 6040
        assert count == manifest["row_counts"]["users"]


def test_movies_table(manifest):
    csv_path = PROCESSED_DIR / "movies.csv"
    assert csv_path.exists()
    assert compute_sha256(csv_path) == manifest["canonical_hashes"]["movies"]

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["movie_id", "title", "release_year"]

        prev_mid = 0
        mids = set()
        count = 0
        for row in reader:
            count += 1
            mid = int(row[0])
            title = row[1]
            year_str = row[2]

            assert mid > prev_mid, "movies must be sorted by movie_id strictly ascending"
            prev_mid = mid
            assert mid not in mids
            mids.add(mid)

            assert len(title) > 0
            if year_str != "":
                year = int(year_str)
                assert 1900 <= year <= 2026

        assert count == 3883
        assert count == manifest["row_counts"]["movies"]


def test_movie_genres_table(manifest):
    csv_path = PROCESSED_DIR / "movie_genres.csv"
    assert csv_path.exists()
    assert compute_sha256(csv_path) == manifest["canonical_hashes"]["movie_genres"]

    # Load movies for FK check
    movies_path = PROCESSED_DIR / "movies.csv"
    with open(movies_path, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        movie_ids = {int(row[0]) for row in r}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["movie_id", "genre_name"]

        prev_key = (-1, "")
        pairs = set()
        count = 0
        genres = set()
        for row in reader:
            count += 1
            mid = int(row[0])
            genre = row[1]
            key = (mid, genre)

            assert key > prev_key, "movie_genres must be sorted by movie_id then genre_name"
            prev_key = key
            assert key not in pairs
            pairs.add(key)

            assert mid in movie_ids, f"FK violation: movie_id {mid} not in movies"
            genres.add(genre)

        assert count == 6408
        assert count == manifest["row_counts"]["movie_genres"]
        assert len(genres) == 18


def test_ratings_table(manifest):
    csv_path = PROCESSED_DIR / "ratings.csv"
    assert csv_path.exists()
    assert compute_sha256(csv_path) == manifest["canonical_hashes"]["ratings"]

    # Load users and movies for FK check
    users_path = PROCESSED_DIR / "users.csv"
    with open(users_path, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        user_ids = {int(row[0]) for row in r}

    movies_path = PROCESSED_DIR / "movies.csv"
    with open(movies_path, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        movie_ids = {int(row[0]) for row in r}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["user_id", "movie_id", "rating", "timestamp", "rated_at"]

        prev_sort_key = (-1, -1, -1, -1)
        user_movie_pairs = set()
        count = 0
        for row in reader:
            count += 1
            uid = int(row[0])
            mid = int(row[1])
            rating = int(row[2])
            ts = int(row[3])
            rated_at = row[4]

            # Sorting check: user_id, movie_id, timestamp, rating
            sort_key = (uid, mid, ts, rating)
            assert sort_key >= prev_sort_key, f"Sorting violation at row {count}: {sort_key} < {prev_sort_key}"
            prev_sort_key = sort_key

            # Business key uniqueness check
            pair = (uid, mid)
            assert pair not in user_movie_pairs, f"Duplicate (user_id, movie_id) pair: {pair}"
            user_movie_pairs.add(pair)

            assert 1 <= rating <= 5, f"Rating {rating} outside 1..5"
            assert uid in user_ids, f"FK violation: user_id {uid} not in users"
            assert mid in movie_ids, f"FK violation: movie_id {mid} not in movies"

            # Check ISO 8601 UTC format
            assert rated_at.endswith("Z"), f"rated_at must end with Z: {rated_at}"
            dt = datetime.strptime(rated_at, "%Y-%m-%dT%H:%M:%SZ")
            assert dt is not None

        assert count == 1000209
        assert count == manifest["row_counts"]["ratings"]
        assert len(user_movie_pairs) == 1000209, "Business key (user_id, movie_id) must be 100% unique"
