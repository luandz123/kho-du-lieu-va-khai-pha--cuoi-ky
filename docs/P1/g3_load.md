# 11B-2 — Nạp G3 production

## Kết quả bàn giao — 11B-2 WAITING_REVIEW, 20/10/2026

Điều phối đã chấp nhận11B-1; kết quả11B-2 này chưa được điều phối review. Đã hoàn thành đúng lần nạp đầu và lần kiểm NO-OP được giao; không nạp thêm phiên bản, không làm dashboard11B.

| Lần | Run_id | Kết quả | Thời gian |
|---|---|---|---:|
|Apply đầu|4648f191bba5455989340dbfefc021ba|COMMITTED, hậu kiểm READ ONLY mới PASS|160.438s|
|Apply kiểm chạy lại|0dec3918c71641b99bd5b47cec2a91f8|COMMITTED_NO_OP, hậu kiểm READ ONLY mới PASS|163.531s|

Thời gian trên là toàn lệnh, gồm băm nguồn/đối soát/hậu kiểm, không chỉ thời gian INSERT.

Một registry contract2/versionkmeans_k4_seed42 active=true/valid=true; user_cluster6040 (assigned6038/insufficientNULL2), quy mô0..3=2478/1393/760/1407; profile72. Hai active view6040/72 cùng version, toàn bộ trường logic so đúng snapshot. Registered_at **2026-10-20T09:00:37.986010Z** không đổi giữa hai lần; model_created_at giữ **2026-10-20T08:32:23.015413Z** từ manifest. Bốn canonical SHA khớp G2 sau cả hai lần; chín bảng staging/DW giữ count/fingerprint mọi trường, gồm surrogate. ACL/schema/role/membership BI không đổi. **19đối tượng11A/11C so API thật và file trước/sau khớp**, không chỉ fallback khi API dừng.

Checkpoint11B-1 **17e9d5664f247b7ee13446ff260937986d17b54a**; code11B-2 chưa commit, SHA bundle thực chạy **5b4ec63472ce588081f77c9e7922438607b331acf05eead2e2d5d241a4bce193**, từng module trong receipt. Các module không đổi giữa hai lần. Không gán checkpoint cũ cho code mới; code_state WORKING_TREE_SHA256_NOT_IN_BASE_COMMIT. Runtime report băm lại byte local, chưa chuẩn hóa LF/CRLF để làm giả hash.

31/31unit và8/8integration trước nạp PASS. Integration giữ guard test production rỗng: **không rerun nó trên trạng thái đã nạp G3**. FAIL proxy simulation và preflight Docker-down giữ nguyên; summary không xóa lịch sử. Test fixture đều dọn, ba bảng thật rỗng trước apply. Sau nạp113file P2/EDA/source manifest/database/dashboard kiểm không đổi.

Bằng chứng: results/warehouse/s11b2/apply_01.json, apply_noop_02.json, handoff_summary.json, các unit_tests*/fixture_* và service_recovery.json. Summary có registry thật, profile aggregates, hai active view và hashes; không user-level rows. Ledger cuối handoff_manifest.json liệt kê file/SHA.

Docker Desktop mở lại và hai container cũ đã start, healthy; không recreate/init/volume reset. Lệnh docker desktop restart riêng trả lỗi stop/context-deadline (giữ ở service_recovery), không force-kill; sau đó engine/API và hai container vẫn hoạt động. Không có helper còn chạy. Không suy nguyên nhân Exited255 cũ. Giới hạn fallback API trong code được ghi minh bạch; lần production thật đã so LIVE_API_AND_ARTIFACTS_MATCH.

Giữ P2 intake G2 NOT_CONFIRMED, PUBLIC TEMP/chưa import-restore/fullrefreshS07 vớiG3 chưa kiểm. Gói đang active là tái tạo P1 Python3.12.14 đã được kiểm nhận; nếu gói cùng version có libraries/provenance khác sẽ bị conflict theo chính sách, không tự giả thành môi trường P2. Chưa đổi DDL/quyền/firewall, ETL, dashboard11B, export ba dashboard, push hoặc PR. Kế hoạch ngoài phạm vi bảo toàn. Nhánh p1-s11b-cluster-intake, HEAD17e9d566…; chỉ checkpoint11B-1 được commit, mọi thay đổi11B-2 chưa stage/commit.

Ý bảo vệ: byte snapshot giữ đúng gói khi file ngoài thay đổi; khóa nguồn+hash cùng transaction ngăn lệch DW; inactive trước/activate cuối ngăn dùng gói nửa chừng; NO-OP giữ registered_at; UNKNOWN sau mất ACK phải quan sát lại, không đoán rollback/retry.

Dừng chờ điều phối review11B-2. Phần thiết kế và lệnh bên dưới giải thích cơ chế đã chạy; không chạy lại apply đầu để tạo mới.

---


Nguồn: điều phối chấp nhận11B-1 và người dùng giao riêng11B-2, cho phép ghi đúng model_registry/user_cluster/cluster_genre_profile của movielens_btl. Không tạo dashboard11B, export/import, ETL, DDL hoặc quyền/firewall.

## Provenance và gói bất biến

Checkpoint cục bộ11B-1 đã review: **17e9d5664f247b7ee13446ff260937986d17b54a**, chỉ21file P1 được stage chọn lọc. Kế hoạch ngoài phạm vi giữ nguyên. Nhánh p1-s11b-cluster-intake; checkpoint này **không chứa code production11B-2**. Code thực chạy còn working tree, được nhận diện bằng SHA-256 từng module trong các report; không gán checkpoint cho lần nạp như thể đã chạy từ code được commit. Chưa push/PR.

Gói đã kiểm nhận ở data/processed/p1_g3_20261020_intake, gồm đủ3file ignored. Version duy nhất kmeans_k4_seed42; hai SHA frozen giữ nguyên:

- user_cluster.csv: `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93`.
- cluster_genre_profile.csv: `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d`.
- manifest: `630453504b71c6b3e38e022f760e2c37a2612a418d3dfdfbf448794c7297d0f0`.

Không tái tạo hoặc đổi gói/producer P2 trong11B-2. `read_package` chụp byte vào bộ nhớ, kiểm đủ gói và metadata trước kết nối ghi. Production dispatcher tái kiểm **byte snapshot trong bộ nhớ**, không mở lại CSV để insert; các hàng insert được dựng từ chính byte snapshot đã xác minh. Mỗi CLI invocation có snapshot riêng đã kiểm; không dùng lại receipt cũ làm thay thế kiểm tra gói.

## Dispatcher và transaction

`python -m etl.load_g3` mặc định dry-run; ghi thật phải có `--apply`. `--expect-empty` dùng cho lần nạp đầu, kiểm cả ở preflight READ ONLY và sau khi khóa trong transaction ghi. Không có fail-injection CLI production.

`production_transaction` là cổng riêng, bắt buộc snapshot/version/hai frozen hash. `fixture_transaction` vẫn từ chối schema analytics và chỉ chấp nhận schema UUID có marker/ownership; không gỡ guard11B-1. Cả hai gọi cùng `_transaction`, cùng insert/so toàn bộ hàng/activation/version policy/COMMIT handling. Fixture không được coi là đã kiểm bốn hash DW production: đường production thực sự gọi check_dw sau khóa, bằng cùng connection; kết quả thật được lưu trong receipt apply.

Một connection, transaction READ COMMITTED:

1. Advisory exclusive `(20261027,1)`, kiểm marker/database thật.
2. SHARE ROW EXCLUSIVE trên ba bảng analytics; SHARE trên ba staging và sáu bảng DW (bốn dimension, bridge, fact). SHARE ngăn DML/TRUNCATE của nguồn từ lúc băm đến COMMIT; không dựa riêng vào các writer có tuân thủ advisory lock hay không.
3. `check_dw` kiểm catalog, băm bốn view bằng serializer P2, cohort/genre/registry sau khi khóa; helper không mở connection riêng. Kiểm `expect_empty` trước INSERT.
4. Registry mới inactive/invalid; insert users và profile từ memory snapshot. Không UPSERT/DO NOTHING/xóa hoặc truncate model.
5. So toàn bộ trường logic của rows đã lưu với snapshot, cùng connection. Chỉ sau đó hạ active cũ và active+valid đúng version. So hai active view với snapshot, kiểm chỉ một model active trước COMMIT.

Cùng identity/payload và đang active+valid: NO-OP, không chạy UPDATE và không đổi registered_at. Identity gồm preprocessing JSONB đã được chấp nhận, payload hashes/config/provenance, libraries, source/canonical hashes, training config hash/K/seed/genre order. Cùng version nhưng khác identity hoặc hàng lưu bị đổi: từ chối. Reactivate/reload chỉ theo chính sách11B-1, sau DW recheck; không tự tạo điều kiện invalidated để thử trên production.

Lỗi trước COMMIT có rollback xác minh connection ở trạng thái IDLE thì báo ROLLED_BACK. Connection không rõ trạng thái hoặc mất ACK lúc COMMIT báo UNKNOWN, mở connection READ ONLY mới để quan sát, không tự retry ghi và không mặc định rollback. Fixture giả lập mất ACK **sau khi COMMIT thật trong schema thử**; không chủ động ngắt kết nối production. Nếu DB đã commit nhưng ghi report hoặc hậu kiểm lỗi, báo rõ DB đã commit, không đổi thành rollback.

## Hậu kiểm và bảo toàn

Sau COMMIT dùng connection READ ONLY mới: kiểm lại bốn canonical hash, metadata, toàn bộ rows, active view, counts/status/cluster/profile và registry. Chụp fingerprint mọi trường của chín bảng nguồn trước/sau, gồm surrogate IDs: count và MD5 của chuỗi row-MD5 theo PK; đây là fingerprint kiểm thay đổi, không phải chữ ký bảo mật. Bốn canonical SHA-256 vẫn được kiểm độc lập. Không ghi nội dung từng user vào report.

Quyền BI: so fingerprint ACL của relation/schema, thuộc tính và memberships của movielens_bi_reader. Dashboard11A/11C: đọc cấu hình19đối tượng bằng REST API chính thức, so hash trước/sau; không tạo chart/dataset/dashboard hoặc ghi metadata trực tiếp. Nếu API không khả dụng, receipt ghi rõ chỉ so file cấu hình local, không giả thành đã kiểm web; kiểm mandatory DB không bị bỏ qua. Lần nạp thật phải đọc receipt để phân biệt phạm vi xác minh.

Lần apply thứ hai được giao riêng để kiểm NO-OP: không truyền expect-empty, không truncate/xóa/invalid model. So registered_at và toàn bộ dữ liệu với lần đầu, cùng frozen identity và code SHA.

## Lệnh đã chuẩn bị

```powershell
# Mặc định chỉ đọc. Mỗi report phải là đường dẫn mới.
.\.venv\Scripts\python.exe -m etl.load_g3 --package data/processed/p1_g3_20261020_intake --report results/warehouse/s11b2/preflight_new.json
# Chỉ chạy khi được giao nạp; lần đầu đã thực hiện không chạy lại để tạo mới.
.\.venv\Scripts\python.exe -m etl.load_g3 --package data/processed/p1_g3_20261020_intake --apply --expect-empty --report results/warehouse/s11b2/apply_01.json
# Lần kiểm NO-OP được giao, không dùng expect-empty.
.\.venv\Scripts\python.exe -m etl.load_g3 --package data/processed/p1_g3_20261020_intake --apply --report results/warehouse/s11b2/apply_noop_02.json
```

Unit: `python -m unittest discover -s tests/warehouse -p 'test_g3*.py' -v`. Integration fixture `python -m tests.warehouse.check_g3_transaction` hiện có guard production analytics rỗng cho giai đoạn trước nạp; **không chạy nguyên trạng sau khi production đã có G3**. Giữ evidence trước nạp; không xóa model thật để làm guard của test cũ đạt.

## Kiểm thử, lịch sử lỗi và giới hạn

31unit và8integration trước nạp kiểm transaction chung, default dry-run, snapshot không đọc lại file, guard dispatcher, production check gọi trước insert cùng connection, unexpected-nonempty, cùng version conflict/NOOP/reload invalidated, rollback bốn pha và UNKNOWN khi mất ACK. Các test ghi chỉ trong fixture có marker, FK vào dimension fixture, được dọn; analytics thật rỗng trước/sau test. Không thử lỗi trên gói nguồn hoặc analytics thật.

Giữ FAIL integration đầu do proxy connection dùng để mô phỏng mất ACK không tương thích psycopg2 SQL formatter, gây lỗi trước COMMIT. Sửa fixture thành injection sau COMMIT thật; PASS sau đó chứng minh UNKNOWN và connection READ ONLY mới thấy model fixture đã commit. Report FAIL cũ giữ nguyên; trường đánh dấu ca đã thử không thay thế trạng thái FAIL của suite.

Giữ FAIL preflight ban đầu vì Docker Engine/API Superset không khả dụng; DB READ ONLY kiểm đạt, chưa apply. Đã mở Docker Desktop và chỉ start hai container Superset cũ, không recreate/init/reset volume. Quan sát Exited255 không xác định nguyên nhân. Hành động phục hồi dịch vụ được ghi riêng, không phải cập nhật dashboard. Cảnh báo pandas DBAPI2 của adapter P2 vẫn được ghi; không sửa P2 để che cảnh báo.

P2 intake G2 vẫn NOT_CONFIRMED. PUBLIC TEMP/chưa import-restore/chưa full refresh helperS07 với G3 vẫn là giới hạn lịch sử. Chưa dashboard11B hoặc export ba dashboard. Hậu kiểm G2 cũ đòi model inactive/rỗng không phải checker sau G3; không bỏ guard đó để ghi pipeline đạt.

Kết quả thực tế và SHA code xem phần bàn giao ở đầu tài liệu; 11B-2 WAITING_REVIEW.
