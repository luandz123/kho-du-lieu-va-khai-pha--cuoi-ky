"""Kết nối DuckDB dùng chung cho các bước bronze -> silver -> gold.

DuckDB đọc/ghi thẳng CSV, TSV.gz, JSON, Parquet trên thư mục máy hoặc MinIO (S3)
bằng SQL, nên không cần Spark cho dữ liệu cỡ vài GB.
"""
from urllib.parse import urlparse

import duckdb

from pipeline import config, lake


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order = false")
    if config.LAKE_ROOT.startswith("s3://"):
        ep = urlparse(config.S3_ENDPOINT)
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"""
            CREATE SECRET lake (TYPE S3, KEY_ID '{config.S3_KEY}', SECRET '{config.S3_SECRET}',
                                ENDPOINT '{ep.netloc}', URL_STYLE 'path', USE_SSL {str(ep.scheme == 'https').lower()})
        """)
    return con


def latest(source: str, table: str, filename: str) -> str:
    part = lake.latest_partition(source, table)
    if part is None:
        raise RuntimeError(f"Chưa có bronze/{source}/{table}")
    if config.LAKE_ROOT.startswith("s3://") and not part.startswith("s3://"):
        part = "s3://" + part
    return f"{part}/{filename}"


def all_partitions(source: str, table: str, pattern: str = "*") -> str:
    """Glob đọc mọi ngày đã nạp, ví dụ để xem lịch sử title.ratings theo ngày."""
    return lake.path("bronze", source, table, "ingest_date=*", pattern)


def has_files(pattern: str) -> bool:
    return bool(lake.filesystem().glob(pattern.removeprefix("s3://")))


def imdb_tsv(path: str) -> str:
    """Biểu thức đọc file TSV của IMDb: không có ký tự trích dẫn, giá trị rỗng ghi là \\N."""
    return (f"read_csv('{path}', delim='\t', quote='', escape='', header=true, "
            r"nullstr='\N', all_varchar=true)")


def write_parquet(con, sql: str, layer: str, table: str) -> int:
    """Ghi kết quả câu SQL thành <layer>/<table>/data.parquet, trả về số dòng."""
    target = lake.path(layer, table, "data.parquet")
    fs = lake.filesystem()
    if not config.LAKE_ROOT.startswith("s3://"):
        fs.makedirs(lake.path(layer, table), exist_ok=True)
    con.execute(f"COPY ({sql}) TO '{target}' (FORMAT parquet, COMPRESSION zstd)")
    n = con.execute(f"SELECT count(*) FROM read_parquet('{target}')").fetchone()[0]
    print(f"{layer} <- {table}: {n:,} dòng")
    return n
