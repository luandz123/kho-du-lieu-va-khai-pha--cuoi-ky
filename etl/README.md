# P1 — S05: cấu trúc đã duyệt và raw staging

## Hiện hành: full refresh 6D và metadata G2

Lệnh tái tạo có ghi trong phạm vi được giao6D: `.\.venv\Scripts\python.exe -X utf8 -m etl.run_etl refresh --env-file .env`. Kiểm marker/catalog/nguồn, một transaction/connection/advisory lock, UPDATE registry inactive/invalid và một TRUNCATE đúng11bảng RESTART IDENTITY, nạp staging→dimension→bridge→fact, kiểm trước commit. Giữ registry metadata, không CASCADE/DROP/bootstrap; không nối CLI tiểu bước.

Hậu kiểm chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_warehouse.py --env-file .env` hoặc `python -m etl.run_etl verify --env-file .env`. Checker tích hợp không dùng guard rỗng/fingerprint surrogate của 6A/B/C, kiểm snapshot logical và model sau refresh. Khi được giao G3 phải bổ sung kiểm model phù hợp, không tự bỏ guard. Không dùng loader/checker tiểu bước cũ cho pipeline.

Hai run16421c84/6501a547 cùng bundle/config/hash/count đạt;65unit hồi quy và fixture seeded snapshot/model rollback đạt; adapter P2 trực tiếp PostgreSQL/raw/CSV PASS. [Bàn giao6D](../docs/P1/s06d_handoff.md), [gói DW](../docs/P1/dw_handoff.md), [manifest](../results/warehouse/dw_manifest.json). File report/manifest xuất nguyên tử sau COMMIT, lỗi xuất không phải rollback DB. CSV đối chiếu chỉ cục bộ dưới data/processed, không commit. Chưa P2 nhậnG2/push/PR/OLAP/dashboard/G3; các đoạn dưới giữ lịch sử từng tiểu bước.

## Hiện hành: 6C đã nạp fact, chờ review

6B đã được điều phối chấp nhận, checkpoint local d698d8e. Fact/view ratings **1000209**, tổng điểm **3582313**, bốn view canonical hash đúng; staging/dimension gồm surrogate/bridge không đổi, analytics rỗng. [Bàn giao6C](../docs/P1/s06c_handoff.md), [summary6C](../results/warehouse/s06c_summary.json). Chưa full refresh6D/G2; chưa commit6C/push/PR.

Hậu kiểm chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_warehouse.py --env-file .env` hoặc `python -m etl.s06c_fact verify --env-file .env`. Unit: `python -m unittest discover -s tests/warehouse -p test_s06c_fact.py -v`. Lệnh đã dùng khi factrỗng: `python -m etl.s06c_fact preflight --env-file .env`, rồi `python -m etl.s06c_fact load --env-file .env`; **không chạy lại loader S05/6A/6B/6C hoặc checker6B rỗngfact**, không xóa để vượtguard. Checker6C kiểm bảo toàn phù hợp với fact đã nạp. Fixture check_s06c_rollback.py chỉ chạy có chủ đích, không phải hậu kiểm chỉ đọc. Các hướng dẫn dưới là lịch sử từng mốc.

## Hiện hành: 6B đã nạp bridge, chờ review

6A đã được điều phối chấp nhận; checkpoint local cfed2c8. Bridge **6408**, ba view users/movies/movie_genres khớp canonical, staging/dimension không đổi; fact/v_ml_ratings/analytics vẫn rỗng. [Bàn giao6B](../docs/P1/s06b_handoff.md), [summary6B](../results/warehouse/s06b_summary.json). Chưa G2/6C/6D; không push/PR.

Hậu kiểm chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 -m etl.s06b_bridge verify --env-file .env`. Unit: `.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests/warehouse -p test_s06b_bridge.py -v`. Lệnh đã dùng để nạp lúc bridge rỗng: `python -m etl.s06b_bridge load --env-file .env`; không chạy lại loadS05/6A/6B hoặc xóa để vượt guard. Checker6A bên dưới là lịch sử, nay đòi bridge rỗng nên không phù hợp; verifier6B kiểm bảo toàn dimension riêng. Xem bàn giao để chạy fixture có chủ đích; fixture không phải hậu kiểm chỉ đọc.

## Hiện hành: 6A đã nạp dimension, chờ review

Xem [bàn giao 6A](../docs/P1/s06a_handoff.md) và [summary 6A](../results/warehouse/s06a_summary.json). Chỉ 4 dimension đã nạp: 6040 user/3883 movie/18 genre/1040 date; bridge/fact/analytics còn rỗng. **Không chạy lại load S05 hoặc load6A** trên trạng thái đã nạp; không tự truncate/xóa để vượt guard. Chưa pipeline full refresh6D/chạy lại tích hợp. Mục S05 dưới đây là hướng dẫn của bước trước.

Kiểm an toàn chỉ đọc sau6A: `.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_s06a_dimensions.py --env-file .env`. Lệnh đã dùng để nạp6A: `python -m etl.s06a_dimensions --env-file .env`; lệnh này từ chối target không rỗng, không dùng làm checker. Chưa commit/push/PR S06 hoặc tự sang6B.

Chỉ bootstrap DDL S04, kiểm đầu vào và nạp ba bảng staging. Không transform/nạp dimension, bridge, fact hoặc kết quả cụm. Database dự án **movielens_btl**, được điều phối chọn và cho phép tạo ở S05; không dùng postgres/template0/template1 để chứa dữ liệu nghiệp vụ.

## Chạy trên PowerShell từ thư mục dự án

```powershell
.\.venv\Scripts\Activate.ps1
python -m etl.s05_staging inputs --raw-dir data/raw/p1_s05/ml-1m
python -m etl.s05_staging bootstrap --env-file .env
python -m etl.s05_staging load --env-file .env --raw-dir data/raw/p1_s05/ml-1m
python -m etl.s05_staging catalog --env-file .env
python -m unittest discover -s tests/warehouse -p test_s05_staging.py -v
python tests/warehouse/check_s05_rollback.py --env-file .env
```

Nếu PowerShell chặn Activate.ps1, dùng trực tiếp `.\.venv\Scripts\python.exe` thay `python`; không cần đổi ExecutionPolicy toàn máy. Kiểm `python -c "import sys; print(sys.executable)"` để xác nhận môi trường dự án.

`.env` cục bộ cần POSTGRES_HOST/PORT/DB/USER/PASSWORD đã điền trên máy, không gửi mật khẩu vào chat. POSTGRES_DB chỉ là database kết nối ban đầu để kiểm/tạo database; mọi bảng dự án luôn nằm trong movielens_btl do script cố định. S05 không sửa credential, .env, role hoặc quyền quản trị. Mỗi tiến trình dùng options UTC và timeout; chỉ log host/port/database, không URI hoặc exception thô.

## Nguồn và phiên bản adapter

Nguồn chính thức: https://files.grouplens.org/datasets/movielens/ml-1m.zip. Mỗi máy tải độc lập vào vị trí mới, không ghi đè dữ liệu đã có. Máy P1 đã tải độc lập trong snapshot kiểm nhận 9299268; S05 kiểm lại bốn hash/dòng rồi sao chép vào `data/raw/p1_s05/ml-1m/`, không lấy raw từ P2. Có thể chỉ định thư mục độc lập khác bằng --raw-dir. Tệp phải là users.dat, movies.dat, ratings.dat, README, Latin-1; manifest P2 chỉ đọc.

Lệnh inputs kiểm byte nguồn/số dòng và dùng adapter+serializer đã review của P2 để tạo bốn bảng **trong bộ nhớ**, so count/hash canonical. Không ghi CSV hoặc DW. Kiểm phiên bản code bằng SHA-256 Git blob LF và xác nhận checkout chỉ khác CRLF của Windows; không chuẩn hóa byte dữ liệu khi hash. Mỗi report lưu commit/hash script thực dùng thay vì tin trường source_code_commit metadata còn sai. Hash nguồn và canonical không thay giá trị kỳ vọng.

## Bootstrap và giới hạn an toàn

Database chưa tồn tại: dùng quyền hiện có để CREATE DATABASE, không tự GRANT/superuser. Database đã tồn tại nhưng thiếu marker nguồn gốc S05 → dừng, giữ nguyên. Marker ghi contract và hash file DDL đã áp dụng, không chứa secret. Nếu thiếu quyền CREATE DATABASE, chủ máy cần tạo database đúng tên và xác minh nguồn gốc/quyền với P1; không tự gắn marker vào database không rõ nguồn để vượt guard.

DDL dùng nguyên file S04 và `btl.target_database=movielens_btl`. Giữ nguyên các câu CREATE/constraint/view; script hoãn COMMIT cuối để so catalog trong cùng transaction, chỉ commit nếu khớp. Không thêm IF NOT EXISTS, không drop hoặc đổi mô hình. Nếu có cấu trúc, chỉ so catalog; không chạy lại DDL mù quáng. CREATE DATABASE riêng không rollback cùng DDL: khi DDL/checker lỗi, database mới có thể còn rỗng, giữ nguyên và kiểm lại trước lần chạy tiếp.

## Staging và kiểm chứng

Đọc nhị phân theo LF, giải mã Latin-1, tách `::`, giữ nguyên từng field và source_line 1-based. users.dat đòi đủ 5 trường nhưng ZIP bị loại ngay tại reader; không giữ raw_line. Số trường sai/blank/NUL/field rỗng thì dừng, không bỏ dòng hoặc deduplicate. Chưa ép kiểu rating/ID/tuổi sang DW.

Ba bảng được TRUNCATE tường minh trong một transaction, không CASCADE; COPY có buffer tạm cục bộ và không commit từng chunk. Chỉ schema staging hoặc schema fixture UUID được code chấp nhận. Trước commit: kiểm count, so **mọi dòng/từng field theo source_line** với nguồn, kiểm lại hash nguồn và xác nhận chín bảng DW/analytics vẫn rỗng. Nạp lại thay snapshot staging, không append. Lỗi rollback; mất kết nối/SQL lỗi không được suy là commit thành công.

Report tự tạo run_id, UTC, thời gian, hash code, counters read/loaded/errors và thống kê tổng hợp tại results/warehouse/s05_*.json. Hash `retained_row_csv_sha256` là SHA-256 CSV UTF-8/LF không header của (source_line, các field giữ lại), **không phải canonical hash**. Dùng hash này so hai lần nạp và rollback. Không log title, user ID, rating history hoặc password.

Rollback integration phải chạy sau khi staging thật đã có. Test tạo schema s05_test_<UUID> và ba bảng fixture, nạp seed tự tạo, thay users/movies rồi cố ý làm ratings malformed. Kiểm trạng thái seed phục hồi, staging thật không đổi và DW/analytics không đổi; cuối cùng dọn chính ba bảng/schema vừa tạo, không CASCADE. Không sửa nguồn thật. Unit tests không kết nối database.

## Kết quả thực trên P1

Xem [bàn giao S05](../docs/P1/s05_handoff.md) và [summary bằng chứng](../results/warehouse/s05_summary.json). Cặp cùng code 04cb9c6: run 0f24c3a (16/10, 10.078s) và f5f11bcd (17/10, 9.281s), đều 6040/3883/1000209 và cùng hash các trường/source_line. Run c122ce2 (16.844s, code b9cf2df) giữ làm lịch sử, không gọi là cặp cùng phiên bản. 9 unit tests và fixture rollback đã đạt; điều phối báo review/chạy lại 9/9 đạt. Được giao công bố PR S05, chưa merge/6A; chưa kiểm G2/ETL DW, quyền BI hoặc phục hồi backup. Không sửa code giữa hai run cùng phiên bản.
