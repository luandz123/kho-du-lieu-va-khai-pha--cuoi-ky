# Dashboard Tổng quan — 11A

URL thật: http://127.0.0.1:8089/superset/dashboard/1/

Superset 6.1.0 dự án 8089; database 1, datasets 1/2, charts 1–8, dashboard 1. Tên/ID đầy đủ trong object_ids.json và evidence/final_verification.json. Bàn giao chi tiết: docs/P1/overview_handoff.md tính từ gốc repository.

- ratings_dataset.sql giữ một dòng user–movie, typed UTC timestamp, không genre bridge; catalog_dataset.sql là danh mục cố định.
- metrics.json, chart_definitions.json, dashboard_definition.json chứa SQL/cấu hình an toàn. Top 10 dùng ROW(count,weightedmean,-movie_id) DESC để giữ ba khóa phá hòa.
- Native time filter tác động chart 1/2/3/4/6/7/8 trước aggregate/Top10; chart 5 danh mục cố định 3883.
- superset_api.py dùng REST API chính thức, login cục bộ trong bộ nhớ; token không lưu/in. Credential BI riêng dashboard/superset/.env.bi bị ignore.
- check_bi_reader.py, reconcile.py, verify_overview.py là lệnh kiểm đã chạy; xem handoff. Không chạy lại create_overview.py trên instance hiện có; script cần database/dataset đã đăng ký, chưa bootstrap máy sạch.
- evidence/ chứa thống kê, ảnh thật và cả FAIL checker đã sửa, không có user history. ZIP export thật trong export/overview_superset.zip chỉ cục bộ, đã scan, chưa kiểm import.

Role BI chỉ SELECT hai view, không DML/CREATE/owner/membership; PUBLIC TEMP mặc định giữ nguyên và được nêu giới hạn. Không xác nhận P2 intake/hai máy, không full refresh/11B/11C/G3/firewall. **11A WAITING_REVIEW**, chưa commit/push/PR.
