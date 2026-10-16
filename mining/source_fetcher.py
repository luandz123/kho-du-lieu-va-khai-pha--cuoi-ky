"""
MovieLens 1M Source Fetcher and Manifest Generator.
P2 owns data/source_manifest.json.
Downloads from official GroupLens repository, extracts raw files,
computes SHA-256 byte hashes and line counts, and produces data/source_manifest.json.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

GROUPLENS_URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"
DATASET_VERSION = "MovieLens 1M"
RAW_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/source_manifest.json")


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file in binary mode."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def count_lines(filepath: Path, encoding: str = "latin-1") -> int:
    """Count physical lines in a text file."""
    with open(filepath, "r", encoding=encoding) as f:
        return sum(1 for _ in f)


def fetch_and_generate_manifest() -> dict:
    """Download MovieLens 1M, extract, and write source_manifest.json."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "ml-1m.zip"

    # Download if not exists
    if not zip_path.exists():
        print(f"Downloading {GROUPLENS_URL} -> {zip_path}...")
        urllib.request.urlretrieve(GROUPLENS_URL, zip_path)
        print("Download complete.")
    else:
        print(f"Using existing archive: {zip_path}")

    # Extract archive
    print(f"Extracting {zip_path} into {RAW_DIR}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(RAW_DIR)
    print("Extraction complete.")

    extracted_dir = RAW_DIR / "ml-1m"
    if not extracted_dir.exists():
        raise FileNotFoundError(f"Expected extracted directory {extracted_dir} does not exist.")

    files_info = {}
    target_files = ["users.dat", "movies.dat", "ratings.dat", "README"]

    for fname in target_files:
        fpath = extracted_dir / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing expected source file: {fpath}")

        sha256 = compute_sha256(fpath)
        line_count = count_lines(fpath, encoding="latin-1")
        size_bytes = fpath.stat().st_size

        files_info[fname] = {
            "relative_path": f"data/raw/ml-1m/{fname}",
            "size_bytes": size_bytes,
            "line_count": line_count,
            "sha256": sha256,
            "encoding": "Latin-1"
        }
        print(f"[{fname}] Lines: {line_count}, SHA-256: {sha256}")

    # Also record the zip file itself
    zip_sha256 = compute_sha256(zip_path)

    manifest_data = {
        "dataset_version": DATASET_VERSION,
        "source_url": GROUPLENS_URL,
        "download_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "archive": {
            "relative_path": "data/raw/ml-1m.zip",
            "size_bytes": zip_path.stat().st_size,
            "sha256": zip_sha256
        },
        "encoding": "Latin-1",
        "delimiter": "::",
        "files": files_info
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated source manifest at {MANIFEST_PATH}")
    return manifest_data


if __name__ == "__main__":
    fetch_and_generate_manifest()
