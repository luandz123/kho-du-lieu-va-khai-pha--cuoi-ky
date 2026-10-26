"""Vẽ các sơ đồ và biểu đồ tiếng Việt cho báo cáo.

Số liệu lấy từ các file kết quả đã có trong repository (results/...), không chạy lại
pipeline. Chạy: python docs/report/make_figures.py (từ thư mục gốc repository).
"""
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 12,
    "axes.titlesize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
})

BLUE = "#1F4E79"
LIGHT = "#DCE6F1"
RED = "#B22222"
GREY = "#7F7F7F"
GREEN = "#2E7D32"
ORANGE = "#E08E0B"


def vn(x, nd=0):
    """Định dạng số kiểu Việt Nam: 1.000.209 và 0,231."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def box(ax, x, y, w, h, title, sub="", fc=LIGHT, ec=BLUE, tc="black", fs=12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.4))
    if sub:
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=tc)
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=fs - 2, color=tc)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=tc)


def arrow(ax, x1, y1, x2, y2, color=BLUE, text=None):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5, mutation_scale=14))
    if text:
        ax.text((x1 + x2) / 2 + 0.05, (y1 + y2) / 2, text, fontsize=9.5, color=GREY,
                ha="left", va="center")


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def fig_architecture():
    fig, ax = canvas(12, 7.2)
    # Tầng nguồn và kho
    box(ax, 0.3, 5.6, 2.4, 1.1, "MovieLens 1M", "users · movies · ratings", fc="#F2F2F2", ec=GREY)
    box(ax, 3.4, 5.6, 2.4, 1.1, "Staging", "PostgreSQL · dạng thô")
    box(ax, 6.5, 5.6, 2.6, 1.1, "Kho dữ liệu (DW)", "Lược đồ sao + bridge")
    box(ax, 9.6, 5.6, 2.1, 1.1, "4 view chuẩn", "giao diện dữ liệu")
    arrow(ax, 2.7, 6.15, 3.4, 6.15, text=None)
    arrow(ax, 5.8, 6.15, 6.5, 6.15)
    arrow(ax, 9.1, 6.15, 9.6, 6.15)
    ax.text(3.05, 6.8, "Extract", fontsize=9.5, color=GREY, ha="center")
    ax.text(6.15, 6.8, "Transform, Load", fontsize=9.5, color=GREY, ha="center")
    # Ba nhánh phân tích
    box(ax, 0.6, 3.1, 3.2, 1.2, "OLAP (O1–O6)", "6 view tổng hợp · Q3")
    box(ax, 4.4, 3.1, 3.2, 1.2, "Phân cụm K-Means", "vector sở thích thể loại · Q1")
    box(ax, 8.2, 3.1, 3.3, 1.2, "Gợi ý Top-5", "Item-based CF + Baseline · Q2")
    arrow(ax, 7.8, 5.6, 2.2, 4.3)
    arrow(ax, 10.65, 5.6, 6.0, 4.3)
    arrow(ax, 10.65, 5.6, 9.85, 4.3)
    # Đầu ra
    box(ax, 0.6, 0.6, 3.2, 1.2, "Superset", "Tổng quan · Xu hướng", fc="#FDECEA", ec=RED)
    box(ax, 4.4, 0.6, 3.2, 1.2, "Schema analytics", "kết quả cụm → Sở thích", fc="#FDECEA", ec=RED)
    box(ax, 8.2, 0.6, 3.3, 1.2, "Công cụ dòng lệnh", "đánh giá · demo gợi ý", fc="#FDECEA", ec=RED)
    arrow(ax, 2.2, 3.1, 2.2, 1.8, color=RED)
    arrow(ax, 6.0, 3.1, 6.0, 1.8, color=RED)
    arrow(ax, 9.85, 3.1, 9.85, 1.8, color=RED)
    ax.text(0.3, 4.75, "TẦNG PHÂN TÍCH VÀ KHAI PHÁ", fontsize=10, color=BLUE, fontweight="bold")
    ax.text(0.3, 2.2, "TẦNG TRÌNH BÀY", fontsize=10, color=RED, fontweight="bold")
    ax.text(0.3, 6.95, "TẦNG DỮ LIỆU", fontsize=10, color=GREY, fontweight="bold")
    fig.savefig(OUT / "kien_truc.png")
    plt.close(fig)


def table_box(ax, x, y, w, title, rows, fc, ec):
    lh = 0.36
    h = lh * (len(rows) + 1) + 0.15
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                fc="white", ec=ec, lw=1.5))
    ax.add_patch(FancyBboxPatch((x, y - lh - 0.05), w, lh + 0.05,
                                boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y - lh / 2 - 0.02, title, ha="center", va="center", fontweight="bold",
            fontsize=11.5, color="white")
    for i, r in enumerate(rows):
        ax.text(x + 0.12, y - lh * (i + 1.5) - 0.06, r, ha="left", va="center", fontsize=10)
    return h


def fig_star_schema():
    fig, ax = canvas(12, 7.6)
    fact_rows = ["PK rating_key", "FK user_key → dim_user", "FK movie_key → dim_movie",
                 "FK date_key → dim_date", "rating (1..5)", "rating_timestamp, rated_at (UTC)",
                 "UNIQUE (user_key, movie_key)"]
    table_box(ax, 4.2, 5.2, 3.6, "FACT_RATING", fact_rows, RED, RED)
    table_box(ax, 0.2, 7.4, 3.2, "DIM_USER", ["PK user_key", "user_id (ID gốc)", "gender",
                                              "age_group", "occupation"], BLUE, BLUE)
    table_box(ax, 8.6, 7.4, 3.2, "DIM_DATE", ["PK date_key", "full_date (UTC)", "calendar_year",
                                              "quarter_number", "month_number"], BLUE, BLUE)
    table_box(ax, 0.2, 3.0, 3.2, "DIM_MOVIE", ["PK movie_key", "movie_id (ID gốc)", "title",
                                               "release_year"], BLUE, BLUE)
    table_box(ax, 4.2, 1.9, 3.6, "BRIDGE_MOVIE_GENRE", ["PK, FK movie_key", "PK, FK genre_key"],
              GREY, GREY)
    table_box(ax, 8.6, 2.2, 3.2, "DIM_GENRE", ["PK genre_key", "genre_name (18 giá trị)"], BLUE, BLUE)
    kw = dict(arrowstyle="-", color=GREY, lw=1.3)
    for (a, b) in [((3.4, 6.2), (4.2, 4.6)), ((8.6, 6.2), (7.8, 4.6)), ((3.4, 2.4), (4.2, 3.4)),
                   ((3.4, 1.7), (4.2, 1.3)), ((8.6, 1.6), (7.8, 1.3))]:
        ax.annotate("", xy=b, xytext=a, arrowprops=kw)
    for (x, y, t) in [(3.55, 5.5, "1 : N"), (8.0, 5.5, "1 : N"), (3.55, 2.95, "1 : N"),
                      (3.5, 1.2, "1 : N"), (8.0, 1.65, "1 : N")]:
        ax.text(x, y, t, fontsize=9.5, color=GREY)
    fig.savefig(OUT / "luoc_do_sao.png")
    plt.close(fig)


def fig_etl_flow():
    fig, ax = canvas(12, 4.6)
    steps = [("1. Kiểm nguồn", "hash · số dòng"), ("2. Staging", "3 bảng thô"),
             ("3. Dimension", "user · movie\ndate · genre"), ("4. Bridge", "6.408 cặp"),
             ("5. Fact", "1.000.209 dòng"), ("6. Đối soát", "count · tổng điểm\nhash · khóa")]
    x = 0.2
    for i, (t, s) in enumerate(steps):
        box(ax, x, 2.2, 1.75, 1.3, t, s, fs=11.5)
        if i < len(steps) - 1:
            arrow(ax, x + 1.75, 2.85, x + 2.0, 2.85)
        x += 2.0
    ax.add_patch(FancyBboxPatch((0.05, 1.95), 11.85, 2.1, boxstyle="round,pad=0.02",
                                fc="none", ec=RED, lw=1.3, ls="--"))
    ax.text(6.0, 3.8, "Một transaction duy nhất (BEGIN … COMMIT)", ha="center", color=RED,
            fontsize=11, fontweight="bold")
    box(ax, 7.0, 0.1, 2.3, 1.0, "COMMIT", "khớp toàn bộ", fc="#E8F5E9", ec=GREEN, fs=11.5)
    box(ax, 9.6, 0.1, 2.3, 1.0, "ROLLBACK", "lệch bất kỳ chỉ số", fc="#FDECEA", ec=RED, fs=11.5)
    arrow(ax, 11.0, 2.2, 8.15, 1.1, color=GREEN)
    arrow(ax, 11.1, 2.2, 10.75, 1.1, color=RED)
    ax.text(0.2, 0.55, "Xóa dữ liệu cũ theo danh sách bảng tường minh,\nđánh dấu kết quả cụm cũ "
            "là không hợp lệ trước khi nạp lại.", fontsize=10.5, color=GREY)
    fig.savefig(OUT / "quy_trinh_etl.png")
    plt.close(fig)


def fig_temporal_split():
    fig, ax = plt.subplots(figsize=(11, 2.6))
    parts = [("Train", 70.0, BLUE, "700.148 đánh giá (70%)\n25/04/2000 – 22/11/2000"),
             ("Validation", 15.0, ORANGE, "150.029 (15%)\n22/11–10/12/2000"),
             ("Test", 15.0, RED, "150.032 (15%)\n10/12/2000–28/02/2003")]
    left = 0
    for name, w, c, sub in parts:
        ax.barh(0, w, left=left, color=c, height=0.5)
        ax.text(left + w / 2, 0, name, ha="center", va="center", color="white", fontweight="bold")
        ax.text(left + w / 2, -0.4, sub, ha="center", va="top", fontsize=9.5)
        left += w
    for xv, lab in [(70, "t₁ (phân vị 70%)"), (85, "t₂ (phân vị 85%)")]:
        ax.plot([xv, xv], [-0.3, 0.33], color="black", lw=1, ls="--")
        ax.text(xv, 0.36, lab, ha="center", va="bottom", fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.0, 0.65)
    ax.axis("off")
    fig.savefig(OUT / "chia_thoi_gian.png")
    plt.close(fig)


def bar_labels(ax, bars, fmt):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt(b.get_height()),
                ha="center", va="bottom", fontsize=10)


def fig_eda():
    eda = json.loads((ROOT / "results/eda/eda_metrics.json").read_text(encoding="utf-8"))
    # Phân bố số sao
    dist = eda["ratings"]["rating_distribution"]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    bars = ax.bar([f"{k} sao" for k in dist], list(dist.values()), color=BLUE)
    bar_labels(ax, bars, lambda v: vn(v))
    ax.set_ylabel("Số đánh giá")
    ax.yaxis.set_major_formatter(lambda v, p: vn(v))
    fig.savefig(OUT / "phan_bo_sao.png")
    plt.close(fig)
    # Số phim theo thể loại
    g = sorted(eda["movies"]["genre_distribution"].items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    bars = ax.barh([k for k, _ in g], [v for _, v in g], color=BLUE)
    for b in bars:
        ax.text(b.get_width() + 10, b.get_y() + b.get_height() / 2, vn(b.get_width()),
                va="center", fontsize=9.5)
    ax.set_xlabel("Số phim (một phim có thể thuộc nhiều thể loại)")
    fig.savefig(OUT / "phim_theo_the_loai.png")
    plt.close(fig)
    # Nhân khẩu học
    ages = eda["users"]["age_distribution"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [2.4, 1]})
    bars = axs[0].bar(list(ages.keys()), list(ages.values()), color=BLUE)
    bar_labels(axs[0], bars, lambda v: vn(v))
    axs[0].set_ylabel("Số người dùng")
    axs[0].set_title("Theo nhóm tuổi")
    gd = eda["users"]["gender_distribution"]
    bars = axs[1].bar(["Nam (M)", "Nữ (F)"], [gd["M"], gd["F"]], color=[BLUE, RED])
    bar_labels(axs[1], bars, lambda v: vn(v))
    axs[1].set_title("Theo giới tính")
    fig.tight_layout()
    fig.savefig(OUT / "nhan_khau_hoc.png")
    plt.close(fig)


QUARTERS = [("2000Q2", 133319), ("2000Q3", 324864), ("2000Q4", 446574), ("2001Q1", 32223),
            ("2001Q2", 15091), ("2001Q3", 12296), ("2001Q4", 8448), ("2002Q1", 8166),
            ("2002Q2", 6385), ("2002Q3", 5309), ("2002Q4", 4186), ("2003Q1", 3348)]


def fig_quarterly():
    assert sum(v for _, v in QUARTERS) == 1000209
    fig, ax = plt.subplots(figsize=(10, 4.2))
    colors = [GREY if q in ("2000Q2", "2003Q1") else BLUE for q, _ in QUARTERS]
    bars = ax.bar([q for q, _ in QUARTERS], [v for _, v in QUARTERS], color=colors)
    bar_labels(ax, bars, lambda v: vn(v))
    ax.set_ylabel("Số đánh giá")
    ax.yaxis.set_major_formatter(lambda v, p: vn(v))
    plt.setp(ax.get_xticklabels(), rotation=35)
    ax.text(0.99, 0.95, "Cột xám: quý biên, quan sát không trọn quý", transform=ax.transAxes,
            ha="right", fontsize=10, color=GREY)
    fig.savefig(OUT / "danh_gia_theo_quy.png")
    plt.close(fig)


def fig_kmeans():
    rows = list(csv.DictReader(open(ROOT / "results/mining/kmeans_experiments.csv", encoding="utf-8")))
    raw = [r for r in rows if r["preprocessing"] == "raw"]
    sc = [r for r in rows if r["preprocessing"] == "standard_scaler"]
    ks = [int(r["k"]) for r in raw]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].plot(ks, [float(r["inertia"]) for r in raw], "o-", color=BLUE)
    axs[0].scatter([4], [float(raw[2]["inertia"])], s=160, facecolors="none", edgecolors=RED, lw=2)
    axs[0].set_title("Inertia (SSE) – dữ liệu tỷ lệ gốc")
    axs[0].set_xlabel("Số cụm K")
    axs[0].set_ylabel("Inertia")
    axs[1].plot(ks, [float(r["silhouette_sample2000"]) for r in raw], "o-", color=BLUE,
                label="Tỷ lệ gốc (raw)")
    axs[1].plot(ks, [float(r["silhouette_sample2000"]) for r in sc], "s--", color=ORANGE,
                label="StandardScaler")
    axs[1].scatter([4], [float(raw[2]["silhouette_sample2000"])], s=160, facecolors="none",
                   edgecolors=RED, lw=2)
    axs[1].set_title("Silhouette (mẫu cố định 2.000 người)")
    axs[1].set_xlabel("Số cụm K")
    axs[1].legend(frameon=False)
    for a in axs:
        a.set_xticks(ks)
    fig.tight_layout()
    fig.savefig(OUT / "kmeans_chon_k.png")
    plt.close(fig)


def fig_cf():
    rows = list(csv.DictReader(open(ROOT / "results/mining/metrics.csv", encoding="utf-8")))
    val = [r for r in rows if r["evaluation_phase"] == "validation"]
    labels = ["Popularity" if r["model_name"].startswith("pop") else f"CF k={r['neighbor_k']}"
              for r in val]
    p = [float(r["macro_precision_at_5"]) for r in val]
    rc = [float(r["macro_recall_at_5"]) for r in val]
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.9))
    for a, vals, t in [(axs[0], p, "Precision@5"), (axs[1], rc, "Recall@5")]:
        cols = [GREY] + [BLUE] * (len(vals) - 1)
        cols[2] = RED  # k=40 được chọn
        bars = a.bar(labels, vals, color=cols)
        bar_labels(a, bars, lambda v: vn(v, 4))
        a.set_title(t + " trên tập validation (471 người)")
        a.set_ylim(0, max(vals) * 1.18)
        a.yaxis.set_major_formatter(lambda v, p: vn(v, 3))
    fig.tight_layout()
    fig.savefig(OUT / "cf_validation.png")
    plt.close(fig)

    test = [r for r in rows if r["evaluation_phase"] == "test"]
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.8))
    names = ["Popularity Baseline", "Item-based CF (k=40)"]
    for a, key, t in [(axs[0], "macro_precision_at_5", "Precision@5"),
                      (axs[1], "macro_recall_at_5", "Recall@5")]:
        vals = [float(r[key]) for r in test]
        bars = a.bar(names, vals, color=[GREY, RED], width=0.55)
        bar_labels(a, bars, lambda v: vn(v, 4))
        a.set_title(t + " trên tập test (1.154 người)")
        a.set_ylim(0, max(vals) * 1.2)
        a.yaxis.set_major_formatter(lambda v, p: vn(v, 2))
    fig.tight_layout()
    fig.savefig(OUT / "cf_test.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_architecture()
    fig_star_schema()
    fig_etl_flow()
    fig_temporal_split()
    fig_eda()
    fig_quarterly()
    fig_kmeans()
    fig_cf()
    print("Đã vẽ:", sorted(p.name for p in OUT.glob("*.png")))
