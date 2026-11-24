"""Hình cho chương 5 (bản nâng cấp): lược đồ sao kho mới và kết quả gợi ý hybrid.

Chạy từ thư mục gốc: python docs/report/make_figures_nang_cap.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "figures" / "nang_cap"
plt.rcParams["font.family"] = "Times New Roman"

DIM, FACT, OPS = "#dbeafe", "#fde68a", "#e5e7eb"


def box(ax, x, y, w, title, rows, color, sub=""):
    h = 0.36 + 0.27 * len(rows)
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.02", fc="white", ec="#334155", lw=1.2))
    ax.add_patch(FancyBboxPatch((x, y - 0.36), w, 0.36, boxstyle="round,pad=0.02", fc=color, ec="#334155", lw=1.2))
    ax.text(x + w / 2, y - 0.18, title + (f"  ({sub})" if sub else ""), ha="center", va="center",
            fontsize=10.5, weight="bold")
    for i, r in enumerate(rows):
        ax.text(x + 0.08, y - 0.36 - 0.27 * (i + 0.55), r, va="center", fontsize=9)
    return (x, y, w, h)


def link(ax, a, b):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color="#475569", lw=1.1))


def star_schema():
    fig, ax = plt.subplots(figsize=(13, 8.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8.2)
    ax.axis("off")
    u = box(ax, 0.2, 8.0, 3.0, "dim_user", ["user_key (PK)", "user_id", "gender, age_group, occupation",
                                            "valid_from, valid_to", "is_current"], DIM, "SCD loại 2")
    s = box(ax, 0.2, 5.0, 3.0, "dim_source", ["source_key (PK)", "source_name: movielens | app"], DIM)
    d = box(ax, 0.2, 3.3, 3.0, "dim_date", ["date_key (PK, YYYYMMDD)", "full_date, year, quarter",
                                            "month, day_of_week, is_weekend"], DIM)
    f = box(ax, 4.4, 6.6, 3.3, "fact_rating", ["PK (user_id, movie_id)", "user_key, movie_key (FK)",
                                               "date_key, source_key (FK)", "rating 1..5, rated_at",
                                               "is_deleted (xóa mềm)", "changed_at (watermark)"], FACT,
            "trạng thái hiện tại")
    m = box(ax, 9.0, 8.0, 3.8, "dim_movie", ["movie_key (PK)", "movie_id, title, year", "imdb_id, imdb_match",
                                             "runtime, directors, top_cast", "countries, oscar_wins",
                                             "enwiki/viwiki_title, poster_url"], DIM, "SCD loại 1")
    g = box(ax, 11.0, 4.9, 1.5, "dim_genre", ["genre_key (PK)", "genre_name"], DIM)
    b = box(ax, 9.0, 4.9, 1.75, "bridge_movie_genre", ["movie_key (FK)", "genre_key (FK)"], DIM)
    e = box(ax, 9.0, 3.1, 3.8, "movie_embedding", ["movie_key (PK, FK)", "doc", "embedding vector(384), HNSW"],
            "#ede9fe", "pgvector")
    i = box(ax, 4.4, 3.4, 3.3, "fact_imdb_rating_daily", ["(movie_key, date_key)", "imdb_rating, imdb_votes",
                                                          "votes_delta"], FACT, "snapshot ngày")
    p = box(ax, 4.4, 2.0, 3.3, "fact_pageviews_daily", ["(movie_key, date_key)", "views"], FACT, "snapshot ngày")
    w = box(ax, 4.4, 0.95, 3.3, "fact_wiki_edit", ["event_id (PK)", "movie_key, date_key (FK)"], FACT, "streaming")
    link(ax, (4.4, 6.0), (3.2, 7.0))
    link(ax, (4.4, 5.2), (3.2, 4.6))
    link(ax, (4.4, 5.0), (3.2, 2.9))
    link(ax, (7.7, 6.0), (9.0, 7.0))
    link(ax, (7.7, 3.0), (9.0, 6.6))
    link(ax, (7.7, 1.7), (9.0, 6.4))
    link(ax, (7.7, 0.6), (9.0, 6.2))
    link(ax, (4.4, 2.9), (3.2, 2.6))
    link(ax, (9.9, 4.9), (9.9, 6.02))
    link(ax, (10.75, 4.45), (11.0, 4.45))
    link(ax, (12.7, 3.1), (12.7, 6.02))
    ax.text(0.2, 1.4, "etl.watermark · etl.pipeline_run:\nvận hành nạp tăng dần",
            fontsize=9, style="italic", wrap=True, color="#334155")
    fig.tight_layout()
    fig.savefig(OUT / "luoc_do_sao_moi.png", dpi=200)
    plt.close(fig)


def hybrid_chart():
    data = json.loads((ROOT / "results/mining/hybrid_evaluation.json").read_text("utf-8"))
    rows = [("Popularity\n(bản cũ)", 0.2017, 0.0271), ("Item-based CF\n(bản cũ)", 0.2310, 0.0353),
            ("Chỉ nội dung\n(E5 + Wikipedia)", 0.2175, 0.0318), (f"Hybrid\n(α = {data['chosen_alpha']})", 0.2314, 0.0352)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    colors = ["#94a3b8", "#60a5fa", "#a78bfa", "#f59e0b"]
    for ax, idx, name in [(axes[0], 1, "Precision@5"), (axes[1], 2, "Recall@5")]:
        vals = [r[idx] for r in rows]
        bars = ax.bar([r[0] for r in rows], vals, color=colors)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v, f"{v:.4f}".replace(".", ","), ha="center",
                    va="bottom", fontsize=10)
        ax.set_title(f"{name} trên tập test (1.154 người dùng)", fontsize=11)
        ax.set_ylim(0, max(vals) * 1.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "hybrid_test.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    star_schema()
    hybrid_chart()
    print("->", OUT)
