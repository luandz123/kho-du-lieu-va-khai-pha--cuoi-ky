# Báo Cáo Phân Cụm Người Dùng Theo Thể Loại Phim (Tiểu Bước 8B - Q1)

Tài liệu này tổng hợp kết quả thử nghiệm mô hình K-Means, đối chiếu đa tiêu chí lựa chọn cấu hình, kiểm định tính ổn định, diễn giải chuyên sâu 4 nhóm người dùng theo tỷ lệ đánh giá thể loại và quy cách đóng gói bàn giao mốc G3 theo Hợp đồng dữ liệu v2.

---

## 1. Phương Pháp Luận & Phạm Vi Tính Metric

### 1.1. Không gian đặc trưng đầu vào (kế thừa từ 8A)
- Vector đặc trưng thể loại của mỗi người dùng $\mathbf{p}_u \in [0, 1]^{18}$ biểu diễn tỷ lệ lượt đánh giá tích cực ($\text{rating} \ge 4$) trên 18 thể loại phim sắp xếp cố định theo thứ tự chữ cái A–Z (`Action` $\to$ `Western`).
- Toàn bộ vector đặc trưng nằm trên hình đơn vị xác suất L1 (simplex): $\sum_{g=1}^{18} p_{u, g} = 1.0$ (sai số $\le 10^{-8}$).
- **Phạm vi đối tượng huấn luyện:** Đúng **6,038 người dùng đủ điều kiện** (`status = "assigned"`, có ít nhất 1 đánh giá tích cực).
- **2 người dùng thiếu bằng chứng** (`user_id` 3598 và 4486, mang `status = "insufficient_evidence"`) được gán `cluster_id = NULL`, tuyệt đối không tham gia vào ma trận huấn luyện của bất kỳ mô hình nào.
- Thuộc tính nhân khẩu học (`gender`, `age_group`, `occupation`) **tuyệt đối không tham gia vào quá trình phân cụm**; chỉ được dùng sau phân cụm để phân tích tương quan thống kê mô tả.

### 1.2. Làm rõ phạm vi tính toán các metric thực nghiệm
- **Toàn bộ 14 cấu hình K-Means** đều được huấn luyện (`fit_predict`) trên **toàn bộ 6,038 người dùng đủ điều kiện**.
- **Inertia (SSE)** và **Kích thước các cụm** (quy mô cụm nhỏ nhất, lớn nhất, số lượng user mỗi cụm) được tính toán trên **toàn bộ 6,038 người dùng đã phân cụm**.
- **Điểm Silhouette** được đánh giá trên **mẫu cố định gồm 2,000 người dùng** (được lấy ngẫu nhiên có thể tái lập với `random_state=42`, mã băm tập mẫu: `afc27da1977cf28e45417b7eaf9ff27faa6028dc4e670367a223c758078db485`).
- **Tham số thuật toán thực dùng:** `KMeans(n_clusters=K, random_state=42, n_init=10, max_iter=300)`.
- **Thông số môi trường và thứ tự dữ liệu:**
  - `scikit-learn`: `1.5.2`
  - `numpy`: `2.0.2`
  - `pandas`: `2.3.3`
  - `python`: `3.12.3`
  - Mã băm thứ tự 18 thể loại (`genre_order_hash`): `bcf3f11af93e4d9392d5ed9072917b784a1d19fdb365092c85c41acd5e5b4665`
  - Mã băm thứ tự 6,038 người dùng (`user_order_hash`): `37eaa087e5d9b6be9a17e61d773a58ee39234e793409294fa0d98cf402f1c24a`

---

## 2. Bảng Kết Quả Thử Nghiệm 14 Cấu Hình ($K=2..8$)

Dưới đây là số liệu đầy đủ của 14 cấu hình (7 giá trị $K \times 2$ phương pháp tiền xử lý), được xuất nguyên bản tại `results/mining/kmeans_experiments.csv`:

| $K$ | Tiền xử lý | Inertia (Toàn bộ 6,038 user) | Silhouette (Mẫu cố định 2,000) | Kích thước cụm nhỏ nhất | Kích thước cụm lớn nhất | Quy mô chi tiết từng cụm | Thời gian chạy (giây) | Ghi chú khả năng diễn giải |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2** | `raw` | 217.7719 | **0.2233** | 2,798 | 3,240 | [2798, 3240] | 0.176 | Silhouette cao hơn (0.22) nhưng phân chia còn thô (chủ yếu tách Drama vs Action/Comedy) |
| **3** | `raw` | 181.0233 | **0.2211** | 1,250 | 2,534 | [2254, 1250, 2534] | 0.197 | Silhouette cao hơn (0.22) nhưng phân chia còn thô (chủ yếu tách Drama vs Action/Comedy) |
| **4** | `raw` | **162.9874** | **0.1860** | **760** | **2,478** | **[2478, 1393, 760, 1407]** | 0.274 | **Cấu hình đề xuất: Phân tách rõ 4 chủ đề thể loại, quy mô cân đối (12.6%-41.0%), độ ổn định cao (ARI>0.97)** |
| **5** | `raw` | 152.1376 | 0.1674 | 524 | 1,604 | [1153, 1298, 524, 1604, 1459] | 0.331 | Cấu hình so sánh thử nghiệm (kém ổn định khi đổi seed, ARI=0.4999) |
| **6** | `raw` | 141.7432 | 0.1723 | 103 | 1,902 | [1207, 860, 103, 685, 1902, 1281] | 0.421 | Bắt đầu phân mảnh thành các cụm phụ quy mô nhỏ (<200 user) |
| **7** | `raw` | 132.0120 | 0.1729 | 101 | 1,340 | [619, 1310, 1340, 1021, 101, 460, 1187] | 0.450 | Bắt đầu phân mảnh thành các cụm phụ quy mô nhỏ (<200 user) |
| **8** | `raw` | 125.5040 | 0.1721 | 101 | 1,308 | [1308, 1220, 450, 984, 183, 1175, 617, 101] | 0.517 | Bắt đầu phân mảnh thành các cụm phụ quy mô nhỏ (<200 user) |
| **2** | `StandardScaler` | 95,141.11 | 0.1472 | 2,360 | 3,678 | [3678, 2360] | 0.179 | Cấu hình so sánh thử nghiệm |
| **3** | `StandardScaler` | 86,041.23 | 0.1398 | 1,475 | 2,642 | [1475, 2642, 1921] | 0.416 | Cấu hình so sánh thử nghiệm |
| **4** | `StandardScaler` | 80,502.67 | 0.1238 | 460 | 1,982 | [460, 1743, 1982, 1853] | 0.335 | Cấu hình so sánh thử nghiệm |
| **5** | `StandardScaler` | 76,187.45 | 0.1199 | 350 | 2,336 | [2336, 350, 1868, 1020, 464] | 0.493 | Cấu hình so sánh thử nghiệm |
| **6** | `StandardScaler` | 72,188.23 | 0.1302 | 100 | 2,335 | [469, 342, 1758, 1034, 100, 2335] | 0.393 | Cấu hình so sánh thử nghiệm |
| **7** | `StandardScaler` | 69,077.42 | 0.1055 | 97 | 1,970 | [1039, 904, 1313, 420, 1970, 97, 295] | 0.628 | StandardScaler chia theo độ lệch chuẩn làm tăng trọng số thể loại hiếm, tạo cụm quy mô nhỏ (<100 user) |
| **8** | `StandardScaler` | 65,742.18 | 0.1018 | 5 | 1,960 | [1960, 1047, 302, 5, 855, 415, 1355, 99] | 0.605 | StandardScaler chia theo độ lệch chuẩn làm tăng trọng số thể loại hiếm, tạo cụm quy mô nhỏ (<100 user) |

---

## 3. Lý Do Lựa Chọn Cấu Hình & Bằng Chứng Kỹ Thuật

### 3.1. So sánh Tradeoff giữa $K=4$ và $K=2, 3$
- Về metric hình học đơn thuần: Cấu hình $K=2$ ($\text{Sil} = 0.2233$) và $K=3$ ($\text{Sil} = 0.2211$) có điểm Silhouette cao hơn $K=4$ ($\text{Sil} = 0.1860$).
- Tuy nhiên, quyết định lựa chọn $K=4$ dựa trên **sự cân bằng đa mục tiêu (multi-criteria tradeoff)**:
  1. **Khả năng diễn giải nghiệp vụ (Interpretability):**
     - Ở $K=2$: Thuật toán chỉ tách dữ liệu thành 2 khối lớn phân cực thô (người đánh giá thiên về Drama vs người đánh giá thiên về Action/Comedy), làm lu mờ hoàn toàn sự khác biệt giữa phim Hài (Comedy) và phim Hành động/Viễn tưởng (Action/Sci-Fi).
     - Ở $K=3$: Nhóm Comedy và Action vẫn bị trộn lẫn hoặc phân chia chưa rõ, không tách bạch được nhóm người dùng có hành vi đánh giá đa dạng, cân bằng các thể loại (Generalist).
     - Ở $K=4$: 4 cụm mang đặc trưng phân hóa rất sắc nét và tự nhiên: (0) Đánh giá đa dạng, (1) Tập trung Drama & Tình cảm, (2) Tập trung Hài kịch, (3) Tập trung Hành động & Viễn tưởng.
  2. **Quy mô cụm cân đối (Cluster Balance):**
     - 4 cụm có tỷ trọng từ 12.6% (760 user) đến 41.0% (2,478 user). Không có cụm nào quá nhỏ hay bị phân mảnh manh mún (<100 user như ở $K \ge 6$).
  3. **Độ ổn định phân vùng vượt bậc (Partition Stability):**
     - Khi kiểm định tính ổn định bằng chỉ số Adjusted Rand Index (ARI) qua các hạt ngẫu nhiên (`random_state` 42 vs 0 và 7):
       - $\text{ARI}(\text{seed}=42, \text{seed}=0) = \mathbf{0.9949}$
       - $\text{ARI}(\text{seed}=42, \text{seed}=7) = \mathbf{0.9763}$
       - $\text{ARI}(\text{seed}=0, \text{seed}=7) = \mathbf{0.9813}$
     - Trong khi đó, mô hình $K=5$ trên dữ liệu `raw` có $\text{ARI}(\text{seed}=42, \text{seed}=0) = 0.4999$, cho thấy $K=5$ bị chia tách không ổn định, cấu trúc cụm phụ thuộc nhiều vào điểm khởi tạo tâm ngẫu nhiên ban đầu.

### 3.2. Bằng chứng định lượng về "Điểm khuỷu" (Elbow Heuristic)
Khái niệm "điểm khuỷu" (Elbow point) được sử dụng như một **heuristic hỗ trợ định tính** dựa trên tốc độ suy giảm biên của Inertia (SSE), không phải là một định luật suy diễn toán học tuyệt đối:
- $K=2 \to 3$: $\Delta \text{SSE} = 181.02 - 217.77 = -36.75$ (giảm 16.9%)
- $K=3 \to 4$: $\Delta \text{SSE} = 162.99 - 181.02 = -18.04$ (giảm 10.0%)
- $K=4 \to 5$: $\Delta \text{SSE} = 152.14 - 162.99 = -10.85$ (giảm 6.7%)
- $K=5 \to 6$: $\Delta \text{SSE} = 141.74 - 152.14 = -10.40$ (giảm 6.8%)
- $K=6 \to 7$: $\Delta \text{SSE} = 132.01 - 141.74 = -9.73$ (giảm 6.9%)
- $K=7 \to 8$: $\Delta \text{SSE} = 125.50 - 132.01 = -6.51$ (giảm 4.9%)

Số liệu cho thấy mức độ cải thiện biên của SSE giảm mạnh từ $K=2 \to 4$ (giảm $>18$ đơn vị mỗi bước), nhưng từ $K=4 \to 5$ trở đi, mức độ giảm SSE chậm lại rõ rệt (chỉ còn khoảng $6-10$ đơn vị mỗi bước). Quan sát này chứng minh sự đổi hướng rõ nét của độ dốc đường cong Inertia quanh khu vực $K=4$.

### 3.3. Tác động của phép tiền xử lý `StandardScaler`
- Do đặc trưng thể loại nằm trên không gian hình đơn vị xác suất ($\sum p_{u,g} = 1$), các thể loại hiếm trong dữ liệu MovieLens 1M (như Film-Noir, Western, Documentary, Fantasy) có tỷ lệ xuất hiện thấp và độ lệch chuẩn nhỏ ($\sigma_g \ll 1$).
- Khi áp dụng `StandardScaler`, phép chuẩn hóa $z_{u,g} = (p_{u,g} - \mu_g) / \sigma_g$ chia giá trị cho độ lệch chuẩn nhỏ này, làm phương sai của mọi thể loại đều bằng 1. Việc này vô tình **khuếch đại trọng số tương đối của các thể loại hiếm trong khoảng cách Euclidean**, khiến quá trình phân cụm bị chi phối mạnh bởi biến động ở các thể loại ít đánh giá.
- Hệ quả thực nghiệm: Mô hình `StandardScaler` sinh ra các cụm quy mô rất nhỏ (ở $K=8$ có cụm chỉ gồm 5 người dùng) và làm giảm mạnh điểm Silhouette của toàn bộ mô hình (chỉ đạt 0.10 – 0.14). Do đó, giữ nguyên tỷ lệ gốc (`raw`) bảo toàn đúng bản chất tỷ trọng đánh giá thực tế của người dùng.

---

## 4. Diễn Giải Q1: Hồ Sơ Cụm & Phân Tích Tương Quan Nhân Khẩu Học

### 4.1. Hồ sơ 4 nhóm người dùng đánh giá (Sử dụng 100% tỷ lệ gốc)

| Mã cụm | Tên định danh nhóm | Quy mô ($N$) | Tỷ trọng | Thể loại nổi bật nhất (Tỷ lệ trung bình) | Đặc trưng tỷ lệ đánh giá |
| :---: | :--- | :---: | :---: | :--- | :--- |
| **0** | **Nhóm người dùng đánh giá đa dạng / Cân bằng các thể loại** | 2,478 | 41.0% | Drama (17.7%), Comedy (16.2%), Action (10.8%), Thriller (9.7%), Romance (6.6%), Sci-Fi (6.3%) | Tỷ lệ đánh giá tích cực phân bổ đều đặn giữa các thể loại đại chúng, không thiên lệch cực đoan về một thể loại riêng lẻ. |
| **1** | **Nhóm người dùng đánh giá tập trung Drama & Tình cảm** | 1,393 | 23.1% | Drama (**34.3%**), Comedy (14.9%), Romance (**8.4%**), Thriller (8.2%) | Tỷ lệ đánh giá tích cực tập trung áp đảo vào các phim thể loại Drama và Phim tình cảm lãng mạn. |
| **2** | **Nhóm người dùng đánh giá tập trung Hài kịch (Comedy)** | 760 | 12.6% | Comedy (**36.0%**), Drama (16.3%), Romance (11.4%), Action (5.3%) | Tỷ lệ đánh giá tích cực tập trung áp đảo vào thể loại Hài kịch, tỷ lệ đánh giá phim Hành động thấp. |
| **3** | **Nhóm người dùng đánh giá tập trung Hành động, Viễn tưởng & Giật gân** | 1,407 | 23.3% | Action (**20.1%**), Sci-Fi (**13.6%**), Thriller (**11.6%**), Drama (10.4%) | Tỷ lệ đánh giá tích cực tập trung vào các thể loại kịch tính: Hành động, Khoa học viễn tưởng và Giật gân. |

*Lưu ý toán học:* `mean_preference` của từng cụm được tính bằng trung bình số học tỷ lệ gốc của các người dùng trong cụm đó. Tổng `mean_preference` trên 18 thể loại của mỗi cụm bằng chính xác $1.0000000$ (sai số lớn nhất $< 10^{-15} \le 10^{-8}$).

---

### 4.2. Tương quan với Thuộc tính Nhân khẩu học (Descriptive Correlation Only)

Baseline nhân khẩu học được tính toán chính xác trên **đúng 6,038 người dùng đủ điều kiện được phân cụm** (không dùng mặc định toàn bộ 6,040 user vì loại trừ 2 user `insufficient_evidence`):

| Nhóm / Cụm | Tỷ lệ Nam (M) | Tỷ lệ Nữ (F) | Nhóm tuổi chủ đạo | Nhóm tuổi 56+ | Nhóm tuổi < 18 |
| :--- | :---: | :---: | :--- | :---: | :---: |
| **Baseline (6,038 user assigned)** | **71.7%** | **28.3%** | 25-34 (34.7%), 35-44 (19.7%), 18-24 (18.3%) | 6.3% | 3.7% |
| **Cụm 0 (Đánh giá đa dạng)** | 73.7% | 26.3% | 25-34 (36.6%), 35-44 (19.8%), 18-24 (19.9%) | 4.4% | 3.4% |
| **Cụm 1 (Tập trung Drama & Romance)** | 61.2% | **38.8%** | 25-34 (31.2%), 35-44 (19.7%), 18-24 (12.7%) | **12.0%** (gần gấp đôi baseline) | 1.4% |
| **Cụm 2 (Tập trung Comedy)** | 55.1% | **44.9%** | 25-34 (34.1%), 18-24 (20.7%), 35-44 (17.8%) | 5.3% | **7.5%** (gấp đôi baseline) |
| **Cụm 3 (Tập trung Action & Sci-Fi)** | **87.4%** | 12.6% | 25-34 (35.3%), 35-44 (20.8%), 18-24 (19.6%) | 4.4% | 4.3% |

#### Quan sát tương quan thống kê:
1. **Cụm 1 (Drama & Tình cảm):** Tỷ lệ người dùng nữ cao hơn mức nền (38.8% so với 28.3% baseline), đồng thời có sự hiện diện cao hơn của nhóm người lớn tuổi (nhóm 56+ chiếm 12.0% so với 6.3% baseline; nhóm 45-55 chiếm 23.0% so với 17.3% baseline).
2. **Cụm 2 (Comedy):** Tỷ lệ người dùng nữ cao nhất trong 4 cụm (44.9%), đồng thời có tỷ trọng người dùng dưới 18 tuổi cao nhất (7.5% so với 3.7% baseline).
3. **Cụm 3 (Action, Sci-Fi & Thriller):** Thiên lệch mạnh về nam giới (87.4% Nam so với 71.7% baseline), tập trung ở độ tuổi thanh niên và trung niên trẻ (18–34 tuổi chiếm 54.8%).

> [!IMPORTANT]
> **Nguyên tắc khoa học dữ liệu:**
> 1. **Nhân khẩu học chỉ là phân tích mô tả sau phân cụm:** Thuộc tính nhân khẩu học hoàn toàn không tham gia vào quá trình tính khoảng cách hoặc phân cụm. Mối quan hệ giữa nhân khẩu học và phân cụm chỉ là tương quan thống kê mô tả (descriptive correlation) trên tập dữ liệu tĩnh, **tuyệt đối không suy diễn quan hệ nhân quả (causality)** hoặc gán ghép động cơ xem phim.
> 2. **PCA chỉ là phép chiếu minh họa trực quan:** Phép chiếu PCA 2 chiều (giải thích 22.1% + 14.5% = 36.6% tổng phương sai) được dùng thuần túy cho mục đích trực quan hóa trên đồ thị 2D, hoàn toàn không được dùng làm không gian phân cụm.

---

## 5. Quy Cách Đóng Gói Giao Nhận Mốc G3 (`results/mining/handoff/`)

Gói bàn giao G3 được xuất tại thư mục cục bộ `results/mining/handoff/` (ngoài Git) theo đúng Hợp đồng dữ liệu v2:
1. **`user_cluster.csv`:**
   - 6,040 dòng dữ liệu (đủ 100% người dùng trong `users.csv`, sắp xếp theo `user_id` tăng dần).
   - Schema: `user_id,cluster_id,status,model_version`.
   - 6,038 người dùng đủ điều kiện mang `status="assigned"` và `cluster_id` $\in \{0, 1, 2, 3\}$.
   - 2 người dùng thiếu bằng chứng (`user_id` 3598 và 4486) mang `status="insufficient_evidence"` và `cluster_id=""` (NULL).
   - `model_version`: `"kmeans_k4_seed42"`.
2. **`cluster_genre_profile.csv`:**
   - 72 dòng ($4 \text{ cụm} \times 18 \text{ thể loại}$, sắp xếp theo `cluster_id`, `genre_name`).
   - Schema: `cluster_id,genre_name,mean_preference,n_users`.
   - `mean_preference` là trung bình số học tỷ lệ gốc của các user `assigned`.
   - Tổng `mean_preference` mỗi cụm bằng chính xác $1.0$ (sai số $\le 10^{-8}$).
   - `n_users` khớp chính xác với số lượng user được phân vào cụm tương ứng (2478, 1393, 760, 1407).
3. **`manifest.json`:**
   - `contract_version`: 2.
   - `model_version`: `"kmeans_k4_seed42"`.
   - Băm cấu hình huấn luyện `training_config_hash`.
   - Lưu trữ SHA-256 byte của 4 bảng canonical thực tế trên đĩa và của 2 tệp CSV bàn giao.
   - Lưu trữ riêng biệt mã băm SHA-256 của mã nguồn trích xuất đặc trưng (`features_code_sha256`) và mã nguồn phân cụm (`clustering_code_sha256`).

---

## 6. Hướng Dẫn Tái Tạo Cho Người 1 (P1)

Tách biệt rõ ràng giữa lệnh tái tạo cấu hình đã chốt và lệnh chạy thử nghiệm mở rộng:

### Lệnh 1: Tái tạo cấu hình đã chốt (Dành cho P1 để đóng gói/nạp DB mà không cần chọn lại K)
```bash
# Kích hoạt môi trường ảo
source .venv/bin/activate

# Tái tạo trực tiếp gói G3 với cấu hình K=4 đã chốt
python mining/clustering.py --mode reproduce --source csv --outdir results/mining/handoff
```
*Thời gian thực thi:* Khoảng 2–3 giây. Sinh trực tiếp `user_cluster.csv`, `cluster_genre_profile.csv` và `manifest.json`.

### Lệnh 2: Chạy toàn bộ lưới thử nghiệm và sinh báo cáo/biểu đồ (Chế độ nghiên cứu)
```bash
# Chạy toàn bộ 14 cấu hình, kiểm định độ ổn định, xuất biểu đồ và tệp tóm tắt
python mining/clustering.py --mode all --source csv --outdir results/mining/handoff --results-dir results/mining
```

### Lệnh 3: Kiểm thử tự động
```bash
pytest tests/mining/test_clustering.py -v
```

*Giới hạn kỹ thuật:* Quy trình trên đã được kiểm chứng độc lập và tự động hóa 100% trên nguồn dữ liệu CSV chuẩn và dữ liệu gốc thô. Tương tác với PostgreSQL Data Warehouse thực tế chưa được kiểm thử trực tiếp do chưa có kết nối mạng tới DB production.
