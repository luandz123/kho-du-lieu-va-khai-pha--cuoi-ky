# Bàn giao 11B-3 — WAITING_REVIEW, 20/10/2026

Đã dựng Dashboard Sở thích thực trên [Superset 8089, dashboard 3](http://127.0.0.1:8089/superset/dashboard/3/). Database1, datasets5/6, charts14–23; SQL/metric/scope đầy đủ tại `dashboard/preferences/README.md`, `chart_definitions.json`, `dashboard_definition.json` và hai dataset SQL. Chưa export/import.

Nguồn duyệt: người dùng chuyển thông báo **điều phối chấp nhận 11B-2**, rồi giao riêng 11B-3. Đã checkpoint chọn lọc 25 file 11B-2 tại **f663dcb4143202dac0835e4d5168e1b8558a6463**, giữ nhánh **p1-s11b-cluster-intake**. Đây là checkpoint code đã review; không gán commit mới cho các run production cũ. Dashboard 11B-3 và hồ sơ lượt này chưa stage/commit/push/PR; kế hoạch ngoài phạm vi giữ nguyên.

## Model và package identity

Model active+valid **kmeans_k4_seed42**, contract2. Gói P1 tái tạo đã kiểm nhận ở `data/processed/p1_g3_20261020_intake/` (ignored), producer code P2 **bab0b4049d4e0b1724418b8a92d8afbeda4bc775**. Môi trường tái tạo P1 Python3.12.14 Windows/sklearn1.5.2, không đổi thành môi trường producer P2 Linux3.12.3. Lượt này không tái tạo gói, không thay metadata/provenance hay chạy apply.

| Byte thực được băm lại | SHA-256 |
|---|---|
|user_cluster.csv|5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93|
|cluster_genre_profile.csv|59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d|
|manifest.json|630453504b71c6b3e38e022f760e2c37a2612a418d3dfdfbf448794c7297d0f0|

Một registry, registered_at **2026-10-20T09:00:37.986010Z**, model_created_at **2026-10-20T08:32:23.015413Z** giữ nguyên. Registry đầy đủ, toàn rows hai bảng cụm, chín bảng staging/DW cả surrogate có count/fingerprint trước–sau giống nhau; đây là kiểm bảo toàn mới, không giả là chạy lại ETL hoặc tính lại bốn canonical hash. Bốn hash chuẩn kế thừa bằng chứng 11B-2 đã được điều phối kiểm nhận; không đổi nguồn.

## Kiểm tra thực tế

Run đối soát cuối **09782a8ea2094b6bbd7c32cc4a2cdb03**, **35.422 giây**, base checkpoint f663dcb, working-tree code thực chạy trong `evidence/reconciliation.json`. SHA runtime `reconcile.py`: **e64d9dd0205e4e1e133a118f487a13493820d4c18b1e25e93bc648efb1f43636**. Báo cáo trước run43d0d402… được giữ nguyên. Sau run cuối chỉ sửa checker so JSON serialization và hồ sơ; không đổi SQL/metric/filter. Hash artifact bản cuối nằm ledger bàn giao, không gán ngược vào report runtime cũ.

| Tổ hợp SQL độc lập ↔ API ↔ UI | Assigned | Insufficient cố định | Baseline cố định | Heatmap |
|---|---:|---:|---:|---:|
|Toàn bộ|6.038|2|6.038|72 ô: 4×18|
|Cụm3|1.407|2|6.038|18 genre|
|Cụm1, tuổi25–34, F|170|2|6.038|18 genre cụm1, không chịu tuổi/giới|

Quy mô 0..3: **2478 /1393 /760 /1407**, tương ứng **41,04 /23,07 /12,59 /23,30%** trên6038. Ca170user: tỷ trọng quy mô **2,8155% trên6038**; tỷ trọng cơ cấu **12,2039% trên1393**; baselineF **1709/6038=28,3041%**; baseline25–34 **2096/6038=34,7135%**. Mẫu số gốc cố định, không chuẩn hóa lại sau filter. Profile một cụm đủ18genre, tổngmean=1; không cộng n_users lặp hoặc fan-out user.

SQL kỳ vọng lấy aggregate độc lập từ bảng user_cluster/profile + registry activevalid + dim_user, không dùng dataset SQL làm đáp án cho chính nó. API đọc actual saved chart config, engine thực **movielens_bi_reader / UTC**. UI native thật: ca3 có applied filters3 trên KPI/bảng, heatmap chỉ1, fixed KPI/baseline0; lưu AX tổng hợp và ảnh.

Fixture SQL `VALUES` trong transaction READ ONLY kiểm mẫu số fixed trước filter và bẫy n_users lặp2genre, không tạo schema/bảng hoặc ghi analytics. Python AST/JSON/ignore/package/config verification PASS. Giữ `verification_FAIL_position_serialization.json`: checker ban đầu so chuỗi JSON có whitespace khác; parsed layout giống hệt, đã sửa checker so cấu trúc, không sửa dashboard nghiệp vụ để ép kiểm tra.

19 object 11A/11C trước–sau khớp. API11A toàn kỳ1000209,2000Q3=324864;11C toàn12quý,2001Q1=32223;Animation2001Q1 QoQ=−91,454056% vẫn lấy prev20068→1715. Không chạy lại bootstrap, ETL hoặc cài view S07. Không tạo lại dashboard11A/11C.

## Quyền và vận hành

Chỉ bổ sung USAGE dw/analytics và SELECT đúng `analytics.v_active_user_cluster`, `analytics.v_active_cluster_genre_profile`, `dw.v_ml_users`. Tổng SELECT7view; không quyền ghi lên bảng dự án, CREATE, membership hoặc quản trị; thử UPDATE WHEREfalse bị42501. Kiểm từ container đang chạy và query thực qua Superset database1, không suy từ READ ONLY session. Không đổi mật khẩu, firewall, DDL hoặc quyền ngoài phạm vi.

Hai container web/metadata **running / healthy, exit_code0** ở quan sát mới. Không cần khởi động lại trong11B-3; không suy nguyên nhân dừng255 lịch sử. Thông tin đăng nhập nằm local ignored, không đưa vào báo cáo.

Mở dashboard, đăng nhập, Apply filters; Clear all trở toàn bộ, Refresh dashboard để đọc lại active views. Không chạy lại create script lên instance đã có IDs. Bảng cơ cấu có cuộn ngang; heatmap desktop1280×900 đã kiểm, viewport kiểm thử được reset sau bàn giao.

## File và giới hạn

Lượt này thêm `dashboard/preferences/` (SQL, grants, API creator, checker, config/IDs, evidence tổng hợp/ảnh), `tests/warehouse/check_preferences_fixture.py`, tài liệu này; bổ sung chọn lọc STATE/DECISIONS/REVIEWS/PROMPTS/S11. Ledger `dashboard/preferences/evidence/handoff_manifest.json` liệt kê hash/file cuối. Không đưa CSVuser-level/ZIPexport/credential lênGit, không sửaP2 hoặc kế hoạch.

Giữ **PUBLIC TEMP**, chưa export/import/restore, chưa kiểm full refresh mới với helperS07/G3, chưa kết nối hai máy. **P2 intake G2 NOT_CONFIRMED**. Chưa commit/push/PR phần11B-3. Kết quả **WAITING_REVIEW**, dừng để điều phối kiểm dashboard.

Ý bảo vệ:

- Grain user khác grain profile; tách dataset để không nhân số người theo18genre.
- Baseline cố định6038 và mẫu số cụm gốc giúp filter không tự làm tỷ lệ thành100%; mọi nhãn phải ghi mẫu số.
- Heatmap là profile đã tính, tuổi/giới không tái tính vector nên bị loại khỏi scope.
- Insufficient NULL vẫn có KPI2 riêng, không biến mất khi chọncụm.
- Active+valid và package identity gắn đúng một phiên bản; nhân khẩu học chỉ mô tả dữ liệu lịch sử, không giải thích nhân quả.
