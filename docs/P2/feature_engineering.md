# Đặc tả Kỹ thuật Đặc trưng Phân cụm Người dùng (Tiểu bước 8A - Q1)

Tài liệu này đặc tả quy trình và công thức trích xuất vector đặc trưng sở thích thể loại của người dùng (User Genre Preference Vectors) phục vụ bài toán phân cụm Q1 theo Data Contract v2 và bộ prompt Người 2.

---

## 1. Mục tiêu và Nguyên tắc Thiết kế (Scope & Invariants)

1. **Phạm vi Q1:**
   - Vector đặc trưng được trích xuất trên toàn bộ lịch sử tương tác để phục vụ phân cụm mô tả (descriptive clustering) người dùng.
   - **Tuyệt đối không rò rỉ (No Data Leakage):** Không đưa đặc trưng phân cụm này hay nhãn cụm ($cluster\_id$) vào tập dữ liệu huấn luyện hoặc đánh giá của bài toán Q2 (Collaborative Filtering / Matrix Factorization).
2. **Không phân biệt đối xử (Fairness & Content-First):**
   - Vector đặc trưng chỉ chứa phân phối sở thích thể loại phim dựa trên đánh giá tích cực.
   - **Tuyệt đối không đưa thuộc tính nhân khẩu học** (`age_group`, `gender`, `occupation`, `zip_code`) vào vector đặc trưng phân cụm.
3. **Thứ tự không gian đặc trưng:**
   - Không gian đặc trưng gồm đúng 18 chiều tương ứng với 18 thể loại phim duy nhất trong MovieLens 1M, sắp xếp theo thứ tự bảng chữ cái chuẩn A–Z:
     1. Action
     2. Adventure
     3. Animation
     4. Children's
     5. Comedy
     6. Crime
     7. Documentary
     8. Drama
     9. Fantasy
     10. Film-Noir
     11. Horror
     12. Musical
     13. Mystery
     14. Romance
     15. Sci-Fi
     16. Thriller
     17. War
     18. Western

---

## 2. Công thức Toán học và Chuẩn hóa

### 2.1. Lọc phản hồi tích cực
Tương tác đánh giá của người dùng $u$ cho phim $m$ có điểm đánh giá $r_{u, m} \in \{1, 2, 3, 4, 5\}$.
Tập hợp các phim được người dùng $u$ đánh giá tích cực ($\ge 4$) được định nghĩa:
$$\mathcal{M}_{u, \ge 4} = \{ m \in \mathcal{M} \mid r_{u, m} \ge 4 \}$$

### 2.2. Xử lý phim đa thể loại (Multi-genre Expansion)
Mỗi phim $m$ có một tập hợp các thể loại $\mathcal{G}_m \subseteq \mathcal{G}$, với $|\mathcal{G}_m| \ge 1$.
Khi người dùng $u$ đánh giá tích cực một bộ phim có $M$ thể loại, sự kiện này được tính là $M$ lượt gắn thể loại tích cực (positive genre associations).

Số lượt gắn thể loại $g$ của người dùng $u$:
$$C_{u, g} = \sum_{m \in \mathcal{M}_{u, \ge 4}} \mathbb{I}(g \in \mathcal{G}_m)$$
với $\mathbb{I}(\cdot)$ là hàm chỉ thị (indicator function).

Tổng số lượt gắn thể loại tích cực của người dùng $u$:
$$S_u = \sum_{g \in \mathcal{G}} C_{u, g} = \sum_{m \in \mathcal{M}_{u, \ge 4}} |\mathcal{G}_m|$$

### 2.3. Chuẩn hóa Vector xác suất (L1 Normalization)
Với người dùng có ít nhất một đánh giá tích cực ($S_u > 0$), thành phần thứ $g$ của vector đặc trưng $\mathbf{p}_u = (p_{u, 1}, p_{u, 2}, \dots, p_{u, 18})$ là tần suất tương đối:
$$p_{u, g} = \frac{C_{u, g}}{S_u}$$

Các ràng buộc toán học bất biến:
- $p_{u, g} \ge 0 \quad \forall g \in \mathcal{G}$ (Không âm)
- $\sum_{g \in \mathcal{G}} p_{u, g} = 1.0$ (Tổng bằng 1 trong sai số cho phép $\epsilon = 10^{-8}$)
- Trạng thái phân loại: $status = \text{"assigned"}$

### 2.4. Xử lý Người dùng Thiếu bằng chứng (Insufficient Evidence)
Với người dùng không có đánh giá tích cực nào ($|\mathcal{M}_{u, \ge 4}| = 0 \implies S_u = 0$):
- Trạng thái phân loại: $status = \text{"insufficient\_evidence"}$
- Nhãn phân cụm: $cluster\_id = \text{NULL}$
- **Quy tắc an toàn:** Không thực hiện phép chia cho $S_u$ (chống lỗi $ZeroDivisionError$).
- **Quy tắc dữ liệu:** Không tạo vector số 0 hoặc vector rỗng để đưa vào ma trận huấn luyện phân cụm. Người dùng mang trạng thái này được lưu riêng vào danh sách theo dõi cục bộ.

---

## 3. Ví dụ Tính tay trên Dữ liệu Mẫu (Synthetic Fixture Walkthrough)

Xem xét bộ dữ liệu nhỏ kiểm chứng (fixture) độc lập gồm 3 người dùng, 3 bộ phim và bảng thể loại:

### Dữ liệu vào
- **Phim và thể loại:**
  - $M_1$: Animation, Children's, Comedy ($|\mathcal{G}_{M_1}| = 3$)
  - $M_2$: Adventure, Children's, Fantasy ($|\mathcal{G}_{M_2}| = 3$)
  - $M_3$: Action, Crime, Thriller ($|\mathcal{G}_{M_3}| = 3$)
- **Đánh giá:**
  - Người dùng $U_1$:
    - $(U_1, M_1, \text{rating}=5) \implies$ Tích cực ($\ge 4$)
    - $(U_1, M_2, \text{rating}=4) \implies$ Tích cực ($\ge 4$)
    - $(U_1, M_3, \text{rating}=2) \implies$ Tiêu cực ($< 4$, loại bỏ)
  - Người dùng $U_2$:
    - $(U_2, M_3, \text{rating}=4) \implies$ Tích cực ($\ge 4$)
  - Người dùng $U_3$:
    - $(U_3, M_1, \text{rating}=3) \implies < 4$
    - $(U_3, M_2, \text{rating}=2) \implies < 4$
    - $(U_3, M_3, \text{rating}=1) \implies < 4$

### Quá trình tính toán chi tiết
1. **Người dùng $U_1$:**
   - Phim tích cực: $\{M_1, M_2\}$
   - Lượt gắn thể loại tích cực:
     - $M_1 \implies$ Animation (+1), Children's (+1), Comedy (+1)
     - $M_2 \implies$ Adventure (+1), Children's (+1), Fantasy (+1)
   - Đếm tổng số lượt:
     - Adventure: 1
     - Animation: 1
     - Children's: 2
     - Comedy: 1
     - Fantasy: 1
     - Các thể loại khác: 0
   - Tổng lượt gắn $S_{U_1} = 1 + 1 + 2 + 1 + 1 = 6$.
   - Chuẩn hóa:
     $$p_{U_1, \text{Adventure}} = \frac{1}{6} \approx 0.1666667$$
     $$p_{U_1, \text{Animation}} = \frac{1}{6} \approx 0.1666667$$
     $$p_{U_1, \text{Children's}} = \frac{2}{6} \approx 0.3333333$$
     $$p_{U_1, \text{Comedy}} = \frac{1}{6} \approx 0.1666667$$
     $$p_{U_1, \text{Fantasy}} = \frac{1}{6} \approx 0.1666667$$
   - Tổng vector: $0.1666667 \times 4 + 0.3333333 = 1.0000000$.
   - Trạng thái: `status = "assigned"`.

2. **Người dùng $U_2$:**
   - Phim tích cực: $\{M_3\}$
   - Lượt gắn thể loại tích cực: Action (+1), Crime (+1), Thriller (+1).
   - Tổng lượt gắn $S_{U_2} = 3$.
   - Chuẩn hóa:
     $$p_{U_2, \text{Action}} = \frac{1}{3} \approx 0.3333333$$
     $$p_{U_2, \text{Crime}} = \frac{1}{3} \approx 0.3333333$$
     $$p_{U_2, \text{Thriller}} = \frac{1}{3} \approx 0.3333333$$
   - Tổng vector: $1.0000000$.
   - Trạng thái: `status = "assigned"`.

3. **Người dùng $U_3$:**
   - Phim tích cực: $\emptyset$ ($S_{U_3} = 0$).
   - Phân loại: `status = "insufficient_evidence"`.
   - Xử lý: Không tính vector đặc trưng, không chia cho 0, không đưa vào ma trận đặc trưng huấn luyện.

---

## 4. Kết quả Thực tế trên Dữ liệu Chuẩn MovieLens 1M

Khi chạy thuật toán trích xuất trên toàn bộ dữ liệu MovieLens 1M đã chuẩn hóa:
- **Tổng số người dùng trong hệ thống:** 6,040
- **Số người dùng đủ điều kiện (`assigned`):** 6,038
- **Số người dùng thiếu bằng chứng (`insufficient_evidence`):** 2
- **Kích thước ma trận đặc trưng:** `(6038, 18)`
- **Tổng số tương tác đánh giá tích cực ($\ge 4$):** 575,281
- **Tổng số lượt gắn thể loại tích cực:** 1,206,999 (trung bình $\approx 2.098$ thể loại/phim)
- **Kiểm định tính hợp lệ của ma trận đặc trưng:**
  - Giá trị nhỏ nhất: $0.0$
  - Giá trị lớn nhất: $\approx 0.7142857$
  - Giá trị hữu hạn (không chứa NaN, Inf): $100\%$
  - Độ lệch lớn nhất của tổng hàng so với $1.0$: $4.44089 \times 10^{-16} \le 10^{-8}$
  - Thứ tự 18 cột: Hoàn toàn khớp với danh sách thể loại từ A–Z.

---

## 5. Chính sách Quản lý Dữ liệu và Bảo mật Thông tin

1. **Không đẩy dữ liệu người dùng cá nhân lên Git:**
   - Các file trích xuất thực tế gồm ma trận đặc trưng (`user_features.parquet`, `user_features.csv`) và danh sách trạng thái người dùng (`user_status.csv`) được lưu trong thư mục `data/features/`.
   - Thư mục này nằm ngoài Git theo cấu hình `.gitignore` (`**/features/`, `*.parquet`, `*.csv`).
   - Tài liệu này và các báo cáo Git chỉ sử dụng số liệu tổng hợp (aggregate metrics) và ví dụ mẫu tự tạo (synthetic fixture), không chứa `user_id` hay lịch sử đánh giá cá nhân của người dùng thật.
2. **Khả năng tái lập (Reproducibility):**
   - Đảm bảo trích xuất từ dữ liệu nguồn thô (`data/raw/ml-1m/`) và từ dữ liệu chuẩn (`data/processed/*.csv`) qua adapter `mining/data_io.py` cho kết quả ma trận giống nhau tuyệt đối.

---

## 6. Bảo Toàn Khóa, Định Dạng & Khả Năng Truy Vết

1. **Khóa liên kết `user_id` (Key Alignment):**
   - Hàng trong ma trận đặc trưng được định danh bởi chỉ mục `user_id`, sắp xếp tăng dần tuyệt đối (`is_monotonic_increasing`).
   - Đảm bảo khi ánh xạ kết quả phân cụm K-Means ở bước 8B, các nhãn cụm gắn chính xác 1-1 với từng người dùng mà không bị lệch dòng.
   - Chưa gán `cluster_id` hay `model_version` ở tiểu bước 8A.
2. **Định dạng tệp & Phụ thuộc thư viện (Dependency Policy):**
   - Định dạng chuẩn bắt buộc: CSV chuẩn hóa (`user_features.csv`, `user_status.csv`).
   - Định dạng Parquet (`user_features.parquet`): Là tùy chọn phụ (optional optimization). Thư viện `pyarrow` không cài mặc định trong môi trường tối thiểu; module sẽ tự động bỏ qua xuất Parquet nếu thiếu dependency mà không gây lỗi chương trình.
3. **Lưu vết cấu hình & Mã băm nguồn (Traceability):**
   - Mỗi lần trích xuất đặc trưng, tệp siêu dữ liệu `data/features/feature_summary.json` (cục bộ) lưu lại:
     - Danh sách 18 thể loại theo thứ tự A–Z.
     - Ngưỡng đánh giá tích cực (`positive_threshold = 4`).
     - Sai số cho phép (`tolerance = 1e-8`) và độ lệch thực tế lớn nhất.
     - Nguồn dữ liệu sử dụng (`raw` hoặc `csv`).
     - SHA-256 của 4 bảng canonical từ `canonical_manifest.json` và commit mã nguồn `source_code_commit`.

