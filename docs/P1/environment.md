# Môi trường P1 Bước 2

Phiên bản P1-S02-v1, 15/10/2026, WAITING_REVIEW. Workspace `D:/kho-du-lieu-va-khai-pha--cuoi-ky`, nhánh `p1-s02-env`, nền G0/main `eff54aee`. S01 được duyệt qua R-P1-01, G0 PR#1 đã MERGED; bước này được giao riêng, chưa được tự duyệt/đẩy.

## Python và thư viện

Runtime nền có sẵn Python3.12.14, Windows AMD64, tại `C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Đã dùng `-m venv .venv`; runtime chạy dự án là `D:/kho-du-lieu-va-khai-pha--cuoi-ky/.venv/Scripts/python.exe`. Pip25.0.1, `include-system-site-packages=false`, mọi import P1 từ `.venv/Lib/site-packages`. Không đổi Python3.14 toàn hệ thống, PATH hay execution policy.

Đây là sử dụng có chủ đích runtime cục bộ, không là Python3.12 cài toàn hệ thống. Nếu bundle/cache thay đổi cần tạo lại venv bằng Python3.12 độc lập phù hợp; chưa kiểm tái lập máy sạch tại S02. P2 tự báo3.12.3/Linux, cùng dòng3.12 nhưng patch/platform khác; chưa chạy ML trên P1 hoặc kiểm PR P2.

| Thư viện trực tiếp | Phiên bản đã cài/import |
|---|---|
| NumPy | 2.0.2 |
| Pandas | 2.3.3 |
| SQLAlchemy | 2.0.43 |
| psycopg2-binary | 2.9.10 |
| python-dotenv | 1.1.1 |

`requirements-p1.txt` khóa11distribution thực tế gồm phụ thuộc gián tiếp. `requirements.txt` gốc chỉ include P1 tại S02; P2 sở hữu requirements riêng, P1 chưa hợp nhất ở đây. Cài bằng wheel vào venv, không nâng pip/cài compiler toàn hệ thống. `pip check` đạt; NumPy/Pandas tính toán và SQLAlchemy SELECT1 trong SQLite memory đạt, chỉ là smoke check thư viện.

## Cấu hình và kiểm tra SQL

`.env` gốc đã tạo bằng mẫu, không in/hash. Điền database có sẵn/user/password tại máy rồi chạy checker như README. Chỉ `SELECT 1` và đọc server_version trong transaction readonly với timeout; không tạo/nạp bảng. Checker không tự tìm mật khẩu pgAdmin/.pgpass hoặc đọc.env khi chưa được chỉ định. Nếu thiếu biến: WAITING_LOCAL_CONFIG/exit2; không coi PostgreSQL Running/readiness là đăng nhập thành công.

Checker Superset truyền cấu hình vào container qua stdin, không argv/URI/log; với localhost đổi sang host.docker.internal. Kiểm SELECT1/hiện diện view/quyền SELECT không tạo DW hoặc cấp role. Tài khoản SQL bất kỳ chạy được không chứng minh đã có role BI chỉ đọc. DW chưa tạo thì nghiệm thu quyền đọc cuối cùng chờ đúng bước.

## Superset kế thừa

Đã chọn lọc5file cấu hình từ workspace cũ vào dashboard/superset và giữ `.env` Superset cục bộ bằng sao chép, không đọc/in/hash. Không đổi SECRET_KEY/password hoặc ghi vào volume mới. Khởi động lại đúng container hiện có, không recreate/init lại, không chạm instance8088/Airflow/RabbitMQ.

- Superset6.1.0, image `btl-movielens-superset:6.1.0-local`, image ID `sha256:dcfd9db7f3085ec5370aa867ace84a6efd893d89d6cf650e8e3f4620f0fa64c1`.
- Driver image psycopg2-binary2.9.13, độc lập driver venv Windows2.9.10.
- Docker Engine29.1.5 Linux, Compose5.0.1, WSL distro docker-desktop version2 Running.
- Project `btl-movielens-superset`; metadata postgres17.11, volume `btl-movielens-superset_metadata_data`; home volume `btl-movielens-superset_superset_home`.
- Web chỉ bind127.0.0.1:8089. Web/metadata healthy, health/login HTTP200. Metadata query `SELECT 1,current_database()` trả1/superset_metadata. Đây là metadata, không là Windows DW.
- Container→host.docker.internal:5432 TCP PASS; SQL/quyền DW chỉ khi có cấu hình đầy đủ. Chưa user UI login, chart, dashboard hoặc export/import.

Compose config --quiet đạt, không in bản cấu hình đã bung secret. Dockerfile ghim6.1.0/driver2.9.13, metadata17.11; image base apache/superset:6.1.0 không còn trong local cache, chưa kiểm rebuild/download máy sạch. Giữ image dự án hiện có. Không dùng latest, down-v, reset metadata hoặc cài tool hệ thống mới.

## Quyền tệp và phạm vi

Đã tạo thư mục P1 và raw/processed. Thư mục P2 chỉ tạo rỗng nếu thiếu, không viết file P2/source_manifest. Ignore kiểm bằng git check-ignore, tracked list không có .env/raw/processed/venv/dump; không cần git rm --cached vì chưa có tệp nhạy cảm tracked. Template nested.env.example được cho phép có chọn lọc, secret.env vẫn bị chặn.

S02 không tải MovieLens, tạo schema/bảng nghiệp vụ/ETL/mô hình hoặc dashboard. Chưa stage/commit/push/PR. Cần duyệt S02 trước Đẩy mốc; nhánh mới luôn bỏ codex/.

Nguồn xác minh phương pháp: [Python3.12 venv](https://docs.python.org/3.12/library/venv.html), [Superset Compose](https://superset.apache.org/docs/installation/docker-compose/).

## Kết quả cập nhật P1-S02-v2

Ngày15/10/2026 lúc20:17–20:18 Asia/Bangkok: SELECT1 bằng.env hiện tại từ Windows và container đều PASS/server17.11/exit0. Superset khởi động lại đúng hai container cũ sau khi chúng đã dừng, health/login200. Bốn view DW chưa tạo/role BI chỉ đọc và UI login chưa xác minh; không tạo đối tượng nghiệp vụ. Xem báo cáo current trong results/warehouse. Chờ duyệt S02, chưa đẩy mốc.
