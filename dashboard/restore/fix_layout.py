"""Sửa bố cục 3 dashboard bị lệch sau khi nhập ZIP (tiêu đề ô không khớp biểu đồ,
thêm hàng ô trùng ở cuối).

Bố cục đúng lấy từ ảnh chụp gốc evidence/production_before.json; mỗi ô được trỏ lại
đúng biểu đồ theo UUID (UUID không đổi khi export/import, còn ID thì đổi). Chỉ ghi
position_json của dashboard qua REST API chính thức; không đụng SQL, dataset, bộ lọc.

Mặc định chỉ kiểm tra (không ghi). Thêm --apply để sửa:
    python dashboard/restore/fix_layout.py                         # xem cần sửa gì
    python dashboard/restore/fix_layout.py --apply                 # sửa + kiểm lại
    python dashboard/restore/fix_layout.py --base http://127.0.0.1:8091 --env-file dashboard/restore/.env
Mật khẩu btl_admin đọc từ ADMIN_PASSWORD trong --env-file; thiếu thì hỏi khi chạy.
"""
import argparse
import copy
import getpass
import http.cookiejar
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "dashboard/restore/evidence/production_before.json"


class API:
    def __init__(self, base, password):
        self.base = base.rstrip("/")
        self.token = self.csrf = None
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        login = {"username": "btl_admin", "password": password, "provider": "db", "refresh": True}
        self.token = self.request("POST", "/api/v1/security/login", login)["access_token"]
        self.csrf = self.request("GET", "/api/v1/security/csrf_token/")["result"]

    def request(self, method, path, body=None):
        headers = {"Content-Type": "application/json", "Referer": self.base + "/"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.csrf:
            headers["X-CSRFToken"] = self.csrf
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, method=method, headers=headers, data=data)
        try:
            with self.opener.open(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            # Không in nội dung phản hồi: API database có thể trả lại thông tin kết nối.
            raise SystemExit(f"Lỗi HTTP {e.code} khi gọi {method} {path.split('?')[0]}") from None
        except urllib.error.URLError as e:
            raise SystemExit(f"Không kết nối được {self.base}: {e.reason}. Superset đã bật chưa?") from None

    def all(self, kind):
        q = urllib.parse.quote("(page_size:100)")
        items = self.request("GET", f"/api/v1/{kind}/?q={q}")["result"]
        return [self.request("GET", f"/api/v1/{kind}/{x['id']}")["result"] for x in items]


def chart_ids(layout):
    return [n["meta"]["chartId"] for n in layout.values()
            if isinstance(n, dict) and n.get("type") == "CHART"]


def read_password(env_file):
    path = Path(env_file)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ADMIN_PASSWORD="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    return getpass.getpass("Mật khẩu btl_admin: ")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # PowerShell mặc định không in được tiếng Việt
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8089")
    ap.add_argument("--env-file", default=str(ROOT / "dashboard/superset/.env"))
    ap.add_argument("--apply", action="store_true", help="ghi bố cục đã sửa (mặc định chỉ kiểm tra)")
    args = ap.parse_args()

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["objects"]
    api = API(args.base, read_password(args.env_file))

    charts = api.all("chart")
    by_uuid = {c["uuid"]: c["id"] for c in charts}
    by_name = {c["slice_name"]: c["id"] for c in charts}
    dashboards = {d["uuid"]: d for d in api.all("dashboard")}
    titles = {d["dashboard_title"]: d for d in dashboards.values()}

    plan, problems = [], []
    for key in ("dashboard/1", "dashboard/2", "dashboard/3"):
        src = snap[key]
        target = dashboards.get(src["uuid"]) or titles.get(src["dashboard_title"])
        if target is None:
            problems.append(f"Không tìm thấy dashboard “{src['dashboard_title']}” trên {args.base}")
            continue
        layout = json.loads(src["position_json"])
        for node in layout.values():
            if isinstance(node, dict) and node.get("type") == "CHART":
                old = node["meta"]["chartId"]
                c = snap[f"chart/{old}"]
                new = by_uuid.get(c["uuid"]) or by_name.get(c["slice_name"])
                if new is None:
                    problems.append(f"Thiếu biểu đồ “{c['slice_name']}” trên {args.base}")
                    continue
                node["meta"].update(chartId=new, uuid=c["uuid"], sliceName=c["slice_name"])
        current = json.loads(target.get("position_json") or "{}")
        ok = current and chart_ids(current) == chart_ids(layout) and len(chart_ids(current)) == len(set(chart_ids(current)))
        plan.append((target, layout, current, ok))
        print(f"- [{target['id']}] {target['dashboard_title']}: hiện có {len(chart_ids(current))} ô, "
              f"đúng phải là {len(chart_ids(layout))} ô → {'ĐÚNG' if ok else 'CẦN SỬA'}")

    if problems:
        print("\nKhông sửa được vì:", *problems, sep="\n  ")
        sys.exit(2)
    todo = [p for p in plan if not p[3]]
    if not todo:
        print("\nCả 3 dashboard đã đúng bố cục, không cần sửa.")
    elif not args.apply:
        print(f"\n{len(todo)} dashboard cần sửa. Chạy lại với --apply để sửa.")
        return
    else:
        backup = ROOT / f"dashboard/restore/backup_layout_{datetime.now():%Y%m%d_%H%M%S}.json"
        backup.write_text(json.dumps({str(t["id"]): cur for t, _, cur, _ in todo}, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        print(f"\nĐã sao lưu bố cục cũ: {backup}")
        for target, layout, _, _ in todo:
            api.request("PUT", f"/api/v1/dashboard/{target['id']}",
                        {"position_json": json.dumps(layout, ensure_ascii=False)})
            got = json.loads(api.request("GET", f"/api/v1/dashboard/{target['id']}")["result"]["position_json"])
            assert chart_ids(got) == chart_ids(layout), "Ghi bố cục không thành công"
            print(f"  Đã sửa [{target['id']}] {target['dashboard_title']}")

    # Kiểm tra mọi biểu đồ trên 3 dashboard đều truy vấn được dữ liệu từ kho
    print("\nKiểm tra từng biểu đồ truy vấn kho dữ liệu:")
    failed = 0
    for target, layout, _, _ in plan:
        for cid in chart_ids(layout):
            ch = api.request("GET", f"/api/v1/chart/{cid}")["result"]
            if not ch.get("query_context"):
                print(f"  ?   [{cid}] {ch['slice_name']} (chưa có query_context, mở dashboard để xem trực tiếp)")
                continue
            ctx = copy.deepcopy(json.loads(ch["query_context"]))
            ctx["force"] = True
            res = api.request("POST", "/api/v1/chart/data", ctx)["result"][0]
            good = res.get("status") == "success"
            failed += not good
            print(f"  {'OK ' if good else 'LỖI'} [{cid}] {ch['slice_name']}")
    print("\nKẾT QUẢ:", "TẤT CẢ BIỂU ĐỒ CHẠY ĐƯỢC" if not failed else f"{failed} biểu đồ lỗi")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
