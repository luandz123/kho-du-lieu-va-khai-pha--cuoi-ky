"""Đăng ký Debezium connector cho DB app (chạy 1 lần sau khi docker compose up).

Debezium đọc WAL của Postgres qua replication slot 'debezium_app' và đẩy mỗi thay đổi
của bảng ratings, users thành 1 message vào Kafka:
  topic app.public.ratings, app.public.users

Chạy: python -m cdc.register
"""
import json
import os
from pathlib import Path

import requests

from pipeline import config


def main():
    spec = json.loads(Path(__file__).with_name("debezium-app.json").read_text(encoding="utf-8"))
    spec["config"]["database.password"] = os.environ["APP_DB_PASSWORD"]
    name = spec["name"]
    url = f"{config.CONNECT_URL}/connectors/{name}/config"
    r = requests.put(url, json=spec["config"], timeout=30)  # PUT = tạo mới hoặc cập nhật
    r.raise_for_status()
    status = requests.get(f"{config.CONNECT_URL}/connectors/{name}/status", timeout=30).json()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
