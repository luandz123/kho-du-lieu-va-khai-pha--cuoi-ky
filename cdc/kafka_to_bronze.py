"""Consumer: đọc message từ Kafka, gom micro-batch, ghi xuống tầng bronze của data lake.

Dùng chung cho 2 luồng:
  - CDC từ DB app:        topic app.public.ratings, app.public.users  -> bronze/app_cdc/<bảng>/
  - Streaming Wikipedia:  topic wiki.movie_edits                       -> bronze/wikimedia/edits/
                          topic wiki.recentchange                      -> bronze/wikimedia/recentchange/

Mỗi batch (tối đa BATCH_SIZE message hoặc FLUSH_SECONDS giây) được ghi thành 1 file JSONL.
Offset Kafka chỉ được commit SAU KHI file đã ghi xong -> nếu consumer chết giữa chừng,
khởi động lại sẽ đọc lại từ offset cũ, không mất dữ liệu (at-least-once). Bản ghi trùng
được loại ở tầng silver (lấy bản mới nhất theo khóa + thời điểm thay đổi).

Chạy: python -m cdc.kafka_to_bronze
"""
from datetime import datetime, timezone
import json
import signal
import time

from confluent_kafka import Consumer

from pipeline import config, lake

TOPICS = {
    "app.public.ratings": ("app_cdc", "ratings"),
    "app.public.users": ("app_cdc", "users"),
    "wiki.movie_edits": ("wikimedia", "edits"),
    "wiki.recentchange": ("wikimedia", "recentchange"),
}
BATCH_SIZE = 500
FLUSH_SECONDS = 10

running = True


def stop(*_):
    global running
    running = False


def flush(buffers: dict) -> int:
    total = 0
    now = datetime.now(timezone.utc)
    for topic, records in buffers.items():
        if not records:
            continue
        source, table = TOPICS[topic]
        target = lake.bronze_path(source, table, f"{now:%Y%m%dT%H%M%S%f}.jsonl", now.date())
        total += lake.put_json_lines(records, target)
        print(f"bronze <- {target} ({len(records)} message)")
        records.clear()
    return total


def main():
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    consumer = Consumer({
        "bootstrap.servers": config.KAFKA_BOOTSTRAP,
        "group.id": "lake-bronze-writer",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe(list(TOPICS))
    buffers = {t: [] for t in TOPICS}
    last_flush = time.time()
    print("Đang nghe:", ", ".join(TOPICS))
    try:
        while running:
            msg = consumer.poll(1.0)
            if msg is not None and not msg.error() and msg.value():
                value = json.loads(msg.value())
                value["_kafka"] = {"topic": msg.topic(), "partition": msg.partition(), "offset": msg.offset()}
                buffers[msg.topic()].append(value)
            pending = sum(len(b) for b in buffers.values())
            if pending >= BATCH_SIZE or (pending and time.time() - last_flush >= FLUSH_SECONDS):
                flush(buffers)
                consumer.commit(asynchronous=False)
                last_flush = time.time()
    finally:
        if any(buffers.values()):
            flush(buffers)
            consumer.commit(asynchronous=False)
        consumer.close()


if __name__ == "__main__":
    main()
