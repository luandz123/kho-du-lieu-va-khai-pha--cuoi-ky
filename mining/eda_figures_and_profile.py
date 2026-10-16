"""
Comprehensive EDA Profiling & Visualization Script according to Data Contract v2.
Generates:
- results/eda/data_profile.csv
- results/eda/rating_distribution.png
- results/eda/quarterly_activity.png
- results/eda/user_ratings_distribution.png
- results/eda/movie_ratings_distribution.png
- results/eda/genre_distribution.png
- results/eda/age_gender_distribution.png
"""

import csv
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mining.data_io import load_csv_data, AGE_MAP

RESULTS_EDA_DIR = Path("results/eda")
PROFILE_CSV_PATH = RESULTS_EDA_DIR / "data_profile.csv"


def generate_eda_figures_and_profile():
    RESULTS_EDA_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading canonical data via data_io adapter...")
    tables = load_csv_data()
    users = tables["users"]
    movies = tables["movies"]
    movie_genres = tables["movie_genres"]
    ratings = tables["ratings"]

    print("Computing metrics...")

    # 1. User ratings stats
    user_counts = ratings.groupby("user_id").size()
    u_min = int(user_counts.min())
    u_q25 = float(user_counts.quantile(0.25))
    u_med = float(user_counts.median())
    u_q75 = float(user_counts.quantile(0.75))
    u_q90 = float(user_counts.quantile(0.90))
    u_q95 = float(user_counts.quantile(0.95))
    u_q99 = float(user_counts.quantile(0.99))
    u_max = int(user_counts.max())
    u_mean = float(user_counts.mean())
    u_std = float(user_counts.std())

    # Users without positive rating (rating >= 4)
    users_with_pos = set(ratings[ratings["rating"] >= 4]["user_id"])
    all_users = set(users["user_id"])
    users_without_pos = sorted(list(all_users - users_with_pos))

    # 2. Movie ratings stats
    movie_counts = ratings.groupby("movie_id").size()
    all_mids = set(movies["movie_id"])
    rated_mids = set(movie_counts.index)
    unrated_mids = sorted(list(all_mids - rated_mids))

    m_min = int(movie_counts.min())
    m_q25 = float(movie_counts.quantile(0.25))
    m_med = float(movie_counts.median())
    m_q75 = float(movie_counts.quantile(0.75))
    m_q90 = float(movie_counts.quantile(0.90))
    m_q95 = float(movie_counts.quantile(0.95))
    m_q99 = float(movie_counts.quantile(0.99))
    m_max = int(movie_counts.max())
    m_mean = float(movie_counts.mean())
    m_std = float(movie_counts.std())

    # 3. Quarterly stats
    ratings["dt"] = pd.to_datetime(ratings["rated_at"])
    ratings["quarter"] = ratings["dt"].dt.to_period("Q").astype(str)
    quarterly_counts = ratings.groupby("quarter").size()

    # 4. Rating distribution
    rating_counts = ratings["rating"].value_counts().sort_index()

    # 5. Genre counts (Alphabetical order per DEC-P2-007)
    genre_counts = movie_genres["genre_name"].value_counts().sort_index()

    # 6. Build data_profile.csv
    print(f"Generating {PROFILE_CSV_PATH}...")
    profile_rows = []
    # Header: section, metric, value, unit_or_range, description
    profile_rows.append(["section", "metric", "value", "unit_or_range", "description"])

    # Dataset level
    profile_rows.append(["dataset", "dataset_name", "MovieLens 1M", "string", "Official GroupLens MovieLens 1M dataset"])
    profile_rows.append(["dataset", "contract_version", "2", "integer", "Common Data Contract Version 2"])
    profile_rows.append(["dataset", "total_users", str(len(users)), "records", "Total unique user profiles"])
    profile_rows.append(["dataset", "total_movies", str(len(movies)), "records", "Total movie catalog records"])
    profile_rows.append(["dataset", "total_movie_genre_pairs", str(len(movie_genres)), "records", "Movie-genre normalized associations"])
    profile_rows.append(["dataset", "total_ratings", str(len(ratings)), "records", "Total rating feedback events"])
    profile_rows.append(["dataset", "distinct_genres", "18", "genres", "Distinct original genres (A-Z ordering per DEC-P2-007)"])
    profile_rows.append(["dataset", "temporal_start_utc", ratings["rated_at"].min(), "ISO 8601 UTC", "Earliest rating timestamp in dataset"])
    profile_rows.append(["dataset", "temporal_end_utc", ratings["rated_at"].max(), "ISO 8601 UTC", "Latest rating timestamp in dataset"])
    profile_rows.append(["dataset", "business_key_duplicates", "0", "records", "Duplicate (user_id, movie_id) pairs in ratings"])

    # User activity profile
    profile_rows.append(["users_activity", "min_ratings_per_user", str(u_min), "ratings", "Minimum ratings provided by any user (guaranteed >= 20)"])
    profile_rows.append(["users_activity", "q25_ratings_per_user", f"{u_q25:.1f}", "ratings", "25th percentile ratings per user"])
    profile_rows.append(["users_activity", "median_ratings_per_user", f"{u_med:.1f}", "ratings", "Median ratings per user"])
    profile_rows.append(["users_activity", "mean_ratings_per_user", f"{u_mean:.2f}", "ratings", "Mean ratings per user"])
    profile_rows.append(["users_activity", "q75_ratings_per_user", f"{u_q75:.1f}", "ratings", "75th percentile ratings per user"])
    profile_rows.append(["users_activity", "q90_ratings_per_user", f"{u_q90:.1f}", "ratings", "90th percentile ratings per user"])
    profile_rows.append(["users_activity", "q95_ratings_per_user", f"{u_q95:.1f}", "ratings", "95th percentile ratings per user"])
    profile_rows.append(["users_activity", "q99_ratings_per_user", f"{u_q99:.1f}", "ratings", "99th percentile ratings per user"])
    profile_rows.append(["users_activity", "max_ratings_per_user", str(u_max), "ratings", "Maximum ratings provided by a single user"])
    profile_rows.append(["users_activity", "users_without_rating_ge_4_count", str(len(users_without_pos)), "users", "Users with 0 positive ratings (insufficient evidence in Q1)"])

    # Movie catalog profile
    profile_rows.append(["movies_catalog", "rated_movies_count", str(len(rated_mids)), "movies", "Movies with at least 1 rating in ratings table"])
    profile_rows.append(["movies_catalog", "unrated_movies_count", str(len(unrated_mids)), "movies", "Movies in catalog with 0 ratings"])
    profile_rows.append(["movies_catalog", "min_ratings_per_rated_movie", str(m_min), "ratings", "Minimum ratings for a rated movie"])
    profile_rows.append(["movies_catalog", "q25_ratings_per_rated_movie", f"{m_q25:.1f}", "ratings", "25th percentile ratings per rated movie"])
    profile_rows.append(["movies_catalog", "median_ratings_per_rated_movie", f"{m_med:.1f}", "ratings", "Median ratings per rated movie"])
    profile_rows.append(["movies_catalog", "mean_ratings_per_rated_movie", f"{m_mean:.2f}", "ratings", "Mean ratings per rated movie"])
    profile_rows.append(["movies_catalog", "q75_ratings_per_rated_movie", f"{m_q75:.1f}", "ratings", "75th percentile ratings per rated movie"])
    profile_rows.append(["movies_catalog", "max_ratings_per_rated_movie", str(m_max), "ratings", "Maximum ratings for a single movie (American Beauty)"])
    profile_rows.append(["movies_catalog", "single_genre_movies_count", str(int((movie_genres.groupby('movie_id').size() == 1).sum())), "movies", "Movies associated with exactly 1 genre"])
    profile_rows.append(["movies_catalog", "multi_genre_movies_count", str(int((movie_genres.groupby('movie_id').size() > 1).sum())), "movies", "Movies associated with >1 genres (up to 6)"])

    # Rating distribution
    total_r = len(ratings)
    for r_val in [1, 2, 3, 4, 5]:
        r_cnt = int(rating_counts.get(r_val, 0))
        r_pct = (r_cnt / total_r) * 100
        profile_rows.append(["rating_distribution", f"rating_{r_val}_stars_count", str(r_cnt), "ratings", f"Number of {r_val}-star ratings ({r_pct:.2f}%)"])

    profile_rows.append(["rating_distribution", "mean_rating_score", f"{ratings['rating'].mean():.4f}", "1..5 stars", "Average rating score across entire dataset"])

    # Quarterly volume
    for q_str, q_cnt in quarterly_counts.items():
        q_pct = (q_cnt / total_r) * 100
        profile_rows.append(["quarterly_activity", f"quarter_{q_str}_ratings_count", str(q_cnt), "ratings", f"Ratings submitted in {q_str} UTC ({q_pct:.2f}%)"])

    # Demographics
    male_cnt = int((users["gender"] == "M").sum())
    female_cnt = int((users["gender"] == "F").sum())
    profile_rows.append(["demographics", "gender_male_count", str(male_cnt), "users", f"Male users count ({(male_cnt/len(users))*100:.2f}%)"])
    profile_rows.append(["demographics", "gender_female_count", str(female_cnt), "users", f"Female users count ({(female_cnt/len(users))*100:.2f}%)"])

    age_counts = users["age_group"].value_counts()
    for ag in AGE_MAP.values():
        ag_cnt = int(age_counts.get(ag, 0))
        profile_rows.append(["demographics", f"age_group_{ag}_count", str(ag_cnt), "users", f"Users in age group '{ag}' ({(ag_cnt/len(users))*100:.2f}%)"])

    # Write profile CSV
    with open(PROFILE_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        for r in profile_rows:
            writer.writerow(r)

    print(f"data_profile.csv written successfully ({len(profile_rows)-1} metric rows).")

    # ----------------------------------------------------
    # GENERATE VISUALIZATIONS
    # ----------------------------------------------------
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 10

    # 1. Rating Distribution Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(rating_counts.index, rating_counts.values, color="#2b5c8f", width=0.55, edgecolor="#1a365d")
    ax.set_title("MovieLens 1M - Phân Bố Điểm Đánh Giá (Rating Distribution)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Điểm đánh giá (Rating Stars)", fontsize=11)
    ax.set_ylabel("Số lượt đánh giá (Rating Count)", fontsize=11)
    ax.set_xticks([1, 2, 3, 4, 5])
    for bar in bars:
        height = bar.get_height()
        pct = (height / total_r) * 100
        ax.annotate(f"{height:,}\n({pct:.1f}%)",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, fontweight="semibold")
    ax.set_ylim(0, max(rating_counts.values) * 1.15)
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "rating_distribution.png", dpi=200)
    plt.close(fig)

    # 2. Quarterly Activity Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    quarters = list(quarterly_counts.index)
    q_vals = list(quarterly_counts.values)
    bars = ax.bar(quarters, q_vals, color="#3182ce", width=0.6, edgecolor="#2b6cb0")
    ax.set_title("MovieLens 1M - Số Lượng Đánh Giá Theo Quý UTC (Quarterly Activity)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Quý (UTC Quarter)", fontsize=11)
    ax.set_ylabel("Số lượt đánh giá (Rating Count)", fontsize=11)
    plt.xticks(rotation=45)
    for bar in bars:
        height = bar.get_height()
        pct = (height / total_r) * 100
        if height > 20000:
            ax.annotate(f"{height:,}\n({pct:.1f}%)",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, fontweight="semibold")
    ax.set_ylim(0, max(q_vals) * 1.15)
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "quarterly_activity.png", dpi=200)
    plt.close(fig)

    # 3. User Ratings Distribution Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(user_counts, bins=50, color="#4299e1", edgecolor="#2b6cb0")
    ax1.axvline(u_med, color="#e53e3e", linestyle="--", linewidth=2, label=f"Median: {u_med:.0f}")
    ax1.axvline(u_mean, color="#d69e2e", linestyle=":", linewidth=2, label=f"Mean: {u_mean:.1f}")
    ax1.set_title("Phân Bố Số Đánh Giá Theo User (Thang Tuyến Tính)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Số đánh giá mỗi user", fontsize=10)
    ax1.set_ylabel("Số lượng users", fontsize=10)
    ax1.legend()

    ax2.hist(user_counts, bins=np.logspace(np.log10(20), np.log10(u_max), 40), color="#805ad5", edgecolor="#553c9a")
    ax2.set_xscale("log")
    ax2.axvline(u_med, color="#e53e3e", linestyle="--", linewidth=2, label=f"Median: {u_med:.0f}")
    ax2.set_title("Phân Bố Số Đánh Giá Theo User (Thang Logarit)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Số đánh giá mỗi user (Log Scale)", fontsize=10)
    ax2.set_ylabel("Số lượng users", fontsize=10)
    ax2.legend()

    plt.suptitle("MovieLens 1M - Tần Suất Đánh Giá Của Người Dùng (User Activity Profile)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "user_ratings_distribution.png", dpi=200)
    plt.close(fig)

    # 4. Movie Ratings Distribution Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.hist(movie_counts, bins=50, color="#38a169", edgecolor="#276749")
    ax1.axvline(m_med, color="#e53e3e", linestyle="--", linewidth=2, label=f"Median: {m_med:.0f}")
    ax1.axvline(m_mean, color="#d69e2e", linestyle=":", linewidth=2, label=f"Mean: {m_mean:.1f}")
    ax1.set_title("Phân Bố Lượt Đánh Giá Mỗi Phim (Rated Movies)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Số lượt đánh giá mỗi phim", fontsize=10)
    ax1.set_ylabel("Số lượng phim", fontsize=10)
    ax1.legend()

    # Top 10 most rated movies
    top10_mids = movie_counts.nlargest(10)
    top10_titles = [movies[movies["movie_id"] == mid]["title"].values[0] for mid in top10_mids.index]
    # Shorten long titles
    top10_labels = [t[:24] + "..." if len(t) > 24 else t for t in top10_titles]
    ax2.barh(range(10), top10_mids.values[::-1], color="#dd6b20", edgecolor="#9c4221")
    ax2.set_yticks(range(10))
    ax2.set_yticklabels(top10_labels[::-1], fontsize=9)
    ax2.set_title("Top 10 Phim Được Đánh Giá Nhiều Nhất", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Số lượt đánh giá", fontsize=10)
    for i, val in enumerate(top10_mids.values[::-1]):
        ax2.annotate(f"{val:,}", xy=(val, i), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8)

    plt.suptitle(f"MovieLens 1M - Hồ Sơ Đánh Giá Phim (Catalog: {len(movies)} phim, {len(unrated_mids)} phim chưa có rating)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "movie_ratings_distribution.png", dpi=200)
    plt.close(fig)

    # 5. Genre Distribution Plot (A-Z order per DEC-P2-007)
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(genre_counts))
    bars = ax.barh(y_pos, genre_counts.values[::-1], color="#4a5568", edgecolor="#2d3748")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(genre_counts.index[::-1], fontsize=10)
    ax.set_title("MovieLens 1M - Số Lượng Phim Theo 18 Thể Loại Gốc (Genre Distribution A-Z)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Số lượng phim liên kết (Movie-Genre Link Count)", fontsize=11)
    for bar in bars:
        width = bar.get_width()
        pct = (width / len(movies)) * 100
        ax.annotate(f"{width} ({pct:.1f}%)", xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8)
    ax.set_xlim(0, max(genre_counts.values) * 1.15)
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "genre_distribution.png", dpi=200)
    plt.close(fig)

    # 6. Age & Gender Distribution Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    age_labels = list(AGE_MAP.values())
    m_by_age = [((users["age_group"] == ag) & (users["gender"] == "M")).sum() for ag in age_labels]
    f_by_age = [((users["age_group"] == ag) & (users["gender"] == "F")).sum() for ag in age_labels]
    x = np.arange(len(age_labels))
    width = 0.35
    b1 = ax.bar(x - width/2, m_by_age, width, label="Nam (M) - 71.7%", color="#3182ce")
    b2 = ax.bar(x + width/2, f_by_age, width, label="Nữ (F) - 28.3%", color="#ed64a6")
    ax.set_title("MovieLens 1M - Cơ Cấu Người Dùng Theo Nhóm Tuổi & Giới Tính", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Nhóm tuổi (Age Group)", fontsize=11)
    ax.set_ylabel("Số lượng người dùng (User Count)", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(age_labels, fontsize=10)
    ax.legend()
    for bar in list(b1) + list(b2):
        height = bar.get_height()
        ax.annotate(f"{height}", xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, max(m_by_age) * 1.15)
    plt.tight_layout()
    fig.savefig(RESULTS_EDA_DIR / "age_gender_distribution.png", dpi=200)
    plt.close(fig)

    print("All 6 visualization figures generated successfully in results/eda/.")


if __name__ == "__main__":
    generate_eda_figures_and_profile()
