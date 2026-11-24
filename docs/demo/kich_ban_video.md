# Kịch bản video – Movie Platform (bản nâng cấp)

Tài liệu này dùng cho **2 việc**:

1. **Làm video** (đưa cho Antigravity): mỗi cảnh có *hình ảnh / thao tác*, *lời thoại* và *chữ trên màn hình*.
2. **Ôn bảo vệ**: cuối mỗi chương có khung **❓ Thầy có thể hỏi**, kèm câu trả lời ngắn (≤ 30 giây nói). Phần cuối là bảng tra số liệu và các câu hỏi khó.

Tất cả số liệu dưới đây lấy từ hệ thống đang chạy (ngày 20/11/2026), không phải ước lượng.

---

## 0. Ghi chú sản xuất (cho Antigravity)

| Mục | Yêu cầu |
|---|---|
| Bản dài | **≈ 15 phút**, 10 chương, mỗi chương mở bằng 1 thẻ tiêu đề 2 giây. Dùng để tự học và gửi thầy xem thêm |
| Bản 5 phút | Ghép các cảnh có nhãn **[5′]** theo thứ tự. Dùng khi trình bày trực tiếp hoặc làm video dự phòng |
| Khung hình | 1920×1080 (hoặc 1440×900 nếu quay bằng script có sẵn), 25–30 fps |
| Giọng đọc | Tiếng Việt, giọng nam hoặc nữ miền Bắc, tốc độ vừa (~150 từ/phút). Đọc **đúng lời thoại** ở mỗi cảnh |
| Phụ đề | Đúng lời thoại, tối đa 2 dòng, đặt ở đáy khung hình |
| Nhạc nền | Rất nhỏ hoặc không có |
| Nhấn mạnh | Phóng to (zoom) vào JSON Kafka, tên file MinIO, các bảng trong kho, như ghi ở từng cảnh |
| **Không được** | Quay màn hình đăng nhập hoặc nội dung file `.env` (có mật khẩu). Không dựng giả số liệu: mọi cảnh là hệ thống chạy thật |

**Tài nguyên có sẵn trong repo:**

| Tài nguyên | Đường dẫn |
|---|---|
| Sơ đồ luồng dữ liệu (PNG, SVG) | `docs/movie_platform_dataflow.png`, `docs/diagram/movie_platform_dataflow.svg` |
| Script quay tự động (Playwright, có phụ đề) | `docs/demo/record_demo.py` → `docs/demo/movie_platform_demo.mp4` |
| Bản video đã quay sẵn (3′52″, không tiếng) | `docs/demo/movie_platform_demo.mp4` – có thể cắt lấy cảnh |

**Trước khi quay** (khởi động ~2 phút):

```bash
docker compose up -d
docker compose -f dashboard/superset/compose.yaml --env-file dashboard/superset/.env up -d
.venv/Scripts/streamlit run app/streamlit_app.py
```

| Giao diện | Địa chỉ |
|---|---|
| App Streamlit | http://localhost:8501 |
| Kafka UI | http://localhost:8080 |
| MinIO Console | http://localhost:9001 (bucket `lake`) |
| Airflow | http://localhost:8081 |
| Superset | http://localhost:8089/superset/dashboard/movie-platform/ |
| Kho Postgres | `localhost:5433`, database `movie_dw` (xem bằng DBeaver / psql) |
| Postgres của app | `localhost:5434`, database `movie_app` |

---

## Chương 1 – Mở đầu: bản cũ thiếu gì, bản mới sửa gì (≈ 1′00″)

**Cảnh 1.1 [5′]** – Thẻ tiêu đề rồi bảng so sánh.

*Hình ảnh:* Bảng 2 cột trên nền sáng.

| Thầy góp ý | Bản mới |
|---|---|
| Chỉ 1 nguồn (MovieLens, file tĩnh) | 7 nguồn, 4 kiểu nạp: file, API, CDC, streaming |
| Không có data lake | MinIO, 3 tầng bronze → silver → gold |
| Không có CDC | Debezium đọc WAL của Postgres → Kafka |
| Demo bằng terminal | App web + Airflow + dashboard Superset |

*Lời thoại:*
> "Ở buổi bảo vệ trước, thầy góp ý bài nhóm em có bốn điểm thiếu: chỉ có một nguồn dữ liệu tĩnh, không có data lake, không có CDC, và phần demo chỉ chạy trên terminal. Bản nâng cấp này sửa đúng bốn điểm đó. Phần còn lại là những gì nhóm em làm thêm: nạp kho tăng dần, điều phối bằng Airflow, và gợi ý phim kết hợp nội dung."

**Cảnh 1.2** – Bảng "Làm thêm".

| Bản cũ | Bản mới |
|---|---|
| `TRUNCATE` rồi nạp lại toàn bộ | Nạp tăng dần: watermark + upsert |
| Chạy tay từng lệnh | Airflow 3 DAG + 9 kiểm tra chất lượng |
| 1 bảng fact | SCD loại 2, xóa mềm, 4 bảng fact |
| Item-based CF | Hybrid CF + nội dung, tìm phim bằng câu tiếng Việt |

*Lời thoại:*
> "Video đi theo đúng đường đi của dữ liệu: từ nguồn, qua Kafka và data lake, vào kho, rồi tới dashboard và mô hình gợi ý."

---

## Chương 2 – Kiến trúc tổng thể (≈ 1′30″)

**Cảnh 2.1 [5′]** – Sơ đồ `docs/movie_platform_dataflow.png`, zoom lần lượt từng cột từ trái sang phải.

*Lời thoại:*
> "Hệ thống chia năm cột. Cột một là nguồn, gồm bốn kiểu. Kiểu file: MovieLens và bộ dữ liệu IMDb. Kiểu API: Wikidata, lượt xem Wikipedia, tóm tắt và poster phim từ Wikipedia. Kiểu CDC: database của một app xem phim do nhóm dựng. Kiểu streaming: luồng sửa bài Wikipedia theo thời gian thực.
>
> Cột hai là tầng nạp. Dữ liệu batch do Airflow lấy theo lịch. Dữ liệu CDC và streaming đi qua Kafka, rồi một consumer gom lại ghi xuống lake.
>
> Cột ba là data lake trên MinIO, chia ba tầng bronze, silver, gold, xử lý bằng DuckDB.
>
> Cột bốn là kho dữ liệu Postgres theo lược đồ sao, có pgvector để lưu vector của phim.
>
> Cột năm là khai thác: dashboard Superset và app Streamlit."

*Chữ trên màn hình:* `Nguồn → Nạp → Data lake → Kho → Khai thác`

**Cảnh 2.2** – Màn hình `docker compose ps` (hoặc Docker Desktop) liệt kê container.

*Lời thoại:*
> "Mọi thành phần chạy bằng một file docker-compose trên một máy: kho Postgres, Postgres của app, MinIO, Kafka, Debezium, Kafka UI, Airflow, consumer và producer. Superset chạy trong một compose riêng."

### ❓ Thầy có thể hỏi

- **Vì sao chọn các công cụ này?** Đều là chuẩn công nghiệp, mã nguồn mở, chạy được trên một máy: Kafka để truyền sự kiện, Debezium là công cụ CDC phổ biến nhất cho Postgres, MinIO tương thích S3, DuckDB xử lý được vài GB dữ liệu mà không cần cluster như Spark, Airflow là công cụ điều phối phổ biến nhất.
- **Vì sao không dùng Spark?** Dữ liệu chỉ vài GB, vừa với RAM một máy. DuckDB đọc Parquet trên S3 bằng SQL, nhanh và nhẹ. Spark chỉ cần khi dữ liệu vượt khả năng một máy.
- **Máy cần bao nhiêu tài nguyên?** Docker dùng khoảng 8 GB RAM. Kafka và Debezium được giới hạn heap 512 MB mỗi cái.

---

## Chương 3 – Nguồn dữ liệu và tích hợp (≈ 1′45″)

**Cảnh 3.1** – Bảng nguồn (có thể lấy từ `docs/ke_hoach_chi_tiet.md`, giai đoạn 2).

| Nguồn | Dạng | Tần suất | Dùng để |
|---|---|---|---|
| MovieLens 1M | file `.dat` | 1 lần | 1.000.209 rating lịch sử, 6.040 user, 3.883 phim |
| IMDb datasets | TSV nén | `title.ratings` hằng ngày | điểm, số vote, đạo diễn, diễn viên, thời lượng |
| Wikidata | SPARQL | 1 lần | ghép IMDb ID ↔ bài Wikipedia, quốc gia, số Oscar |
| Wikipedia Pageviews | REST | hằng ngày | lượt xem bài của 500 phim nhiều rating nhất |
| Wikipedia API | MediaWiki | 1 lần | đoạn mô tả (3.717 phim tiếng Anh, 405 tiếng Việt), poster (3.636 phim) |
| App xem phim | Postgres → CDC | liên tục | rating mới, xóa rating, đổi thông tin người dùng |
| Wikimedia EventStreams | luồng thời gian thực | liên tục | lượt sửa bài Wikipedia |

*Lời thoại:*
> "Bảy nguồn này khác nhau cả về định dạng lẫn nhịp cập nhật. IMDb cập nhật file điểm mỗi ngày, nên mỗi ngày nhóm em chụp lại một bản để theo dõi xu hướng điểm. Wikipedia cho biết phim nào đang được quan tâm qua lượt xem bài. Còn app xem phim là nguồn dữ liệu sống: người dùng chấm điểm liên tục."

**Cảnh 3.2** – Zoom vào code ghép phim trong `transform/silver.py` (hàm `movies`), sau đó bảng kết quả.

*Lời thoại:*
> "Khó nhất là ghép MovieLens với IMDb, vì hai nguồn không có khóa chung. Bước một, dùng file links.csv của MovieLens: ghép được 2.949 phim. Bước hai, với phim còn lại, nhóm em chuẩn hóa tên phim: bỏ dấu, đưa mạo từ 'The' ở cuối lên đầu, tách tên thay thế trong ngoặc, rồi ghép theo tên và năm, cho phép lệch một năm. Nếu nhiều phim cùng khớp thì chọn phim nhiều lượt vote nhất. Bước này ghép thêm được 857 phim. Tổng cộng khớp 98%. 77 phim còn lại để trống, vì ghép sai còn tệ hơn thiếu dữ liệu."

*Chữ trên màn hình:* `links.csv: 2.949 · tên + năm: 857 · không khớp: 77 → khớp 98%`

### ❓ Thầy có thể hỏi

- **Ghép theo tên có sai không, kiểm tra thế nào?** Có thể sai với các bản làm lại cùng tên. Nhóm giảm rủi ro bằng ràng buộc năm lệch tối đa 1 và ưu tiên phim nhiều vote. Đã xem tay một mẫu ngẫu nhiên, ví dụ "Bloody Child, The (1996)" ↔ "The Bloody Child (1996)". Cột `imdb_match` trong `dim_movie` ghi rõ phim nào ghép bằng cách nào.
- **links.csv lấy ở đâu khi ML-1M không có?** Lấy từ bộ ml-latest-small. MovieLens giữ nguyên movieId giữa các phiên bản nên dùng chung được.
- **Gọi API Wikipedia có bị chặn không?** Có giới hạn: 10 request/phút nếu không khai báo thông tin liên hệ. Code giãn cách request, thử lại khi bị lỗi 429 và chờ đúng số giây trong header `Retry-After`. Lượt xem chỉ lấy cho 500 phim nhiều rating nhất. Phần tóm tắt dùng API lấy 20 bài mỗi request.
- **TMDB thì sao?** TMDB bị chặn ở mạng Việt Nam, nên nhóm thay bằng Wikipedia (mô tả và poster) và IMDb (điểm).

---

## Chương 4 – CDC: bắt thay đổi từ database của app (≈ 2′00″)

**Cảnh 4.1 [5′]** – App → tab **Chấm điểm** → **➕ Tạo người dùng mới** → chấm 5★ Toy Story, Toy Story 2. Panel bên phải hiện ✅ Postgres → ✅ Kafka → ✅ MinIO.

*Lời thoại:*
> "Đây là app xem phim. Em tạo một người dùng mới, chưa có lịch sử, rồi chấm năm sao cho Toy Story và Toy Story 2. Mỗi thao tác là một lệnh INSERT vào Postgres của app. App không gửi gì sang Kafka. Debezium tự đọc thay đổi từ WAL của Postgres. Panel bên phải theo dõi thay đổi này đi qua từng chặng, kèm thời điểm."

**Cảnh 4.2 [5′]** – Kafka UI → topic `app.public.ratings` → Messages → mở message mới nhất. **Zoom vào JSON.**

```json
{ "before": null,
  "after":  { "user_id": 6047, "movie_id": 3114, "rating": 5, ... },
  "source": { "connector": "postgresql", "db": "movie_app", "table": "ratings", "lsn": 29385432, ... },
  "op": "c", "ts_ms": 1795116188... }
```

*Lời thoại:*
> "Đây là message Debezium gửi vào Kafka. 'op' bằng 'c' nghĩa là create, tức thêm mới. 'before' rỗng vì trước đó chưa có dòng này, 'after' là dòng vừa thêm. Trường 'lsn' là vị trí của thay đổi trong WAL, dùng để sắp đúng thứ tự và loại bản ghi trùng ở bước sau. Nếu sửa điểm thì 'op' là 'u' và có cả 'before' lẫn 'after'. Nếu xóa thì 'op' là 'd' và 'after' rỗng."

**Cảnh 4.3** – Màn hình SQL trên Postgres của app (cổng 5434):

```sql
SHOW wal_level;                                           -- logical
SELECT * FROM pg_publication_tables;                      -- ratings, users
SELECT slot_name, plugin, active FROM pg_replication_slots;   -- debezium_app, pgoutput, true
```

*Lời thoại:*
> "Để Debezium đọc được WAL, Postgres phải bật wal_level bằng logical. Publication khai báo những bảng được phát thay đổi, ở đây là ratings và users. Replication slot giúp Postgres nhớ Debezium đã đọc tới đâu. Nếu Debezium tắt rồi bật lại, nó đọc tiếp từ đúng chỗ đó, không mất thay đổi nào."

### ❓ Thầy có thể hỏi

- **CDC khác đọc theo cột `updated_at` thế nào?** CDC đọc WAL – nhật ký Postgres vốn phải ghi – nên:
  - không quét bảng nguồn, không làm chậm app;
  - bắt được cả **DELETE** (truy vấn theo `updated_at` không thấy dòng đã xóa);
  - không sót thay đổi xảy ra giữa hai lần quét;
  - giữ đúng thứ tự theo LSN;
  - không phụ thuộc vào việc app có cập nhật `updated_at` đúng hay không.
- **WAL là gì?** Write-Ahead Log: Postgres ghi mọi thay đổi vào log *trước* khi ghi vào bảng, để phục hồi khi sập. `wal_level = logical` cho phép giải mã log thành thay đổi theo từng dòng.
- **`REPLICA IDENTITY FULL` để làm gì?** Để WAL ghi cả giá trị cũ của dòng. Nhờ vậy UPDATE và DELETE có `before` đầy đủ. Đánh đổi: WAL lớn hơn.
- **Debezium chết lâu thì sao?** Replication slot giữ WAL từ điểm chưa đọc, nên không mất dữ liệu. Nhưng WAL sẽ tích lại và có thể đầy ổ đĩa. Đây là rủi ro vận hành lớn nhất của CDC trên Postgres, cần giám sát độ trễ của slot.
- **Snapshot ban đầu là gì?** Lần đầu chạy, Debezium đọc toàn bộ bảng hiện có (`op: r`) rồi mới đọc WAL. Bảng `users` có 6.040 dòng nên sinh 6.040 sự kiện `r`. Silver bỏ qua các sự kiện này vì chúng trùng với dữ liệu MovieLens.
- **Tombstone là gì?** Message rỗng Debezium gửi sau DELETE để Kafka log compaction xóa key. Nhóm tắt (`tombstones.on.delete=false`) vì không dùng compaction.

---

## Chương 5 – Kafka và consumer (≈ 1′15″)

**Cảnh 5.1** – Kafka UI → Topics: 4 topic; mở tab **Consumers** → group `lake-bronze-writer`, lag = 0.

*Lời thoại:*
> "Kafka có bốn topic: hai topic CDC là app.public.ratings và app.public.users, hai topic streaming là wiki.recentchange và wiki.movie_edits. Mỗi topic có ba partition. Consumer group lake-bronze-writer đọc cả bốn topic. Lag bằng không nghĩa là consumer đã đọc kịp hết."

**Cảnh 5.2** – Code `cdc/kafka_to_bronze.py`, tô sáng 2 dòng `flush(buffers)` và `consumer.commit(...)`.

*Lời thoại:*
> "Consumer gom message thành micro-batch: đủ năm trăm message hoặc đủ mười giây thì ghi một file xuống lake. Điểm quan trọng: nó chỉ commit offset sau khi ghi file xong. Nếu consumer chết giữa chừng, khi khởi động lại nó đọc lại từ offset cũ. Không mất dữ liệu, chỉ có thể bị trùng, và bản trùng được loại ở tầng silver. Đây gọi là at-least-once."

### ❓ Thầy có thể hỏi

- **Vì sao cần Kafka ở giữa, không cho Debezium ghi thẳng MinIO?** Kafka tách bên gửi khỏi bên nhận: làm vùng đệm khi phía sau chậm hoặc chết, cho nhiều consumer cùng đọc một luồng, và cho đọc lại (replay) vì message được giữ 72 giờ.
- **Thứ tự message có đảm bảo không?** Chỉ trong cùng một partition. Debezium dùng khóa chính làm key, nên mọi thay đổi của cùng một dòng vào cùng partition và giữ đúng thứ tự.
- **at-most-once, at-least-once, exactly-once khác nhau thế nào?** Commit trước rồi xử lý thì có thể mất (at-most-once). Xử lý xong rồi commit thì không mất nhưng có thể trùng (at-least-once, dự án dùng cách này). Exactly-once cần transaction. Ở đây đạt *hiệu quả* exactly-once nhờ silver khử trùng theo LSN và kho upsert theo khóa.
- **Micro-batch 10 giây sinh nhiều file nhỏ, có sao không?** Đây là vấn đề "small files": càng nhiều file nhỏ thì đọc càng chậm. Hướng xử lý là gộp file định kỳ (compaction) hoặc tăng khoảng gom. Với quy mô bài này chưa ảnh hưởng.

---

## Chương 6 – Data lake: bronze → silver → gold (≈ 1′45″)

**Cảnh 6.1 [5′]** – MinIO → bucket `lake` → `bronze/app_cdc/ratings/ingest_date=…/` → sắp xếp theo *Last Modified*, file mới nhất đầu tiên (đúng tên file panel trong app đã hiện).

*Lời thoại:*
> "Đây là data lake trên MinIO, tương thích chuẩn S3 của Amazon. Bucket lake có ba tầng. Tầng bronze giữ dữ liệu thô, đúng như nguồn gửi về. File vừa xuất hiện ở đây chính là micro-batch chứa hai rating em vừa chấm."

**Cảnh 6.2** – Bảng 3 tầng.

| Tầng | Nội dung | Định dạng |
|---|---|---|
| Bronze | Thô, giữ nguyên nguồn; chia thư mục theo `ingest_date` | DAT, CSV, TSV.gz, JSONL |
| Silver | Làm sạch, ép kiểu, khử trùng CDC theo LSN, ghép các nguồn | Parquet (nén zstd) |
| Gold | Đúng hình dạng kho: `dim_*`, `fact_*`, khóa tự nhiên | Parquet |

*Lời thoại:*
> "Silver làm sạch dữ liệu và xử lý CDC. Với mỗi cặp người dùng và phim, nó chỉ giữ sự kiện mới nhất theo LSN. Nếu sự kiện mới nhất là xóa thì đánh dấu is_deleted. Silver cũng ghép MovieLens với IMDb và Wikipedia. Gold đưa dữ liệu về đúng hình dạng các bảng trong kho. Silver và gold lưu bằng Parquet: file rating 23 MB dạng gốc chỉ còn 6 MB."

**Cảnh 6.3** – Zoom vào đoạn SQL khử trùng trong `transform/silver.py`:

```sql
QUALIFY row_number() OVER (PARTITION BY user_id, movie_id ORDER BY lsn DESC, ts_ms DESC) = 1
```

### ❓ Thầy có thể hỏi

- **Data lake khác data warehouse?** Lake lưu mọi định dạng, chi phí thấp, đọc theo lược đồ lúc dùng (schema-on-read). Kho có lược đồ chặt (schema-on-write), tối ưu cho truy vấn phân tích.
- **Vì sao cần bronze, sao không làm sạch luôn?** Bronze giữ dữ liệu gốc để có thể **xử lý lại** khi phát hiện lỗi logic ở silver hay gold, mà không cần lấy lại từ nguồn (có nguồn không lấy lại được, như sự kiện CDC đã qua).
- **Vì sao Parquet?** Lưu theo cột nên chỉ đọc cột cần dùng; nén tốt; giữ kiểu dữ liệu; có thống kê min/max để bỏ qua các khối không cần đọc.
- **DuckDB là gì?** Cơ sở dữ liệu phân tích chạy ngay trong tiến trình Python (giống SQLite nhưng lưu theo cột). Đọc thẳng CSV, JSON, Parquet trên S3 bằng SQL.
- **Chạy lại silver/gold có sao không?** Không: các bước là *idempotent*, cùng đầu vào thì ra cùng kết quả. Vì vậy Airflow có thể thử lại (retry) an toàn.

---

## Chương 7 – Kho dữ liệu: nạp tăng dần, SCD, kiểm tra chất lượng (≈ 2′00″)

**Cảnh 7.1** – Lược đồ kho (DBeaver ER diagram, hoặc khối "Kho dữ liệu" trên sơ đồ).

| Bảng | Loại | Grain / ghi chú |
|---|---|---|
| `dim_user` | dimension, **SCD loại 2** | 1 phiên bản người dùng; `valid_from`, `valid_to`, `is_current` |
| `dim_movie` | dimension, **SCD loại 1** | ghi đè; có đạo diễn, diễn viên, quốc gia, Oscar, poster |
| `dim_date`, `dim_genre` (+ bridge), `dim_source` | dimension | |
| `fact_rating` | fact – trạng thái hiện tại | 1 cặp user × phim; `is_deleted` cho xóa mềm |
| `fact_imdb_rating_daily` | periodic snapshot | 1 phim × 1 ngày (đã có 11.400 dòng = 3 ngày) |
| `fact_pageviews_daily` | periodic snapshot | 1 phim × 1 ngày (45.988 dòng) |
| `fact_wiki_edit` | transaction (streaming) | 1 lần sửa bài |
| `movie_embedding` | vector (pgvector) | 3.883 vector 384 chiều, chỉ mục HNSW |
| `etl.watermark`, `etl.pipeline_run` | vận hành | mốc đã nạp; nhật ký từng lần chạy |

*Lời thoại:*
> "Kho vẫn theo lược đồ sao như bản cũ, nhưng có thêm ba loại bảng fact. Một bảng rating. Hai bảng chụp nhanh hằng ngày: điểm IMDb và lượt xem Wikipedia. Một bảng sự kiện streaming: lượt sửa bài Wikipedia. Bảng dim_user giữ lịch sử theo SCD loại hai, còn dim_movie ghi đè theo SCD loại một."

**Cảnh 7.2 [5′]** – Tiếp tục trong app: bấm **▶ Chạy pipeline ngay** → panel: Airflow 1/4 … 4/4 → ✅ Kho → "đã vào kho sau ~30 giây". Kéo xuống: **gợi ý trước** (phim phổ biến) và **sau** (A Bug's Life, Aladdin, Babe… gắn nhãn MỚI).

*Lời thoại:*
> "Em bấm chạy pipeline. Airflow chạy bốn bước: bronze sang silver, silver sang gold, nạp kho, rồi kiểm tra chất lượng. Chỉ khoảng ba mươi giây sau khi chấm, rating đã nằm trong kho. Ngay bên dưới là gợi ý cho người dùng này. Trước khi chấm, vì chưa có lịch sử, hệ thống gợi ý phim phổ biến. Sau khi chấm hai phim hoạt hình, cả năm gợi ý đều đổi sang phim hoạt hình và gia đình. Dữ liệu mới đã đi hết đường ống tới tận mô hình."

**Cảnh 7.3** – Trình bày nạp tăng dần: zoom `warehouse/load.py` (hàm `fact_rating`), rồi chạy SQL:

```sql
SELECT * FROM etl.watermark;
SELECT step, rows_in, rows_out, finished_at - started_at AS duration
FROM etl.pipeline_run ORDER BY run_id DESC LIMIT 6;
```

*Lời thoại:*
> "Bản cũ xóa sạch bảng rồi nạp lại một triệu dòng. Bản mới nạp tăng dần. Bảng watermark lưu thời điểm thay đổi lớn nhất đã nạp. Mỗi lần chạy chỉ đọc những dòng mới hơn mốc đó trừ đi một giờ. Đọc lùi một giờ để không bỏ sót sự kiện đến muộn, vì Kafka có ba partition. Sau đó dùng INSERT ON CONFLICT DO UPDATE, và chỉ ghi đè khi bản mới hơn. Vì vậy chạy lại bao nhiêu lần cũng không nhân đôi dữ liệu. Lần đầu nạp mất khoảng hai phút, các lần sau chỉ vài giây."

**Cảnh 7.4** – SCD2: trong app đổi nghề của user mới → chạy pipeline → panel báo "dim_user: phiên bản mới …, tổng 2 phiên bản". Rồi SQL:

```sql
SELECT user_key, occupation, valid_from, valid_to, is_current
FROM dw.dim_user WHERE user_id = <id> ORDER BY valid_from;
```

*Lời thoại:*
> "Khi người dùng đổi nghề, kho không ghi đè. Nó đóng phiên bản cũ bằng valid_to, rồi thêm phiên bản mới. Mỗi rating được gắn với phiên bản người dùng có hiệu lực tại thời điểm chấm. Nhờ vậy phân tích theo nghề nghiệp vẫn đúng với quá khứ."

**Cảnh 7.5** – Log task `data_quality` trong Airflow: 9 dòng `[OK ]`.

*Lời thoại:*
> "Cuối mỗi lần chạy có chín kiểm tra chất lượng. Ví dụ: rating nằm trong khoảng một đến năm; mỗi người dùng có đúng một phiên bản hiện tại; rating trỏ đúng phiên bản theo thời điểm; số dòng giữa gold và kho phải khớp; số rating đã xóa phải khớp; kho phải bắt kịp thay đổi mới nhất trong lake. Một kiểm tra sai thì task chuyển đỏ và dừng."

### ❓ Thầy có thể hỏi

- **Grain của `fact_rating`?** Một dòng cho một cặp người dùng × phim, giữ **rating hiện tại**. Chấm lại thì ghi đè, xóa thì `is_deleted = true`. Muốn giữ lịch sử từng lần chấm thì thêm một bảng transaction, mỗi sự kiện CDC một dòng.
- **Xóa rating thì kho xử lý thế nào?** Xóa mềm: giữ dòng, đánh dấu `is_deleted`. Lý do: giữ được dấu vết, và đối soát được với lake. Các view và app lọc `NOT is_deleted`.
- **SCD loại 1 khác loại 2?** Loại 1 ghi đè, mất lịch sử (dùng cho `dim_movie`, vì chỉ cần thông tin phim mới nhất). Loại 2 giữ lịch sử bằng nhiều phiên bản (dùng cho `dim_user`). Loại 2 bắt buộc có surrogate key (`user_key`) vì một `user_id` có nhiều dòng.
- **Phiên bản đầu tiên `valid_from` là gì?** `1990-01-01`, tức trước mọi rating của MovieLens (năm 2000), để rating cũ luôn tìm được phiên bản.
- **Periodic snapshot khác transaction fact?** Transaction: một dòng cho một sự kiện, chỉ thêm. Periodic snapshot: một dòng cho một thực thể mỗi kỳ (phim × ngày), dùng để xem xu hướng. Lượt xem cộng được theo ngày; điểm IMDb **không cộng** được (chỉ lấy trung bình hoặc giá trị cuối kỳ).
- **Watermark ghi trước hay sau dữ liệu?** Ghi trong **cùng transaction** với dữ liệu. Nếu ghi watermark trước mà nạp lỗi thì sẽ mất dữ liệu.
- **Vì sao không kiểm tra khóa NULL, trùng khóa?** Ràng buộc PK/FK và NOT NULL trong kho đã chặn ngay lúc ghi.

---

## Chương 8 – Airflow và dashboard (≈ 1′15″)

**Cảnh 8.1 [5′]** – Airflow → DAG `movie_incremental` → Grid: các lần chạy xanh; mở Graph view thấy 4 task.

*Lời thoại:*
> "Airflow có ba DAG. movie_incremental chạy mỗi mười lăm phút cho dữ liệu CDC và streaming. movie_daily chạy tám giờ sáng mỗi ngày, lấy điểm IMDb và lượt xem Wikipedia. movie_bootstrap chạy tay một lần để nạp toàn bộ từ đầu. Mỗi task chỉ gọi đúng một lệnh Python của dự án. Việc nặng do DuckDB và Postgres làm, Airflow chỉ điều phối."

**Cảnh 8.2 [5′]** – Superset dashboard `movie-platform`, cuộn từ trên xuống.

*Lời thoại:*
> "Dashboard mới đọc thẳng từ kho bằng một tài khoản chỉ có quyền đọc, tự làm mới mỗi sáu mươi giây. Có số rating mới từ app qua CDC; phim đang được quan tâm theo lượt xem Wikipedia, ví dụ Home Alone tăng mạnh khi gần Giáng sinh; so sánh điểm MovieLens với IMDb, ví dụ người dùng MovieLens chấm Pokémon thấp hơn IMDb khoảng 2,9 điểm trên thang mười; và giám sát pipeline."

### ❓ Thầy có thể hỏi

- **`catchup=False`, `max_active_runs=1` để làm gì?** `catchup=False`: không chạy bù các kỳ đã qua khi bật DAG. `max_active_runs=1`: không để hai lần chạy chồng nhau cùng ghi kho.
- **Task lỗi thì sao?** Thử lại 2 lần, mỗi lần cách 1 phút. Vẫn lỗi thì DAG đỏ và các task sau không chạy. Retry an toàn vì các bước đều idempotent.
- **Vì sao cần công cụ điều phối thay cho cron?** Có quan hệ phụ thuộc giữa các bước, thử lại, lưu lịch sử chạy, xem log từng task, chạy tay qua giao diện hoặc API (nút trong app gọi REST API của Airflow).
- **Embedding có chạy trong Airflow không?** Không, chạy tay (`python -m ai.embeddings`) vì cần PyTorch, mà image Airflow không cài để giữ nhẹ. Mô tả phim gần như không đổi nên không cần chạy thường xuyên.

---

## Chương 9 – Phần AI: gợi ý hybrid và tìm phim bằng tiếng Việt (≈ 2′00″)

**Cảnh 9.1 [5′]** – App → **Tìm phim theo mô tả** → gõ "phim kinh dị về cá mập" → **Jaws** đứng đầu. Gõ thêm "tàu chìm, chuyện tình trên biển" → **Titanic**.

*Lời thoại:*
> "Mỗi phim được ghép thành một đoạn văn: tên, thể loại, đoạn mở đầu bài Wikipedia, đạo diễn, diễn viên. Mô hình multilingual-e5-small biến đoạn văn đó thành một vector ba trăm tám mươi tư chiều, lưu trong kho bằng pgvector. Khi em gõ câu tiếng Việt, câu đó cũng thành vector, và kho tìm các phim có vector gần nhất theo cosine. Mô hình học đa ngôn ngữ, nên câu tiếng Việt vẫn tìm ra Jaws dù mô tả phim viết bằng tiếng Anh."

**Cảnh 9.2** – Bảng kết quả đánh giá (`results/mining/hybrid_evaluation.json`).

| Tập test, 1.154 người dùng | Precision@5 | Recall@5 |
|---|---|---|
| Popularity (bản cũ) | 0,2017 | 0,0271 |
| Item-based CF (bản cũ) | 0,2310 | **0,0353** |
| Chỉ nội dung (E5 + mô tả Wikipedia) | 0,2175 | 0,0318 |
| Hybrid (α = 0,9) | **0,2314** | 0,0352 |

*Lời thoại:*
> "Gợi ý hybrid cộng hai điểm: điểm CF từ hành vi chấm điểm, và điểm nội dung từ vector mô tả phim. Nhóm em đánh giá đúng theo giao thức của bản cũ: chia dữ liệu theo thời gian, chọn trọng số trên tập validation, báo kết quả trên tập test. Chạy lại CF ra đúng con số của bản cũ, nên so sánh là công bằng. Nói thật là hybrid chỉ ngang CF. Nhưng gợi ý chỉ dựa trên mô tả phim, không dùng hành vi của ai, đã vượt mô hình phổ biến của bản cũ. Đó là giá trị của các nguồn dữ liệu mới."

**Cảnh 9.3** – App → **Người dùng mới**: chọn 3 phim, so sánh "Chỉ CF" và "Hybrid".

*Lời thoại:*
> "Phần nội dung còn làm được ba việc CF không làm được: gợi ý phim mới chưa ai chấm, tìm phim bằng câu mô tả, và giải thích vì sao gợi ý."

### ❓ Thầy có thể hỏi

- **Item-based CF tính thế nào?** Mỗi phim là một vector điểm của các người dùng. Độ tương đồng giữa hai phim là cosine của hai vector. Điểm của phim ứng viên bằng tổng độ tương đồng với các phim người dùng đã chấm ≥ 4 sao, chỉ tính trong 40 hàng xóm gần nhất.
- **Hybrid trộn thế nào?** `điểm = α·CF + (1−α)·nội dung`. Cả hai được chuẩn hóa về [0, 1] (chia cho giá trị lớn nhất). Phần nội dung là cosine giữa vector phim và trung bình vector các phim người dùng thích, nhân thêm độ phổ biến theo thang log. Không có bước nhân này, phần nội dung toàn gợi ý phim gần như không ai xem: P@5 chỉ khoảng 0,02.
- **Vì sao chia theo thời gian, không chia ngẫu nhiên?** Để không dùng dữ liệu tương lai đoán quá khứ (rò rỉ dữ liệu). Mốc t1 = 974862386, t2 = 976422051, giữ nguyên như bản cũ.
- **Precision@5, Recall@5 là gì?** P@5: trong 5 phim gợi ý có bao nhiêu phim người dùng thực sự thích, chia 5. R@5: trong toàn bộ phim người dùng thích ở giai đoạn test, tìm được bao nhiêu phần. Recall thấp vì mỗi người thích nhiều phim mà chỉ được gợi ý 5.
- **Vì sao hybrid không tốt hơn CF?** MovieLens có lịch sử dày (trung bình hơn 160 rating mỗi người), CF đã rất mạnh. Lợi ích của nội dung thể hiện ở cold-start và ở tìm kiếm, không ở chỉ số offline này. Với người mới chỉ có 3 rating, hai mô hình tương đương.
- **Thử những mô hình embedding nào?** MiniLM với chỉ tên và thể loại (nội dung P@5 = 0,153) → MiniLM với mô tả Wikipedia (0,170) → E5 với mô tả Wikipedia (0,2175). Cả chất lượng dữ liệu lẫn mô hình đều quan trọng.
- **Tiền tố `query:` / `passage:` là gì?** Mô hình E5 được huấn luyện với tiền tố này: câu hỏi thêm `query:`, tài liệu thêm `passage:`. Thiếu tiền tố thì chất lượng giảm.
- **HNSW là gì?** Chỉ mục dạng đồ thị nhiều tầng để tìm vector *gần đúng* rất nhanh. Với 3.883 phim thì quét toàn bộ cũng nhanh; HNSW để chứng minh hệ thống mở rộng được.

---

## Chương 10 – Streaming thời gian thực và kết luận (≈ 1′00″)

**Cảnh 10.1 [5′]** – Kafka UI → topic `wiki.recentchange` → chế độ **Live Mode**, message chảy liên tục.

*Lời thoại:*
> "Ngoài CDC, hệ thống còn một luồng streaming thật. Producer đọc luồng sửa bài Wikipedia theo thời gian thực, lọc các lần sửa trên Wikipedia tiếng Anh và tiếng Việt, khoảng một đến ba sự kiện mỗi giây, rồi đẩy vào Kafka. Những lần sửa bài về phim có trong kho được nạp vào bảng fact_wiki_edit, hiện đã có 147 lần. Nếu mất kết nối, producer nối lại từ thời điểm của sự kiện cuối cùng, nên không mất sự kiện."

**Cảnh 10.2 [5′]** – Quay lại sơ đồ, tô sáng 4 khối mới (CDC, Kafka, MinIO, Airflow).

*Lời thoại:*
> "Tóm lại, bản nâng cấp có bảy nguồn với bốn kiểu nạp: file, API, CDC và streaming. Có data lake ba tầng, kho nạp tăng dần có SCD loại hai và chín kiểm tra chất lượng, Airflow điều phối, và phần AI tìm phim bằng ngữ nghĩa. Em xin cảm ơn thầy đã theo dõi."

### ❓ Thầy có thể hỏi

- **SSE là gì?** Server-Sent Events: một kết nối HTTP mở lâu, server đẩy sự kiện xuống liên tục. Code nhận dạng JSON từng dòng (`Accept: application/json`). Khi nối lại thì dùng tham số `since`, có tác dụng như `Last-Event-ID` của SSE.
- **Event time khác processing time?** Event time là lúc sự kiện xảy ra (lúc sửa bài). Processing time là lúc hệ thống nhận được. Bảng `fact_wiki_edit` lưu event time (`edited_at`).

---

## Phụ lục A – Các câu hỏi khó và cách trả lời thẳng

| Câu hỏi | Trả lời |
|---|---|
| Có dùng AI để làm bài không? | Có dùng AI hỗ trợ viết code và tra cứu, giống dùng tài liệu. Nhưng em hiểu từng phần và có thể chạy lại, giải thích, sửa trực tiếp trước mặt thầy. *(Chỉ nói điều này nếu đúng là em đã nắm được – hãy tự chạy lại từng chương ở trên.)* |
| Hệ thống có chịu được dữ liệu lớn không? | Hiện chạy một máy (Kafka 1 node, MinIO 1 node, DuckDB). Muốn mở rộng: tăng partition và số broker Kafka, MinIO phân tán, thay DuckDB bằng Spark khi dữ liệu vượt một máy. Kiến trúc không phải đổi. |
| Điểm yếu lớn nhất? | (1) Chạy một node, chưa có dự phòng lỗi. (2) Message Debezium dạng JSON, chưa có Schema Registry nên đổi cấu trúc bảng nguồn có thể làm hỏng pipeline. (3) Micro-batch sinh nhiều file nhỏ, chưa có bước gộp file. (4) Embedding chạy tay. (5) MovieLens là dữ liệu cũ (2000–2003), phần "thời gian thực" đến từ app giả lập và Wikipedia. |
| Dữ liệu app là thật hay giả? | App và người dùng là mô phỏng: có script giả lập hành vi, và có thể thao tác tay trên app. Còn CDC, Kafka, lake và kho đều chạy thật. |
| Vì sao Postgres làm kho, không dùng kho cột? | Dữ liệu khoảng 1 triệu dòng, Postgres đủ nhanh, có pgvector cho phần AI, và quen thuộc với Superset. Lớn hơn thì cân nhắc ClickHouse hoặc một kho cột. |
| Bảo mật thế nào? | Mọi cổng chỉ mở trên `127.0.0.1`. Mật khẩu nằm trong `.env` (không đưa lên Git). Superset dùng tài khoản chỉ đọc `bi_reader`. |
| Pipeline lỗi giữa chừng thì sao? | Dữ liệu và watermark ghi cùng transaction, lỗi thì rollback, mốc không đổi. Airflow thử lại 2 lần. Bronze vẫn giữ dữ liệu thô để chạy lại. |
| Mất bao lâu để một rating vào kho? | Khoảng 25–35 giây khi bấm chạy tay (Debezium < 1 giây, consumer ≤ 10 giây, Airflow ~15 giây). Nếu để chạy theo lịch thì tối đa 15 phút. |

## Phụ lục B – Bảng số liệu tra nhanh

| Mục | Số |
|---|---|
| Rating MovieLens | 1.000.209 (6.040 user, 3.883 phim, 2000–2003) |
| Ghép IMDb | 2.949 (links.csv) + 857 (tên + năm) = 3.806 phim (98%); 77 không khớp |
| Có bài Wikipedia tiếng Anh | 3.717 phim; tiếng Việt 405; poster 3.636 |
| Lượt xem Wikipedia | 500 phim × 90 ngày ≈ 46.000 dòng |
| Điểm IMDb theo ngày | 3.800 phim/ngày, đang có 3 ngày (11.400 dòng) |
| Kafka | 4 topic × 3 partition, giữ 72 giờ |
| Consumer | flush khi đủ 500 message hoặc 10 giây |
| Parquet | file rating 23 MB → 6 MB |
| Nạp kho | lần đầu ~2 phút; tăng dần vài giây; đọc lùi 1 giờ |
| Kiểm tra chất lượng | 9 |
| Airflow | 3 DAG; `movie_incremental` mỗi 15 phút, 4 task, ~15 giây |
| Từ lúc chấm đến lúc vào kho | ~25–35 giây |
| Embedding | 3.883 vector × 384 chiều, multilingual-e5-small, chỉ mục HNSW |
| Gợi ý (test 1.154 user) | CF 0,2310 / 0,0353 · hybrid 0,2314 / 0,0352 · nội dung 0,2175 / 0,0318 · popularity 0,2017 / 0,0271 |
| Dashboard Superset | 8 chart, làm mới 60 giây, tài khoản chỉ đọc |

## Phụ lục C – Bảng tra khái niệm (1 câu)

| Khái niệm | Một câu |
|---|---|
| WAL | Nhật ký ghi trước của Postgres; CDC đọc nó thay vì quét bảng |
| Replication slot | Postgres nhớ vị trí đã đọc và giữ WAL; dừng lâu thì đầy đĩa |
| LSN | Vị trí trong WAL, dùng để sắp thứ tự và khử trùng |
| at-least-once | Ghi xong mới commit offset: không mất, có thể trùng |
| Medallion | bronze thô → silver sạch → gold phục vụ |
| Parquet | Lưu theo cột, nén tốt, có kiểu dữ liệu và thống kê |
| Watermark | Mốc lớn nhất đã nạp |
| Upsert | Có thì cập nhật, chưa có thì thêm; chạy lại không nhân đôi |
| Idempotent | Chạy lại nhiều lần ra cùng kết quả, nên retry an toàn |
| Grain | Một dòng fact đại diện cho cái gì |
| SCD loại 2 | Giữ lịch sử bằng nhiều phiên bản `valid_from` / `valid_to` |
| Periodic snapshot | Một dòng cho một thực thể mỗi kỳ (phim × ngày) |
| Embedding | Vector biểu diễn nghĩa; gần nghĩa thì gần nhau |
| Cosine | Đo độ giống của 2 vector theo góc giữa chúng |
| HNSW | Chỉ mục đồ thị để tìm vector gần đúng, nhanh |
| Cold-start | Thiếu lịch sử (người mới, phim mới) nên CF không dùng được |
| P@K / R@K | Tỷ lệ đúng trong top-K / tỷ lệ tìm lại được phim liên quan |
