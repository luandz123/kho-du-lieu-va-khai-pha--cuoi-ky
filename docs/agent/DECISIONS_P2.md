# DECISIONS_P2 - Sổ Tay Quyết Định Kiến Trúc & Kỹ Thuật (P2)

Tài liệu này ghi nhận toàn bộ các quyết định kỹ thuật, kiến trúc và phạm vi thực hiện của Người 2 (P2 - Data Mining & EDA).

---

### [DEC-P2-001] Xác định Workspace và Hệ điều hành thực tế
- **Bối cảnh**: Prompt khởi tạo ghi đường dẫn mẫu `D:\BTL_Kho_Du_Lieu` (Windows), nhưng môi trường thực tế của Người 2 là Linux Ubuntu 24.04.1 LTS x86_64 tại `/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`.
- **Quyết định**: Sử dụng toàn bộ đường dẫn thực tế theo chuẩn POSIX trên Linux (`/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`), cập nhật vào toàn bộ hồ sơ theo dõi cục bộ.

---

### [DEC-P2-002] Cơ chế loại trừ tệp cục bộ trước khi P1 bàn giao `.gitignore`
- **Bối cảnh**: Tệp `.gitignore` do P1 sở hữu và sẽ được bàn giao ở mốc G0. Tuy nhiên P2 cần tạo môi trường ảo `.venv` và lưu trữ `data/` mà không vô tình đưa vào commit của P2.
- **Quyết định**: Sử dụng `.git/info/exclude` để cấu hình bỏ qua cục bộ `.venv/`, `data/raw/`, `data/processed/`, `.env`, `__pycache__/`, `.pytest_cache/`. Điều này tuân thủ 100% nguyên tắc không sửa chéo file của P1 mà vẫn đảm bảo working tree sạch.

---

### [DEC-P2-003] Cô lập thư viện P2 trong `docs/P2/requirements-p2.txt`
- **Bối cảnh**: `requirements.txt` gốc do P1 sở hữu và sẽ chỉ được hợp nhất ở Bước 12A.
- **Quyết định**: P2 chỉ định nghĩa các thư viện phục vụ EDA, phân cụm K-Means, Item-based CF và kiểm thử trong `docs/P2/requirements-p2.txt`.

---

### [DEC-P2-004] Lựa chọn Stack thư viện khoa học dữ liệu
- **Bối cảnh**: Cần các thư viện đã kiểm chứng, tương thích tối đa với Python 3.12 trên Ubuntu 24.04:
  - `numpy>=1.26.4,<2.1.0`
  - `pandas>=2.2.2,<3.0.0`
  - `scipy>=1.13.0,<1.15.0`
  - `scikit-learn>=1.4.2,<1.6.0`
  - `pytest>=8.1.1,<9.0.0`
  - `requests>=2.31.0,<3.0.0`
- **Quyết định**: Chốt các dải phiên bản trên để đảm bảo tính tái lập (reproducibility), không dùng các phiên bản chưa ổn định.

---

### [DEC-P2-005] Xử lý sự cố dung lượng đĩa khả dụng
- **Bối cảnh**: Dung lượng đĩa khả dụng ban đầu chỉ có ~771MB do 33GB tệp đã xóa bị giữ trong `~/.local/share/Trash`.
- **Quyết định**: Được người dùng phê duyệt trực tiếp qua câu hỏi tương tác, tiến hành làm rỗng Thùng rác để giải phóng 33GB thực tế, nâng dung lượng trống lên ~34GB, loại bỏ hoàn toàn rủi ro thiếu đĩa.

---

### [DEC-P2-006] Quy ước đặt tên nhánh Git mới không có tiền tố `codex/`
- **Bối cảnh**: Ban đầu tài liệu hướng dẫn mẫu có dùng ví dụ nhánh dạng `codex/p2-s08-clusters` hoặc `codex/p2-s02-env`. Nhóm đã họp và chốt quy ước thống nhất cho toàn bộ các mốc từ Bước 3 trở đi: tên nhánh mới KHÔNG có tiền tố `codex/` (ví dụ `p2-s03-eda`).
- **Quyết định**: Áp dụng quy ước tên nhánh mới không tiền tố `codex/` (cụ thể nhánh Bước 3 là `p2-s03-eda`) cho toàn bộ công việc của P2, đảm bảo tính đồng bộ với Người 1 và kho mã nguồn chung.

---

### [DEC-P2-007] Thứ tự thể loại `genre_order` theo bảng chữ cái A–Z
- **Bối cảnh**: Hợp đồng dữ liệu v2 quy định gói handoff phân cụm (`cluster_genre_profile.csv` và `manifest.json`) phải chứa danh mục thể loại và `genre_order` thống nhất, xuất đủ $K \times \text{genres}$ dòng gồm cả tỷ lệ 0.
- **Quyết định**: Cố định thứ tự thể loại (`genre_order`) theo thứ tự bảng chữ cái tiếng Anh (alphabetical order A–Z) của 18 thể loại gốc trong MovieLens 1M: `Action`, `Adventure`, `Animation`, `Children's`, `Comedy`, `Crime`, `Documentary`, `Drama`, `Fantasy`, `Film-Noir`, `Horror`, `Musical`, `Mystery`, `Romance`, `Sci-Fi`, `Thriller`, `War`, `Western`. Thứ tự này được áp dụng xuyên suốt trong trích xuất đặc trưng vector, ma trận hồ sơ thể loại và manifest.

---

### [DEC-P2-008] Xác thực toàn vẹn DataFrame trong bộ nhớ và đóng băng fingerprint G3
- **Bối cảnh**: Điều phối viên phát hiện kẽ hở: nếu sửa dữ liệu trong bộ nhớ sau khi loader nạp, CLI vẫn xuất gói mang hash tệp nguồn cũ trên đĩa mà không phát hiện sự sai lệch. Đồng thời cần bảo đảm tính bất biến của `model_version="kmeans_k4_seed42"`.
- **Quyết định**: 
  1. Ngay sau khi `load_data`, gọi `verify_and_hash_input_tables` để serialize và băm SHA-256 chính 4 DataFrame trong bộ nhớ theo chuẩn Data Contract v2. Bất kỳ sai lệch nào so với `canonical_manifest.json` sẽ ném `InputDataIntegrityError` và CLI lập tức thoát với exit code khác 0 mà không ghi đè gói.
  2. Truyền trực tiếp `canonical_hashes` đã kiểm vào hàm xuất `export_g3_handoff_package` và ghi vào `manifest["canonical_hashes"]` chuẩn hợp đồng.
  3. Đóng băng chặt chẽ `model_version="kmeans_k4_seed42"` với fingerprint chốt ($K=4$, raw, seed=42, n_init=10, 4 hash canonical và 2 hash CSV). Nghiêm cấm tái sử dụng version cho dữ liệu hoặc cấu hình khác.
  4. Đọc phiên bản `scikit-learn` động từ môi trường runtime thay vì ghi cứng.
  5. Bỏ mọi assertion ép cứng ngưỡng ARI trong unit tests, chỉ kiểm tính hợp lệ toán học $[-1.0, 1.0]$ và self-comparison bằng 1.0.

---

### [DEC-P2-009] Xuất bản nguyên tử theo từng tệp (Per-file Atomic Publication) và bảo toàn gói G3
- **Bối cảnh**: Điều phối viên phát hiện lỗi thứ tự trong `export_g3_handoff_package`: hai tệp CSV ban đầu bị ghi trực tiếp vào thư mục đích trước khi kiểm tra hash đóng băng, khiến việc xuất với nhãn hoán vị làm hỏng hai CSV đích dù hàm báo `ValueError`. Đồng thời, ba lệnh `os.replace` nối tiếp chỉ đảm bảo tính nguyên tử ở cấp độ từng tệp riêng biệt trên filesystem POSIX chứ không phải giao dịch nguyên tử liên tệp (multi-file atomic transaction).
- **Quyết định & Cam kết kỹ thuật**:
  1. **Bảo toàn khi validation thất bại:** Toàn bộ DataFrame, chuỗi byte CSV, mã băm SHA-256 và cấu trúc `manifest` được dựng và kiểm tra 100% trong bộ nhớ trước khi sửa bất kỳ tệp nào của gói đích. Nếu kiểm tra thất bại ở giai đoạn này, gói cũ trên đĩa giữ nguyên 100% từng byte, và thư mục chưa tồn tại không để lại bất kỳ tệp dở dang nào.
  2. **Nguyên tử từng tệp qua Staging:** Sau khi kiểm tra đạt, tệp được ghi vào thư mục staging tạm thời (`tempfile.TemporaryDirectory`) rồi thay thế nguyên tử từng tệp (`os.replace`).
  3. **Giới hạn I/O và sự cố giữa chừng:** Do ba lệnh `os.replace` diễn ra tuần tự, nếu có lỗi I/O hoặc gián đoạn tiến trình giữa các lần replace (ví dụ replace thành công CSV nhưng chưa kịp replace manifest), thư mục đích có thể rơi vào trạng thái không nhất quán. Hệ thống không có cơ chế tự động rollback liên tệp.
  4. **Quy định đối với bên nhận (Downstream Receiver / Person 1 / Analytics):** Bên nhận bắt buộc phải kiểm tra sự tồn tại của `manifest.json` và xác thực đủ cả hai mã băm SHA-256 của `user_cluster.csv` và `cluster_genre_profile.csv` trước khi nạp vào analytics/kho dữ liệu. Nếu phát hiện gói hỏng hoặc checksum không khớp, phải dừng quy trình và tái tạo sang thư mục mới hoàn toàn, đồng thời giữ nguyên thư mục lỗi để kiểm toán.
  5. **Chống tái sử dụng gói không nhất quán:** Nếu một gói bị hỏng dở dang do lỗi I/O, lần xuất tiếp theo vào thư mục đó sẽ bị cơ chế pre-flight integrity check từ chối ngay lập tức (báo checksum mismatch / corrupted package), tuyệt đối không âm thầm tiếp tục sử dụng hay ghi đè.
  6. **Phạm vi kỹ thuật:** Chưa cần mở rộng sang cơ chế giao dịch filesystem đa tệp phức tạp hoặc chịu mất điện đột ngột.

---

### [DEC-P2-010] Khế ước Phép chia Thời gian và Giao thức Đánh giá Q2 (Tiểu bước 9A)
- **Bối cảnh**: Dự án yêu cầu phân vùng thời gian toàn cục theo tỷ lệ 70% Train / 15% Validation / 15% Test để tránh rò rỉ dữ liệu tương lai (temporal data leakage). Đồng thời cần xác lập giao thức đánh giá offline cho bài toán Q2 Recommendation.
- **Quyết định**:
  1. Sử dụng phương pháp quantile tuyến tính trên mốc timestamp toàn cục để xác định $t_1 = 974862386$ (`2000-11-22T03:06:26Z`) và $t_2 = 976422051$ (`2000-12-10T04:20:51Z`).
  2. Quy tắc hòa mốc (tie-breaking): toàn bộ rating có `timestamp == t1` thuộc về Train (700,148 ratings, 70.0002%); `timestamp == t2` thuộc về Validation (150,029 ratings, 14.9998%); và `timestamp > t2` thuộc về Test (150,032 ratings, 15.0001%).
  3. Cohort đánh giá Validation: Lọc đúng các user có $\ge 5$ ratings trong Train và có ít nhất 1 rating $\ge 4$ trong kỳ Validation $\to$ xác định chính xác 471 user đủ điều kiện (eligible cohort), mã băm SHA-256 là `ba0f9648c46999712f4339a81f0b6c0cb45b4bd3bc5ad1184d8885e580fd101f`.
  4. Mẫu số Recall@5: Tính trên toàn bộ số phim relevant ($rating \ge 4$) của người dùng trong kỳ đánh giá, bao gồm cả các phim mới (novel items) chưa từng xuất hiện trong tập Train.
  5. Đóng băng khế ước tại `results/mining/split_manifest.json`.

---

### [DEC-P2-011] Giao thức Triển khai & Đánh giá Popularity Baseline (Tiểu bước 9B)
- **Bối cảnh**: Cần một mô hình cơ sở (baseline) phi cá nhân hóa vững chắc để làm mốc quy chiếu cho thuật toán Item-based Collaborative Filtering ở Bước 10.
- **Quyết định**:
  1. **Huấn luyện:** Đếm toàn bộ số lượt rating (1–5 sao) trên tập Train ($timestamp \le t_1$) theo `movie_id`. Sắp xếp xác định: `rating_count DESC, movie_id ASC`. Tuyệt đối không sử dụng dữ liệu từ Validation hay Test, không áp dụng negative sampling.
  2. **Candidate Universe theo từng user:** $\text{Candidate}(u) = \mathcal{I}_{\text{train}} \setminus \text{History}_{\text{train}}(u)$. Số lượng candidate không cố định mà dao động từ 2,193 đến 3,628 phim trên cohort 471 user.
  3. **Gợi ý Top-5:** Loại bỏ toàn bộ phim người dùng đã đánh giá trong kỳ Train, lấy tối đa 5 phim đứng đầu danh sách thịnh hành còn lại của candidate universe. Danh sách gợi ý của từng user có thể khác nhau do sự khác biệt về lịch sử đã loại trừ.
  4. **Kết quả Macro:** Đo đạc trên 471 user cohort validation đạt **Macro-Precision@5 = 16.9851%** và **Macro-Recall@5 = 3.1261%** (tổng 400 hits).
  5. **Nguyên tắc diễn giải kỹ thuật:** Precision phản ánh tỷ lệ relevant trong Top 5 theo giao thức ngoại tuyến, không tương đương với xác suất người dùng ngẫu nhiên xem phim. Recall thấp là tổ hợp đa nhân tố (giới hạn Top 5, kích thước tập relevant lớn, tính chất đại chúng). Không kết luận mô hình CF tốt hơn baseline trước khi có kết quả thực nghiệm.
  6. **Bảo mật & Cục bộ:** Giữ toàn bộ gợi ý chi tiết và metric per-user ngoài Git; chỉ xuất bản kết quả tổng hợp `results/mining/baseline_popularity_validation.json`.
