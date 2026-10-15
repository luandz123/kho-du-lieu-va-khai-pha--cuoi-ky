# Tiêu chí nghiệm thu nội bộ

> Cập nhật P1-G0-v1 (15/10/2026): S01-v1 được duyệt theo R-P1-01, nguyên văn “Duyệt”. Python3.12 chung và main đã chốt; các nhánh mới bỏ codex/, G0 dùng p1-g0-contract. Phần thân dưới giữ nội dung S01 đã duyệt, các nhãn chờ duyệt là lịch sử. Bản ghi cập nhật G0 đang WAITING_REVIEW; P2 chưa xác nhận contract và chưa merge G0. P2 báo đã có venv3.12.3 và PR môi trường chờ review, chưa phải bằng chứng P1 chạy được.


Phiên bản **P1-S01-v1**, 15/10/2026, **WAITING_REVIEW**. Đọc cùng project_spec.md và shared/data_contract.md (v2). Rubric giảng viên chưa xác minh; dưới đây là tiêu chí nội bộ đề nghị duyệt. Tên sản phẩm là đầu ra tương lai, không xác nhận đã chạy.

## 1. Ba câu hỏi

| Q | Đầu ra | Cách kiểm tra | Bằng chứng cần lưu | Giới hạn |
|---|---|---|---|---|
| Q1 | Feature, bảng thử K/seed/scaler, heatmap/PCA, cơ cấu cụm, gói handoff3 tệp | Tính tay user đa genre, vector tổng1; thiếu tích cực→NULL/status đúng; tuổi/giới không vào feature. K2..8/seed42/n_init10, kiểm seed0/7 cấu hình chọn. Heatmap tỷ lệ gốc; đủ K×genre, tổng profile sai số≤1e-8; một dòng/user, hash/model_version nhất quán | results/mining/: config/nguồn/phiên bản, kmeans_experiments.csv (user,K,seed,scaler,inertia,Silhouette,thời gian), biểu đồ/nhân khẩu học; handoff/manifest | Không ngưỡng Silhouette buộc đạt; PCA minh họa; không nhân quả/thay đổi cùng người theo tuổi |
| Q2 | CF Top5, Popularity Baseline, split/validation/test, metric, CLI | Mốc UTC/timestamp cùng phía; train-only khi validation, train+val khi test. k20/40/80 theo Recall validation, hòa k nhỏ; test 1 lần sau chốt. Cùng user/ứng viên; không phim đã biết/lấy mẫu âm. ≥5history/≥1positive kỳ đánh giá. Tính tay hit/P@5/R@5, giữ phim mới ở mẫu số Recall; fallback và demo nhiều/ít/không seed | results/mining/: split_manifest.json, chọn k/config, metrics.csv (user đủ/bị loại,P@5,R@5,fallback,phim mới,thời gian), recommendations_sample.csv cục bộ, kiểm leakage và demo tách mô hình | Không cần CF thắng baseline; P@5 vẫn chia5 khi trả<5; không tune test/tuyên bố hiệu quả lượt xem |
| Q3 | O4/O5/O6, count/QoQ/tỷ trọng, dashboard Xu hướng | Genre×quý trong biên fact, điền0 trước LAG; prev0→NULL; quý biên đánh dấu; prev<100 không xếp hạng. Kiểm đa genre, mẫu số lượt gắn genre và đối soát tuyệt đối | results/olap/: SQL/kết quả/ca biên; dashboard/: metric/filter, ảnh/export thật, BI–SQL | Không kết luận tăng trưởng quý biên thiếu quan sát, nhu cầu hiện tại/doanh thu; min/max không chứng minh thu thập đầy đủ |

## 2. Nền tảng và tích hợp

| Mã | Điều kiện | Kiểm tra và bằng chứng dự kiến |
|---|---|---|
| ENV | Đúng môi trường riêng, phiên bản chốt hai máy | Runtime/path/requirements theo vai trò/import thật; SELECT1/server_version qua SQL. Readiness/cổng mở không đủ; không log bí mật |
| DATA | Nguồn/canonical giống nhau | source_manifest P2: hash/dòng nguồn; EDA thiếu/trùng/FK/rating/tuổi/genre/năm/min-max; canonical_manifest schema/count/hash/tập mã. P1 tự tải/đối chiếu |
| DW | Grain/khóa/bridge đúng | ERD/từ điển/DDL; PK/FK/CHECK; UNIQUE user–movie sau EDA;4 view đúng cột, không nhân rating với genre |
| ETL | Transaction/rollback/chạy lại đúng | Hai lần nạp tương đương; hash/count/tổng điểm/user-phim/min-max khớp; ca rating sai/FK/trùng xung đột rollback không commit dở; reject/log không bí mật |
| G2 | DW thật trùng EDA | P2 G2-P2 sớm; schema/hash/count/tập mã, đọc4 view trên DW; CSV không thay xác nhận cuối |
| OLAP | O1–O6 đúng | Kết quả KPI/top10/pivot/slice/dice/roll-up/drill-down/lọc; tổng hệ thống từ fact, AVG có trọng số, ca đa genre/quý trống/prev0/quý biên |
| BI | Ba dashboard chạy | Tổng quan/Sở thích/Xu hướng, grain/metric/time/filter đúng;≥3 tổ hợp SQL gồm đa genre; ảnh/export thật, analytics cùng model_version |
| SUPERSET | Môi trường/quyền thật | Linux container/ghim phiên bản/init/health/login/driver; query từ container bằng tài khoản đọc view. Metadata/volume riêng; HTTP200 không đủ chứng minh BI |
| REPRO | Tái lập đúng ứng viên/phục hồi | 12A commit/requirements/config→12-P2 chạy không tune test→12B; pg_dump/restore DW, backup metadata riêng, import dashboard trên phạm vi sạch được phép, đối soát sau phục hồi |
| DOC | Tài liệu khớp kết quả | Báo cáo6 chương, dẫn nguồn/hình/bảng/giới hạn/phân công; README/slide/demo/tập bảo vệ; thời lượng dự kiến không phải rubric |
| GIT | Đúng vai trò/mốc | Diff/stage từng đường dẫn; không user data/bí mật/dump/venv; commit/PR ghi sau thành công; APPROVED riêng MERGED, merge sau xác nhận cụ thể |

## 3. Điều kiện duyệt S01

- [ ] Chốt Q1–Q3/phương pháp/baseline/metric và nghiệm thu.
- [ ] Contract2 MD/JSON đầy đủ; P2 phải xác nhận riêng trước 3-P2.
- [ ] Workflow/quyền file/G0–G5, lịch 15–27/10, chuỗi12A→12-P2→12B được chốt.
- [ ] Chốt hướng Python chung (P1 3.14/P2 3.12.3), PostgreSQL 17.11, Superset 8089 và kế thừa.
- [ ] Hồ sơ mới ghi đúng duyệt S00; không tự duyệt S01/ánh xạ hồ sơ chung.
- [ ] Rubric/tên-MSSV/checkout P2/máy bảo vệ còn thiếu được ghi rõ.

Các ô chưa đánh dấu vì chưa có duyệt S01. Kiểm tra tài liệu không chứng minh ENV/DATA/DW/ETL/ML/BI đạt.
