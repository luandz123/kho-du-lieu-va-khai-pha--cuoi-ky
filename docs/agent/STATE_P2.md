# STATE_P2 - Trạng Thái Hiện Tại Của Người 2

- **Vai trò**: Người 2 (P2 - Khai phá dữ liệu & EDA)
- **Dự án**: BTL Kho dữ liệu và Khai phá dữ liệu (Bảo vệ 27/10/2026)
- **Workspace máy thực tế**: `/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`
- **Hệ điều hành**: Linux Ubuntu 24.04.1 LTS (Kernel `6.14.0-37-generic`, x86_64)
- **Phần cứng**: 13th Gen Intel Core i7-13620H (16 vCPUs), 15GB RAM (~7.1GB free), Đĩa trống ~34GB
- **Môi trường Python**: Python 3.12.3 tại `.venv/bin/python`
- **Nhánh Git hiện tại**: `codex/p2-s02-env`
- **Thời điểm cập nhật**: 2026-10-15 16:46:00 +07:00

---

## 1. Bảng Trạng Thái Các Bước (P2)

| Bước | Mô tả nội dung | Trạng thái | Ghi chú / Tiền đề |
| :--- | :--- | :--- | :--- |
| **Bước 0** | Khảo sát hiện trạng máy Người 2 | `APPROVED` | Duyệt lúc 16:42:29 ngày 15/10/2026. Lời duyệt lưu tại REVIEWS_P2.md. |
| **Bước 1** | Chuẩn bị Hợp đồng dữ liệu & Mốc nền G0 | *P1 sở hữu* | P1 tạo `docs/shared/data_contract.md/.json`. P2 chờ nhận trước Bước 3. |
| **Bước 2-P2** | Thiết lập môi trường độc lập cho P2 | `WAITING_REVIEW` (Merge PR) | Duyệt chức năng lúc 17:21:25. Đã mở PR [#2](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/2) (commit `afc005d`). Đang chờ review & merge. |
| **Bước 3** | Tải dữ liệu nguồn & Kiểm tra EDA Canonical | `NOT_STARTED` | Chờ Hợp đồng dữ liệu v2 từ P1 được duyệt và chuyển sang. |
| **Bước 4-P2** | Khai phá dữ liệu Q1: Phân cụm K-Means | `NOT_STARTED` | Chờ Bước 3 hoàn thành. |
| **Bước 5-P2** | Khai phá dữ liệu Q2: Item-based CF & Baseline | `NOT_STARTED` | Chờ Bước 4-P2 hoàn thành. |

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
