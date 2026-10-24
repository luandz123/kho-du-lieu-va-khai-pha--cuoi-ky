# DECISIONS_P2 - Sổ Tay Quyết Định Kiến Trúc & Kỹ Thuật (P2)

Tài liệu này ghi nhận toàn bộ các quyết định kỹ thuật, kiến trúc và phạm vi thực hiện của Người 2 (P2 - Data Mining & EDA).

---

### [DEC-P2-001] Xác định Workspace và Hệ điều hành thực tế
- **Bối cảnh**: Prompt khởi tạo ghi đường dẫn mẫu `D:\BTL_Kho_Du_Lieu` (Windows), nhưng môi trường thực tế của Người 2 là Linux Ubuntu 24.04.1 LTS x86_64 tại `<workspace-root>`.
- **Quyết định**: Sử dụng toàn bộ đường dẫn thực tế theo chuẩn POSIX trên Linux (`<workspace-root>`), cập nhật vào toàn bộ hồ sơ theo dõi cục bộ.

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

---

### [DEC-P2-012] Thiết Kế & Lựa Chọn Siêu Tham Số k Cho Item-based CF (Tiểu Bước 10A)
- **Bối cảnh**: Triển khai thuật toán Item-based Collaborative Filtering trên tập Train và lựa chọn siêu tham số láng giềng $k \in \{20, 40, 80\}$ trên cohort 471 người dùng Validation trước khi tiến hành đánh giá Test ở Bước 10B.
- **Quyết định**:
  1. **Huấn luyện độc lập trên Train:** Chỉ fit ma trận thưa Movie $\times$ User `float32` trên tập Train ($timestamp \le t_1$). Tính tương đồng Cosine theo khối (`batch_size=500`) sau khi chuẩn hóa chuẩn L2 trên từng hàng phim; triệt tiêu đường chéo ($\text{sim}(i, i) = 0.0$); chỉ giữ tương đồng dương ($\text{sim} > 0$); cắt tỉa lưu trữ tối đa 80 láng giềng dương theo thứ tự `similarity DESC, neighbor_movie_id ASC`. Tuyệt đối không dùng thông tin phân cụm Q1 hay dữ liệu Validation.
  2. **Hướng tính điểm Seed $\to$ Candidate:** Với mỗi seed $j \in \text{Seed}(u) = \{j \in \text{History}_{\text{train}}(u) \mid r_{u, j} \ge 4\}$, ứng viên $i \in \text{Candidate}(u) = \mathcal{I}_{\text{train}} \setminus \text{History}_{\text{train}}(u)$ nhận điểm nếu $i \in N_k(j)$. Phá hòa xếp hạng: `score DESC, train_popularity DESC, movie_id ASC`.
  3. **Cơ chế Fallback & Tách biệt Điểm:** Nếu ít hơn 5 ứng viên CF có điểm dương, bổ sung từ danh sách Popularity Train (đã loại trừ lịch sử và item đã chọn). Tách biệt nhãn `score_type="cf"` và `score_type="popularity_fallback"` (`score=None`).
  4. **Quy tắc chọn $k^*$ cố định:** Tiêu chí chọn $k^*$ là Macro-Recall@5 chưa làm tròn trên Validation cao nhất. Kết quả: $k=40$ đạt `0.03007556334371585` > $k=80$ (`0.02866586314500013`) > $k=20$ (`0.02856536704222439`). Chốt chọn $k^* = 40$. Giữ vững tiêu chí chọn theo quy tắc a priori, không đổi sang chọn theo Precision hay Hits dù baseline có Recall cao hơn.
  5. **Nguyên tắc diễn giải trung thực:** CF $k=40$ có Precision@5 cao hơn baseline (18.0042% vs 16.9851%, +24 hits), nhưng Recall@5 thấp hơn baseline (3.0076% vs 3.1261%). Recall@5 không phải là độ bao phủ danh mục (catalog coverage). Mọi nhận định về phim bom tấn hay ngách sở thích chỉ là giả thuyết làm việc nếu chưa có phân tích thực nghiệm riêng. Tuyệt đối không ép CF phải thắng baseline.
  6. **Bảo mật & Cục bộ:** Giữ toàn bộ gợi ý chi tiết và metric per-user ngoài Git; chỉ xuất bản kết quả tổng hợp `results/mining/cf_validation_experiments.json`.

---

### [DEC-P2-013] Đánh Giá Test Chính Thức 1 Lần, Khóa Evaluator, Truy Vết & Ràng Buộc CLI (Tiểu Bước 10B)
- **Bối cảnh**: Tiến hành đánh giá mô hình Item-based CF với siêu tham số đóng băng $k^*=40$ đối đầu Popularity Baseline trên tập Test đúng 1 lần duy nhất, xây dựng CLI gợi ý và đóng gói giao nộp theo yêu cầu của Điều phối.
- **Quyết định**:
  1. **Huấn luyện mô hình Test trên Train + Validation:** Huấn luyện trên toàn bộ tương tác trước mốc $t_2 = 976422051$ (850,177 ratings, 3,669 phim, 5,715 user). Giữ nguyên toàn bộ cấu hình đã đóng băng ($k=40$, top-5, float32, cosine L2, tie-breaking `score DESC, train_pop DESC, movie_id ASC`, fallback popularity).
  2. **Đánh giá đúng 1 lần trên Test:** Đánh giá cả hai mô hình (Baseline và CF $k=40$) trên cùng cohort 1,154 user (mã băm cohort `8cdc8ea49454e6451a0d87629a0d2b8b6ba7df5e933a7d82fee2b9075c931bb8`) và cùng không gian candidate per-user. Mẫu số Recall@5 giữ nguyên tắc tính trên toàn bộ positive test ratings (bao gồm 16 phim mới trong cohort).
  3. **Khóa Evaluator tuyệt đối (Pre-execution Lock):** Loại bỏ hoàn toàn cờ `--force`. Script `cf_test_evaluation.py` tự động từ chối và bắn `FileExistsError` ngay trước khi gọi `load_data` hoặc pipeline nếu tệp receipt HOẶC tệp output đã tồn tại. Toàn bộ kết quả và receipt gốc được bảo toàn nguyên trạng, không bị ghi đè. Kiểm thử guard bằng fixture độc lập, mock cả `load_data` và `run_cf_test_evaluation_pipeline` để chứng minh không gọi vào dữ liệu thật.
  4. **Truy vết mã nguồn Evaluator (Provenance Trace):** Bản snapshot thực thi lượt test chính thức (`eval_original.py`) có LF SHA-256 là `e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d` và Git blob SHA-1 là `d7c97bae8b6de3449c0306a2f841325f5434f248`, khớp chính xác 100% với các trường băm trong receipt. Bản công bố tại commit `24ada6d8` có LF hash `578353a8...` do cập nhật schema receipt sau khi hoàn tất chạy test lúc 03:45:02Z. Toàn bộ thay đổi thuần túy thuộc về schema xuất bản và tài liệu; 0% thay đổi thuật toán. Hồ sơ truy vết được ghi nhận độc lập tại `results/mining/evaluator_provenance_trace.json`. Giữ nguyên hash lịch sử trong receipt, không chạy lại test.
  5. **Biên lai & Checksum chống chạy đè:** Giá trị băm `receipt_sha256_checksum` là checksum kiểm tra toàn vẹn (integrity digest), không phải chữ ký số xác thực (digital signature) và không được coi là bằng chứng tuyệt đối chưa từng chạy lại.
  6. **Kết luận trung thực:** Sử dụng câu kết luận chuẩn xác: *“Trong lượt đánh giá test đã chốt, CF cao hơn baseline trên Precision@5 và Recall@5.”* (CF đạt Precision@5=0.231023, Recall@5=0.03530289, Hits=1333 vs Baseline 0.201733, 0.02712408, Hits=1164). Không suy diễn thành vượt trội tổng quát hay có ý nghĩa thống kê khi chưa kiểm định. Báo rõ tỷ lệ fallback: 2/1,154 ≈ 0.1733%.
  7. **Ràng buộc CLI với Manifest & Khảo sát:** `mining/recommend.py` ở chế độ `--mode evaluation` lấy cutoff $t_2$, định danh model `item_based_cf_k40_eval_v1`, $k=40$, input table hashes và danh mục thư viện trực tiếp từ receipt manifest. Xác minh dữ liệu nạp trước khi fit, từ chối ngay nếu sai hash bảng, sai cutoff ratings count/timestamp hoặc lệch model identity. Ghi nhận đúng bản chất tái dựng mô hình trong bộ nhớ (in-memory fit) tại runtime, thống nhất mapping model identity. Chế độ `--mode demo` có manifest/version riêng và nghiêm cấm lấy metric offline.
  8. **Bảo mật & Giữ ngoài Git:** Model binary, lịch sử chi tiết, per-user recommendations và per-user metrics giữ ngoài Git.
  9. **Công bố Snapshot Tĩnh & Khóa Manifest Mặc Định trong CLI:** Đưa snapshot thực thi evaluator gốc vào `docs/P2/provenance/eval_original.py` (32,508 bytes, LF, SHA-256 `e3fa2eff...`, Git blob `d7c97bae...`) chỉ phục vụ kiểm toán tĩnh độc lập, không thực thi. Nâng cấp CLI `mining/recommend.py` ở chế độ mặc định tự kiểm tra trước fit: trạng thái `OFFICIAL_COMPLETED`, `model_version="item_based_cf_k40_eval_v1"`, `cutoff=976422051`, `training_count=850177`, `neighbor_k=40`, `frozen recommendation_top_n=5`, và đủ 4 canonical hashes không dùng default để che trường thiếu. Mọi vi phạm đều bị từ chối trước khi dựng similarity. Mở PR bổ sung vào `main` sau khi PR #23 đã merge.

---

### [DEC-P2-014] Xác Định Môi Trường Thực Tế Bước 12-P2 Trên Máy P2 / Windows
- **Bối cảnh**: Tại các bước trước, một số tài liệu ghi nhận môi trường Linux Ubuntu (`<workspace-root>`). Hiện tại phiên làm việc thực tế của Người 2 đang vận hành trên máy P2 tại workspace `<workspace-root>`, chạy hệ điều hành Windows 11 (x86_64), dịch vụ PostgreSQL 17.4 cục bộ, độc lập hoàn toàn với máy và mạng của Người 1.
- **Quyết định**:
  1. Ghi nhận trung thực môi trường thực tế hiện tại là **Windows 11 (x86_64)** trong toàn bộ hồ sơ (`STATE_P2.md`, `DECISIONS_P2.md`).
  2. Kết luận tái lập Bước 12-P2 sẽ ghi nhận là **“Tái lập trên máy P2 / Windows”**; tuyệt đối **không ghi nhận đã xác minh trên Linux**.
  3. Bảo toàn nguyên trạng working tree, dữ liệu raw/canonical, receipt và virtual environment hiện có, không cài lại máy hay chuyển môi trường. Dừng chờ Điều phối viên cấp full merge commit SHA của PR 12A trước khi triển khai Phần B.

---

### [DEC-P2-015] Kiểm Nhận Handoff G2 Từ Kho Dữ Liệu & Tái Lập Pipeline Khai Phá (Bước 12-P2)
- **Bối cảnh**: Điều phối viên giao P2 thực hiện Phần B — Bước 12-P2 tại merge commit ứng viên cố định `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` (PR #25) trên máy P2 / Windows 11 độc lập.
- **Quyết định & Kết quả**:
  1. **Tách biệt Checkout & Môi trường**: Tạo checkout tại `tmp/checkout_12a` tại đúng candidate SHA. Khởi tạo virtual environment sạch `tmp/venv_12a` với Python 3.12.6, cài đặt nguyên gốc `requirements.txt` (`No broken requirements found.`). Toàn bộ working tree và hồ sơ của P2 tại nhánh `main` được bảo toàn nguyên vẹn.
  2. **Tái tạo CSDL DW-Only**: Chạy `etl/recreate_integration_dw.py` ở chế độ plan đạt, sau đó apply tạo CSDL `movielens_btl_int_20261023_e7b2219c` (Run ID `e7b2219c75e847e38005de5d0e2509a9`) trên PostgreSQL 17.4 cục bộ của P2. Toàn bộ 1,000,209 ratings, 6,040 users, 3,883 movies, 6,408 genres được nạp thành công với transaction `COMMITTED`.
  3. **Kiểm nhận Mốc G2 & Tương đương 3 chiều**: Sử dụng adapter `load_dw_data()` nạp 4 view hợp đồng (`dw.v_ml_*`). Kết quả đối chiếu với RAW và CSV: 100% khớp schema, kiểu dữ liệu, thứ tự cột, định dạng ISO-8601 UTC và mã băm SHA-256 canonical. Chính thức xác nhận: **`P2 intake G2 = CONFIRMED`**.
  4. **Tái lập Pipeline Khai phá từ DW**:
     - Q1 Feature Extraction: Tạo ma trận $(6038, 18)$ và phân cụm K-Means ($K=4$, seed 42) xuất vào thư mục riêng `tmp/g3_reproduced_dw` ngoài Git. Cả hai tệp `user_cluster.csv` và `cluster_genre_profile.csv` khớp 100% từng byte mã băm SHA-256 với fingerprint đóng băng (`5812d961...` và `59f9237e...`).
     - CLI Recommender: Chạy 3 ca kiểm thử từ DW gồm evaluation có seed, evaluation fallback và demo. Đảm bảo Top-5 duy nhất, không trùng lặp, loại bỏ lịch sử, tách biệt điểm CF và fallback. Tệp kết quả lưu cục bộ tại `tmp/` ngoài Git.
  5. **Bảo toàn Đánh giá Test Chính thức**: Tuyệt đối không chạy evaluator test trên dữ liệu thật, không điều chỉnh $k$. 31/31 unit test CF, guard và recommender đạt PASS 100% trên môi trường mới.
  6. **Bàn giao & Giới hạn**: Lập báo cáo đầy đủ tại `docs/P2/integration_report.md` và `docs/agent/steps/P2/S12.md`. Giữ nguyên tắc không đưa credential, dữ liệu người dùng hay binary model lên Git. Trạng thái trước công bố là `12-P2 WAITING_REVIEW`; hiện G2 đã được điều phối chấp nhận, PR #28 đã merge tại `88c5c7b952553523f58e82ed6546179451eb6b65`; G4 chưa chốt.





Hồ sơ môi trường Bước 12-P2 công bố: [environment.json](../../results/mining/integration_p2/environment.json). `<workspace-root>` là đường dẫn do người chạy chọn; chi tiết đường dẫn cá nhân giữ cục bộ ngoài Git.


### [DEC-P2-016] Bản thảo báo cáo 13-P2 sau nghiệm thu G4

- Ngày 24/10/2026, điều phối qua người dùng nghiệm thu 12B/G4 trong phạm vi đã kiểm và giao chương 2/5/6 theo report_outline. Tách lời duyệt khỏi PR30 MERGED tại `67fd9eb6b98211485b713c99e829291bc3b50f57`; candidate thực kiểm vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`.
- Bảo toàn workspace đang có untracked P1; fetch main rồi tạo worktree riêng/nhánh `codex/p2-s13-report` từ origin/main, không reset/stash hoặc chuyển nhánh checkout P1 đang dùng.
- Chương 2 giải thích phương pháp/công thức với fixture giả; chương 5 dùng summary/receipt đã chốt và trình bày cả Recall validation CF thấp hơn baseline; chương 6 kết luận có giới hạn. Không chạy lại pipeline/evaluator/test hoặc thay receipt.
- Dùng bảng profile/nhân khẩu học để tránh nhãn ảnh khó đọc; hai ảnh chính có caption về đơn vị/mẫu số. PCA dẫn nhãn ảnh 35,5%+24,9%, công khai khác số diễn giải cũ; không sửa ảnh nguồn. CSV thử nghiệm không có trong Git, lấy 14 dòng experiments_summary đã công bố. Không tái tính dữ liệu cá nhân.
- Giữ phần P1 nguyên trạng, đánh dấu trạng thái cũ cần cập nhật lúc ghép. Bản thảo 13-P2 WAITING_REVIEW; chưa commit/push/PR, chưa DOCX tổng/G5.


### [DEC-P2-017] Chỉnh biên tập và công bố phần báo cáo P2

Ngày 24/10/2026, điều phối chấp nhận nội dung chính và cho phép commit/push/mở PR phần P2, thay chỉ thị dừng ở bản thảo trước. Tạm loại PCA/các tỷ lệ phương sai khỏi bản chính để không chọn giữa hai nguồn mâu thuẫn chưa xác minh; ghi đầy đủ ở editorial_notes.md, giữ ảnh gốc. Chuyển quản lý review/PR/ghép sang hồ sơ, sửa nhãn cohort và bỏ ưu thế biểu diễn chưa có đối chứng. Không đổi công thức/bảng số liệu/receipt/nguồn, không chạy mô hình/evaluator, không sửa P1. Giữ G4 đạt đúng phạm vi, G5 chưa hoàn thành; PR chờ review, không tự merge.
