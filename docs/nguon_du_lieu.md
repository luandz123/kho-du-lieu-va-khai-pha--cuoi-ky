# Nguồn dữ liệu cho bản nâng cấp

Kiểm tra thực tế ngày 17/11/2026 từ mạng nhà (Việt Nam).

## Tổng hợp

| # | Nguồn | Loại | Tần suất cập nhật | Cần key | Truy cập từ VN | Vai trò |
|---|---|---|---|---|---|---|
| 1 | **MovieLens 1M** (đang dùng) | File CSV/DAT | Tĩnh (2000–2003) | Không | OK | Lịch sử rating để huấn luyện gợi ý |
| 2 | **IMDb Non-Commercial Datasets** | File TSV.gz | **Hằng ngày** | Không | OK | Điểm và số lượt vote IMDb, đạo diễn, diễn viên, thời lượng |
| 3 | **Wikimedia Pageviews API** | REST API (JSON) | **Theo giờ** | Không | OK | Mức độ quan tâm tới từng phim (lượt xem trang Wikipedia) |
| 4 | **Wikimedia EventStreams** | Luồng SSE **thời gian thực** | Liên tục (vài chục sự kiện/giây) | Không | OK | Luồng streaming thật để đẩy vào Kafka |
| 5 | **Wikidata SPARQL** | API truy vấn | Liên tục | Không | OK | Bảng ánh xạ IMDb ID ↔ bài Wikipedia, quốc gia, giải thưởng |
| 6 | **App xem phim tự dựng** (Postgres) | Database giao dịch | Thời gian thực | Không | Chạy trên máy | Nguồn cho **CDC** (Debezium) |
| 7 | TMDB API | REST API | Liên tục | Có (miễn phí) | **Bị chặn**, cần VPN/đổi DNS | Poster, mô tả phim. Không bắt buộc |
| 8 | Trakt API | REST API | Thời gian thực ("đang xem") | Có (miễn phí) | Chưa thử với key | Số người đang xem. Không bắt buộc |
| 9 | OMDb API | REST API | — | Có (1.000 lượt/ngày) | OK | Dự phòng cho poster và tóm tắt phim |

**Đề xuất dùng: 1 + 2 + 3 + 4 + 5 + 6.** Cả 6 nguồn đều không cần đăng ký và đều tải được. TMDB và Trakt chỉ thêm nếu có thời gian.

## Chi tiết

### 2. IMDb Non-Commercial Datasets

- Trang: <https://data.imdb.com/non-commercial-datasets/>, file tại `https://datasets.imdbws.com/`.
- Giấy phép: chỉ cho mục đích cá nhân, phi thương mại. Bài tập lớn thuộc diện này.
- Bản mới nhất lúc kiểm tra cập nhật ngày 16/11/2026.

| File | Dung lượng (nén) | Cột chính | Dùng để |
|---|---|---|---|
| `title.ratings.tsv.gz` | 8,8 MB | tconst, averageRating, numVotes | **Chụp hằng ngày** → fact snapshot (xu hướng vote theo ngày) |
| `title.basics.tsv.gz` | 230 MB | tconst, titleType, primaryTitle, startYear, runtimeMinutes, genres | Thời lượng, thể loại IMDb |
| `title.crew.tsv.gz` | 84 MB | tconst, directors, writers | Đạo diễn, biên kịch |
| `title.principals.tsv.gz` | 791 MB | tconst, nconst, category, characters | Diễn viên chính |
| `name.basics.tsv.gz` | 313 MB | nconst, primaryName, birthYear, primaryProfession | Tên người |
| `title.akas.tsv.gz` | 523 MB | titleId, title, region, language | Tên phim tiếng Việt (region = VN) |

- Giá trị rỗng ghi là `\N`.
- **Ổ C: chỉ còn 6,5 GB**, phải lưu các file này ở ổ D:. Chỉ giữ lại những dòng thuộc phim có trong MovieLens ngay ở tầng silver.
- Ý tưởng "real time": IMDb chỉ cập nhật theo ngày. Chạy DAG mỗi sáng tải `title.ratings` mới, so với hôm trước → bảng `fact_imdb_rating_daily`. Thấy được phim nào đang tăng vote nhanh.

### Ghép MovieLens với IMDb

- MovieLens có file `links.csv` (movieId → imdbId → tmdbId). ML-1M không kèm file này, nhưng movieId giữ nguyên giữa các phiên bản MovieLens.
- Đã thử với bộ `ml-latest-small` (1 MB): khớp **2.949 / 3.883 phim (76%)**.
- Muốn khớp gần 100% thì dùng `links.csv` trong bộ `ml-32m` (file zip khoảng 240 MB, chỉ lấy `links.csv`).
- Khóa nối: `imdbId` của MovieLens (dạng số `0114709`) = `tconst` của IMDb (dạng `tt0114709`).

### 3. Wikimedia Pageviews API

- Endpoint:
  `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{Tên_bài}/{daily|hourly}/{từ}/{đến}`
- Không cần key, chỉ cần gửi header `User-Agent` có tên dự án.
- Đã thử: bài "Inception" có khoảng 4.300–4.600 lượt xem/ngày trong tuần 10–16/11/2026.
- Dùng làm chỉ số "độ hot hiện tại" của phim → bảng `fact_movie_pageviews` (grain: phim × giờ hoặc phim × ngày).
- Kết hợp với IMDb: phim cũ nhưng lượt xem Wikipedia tăng đột biến (vì có phần mới, diễn viên mất, lên Netflix...) → đưa vào gợi ý "đang được quan tâm".

### 4. Wikimedia EventStreams (thời gian thực thật sự)

- Endpoint: `https://stream.wikimedia.org/v2/stream/recentchange` (Server-Sent Events, hoặc JSON từng dòng nếu gửi `Accept: application/json`).
- Không cần key. Wikimedia khuyên chỉ dùng ở quy mô nhỏ, phù hợp bài tập.
- Đã thử: nhận được sự kiện ngay trong 1 giây.
- Cách dùng: producer Python đọc luồng → lọc các chỉnh sửa trên bài Wikipedia của phim có trong kho (dựa vào bảng ánh xạ ở nguồn 5) → đẩy vào topic Kafka `wiki.movie_edits` → consumer ghi vào bronze.
- Khi demo: mở Kafka UI thấy message chảy liên tục. Đây là luồng streaming thật, khác với CDC ở nguồn 6.

### 5. Wikidata SPARQL

- Endpoint: `https://query.wikidata.org/sparql`, không cần key, đã thử truy cập được.
- Một câu truy vấn lấy được toàn bộ phim có IMDb ID (thuộc tính `P345`) kèm tên bài Wikipedia tiếng Anh, có thể lấy thêm quốc gia, giải Oscar, kinh phí.
- Đây là "cầu nối" để biết phim MovieLens nào ứng với bài Wikipedia nào (cần cho nguồn 3 và 4).

### 6. App xem phim tự dựng + CDC

- Postgres riêng, schema `app` (users, movies, ratings, watch_history).
- Người dùng chấm điểm trên app Streamlit, script giả lập sinh thêm rating.
- Debezium đọc WAL → Kafka topic `app.public.ratings` → bronze.

### 7–9. Nguồn không bắt buộc

- **TMDB:** `api.themoviedb.org` và `www.themoviedb.org` bị reset kết nối từ mạng hiện tại (nhiều nhà mạng ở VN chặn TMDB). Riêng file export hằng ngày ở `files.tmdb.org` vẫn tải được, nhưng file này chỉ có ID và độ phổ biến. Muốn dùng API phải bật VPN hoặc đổi DNS (ví dụ 1.1.1.1) và đăng ký key.
- **Trakt:** API trả 403 khi không có key. Đăng ký app miễn phí tại trakt.tv để lấy Client ID; endpoint `/movies/trending` trả số người đang xem.
- **OMDb:** cần key miễn phí (1.000 lượt/ngày), trả poster và tóm tắt theo IMDb ID. Dùng thay TMDB để có poster cho app nếu không vượt được chặn.

## Bức tranh 3 kiểu nạp dữ liệu

| Kiểu | Nguồn | Công cụ |
|---|---|---|
| **Batch** (theo ngày) | MovieLens, IMDb datasets, Wikidata | Airflow → MinIO bronze |
| **Micro-batch** (theo giờ) | Wikimedia Pageviews | Airflow mỗi giờ → MinIO bronze |
| **Streaming / thời gian thực** | Wikimedia EventStreams, App (CDC) | Kafka → consumer → MinIO bronze |

Bài có đủ cả batch, micro-batch lẫn streaming, và có CDC thật. Đây đúng là những gì thầy chê thiếu ở bản cũ.
