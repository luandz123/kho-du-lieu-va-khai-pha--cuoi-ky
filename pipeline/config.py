"""Cấu hình chung cho pipeline, đọc từ biến môi trường hoặc file .env.

LAKE_ROOT quyết định data lake nằm ở đâu:
  - "s3://lake"            -> MinIO (khi chạy bằng docker compose)
  - "D:/movie-data/lake"   -> thư mục trên máy (khi chưa bật MinIO)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_HOME = Path(os.getenv("DATA_HOME", "D:/movie-data"))
DOWNLOAD_DIR = DATA_HOME / "downloads"          # file tải về để dùng lại, không phải lake
LAKE_ROOT = os.getenv("LAKE_ROOT", (DATA_HOME / "lake").as_posix()).rstrip("/")

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET = os.getenv("S3_SECRET_KEY", "")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CONNECT_URL = os.getenv("CONNECT_URL", "http://localhost:8083")


def dw_dsn() -> str:
    """Kho dữ liệu mới (container dw, cổng 5433 trên máy)."""
    return (f"host={os.getenv('DW_HOST', '127.0.0.1')} port={os.getenv('DW_PORT', '5433')} "
            f"dbname=movie_dw user=dw password={os.getenv('DW_PASSWORD', '')}")


def app_dsn() -> str:
    """Database giao dịch của app xem phim (container app-db, cổng 5434 trên máy)."""
    return (f"host={os.getenv('APP_DB_HOST', '127.0.0.1')} port={os.getenv('APP_DB_PORT', '5434')} "
            f"dbname=movie_app user=app password={os.getenv('APP_DB_PASSWORD', '')}")


# Wikimedia phân loại client theo User-Agent (https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits):
#   không có thông tin liên hệ  -> 10 request/phút
#   có URL hoặc email liên hệ   -> 200 request/phút
# Muốn nhanh hơn: đặt trong .env, ví dụ
#   WIKIMEDIA_CONTACT=https://github.com/<tài-khoản>/<repo>
WIKIMEDIA_CONTACT = os.getenv("WIKIMEDIA_CONTACT", "").strip()
USER_AGENT = os.getenv(
    "HTTP_USER_AGENT",
    f"movielens-dw-student-project/1.0 ({WIKIMEDIA_CONTACT}; educational)" if WIKIMEDIA_CONTACT
    else "movielens-dw-student-project/1.0 (educational)")
# Khoảng cách tối thiểu giữa 2 request tới Wikimedia (giây), để không bị trả 429.
WIKIMEDIA_MIN_INTERVAL = float(os.getenv("WIKIMEDIA_MIN_INTERVAL", "0.35" if WIKIMEDIA_CONTACT else "6.5"))

ML1M_DIR = Path(os.getenv("ML1M_DIR", "data/raw/ml-1m"))
