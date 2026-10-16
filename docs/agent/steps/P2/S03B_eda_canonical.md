# Báo Cáo Bước 3B-P2: Tải Nguồn, Source Manifest & Khảo Sát EDA Canonical

- **Mã bước**: `P2-S03B`
- **Nhánh Git**: `p2-s03-eda`
- **Thời gian thực hiện**: 2026-10-15 17:42:00 +07:00
- **Trạng thái**: `WAITING_REVIEW`

---

## 1. Mục Tiêu & Đầu Vào
- **Mục tiêu**:
  - Tải tập dữ liệu gốc MovieLens 1M từ GroupLens vào `data/raw/` (không commit).
  - Tính toán SHA-256 byte và đếm số dòng từng tệp nguồn, tạo `data/source_manifest.json` do P2 sở hữu.
  - Thực hiện EDA toàn diện theo Hợp đồng dữ liệu v2: kiểm tra tính duy nhất của ID `users`, `movies`, cặp `(movie_id, genre_name)`, cặp nghiệp vụ `(user_id, movie_id)`, kiểm tra miền giá trị rating 1..5, khóa tham chiếu, trích xuất `release_year`, ánh xạ `age_group`, định dạng `rated_at` theo UTC ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`).
  - Nếu phát hiện trùng hoặc lỗi nguồn: dừng ngay báo cáo. Nếu dữ liệu sạch: chuẩn hóa và xuất 4 bảng canonical CSV vào `data/processed/`, tính SHA-256 byte và tạo `results/eda/canonical_manifest.json`.
- **Đầu vào**:
  - Quyết định phê duyệt Bước 3A-P2 và xác nhận Hợp đồng dữ liệu v2 từ người dùng (lưu tại `REVIEWS_P2.md`).
  - Tệp lưu trữ MovieLens 1M tại `https://files.grouplens.org/datasets/movielens/ml-1m.zip`.

---

## 2. Các Công Việc Đã Thực Hiện

### A. Tải nguồn & Khởi tạo `data/source_manifest.json`
- Đã tải tệp `ml-1m.zip` (5,917,549 bytes) từ GroupLens và giải nén vào `data/raw/ml-1m/`.
- Tính mã băm SHA-256 và đếm số dòng vật lý:
  - `users.dat`: 6,040 dòng, SHA-256: `1dc3a95300cb19f7c10e027daf29b8cdf1d908dab65b5edfb45950aa389a10a3`
  - `movies.dat`: 3,883 dòng, SHA-256: `0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9`
  - `ratings.dat`: 1,000,209 dòng, SHA-256: `506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f`
  - `README`: 170 dòng, SHA-256: `2d5ddce86ccbd247207456165827b4b9ddf27282bca93807d4c763e28414f133`
- Tạo tệp `data/source_manifest.json` đầy đủ metadata theo đúng hợp đồng.

### B. Kết quả khảo sát EDA theo Hợp đồng v2
1. **Bảng Users**:
   - 6,040 bản ghi, toàn bộ `user_id` là duy nhất.
   - `gender`: 4,331 Nam ('M') và 1,709 Nữ ('F').
   - `age`: 100% thuộc 7 nhóm tuổi quy định, đã ánh xạ thành công sang `age_group` (nhóm đông nhất là 25-34 với 2,096 người).
   - `occupation`: 21 mã nguồn nguyên thủy (0..20) giữ nguyên.
   - Mã bưu điện (Zip-code) đã được loại bỏ hoàn toàn.
2. **Bảng Movies & Movie Genres**:
   - 3,883 phim, toàn bộ `movie_id` là duy nhất.
   - `release_year`: 100% tiêu đề phim khớp nhóm 4 chữ số trong ngoặc ở cuối chuỗi (`YEAR_PATTERN = re.compile(r"\((\d{4})\)$")`). Không có phim nào bị thiếu năm hoặc sai mẫu (năm phát hành từ 1919 đến 2000).
   - `movie_genres`: 6,408 cặp `(movie_id, genre_name)`, 100% duy nhất, bao gồm đúng 18 thể loại gốc.
3. **Bảng Ratings**:
   - 1,000,209 lượt đánh giá.
   - **Xác nhận tính duy nhất của khóa nghiệp vụ**: **0 bản ghi trùng lặp cặp `(user_id, movie_id)`**. Mỗi người dùng đánh giá mỗi bộ phim tối đa 1 lần trong tập dữ liệu.
   - **Miền giá trị**: 100% ratings nằm trong khoảng nguyên 1..5 (điểm trung bình hệ thống: 3.5816).
   - **Tính toàn vẹn tham chiếu**: 100% `user_id` tồn tại trong bảng `users`, 100% `movie_id` tồn tại trong bảng `movies`. Không có khóa ngoại mồ côi.
   - **Thời gian**: Chuyển đổi timestamp Unix sang chuỗi UTC ISO 8601 kết thúc bằng `Z` (`YYYY-MM-DDTHH:MM:SSZ`), trải dài từ `2000-04-25T23:05:32Z` đến `2003-02-28T17:49:50Z`.

> **Kết luận EDA**: Dữ liệu nguồn MovieLens 1M đạt chất lượng tuyệt hảo, **100% sạch, nhất quán và toàn vẹn**, không cần áp dụng bất kỳ chính sách loại bỏ hay sửa đổi bất thường nào.

### C. Xuất dữ liệu chuẩn Canonical CSV & Manifest
- Xuất 4 tệp CSV chuẩn sang `data/processed/` (mã hóa UTF-8 không BOM, dấu phẩy, kết thúc dòng LF, rỗng cho NULL, số nguyên không có `.0`):
  1. `users.csv`: 6,040 dòng dữ liệu, sắp xếp theo `user_id` ASC.
  2. `movies.csv`: 3,883 dòng dữ liệu, sắp xếp theo `movie_id` ASC.
  3. `movie_genres.csv`: 6,408 dòng dữ liệu, sắp xếp theo `movie_id` ASC rồi `genre_name` ASC.
  4. `ratings.csv`: 1,000,209 dòng dữ liệu, sắp xếp theo `user_id` ASC, `movie_id` ASC, `timestamp` ASC, `rating` ASC.
- Tính mã băm SHA-256 byte từng bảng và ghi nhận vào `results/eda/canonical_manifest.json`:
  - `users`: `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f`
  - `movies`: `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b`
  - `movie_genres`: `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf`
  - `ratings`: `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf`
- Xuất báo cáo tổng hợp tại `results/eda/eda_summary.md` và `results/eda/eda_metrics.json`.

---

## 3. Quyết Định Kỹ Thuật Đã Ghi Nhận
- Đã ghi nhận `[DEC-P2-007]` trong `DECISIONS_P2.md`: Cố định thứ tự thể loại `genre_order` theo bảng chữ cái tiếng Anh (A–Z) cho 18 thể loại gốc MovieLens 1M.

---

## 4. Kiểm Thử Tự Động (Automated Testing)
- Tạo 2 bộ kiểm thử chuyên biệt:
  - `tests/mining/test_source_manifest.py`: Kiểm tra cấu trúc source manifest, đối soát SHA-256 và số dòng của các tệp nguồn trên đĩa.
  - `tests/mining/test_canonical_data.py`: Kiểm tra schema, tính duy nhất khóa chính, tính duy nhất khóa nghiệp vụ `(user_id, movie_id)`, khóa ngoại, thứ tự sắp xếp và đối soát hash SHA-256 byte của 4 bảng CSV chuẩn.
