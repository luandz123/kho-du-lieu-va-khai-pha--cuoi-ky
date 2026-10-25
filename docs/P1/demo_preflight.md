# Kiểm tra demo Superset 8089 trước bảo vệ

Ngày kiểm: **25/10/2026**. Phạm vi: khởi động hai container dự án hiện hữu, truy vấn chỉ đọc và UI/API chính thức. **WAITING_REVIEW; G4 vẫn ĐẠT I01–I15, G5 chưa hoàn thành.**

## Hiện trạng và phạm vi khởi động

Trước thao tác, cả `btl-movielens-superset-metadata-1` và `btl-movielens-superset-web-1` đều `exited`, exit 255, `OOMKilled=false`, trường runtime Error rỗng. Hai thời điểm FinishedAt đều khoảng `2026-10-24T12:30:01Z`. Docker Desktop/backend đang chạy và phản hồi; Docker Engine 29.1.5 truy cập được. Đây là quan sát, **chưa xác định nguyên nhân dừng**. Không suy rằng false của OOMKilled loại trừ mọi vấn đề tài nguyên.

Đọc 250 dòng log gần nhất mỗi container (metadata có 238 dòng); log thô giữ trong `tmp/pre_submit_20261025/` ignored. Metadata có hai dòng chứa shutdown; web có chín dòng chứa ERROR và tám dòng Traceback. Không có đủ bằng chứng gắn chúng với nguyên nhân exit 255; không công bố log thô hoặc nội dung có thể chứa cấu hình riêng. Không thay image, volume, cấu hình, quyền hoặc dữ liệu để xử lý.

Đã chạy `docker start` đúng hai tên được giao, không compose up/recreate/build/upgrade. Sau đó cả hai running/healthy, cổng web vẫn bind `127.0.0.1:8089`. Không start/stop hoặc sửa tài nguyên 8091/8092 hay dự án khác.

## Lệnh trước demo

Chạy tại máy P1, không chứa credential:

```powershell
docker version --format '{{.Server.Version}}'
docker inspect --format '{{.Name}} | {{.State.Status}} | {{.State.ExitCode}} | {{.State.OOMKilled}}' btl-movielens-superset-metadata-1 btl-movielens-superset-web-1
docker start btl-movielens-superset-metadata-1
docker inspect --format '{{.State.Health.Status}}' btl-movielens-superset-metadata-1
# Chỉ tiếp khi metadata healthy, sau đó:
docker start btl-movielens-superset-web-1
docker inspect --format '{{.State.Health.Status}}' btl-movielens-superset-web-1
(Invoke-WebRequest http://127.0.0.1:8089/health).StatusCode
```

Nếu container đã running/healthy thì chỉ kiểm, không khởi tạo lại. Nếu tên không tồn tại, health không đạt hoặc endpoint không mở: giữ trạng thái, thu log riêng và báo lỗi; không tự thay bằng instance khác hoặc dùng ETL/restore chữa lỗi giao diện. Không đưa `docker inspect` đầy đủ hoặc `.env` lên chat/Git vì có thể chứa bí mật.

## Dấu hiệu sẵn sàng và ca trình diễn

Đăng nhập bằng tài khoản demo đã cấu hình cục bộ; không ghi mật khẩu vào tài liệu hoặc URI. Dùng cửa sổ trình duyệt đủ rộng để thấy filter và KPI; ở pane hẹp dashboard có cuộn ngang/dọc, cần mở rộng cửa sổ khi bảo vệ. Không sửa layout để che vấn đề hiển thị.

| Trang | URL | Ca kiểm và số phải đọc đúng |
|---|---|---|
| Tổng quan | http://127.0.0.1:8089/superset/dashboard/1/ | No filter: 1.000.209 rating; tổng điểm 3.582.313; mean 3,5815644530; 6.040 user; 3.706 phim có rating; danh mục cố định 3.883 |
| Tổng quan có thời gian | Cùng dashboard 1 | Q3/2000, từ 01/07 đến trước 01/10 UTC: 324.864 rating; filter trước tổng hợp/Top10, KPI danh mục vẫn cố định |
| Xu hướng | http://127.0.0.1:8089/superset/dashboard/2/ | Chọn 2001 Q1 và Animation: count 1.715, prev 20.068, mẫu số genre 63.335, share≈2,70782348%, QoQ≈−91,45405621%, hạng 1 là giảm ít nhất |
| Sở thích | http://127.0.0.1:8089/superset/dashboard/3/ | Toàn bộ: assigned 6.038, baseline 6.038, thiếu bằng chứng 2; model kmeans_k4_seed42 |
| Sở thích lọc | Cùng dashboard 3 | Cụm1/F/25–34: assigned 170; baseline 6.038 và thiếu bằng chứng 2 giữ cố định; heatmap đủ 18 genre của cụm1, không chịu tuổi/giới |

Thao tác bộ lọc là trạng thái xem, không Save/Edit dashboard. Đợi chart tải xong trước khi đọc số; reset/Clear all khi chuyển ca. Không cộng count các genre thành tổng rating, không diễn giải rating là lượt xem hoặc nhu cầu hiện tại.

## Bằng chứng mới

Script [dashboard/demo_preflight.py](../../dashboard/demo_preflight.py) đăng nhập bằng API chính thức; không sửa metadata DB. SQL độc lập dùng connection `REPEATABLE READ`, `READ ONLY` vào đúng `movielens_btl`; chỉ SELECT. Superset truy vấn thực bằng `movielens_bi_reader`. Không coi READ ONLY của connection trực tiếp là bằng chứng một tài khoản quản trị không có quyền ghi.

Lần kiểm SQL/API mới: run `3ca533f8a35648e69245fb145f55c271`, [receipt](../../results/warehouse/demo_preflight_20261025/preflight_3ca533f8a35648e69245fb145f55c271.json), PASS. Đối chiếu KPI toàn kỳ/Q3, Animation Q1/2001 và hai ca Sở thích bằng dữ liệu tổng hợp từ fact/bridge/registry. Hash cấu hình nghiệp vụ của 23 chart và ba dashboard trước/sau giống nhau. Không gọi checker lịch sử có guard analytics rỗng; không sửa hoặc chạy lại các report trước đây.

```powershell
.\tmp\s12a-venv\Scripts\python.exe dashboard/demo_preflight.py
```

Mỗi lần chạy ghi receipt mới, giữ FAIL nếu có; không ghi đè bằng chứng lịch sử. Lệnh này chỉ kiểm dữ liệu/dashboard, không chạy ETL/G3/evaluator/CLI huấn luyện. Bằng chứng UI mới nằm cùng thư mục receipt: ảnh Tổng quan, Xu hướng có filter và Sở thích; quan sát UI bổ sung được ghi trong `ui_observation.json`. Ảnh ở pane hẹp không thay bảng/receipt số chính xác.

## Phương án dự phòng

1. Khi web chậm: kiểm health và connection, đợi hoặc Refresh dashboard; chỉ khởi động đúng container đang dừng. Nếu cần sửa cấu hình/quyền/dữ liệu thì báo điều phối trước.
2. Khi không khôi phục được trong thời gian demo: dùng PDF báo cáo, ảnh UI và receipt SQL/API đã lưu, ghi rõ đó là bằng chứng lịch sử thay vì gọi là demo live.
3. Có thể trình bày SQL chỉ đọc trên DW đang có nếu kết nối sẵn; không ETL/full refresh, reload model, restore, mở firewall hoặc đưa credential quản trị cho người khác.
4. Backup/clone/instance thử giữ nguyên để review; việc phục hồi là bước riêng cần được giao. ZIP import, metadata restore và DW restore là ba cơ chế khác nhau.

Không kết luận hệ thống ổn định lâu dài chỉ từ một lần health/PASS. Trước buổi bảo vệ cần kiểm lại ngắn theo checklist này; không đăng ký tác vụ tự khởi động hoặc đổi restart policy trong lượt hiện tại.
