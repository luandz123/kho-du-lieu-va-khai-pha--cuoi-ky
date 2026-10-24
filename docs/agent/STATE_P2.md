# STATE_P2 - Trạng Thái Hiện Tại Của Người 2

- **Vai trò**: Người 2 (P2 - Khai phá dữ liệu & EDA)
- **Dự án**: BTL Kho dữ liệu và Khai phá dữ liệu (Bảo vệ 27/10/2026)
- **Workspace máy thực tế**: `<workspace-root>` (Máy P2 độc lập với máy P1)
- **Hệ điều hành**: Windows 11 (x86_64)
- **Phần cứng & Dịch vụ**: 13th Gen Intel Core i7-13620H (16 vCPUs), 16GB RAM, Đĩa C: trống ~62.5GB; PostgreSQL 17.4 local service
- **Môi trường Python**: Python 3.12.6 tại `.venv\Scripts\python.exe`
- **Nhánh lập hồ sơ trước công bố**: `codex/p2-s12-integration-report` (tạo từ candidate commit `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`)
- **Thời điểm cập nhật**: 2026-10-24 (hiệu chỉnh hồ sơ công bố; không chạy lại pipeline)

- **Ghi chú môi trường Bước 12-P2**: Thực hiện tái lập và kiểm nhận trên máy P2 / Windows độc lập; kết luận trung thực theo môi trường thực tế Windows (không ghi nhận là đã xác minh trên Linux).

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
| **Bước 10** | Q2: Item-based CF & Đánh giá Test đúng 1 lần & CLI | `APPROVED` | PR [#23](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/23) và PR bổ sung #24 đã merge vào `main` tại commit `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02`. Snapshot gốc tại `docs/P2/provenance/eval_original.py`, 31/31 CF tests đạt. Đã nghiệm thu kỹ thuật. |
| **Bước 12-P2** | Kiểm nhận G2 & Tái lập pipeline khai phá từ DW | `G2 ACCEPTED / PR28 MERGED` | Thực hiện tại candidate SHA `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` (PR #25) trên máy P2 / Windows 11. Tái tạo CSDL `movielens_btl_int_20261023_e7b2219c` trên PostgreSQL 17.4 cục bộ. Kiểm nhận 4 view DW khớp 100% SHA-256 canonical tương đương 3 chiều RAW / CSV / DW (`p2_intake_g2: CONFIRMED`). Tái lập Q1/G3 K-Means ($K=4$, seed 42) khớp 100% fingerprint CSV frozen vào `tmp/g3_reproduced_dw`. Chạy 3 ca CLI `mining.recommend` từ DW (seed, fallback, demo) loại lịch sử và Top-5 duy nhất. Bảo toàn nguyên vẹn đánh giá test (31/31 unit test PASS). Đã lập `docs/P2/integration_report.md` và `docs/agent/steps/P2/S12.md`. PR #28 đã merge tại `88c5c7b952553523f58e82ed6546179451eb6b65`, G2 đã được điều phối chấp nhận; G4 chưa chốt. |



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

Hồ sơ môi trường Bước 12-P2 công bố: [environment.json](../../results/mining/integration_p2/environment.json). `<workspace-root>` là đường dẫn do người chạy chọn; chi tiết đường dẫn cá nhân giữ cục bộ ngoài Git.
