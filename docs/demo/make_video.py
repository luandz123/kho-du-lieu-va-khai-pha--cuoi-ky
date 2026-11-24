"""Dựng video demo có lồng tiếng (≈ 5 phút) cho phần trình bày bản nâng cấp.

Khác record_demo.py (chỉ có phụ đề): video này có giọng đọc tiếng Việt, phụ đề khớp từng câu,
nhãn chương ở góc trên, phóng to vào JSON Kafka / file MinIO / panel hành trình.

Cách làm để hình và tiếng luôn khớp:
  1. Sinh trước mọi đoạn thoại bằng edge-tts (biết độ dài và mốc thời gian từng câu).
  2. Quay hệ thống thật bằng Playwright; mỗi lần gọi say(...) ghi lại mốc giây trong video,
     rồi chờ đọc xong mới thao tác tiếp. Thao tác chậm (chờ pipeline) chỉ làm dài video, không lệch tiếng.
  3. ffmpeg đặt từng đoạn thoại đúng mốc, đốt phụ đề ASS vào hình.

Yêu cầu: hệ thống đang chạy như trong docs/demo/kich_ban_video.md (Docker + Superset + Streamlit cổng 8501).
Chạy:  python docs/demo/make_video.py   ->  docs/demo/movie_platform_demo_longtieng.mp4
"""
import asyncio
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "D:/movie-data/ms-playwright")
from dotenv import dotenv_values  # noqa: E402
import edge_tts  # noqa: E402
import imageio_ffmpeg  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = HERE / "build_longtieng"
OUT = HERE / "movie_platform_demo_longtieng.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICE, RATE = "vi-VN-HoaiMyNeural", ""
SPEED = 1.12                                  # tăng tốc lúc ghép (edge-tts không còn nhận tham số rate)
APP = "http://localhost:8501"
KAFKA_UI = "http://localhost:8080/ui/clusters/movie-platform/all-topics"
MINIO, AIRFLOW, SUPERSET = "http://localhost:9001", "http://localhost:8081", "http://localhost:8089"
VIEW = {"width": 1440, "height": 900}
REC = VIEW                                    # Playwright quay đúng kích thước viewport; ffmpeg phóng lên 1920×1200
env = dotenv_values(ROOT / ".env")
sup = dotenv_values(ROOT / "dashboard/superset/.env")

# ---------------------------------------------------------------- lời thoại
LINES = {
    "intro": "Đây là phần trình bày bản nâng cấp của nhóm Luận và Hùng, đề tài phân tích xu hướng xem phim và gợi ý "
             "nội dung. Ở buổi bảo vệ trước, thầy góp ý bốn điểm: chỉ có một nguồn dữ liệu tĩnh, không có data lake, "
             "không có CDC, và demo chỉ chạy trên terminal. Bản này sửa đúng bốn điểm đó. Ngoài ra nhóm em làm thêm "
             "nạp kho tăng dần, điều phối bằng Airflow, và gợi ý phim kết hợp nội dung.",
    "d0": "Kiến trúc mới gồm năm cột, dữ liệu đi từ trái sang phải.",
    "d1": "Cột một là bảy nguồn với bốn kiểu nạp. Kiểu file: MovieLens và IMDb. Kiểu API: Wikidata, lượt xem và "
          "tóm tắt bài Wikipedia. Kiểu CDC: database của app xem phim do nhóm dựng. Và streaming: luồng sửa bài "
          "Wikipedia theo thời gian thực.",
    "d2": "Cột hai là tầng nạp. Dữ liệu batch do Airflow lấy theo lịch. Dữ liệu CDC và streaming đi qua Kafka, "
          "rồi một consumer gom thành micro-batch ghi xuống lake.",
    "d3": "Cột ba là data lake trên MinIO, chia ba tầng bronze, silver, gold, xử lý bằng DuckDB và lưu dạng Parquet.",
    "d4": "Cột bốn là kho Postgres theo lược đồ sao, nạp tăng dần, có SCD loại hai, và pgvector để lưu vector phim.",
    "d5": "Cột năm là khai thác: dashboard Superset và app Streamlit. Bây giờ em đi theo một thay đổi thật "
          "qua toàn bộ hệ thống.",
    "a1": "Đây là app xem phim. Em tạo một người dùng mới, chưa có lịch sử chấm điểm.",
    "a2": "Người này chấm năm sao cho Toy Story và Toy Story 2. Mỗi thao tác là một lệnh INSERT vào Postgres của "
          "app. App không gửi gì sang Kafka. Debezium tự đọc thay đổi từ nhật ký WAL của Postgres.",
    "a3": "Panel bên phải theo dõi thay đổi qua từng chặng: Postgres, Kafka, rồi data lake. Consumer gom "
          "micro-batch mười giây, nên chỉ vài giây sau, rating đã nằm ở tầng bronze.",
    "a4": "Em bấm chạy pipeline. Airflow chạy bốn bước: bronze sang silver, chỉ giữ bản mới nhất theo LSN. "
          "Silver sang gold. Nạp tăng dần vào kho. Cuối cùng là chín kiểm tra chất lượng.",
    "a5": "Nạp tăng dần nghĩa là mỗi lần chỉ đọc những thay đổi mới hơn mốc watermark, lùi lại một giờ để không sót "
          "sự kiện đến muộn, rồi upsert theo khóa. Chạy lại bao nhiêu lần cũng không nhân đôi dữ liệu.",
    "a6": "Chỉ khoảng nửa phút sau khi chấm, rating đã nằm trong kho. Bên dưới là gợi ý cho người dùng này. "
          "Trước khi chấm, vì chưa có lịch sử, hệ thống gợi ý phim phổ biến. Sau khi chấm hai phim hoạt hình, "
          "gợi ý đổi sang phim hoạt hình và gia đình. Dữ liệu mới đã đi hết đường ống, tới tận mô hình gợi ý.",
    "k1": "Bây giờ em kiểm chứng trên từng hệ thống. Đây là Kafka, topic app chấm public chấm ratings, "
          "message mới nhất là do Debezium gửi.",
    "k2": "Trường op bằng chữ c, nghĩa là thêm mới. Before rỗng, after là dòng vừa thêm. LSN là vị trí của thay đổi "
          "trong WAL, dùng để sắp đúng thứ tự và loại bản trùng. Nếu sửa điểm thì op là u, nếu xóa thì op là d.",
    "m1": "Đây là data lake MinIO, bucket lake có ba tầng bronze, silver và gold.",
    "m2": "Trong bronze, mỗi micro-batch của consumer là một file JSON lines, giữ nguyên dữ liệu thô. File mới nhất "
          "chứa hai rating vừa chấm. Consumer chỉ commit offset sau khi ghi file xong, nên không mất dữ liệu.",
    "f1": "Airflow có ba DAG. Movie incremental chạy mỗi mười lăm phút cho CDC và streaming. Movie daily chạy mỗi "
          "sáng, lấy điểm IMDb và lượt xem Wikipedia. Movie bootstrap chạy tay để nạp từ đầu. Lần chạy mới nhất "
          "là do nút trong app gọi API của Airflow, cả bốn task đều xanh.",
    "s1": "Dashboard Superset đọc thẳng từ kho bằng tài khoản chỉ có quyền đọc, tự làm mới mỗi sáu mươi giây. "
          "Có rating mới từ app qua CDC, phim đang được quan tâm theo lượt xem Wikipedia, và so sánh điểm "
          "MovieLens với IMDb.",
    "s2": "Phía dưới là giám sát pipeline, và lịch sử phiên bản người dùng theo SCD loại hai.",
    "ai1": "Phần AI. Mỗi phim được ghép thành một đoạn văn gồm tên, thể loại, mô tả Wikipedia, đạo diễn và diễn "
           "viên. Mô hình multilingual E5 biến đoạn văn đó thành vector ba trăm tám mươi tư chiều, lưu bằng pgvector.",
    "ai2": "Em gõ câu tiếng Việt: phim kinh dị về cá mập. Kết quả đầu tiên là Jaws, dù mô tả phim viết bằng "
           "tiếng Anh, vì mô hình học đa ngôn ngữ.",
    "ai3": "Thử câu khác: tàu chìm, chuyện tình trên biển. Kết quả là Titanic. Gợi ý hybrid cộng điểm CF với "
           "điểm nội dung này, nên gợi ý được cả cho người dùng mới.",
    "w1": "Cuối cùng là luồng streaming thật. Producer đọc luồng sửa bài Wikipedia theo thời gian thực, khoảng một "
          "đến ba sự kiện mỗi giây, rồi đẩy vào Kafka. Các lần sửa bài về phim có trong kho được nạp vào bảng "
          "fact wiki edit.",
    "end": "Tóm lại, bản nâng cấp có bảy nguồn với bốn kiểu nạp, CDC bằng Debezium và Kafka, data lake ba tầng, "
           "kho nạp tăng dần có SCD loại hai và chín kiểm tra chất lượng, Airflow điều phối, và tìm phim bằng ngữ "
           "nghĩa. Em xin cảm ơn thầy đã theo dõi.",
}
# Phụ đề hiển thị khác lời đọc ở vài chỗ (tên kỹ thuật viết đúng chính tả).
SUB_FIX = [("app chấm public chấm ratings", "app.public.ratings"), ("fact wiki edit", "fact_wiki_edit"),
           ("Movie incremental", "movie_incremental"), ("Movie daily", "movie_daily"),
           ("Movie bootstrap", "movie_bootstrap"), ("op bằng chữ c", "op = \"c\""), ("op là u", "op = \"u\""),
           ("op là d", "op = \"d\""), ("multilingual E5", "multilingual-e5-small")]


async def _tts(key: str, text: str):
    mp3, meta = BUILD / f"{key}.mp3", BUILD / f"{key}.json"
    if mp3.exists() and meta.exists() and json.loads(meta.read_text("utf-8")).get("key") == text + VOICE + RATE:
        return
    for attempt in range(30):   # dịch vụ thỉnh thoảng trả về rỗng: thử lại, giãn dần
        audio, sents = bytearray(), []
        try:
            async for ch in edge_tts.Communicate(text, VOICE, boundary="SentenceBoundary").stream():
                if ch["type"] == "audio":
                    audio += ch["data"]
                elif ch["type"] == "SentenceBoundary":
                    sents.append({"start": ch["offset"] / 1e7, "end": (ch["offset"] + ch["duration"]) / 1e7,
                                  "text": ch["text"]})
            break
        except edge_tts.exceptions.NoAudioReceived:
            print(f"  {key}: không nhận được tiếng, thử lại lần {attempt + 1}")
            await asyncio.sleep(2 + attempt % 5)
    else:
        raise RuntimeError(f"edge-tts lỗi ở đoạn {key}")
    mp3.write_bytes(bytes(audio))
    dur = probe_duration(mp3)
    meta.write_text(json.dumps({"key": text + VOICE + RATE, "text": text, "dur": dur, "sents": sents}, ensure_ascii=False), "utf-8")


def probe_duration(path: Path) -> float:
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def make_tts():
    BUILD.mkdir(exist_ok=True)

    async def run():
        for k, t in LINES.items():
            await _tts(k, t)
    asyncio.run(run())
    meta = {k: json.loads((BUILD / f"{k}.json").read_text("utf-8")) for k in LINES}
    for m in meta.values():   # quy đổi mọi mốc thời gian theo tốc độ đọc khi ghép
        m["dur"] /= SPEED
        for x in m["sents"]:
            x["start"] /= SPEED
            x["end"] /= SPEED
    return meta


# ---------------------------------------------------------------- trang tĩnh (thẻ mở đầu, sơ đồ)
BASE_CSS = """body{margin:0;height:100vh;overflow:hidden;font-family:"Segoe UI",sans-serif;color:#0f172a;
background:radial-gradient(circle at 20% 10%,#e0e7ff,#fff 55%)}"""

INTRO = f"""<!doctype html><meta charset="utf-8"><style>{BASE_CSS}
.wrap{{height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center}}
.tag{{color:#4f46e5;font-weight:700;letter-spacing:2px;font-size:15px}} h1{{font-size:50px;margin:8px 0 6px}}
.sub{{color:#475569;font-size:20px;margin-bottom:34px}}
table{{border-collapse:separate;border-spacing:0;font-size:21px;background:#fff;border-radius:14px;
box-shadow:0 10px 40px rgba(15,23,42,.12);overflow:hidden}}
th{{background:#0f172a;color:#fff;padding:14px 26px;text-align:left}} td{{padding:13px 26px;border-top:1px solid #e2e8f0}}
td:first-child{{color:#b91c1c}} td:last-child{{color:#15803d;font-weight:600}}
tr{{opacity:0;transform:translateY(12px);transition:all .5s}} tr.on{{opacity:1;transform:none}}</style>
<div class="wrap"><div class="tag">BẢN NÂNG CẤP · KHO DỮ LIỆU VÀ KHAI PHÁ DỮ LIỆU</div>
<h1>Movie Platform</h1><div class="sub">Phân tích xu hướng xem phim và gợi ý nội dung · nhóm Luận – Hùng</div>
<table><tr class="on"><th>Thầy góp ý (bản cũ)</th><th>Bản nâng cấp</th></tr>
<tr><td>Chỉ 1 nguồn, file tĩnh</td><td>7 nguồn · 4 kiểu nạp: file, API, CDC, streaming</td></tr>
<tr><td>Không có data lake</td><td>MinIO · bronze → silver → gold</td></tr>
<tr><td>Không có CDC</td><td>Debezium đọc WAL Postgres → Kafka</td></tr>
<tr><td>Demo bằng terminal</td><td>App web · Airflow · dashboard Superset</td></tr>
<tr><td>Nạp lại toàn bộ, chạy tay</td><td>Nạp tăng dần · SCD2 · 9 kiểm tra · 3 DAG</td></tr>
<tr><td>Chỉ CF</td><td>Hybrid CF + nội dung · tìm phim bằng tiếng Việt</td></tr></table></div>
<script>window.reveal=i=>document.querySelectorAll('tr')[i].classList.add('on')</script>"""

# Vùng trên sơ đồ (tỉ lệ theo ảnh 2000×1140): x0, y0, x1, y1
REGIONS = {"d1": (0.02, 0.10, 0.225, 0.75), "d2": (0.235, 0.10, 0.385, 0.80), "d3": (0.395, 0.10, 0.575, 0.80),
           "d4": (0.585, 0.10, 0.80, 0.80), "d5": (0.815, 0.10, 0.985, 0.78)}
HILITE = [(0.043, 0.502, 0.215, 0.618), (0.249, 0.494, 0.371, 0.70), (0.403, 0.138, 0.567, 0.79),
          (0.598, 0.138, 0.794, 0.65), (0.249, 0.805, 0.793, 0.878)]

FLOW = f"""<!doctype html><meta charset="utf-8"><style>{BASE_CSS}
body{{background:#fff}} #stage{{position:absolute;left:0;top:0;width:1440px;height:821px;margin-top:40px;
transform-origin:0 0;transition:transform 1.3s cubic-bezier(.4,0,.2,1)}} #stage img{{width:100%;height:100%}}
.hl{{position:absolute;border:4px solid #f97316;border-radius:12px;opacity:0;transition:opacity .6s}} .hl.on{{opacity:1;animation:pulse 1.6s infinite}}
@keyframes pulse{{50%{{box-shadow:0 0 0 6px rgba(249,115,22,.25)}}}}</style>
<div id="stage"><img src="flow.png"></div>
<script>
const W=1440,H=821,VW=1440,VH=900,TOP=40;
window.zoom=(r)=>{{const s=document.getElementById('stage');
 if(!r){{s.style.transform='none';return}}
 const [x0,y0,x1,y1]=r, w=(x1-x0)*W, h=(y1-y0)*H, k=Math.min(VW*0.94/w,(VH-150)*0.96/h,2.6);
 const cx=(x0+x1)/2*W, cy=(y0+y1)/2*H+TOP;
 s.style.transform=`translate(${{VW/2-cx*k}}px,${{(VH-110)/2-cy*k+TOP*(k-1)*0}}px) scale(${{k}})`;}};
window.hilite=(boxes)=>{{const s=document.getElementById('stage');
 boxes.forEach((b,i)=>{{const d=document.createElement('div');d.className='hl';
  Object.assign(d.style,{{left:b[0]*W+'px',top:b[1]*H+'px',width:(b[2]-b[0])*W+'px',height:(b[3]-b[1])*H+'px'}});
  s.appendChild(d);setTimeout(()=>d.classList.add('on'),i*700);}});}};
</script>"""

# Vòng tròn đỏ ở chỗ bấm (video Playwright không có con trỏ) + hàm phóng to 1 phần tử.
INIT_JS = """
document.addEventListener('click', (e) => {
  const r = document.createElement('div');
  Object.assign(r.style, {position:'fixed', left:(e.clientX-22)+'px', top:(e.clientY-22)+'px', width:'44px',
    height:'44px', borderRadius:'50%', border:'4px solid #ef4444', zIndex:2147483647, pointerEvents:'none',
    transition:'all .6s ease-out'});
  document.documentElement.appendChild(r);
  requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
  setTimeout(() => r.remove(), 700);
}, true);
window.__focus = (el, maxK) => {
  const h = document.documentElement;
  h.style.transition = 'transform 1s cubic-bezier(.4,0,.2,1)'; h.style.transformOrigin = '0 0';
  if (!el) { h.style.transform = 'none'; return; }
  const b = el.getBoundingClientRect(), VW = innerWidth, VH = innerHeight - 120;
  const k = Math.min(maxK, VW * 0.92 / b.width, VH * 0.92 / b.height);
  const cx = b.left + b.width / 2, cy = b.top + Math.min(b.height, VH / k) / 2;
  h.style.transform = `translate(${VW / 2 - cx * k}px, ${VH / 2 - cy * k}px) scale(${k})`;
};
"""


# ---------------------------------------------------------------- quay
class Recorder:
    def __init__(self, page, meta):
        self.page, self.meta = page, meta
        self.t0 = time.monotonic()
        self.cues, self.chapters = [], []
        self.busy_until = 0.0

    def now(self):
        return time.monotonic() - self.t0

    def chapter(self, name):
        self.chapters.append((self.now(), name))

    def say(self, key, wait=True):
        """Bắt đầu đọc đoạn `key` (chờ đoạn trước đọc xong). wait=True: chờ đọc xong mới trả về."""
        self.pause_until(self.busy_until + 0.35)
        start = self.now()
        self.cues.append((start, key))
        self.busy_until = start + self.meta[key]["dur"]
        if wait:
            self.pause_until(self.busy_until)
        return self.meta[key]["sents"]

    def at_sentence(self, key, i):
        """Chờ tới lúc bắt đầu câu thứ i của đoạn đang đọc."""
        start = next(t for t, k in reversed(self.cues) if k == key)
        self.pause_until(start + self.meta[key]["sents"][i]["start"])

    def pause_until(self, t):
        ms = int((t - self.now()) * 1000)
        if ms > 0:
            self.page.wait_for_timeout(ms)

    def wait(self, ms):
        self.page.wait_for_timeout(ms)


def record(meta, tmp: Path):
    (tmp / "intro.html").write_text(INTRO, "utf-8")
    (tmp / "flow.html").write_text(FLOW, "utf-8")
    shutil.copy(ROOT / "docs/movie_platform_dataflow.png", tmp / "flow.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        # Đăng nhập MinIO và làm nóng app ở context không quay.
        pre = browser.new_context(viewport=VIEW)
        pg = pre.new_page()
        pg.goto(f"{MINIO}/login")
        pg.fill("#accessKey", env["S3_ACCESS_KEY"])
        pg.fill("#secretKey", env["S3_SECRET_KEY"])
        pg.keyboard.press("Enter")
        pg.wait_for_url(re.compile(r".*/browser.*"), timeout=30000)
        pg.goto(APP)
        pg.get_by_text("Mã người dùng").first.wait_for(timeout=180000)
        pg.wait_for_timeout(8000)
        state = pre.storage_state()
        pre.close()

        ctx = browser.new_context(viewport=VIEW, storage_state=state,
                                  record_video_dir=str(tmp / "video"), record_video_size=REC)
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        R = Recorder(page, meta)

        def goto(url, settle=2500):
            page.goto(url)
            page.wait_for_timeout(settle)

        def focus(locator, k=1.8):
            locator.evaluate(f"el => window.__focus(el, {k})")

        def mark(locator):   # viền cam quanh phần tử (Streamlit cuộn trong khung riêng, không phóng to được)
            locator.evaluate("el => Object.assign(el.style, {outline: '4px solid #f97316', outlineOffset: '6px', "
                             "borderRadius: '10px'})")

        def unfocus():
            page.evaluate("window.__focus(null)")
            page.wait_for_timeout(1000)

        def login(url, user, password):
            helper = ctx.new_page()
            helper.goto(f"{url}/login/")
            helper.fill("#username", user)
            helper.fill("#password", password)
            helper.keyboard.press("Enter")
            helper.wait_for_url(lambda u: "/login" not in u, timeout=30000)
            helper.close()
            page.bring_to_front()

        # 1. Mở đầu
        goto((tmp / "intro.html").as_uri(), 800)
        R.chapter("1 · Bản cũ → bản nâng cấp")
        R.say("intro", wait=False)
        R.at_sentence("intro", 1)          # câu 2 kể 4 góp ý: hiện lần lượt 4 dòng
        for i in range(1, 5):
            page.evaluate(f"reveal({i})")
            R.wait(1500)
        R.at_sentence("intro", len(meta["intro"]["sents"]) - 1)   # câu cuối: phần làm thêm
        for i in (5, 6):
            page.evaluate(f"reveal({i})")
            R.wait(700)
        R.pause_until(R.busy_until)

        # 2. Kiến trúc
        goto((tmp / "flow.html").as_uri(), 500)
        R.chapter("2 · Kiến trúc tổng thể")
        R.say("d0")
        for key in ["d1", "d2", "d3", "d4", "d5"]:
            page.evaluate(f"zoom({list(REGIONS[key])})")
            R.wait(900)
            R.say(key, wait=key != "d5")
        page.evaluate("zoom(null)")
        R.pause_until(R.busy_until)

        # 3. CDC trực tiếp trên app
        goto(APP, 5000)
        page.get_by_role("tab", name="Chấm điểm").click()
        page.wait_for_timeout(2500)
        R.chapter("3 · CDC: thay đổi thật đi qua hệ thống")
        R.say("a1", wait=False)
        R.at_sentence("a1", 1)
        page.get_by_role("button", name=re.compile("Tạo người dùng mới")).first.click()
        R.say("a2", wait=False)
        R.wait(2500)
        page.get_by_role("button", name="Chấm", exact=True).nth(0).click()
        R.wait(3500)
        page.get_by_role("button", name="Chấm", exact=True).nth(1).click()
        R.pause_until(R.busy_until)
        panel = page.locator('[data-testid="stColumn"]').filter(has_text="Hành trình của thay đổi").last
        mark(panel)
        R.say("a3", wait=False)
        page.get_by_text("app_cdc/ratings/ingest_date").wait_for(timeout=90000)
        R.pause_until(R.busy_until)

        R.chapter("4 · Pipeline: lake → kho")
        page.get_by_role("button", name=re.compile("Chạy pipeline ngay")).click()
        R.say("a4", wait=False)
        R.wait(1500)
        done = page.get_by_text("Thay đổi đã vào kho sau")
        R.pause_until(R.busy_until)
        if not done.is_visible():
            R.say("a5", wait=False)
        done.wait_for(timeout=240000)
        R.pause_until(R.busy_until)
        R.wait(1200)
        R.say("a6", wait=False)
        R.at_sentence("a6", 1)
        page.get_by_text("Sau (phim mới").scroll_into_view_if_needed()
        R.pause_until(R.busy_until)
        R.wait(800)

        # 5. Kiểm chứng: Kafka, MinIO
        goto(f"{KAFKA_UI}/app.public.ratings/messages?seekDirection=BACKWARD&seekType=LATEST", 3500)
        R.chapter("5 · Kiểm chứng: Kafka và data lake")
        R.say("k1", wait=False)
        R.wait(1500)
        page.locator("tbody tr").first.locator("td").first.click()
        R.pause_until(R.busy_until)
        focus(page.locator("#schema").first, 1.9)
        R.wait(900)
        R.say("k2")
        unfocus()

        goto(f"{MINIO}/browser/lake", 3000)
        R.say("m1", wait=False)
        for name in ["bronze", "app_cdc", "ratings"]:
            page.get_by_text(name, exact=True).first.click()
            R.wait(1800)
        page.get_by_text(re.compile(r"^ingest_date=")).last.click()
        R.wait(2000)
        page.get_by_text("Last Modified", exact=True).click()
        R.wait(600)
        page.get_by_text("Last Modified", exact=True).click()
        R.wait(1200)
        R.pause_until(R.busy_until)
        newest = page.locator('[role="row"]').filter(has_text=".jsonl").first
        try:
            focus(newest, 2.0)
        except Exception:
            pass
        R.say("m2")
        unfocus()

        # 6. Airflow, Superset
        login(AIRFLOW, "admin", env["AIRFLOW_ADMIN_PASSWORD"])
        goto(f"{AIRFLOW}/dags/movie_incremental/grid", 3500)
        R.chapter("6 · Airflow và dashboard")
        R.say("f1")

        login(SUPERSET, "btl_admin", sup["ADMIN_PASSWORD"])
        goto(f"{SUPERSET}/superset/dashboard/movie-platform/", 9000)
        R.say("s1")
        page.mouse.move(720, 520)
        R.say("s2", wait=False)
        for _ in range(8):
            page.mouse.wheel(0, 120)
            R.wait(150)
        R.pause_until(R.busy_until)
        R.wait(600)

        # 7. AI
        goto(APP, 5000)
        page.get_by_role("tab", name="Tìm phim theo mô tả").click()
        R.wait(1500)
        R.chapter("7 · AI: tìm phim bằng tiếng Việt")
        R.say("ai1")
        box = page.get_by_label("Mô tả", exact=True)
        for key, query in [("ai2", "phim kinh dị về cá mập"), ("ai3", "tàu chìm, chuyện tình trên biển")]:
            box.click()
            box.press("Control+A")
            box.press("Backspace")
            box.type(query, delay=60)
            box.press("Enter")
            R.wait(4500)
            R.say(key)

        # 8. Streaming + tổng kết
        goto(f"{KAFKA_UI}/wiki.recentchange/messages?seekDirection=TAILING&seekType=LATEST", 2500)
        R.chapter("8 · Streaming thời gian thực")
        R.say("w1")
        R.wait(1000)

        goto((tmp / "flow.html").as_uri(), 400)
        R.chapter("Tổng kết")
        page.evaluate(f"hilite({json.dumps(HILITE)})")
        R.say("end")
        R.wait(2000)
        total = R.now()

        video = page.video.path()
        ctx.close()
        browser.close()
    return Path(video), R.cues, R.chapters, total


# ---------------------------------------------------------------- phụ đề + ghép
def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(cues, chapters, meta, total):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1200
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Segoe UI,40,&H00FFFFFF,&H00FFFFFF,&H30271811,&H30271811,1,0,0,0,100,100,0,0,3,14,0,2,220,220,46,1
Style: Chap,Segoe UI,30,&H00FFFFFF,&H00FFFFFF,&H10E5464F,&H10E5464F,1,0,0,0,100,100,0,0,3,10,0,9,40,40,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for i, (t, name) in enumerate(chapters):
        end = chapters[i + 1][0] if i + 1 < len(chapters) else total
        ev.append(f"Dialogue: 1,{ass_time(t)},{ass_time(end)},Chap,,0,0,0,,{name}")
    for start, key in cues:
        sents = meta[key]["sents"]
        for j, s in enumerate(sents):
            text = s["text"]
            for a, b in SUB_FIX:
                text = text.replace(a, b)
            end = start + (sents[j + 1]["start"] if j + 1 < len(sents) else s["end"] + 0.4)
            ev.append(f"Dialogue: 0,{ass_time(start + s['start'])},{ass_time(end)},Sub,,0,0,0,,{text}")
    return head + "\n".join(ev) + "\n"


PRE, POST, MIN_GAP = 2.2, 1.2, 1.0   # giữ 2,2 s hình trước mỗi đoạn thoại, 1,2 s sau; bỏ phần lặng còn lại


def keep_segments(cues, meta, total):
    """Các khoảng thời gian giữ lại trong bản quay thô: quanh lời thoại. Bỏ lúc chờ trang tải / chờ pipeline."""
    segs = []
    for start, key in cues:
        a, b = max(0.0, start - PRE), min(total, start + meta[key]["dur"] + POST)
        if segs and a <= segs[-1][1] + MIN_GAP:
            segs[-1][1] = max(segs[-1][1], b)
        else:
            segs.append([a, b])
    segs[-1][1] = total
    return segs


def remap(t, segs):
    """Đổi mốc thời gian bản thô -> bản đã cắt."""
    acc = 0.0
    for a, b in segs:
        if t < a:
            return acc
        if t <= b:
            return acc + t - a
        acc += b - a
    return acc


def mux(video: Path, cues, chapters, meta, total, tmp: Path):
    segs = keep_segments(cues, meta, total)
    new_total = sum(b - a for a, b in segs)
    cues2 = [(remap(t, segs), k) for t, k in cues]
    chapters2 = [(remap(t, segs), n) for t, n in chapters]
    (tmp / "subs.ass").write_text(build_ass(cues2, chapters2, meta, new_total), "utf-8")

    # Tiếng: nối tiếp [im lặng, đoạn thoại, im lặng, …] (các đoạn không chồng nhau).
    inputs, filters, parts, cursor = ["-i", str(video)], [], [], 0.0
    for i, (start, key) in enumerate(cues2, start=1):
        inputs += ["-i", str(BUILD / f"{key}.mp3")]
        gap = max(0.0, start - cursor)
        filters.append(f"aevalsrc=0:c=stereo:s=48000:d={gap:.3f}[g{i}]")
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atempo={SPEED}[a{i}]")
        parts += [f"[g{i}]", f"[a{i}]"]
        cursor = start + meta[key]["dur"]
    filters.append(f"{''.join(parts)}concat=n={len(parts)}:v=0:a=1,apad[aout]")
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in segs)
    filters.append(f"[0:v]fps=30,scale=1920:1200:flags=lanczos,select='{sel}',setpts=N/30/TB,subtitles=subs.ass[vout]")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[vout]", "-map", "[aout]", "-t", f"{new_total:.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(OUT)],
                   check=True, cwd=tmp)
    return new_total


def main():
    import sys
    meta = make_tts()
    raw, tl = BUILD / "raw.webm", BUILD / "timeline.json"
    if "--remux" not in sys.argv:   # --remux: chỉ ghép lại từ bản quay thô đã lưu
        print("lời thoại:", f"{sum(m['dur'] for m in meta.values()):.0f} giây")
        tmp = Path(tempfile.mkdtemp())
        video, cues, chapters, total = record(meta, tmp)
        shutil.copy(video, raw)
        tl.write_text(json.dumps({"cues": cues, "chapters": chapters, "total": total}, ensure_ascii=False,
                                 indent=1), "utf-8")
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"đã quay {total:.0f} giây")
    t = json.loads(tl.read_text("utf-8"))
    tmp = Path(tempfile.mkdtemp())
    length = mux(raw, t["cues"], t["chapters"], meta, t["total"], tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"-> {OUT}  ({int(length // 60)}:{int(length % 60):02d})")


if __name__ == "__main__":
    main()
