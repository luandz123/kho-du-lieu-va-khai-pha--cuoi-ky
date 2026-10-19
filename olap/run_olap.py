"""Install the six approved OLAP views, or read/export aggregate O1-O6 results."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from etl.run_etl import atomic_json
from etl.s05_staging import ROOT, SafeError, assert_project, catalog, config, connect, sha256

VIEWS = ["analytics.v_olap_" + s for s in ["kpi", "movie_metrics", "genre_age_gender", "time_rollup", "genre_quarter", "movie_day_segment"]]
CODE = ["olap/run_olap.py", "olap/queries.sql", "database/views.sql", "etl/s05_staging.py"]


def json_value(value):
    """Preserve NUMERIC precision and ISO dates in aggregate metadata."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def report_payload(report):
    return json.loads(json.dumps(report, default=json_value))


def queries():
    text = (ROOT / "olap/queries.sql").read_text(encoding="utf-8")
    parts = re.split(r"-- name: (O[1-6])\s*\n", text)
    result = dict(zip(parts[1::2], parts[2::2]))
    if set(result) != {"O" + str(i) for i in range(1, 7)}:
        raise SafeError("SIX_NAMED_QUERIES_REQUIRED")
    return result


def rows(conn, statement, params=None):
    with conn.cursor() as cur:
        cur.execute(statement, params)
        return [dict(zip([c.name for c in cur.description], r)) for r in cur.fetchall()]


def guard_signature(conn):
    """No user history output: table identity/aggregate signature and contract definitions."""
    with conn.cursor() as cur:
        cur.execute("SELECT c.oid,n.nspname,c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname IN ('staging','dw','analytics') ORDER BY 2,3")
        tables = cur.fetchall()
        cur.execute("SELECT (SELECT count(*) FROM dw.fact_rating),(SELECT sum(rating) FROM dw.fact_rating),(SELECT count(*) FROM dw.dim_user),(SELECT count(*) FROM dw.dim_movie),(SELECT count(*) FROM dw.bridge_movie_genre),(SELECT count(*) FROM analytics.model_registry),(SELECT count(*) FROM analytics.user_cluster),(SELECT count(*) FROM analytics.cluster_genre_profile)")
        counts = cur.fetchone()
        cur.execute("SELECT viewname,definition FROM pg_views WHERE schemaname='dw' AND viewname LIKE 'v_ml_%' ORDER BY viewname")
        definitions = cur.fetchall()
    body = json.dumps([tables, counts, definitions], default=str, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def install(c):
    conn = connect(c)
    try:
        with conn:
            assert_project(conn); catalog(conn)
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261027,1)")
                cur.execute("SELECT schemaname||'.'||viewname FROM pg_views WHERE schemaname||'.'||viewname=ANY(%s)", (VIEWS,))
                if cur.fetchall():
                    raise SafeError("OLAP_VIEWS_ALREADY_EXIST_INSPECT_BEFORE_INSTALL")
            before = guard_signature(conn)
            script = (ROOT / "database/views.sql").read_text(encoding="utf-8")
            if re.findall(r"CREATE VIEW ([\w.]+)", script) != VIEWS:
                raise SafeError("OLAP_VIEW_ALLOWLIST_MISMATCH")
            with conn.cursor() as cur:
                cur.execute(script)
            after = guard_signature(conn)
            if before != after:
                raise SafeError("TABLE_OR_CONTRACT_CHANGED_DURING_VIEW_INSTALL")
            verified = catalog(conn)
        return {"transaction": "COMMITTED", "installed_views": VIEWS, "catalog_views": verified["views"],
                "table_and_contract_signature_unchanged": True, "signature": before}
    finally:
        conn.close()


def export_table(folder, name, data):
    path = folder / (name + ".csv")
    with path.open("x", encoding="utf-8", newline="") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(data)
    return {"rows": len(data), "path": str(path.relative_to(ROOT)), "sha256": sha256(path)}


def verify_outputs(conn, outputs):
    k = outputs["O1"][0]
    if tuple(k[x] for x in ["catalog_users", "catalog_movies", "rated_users", "rated_movies", "rating_count", "rating_sum"]) != (6040, 3883, 6040, 3706, 1000209, 3582313):
        raise SafeError("OLAP_KPI_DIFFERS_FROM_G2")
    if k["mean_rating"] != Decimal(3582313) / Decimal(1000209):
        # PostgreSQL NUMERIC division scale differs from Python Decimal context.
        if abs(k["mean_rating"] - Decimal(3582313) / Decimal(1000209)) > Decimal('1e-15'):
            raise SafeError("OLAP_MEAN_NOT_WEIGHTED")
    for level in ["year", "quarter", "month"]:
        group = [r for r in outputs["O4"] if r["time_level"] == level]
        if sum(r["rating_count"] for r in group) != k["rating_count"] or sum(r["rating_sum"] for r in group) != k["rating_sum"]:
            raise SafeError("ROLLUP_COUNT_OR_SUM_MISMATCH")
    quarterly = {}
    for r in outputs["O5"]:
        quarterly.setdefault(r["quarter_start"], []).append(r)
        prev = r["previous_rating_count"]
        if (prev is None or prev == 0) and r["qoq_pct"] is not None:
            raise SafeError("ZERO_PREVIOUS_QOQ_NOT_NULL")
        if r["growth_rank"] is not None and (prev < 100 or r["is_boundary_partial"] or r["previous_is_boundary_partial"]):
            raise SafeError("FIXED_THRESHOLD_OR_BOUNDARY_RANKING_VIOLATED")
    for quarter, data in quarterly.items():
        if len(data) != 18 or len({r["genre_name"] for r in data}) != 18:
            raise SafeError("INCOMPLETE_GENRE_QUARTER_GRID")
        if sum(r["rating_count"] for r in data) != data[0]["genre_assignment_total"]:
            raise SafeError("SHARE_DENOMINATOR_MISMATCH")
        if abs(sum(r["genre_share_pct"] for r in data) - 100) > Decimal('1e-12'):
            raise SafeError("GENRE_SHARES_NOT_100")
    # Independent fact-only reference for the selected O6 slice (no aggregate view).
    direct = rows(conn, """SELECT count(*) AS n,sum(f.rating) AS s FROM dw.fact_rating f
      JOIN dw.dim_user u ON u.user_key=f.user_key
      WHERE u.age_group='18-24' AND f.rated_date>='2000-07-01' AND f.rated_date<'2001-01-01'
      AND EXISTS(SELECT 1 FROM dw.bridge_movie_genre b JOIN dw.dim_genre g ON g.genre_key=b.genre_key
                 WHERE b.movie_key=f.movie_key AND g.genre_name='Comedy')""")[0]
    if sum(r["rating_count"] for r in outputs["O6"]) != direct["n"] or sum(r["rating_sum"] for r in outputs["O6"]) != direct["s"]:
        raise SafeError("O6_FILTER_OR_GRAIN_MISMATCH")
    return {"kpi_matches_g2": True, "rollup_each_level_matches_fact": True, "grid_quarters": len(quarterly),
            "genre_grid_rows": len(outputs["O5"]), "share_sums_100": True, "fixed_threshold": 100,
            "o6_fact_reference_count": direct["n"], "o6_fact_reference_sum": direct["s"]}


def run(c, folder):
    conn = connect(c)
    try:
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn:
            assert_project(conn); cat = catalog(conn)
            before = guard_signature(conn)
            q = queries(); out = {}
            params = {"gender": "F", "genres": None, "ages": None}
            for name in ["O1", "O2", "O3", "O4", "O5", "O6"]:
                args = params if name == "O3" else ({"gender": None, "genres": ["Comedy"], "ages": ["18-24"], "start_date": date(2000,7,1), "end_date": date(2001,1,1)} if name == "O6" else None)
                out[name] = rows(conn, q[name], args)
            checks = verify_outputs(conn, out)
            out["O3_all_genders"] = rows(conn, q["O3"], {"gender": None, "genres": None, "ages": None})
            out["O3_dice"] = rows(conn, q["O3"], {"gender": "F", "genres": ["Comedy", "Drama"], "ages": ["18-24"]})
            pivot = {}
            for r in out["O3"]:
                item = pivot.setdefault(r["genre_name"], {"genre_name": r["genre_name"]})
                item[r["age_group"] + "_count"] = r["rating_count"]
                item[r["age_group"] + "_mean"] = r["mean_rating"]
            out["O3_pivot_F"] = list(pivot.values())
            if guard_signature(conn) != before:
                raise SafeError("SOURCE_SNAPSHOT_CHANGED_DURING_OLAP")
        exports = {name: export_table(folder, name, data) for name, data in out.items()}
        ranked = [r for r in out["O5"] if r["growth_rank"] == 1]
        return {"readonly_session": True, "catalog_views": cat["views"], "checks": checks,
                "parameters": {"O3": params, "O6": {"genres": ["Comedy"], "ages": ["18-24"], "gender": None, "start_date_inclusive": "2000-07-01", "end_date_exclusive": "2001-01-01"}},
                "exports": exports, "kpi": out["O1"][0], "top10": out["O2"], "q3_quarter_winners": ranked,
                "eligible_ranked_rows": sum(r["eligible_for_ranking"] for r in out["O5"]),
                "boundary_quarters": sorted({r["quarter_start"] for r in out["O5"] if r["is_boundary_partial"]}),
                "o3_dice": out["O3_dice"], "source_snapshot_signature": before}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "run"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    args = parser.parse_args()
    run_id, start = uuid.uuid4().hex, time.monotonic()
    folder = ROOT / "results/olap" / ("s07_" + run_id); folder.mkdir()
    report = {"step": "S07", "action": args.action, "run_id": run_id,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],cwd=ROOT,text=True).strip(),
              "code_state": "WORKING_TREE_HASH_AT_RUN", "code_sha256": {p:sha256(ROOT/p) for p in CODE},
              "g2_manifest_run_id": json.loads((ROOT/'results/warehouse/dw_manifest.json').read_text(encoding='utf-8'))['run_id'],
              "personal_rows_exported": False}
    try:
        c = config(args.env_file)
        report.update(status="PASS", result=install(c) if args.action=="install" else run(c,folder))
    except Exception as e:
        report.update(status="FAIL",error_category=getattr(e,'code','OLAP_SQL_OR_LOCAL_ERROR'),sqlstate=getattr(e,'pgcode',None))
    report['duration_seconds']=round(time.monotonic()-start,3)
    try:
        atomic_json(folder/'report.json',report_payload(report))
    except Exception:
        print(json.dumps({'status':'FAIL','run_id':run_id,'error_category':'REPORT_PUBLICATION_FAILED','database_action':args.action}))
        return 2
    print(json.dumps({'status':report['status'],'run_id':run_id,'report':str((folder/'report.json').relative_to(ROOT)),'error_category':report.get('error_category')}))
    return 0 if report['status']=='PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
