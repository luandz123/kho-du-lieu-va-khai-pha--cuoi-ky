# Superset dự án tại máy P1

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
