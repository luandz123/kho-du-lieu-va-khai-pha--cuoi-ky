"""Nguồn 1: MovieLens.

- ML-1M (users, movies, ratings): lịch sử rating, đưa nguyên file gốc vào bronze.
- links.csv của bộ ml-latest-small: ánh xạ movieId -> imdbId -> tmdbId. ML-1M không kèm
  file này, nhưng movieId giữ nguyên giữa các phiên bản MovieLens. Bộ nhỏ chỉ khớp
  khoảng 76% phim của ML-1M; phần còn lại được ghép theo tên + năm với IMDb ở tầng silver.
  (Bộ ml-32m khớp đủ hơn nhưng file 240 MB, máy chủ GroupLens tải từ VN rất chậm.)

Chạy: python -m sources.movielens
"""
import csv
import io
import zipfile

from pipeline import config, lake
from sources.web import download

LINKS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


def ingest_ml1m():
    for name in ("users.dat", "movies.dat", "ratings.dat"):
        src = config.ML1M_DIR / name
        target = lake.bronze_path("movielens", name.removesuffix(".dat"), name)
        lake.put_file(src, target)
        print("bronze <-", target)


def ingest_links():
    zip_path = download(LINKS_URL, config.DOWNLOAD_DIR / "ml-latest-small.zip")
    with zipfile.ZipFile(zip_path) as z:
        data = z.read("ml-latest-small/links.csv")
    target = lake.bronze_path("movielens", "links", "links.csv")
    lake.put_bytes(data, target)
    ml1m_ids = {line.split("::")[0] for line in open(config.ML1M_DIR / "movies.dat", encoding="latin-1")}
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    matched = sum(1 for r in rows if r["movieId"] in ml1m_ids and r["imdbId"])
    print("bronze <-", target)
    print(f"  links.csv: {len(rows)} phim, khớp {matched}/{len(ml1m_ids)} phim của ML-1M")


if __name__ == "__main__":
    ingest_ml1m()
    ingest_links()
