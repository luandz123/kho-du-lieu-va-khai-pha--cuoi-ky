# STATE_P2 - Trạng Thái Hiện Tại Của Người 2

- **Vai trò**: Người 2 (P2 - Khai phá dữ liệu & EDA)
- **Dự án**: BTL Kho dữ liệu và Khai phá dữ liệu (Bảo vệ 27/10/2026)
- **Workspace máy thực tế**: `/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`
- **Hệ điều hành**: Linux Ubuntu 24.04.1 LTS (Kernel `6.14.0-37-generic`, x86_64)
- **Phần cứng**: 13th Gen Intel Core i7-13620H (16 vCPUs), 15GB RAM (~7.1GB free), Đĩa trống ~34GB
- **Môi trường Python**: Python 3.12.3 tại `.venv/bin/python`
- **Nhánh Git hiện tại**: `p2-s03-eda`
- **Thời điểm cập nhật**: 2026-10-15 17:34:00 +07:00

---

## 1. Bảng Trạng Thái Các Bước (P2)

| Bước | Mô tả nội dung | Trạng thái | Ghi chú / Tiền đề |
| :--- | :--- | :--- | :--- |
| **Bước 0** | Khảo sát hiện trạng máy Người 2 | `APPROVED` | Duyệt lúc 16:42:29 ngày 15/10/2026. Lời duyệt lưu tại REVIEWS_P2.md. |
| **Bước 1** | Chuẩn bị Hợp đồng dữ liệu & Mốc nền G0 | *P1 sở hữu* | P1 đã đưa G0 lên `main` (commit `5c31e80`, PR #1 `eff54ae`). |
| **Bước 2-P2** | Thiết lập môi trường độc lập cho P2 | `MERGED` | PR [#2](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/2) đã merge vào `main` (commit `ff87081`). |
| **Bước 3A-P2**| Nhận mốc G0 & Xác nhận hợp đồng dữ liệu v2 | `APPROVED` | Duyệt lúc 17:38:48 ngày 15/10/2026. Lời duyệt lưu tại REVIEWS_P2.md. |
| **Bước 3** | EDA, Adapter & Chuẩn bị bàn giao G1 | `WAITING_REVIEW` | Nhánh `p2-s03-eda`. PR [#4](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/4) đã mở vào `main`. 18/18 tests PASSED. Chờ điều phối review và merge G1. |
| **Bước 8** | Khai phá dữ liệu Q1: Đặc trưng 8A & K-Means 8B | `NOT_STARTED` | Chờ duyệt và merge Bước 3 (G1). |

| **Bước 9** | Khai phá dữ liệu Q2: Temporal Split & Baseline | `NOT_STARTED` | Chờ Bước 8 hoàn thành. |
| **Bước 10** | Khai phá dữ liệu Q2: Item-based CF & CLI | `NOT_STARTED` | Chờ Bước 9 hoàn thành. |


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
