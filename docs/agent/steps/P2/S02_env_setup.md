# Báo Cáo Bước 2-P2: Thiết Lập Môi Trường Độc Lập Cho Người 2

- **Mã bước**: `P2-S02`
- **Nhánh Git**: `codex/p2-s02-env`
- **Commit SHA**: `afc005d`
- **Pull Request**: [#2](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/2)
- **Thời gian thực hiện**: 2026-10-15 17:23:28 +07:00
- **Trạng thái**: `WAITING_REVIEW` (Đã duyệt chức năng, đang chờ review và merge PR #2 vào `main`)

---

## 1. Mục Tiêu & Đầu Vào
- **Mục tiêu**: Xây dựng môi trường Python ảo độc lập cho Người 2 (P2 - Data Mining & EDA), định nghĩa danh sách gói phụ thuộc riêng tại `docs/P2/requirements-p2.txt`, cài đặt và kiểm thử hoạt động của các thư viện tính toán ma trận và máy học (K-Means, Cosine Similarity, Sparse Matrix).
- **Đầu vào**:
  - Quyết định duyệt Bước 0 từ người dùng (lưu tại `docs/agent/REVIEWS_P2.md`).
  - Python 3.12.3 trên máy Ubuntu 24.04.1 LTS.

---

## 2. Các Công Việc Đã Thực Hiện

1. **Khắc phục nghẽn bộ nhớ đĩa**:
   - Phát hiện 33GB tệp đã xóa bị lưu giữ tại `~/.local/share/Trash`.
   - Được người dùng xác nhận và phê duyệt trực tiếp, tiến hành dọn sạch Thùng rác.
   - Dung lượng đĩa khả dụng trên `/home` tăng từ **771 MB** lên **~34 GB** (giải quyết triệt để nút thắt tài nguyên).
2. **Khởi tạo bộ hồ sơ theo dõi cho P2**:
   - `docs/agent/STATE_P2.md`: Lưu trạng thái hiện tại, lộ trình các bước và phân định quyền sở hữu tệp.
   - `docs/agent/DECISIONS_P2.md`: Lưu các quyết định kiến trúc DEC-P2-001 đến DEC-P2-005.
   - `docs/agent/REVIEWS_P2.md`: Lưu nguyên văn lời duyệt Bước 0 của người dùng.
   - `docs/agent/PROMPTS_P2.md`: Ghi nhật ký prompt và chỉ đạo từ người dùng.
   - `docs/agent/steps/P2/S00_survey.md`: Báo cáo chi tiết khảo sát hiện trạng Bước 0.
3. **Quản lý Git & Cách ly tệp**:
   - Tạo nhánh làm việc: `codex/p2-s02-env`.
   - Cấu hình loại trừ cục bộ tại `.git/info/exclude` (bỏ qua `.venv/`, `data/raw/`, `data/processed/`, `.env`, `__pycache__/`, `.pytest_cache/`) để không sửa chéo tệp `.gitignore` do P1 sở hữu trước mốc G0.
4. **Thiết lập môi trường ảo `.venv` & Quản lý gói phụ thuộc**:
   - Tạo `.venv` dựa trên Python 3.12.3: `python3 -m venv .venv`.
   - Khởi tạo `docs/P2/requirements-p2.txt` độc lập cho P2 (không chạm vào `requirements.txt` tổng do P1 sở hữu):
     - `numpy==2.0.2`
     - `pandas==2.3.3`
     - `scipy==1.14.1`
     - `scikit-learn==1.5.2`
     - `pytest==8.4.2`
     - `requests==2.34.2`
   - Cài đặt thành công toàn bộ dependencies vào `.venv`.
5. **Kiểm thử môi trường (Smoke Test)**:
   - Viết bài test kiểm thử tự động tại `tests/mining/test_env.py` bao gồm 4 ca kiểm thử:
     - `test_python_version`: Xác nhận Python runtime >= 3.12.
     - `test_core_libraries_imported`: Xác nhận import thành công và phiên bản hợp lệ của `numpy`, `pandas`, `scipy`.
     - `test_sparse_matrix_and_similarity`: Kiểm tra ma trận thưa Scipy CSR và tính Cosine Similarity (nền tảng cho Q2 Item-based CF).
     - `test_kmeans_execution`: Kiểm tra thuật toán Scikit-learn KMeans phân cụm (nền tảng cho Q1 User Clustering).
   - Chạy lệnh kiểm thử:
     ```bash
     .venv/bin/pytest tests/mining/test_env.py -v
     ```
   - **Kết quả**: 4/4 bài kiểm tra **PASSED** trong 1.22s.

---

## 3. Bằng Chứng Thực Nghiệm

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0 -- /home/luan/kho-du-lieu-va-khai-pha--cuoi-ky/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /home/luan/kho-du-lieu-va-khai-pha--cuoi-ky
collecting ... collected 4 items

tests/mining/test_env.py::test_python_version PASSED                     [ 25%]
tests/mining/test_env.py::test_core_libraries_imported PASSED            [ 50%]
tests/mining/test_env.py::test_sparse_matrix_and_similarity PASSED       [ 75%]
tests/mining/test_env.py::test_kmeans_execution PASSED                   [100%]

============================== 4 passed in 1.22s ===============================
```

---

## 4. Danh Sách Tệp Thay Đổi / Tạo Mới (Thuộc Quyền P2)

- `docs/P2/requirements-p2.txt`: Danh mục thư viện phụ thuộc P2.
- `docs/agent/STATE_P2.md`: Nhật ký trạng thái P2.
- `docs/agent/DECISIONS_P2.md`: Sổ tay quyết định kiến trúc P2.
- `docs/agent/REVIEWS_P2.md`: Nhật ký phê duyệt của P2.
- `docs/agent/PROMPTS_P2.md`: Nhật ký chỉ đạo của P2.
- `docs/agent/steps/P2/S00_survey.md`: Hồ sơ khảo sát Bước 0.
- `docs/agent/steps/P2/S02_env_setup.md`: Hồ sơ thiết lập môi trường Bước 2-P2.
- `tests/mining/__init__.py`: Package init.
- `tests/mining/test_env.py`: Bộ kiểm thử môi trường độc lập P2.

---

## 5. Giới Hạn & Tiền Đề Cho Bước Kế Tiếp

- **Tiền đề**:
  - Chờ P1 hoàn thành **Bước 1** (Soạn thảo Hợp đồng dữ liệu v2 tại `docs/shared/data_contract.md`, `data_contract.json` và đưa mốc nền G0 lên `main`).
  - P2 tiếp nhận và xác nhận hợp đồng trước khi bước vào **Bước 3 (EDA & Tải dữ liệu nguồn)**.
- **Trạng thái**: Đã sẵn sàng 100% môi trường tính toán để bắt đầu tải dữ liệu nguồn, tính SHA-256 manifest và làm sạch EDA.
