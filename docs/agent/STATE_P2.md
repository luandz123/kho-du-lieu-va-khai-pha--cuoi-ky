# STATE_P2 - Trạng Thái Hiện Tại Của Người 2

- **Vai trò**: Người 2 (P2 - Khai phá dữ liệu & EDA)
- **Dự án**: BTL Kho dữ liệu và Khai phá dữ liệu (Bảo vệ 27/10/2026)
- **Workspace máy thực tế**: `/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`
- **Hệ điều hành**: Linux Ubuntu 24.04.1 LTS (Kernel `6.14.0-37-generic`, x86_64)
- **Phần cứng**: 13th Gen Intel Core i7-13620H (16 vCPUs), 15GB RAM (~7.1GB free), Đĩa trống ~34GB
- **Môi trường Python**: Python 3.12.3 tại `.venv/bin/python`
- **Nhánh Git hiện tại**: `codex/p2-s10-finalization`
- **Thời điểm cập nhật**: 2026-10-22 13:10:00 +07:00

---

## 1. Bảng Trạng Thái Các Bước (P2)

| Bước | Mô tả nội dung | Trạng thái | Ghi chú / Tiền đề |
| :--- | :--- | :--- | :--- |
| **Bước 0** | Khảo sát hiện trạng máy Người 2 | `APPROVED` | Duyệt lúc 16:42:29 ngày 15/10/2026. Lời duyệt lưu tại REVIEWS_P2.md. |
| **Bước 1** | Chuẩn bị Hợp đồng dữ liệu & Mốc nền G0 | *P1 sở hữu* | P1 đã đưa G0 lên `main` (commit `5c31e80`, PR #1 `eff54ae`). |
| **Bước 2-P2** | Thiết lập môi trường độc lập cho P2 | `MERGED` | PR [#2](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/2) đã merge vào `main` (commit `ff87081`). |
| **Bước 3A-P2**| Nhận mốc G0 & Xác nhận hợp đồng dữ liệu v2 | `APPROVED` | Duyệt lúc 17:38:48 ngày 15/10/2026. Lời duyệt lưu tại REVIEWS_P2.md. |
| **Bước 3** | EDA, Adapter & Bàn giao G1 | `MERGED` | PR #5 (head `b73c8e2`) đã được điều phối review và merge vào `main` (commit `a8d2615`). 23/23 tests passed trên Windows. |
| **Bước 8A** | Q1: Trích xuất đặc trưng thể loại người dùng | `MERGED` | PR [#8](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/8) đã được điều phối review và merge vào `main` (commit `52dd682`). 27/27 tests passed. |
| **Bước 8B** | Q1: K-Means, Diễn giải & Gói cụm G3 | `MERGED` | PR [#12](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/12) đã được điều phối review và merge vào `main` (commit `be8c889`). 16/16 test clustering đạt. Đã chỉnh docstring cam kết xuất bản theo nguyên tử từng file. |
| **Bước 9A** | Q2: Phép chia thời gian & Giao thức đánh giá | `MERGED` | PR [#16](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/16) đã merge vào `main` tại commit `afeeec0`. 52/52 tests passed. Rà soát độc lập khớp toàn bộ count, mốc UTC và cohort 471. |
| **Bước 9B** | Q2: Popularity Baseline trên Validation | `MERGED` | PR [#17](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/17) và PR bổ sung [#19](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/19) đã merge vào `main` tại commit `6a0adbf`. |
| **Bước 10** | Q2: Item-based CF & Đánh giá Test đúng 1 lần & CLI | `10B WAITING_REVIEW` | PR #22 đã merge vào `main` tại commit `14cfe0d`. Bản sửa provenance `9f4a876` đã được ghép cùng toàn bộ gói 10B lên nhánh `codex/p2-s10-finalization`. Kết quả đánh giá test duy nhất (`test_run_s10b_official_20261022_034458`: CF k*=40 đạt Precision@5=0.231023, Recall@5=0.03530289, Hits=1333 so với Baseline 0.201733, 0.02712408, Hits=1164) đã công bố đầy đủ trong `cf_test_evaluation.json`, `cf_test_evaluation_receipt.json`, `metrics.csv`. CLI `recommend.py` và 18/18 CF tests đạt chuẩn. Đã mở PR vào `main` chờ điều phối review. |


---

## 2. Quyền Sở Hữu Tệp & Thư Mục (P2)

- **P2 được phép ghi**:
  - `mining/`
  - `tests/mining/`
  - `results/eda/`
  - `results/mining/`
  - `docs/P2/` (bao gồm `docs/P2/requirements-p2.txt`)
  - `docs/agent/steps/P2/`
  - Các tệp `*_P2.md` trong `docs/agent/` (`STATE_P2.md`, `DECISIONS_P2.md`, `REVIEWS_P2.md`, `PROMPTS_P2.md`)
  - `data/source_manifest.json`
- **Cục bộ riêng không commit**:
  - `data/raw/`
  - `data/processed/`
  - `.venv/`
  - `.env`
- **Tuyệt đối không ghi**:
  - Không ghi vào thư mục P1 (`database/`, `etl/`, `olap/`, `dashboard/`, `tests/warehouse/`, `results/warehouse/`, `results/olap/`, `docs/P1/`, `docs/shared/`, `*_P1.md`).
  - Không sửa `requirements.txt` gốc hoặc `.gitignore` (thuộc sở hữu P1).
