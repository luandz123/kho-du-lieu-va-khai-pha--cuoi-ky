# Danh mục bằng chứng báo cáo — chuẩn bị 13A v1

## Hiện hành sau nghiệm thu G4 — 24/10/2026

Điều phối đã nghiệm thu 12-P2 và12B, xác nhận **G4 ĐẠT** trong phạm vi I01–I15. PR30 MERGED `67fd9eb6b98211485b713c99e829291bc3b50f57`; candidate thực chạy vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. P2 intakeG2CONFIRMED trên Windows/Python3.12.6/PG17.4; P1 Windows/Python3.12.14/PG17.11. Không kiểm Linux/SupersetP2 hoặc phục hồi toàn stack máy mới. [Ma trận nghiệm thu](integration_acceptance.md), [ghi nhận mới](g4_acceptance_20261024.json).

Các đoạn chờ P2/G4 bên dưới là snapshot lập dàn ý/chỉ mục trước nghiệm thu; không dùng làm trạng thái hiện hành. Nguồn bổ sung cho các mục E18/E20 và kết luận chương1/3/4/6 là ma trận/ghi nhận mới nêu trên. Chưa nhận đủ chương 2/5/6 P2 được duyệt để ghép; G5 chưa hoàn thành.

## Cập nhật hiện hành 24/10/2026 — dàn ý được điều phối duyệt

Điều phối duyệt dàn ý13A và danh mục bằng chứng, giao công bố riêng trước khi viết bản thảo P1 chương1/3/4. P2 **đã báo G2 CONFIRMED**, tái lập candidate `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` trên máy Windows độc lập, Python3.12.6/PostgreSQL17.4. Nguồn là thông điệp điều phối qua người dùng, bằng chứng công bố của P2 **đang chờ điều phối review**; P1 chưa kiểm độc lập lượt P2. Không ghi đã kiểmLinux, **G4 chưa hoàn thành**. Chi tiết nguồn ở `docs/P1/p2_intake_reported_20261024.json`. Các mụcNOT_CONFIRMED/WAITING_REVIEW/OPEN bên dưới và audit13A là snapshot lịch sử, không sửa thành bằng chứng mới.

Thiếu rubric/mẫu chính thức không chặn bản thảo; không tự áp số trang/thể thức bắt buộc. Dàn ý được duyệt khác PR đãmerge; bản thảo chương chỉWAITING_REVIEW, không ghép vào PR dàn ý, khôngDOCX/slide. Không pipeline/evaluator hoặc đổi tài nguyên.

23/10/2026, **WAITING_REVIEW**. Tất cả đường dẫn trong bảng tính từ root repository. Đây là chỉ mục nguồn hiện có, không là kết quả chạy lại. Dàn ý/phân công: `docs/report_outline.md`.

Candidate đang P2 kiểm nhận: `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`, merge PR25 được xác minh qua API trong `docs/P1/pr25_merged_observation.json`. Checkout dùng lập dàn ý vẫn ở `e59026142da1b29c6324cc07cb19d23172ce4e83`, không chuyển nhánh/ghi đè công việc để chuẩn bị tài liệu. Không suy candidate đã đạt G4; P2 intake G2 **NOT_CONFIRMED**.

## Ánh xạ luận điểm và số liệu

| Mã / chương | Nội dung được phép trình bày | Artifact và vị trí tra cứu | Loại bằng chứng / giới hạn |
|---|---|---|---|
| E01 / 1,6 | Q1 nhóm sở thích/nhân khẩu học lịch sử; Q2 Top 5; Q3 đánh giá theo quý; phạm vi và phân công | `docs/project_spec.md`; `docs/acceptance.md`; `docs/shared/github_workflow.md` | Đặc tả/tiêu chí nội bộ, không là số đo hoặc rubric chính thức; các cập nhật trạng thái cũ có nhãn lịch sử |
| E02 / 3 | Nguồn MovieLens 1M và checksum tệp, Latin-1, `::` | `data/source_manifest.json`; `results/eda/data_profile.csv`; `docs/P2/data_understanding.md` | Nguồn P2, đối chiếu với nguồn P1 trong hồ sơ S05/12A; không sao chép raw lên báo cáo/Git |
| E03 / 3 | Users 6040, movies 3883, cặp movie–genre 6408, ratings 1000209; khóa/FK/miền và UTC | `results/eda/canonical_manifest.json`; `results/eda/data_profile.csv`; `results/eda/eda_metrics.json` | Số liệu EDA; không dùng câu “100% sạch” thay count kiểm lỗi cụ thể; row_count không gồm header |
| E04 / 2,3 | Hợp đồng2, bốn bảng logic, thứ tự cột, NULL/năm, UTC-Z và serializer | `docs/shared/data_contract.md`; `docs/shared/data_contract.json`; `mining/data_io.py` | Quy ước + code triển khai, không tự là chứng minh dữ liệu đúng |
| E05 / 3 | Grain đánh giá nguồn, bốn dimension, bridge, fact, UNIQUE user–movie sau EDA, registry/active views | `database/schema.sql`; `database/erd.md`; `database/data_dictionary.md`; `database/source_to_target.md` | Thiết kế/SQL; bằng chứng thực thi/catalog tra S05 và postflight12A, không đồng nhất bản vẽ với DDL đã chạy |
| E06 / 4 | Staging giữ trường/source_line, không nhân dòng khi chạy lại, rollback fixture | `results/warehouse/s05_summary.json`; `docs/agent/steps/P1/S05.md` | Bằng chứng S05 lịch sử, code/hash/run thực nằm trong summary và báo cáo được dẫn; không chạy lại load tiểu bước sau khi DW có dữ liệu |
| E07 / 4 | Atomic refresh/đối soát, hai run cùng phiên bản, rollback phục hồi snapshot/model | `results/warehouse/s06d_summary.json`; `results/warehouse/s06d_rollback_5c9c553454e54e81953fded2d524877c.json`; `docs/agent/steps/P1/S06.md` | Hai run `16421c84a7a244b5ad4b60f4ce4dfbc6` và `6501a547065246869b98b6ab6531190e`; fixture tự tạo, không đổi receipt cũ |
| E08 / 3,4 | Bốn view canonical khớp raw/CSV/DW tại P1 | `results/warehouse/dw_manifest.json`; `results/warehouse/s06d_adapter_c75f9cb0ceb04d74bfa36e140d812754.json`; `docs/P1/dw_handoff.md` | Kết quả P1, không là xác nhận P2 intake G2 |
| E09 / 4,6 | KPI 1000209 rating, tổng điểm3582313, mean3.5815644530293169; 6040 user/3706 phim có rating, 3883 phim danh mục | `results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json`; `docs/P1/olap_findings.md` | Run `af6dbc20b40d4a47aa3ea71bde6fd107`, SQL O1; danh mục khác phim có rating; mean SUM/COUNT |
| E10 / 4,6 | O1–O6; Top1 American Beauty:3428; O4 mỗi cấp riêng tổng1000209; O5 18×12=216 ô | `olap/queries.sql`; `database/views.sql`; `results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json`; `docs/P1/olap_findings.md` | Kết quả S07; không cộng year/quarter/month, không cộng genre thành tổng hệ thống |
| E11 / 4,6 | Animation Q4/2000:13102→20068,+53.17%; Q1/2001:20068→1715,−91.454056%; quý biên/prev≥100 | `docs/P1/olap_findings.md`; `dashboard/trends/evidence/reconciliation.json`; `dashboard/trends/genre_dataset.sql` | Count/QoQ thực nghiệm; hạng1 Q1/2001 nghĩa giảm ít nhất trong tập đủ điều kiện. Không suy nhu cầu hiện tại. Mẫu số share là lượt gán mọi genre cùng quý |
| E12 / 2,5,6 | K4/raw/seed42; silhouette mẫu2000=0.1860, K2=0.2233 cao hơn; chọn đa tiêu chí; ARI42/0=0.9949,42/7=0.9763 | `results/mining/clustering_summary.json`; `results/mining/kmeans_experiments.csv`; `docs/P2/clustering_interpretation.md`; `docs/P2/feature_engineering.md` | Kết quả P2 đã công bố, không tính lại. Thời gian có thể khác giữa lượt chạy: chọn một artifact/run cụ thể khi lập bảng, không ghép thời gian trong văn bản với CSV thành một run |
| E13 / 5,4 | 6038 assigned,2 insufficient; cụm0..3=2478/1393/760/1407;72 profile, model kmeans_k4_seed42 | `results/mining/clustering_summary.json`; `results/warehouse/s11b2/handoff_summary.json`; `dashboard/preferences/evidence/reconciliation.json` | Đối chiếu package/DB P1; tên cụm mô tả theo P2. Không cộng n_users lặp trên18genre. Tuổi/giới dùng sau phân cụm, không suy nhân quả |
| E14 / 2,5 | t1=974862386, t2=976422051; chọn k40 qua validation, lịch sử test=train+validation | `results/mining/split_manifest.json`; `results/mining/cf_validation_experiments.json`; `docs/P2/evaluation_protocol.md` | Giao thức/validation đã đóng băng; không tune test hoặc đưa cụm toàn lịch sử Q1 vào Q2 |
| E15 / 5,6 | Metrics test baseline/CF, cohort1154, fallback2, k40, phim mới vẫn trong mẫu số Recall | `results/mining/cf_test_evaluation_receipt.json`; `results/mining/cf_test_evaluation.json` | Receipt chính thức run `test_run_s10b_official_20261022_034458`; số gốc ở bảng dưới. Đây là tham chiếu, không là lần đánh giá lại từ DW12A |
| E16 / 4,5 | CLI --source dw thực, seed/cutoff/unseen/Top5 và engine BI đúng DB thử; metrics official chỉ tham chiếu | `results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/postflight.json`; `results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/official_test_metrics_reference.json` | Hậu kiểm P112A; output cá nhân/raw CLI ignored, chỉ dùng aggregate. Không trích user ID, lịch sử hoặc danh sách gợi ý gắn user |
| E17 / 4 | Ba dashboard: số liệu, scope, BI SELECT, ba tổ hợp filter, baseline fixed6038/insufficient2 | `dashboard/overview/evidence/final_verification.json`; `dashboard/trends/evidence/final_verification.json`; `dashboard/preferences/evidence/verification.json`; các reconciliation.json tương ứng | SQL/API/UI lịch sử tại8089 theo từng hồ sơ; không gọi session READ ONLY là bằng chứng role không có write. Quyền kiểm riêng trong bi_reader*.json |
| E18 / 4,6 | Hai chu trình tích hợp; registry invalid sau ETL, reload đúng identity và NO-OP sau G3;8092 | `results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json`; `cycle1_etl.json`, `cycle2_etl.json`, `cycle1_g3.json`, `cycle2_g3.json` cùng thư mục; `docs/P1/integration_runbook.md` | Run57c1e8e3…,833.922s, Windows/Python3.12.14,88test trong hồ sơ lịch sử. Runtime code chưa commit lúc chạy, code công bố3334ff8…, candidate merge4546d5b… là ba mốc khác nhau. P2/G4 còn chờ |
| E19 / 4 | ZIP thật3dashboard/23chart/6dataset, import chính thức rồi REST layout; khác metadata restore và DW restore | `dashboard/restore/README.md`; `dashboard/restore/evidence/`; `dashboard/metadata_restore/evidence/restore_receipt.json`; `docs/P1/integration_prep/README.md`; `results/warehouse/s12a_prep/` | Cùng máy/version, DW hiện hữu; không tuyên bố ZIP tự restore đầy đủ hoặc phục hồi máy mới. DB-level ACL clone khác nguồn. Dump/key/config chỉ cục bộ |
| E20 / 1,6 | PR25MERGED; candidate đang P2 kiểm nhận; chưaG4/P2intake | `docs/P1/pr25_merged_observation.json`; `docs/agent/steps/P1/S13A.md`; `docs/agent/STATE_P1.md` | Quan sát API mới + thông tin điều phối; chưa có báo cáo12-P2 trong lượt chuẩn bị này. Không dùng báo cáo OPEN cũ làm trạng thái hiện tại |

## Metrics test trích nguyên receipt (không chạy evaluator)

Run `test_run_s10b_official_20261022_034458`, `metrics_comparison` trong receipt, cùng cohort 1154 user và candidate universe. Các số dưới dùng độ chính xác đã ghi trong receipt, không tính lại delta từ số làm tròn.

| Mô hình | macro_precision_at_5 | macro_recall_at_5 | total_hits | fallback_users_count |
|---|---:|---:|---:|---:|
| popularity_baseline | 0.201733 | 0.02712408 | 1164 | 0 |
| item_based_cf_k40 | 0.231023 | 0.03530289 | 1333 | 2 |

Kết luận được phép: CF cao hơn baseline trong lượt test đã chốt; không suy thành vượt trội mọi bối cảnh hoặc có ý nghĩa thống kê. Fallback CF 2/1154, receipt ghi 0.1733%. Cần kèm điều kiện cohort, split và cold start để người đọc hiểu mẫu số. Checksum trong receipt là checksum, không là chữ ký số; SHA byte file hiện tại được ghi riêng trong hồ sơ13A, không thay trường nội bộ để ép khớp.

## Chọn hình/bảng tiêu biểu

| Mã dự kiến | Nguồn thực có sẵn | Chú thích và kiểm trước ghép |
|---|---|---|
| H2 ERD | `database/erd.md` | Mermaid chỉnh sửa được; render khi viết báo cáo, giữ PK/FK/1:N và bridge; chưa có PNG mới trong13A |
| H3/H4 EDA | `results/eda/rating_distribution.png`; `results/eda/quarterly_activity.png` | Phân bố đánh giá và hoạt động lịch sử, không lượt xem |
| H5 Tổng quan | `dashboard/overview/evidence/all_history_charts.jpg`; `2000_q3_charts.jpg` cùng thư mục | Ảnh UI11A lịch sử; ghi toàn kỳ/Q3, nguồn instance8089 theo hồ sơ, không nhận là ảnh8092 mới |
| H6 Xu hướng | `dashboard/trends/evidence/comedy_charts.jpg`; `three_genres_qoq.jpg` cùng thư mục | Chọn một ảnh đủ rõ count/QoQ âm và nhãn filter; bảng Animation dùng E11, không gán ảnhComedy thànhAnimation |
| H7 Sở thích | `dashboard/preferences/evidence/ui_all_dashboard.jpg`; `ui_demographic_baseline.jpg` cùng thư mục | Làm rõ profile chỉ chịu filter cụm, baseline6038 và insufficient2 cố định |
| H8 Chọn K | `results/mining/kmeans_elbow_silhouette.png` | Inertia khác không gian không so trực tiếp; silhouette tính mẫu2000, không phải toàn6038 |
| H9/H10/H11 Q1 | `results/mining/cluster_genre_heatmap.png`; `cluster_pca_2d.png`; `cluster_demographics.png` cùng thư mục | Profile tỷ lệ gốc; PCA minh họa; tuổi/giới chỉ mô tả mẫu |
| B4/B7 nguồn và DW | E03/E08/E18 | Count/hash, không có dòng user-level; dài hash có thể chuyển phụ lục |
| B10 Q3 | E09–E11 | Rút gọn vài quý đủ điều kiện, ghi cả count/QoQ/share/mẫu số và quý biên |
| B12/B13/B14 ML | E12/E14/E15 | Bảng 14 cấu hình có thể để phụ lục; validation khác test; metrics test đúng receipt |

Các ảnh trên là ứng viên, chưa phải đã duyệt bố cục báo cáo. Khi ghép phải xem lại độ rõ, nhãn trục, phạm vi filter và nội dung riêng tư trên từng ảnh; cắt hoặc che vùng nhạy cảm nếu có trước đưa bản nộp. Không tự xác nhận ảnh đã sạch chỉ vì đường dẫn tồn tại. Không đưa screenshot output CLI có user, URL credential hoặc thông tin tài khoản.

## Tách kết quả, diễn giải và giả thuyết

- **Thực nghiệm:** count/hash/metric/profile/filter/rollback có artifact, run và phạm vi môi trường cụ thể ở bảng. Không gán commit công bố cho code chưa commit lúc chạy; không đổi PASS/FAIL lịch sử.
- **Diễn giải mô tả:** tên cụm theo tỷ lệ genre, cơ cấu nhân khẩu học, lý do chọn K4 đa tiêu chí, “giảm ít nhất” khi QoQ âm. Luôn dẫn số hỗ trợ, không trình thành quan hệ nhân quả.
- **Giả thuyết/đề xuất:** nguyên nhân biến động đóng góp đánh giá, nhu cầu hiện tại, tác động kinh doanh hoặc cải tiến chưa đo. Nếu không có bằng chứng, ghi chưa kiểm chứng hoặc bỏ; không viết thành kết luận thực nghiệm.

## Phần đang thiếu trước khóa báo cáo

1. Báo cáo12-P2 kiểm candidate4546d5b…, môi trường Linux/P2 và DW thật; P2 intakeG2 vẫnNOT_CONFIRMED.
2. Kết quả xử lý lỗi/12B và G4; chưa ghi tích hợp hai máy hoặc G4 đạt.
3. Rubric/mẫu trình bày/thời lượng chính thức và thông tin hành chính nhóm do nhóm xác nhận.
4. Các chương P1/P2 được giao viết, review hai phần, lựa chọn ảnh/bảng và nguồn tham khảo học thuật; lượt này chỉ lập dàn ý/chỉ mục, chưa viết báo cáo cuối.

Không chạy lại ETL/G3/evaluator/dump/restore để lấp khoảng trống tài liệu; giữ8089 và tài nguyên thử. Ledger SHA13A chỉ kiểm file hiện có, không nâng phạm vi kiểm runtime.
