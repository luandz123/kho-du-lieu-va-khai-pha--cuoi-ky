"""Producer streaming: Wikimedia EventStreams -> Kafka topic wiki.movie_edits.

https://stream.wikimedia.org/v2/stream/recentchange phát MỌI chỉnh sửa trên các trang
Wikimedia theo thời gian thực (vài chục sự kiện/giây). Producer chỉ giữ lại những lần sửa
bài Wikipedia (tiếng Anh/Việt) của các phim có trong kho, rồi đẩy vào Kafka.

Chạy: python -m streaming.wiki_producer
"""
import json
import signal
import time

from confluent_kafka import Producer
import pyarrow.parquet as pq
import requests

from pipeline import config, lake

STREAM = "https://stream.wikimedia.org/v2/stream/recentchange"
TOPIC = "wiki.movie_edits"        # chỉ bài về phim trong kho -> fact_wiki_edit
TOPIC_ALL = "wiki.recentchange"   # mọi lần sửa Wikipedia en/vi -> theo dõi luồng theo thời gian thực
running = True


def stop(*_):
    global running
    running = False


def watched_titles() -> dict[tuple[str, str], str]:
    """(wiki, tên bài) -> imdb_id, ví dụ ('enwiki', 'Inception') -> 'tt1375666'."""
    with lake.filesystem().open(lake.path("silver", "wiki_links", "data.parquet"), "rb") as f:
        rows = pq.read_table(f, columns=["imdb_id", "enwiki_title", "viwiki_title"]).to_pylist()
    out = {}
    for r in rows:
        if r["enwiki_title"]:
            out[("enwiki", r["enwiki_title"])] = r["imdb_id"]
        if r["viwiki_title"]:
            out[("viwiki", r["viwiki_title"])] = r["imdb_id"]
    return out


def main():
    signal.signal(signal.SIGINT, stop)
    titles = watched_titles()
    print(f"Theo dõi {len(titles)} bài Wikipedia về phim")
    producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP, "linger.ms": 200})
    seen = sent = edits = 0
    last_report = time.time()
    # Accept: application/json -> server trả mỗi sự kiện 1 dòng JSON (thay cho định dạng SSE).
    headers = {"User-Agent": config.USER_AGENT, "Accept": "application/json"}
    # Mất kết nối thì nối lại với ?since=<thời điểm sự kiện cuối đã nhận> để đọc tiếp, không mất sự kiện
    # (EventStreams cho phép đọc lại vài ngày gần nhất). Có thể nhận trùng vài sự kiện ở chỗ nối:
    # silver khử trùng theo event_id.
    last_dt = None
    while running:
        try:
            params = {"since": last_dt} if last_dt else None
            with requests.get(STREAM, headers=headers, params=params, stream=True, timeout=(10, 60)) as r:
                for line in r.iter_lines():
                    if not running:
                        break
                    if not line:
                        continue
                    ev = json.loads(line)
                    seen += 1
                    last_dt = ev.get("meta", {}).get("dt", last_dt)
                    if ev.get("wiki") not in ("enwiki", "viwiki") or ev.get("type") not in ("edit", "new"):
                        continue
                    length = ev.get("length") or {}
                    record = {
                        "event_id": ev["meta"]["id"], "wiki": ev["wiki"], "title": ev["title"],
                        "edited_at": ev["meta"]["dt"], "is_bot": ev.get("bot", False),
                        "size_delta": (length.get("new") or 0) - (length.get("old") or 0),
                    }
                    # Luồng chung: mọi lần sửa Wikipedia tiếng Anh/Việt (vài sự kiện mỗi giây).
                    producer.produce(TOPIC_ALL, key=ev["wiki"], value=json.dumps(record, ensure_ascii=False))
                    edits += 1
                    # Luồng lọc: chỉ bài về phim có trong kho.
                    imdb = titles.get((ev["wiki"], ev["title"]))
                    if imdb:
                        record["imdb_id"] = imdb
                        producer.produce(TOPIC, key=imdb, value=json.dumps(record, ensure_ascii=False))
                        sent += 1
                        print(f"PHIM [{record['edited_at']}] {record['wiki']}: {record['title']} ({record['size_delta']:+d} byte)")
                    if time.time() - last_report >= 30:
                        print(f"  {seen:,} sự kiện Wikimedia, {edits:,} lần sửa en/vi -> {TOPIC_ALL}, "
                              f"{sent} lần sửa bài phim -> {TOPIC}")
                        last_report = time.time()
                    producer.poll(0)
        except requests.RequestException as e:
            print(f"Mất kết nối EventStreams, nối lại từ {last_dt}:", e)
            time.sleep(2)
    producer.flush(10)


if __name__ == "__main__":
    main()
