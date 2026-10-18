# Trạng thái P1

## Hiện hành — 6A WAITING_REVIEW, 18/10/2026

Điều phối chấp nhận S05 sau review code/bằng chứng và giao riêng 6A. Ghi đúng nguồn điều phối, không tạo lời duyệt nguyên văn người dùng. S05 APPROVED theo điều phối; PR #7 API xác minh MERGED/8de1c7b9c39a7fe7aa0ec6bc671eec1ce490f6d6. Các trạng thái OPEN/chờ duyệt S05 bên dưới là lịch sử.

Đã bảo toàn plan untracked, tracked sạch trước fetch/switch. Main mới còn có PR #8/P2; nhánh **p1-s06-etl**, HEAD nền **52dd682920e0587f3a474fe284b9bf5635ab6aac**. Không sửa P2 hoặc tự duyệt 8A, không commit/push/PR S06. DDL và module S05 giữ nguyên, không bootstrap.

Read-only preflight xác minh movielens_btl/marker/catalog, nguồn và toàn bộ trường/source_line staging đúng snapshot S05, chín target rỗng. Nạp bốn dimension một transaction/khóa chung: **6040 user, 3883 movie, 18 genre, 1040 date**; ngày liên tục 2000-04-25..2003-02-28 UTC, cột lịch generated đúng. Hash v_ml_users/v_ml_movies khớp canonical. Bridge/fact/3 analytics và hai view còn lại vẫn rỗng, chưa G2.

Code thực chạy cuối SHA-256 **77d3450b1c7f7e207984ec7f376a0af268ef8b83ddfb38f69e82553ab7f3d7a2**, working tree chưa commit. Unit13/fixture428e7cb4/load3b6f0cda cùng loader hash; read-only sau commit PASS, staging giữ nguyên. Fixture unique-date lỗi ở dimension cuối rollback cả bốn bảng thử, không đổi production. Lần đầu thiếu sort khi hash view đã rollback toàn bộ, có report FAIL và sửa caller/test hồi quy, không đổi DDL/nguồn/hash kỳ vọng. Identity có thể nhảy sau rollback; không reset hoặc dùng surrogate như ID nguồn.

Bàn giao docs/P1/s06a_handoff.md; code etl/s06a_dimensions.py; test/check trong tests/warehouse; bằng chứng results/warehouse/s06a_summary.json và các run. Hồ sơ steps/P1/S06.md. **6A WAITING_REVIEW**, 6B/6C/6D NOT_STARTED. Không chạy lại load S05 sau khi dimension có dữ liệu; chưa pipeline full refresh tích hợp/chạy lại, chưa OLAP/dashboard/BI/backup. Dừng, không tự chuyển 6B.

## Hiện hành — công bố S05, 17/10/2026

S05 **WAITING_REVIEW** phần PR; **PR #7 OPEN, chưa MERGED**. Nguồn: điều phối báo đã review code/đối chiếu bằng chứng, chạy lại 9/9 unit test đạt, chưa thấy lỗi code chặn PR; giao chốt bằng chứng rồi commit/push/mở PR. Đây không phải lời duyệt nguyên văn của người dùng và không suy thành nghiệm thu ETL DW/G2. Chưa merge/6A.

Đã chạy thêm đúng một lần staging trên movielens_btl bằng code hiện tại, không sửa code. Cặp bằng chứng cùng phiên bản: **0f24c3af4b8941dda6cb4d4ce075957d → f5f11bcd42314042b34bfa1ff66e1f56**, cùng SHA-256 **04cb9c6082bbe6224d4c2e7e4d33f312140f25dce52c4a8fbc54d2aebdf8e92f**. Count 6040/3883/1000209, ba hash retained-row và mọi field/source_line giống nhau; chín bảng DW/analytics đều rỗng. Run mới 17/10/2026 14:41:09.503758Z (21:41:09.503758+07), 9.281s; mốc A 16/10 16:04:50.909826Z, 10.078s. Run c122ce2/16.844s khác code là lịch sử, không dùng làm cặp cùng phiên bản. Giữ nguyên chín báo cáo cũ và các FAIL.

Nhánh p1-s05-staging, HEAD trước công bố c3e4f998. Chỉ stage S05/P1; kế hoạch untracked ngoài phạm vi, raw/processed/.env/venv không đưa lên Git. Commit công việc trước fetch/đồng bộ nếu cần, không reset/force hoặc sửa P2. Summary/handoff đã thống nhất thứ tự run theo thời điểm; hash artifact cập nhật sau chỉnh hồ sơ. Commit/push/URL PR ghi sau xác minh, không ghi trước. Chưa kiểm ETL DW/G2, quyền BI hoặc phục hồi backup.

Các mục S05 “chưa được giao đẩy” bên dưới là lịch sử của lượt ban đầu.

Đã kiểm công bố trước commit **19/19 đạt**, stage chọn lọc đúng 25 file S05/P1; commit nội dung `7981844ed2f4b50ed0705db5c04562d7e8fcf028`. Sau tracked tree sạch mới fetch; origin/main vẫn c3e4f998, đã là ancestor, không cần merge. Code và chín báo cáo lịch sử giữ nguyên, kế hoạch ngoài phạm vi không stage. Tài liệu/summary/hash cập nhật trạng thái code đã commit, không sửa run cũ; push/PR còn chờ thực hiện/xác minh ở mốc công bố.

Đã kiểm sau fetch **8/8 đạt**, commit hồ sơ/hashes `2417416aee976440d4fce4dd1b512a22bd703dd3`; push -u thành công, remote SHA khớp. Đã mở https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/7, API OPEN/merged=false, base main/c3e4f998, head lúc mở 2417416. Rà đủ 25 file và từng blob remote khớp local. Cập nhật hồ sơ công bố này tiếp tục cùng PR, giữ code 04cb9c6 và các run cũ. Tracked tree sẽ kiểm sạch sau push hồ sơ cuối, chỉ giữ kế hoạch untracked ngoài phạm vi. Dừng chờ review PR, chưa merge hoặc sang 6A.

## Hiện hành — S05 WAITING_REVIEW

Điều phối giao Bước 5 sau S04 PR #6 đã merge. API xác nhận merge `c3e4f998b3d8a0248770aeefada7200471fb3037`; main đã fast-forward, nhánh **p1-s05-staging**, HEAD nền c3e4f998. Tracked tree sạch trước đổi nhánh, kế hoạch untracked ngoài phạm vi giữ nguyên. Không commit/push/PR trong lượt S05. Các mục S04 OPEN bên dưới là lịch sử trước merge.

Điều phối chọn database **movielens_btl** khi chưa có tên riêng, cho phép tạo mới bằng quyền hiện có. Khảo sát xác nhận target chưa tồn tại; đã tạo trên PostgreSQL 17.11, 127.0.0.1:5432, không đổi credential/role. Database postgres chỉ là kết nối quản trị, không nhận dữ liệu nghiệp vụ. DDL S04 giữ nguyên, thực thi có guard đúng target; catalog đã kiểm thực **12 bảng/64 cột/9 FK/27 CHECK/8 index tường minh/6 view**. Chỉ 3 bảng staging có dữ liệu; chín bảng DW/analytics vẫn 0 dòng.

Nguồn P1 tự tải trước đây được hash lại và sao chép riêng vào data/raw/p1_s05/ml-1m; bốn source hash/line_count và bốn canonical hash/count khớp manifest P2. Dùng adapter đã review, xác minh Git blob đúng LF và checkout chỉ khác CRLF; không sửa manifest/P2 hoặc chuẩn hóa byte nguồn để ép khớp. Một SHA metadata P2 còn lệch được ghi riêng bằng commit/hash adapter thực.

Hai lần nạp staging **6040 users / 3883 movies / 1000209 ratings**, cùng hash trường/source_line, so toàn bộ nội dung nguồn; không nhân đôi. 9/9 unit tests và fixture rollback thật trong schema tách biệt PASS; seed fixture phục hồi đúng, staging thật/DW/analytics không đổi, schema thử đã dọn. Lỗi đầu kiểm phiên bản CRLF và lỗi checker catalog đã xử lý, giữ báo cáo FAIL; DDL lỗi checker được rollback, database mới rỗng giữ nguyên rồi kiểm/nạp lại, không đổi mô hình.

Code/hướng dẫn `etl/s05_staging.py`, `etl/README.md`; test trong tests/warehouse; bàn giao `docs/P1/s05_handoff.md`; tổng hợp kết quả/hash từng run `results/warehouse/s05_summary.json`; hồ sơ `steps/P1/S05.md`. Phiên bản S05 là **working tree chưa commit**, dùng SHA-256 code trong bằng chứng, không gán code S05 cho commit nền. Không nạp dimension/bridge/fact hoặc làm 6A/G2/OLAP/dashboard, không bật Superset. **S05 WAITING_REVIEW**, dừng chờ điều phối, chưa tự chuyển bước.

## Hiện hành — công bố S04 v2

**S04 APPROVED ở mức thiết kế theo điều phối; PR #6 OPEN, WAITING_REVIEW PR, chưa MERGED. Chưa kiểm thử PostgreSQL hoặc triển khai.** Nguồn ghi nhận: **Điều phối chấp nhận S04 v2 ở mức thiết kế**; không phải lời duyệt nguyên văn của người dùng. Các trạng thái WAITING_REVIEW v2/v1 bên dưới là lịch sử trước thông báo chấp nhận.

Được giao commit, push nhánh p1-s04-schema và mở PR vào main; **chưa merge**. Giữ checkpoint aeb41d1 nguyên lịch sử, rà cả checkpoint và diff PR. Không đưa kế hoạch untracked ngoài phạm vi vào Git. Chưa thực thi DDL/staging/ETL; Bước 5 chỉ sau PR S04 được chốt và lệnh tiếp theo.

Giữ các quyết định kỹ thuật đã review, không thay DDL. 37/37 là kiểm tĩnh v2 đã chạy ở lượt thiết kế, không tự ghi chạy lại trong công bố; kiểm công bố/hash và kết quả Git được ghi riêng theo kết quả thật. Commit/PR/HEAD công bố bổ sung sau khi thực hiện và xác minh.

Đã commit chọn lọc 16 file bằng `a4f0cb9`, trước fetch. Fetch xác nhận origin/main `a8d2615df1e5aa522b2cceaaa073336d61013b83`; tích hợp bằng merge `c7743ab75ba36b9e2fc44d8315d3c6f75cd94204`, không conflict. Checkpoint aeb41d1 vẫn là ancestor. Diff dự kiến PR gồm 21 file P1 (kể cả checkpoint), không file P2 hoặc kế hoạch ngoài phạm vi. Kiểm công bố trước commit 15/15 đạt; đồng bộ/hash và push/PR được xác minh riêng tiếp theo.

Đã kiểm sau đồng bộ 12/12 đạt, cập nhật hash và commit hồ sơ `68af045cde1582be367dec95c10ffc8c782e0d0a`. Push -u thành công, remote SHA khớp; mở https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/6, API OPEN/merged=false, base main/a8d2615, head lúc mở 68af045. Rà API đủ 21 file và blob từng file khớp local; không P2/data/secret, checkpoint giữ nguyên. Commit hồ sơ công bố tiếp theo thuộc cùng PR, không thay DDL. Chỉ còn kế hoạch untracked ngoài phạm vi; không stage. Dừng chờ review PR, không merge/S05.

## Hiện hành — 16/10/2026, P1-S04-draft-v2

**S04 WAITING_REVIEW bản thiết kế hoàn thiện; chưa APPROVED và chưa triển khai.** Tiếp tục đúng lệnh điều phối mới, kế thừa sáu file database của v1; không tạo lại mô hình hoặc ghi đè bằng bản khác. Phần v1 và v0 dưới đây là lịch sử.

- API xác minh PR #3/#4/#5 MERGED. Căn cứ sửa mới: PR #5 head `b73c8e2bc3bc98ff8576f75c02416cf2582bdc73`, merge `a8d2615df1e5aa522b2cceaaa073336d61013b83`. Snapshot manifest/provenance P1 tại `docs/P1/s04_inputs_pr5.json`; không pull/merge vào checkout đang dở, không ghi file P2.
- Bốn checksum/count/source hash không đổi; tập mã đã có; ba hash script provenance khớp. Điều phối báo đối soát độc lập và 23/23 test đạt; đã đọc log PR #5, không chạy lại pytest/EDA. `source_code_commit` còn lệch SHA gốc trong provenance; P2 đang sửa, **không chặn thiết kế**. Adapter DW thật chờ G2. Không tự ghi G1 toàn bộ/3B hoặc S04 APPROVED.
- Nhánh vẫn `p1-s04-schema`, HEAD `aeb41d1fab5aa2760d69220e2eaefc401723eb0c`. Không commit mới, fetch/pull/merge, reset, stash, chuyển nhánh, push hay PR trong lượt hoàn thiện. Checkpoint ở v1 thuộc lịch sử, không phải thao tác mới.
- Giữ nguyên định nghĩa SQL; chỉ cập nhật comment phiên bản/căn cứ. Làm rõ NULL năm, count đa genre, numeric SUM/COUNT, một TRUNCATE đúng phạm vi, kiểm trước commit bằng cùng connection, nạp lại/rollback và lỗi mất kết nối khi commit. Mọi phần đều là thiết kế.
- Bàn giao `database/` sáu file, `docs/P1/s04_review_v2.md`, `s04_inputs_pr5.json`, `s04_design_checks_v2.json` và hồ sơ P1 cập nhật. Bằng chứng v1 `s04_design_checks.json` và kế hoạch untracked ngoài phạm vi giữ nguyên byte. Chưa DDL, tạo DB/schema/view, staging/ETL/dashboard hoặc bật Superset.
- Chờ review lựa chọn schema/khóa, view UTC-Z, registry/active, full refresh và công thức tỷ trọng genre. Tên database/quyền thực thi chưa chốt; kiểm SQL thực và raw/csv/DW trên PostgreSQL chưa làm. Không tự chuyển S05 sau bàn giao.
- Kiểm mới v2: **37/37 tĩnh đạt**, 12 bảng/64 cột/9 FK/8 index; bốn view khớp contract về cột/thứ tự/kiểu suy ra. Giữ v1 evidence nguyên byte. Đây không phải chạy SQL hoặc 23 test P2 chạy lại.

## Lịch sử — 16/10/2026, P1-S04-draft-v1

**S04 WAITING_REVIEW bản nháp. Chưa APPROVED, chưa push/mở PR S04, chưa chạy DDL.** Các mục phiên bản cũ bên dưới giữ nguyên làm lịch sử, không còn mô tả trạng thái hiện hành.

- Lệnh mới của điều phối cho phép thiết kế nháp song song trong khi P2 sửa G1; đây là điều chỉnh thứ tự có phạm vi, **không xác nhận G1 đã nghiệm thu toàn bộ**. Không ghi P2 hoặc 3B APPROVED.
- PR #3 môi trường đã MERGED: `9846219eb0944e75e57f349e1bcfc88c7d1e8088`; PR #4 G1 đã MERGED: `b71d439fa2cc3ee84c40f4a28dc6fe00c8326d42`. Đã xác minh API trong lượt này; chưa tự merge gì.
- Căn cứ dữ liệu: head G1 `9299268278900814f939e0e4214d23a31e09ef64`, contract v2, hai manifest và bằng chứng `docs/P1/g1_verification_9299268.json`. Bốn nguồn/bốn canonical đã được điều phối kiểm độc lập; lượt này chỉ đối chiếu bằng chứng, không tải/hash lại nguồn.
- Đã bảo toàn chín file P1 dở dang bằng commit cục bộ `2385a7ddf612a821ada7472dffc60cc2639da83a` trên nhánh cũ. Sau fast-forward main đến b71d439 và tạo `p1-s04-schema`, kế thừa nguyên nội dung bằng checkpoint `aeb41d1fab5aa2760d69220e2eaefc401723eb0c`. Chưa push checkpoint. Tài liệu kế hoạch untracked ngoài phạm vi giữ nguyên, không đưa vào commit.
- Đầu ra nháp: `database/schema.sql`, `erd.md`, `data_dictionary.md`, `source_to_target.md`, `refresh_and_reconciliation.md`, `README.md`. Ba staging; sáu bảng DW; bốn view contract; hai bảng kết quả cụm cộng registry kỹ thuật và hai view active đề xuất. Không sửa contract hoặc file P2.
- Kiểm tĩnh và giới hạn xem `docs/P1/s04_design_checks.json` và `steps/P1/S04.md`: không kết nối DB, không thực thi/parser PostgreSQL, không nạp staging/ETL, không bật Superset. Không lấy kiểm tra SQL 15/10 làm kiểm tra mới.
- Chờ review lựa chọn khóa, UTC-Z ở view, registry/active, full refresh và tỷ trọng genre. R1–R6 adapter/hồ sơ G1 còn chờ PR sửa và kiểm nhận theo commit; chưa giao G2, chưa có G3 được kiểm nhận. Tên database dự án/quyền thực thi sẽ chốt ở bước được giao; chưa tạo database.

Mốc kế tiếp chỉ sau điều phối: review bản nháp và kiểm nhận PR sửa G1. Không tự sang DDL/staging/ETL.

Phiên bản **P1-S04-v0**, 15/10/2026, Asia/Bangkok. Workspace `D:/kho-du-lieu-va-khai-pha--cuoi-ky`; bản cũ `D:/BTL_Kho_Du_Lieu` giữ nguyên, chưa ánh xạ hồ sơ chung.

## Tiền đề và bước hiện tại

- S00 APPROVED R-P1-00; S01 APPROVED R-P1-01 “Duyệt”. Python3.12 chung/main đã chốt.
- G0 APPROVED R-P1-G0 “Duyệt và đẩy g0”; PR#1 MERGED/main `eff54aee4a61f1a2dd6bad69cf3b6a713083b17e` đã xác minh. Giữ nhánh p1-g0-contract.
- Bước hiện tại **2-P1**, nhánh **p1-s02-env** (không codex/), trạng thái chức năng **APPROVED** theo R-P1-S02 “duyệt và đẩy bước2”; đã commit/push và mở **PR#3 OPEN, chưa MERGED**; SQL theo.env hiện tại **SELECT_1_PASS/17.11/exit0 từ cả Windows và container**; không sửa.env/tạoDB. Các lỗiSQL trước là lịch sử. Đã công bố commit6ef3a95/merge origin-main f761497, upstream origin/p1-s02-env. PR https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/3 đã OPEN; chưa có quyền merge.
- Contract2 không đổi. P1 đã xác nhận; chưa nhận xác nhận P2. Không chờ P2 để thiết lập P1; không tự làm EDA/4-P1.

## Đã thực hiện

Tạo thư mục P1/raw/processed, thư mục P2 chỉ rỗng nếu thiếu; không ghi file P2. Tạo .venv Python3.12.14 từ runtime cục bộ có sẵn; pip25.0.1, include-system-site-packages=false; import thư viện từ đúng.venv. Khóa11distribution tại docs/P1/requirements-p1.txt; requirements gốc chỉ include P1, chưa hợp nhất P2.

Trực tiếp: numpy2.0.2/pandas2.3.3/SQLAlchemy2.0.43/psycopg2-binary2.9.10/python-dotenv1.1.1. pip check/import/smoke NumPy-Pandas-SQLAlchemy memory đạt. Không cài ML trên P1 hoặc nhận PR P2 đã đạt.

Runtime nền `C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`3.12.14, không cài/đổi Python3.14 toàn hệ thống. Venv còn phụ thuộc runtime nền/cache; phải tạo lại bằng3.12 phù hợp nếu đường dẫn đó mất, không giả độc lập hoàn toàn.

Superset dự án6.1.0/8089 và metadata postgres17.11 đã khởi động lại đúng container/image/volume cũ, healthy, health/login200, driver2.9.13 import, metadata SELECT1 đạt. Container→Windows5432 TCP PASS. Giữ nguyên8088/Airflow/RabbitMQ và mọi database khác. Sao chép chọn lọc5file cấu hình và bảo toàn file.env Superset cục bộ, không đọc/in/hash bí mật, không recreate/reset/init lại. Root.env tạo từ mẫu cho người dùng điền SQL Windows.

## SQL hiện tại và giới hạn còn lại

Sau user báo “đã sửa”, kiểm lúc20:17–20:18 ngày15/10/2026: Windows và container đều SELECT_1_PASS/server17.11/exit0 với.env thật. Lần đầu Superset dừng, đã docker start lại đúng metadata/web, health/login200. Không đổi credential/tạoDB hoặc recreate/reset volume.

Bốn view dw.v_ml_* NOT_CREATED; dedicated_dw_read_role_verified=false. UI login chưa xác minh, dashboard/export chưa làm. Những phần này chờ bước nghiệp vụ phù hợp; không đánh dấu DW/BI đạt theo SELECT1. Các báo cáo lỗiSQL/diagnostic trước là lịch sử, báo cáo current và setup_summary đã cập nhật PASS.

## Bằng chứng và giới hạn

Hướng dẫn README/docs/P1/environment.md/dashboard/superset/README.md; checker tests/warehouse/check_environment.py và check_superset.py; báo cáo thực results/warehouse/environment_check.json, superset_environment_check.json, setup_summary.json. Mã lỗi cụ thể, không exception/URI/password thô.

Ignore đã kiểm secret2file/venv/raw/processed/dump; template root/nested được phép; tracked list chưa có dữ liệu/bí mật, không cần bỏ theo dõi. git diff --check đạt. Đã stage/commit/push phần P1 có chọn lọc, không secret/data; PR#3 OPEN. Chưa user UI login/chart/dashboard/export/import, rebuild máy sạch, benchmark hoặc tái lập P2. Rubric/tên-MSSV/máy bảo vệ còn chưa xác minh.

## Mốc tiếp theo

Đẩy S02 đã xong: PR#3 OPEN vào main, chưa MERGED. Đã tích hợp nguyên main ff87081/P2, kiểm9file P2 byte-for-byte trùng remote. Chờ review/xác nhận merge cụ thể; chưa chuyển bước. Commit cập nhật hồ sơ công bố thuộc cùng PR, không thay code/phạm vi.


## Yêu cầu Bước4 và trạng thái hiện hành

Bước đang được giao **S04 — BLOCKED** vì thiếu G1/EDA. Kiểm fetch origin/main ff87081... chưa có docs/agent/steps/P2/S03.md, docs/P2/data_understanding.md, results/eda/data_profile.csv, data/source_manifest.json, results/eda/canonical_manifest.json. Không có duyệt S03/contract xác nhận P2 từ đầu vào bàn giao. S02-P1 APPROVED nhưng PR#3 vẫn OPEN/merged=false theo API; chưa có lệnh tự merge.

Giữ nhánh p1-s02-env, chỉ thêm hồ sơ S04/STATE/DECISIONS/PROMPTS cục bộ chưa commit/push vào PR#3. Không tạo nhánh/schema/DDL hoặc tải nguồn trước khi đủ G1 để đối chiếu. Đọc steps/P1/S04.md để biết kiểm tra/missing inputs. Các mục “bước hiện tại2-P1” phía trên là lịch sử công bố môi trường; S04 hiện BLOCKED, không tự duyệt P2.

Mốc tiếp: nhận/xác minh PR G1 EDA đã duyệt/merge đủ5file và merge P1 môi trường trước thiết kế; không tự thay EDA hoặc đoán khóa/kiểu. Chưa tạo thiết kế để duyệt.
