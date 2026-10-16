"""
Data I/O Adapter Module according to Data Contract v2.

Provides unified interface for loading MovieLens 1M data from:
- 'raw'  : data/raw/ml-1m/*.dat (GroupLens Latin-1 with :: delimiter)
- 'csv'  : data/processed/*.csv (Canonical UTF-8 CSVs)
- 'dw'   : PostgreSQL DW views dw.v_ml_* (logical tables, no genre-join)

Ensures consistent logical schemas, column ordering, sorting, and serialization.
Guarantees byte-level equivalence between 'raw' and 'csv' sources.
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw/ml-1m")
PROCESSED_DIR = Path("data/processed")
CANONICAL_MANIFEST_PATH = Path("results/eda/canonical_manifest.json")

AGE_MAP: Dict[int, str] = {
    1: "Under 18",
    18: "18-24",
    25: "25-34",
    35: "35-44",
    45: "45-49",
    50: "50-55",
    56: "56+",
}

YEAR_PATTERN = re.compile(r"\((\d{4})\)$")

TABLE_SCHEMAS: Dict[str, List[str]] = {
    "users": ["user_id", "gender", "age_group", "occupation"],
    "movies": ["movie_id", "title", "release_year"],
    "movie_genres": ["movie_id", "genre_name"],
    "ratings": ["user_id", "movie_id", "rating", "timestamp", "rated_at"],
}

SORT_KEYS: Dict[str, List[str]] = {
    "users": ["user_id"],
    "movies": ["movie_id"],
    "movie_genres": ["movie_id", "genre_name"],
    "ratings": ["user_id", "movie_id", "timestamp", "rating"],
}

DW_VIEWS: Dict[str, str] = {
    "users": "dw.v_ml_users",
    "movies": "dw.v_ml_movies",
    "movie_genres": "dw.v_ml_movie_genres",
    "ratings": "dw.v_ml_ratings",
}


class DWConnectionError(RuntimeError):
    """Raised when data warehouse connection or DW view access fails."""
    pass


def _normalize_rated_at_val(val: Any) -> Tuple[str, int]:
    """
    Normalize a single rated_at value to (canonical_utc_iso_str, epoch_seconds).
    Handles:
    - datetime / pd.Timestamp (timezone-aware or naive assumed UTC)
    - string ISO 8601 (with Z or timezone offset)
    """
    if isinstance(val, (datetime, pd.Timestamp)):
        if getattr(val, "tzinfo", None) is not None and val.tzinfo is not None:
            dt_utc = val.astimezone(timezone.utc)
        else:
            dt_utc = val.replace(tzinfo=timezone.utc)
        epoch = int(dt_utc.timestamp())
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), epoch

    val_str = str(val).strip()
    if val_str.endswith("Z"):
        dt = datetime.fromisoformat(val_str[:-1] + "+00:00")
    else:
        dt = datetime.fromisoformat(val_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    epoch = int(dt.timestamp())
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), epoch


def _normalize_and_validate_ratings(df_ratings: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize rated_at to canonical UTC format YYYY-MM-DDTHH:MM:SSZ and verify
    strict equivalence with the timestamp (epoch seconds) column.
    """
    df = df_ratings.copy()
    df["user_id"] = df["user_id"].astype(int)
    df["movie_id"] = df["movie_id"].astype(int)
    df["rating"] = df["rating"].astype(int)
    df["timestamp"] = df["timestamp"].astype("int64")

    normalized_strings = []
    ts_values = df["timestamp"].to_numpy()

    for i, val in enumerate(df["rated_at"]):
        iso_utc, epoch = _normalize_rated_at_val(val)
        if epoch != ts_values[i]:
            raise ValueError(
                f"Timestamp mismatch at row {i}: timestamp={ts_values[i]} vs rated_at={val} (epoch={epoch})"
            )
        normalized_strings.append(iso_utc)

    df["rated_at"] = normalized_strings
    return df


def serialize_df_to_canonical_csv_bytes(table_name: str, df: pd.DataFrame) -> bytes:
    """
    Serialize a logical DataFrame to standard canonical CSV bytes according to Contract v2.
    Rules: UTF-8, no BOM, comma delimiter, LF line terminator, header present,
    minimal quoting, empty string for NULL, integer without .0.
    """
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(f"Unknown table: {table_name}")

    expected_cols = TABLE_SCHEMAS[table_name]
    if list(df.columns) != expected_cols:
        raise ValueError(
            f"Table {table_name} column mismatch: expected {expected_cols}, got {list(df.columns)}"
        )

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=",", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(expected_cols)

    for row in df.itertuples(index=False):
        formatted_row = []
        for val in row:
            if pd.isna(val) or val is None:
                formatted_row.append("")
            elif isinstance(val, (datetime, pd.Timestamp)):
                iso_utc, _ = _normalize_rated_at_val(val)
                formatted_row.append(iso_utc)
            elif isinstance(val, (int, np.integer)):
                formatted_row.append(int(val))
            elif isinstance(val, (float, np.floating)):
                if val.is_integer():
                    formatted_row.append(int(val))
                else:
                    formatted_row.append(val)
            else:
                formatted_row.append(str(val))
        writer.writerow(formatted_row)

    return buf.getvalue().encode("utf-8")


def compute_canonical_hash(table_name: str, df: pd.DataFrame) -> str:
    """Compute SHA-256 hex digest of canonically serialized DataFrame."""
    return hashlib.sha256(serialize_df_to_canonical_csv_bytes(table_name, df)).hexdigest()


# ---------------------------------------------------------------------------
# RAW SOURCE LOADERS
# ---------------------------------------------------------------------------

def _load_raw_users(raw_dir: Path) -> pd.DataFrame:
    users_dat = raw_dir / "users.dat"
    if not users_dat.exists():
        raise FileNotFoundError(f"Missing raw file: {users_dat}")

    records = []
    user_ids = set()
    with open(users_dat, "r", encoding="latin-1") as f:
        for line_num, line in enumerate(f, start=1):
            parts = line.strip().split("::")
            if len(parts) != 5:
                raise ValueError(f"Malformed users.dat line {line_num}: {line}")
            uid_str, gender, age_str, occ_str, _ = parts
            uid = int(uid_str)
            if uid in user_ids:
                raise ValueError(f"Duplicate user_id {uid} at line {line_num}")
            user_ids.add(uid)

            age_code = int(age_str)
            if age_code not in AGE_MAP:
                raise ValueError(f"Unknown age code {age_code} at line {line_num}")

            records.append((uid, gender, AGE_MAP[age_code], int(occ_str)))

    # Sort strictly by user_id ascending
    records.sort(key=lambda x: x[0])
    df = pd.DataFrame(records, columns=TABLE_SCHEMAS["users"])
    df["user_id"] = df["user_id"].astype(int)
    df["occupation"] = df["occupation"].astype(int)
    return df


def _load_raw_movies_and_genres(raw_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    movies_dat = raw_dir / "movies.dat"
    if not movies_dat.exists():
        raise FileNotFoundError(f"Missing raw file: {movies_dat}")

    movies_records = []
    genres_records = []
    movie_ids = set()
    mg_pairs = set()

    with open(movies_dat, "r", encoding="latin-1") as f:
        for line_num, line in enumerate(f, start=1):
            parts = line.strip().split("::")
            if len(parts) != 3:
                raise ValueError(f"Malformed movies.dat line {line_num}: {line}")
            mid_str, title, genres_str = parts
            mid = int(mid_str)
            if mid in movie_ids:
                raise ValueError(f"Duplicate movie_id {mid} at line {line_num}")
            movie_ids.add(mid)

            match = YEAR_PATTERN.search(title.strip())
            release_year = int(match.group(1)) if match else None
            movies_records.append((mid, title, release_year))

            for g in genres_str.split("|"):
                g = g.strip()
                pair = (mid, g)
                if pair in mg_pairs:
                    raise ValueError(f"Duplicate genre pair {pair} at line {line_num}")
                mg_pairs.add(pair)
                genres_records.append(pair)

    # Sort movies by movie_id ascending
    movies_records.sort(key=lambda x: x[0])
    # Sort movie_genres by movie_id ascending, then genre_name ascending
    genres_records.sort(key=lambda x: (x[0], x[1]))

    df_movies = pd.DataFrame(movies_records, columns=TABLE_SCHEMAS["movies"])
    df_movies["movie_id"] = df_movies["movie_id"].astype(int)
    df_movies["release_year"] = df_movies["release_year"].astype("Int64")

    df_genres = pd.DataFrame(genres_records, columns=TABLE_SCHEMAS["movie_genres"])
    df_genres["movie_id"] = df_genres["movie_id"].astype(int)

    return df_movies, df_genres


def _load_raw_ratings(raw_dir: Path) -> pd.DataFrame:
    ratings_dat = raw_dir / "ratings.dat"
    if not ratings_dat.exists():
        raise FileNotFoundError(f"Missing raw file: {ratings_dat}")

    records = []
    user_movie_pairs = set()

    with open(ratings_dat, "r", encoding="latin-1") as f:
        for line_num, line in enumerate(f, start=1):
            parts = line.strip().split("::")
            if len(parts) != 4:
                raise ValueError(f"Malformed ratings.dat line {line_num}: {line}")
            uid_str, mid_str, rating_str, ts_str = parts
            uid, mid, rating, ts = int(uid_str), int(mid_str), int(rating_str), int(ts_str)

            pair = (uid, mid)
            if pair in user_movie_pairs:
                raise ValueError(f"Duplicate rating pair (user_id={uid}, movie_id={mid}) at line {line_num}")
            user_movie_pairs.add(pair)

            if not (1 <= rating <= 5):
                raise ValueError(f"Rating {rating} outside 1..5 at line {line_num}")

            rated_at_utc = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            records.append((uid, mid, rating, ts, rated_at_utc))

    # Sort ratings by user_id, movie_id, timestamp, rating
    records.sort(key=lambda x: (x[0], x[1], x[2], x[3]))

    df = pd.DataFrame(records, columns=TABLE_SCHEMAS["ratings"])
    df["user_id"] = df["user_id"].astype(int)
    df["movie_id"] = df["movie_id"].astype(int)
    df["rating"] = df["rating"].astype(int)
    df["timestamp"] = df["timestamp"].astype("int64")
    return df


def load_raw_data(raw_dir: Path = RAW_DIR) -> Dict[str, pd.DataFrame]:
    """Load all 4 canonical tables parsed directly from raw GroupLens .dat files."""
    users_df = _load_raw_users(raw_dir)
    movies_df, movie_genres_df = _load_raw_movies_and_genres(raw_dir)
    ratings_df = _load_raw_ratings(raw_dir)
    return {
        "users": users_df,
        "movies": movies_df,
        "movie_genres": movie_genres_df,
        "ratings": ratings_df,
    }


# ---------------------------------------------------------------------------
# CSV SOURCE LOADERS
# ---------------------------------------------------------------------------

def load_csv_data(processed_dir: Path = PROCESSED_DIR) -> Dict[str, pd.DataFrame]:
    """Load all 4 canonical tables from canonical CSV files."""
    users_path = processed_dir / "users.csv"
    movies_path = processed_dir / "movies.csv"
    genres_path = processed_dir / "movie_genres.csv"
    ratings_path = processed_dir / "ratings.csv"

    for p in [users_path, movies_path, genres_path, ratings_path]:
        if not p.exists():
            raise FileNotFoundError(f"Missing canonical CSV file: {p}")

    users_df = pd.read_csv(
        users_path,
        dtype={"user_id": int, "gender": str, "age_group": str, "occupation": int},
    )
    movies_df = pd.read_csv(
        movies_path,
        dtype={"movie_id": int, "title": str, "release_year": "Int64"},
    )
    genres_df = pd.read_csv(
        genres_path,
        dtype={"movie_id": int, "genre_name": str},
    )
    ratings_df = pd.read_csv(
        ratings_path,
        dtype={"user_id": int, "movie_id": int, "rating": int, "timestamp": "int64", "rated_at": str},
    )

    return {
        "users": users_df[TABLE_SCHEMAS["users"]],
        "movies": movies_df[TABLE_SCHEMAS["movies"]],
        "movie_genres": genres_df[TABLE_SCHEMAS["movie_genres"]],
        "ratings": ratings_df[TABLE_SCHEMAS["ratings"]],
    }


# ---------------------------------------------------------------------------
# DATA WAREHOUSE (DW) SOURCE LOADER
# ---------------------------------------------------------------------------

def load_dw_data(connection_or_engine: Optional[Any] = None) -> Dict[str, pd.DataFrame]:
    """
    Load all 4 canonical tables from PostgreSQL DW views (dw.v_ml_*).
    Retains exact logical schema, sorting, and source IDs.
    Does NOT join movie_genres into ratings.

    If connection_or_engine is None, attempts to construct a connection using
    environment variables (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD),
    never logging passwords or connection URIs.
    """
    conn = connection_or_engine
    close_conn = False

    if conn is None:
        # Try psycopg2 or sqlalchemy if installed
        try:
            import psycopg2  # type: ignore
            host = os.getenv("PGHOST", "localhost")
            port = int(os.getenv("PGPORT", "5432"))
            dbname = os.getenv("PGDATABASE", "movielens_dw")
            user = os.getenv("PGUSER", "postgres")
            password = os.getenv("PGPASSWORD", "")
            conn = psycopg2.connect(
                host=host, port=port, dbname=dbname, user=user, password=password, connect_timeout=3
            )
            close_conn = True
        except Exception as e:
            err_type = type(e).__name__
            raise DWConnectionError(
                f"DW connection not available ({err_type}). DW views dw.v_ml_* require Person 1 (P1) milestone G2. "
                "Use source='csv' or source='raw' for current mining workflows. "
                "Raw credentials and connection details are suppressed for security."
            ) from None

    results = {}
    try:
        # Helper to execute query whether conn is DB-API connection or SQLAlchemy Engine
        def _query(sql: str) -> pd.DataFrame:
            if hasattr(conn, "connect"):  # SQLAlchemy Engine
                with conn.connect() as active_conn:
                    return pd.read_sql(sql, active_conn)
            else:  # DB-API connection (psycopg2, sqlite3)
                return pd.read_sql(sql, conn)

        # 1. users
        sql_users = "SELECT user_id, gender, age_group, occupation FROM dw.v_ml_users ORDER BY user_id ASC"
        df_users = _query(sql_users)
        df_users["user_id"] = df_users["user_id"].astype(int)
        df_users["occupation"] = df_users["occupation"].astype(int)
        results["users"] = df_users[TABLE_SCHEMAS["users"]]

        # 2. movies
        sql_movies = "SELECT movie_id, title, release_year FROM dw.v_ml_movies ORDER BY movie_id ASC"
        df_movies = _query(sql_movies)
        df_movies["movie_id"] = df_movies["movie_id"].astype(int)
        df_movies["release_year"] = df_movies["release_year"].astype("Int64")
        results["movies"] = df_movies[TABLE_SCHEMAS["movies"]]

        # 3. movie_genres
        sql_genres = "SELECT movie_id, genre_name FROM dw.v_ml_movie_genres ORDER BY movie_id ASC, genre_name ASC"
        df_genres = _query(sql_genres)
        df_genres["movie_id"] = df_genres["movie_id"].astype(int)
        results["movie_genres"] = df_genres[TABLE_SCHEMAS["movie_genres"]]

        # 4. ratings (without joining genres)
        sql_ratings = "SELECT user_id, movie_id, rating, timestamp, rated_at FROM dw.v_ml_ratings ORDER BY user_id ASC, movie_id ASC, timestamp ASC, rating ASC"
        df_ratings = _query(sql_ratings)
        df_ratings = _normalize_and_validate_ratings(df_ratings)
        results["ratings"] = df_ratings[TABLE_SCHEMAS["ratings"]]

    except Exception as e:
        if isinstance(e, DWConnectionError):
            raise
        err_type = type(e).__name__
        raise DWConnectionError(
            f"Failed to query DW views dw.v_ml_* ({err_type}). "
            "Note: DW views require Person 1 (P1) milestone G2. "
            "Raw credentials and connection details are suppressed for security."
        ) from None
    finally:
        if close_conn and conn is not None and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass

    return results



# ---------------------------------------------------------------------------
# UNIFIED INTERFACE & EQUIVALENCE CHECK
# ---------------------------------------------------------------------------

def load_data(
    source: str = "csv",
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    connection_or_engine: Optional[Any] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Unified loader for MovieLens 1M logical tables.
    source options:
      - 'raw': parse raw files in data/raw/ml-1m/
      - 'csv': read canonical CSVs in data/processed/
      - 'dw' : query PostgreSQL views dw.v_ml_*
    """
    s = source.lower().strip()
    if s == "raw":
        return load_raw_data(raw_dir=raw_dir)
    elif s == "csv":
        return load_csv_data(processed_dir=processed_dir)
    elif s == "dw":
        return load_dw_data(connection_or_engine=connection_or_engine)
    else:
        raise ValueError(f"Unknown data source '{source}'. Expected 'raw', 'csv', or 'dw'.")



def verify_raw_csv_equivalence(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
) -> Dict[str, Dict[str, Any]]:
    """
    Verifies that raw and CSV data sources produce identical schemas,
    row counts, cell values, and canonical SHA-256 serialized hashes.
    """
    raw_data = load_raw_data(raw_dir=raw_dir)
    csv_data = load_csv_data(processed_dir=processed_dir)

    manifest_hashes = {}
    if CANONICAL_MANIFEST_PATH.exists():
        import json
        with open(CANONICAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            manifest_hashes = manifest.get("canonical_hashes", {})

    report = {}
    all_equivalent = True

    for tbl in ["users", "movies", "movie_genres", "ratings"]:
        raw_df = raw_data[tbl]
        csv_df = csv_data[tbl]

        raw_hash = compute_canonical_hash(tbl, raw_df)
        csv_hash = compute_canonical_hash(tbl, csv_df)
        expected_hash = manifest_hashes.get(tbl, "")

        shapes_match = (raw_df.shape == csv_df.shape)
        cols_match = (list(raw_df.columns) == list(csv_df.columns))
        hashes_match = (raw_hash == csv_hash)
        matches_manifest = (raw_hash == expected_hash) if expected_hash else True

        is_equiv = shapes_match and cols_match and hashes_match and matches_manifest
        if not is_equiv:
            all_equivalent = False

        report[tbl] = {
            "equivalent": is_equiv,
            "raw_rows": len(raw_df),
            "csv_rows": len(csv_df),
            "raw_hash": raw_hash,
            "csv_hash": csv_hash,
            "manifest_hash": expected_hash,
            "hashes_match": hashes_match,
        }

    report["overall_equivalence"] = all_equivalent  # type: ignore
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MovieLens 1M Data I/O Adapter (Contract v2)")
    parser.add_argument("--source", choices=["raw", "csv", "dw"], default="csv", help="Data source to load")
    parser.add_argument("--verify-equivalence", action="store_true", help="Verify raw and csv source equivalence")
    args = parser.parse_args()

    if args.verify_equivalence:
        print("=== VERIFYING RAW <-> CSV EQUIVALENCE (Data Contract v2) ===")
        rep = verify_raw_csv_equivalence()
        for tbl in ["users", "movies", "movie_genres", "ratings"]:
            info = rep[tbl]
            status = "PASS" if info["equivalent"] else "FAIL"
            print(f"[{status}] Table '{tbl}': rows={info['raw_rows']}, hash={info['raw_hash'][:16]}...")
        overall = rep.get("overall_equivalence")
        if overall:
            print("Overall Equivalence: PASSED")
            return 0
        else:
            print("Overall Equivalence: FAILED", file=sys.stderr)
            return 1

    print(f"Loading data from source: {args.source}...")
    try:
        tables = load_data(source=args.source)
        for tbl, df in tables.items():
            print(f"  - Table {tbl}: {df.shape[0]} rows, columns={list(df.columns)}")
        print("Load successful.")
        return 0
    except DWConnectionError as e:
        print(f"[ERROR] DW access failed: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[ERROR] Loading data failed ({type(e).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
