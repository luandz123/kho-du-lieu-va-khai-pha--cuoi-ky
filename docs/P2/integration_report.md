# Báo Cáo Kiểm Nhận Tích Hợp G2 & Tái Lập Pipeline Khai Phá (Bước 12-P2)

- **Người thực hiện**: Người 2 (P2 - Data Mining & EDA)
- **Thời điểm thực hiện**: 2026-10-23 22:20:00 +07:00
- **Trạng thái**: G2 đã được điều phối chấp nhận; PR [#28](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/28) đã merge tại `88c5c7b952553523f58e82ed6546179451eb6b65`. G4 chưa chốt.
- **Cam kết phạm vi**: Chỉ cập nhật tài liệu và hồ sơ thuộc phạm vi sở hữu của P2; không sửa file P1; không tải dữ liệu nhạy cảm, credential hoặc model binary lên Git.

---

## 1. Môi Trường Thực Thi & Commit Ứng Viên Cố Định

- **Commit ứng viên cố định (Candidate Merge SHA)**:
  `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` (Merge commit PR #25 `codex/p1-s12a-integration`)
- **Checkout tách biệt**:
  `tmp/checkout_12a` (HEAD xác minh tại `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`, working tree sạch). Working tree chính của P2 tại `main` được bảo toàn nguyên vẹn.
- **Hệ điều hành**: Windows 11 (x86_64) trên máy P2 độc lập hoàn toàn với máy P1.
- **Môi trường Python**: Python 3.12.6 tại virtual environment mới `tmp/venv_12a`.
- **Dịch vụ CSDL**: PostgreSQL 17.4 chạy cục bộ trên máy P2 (`127.0.0.1:5432`).
- **Thư viện phụ thuộc**: Cài đặt nguyên gốc từ `requirements.txt` tại candidate SHA:
  - `numpy==2.0.2`, `pandas==2.3.3`, `scipy==1.14.1`, `scikit-learn==1.5.2`
  - `psycopg2-binary==2.9.10`, `SQLAlchemy==2.0.43`, `pytest==8.4.2`, `matplotlib==3.10.7`
  - `joblib==1.6.0`, `threadpoolctl==3.7.0`, `requests==2.32.5`
  - Kết quả `pip check`: `No broken requirements found.` (không phát hiện xung đột dependency được khai báo; không chứng minh tương thích tuyệt đối, không chỉnh sửa dependency).

---

Các lệnh bên dưới là hướng dẫn tái sử dụng hồ sơ, không phải một lần chạy mới. Quy ước `<workspace-root>` là thư mục gốc do người chạy chọn; checkout và venv là hai thư mục ngang hàng bên trong `tmp/` của workspace đó. Chạy tất cả lệnh từ checkout candidate:

```powershell
$workspaceRoot = (Get-Location).Path # bắt đầu tại workspace root
$checkout = Join-Path $workspaceRoot 'tmp/checkout_12a'
$venvPython = Join-Path $workspaceRoot 'tmp/venv_12a/Scripts/python.exe'
Set-Location $checkout
```

Checkout phải ở candidate SHA nêu trên; venv dùng requirements của checkout đó. `.env`, `data/raw/ml-1m` và `tmp/` trong các lệnh là đường dẫn tương đối với checkout. `.env` và kết quả chi tiết giữ ngoài Git. Cấu hình kết nối DW theo `.env` cục bộ trước khi gọi CLI.

## 2. Nhật Ký Tái Tạo CSDL Tích Hợp (DW-Only Reconstruction)

1. **Kiểm tra nguồn MovieLens 1M và `source_manifest.json`**:
   - Thư mục nguồn: `data/raw/ml-1m`
   - Cả 4 tệp `movies.dat`, `ratings.dat`, `README`, `users.dat` đều khớp chính xác 100% SHA-256 và kích thước byte theo bản kê `data/source_manifest.json`.
2. **Thực thi chế độ Plan-only**:
   - Lệnh: `& $venvPython etl/recreate_integration_dw.py`
   - Kết quả: `{"mode": "PLAN_ONLY", "creates_database": false, "superset_required": false}` (Đạt).
3. **Thực thi chế độ Apply**:
   - Lệnh: `& $venvPython etl/recreate_integration_dw.py --apply --raw-dir data/raw/ml-1m --env-file .env --date 20261023 --report tmp/p2_recreate_dw_report.json`
   - **Run ID**: `e7b2219c75e847e38005de5d0e2509a9`
   - **Tên CSDL tích hợp được tạo**: `movielens_btl_int_20261023_e7b2219c`
   - **Owner**: `postgres`
   - **Transaction**: `COMMITTED`
   - **Số dòng nạp**:
     - `users`: 6,040 dòng
     - `movies`: 3,883 dòng
     - `movie_genres`: 6,408 dòng
     - `ratings`: 1,000,209 dòng
   - **Mã băm bảng chuẩn (Canonical Hashes) tại DW**:
     - `users`: `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f`
     - `movies`: `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b`
     - `movie_genres`: `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf`
     - `ratings`: `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf`
   - Bằng chứng tái tạo công bố tại [dw_reconstruction.json](../../results/mining/integration_p2/dw_reconstruction.json) (bản tổng hợp công bố; báo cáo chi tiết giữ cục bộ ngoài Git).

---

## 3. Kiểm Nhận Mốc G2 & Đối Chiếu Tương Đương 3 Chiều (RAW / CSV / DW)

Sử dụng adapter `load_dw_data()` đọc trực tiếp 4 view hợp đồng:
- `dw.v_ml_users`
- `dw.v_ml_movies`
- `dw.v_ml_movie_genres`
- `dw.v_ml_ratings`

### Bảng Đối Chiếu Tính Toàn Vẹn & Tương Đương

| Bảng dữ liệu | Số dòng RAW | Số dòng CSV | Số dòng DW | SHA-256 Canonical (Khớp 100%) | Trạng thái tương đương |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `users` | 6,040 | 6,040 | 6,040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` | **PASS (100% khớp)** |
| `movies` | 3,883 | 3,883 | 3,883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` | **PASS (100% khớp)** |
| `movie_genres` | 6,408 | 6,408 | 6,408 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` | **PASS (100% khớp)** |
| `ratings` | 1,000,209 | 1,000,209 | 1,000,209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` | **PASS (100% khớp)** |

- **Kiểm tra định dạng & thời gian**: Cột `rated_at` định dạng chuẩn ISO-8601 UTC kết thúc bằng `Z`, không có độ trôi timezone. Thứ tự cột và kiểu dữ liệu tuân thủ tuyệt đối Data Contract v2.
- **Kết luận Intake G2**: **`P2 intake G2 = CONFIRMED`** (Đã cập nhật trong báo cáo tái tạo DW).

---

## 4. Tái Lập Pipeline Khai Phá Từ Nguồn DW

### 4.1. Trích Xuất Đặc Trưng Q1 & Tái Lập Gói Phân Cụm G3
- **Nguồn đầu vào**: CSDL `movielens_btl_int_20261023_e7b2219c` (`--source dw`).
- **Trích xuất đặc trưng**: Tạo thành công ma trận đặc trưng thể loại $(6038, 18)$ và 2 user không đủ điều kiện phân cụm.
- **Mô hình K-Means**: $K=4$, preprocessing `raw`, seed `42`, $n\_init=10$, model_version `kmeans_k4_seed42`.
- **Thư mục xuất bản**: Xuất độc lập vào thư mục cục bộ mới `tmp/g3_reproduced_dw` (không ghi đè gói đã chốt).
- **Đối chiếu Fingerprint Đóng Băng**:
  - `user_cluster.csv`: 6,040 dòng, SHA-256 `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93` (Khớp 100%).
  - `cluster_genre_profile.csv`: 72 dòng, SHA-256 `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d` (Khớp 100%).
  - “Bit-for-bit identical” chỉ áp dụng hai CSV đã đối chiếu ở trên; không áp dụng toàn bộ manifest hoặc môi trường.

### 4.2. Kiểm Thử CLI Gợi Ý Từ Nguồn DW (`mining.recommend`)
Đã thực thi 3 ca kiểm thử đại diện từ DW với biến môi trường kết nối chuẩn POSIX/Windows:

1. **Evaluation có seed**: model `item_based_cf_k40_eval_v1`, cutoff $t_2 = 976422051$, training scope 850,177 ratings; Top-5 có score type `cf`.
2. **Evaluation fallback**: cùng model evaluation và cutoff; kích hoạt fallback khi không có seed phù hợp. Top-5 có score type `popularity_fallback`, điểm `N/A (Popularity Fallback)`.
3. **Demo**: model `item_based_cf_k40_DEMO_full_history_v1`, sử dụng toàn bộ lịch sử; Top-5 có score type `cf`, không dùng để lấy metric offline.

Score CF là điểm xếp hạng tổng hợp từ similarity, không phải trực tiếp một giá trị cosine. Cả ba ca đạt Top-5 duy nhất và loại trừ lịch sử. Đây là ba ca tổng hợp để công bố; ID, số rating/seed và danh sách phim theo từng người dùng giữ cục bộ ngoài Git. Bằng chứng: [CLI summary](../../results/mining/integration_p2/cli_verification_summary.json).

Lệnh mẫu dưới đây chạy trong PowerShell tại checkout candidate, thay `<case-user>` bằng ca phù hợp cục bộ:

```powershell
& $venvPython -m mining.recommend --source dw --user-id <case-user> --mode evaluation --top-n 5 --output-json tmp/recommend_evaluation.json
& $venvPython -m mining.recommend --source dw --user-id <case-user> --mode demo --top-n 5 --output-json tmp/recommend_demo.json
```

Chạy lệnh evaluation cho cả ca có seed và fallback; placeholder phải được thay trước khi chạy.

---

## 5. Bảo Toàn Đánh Giá Test Chính Thức

- **Bảo toàn kết quả Test**: Tuyệt đối không gọi `mining/cf_test_evaluation.py` trên dữ liệu thật. Không điều chỉnh siêu tham số $k$. Không sửa đổi các tệp kết quả nghiệm thu (`cf_test_evaluation_receipt.json`, `cf_test_evaluation.json`, `metrics.csv`).
- **Kiểm thử độc lập**: Chạy 22 unit test bảo vệ evaluator và CLI (`test_cf_test_evaluation.py`, `test_recommend.py`) bằng interpreter của venv mới `tmp/venv_12a`:
  - `tests/mining/test_cf_test_evaluation.py`: 7/7 PASSED.
  - `tests/mining/test_recommend.py`: 15/15 PASSED.
  - `tests/mining/test_cf.py`: 9/9 PASSED.
  - **Tổng cộng**: 31/31 tests PASS (100%).

---

## 6. Giới Hạn Còn Lại & Tuyên Bố Môi Trường


1. **Phạm vi môi trường**: Toàn bộ quy trình Bước 12-P2 được thực hiện và tái lập thành công trên **máy P2 / Windows 11**. Bản báo cáo này xác nhận tính tái lập trên môi trường P2/Windows; **không tuyên bố đã xác minh trên Linux**.
2. **Phạm vi hạ tầng**: Không cài đặt Superset hoặc nạp analytics lên máy P2 (chưa có yêu cầu và không phụ thuộc hạ tầng P1).
3. **Trạng thái quy trình**: Trước công bố, Bước 12-P2 ở `12-P2 WAITING_REVIEW`. Hiện G2 đã được điều phối chấp nhận và PR #28 đã merge; G4 chưa chốt.

---

## 7. Đóng Gói Bằng Chứng Tổng Hợp (`results/mining/integration_p2/`)

Toàn bộ bằng chứng tổng hợp đã được rà soát an toàn (loại bỏ tuyệt đối thông tin credential, đường dẫn riêng tư trên máy cá nhân và dữ liệu định danh theo người dùng) và xuất bản tại thư mục `results/mining/integration_p2/`:

1. [environment.json](../../results/mining/integration_p2/environment.json): Thông số môi trường Windows 11, Python 3.12.6, PostgreSQL 17.4 và 34 dependencies được ghi nhận và kết quả `pip check` không phát hiện xung đột được khai báo.
2. [dw_reconstruction.json](../../results/mining/integration_p2/dw_reconstruction.json): Run ID `e7b2219c...`, database `movielens_btl_int_20261023_e7b2219c`, transaction `COMMITTED`, 4 mã băm canonical và số dòng thực nạp.
3. [source_equivalence.json](../../results/mining/integration_p2/source_equivalence.json): Bảng đối chiếu chi tiết 4 bảng dữ liệu, chứng minh tính tương đương 100% giữa RAW, CSV và DW views.
4. [g3_reproduction.json](../../results/mining/integration_p2/g3_reproduction.json): Bằng chứng tái lập gói phân cụm G3 K-Means ($K=4$, seed 42) từ DW, khớp từng byte mã băm của 2 tệp CSV frozen.
5. [cli_verification_summary.json](../../results/mining/integration_p2/cli_verification_summary.json): Báo cáo tổng hợp kiểm thử 3 ca CLI `mining.recommend` từ DW (seed, fallback, demo), chứng minh logic loại trừ lịch sử, tính duy nhất của Top-5 và tách biệt float score / fallback string mà không chứa user_id, seed hay danh sách item chi tiết.
6. [test_suite_log.txt](../../results/mining/integration_p2/test_suite_log.txt): Nhật ký thực thi 31 unit test độc lập (`test_cf_test_evaluation.py`, `test_recommend.py`, `test_cf.py`) đạt 100% PASS, đã rà soát và ẩn đường dẫn tuyệt đối cục bộ.
7. [manifest.json](../../results/mining/integration_p2/manifest.json): Bảng kê mã băm SHA-256 và kích thước byte của toàn bộ 6 tệp artifact trên.

