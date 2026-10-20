# Quyết định P1

P1-D98: Theo lệnh điều phối chấp nhận11B-1, checkpoint17e9d56, mở dispatcher production riêng mặc địnhdryrun/--apply; không gỡ guard fixture. Giữ mapping preprocessingJSONB đã được chấp nhận; băm snapshotmemory trướcghi vàfreshDW saukhóa; cùngtransaction kiểm+nạp+activecuối. Nguồn9bảngSHARE,3analyticsSHAREROWEXCLUSIVE, advisory20261027,1. UNKNOWN khiCOMMITACKkhôngrõ, khôngretryghi.

P1-D99: Đã chạy đúngapply COMMITTED4648f191 vàapply kiểmNOOP0dec3918; registered_atvàtoàn dữliệu giữnguyên, cảhaihậu kiểmconnectionROmới. 31unit/8integration/4hashG2/ninefingerprints/BIACL/19Supersetobjects đạt. Chỉcheckpoint11B-1 đượccommit; code11B-2 workingtreeSHA khônggán17e9d56làmcodeversion. GiữFAILcũ/P2NOT_CONFIRMED, chưa dashboard11B/ETL/DDL/quyền/export/pushPR. 11B-2WAITING_REVIEW.


P1-D96: Theo lệnh điều phối20/10, xác minh PR15MERGED371aab7/côngbố11Cđượcchấpnhận; đồngbộmain/tạo p1-s11b-cluster-intake, giữ kếhoạch. Chỉ giao11B-1kiểmG3/dry-run, không ghi analytics. Tái tạo bằngcodeP2bab0b404 trong tmp/g3_venvriêng, giữ frozenpins; khácPythonpatch/OSnhưngchecksumkhớp. Không sửaP2 hoặcdependencyP1.

P1-D97 (đề xuất cần review trong11B-1): dùng preprocessing jsonb hiện có để lưu method/training_config/payloadsha/provenance, kết hợp registryfields để xác định identity. Cùngversiongiốnghàng/metadata activevalid=>NOOP; khácpayload=>reject; invalidated+hairesultsrỗng+identitygiống chỉ dựkiếnreload sauDWrecheck. Engine hiệnkhóa production, chỉ fixture. Không tự duyệt mapping/dispatcherproduction; chờ11B-2.


P1-D95: PR15 OPEN/chưaMERGED được API xác minh tại HEADbdb14fce8deb830999bcb4c17655100a72e6514e/base5a42c73c39c00780b2d5442c45662d93bdf0f23b; đủ52file/PRblob/remotetree khớp Git. Code tái tạobdb14fce8deb830999bcb4c17655100a72e6514e; runtimebase/hash giữ riêng. Chức năng APPROVED theo điều phối, PRWAITING_REVIEW. Chỉ cập nhật hồ sơ sau mở, không đổiSQL/metric/filter/ETL hoặc tựmerge/11B/G3.

P1-D94: Theo thông báo điều phối do người dùng chuyển20/10, chức năng11C APPROVED; được commit/push/mởPR p1-s11c-trends vào main, gồm hồ sơ hậu merge11A đã ghép chọn lọc. Không đổi SQL/metric/filter và không rerun ETL/create/3khoảng chỉ để công bố. PR chưa merge; giữ report/hash cũ và giới hạn BI/P2/restore/fullrefreshS07; không11B/G3.

P1-D92: Theo lệnh điều phối chấp nhận công bố11A/PR14MERGED, checkpoint11hồsơP1 c09ae5b rồi ghép52d566a trên p1-s11c-trends sau main5a42c73; khôngstageplan. Cho11C dùng native quarter_select trọnquý, genrefilter khôngtácđộng O4system. QoQ/share/rank tínhfullseries trướcfilter, fixed100/cờbiên/allgenre18 giữnguyên. Thêm USAGEanalytics/SELECTđúng2viewcho BIrolecũ, khôngrotatecredential. Không11B/G3/export/ETL.

P1-D93: 11C dùng mộtôquý×genre với MAX metric đểlấy chỉsốtínhsẵn, khôngSUM%/khôngAVGQoQ. NULL hiểnthịN/A. Hạng1âm ghi giảmítnhất. Superset tựsinh4fieldmàu: ghiriêng, kiểmexactmọifieldnghiệpvụ/filter/layout khác; không sửa côngthứcS07. 3tổhợpSQL/API/UIđạt,11Anguyênvẹn; WAITING_REVIEW, chưaPR/commit11C.


P1-D91: API phát hiện PR14 MERGED bởi hungvu205 tại 5a42c73c39c00780b2d5442c45662d93bdf0f23b khi guard chuẩn bị commit hồ sơ. Agentkhôngmerge; khôngstage/commit/push saupháthiện. Giữ localnotes chưa thuộcmain, ghi observation riêng; không tựmởPRkhác/chuyển11C11B hoặc suy lệnh mới từ trạngtháiGitHub. 50blob đãmerge vẫnkhớpHEADef82fc4.

P1-D90: Push/mở [PR #14](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/14) thànhcông, OPEN/chưaMERGED. Đãkiểm50file/blob tạiHEADef82fc4/base988874d. Codecommit5915702 riêngruntimebase/hash; ledger currentdocshash cập nhật, không sửa snapshot21bằngchứng. Khôngmerge hoặc chuyển11C/11B; giữ cácgiớihạn và quan sát mới containers/API riêng.

## Công bố 11A theo điều phối, 19/10/2026

P1-D87: Điều phối chấp nhận chức năng11A sau kiểm hồ sơ/hash/cấu hình thật, giao commit/push/PR, không merge/11C/11B. Không ghi thành lời duyệt nguyên văn người dùng. Chỉ stage đường dẫn11A/P1, bảo toàn kế hoạch và lịch sử PASS/FAIL.

P1-D88: Quan sát mới container/API/cấu hình ghi riêng; thông tin hai container từng exit255 và được restart là báo cáo điều phối, nguyên nhân chưa xác định. Agent chỉ đọc trạng thái/API, không rerun ETL/reconciliation/create hoặc đổi metric/filter. Giữ PUBLIC TEMP/chưarestore/P2/fullrefreshS07; credential/ZIP localignored.

P1-D89: Ledger bàn giao45artifact là snapshot review; tài liệu sau chỉnh có hash trong ledger công bố riêng. Commitcode công bố khác runtimebase988874d và workingtree SHA lúc kiểm. Đồng bộ main sau commit an toàn, không reset/force hoặc sửaP2, kiểm toàn bộ blobPR saupush.


## 11A — thực hiện theo lệnh điều phối, chờ review

P1-D82: PR13 MERGED988874d được kiểm API/Git, agentkhôngmerge; main fastforward rồi tạo p1-s11a-overview. Giữ plan/reportOPEN vàG2/S07run cũ; khôngcommit/push/PR11A.

P1-D83: Tái dùng Superset8089, chỉstart2container dựán, mọi cấu hìnhquaAPI. Tạo roleBI khi kiểm thấy chưa tồn tại, secretlocalignored; chỉCONNECT/USAGE/SELECT2view. Effective24relation vàrealengine đúngreader, khôngDML/CREATE/owner/membership/sequencewrite; PUBLIC TEMP mặcđịnh ghi rõ, khôngrevokePUBLIC/cấp quyềnngoàiphạmvi.

P1-D84: Virtualratingdataset giữgrain vàUTCcast, titlejoin1:1/nogenre. MeanSUM/COUNT; catalogdataset/chart5cốđịnhloạifilter. NativeUTCfiltertrướcaggregate/limit; sortmetricROW(count,mean,-ID)DESC bảođảm3khóapháhòa, khôngdùngmetrictrộnđiểm.

P1-D85: SQLđộc lập đối3khoảng vớiactualSupersetchart vàảnhnativefilter, cófixturehòa; PASS/FAILchecker giữ lại. ExportrealZIPcụcbộscansecretPASS, passwordmasked, khônggọiimportrestoređạt. Scriptcreatekhôngphảibootstrapmáysạch; khungnhìndesktopđãkiểm/reset, mobilechưatốiưu.

P1-D86: BIreaderP1verifiedkhácP2intake/kếtnốihai máy; G2metadatafalse lịch sử khôngsửa. 11AWAITING_REVIEW, 11B/11C/G3chưalàm; khôngrerunfullrefresh đểkiểmhelperS07.

P1-D81: Push và mở [PR #13](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/13) thành công, OPEN/chưaMERGED. API kiểm đủ44file/blob ởHEAD38ea7ea, basebe8c889, codecommit9456574; kiểm cuối sau push hồ sơ không gán SHA chính ledger vào chínhfile. FunctionalAPPROVED theo điều phối khác PRWAITING_REVIEW. Giữ giới hạn và khôngmerge/tựchuyển11A.

## Công bố S07 theo lệnh điều phối, 19/10/2026

P1-D78: Điều phối chấp nhận S07 kết quả cục bộ sau review SQL/code,73unit/37artifact/Q3; giao commit/push/PR, chưa merge. Ghi riêng functional acceptance, PRreview và MERGED. Không tạo lời duyệt nguyên văn người dùng hoặc tự chuyển dashboard11A.

P1-D79: Đóng gói cả hai commit hồ sơ G2 ghép kèm và S07. Chỉ chín CSV tổng hợp của run af6dbc20 trong ngoại lệ .gitignore chính xác; CSV runlỗi cục bộ khôngstage, observationFAIL giữ Git. Không đổi code/SQL đã review, bảng/contract/P2/nguồn; không rerunDB vì hồ sơ.

P1-D80: Giữ run/base/hashcode và ledger bàn giao37artifact lịch sử bất biến; ledger công bố ghi hash tài liệu hiện tại, codecommit công bố riêng với runtimebase59ed6ed. Commit phần việc trướcfetch/tíchhợpmain, chỉ stage đườngdẫnP1 đã rà. Khôngreset/force hoặc ghiđèP2. Giới hạn fullrefreshhelper/accountreadonly/P2intake giữ nguyên.

---

## S07 — thực hiện theo lệnh điều phối, chờ review

P1-D74: PR9 đã MERGED bên ngoài agent; ghép chọn lọc hồ sơ500b293 và quan sát hậu merge sau checkpoint an toàn. Giữ report OPEN/run cũ là lịch sử, cập nhật MERGED ở hồ sơ mới. Không suy P2 đã nhận G2.

P1-D75: Chỉ thêm sáu view analytics, không đổi bảng/bốn view contract. Catalog allowlist nhận core G2 và đúng bộ sáu view tùy chọn; từ chối partial/rogue. Đây là điều chỉnh helper để hậu kiểm tích hợp đọc được snapshot S07, đã regression73test; không tuyên bố fullrefresh đã chạy với helper mới.

P1-D76: O1/O4 tổng rating duy nhất; O3/O5 count gán genre. Mean SUM/COUNT. O6 EXISTS chọn hợp genre tránh nhân rating; ngày UTC và khoảng nửa mở. O5 đủ genre×quý/zero-fill trướcLAG; n_prev0 NULL, ngưỡng100 giữ cố định; quý hiện tại/trước là biên không rank; share chia tổng gán genre cùng quý, bộ lọc O5 toàn bộ.

P1-D77: Metadata Decimal xuất chuỗi giữ precision, ngày ISO; exporter sửa riêng OLAP. Giữ quan sát FAIL và CSV cục bộ lần lỗi, không ghi lại thành PASS; run mới/fixture mới có SHA thực. Chỉ allowlist CSV tổng hợp đúng thư mục runPASS, chưa stage/push. Các quyết định S07 hiện là thực thi theo phạm vi giao, kết quả WAITING_REVIEW.

---
Các mục dưới đây là hồ sơ lịch sử tại thời điểm ghi; trạng thái hiện hành xem mục mới nhất bên trên.

## Công bố ETL/G2

P1-D73: Code6D công bố4fa9cf17aa41e5ff84d4490886eeac27971e46f6, origin/main52dd682 không đổi saufetch nên không merge. Push và mởPR#9 thành công; API OPEN/chưaMERGED,65file/blob khớpGit ởHEADlúcmở11a3d73. Giữ PRreview riêng với6Dđãchấpnhận vàP2NOT_CONFIRMED. CI0check/statuspending không phảiPASS; finalHEAD của commit hồ sơ được xác minh riêng, không tự ghi SHA của chính file ledger trong file đó.

P1-D71: Điều phối chấp nhận6D cục bộ và giao commit/push/mở PR, không merge. Rà toàn bộ gói từmain gồm checkpoint6A/B/C và6D; giữ report thực chạy/hash/nguồn nguyên vẹn, không stage kế hoạch/data/secret. Bằng chứng công bố và commit tái tạo ghi riêng, không sửa runtime report để gán commit mới.

P1-D72: Ledger6D là snapshot29artifact lúc bàn giao. Các hồ sơ mới được cập nhật review/công bố có hash riêng trong g2_publication.json, không viết lại ledger/run lịch sử. So Git code LF với Windows CRLF bằng normalize khi đối chiếu; không chạm byte raw/canonical. G2 chưa P2 nhận, session readonly không đổi thành tài khoản chỉ đọc. Chuẩn bị read-only account/đường kết nối hoặc DW cục bộ P2 là phương án, chưa được thực thi trong lượt công bố.

## S06 — tích hợp 6D, 18/10/2026

P1-D65: Điều phối chấp nhận 6C sau review và chạy lại 17 unit test, giao riêng 6D. Checkpoint cục bộ c143f5d giữ 19 file 6C đã review; tiếp tục p1-s06-etl, không push/PR, không stage kế hoạch ngoài phạm vi hoặc dữ liệu cá nhân.

P1-D66: Full refresh dùng một connection/transaction và advisory lock (20261027,1). Kiểm marker/catalog/nguồn trước ghi, vô hiệu hóa registry, một TRUNCATE tường minh 11 bảng RESTART IDENTITY, giữ metadata registry. Không CASCADE/DROP/bảng ngoài danh sách; nạp và đối soát bằng cùng connection trước COMMIT, không nối các CLI riêng.

P1-D67: Tái sử dụng quy tắc parse/transform/mapping/insert/serializer. S05 tách copy_staging khỏi TRUNCATE để 6D không truncate thêm lần nữa; guard namespace insert 6A/B/C chỉ mở thêm schema fixture6D. Guard tiểu bước vẫn giữ trong các công cụ lịch sử. Hậu kiểm tích hợp dùng nguồn, PK/FK/miền/UTC/hash/model, không dựa fingerprint surrogate cũ hoặc fact rỗng. 65 unit test hồi quy và fixture cả pipeline đã chạy; version bundle ghi hash mới, không sửa report cũ.

P1-D68: Fixture tự tạo giữ đầy đủ constraints từ DDL đã duyệt trong schema riêng. Sáu nhóm lỗi sau invalidate/TRUNCATE/nạp một phần phải phục hồi snapshot cũ của 12 bảng, identity và model active/valid cùng kết quả cụm; không chỉ kiểm dữ liệu mới về rỗng. Model fixture ghi rõ không phải mô hình thật/G3. Production không được nạp model giả.

P1-D69: Mất kết nối COMMIT giữ trạng thái chưa xác định, reconnect kiểm snapshot/model nhưng không suy ra commit thành công nếu snapshot tương đương trước/sau. Unit kiểm đường xử lý này bằng mô phỏng; không cắt kết nối thật. Ghi manifest/report sau COMMIT qua file tạm và thay tên; lỗi filesystem giữ DB đã commit và G2 chưa bàn giao, không gọi là rollback DB.

P1-D70: G2 chỉ chuẩn bị metadata và hướng dẫn để review; kiểm adapter P2 bằng PostgreSQL thật tại máy P1, raw/CSV/DW cùng serializer. Không sửa file P2, CSV chỉ cục bộ ngoài Git. Session readonly không thay tài khoản chỉ đọc hoặc chứng minh P2 kết nối từ xa; ghi phần quyền còn thiếu riêng. Chưa có xác nhận P2 nhận G2, chưa OLAP/dashboard/nạp G3 hoặc push/PR.

## S06 — riêng 6C, 18/10/2026

P1-D61: Điều phối chấp nhận6B và giao6C; rà/stage đúng19fileP1 rồi checkpoint local d698d8e trên p1-s06-etl. Không push/PR/chuyểnnhánh, không kế hoạch/data/secret; giữ nguyên report/hash và helper6A/6B/DDL/manifest/P2.

P1-D62: Chỉ insert fact qua mapping user/movie/ngày UTC kiểm duy nhất và đầy đủ; parse nghiêm ngặt ID/rating1..5/timestamp int64 và tính duy nhất user–movie xuyên lô. Không join genre, inner join bỏ khóa, upsert hoặc bỏ dòng. Instant có timezone UTC và ngày generated trong DB, không phụ thuộc timezone máy; một transaction/khóa snapshot chung và kiểm trước commit bằng cùng connection.

P1-D63: Đối soát mọi trường logic streaming theo contract sort, serializer G1 theochunk với mộtheader cótestbyteequivalence. Kiểm factPK/FK/UQ/rating/epoch/ngày, tổngđiểm/phân bốsao/user-phim/UTC và bốn canonicalhash; fingerprints dimension gồm surrogate so6B và bridge/staging trước/sau. Không coi4hash sau6C là đãxuất/kiểmnhậnG2 hoặc tíchhợp6D.

P1-D64: Hậu kiểm6C riêng readonly/repeatableread; tests/warehouse/check_warehouse.py cốđịnh verify, không dùng checker6B rỗngfact và không sửa bằng chứngcũ. Fixture7ca lỗi sau1000insert rollback0 cùng code18ce72f9; dữ liệu giả/schema táchbiệt đãdọn. 6CWAITING_REVIEW, khôngrerunloadercũ/6C/xóadữliệu, chưa6D/G2/OLAP/dashboard/analytics/push/PR.

## S06 — riêng 6B, 18/10/2026

P1-D57: Điều phối chấp nhận6A và giao6B, cho phép checkpoint local6A; cfed2c8 chỉ local trên p1-s06-etl, chưa push/PR. Bảo toàn cả reportPASS/FAIL/hashcode6A, kế hoạch untracked ngoài phạm vi và fileP2; ghi cập nhật review riêng, không sửa lịch sử.

P1-D58: Bridge ánh xạ từng IDphim/têngenre sang surrogate hiện có, kiểm duy nhất/đủ, không innerjoin làm mất dữ liệu, không deduplicate hoặc dùng IDnguồn như surrogate. Chỉ insertbridge rỗng trong transaction/khóa snapshot chung; toàncặp/PK/FK/sốgenrephim/hash và bảo toàn dimension/staging kiểm cùng connection trướccommit.

P1-D59: Hậu kiểm6B riêng dùng readonly+repeatableread, đối chiếu fingerprints mọi trường dimension gồm surrogate với baseline trong loadreport. Không dùng checker6A nguyên trạng khi bridge đã nạp, không sửa bằng chứng6A để che trạng thái mới. Loader/check6A vàS05 giữ nguyên; ledger6A là snapshot tại checkpoint.

P1-D60: 6BWAITING_REVIEW sau6408cặp/hashđúng/unit15/fixture/hậukiểmPASS; chỉ ba view có dữ liệu, G2 chưa hoànthành. Không rerunloadS05/6A/6B, không6C/6D/OLAP/dashboard hoặcpush/PR. Lỗi scriptfixture kiểm catalog trướccleanup đã sửa thứ tự, giữFAIL; không nới catalogguard hoặc đổiDDL/loader.

## S06 — riêng 6A, 18/10/2026

P1-D52: Điều phối chấp nhận S05 và giao riêng 6A; PR #7 MERGED đúng8de1c7b đã xác minh. Main52dd682 còn PR #8/P2, chỉ kế thừa, không sửa/chạy/duyệt P2. Nhánh p1-s06-etl, không commit/push/PR ở lượt này.

P1-D53: Insert bốn dimension vào target rỗng trong một transaction/khóa advisory chung; khóa staging chống đổi snapshot và target chống ghi cạnh tranh, kiểm toàn field/source/code sets/hashes trước commit. Không truncate/delete/upsert/bootstrap/DDL hoặc nạp bridge/fact/analytics. Trạng thái khác dự kiến thì dừng kiểm nguồn gốc.

P1-D54: Tính hash view phải ORDER BY/stable sort theo contract vì serializer không tự sort. Lần đầu thiếu sort rollback hoàn toàn; giữ FAIL, sửa caller và regression test, không đổi nguồn/DDL/hash kỳ vọng. Loader cuối77d3450b có unit13/fixture/load cùng hash.

P1-D55: Date lịch UTC continuous 1040 ngày lấy min/max Unix giây, generated calendar kiểm từng ngày; NULL năm vẫn giữ. Surrogate chỉ nội bộ, có thể gap sau rollback, không reset hoặc giả bằng ID nguồn. Hai view users/movies đúng không thay G2 đủ bốn view.

P1-D56: Sau 6A không gọi lại load S05 (đòi DW/analytics rỗng), không tự xóa để rerun6A hoặc tuyên bố integrated full refresh. 6D được giao riêng sau các tiền đề. 6A WAITING_REVIEW; 6B/C/D chưa làm.

## Chốt bằng chứng và công bố S05 — 17/10/2026

P1-D51: Push nhánh p1-s05-staging và PR #7 vào main đã thành công, API xác minh OPEN/merged=false ở head mở 2417416/base c3e4f998. Đủ 25 file/blob khớp local, 19+8 kiểm công bố đạt. Giữ code và mọi run cũ; cập nhật hồ sơ kết quả tiếp tục cùng PR. Chưa merge, chưa ETL DW/G2/6A/quyền BI/backup restore.

P1-D48: Điều phối báo review code/bằng chứng và chạy lại 9/9 unit test đạt, chưa phát hiện lỗi chặn PR; giao thêm một load cùng code rồi commit/push/mở PR, chưa merge/6A. Ghi đúng nguồn điều phối, không tạo lời duyệt nguyên văn của người dùng.

P1-D49: Chọn cặp **0f24c3a → f5f11bcd**, cùng code_sha256 04cb9c6082bbe6224d4c2e7e4d33f312140f25dce52c4a8fbc54d2aebdf8e92f; 10.078s → 9.281s, count/hash/field/source_line khớp, chín target rỗng. c122ce2/16.844s là run lịch sử khác code, không bằng chứng cùng phiên bản. Không sửa code giữa cặp run, không sửa báo cáo cũ; summary/handoff sắp theo started_at_utc.

P1-D50: Công bố đúng phạm vi S05/P1 sau đối chiếu bổ sung thành công; bảo toàn kế hoạch untracked, code và raw/P2. Hash artifact làm mới, lịch sử FAIL giữ nguyên. Chưa nghiệm thu ETL DW/G2/quyền BI/backup restore hoặc cho phép merge/chuyển bước.

## S05 — staging, chờ review

P1-D43: Theo lệnh điều phối mới, database riêng **movielens_btl** được chọn/cho phép tạo nếu chưa có và đủ quyền. Đã xác minh target chưa tồn tại, role hiện có được CREATE DATABASE; không đổi credential/quyền quản trị, không dùng postgres chứa nghiệp vụ. Database đã có mà không xác minh marker nguồn gốc thì script dừng giữ nguyên.

P1-D44: Sau xác minh PR #6 MERGED/c3e4f998, fast-forward main và tạo p1-s05-staging, giữ kế hoạch untracked và không sửa P2. S05 chưa được commit/push/PR; code được nhận diện bằng hash working tree và HEAD nền riêng biệt.

P1-D45: Áp dụng nguyên DDL S04 với guard; hoãn COMMIT cuối để so catalog trong cùng transaction. Không đổi mô hình hoặc thêm IF NOT EXISTS. Kiểm lỗi catalog ban đầu rollback toàn DDL; CREATE DATABASE riêng còn rỗng, không drop. Checker đã sửa và catalog thực khớp.

P1-D46: Nguồn độc lập P1 hash lại đúng byte; phiên bản code adapter đối chiếu Git blob LF và xác nhận checkout chỉ khác CRLF. Đây chỉ là nhận diện code, không đổi hash byte nguồn/canonical. Staging giữ source_line và raw text, loại ZIP, ba bảng nạp một transaction và so mọi field trước commit; không full refresh/nạp DW.

P1-D47: Hai lần staging cùng count/hash; fixture malformed tách biệt chứng minh rollback sau đã COPY users/movies. Chỉ dọn bảng/schema fixture vừa tạo, không CASCADE. S05 WAITING_REVIEW; không suy kiểm này thành G2, quyền BI hoặc chấp nhận chức năng ETL DW.

## Công bố S04 v2 — sau review của điều phối

P1-D42: Đẩy/mở PR #6 thành công trên p1-s04-schema → main; API xác minh OPEN/merged=false và 21 blob khớp local ở head công bố 68af045. Giữ checkpoint, không thay DDL hoặc sửa P2. Commit hồ sơ công bố tiếp theo thuộc cùng mốc; PR vẫn chờ review, chưa merge/S05. Kiểm công bố và hash đã cập nhật, không chạy lại 37 kiểm thiết kế hoặc PostgreSQL.

P1-D40: Nguồn ghi nhận **Điều phối chấp nhận S04 v2 ở mức thiết kế**; không gán thành lời duyệt nguyên văn của người dùng. Các phương án D31–D35/D38–D39 được chấp nhận ở phạm vi thiết kế theo danh sách điều phối, không thay DDL trong lượt công bố. Tên database/quyền thực thi và kiểm PostgreSQL thật còn thuộc bước sau.

P1-D41: Được commit/push/mở PR main trên p1-s04-schema, giữ checkpoint aeb41d1 không rewrite, commit phần đang dở trước đồng bộ origin/main. Rà toàn diff kể cả checkpoint; kế hoạch untracked ngoài phạm vi không stage. Không merge PR hoặc thực thi DDL. Lưu kết quả/hashes theo thực tế, không biến 37 kiểm cũ thành lần chạy mới.

## S04-draft-v2 — 16/10/2026 (đề xuất chờ review)

| Mã | Nội dung | Căn cứ/trạng thái |
|---|---|---|
| P1-D36 | Kế thừa v1, tiếp tục hoàn thiện theo đầu vào PR #5 đã merge; không chờ SHA metadata hoặc 8A để thiết kế | Lệnh điều phối mới; không thay lời duyệt G1/3B/S04. Định nghĩa DDL giữ nguyên |
| P1-D37 | Giữ nguyên checkout p1-s04-schema/aeb41d1, đọc snapshot PR #5 qua API/URL commit cố định | Bảo toàn dirty tree, không commit/fetch/pull/merge/reset/stash; không chép hoặc sửa P2 |
| P1-D38 | Đối soát trước commit phải dùng cùng connection/transaction nạp; kiểm adapter P2 trên DW đã commit ở G2 riêng | Bổ sung thiết kế, chưa chạy. Không dùng connection mới để chứng minh dữ liệu chưa commit |
| P1-D39 | Năm không khớp→NULL, không 0; numeric SUM/COUNT; reload full snapshot, PK/UQ chặn trùng; mất kết nối khi commit phải xác minh lại | Bổ sung cách triển khai/đối soát tương lai, không DML hoặc ETL ở S04 |

23/23 là báo cáo điều phối và log bàn giao đã đọc, không phải test P1 chạy mới. Source/canonical checksum không đổi, code sets đủ, ba script hash khớp; source_code_commit còn một SHA sai cần P2 sửa. WAITING_REVIEW thiết kế, chưa quyền áp dụng hoặc đẩy.

## S04-draft-v1 — 16/10/2026 (cập nhật mới; lịch sử giữ nguyên)

| Mã | Nội dung | Trạng thái/căn cứ |
|---|---|---|
| P1-D29 | Điều phối cho viết thiết kế nháp song song khi G1 còn PR sửa adapter/hồ sơ | Lệnh mới có phạm vi; thay việc chờ thiết kế tại D28, không duyệt G1 toàn bộ hoặc S04 |
| P1-D30 | Bảo toàn riêng chín file P1 bằng 2385a7d, main fast-forward b71d439, nhánh p1-s04-schema, kế thừa checkpoint aeb41d1 | Đã thực hiện cục bộ; không reset/stash/ghi P2/push; kế hoạch untracked ngoài phạm vi giữ nguyên |
| P1-D31 | UNIQUE fact user_key–movie_key; bốn dimension, bridge; surrogate nội bộ | Đề xuất cần review, dựa duplicate_pairs=0 và FK/miền/count trong bằng chứng 9299268, không suy từ báo cáo sạch |
| P1-D32 | Fact TIMESTAMPTZ + Unix, ngày UTC generated/FK ghép; view xuất TEXT UTC-Z đúng contract | Đề xuất cần review; không thay contract, không bỏ yêu cầu P2 sửa/test adapter datetime R1 |
| P1-D33 | Hai bảng cụm theo model_version + registry kỹ thuật và hai view active; kiểm toàn gói trước activate | Đề xuất cần review, tối đa một active, thiếu bằng chứng dùng NULL; không tự tạo model hoặc đổi giao diện P2 |
| P1-D34 | Full refresh transaction trong DB dự án riêng; vô hiệu hóa/xóa kết quả cụm, giữ metadata registry, nạp lại sau đối soát hash | Đề xuất cần review; không DROP/CASCADE, lỗi rollback, không hứa DB và file manifest atomic cùng nhau |
| P1-D35 | Tỷ trọng genre BI mặc định theo lượt gán đánh giá–genre; mean rating roll-up bằng SUM/COUNT | Đề xuất cần review, không cộng genre thành số rating duy nhất và không thay công thức vector ML của P2 |

S04 chỉ **WAITING_REVIEW bản nháp**. PR #3/#4 merge đã xác minh; R1–R6 chưa có kết quả sửa được kiểm nhận. Chưa chạy SQL, tạo DB/schema/view, load/ETL, bật Superset, push hoặc PR S04. Quyền viết nháp không phải quyền thực thi.

Phiên bản P1-S01-v1 ngày 15/10/2026. Không thay thế hồ sơ duyệt; đề xuất chưa phải quyết định nhóm đã duyệt.

| Mã | Nội dung và tác động | Trạng thái/căn cứ |
|---|---|---|
| P1-D01 | MovieLens1M/PostgreSQL/Python/6 OLAP/K-Means/CF+baseline+metric/3 Superset/report-slide; giới hạn Q1–Q3 | Ràng buộc Prompt chung, không mở rộng |
| P1-D02 | Checkout hiện tại; giữ bản cũ; S00 đã duyệt, S01 được giao | Xác minh local và “duyệt bước 0”; không phải duyệt S01 |
| P1-D03 | Contract2 nguyên quy ước, MD/JSON/workflow | WAITING_REVIEW, P1/P2 chưa xác nhận |
| P1-D04 | PostgreSQL 17.11 thay15/16 ghi trong nền; SQL/quyền kiểm lại | Đề xuất trình ở S00, cụ thể hóa S01 chờ chốt; không nhập lời duyệt bản cũ |
| P1-D05 | P1 Python 3.14/P2 Linux3.12.3; đề nghị dòng 3.12 chung tại G0 | WAITING_REVIEW; chưa chọn patch/pin hoặc cài P1; P2 tự báo, chưa test |
| P1-D06 | Kế thừa chọn lọc Superset6.1.0/8089, metadata riêng, giữ 8088/dịch vụ khác | WAITING_REVIEW; chưa copy/khởi động/chứng minh chạy hiện tại |
| P1-D07 | Nặng chạy lần lượt, thưa/theo lô, đo tài nguyên | WAITING_REVIEW; không tự đổi K/lọc phim/lấy mẫu Silhouette |
| P1-D08 | Lịch15–26/10, bảo vệ27/10; G0–G5; 12A→12-P2→12B và cụm trước CF | Lịch đề nghị S01 chờ duyệt; hạn bảo vệ là ràng buộc; không bỏ gate |
| P1-D09 | Hồ sơ chung cũ chỉ đọc, chưa ánh xạ/nhận APPROVED | Prompt chung; cần nhóm chốt cách kế thừa trước ánh xạ |
| P1-D10 | Không cần CF thắng baseline, không ngưỡng Silhouette buộc đạt; tính đúng/tái lập | Theo kế hoạch và lệnh S01; chi tiết acceptance chờ duyệt |
| P1-D11 | Remote có lịch sử, G0 qua nhánh/PR | Git local; kiểm quyền/remote thật khi G0 được giao; S01 không đẩy |
| P1-D12 | Rubric/checkout P2/máy bảo vệ chưa xác minh | Giới hạn bằng chứng, không biến tiêu chí nội bộ thành rubric |

Đổi giao diện cần phiên bản mới, chủ file xác nhận và nêu đầu ra phải chạy lại; không tự sửa hoặc tự duyệt bước cũ.

## Cập nhật tại G0 ngày15/10/2026

R-P1-01 duyệt P1-S01-v1; các nhãn đề xuất trong bảng là lịch sử. P1-D03 (phía P1), D04/D06/D07/D08 và phạm vi/nghiệm thu được duyệt; chưa đồng nghĩa runtime đã đạt. P1-D09 tiếp tục giữ hồ sơ cũ nguyên trạng; chưa có lựa chọn ánh xạ cụ thể để thi hành.

| Mã | Quyết định mới | Căn cứ và tác động |
|---|---|---|
| P1-D13 | Dòng Python3.12 chung, main mặc định | Người dùng “Duyệt” sau câu hỏi xác nhận. P1 còn3.14; cài/kiểm chứng3.12 thuộc setup, chưa chốt patch/pin tổng |
| P1-D14 | Nhánh mới không có codex/; G0 p1-g0-contract | Nguyên văn “các nhánh tạo sẽ không có codex đằng trước”. Thay quy ước tên của workflow nguồn; không tự đổi/xóa nhánh của P2 hoặc nhánh cũ |
| P1-D15 | Tám tệp nền G0 stage có chọn lọc; hồ sơ agent cập nhật cục bộ, chưa stage | Bootstrap tối thiểu; không git add .; commit/push/PR chờ Đẩy G0 |
| P1-D16 | P2 báo đã xong2/PR chờ duyệt, Python3.12.3 với các pin | numpy2.0.2/scipy1.14.1/scikit-learn1.5.2/pandas2.3.3/pytest8.4.2 là thông tin do người dùng chuyển, chưa kiểm PR hoặc chạy P1; không ghi requirements P2 |

Remote HEAD/fetch đã xác minh main/b7698b2, main...origin/main=0/0. Quyền đọc đạt; quyền ghi chưa thực kiểm. Không dùng quyền đọc để tuyên bố quyền push.

## Kết quả Đẩy G0

P1-D17, ngày15/10/2026: người dùng “Duyệt và đẩy g0” duyệt bộ G0/cấp quyền commit-push-PR. Commit5c31e80 thành công, push403 vì tài khoản GitHub hungvu205 thiếu quyền ghi repo luandz123/kho-du-lieu-va-khai-pha--cuoi-ky. Giữ commit/remote/nhánh, không tự đổi danh tính hoặc tạo fork. G0 APPROVED chức năng, công bố BLOCKED, PR/MERGED chưa có. Sau bổ sung quyền tiếp tục đúng commit theo quyền đẩy đã có; không cần xin lại duyệt mốc, merge vẫn riêng.

P1-D18, ngày15/10/2026: sau “đã vào push lại”, push5c31e80 thành công và mở PR#1 OPEN vào main. Blocker403 đã giải quyết; giữ nguyên commit/nhánh, không tạo fork/đổi remote. Dừng trước merge; P2 nhận main sau merge và xác nhận contract.

P1-D19, ngày15/10/2026: sau “đã merge”, xác minh GitHub PR#1 MERGED/eff54aee..., đồng bộ main bằng fast-forward, giữ nhánh G0 và hồ sơ cục bộ. Mốc nền sẵn sàng cho P2 pull/xác nhận contract; không tự sang bước2 hoặc gửi tin chat khác.

## S02-P1-v1 ngày15/10/2026

P1-D20: nhánh p1-s02-env không codex/, theo lệnh mới; chỉ setup sau S01 duyệt/G0 merge, chưa đẩy.

P1-D21: dùng Python3.12.14 bundled có sẵn để tạo venv, không cài toàn hệ thống hoặc đổi3.14; ghi base_prefix/cache dependency và nhu cầu tạo lại. P1 pins đã cài/import thực, requirements gốc chỉ include P1, chưa hợp nhất P2 hoặc nhận ML đã chạy.

P1-D22: kế thừa chọn lọc Superset6.1.0/8089, giữ metadata/volume/key/env hiện có. Sao chép secret.env cục bộ không đọc/in/hash; dùng docker start container cũ để tránh reset/recreate; config ghim6.1.0/postgres17.11, chưa rebuild máy sạch.

P1-D23: checker SQL readonly/timeout/SELECT1, .env chỉ đọc khi explicit; container nhận cấu hình qua stdin. Không raw exception/credential log; thiếu/failed là exit2/3. MetadataSQL/TCP không thay SQL Windows. Xác thực hiện lỗi, chờ user sửa, không đoán mật khẩu hoặc tạoDB.

P1-D24: nested.env.example được allowlist, secret.env vẫn ignore. Không có sensitive tracked nên không cần bỏ theo dõi; không sửa lịch sử Git. S02 giữ phạm vi chưa DW/ETL/mining/dashboard.

P1-D25: S02-v2 sau user báo đã sửa, cả host/container SELECT1_PASS17.11/exit0 theo.env thật. Khởi động lại hai container dự án đã dừng, giữ volume/key. Các lỗiSQL trước đã giải quyết; view/roleBI/UI/dashboard còn chưa nghiệm thu. Chờ duyệt S02, không tự chuyển bước/đẩy.

P1-D26: người dùng “duyệt và đẩy bước2” duyệt P1-S02-v2, cấp quyền commit/push/PR, không merge. Fetch trước đẩy thấy origin/main ff87081 đã gộp PR#2/P2, chỉ thêm file P2 không trùng; tích hợp nguyên vẹn sau commit phần P1, không sửa/chạy hoặc tự duyệt sản phẩm P2. Từ S02 đưa hồ sơ P1/tiền đề G0-S00-S01 vào Git để lưu dấu vết; giới hạn8tệp chỉ áp dụng bootstrap G0, không gom file môi trường/dữ liệu/bí mật.

P1-D27: công bố S02-v2 qua commit6ef3a95, tích hợp nguyên main/P2 bằng f761497 không conflict,9file P2 giữ nguyên. Push thành công/mở PR#3 OPEN, chưa MERGED. Commit chỉ cập nhật hồ sơ công bố tiếp theo thuộc cùng mốc; giữ giới hạn DW/BI/ML và dừng trước merge/bước tiếp.

P1-D28: khi nhận bước4, fetch/API cho thấy PR#3 vẫn OPEN và G1/5file EDA chưa có trên main/local. Ghi S04 BLOCKED vì thiếu đầu vào; không đoán UNIQUE/kiểu, không tạoDDL/thiết kế/tải nguồn khi chưa manifest đối chiếu. Không coi lệnh S04 là duyệt S03 hoặc cho phép merge PR. Chỉ cập nhật hồ sơ cục bộ, không đưa S04 vào PR môi trường đang chờ.
