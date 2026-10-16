"""
Tests for source manifest integrity.
Verifies that data/source_manifest.json exists and accurately reflects
the raw MovieLens 1M files downloaded from GroupLens.
"""
import hashlib
import json
from pathlib import Path
import pytest

MANIFEST_PATH = Path("data/source_manifest.json")
RAW_DIR = Path("data/raw/ml-1m")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path: Path, encoding="latin-1") -> int:
    with open(path, "r", encoding=encoding) as f:
        return sum(1 for _ in f)


def test_source_manifest_structure():
    assert MANIFEST_PATH.exists(), "data/source_manifest.json must exist."
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("dataset_version") == "MovieLens 1M"
    assert manifest.get("source_url") == "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
    assert "download_date_utc" in manifest
    assert manifest.get("encoding") == "Latin-1"
    assert manifest.get("delimiter") == "::"
    assert "files" in manifest

    expected_files = ["users.dat", "movies.dat", "ratings.dat", "README"]
    for fname in expected_files:
        assert fname in manifest["files"], f"Missing {fname} in source manifest."
        finfo = manifest["files"][fname]
        assert finfo["sha256"] is not None
        assert finfo["line_count"] > 0
        assert finfo["size_bytes"] > 0


def test_raw_files_checksums_and_counts():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for fname, info in manifest["files"].items():
        fpath = Path(info["relative_path"])
        assert fpath.exists(), f"Source file {fpath} does not exist on disk."
        real_sha256 = compute_sha256(fpath)
        assert real_sha256 == info["sha256"], f"SHA-256 mismatch for {fname}"
        real_lines = count_lines(fpath, encoding=info.get("encoding", "latin-1"))
        assert real_lines == info["line_count"], f"Line count mismatch for {fname}"
