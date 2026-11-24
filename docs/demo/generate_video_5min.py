"""Kịch bản quay video demo 5 phút hoàn chỉnh cho Movie Platform.
Tự động lồng tiếng AI Tiếng Việt (chuẩn giọng nam miền Bắc vi-VN-NamMinhNeural),
phụ đề đồng bộ chính xác từng mili-giây, hiệu ứng click và thẻ tiêu đề từng chương.
"""

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import wave

from dotenv import dotenv_values
import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "D:/movie-data/ms-playwright")

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "docs/demo"
AUDIO_DIR = DEMO_DIR / "audio_5min"
OUT_VIDEO = DEMO_DIR / "movie_platform_demo_5min.mp4"

APP_URL = "http://localhost:8501"
KAFKA_UI = "http://localhost:8080/ui/clusters/movie-platform/all-topics"
MINIO_URL = "http://localhost:9001"
AIRFLOW_URL = "http://localhost:8081"
SUPERSET_URL = "http://localhost:8089"

VIEWPORT = {"width": 1440, "height": 900}

env = dotenv_values(ROOT / ".env")
sup = dotenv_values(ROOT / "dashboard/superset/.env")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

OVERLAY_JS = """
window.__cap = (t) => {
  let d = document.getElementById('__cap');
  if (!d) {
    d = document.createElement('div');
    d.id = '__cap';
    Object.assign(d.style, {
      position: 'fixed',
      left: '50%',
      bottom: '24px',
      transform: 'translateX(-50%)',
      maxWidth: '1280px',
      width: 'auto',
      background: 'rgba(15, 23, 42, 0.92)',
      border: '1px solid rgba(56, 189, 248, 0.35)',
      color: '#f8fafc',
      font: '600 20px "Segoe UI", -apple-system, sans-serif',
      padding: '12px 28px',
      borderRadius: '14px',
      zIndex: 2147483647,
      textAlign: 'center',
      lineHeight: '1.45',
      pointerEvents: 'none',
      boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45)',
      letterSpacing: '0.2px',
      backdropFilter: 'blur(8px)',
      transition: 'opacity 0.2s ease-in-out'
    });
    document.documentElement.appendChild(d);
  }
  if (!t) {
    d.style.display = 'none';
  } else {
    d.innerHTML = t;
    d.style.display = 'block';
  }
};

document.addEventListener('click', (e) => {
  const r = document.createElement('div');
  Object.assign(r.style, {
    position: 'fixed',
    left: (e.clientX - 24) + 'px',
    top: (e.clientY - 24) + 'px',
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    border: '4px solid #38bdf8',
    backgroundColor: 'rgba(56, 189, 248, 0.25)',
    zIndex: 2147483647,
    pointerEvents: 'none',
    transition: 'all 0.65s ease-out',
    opacity: '1'
  });
  document.documentElement.appendChild(r);
  requestAnimationFrame(() => {
    r.style.transform = 'scale(2.0)';
    r.style.opacity = '0';
  });
  setTimeout(() => r.remove(), 700);
}, true);
"""


def get_audio_duration(path: Path) -> float:
    res = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, m_, s = m.groups()
        return int(h) * 3600 + int(m_) * 60 + float(s)
    return 0.0


def make_card_html(chapter_tag: str, title: str, subtitle: str, body: str = "") -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: radial-gradient(circle at 50% 40%, #1e293b 0%, #0f172a 100%);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #f8fafc;
    overflow: hidden;
  }}
  .tag {{
    font-size: 20px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: #38bdf8;
    margin-bottom: 14px;
    background: rgba(56, 189, 248, 0.12);
    padding: 6px 20px;
    border-radius: 9999px;
    border: 1px solid rgba(56, 189, 248, 0.35);
  }}
  .chapter-title {{
    font-size: 46px;
    font-weight: 800;
    letter-spacing: -0.5px;
    text-align: center;
    max-width: 1100px;
    line-height: 1.25;
    background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
  }}
  .sub {{
    font-size: 22px;
    color: #94a3b8;
    font-weight: 500;
    text-align: center;
  }}
  {body}
</style>
</head>
<body>
  <div class="tag">{chapter_tag}</div>
  <div class="chapter-title">{title}</div>
  <div class="sub">{subtitle}</div>
</body>
</html>"""


def make_table_html() -> str:
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    font-family: "Segoe UI", -apple-system, sans-serif;
    color: #f8fafc;
  }
  .header {
    text-align: center;
    margin-bottom: 24px;
  }
  h1 {
    font-size: 42px;
    margin: 0 0 6px 0;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  p {
    font-size: 20px;
    color: #94a3b8;
    margin: 0;
    font-weight: 500;
  }
  table {
    border-collapse: separate;
    border-spacing: 0;
    background: rgba(30, 41, 59, 0.85);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5);
    width: 1200px;
    font-size: 20px;
    border: 1px solid rgba(148, 163, 184, 0.2);
  }
  th {
    background: #1e3a8a;
    color: #f8fafc;
    padding: 16px 24px;
    text-align: left;
    font-weight: 700;
    font-size: 21px;
    letter-spacing: 0.5px;
    border-bottom: 2px solid #3b82f6;
  }
  td {
    padding: 18px 24px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    line-height: 1.5;
  }
  tr:last-child td {
    border-bottom: none;
  }
  tr:nth-child(even) td {
    background: rgba(15, 23, 42, 0.4);
  }
  .old-col {
    width: 42%;
    color: #f87171;
    font-weight: 600;
  }
  .new-col {
    width: 58%;
    color: #34d399;
    font-weight: 600;
  }
</style>
</head>
<body>
  <div class="header">
    <h1>Movie Platform · Bản nâng cấp</h1>
    <p>Kho dữ liệu và Khai phá dữ liệu · Nhóm Luận – Hùng</p>
  </div>
  <table>
    <tr>
      <th>Thầy góp ý (bản cũ)</th>
      <th>Bản mới sửa đúng 4 điểm</th>
    </tr>
    <tr>
      <td class="old-col">❌ Chỉ 1 nguồn (MovieLens, file tĩnh)</td>
      <td class="new-col">✅ 7 nguồn · 4 kiểu nạp: file, API, CDC, streaming</td>
    </tr>
    <tr>
      <td class="old-col">❌ Không có data lake</td>
      <td class="new-col">✅ MinIO · 3 tầng bronze → silver → gold (DuckDB, Parquet)</td>
    </tr>
    <tr>
      <td class="old-col">❌ Không có CDC</td>
      <td class="new-col">✅ Debezium đọc WAL Postgres → Kafka</td>
    </tr>
    <tr>
      <td class="old-col">❌ Demo bằng terminal</td>
      <td class="new-col">✅ App Streamlit + Airflow + Dashboard Superset</td>
    </tr>
  </table>
</body>
</html>"""


def make_diagram_html() -> str:
    return """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: #0b1120;
    font-family: "Segoe UI", sans-serif;
    color: #f8fafc;
    overflow: hidden;
  }
  .pipeline-header {
    margin-bottom: 12px;
    font-size: 24px;
    font-weight: 700;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    padding: 8px 24px;
    border-radius: 9999px;
    border: 1px solid rgba(56, 189, 248, 0.3);
    letter-spacing: 1px;
  }
  img {
    max-width: 95vw;
    max-height: 84vh;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    background: #ffffff;
    padding: 6px;
  }
</style>
</head>
<body>
  <div class="pipeline-header">Nguồn → Nạp → Data lake → Kho → Khai thác</div>
  <img src="flow.png">
</body>
</html>"""


def main():
    print("=== BẮT ĐẦU QUY TRÌNH QUAY VIDEO DEMO 5 PHÚT ===", flush=True)
    tmp = DEMO_DIR / "temp_render_5min"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    video_tmp = tmp / "raw_video"
    video_tmp.mkdir(parents=True, exist_ok=True)

    # 1. Tạo các trang HTML
    (tmp / "intro_table.html").write_text(make_table_html(), encoding="utf-8")
    shutil.copy(ROOT / "docs/movie_platform_dataflow.png", tmp / "flow.png")
    (tmp / "diagram.html").write_text(make_diagram_html(), encoding="utf-8")

    titles = {
        "c1": ("Chương 1", "Mở đầu: Bản cũ thiếu gì, bản mới sửa gì", "So sánh đóng góp mới so với buổi bảo vệ trước"),
        "c2": ("Chương 2", "Kiến trúc tổng thể", "5 cột dữ liệu: Nguồn → Nạp → Lake → Kho → Khai thác"),
        "c4": ("Chương 4", "Bắt thay đổi dữ liệu (CDC) & Mô hình gợi ý", "Debezium đọc WAL Postgres → Kafka → Lake → Kho"),
        "c6": ("Chương 6", "Data Lake trên MinIO", "3 tầng Medallion: Bronze → Silver → Gold"),
        "c8": ("Chương 8", "Điều phối Airflow & Dashboard Superset", "Tự động hóa luồng dữ liệu và trực quan hóa phân tích"),
        "c9": ("Chương 9", "Trí tuệ nhân tạo (AI)", "Gợi ý Hybrid & Tìm kiếm phim bằng ngữ nghĩa tiếng Việt"),
        "c10": ("Chương 10", "Streaming thời gian thực & Kết luận", "Luồng sự kiện Wikipedia và tổng kết hệ thống"),
    }
    for k, (tag, t, s) in titles.items():
        (tmp / f"title_{k}.html").write_text(make_card_html(tag, t, s), encoding="utf-8")

    (tmp / "end.html").write_text(
        make_card_html("KẾT THÚC", "Cảm ơn thầy đã theo dõi", "Movie Platform · Đề tài Kho dữ liệu và Khai phá dữ liệu"),
        encoding="utf-8",
    )

    audio_timeline = []  # danh sách tuple (start_sec, audio_path)

    with sync_playwright() as p:
        print("[1/4] Khởi động trình duyệt Chrome và chuẩn bị phiên đăng nhập...", flush=True)
        browser = p.chromium.launch(channel="chrome")

        # Đăng nhập ngầm MinIO để không quay màn hình login
        pre = browser.new_context(viewport=VIEWPORT)
        pg = pre.new_page()
        pg.goto(f"{MINIO_URL}/login")
        pg.fill("#accessKey", env["S3_ACCESS_KEY"])
        pg.fill("#secretKey", env["S3_SECRET_KEY"])
        pg.keyboard.press("Enter")
        pg.wait_for_url(re.compile(r".*/browser.*"), timeout=30000)
        pg.goto(APP_URL)
        pg.get_by_text("Mã người dùng").first.wait_for(timeout=120000)
        pg.wait_for_timeout(4000)
        state = pre.storage_state()
        pre.close()

        # Context quay video
        ctx = browser.new_context(
            viewport=VIEWPORT,
            storage_state=state,
            record_video_dir=str(video_tmp),
            record_video_size=VIEWPORT,
        )
        ctx.add_init_script(OVERLAY_JS)
        page = ctx.new_page()

        video_start_time = time.time()

        def speak(audio_key: str, cap_text: str = "", extra_wait: float = 0.5):
            audio_path = AUDIO_DIR / f"{audio_key}.mp3"
            dur = get_audio_duration(audio_path)
            now_sec = time.time() - video_start_time
            audio_timeline.append((now_sec, audio_path))
            if cap_text:
                page.evaluate("t => window.__cap && window.__cap(t)", cap_text)
            else:
                page.evaluate("t => window.__cap && window.__cap('')", "")
            page.wait_for_timeout(int((dur + extra_wait) * 1000))

        def goto(url: str, settle: int = 1500):
            page.goto(url)
            page.wait_for_timeout(settle)

        def login_background(url: str, user: str, pwd: str):
            helper = ctx.new_page()
            helper.goto(f"{url}/login/")
            helper.fill("#username", user)
            helper.fill("#password", pwd)
            helper.keyboard.press("Enter")
            helper.wait_for_url(lambda u: "/login" not in u, timeout=30000)
            helper.close()

        print("[2/4] Tiến hành quay từng cảnh theo kịch bản...", flush=True)

        # === CHƯƠNG 1 ===
        print("-> Chương 1", flush=True)
        goto((tmp / "title_c1.html").as_uri(), 600)
        speak("t_c1", extra_wait=0.2)

        goto((tmp / "intro_table.html").as_uri(), 800)
        speak(
            "c1_1",
            "Ở buổi bảo vệ trước, thầy góp ý 4 điểm thiếu: chỉ 1 nguồn tĩnh, không có data lake, không có CDC, demo terminal. "
            "Bản nâng cấp sửa đúng 4 điểm đó và làm thêm: nạp tăng dần, Airflow, gợi ý hybrid.",
            extra_wait=0.8,
        )

        # === CHƯƠNG 2 ===
        print("-> Chương 2", flush=True)
        goto((tmp / "title_c2.html").as_uri(), 600)
        speak("t_c2", extra_wait=0.2)

        goto((tmp / "diagram.html").as_uri(), 800)
        speak(
            "c2_1_p1",
            "Cột 1 là nguồn (4 kiểu): File (MovieLens & IMDb), API (Wikipedia & Wikidata), "
            "CDC (Database App xem phim), và Streaming thời gian thực.",
            extra_wait=0.4,
        )
        speak(
            "c2_1_p2",
            "Cột 2: Nạp (Airflow, Kafka) → Cột 3: Data Lake MinIO 3 tầng (DuckDB) → "
            "Cột 4: Kho Postgres + pgvector → Cột 5: Superset & App Streamlit.",
            extra_wait=0.8,
        )

        # === CHƯƠNG 4 & 7: HÀNH TRÌNH CDC & PIPELINE LIÊN TỤC TRÊN APP ===
        print("-> Chương 4 & 7 (App CDC end-to-end)", flush=True)
        goto((tmp / "title_c4.html").as_uri(), 600)
        speak("t_c4", extra_wait=0.2)

        goto(APP_URL, 4000)
        page.get_by_role("tab", name="Chấm điểm").click()
        page.wait_for_timeout(2000)

        # Cảnh 4.1: Tạo user mới và chấm 5★ 2 phim
        audio_path_41 = AUDIO_DIR / "c4_1_p1.mp3"
        dur_41 = get_audio_duration(audio_path_41)
        audio_timeline.append((time.time() - video_start_time, audio_path_41))
        page.evaluate(
            "t => window.__cap && window.__cap(t)",
            "<b>App xem phim</b>: Tạo người dùng mới chưa có lịch sử, rồi chấm 5★ cho <b>Toy Story</b> và <b>Toy Story 2</b>.",
        )

        page.get_by_role("button", name=re.compile("Tạo người dùng mới")).first.click()
        page.wait_for_timeout(2500)
        page.get_by_role("button", name="Chấm", exact=True).nth(0).click()
        page.wait_for_timeout(2500)
        page.get_by_role("button", name="Chấm", exact=True).nth(1).click()
        page.wait_for_timeout(int(max(500, (dur_41 - 5.5) * 1000)))

        # Đoạn 4.1 p2: theo dõi Debezium
        speak(
            "c4_1_p2",
            "Mỗi thao tác INSERT vào Postgres của app. <b>Debezium</b> tự đọc WAL → <b>Kafka</b> → "
            "consumer gom micro-batch 10s → ghi xuống <b>MinIO bronze</b>.",
            extra_wait=0.2,
        )
        # Đợi hiển thị tên file bronze trong panel
        page.get_by_text("app_cdc/ratings/ingest_date").wait_for(timeout=60000)
        page.wait_for_timeout(2500)

        # Cảnh 7.2: Bấm Chạy pipeline ngay TRONG CÙNG PHIÊN APP
        audio_path_71 = AUDIO_DIR / "c7_2_p1.mp3"
        dur_71 = get_audio_duration(audio_path_71)
        audio_timeline.append((time.time() - video_start_time, audio_path_71))
        page.evaluate(
            "t => window.__cap && window.__cap(t)",
            "Bấm <b>Chạy pipeline ngay</b>: Airflow chạy 4 bước (bronze → silver → gold → nạp kho → 9 kiểm tra chất lượng). "
            "Chỉ ~30 giây là rating đã vào kho.",
        )
        page.get_by_role("button", name=re.compile("Chạy pipeline ngay")).click()
        page.wait_for_timeout(int(dur_71 * 1000))

        # Đợi pipeline hoàn tất
        page.get_by_text("Thay đổi đã vào kho sau").wait_for(timeout=180000)
        page.wait_for_timeout(2000)

        # Cuộn xuống xem gợi ý Trước và Sau
        page.get_by_text("Sau (phim mới").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        speak(
            "c7_2_p2",
            "Gợi ý <b>Trước</b>: phim phổ biến. <b>Sau</b> khi chấm 2 phim hoạt hình: toàn bộ 5 gợi ý đổi sang "
            "phim hoạt hình và gia đình (nhãn <b>MỚI</b>).",
            extra_wait=1.5,
        )

        # === CHƯƠNG 4.2: KIỂM CHỨNG KAFKA UI ===
        print("-> Chương 4.2 (Kafka UI)", flush=True)
        goto(f"{KAFKA_UI}/app.public.ratings/messages?seekDirection=BACKWARD&seekType=LATEST", 3500)
        page.locator("tbody tr").first.locator("td").first.click()
        page.wait_for_timeout(1000)
        page.evaluate("document.body.style.zoom = '1.2'")
        speak(
            "c4_2",
            "<b>Kafka UI</b>: Message Debezium có <code>op: 'c'</code> (thêm mới), <code>before: null</code>, "
            "<code>after</code> là dữ liệu mới, <code>lsn</code> để sắp thứ tự và khử trùng.",
            extra_wait=1.0,
        )
        page.evaluate("document.body.style.zoom = '1.0'")

        # === CHƯƠNG 6: DATA LAKE MINIO ===
        print("-> Chương 6 (MinIO Lake)", flush=True)
        goto((tmp / "title_c6.html").as_uri(), 600)
        speak("t_c6", extra_wait=0.2)

        goto(f"{MINIO_URL}/browser/lake", 4000)
        for name in ["bronze", "app_cdc", "ratings"]:
            page.get_by_text(name, exact=True).first.click()
            page.wait_for_timeout(1800)
        page.get_by_text(re.compile(r"^ingest_date=")).last.click()
        page.wait_for_timeout(2000)
        # Bấm Last Modified 2 lần
        page.get_by_text("Last Modified", exact=True).click()
        page.wait_for_timeout(600)
        page.get_by_text("Last Modified", exact=True).click()
        page.wait_for_timeout(1000)

        speak(
            "c6_1",
            "<b>MinIO</b> (Data Lake S3): Tầng <b>bronze</b> giữ dữ liệu thô. "
            "File vừa xuất hiện chính là micro-batch chứa 2 rating vừa chấm.",
            extra_wait=1.0,
        )

        # === CHƯƠNG 8: AIRFLOW & SUPERSET ===
        print("-> Chương 8 (Airflow & Superset)", flush=True)
        goto((tmp / "title_c8.html").as_uri(), 600)
        speak("t_c8", extra_wait=0.2)

        login_background(AIRFLOW_URL, "admin", env["AIRFLOW_ADMIN_PASSWORD"])
        goto(f"{AIRFLOW_URL}/dags/movie_incremental/grid", 3500)
        speak(
            "c8_1",
            "<b>Airflow</b>: DAG <code>movie_incremental</code> chạy mỗi 15 phút. 4 task đều xanh. "
            "Airflow điều phối, DuckDB và Postgres xử lý dữ liệu nặng.",
            extra_wait=1.0,
        )

        login_background(SUPERSET_URL, "btl_admin", sup["ADMIN_PASSWORD"])
        goto(f"{SUPERSET_URL}/superset/dashboard/movie-platform/", 8000)
        audio_path_82 = AUDIO_DIR / "c8_2.mp3"
        dur_82 = get_audio_duration(audio_path_82)
        audio_timeline.append((time.time() - video_start_time, audio_path_82))
        page.evaluate(
            "t => window.__cap && window.__cap(t)",
            "<b>Superset</b> đọc kho qua tài khoản chỉ đọc: rating mới từ CDC, lượt xem Wikipedia Home Alone, "
            "so sánh điểm Pokémon, giám sát pipeline.",
        )

        page.mouse.move(720, 500)
        scroll_steps = 8
        step_wait = (dur_82 / scroll_steps) * 1000
        for _ in range(scroll_steps):
            page.mouse.wheel(0, 110)
            page.wait_for_timeout(int(step_wait))
        page.wait_for_timeout(800)

        # === CHƯƠNG 9: PHẦN AI & TÌM PHIM TIẾNG VIỆT ===
        print("-> Chương 9 (AI Semantic Search)", flush=True)
        goto((tmp / "title_c9.html").as_uri(), 600)
        speak("t_c9", extra_wait=0.2)

        goto(APP_URL, 4000)
        page.get_by_role("tab", name="Tìm phim theo mô tả").click()
        page.wait_for_timeout(2000)

        box = page.get_by_label("Mô tả", exact=True)
        box.click()
        box.press("Control+A")
        box.press("Backspace")
        box.type("phim kinh dị về cá mập", delay=65)
        box.press("Enter")
        page.wait_for_timeout(3500)

        speak(
            "c9_1_p1",
            "Mỗi phim được mã hóa vector 384 chiều bằng <code>multilingual-e5-small</code> lưu trong Postgres qua <code>pgvector</code>.",
            extra_wait=0.6,
        )

        box.click()
        box.press("Control+A")
        box.press("Backspace")
        box.type("tàu chìm, chuyện tình trên biển", delay=65)
        box.press("Enter")
        page.wait_for_timeout(3500)

        speak(
            "c9_1_p2",
            "Câu tiếng Việt tìm ra <b>Jaws</b> và <b>Titanic</b> nhờ vector đa ngôn ngữ và chỉ mục HNSW, "
            "dù mô tả gốc trên Wikipedia viết bằng tiếng Anh.",
            extra_wait=1.0,
        )

        # === CHƯƠNG 10: STREAMING THỜI GIAN THỰC & KẾT LUẬN ===
        print("-> Chương 10 (Streaming & Kết luận)", flush=True)
        goto((tmp / "title_c10.html").as_uri(), 600)
        speak("t_c10", extra_wait=0.2)

        goto(f"{KAFKA_UI}/wiki.recentchange/messages?seekDirection=TAILING&seekType=LATEST", 3000)
        speak(
            "c10_1",
            "<b>Streaming thật</b>: Producer đọc luồng Wikimedia EventStreams thời gian thực, lọc sửa bài Wikipedia, "
            "nạp vào <code>fact_wiki_edit</code>.",
            extra_wait=1.0,
        )

        goto((tmp / "diagram.html").as_uri(), 600)
        speak(
            "c10_2",
            "Tóm lại: 7 nguồn, 4 kiểu nạp, lake 3 tầng, kho tăng dần SCD2, 9 kiểm tra chất lượng, Airflow & AI ngữ nghĩa. "
            "Em xin cảm ơn thầy đã theo dõi!",
            extra_wait=0.5,
        )

        goto((tmp / "end.html").as_uri(), 2500)
        page.evaluate("t => window.__cap && window.__cap('')", "")
        page.wait_for_timeout(2000)

        raw_video_path = page.video.path()
        ctx.close()
        browser.close()

    print("[3/4] Trình duyệt đã ghi hình xong. Tổng hợp âm thanh đồng bộ...", flush=True)
    # Đo độ dài video đã quay
    res = subprocess.run([FFMPEG, "-i", raw_video_path], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    total_video_sec = 0.0
    if m:
        h, m_, s = m.groups()
        total_video_sec = int(h) * 3600 + int(m_) * 60 + float(s)
    print(f"-> Độ dài video thô: {total_video_sec:.2f} giây", flush=True)

    # Tạo buffer âm thanh PCM stereo 44.1kHz
    SAMPLE_RATE = 44100
    total_samples = int((total_video_sec + 2.0) * SAMPLE_RATE)
    master_audio = np.zeros((total_samples, 2), dtype=np.int16)

    wav_cache = tmp / "wavs"
    wav_cache.mkdir(parents=True, exist_ok=True)

    for start_sec, mp3_file in audio_timeline:
        wav_file = wav_cache / f"{mp3_file.stem}.wav"
        if not wav_file.exists():
            subprocess.run(
                [FFMPEG, "-y", "-loglevel", "error", "-i", str(mp3_file), "-ar", str(SAMPLE_RATE), "-ac", "2", "-f", "wav", str(wav_file)],
                check=True,
            )
        with wave.open(str(wav_file), "rb") as w:
            n_frames = w.getnframes()
            data = np.frombuffer(w.readframes(n_frames), dtype=np.int16).reshape(-1, 2)
            start_idx = int(start_sec * SAMPLE_RATE)
            end_idx = start_idx + len(data)
            if end_idx <= total_samples:
                master_audio[start_idx:end_idx] = data
            elif start_idx < total_samples:
                fit_len = total_samples - start_idx
                master_audio[start_idx:] = data[:fit_len]

    master_wav = tmp / "master_soundtrack.wav"
    with wave.open(str(master_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(master_audio.tobytes())

    print("[4/4] Mux video và âm thanh bằng FFmpeg...", flush=True)
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-loglevel",
            "info",
            "-i",
            raw_video_path,
            "-i",
            str(master_wav),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "21",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(OUT_VIDEO),
        ],
        check=True,
    )

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"=== HOÀN TẤT: Video đã xuất ra tại {OUT_VIDEO} ===", flush=True)


if __name__ == "__main__":
    main()
