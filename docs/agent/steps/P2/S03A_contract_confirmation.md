# Báo Cáo Bước 3A-P2: Nhận Mốc G0 & Xác Nhận Hợp Đồng Dữ Liệu v2

- **Mã bước**: `P2-S03A`
- **Nhánh Git**: `p2-s03-eda` (tạo từ `main` mới nhất sau khi G0 và PR #2 được merge)
- **Thời gian thực hiện**: 2026-10-15 17:34:00 +07:00
- **Trạng thái**: `WAITING_REVIEW`

---

## 1. Mục Tiêu & Đầu Vào
- **Mục tiêu**: 
  - Tiếp nhận mốc nền G0 từ Người 1 (P1) trên nhánh `main`.
  - Kiểm tra và kích hoạt quy ước tên nhánh mới không có tiền tố `codex/` (`p2-s03-eda`).
  - Kiểm tra tệp `.gitignore` từ `main`.
  - Đối chiếu toàn diện Hợp đồng dữ liệu chung phiên bản 2 (`docs/shared/data_contract.md` và `data_contract.json`) với tài liệu chuẩn từ người dùng.
- **Đầu vào**:
  - `origin/main` commit `ff87081` (đã merge PR #1 của P1 và PR #2 của P2).
  - Nội dung Hợp đồng dữ liệu v2 từ người dùng.

---

## 2. Các Công Việc Đã Thực Hiện

1. **Ghi nhận quyết định đặt tên nhánh**:
   - Bổ sung `[DEC-P2-006]` vào `docs/agent/DECISIONS_P2.md`: Nhóm thống nhất các nhánh mới từ Bước 3 trở đi KHÔNG có tiền tố `codex/` (ví dụ `p2-s03-eda`).
2. **Đồng bộ với `origin/main`**:
   - `git fetch origin`: Ghi nhận commit `5c31e80` (G0 của P1) và merge PR #1 (`eff54ae`), merge PR #2 (`ff87081`).
   - Chuyển sang `main` và chạy `git pull --ff-only origin main` thành công, cập nhật 17 tệp mốc nền G0.
   - Tạo nhánh làm việc mới: `p2-s03-eda`.
3. **Kiểm tra `.gitignore` mốc G0**:
   - Đã xác minh tệp `.gitignore` do P1 bàn giao:
     - Đã loại trừ đầy đủ: `.env`, `.env.*`, `/data/raw/`, `/data/processed/`, `*.dat`, `*.csv`, `*.zip`, `.venv/`, `venv/`, `__pycache__/`, `.pytest_cache/`, `/results/mining/handoff/`, `**/user_cluster*`.
   - Kết luận: `.git/info/exclude` cục bộ của P2 từ nay đóng vai trò lớp bảo vệ thứ hai.
4. **Đối chiếu chi tiết Hợp đồng dữ liệu v2**:
   - Kiểm tra `docs/shared/data_contract.json`: Parse thành công bằng Python JSON parser, `contract_version == 2`.
   - Đối chiếu từng điều khoản giữa `data_contract.md`, `data_contract.json` và chỉ thị người dùng:
     - **Bốn bảng logic & thứ tự cột**:
       - `users(user_id int, gender text, age_group text, occupation int)`: Khớp 100%.
       - `movies(movie_id int, title text, release_year int nullable)`: Khớp 100%.
       - `movie_genres(movie_id int, genre_name text)`: Khớp 100%.
       - `ratings(user_id int, movie_id int, rating int, timestamp int64, rated_at UTC)`: Khớp 100%.
     - **Khóa & Grain**:
       - `users` PK `user_id`, `movies` PK `movie_id`, `movie_genres` PK `(movie_id, genre_name)`: Khớp 100%.
       - `ratings` grain là một bản ghi nguồn; khóa nghiệp vụ `(user_id, movie_id)` chỉ chốt sau khi EDA xác nhận duy nhất: Khớp 100%.
     - **Làm sạch & Chuẩn hóa**:
       - Nhãn tuổi (7 nhóm: Under 18, 18-24, 25-34, 35-44, 45-49, 50-55, 56+): Khớp 100%.
       - `gender` giữ `F/M`, `occupation` giữ mã nguồn nguyên: Khớp 100%.
       - `title` giữ nguyên chuỗi nguồn: Khớp 100%.
       - `release_year`: Lấy 4 chữ số trong ngoặc cuối tiêu đề, không khớp thì NULL: Khớp 100%.
       - Giữ tên genre nguồn, không dùng ZIP code: Khớp 100%.
     - **Định dạng nguồn & CSV chuẩn**:
       - Đọc nguồn: `Latin-1`, phân cách `::`: Khớp 100%.
       - CSV chuẩn: `UTF-8` không BOM, dấu phẩy, `LF`, có header, quote theo CSV chuẩn, NULL là ô rỗng, số nguyên không có `.0`: Khớp 100%.
       - Thứ tự sắp xếp 4 bảng: Khớp 100%.
       - Hash SHA-256 byte từng bảng, quy tắc tuần tự hóa giống nhau cho raw/csv/dw: Khớp 100%.
     - **Manifest & Gói bàn giao cụm (P2 → P1)**:
       - `data/source_manifest.json` do P2 quản lý: Khớp 100%.
       - `results/eda/canonical_manifest.json` do P2 xuất: Khớp 100%.
       - Gói cụm 3 tệp (`user_cluster.csv`, `cluster_genre_profile.csv`, `manifest.json`), ràng buộc $K \times \text{genres}$, dung sai tổng $10^{-8}$, loại `insufficient_evidence` khỏi tính trung bình: Khớp 100%.
     - **Bốn view DW của P1**:
       - `dw.v_ml_users`, `dw.v_ml_movies`, `dw.v_ml_movie_genres`, `dw.v_ml_ratings`: Khớp 100%.

---

## 3. Các Điểm P2 Cần Chốt & Lưu Ý Thêm Với P1

1. **Chuỗi ISO 8601 UTC `rated_at`**:
   - Quy định định dạng `YYYY-MM-DDTHH:MM:SSZ` (có hậu tố `Z` bắt buộc đại diện cho UTC). P2 và P1 cần đảm bảo cùng logic format này trong Python và SQL để hash SHA-256 byte bảng `ratings` khớp tuyệt đối.
2. **Thứ tự danh sách thể loại trong Manifest (`genre_order`)**:
   - Manifest gói cụm yêu cầu `genre_order`. P2 sẽ dùng thứ tự sắp xếp bảng chữ cái (alphabetical order) của 18 thể loại gốc MovieLens 1M để đảm bảo tính tái lập 100%.
3. **Chính sách khi phát hiện bản ghi trùng lặp / ngoại lai**:
   - Nếu EDA phát hiện trùng lặp khóa nghiệp vụ `(user_id, movie_id)` hoặc lỗi toàn vẹn tham chiếu, P2 sẽ dừng ngay và báo cáo để nhóm chốt chính sách xử lý chung trước khi chuẩn hóa dữ liệu.

---

## 4. Kết Luận & Đề Xuất
- Hợp đồng dữ liệu v2 đã hoàn toàn rõ ràng, chặt chẽ, không có xung đột hay mâu thuẫn giữa văn bản và JSON.
- P2 sẵn sàng xác nhận hợp đồng dữ liệu v2.
- Sau khi được người dùng duyệt Bước 3A, P2 sẽ chuyển sang Bước 3B: Tải dữ liệu nguồn GroupLens, tính SHA-256 manifest, làm sạch và xuất bộ dữ liệu chuẩn Canonical CSV.
