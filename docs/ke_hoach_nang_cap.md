# Kế hoạch nâng cấp đề tài – Phân tích xu hướng xem phim và gợi ý nội dung

Mục tiêu: sửa đúng những điểm bị chê khi bảo vệ (1 nguồn, không data lake, không CDC, demo chỉ có terminal, không giải thích được sơ đồ) và làm **cả Data lẫn AI**, để xin demo lại.

## 1. Hiện trạng và mục tiêu

| | Hiện tại | Sau nâng cấp |
|---|---|---|
| Nguồn | 1 nguồn: MovieLens 1M (CSV tĩnh 2000–2003) | 3 nguồn khác loại: CSV + REST API (TMDB) + database giao dịch (app xem phim) |
| Nạp dữ liệu | Full refresh: `TRUNCATE` rồi nạp lại | Nạp lần đầu + **CDC** (Debezium → Kafka) + nạp tăng dần (upsert) |
| Lưu trữ trung gian | Không có, đi thẳng staging → DW | **Data lake MinIO** 3 tầng bronze / silver / gold (Parquet) |
| Điều phối | Chạy tay từng lệnh Python | **Airflow** DAG, xem được trên giao diện web |
| Kho dữ liệu | Lược đồ sao, 1 bảng fact | Giữ lược đồ sao, mở rộng `dim_movie`, thêm fact snapshot độ phổ biến |
| Khai phá | K-Means + item-based CF | Thêm **gợi ý hybrid** (CF + nội dung), xử lý cold-start, **tìm phim bằng câu mô tả** (embedding) |
| Demo | Terminal + Superset | **App Streamlit**: chấm điểm phim → CDC → pipeline → dashboard và gợi ý thay đổi |

## 2. Kiến trúc đích

```
 MovieLens 1M (CSV) ─────────────┐
 TMDB API (JSON) ────────────────┼──▶ MinIO: bronze ──▶ silver ──▶ gold ──▶ PostgreSQL DW
 App Postgres (OLTP) ─ Debezium ─┘          (DuckDB xử lý)                  │        │
          ▲              │                                                  ▼        ▼
          │            Kafka ──▶ consumer ──▶ bronze/cdc                Superset   Mô hình
          │                                                                         │
          └──────────── App Streamlit (chấm điểm, gợi ý, tìm phim) ◀────────────────┘

                       Airflow điều phối toàn bộ các bước batch
```

Tất cả chạy bằng một file `docker-compose.yml`: postgres-dw, postgres-app, minio, kafka (KRaft, 1 node), debezium-connect, kafka-ui, airflow, superset, streamlit.

> Máy nên có **≥ 16 GB RAM**. Nếu thiếu, bật từng nhóm service theo profile của compose, hoặc thay Kafka bằng Redpanda (nhẹ hơn, cùng giao thức).

## 3. Các giai đoạn

Mỗi giai đoạn có mục **"Phải tự trả lời được"**. Chưa trả lời được thì chưa sang giai đoạn sau.

### Giai đoạn 0 – Dọn repo, dựng khung (1 ngày)

- Tạo nhánh mới `nang-cap`. Chuyển các thư mục `**/evidence/`, `docs/agent/`, các file `*_handoff*`, `*publication*`, `*audit*.json` sang nhánh lưu trữ `archive-ai-log`, xóa khỏi nhánh chính. Repo chỉ giữ code, dữ liệu mẫu, báo cáo.
- Cấu trúc thư mục mới:
  ```
  sources/      tải dữ liệu từ 3 nguồn
  lake/         bronze → silver → gold
  cdc/          cấu hình Debezium, consumer
  warehouse/    schema, nạp tăng dần (gom từ database/ + etl/)
  orchestration/airflow/dags/
  mining/       giữ nguyên + hybrid + semantic search
  app/          Streamlit
  docker-compose.yml
  ```
- Viết `docker-compose.yml` với Postgres DW + MinIO trước, các service khác thêm dần.

**Phải tự trả lời được:** mỗi container làm gì, vì sao tách DB giao dịch (app) và DB kho (DW).

### Giai đoạn 1 – Ba nguồn dữ liệu (2 ngày)

1. **MovieLens 1M (CSV):** dùng lại `mining/source_fetcher.py`.
2. **TMDB API:**
   - Đăng ký API key miễn phí tại themoviedb.org (em tự đăng ký, key để trong `.env`).
   - Ánh xạ `movieId` → `tmdbId` bằng file `links.csv` của bộ MovieLens 25M/32M (movieId giữ nguyên giữa các phiên bản). Phim không khớp thì tìm theo tên + năm, còn lại ghi vào bảng lỗi.
   - Lấy về: `overview`, `poster_path`, `runtime`, `budget`, `revenue`, `vote_average`, `vote_count`, `popularity`, đạo diễn, 5 diễn viên chính, keywords.
   - Lưu nguyên JSON trả về (không sửa), có cache để không gọi lại; tôn trọng giới hạn tốc độ của API.
3. **App xem phim (Postgres OLTP):**
   - Schema `app`: `users`, `movies`, `ratings(user_id, movie_id, rating, created_at, updated_at)`, `watch_history`.
   - Seed users và movies từ MovieLens.
   - Script `simulate_activity.py`: sinh rating mới liên tục (vài rating/giây) để có dữ liệu "đang sống" cho CDC.

**Phải tự trả lời được:** 3 nguồn khác nhau thế nào (file / API / DB), mỗi nguồn khó ở đâu (định dạng, rate limit, dữ liệu thay đổi liên tục); ghép MovieLens với TMDB bằng khóa nào; tỷ lệ khớp được bao nhiêu phần trăm.

### Giai đoạn 2 – Data lake trên MinIO (2–3 ngày)

| Tầng | Nội dung | Định dạng |
|---|---|---|
| **bronze** | Dữ liệu thô đúng như nguồn, không sửa. Phân vùng `source=.../ingest_date=YYYY-MM-DD/` | CSV/JSON gốc, CDC ở dạng JSON |
| **silver** | Đã làm sạch, ép kiểu, bỏ trùng, chuẩn hóa thể loại, ghép ID MovieLens ↔ TMDB | Parquet |
| **gold** | Bảng sẵn sàng nạp kho: `dim_movie`, `dim_user`, `fact_rating`, `fact_movie_popularity` | Parquet |

- Dùng **DuckDB** đọc/ghi thẳng S3 (MinIO) bằng SQL, nhẹ hơn Spark nhiều.
- Mỗi lần chạy ghi lại số dòng vào/ra/lỗi vào bảng `audit.pipeline_run` để hiện lên dashboard giám sát.

**Phải tự trả lời được:** data lake khác data warehouse ở đâu; vì sao cần tầng bronze giữ dữ liệu thô (chạy lại được khi phát hiện lỗi logic); vì sao dùng Parquet thay CSV (dạng cột, nén, giữ kiểu dữ liệu).

### Giai đoạn 3 – CDC (2–3 ngày)

- Bật `wal_level=logical` cho postgres-app.
- Đăng ký **Debezium PostgreSQL connector** theo dõi `app.ratings` và `app.users` → topic Kafka `app.public.ratings`.
- **Consumer Python** đọc topic, gom micro-batch (ví dụ 30 giây hoặc 1.000 bản ghi) rồi ghi vào `bronze/source=app_cdc/`. Xử lý đủ 3 loại thao tác: `c` (thêm), `u` (sửa), `d` (xóa).
- **Kafka UI** để demo: thấy message xuất hiện khi chấm điểm trên app.
- Phương án dự phòng nếu không kịp: nạp tăng dần theo cột `updated_at` (watermark). Phải nói rõ với thầy đây là incremental, chưa phải CDC log-based.

**Phải tự trả lời được:** CDC dựa trên log (WAL) khác polling theo `updated_at` ở đâu (bắt được DELETE, không tải DB nguồn); một message Debezium gồm `before`, `after`, `op`, `ts_ms`; consumer chết giữa chừng thì sao (offset Kafka, ghi idempotent).

### Giai đoạn 4 – Kho dữ liệu nạp tăng dần (2 ngày)

- Giữ lược đồ sao hiện tại, bổ sung:
  - `dim_movie` thêm: `tmdb_id`, `overview`, `runtime`, `budget`, `revenue`, `director`, `poster_url`.
  - `dim_source` (MovieLens / App): biết rating đến từ nguồn nào.
  - Bảng fact mới `fact_movie_popularity` (periodic snapshot): độ phổ biến và điểm TMDB của từng phim theo ngày. Bài sẽ có 2 loại fact: transaction (rating) và periodic snapshot.
- Thay `TRUNCATE` + nạp lại bằng **upsert** (`INSERT ... ON CONFLICT DO UPDATE`) cho dim và `fact_rating`, kèm bảng `etl_watermark` lưu mốc đã nạp.
- Rating bị xóa ở app → đánh dấu `is_deleted` trong fact (xóa mềm).
- Cân nhắc **SCD loại 2** cho `dim_user` (user đổi nghề nghiệp/nhóm tuổi trong app) làm điểm cộng.

**Phải tự trả lời được:** grain của từng fact; SCD loại 1 và loại 2 khác nhau thế nào, vì sao chọn loại đó cho từng dim; chạy pipeline 2 lần liên tiếp có bị nhân đôi dữ liệu không và vì sao.

### Giai đoạn 5 – Điều phối bằng Airflow (1–2 ngày)

DAG `movie_pipeline` (mỗi 15 phút, chạy tay được khi demo):

```
ingest_tmdb (theo ngày) ─┐
cdc_to_bronze ───────────┼─▶ bronze_to_silver ─▶ silver_to_gold ─▶ load_dw ─▶ data_quality_check ─▶ refresh_recommendations
```

- `data_quality_check`: không có khóa ngoại mồ côi, rating trong khoảng 1–5, số dòng gold khớp DW. Sai thì task đỏ, dừng pipeline.
- Consumer CDC chạy như một service riêng (luôn bật), không nằm trong DAG.

**Phải tự trả lời được:** vì sao cần công cụ điều phối thay cho cron; một task lỗi thì các task sau xử lý thế nào; retry.

### Giai đoạn 6 – Phần AI (3–4 ngày)

1. **Gợi ý hybrid:** điểm = α · CF (đã có) + (1 − α) · độ tương đồng nội dung (TF-IDF hoặc embedding của overview + thể loại + keywords + đạo diễn).
   - Đánh giá trên **đúng tập chia theo thời gian cũ**, so 3 mô hình: Popularity, CF, Hybrid (Precision@5, Recall@5).
   - Thử riêng **người dùng mới** (ít hơn 5 rating): CF bó tay, hybrid vẫn gợi ý được. Đây là luận điểm mạnh khi trình bày.
2. **Tìm phim bằng câu mô tả:** embedding overview bằng mô hình đa ngôn ngữ (`paraphrase-multilingual-MiniLM-L12-v2`) để gõ được tiếng Việt; lưu vector trong Postgres bằng **pgvector**, tìm theo cosine.
3. **Giải thích gợi ý:** "Gợi ý vì bạn đã thích *X*, *Y*" (lấy các phim lân cận đóng góp nhiều nhất).
4. Phân cụm K-Means: chạy lại khi có user mới, cập nhật cụm của user trên app.

**Phải tự trả lời được:** CF item-based tính độ tương đồng thế nào; vì sao chia train/test theo thời gian; cold-start là gì; embedding là gì, vì sao tìm được "phim buồn về du hành thời gian" dù mô tả phim không có đúng các chữ đó.

### Giai đoạn 7 – App Streamlit (2–3 ngày)

| Trang | Chức năng |
|---|---|
| Gợi ý cho bạn | Chọn user → 5 phim kèm poster, lý do gợi ý, cụm sở thích của user |
| Chấm điểm | Tìm phim, chấm 1–5 sao → ghi vào postgres-app (kích hoạt CDC) |
| Tìm phim | Ô nhập mô tả tự do → danh sách phim gần nhất |
| Người dùng mới | Chọn 3 phim yêu thích → gợi ý ngay (minh họa cold-start) |
| Pipeline | Trạng thái lần chạy gần nhất, số dòng mỗi tầng, link sang Airflow / MinIO / Kafka UI / Superset |

### Giai đoạn 8 – Bổ sung dashboard (1 ngày)

- Dashboard cũ giữ nguyên.
- Thêm: ngân sách so với điểm đánh giá, top đạo diễn, so sánh điểm MovieLens với điểm TMDB, rating mới từ app theo giờ (thấy được dữ liệu CDC đổ vào).
- Dashboard **giám sát pipeline** từ `audit.pipeline_run`: số dòng mỗi tầng, thời gian chạy, số bản ghi lỗi.

### Giai đoạn 9 – Chuẩn bị demo và hỏi đáp (2 ngày)

- Vẽ lại sơ đồ kiến trúc bằng tay (draw.io). **Tự vẽ để nhớ.**
- Kịch bản demo 5 phút (mục 4), quay video dự phòng.
- Phụ lục bổ sung 1–2 trang: những gì thêm so với bản đã nộp, ảnh chụp kết quả.
- Luyện hỏi đáp: gom toàn bộ mục "Phải tự trả lời được" ở trên thành bộ câu hỏi, nhờ người khác hỏi vặn.
- Gửi email xin thầy kèm video và link repo.

## 4. Kịch bản demo (5 phút)

1. **(30 giây)** Sơ đồ kiến trúc: 3 nguồn → lake → DW → dashboard + mô hình → app.
2. **(1 phút)** Mở app, chọn user 1: 5 phim gợi ý kèm poster và lý do.
3. **(1 phút)** Chấm 5 sao cho 3 phim hoạt hình → mở Kafka UI thấy 3 message → mở MinIO thấy file mới ở `bronze/source=app_cdc/`.
4. **(1 phút)** Bấm chạy DAG trên Airflow, các task lần lượt chuyển xanh.
5. **(1 phút)** Refresh Superset: số rating mới tăng → quay lại app: gợi ý của user 1 đã nghiêng về hoạt hình.
6. **(30 giây)** Gõ "phim buồn về du hành thời gian" ở trang Tìm phim.

## 5. Thời gian và thứ tự ưu tiên

| Tuần | Giai đoạn | Kết quả cuối tuần |
|---|---|---|
| 1 | 0, 1, 2 | 3 nguồn đổ vào MinIO 3 tầng, nạp được vào DW |
| 2 | 3, 4, 5 | CDC chạy, DW nạp tăng dần, DAG Airflow xanh |
| 3 | 6, 7, 8, 9 | App + hybrid + tìm kiếm, demo trơn tru, gửi email |

**Nếu chỉ có 1 tuần (bản tối thiểu):** giai đoạn 0 → 1 → 2 → 3 (dùng phương án watermark nếu Debezium khó) → app Streamlit 2 trang (Gợi ý + Chấm điểm). Đã đủ trả lời 4 điểm thầy chê.

## 6. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Máy yếu, Docker chạy không nổi | Compose profiles, Redpanda thay Kafka, tắt Superset khi không dùng |
| TMDB không khớp được hết phim | Ghi bảng lỗi, báo tỷ lệ khớp; vẫn là kết quả trung thực |
| Debezium cấu hình khó | Phương án watermark ở giai đoạn 3 |
| Hybrid không tốt hơn CF | Vẫn báo trung thực; lợi thế chính là cold-start |
| Lại bị cho là lạm dụng AI | Tự gõ code chính, tự vẽ sơ đồ, commit nhỏ theo từng bước, luyện hỏi đáp |
