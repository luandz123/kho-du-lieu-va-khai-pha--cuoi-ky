# 11B-3 · Dashboard sở thích

Dashboard thực: http://127.0.0.1:8089/superset/dashboard/3/ (Superset 6.1.0, cổng 8089).
Database 1 dùng `movielens_bi_reader`; datasets **5 users**, **6 profile**; charts **14–23**.
Mở dashboard, đăng nhập cục bộ, chọn filter rồi **Apply filters**; **Clear all** trả toàn bộ. **Refresh dashboard** đọc lại các view active+valid sau khi có thay đổi được duyệt. Không chạy lại script tạo trên instance hiện có.

## Nguồn và grain

`users_dataset.sql`: active user cluster JOIN `dw.v_ml_users`, **một dòng/user**, giữ cả insufficient với cluster NULL. Window tính mẫu số trên toàn cohort trước WHERE native ở truy vấn ngoài. Không có join profile vào user.

`profile_dataset.sql`: active profile, **một dòng/cụm×genre**; MAX(mean_preference) cho mỗi ô. Không SUM n_users lặp trên 18 genre. Profile P2 là trung bình vector tỷ lệ genre từ rating tích cực ≥4; không phải tỷ lệ số user thích genre, lượt xem hoặc doanh thu.

Tên mô tả từ `docs/P2/clustering_interpretation.md`: 0 đa dạng/cân bằng, 1 Drama/tình cảm, 2 Comedy, 3 Action/Sci-Fi/Thriller. Nhân khẩu học không tham gia huấn luyện. Không suy nhân quả hoặc sở thích cùng một người thay đổi theo tuổi.

## Metric và mẫu số

| Chart | ID | Metric / mẫu số |
|---|---:|---|
|Assigned được lọc|14|COUNT user WHERE status=assigned|
|Thiếu bằng chứng cố định|15|COUNT status=insufficient_evidence trên toàn model, hiện 2|
|Baseline cố định|16|MAX(assigned_total), hiện 6.038|
|Quy mô cụm|17|COUNT assigned; 100×COUNT / MAX(assigned_total=6038)|
|Phiên bản model|18|model_version, COUNT assigned và insufficient, không lọc|
|Heatmap|19|MAX(mean_preference) cho cluster×genre; thang màu cố định 0–0,4; tooltip dạng %; không chuẩn hóa theo rank|
|Giới tính theo cụm|20|COUNT đang lọc; quy mô cụm gốc; 100×COUNT/quy mô cụm gốc; baseline giới cố định/6038|
|Baseline giới|21|COUNT assigned theo F/M trên toàn cohort|
|Tuổi theo cụm|22|COUNT đang lọc; quy mô cụm gốc; 100×COUNT/quy mô cụm gốc; baseline tuổi cố định/6038|
|Baseline tuổi|23|COUNT assigned theo 7 nhóm tuổi trên toàn cohort|

Baseline luôn cố định toàn bộ 6.038 assigned, **không chịu cả filter nhân khẩu học**. Khi đồng thời lọc tuổi/giới, % cụm là phần user thỏa điều kiện trên **quy mô gốc cụm**; tổng đang hiển thị có thể dưới 100%. Baseline từng tuổi/giới vẫn là phân bố đơn biến toàn cohort, không phải baseline có điều kiện theo filter còn lại. Không diễn giải hai tỷ lệ đó như một so sánh nhân quả hoặc đã điều chỉnh nhân khẩu học.

## Scope native filters

| Filter | 14 /17 /20 /22 | Heatmap19 | 15 /16 /18 /21 /23 |
|---|---|---|---|
|Cụm 0–3|Có|Có|Không|
|Nhóm tuổi|Có|Không|Không|
|Giới tính|Có|Không|Không|

Filter cụm lấy options từ dataset profile (chỉ 0–3), không chọn NULL ngoài ý muốn. Nhóm thiếu bằng chứng luôn có KPI riêng ngoài mọi scope. Heatmap giữ toàn bộ profile cụm dù chọn tuổi/giới; không trình bày như đã tái huấn luyện/tái tính.

## Kiểm tra an toàn

PowerShell tại workspace, dùng đúng môi trường P1:

```powershell
.\.venv\Scripts\Activate.ps1
python tests/warehouse/check_preferences_fixture.py
python dashboard/preferences/reconcile.py
python dashboard/preferences/verify.py
```

Các lệnh trên chỉ đọc DB; reconcile gọi chart/data API với truy vấn tổng hợp. Không gọi loader G3, ETL hoặc fixture yêu cầu analytics rỗng. `reconcile.py` lưu FAIL riêng nếu lỗi; trước khi chạy lại hãy giữ bản PASS cũ bằng tên run_id. `verify.py` lưu quan sát mới, không thay cấu hình Superset.

`prepare.py` là thao tác chuẩn bị có GRANT giới hạn ba view, đã chạy, có guard bảo toàn baseline; không chạy lại để ghi đè baseline. `create_preferences.py` chỉ dùng lần đầu khi chưa có IDs; guard chặn chạy lại. Mọi thay đổi object hiện có phải kiểm tra IDs/API trước. Cấu hình SQL/metric/filter thực được lưu qua REST API chính thức; không sửa metadata DB.

Quyền bổ sung trong `bi_grants.sql`. Credential chỉ ở cấu hình local ignored; không gửi credential quản trị. Quyền hiệu lực được kiểm từ container Superset: SELECT đúng 7 view, không project write/CREATE/role membership; session READ ONLY không được dùng thay bằng chứng quyền. PUBLIC TEMP mặc định vẫn tồn tại.

API độc lập ba tổ hợp, ảnh UI và snapshot cấu hình trong `evidence/`. 11A/11C được so 19 object và chạy truy vấn toàn kỳ/có filter; không sửa nghiệp vụ. Không chạy lại full pipeline. Superset có thể tự lưu JSON whitespace/cấu hình màu khi render; checker so cấu trúc bố cục và filter nghiệp vụ, lưu bản observed riêng.

Tham khảo API plugin heatmap đúng phiên bản: [Apache Superset 6.1.0 control panel](https://github.com/apache/superset/blob/6.1.0/superset-frontend/plugins/plugin-chart-echarts/src/Heatmap/controlPanel.tsx). Không bật normalized/rank, không hiển thị nhãn 72 giá trị chồng lấn; giá trị chính xác có trong API đối soát/tooltip.

Giới hạn: bảng nhân khẩu học cần cuộn ngang để xem đủ cột; desktop heatmap kiểm ở 1280×900, panel hẹp chưa tối ưu. Chưa export/import/restore ba dashboard; chưa kết nối hai máy/P2 intake; chưa full refresh mới với helper S07/G3. Không tự nâng các giới hạn thành PASS.
