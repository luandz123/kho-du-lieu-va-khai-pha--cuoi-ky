"""Nguồn 4: Wikimedia Pageviews API – lượt xem bài Wikipedia của từng phim.

Đây là chỉ số "độ quan tâm hiện tại" của phim, cập nhật theo giờ.
Endpoint: /metrics/pageviews/per-article/en.wikipedia/all-access/user/{bài}/{daily|hourly}/{từ}/{đến}

Wikimedia giới hạn tốc độ khá chặt với ứng dụng không đăng ký (bị trả 429 nếu gửi song song),
nên chỉ theo dõi N phim được chấm điểm nhiều nhất và gửi tuần tự từng request.

Chạy:
  python -m sources.pageviews --days 90            # lấy lại 90 ngày gần nhất (lần đầu)
  python -m sources.pageviews --days 3             # chạy hằng ngày
  python -m sources.pageviews --hourly --hours 48  # theo giờ, 48 giờ gần nhất
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from urllib.parse import quote

from pipeline import lake
from sources.web import get
from transform.duck import connect

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def tracked_articles(top: int) -> dict[str, str]:
    """IMDb ID -> tên bài Wikipedia tiếng Anh của `top` phim có nhiều rating nhất."""
    sql = f"""
        SELECT w.imdb_id, w.enwiki_title
        FROM read_parquet('{lake.path('silver', 'wiki_links', 'data.parquet')}') w
        JOIN read_parquet('{lake.path('silver', 'movies', 'data.parquet')}') m USING (imdb_id)
        JOIN (SELECT movie_id, count(*) AS n FROM read_parquet('{lake.path('silver', 'ratings', 'data.parquet')}')
              GROUP BY movie_id) r USING (movie_id)
        WHERE w.enwiki_title IS NOT NULL
        ORDER BY r.n DESC LIMIT {top}
    """
    return dict(connect().execute(sql).fetchall())


def fetch_one(imdb: str, article: str, granularity: str, start: str, end: str) -> list[dict]:
    url = f"{API}/{quote(article.replace(' ', '_'), safe='')}/{granularity}/{start}/{end}"
    r = get(url, timeout=30)
    if r.status_code == 404:  # bài không có lượt xem nào trong khoảng thời gian này
        return []
    r.raise_for_status()
    return [{"imdb": imdb, **item} for item in r.json().get("items", [])]


def main(granularity: str, start: datetime, end: datetime, top: int):
    fmt = "%Y%m%d00" if granularity == "daily" else "%Y%m%d%H"
    s, e = start.strftime(fmt), end.strftime(fmt)
    articles = tracked_articles(top)
    rows, errors = [], 0
    for k, (imdb, article) in enumerate(articles.items(), 1):
        try:
            rows.extend(fetch_one(imdb, article, granularity, s, e))
        except Exception:
            errors += 1
        if k % 50 == 0:
            print(f"  pageviews: {k}/{len(articles)} bài, {errors} lỗi")
    now = datetime.now(timezone.utc)
    target = lake.bronze_path("wikimedia", f"pageviews_{granularity}",
                              f"pageviews_{now:%Y%m%dT%H%M%S}.jsonl", now.date())
    n = lake.put_json_lines(rows, target)
    print("bronze <-", target, f"({n} dòng, {len(articles)} bài, {errors} lỗi)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hourly", action="store_true")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--top", type=int, default=500, help="số phim theo dõi (nhiều rating nhất)")
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    if a.hourly:
        main("hourly", now - timedelta(hours=a.hours), now, a.top)
    else:
        main("daily", now - timedelta(days=a.days), now - timedelta(days=1), a.top)
