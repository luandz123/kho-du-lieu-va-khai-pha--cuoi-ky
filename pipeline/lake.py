"""Đọc/ghi data lake 3 tầng: bronze -> silver -> gold.

Quy ước đường dẫn:
  bronze/<nguồn>/<bảng>/ingest_date=YYYY-MM-DD/<file gốc>      dữ liệu thô, không sửa
  silver/<bảng>/...parquet                                      đã làm sạch, ép kiểu
  gold/<bảng>/...parquet                                        sẵn sàng nạp kho

Dùng fsspec nên cùng một code chạy được cho thư mục trên máy và MinIO (s3://).
"""
from datetime import date, datetime, timezone
import json

import fsspec

from pipeline import config


def filesystem():
    if config.LAKE_ROOT.startswith("s3://"):
        return fsspec.filesystem(
            "s3",
            key=config.S3_KEY,
            secret=config.S3_SECRET,
            client_kwargs={"endpoint_url": config.S3_ENDPOINT},
        )
    return fsspec.filesystem("file", auto_mkdir=True)


def path(*parts: str) -> str:
    return "/".join([config.LAKE_ROOT, *[p.strip("/") for p in parts]])


def bronze_path(source: str, table: str, filename: str, ingest_date: date | None = None) -> str:
    d = (ingest_date or datetime.now(timezone.utc).date()).isoformat()
    return path("bronze", source, table, f"ingest_date={d}", filename)


def put_file(local_file, target: str) -> str:
    fs = filesystem()
    fs.put(str(local_file), target)
    return target


def put_bytes(data: bytes, target: str) -> str:
    fs = filesystem()
    with fs.open(target, "wb") as f:
        f.write(data)
    return target


def put_json_lines(records, target: str) -> int:
    n = 0
    fs = filesystem()
    with fs.open(target, "wb") as f:
        for r in records:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode("utf-8"))
            n += 1
    return n


def exists(target: str) -> bool:
    return filesystem().exists(target)


def latest_partition(source: str, table: str) -> str | None:
    """Thư mục ingest_date mới nhất của một bảng bronze (None nếu chưa có)."""
    fs = filesystem()
    base = path("bronze", source, table)
    if not fs.exists(base):
        return None
    parts = sorted(p for p in fs.ls(base, detail=False) if "ingest_date=" in p)
    return parts[-1] if parts else None
