# BTL Kho dữ liệu và Khai phá dữ liệu

## Hiện hành — PR #21 OPEN, WAITING_REVIEW PR

Đã công bố [PR #21](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/21) vào main, nhánh `codex/p1-s12a-prep`. GitHub đã xác minh OPEN/merged=false; agent không merge. Code công bố/tái tạo tại `a32dfcb407009fd5d404035d6c82d787e0411505` (đã tích hợp main `9efa05379fc8323f1b656632e140ac5a3a4354ea`); commit hồ sơ sau đó không đổi code/runtime. Quan sát remote từng thời điểm và danh sách file tại docs/P1/pre12a_publication/remote_observation.json; HEAD đó là snapshot lịch sử trước commit hồ sơ, không gán vào run cũ.

Điều phối đã chấp nhận chức năng chuẩn bị DW/kiểm kê/metadata restore. **PR WAITING_REVIEW, chưa MERGED; chưa PR chốt12A/G4.** Giữ giới hạn database-level ACL clone khác nguồn; cùng máy/version/DW hiện hữu; ZIP import vẫn cần REST layout. Chưa kiểm full refresh sauS07/G3, nghiệm thu CF/CLI cuối, P2 intakeG2, requirements tổng hoặc candidate. Dump/env/key/config private/rawlogs/user-level và kế hoạch ngoài phạm vi không Git. Giữ FAIL/lịch sử metadata chưa restore; kết quả metadata đạt ghi trong receipt mới riêng. Không tạo lại tài nguyên để công bố.

## Công bố phần chuẩn bị tích hợp — 21/10/2026

Điều phối chấp nhận backup/restore DW, kiểm kê và metadata restore riêng8092; đang đóng gói PR trên `codex/p1-s12a-prep`, **chưa phải PR chốt12A/G4**. [Runbook DW/kiểm kê](docs/P1/integration_prep/README.md), [metadata restore](dashboard/metadata_restore/README.md) và receipt mới phân biệt với ZIP import/REST layout. Giữ nguyên báo cáo lịch sử. Database-level ACL DW clone khác nguồn; giới hạn same-host/version/DW hiện hữu vẫn áp dụng. Chưa full refresh tích hợp, nghiệm thu CF/CLI cuối, P2 intake G2, requirements/candidate.

## Chuẩn bị tiếp: metadata restore 8092 — WAITING_REVIEW, 21/10/2026

Phần backup/restore DW và kiểm kê trước 12A đã được điều phối chấp nhận, lưu checkpoint cục bộ `d3f00cc6a068868662a7040459a51ff46e49e231`. Đã restore metadata Superset 6.1.0 vào instance riêng 8092 bằng pg_restore, dùng bản SECRET_KEY/config đã backup. [Runbook và bằng chứng metadata restore](dashboard/metadata_restore/README.md) phân biệt rõ metadata restore với DW restore và ZIP import cần REST layout. Hồ sơ trước ghi metadata chưa restore được giữ nguyên làm lịch sử. **Chưa chốt 12A/G4**, CF/Bước10 P2 còn chờ, P2 intake G2 NOT_CONFIRMED. Không full refresh, hợp nhất requirements, chọn candidate hoặc push/PR.

## Chuẩn bị trước 12A — WAITING_REVIEW, 21/10/2026

PR18 đã xác minh MERGED tại `0692822ceb5cba0e523ec45629bdea31a0d45562`; báo cáo OPEN bên dưới giữ lịch sử. Đang trên `codex/p1-s12a-prep`, **chưa đủ tiền đề/chưa hoàn thành12A/G4**, chưa chọn commit ứng viên hoặc hợp nhất requirements. CF/CLI/evaluation cuối/Bước10P2 đang chờ; P2intakeG2NOT_CONFIRMED; chưa fullrefresh tích hợp sauS07/G3.

[README chuẩn bị và inventory](docs/P1/integration_prep/README.md), [checklist sơ bộ](docs/integration_checklist.md), [bằng chứng backup/restore](results/warehouse/s12a_prep/): DW đã pg_dump nhất quán vàrestore vàoDBthửmới, bốncanonical/catalog/model/OLAP khớp. MetadataSuperset mớibackup/kiểmarchive, **chưarestoremetadata**. Dump/rawlog/secretconfig chỉ nằmlocalignored; không chạy lại--apply đểreview, không dùngguardproductiontrênclone. ZIPdashboard vẫn cần snapshot+UUIDmapping+RESTlayout, không phảiDWbackup. GiữDBcloneđểreview; chưacommit/push/PRlượtchuẩnbị, chưa12A/cuốibáocáo.

## Công bố toàn bộ 11B — được điều phối chấp nhận, chờ review PR

[PR #18](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/18) **OPEN**, chưa merge. Code tái lập `050b601c916b7b4f6be476640673c9978e0ba979`; [snapshot kiểm remote lúc mở](docs/P1/11b_publication_remote.json) và [danh sách toàn PR](docs/P1/11b_pr_files.json). Commit hồ sơ mới không thay hash runtime lịch sử.

11B-1 kiểm nhận G3/dry-run, 11B-2 loader transaction/NO-OP, 11B-3 dashboard sở thích và 11B-4 export/import + phục hồi bố cục trên instance riêng8091 đã được điều phối chấp nhận theo phạm vi tương ứng. Hồ sơ PR/commit/kiểm công bố: [11B publication](docs/P1/11b_publication.md). Các nhãn chờ duyệt/ZIP ignored/chưa11B trong tài liệu/báo cáo cũ bên dưới là quan sát lịch sử, không ghi lại run cũ thành commit mới.

Tái lập cấu hình dashboard cần **đủ bộ**, không chỉ ZIP:

- [ZIP export thật ba dashboard](dashboard/superset_export.zip), đúng SHA-256 `b5a9c987e7d1e7f56b21f92785370cdb9089a4d1efc01c128568127d938f6fae`.
- [Snapshot bố cục và cấu hình nguồn](dashboard/restore/evidence/production_before.json) và [mapping UUID/ID quan sát ở8091](dashboard/restore/evidence/uuid_mapping.json).
- [Script import + phục hồi bố cục qua REST API](dashboard/restore/import_bundle.py), [hướng dẫn credential local và tái lập](dashboard/restore/README.md), [bàn giao restore](docs/P1/dashboard_restore_handoff.md).
- [G3 intake](docs/P1/g3_intake.md), [loader](docs/P1/g3_load.md), [dashboard sở thích](docs/P1/preferences_handoff.md).

ZIP nguyên bản có ô layout legacy thiếuUUID, exporter thêm ô orphan. Script import trên **instance mới rỗng**, remap theoUUID rồi PUT layout bằng API để giữ8/5/10ô; không tuyên bố ZIP tự import hoàn chỉnh. Không import vào8089 hoặc chạy lại instance8091 đã có dữ liệu. ZIP duy nhất này được phép Git, các ZIP khác và credential/raw/processed/góiG3/user-level vẫn bị ignore. Không chỉnh ZIP hoặc production để che giới hạn.

Producer gói active giữ commit `bab0b4049d4e0b1724418b8a92d8afbeda4bc775`, không đổi theoHEAD mới. Guard P1 kiểm provenance lịch sử từ blob commit đó và vẫn chặn fileP2 bẩn; không tái tạo model/đổi manifest. Xác minh41test trong checkout tích hợp main, giữ lỗi compatibility trước sửa để truy vết. Giới hạn: cùng máy/Superset6.1.0/DW hiện hữu; chưa backup/restore DW, kết nối hai máy hoặc P2 intakeG2 (`NOT_CONFIRMED`); chưa full refresh mới với helperS07/G3, PUBLIC TEMP còn. Instance8091 vàvolume thử giữ để review. Không tự merge hoặc chuyển12A.

Quan sát mới: PR14 đã MERGED bên ngoài agent tại 5a42c73c39c00780b2d5442c45662d93bdf0f23b; agent không merge. Gói công bố ef82fc4 gồm50file/blob đã kiểm. Hồ sơ trạng thái sau mởPR đang local/chưa commit-push, xem docs/P1/overview_post_merge_observation.json; các mụcOPEN dưới đây giữ lịch sử. Dừng, chưa11C/11B.

Hiện hành19/10/2026: [PR #14 — 11A](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/14) OPEN/chờ review, chưa merge/11C/11B. 11A đã được điều phối chấp nhận chức năng; các mục chưa được giao công bố/chưa commit phía dưới giữ lịch sử. Hồ sơ mới docs/P1/overview_publication.json.

11A đã được điều phối chấp nhận chức năng và giao công bố PR; chưa merge/11C/11B. Hồ sơ công bố mới: docs/P1/overview_publication.md; các trạng thái chờ review kết quả bên dưới giữ lịch sử.

## Hiện hành — 11A Tổng quan chờ review

PR13 S07 đã MERGED tại `988874d7b5897a5615acfebdf571c6d55861ddc2`. Dashboard thật: http://127.0.0.1:8089/superset/dashboard/1/ . **11A WAITING_REVIEW**, database1/datasets1–2/charts1–8; xem docs/P1/overview_handoff.md và docs/agent/steps/P1/S11.md. Chưa commit/push/PR11A, chưa 11B/11C/G3. Các trạng thái OPEN/chưa dashboard phía dưới là lịch sử.

S07 đã được điều phối chấp nhận ở mức kết quả; [PR #13](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/13) OPEN/chờ review, chưa merge/dashboard. Hồ sơ công bố: docs/P1/s07_publication.md. Report/ledger thực chạy giữ lịch sử; phần kiểm và trạng thái mới ghi riêng.

## Cập nhật S07 — PR9 đã MERGED; các mục công bố phía dưới là lịch sử

Điều phối xác nhận PR9 G2 MERGED tại ad51ba6536d0468c05b833ac05be9f18e9d9d87f bởi hungvu205, agent không merge. Code ETL công bố tái tạo 4fa9cf17aa41e5ff84d4490886eeac27971e46f6; snapshot G2 run6501a547 giữ nguyên. Hồ sơ500b293 và observation hậu merge đã ghép chọn lọc trên p1-s07-olap, chưa công bố PR mới. Report công bố OPEN/run cũ giữ nguyên để truy vết.

S07 thêm sáu view tổng hợp analytics, không đổi bốn view contract/bảng. Có hậu kiểm chỉ đọc khớp G2; không chạy lại full refresh. Catalog helper chỉ mở allowlist bộ sáu view; hash S07 không thay bundle lịch sử. Kết quả S07 WAITING_REVIEW, xem docs/agent/steps/P1/S07.md và docs/P1/olap_findings.md (tính từ gốc repository). Chưa dashboard/G3/quyền BI; P2 intake NOT_CONFIRMED và dedicated_read_only_account_verified=false.

---

MovieLens 1M → PostgreSQL staging/DW → Python ETL → 6 OLAP → K-Means và item-based CF/Popularity Baseline → 3 dashboard Apache Superset. Bảo vệ **27/10/2026**.

## Trạng thái nền G0

Bước 1 đã được người dùng duyệt. **Python 3.12** là dòng phiên bản chung; P2 báo đã có môi trường 3.12.3/Linux, P1 chưa thiết lập 3.12 trong checkout này. `main` là nhánh mặc định. Nhánh G0: `p1-g0-contract`; các nhánh mới không có tiền tố `codex/` theo quyết định nhóm ngày15/10/2026.

G0 đã MERGED qua PR #1, main tại `eff54aee`. Bước 2-P1 đã được người dùng duyệt chức năng (P1-S02-v2) và giao đẩy nhánh `p1-s02-env`; merge cần xác nhận riêng. SELECT1 từ Windows và container đều đạt17.11; health/login Superset200. View DW/roleBI chỉ đọc, đăng nhập UI và dashboard chưa nghiệm thu. ETL, mô hình và dashboard nghiệp vụ chưa triển khai ở bước này.

## Môi trường P1 tại Bước 2

Đã tạo `.venv` **Python 3.12.14**, cài và kiểm chứng thư viện P1; khóa phiên bản tại [requirements P1](docs/P1/requirements-p1.txt). [requirements.txt](requirements.txt) hiện chỉ dẫn vào bộ P1; hợp nhất dependency P2 ở12A sau kiểm chứng. Không coi báo cáo môi trường P2 là kết quả chạy P1 hoặc ngược lại.

Runtime nền dùng bản3.12.14 có sẵn tại `C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`, không cài toàn hệ thống. `.venv` tách site-packages nhưng còn phụ thuộc runtime nền; nếu cache này thay đổi/mất phải tạo lại bằng Python3.12 đã kiểm chứng. Không chép `.venv` sang máy khác.

Từ PowerShell tại thư mục dự án:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -m pip check
python tests/warehouse/check_environment.py --db --env-file .env --report results/warehouse/environment_check.json
python tests/warehouse/check_superset.py --env-file .env
```

Nếu chính sách PowerShell chặn kích hoạt, không cần đổi policy toàn hệ thống: dùng trực tiếp `.\.venv\Scripts\python.exe` thay `python`. Tạo lại môi trường trên máy đã có Python3.12: chạy runtime3.12 với `-m venv .venv`, rồi `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

`.env` gốc đã được tạo cục bộ bằng mẫu. Người dùng tự điền tên database **đang tồn tại**, user được phép kết nối và mật khẩu vào POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD; không gửi chat/commit. Bước2 không tự tạo database hoặc đoán account. Checker chỉ đọc tệp được chỉ định rõ, không in cấu hình/exception thô, không tạo bảng. Exit0: kiểm tra yêu cầu đạt; exit2: thiếu cấu hình SQL; exit3: kết nối SQL lỗi; exit1: môi trường/dịch vụ lỗi. SELECT1 trong SQLite hoặc metadata Superset không thay bằng chứng SELECT1 PostgreSQL Windows.

Superset dự án6.1.0 đã khởi động tại http://127.0.0.1:8089/login/; health/login trả200, metadata riêng healthy. [Hướng dẫn Superset](dashboard/superset/README.md) và [hồ sơ môi trường P1](docs/P1/environment.md). Trang login mở được chưa chứng minh user đăng nhập hoặc quyền đọc DW. Giữ nguyên Superset cũ8088/dịch vụ khác. Chi tiết kiểm tra không bí mật tại results/warehouse/; thiếu SQL đăng nhập hiện tại không được đánh dấu đạt.

Môi trường ảo là nơi chứa thư viện riêng của dự án; dependency là các thư viện cần chạy chương trình, được khóa phiên bản để tái lập. Biến môi trường/cấu hình cục bộ cung cấp thông tin kết nối; chúng không thay thế quyền truy cập thật trên database.

## Tài liệu cần đọc

- [Đặc tả Q1–Q3 và lịch](docs/project_spec.md)
- [Nghiệm thu nội bộ](docs/acceptance.md) — rubric chính thức chưa xác minh
- [Hợp đồng dữ liệu v2](docs/shared/data_contract.md) và [JSON](docs/shared/data_contract.json)
- [Quy trình GitHub, quyền file và G0–G5](docs/shared/github_workflow.md)

Rating là đánh giá, timestamp là thời điểm đánh giá. Q1 mô tả nhóm sở thích/nhân khẩu học lịch sử; Q2 gợi ý Top5 và đánh giá độc lập; Q3 phân tích count/QoQ theo quý trong dữ liệu. Không suy lượt xem, nhu cầu hiện tại hoặc doanh thu.

## P2 nhận mốc nền sau khi G0 đã merge

Chỉ chạy sau khi xác nhận PR G0 đã merge. Clone vào **thư mục mới chưa tồn tại**, không chép đè checkout đang có thay đổi:

```powershell
git clone https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky.git BTL_MovieLens_P2
cd BTL_MovieLens_P2
git switch main
git pull --ff-only origin main
git log -1 --oneline
```

Nếu P2 đã có checkout riêng (đã có PR môi trường), giữ checkout đó: kiểm tra `git status`, bảo toàn thay đổi trên nhánh P2 rồi fetch/pull hoặc merge `origin/main` khi sạch; không clone đè và không tự reset. Sau đồng bộ, đọc/xác nhận contract2 theo commit G0 đã merge. Chỉ bắt đầu EDA khi contract được cả hai xác nhận và có lệnh giao bước3; tạo nhánh mới, ví dụ `p2-s03-eda`, từ main mới nhất. Giữ nguyên PR môi trường đang chờ review, không tự merge PR đó.

## Cấu hình và dữ liệu cục bộ

**Cập nhật công bố ETL/G2:** điều phối chấp nhận6D cục bộ; **[PR#9 OPEN, chờ review](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/9)**, chưa merge/P2 nhậnG2. Codecommit **4fa9cf17aa41e5ff84d4490886eeac27971e46f6**; [hồ sơ công bố](docs/P1/g2_publication.md) phân biệt commitcode với base/hash runtime và liệt kê đủ65file. Giữ report lịch sử, chưa xác minh tài khoản chỉ đọc/P2 remote, không chia sẻ credential quản trị. Các trạng thái WAITING_REVIEW6D/chưapush dưới đây là lịch sử tại bàn giao.

Hiện hành **6D WAITING_REVIEW**, 6C được điều phối chấp nhận: full refresh chung một transaction đã chạy hai lần, cùng code/config và bốn hash/count;65unit/fixture rollback/adapter rawCSV DW/hậu kiểm chỉ đọc PASS. [Bàn giao6D](docs/P1/s06d_handoff.md), [gói DW](docs/P1/dw_handoff.md), [manifest](results/warehouse/dw_manifest.json). Hậu kiểm tích hợp chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_warehouse.py --env-file .env`; tái tạo có ghi: `python -m etl.run_etl refresh --env-file .env`. Không dùng checker/CLI tiểu bước cũ cho full refresh. Metadata G2 chờ review và xác nhận P2; chưa push/PR/OLAP/dashboard/G3. Các mục dưới là lịch sử.

Hiện hành **6C WAITING_REVIEW**, 6B đã được điều phối chấp nhận: fact/view ratings **1000209** dòng, tổng điểm **3582313**, bốn hash canonical khớp; staging/dimension/bridge giữ nguyên, analytics rỗng. [Bàn giao6C](docs/P1/s06c_handoff.md), [summary6C](results/warehouse/s06c_summary.json). Hậu kiểm chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_warehouse.py --env-file .env`. Không chạy lại loader cũ/6C hoặc checker6B đòi fact rỗng; chưa6D/G2/OLAP/dashboard. Các đoạn dưới là lịch sử từng mốc.

Hiện hành **6B WAITING_REVIEW**, 6A đã được điều phối chấp nhận: bridge có **6408 cặp**, staging/dimension giữ nguyên, fact/analytics rỗng. Xem [bàn giao 6B](docs/P1/s06b_handoff.md) và [summary](results/warehouse/s06b_summary.json). Hậu kiểm chỉ đọc: `.\.venv\Scripts\python.exe -X utf8 -m etl.s06b_bridge verify --env-file .env`. Không chạy lại load S05/6A/6B hoặc checker6A cũ đòi bridge rỗng; chưa 6C/6D/G2. Các đoạn hiện hành cũ bên dưới giữ lịch sử từng mốc.

Hiện hành 6A: bốn dimension đã nạp và đang WAITING_REVIEW; xem [bàn giao 6A](docs/P1/s06a_handoff.md) và [bằng chứng](results/warehouse/s06a_summary.json). Staging giữ nguyên, bridge/fact/analytics vẫn rỗng; **không chạy lại load S05 sau 6A**, chưa full refresh tích hợp/G2. Đoạn S05 dưới đây là lịch sử trước khi nạp dimension.

S05 đã tạo cấu trúc được duyệt tại database riêng `movielens_btl` và nạp raw staging, đang WAITING_REVIEW. Xem [hướng dẫn S05](etl/README.md), [bàn giao](docs/P1/s05_handoff.md) và [bằng chứng tổng hợp](results/warehouse/s05_summary.json). Chưa nạp dimension/bridge/fact, chưa G2; các hướng dẫn/mốc trước trong README là lịch sử tương ứng, không cấp quyền tự chạy bước tiếp.

`.env.example` là mẫu không bí mật. `.env` gốc phục vụ PostgreSQL Windows; `dashboard/superset/.env` phục vụ metadata/admin Superset và giữ key cũ khi kế thừa volume. Hai file này và `.venv` chỉ nằm cục bộ, không đưa lên Git. Không chuyển nguyên `.venv` giữa máy/checkouts.

Mỗi máy tự tải MovieLens từ nguồn chính thức và đối soát hash theo contract. Không đưa raw/processed, dữ liệu theo user, gói cụm, mô hình lớn, dump, metadata/volume Superset hoặc export có connection URI lên Git/Release/Artifact. `.gitignore` mặc định chặn CSV/ZIP; kết quả tổng hợp và export dashboard chỉ được cho phép có chọn lọc sau rà soát ở mốc liên quan.

## Phân vai và quyền thực hiện

P1: DW/ETL/OLAP/Superset và ghép tổng. P2: EDA/K-Means/CF/baseline/metric/CLI. P2 quản lý `docs/P2/requirements-p2.txt`, không sửa requirements gốc. P1 chỉ hợp nhất dependency tại12A sau kiểm chứng; không sao chép pin P2 thành thư viện đã chạy trên P1.

Sau duyệt và lệnh **Đẩy G0**, commit/push nhánh rồi mở PR vào main. Merge cần xác nhận cụ thể; không push thẳng main, force-push, đổi remote hoặc xóa nhánh. APPROVED chức năng khác PR MERGED.

## Dashboard xu hướng 11C — chờ review

Mở http://127.0.0.1:8089/superset/dashboard/2/ ; hướng dẫn/SQL/filter tại [dashboard/trends](dashboard/trends/README.md), bằng chứng và bàn giao [11C](docs/P1/trends_handoff.md). Chỉ chọn quý nguyên vẹn; genre không lọc tổng rating hệ thống. Chưa công bố PR11C hoặc làm11B/G3.

Cập nhật20/10/2026: điều phối chấp nhận chức năng11C; đang công bố PR theo lệnh riêng. Trạng thái PR/commit và kiểm công bố xem docs/P1/trends_publication.md tính từ repository. Các nhãn chờ review kết quả ở trên là lịch sử; không tự merge hoặc chuyển11B/G3.

Đã công bố [PR #15](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/15), OPEN/chờ review PR; code tái tạo `bdb14fce8deb830999bcb4c17655100a72e6514e`. Chức năng đã được điều phối chấp nhận, chưa merge. Chi tiết kiểm52blob và HEAD/base lúc mở tại docs/P1/trends_publication.json.
