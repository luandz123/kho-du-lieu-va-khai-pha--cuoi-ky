# Superset dự án tại máy P1

Quan sát mới: PR14 đã MERGED bên ngoài agent tại 5a42c73c39c00780b2d5442c45662d93bdf0f23b; agent không merge. Gói công bố ef82fc4 gồm50file/blob đã kiểm. Hồ sơ trạng thái sau mởPR đang local/chưa commit-push, xem docs/P1/overview_post_merge_observation.json; các mụcOPEN dưới đây giữ lịch sử. Dừng, chưa11C/11B.

Hiện hành19/10/2026: [PR #14 — 11A](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/14) OPEN/chờ review, chưa merge/11C/11B. 11A đã được điều phối chấp nhận chức năng; các mục chưa được giao công bố/chưa commit phía dưới giữ lịch sử. Hồ sơ mới docs/P1/overview_publication.json.

## Cập nhật 11A, 19/10/2026

Instance dự án đã khởi động lại bằng hai container hiện có, không init hoặc đổi metadata/key. Đã đăng nhập UI/API và tạo dashboard Tổng quan thật tại http://127.0.0.1:8089/superset/dashboard/1/ . Database1 dùng role BI mới chỉ SELECT hai view; cấu hình bí mật riêng dashboard/superset/.env.bi bị Git ignore, khác metadata/admin và `.env` SQL quản trị gốc. Không in/hash các tệp bí mật.

SQL/metric/filter, quyền thực, ba khoảng đối soát và ảnh ở dashboard/overview/; bàn giao docs/P1/overview_handoff.md. **11A WAITING_REVIEW**, chưa commit/push/PR/11B/11C/G3. Reader thực có bằng chứng mới tại P1; không suy P2 đã truy cập. PUBLIC TEMP mặc định còn, không có quyền ghi bảng/view dự án. ZIP export thật đã scan chỉ cục bộ; import chưa kiểm. Các mục S02/chưa dashboard bên dưới là lịch sử.

Phiên bản S02-P1-v1. Instance được kế thừa từ workspace cũ, không tạo lại metadata hoặc đổi password/key.

| Thành phần | Phiên bản/vị trí |
|---|---|
| Superset | 6.1.0, image btl-movielens-superset:6.1.0-local |
| Driver trong image | psycopg2-binary 2.9.13 |
| Metadata | PostgreSQL17.11 trong service metadata, khác PostgreSQL Windows/DW |
| Web | http://127.0.0.1:8089/login/ |
| Dịch vụ khác | Superset cũ8088/Airflow/RabbitMQ giữ nguyên |

`compose.yaml`, Dockerfile, superset_config.py, init_metadata.py và .dockerignore được chép chọn lọc từ bản cũ. `.env` Superset cũ được bảo toàn bằng thao tác sao chép tệp cục bộ, không đọc/in/hash; không nằm trong Git. File này chỉ chứa key/password metadata/admin Superset, khác `.env` gốc dành cho SQL Windows.

## Khởi động và kiểm tra

Từ thư mục dự án:

```powershell
docker compose -f dashboard/superset/compose.yaml config --quiet
docker compose -f dashboard/superset/compose.yaml start metadata web
.\.venv\Scripts\python.exe tests/warehouse/check_superset.py --env-file .env
```

S02 đã khởi động **container hiện có** bằng docker start để giữ nguyên image/env/volume và tránh init lại. Compose cùng project name nhận diện instance đó. Nếu tạo mới tại máy khác: chuẩn bị `.env` Superset cục bộ bằng mẫu, sinh bí mật riêng cho môi trường mới; build image rồi `docker compose -f dashboard/superset/compose.yaml up -d`. Máy mới phải tải được image apache/superset:6.1.0 và postgres:17.11; S02 chưa kiểm rebuild từ mạng trên máy sạch. Không dùng `latest`. Image ID thực và volume được ghi trong hồ sơ S02.

Không chạy `down -v`, xóa volume hoặc sinh lại SECRET_KEY/password cho metadata hiện có. Muốn đổi môi trường phải có quy trình sao lưu/chuyển đổi được giao riêng.

## Đăng nhập và kết nối DW

Username admin của bản kế thừa là `btl_admin`; mật khẩu nằm trong `.env` Superset cục bộ. Người dùng tự xem/nhập tại máy, không gửi chat. HTTP200 trang login không chứng minh đăng nhập UI thành công hoặc đã có dashboard.

Trong container, `localhost` là container. Dùng `host.docker.internal` để truy cập PostgreSQL Windows, hoặc tên service nếu DW ở cùng mạng Compose. Checker chỉ đọc cấu hình gốc qua tham số rõ ràng, chuyển credential vào container bằng stdin, không in URI/password; chỉ SELECT1 và kiểm tra view/quyền, không tạo schema.

Kết nối SQL bằng tài khoản hiện có không chứng minh tài khoản BI chỉ đọc đã được cấp. View DW chưa tạo thì quyền đọc cuối cùng chưa nghiệm thu; không tạo bảng nghiệp vụ ở S02. Ba dashboard/export/import thuộc bước11, không có ZIP giả.

Nguồn: [Superset Docker Compose](https://superset.apache.org/docs/installation/docker-compose/).
