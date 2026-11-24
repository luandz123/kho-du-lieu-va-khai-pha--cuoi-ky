@chapter CHƯƠNG 5. NÂNG CẤP THÀNH NỀN TẢNG DỮ LIỆU NHIỀU NGUỒN GẦN THỜI GIAN THỰC

Các chương 2 đến 4 xây dựng hệ thống trên một nguồn dữ liệu tĩnh (MovieLens 1M, 2000–2003), nạp toàn bộ bằng tay và trình diễn chủ yếu qua dòng lệnh. Chương này trình bày bản nâng cấp nhằm khắc phục bốn hạn chế đó: (i) tích hợp **bảy nguồn dữ liệu** với bốn kiểu nạp là tệp, API, CDC và streaming; (ii) bổ sung **data lake** ba tầng; (iii) thu thập thay đổi từ cơ sở dữ liệu giao dịch bằng **CDC**; (iv) trình diễn qua **ứng dụng web, Airflow và dashboard** tự làm mới. Ngoài ra, kho dữ liệu được chuyển sang **nạp tăng dần** có SCD loại 2, quy trình được điều phối tự động kèm kiểm tra chất lượng, và phần gợi ý được mở rộng thành **mô hình lai** có tìm phim bằng câu tiếng Việt. Toàn bộ số liệu trong chương được lấy từ hệ thống đang chạy tại ngày 20/11/2026.

## 5.1. Mục tiêu và tổng quan thay đổi

Bảng 5.1 tóm tắt những điểm khác biệt giữa bản nền tảng (chương 2–4) và bản nâng cấp.

@table Bảng 5.1. So sánh bản nền tảng và bản nâng cấp
@widths 3.6,5.4,7
| Khía cạnh | Bản nền tảng | Bản nâng cấp |
| Nguồn dữ liệu | 1 nguồn: MovieLens 1M, tệp tĩnh | 7 nguồn, 4 kiểu nạp: tệp (MovieLens, IMDb), API (Wikidata, Wikipedia Pageviews, Wikipedia tóm tắt và poster), CDC (cơ sở dữ liệu của ứng dụng xem phim), streaming (Wikimedia EventStreams) |
| Lưu trữ trung gian | Schema staging trong PostgreSQL | Data lake MinIO (chuẩn S3) chia ba tầng bronze → silver → gold, xử lý bằng DuckDB, lưu Parquet |
| Thu thập thay đổi | Không có | Debezium đọc WAL của PostgreSQL → Kafka → data lake; bắt đủ INSERT, UPDATE, DELETE |
| Chiến lược nạp kho | Nạp toàn bộ trong một giao dịch | Nạp tăng dần theo watermark và upsert; chạy lại không nhân đôi |
| Mô hình chiều | 1 bảng sự kiện, chiều ghi đè | 4 bảng sự kiện (giao dịch, chụp nhanh hằng ngày, streaming), SCD loại 2 cho người dùng, xóa mềm |
| Điều phối | Chạy tay từng lệnh Python | Apache Airflow: 3 DAG, thử lại tự động, 9 kiểm tra chất lượng |
| Trình diễn | Dòng lệnh và 3 dashboard tĩnh | Ứng dụng Streamlit 5 trang, dashboard Superset tự làm mới 60 giây, Kafka UI, MinIO Console |
| Gợi ý | Item-based CF | Lai CF + nội dung (embedding đa ngôn ngữ); tìm phim bằng câu tiếng Việt (pgvector) |

## 5.2. Kiến trúc tổng thể

Hình 5.1 trình bày luồng dữ liệu của bản nâng cấp, chia thành năm cột từ trái sang phải.

@fig ../movie_platform_dataflow.png | Hình 5.1. Luồng dữ liệu của bản nâng cấp | 16

- **Nguồn:** bảy nguồn với bốn kiểu nạp (mục 5.3).
- **Nạp:** dữ liệu batch do các task Airflow lấy theo lịch và ghi nguyên bản vào tầng bronze; dữ liệu CDC và streaming đi qua Kafka, sau đó một consumer gom thành micro-batch và ghi xuống bronze.
- **Data lake:** MinIO lưu ba tầng bronze, silver, gold; các bước biến đổi viết bằng SQL và chạy trên DuckDB, đọc ghi trực tiếp trên S3.
- **Kho dữ liệu:** PostgreSQL 17 kèm phần mở rộng pgvector, lược đồ sao được nạp tăng dần từ tầng gold.
- **Khai thác:** dashboard Superset và ứng dụng Streamlit.

Mọi thành phần chạy bằng một tệp `docker-compose.yml` trên một máy (Bảng 5.2); Superset chạy trong một compose riêng. Toàn bộ hệ thống dùng khoảng 8 GB RAM; Kafka và Debezium được giới hạn bộ nhớ heap 512 MB mỗi dịch vụ.

@table Bảng 5.2. Các dịch vụ của bản nâng cấp
@widths 4.2,4.6,7.2
| Dịch vụ | Công nghệ, phiên bản | Vai trò |
| dw | PostgreSQL 17 + pgvector 0.8.0 | Kho dữ liệu: lược đồ sao, vector phim, nhật ký nạp |
| app-db | PostgreSQL 17 | Cơ sở dữ liệu giao dịch của ứng dụng xem phim, bật wal_level = logical |
| kafka | Apache Kafka 3.9.0 (KRaft) | Hàng đợi sự kiện, 3 partition mỗi topic, giữ dữ liệu 72 giờ |
| connect | Debezium 2.7.3 | Đọc WAL của app-db, phát sự kiện thay đổi vào Kafka |
| cdc-consumer | Python | Đọc Kafka, gom micro-batch, ghi tầng bronze |
| wiki-producer | Python | Đọc luồng Wikimedia EventStreams, đẩy vào Kafka |
| minio | MinIO (chuẩn S3) | Data lake, bucket `lake` |
| airflow | Apache Airflow 2.10.4 | Điều phối 3 DAG |
| kafka-ui | Kafka UI | Quan sát topic, message, consumer group |
| superset | Apache Superset 6.1.0 | Dashboard, kết nối kho bằng tài khoản chỉ đọc |

## 5.3. Tích hợp dữ liệu từ nhiều nguồn

### 5.3.1. Bảy nguồn dữ liệu

Bảng 5.3 liệt kê các nguồn dữ liệu. Các nguồn khác nhau cả về định dạng lẫn nhịp cập nhật: có nguồn chỉ lấy một lần, có nguồn cập nhật mỗi ngày, có nguồn sinh dữ liệu liên tục.

@table Bảng 5.3. Bảy nguồn dữ liệu của bản nâng cấp
@widths 3.4,2.8,2.6,7.2
| Nguồn | Dạng | Tần suất | Nội dung sử dụng |
| MovieLens 1M | Tệp .dat | Một lần | 1.000.209 lượt đánh giá lịch sử, 6.040 người dùng, 3.883 phim |
| IMDb datasets | TSV nén | Hằng ngày | Điểm và số lượt bình chọn (title.ratings), thời lượng, đạo diễn, diễn viên |
| Wikidata | SPARQL | Một lần | Ghép mã IMDb với bài Wikipedia tiếng Anh, tiếng Việt; quốc gia; số giải Oscar |
| Wikipedia Pageviews | REST API | Hằng ngày | Lượt xem bài Wikipedia theo ngày của 500 phim nhiều đánh giá nhất |
| Wikipedia API | MediaWiki API | Một lần | Đoạn mở đầu bài viết (3.717 phim tiếng Anh, 405 phim tiếng Việt) và ảnh poster (3.636 phim) |
| Ứng dụng xem phim | PostgreSQL → CDC | Liên tục | Đánh giá mới, xóa đánh giá, thay đổi thông tin người dùng |
| Wikimedia EventStreams | Luồng sự kiện (SSE) | Liên tục | Các lần sửa bài trên Wikipedia tiếng Anh và tiếng Việt |

Nguồn IMDb cung cấp tệp `title.ratings` cập nhật mỗi ngày, nên mỗi ngày hệ thống chụp lại một bản để theo dõi biến động điểm và số lượt bình chọn. Lượt xem Wikipedia phản ánh mức độ quan tâm của công chúng tới từng phim. Ứng dụng xem phim là nguồn dữ liệu “sống”: người dùng chấm điểm, sửa điểm, xóa điểm, đổi thông tin cá nhân bất cứ lúc nào.

Các API của Wikimedia giới hạn tốc độ truy cập: 10 request mỗi phút với ứng dụng không khai báo thông tin liên hệ. Mã nguồn gọi API tuần tự, giãn cách giữa các request, gặp lỗi HTTP 429 thì chờ đúng số giây trong header `Retry-After` rồi thử lại. Phần tóm tắt bài viết dùng API lấy 20 bài mỗi request; phần lượt xem chỉ lấy cho 500 phim nhiều đánh giá nhất. Ban đầu nhóm dự định dùng TMDB cho mô tả và poster phim, nhưng dịch vụ này không truy cập được từ mạng tại Việt Nam, nên được thay bằng Wikipedia và IMDb.

### 5.3.2. Ghép MovieLens với IMDb

Khó khăn lớn nhất khi tích hợp là MovieLens và IMDb không có khóa chung. Nhóm ghép theo hai bước:

- **Bước 1 – theo bảng liên kết:** dùng tệp `links.csv` của bộ ml-latest-small. ML-1M không kèm tệp này, nhưng MovieLens giữ nguyên `movieId` giữa các phiên bản, nên dùng chung được. Bước này ghép được **2.949** phim.
- **Bước 2 – theo tên và năm:** với các phim còn lại, tên phim được chuẩn hóa (bỏ dấu, chuyển mạo từ “The”, “A” ở cuối tên lên đầu, tách tên thay thế trong ngoặc), sau đó ghép theo tên và năm phát hành, cho phép lệch tối đa một năm. Nếu nhiều phim IMDb cùng khớp thì chọn phim có nhiều lượt bình chọn nhất. Bước này ghép thêm **857** phim, ví dụ “Bloody Child, The (1996)” khớp với “The Bloody Child (1996)”.

Tổng cộng **98%** số phim được ghép với IMDb. 77 phim còn lại được để trống thay vì đoán, vì ghép sai còn gây hại hơn thiếu dữ liệu. Cột `imdb_match` trong bảng `dim_movie` ghi rõ mỗi phim được ghép bằng cách nào (`links`, `title_year` hoặc rỗng), giúp truy vết khi cần kiểm tra.

## 5.4. Thu thập thay đổi dữ liệu (CDC) và Kafka

### 5.4.1. Cơ sở dữ liệu nguồn của ứng dụng

Ứng dụng xem phim có cơ sở dữ liệu PostgreSQL riêng với hai bảng `users` và `ratings`, được khởi tạo bằng dữ liệu người dùng của MovieLens. Để Debezium đọc được thay đổi, cơ sở dữ liệu này được cấu hình:

- `wal_level = logical`: cho phép giải mã WAL thành thay đổi theo từng dòng.
- Publication `dbz_publication` cho hai bảng `ratings` và `users`: khai báo những bảng được phát thay đổi qua plugin `pgoutput`.
- Replication slot `debezium_app`: PostgreSQL ghi nhớ Debezium đã đọc tới vị trí nào trong WAL. Khi Debezium khởi động lại, nó đọc tiếp đúng từ vị trí đó, không bỏ sót thay đổi.
- `REPLICA IDENTITY FULL`: WAL ghi cả giá trị cũ của dòng, nhờ đó sự kiện UPDATE và DELETE có trường `before` đầy đủ.

**Ứng dụng không gửi gì sang Kafka.** Mỗi thao tác trên ứng dụng chỉ là một lệnh INSERT, UPDATE hoặc DELETE vào cơ sở dữ liệu của chính nó; Debezium tự đọc thay đổi từ WAL. Đây là điểm khác biệt cơ bản giữa CDC dựa trên log với việc ứng dụng tự ghi sự kiện, hoặc với việc định kỳ truy vấn theo cột `updated_at`.

### 5.4.2. Sự kiện thay đổi của Debezium

Hình 5.2 là một message do Debezium gửi vào topic `app.public.ratings` khi người dùng 6050 chấm 5 sao cho phim Toy Story 2 (mã 3114).

@fig figures/nang_cap/kafka_json.jpg | Hình 5.2. Message Debezium cho một lượt đánh giá mới (Kafka UI) | 14

Các trường quan trọng của message gồm:

- `op`: loại thay đổi; `c` là thêm mới, `u` là cập nhật, `d` là xóa, `r` là đọc trong lần chụp ban đầu (snapshot).
- `before` và `after`: giá trị của dòng trước và sau thay đổi. Với thêm mới, `before` rỗng; với xóa, `after` rỗng.
- `source.lsn`: vị trí của thay đổi trong WAL, dùng để sắp đúng thứ tự và loại bản ghi trùng ở tầng silver.
- `ts_ms`: thời điểm Debezium xử lý sự kiện.

Debezium chạy ở chế độ `snapshot.mode = initial`: lần đầu khởi động, nó đọc toàn bộ dữ liệu hiện có (sự kiện `op = r`) rồi mới chuyển sang đọc WAL. Bảng `users` có 6.040 dòng nên sinh 6.040 sự kiện `r`; tầng silver bỏ qua các sự kiện này vì chúng trùng với dữ liệu MovieLens đã nạp. Message rỗng (tombstone) sau mỗi lần xóa được tắt (`tombstones.on.delete = false`) vì hệ thống không dùng cơ chế log compaction của Kafka.

### 5.4.3. Kafka và consumer ghi data lake

Kafka có bốn topic, mỗi topic ba partition, giữ dữ liệu 72 giờ: hai topic CDC (`app.public.ratings`, `app.public.users`) và hai topic streaming (`wiki.recentchange`, `wiki.movie_edits`). Debezium dùng khóa chính của dòng làm key của message, nên mọi thay đổi của cùng một dòng rơi vào cùng một partition và giữ đúng thứ tự.

Kafka đứng giữa nguồn và data lake để tách bên gửi khỏi bên nhận: làm vùng đệm khi phía sau chậm hoặc dừng, cho nhiều consumer cùng đọc một luồng, và cho phép đọc lại dữ liệu trong thời gian lưu giữ.

Consumer thuộc consumer group `lake-bronze-writer`, đọc cả bốn topic và gom message thành micro-batch: đủ **500 message hoặc 10 giây** thì ghi một tệp JSON Lines xuống tầng bronze. Mỗi dòng trong tệp giữ nguyên message gốc kèm thông tin `_kafka` (topic, partition, offset). Điểm quan trọng nhất là consumer **chỉ commit offset sau khi tệp đã được ghi xong**:

@code
BATCH_SIZE, FLUSH_SECONDS = 500, 10
...
if pending >= BATCH_SIZE or (pending and time.time() - last_flush >= FLUSH_SECONDS):
    flush(buffers)                       # ghi tệp JSONL xuống MinIO trước
    consumer.commit(asynchronous=False)  # rồi mới commit offset
    last_flush = time.time()
@endcode

Nếu consumer dừng giữa chừng, khi khởi động lại nó đọc lại từ offset chưa commit: dữ liệu không mất, chỉ có thể bị ghi trùng (ngữ nghĩa *at-least-once*). Bản trùng được loại ở tầng silver nhờ khử trùng theo khóa và LSN; kết hợp với upsert ở kho, hệ thống đạt hiệu quả tương đương *exactly-once* mà không cần giao dịch phân tán.

### 5.4.4. Luồng streaming từ Wikipedia

Ngoài CDC, hệ thống có một luồng streaming thật. Producer giữ một kết nối HTTP mở lâu tới Wikimedia EventStreams (giao thức Server-Sent Events), lọc các lần sửa và tạo bài trên Wikipedia tiếng Anh và tiếng Việt (khoảng một đến ba sự kiện mỗi giây) rồi đẩy vào topic `wiki.recentchange`. Những lần sửa bài về phim có trong kho được đẩy thêm vào topic `wiki.movie_edits` và cuối cùng được nạp vào bảng `fact_wiki_edit` (147 lần sửa tại thời điểm viết báo cáo). Khi mất kết nối, producer nối lại kèm tham số `since` bằng thời điểm của sự kiện cuối cùng đã nhận, nên không mất sự kiện. Bảng sự kiện lưu thời điểm sửa bài (event time) chứ không phải thời điểm hệ thống nhận được (processing time).

## 5.5. Data lake ba tầng

Data lake chạy trên MinIO, tương thích giao thức S3 của Amazon, với bucket `lake` chia ba tầng theo kiến trúc medallion (Bảng 5.4).

@table Bảng 5.4. Ba tầng của data lake
@widths 2.4,7.6,6
| Tầng | Nội dung | Định dạng |
| Bronze | Dữ liệu thô đúng như nguồn gửi về, chia thư mục theo ngày nhận `ingest_date=YYYY-MM-DD` | DAT, CSV, TSV.gz, JSONL |
| Silver | Làm sạch, ép kiểu; khử trùng sự kiện CDC theo khóa và LSN; ghép các nguồn (MovieLens ↔ IMDb ↔ Wikidata ↔ Wikipedia) | Parquet nén zstd |
| Gold | Đúng hình dạng các bảng của kho (`dim_*`, `fact_*`) theo khóa tự nhiên, kèm `changed_at` để nạp tăng dần | Parquet |

Hình 5.3 là thư mục chứa sự kiện CDC của bảng đánh giá trong ngày 20/11/2026, sắp xếp theo thời gian sửa đổi: tệp mới nhất (15:49) là micro-batch chứa hai lượt đánh giá vừa chấm trên ứng dụng.

@fig figures/nang_cap/minio_bronze.jpg | Hình 5.3. Tầng bronze trên MinIO Console với tệp micro-batch mới nhất | 14

**Tầng silver.** Với sự kiện CDC của bảng đánh giá, silver lấy dòng `after` (hoặc `before` nếu là xóa), chỉ giữ sự kiện mới nhất của mỗi cặp người dùng – phim theo LSN; nếu sự kiện mới nhất là xóa thì gắn cờ `is_deleted`. Đoạn SQL rút gọn trong `transform/silver.py`:

@code
WITH ev AS (
    SELECT op, coalesce(after, before) AS row, source.lsn AS lsn, ts_ms
    FROM read_json('s3://lake/bronze/app_cdc/ratings/*/*.jsonl', ...))
SELECT row.user_id, row.movie_id, row.rating,
       to_timestamp(ts_ms / 1000) AS changed_at, op = 'd' AS is_deleted
FROM ev
QUALIFY row_number() OVER (PARTITION BY row.user_id, row.movie_id
                           ORDER BY lsn DESC, ts_ms DESC) = 1
@endcode

Với bảng người dùng, silver chỉ lấy sự kiện `c` và `u`, bỏ 6.040 sự kiện snapshot `r` vì trùng dữ liệu MovieLens.

**Lý do giữ tầng bronze.** Bronze cho phép xử lý lại khi phát hiện lỗi logic ở silver hoặc gold mà không cần lấy lại dữ liệu từ nguồn. Điều này đặc biệt quan trọng với sự kiện CDC và streaming: các sự kiện đã qua không thể lấy lại từ nguồn. Các bước silver và gold có tính *idempotent* (cùng đầu vào cho cùng kết quả), nên Airflow có thể thử lại an toàn.

**Lý do dùng Parquet và DuckDB.** Parquet lưu theo cột nên chỉ đọc các cột cần dùng, nén tốt và giữ kiểu dữ liệu: tệp đánh giá 23 MB ở dạng gốc chỉ còn 6 MB ở dạng Parquet. DuckDB là cơ sở dữ liệu phân tích chạy ngay trong tiến trình Python, đọc ghi trực tiếp CSV, JSON và Parquet trên S3 bằng SQL. Với quy mô vài GB, DuckDB đủ nhanh trên một máy mà không cần cụm Spark.

## 5.6. Kho dữ liệu nạp tăng dần

### 5.6.1. Lược đồ sao mở rộng

Kho dữ liệu của bản nâng cấp vẫn theo lược đồ sao nhưng mở rộng cả chiều lẫn bảng sự kiện (Hình 5.4, Bảng 5.5).

@fig figures/nang_cap/luoc_do_sao_moi.png | Hình 5.4. Lược đồ sao của kho dữ liệu bản nâng cấp | 16

@table Bảng 5.5. Các bảng trong kho dữ liệu bản nâng cấp
@widths 4.6,3.8,5.2,2.4
| Bảng | Loại | Grain, ghi chú | Số dòng |
| dim_user | Chiều, SCD loại 2 | Một phiên bản người dùng; valid_from, valid_to, is_current | 6.049 |
| dim_movie | Chiều, SCD loại 1 | Ghi đè; thêm đạo diễn, diễn viên, quốc gia, Oscar, poster | 3.883 |
| dim_date, dim_genre, dim_source | Chiều | Lịch ngày 1995–2030; 18 thể loại; nguồn movielens / app | – |
| fact_rating | Sự kiện, trạng thái hiện tại | Một cặp người dùng × phim; is_deleted cho xóa mềm | 1.000.277 |
| fact_imdb_rating_daily | Chụp nhanh định kỳ | Một phim × một ngày | 11.400 |
| fact_pageviews_daily | Chụp nhanh định kỳ | Một phim × một ngày | 45.988 |
| fact_wiki_edit | Giao dịch (streaming) | Một lần sửa bài Wikipedia | 147 |
| movie_embedding | Vector (pgvector) | Vector 384 chiều, chỉ mục HNSW | 3.883 |
| etl.watermark, etl.pipeline_run | Vận hành | Mốc đã nạp; nhật ký từng lần chạy | – |

Bảng `fact_rating` giữ **đánh giá hiện tại** của mỗi cặp người dùng × phim: chấm lại thì ghi đè, xóa thì đánh dấu `is_deleted`. Khóa chính là cặp khóa tự nhiên `(user_id, movie_id)` để phục vụ upsert; các khóa thay thế `user_key`, `movie_key`, `date_key`, `source_key` vẫn là khóa ngoại tới các bảng chiều. Chiều `dim_source` cho phép tách đánh giá lịch sử của MovieLens (6.040 người dùng ban đầu) với đánh giá mới từ ứng dụng qua CDC (74 lượt tại thời điểm viết báo cáo). Hai bảng chụp nhanh có thước đo khác nhau về tính cộng: lượt xem cộng được theo ngày, còn điểm IMDb **không cộng được**, chỉ lấy trung bình hoặc giá trị cuối kỳ.

### 5.6.2. Nạp tăng dần bằng watermark và upsert

Bản nền tảng xóa sạch bảng rồi nạp lại một triệu dòng ở mỗi lần chạy. Bản nâng cấp chỉ nạp phần thay đổi:

- Bảng `etl.watermark` lưu thời điểm thay đổi lớn nhất (`changed_at`) đã nạp vào kho.
- Mỗi lần chạy chỉ đọc các dòng ở tầng gold có `changed_at` lớn hơn **mốc watermark trừ đi một giờ**. Việc đọc lùi một giờ tránh bỏ sót các sự kiện đến muộn, do Kafka có ba partition và consumer có thể ghi lại dữ liệu theo ngữ nghĩa at-least-once.
- Dữ liệu được ghi bằng `INSERT ... ON CONFLICT DO UPDATE`, **chỉ ghi đè khi bản mới hơn**, nên phần chồng lấn do đọc lùi hay việc chạy lại không làm nhân đôi dữ liệu.
- Dữ liệu và watermark được ghi trong **cùng một giao dịch**. Nếu ghi watermark trước mà nạp dữ liệu thất bại, các thay đổi trong khoảng đó sẽ bị mất vĩnh viễn.

@code
INSERT INTO dw.fact_rating AS f (...) SELECT ... FROM staged
ON CONFLICT (user_id, movie_id) DO UPDATE SET
    user_key = EXCLUDED.user_key, date_key = EXCLUDED.date_key, source_key = EXCLUDED.source_key,
    rating = EXCLUDED.rating, rated_at = EXCLUDED.rated_at, is_deleted = EXCLUDED.is_deleted,
    changed_at = EXCLUDED.changed_at, loaded_at = now()
WHERE EXCLUDED.changed_at > f.changed_at;      -- chỉ ghi đè khi bản mới hơn
@endcode

Lần nạp đầu tiên (khoảng một triệu dòng) mất khoảng hai phút; các lần sau chỉ mất vài giây. Mỗi bước ghi một dòng vào `etl.pipeline_run` với số dòng vào, số dòng ra, thời gian và trạng thái, phục vụ giám sát trên dashboard.

### 5.6.3. Chiều thay đổi chậm loại 2 cho người dùng

Khi người dùng đổi nghề nghiệp hoặc nhóm tuổi trên ứng dụng, kho không ghi đè mà đóng phiên bản cũ (gán `valid_to`, `is_current = false`) và thêm phiên bản mới. Mỗi đánh giá được gắn với phiên bản người dùng **có hiệu lực tại thời điểm chấm**, nhờ đó phân tích theo nghề nghiệp vẫn đúng với quá khứ. Phiên bản đầu tiên của mỗi người dùng có `valid_from = 1990-01-01`, trước mọi đánh giá của MovieLens, để đánh giá lịch sử luôn tìm được phiên bản phù hợp. Ngược lại, `dim_movie` dùng SCD loại 1 (ghi đè) vì phân tích chỉ cần thông tin phim mới nhất. SCD loại 2 bắt buộc dùng khóa thay thế `user_key`, vì một `user_id` có thể có nhiều dòng; chỉ mục duy nhất có điều kiện `UNIQUE (user_id) WHERE is_current` bảo đảm mỗi người chỉ có một phiên bản hiện tại.

### 5.6.4. Kiểm tra chất lượng dữ liệu

Cuối mỗi lần chạy `movie_incremental` và `movie_bootstrap` có chín kiểm tra chất lượng (Bảng 5.6). Chỉ cần một kiểm tra sai, chương trình thoát với mã lỗi, task trên Airflow chuyển đỏ và các bước phía sau không chạy. Các lỗi như khóa rỗng, trùng khóa hay sai tham chiếu đã được ràng buộc khóa chính, khóa ngoại và `NOT NULL` của kho chặn ngay khi ghi, nên không cần kiểm tra lại.

@table Bảng 5.6. Chín kiểm tra chất lượng sau mỗi lần nạp
@widths 0.9,7.4,7.7
| # | Kiểm tra | Mục đích |
| 1 | Đánh giá nằm trong khoảng 1–5 | Miền giá trị |
| 2 | Mỗi người dùng có đúng một phiên bản hiện tại | Tính đúng của SCD loại 2 |
| 3 | Các phiên bản của một người không chồng lấn thời gian | Tính đúng của SCD loại 2 |
| 4 | Đánh giá trỏ đúng phiên bản có hiệu lực tại thời điểm chấm | Gắn khóa theo thời gian |
| 5 | Không có đánh giá ở thời điểm tương lai | Phát hiện lỗi đồng hồ, lỗi múi giờ |
| 6 | Phim nào cũng có ít nhất một thể loại | Đầy đủ bảng cầu nối |
| 7 | Số cặp người dùng – phim ở gold bằng ở kho | Đối soát lake ↔ kho |
| 8 | Số đánh giá đã xóa ở gold bằng ở kho | Đối soát xóa mềm |
| 9 | Kho bắt kịp thay đổi mới nhất trong lake | Độ tươi của dữ liệu |

Các kiểm tra 7–9 đối soát giữa hai hệ thống khác nhau: DuckDB đọc trạng thái mới nhất của từng cặp ở tầng gold, PostgreSQL đếm trên kho, rồi so sánh kết quả. Đây là bước kế thừa tinh thần đối soát của bản nền tảng (mục 3.2.4) cho bối cảnh nạp tăng dần.

## 5.7. Điều phối bằng Apache Airflow

Airflow 2.10.4 chạy với LocalExecutor và có ba DAG (Bảng 5.7). Mỗi task chỉ gọi đúng một lệnh Python của dự án; phần xử lý nặng do DuckDB và PostgreSQL đảm nhận, Airflow chỉ điều phối.

@table Bảng 5.7. Ba DAG trên Airflow
@widths 3.8,3.2,9
| DAG | Lịch chạy | Các bước |
| movie_incremental | Mỗi 15 phút | bronze_to_silver → silver_to_gold → load_warehouse → data_quality |
| movie_daily | 08:00 mỗi ngày | Tải điểm IMDb và lượt xem Wikipedia (song song) → silver → gold → nạp hai bảng chụp nhanh |
| movie_bootstrap | Chạy tay | Nạp toàn bộ từ đầu: MovieLens, IMDb, Wikidata, tóm tắt và lượt xem Wikipedia 90 ngày → silver → gold → kho → kiểm tra chất lượng |

Các DAG được cấu hình `catchup = False` (không chạy bù các kỳ đã qua khi bật DAG), `max_active_runs = 1` (không để hai lần chạy chồng nhau cùng ghi kho) và `retries = 2` (thử lại hai lần, mỗi lần cách một phút). Việc thử lại an toàn vì mọi bước đều idempotent. Ứng dụng web có nút “Chạy pipeline ngay” gọi REST API của Airflow để kích hoạt `movie_incremental` mà không phải chờ tới lịch 15 phút. Hình 5.5 cho thấy lịch sử chạy của DAG này với cả bốn task đều thành công.

@fig figures/nang_cap/airflow_grid.jpg | Hình 5.5. Lịch sử chạy DAG movie_incremental trên Airflow | 15

Bước tạo embedding không chạy trong Airflow vì cần thư viện PyTorch, trong khi image Airflow được giữ gọn nhẹ; mô tả phim gần như không đổi nên bước này chỉ cần chạy tay khi có dữ liệu mô tả mới.

## 5.8. Kiểm chứng đầu – cuối trên ứng dụng

Ứng dụng Streamlit có năm trang: Gợi ý cho bạn, Chấm điểm, Người dùng mới, Tìm phim theo mô tả và Pipeline. Mọi thao tác ghi thẳng vào cơ sở dữ liệu của ứng dụng, đúng như một ứng dụng giao dịch thông thường. Trang Chấm điểm có thêm **panel hành trình** theo dõi một thay đổi đi qua từng chặng của hệ thống: tìm message tương ứng trong Kafka (theo key và thời điểm), tìm tệp chứa message đó ở tầng bronze (theo partition và offset), theo dõi lần chạy Airflow và kiểm tra dòng tương ứng trong kho.

Hình 5.6 là kết quả một lần kiểm chứng: tạo người dùng mới 6050, chấm 5 sao cho Toy Story và Toy Story 2, rồi bấm chạy pipeline.

@fig figures/nang_cap/app_pipeline.jpg | Hình 5.6. Panel hành trình của một thay đổi trên ứng dụng | 15

@table Bảng 5.8. Mốc thời gian của thay đổi trong Hình 5.6
@widths 5,2.6,8.4
| Chặng | Thời điểm | Bằng chứng |
| PostgreSQL của ứng dụng | 15:49:00 | INSERT lượt đánh giá Toy Story 2 |
| Kafka (Debezium đọc WAL) | 15:49:01 | Topic app.public.ratings, op = c, partition 1, offset 28 |
| MinIO bronze (consumer) | 15:49:03 | Tệp app_cdc/ratings/ingest_date=2026-11-20/20261120T084903169128.jsonl |
| Airflow movie_incremental | 15:49:25 | Lần chạy thủ công, 4/4 task thành công |
| Kho dữ liệu | 15:49:40 | Dòng tương ứng trong dw.fact_rating, rating = 5 |

Như vậy, chỉ khoảng **40 giây** sau khi người dùng chấm điểm, thay đổi đã đi qua toàn bộ hệ thống và nằm trong kho; trong đó hơn 20 giây là thời gian chờ kích hoạt và khởi động task của Airflow. Ngay bên dưới panel, ứng dụng hiển thị gợi ý cho người dùng trước và sau khi chấm (Hình 5.7): trước khi chấm, người dùng chưa có lịch sử nên được gợi ý phim phổ biến (American Beauty, các phim Star Wars, Jurassic Park); sau khi chấm hai phim hoạt hình, cả năm gợi ý chuyển sang phim hoạt hình và gia đình (A Bug's Life, Aladdin, Babe…). Dữ liệu mới đã đi hết đường ống tới tận mô hình gợi ý.

@fig figures/nang_cap/app_goi_y.jpg | Hình 5.7. Gợi ý cho người dùng mới trước và sau khi chấm điểm | 15

Tương tự, khi người dùng xóa một đánh giá, Debezium phát sự kiện `op = d`, silver gắn `is_deleted = true` và kho đánh dấu xóa mềm; khi người dùng đổi nghề nghiệp, panel báo `dim_user` có thêm một phiên bản theo SCD loại 2. Cả hai trường hợp đã được kiểm thử và đều vượt qua chín kiểm tra chất lượng.

## 5.9. Dashboard thời gian thực

Dashboard mới `movie-platform` trên Superset gồm 8 biểu đồ đọc thẳng từ các khung nhìn phân tích của kho, tự làm mới mỗi 60 giây và kết nối bằng vai trò `bi_reader` chỉ có quyền đọc (Hình 5.8):

- số đánh giá mới từ ứng dụng qua CDC và biểu đồ theo giờ;
- phim đang được quan tâm theo lượt xem Wikipedia 7 ngày gần nhất và mức tăng so với 7 ngày trước, ví dụ Home Alone tăng mạnh khi gần Giáng sinh;
- lượt xem Wikipedia theo thể loại;
- so sánh điểm MovieLens với điểm IMDb (quy về cùng thang điểm 10): người dùng MovieLens chấm các phim Pokémon thấp hơn IMDb khoảng 2,9 điểm;
- đạo diễn có nhiều phim được chấm (lấy từ IMDb);
- lịch sử phiên bản người dùng theo SCD loại 2 và giám sát các lần chạy pipeline.

@fig figures/nang_cap/superset_1.jpg | Hình 5.8. Dashboard thời gian thực trên Apache Superset | 15.5

Các biểu đồ này chỉ có được nhờ các nguồn dữ liệu mới: bản nền tảng chỉ có điểm MovieLens nên không thể so sánh với IMDb, không đo được mức độ quan tâm hiện tại và không có dữ liệu mới phát sinh.

## 5.10. Gợi ý lai và tìm phim theo ngữ nghĩa

### 5.10.1. Biểu diễn phim bằng embedding

Mỗi phim được ghép thành một đoạn văn gồm tên, thể loại, đoạn mở đầu bài Wikipedia (700 ký tự tiếng Anh và 400 ký tự tiếng Việt nếu có), đạo diễn, diễn viên và quốc gia. Mô hình `intfloat/multilingual-e5-small` biến đoạn văn này thành một vector 384 chiều; vector của 3.883 phim được lưu trong bảng `movie_embedding` bằng kiểu `vector` của pgvector, kèm chỉ mục HNSW. Theo cách mô hình E5 được huấn luyện, tài liệu được thêm tiền tố `passage:` và câu truy vấn thêm tiền tố `query:`; thiếu tiền tố này thì chất lượng tìm kiếm giảm.

### 5.10.2. Tìm phim bằng câu tiếng Việt

Khi người dùng gõ một câu mô tả, câu đó cũng được biến thành vector và kho tìm các phim có vector gần nhất theo khoảng cách cosine (toán tử `<=>` của pgvector):

@code
SELECT m.title, 1 - (e.embedding <=> %(q)s::vector) AS similarity
FROM dw.movie_embedding e JOIN dw.dim_movie m USING (movie_key)
ORDER BY e.embedding <=> %(q)s::vector
LIMIT 10;
@endcode

Vì mô hình học đa ngôn ngữ, câu cùng nghĩa ở các ngôn ngữ khác nhau cho vector gần nhau. Câu “phim kinh dị về cá mập” trả về Jaws (1975) ở vị trí đầu tiên (Hình 5.9), câu “tàu chìm, chuyện tình trên biển” trả về Titanic (1997), dù mô tả của cả hai phim đều viết bằng tiếng Anh.

@fig figures/nang_cap/tim_phim_jaws.jpg | Hình 5.9. Tìm phim bằng câu tiếng Việt trên ứng dụng | 15

### 5.10.3. Mô hình lai CF và nội dung

Mô hình lai kết hợp hai điểm cho mỗi phim ứng viên i của người dùng u:

@eq \mathrm{score}(u, i) = \alpha \cdot \widetilde{\mathrm{CF}}(u, i) + (1 - \alpha) \cdot \widetilde{\mathrm{CB}}(u, i)

trong đó CF là điểm item-based CF ở mục 4.2.2 (k = 40), CB là điểm nội dung bằng cosine giữa vector của phim i và trung bình vector các phim người dùng đánh giá từ 4 sao, nhân với một hệ số độ phổ biến theo thang logarit. Cả hai điểm được chuẩn hóa về đoạn [0, 1] bằng cách chia cho giá trị lớn nhất của từng người dùng. Hệ số độ phổ biến là cần thiết: không có nó, phần nội dung toàn gợi ý những phim gần như không ai xem và Precision@5 chỉ còn khoảng 0,02.

### 5.10.4. Đánh giá

Mô hình được đánh giá **đúng theo giao thức của chương 4**: cùng mốc chia thời gian t₁, t₂, cùng tập người dùng, cùng tập ứng viên; hệ số α được chọn trên tập validation và kết quả được báo cáo một lần trên tập test. Chạy lại item-based CF cho đúng kết quả của chương 4 (Precision@5 = 0,231023, Recall@5 = 0,035303), nên phép so sánh là công bằng. Trên validation, α = 0,9 cho Recall@5 cao nhất (0,030246) và được chọn. Kết quả trên tập test được trình bày trong Bảng 5.9 và Hình 5.10.

@table Bảng 5.9. Kết quả gợi ý trên tập test (1.154 người dùng)
@widths 9,3.5,3.5
| Mô hình | Precision@5 | Recall@5 |
| Popularity Baseline (chương 4) | 0,2017 | 0,0271 |
| Item-based CF, k = 40 (chương 4) | 0,2310 | **0,0353** |
| Chỉ nội dung (E5 + mô tả Wikipedia và IMDb) | 0,2175 | 0,0318 |
| **Lai CF + nội dung, α = 0,9** | **0,2314** | 0,0352 |
| Giả lập người dùng mới chỉ có 3 đánh giá: CF / lai | 0,1055 / 0,1059 | 0,0134 / 0,0140 |

@fig figures/nang_cap/hybrid_test.png | Hình 5.10. So sánh các mô hình gợi ý trên tập test | 15.5

Kết quả cho thấy mô hình lai **chỉ ngang với CF** về chỉ số offline (Precision@5 0,2314 so với 0,2310, Recall@5 0,0352 so với 0,0353); nhóm không coi đây là một cải thiện. Lý do là MovieLens có lịch sử rất dày (trung bình hơn 160 lượt mỗi người), nên CF đã rất mạnh. Tuy vậy, có ba kết quả đáng chú ý:

- Mô hình **chỉ dùng mô tả phim**, không dùng hành vi chấm điểm của bất kỳ ai, đạt Precision@5 = 0,2175, **vượt Popularity Baseline**. Đây là giá trị trực tiếp của các nguồn dữ liệu mới (IMDb, Wikipedia).
- Chất lượng dữ liệu và mô hình đều ảnh hưởng rõ: phần nội dung đạt Precision@5 = 0,153 với mô hình MiniLM chỉ dùng tên và thể loại, tăng lên 0,170 khi thêm mô tả Wikipedia và 0,2175 khi chuyển sang mô hình E5.
- Phần nội dung làm được những việc CF không làm được: gợi ý phim mới chưa có ai chấm, tìm phim bằng câu mô tả và giải thích lý do gợi ý (“vì bạn thích …”). Với người dùng mới chỉ có ba đánh giá, hai mô hình tương đương nhau trong phạm vi sai số.

## 5.11. Kết luận chương 5

Bản nâng cấp đã chuyển hệ thống từ một kho dữ liệu nạp tay trên một nguồn tĩnh thành một nền tảng dữ liệu nhiều nguồn, cập nhật gần thời gian thực. Bảy nguồn với bốn kiểu nạp được tích hợp qua data lake ba tầng; thay đổi trên cơ sở dữ liệu giao dịch được Debezium bắt từ WAL và đưa vào kho trong khoảng 40 giây; kho được nạp tăng dần, có SCD loại 2, xóa mềm, bốn loại bảng sự kiện và chín kiểm tra chất lượng; toàn bộ quy trình được Airflow điều phối và kiểm chứng trực quan trên ứng dụng web, dashboard tự làm mới. Ở phần khai phá, embedding đa ngôn ngữ từ mô tả Wikipedia cho phép tìm phim bằng câu tiếng Việt; mô hình lai ngang với CF trên chỉ số offline, còn mô hình chỉ dùng nội dung đã vượt mô hình cơ sở theo độ phổ biến.
