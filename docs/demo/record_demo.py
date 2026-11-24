"""Quay video demo bản nâng cấp (có phụ đề tiếng Việt) bằng Playwright + Chrome có sẵn trên máy.

Kịch bản: giới thiệu → sơ đồ → app: tạo người dùng mới, chấm 2 phim, panel theo dõi CDC → chạy pipeline →
gợi ý trước/sau → Kafka UI → MinIO → Airflow → Superset → tìm phim tiếng Việt → streaming Wikipedia.

Yêu cầu trước khi chạy:
  docker compose up -d                       (kho, app DB, Kafka, Debezium, MinIO, Airflow, consumer, producer)
  docker compose -f dashboard/superset/compose.yaml --env-file dashboard/superset/.env up -d
  streamlit run app/streamlit_app.py         (cổng 8501)

Chạy: python docs/demo/record_demo.py      -> docs/demo/movie_platform_demo.mp4
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import os

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "D:/movie-data/ms-playwright")  # bộ ghi video của Playwright
from dotenv import dotenv_values  # noqa: E402
import imageio_ffmpeg  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "movie_platform_demo.mp4"
APP = "http://localhost:8501"
KAFKA_UI = "http://localhost:8080/ui/clusters/movie-platform/all-topics"
MINIO, AIRFLOW, SUPERSET = "http://localhost:9001", "http://localhost:8081", "http://localhost:8089"
SIZE = {"width": 1440, "height": 900}
env = dotenv_values(ROOT / ".env")
sup = dotenv_values(ROOT / "dashboard/superset/.env")

# Phụ đề ở đáy màn hình + vòng tròn đánh dấu chỗ bấm (video Playwright không có con trỏ chuột).
OVERLAY_JS = """
window.__cap = (t) => {
  let d = document.getElementById('__cap');
  if (!d) {
    d = document.createElement('div'); d.id = '__cap';
    Object.assign(d.style, {position:'fixed', left:'50%', bottom:'26px', transform:'translateX(-50%)',
      maxWidth:'1240px', background:'rgba(17,24,39,.9)', color:'#fff', font:'600 21px "Segoe UI", sans-serif',
      padding:'12px 24px', borderRadius:'12px', zIndex:2147483647, textAlign:'center', lineHeight:'1.45',
      pointerEvents:'none', boxShadow:'0 6px 24px rgba(0,0,0,.25)'});
    document.documentElement.appendChild(d);
  }
  d.innerHTML = t; d.style.display = t ? 'block' : 'none';
};
document.addEventListener('click', (e) => {
  const r = document.createElement('div');
  Object.assign(r.style, {position:'fixed', left:(e.clientX-22)+'px', top:(e.clientY-22)+'px', width:'44px',
    height:'44px', borderRadius:'50%', border:'4px solid #ef4444', zIndex:2147483647, pointerEvents:'none',
    transition:'all .6s ease-out', opacity:'1'});
  document.documentElement.appendChild(r);
  requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
  setTimeout(() => r.remove(), 700);
}, true);
"""


def card_html(title: str, body: str) -> str:
    return f"""<!doctype html><meta charset="utf-8"><style>
    body{{margin:0;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;
    font-family:"Segoe UI",sans-serif;background:linear-gradient(135deg,#eef2ff,#ffffff);color:#111827}}
    h1{{font-size:46px;margin:0 0 18px}} table{{border-collapse:collapse;font-size:21px;margin-top:10px}}
    td,th{{border-bottom:1px solid #d1d5db;padding:10px 18px;text-align:left}} th{{color:#4f46e5}}
    p{{font-size:22px;color:#4b5563;margin:4px}} img{{max-width:96vw;max-height:88vh}}</style>
    <h1>{title}</h1>{body}"""


INTRO = card_html("Movie Platform · bản nâng cấp", """
<p>Bài tập lớn Kho dữ liệu và Khai phá dữ liệu · nhóm Luận – Hùng</p>
<table><tr><th>Bản cũ (thầy góp ý)</th><th>Bản mới</th></tr>
<tr><td>Chỉ 1 nguồn (MovieLens, file tĩnh)</td><td>7 nguồn · 4 kiểu nạp: file, API, CDC, streaming</td></tr>
<tr><td>Không có data lake</td><td>MinIO · bronze → silver → gold (DuckDB, Parquet)</td></tr>
<tr><td>Không có CDC</td><td>Debezium đọc WAL Postgres → Kafka</td></tr>
<tr><td>Demo bằng terminal</td><td>App Streamlit + Airflow + dashboard Superset</td></tr></table>""")


def main():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "intro.html").write_text(INTRO, encoding="utf-8")
    shutil.copy(ROOT / "docs/movie_platform_dataflow.png", tmp / "flow.png")
    (tmp / "flow.html").write_text(card_html("", '<img src="flow.png">'), encoding="utf-8")
    (tmp / "end.html").write_text(card_html("Cảm ơn thầy đã theo dõi", "<p>Movie Platform · bản nâng cấp</p>"),
                                  encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")

        # 1. Đăng nhập trước (không quay) để video không có màn hình đăng nhập; làm nóng app.
        pre = browser.new_context(viewport=SIZE)
        pg = pre.new_page()
        pg.goto(f"{MINIO}/login")
        pg.fill("#accessKey", env["S3_ACCESS_KEY"])
        pg.fill("#secretKey", env["S3_SECRET_KEY"])
        pg.keyboard.press("Enter")
        pg.wait_for_url(re.compile(r".*/browser.*"), timeout=30000)
        pg.goto(APP)
        pg.get_by_text("Mã người dùng").first.wait_for(timeout=120000)
        pg.wait_for_timeout(8000)
        state = pre.storage_state()
        pre.close()

        # 2. Quay
        ctx = browser.new_context(viewport=SIZE, storage_state=state,
                                  record_video_dir=str(tmp / "video"), record_video_size=SIZE)
        ctx.add_init_script(OVERLAY_JS)
        page = ctx.new_page()

        def cap(text, wait=0):
            page.evaluate("t => window.__cap && window.__cap(t)", text)
            if wait:
                page.wait_for_timeout(wait)

        def goto(url, settle=2500):
            page.goto(url)
            page.wait_for_timeout(settle)

        def login(url, user, password):
            """Airflow và Superset cùng dùng cookie `session` trên localhost, đăng nhập bên này làm mất phiên
            bên kia. Nên đăng nhập ở tab phụ (không đưa vào video) NGAY TRƯỚC khi mở từng trang."""
            helper = ctx.new_page()
            helper.goto(f"{url}/login/")
            helper.fill("#username", user)
            helper.fill("#password", password)
            helper.keyboard.press("Enter")
            helper.wait_for_url(lambda u: "/login" not in u, timeout=30000)
            helper.close()

        goto((tmp / "intro.html").as_uri(), 500)
        cap("Video demo phần cải tiến · chỉ trình bày những điểm mới so với bản đã bảo vệ", 9000)
        goto((tmp / "flow.html").as_uri(), 500)
        cap("Kiến trúc mới: 7 nguồn → Kafka / Airflow → data lake MinIO 3 tầng → kho Postgres + pgvector "
            "→ Superset và app", 12000)

        # --- App: CDC end-to-end
        goto(APP, 6000)
        page.get_by_role("tab", name="Chấm điểm").click()
        page.wait_for_timeout(2500)
        cap("<b>App xem phim</b> (Streamlit): mọi thao tác ghi thẳng vào <b>Postgres của app</b> — nguồn của CDC",
            4000)
        cap("Tạo người dùng mới → <b>INSERT</b> vào bảng <code>users</code>. Người mới chưa có lịch sử chấm điểm", 1500)
        page.get_by_role("button", name=re.compile("Tạo người dùng mới")).first.click()
        page.wait_for_timeout(4000)
        cap("Người dùng mới chấm 5★ cho <b>Toy Story</b> và <b>Toy Story 2</b>", 1500)
        page.get_by_role("button", name="Chấm", exact=True).nth(0).click()
        page.wait_for_timeout(3500)
        page.get_by_role("button", name="Chấm", exact=True).nth(1).click()
        cap("Panel bên phải theo dõi thay đổi: <b>Debezium</b> đọc WAL → <b>Kafka</b> → consumer gom micro-batch "
            "10 giây → <b>MinIO bronze</b>")
        page.get_by_text("app_cdc/ratings/ingest_date").wait_for(timeout=60000)
        page.wait_for_timeout(4000)
        cap("Đã có trong data lake. Bấm <b>Chạy pipeline ngay</b> → Airflow chạy DAG <code>movie_incremental</code>", 1500)
        page.get_by_role("button", name=re.compile("Chạy pipeline ngay")).click()
        cap("Airflow: bronze → silver (bản mới nhất theo LSN) → gold → <b>nạp tăng dần</b> vào kho "
            "→ 9 kiểm tra chất lượng")
        page.get_by_text("Thay đổi đã vào kho sau").wait_for(timeout=180000)
        page.wait_for_timeout(2500)
        cap("Rating đã vào kho dữ liệu — cả hành trình chỉ mất vài chục giây", 4000)
        page.get_by_text("Sau (phim mới").scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        cap("Gợi ý <b>trước</b>: phim phổ biến. <b>Sau</b>: phim hoạt hình hợp sở thích vừa chấm (nhãn MỚI)", 9000)

        # --- Kiểm chứng trên từng hệ thống thật
        goto(f"{KAFKA_UI}/app.public.ratings/messages?seekDirection=BACKWARD&seekType=LATEST", 4000)
        cap("<b>Kafka UI</b>: 2 message Debezium mới nhất của người dùng vừa tạo — <code>op: c</code>, "
            "<code>before = null</code>, <code>after</code> là dòng mới", 1500)
        page.locator("tbody tr").first.locator("td").first.click()
        page.wait_for_timeout(7000)
        goto(f"{MINIO}/browser/lake", 5000)
        cap("<b>MinIO</b> (data lake): bucket <code>lake</code> có 3 tầng bronze / silver / gold", 3500)
        for name in ["bronze", "app_cdc", "ratings"]:
            page.get_by_text(name, exact=True).first.click()
            page.wait_for_timeout(2500)
        page.get_by_text(re.compile(r"^ingest_date=")).last.click()
        page.wait_for_timeout(2500)
        page.get_by_text("Last Modified", exact=True).click()   # bấm 2 lần: file mới nhất lên đầu
        page.wait_for_timeout(600)
        page.get_by_text("Last Modified", exact=True).click()
        page.wait_for_timeout(1500)
        cap("Tầng <b>bronze</b>: mỗi micro-batch của consumer là 1 file JSONL, giữ nguyên dữ liệu thô", 6000)
        login(AIRFLOW, "admin", env["AIRFLOW_ADMIN_PASSWORD"])
        goto(f"{AIRFLOW}/dags/movie_incremental/grid", 4000)
        cap("<b>Airflow</b>: DAG <code>movie_incremental</code> chạy mỗi 15 phút hoặc bấm tay — "
            "4 task đều xanh", 8000)
        login(SUPERSET, "btl_admin", sup["ADMIN_PASSWORD"])
        goto(f"{SUPERSET}/superset/dashboard/movie-platform/", 10000)
        cap("<b>Superset</b>: dashboard mới đọc kho — rating từ app qua CDC, phim đang được quan tâm "
            "(lượt xem Wikipedia), MovieLens so với IMDb", 9000)
        page.mouse.move(720, 520)
        for _ in range(7):
            page.mouse.wheel(0, 120)
            page.wait_for_timeout(120)
        cap("Giám sát pipeline và lịch sử phiên bản người dùng (SCD loại 2)", 6000)

        # --- AI: tìm phim bằng tiếng Việt
        goto(APP, 6000)
        page.get_by_role("tab", name="Tìm phim theo mô tả").click()
        page.wait_for_timeout(2000)
        cap("<b>Tìm phim bằng câu tiếng Việt</b>: embedding đa ngôn ngữ (multilingual-e5-small) + pgvector", 1500)
        box = page.get_by_label("Mô tả", exact=True)
        box.click()
        box.press("Control+A")
        box.press("Backspace")
        box.type("phim kinh dị về cá mập", delay=70)
        box.press("Enter")
        page.wait_for_timeout(7000)
        cap("Kết quả đầu tiên là <b>Jaws</b> — dù mô tả phim trên Wikipedia viết bằng tiếng Anh", 6000)

        # --- Streaming
        goto(f"{KAFKA_UI}/wiki.recentchange/messages?seekDirection=TAILING&seekType=LATEST", 3000)
        cap("<b>Streaming</b>: luồng sửa bài Wikipedia thời gian thực (Wikimedia EventStreams) chảy vào Kafka", 12000)

        goto((tmp / "end.html").as_uri(), 500)
        cap("", 3000)
        video = page.video.path()
        ctx.close()
        browser.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", video, "-c:v", "libx264", "-preset", "medium",
                    "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("->", OUT)


if __name__ == "__main__":
    main()
