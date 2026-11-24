"""Theo dõi 1 thay đổi trên DB app đi qua từng chặng của pipeline:

  Postgres app → Kafka (Debezium) → MinIO bronze (consumer) → Airflow → kho dữ liệu

Mỗi hàm chỉ ĐỌC (không commit offset Kafka, không ghi gì), trả về None nếu chặng đó chưa tới.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
import uuid

from confluent_kafka import Consumer, TopicPartition
import psycopg2
import requests

from pipeline import config, lake

AIRFLOW = os.getenv("AIRFLOW_URL", "http://localhost:8081")
DAG = "movie_incremental"
TOLERANCE = timedelta(seconds=5)   # lệch giờ cho phép giữa app, Postgres và Debezium


@dataclass
class Change:
    table: str                 # "ratings" | "users"
    action: str                # mô tả cho người xem, vd "INSERT 5★ Toy Story"
    user_id: int
    movie_id: int | None
    at: datetime               # thời điểm (UTC) app ghi vào Postgres
    kafka: dict | None = None
    bronze: dict | None = None
    airflow: dict | None = None
    dw: dict | None = None
    recs_before: list = field(default_factory=list)
    recs_after: list | None = None

    def key_matches(self, row: dict | None) -> bool:
        if not row or row.get("user_id") != self.user_id:
            return False
        return self.table == "users" or row.get("movie_id") == self.movie_id


# ------------------------------------------------------------------ Kafka
def find_in_kafka(ch: Change, lookback: int = 500) -> dict | None:
    """Đọc ~lookback message cuối của mỗi partition, tìm sự kiện Debezium khớp khóa và thời điểm."""
    topic = f"app.public.{ch.table}"
    c = Consumer({"bootstrap.servers": config.KAFKA_BOOTSTRAP, "group.id": f"journey-{uuid.uuid4()}",
                  "enable.auto.commit": False, "auto.offset.reset": "earliest"})
    try:
        meta = c.list_topics(topic, timeout=5).topics.get(topic)
        if meta is None:
            return None
        ends, assign = {}, []
        for p in meta.partitions:
            low, high = c.get_watermark_offsets(TopicPartition(topic, p), timeout=5)
            if high > low:
                ends[p] = high
                assign.append(TopicPartition(topic, p, max(low, high - lookback)))
        if not assign:
            return None
        c.assign(assign)
        min_ms = (ch.at - TOLERANCE).timestamp() * 1000
        best, done = None, set()
        while len(done) < len(ends):
            msg = c.poll(2.0)
            if msg is None:
                break
            if msg.error() or msg.value() is None:
                continue
            if msg.offset() >= ends[msg.partition()] - 1:
                done.add(msg.partition())
            v = json.loads(msg.value())
            row = v.get("after") or v.get("before")
            if v.get("ts_ms", 0) >= min_ms and ch.key_matches(row):
                best = {"partition": msg.partition(), "offset": msg.offset(), "op": v["op"],
                        "at": datetime.fromtimestamp(v["ts_ms"] / 1000, timezone.utc), "topic": topic}
        return best
    finally:
        c.close()


# ------------------------------------------------------------------ MinIO bronze
def find_in_bronze(ch: Change) -> dict | None:
    """Tìm file JSONL mà consumer đã ghi chứa đúng partition/offset của sự kiện."""
    k = ch.kafka
    fs = lake.filesystem()
    day = k["at"].date().isoformat()
    folder = lake.path("bronze", "app_cdc", ch.table, f"ingest_date={day}")
    fs.invalidate_cache()  # s3fs nhớ danh sách thư mục từ lần gọi trước -> không thấy file mới
    if not fs.exists(folder):
        return None
    since = (k["at"] - TOLERANCE).strftime("%Y%m%dT%H%M%S")
    files = sorted((f for f in fs.ls(folder, detail=False) if f.rsplit("/", 1)[-1] >= since), reverse=True)
    for f in files[:20]:
        with fs.open(f, "rb") as fh:
            for line in fh:
                meta = json.loads(line).get("_kafka", {})
                if meta.get("partition") == k["partition"] and meta.get("offset") == k["offset"]:
                    name = f.rsplit("/", 1)[-1]
                    written = datetime.strptime(name[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                    return {"path": f.split("bronze/", 1)[-1], "at": written}
    return None


# ------------------------------------------------------------------ Airflow
def airflow_run(after: datetime) -> dict | None:
    """Lần chạy movie_incremental đầu tiên bắt đầu SAU khi file bronze đã có."""
    auth = ("admin", os.getenv("AIRFLOW_ADMIN_PASSWORD", ""))
    r = requests.get(f"{AIRFLOW}/api/v1/dags/{DAG}/dagRuns", params={"order_by": "-start_date", "limit": 10},
                     auth=auth, timeout=10)
    r.raise_for_status()
    runs = [x for x in r.json()["dag_runs"]
            if x.get("start_date") and datetime.fromisoformat(x["start_date"]) >= after]
    if not runs:
        return None
    run = min(runs, key=lambda x: x["start_date"])
    ti = requests.get(f"{AIRFLOW}/api/v1/dags/{DAG}/dagRuns/{run['dag_run_id']}/taskInstances",
                      auth=auth, timeout=10).json()["task_instances"]
    ok = [t for t in ti if t["state"] == "success"]
    running = [t["task_id"] for t in ti if t["state"] in ("running", "queued", "up_for_retry")]
    failed = [t["task_id"] for t in ti if t["state"] == "failed"]
    return {"run_id": run["dag_run_id"], "state": run["state"], "done": len(ok), "total": len(ti),
            "running": running[0] if running else None, "failed": failed,
            "at": datetime.fromisoformat(run["start_date"])}   # giờ bắt đầu: trước lúc nạp kho


def trigger_pipeline() -> str:
    r = requests.post(f"{AIRFLOW}/api/v1/dags/{DAG}/dagRuns", json={},
                      auth=("admin", os.getenv("AIRFLOW_ADMIN_PASSWORD", "")), timeout=15)
    r.raise_for_status()
    return r.json()["dag_run_id"]


# ------------------------------------------------------------------ kho
def find_in_dw(ch: Change) -> dict | None:
    since = ch.at - TOLERANCE
    with psycopg2.connect(config.dw_dsn()) as conn, conn.cursor() as cur:
        if ch.table == "ratings":
            cur.execute("""SELECT rating, is_deleted, loaded_at FROM dw.fact_rating
                           WHERE user_id = %s AND movie_id = %s AND changed_at >= %s""",
                        (ch.user_id, ch.movie_id, since))
            row = cur.fetchone()
            if row:
                state = "is_deleted = true" if row[1] else f"rating = {row[0]}"
                return {"detail": f"dw.fact_rating: {state}", "at": row[2]}
        else:
            cur.execute("""SELECT occupation, valid_from, user_key FROM dw.dim_user
                           WHERE user_id = %s AND valid_from >= %s ORDER BY valid_from DESC LIMIT 1""",
                        (ch.user_id, since))
            row = cur.fetchone()
            if row:
                cur.execute("SELECT count(*) FROM dw.dim_user WHERE user_id = %s", (ch.user_id,))
                n = cur.fetchone()[0]
                return {"detail": f"dw.dim_user: phiên bản mới '{row[0]}' (user_key {row[2]}), "
                                  f"tổng {n} phiên bản", "at": row[1]}
    return None


def advance(ch: Change) -> None:
    """Kiểm tra lần lượt các chặng chưa xong; dừng ở chặng đầu tiên chưa tới."""
    if ch.kafka is None:
        ch.kafka = find_in_kafka(ch)
        if ch.kafka is None:
            return
    if ch.bronze is None:
        ch.bronze = find_in_bronze(ch)
        if ch.bronze is None:
            return
    if ch.airflow is None or ch.airflow["state"] != "success":
        ch.airflow = airflow_run(ch.bronze["at"])
        if ch.airflow is None or ch.airflow["state"] != "success":
            return
    if ch.dw is None:
        ch.dw = find_in_dw(ch)
