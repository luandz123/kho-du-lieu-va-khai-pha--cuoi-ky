# Hồ sơ gói tích hợp12A — WAITING_REVIEW, chưa chọn candidate cuối

## Cập nhật hiện hành 24/10/2026 — dàn ý được điều phối duyệt

Điều phối duyệt dàn ý13A và danh mục bằng chứng, giao công bố riêng trước khi viết bản thảo P1 chương1/3/4. P2 **đã báo G2 CONFIRMED**, tái lập candidate `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` trên máy Windows độc lập, Python3.12.6/PostgreSQL17.4. Nguồn là thông điệp điều phối qua người dùng, bằng chứng công bố của P2 **đang chờ điều phối review**; P1 chưa kiểm độc lập lượt P2. Không ghi đã kiểmLinux, **G4 chưa hoàn thành**. Chi tiết nguồn ở `docs/P1/p2_intake_reported_20261024.json`. Các mụcNOT_CONFIRMED/WAITING_REVIEW/OPEN bên dưới và audit13A là snapshot lịch sử, không sửa thành bằng chứng mới.

Thiếu rubric/mẫu chính thức không chặn bản thảo; không tự áp số trang/thể thức bắt buộc. Dàn ý được duyệt khác PR đãmerge; bản thảo chương chỉWAITING_REVIEW, không ghép vào PR dàn ý, khôngDOCX/slide. Không pipeline/evaluator hoặc đổi tài nguyên.

## Cập nhật hậu merge23/10/2026 — candidate đang P2 kiểm nhận

PR25 đã MERGED, API xác minh merge commit `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` tại `docs/P1/pr25_merged_observation.json`. Theo điều phối đây là candidate đang12-P2 kiểm nhận; không phải HEAD nhánh e590261… và chưa là G4đạt. P2intakeG2NOT_CONFIRMED cho tới báo cáo thực tế. Tiêu đề và các đoạn OPEN/chưa chọn bên dưới giữ như hồ sơ lịch sử trước merge; cập nhật này có hiệu lực hiện hành. Không sửa code/run hash hoặc receipt cũ, không tự chốtG4.

## Hiện hành — PR25 OPEN, WAITING_REVIEW PR12A

Đã công bố [PR #25](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/25) vào main, nhánh codex/p1-s12a-integration. API xác minh OPEN/merged=false; agent không merge. Code công bố `3334ff8388cb0627c1af3d0b0c289f08f7e6e65e`, base main/PR24 `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02`. Commit hồ sơ sau đó không đổi code; quan sát remote đầu và code_reference.json tại docs/P1/12a_publication/ ghi snapshot/version riêng, không gán commit công bố vào run cũ.

Kỹ thuật12A run57c1e8e3d3f445c4b3eeddbfc3364709 đã được điều phối chấp nhận; runtime bundle3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22/receipt/PASS/FAIL giữ nguyên. Kiểm công bố chỉ đọc file/Git/Docker inventory, không ETL/G3/dump/restore/evaluator lại. SourceP2/metric/SQLcontract/guardproduction gốc không đổi; P2intakeG2NOT_CONFIRMED, môi trường tổng Linux/P2 và DW-onlyapply riêng chưa được kiểm trênP1.

**Candidate cuối chỉ là merge commit của PR12A sau review và merge; hiện CHƯA CHỌN, không dùng HEAD nhánh. G4 chưa hoàn thành.** 8089demo và8092review healthy,8091dừng; giữ DBtíchhợp/clone/backup/metadata/volume. Không commit kế hoạch untracked ngoài phạm vi hoặc credential/user-level/privateCLI/modelbinary. Dừng chờ review PR25.

## Công bố12A — kỹ thuật được điều phối chấp nhận, PR đang chuẩn bị

Điều phối chấp nhận phần kỹ thuật12A tại run `57c1e8e3d3f445c4b3eeddbfc3364709` và giao commit/push/PR. Đây là review kỹ thuật qua điều phối, không phải lời duyệt trực tiếp của người dùng choG4. Nhánh `codex/p1-s12a-integration`; nền PR24 đã merge `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02`. Không chạy lại ETL/G3/dump/restore/evaluator để công bố.

Giữ nguyên code hash thực chạy khi chưa commit, runtime report/PASS/FAIL/receipt test; commit công bố sẽ được ghi riêng. Lệnh DW-only cho P2 ở integration_runbook.md: plan-only đã chạy, apply riêng chưa chạy trênP1; chưa kiểmLinux/P2. Metric test chỉ tham chiếu receipt đã chốt, không phải metric vừa đánh giá lại từDW. P2intakeG2 **NOT_CONFIRMED**, G4 chưa hoàn thành.

**Candidate cuối sẽ là merge commit của PR12A sau khi được review và merge. Chưa chọn HEAD nhánh làm candidate, chưa gửi mốcP2, không tự merge.** Chỉ stage phần12A đã rà; kế hoạch ngoài phạm vi/credential/backup/user-level/modelbinary/CLIprivate khôngGit. Tài nguyên giữ:DBtíchhợp,backup/clone cũ,8092đểreview;8089demo,8091dừng.

Base thực tế `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02` sau PR24 MERGED `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02`; HEAD P2 đã nghiệm thu `9ef301373ecbaa7e794215bd09465a87ac0fd363`. Nhánh `codex/p1-s12a-integration`, code12A chưa commit. **Commit candidate cuối: CHƯA CHỌN**, chưa gửi P2/chốtG4. Base không được coi là candidate đã nghiệm thu.

## Thành phần / phiên bản

- Contract2; schema/table/contractview và OLAP SQL đã duyệt không đổi. Các helper ETL/G3 chỉ đổi import sang dispatcher context; ordinary connection vẫn dùng assert_project gốc nguyên byte. Context riêng phải khớp tên/marker/owner/runID.
- Requirements tổng và venv mới tmp/s12a-venv, Python3.12.14 Windows; freeze/import/pip check trong environment.json. Superset6.1.0 riêng.88test mục tiêu đạt; chưa xác nhận môi trường tổng trên Linux.
- P2 CLI/evaluation từ PR24 giữ nguyên. Frozen CF k40/cutoff976422051; receipt chính thức chỉ đọc tham chiếu, không chạy lại evaluator.
- G3 local frozen producer bab0b4049d4e0b1724418b8a92d8afbeda4bc775; model kmeans_k4_seed42. Không tái tạo package, không đổi metadata/library/provenance theoHEADmới.

## Hash nguồn / cấu hình / gói

Canonical hashes:

```json
{
  "users": "7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f",
  "movies": "154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b",
  "movie_genres": "9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf",
  "ratings": "06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf"
}
```

Source hashes:

```json
{
  "users.dat": "1dc3a95300cb19f7c10e027daf29b8cdf1d908dab65b5edfb45950aa389a10a3",
  "movies.dat": "0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9",
  "ratings.dat": "506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f",
  "README": "2d5ddce86ccbd247207456165827b4b9ddf27282bca93807d4c763e28414f133"
}
```

G3 training_config_hash `8fc755ef7234422a556c5fa725520ddd985a3aeeaef92cbb4362d9e21c2c0786`, manifestSHA `630453504b71c6b3e38e022f760e2c37a2612a418d3dfdfbf448794c7297d0f0`. Hai CSV frozen:

```json
{
  "user_cluster.csv": "5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93",
  "cluster_genre_profile.csv": "59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d"
}
```

CF config_hash lấy từ receipt đã nghiệm thu, không tự đặt lại; metrics/source hash ghi trong official_test_metrics_reference.json. BundleSHA **3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22** là SHA256 của JSON sorted/separators(',',':') trên dictionary summary.code_sha256; từng code/config/SQL thực chạy được băm riêng trong summary. Không gán base như thể chứa code chưa commit.

## Hai chu trình thực tế

Run `57c1e8e3d3f445c4b3eeddbfc3364709`, tổng `833.922` giây; database `movielens_btl_int_20261023_57c1e8e3` mới, owner/marker riêng, không đụng demo hoặc clone backup.

| Kiểm | Chu trình1 | Chu trình2 |
|---|---|---|
|ETL transaction|COMMITTED|COMMITTED|
|Bốn canonical/count|Khớp manifest|Khớp manifest, không tăng dòng|
|Registry sauETL|0, chưa có model|Giữ1row, active=0/valid=0|
|Kết quả cụm sauETL|Rỗng/activeviews rỗng|Rỗng/activeviews rỗng|
|Nạp G3|INSERT_NEW_VERSION|RELOAD_IDENTICAL_INVALIDATED_VERSION|
|Hậu kiểm G3|6040user/72profile, activevalid|Cùng identity/payload, không trộn phiên bản|
|Apply kiểm lại|COMMITTED_NO_OP|COMMITTED_NO_OP|
|Registered_at|Lưu lầnđầu|Giữ nguyên|
|ML CLI DW|2evaluation/1demo, exit0|Cùng3ca, exit0|
|Dashboard8092 forcequery/filter|Cả3dashboard đạt|Cả3dashboard đạt|

Chu trình mỗi lần ghi file riêng cycleN_etl.json, cycleN_dw_before_model.json, cycleN_g3.json. SQL OLAP6view cài một lần, tái dùng trên DW refresh; bổ sung O1–O6 READONLY sau ETL2 và trước G3(active0), đồng thời inference, ở olap_all_six.json. Không mô tả thao tác này như đã chạy trước CLI1. Các đối soát dashboard O4/O5 chạy sau G3 trong mỗi chu trình; G3 không thay nguồn metric OLAP. KPI1000209/tổng3582313,6.040user/3.706phim córating. Q3/2000=324864; Animation1715/prev20068/QoQ−91.454056%/mẫu63335; assigned6038/170,baseline6038,insufficient2,heatmap18genre chỉfiltercluster.

## Lệnh thực và bằng chứng

```powershell
.\tmp\s12a-venv\Scripts\python.exe -m pip check
.\tmp\s12a-venv\Scripts\python.exe -m pytest tests/warehouse/test_integration_target.py tests/warehouse/test_s06d_refresh.py tests/warehouse/test_g3_dispatcher.py tests/warehouse/test_s07_catalog.py -q
.\tmp\s12a-venv\Scripts\python.exe -m pytest tests/warehouse/test_s05_staging.py tests/warehouse/test_s06a_dimensions.py tests/warehouse/test_s06b_bridge.py tests/warehouse/test_s06c_fact.py -q
.\tmp\s12a-venv\Scripts\python.exe etl/run_integration.py --apply
.\tmp\s12a-venv\Scripts\python.exe tests/warehouse/check_integration_result.py --run 57c1e8e3d3f445c4b3eeddbfc3364709
```

Apply đã chạy; không chạy lại chỉ để review vì sẽ tạo DBthử mới. Postflight chỉ đọc; seed/history/recommendation outputs và rawCLIlogs ignored. Cycle1 privatefiles được sao lưu trước cycle2; hậu kiểm so SHA từng cycle với output thực, không công bố lịch sử user. Metric test là tham chiếu P2 đã nghiệm thu, không phải số đo12A.

## P2 tự tái tạo và điều kiện đạt

[Runbook](integration_runbook.md) đi đúng thứ tự môi trường/tải nguồn→schema→staging/ETL→DW→OLAP→ML→G3→Superset, có lệnh DW-only không cần nhận dump/Superset. P2 tự tải nguồn/sohash, dùng localcredential và DBmới; `etl/recreate_integration_dw.py` defaultplan-only đã kiểm, đườngapply riêng chưa được chạy thêm trênP1; core transaction/guard/serializer đã được kiểm trong hai chu trình chính. P2 phải gửi xác nhận từ máy mình; **P2 intakeG2 NOT_CONFIRMED**.

Điều kiện đề nghị review: hai chu trình COMMITTED,4hash/count giống nhau,modelinvalidate/reload/NOOP đúng,registryidentity giữ,MLDW/seed/cutoff và3dashboard đúng; nguồn8089/DW/model/ACL không đổi; khôngsửaP2/receipt/source. READONLY hậu kiểm ghi riêng khi chạy xong. Chưa candidatecuối/PR/commit/push/G4 hoặc báo cáo cuối.

Giới hạn: same-host Windows/PG17.11/Superset6.1.0, dữ liệu lịch sử; không kiểm Linux/two-machine/off-machine DR trong lượt này. Metadata restore/DW clone/backup cũ giữ nguyên,8091dừng;8092giữ kết nối DBtíchhợp. Biến môi trường local, PUBLIC TEMP theo mặc định; không cấpDML/CREATE/admin hoặc đổi production/firewall. Cảnh báo pandas DBAPI2 giữ minh bạch, dữ liệu được kiểm byte/hash.
