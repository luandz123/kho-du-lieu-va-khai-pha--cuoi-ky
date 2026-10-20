# 11B-1 — Kiểm nhận G3 và loader dry-run (WAITING_REVIEW)

Điều phối xác nhận PR15 đã merge tại `371aab7e43742dc1e5c330077ffbd49fcef5fe09` và chấp nhận công bố11C. API và Git đã xác minh; agent không merge. Báo cáo OPEN cũ giữ nguyên, quan sát mới ở `docs/P1/trends_post_merge_observation.json`.

## Nguồn gói và môi trường

Không có gói G3 cục bộ khi bắt đầu. Đã tái tạo một lần bằng code P2 đã merge, commit gần nhất sửa `mining/clustering.py` là **bab0b4049d4e0b1724418b8a92d8afbeda4bc775**, checkout main/base **371aab7e43742dc1e5c330077ffbd49fcef5fe09**. Không sửa file P2 hoặc hash kỳ vọng. Đây là **gói tái tạo tại P1**, không phải xác nhận P2 đã trực tiếp chuyển gói hoặc nhận G2.

Môi trường riêng ignored `tmp/g3_venv`: Python3.12.14 Windows, numpy2.0.2, pandas2.3.3, scipy1.14.1, scikit-learn1.5.2, matplotlib3.10.7; OMP/OPENBLAS/MKL threads=1. Python patch/OS khác P2 Linux3.12.3, nhưng hai checksum frozen thực tế **khớp tuyệt đối**. Manifest ghi đúng runtime P1, không giả thành runtime P2. Không cài hoặc đổi dependency `.venv` P1; freeze trước/sau khớp requirements-p1 đã có. Chi tiết provenance/config/library tại `results/warehouse/s11b1/reproduction.json`.

Bốn canonical CSV lấy từ export G2 cục bộ đã có tại `data/processed/p1_g2_c75f9cb0ceb04d74bfa36e140d812754`, băm từng byte khớp manifest trước khi copy vào bốn đường dẫn canonical đang thiếu ở `data/processed/`. Không ghi đè dữ liệu sẵn có, không sửa raw hoặc manifest P2. CLI P2 tiếp tục kiểm hash dữ liệu thực nạp và frozen fingerprint.

Gói mới nằm tại **data/processed/p1_g3_20261020_intake/**, gồm đủ3file, toàn bộ ignored. Không đưa CSV user-level lên Git. Hai CSV được băm lại độc lập, không tin riêng manifest:

| Tệp | SHA-256 thực tế |
|---|---|
|user_cluster.csv|5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93|
|cluster_genre_profile.csv|59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d|
|manifest.json|630453504b71c6b3e38e022f760e2c37a2612a418d3dfdfbf448794c7297d0f0|

Không chạy lại producer trên thư mục đã có gói. Ba `os.replace` của producer **không nguyên tử trên toàn gói** khi lỗi I/O; consumer yêu cầu đủ3file, đọc thành snapshot trong bộ nhớ, kiểm lại byte mỗi thành viên và checksum/fingerprint trước khi kết nối DB. Gói thiếu, thay đổi giữa lúc đọc hoặc hỏng bị từ chối; không sửa giá trị kỳ vọng cho khớp.

## Kiểm nhận thực tế

`etl/g3_intake.py` tách `read_package`/`validate_records` khỏi `check_dw` và không có CLI ghi production. Đã kiểm contract2, version **kmeans_k4_seed42**, algorithm/K=4/seed42/n_init10/raw, thứ tự18genre, user order hash, training config hash theo serializer P2, UTC, row_count/checksum, source/canonical hashes và provenance code P2. Hash source code được phân biệt LF Git với CRLF checkout Windows; byte dữ liệu nguồn/CSV không chuẩn hóa lại.

Kết quả: **6040 user gốc duy nhất**, đủ FK dim_user; **6038 assigned**, **2 insufficient_evidence có cluster NULL**. Cụm0..3: **2478 /1393 /760 /1407**. Profile đủ **72 khóa=4×18genre**, tên khớp dim_genre; mean hữu hạn [0,1], tổng mỗi cụm bằng1 trong1e-8; n_users đúng quy mô assigned. Không lưu ID thật của hai user thiếu bằng chứng trong bằng chứng Git.

Dry-run cuối **14c7eb52e34a4b0da6b0c158b56175cd**, report `intake_run_02.json`, kết nối `movielens_btl`, **transaction_read_only=on**, khóa advisory shared cùng họ khóa ETL. Đã đọc/băm mới cả bốn view DW bằng adapter/serializer P2, khớp gói, G1 và manifest G2:

| View | Số dòng | SHA-256 |
|---|---:|---|
|dw.v_ml_users|6040|7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f|
|dw.v_ml_movies|3883|154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b|
|dw.v_ml_movie_genres|6408|9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf|
|dw.v_ml_ratings|1000209|06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf|

Marker/catalog khớp thiết kế. Registry/user_cluster/profile thật đều **0 trước/sau**, active views rỗng; không INSERT/UPDATE/TRUNCATE analytics. Mapping dùng user_id nguồn trực tiếp, genre_name nguyên gốc; profile lấy model_version từ cùng manifest, không dùng surrogate cho gói. Plan: INSERT registry inactive →6040user rows →72profile rows →đối soát cùng connection →activate.

## Transaction và chính sách chạy lại

`etl/g3_transaction.py` là engine chuẩn bị, **chỉ cho thực thi trong schema fixture P1 có UUID, marker và ownership đúng**. Gọi với `analytics` bị từ chối `PRODUCTION_WRITE_DISABLED_11B1`; chưa có `--apply`. Việc mở dispatcher ghi production thuộc lệnh11B-2 sau review, chưa tuyên bố production loader đã chạy.

Kế hoạch production sau khi được phép: kiểm package ngoài DB trước; bắt đầu một transaction READ COMMITTED; lấy advisory exclusive `(20261027,1)` cùng ETL, khóa dimension để đọc ổn định và ba bảng analytics để ghi. Kiểm lại marker/catalog, bốn hash, cohort và registry bằng cùng connection **sau khi có khóa**. Không gọi nối nhiều CLI/connection. Tạo registry inactive/invalid, nạp hai bảng, kiểm toàn hàng/FK/miền/grid/profile/metadata trước COMMIT; cuối cùng hạ active cũ và active+valid phiên bản mới. Một lỗi rollback toàn bộ, kể cả active model cũ. Không thay DDL hoặc guard full-refresh ETL.

Preprocessing jsonb hiện có lưu object `{method,training_config,g3_payload_sha256,code_provenance}`; registry còn lưu riêng libraries/source/canonical/config hash/K/seed/genre_order/model_created_at. Không thêm cột. Đây là ánh xạ metadata của loader cần review; không thay công thức đặc trưng hoặc label cụm. Manifest đầy đủ vẫn giữ cục bộ; registered_at khác thời điểm model_generated_at.

- Cùng version, payload/config/provenance/libraries và toàn bộ hàng đã lưu giống, active+valid: **NO-OP**, không cập nhật registered_at.
- Cùng identity, rows đủ nhưng inactive: chỉ dự kiến reactivate sau đối chiếu DW mới.
- Full refresh giữ registry nhưng đã invalid/inactive và cả hai bảng kết quả của version rỗng: cho phép dự kiến reload cùng identity sau đối chiếu DW mới. Không tự chạy ETL để tạo tình trạng này.
- Cùng version nhưng checksum/config/provenance/library hoặc hàng lưu khác: **từ chối conflict**, kể cả version đang inactive. Không ON CONFLICT DO NOTHING/UPSERT/ghi đè để né lỗi. Metadata thiếu payload identity trong registry cũ cũng bị chặn, cần điều phối review.
- Manifest tái tạo khác thời điểm nhưng cùng payload/metadata identity không tự thành phiên bản mới; không đổi nhãn để ép khớp. Mất kết nối lúc COMMIT phải ghi kết quả chưa xác định và kiểm lại, không suy rollback.

## Kiểm thử và bằng chứng

**23/23 unit tests đạt**, fixture tự tạo và độc lập với gói thật: checksum/frozen mismatch, gói thiếu, encoding, trùng/mồ côi/thiếu user, status/NULL/cluster/version sai, profile thiếu/trùng/lạ genre, NaN/Infinity/ngoài miền, sum sai, n_users lệch, version conflict, guard production. Tests đọc package không kết nối DB. Một FAIL ban đầu do snapshot dict dùng chung tham chiếu mutable đã được sửa bằng deepcopy; report FAIL và PASS trước/sau giữ riêng.

**5/5 integration tests PostgreSQL đạt**, chỉ trong schema `p1_g3_fixture_<UUID>`, dùng cấu trúc LIKE bảng đã duyệt, khôi phục FK vào dimension fixture. Kiểm activate sau đủ hàng, rerun NO-OP, từ chối cùng version payload khác, reload version invalidated, và rollback tại **registry/users/profiles/activate** đều phục hồi chính xác fingerprint snapshot cũ và active model cũ. Ba bảng analytics thật0 trước/sau; schema fixture đã dọn đúng ownership/marker. Report `transaction_fixture.json`, không sửa report PASS đầu tiên. Chưa thử mất kết nối lúc COMMIT.

Không chạy lại ETL/Superset11A11C. Pandas phát cảnh báo DBAPI2 psycopg2 không thuộc kiểu kết nối chính thức của read_sql; thao tác đọc thực tế và bốn hash vẫn đạt. Giữ cảnh báo này làm giới hạn adapter, không sửa file P2 hoặc tuyên bố đã dùng SQLAlchemy. Dry-run READ ONLY là thuộc tính transaction hiện tại, không đồng nghĩa tài khoản admin biến thành reader.

## Lệnh (PowerShell từ workspace)

```powershell
# Dry-run: dùng report path mới để giữ lịch sử, không ghi DB.
.\.venv\Scripts\python.exe -m etl.g3_intake --package data/processed/p1_g3_20261020_intake --dry-run --report results/warehouse/s11b1/intake_review_new.json
.\.venv\Scripts\python.exe -m unittest discover -s tests/warehouse -p test_g3_intake.py -v
# Integration chỉ tạo/dọn schema fixture; lưu report cũ trước khi chạy lại.
.\.venv\Scripts\python.exe -m tests.warehouse.check_g3_transaction
```

Lệnh tái tạo đã thực hiện và full freeze ở reproduction.json; nếu cần tái tạo nữa phải chọn **thư mục mới chưa tồn tại**, kiểm bốn CSV đầu vào trước, dùng `tmp/g3_venv/Scripts/python.exe mining/clustering.py --mode reproduce --source csv --outdir <thu_muc_moi> --results-dir <tmp_moi>`. Không thêm `--mode explore/all`, không bỏ frozen fingerprint. Không tự cài vào `.venv` P1.

## Bàn giao và điểm cần review

Nhánh **p1-s11b-cluster-intake**, HEAD/base **371aab7e43742dc1e5c330077ffbd49fcef5fe09**. File mới:2module etl,2test, `results/warehouse/s11b1/` chỉ metadata/aggregate/fixture, tài liệu này và quan sát merge11C. Cập nhật S11/STATE/DECISIONS/REVIEWS/PROMPTS; ledger và SHA cuối tại `results/warehouse/s11b1/handoff_manifest.json`. Kế hoạch untracked ngoài phạm vi giữ nguyên. **Chưa stage/commit/push/PR**.

Cần điều phối review G3 thực so DW, mapping metadata registry, chính sách cùng version/invalidated và engine fixture trước khi giao11B-2. Gói kiểm nhận tại P1 không thay trạng thái **P2 intake G2 NOT_CONFIRMED**. Chưa load analytics, dashboard11B, export/import ba dashboard, đổi quyền hoặc firewall. **11B-1 WAITING_REVIEW**, dừng.

Ý bảo vệ: (1)checksum byte chống gói lẫn/hỏng, manifest không tự chứng minh dữ liệu; (2)ID nguồn và fingerprint DW giữ cùng cohort; (3)hai user thiếu bằng chứng không bị ép vào cụm; (4)metadata version và active views tránh trộn phiên bản; (5)dry-run đọc khác nạp thật, transaction rollback giữ nguyên model trước.
