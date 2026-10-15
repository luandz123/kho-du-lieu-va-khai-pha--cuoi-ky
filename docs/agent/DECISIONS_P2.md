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
