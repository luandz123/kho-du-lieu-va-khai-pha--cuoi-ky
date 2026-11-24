"""Nạp tầng gold vào kho dữ liệu Postgres theo kiểu TĂNG DẦN (incremental), không TRUNCATE.

Cách làm chung cho mỗi bảng:
  1. DuckDB đọc gold (Parquet trên MinIO), chỉ lấy dòng mới hơn watermark nếu có.
  2. COPY vào bảng tạm trong Postgres (nhanh hơn INSERT từng dòng rất nhiều).
  3. Một câu SQL MERGE/UPSERT từ bảng tạm vào bảng thật: đổi khóa tự nhiên -> khóa thay thế.
  4. Ghi số dòng vào etl.pipeline_run, cập nhật etl.watermark.

Chạy 2 lần liên tiếp không nhân đôi dữ liệu (idempotent) vì mọi bước đều upsert theo khóa.

  dim_movie   SCD loại 1: ghi đè giá trị mới
  dim_user    SCD loại 2: đóng phiên bản cũ (valid_to), mở phiên bản mới
  fact_rating upsert theo (user_id, movie_id), chỉ nạp dòng có changed_at > watermark

Chạy: python -m warehouse.load [bảng ...]
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import io
import sys

import pandas as pd
import psycopg2

from pipeline import config, lake
from transform.duck import connect as duck

# Khoảng đọc lùi so với watermark để không bỏ sót sự kiện CDC đến muộn.
LOOKBACK = "1 HOUR"


def g(table: str) -> str:
    return f"read_parquet('{lake.path('gold', table, 'data.parquet')}')"


def pg_array(values) -> str | None:
    if values is None or values is pd.NA or (isinstance(values, float) and pd.isna(values)):
        return None
    items = ['"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"' for v in values]
    return "{" + ",".join(items) + "}"


def copy_df(cur, df: pd.DataFrame, table: str, ddl: str):
    """Tạo bảng tạm theo ddl rồi COPY DataFrame vào."""
    cur.execute(f"CREATE TEMP TABLE {table} ({ddl}) ON COMMIT DROP")
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    cur.copy_expert(f"COPY {table} FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)


@contextmanager
def run_log(cur, step: str):
    cur.execute("INSERT INTO etl.pipeline_run (step, started_at, status) VALUES (%s, now(), 'running') RETURNING run_id",
                (step,))
    run_id = cur.fetchone()[0]
    stats = {"rows_in": 0, "rows_out": 0}
    try:
        yield stats
    except Exception as e:
        cur.connection.rollback()
        cur.execute("""UPDATE etl.pipeline_run SET finished_at = now(), status = 'failed', message = %s
                       WHERE run_id = %s""", (str(e)[:500], run_id))
        cur.connection.commit()
        raise
    cur.execute("""UPDATE etl.pipeline_run SET finished_at = now(), status = 'success', rows_in = %s, rows_out = %s
                   WHERE run_id = %s""", (stats["rows_in"], stats["rows_out"], run_id))
    print(f"{step}: đọc {stats['rows_in']:,} dòng gold, ghi/cập nhật {stats['rows_out']:,} dòng kho")


def watermark(cur, name: str) -> datetime:
    cur.execute("SELECT value FROM etl.watermark WHERE name = %s", (name,))
    row = cur.fetchone()
    return row[0] if row else datetime(1900, 1, 1, tzinfo=timezone.utc)


def set_watermark(cur, name: str, value):
    cur.execute("""INSERT INTO etl.watermark (name, value) VALUES (%s, %s)
                   ON CONFLICT (name) DO UPDATE SET value = EXCLUDED.value, updated_at = now()""", (name, value))


# ------------------------------------------------------------------ dimensions
def dim_movie(cur, con):
    with run_log(cur, "load.dim_movie") as st:
        df = con.execute(f"SELECT * FROM {g('dim_movie')}").df()
        for col in ["directors", "top_cast", "countries"]:
            df[col] = df[col].map(pg_array)
        for col in ["year", "runtime_minutes", "oscar_wins"]:
            df[col] = df[col].astype("Int64")
        st["rows_in"] = len(df)
        copy_df(cur, df, "tmp_movie", """movie_id int, title text, year smallint, imdb_id text, imdb_match text,
                runtime_minutes smallint, directors text[], top_cast text[], countries text[], oscar_wins smallint,
                enwiki_title text, viwiki_title text, poster_url text""")
        cur.execute("""
            INSERT INTO dw.dim_movie AS d (movie_id, title, year, imdb_id, imdb_match, runtime_minutes, directors,
                                           top_cast, countries, oscar_wins, enwiki_title, viwiki_title,
                                           poster_url)
            SELECT * FROM tmp_movie
            ON CONFLICT (movie_id) DO UPDATE SET
                title = EXCLUDED.title, year = EXCLUDED.year, imdb_id = EXCLUDED.imdb_id,
                imdb_match = EXCLUDED.imdb_match, runtime_minutes = EXCLUDED.runtime_minutes,
                directors = EXCLUDED.directors, top_cast = EXCLUDED.top_cast, countries = EXCLUDED.countries,
                oscar_wins = EXCLUDED.oscar_wins, enwiki_title = EXCLUDED.enwiki_title,
                viwiki_title = EXCLUDED.viwiki_title, poster_url = EXCLUDED.poster_url, updated_at = now()
            WHERE (d.title, d.year, d.imdb_id, d.runtime_minutes, d.directors, d.top_cast, d.countries,
                   d.oscar_wins, d.enwiki_title, d.viwiki_title, d.poster_url)
                  IS DISTINCT FROM
                  (EXCLUDED.title, EXCLUDED.year, EXCLUDED.imdb_id, EXCLUDED.runtime_minutes, EXCLUDED.directors,
                   EXCLUDED.top_cast, EXCLUDED.countries, EXCLUDED.oscar_wins, EXCLUDED.enwiki_title,
                   EXCLUDED.viwiki_title, EXCLUDED.poster_url)""")
        st["rows_out"] = cur.rowcount

    with run_log(cur, "load.genre") as st:
        df = con.execute(f"SELECT * FROM {g('movie_genre')}").df()
        st["rows_in"] = len(df)
        copy_df(cur, df, "tmp_genre", "movie_id int, genre_name text")
        cur.execute("INSERT INTO dw.dim_genre (genre_name) SELECT DISTINCT genre_name FROM tmp_genre "
                    "ON CONFLICT (genre_name) DO NOTHING")
        cur.execute("""
            INSERT INTO dw.bridge_movie_genre (movie_key, genre_key)
            SELECT m.movie_key, ge.genre_key FROM tmp_genre t
            JOIN dw.dim_movie m USING (movie_id) JOIN dw.dim_genre ge USING (genre_name)
            ON CONFLICT DO NOTHING""")
        st["rows_out"] = cur.rowcount


def dim_user(cur, con):
    """SCD loại 2."""
    # Nạp theo thứ tự thời gian: phiên bản gốc (MovieLens) trước, thay đổi từ app sau.
    with run_log(cur, "load.dim_user") as st:
        all_versions = con.execute(f"SELECT * FROM {g('dim_user')} ORDER BY changed_at").df()
        st["rows_in"] = len(all_versions)
        for _, df in all_versions.groupby(all_versions["changed_at"] > pd.Timestamp("1990-01-02", tz="UTC")):
            st["rows_out"] += _merge_user_versions(cur, df)


def _merge_user_versions(cur, df) -> int:
    cur.execute("DROP TABLE IF EXISTS tmp_user")
    copy_df(cur, df, "tmp_user", "user_id int, gender char(1), age_group text, occupation text, changed_at timestamptz")
    # 1. Đóng phiên bản hiện tại nếu thuộc tính đã đổi.
    cur.execute("""
        UPDATE dw.dim_user d SET valid_to = t.changed_at, is_current = false
        FROM tmp_user t
        WHERE d.user_id = t.user_id AND d.is_current AND t.changed_at > d.valid_from
          AND (d.gender, d.age_group, d.occupation) IS DISTINCT FROM (t.gender, t.age_group, t.occupation)""")
    closed = cur.rowcount
    # 2. Thêm phiên bản mới cho user chưa có phiên bản hiện tại (user mới hoặc vừa bị đóng).
    cur.execute("""
        INSERT INTO dw.dim_user (user_id, gender, age_group, occupation, valid_from)
        SELECT t.user_id, t.gender, t.age_group, t.occupation, t.changed_at FROM tmp_user t
        WHERE NOT EXISTS (SELECT 1 FROM dw.dim_user d WHERE d.user_id = t.user_id AND d.is_current)""")
    if closed:
        print(f"  SCD2: {closed} người dùng đổi thông tin -> đóng phiên bản cũ, thêm phiên bản mới")
    return cur.rowcount


# ------------------------------------------------------------------ facts
def fact_rating(cur, con):
    with run_log(cur, "load.fact_rating") as st:
        wm = watermark(cur, "fact_rating")
        # Đọc lùi LOOKBACK so với watermark: sự kiện CDC có thể đến bronze muộn (Kafka 3 partition,
        # consumer at-least-once), changed_at nhỏ hơn mốc đã nạp. Đọc lại phần chồng lấn không sao
        # vì upsert chỉ ghi đè khi bản mới hơn (điều kiện WHERE bên dưới).
        # Cùng 1 cặp (user, phim) có thể có cả rating MovieLens lẫn rating mới trên app:
        # giữ bản thay đổi gần nhất.
        df = con.execute(f"""
            SELECT * FROM {g('fact_rating')} WHERE changed_at > ?::TIMESTAMPTZ - INTERVAL {LOOKBACK}
            QUALIFY row_number() OVER (PARTITION BY user_id, movie_id ORDER BY changed_at DESC) = 1""", [wm]).df()
        st["rows_in"] = len(df)
        if df.empty:
            return
        copy_df(cur, df, "tmp_rating", """user_id int, movie_id int, rating smallint, rated_at timestamptz,
                source text, is_deleted boolean, changed_at timestamptz""")
        cur.execute("""
            INSERT INTO dw.fact_rating AS f (user_id, movie_id, user_key, movie_key, date_key, source_key,
                                             rating, rated_at, is_deleted, changed_at)
            SELECT t.user_id, t.movie_id, u.user_key, m.movie_key,
                   to_char(t.rated_at AT TIME ZONE 'UTC', 'YYYYMMDD')::int, s.source_key,
                   t.rating, t.rated_at, t.is_deleted, t.changed_at
            FROM tmp_rating t
            JOIN dw.dim_movie m USING (movie_id)
            JOIN dw.dim_source s ON s.source_name = t.source
            -- phiên bản người dùng có hiệu lực TẠI THỜI ĐIỂM chấm điểm (SCD2)
            JOIN dw.dim_user u ON u.user_id = t.user_id AND t.rated_at >= u.valid_from
                               AND (u.valid_to IS NULL OR t.rated_at < u.valid_to)
            ON CONFLICT (user_id, movie_id) DO UPDATE SET
                user_key = EXCLUDED.user_key, date_key = EXCLUDED.date_key, source_key = EXCLUDED.source_key,
                rating = EXCLUDED.rating, rated_at = EXCLUDED.rated_at, is_deleted = EXCLUDED.is_deleted,
                changed_at = EXCLUDED.changed_at, loaded_at = now()
            WHERE EXCLUDED.changed_at > f.changed_at""")
        st["rows_out"] = cur.rowcount
        # Watermark không bao giờ lùi; ghi trong cùng transaction với dữ liệu (commit ở main()).
        set_watermark(cur, "fact_rating", max(wm, df["changed_at"].max().to_pydatetime()))


def fact_imdb_rating_daily(cur, con):
    with run_log(cur, "load.fact_imdb_rating_daily") as st:
        df = con.execute(f"SELECT * FROM {g('fact_imdb_rating_daily')}").df()
        df["votes_delta"] = df["votes_delta"].astype("Int64")
        st["rows_in"] = len(df)
        copy_df(cur, df, "tmp_imdb", "movie_id int, snapshot_date date, imdb_rating numeric(3,1), imdb_votes int, votes_delta int")
        cur.execute("""
            INSERT INTO dw.fact_imdb_rating_daily (movie_key, date_key, imdb_rating, imdb_votes, votes_delta)
            SELECT m.movie_key, to_char(t.snapshot_date, 'YYYYMMDD')::int, t.imdb_rating, t.imdb_votes, t.votes_delta
            FROM tmp_imdb t JOIN dw.dim_movie m USING (movie_id)
            ON CONFLICT (movie_key, date_key) DO UPDATE SET
                imdb_rating = EXCLUDED.imdb_rating, imdb_votes = EXCLUDED.imdb_votes, votes_delta = EXCLUDED.votes_delta""")
        st["rows_out"] = cur.rowcount


def fact_pageviews_daily(cur, con):
    with run_log(cur, "load.fact_pageviews_daily") as st:
        if not lake.exists(lake.path("gold", "fact_pageviews_daily", "data.parquet")):
            return
        cur.execute("SELECT coalesce(max(full_date), '1900-01-01') FROM dw.fact_pageviews_daily JOIN dw.dim_date USING (date_key)")
        since = cur.fetchone()[0]
        # Lấy lại 2 ngày gần nhất vì số liệu ngày hôm qua có thể còn được Wikimedia cập nhật.
        df = con.execute(f"SELECT * FROM {g('fact_pageviews_daily')} WHERE view_date >= ?::DATE - 2", [since]).df()
        st["rows_in"] = len(df)
        copy_df(cur, df, "tmp_pv", "movie_id int, view_date date, views int")
        cur.execute("""
            INSERT INTO dw.fact_pageviews_daily (movie_key, date_key, views)
            SELECT m.movie_key, to_char(t.view_date, 'YYYYMMDD')::int, t.views
            FROM tmp_pv t JOIN dw.dim_movie m USING (movie_id)
            ON CONFLICT (movie_key, date_key) DO UPDATE SET views = EXCLUDED.views""")
        st["rows_out"] = cur.rowcount


def fact_wiki_edit(cur, con):
    with run_log(cur, "load.fact_wiki_edit") as st:
        df = con.execute(f"SELECT * FROM {g('fact_wiki_edit')}").df()
        st["rows_in"] = len(df)
        if df.empty:
            return
        copy_df(cur, df, "tmp_edit", "event_id text, movie_id int, wiki text, edited_at timestamptz, is_bot boolean, size_delta int")
        cur.execute("""
            INSERT INTO dw.fact_wiki_edit (event_id, movie_key, date_key, edited_at, wiki, is_bot, size_delta)
            SELECT t.event_id, m.movie_key, to_char(t.edited_at AT TIME ZONE 'UTC', 'YYYYMMDD')::int,
                   t.edited_at, t.wiki, t.is_bot, t.size_delta
            FROM tmp_edit t JOIN dw.dim_movie m USING (movie_id)
            ON CONFLICT (event_id) DO NOTHING""")
        st["rows_out"] = cur.rowcount


# Thứ tự quan trọng: bảng chiều trước, bảng sự kiện sau (fact cần khóa của dim).
STEPS = {f.__name__: f for f in [dim_movie, dim_user, fact_rating, fact_imdb_rating_daily,
                                  fact_pageviews_daily, fact_wiki_edit]}


def main(names):
    con = duck()
    with psycopg2.connect(config.dw_dsn()) as conn:
        cur = conn.cursor()
        for name in names or STEPS:
            STEPS[name](cur, con)
            conn.commit()


if __name__ == "__main__":
    main(sys.argv[1:])
