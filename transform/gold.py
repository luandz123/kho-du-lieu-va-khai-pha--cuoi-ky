"""Tầng gold: bảng đã đúng hình dạng của kho (chiều + sự kiện), dùng khóa tự nhiên.
Bước nạp kho (warehouse/load.py) chỉ việc đổi khóa tự nhiên sang khóa thay thế và upsert.

Bảng tạo ra:
  gold/dim_movie, gold/movie_genre, gold/dim_user
  gold/fact_rating            MovieLens + app (CDC), có cột changed_at để nạp tăng dần
  gold/fact_imdb_rating_daily điểm IMDb mỗi ngày + số vote tăng thêm so với hôm trước
  gold/fact_pageviews_daily, gold/fact_wiki_edit

Chạy: python -m transform.gold [tên bảng ...]
"""
import sys

from pipeline import lake
from transform.duck import connect, write_parquet

AGE = {1: "Under 18", 18: "18-24", 25: "25-34", 35: "35-44", 45: "45-49", 50: "50-55", 56: "56+"}
OCCUPATION = ["other", "academic/educator", "artist", "clerical/admin", "college/grad student",
              "customer service", "doctor/health care", "executive/managerial", "farmer", "homemaker",
              "K-12 student", "lawyer", "programmer", "retired", "sales/marketing", "scientist",
              "self-employed", "technician/engineer", "tradesman/craftsman", "unemployed", "writer"]


def s(table: str) -> str:
    return f"read_parquet('{lake.path('silver', table, 'data.parquet')}')"


def _lookups(con):
    con.execute("CREATE OR REPLACE TEMP TABLE age_map AS SELECT * FROM (VALUES "
                + ", ".join(f"({k}, '{v}')" for k, v in AGE.items()) + ") t(age, age_group)")
    con.execute("CREATE OR REPLACE TEMP TABLE occ_map AS SELECT * FROM (VALUES "
                + ", ".join(f"({i}, '{v}')" for i, v in enumerate(OCCUPATION)) + ") t(occupation, occupation_name)")


def dim_movie(con):
    # Ảnh poster lấy từ Wikipedia; nếu chưa tải tóm tắt thì để trống.
    if lake.exists(lake.path("silver", "summaries", "data.parquet")):
        summaries = s("summaries")
    else:
        summaries = "(SELECT NULL::VARCHAR AS imdb_id, NULL::VARCHAR AS poster_url LIMIT 0)"
    sql = f"""
        SELECT m.movie_id, m.title, m.year, m.imdb_id, m.match_method AS imdb_match,
               i.runtime_minutes, i.directors, i.top_cast,
               w.countries, w.oscar_wins, w.enwiki_title, w.viwiki_title, su.poster_url
        FROM {s('movies')} m
        LEFT JOIN {s('imdb_movies')} i USING (imdb_id)
        LEFT JOIN {s('wiki_links')} w USING (imdb_id)
        LEFT JOIN {summaries} su USING (imdb_id)
    """
    return write_parquet(con, sql, "gold", "dim_movie")


def movie_genre(con):
    sql = f"SELECT movie_id, unnest(genres) AS genre_name FROM {s('movies')}"
    return write_parquet(con, sql, "gold", "movie_genre")


def dim_user(con):
    """Các phiên bản của người dùng, để nạp theo SCD loại 2:
      - phiên bản gốc từ MovieLens, coi như có hiệu lực từ 1990 (trước mọi rating);
      - phiên bản mới nhất từ app (nếu người dùng đã đổi thông tin), có hiệu lực từ lúc đổi."""
    _lookups(con)
    sql = f"""
        WITH latest AS (
            SELECT user_id, gender, age, occupation, TIMESTAMPTZ '1990-01-01 00:00:00+00' AS changed_at
            FROM {s('users')} u
            UNION ALL
            SELECT user_id, gender, age, occupation, changed_at FROM {s('app_users')})
        SELECT l.user_id, l.gender, a.age_group, o.occupation_name AS occupation, l.changed_at
        FROM latest l JOIN age_map a USING (age) JOIN occ_map o USING (occupation)
    """
    return write_parquet(con, sql, "gold", "dim_user")


def fact_rating(con):
    sql = f"""
        SELECT user_id, movie_id, rating, rated_at, 'movielens' AS source, false AS is_deleted,
               rated_at AS changed_at
        FROM {s('ratings')}
        UNION ALL
        SELECT user_id, movie_id, rating, rated_at, 'app', is_deleted, changed_at
        FROM {s('app_ratings')}
    """
    return write_parquet(con, sql, "gold", "fact_rating")


def fact_imdb_rating_daily(con):
    sql = f"""
        SELECT m.movie_id, r.snapshot_date, r.imdb_rating, r.imdb_votes,
               r.imdb_votes - lag(r.imdb_votes) OVER (PARTITION BY m.movie_id ORDER BY r.snapshot_date) AS votes_delta
        FROM {s('imdb_ratings')} r JOIN {s('movies')} m USING (imdb_id)
    """
    return write_parquet(con, sql, "gold", "fact_imdb_rating_daily")


def fact_pageviews_daily(con):
    sql = f"""
        SELECT m.movie_id, p.view_date, p.views
        FROM {s('pageviews')} p JOIN {s('movies')} m USING (imdb_id)
    """
    return write_parquet(con, sql, "gold", "fact_pageviews_daily")


def fact_wiki_edit(con):
    sql = f"""
        SELECT e.event_id, m.movie_id, e.wiki, e.edited_at, e.is_bot, e.size_delta
        FROM {s('wiki_edits')} e JOIN {s('movies')} m USING (imdb_id)
        QUALIFY row_number() OVER (PARTITION BY e.event_id ORDER BY m.movie_id) = 1
    """
    return write_parquet(con, sql, "gold", "fact_wiki_edit")


STEPS = {f.__name__: f for f in [dim_movie, movie_genre, dim_user, fact_rating,
                                  fact_imdb_rating_daily, fact_pageviews_daily, fact_wiki_edit]}

if __name__ == "__main__":
    con = connect()
    for name in sys.argv[1:] or STEPS:
        STEPS[name](con)
