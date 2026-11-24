"""Các DAG điều phối pipeline. Mỗi task chạy 1 lệnh `python -m ...` của dự án,
giống hệt khi chạy tay, nên dễ thử từng bước và dễ giải thích.

  movie_incremental  mỗi 15 phút (và bấm chạy tay khi demo):
      dữ liệu CDC + streaming trong bronze -> silver -> gold -> kho -> kiểm tra chất lượng
  movie_daily        mỗi ngày 08:00 UTC (sau khi IMDb cập nhật file):
      tải điểm IMDb + lượt xem Wikipedia -> silver -> gold -> kho
  movie_bootstrap    chạy tay 1 lần: nạp toàn bộ từ đầu (nguồn tĩnh MovieLens, IMDb, Wikidata)
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULTS = {"retries": 2, "retry_delay": timedelta(minutes=1)}


def step(dag, task_id, module, *args):
    return BashOperator(task_id=task_id, dag=dag, cwd="/opt/project",
                        bash_command=f"python -m {module} {' '.join(args)}".strip())


# ---------------------------------------------------------------- mỗi 15 phút
with DAG("movie_incremental", start_date=datetime(2026, 11, 1), schedule="*/15 * * * *",
         catchup=False, max_active_runs=1, default_args=DEFAULTS,
         tags=["cdc", "streaming"], doc_md=__doc__) as incremental:
    silver_cdc = step(incremental, "bronze_to_silver", "transform.silver", "app_ratings", "app_users", "wiki_edits")
    gold_cdc = step(incremental, "silver_to_gold", "transform.gold", "dim_user", "fact_rating", "fact_wiki_edit")
    load_cdc = step(incremental, "load_warehouse", "warehouse.load", "dim_user", "fact_rating", "fact_wiki_edit")
    check = step(incremental, "data_quality", "warehouse.quality")
    silver_cdc >> gold_cdc >> load_cdc >> check

# ---------------------------------------------------------------- mỗi ngày
with DAG("movie_daily", start_date=datetime(2026, 11, 1), schedule="0 8 * * *",
         catchup=False, max_active_runs=1, default_args=DEFAULTS,
         tags=["batch"], doc_md=__doc__) as daily:
    imdb = step(daily, "ingest_imdb_ratings", "sources.imdb")
    pageviews = step(daily, "ingest_wiki_pageviews", "sources.pageviews", "--days", "3")
    silver_daily = step(daily, "bronze_to_silver", "transform.silver", "imdb_ratings", "pageviews")
    gold_daily = step(daily, "silver_to_gold", "transform.gold", "fact_imdb_rating_daily", "fact_pageviews_daily")
    load_daily = step(daily, "load_warehouse", "warehouse.load", "fact_imdb_rating_daily", "fact_pageviews_daily")
    [imdb, pageviews] >> silver_daily >> gold_daily >> load_daily

# ---------------------------------------------------------------- chạy tay 1 lần
with DAG("movie_bootstrap", start_date=datetime(2026, 11, 1), schedule=None,
         catchup=False, default_args=DEFAULTS, tags=["batch"], doc_md=__doc__) as bootstrap:
    ml = step(bootstrap, "ingest_movielens", "sources.movielens")
    imdb_full = step(bootstrap, "ingest_imdb_full", "sources.imdb")
    silver_base = step(bootstrap, "silver_movies", "transform.silver", "users", "ratings", "movies", "imdb_movies", "imdb_ratings")
    wikidata = step(bootstrap, "ingest_wikidata", "sources.wikidata")
    silver_wiki = step(bootstrap, "silver_wiki_links", "transform.silver", "wiki_links")
    summaries = step(bootstrap, "ingest_wiki_summaries", "sources.wiki_summaries")
    pv = step(bootstrap, "ingest_wiki_pageviews_90d", "sources.pageviews", "--days", "90")
    silver_rest = step(bootstrap, "silver_rest", "transform.silver", "summaries", "pageviews", "app_ratings",
                       "app_users", "wiki_edits")
    gold_all = step(bootstrap, "silver_to_gold", "transform.gold")
    load_all = step(bootstrap, "load_warehouse", "warehouse.load")
    check_all = step(bootstrap, "data_quality", "warehouse.quality")
    # Wikimedia giới hạn tốc độ theo IP nên 2 bước gọi Wikipedia chạy nối tiếp, không song song.
    [ml, imdb_full] >> silver_base >> wikidata >> silver_wiki >> summaries >> pv >> silver_rest
    silver_rest >> gold_all >> load_all >> check_all
    # Embedding (ai.embeddings) cần PyTorch nên chạy trên máy: python -m ai.embeddings
