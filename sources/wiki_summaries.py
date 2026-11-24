"""Nguồn 5: đoạn tóm tắt (phần mở đầu) và ảnh đại diện (thường là poster) bài Wikipedia
của từng phim, tiếng Anh và tiếng Việt.

Dùng cho phần AI:
  - gợi ý theo nội dung (content-based): phim có mô tả giống nhau thì gần nhau;
  - tìm phim bằng câu mô tả tự do (embedding + pgvector).

MediaWiki Action API cho lấy phần mở đầu của tối đa 20 bài trong 1 request
(prop=extracts&exintro&exlimit=20), nên ~3.700 phim chỉ cần ~190 request.

Chạy: python -m sources.wiki_summaries
"""
from datetime import datetime, timezone

import pyarrow.parquet as pq

from pipeline import lake
from sources.web import get

BATCH = 20


def fetch(wiki: str, titles: list[str]) -> dict[str, dict]:
    r = get(f"https://{wiki}.wikipedia.org/w/api.php", params={
        "action": "query", "prop": "extracts|pageimages", "piprop": "thumbnail", "pithumbsize": 300,
        "pilicense": "any",   # poster phim thường là ảnh không tự do (fair use), mặc định API bỏ qua
        "pilimit": BATCH, "exintro": 1, "explaintext": 1, "exlimit": BATCH,
        "redirects": 1, "format": "json", "formatversion": 2, "titles": "|".join(titles)}, timeout=60)
    r.raise_for_status()
    q = r.json().get("query", {})
    # Bài bị chuyển hướng: map tên gốc -> tên đích để trả kết quả theo tên đã hỏi.
    redirect = {x["to"]: x["from"] for x in q.get("redirects", [])}
    norm = {x["to"]: x["from"] for x in q.get("normalized", [])}
    out = {}
    for page in q.get("pages", []):
        if page.get("extract") or page.get("thumbnail"):
            title = redirect.get(page["title"], page["title"])
            out[norm.get(title, title)] = {"extract": page.get("extract"),
                                           "image": (page.get("thumbnail") or {}).get("source")}
    return out


def main():
    with lake.filesystem().open(lake.path("silver", "wiki_links", "data.parquet"), "rb") as f:
        links = pq.read_table(f, columns=["imdb_id", "enwiki_title", "viwiki_title"]).to_pylist()
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for wiki, col in [("en", "enwiki_title"), ("vi", "viwiki_title")]:
        by_title = {r[col]: r["imdb_id"] for r in links if r[col]}
        titles = list(by_title)
        for i in range(0, len(titles), BATCH):
            for title, page in fetch(wiki, titles[i:i + BATCH]).items():
                if title in by_title:
                    rows.append({"imdb_id": by_title[title], "lang": wiki, "title": title,
                                 "extract": page["extract"], "image": page["image"], "fetched_at": fetched_at})
            if (i // BATCH) % 20 == 0:
                print(f"  {wiki}wiki: {min(i + BATCH, len(titles))}/{len(titles)} bài")
    target = lake.bronze_path("wikimedia", "summaries", "summaries.jsonl")
    n = lake.put_json_lines(rows, target)
    print("bronze <-", target, f"({n} đoạn tóm tắt)")


if __name__ == "__main__":
    main()
