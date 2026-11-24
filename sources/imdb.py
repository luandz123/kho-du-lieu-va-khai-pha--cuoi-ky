"""Nguồn 2: IMDb Non-Commercial Datasets (https://data.imdb.com/non-commercial-datasets/).

File TSV nén gzip, IMDb cập nhật lại hằng ngày. Giấy phép: chỉ dùng cá nhân, phi thương mại.

- title.ratings  (~9 MB):  tải MỖI NGÀY -> theo dõi điểm và số vote thay đổi theo ngày.
- title.basics, title.crew, title.principals, name.basics: thông tin phim, đạo diễn,
  diễn viên. Ít thay đổi nên chỉ tải khi chưa có hoặc khi chạy với --full.

Chạy:
  python -m sources.imdb            # chỉ title.ratings của hôm nay
  python -m sources.imdb --full     # tải đủ 5 file
"""
import argparse
from datetime import datetime, timezone

from pipeline import config, lake
from sources.web import download

BASE = "https://datasets.imdbws.com"
DAILY = ["title.ratings"]
STATIC = ["title.basics", "title.crew", "title.principals", "name.basics"]


def ingest(name: str, *, refresh: bool) -> str:
    today = datetime.now(timezone.utc).date()
    # File tải về được đặt tên theo ngày để mỗi ngày giữ một bản riêng.
    local = config.DOWNLOAD_DIR / "imdb" / today.isoformat() / f"{name}.tsv.gz"
    download(f"{BASE}/{name}.tsv.gz", local, refresh=refresh)
    target = lake.bronze_path("imdb", name.replace(".", "_"), f"{name}.tsv.gz", today)
    lake.put_file(local, target)
    print("bronze <-", target)
    return target


def main(full: bool = False):
    for name in DAILY:
        ingest(name, refresh=False)
    for name in STATIC:
        if full or lake.latest_partition("imdb", name.replace(".", "_")) is None:
            ingest(name, refresh=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="tải lại cả các file ít thay đổi")
    main(ap.parse_args().full)
