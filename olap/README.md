# S07 OLAP trên DW dự án

Nguồn PostgreSQL movielens_btl đã kiểm nhận G2; không chạy lại ETL. Chạy từ gốc repository bằng Python riêng:

```powershell
.\.venv\Scripts\Activate.ps1
python -m olap.run_olap run --env-file .env
python tests/warehouse/check_s07_olap.py
python -m unittest discover -s tests/warehouse -p "test_*.py"
```

`run` chỉ đọc, xuất O1–O6 cùng ba biến thể O3 vào thư mục run mới results/olap/s07_<run_id>. Report chứa hash code/CSV, snapshot G2, tham số, checks và dữ liệu tổng hợp. Không chứa user_id hoặc lịch sử từng user. Decimal JSON dùng chuỗi, ngày dùng ISO; CSV UTF-8, LF. Các CSV canonical/raw vẫn bị ignore. Chỉ cho phép Git bộ CSV tổng hợp của run đã review trong .gitignore; run khác mặc định cục bộ.

Trên DW mới chưa có sáu view, lệnh sau tạo view trong một transaction sau kiểm marker/catalog và allowlist:

```powershell
python -m olap.run_olap install --env-file .env
```

**Máy P1 đã install thành công, không chạy lại install.** Khi tên đã tồn tại, script dừng để kiểm tra thay vì replace. Không tạo database, table hoặc thay bốn view contract. Fixture tạo schema riêng từ ràng buộc được duyệt, nạp dữ liệu tự tạo rồi rollback toàn schema, kiểm production giữ nguyên.

queries.sql gồm sáu khối có tên O1–O6. Các placeholder psycopg2 được bind, không nối chuỗi tham số. `run` dùng O3 gender=F; xuất thêm mọi giới, dice F/18–24/Comedy+Drama và pivot F. O6 dùng Comedy, tuổi 18–24, mọi giới, từ 2000-07-01 đến trước 2001-01-01. Dùng `queries()` và `rows()` với connection READ ONLY để bind bộ lọc khác; start_date bao gồm, end_date loại trừ; genres nhiều phần tử là phép hợp qua EXISTS. Không cộng các genre thành rating duy nhất.

View có grain/metric/mẫu số ghi ngay trên SQL. O5 áp dụng toàn bộ genre/demographic, mẫu số là lượt gắn genre cùng quý. QoQ trước 0 NULL, ngưỡng trước >=100 cố định, loại quý biên và quý ngay sau biên khỏi xếp hạng. Các quý nội bộ vẫn chỉ là quan sát lịch sử.

Catalog helper S05 được mở allowlist đúng bộ sáu view bổ sung; không đổi chuẩn hóa, DDL bảng hoặc guard bước lịch sử. Không dùng hash code S07 thay cho bundle 6D cũ. Không chạy load S05/6A/6B/6C trên snapshot hiện tại.

Xem docs/P1/olap_findings.md và docs/agent/steps/P1/S07.md để đọc số liệu, bằng chứng và giới hạn. Chưa dashboard, Superset BI, G3 hoặc thay quyền. Session READ ONLY không chứng minh account chỉ có quyền đọc.
