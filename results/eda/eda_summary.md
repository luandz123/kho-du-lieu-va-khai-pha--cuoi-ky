# Báo Cáo Khảo Sát & Phân Tích Dữ Liệu Khám Phá (EDA) - Canonical v2

- **Bộ dữ liệu**: MovieLens 1M (GroupLens)
- **Hợp đồng dữ liệu**: Phiên bản 2 (`docs/shared/data_contract.md` & `.json`)
- **Thời điểm trích xuất**: 2000-04-25T23:05:32Z đến 2003-02-28T17:49:50Z
- **Trạng thái làm sạch**: **100% SẠCH & KHỚP HỢP ĐỒNG** (Không có lỗi hoặc dị biệt cần chính sách làm sạch đặc thù)

---

## 1. Kết Quả Kiểm Tra Tính Toàn Vẹn & Khóa Nghiệp Vụ

| Bảng logic | Số dòng | Khóa chính / Khóa nghiệp vụ | Tính duy nhất | Ràng buộc khóa ngoại |
| :--- | :---: | :--- | :---: | :---: |
| **users** | 6,040 | `user_id` (int) | **100% Unique** | Không có |
| **movies** | 3,883 | `movie_id` (int) | **100% Unique** | Không có |
| **movie_genres** | 6,408 | `(movie_id, genre_name)` | **100% Unique** | 100% `movie_id` tồn tại trong `movies` |
| **ratings** | 1,000,209 | `(user_id, movie_id)` | **100% Unique (0 bản ghi trùng)** | 100% `user_id` và `movie_id` tồn tại |

> **Xác nhận quan trọng**: Trong toàn bộ 1,000,209 bản ghi đánh giá nguồn, **KHÔNG CÓ BẤT KỲ CẶP (user_id, movie_id) NÀO BỊ TRÙNG LẶP**. Khóa nghiệp vụ `(user_id, movie_id)` chính thức được xác nhận là duy nhất, đủ điều kiện để Người 1 (P1) tạo ràng buộc `UNIQUE (user_id, movie_id)` trong DW.

---

## 2. Thống Kê Đặc Trưng Các Bảng

### Bảng Users (6,040 người dùng)
- **Giới tính**: Nam: 4,331 (71.71%), Nữ: 1,709 (28.29%).
- **Cơ cấu 7 nhóm tuổi chuẩn hóa**:
  - `Under 18`: 222 (3.68%)
  - `18-24`: 1,103 (18.26%)
  - `25-34`: 2,096 (34.70%) — *Nhóm chiếm tỷ trọng cao nhất*
  - `35-44`: 1,193 (19.75%)
  - `45-49`: 550 (9.11%)
  - `50-55`: 496 (8.21%)
  - `56+`: 380 (6.29%)
- **Nghề nghiệp**: 21 mã số nguồn (0..20) được giữ nguyên.
- **Mã ZIP**: Đã loại bỏ hoàn toàn theo hợp đồng.

### Bảng Movies & Movie Genres (3,883 phim, 6,408 liên kết thể loại)
- **Năm phát hành (`release_year`)**: 100% phim khớp mẫu 4 chữ số trong ngoặc ở cuối tiêu đề. Năm phát hành từ 1919 đến 2000.
- **18 Thể loại gốc** (sắp xếp theo DEC-P2-007):
  `Action` (503), `Adventure` (283), `Animation` (105), `Children's` (251), `Comedy` (1,200), `Crime` (211), `Documentary` (127), `Drama` (1,603), `Fantasy` (68), `Film-Noir` (44), `Horror` (343), `Musical` (114), `Mystery` (106), `Romance` (471), `Sci-Fi` (276), `Thriller` (492), `War` (143), `Western` (68).

### Bảng Ratings (1,000,209 lượt đánh giá)
- **Điểm đánh giá**: 100% nằm trong khoảng nguyên 1..5.
  - 1 sao: 56,174 (5.62%)
  - 2 sao: 107,557 (10.75%)
  - 3 sao: 261,197 (26.11%)
  - 4 sao: 348,971 (34.89%) — *Phổ biến nhất*
  - 5 sao: 226,310 (22.63%)
  - **Điểm trung bình toàn hệ thống**: **3.5816**
- **Khoảng thời gian (`rated_at`)**: Từ `2000-04-25T23:05:32Z` đến `2003-02-28T17:49:50Z` (gần 3 năm).

---

## 3. Mã Băm SHA-256 Bộ Dữ Liệu Chuẩn (Canonical CSV)

| Bảng chuẩn | Đường dẫn tệp | Số dòng (kể cả header) | SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| **users** | `data/processed/users.csv` | 6,041 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| **movies** | `data/processed/movies.csv` | 3,884 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| **movie_genres** | `data/processed/movie_genres.csv` | 6,409 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| **ratings** | `data/processed/ratings.csv` | 1,000,210 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |
