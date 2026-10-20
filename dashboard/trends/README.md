# 11C — Xu hướng đánh giá theo quý (WAITING_REVIEW)

Mở <http://127.0.0.1:8089/superset/dashboard/2/> bằng trình duyệt desktop, đăng nhập tài khoản Superset cục bộ. Database1 dùng `movielens_bi_reader`; dataset3 `P1_11C_quarter`, dataset4 `P1_11C_genre`; charts9–13. Dashboard1 Tổng quan được giữ nguyên.

## Sử dụng

1. Chọn các **quý trọn vẹn** ở “Quý hiển thị (UTC)”; chọn nhiều quý liên tiếp để xem khoảng. Bỏ chọn là toàn kỳ. Không hỗ trợ khoảng ngày lẻ hoặc bộ lọc tuổi/giới cho O5.
2. Chọn một/nhiều genre, bấm **Apply filters**. Genre chỉ tác động charts10–13. Chart9 luôn biểu diễn tổng rating duy nhất của quý, không chịu genre.
3. **Clear all** trả về toàn kỳ/toàn genre. Bấm **Refresh dashboard** để truy vấn lại. Cuộn xuống xem QoQ và bảng chi tiết; bảng có thanh cuộn ngang/phân trang. NULL hiển thị N/A.
4. Tỷ trọng không chuẩn hóa lại thành100% khi chọn một genre; không cộng các genre thành rating duy nhất. Quý hiển thị được lọc sau phép LAG/rank trên toàn chuỗi.

## SQL và metric

`quarter_dataset.sql`: O4 chỉ `time_level='quarter'`, một dòng/quý UTC. `genre_dataset.sql`: O5 đầy đủ 18×12 ô; xếp hạng trên tập đủ điều kiện toàn bộ genre trước filter hiển thị. Không thay view/bảng PostgreSQL.

| Chart | Dataset / grain | Metric | Bộ lọc |
|---|---|---|---|
|9 tổng duy nhất|3 / quý|MAX(rating_count), đúng một hàng/quý|quý|
|10 lượt gắn genre|4 / quý × genre|MAX(rating_count)|quý, genre|
|11 QoQ|4 / quý × genre|MAX(qoq_pct), đơn vị %|quý, genre|
|12 tỷ trọng|4 / quý × genre|MAX(genre_share_pct), đơn vị %|quý, genre|
|13 chi tiết|4 / quý × genre|MAX count/previous/denominator/share/QoQ/rank; trạng thái là chiều|quý, genre|

Không SUM hoặc AVG các phần trăm theo nhiều quý. MAX chỉ lấy giá trị của một ô grain đã được group đầy đủ; không phải quy tắc tổng hợp tùy ý. Tỷ trọng =100×n_genre/tổng lượt gắn tất cả genre cùng quý. QoQ=100×(n−n_trước)/n_trước; mẫu0/chưa có ⇒ NULL. View S07 zero-fill trước LAG. Rank dùng QoQ giảm, count giảm, genre tăng; n_trước≥100 và cả hai quý không biên. Hạng giữ nguyên khi lọc một genre. Quý2000Q2/2003Q1 thiếu quan sát; quý2000Q3 có quý trước biên nên không rank. Hạng1 âm là giảm ít nhất.

## Lệnh kiểm tra (PowerShell, từ workspace)

```powershell
.\.venv\Scripts\python.exe dashboard/trends/reconcile.py
.\.venv\Scripts\python.exe dashboard/trends/verify.py
```

Hai lệnh chỉ đọc DW/API; reconcile tạo report mới tại `evidence/reconciliation.json`, nên lưu report trước đó bằng run_id nếu cần chạy lại. Không chạy checker11A cũ yêu cầu chỉ2view SELECT sau khi đã bổ sung2view11C. Không chạy lại `create_trends.py` trên instance đã có IDs: guard sẽ từ chối. `prepare.py` chỉ dùng cho GRANT đúng phạm vi sau khi kiểm role được quản lý và credential có sẵn; không thay mật khẩu. Tái tạo trên instance khác phải kiểm IDs trước, không chép IDs rồi coi đã có dashboard.

SQL GRANT thực chạy ở `bi_grants.sql`. Credential chỉ trong `dashboard/superset/.env.bi` ignored. PUBLIC TEMP mặc định còn, không có quyền ghi bảng dự án; P2/hai máy chưa xác minh. Chưa export/import/restore, chưa kiểm full refresh mới với helperS07, chưa11B/G3.

Bàn giao đầy đủ: `docs/P1/trends_handoff.md`; số liệu API/SQL và ảnh thật tại `evidence/`. JSON chỉ tổng hợp, không có lịch sử từng user. Trạng thái11C WAITING_REVIEW, chưa commit/push/PR.

Cập nhật20/10/2026: điều phối chấp nhận chức năng11C; đang công bố PR theo lệnh riêng. Trạng thái PR/commit và kiểm công bố xem docs/P1/trends_publication.md tính từ repository. Các nhãn chờ review kết quả ở trên là lịch sử; không tự merge hoặc chuyển11B/G3.
