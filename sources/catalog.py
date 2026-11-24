"""Danh sách phim của ML-1M kèm IMDb ID, lấy từ silver/movies.

silver/movies đã ghép IMDb ID bằng links.csv và theo tên + năm (khoảng 98% phim).
Các nguồn sau (Wikidata, Pageviews) chỉ cần lấy dữ liệu cho đúng những phim này.
"""
import pyarrow.parquet as pq

from pipeline import lake


def ml1m_imdb_ids() -> dict[int, str]:
    """movieId -> tconst IMDb (dạng 'tt0114709')."""
    target = lake.path("silver", "movies", "data.parquet")
    if not lake.exists(target):
        raise RuntimeError("Chưa có silver/movies, chạy: python -m transform.silver movies")
    with lake.filesystem().open(target, "rb") as f:
        t = pq.read_table(f, columns=["movie_id", "imdb_id"]).to_pylist()
    return {r["movie_id"]: r["imdb_id"] for r in t if r["imdb_id"]}
