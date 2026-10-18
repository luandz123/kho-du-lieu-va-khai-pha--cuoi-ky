# Bàn giao 6D — full refresh và metadata G2

**Cập nhật công bố:** điều phối đã chấp nhận6D ở mức cục bộ sau review/65unit/29artifact; giao commit, push và mởPR ETL/G2, chưa merge. Nhãn WAITING_REVIEW phía dưới là lịch sử bản bàn giao. Report runtime, hai run/bundle/config và summary6D giữ nguyên; commit code công bố được ghi riêng tại [hồ sơ công bố](g2_publication.md), không đổi base_commit của run. P2 vẫn chưa xác nhận G2, quyền tài khoản chỉ đọc/remote chưa được xác minh.

Đã công bố **PR#9 OPEN/chưa merge**, codecommit **4fa9cf17aa41e5ff84d4490886eeac27971e46f6**, base52dd682. APIđủ65file/blob khớpGit tạiHEADlúcmở11a3d73; hồ sơ tiếp theo chỉ ghi trạng thái, không thay code đã kiểm hoặc báo cáo runtime. Xem linkPR/filelist/provenance trong hồ sơ công bố.

18/10/2026, Asia/Bangkok. **6D WAITING_REVIEW**. Phạm vi riêng 6D, kế thừa S04/S05/6A/B/C; không OLAP/dashboard/G3. Trạng thái review và kết quả hậu kiểm cuối được ghi trong STATE/S06 và [summary6D](../../results/warehouse/s06d_summary.json). G2 mới chuẩn bị để review, **P2 chưa xác nhận kiểm nhận**.

## Căn cứ và Git

Điều phối chấp nhận6C sau review code, chạy lại17/17 unit test và đối chiếu bằng chứng/hash; ghi đúng nguồn điều phối, không tự tạo lời duyệt nguyên văn. Đã đọc STATE/S04/S06/SQL/mapping/refresh/contractv2/manifest và đoạn6D trong WordP1. Giữ nhánh **p1-s06-etl**; rà diff/hash/secret và stage đúng19file6C, checkpoint cục bộ **c143f5d7081da041aad38c0a97c0a8ac0ef721cb**. Không fetch/merge/reset/stash/switch/push/PR. Kế hoạch ngoài phạm vi untracked giữ nguyên byte, không stage; không sửa P2, nguồn, contract hoặc DDL.

Code6D là working tree sau checkpoint, không gán code mới cho c143f5d. Bundle thực chạy **b858a879b6a0d03ef5b7b1533caf93d1c76f421b8171b5579f61ced840638422**, gồm run_etl và bốn helper S05/6A/B/C, hash file vật lý trong report. Cấu hình không bí mật **e2b56ec949d873a395b4af4d9ff351967b2f3d48984dbb8b08922fcb0e114dfd**; không hash/in `.env`, credential hoặc URI.

## Tích hợp và tác động refactor

`etl/run_etl.py` kiểm nguồn/hash, config và marker/catalog movielens_btl trước ghi. Transaction ghi dùng một connection và advisory lock(20261027,1), khóa registry; cập nhật toàn registry inactive/invalid rồi **một TRUNCATE RESTART IDENTITY** gồm analytics.user_cluster, analytics.cluster_genre_profile, dw.fact_rating, dw.bridge_movie_genre, dw.dim_user, dw.dim_movie, dw.dim_date, dw.dim_genre và ba staging. Giữ model_registry metadata. Không CASCADE/DROP/bảng ngoài danh sách, không bootstrap hoặc thay DDL.

Nạp COPY staging→dimension→bridge→fact bằng các hàm đã kiểm; không gọi CLI/connection có commit riêng. Kiểm cùng connection trước commit: nguồn/staging mọi field/source_line, dimension logical/generated UTC/genre/year/NULL, PK/FK/rating/grain/epoch, toàn trường view ratings, tổng hợp và bốn canonical hash. Không join genre vào fact. Metadata registry ngoài hai flags phải giữ nguyên; result tables và active views rỗng sau refresh. Lỗi trước commit rollback cả pipeline; SQL và file xuất không có transaction chung.

Thay đổi helper có chủ đích:

- S05 tách `copy_staging` khỏi TRUNCATE; `refresh_body` lịch sử vẫn khóa/truncate staging rồi gọi COPY như trước. Parser Latin-1/`::`, bỏ ZIP, counters và kiểm toàn trường giữ nguyên. 6D gọi COPY trực tiếp sau TRUNCATE chung nên không truncate lần hai.
- Guard namespace insert6A/B/C mở thêm đúng `s06d_test_<12hex>` cho fixture. Guard target rỗng/rule parse/mapping/miền của các loader riêng vẫn giữ. Không sửa quy tắc chuẩn hóa/serializer P2.
- Hậu kiểm tích hợp `check_warehouse.py` chuyển sang `run_etl verify`, không phụ thuộc một run6C hoặc fingerprint surrogate6A/B. Nguồn/logic/khóa/hash/model là tiêu chí, identity không phải bằng chứng tương đương.
- Report/hash thực chạy cũ giữ nguyên. Phiên bản helper cũ có tại checkpoint; helper mới có hash trong bundle6D. Ledger cũ mô tả snapshot lịch sử, không sửa JSON để ép khớp file hiện tại.

## Hai lần chạy cùng phiên bản

| Thứ tự | run_id | Kết quả | Giây |
|---|---|---|---:|
| 1 | 16421c84a7a244b5ad4b60f4ce4dfbc6 | PASS / COMMITTED | 151.047 |
| 2 | 6501a547065246869b98b6ab6531190e | PASS / COMMITTED | 164.672 |

Code bundle và config fingerprint bằng nhau, không sửa giữa hai run. [Repeatability report](../../results/warehouse/s06d_repeatability.json) đối chiếu toàn bộ `checks` bằng nhau, không chỉ count hoặc surrogate. Mỗi run chỉ một TRUNCATE, counters staging read/loaded đúng và errors0; bốn hash/count, dữ liệu dimension/bridge/fact và trạng thái model khớp. Manifest sau COMMIT trỏ run2, chưa xác nhận P2 nhậnG2.

| Bảng logic | Count | Canonical SHA-256 |
|---|---:|---|
| users | 6040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | 3883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | 6408 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | 1000209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

Tổng điểm **3582313**, phân bố sao1→5 **56174/107557/261197/348971/226310**, user/phim có rating **6040/3706**. Trùng user–movie/FK mồ côi/rating sai/epoch-ngày UTC lệch đều0. UTC **2000-04-25T23:05:32Z..2003-02-28T17:49:50Z**, lịch liên tục1040ngày. Stage6040/3883/1000209, dimension6040/3883/18/1040, bridge6408, fact1000209. View không nối genre nên không nhân rating.

Production có **0 registry / 0 active / 0 valid**, hai bảng kết quả và active views đều0. Không nạp model giả hoặc góiG3. Tình huống registry cũ không rỗng được kiểm bằng fixture tách biệt phía dưới.

## Regression, rollback và xuất metadata

**65/65 unit test** hiện hành đạt:54test lịch sử S05/6A/B/C và11test6D. Report `s06d_unit_46211bbea754466aa1f9f7d360eff091.json` cùng bundle với hai run. Giữ report62test trước đó để truy vết, không gọi nó là cùng phiên bản cuối.

Fixture PostgreSQL cùng bundle: `s06d_rollback_5c9c553454e54e81953fded2d524877c.json`, PASS. Sao chép định nghĩa12bảng/6view/index/constraints từ DDL đã duyệt vào **schema riêng**; không chạy DDL trên staging/dw/analytics thật. Seed snapshot cũ không rỗng: ba staging, bốn dimension, bridge, fact, registry active+valid, user_cluster và profile. Model metadata hoàn toàn tự tạo, ghi rõ NOT_REAL_MODEL, không phải kết quả ML/G3.

Sáu ca lỗi dùng **cùng hàm điều phối transaction** và hàm COPY/transform/insert thật: parse sau usersCOPY; missing mapping; FK SQLSTATE23503; rating ngoài miền; cặp user–movie trùng; checksum sai sau đã nạp toàn bộ dữ liệu mới. Mỗi ca kiểm đúng loại lỗi, một TRUNCATE, snapshot của cả12bảng **gồm mọi field**, identity state và active/valid model+results khôi phục đúng baseline. Không chỉ chứng minh bảng mới rỗng. Ca thành công tiếp theo giữ registry1 nhưng inactive/invalid và dọn hai bảng kết quả. Fixture/schema đã dọn đúng đối tượng, không CASCADE; signature production trước/sau không đổi. Report fixture trước lần tăng unit/end-source-guard cũng được giữ, không gộp thành bằng chứng bản cuối.

Mất kết nối lúc COMMIT được unit mô phỏng: kết quả giữ chưa xác định, code reconnect kiểm snapshot/model nhưng không gán commit thành công từ snapshot tương đương. Không thực sự cắt kết nối PostgreSQL trong lượt này. Unit mô phỏng lỗi rename/report/manifest sau COMMIT: DB vẫn đã commit, G2 publication thất bại; không rollback giả. Hai run thực đều công bố report/manifest thành công bằng file tạm+fsync+replace. Chỉ manifest gần nhất được cập nhật, report từng run không ghi đè.

## Adapter, hậu kiểm và G2

Adapter P2 run **c75f9cb0ceb04d74bfa36e140d812754** **PASS / 50.453s**: đọc trực tiếp PostgreSQL, so raw/CSV/DW theo mọi cell, schema/order, count và hash của cả bốn bảng. Adapter Git blob SHA **748eef31e0aaf17ceca430938d71657df6ca1a020158f6ba8709e2cab65b1c72**, không sửa file P2. CSV canonical chỉ cục bộ tại `data/processed/p1_g2_c75f9cb0ceb04d74bfa36e140d812754/`, ngoài Git. Không lấy test fixture thay adapter DW thật.

`SHOW transaction_read_only` trả **on**, nhưng role hiện tại **superuser/có quyền tạo DB, role và ghi bảng dự án**. Vì vậy session đọc đã kiểm không phải bằng chứng tài khoản chỉ đọc dành cho P2. Không tạo/cấp quyền hoặc thay credential. **P2 remote connectivity chưa xác minh**. Hậu kiểm tích hợp chỉ đọc cuối được index riêng ở summary6D.

Hậu kiểm tích hợp run **21f0d343d42543c2ab176c3ac554841e PASS / 58.313s**, READ ONLY / REPEATABLE READ; bốn hash và toàn bộ kiểm tra logic/tổng hợp/model khớp run2. Không phụ thuộc run6C hoặc fingerprint surrogate lịch sử. Không chạy thêm refresh sau hai run để đổi số liệu hoặc khắc phục artifact.

Gói metadata: [dw_manifest.json](../../results/warehouse/dw_manifest.json), [dw_handoff.md](dw_handoff.md), SQL/view S04 hiện có, run reports và summary. Manifest gồm contract2, bốn hash/count, source hashes, tổng điểm/sao/biên UTC và phiên bản ETL. CSV không thuộc Git hoặc gói metadata public. P2 phải nhận đúng commit sau công bố/merge khi được giao, kiểm lại DW/hash và gửi xác nhận thật; agent không tự ghi P2 đã kiểm nhận.

## Lệnh chạy và file

PowerShell tại thư mục dự án với `.venv` đã có:

```powershell
.\.venv\Scripts\Activate.ps1
python -X utf8 -m etl.run_etl refresh --env-file .env
python -X utf8 tests/warehouse/check_warehouse.py --env-file .env
python -X utf8 -m unittest discover -s tests/warehouse -p 'test_*.py'
```

Refresh là thao tác ghi đúng phạm vi được giao6D. Checker chỉ đọc không refresh, không phụ thuộc run lịch sử; nó kiểm trạng thái ngay sau refresh, trướcG3. Không dùng loader/checker tiểu bước cũ cho snapshot sau full refresh. Fixture `check_s06d_rollback.py --env-file .env` và adapter `check_g2_adapter.py --env-file .env` là các kiểm có chủ đích (fixture tạo schema thử; adapter tạo CSV cục bộ), không phải checker chỉ đọc thông thường.

File6D: run_etl, refactor bốn helper, checker tích hợp, unit/fixture/adapter trong tests/warehouse, manifest/runreports/repeatability/summary trong results/warehouse, hai tài liệu bàn giao, README/etl/database và hồ sơ S06/STATE/DECISIONS/REVIEWS/PROMPTS P1. Danh sách đầy đủ và hash từng artifact trong summary. Kế hoạch ngoài phạm vi, nguồn, contract, DDL, P2 và report6A/B/C không sửa.

## Giới hạn, cần review và ý bảo vệ

Chờ điều phối review6D: phạm vi transaction/TRUNCATE, refactor và regression, hai run cùng code/config, fixture snapshot/model rollback, adapter/hậu kiểm và metadataG2. Chưa commit6D/push/PR, chưa xác nhận P2 nhậnG2, chưa OLAP/dashboard/G3/BI hoặc phục hồi backup. Không kiểm network-loss thật, quyền account chỉ đọc hoặc kết nối từ máy P2 chưa được suy từ session local. Hiệu năng151/165giây chỉ là số đo hai run hiện tại, không cam kết SLA hoặc máy bảo vệ.

1. Atomic full refresh khác việc nối các CLI có commit riêng: lỗi phải khôi phục cả staging/DW/model cũ.
2. Một TRUNCATE tường minh gồm cả bảng tham chiếu, giữ registry metadata và không CASCADE.
3. Tương đương theo ID nguồn/nội dung/UTC/hash; surrogate được phép đổi và không phải bằng chứng nghiệp vụ.
4. Hai lần chạy và fixture seeded snapshot kiểm cả tính lặp lại lẫn rollback, gồm cờ model để BI không dùng kết quả cũ.
5. Commit DB và xuất file là hai giai đoạn; lỗi xuất G2 không đồng nghĩa rollback DB, và session readonly không thay tài khoản chỉ đọc.
