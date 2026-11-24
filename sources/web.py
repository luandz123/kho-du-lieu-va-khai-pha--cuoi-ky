"""Tải file qua HTTP có cache, thử lại và hiển thị tiến độ đơn giản."""
from pathlib import Path
import threading
import time
from urllib.parse import urlparse

import requests

from pipeline import config

session = requests.Session()
session.headers["User-Agent"] = config.USER_AGENT

WIKIMEDIA_HOSTS = ("wikimedia.org", "wikipedia.org", "wikidata.org")
_lock = threading.Lock()
_last_wikimedia = 0.0


def _throttle(url: str):
    """Giãn cách các request tới Wikimedia theo WIKIMEDIA_MIN_INTERVAL (dùng chung mọi luồng)."""
    global _last_wikimedia
    if not urlparse(url).hostname.endswith(WIKIMEDIA_HOSTS):
        return
    with _lock:
        wait = _last_wikimedia + config.WIKIMEDIA_MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_wikimedia = time.monotonic()


def get(url, *, params=None, headers=None, timeout=60, retries=6):
    """GET có thử lại khi lỗi mạng hoặc bị giới hạn tốc độ (429/5xx).
    Khi bị 429, chờ đúng số giây máy chủ yêu cầu trong header Retry-After."""
    for attempt in range(retries):
        wait = 2 ** attempt
        try:
            _throttle(url)
            r = session.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                retry_after = r.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    wait = max(wait, int(retry_after))
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            if attempt == retries - 1:
                raise
            time.sleep(min(wait, 120))


def download(url: str, dest: Path, *, refresh: bool = False) -> Path:
    """Tải url về dest. Đã có file thì dùng lại, trừ khi refresh=True."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not refresh:
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    with session.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done, last = 0, 0.0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total and time.time() - last > 5:
                    print(f"  {dest.name}: {done / total:.0%} ({done >> 20} / {total >> 20} MB)")
                    last = time.time()
    tmp.replace(dest)
    return dest
