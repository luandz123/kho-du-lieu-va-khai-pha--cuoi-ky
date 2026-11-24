"""Nạp dữ liệu ban đầu cho DB app: danh sách người dùng và phim (lấy từ silver).

Bảng ratings của app để TRỐNG: mọi rating trên app đều là dữ liệu MỚI, đi vào kho qua CDC.

Chạy: python -m app_source.seed
"""
import psycopg2
from psycopg2.extras import execute_values
import pyarrow.parquet as pq

from pipeline import config, lake


def read(table, columns):
    with lake.filesystem().open(lake.path("silver", table, "data.parquet"), "rb") as f:
        return pq.read_table(f, columns=columns).to_pylist()


def main():
    users = read("users", ["user_id", "gender", "age", "occupation"])
    movies = read("movies", ["movie_id", "title", "year", "imdb_id"])
    with psycopg2.connect(config.app_dsn()) as conn, conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO users (user_id, gender, age, occupation) VALUES %s
            ON CONFLICT (user_id) DO NOTHING""",
            [(u["user_id"], u["gender"], u["age"], u["occupation"]) for u in users])
        execute_values(cur, """
            INSERT INTO movies (movie_id, title, year, imdb_id) VALUES %s
            ON CONFLICT (movie_id) DO NOTHING""",
            [(m["movie_id"], m["title"], m["year"], m["imdb_id"]) for m in movies])
        cur.execute("SELECT (SELECT count(*) FROM users), (SELECT count(*) FROM movies)")
        print("App DB: %s users, %s movies" % cur.fetchone())


if __name__ == "__main__":
    main()
