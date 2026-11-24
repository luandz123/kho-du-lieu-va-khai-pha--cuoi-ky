"""Tầng silver: làm sạch, ép kiểu, ghép các nguồn với nhau. Ghi ra Parquet.

Bảng tạo ra:
  silver/users            người dùng ML-1M
  silver/movies           phim ML-1M + imdb_id (ghép bằng links.csv, thiếu thì theo tên + năm)
  silver/ratings          rating lịch sử ML-1M
  silver/imdb_movies      thông tin IMDb của các phim trên: thời lượng, đạo diễn, diễn viên
  silver/imdb_ratings     điểm IMDb theo từng ngày đã tải (mỗi ngày một bản chụp)
  silver/wiki_links       IMDb ID -> bài Wikipedia, quốc gia, số Oscar
  silver/pageviews        lượt xem Wikipedia theo ngày, bỏ trùng giữa các lần tải

Chạy: python -m transform.silver [tên bảng ...]
"""
import re
import sys
import unicodedata

import pandas as pd

from pipeline import lake
from transform.duck import all_partitions, connect, has_files, imdb_tsv, latest, write_parquet

ARTICLES = r",\s*(The|A|An|La|Le|Les|L'|Il|Lo|Das|Der|Die|El|Los|Las|Det|Den)$"


def _dat(path: str, columns: dict) -> str:
    """File .dat của ML-1M ngăn cách bằng '::' (users, ratings chỉ có ký tự ASCII)."""
    cols = ", ".join(f"'{k}': '{v}'" for k, v in columns.items())
    return (f"read_csv('{path}', delim='::', header=false, quote='', escape='', "
            f"columns={{{cols}}})")


def users(con):
    src = _dat(latest("movielens", "users", "users.dat"),
               {"user_id": "INTEGER", "gender": "VARCHAR", "age": "INTEGER", "occupation": "INTEGER", "zip": "VARCHAR"})
    return write_parquet(con, f"SELECT user_id, gender, age, occupation FROM {src}", "silver", "users")


def ratings(con):
    src = _dat(latest("movielens", "ratings", "ratings.dat"),
               {"user_id": "INTEGER", "movie_id": "INTEGER", "rating": "INTEGER", "ts": "BIGINT"})
    sql = f"""
        SELECT user_id, movie_id, rating, to_timestamp(ts) AS rated_at, 'movielens' AS source
        FROM {src} WHERE rating BETWEEN 1 AND 5
        QUALIFY row_number() OVER (PARTITION BY user_id, movie_id ORDER BY ts DESC) = 1
    """
    return write_parquet(con, sql, "silver", "ratings")


# ---------------------------------------------------------------- ghép phim với IMDb
def norm(title: str) -> str:
    t = re.sub(ARTICLES, lambda m: "", title.strip(), flags=re.I) if re.search(ARTICLES, title, re.I) else title
    art = re.search(ARTICLES, title.strip(), re.I)
    if art:
        t = f"{art.group(1)} {t}"
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = t.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def split_ml_title(raw: str) -> tuple[list[str], int | None]:
    """'City of Lost Children, The (Cité des enfants perdus, La) (1995)'
    -> (['the city of lost children', 'la cite des enfants perdus'], 1995)"""
    m = re.match(r"^(.*)\((\d{4})\)\s*$", raw.strip())
    title, year = (m.group(1).strip(), int(m.group(2))) if m else (raw, None)
    names = [title]
    alt = re.match(r"^(.*?)\s*\((.+)\)$", title)
    if alt:
        names = [alt.group(1), alt.group(2).removeprefix("a.k.a. ")]
    return [norm(n) for n in names if n], year


def movies(con):
    # movies.dat mã hóa latin-1 (tên phim có dấu tiếng Pháp, Đức...) nên đọc bằng pandas.
    with lake.filesystem().open(latest("movielens", "movies", "movies.dat"), "rb") as f:
        ml = pd.read_csv(f, sep="::", engine="python", header=None, encoding="latin-1",
                         names=["movie_id", "title", "genres"])
    links = con.execute(f"""
        SELECT movieId AS movie_id, 'tt' || lpad(imdbId::VARCHAR, 7, '0') AS imdb_id
        FROM read_csv('{latest("movielens", "links", "links.csv")}', header=true, all_varchar=false)
    """).df()
    ml = ml.merge(links, on="movie_id", how="left")
    ml["match_method"] = ml["imdb_id"].notna().map({True: "links", False: None})

    # Phim chưa có imdb_id: tìm trong IMDb phim cùng tên (đã chuẩn hóa) và năm lệch tối đa 1.
    basics = con.execute(f"""
        SELECT b.tconst, b.primaryTitle, b.originalTitle, TRY_CAST(b.startYear AS INT) AS year,
               coalesce(TRY_CAST(r.numVotes AS INT), 0) AS votes
        FROM {imdb_tsv(latest("imdb", "title_basics", "title.basics.tsv.gz"))} b
        LEFT JOIN {imdb_tsv(latest("imdb", "title_ratings", "title.ratings.tsv.gz"))} r USING (tconst)
        WHERE b.titleType IN ('movie', 'tvMovie', 'video') AND TRY_CAST(b.startYear AS INT) <= 2001
    """).df()
    index: dict[str, list] = {}
    for row in basics.itertuples(index=False):
        for t in {norm(row.primaryTitle or ""), norm(row.originalTitle or "")}:
            if t:
                index.setdefault(t, []).append(row)

    def find(raw):
        names, year = split_ml_title(raw)
        cands = [c for n in names for c in index.get(n, []) if year and c.year and abs(c.year - year) <= 1]
        if not cands:
            return None
        return max(cands, key=lambda c: (c.year == year, c.votes)).tconst

    miss = ml["imdb_id"].isna()
    ml.loc[miss, "imdb_id"] = ml.loc[miss, "title"].map(find)
    ml.loc[miss & ml["imdb_id"].notna(), "match_method"] = "title_year"

    ml["year"] = ml["title"].str.extract(r"\((\d{4})\)\s*$")[0].astype("Int64")
    ml["clean_title"] = ml["title"].str.replace(r"\s*\(\d{4}\)\s*$", "", regex=True)
    ml["genres"] = ml["genres"].str.split("|")
    con.register("ml_movies", ml[["movie_id", "clean_title", "year", "genres", "imdb_id", "match_method"]])
    n = write_parquet(con, "SELECT movie_id, clean_title AS title, year, genres, imdb_id, match_method FROM ml_movies",
                      "silver", "movies")
    stats = ml["match_method"].value_counts(dropna=False).to_dict()
    print(f"  ghép IMDb: {stats} trên tổng {len(ml)} phim")
    return n


def _movie_ids(con) -> str:
    return f"(SELECT imdb_id FROM read_parquet('{lake.path('silver', 'movies', 'data.parquet')}') WHERE imdb_id IS NOT NULL)"


def imdb_movies(con):
    ids = _movie_ids(con)
    b = imdb_tsv(latest("imdb", "title_basics", "title.basics.tsv.gz"))
    c = imdb_tsv(latest("imdb", "title_crew", "title.crew.tsv.gz"))
    p = imdb_tsv(latest("imdb", "title_principals", "title.principals.tsv.gz"))
    nm = imdb_tsv(latest("imdb", "name_basics", "name.basics.tsv.gz"))
    sql = f"""
        WITH m AS (SELECT * FROM {b} WHERE tconst IN {ids}),
        names AS (SELECT nconst, primaryName FROM {nm}),
        crew AS (
            SELECT tconst, unnest(string_split(directors, ',')) AS nconst,
                   generate_subscripts(string_split(directors, ','), 1) AS pos
            FROM {c} WHERE tconst IN {ids} AND directors IS NOT NULL),
        dirs AS (
            SELECT crew.tconst, list(n.primaryName ORDER BY crew.pos) AS directors
            FROM crew JOIN names n USING (nconst) GROUP BY crew.tconst),
        cast_ AS (
            SELECT p.tconst, list(n.primaryName ORDER BY TRY_CAST(p.ordering AS INT)) AS top_cast
            FROM {p} p JOIN names n USING (nconst)
            WHERE p.tconst IN {ids} AND p.category IN ('actor', 'actress')
              AND TRY_CAST(p.ordering AS INT) <= 6
            GROUP BY p.tconst)
        SELECT m.tconst AS imdb_id, m.primaryTitle AS imdb_title, m.originalTitle AS original_title,
               TRY_CAST(m.startYear AS INT) AS start_year, TRY_CAST(m.runtimeMinutes AS INT) AS runtime_minutes,
               string_split(m.genres, ',') AS imdb_genres, d.directors, c.top_cast
        FROM m LEFT JOIN dirs d USING (tconst) LEFT JOIN cast_ c USING (tconst)
    """
    return write_parquet(con, sql, "silver", "imdb_movies")


def imdb_ratings(con):
    """Mỗi lần tải title.ratings là một bản chụp; giữ tất cả để thấy điểm thay đổi theo ngày."""
    path = all_partitions("imdb", "title_ratings", "title.ratings.tsv.gz")
    sql = f"""
        SELECT tconst AS imdb_id,
               CAST(regexp_extract(filename, 'ingest_date=(\\d{{4}}-\\d{{2}}-\\d{{2}})', 1) AS DATE) AS snapshot_date,
               CAST(averageRating AS DECIMAL(3,1)) AS imdb_rating, CAST(numVotes AS INT) AS imdb_votes
        FROM read_csv('{path}', delim='\t', quote='', header=true, filename=true, all_varchar=true)
        WHERE tconst IN {_movie_ids(con)}
    """
    return write_parquet(con, sql, "silver", "imdb_ratings")


def wiki_links(con):
    sql = f"""
        SELECT imdb AS imdb_id, regexp_extract(film, 'Q\\d+$') AS wikidata_id,
               enwiki AS enwiki_title, viwiki AS viwiki_title,
               CASE WHEN countries = '' THEN [] ELSE string_split(countries, '|') END AS countries,
               CAST(oscar_wins AS INT) AS oscar_wins
        FROM read_json('{latest("wikidata", "film_links", "film_links.jsonl")}', format='newline_delimited')
        QUALIFY row_number() OVER (PARTITION BY imdb ORDER BY enwiki IS NULL, film) = 1
    """
    return write_parquet(con, sql, "silver", "wiki_links")


def pageviews(con):
    path = all_partitions("wikimedia", "pageviews_daily", "*.jsonl")
    sql = f"""
        SELECT imdb AS imdb_id, strptime(substr(timestamp, 1, 8), '%Y%m%d')::DATE AS view_date,
               max(views)::INT AS views
        FROM read_json('{path}', format='newline_delimited',
                       columns={{'imdb': 'VARCHAR', 'timestamp': 'VARCHAR', 'views': 'BIGINT'}})
        GROUP BY ALL
    """
    return write_parquet(con, sql, "silver", "pageviews")


# ---------------------------------------------------------------- dữ liệu CDC và streaming
def app_ratings(con):
    """Thay đổi rating từ app (Debezium). Một cặp (user, phim) có thể có nhiều sự kiện
    c/u/d, và consumer at-least-once có thể ghi trùng -> giữ sự kiện MỚI NHẤT theo LSN."""
    path = all_partitions("app_cdc", "ratings", "*.jsonl")
    if not has_files(path):
        sql = """SELECT NULL::INT user_id, NULL::INT movie_id, NULL::INT rating, NULL::TIMESTAMPTZ rated_at,
                        NULL::TIMESTAMPTZ changed_at, NULL::BOOLEAN is_deleted, NULL::VARCHAR op LIMIT 0"""
        return write_parquet(con, sql, "silver", "app_ratings")
    sql = f"""
        WITH ev AS (
            SELECT op, coalesce(after, before) AS row, source.lsn AS lsn, ts_ms
            FROM read_json('{path}', format='newline_delimited', union_by_name=true,
                columns={{'op': 'VARCHAR', 'ts_ms': 'BIGINT', 'source': 'STRUCT(lsn BIGINT)',
                          'before': 'STRUCT(user_id INT, movie_id INT, rating INT, created_at VARCHAR)',
                          'after':  'STRUCT(user_id INT, movie_id INT, rating INT, created_at VARCHAR)'}}))
        SELECT row.user_id, row.movie_id, row.rating,
               row.created_at::TIMESTAMPTZ AS rated_at, to_timestamp(ts_ms / 1000) AS changed_at,
               op = 'd' AS is_deleted, op
        FROM ev
        QUALIFY row_number() OVER (PARTITION BY row.user_id, row.movie_id ORDER BY lsn DESC, ts_ms DESC) = 1
    """
    return write_parquet(con, sql, "silver", "app_ratings")


def app_users(con):
    """Thay đổi thông tin người dùng từ app: lấy trạng thái mới nhất của mỗi user."""
    path = all_partitions("app_cdc", "users", "*.jsonl")
    if not has_files(path):
        sql = """SELECT NULL::INT user_id, NULL::VARCHAR gender, NULL::INT age, NULL::INT occupation,
                        NULL::TIMESTAMPTZ changed_at LIMIT 0"""
        return write_parquet(con, sql, "silver", "app_users")
    sql = f"""
        SELECT after.user_id, after.gender, after.age, after.occupation, to_timestamp(ts_ms / 1000) AS changed_at
        FROM read_json('{path}', format='newline_delimited',
             columns={{'op': 'VARCHAR', 'ts_ms': 'BIGINT', 'source': 'STRUCT(lsn BIGINT)',
                       'after': 'STRUCT(user_id INT, gender VARCHAR, age INT, occupation INT)'}})
        WHERE op IN ('c', 'u')          -- 'r' là bản chụp ban đầu, trùng với dữ liệu MovieLens
        QUALIFY row_number() OVER (PARTITION BY after.user_id ORDER BY source.lsn DESC) = 1
    """
    return write_parquet(con, sql, "silver", "app_users")


def wiki_edits(con):
    path = all_partitions("wikimedia", "edits", "*.jsonl")
    if not has_files(path):
        sql = """SELECT NULL::VARCHAR event_id, NULL::VARCHAR imdb_id, NULL::VARCHAR wiki, NULL::TIMESTAMPTZ edited_at,
                        NULL::BOOLEAN is_bot, NULL::INT size_delta LIMIT 0"""
        return write_parquet(con, sql, "silver", "wiki_edits")
    sql = f"""
        SELECT DISTINCT ON (event_id) event_id, imdb_id, wiki, edited_at::TIMESTAMPTZ AS edited_at, is_bot, size_delta
        FROM read_json('{path}', format='newline_delimited',
             columns={{'event_id': 'VARCHAR', 'imdb_id': 'VARCHAR', 'wiki': 'VARCHAR', 'edited_at': 'VARCHAR',
                       'is_bot': 'BOOLEAN', 'size_delta': 'INT'}})
    """
    return write_parquet(con, sql, "silver", "wiki_edits")


def summaries(con):
    """Đoạn mở đầu bài Wikipedia: mỗi phim tối đa 1 bản tiếng Anh + 1 bản tiếng Việt."""
    sql = f"""
        SELECT imdb_id,
               max(extract) FILTER (WHERE lang = 'en') AS summary_en,
               max(extract) FILTER (WHERE lang = 'vi') AS summary_vi,
               coalesce(max(image) FILTER (WHERE lang = 'en'), max(image) FILTER (WHERE lang = 'vi')) AS poster_url
        FROM read_json('{latest("wikimedia", "summaries", "summaries.jsonl")}', format='newline_delimited')
        GROUP BY imdb_id
    """
    return write_parquet(con, sql, "silver", "summaries")


STEPS = {"users": users, "ratings": ratings, "movies": movies, "imdb_movies": imdb_movies,
         "imdb_ratings": imdb_ratings, "wiki_links": wiki_links, "pageviews": pageviews,
         "app_ratings": app_ratings, "app_users": app_users, "wiki_edits": wiki_edits,
         "summaries": summaries}
# Các bước chạy thường xuyên (mỗi lần DAG chạy); các bước còn lại chỉ cần khi nguồn tĩnh thay đổi.
FREQUENT = ["imdb_ratings", "pageviews", "app_ratings", "app_users", "wiki_edits"]

if __name__ == "__main__":
    con = connect()
    for name in sys.argv[1:] or STEPS:
        STEPS[name](con)
