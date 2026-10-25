# Dàn ý báo cáo chung — chuẩn bị 13A v1

## Hiện hành sau nghiệm thu G4 — 24/10/2026

Điều phối đã nghiệm thu 12-P2 và12B, xác nhận **G4 ĐẠT** trong phạm vi I01–I15. PR30 MERGED `67fd9eb6b98211485b713c99e829291bc3b50f57`; candidate thực chạy vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. P2 intakeG2CONFIRMED trên Windows/Python3.12.6/PG17.4; P1 Windows/Python3.12.14/PG17.11. Không kiểm Linux/SupersetP2 hoặc phục hồi toàn stack máy mới. [Ma trận nghiệm thu](P1/integration_acceptance.md), [ghi nhận mới](P1/g4_acceptance_20261024.json).

Các đoạn chờ P2/G4 bên dưới là snapshot lập dàn ý/chỉ mục trước nghiệm thu; không dùng làm trạng thái hiện hành. Nguồn bổ sung cho các mục E18/E20 và kết luận chương1/3/4/6 là ma trận/ghi nhận mới nêu trên. Chưa nhận đủ chương 2/5/6 P2 được duyệt để ghép; G5 chưa hoàn thành.

## Cập nhật hiện hành 24/10/2026 — dàn ý được điều phối duyệt

Điều phối duyệt dàn ý13A và danh mục bằng chứng, giao công bố riêng trước khi viết bản thảo P1 chương1/3/4. P2 **đã báo G2 CONFIRMED**, tái lập candidate `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` trên máy Windows độc lập, Python3.12.6/PostgreSQL17.4. Nguồn là thông điệp điều phối qua người dùng, bằng chứng công bố của P2 **đang chờ điều phối review**; P1 chưa kiểm độc lập lượt P2. Không ghi đã kiểmLinux, **G4 chưa hoàn thành**. Chi tiết nguồn ở `docs/P1/p2_intake_reported_20261024.json`. Các mụcNOT_CONFIRMED/WAITING_REVIEW/OPEN bên dưới và audit13A là snapshot lịch sử, không sửa thành bằng chứng mới.

Thiếu rubric/mẫu chính thức không chặn bản thảo; không tự áp số trang/thể thức bắt buộc. Dàn ý được duyệt khác PR đãmerge; bản thảo chương chỉWAITING_REVIEW, không ghép vào PR dàn ý, khôngDOCX/slide. Không pipeline/evaluator hoặc đổi tài nguyên.

Ngày 23/10/2026. **WAITING_REVIEW**. Bảo vệ 27/10/2026.

Điều phối giao chuẩn bị dàn ý song song với 12-P2, sớm hơn thứ tự nền 12B → 13A. Đây chỉ là điều chỉnh cho phần chuẩn bị tài liệu; không thay điều kiện nghiệm thu G4 hoặc cho phép viết/ghép báo cáo cuối. PR25 đã MERGED tại `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`; đây là candidate đang được P2 kiểm nhận, chưa phải kết quả tích hợp hai máy đã nghiệm thu. P2 intake G2 = **NOT_CONFIRMED**. Quan sát API mới: `P1/pr25_merged_observation.json`; các báo cáo OPEN và receipt cũ giữ nguyên.

## Căn cứ, phân công và quy tắc dùng nguồn

- Đặc tả: `project_spec.md`; tiêu chí nội bộ: `acceptance.md`; hợp đồng v2: `shared/data_contract.md` và `.json`; quyền sở hữu: `shared/github_workflow.md`.
- Kế hoạch nền đọc tại `docs/KE_HOACH_BTL_MOVIELENS.md` cục bộ, ngoài phạm vi Git: tài liệu tham khảo, không là bằng chứng hoàn thành hoặc rubric. Nếu máy nhận không có file này, dùng đặc tả và dàn ý hiện tại để theo dõi phân công.
- Bộ prompt P1 được đọc từ file Word người dùng cung cấp; nội dung đó là tài liệu tham khảo, quyền thực thi theo lệnh điều phối hiện hành. Rubric/mẫu báo cáo/thời lượng chính thức của giảng viên chưa được xác minh bằng tài liệu trong repository. Không trình tiêu chí nội bộ thành yêu cầu chính thức.
- P1 viết chương **1, 3, 4**; P2 viết chương **2, 5, 6**. P1 tổng hợp bản cuối sau khi hai phần được duyệt. Lượt này chưa tạo file phần P2, DOCX hoặc slide.
- Mỗi số liệu/kết luận dẫn mã E trong `P1/report_evidence_index.md`. Ưu tiên dữ liệu máy đọc được và receipt; dùng văn bản diễn giải làm ngữ cảnh. Giữ run/commit/hash thực chạy tách commit công bố và candidate.

## Chương 1 — Bài toán, mục tiêu và phạm vi (P1)

**Mục tiêu:** xác định nhóm giải quyết việc gì và giới hạn kết luận.

**Các mục và nội dung:** 1.1 bối cảnh phân tích dữ liệu đánh giá phim lịch sử; 1.2 Q1 nhóm sở thích và cơ cấu tuổi/giới, Q2 gợi ý Top 5, Q3 số đánh giá theo quý; 1.3 phạm vi MovieLens 1M/PostgreSQL/Python/Superset, sản phẩm bắt buộc; 1.4 vai trò hai thành viên và luồng G0–G5; 1.5 tiêu chí nội bộ và cách kiểm chứng. Không thêm Apriori, Power BI, website, streaming, đạo diễn/diễn viên.

**Bảng/hình:** B1 ma trận Q → phương pháp → đầu ra → bằng chứng; B2 phân công và trạng thái mốc. H1 sơ đồ luồng nguồn → staging → DW → OLAP/ML → BI dự kiến biên tập từ kiến trúc đã có, chưa là hình mới đã tạo.

**Nguồn:** `project_spec.md`, `acceptance.md`, `shared/github_workflow.md`, `P1/integration_prep/component_inventory.json`, E01/E18.

**Còn chờ P2:** kết quả tái lập candidate, giới hạn môi trường và kết luận G4 qua 12B; chưa ghi dự án hoàn tất.

## Chương 2 — Cơ sở lý thuyết và phương pháp (P2)

**Mục tiêu:** giải thích vì sao chọn DW/OLAP, K-Means và item-based CF, cùng định nghĩa đánh giá.

**Các mục và nội dung:** 2.1 staging, mô hình sao, grain, fact/dimension/bridge; 2.2 ETL theo lô, transaction, đối soát và rollback; 2.3 roll-up, drill-down, slice, dice, pivot; 2.4 K-Means trên tỷ lệ genre tích cực, inertia/Silhouette/ARI, PCA chỉ minh họa; 2.5 cosine item-based, láng giềng dương, điểm xếp hạng, Popularity Baseline và fallback; 2.6 chia thời gian, tránh leakage, macro Precision@5/Recall@5 và cold start. Công thức phải thống nhất code, không gọi score CF là sao dự đoán. Bổ sung trích dẫn học thuật/tài liệu chính thức khi viết chương, chưa coi danh mục tham khảo đã hoàn chỉnh.

**Bảng/hình:** B3 định nghĩa chỉ số và mẫu số; ví dụ tính tay bằng fixture tự tạo cho phim hai genre, vector sở thích và hit@5; sơ đồ split tham chiếu manifest, chưa dùng lịch sử user thật.

**Nguồn:** `P2/feature_engineering.md`, `P2/evaluation_protocol.md`, `mining/` (tính từ root), `shared/data_contract.md`, E04/E12/E14.

**Còn chờ P2:** xác nhận diễn giải khớp phiên bản candidate và tài liệu chương 2 được duyệt; không thay thuật toán/metric đã chốt.

## Chương 3 — Dữ liệu, EDA và thiết kế kho (P1)

**Mục tiêu:** nối số đo EDA thực tế của P2 với quyết định thiết kế có thể kiểm chứng.

**Các mục và nội dung:** 3.1 nguồn GroupLens, provenance/hash, Latin-1 và dấu `::`; 3.2 EDA: count, miền, thiếu/trùng, FK, đa genre, khoảng UTC; 3.3 hợp đồng bốn bảng logic/serializer v2 và ID nguồn; 3.4 staging/dw/analytics, bốn dimension, bridge và fact grain một đánh giá; 3.5 PK/FK/UNIQUE user–movie dựa EDA, CHECK/nullability/index; 3.6 bốn view giao tiếp, registry/version và hai bảng kết quả cụm. Năm không khớp ngoặc cuối → NULL là quy tắc thiết kế; phân biệt với số NULL thực tế của snapshot.

**Bảng/hình:** B4 thống kê nguồn/canonical (không tính header vào row_count); B5 chất lượng/khóa/FK; B6 từ điển tóm tắt và source–target mapping; H2 ERD chỉnh sửa được; H3 phân bố sao và H4 hoạt động theo quý từ EDA.

**Nguồn:** `../data/source_manifest.json`, `../results/eda/data_profile.csv`, `P2/data_understanding.md`, `../results/eda/canonical_manifest.json`, `../database/erd.md`, `../database/data_dictionary.md`, `../database/source_to_target.md`, `../database/schema.sql`; E02–E05. Các đường dẫn ở đây tính từ thư mục docs, trừ khi ghi rõ root.

**Còn chờ P2:** báo cáo xác nhận adapter đọc DW candidate, tương đương raw/CSV/DW trên môi trường P2; không lấy khẩu hiệu “100% sạch” thay bảng kiểm định lượng.

## Chương 4 — ETL, đối soát, OLAP và dashboard (P1)

**Mục tiêu:** trình bày triển khai DW/BI và trả lời Q3 bằng bằng chứng thực nghiệm.

**Các mục và nội dung:** 4.1 môi trường, staging và tách cấu hình riêng tư; 4.2 dimension → bridge → fact, UTC, mapping và chống mất dòng; 4.3 full refresh cùng connection/transaction/khóa, vô hiệu hóa model, đối soát trước commit, rollback và chạy lại; 4.4 O1–O6 và năm thao tác OLAP; 4.5 ba dashboard, BI reader, scope/time filter và các mẫu số; 4.6 Q3: count, zero-fill trước LAG, QoQ, ngưỡng quý trước ≥100, quý biên và hạng cao có thể là giảm; 4.7 kiểm tích hợp P1 và các cách phục hồi, phân biệt DW restore, metadata restore, ZIP + REST layout.

**Bảng/hình:** B7 counts/hash bốn view; B8 hai chu trình 12A, checkpoint sau ETL khác sau G3; B9 ca rollback/đối soát và phạm vi đã kiểm; B10 kết quả O1–O6, Top 10 rút gọn, QoQ có count/mẫu số; H5 Tổng quan, H6 Xu hướng, H7 Sở thích với nhãn filter; B11 ma trận scope và ba cơ chế phục hồi.

**Nguồn:** `../etl/`, `../tests/warehouse/`, `../database/refresh_and_reconciliation.md`, `P1/olap_findings.md`, `P1/integration_runbook.md`, `../dashboard/`, `../results/warehouse/`, `../results/olap/`; E06–E11/E17–E20.

**Còn chờ P2:** 12-P2 trên candidate, xử lý lỗi qua 12B và G4; chưa kết luận tái lập hai máy. SQL/API kiểm trên 8092 và ảnh UI cũ của dashboard phải ghi đúng instance/run, không gán ảnh cũ thành ảnh tích hợp mới.

## Chương 5 — Thực nghiệm K-Means và gợi ý phim (P2)

**Mục tiêu:** trả lời Q1/Q2, đối chiếu baseline và chỉ ra giới hạn thực nghiệm.

**Các mục và nội dung:** 5.1 feature rating ≥4, tỷ lệ 18 genre, 6.038 assigned/2 thiếu bằng chứng; 5.2 K=2..8 × raw/StandardScaler, mẫu Silhouette cố định 2.000, chọn K4 đa tiêu chí và ổn định seed; 5.3 hồ sơ cụm và cơ cấu tuổi/giới so baseline assigned, không nhân quả; 5.4 temporal split/cutoff, cùng cohort/candidate, chọn k40 trên validation; 5.5 test chính thức CF và Popularity, fallback, phim mới trong mẫu số Recall; 5.6 CLI evaluation/demo qua DW, tách suy luận với đánh giá test chính thức. Không đưa feature Q1 toàn lịch sử vào giao thức Q2.

**Bảng/hình:** B12 14 cấu hình và ARI; H8 elbow/Silhouette, H9 heatmap, H10 PCA minh họa, H11 nhân khẩu học; B13 validation k20/40/80; B14 metrics test nguyên receipt, cohort và fallback; B15 ca CLI bằng thống kê tổng hợp, không in user ID/lịch sử cá nhân.

**Nguồn:** `P2/clustering_interpretation.md`, `P2/evaluation_protocol.md`, `../results/mining/clustering_summary.json`, `../results/mining/kmeans_experiments.csv`, `../results/mining/split_manifest.json`, `../results/mining/cf_validation_experiments.json`, `../results/mining/cf_test_evaluation_receipt.json`; E12–E16.

**Còn chờ P2:** nội dung phần 5 được duyệt và báo cáo 12-P2. Metrics test là kết quả tham chiếu receipt đã chốt, tuyệt đối không chạy lại hoặc mô tả là vừa đo lại từ DW.

## Chương 6 — Kết luận, giới hạn và hướng phát triển (P2)

**Mục tiêu:** tổng hợp trả lời Q1–Q3 theo đúng mức bằng chứng, tránh lặp toàn bộ chương thực nghiệm.

**Các mục và nội dung:** 6.1 bảng trả lời Q1/Q2/Q3 dẫn về chương 4/5; 6.2 phạm vi đã đạt và trạng thái tích hợp; 6.3 giới hạn mẫu tự chọn/lịch sử/độ thưa/cold start, Silhouette và nhân khẩu học chỉ mô tả, chưa kiểm định ý nghĩa thống kê; 6.4 giới hạn hạ tầng/tái lập/restore và việc còn chờ; 6.5 hướng phát triển trong phạm vi đề tài, ghi là đề xuất chưa triển khai. Rating không là lượt xem, timestamp không là thời lượng xem; không suy nhu cầu hiện tại/doanh thu hoặc sở thích cùng người thay đổi theo tuổi.

**Bảng/hình:** B16 ma trận câu trả lời → bằng chứng → giới hạn; B17 nghiệm thu nội bộ theo snapshot cuối, ô G4/P2 còn chờ cho tới xác nhận thật. Không cần hình mới nếu chỉ lặp chương 4/5.

**Nguồn:** `acceptance.md`, `P1/report_evidence_index.md`, `P1/olap_findings.md`, `P2/clustering_interpretation.md`, receipt test, `integration_checklist.md`; E01/E12–E20.

**Còn chờ P2:** kết quả 12-P2; kết luận tích hợp cuối sau 12B/G4; duyệt chương 6. Không trình hướng phát triển thành tính năng đã hoàn thành.

## Danh mục hình, bảng và quy trình ghép

Mã H1–H11/B1–B17 ở trên là số dự kiến; đánh số lại sau khi duyệt phần viết. Nguồn hình thực, tình trạng ảnh và lựa chọn rút gọn ở `P1/report_evidence_index.md`. ERD giữ Mermaid để sửa được; không tạo hình giả. Phụ lục dự kiến: dictionary/mapping rút gọn, sáu SQL, lệnh tái lập, contract/source/canonical/package hashes, bảng test và phạm vi restore; không đưa dump hoặc dữ liệu theo user.

P1 và P2 viết phần riêng sau khi được giao và dàn ý được duyệt, không cùng sửa DOCX tổng. P1 chỉ ghép sau hai phần được duyệt, kiểm chéo số liệu/đơn vị/mẫu số/nguồn hình, rồi xin review bản tổng. Lịch mục tiêu tham chiếu: 24/10 viết phần; 25/10 tổng hợp sau duyệt; 26/10 tổng duyệt; 27/10 bảo vệ. Đây là mục tiêu phụ thuộc phê duyệt, không cam kết G4 đã đạt.

**Cần điều phối chốt:** dàn ý sáu chương/phân công; mức rút gọn hình bảng; mẫu báo cáo/rubric chính thức; kết quả P2 và G4 trước khi khóa kết luận tích hợp. Chưa viết báo cáo hoàn chỉnh, DOCX/slide, commit/push/PR trong lượt chuẩn bị này.
