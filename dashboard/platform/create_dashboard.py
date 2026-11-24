"""Tạo dashboard "Movie Platform · Thời gian thực" trên Superset (bản nâng cấp) qua REST API.

Đọc kho mới (container dw, cổng 5433) bằng tài khoản chỉ đọc bi_reader, từ các view analytics.*
Chạy lại được: xóa chart/dashboard cũ cùng tên rồi tạo lại.

Chạy: python dashboard/platform/create_dashboard.py
"""
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote
import urllib.error
import urllib.request

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "dashboard" / "overview"))
from superset_api import SupersetAPI  # noqa: E402

load_dotenv(ROOT / ".env")
DB_NAME = "Movie Platform DW"
PREFIX = "Platform · "
SLUG = "movie-platform"


def rison(v) -> str:
    """Superset nhận tham số q dạng Rison (gọn hơn JSON, dùng được trong URL)."""
    if isinstance(v, dict):
        return "(" + ",".join(f"{k}:{rison(x)}" for k, x in v.items()) + ")"
    if isinstance(v, list):
        return "!(" + ",".join(rison(x) for x in v) + ")"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("!", "!!").replace("'", "!'") + "'"


def query(obj) -> str:
    return quote(rison(obj), safe="(),:!'")


def find(api, resource, field, value):
    q = query({"filters": [{"col": field, "opr": "eq", "value": value}]})
    res = api.request("GET", f"/api/v1/{resource}/?q={q}")["result"]
    return res[0]["id"] if res else None


def database(api):
    uri = (f"postgresql+psycopg2://bi_reader:{os.environ['BI_READER_PASSWORD']}"
           f"@host.docker.internal:5433/movie_dw")
    db_id = find(api, "database", "database_name", DB_NAME)
    body = {"database_name": DB_NAME, "sqlalchemy_uri": uri, "expose_in_sqllab": True}
    if db_id:
        api.request("PUT", f"/api/v1/database/{db_id}", body)
        return db_id
    return api.request("POST", "/api/v1/database/", body)["id"]


def dataset(api, db_id, view):
    ds = find(api, "dataset", "table_name", view)
    if ds:
        api.request("PUT", f"/api/v1/dataset/{ds}/refresh")
        return ds
    return api.request("POST", "/api/v1/dataset/", {"database": db_id, "schema": "analytics", "table_name": view})["id"]


def metric(sql, label):
    return {"expressionType": "SQL", "sqlExpression": sql, "label": label}


def charts(ds):
    """(khóa, tiêu đề, dataset, form_data, độ rộng, chiều cao)."""
    return [
        ("app_total", "Rating mới từ app (qua CDC)", ds["v_app_ratings_hourly"],
         {"viz_type": "big_number_total", "metric": metric("SUM(ratings)", "Rating mới"),
          "subheader": "tổng số rating đổ về kho qua Debezium → Kafka → MinIO", "y_axis_format": ",d"}, 4, 22),
        ("app_hourly", "Rating mới từ app theo giờ", ds["v_app_ratings_hourly"],
         {"viz_type": "echarts_timeseries_bar", "x_axis": "hour", "time_grain_sqla": "PT1H",
          "metrics": [metric("SUM(ratings)", "Rating mới")], "groupby": [], "show_legend": False,
          "y_axis_format": ",d", "rich_tooltip": True}, 8, 22),
        ("trending", "Phim đang được quan tâm · lượt xem Wikipedia 7 ngày", ds["v_trending_movies"],
         {"viz_type": "table", "query_mode": "raw",
          "all_columns": ["title", "year", "views_7d", "views_prev_7d", "growth_pct"],
          "order_by_cols": [json.dumps(["views_7d", False])], "row_limit": 15, "page_length": 15,
          "show_cell_bars": True}, 6, 50),
        ("genre_views", "Lượt xem Wikipedia theo thể loại", ds["v_pageviews_by_genre"],
         {"viz_type": "echarts_timeseries_line", "x_axis": "full_date", "time_grain_sqla": "P1D",
          "metrics": [metric("SUM(views)", "Lượt xem")], "groupby": ["genre_name"], "series_limit": 6,
          "series_limit_metric": metric("SUM(views)", "Lượt xem"), "rich_tooltip": True,
          "y_axis_format": ",d"}, 6, 50),
        ("gap", "MovieLens (×2) so với IMDb · chênh lệch lớn nhất", ds["v_movielens_vs_imdb"],
         {"viz_type": "table", "query_mode": "raw",
          "all_columns": ["title", "year", "ml_avg", "imdb_rating", "gap_ml_minus_imdb", "ml_ratings", "imdb_votes"],
          "order_by_cols": [json.dumps(["gap_ml_minus_imdb", True])], "row_limit": 15, "page_length": 15}, 6, 50),
        ("directors", "Đạo diễn được chấm nhiều nhất (từ IMDb)", ds["v_director_stats"],
         {"viz_type": "table", "query_mode": "raw", "all_columns": ["director", "movies", "ratings", "avg_rating"],
          "order_by_cols": [json.dumps(["ratings", False])], "row_limit": 15, "page_length": 15,
          "show_cell_bars": True}, 6, 50),
        ("scd2", "Lịch sử phiên bản người dùng (SCD loại 2)", ds["v_user_versions"],
         {"viz_type": "table", "query_mode": "raw",
          "all_columns": ["user_id", "user_key", "occupation", "age_group", "valid_from", "valid_to", "is_current"],
          "order_by_cols": [json.dumps(["user_id", True]), json.dumps(["valid_from", True])],
          "row_limit": 50, "page_length": 10}, 6, 40),
        ("runs", "Giám sát pipeline · các lần chạy gần nhất", ds["v_pipeline_runs"],
         {"viz_type": "table", "query_mode": "raw",
          "all_columns": ["step", "status", "started_at", "seconds", "rows_in", "rows_out"],
          "order_by_cols": [json.dumps(["run_id", False])], "row_limit": 30, "page_length": 10}, 6, 40),
    ]


def query_context(ds_id, form) -> dict:
    """Câu truy vấn tương ứng form_data, để API /chart/{id}/data trả được dữ liệu (dùng để kiểm tra)."""
    q = {"filters": [], "extras": {"where": "", "having": ""}, "row_limit": form.get("row_limit", 1000)}
    vt = form["viz_type"]
    if vt == "big_number_total":
        q.update(columns=[], metrics=[form["metric"]])
    elif vt.startswith("echarts_timeseries"):
        axis = {"timeGrain": form["time_grain_sqla"], "columnType": "BASE_AXIS", "sqlExpression": form["x_axis"],
                "label": form["x_axis"], "expressionType": "SQL"}
        q.update(columns=[axis, *form["groupby"]], metrics=form["metrics"], orderby=[[form["metrics"][0], False]],
                 series_columns=form["groupby"], series_limit=form.get("series_limit", 0),
                 series_limit_metric=form.get("series_limit_metric"))
    else:
        # Không có metrics -> truy vấn dạng raw (SELECT cột, không GROUP BY).
        q.update(columns=form["all_columns"],
                 orderby=[json.loads(o) for o in form.get("order_by_cols", [])])
    return {"datasource": {"id": ds_id, "type": "table"}, "force": False, "queries": [q],
            "form_data": form, "result_format": "json", "result_type": "full"}


def main():
    api = SupersetAPI()
    db_id = database(api)
    views = ["v_app_ratings_hourly", "v_trending_movies", "v_pageviews_by_genre", "v_movielens_vs_imdb",
             "v_director_stats", "v_user_versions", "v_pipeline_runs"]
    ds = {v: dataset(api, db_id, v) for v in views}

    old = find(api, "dashboard", "slug", SLUG)
    if old:
        api.request("DELETE", f"/api/v1/dashboard/{old}")
    q = query({"filters": [{"col": "slice_name", "opr": "sw", "value": PREFIX}], "page_size": 100})
    for c in api.request("GET", f"/api/v1/chart/?q={q}")["result"]:
        api.request("DELETE", f"/api/v1/chart/{c['id']}")

    ids, layout = {}, []
    for key, title, ds_id, form, width, height in charts(ds):
        form = {"datasource": f"{ds_id}__table", "time_range": "No filter", "adhoc_filters": [], **form}
        ids[key] = api.request("POST", "/api/v1/chart/", {
            "slice_name": PREFIX + title, "viz_type": form["viz_type"], "datasource_id": ds_id,
            "datasource_type": "table", "params": json.dumps(form),
            "query_context": json.dumps(query_context(ds_id, form))})["id"]
        layout.append((key, width, height))

    pos = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
           "GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []}}
    note = ("### Movie Platform · bản nâng cấp\n"
            "Nguồn: **MovieLens** (lịch sử) · **IMDb** (điểm hằng ngày) · **Wikipedia** (lượt xem, sửa bài) · "
            "**App** (rating mới qua CDC). Kho nạp tăng dần bởi Airflow mỗi 15 phút.")
    pos["GRID_ID"]["children"].append("NOTE")
    pos["NOTE"] = {"id": "NOTE", "type": "MARKDOWN", "parents": ["ROOT_ID", "GRID_ID"], "children": [],
                   "meta": {"width": 12, "height": 14, "code": note}}
    row, used, n = None, 12, 0
    for key, width, height in layout:
        if used + width > 12:
            n += 1
            row = f"ROW{n}"
            pos[row] = {"id": row, "type": "ROW", "parents": ["ROOT_ID", "GRID_ID"], "children": [],
                        "meta": {"background": "BACKGROUND_TRANSPARENT"}}
            pos["GRID_ID"]["children"].append(row)
            used = 0
        node = f"CHART-{key}"
        pos[row]["children"].append(node)
        pos[node] = {"id": node, "type": "CHART", "parents": ["ROOT_ID", "GRID_ID", row], "children": [],
                     "meta": {"chartId": ids[key], "width": width, "height": height}}
        used += width

    dash = api.request("POST", "/api/v1/dashboard/", {
        "dashboard_title": "Movie Platform · Thời gian thực", "slug": SLUG, "published": True,
        "position_json": json.dumps(pos),
        "json_metadata": json.dumps({"refresh_frequency": 60, "color_scheme": "supersetColors"})})["id"]
    for cid in ids.values():
        api.request("PUT", f"/api/v1/chart/{cid}", {"dashboards": [dash]})
    print(f"Dashboard: {api.base}/superset/dashboard/{SLUG}/  ({len(ids)} chart)")
    for key, cid in ids.items():
        req = urllib.request.Request(f"{api.base}/api/v1/chart/{cid}/data/",
                                     headers={"Authorization": "Bearer " + api.token, "Referer": api.base + "/"})
        try:
            with api.opener.open(req, timeout=120) as r:
                res = json.loads(r.read())["result"][0]
            print(f"  {key:12s} {res['rowcount']:>5} dòng")
        except urllib.error.HTTPError as e:
            print(f"  {key:12s} LỖI HTTP {e.code}")


if __name__ == "__main__":
    main()
