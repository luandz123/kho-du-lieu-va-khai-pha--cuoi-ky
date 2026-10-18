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

### [DEC-P2-009] Xuất bản nguyên tử (Atomic Publication) và bảo toàn gói G3 chống phá hủy khi kiểm tra thất bại
- **Bối cảnh**: Điều phối viên phát hiện lỗi thứ tự trong `export_g3_handoff_package`: hai tệp CSV được ghi trực tiếp vào thư mục đích trước khi kiểm tra hash đóng băng. Khi truyền nhãn hoán vị, hàm ném `ValueError` nhưng hai CSV đích đã bị thay thế, làm mất tính toàn vẹn và phá hỏng gói cũ.
- **Quyết định**:
  1. Toàn bộ quá trình tạo DataFrame, chuyển đổi sang chuỗi byte CSV, tính băm SHA-256 và dựng cấu trúc `manifest` được thực hiện 100% trong bộ nhớ trước khi chạm vào bất kỳ tệp nào của gói đích.
  2. Thực hiện nghiêm ngặt kiểm tra tính nhất quán nội bộ của gói đã tồn tại trên đĩa (tồn tại đầy đủ CSV + manifest, parse JSON hợp lệ, checksum trên đĩa khớp với manifest). Tuyệt đối không âm thầm bỏ qua manifest hỏng để ghi đè.
  3. Kiểm tra chống tái sử dụng version: cùng `model_version` nhưng payload (mã băm CSV dự kiến) hoặc `canonical_hashes` khác biệt với gói đang có phải bị từ chối ngay lập tức trước khi ghi.
  4. Chỉ công bố (publish) khi mọi kiểm tra contract, fingerprint và checksum đều đạt: ghi các tệp vào thư mục tạm trung gian (`tempfile.TemporaryDirectory`) rồi thay thế nguyên tử (`os.replace`). Nếu kiểm tra thất bại ở bất kỳ khâu nào, gói cũ trên đĩa giữ nguyên 100% từng byte, và thư mục chưa tồn tại không để lại bất kỳ tệp dở dang nào.



