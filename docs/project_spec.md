# Đặc tả dự án MovieLens 1M

> Cập nhật P1-G0-v1 (15/10/2026): S01-v1 được duyệt theo R-P1-01, nguyên văn “Duyệt”. Python3.12 chung và main đã chốt; các nhánh mới bỏ codex/, G0 dùng p1-g0-contract. Phần thân dưới giữ nội dung S01 đã duyệt, các nhãn chờ duyệt là lịch sử. Bản ghi cập nhật G0 đang WAITING_REVIEW; P2 chưa xác nhận contract và chưa merge G0. P2 báo đã có venv3.12.3 và PR môi trường chờ review, chưa phải bằng chứng P1 chạy được.


Phiên bản **P1-S01-v1**, ngày 15/10/2026 (Asia/Bangkok), **WAITING_REVIEW**. Bảo vệ ngày **27/10/2026**. Đây là đặc tả đề nghị duyệt, không phải báo cáo kết quả đã triển khai.

## 1. Căn cứ và hiện trạng

Nguồn nền: `D:/Downloads/Ke_hoach_BTL_2_nguoi_Superset.docx`. Nguồn quy ước hai vai trò: `D:/Downloads/Bo_prompt_NGUOI_1_DW_ETL_OLAP_Superset_GitHub.docx`, cập nhật 15/10. Prompt trực tiếp của người dùng có ưu tiên; tài liệu không tự cấp quyền chạy bước khác. Rubric chính thức chưa xác minh; acceptance.md là tiêu chí nội bộ.

Workspace P1: `D:/kho-du-lieu-va-khai-pha--cuoi-ky`. Checkout có main/b7698b2 và remote cấu hình https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky.git; quyền GitHub chưa kiểm tra. Bản cũ `D:/BTL_Kho_Du_Lieu` giữ nguyên, hồ sơ chung chỉ đọc, chưa ánh xạ hoặc chuyển lời duyệt sang hồ sơ P1 mới.

S00 được duyệt bằng nguyên văn “duyệt bước 0”. P2 cung cấp Linux/Python 3.12.3/GCC 13.3.0 trong chat S01; chưa xác minh đường dẫn, checkout riêng hoặc dependency P2. Đây là thông tin môi trường, không phải duyệt S01/hợp đồng.

## 2. Câu hỏi và luồng bằng chứng

| Câu hỏi | Nội dung | DW, phân tích và đầu ra |
|---|---|---|
| Q1 | Có những nhóm sở thích nào; cơ cấu tuổi/giới giữa các nhóm khác nhau ra sao trong dữ liệu lịch sử? | Bốn view → vector tỷ lệ genre tích cực → K-Means → gói cụm có phiên bản → analytics → dashboard Sở thích |
| Q2 | Gợi ý Top 5 phim theo lịch sử đánh giá như thế nào? | Rating từ DW → chia thời gian → item-based CF và Popularity Baseline → Precision@5/Recall@5 → bảng thực nghiệm và CLI |
| Q3 | Số lượt đánh giá theo thể loại tăng trưởng thế nào qua các quý trong kỳ dữ liệu? | Fact/bridge → O4/O5/O6 → count, QoQ, tỷ trọng → dashboard Xu hướng |

Rating là đánh giá, timestamp là thời điểm đánh giá. Không suy luận lượt xem/thời lượng xem, sở thích cùng một người đổi theo tuổi, nhu cầu hiện tại, doanh thu hoặc thông tin đạo diễn/diễn viên.

## 3. Phạm vi và sản phẩm

Bắt buộc: MovieLens 1M; PostgreSQL staging/DW; Python ETL có đối soát, rollback và chạy lại; 6 OLAP; K-Means Q1; item-based CF Top 5, Popularity Baseline và đánh giá Q2; 3 dashboard Superset; báo cáo, slide, demo, hướng dẫn tái lập/phục hồi.

Loại trừ: Apriori/luật kết hợp, Power BI, website sản phẩm, streaming, học sâu, ghép đạo diễn/diễn viên, SCD Type 2 và ETL tăng dần. Giao diện Superset phục vụ BI nội bộ thuộc phạm vi.

| Nhóm | Đầu ra dự kiến, chưa phải xác nhận tệp đã tồn tại |
|---|---|
| DW/ETL | database/: schema/view/ERD/từ điển; etl/: pipeline/log; tests/warehouse/; results/warehouse/ |
| OLAP | olap/: O1–O6/view; results/olap/: kết quả và đối soát |
| Khai phá P2 | mining/, tests/mining/, results/eda/, results/mining/: EDA/adapter/manifest, K-Means, CF/baseline/metric, CLI và gói cụm |
| BI | dashboard/: cấu hình ghim phiên bản, dataset/metric, 3 dashboard, ảnh và export thật |
| Tài liệu | docs/bao_cao_BTL.docx, docs/slide_BTL.pptx, report_outline.md, slide_outline.md, integration_checklist.md, demo_script.md và README |

## 4. Dữ liệu, DW và ETL

Nguồn users.dat/movies.dat/ratings.dat; mỗi máy tự tải từ GroupLens và so hash, không phân phối dữ liệu qua Git. Số 1.000.209 rating/6.040 user trong kế hoạch là kỳ vọng, chưa phải kết quả chạy. Số phim, khoảng thời gian, trùng, mã và khóa phải xác minh bằng EDA. Tuân thủ [hợp đồng v2](shared/data_contract.md) và JSON tương ứng; hai người xác nhận trước 3-P2.

Grain fact_rating là một bản ghi đánh giá nguồn. Dimension user/movie/date/genre dùng surrogate key trong DW, giữ ID nguồn. Bridge movie–genre biểu diễn phim nhiều thể loại. UNIQUE user–movie chỉ sau EDA; CHECK rating 1..5; FK hợp lệ; UTC thống nhất. Bốn view hợp đồng không nối genre vào ratings.

Full refresh theo lô, transaction/kiểm tra trước commit, rollback khi lỗi. Trùng/lỗi nguồn cần chính sách chung, không tự loại/gộp. Đối soát nguồn–canonical–DW bằng hash byte CSV chuẩn, count, tổng điểm, user/phim có rating, min/max timestamp và khóa. Hai lần nạp phải cho nội dung tương đương. Không drop database ngoài phạm vi.

## 5. OLAP và dashboard

| Mã | Phân tích |
|---|---|
| O1 | KPI user/phim danh mục và có rating; tổng rating; điểm trung bình |
| O2 | Top 10 phim theo số rating, kèm điểm trung bình |
| O3 | Điểm trung bình/count theo genre × nhóm tuổi; lọc giới tính; pivot/slice/dice |
| O4 | Count năm → quý → tháng; roll-up/drill-down |
| O5 | Count, QoQ và tỷ trọng genre theo quý |
| O6 | Lọc genre, nhóm tuổi, thời kỳ; đi sâu tháng/phim |

Tổng hệ thống lấy từ fact, không cộng count các genre. AVG = SUM(rating)/COUNT; không trung bình không trọng số của trung bình nhóm. QoQ = 100 × (n_t − n_prev)/n_prev; lưới genre × quý trong biên fact, điền 0 trước LAG; prev=0 → NULL/N/A. Đánh dấu quý biên thiếu quan sát, không dùng kết luận tăng trưởng quý đầy đủ. Chỉ xếp hạng tăng trưởng khi quý trước có ít nhất 100 rating genre. Tỷ trọng chia tổng lượt gắn genre trong quý, khác rating duy nhất; luôn hiển thị số tuyệt đối. Min/max không chứng minh mọi quý thu thập đầy đủ.

- Tổng quan: KPI, Top 10, phân bố sao, lọc thời gian; tách danh mục với phim có rating.
- Sở thích: quy mô cụm, heatmap tỷ lệ gốc, cơ cấu tuổi/giới so với toàn bộ user đủ điều kiện, lọc cụm.
- Xu hướng: count quý, QoQ/tỷ trọng, nhãn quý biên, lọc thời gian/genre.

View xử lý join/bridge, mỗi dataset ghi grain/metric/time grain/native filter. Đối soát ít nhất 3 tổ hợp SQL gồm phim nhiều genre. Metadata Superset tách DW, volume bền vững; dùng tài khoản đọc view và query thật từ container. localhost container không phải Windows host. Export/import thật trên instance sạch được phép; ảnh/video chỉ dự phòng.

## 6. Q1 K-Means

Rating ≥4 là tích cực. Mỗi user đếm lượt gắn genre phim tích cực/chia tổng lượt gắn, vector tổng 1. Zero là chưa có bằng chứng, không là điểm 0. Không có tích cực → insufficient_evidence/cluster_id NULL, không chia 0. Tuổi/giới không làm feature, chỉ ghép sau phân cụm.

So sánh tỷ lệ gốc/StandardScaler; K=2..8, random_state=42, n_init=10. Chọn theo inertia/Silhouette trên cùng dữ liệu, quy mô/khả năng diễn giải; kiểm seed 0/7 cho cấu hình chọn. PCA 2D chỉ minh họa; heatmap dùng tỷ lệ gốc kể cả mô hình chuẩn hóa. Không ngưỡng Silhouette buộc đạt. Q1 toàn lịch sử độc lập Q2; không đưa cụm toàn lịch sử vào đánh giá Q2.

## 7. Q2 CF và đánh giá

Ma trận thưa phim × user từ rating lịch sử huấn luyện; cosine, bỏ self-similarity, chỉ similarity >0. Seed là phim rating ≥4 trong lịch sử được phép dùng. Điểm ứng viên i = tổng similarity(i,j) với i nằm trong k láng giềng của seed j; là điểm xếp hạng, không phải sao dự đoán. Hòa: phổ biến trong lịch sử huấn luyện rồi movie_id tăng. Loại phim đã đánh giá; thiếu seed/ứng viên thì bổ sung phim phổ biến chưa biết và báo tỷ lệ fallback. Baseline riêng: Top 5 theo count rating lịch sử huấn luyện, hòa movie_id.

Mốc chung t1/t2 khoảng phân vị 70%/85% timestamp: train ≤t1, validation (t1,t2], test >t2; timestamp bằng nhau cùng phía. Lưu mốc UTC/count/tỷ lệ thật. k={20,40,80}, chọn Recall@5 validation, hòa k nhỏ. Chốt rồi xây lại trên train+validation, test một lần. Validation chỉ dùng train; test dùng train+validation cho similarity/seed/popularity. Không tune test khi tái lập.

User đủ điều kiện: ≥5 rating lịch sử huấn luyện, ≥1 phim rating ≥4 kỳ đánh giá. Cùng user/ứng viên giữa CF và baseline; toàn bộ phim huấn luyện trừ lịch sử, không lấy mẫu âm. Phim mới chỉ có ở kỳ đánh giá vẫn trong mẫu số Recall và báo tỷ lệ. Precision@5=hit/5 kể cả trả <5; Recall@5=hit/số phim yêu thích kỳ đánh giá; trung bình user không trọng số. Demo toàn lịch sử tách mô hình đánh giá, gồm nhiều/ít/không seed. CF không bắt buộc thắng baseline; báo thật và giải thích.

## 8. Công nghệ và điều chỉnh cần chốt

| Thành phần | Hiện trạng | Đề nghị chờ duyệt |
|---|---|---|
| PostgreSQL | P1 17.11, service/readiness đạt; SQL hiện tại chưa xác minh | Dùng 17.11 thay 15/16 ghi trong nền; kiểm SQL/quyền tại setup |
| Python | P1 3.14.0; P2 tự báo Linux 3.12.3/GCC13.3.0 | Dòng Python 3.12 chung tại G0; kiểm thư viện hai máy. P1 chưa xác minh có 3.12, chưa cài; runtime toàn hệ thống cần giao riêng. Chưa chốt patch hoặc pin |
| Superset | Cũ 3.1.0/8088 healthy; dự án 6.1.0-local/8089 stopped tại S00 | Kiểm tra/kế thừa chọn lọc dự án8089, ghim phiên bản, giữ 8088; không coi bản cũ đã nghiệm thu |
| Tài nguyên | RAM15,67GiB, trống5,71→2,47GiB; C33,31/D88,52GiB trống | Nặng chạy lần lượt, thưa/theo lô, đo thực tế. Không tự tắt dịch vụ, lọc phim, giảm K/lấy mẫu Silhouette |
| Hồ sơ | Checkout mới có lịch sử, bản cũ chưa commit | Kế thừa chọn lọc, chưa ánh xạ hồ sơ chung khi nhóm chưa chốt |

## 9. Vai trò và phụ thuộc

P1 chủ trì DW/ETL/OLAP/Superset, phần dữ liệu/kho và ghép tổng. P2 chủ trì EDA/adapter/K-Means/CF/baseline/metric/CLI và phần khai phá. Cả hai kiểm tra chéo, tái lập và tổng duyệt. Tên/MSSV/checkout P2/máy bảo vệ chưa xác minh. Quyền file tại [workflow](shared/github_workflow.md).

| Bước/mốc | Tiền đề và bàn giao |
|---|---|
| S01 → G0 | S00 APPROVED, thông tin runtime P2 đã tự báo; S01 chờ duyệt. G0 sau duyệt/giao riêng; thống nhất Python/contract; nhánh/PR vì remote có lịch sử |
| 2-P1 / 2-P2 / 3-P2 | 2-P1 sau G0; P2 chuẩn bị Python độc lập. 3-P2 chỉ sau cả hai xác nhận contract, không chờ Docker P1 |
| G1 → 4 → 5-P1 | EDA/adapter/manifest G1 duyệt và merge, 2-P1 đạt; schema rồi staging, duyệt từng bước |
| 6A→6B→6C→6D / G2 | Duyệt từng phần; gói DW/view/manifest; P2 chạy G2-P2 sớm, P1 tiếp OLAP |
| 8–10-P2 / G3 | Sau G1 phát triển qua adapter, cuối cùng xác nhận DW qua G2-P2; cụm sau 8B bàn giao trước CF sau 10 |
| 7 / 11-P1 | 7 sau 6D; 11A Tổng quan/11C Xu hướng sau 7; 11B Sở thích cần gói cụm8B/G3 đúng hash/version được duyệt, không chờ CF |
| 12A-P1→12-P2→12B-P1 / G4 | PR chức năng merge → ứng viên/requirements tổng → P2 tái lập đúng commit → báo cáo P2 duyệt/merge → P1 chốt; không chờ vòng |
| 13A→13 / G5 | Sau12B duyệt/merge: dàn ý; P1 chương 1/3/4, P2 phần khai phá được giao; duyệt/merge từng phần trước ghép |
| 14 / G5 | Sau duyệt báo cáo; 14A bàn giao dàn ý sớm; slide/demo/tổng duyệt/tag sau nghiệm thu và xác nhận cụ thể |

APPROVED chức năng khác PR MERGED. Chỉ đợi tiền đề bước được giao; lịch không cấp quyền tự chuyển bước.

## 10. Lịch mục tiêu

| Ngày 2026 | Mục tiêu, chưa phải kết quả |
|---|---|
| 15–16/10 | Kiểm kê, S01, G0, môi trường/EDA |
| 17–19/10 | DW/ETL, K-Means/CF, G2/G3 |
| 20–21/10 | OLAP, Superset, đối soát |
| 22–23/10 | 12A → 12-P2 → 12B |
| 24–25/10 | Báo cáo và slide |
| 26/10 | Tái lập/phục hồi, tổng duyệt, tag sau nghiệm thu |
| 27/10 | Bảo vệ |

Lịch mới từ tài liệu P1 15/10 thay lịch mục tiêu nền bắt đầu13/10, trình duyệt phiên bản này; không sửa nguồn gốc. Nếu trễ, giữ tính đúng/baseline/metric/tích hợp; không tự bỏ sản phẩm. Báo cáo6 chương theo nền; demo khoảng9 phút là dự kiến, thời lượng chính thức chưa xác minh.

Cần chốt S01: đặc tả/nghiệm thu, contract v2/workflow, PostgreSQL 17.11, Python chung/cách chuẩn bị P1, Superset 8089, lịch/điểm đồng bộ và cách kế thừa/ánh xạ bản cũ. P2 xác nhận contract riêng trước EDA, không suy từ duyệt P1.
