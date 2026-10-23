# Kế hoạch 12A-P1 — chưa thực thi, 23/10/2026

## Hiện hành23/10/2026 —12A IN_PROGRESS sau gate MERGED

Đã kiểm PR24 MERGED01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02, HEAD9ef301373ecbaa7e794215bd09465a87ac0fd363 đúng điều phối nghiệm thu. Quan sát OPEN trước giữ nguyên, quan sát mới docs/P1/12a_gate_merged_observation.json. Nhánh codex/p1-s12a-integration, base01d51a2; hồ sơ cục bộ giữ nguyên, không commit/stash/reset. Chuyển main ban đầu bị Git chặn bảo toàn hồ sơ; nhánh đang giữ được fast-forward rồi tạo nhánh tích hợp từ đúng main remote. Không mất dữ liệu, không gọi base là candidate.

Venv mới tmp/s12a-venv Python3.12.14, pip check/import đạt,34test guard/ETL/G3/catalog đạt. Database tích hợp riêng movielens_btl_int_20261023_57c1e8e3, run57c1e8e3d3f445c4b3eeddbfc3364709 đang thực thi hai chu trình, chưa ghi PASS. Context guard tên/marker/owner riêng, production assert_project gốc không đổi. 8089/8092 containers cũ được start sau trạng thái stopped255 để phục vụ demo/snapshot/kiểm, không init/recreate;8091giữdừng. Chỉ kết nối8092 sang DBthử quaAPI, không sửa8089/P2/nguồn/productionACL. P2 intakeNOT_CONFIRMED; chưa candidate/G4/commit/push/PR.

## Gate hiện tại

Điều phối báo nghiệm thu kỹ thuật Bước10B tại HEAD PR24 `9ef301373ecbaa7e794215bd09465a87ac0fd363`. GitHub vừa kiểm PR24 **OPEN, merged=false, merged_at=null**; chưa đủ điều kiện bắt đầu thực thi. `merge_commit_sha` có giá trị khi PR còn OPEN không phải bằng chứng đã merge. Chỉ khi API xác nhận MERGED và commit thực thuộc main mới được tiếp tục.

PR21 đã xác minh MERGED tại `eeb351c44e6cc3223cbd56b722506f91a24f8b5a`; báo cáo OPEN cũ giữ nguyên. Checkout hiện tại vẫn `codex/p1-s12a-prep`, HEAD `ae9677094fe3b630cf34c82a0fdd647d53c78828`. Đây là mốc quan sát, không phải base 12A hoặc candidate. Kế hoạch ngoài phạm vi chưa track được giữ nguyên. Lượt này không fetch/pull/chuyển nhánh hoặc thay dịch vụ/database/môi trường.

## Trình tự sau khi PR24 MERGED

| Giai đoạn | Thao tác dự kiến | Điều kiện / bằng chứng cần lưu |
|---|---|---|
| Gate và Git | Xác minh PR24 MERGED, HEAD đã nghiệm thu và lịch sử main; bảo toàn thay đổi rồi đồng bộ main an toàn, tạo `codex/p1-s12a-integration` | Commit nền thực tế, quan sát merge PR21/24, Git status; không tự merge PR24 hoặc gọi base là candidate |
| Đọc đầu vào | Đọc STATE/DECISIONS/REVIEWS/S12 của P1, S10/CLI/receipt cuối P2, contract2, manifest và cấu hình frozen | Chỉ dùng tài liệu PR24 đã merge; bản S10 hiện trong checkout còn10A không đại diện đầu ra10B |
| Dependency | Hợp nhất requirements P1/P2 trên nhánh mới, giữ Superset6.1.0 riêng; tạo venv mới trong `tmp/s12a-venv/` ignored | Python3.12, exact installed versions, pip check/import, đối chiếu producer fingerprint; không thay `.venv` demo hoặc file P2 |
| Đích tích hợp | Tạo DB mới tên riêng có ngày/run ID, không dùng demo/clone cũ; lập guard tên+marker+owner+catalog và cờ apply, mặc định dry-run | Đích chưa tồn tại, ownership đúng; không DROP/clean hoặc làm rộng guard production; env riêng local ignored |
| Chu trình1 | Kiểm nguồn → schema/staging/full refresh → DW → OLAP → ML qua DW → loader G3 → hậu kiểm | Tách checkpoint ETL/G3, canonical hash/count, model state, run ID/code/config/package hashes |
| Chu trình2 | Lặp cùng logic/config trên chính DB tích hợp; giữ registry, ETL vô hiệu hóa model cũ rồi loader tái kiểm/active | Registry identity/registered_at theo chính sách đã duyệt; không xóa registry, không tăng dòng/trộn version; kiểm NO-OP/conflict phù hợp |
| Superset thử | Snapshot cấu hình8092, đổi kết nối bằng API/UI chính thức sang DB tích hợp qua BI reader; chỉ SELECT view cần thiết trên đích thử | Không sửa8089/8091, không cấp quyền production/firewall; kiểm ba dashboard và filter, clear/refresh cache sau ETL/G3 |
| Hồ sơ bàn giao | README đúng thứ tự tái lập, `docs/P1/integration_candidate.md`, S12A/STATE WAITING_REVIEW | Chỉ đề xuất gói/điều kiện, chưa chọn/gửi candidate cuối hoặc chốtG4; không commit/push/PR12A khi chưa được giao |

## Chỗ cần tích hợp có kiểm soát

Code hiện tại `etl/run_etl.py` gọi `assert_project` trong refresh/verify và loader G3 cũng bảo vệ đích production. **Chỉ đổi env sang DB mới chưa đủ.** Khi gate đạt, cần thiết kế context/dispatcher tích hợp riêng: guard chỉ chấp nhận đúng target đã cấp phép, marker và owner; kiểm sau khóa cùng connection. Tái sử dụng pure parse/transform/insert/serializer/catalog helpers, không monkeypatch, tắt guard hoặc dùng fixture-schema để đi vòng guard production.

Chu trình refresh giữ một connection/transaction và advisory lock `(20261027,1)`, danh sách TRUNCATE tường minh, giữ registry metadata; kiểm trước commit và rollback đúng thiết kế. Báo cáo sau ETL phải thể hiện model inactive/invalid và bảng cụm rỗng. Sau loader mới được báo active+valid và kiểm lại dữ liệu/model/view. Báo cáo file được xuất sau COMMIT; mất kết nối tại COMMIT phải ghi UNKNOWN và đối soát mới, không tự retry ghi.

## Dữ liệu, G3 và ML

- Contract2: ID nguồn, thứ tự cột, CSV canonical UTF-8/LF/NULL rỗng, timestamp giây Unix và UTC-Z theo serializer P2. Kiểm đủ bốn hash trước ML, không chỉ COUNT.
- Dùng gói G3 local đã kiểm trước khi quyết định tái tạo. Producer frozen `bab0b4049d4e0b1724418b8a92d8afbeda4bc775`, model `kmeans_k4_seed42`; không thay provenance theo HEAD tích hợp.
- Hai SHA CSV frozen: users `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93`, profile `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d`. Kiểm byte thực, đầy đủ config/library/provenance và source hash. Không tái tạo đúng identity thì dừng; không đổi hash kỳ vọng.
- 6.040 user, 6.038 assigned/2 insufficient, cụm2478/1393/760/1407,72profile; mapping/status/NULL/FK/profile sums đúng. Giữ NO-OP/conflict/reload chính sách11B, registry không bị xóa để ép đạt.
- Adapter `--source dw` phải đọc DB tích hợp thật. Lệnh CLI/evaluation cụ thể chỉ chốt sau đọc PR24 merged và manifest/cutoff/k40/receipt cuối. **Không gọi evaluator test chính thức lần nữa.** Metric test trích receipt đã nghiệm thu, ghi nguồn/hash, phân biệt với ca demo vừa chạy. Kết quả cá nhân/seed/recommendations lưu ignored.

## Môi trường và kết quả cần kiểm

Requirements tổng chỉ sửa sau gate, dựa exact version đã kiểm và dải P2. NumPy2.0.2/pandas2.3.3/scipy1.14.1/scikit-learn1.5.2 là căn cứ từ môi trường P2 đã bàn giao; không tự cho rằng mọi dependency cuối PR24 đã giống. Kiểm Windows/Linux, optional Parquet/plotting, driver PostgreSQL và biến env mẫu; không đưa Superset vào venv chung. Không sửa requirements P2 hoặc thuật toán/metric/config frozen.

KPI nền1.000.209rating/tổng3.582.313,6040user/3706phim córating/3883phim danh mục. BI kiểm Tổng quan toàn kỳ/Q3=1000209/324864; Animation2001Q1=1715/prev20068/QoQ−91.454056%; Sở thích assigned6038/170, baseline6038, insufficient2 và scope heatmap. Sau chu trình2 không được dùng cache/model cũ để kết luận đạt.

Hướng dẫn cuối phải đủ: môi trường/tải nguồn → schema → staging/ETL → DW check → OLAP → ML qua DW → loader G3 → Superset; lệnh thật/credential local/manual steps/backup-restore/giới hạn. P2 có phương án tải nguồn và tái tạo DW riêng, không phụ thuộc nhận dump. P2 intakeG2 vẫn NOT_CONFIRMED đến khi có xác nhận thực.

## Bàn giao hiện tại

**Kế hoạch WAITING_REVIEW; thực thi12A NOT_STARTED do PR24 còn OPEN.** Chưa tạo branch12A/venv/database, chưa hợp nhất requirements hoặc thay8092. Chưa tạo candidate cuối, chưa chạy pipeline/ML/UI/test, chưa commit/push/PR. Chờ điều kiện MERGED; giữ production và toàn bộ backup/clone/volume cũ.
