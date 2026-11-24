"""Vẽ sơ đồ luồng dữ liệu bản nâng cấp (Movie Platform) đúng theo code hiện tại.

Sinh docs/diagram/movie_platform_dataflow.svg rồi dùng Chrome/Edge headless chụp ra
docs/movie_platform_dataflow.png (2000 x 1140).

Chạy: python docs/diagram/make_dataflow.py
"""
from html import escape
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SVG = HERE / "movie_platform_dataflow.svg"
HTML = HERE / "movie_platform_dataflow.html"
PNG = HERE.parent / "movie_platform_dataflow.png"
W, H = 2000, 1140

SANS = "Segoe UI, Arial, sans-serif"
MONO = "Consolas, Menlo, monospace"
INK, MUTED = "#111827", "#4b5563"
BLUE, TEAL, ORANGE, PURPLE = "#2563eb", "#0d9488", "#ea580c", "#7c3aed"
GREEN, GRAY, MAGENTA, INDIGO = "#16a34a", "#64748b", "#be185d", "#4f46e5"

out: list[str] = []


def box(x, y, w, h, stroke, fill="#ffffff", rx=10, sw=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def text(x, y, s, size=15, weight=400, fill=INK, anchor="start", family=SANS, rotate=None):
    t = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    out.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
               f'fill="{fill}" text-anchor="{anchor}"{t}>{escape(s)}</text>')


def arrow(points, color, dash=False, sw=2.4, halo=False):
    pts = " ".join(f"{x},{y}" for x, y in points)
    if halo:  # viền trắng để chỗ 2 đường cắt nhau nhìn rõ đường nào đi trên
        out.append(f'<polyline points="{pts}" fill="none" stroke="#ffffff" stroke-width="9"/>')
    d = ' stroke-dasharray="7 6"' if dash else ""
    mid = color.lstrip("#")
    out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}"{d} '
               f'marker-end="url(#a{mid})"/>')


def card(x, y, w, h, title, subs, stroke, title_color=INK, mono_subs=()):
    box(x, y, w, h, stroke, "#ffffff", rx=8, sw=1.8)
    text(x + 12, y + 23, title, 16, 600, title_color)
    for i, s in enumerate(subs):
        mono = i in mono_subs
        text(x + 12, y + 43 + i * 18, s, 12 if mono else 13.5, 400, MUTED, family=MONO if mono else SANS)


def group(x, y, w, h, label, color, fill):
    box(x, y, w, h, color, fill, rx=12, sw=1.6, dash="6 5")
    text(x + 15, y + 22, label, 14, 700, color)


def pill(cx, cy, s, color, fill="#ffffff", size=13, vertical=False, w=None):
    w = w or int(len(s) * size * 0.56) + 26
    if vertical:
        box(cx - 13, cy - w / 2, 26, w, color, fill, rx=13, sw=1.6)
        text(cx + 5, cy, s, size, 600, color, anchor="middle", rotate=-90)
    else:
        box(cx - w / 2, cy - 14, w, 28, color, fill, rx=14, sw=1.6)
        text(cx, cy + 5, s, size, 600, color, anchor="middle")


def row(x, y, w, name, tag, tag_color):
    box(x, y, w, 30, "#bbf7d0", "#f0fdf4", rx=6, sw=1.2)
    text(x + 12, y + 20, name, 14, 400, INK, family=MONO)
    text(x + w - 12, y + 20, tag, 12.5, 600, tag_color, anchor="end")


# ---------------------------------------------------------------- tiêu đề
text(48, 58, "Movie Platform — luồng dữ liệu (bản nâng cấp)", 32, 700)
text(48, 92, "7 nguồn · 4 kiểu nạp (file, API, CDC, streaming) → Kafka / Airflow → MinIO (bronze → silver → gold) "
             "→ kho Postgres + pgvector → Superset / Streamlit", 16, 400, MUTED)
for x, s in [(85, "1 · NGUỒN"), (500, "2 · NẠP"), (810, "3 · DATA LAKE"), (1200, "4 · KHO DỮ LIỆU"),
             (1655, "5 · KHAI THÁC")]:
    text(x, 140, s, 15, 700, "#374151")

# ---------------------------------------------------------------- 1. nguồn
group(85, 160, 345, 158, "FILE · batch", BLUE, "#eff6ff")
card(98, 193, 318, 55, "MovieLens 1M", ["rating lịch sử 2000–2003 · 1.000.209 rating"], BLUE)
card(98, 255, 318, 55, "IMDb datasets", ["TSV.gz · title.ratings tải lại hằng ngày"], BLUE)

group(85, 333, 345, 224, "API · batch", TEAL, "#f0fdfa")
card(98, 366, 318, 55, "Wikidata", ["SPARQL · IMDb ID ↔ bài Wikipedia"], TEAL)
card(98, 428, 318, 55, "Wikipedia Pageviews", ["lượt xem theo ngày · 500 phim"], TEAL)
card(98, 490, 318, 55, "Wikipedia API", ["MediaWiki · tóm tắt + poster"], TEAL)

group(85, 572, 345, 132, "CDC · log-based", ORANGE, "#fff7ed")
card(98, 605, 170, 88, "App xem phim", ["Postgres · WAL", "REPLICA IDENTITY FULL", "bảng ratings, users"],
     ORANGE, mono_subs=(1,))
card(285, 605, 131, 88, "Debezium", ["pgoutput", "slot debezium_app"], ORANGE)

group(85, 719, 345, 118, "STREAMING · real-time", PURPLE, "#f5f3ff")
card(98, 752, 170, 74, "Wikimedia", ["EventStreams (SSE)"], PURPLE)
card(285, 752, 131, 74, "Producer", ["lọc enwiki, viwiki", "~1–3 sự kiện/s"], PURPLE)

# ---------------------------------------------------------------- 2. nạp
box(500, 160, 240, 388, INK)
text(620, 290, "Task nạp", 19, 700, anchor="middle")
text(620, 315, "(Airflow)", 16, 400, MUTED, anchor="middle")
for i, s in enumerate(["batch theo lịch", "", "movie_daily:", "IMDb ratings, pageviews", "",
                       "movie_bootstrap:", "MovieLens, IMDb,", "Wikidata, Wikipedia", "",
                       "ghi file gốc vào bronze"]):
    text(620, 355 + i * 19, s, 14, 600 if s.endswith(":") else 400, MUTED, anchor="middle")

box(500, 565, 240, 230, INK)
text(620, 597, "Kafka", 20, 700, anchor="middle")
for i, (t, c, f) in enumerate([("app.public.ratings", ORANGE, "#fff7ed"), ("app.public.users", ORANGE, "#fff7ed"),
                               ("wiki.recentchange", PURPLE, "#f5f3ff"), ("wiki.movie_edits", PURPLE, "#f5f3ff")]):
    box(518, 614 + i * 36, 204, 28, c, f, rx=6, sw=1.2)
    text(620, 633 + i * 36, t, 13.5, 400, c, anchor="middle", family=MONO)
text(620, 778, "3 partition / topic · UI :8080", 13, 400, MUTED, anchor="middle")

box(500, 812, 240, 88, INK)
text(620, 838, "Consumer", 17, 700, anchor="middle")
text(620, 862, "micro-batch 10 giây / 500 message", 13, 400, MUTED, anchor="middle")
text(620, 884, "commit offset SAU khi ghi lake", 13, 400, MUTED, anchor="middle")

# ---------------------------------------------------------------- 3. data lake
box(810, 160, 322, 740, INK, sw=2.4)
text(971, 192, "MinIO · bucket lake (S3)", 19, 700, anchor="middle")
text(971, 214, "xử lý bằng DuckDB · silver/gold lưu Parquet", 14, 400, MUTED, anchor="middle")

box(828, 232, 286, 190, "#c2410c", "#fff7ed", rx=8)
text(846, 258, "BRONZE", 18, 700, "#c2410c")
for i, (s, mono) in enumerate([("dữ liệu thô, giữ nguyên file gốc", 0), ("DAT · CSV · TSV.gz · JSONL", 0),
                               ("app_cdc/ratings, app_cdc/users", 1), ("wikimedia/recentchange, edits", 1),
                               (".../ingest_date=YYYY-MM-DD/", 1), ("→ xử lý lại được khi sai logic", 0)]):
    text(846, 284 + i * 21, s, 12.5 if mono else 14, 400, MUTED, family=MONO if mono else SANS)

arrow([(971, 422), (971, 449)], GRAY)
box(828, 452, 286, 200, GRAY, "#f1f5f9", rx=8)
text(846, 478, "SILVER", 18, 700, "#334155")
for i, s in enumerate(["làm sạch, ép kiểu", "CDC: bản mới nhất theo khóa + LSN",
                       "op = d → is_deleted (xóa mềm)", "users: bỏ snapshot op = r",
                       "ghép phim ML ↔ IMDb (98%)", "tóm tắt + poster Wikipedia"]):
    text(846, 504 + i * 21, s, 14, 400, MUTED)

arrow([(971, 652), (971, 679)], GRAY)
box(828, 682, 286, 200, "#ca8a04", "#fefce8", rx=8)
text(846, 708, "GOLD", 18, 700, "#a16207")
for i, s in enumerate(["đúng hình dạng kho: dim_* / fact_*", "khóa tự nhiên + changed_at",
                       "là chuẩn để đối soát với kho", "(kiểm tra chất lượng)"]):
    text(846, 734 + i * 21, s, 14, 400, MUTED)

# ---------------------------------------------------------------- 4. kho
box(1200, 160, 385, 580, GREEN, sw=2.4)
text(1392, 192, "Postgres + pgvector", 19, 700, GREEN, anchor="middle")
text(1392, 214, "lược đồ sao · nạp tăng dần", 14, 400, MUTED, anchor="middle")
text(1218, 242, "DIMENSION", 13, 700, "#374151")
row(1218, 250, 349, "dim_user", "SCD loại 2", ORANGE)
row(1218, 286, 349, "dim_movie", "SCD loại 1", INK)
text(1220, 334, "+ dim_date · dim_genre (bridge) · dim_source", 12.5, 400, MUTED)
text(1218, 362, "FACT", 13, 700, "#374151")
row(1218, 370, 349, "fact_rating", "trạng thái hiện tại", BLUE)
row(1218, 406, 349, "fact_imdb_rating_daily", "snapshot ngày", GREEN)
row(1218, 442, 349, "fact_pageviews_daily", "snapshot ngày", GREEN)
row(1218, 478, 349, "fact_wiki_edit", "streaming", PURPLE)
text(1218, 534, "ETL", 13, 700, "#374151")
row(1218, 542, 349, "etl.watermark", "đọc lùi 1 giờ", INK)
row(1218, 578, 349, "etl.pipeline_run", "nhật ký + 9 check", INK)
text(1220, 628, "ON CONFLICT DO UPDATE khi bản mới hơn", 12.5, 400, MUTED)
text(1220, 645, "→ chạy lại không nhân đôi", 12.5, 400, MUTED)
text(1218, 674, "VECTOR", 13, 700, "#374151")
row(1218, 682, 349, "movie_embedding", "HNSW · cosine", MAGENTA)

box(1200, 790, 385, 110, MAGENTA, "#fdf2f8", rx=10, sw=2)
text(1392, 817, "Embedding · multilingual-e5-small", 16, 700, MAGENTA, anchor="middle")
text(1392, 840, "384 chiều · đọc silver: mô tả Wikipedia + IMDb", 13.5, 400, MUTED, anchor="middle")
text(1392, 861, "“passage: …” / “query: …”", 13.5, 400, MUTED, anchor="middle")
text(1392, 884, "chạy tay: python -m ai.embeddings", 12.5, 400, MUTED, anchor="middle", family=MONO)

# ---------------------------------------------------------------- 5. khai thác
box(1655, 160, 295, 155, INK)
text(1802, 198, "Superset", 20, 700, anchor="middle")
text(1802, 228, "dashboard movie-platform", 14, 400, MUTED, anchor="middle")
text(1802, 250, "8 chart · tự làm mới 60 giây", 14, 400, MUTED, anchor="middle")
text(1802, 280, ":8089", 13, 400, MUTED, anchor="middle", family=MONO)

box(1655, 355, 295, 391, INK)
text(1802, 390, "App Streamlit · 5 trang", 19, 700, anchor="middle")
for i, (t, s) in enumerate([("Gợi ý", "hybrid CF + nội dung · lý do"), ("Chấm điểm", "ghi app DB · xóa · đổi nghề"),
                            ("Người dùng mới", "cold-start · chọn 3 phim"), ("Tìm phim", "câu tiếng Việt → pgvector"),
                            ("Pipeline", "chạy DAG · xem kho")]):
    box(1672, 410 + i * 66, 262, 58, "#d1d5db", "#ffffff", rx=6, sw=1.2)
    text(1686, 433 + i * 66, t, 15, 600)
    text(1686, 454 + i * 66, s, 13, 400, MUTED)

# ---------------------------------------------------------------- Airflow
box(500, 920, 1085, 80, INDIGO, "#eef2ff", rx=10, sw=2)
text(518, 951, "Airflow · điều phối", 18, 700, INDIGO)
text(712, 951, "movie_incremental (15 phút): bronze → silver → gold → nạp kho → kiểm tra chất lượng (9 check)",
     15, 400, INK)
text(518, 980, "movie_daily (08:00): IMDb + pageviews · movie_bootstrap (chạy tay): MovieLens, IMDb, Wikidata, "
               "Wikipedia · UI :8081", 14, 400, MUTED)

# ---------------------------------------------------------------- mũi tên
for y in (220, 282):
    arrow([(416, y), (497, y)], BLUE)
for y in (393, 455, 517):
    arrow([(416, y), (497, y)], TEAL)
arrow([(268, 649), (282, 649)], ORANGE)
arrow([(416, 649), (497, 649)], ORANGE)
arrow([(268, 789), (282, 789)], PURPLE)
arrow([(416, 789), (455, 789), (455, 720), (497, 720)], PURPLE)
arrow([(620, 795), (620, 809)], INK)
arrow([(740, 320), (807, 320)], "#334155")
arrow([(740, 856), (775, 856), (775, 380), (807, 380)], "#334155")

# gold -> kho (nạp tăng dần), rồi silver -> embedding (cắt qua, có viền trắng)
arrow([(1114, 790), (1160, 790), (1160, 420), (1197, 420)], GREEN, sw=2.6)
pill(1160, 680, "nạp tăng dần · upsert", GREEN, "#f0fdf4", vertical=True)
arrow([(1114, 560), (1182, 560), (1182, 845), (1197, 845)], MAGENTA, halo=True)
arrow([(1392, 790), (1392, 715)], MAGENTA)

arrow([(1585, 237), (1652, 237)], GREEN, sw=2.6)
arrow([(1585, 560), (1652, 560)], GREEN, sw=2.6)

# điều phối + nút chạy pipeline + vòng demo (nét đứt)
arrow([(971, 920), (971, 903)], GRAY, dash=True)
pill(971, 912, "điều phối", GRAY, "#f8fafc", size=12.5)
arrow([(1800, 746), (1800, 960), (1588, 960)], ORANGE, dash=True)
pill(1800, 850, "Chạy pipeline ngay", ORANGE, "#fff7ed")
arrow([(1915, 746), (1915, 1048), (48, 1048), (48, 649), (95, 649)], ORANGE, dash=True)
pill(990, 1048, "vòng demo: chấm điểm / xóa / đổi nghề trên app → Postgres → Debezium → Kafka → lake → kho "
                "→ thấy lại trên app / Superset", ORANGE, "#fff7ed", size=13.5)

# ---------------------------------------------------------------- chú thích
lx = 48
for color, label, dash in [(BLUE, "file batch", False), (TEAL, "API", False), (ORANGE, "CDC / thao tác demo", False),
                           (PURPLE, "streaming", False), (GREEN, "kho → khai thác", False),
                           (MAGENTA, "embedding", False), (GRAY, "nét đứt = điều phối / kích hoạt", True)]:
    d = ' stroke-dasharray="7 6"' if dash else ""
    out.append(f'<line x1="{lx}" y1="1100" x2="{lx + 30}" y2="1100" stroke="{color}" stroke-width="3"{d}/>')
    text(lx + 40, 1105, label, 14, 400, "#374151")
    lx += 40 + int(len(label) * 7.6) + 34

markers = "".join(
    f'<marker id="a{c.lstrip("#")}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
    for c in {BLUE, TEAL, ORANGE, PURPLE, GREEN, GRAY, MAGENTA, INK, "#334155"})
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       f'<defs>{markers}</defs><rect width="{W}" height="{H}" fill="#ffffff"/>' + "\n".join(out) + "</svg>")
SVG.write_text(svg, encoding="utf-8")
HTML.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style>{svg}',
                encoding="utf-8")

browser = next((p for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                            shutil.which("chromium"), shutil.which("google-chrome")] if p and Path(p).exists()), None)
if browser is None:
    raise SystemExit(f"Không tìm thấy Chrome/Edge; mở {SVG} và xuất PNG bằng tay")
subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={W},{H}", f"--screenshot={PNG}", HTML.as_uri()], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
HTML.unlink()
print("->", SVG, "\n->", PNG)
