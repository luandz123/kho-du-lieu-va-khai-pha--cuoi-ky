# Chuẩn bị trước 12A — WAITING_REVIEW, 21/10/2026

## Cập nhật 21/10/2026 — metadata restore riêng 8092

Phần DW/kiểm kê bên dưới đã được điều phối chấp nhận và lưu checkpoint cục bộ `d3f00cc6a068868662a7040459a51ff46e49e231`. [Runbook metadata restore mới](../../../dashboard/metadata_restore/README.md) và bằng chứng riêng ghi việc restore chính thức metadata vào instance8092, dùng key/config backup, không import ZIP hoặc sửa layout. Nội dung “metadata chưa restore” phía dưới là quan sát lịch sử của lượt backup trước, không bị ghi đè.

**Chuẩn bị tiếp WAITING_REVIEW; 12A/G4 chưa chốt.** Cùng máy/version, DW hiện hữu; chưa full refresh sau S07/G3, CF/Bước10P2 còn chờ và P2 intake G2 NOT_CONFIRMED. Không hợp nhất requirements/chọn candidate/push/PR phần mới.

Đây là kiểm backup/restore DW và kiểm kê sơ bộ được điều phối giao riêng. **12A chưa đủ tiền đề, chưa hoàn thành; chưa chọn commit ứng viên/G4 hoặc hợp nhất requirements.** CF/CLI/evaluation cuối và Bước10 của P2 còn chờ. P2 intake G2 vẫn **NOT_CONFIRMED**. Ngày bảo vệ27/10/2026 không thay các điều kiện này.

Main đã đồng bộ an toàn tại **0692822ceb5cba0e523ec45629bdea31a0d45562**, nhánh **codex/p1-s12a-prep** theo tên chỉ định riêng lần này. [Quan sát PR18 MERGED](../pr18_merged_observation.json) ghi actorhungvu205/agentkhôngmerge; reportOPEN cũ giữ nguyên. Base này chỉ là checkout làm việc, **không phải commit ứng viên tích hợp**. Kế hoạch untracked ngoài phạm vi/P2 giữ nguyên.

## Kiểm kê thành phần và tiền đề

[Inventory đầy đủ](component_inventory.json) có full commit thay đổi artifact gần nhất, lệnh tham chiếu và trạng thái. Commit file gần nhất khác commit producer của gói đang active.

| Thành phần | Commit gốc/căn cứ | Lệnh xem/chạy tham chiếu | Trạng thái thực tế |
|---|---|---|---|
|Nguồn MovieLens1M/G1|7a284b9f108dd64b030305cf51b8614b770a2296|Đọc source_manifest/canonical_manifest; tải riêng khi được giao|Nguồn đã kiểm ởS05/G2; lượt này không tải/ghi raw; bốn canonicalDW kiểm mới|
|Schema staging/dw/analytics|a4f0cb944b8c70babe3a59266cd0ecea9ff0ed63; PR6mergec3e4f998…|catalog chỉ đọc; không chạy lại schema.sql|S04/S05 đã duyệt; clone12bảng/12view/64cột/9FK/27CHECK khớp|
|Staging/ETL/G2|4fa9cf17aa41e5ff84d4490886eeac27971e46f6; PR9mergead51ba65…|`python -m etl.run_etl verify --env-file .env` là tham chiếu, không chạy refresh|6D có hai run cũ; **chưa kiểm full refresh sau S07/G3**|
|Bốn view DW/manifest|4fa9cf17…; run6501a547065246869b98b6ab6531190e|SerializerP2 trên connectionREADONLY|Bốn hash/count mới trên nguồn và clone khớp; **P2 intake chưa xác nhận**|
|Sáu view OLAP|94565740cf40cff92ce6b1af553eec110316ae0e; PR13merge988874d7…|`SELECT` từ analytics.v_olap_*; tham số trongolap/queries.sql|Đã duyệt; KPI/Top1/rollup/Q3/Animation đối chiếu mới, không cài lại view|
|G3 producer/model|**bab0b4049d4e0b1724418b8a92d8afbeda4bc775**|Chỉ dùng checkout producer đúng khi được giao tái tạo vào thư mục mới|kmeans_k4_seed42 activevalid,6038assigned+2insufficient; không theoHEADmới để đổi provenance|
|G3 intake/loader|11B2checkpointf663dcb…; guardP1côngbố050b601c…; PR18merge0692822…|`etl.load_g3` mặc địnhdry-run nếu được giao; khôngapply ở lượt này|Apply/NOOP cũ đã duyệt; registry/payload/registered_at giữ nguyên saubackup|
|Superset Tổng quan|5915702d414f0385208b696329a2aed215db8762|http://127.0.0.1:8089/superset/dashboard/1/|32objectproduction kiểmtrước/sau khôngđổi|
|Superset Xu hướng|bdb14fce8deb830999bcb4c17655100a72e6514e|http://127.0.0.1:8089/superset/dashboard/2/|QuýUTC/genre/QoQtheođịnhnghĩa đãduyệt|
|Superset Sở thích|4cc9ca8518f55c9e2683d3e8a58f9d9558296fe4|http://127.0.0.1:8089/superset/dashboard/3/|G3activevalid, baseline vàscope cũ giữ nguyên|
|ZIP/import/RESTlayout|e49c3b26721be09bd98ba56e73e62263006e7a55; PR18|[Runbook restore](../../../dashboard/restore/README.md)|**ZIP cần snapshot+UUIDmapping+REST phục hồi layout**; không importmộtbước|
|CF/CLI/evaluation cuối P2|Chưa có commit cuối được chốt; evaluation hiện có ở53e2f603… chỉ là phần đãmerge|Chờ đầu vào/lệnhchạy cuối từP2|**CF/Bước10 đang chờ**, không xác nhận ML/evaluation cuối đã tích hợp|

Các lệnh trên là bản đồ tham chiếu, không cấp quyền tự chạy bước mới. Lượt này không chạy ETL/fullrefresh, applyG3, importmetadata, gửi candidateP2, đổi quyền/firewall hoặc bắt đầu báo cáo cuối. `requirements.txt` và fileP2 được bảo toàn.

## Backup/restore DW thực tế

Run **2856ed49e9ba494090e2acae73b41b9a**, code mới trong workingtree tại base0692822…, chưa commit. Tổng thời gian **252.891s**, gồm băm dữ liệu/backup/restore/hậu kiểm/metadata backup. CodeSHA thực chạy và các phép kiểm nằm [receipt](../../../results/warehouse/s12a_prep/backup_restore_2856ed49e9ba494090e2acae73b41b9a.json); không gán basecommit như thể đã chứa script mới.

Nguồn PostgreSQL Windows17.11, database **movielens_btl**, ownerpostgres, UTF8/libc locale English_United States.1258. Host pg_dump/pg_restore17.11. Dữ liệu nguồn khoảng279.049.907byte, ổD lúc script kiểm còn93.808.975.872byte (~87,4GiB), vượt ngưỡng script3×DBsize+1GiB. Đây là kiểm dung lượng cho thao tác này, không kết luận toàn máy đủ mạnh chỉ từ công cụ đã cài.

Dump dùng **pg_dump custom + snapshotMVCC được export**, sourceconnection REPEATABLE READ/READONLY và advisoryshared(20261027,1) giữ trong toàn đoạn kiểm; không fullrefresh/truncate/reload. pg_dump tự bảo đảm consistency snapshot, không sao chép các bảng từng thời điểm khác nhau. Dump bao gồm toàn CSDL dự án, dữ liệu staging/DW/analytics, sequence,view,constraint,index,objectowner/ACL; không globalroles/password hoặc CREATE DATABASE.

| Artifact cục bộ ignored | Kích thước | SHA-256 |
|---|---:|---|
|dw.dump|19.618.251byte|ac3f16548a4ffa9299dc4434927f929bff3f353cf63843f5986ed05c28b8f1c4|
|superset_metadata.dump|342.955byte|43665b8c70c13d295ad7c6f3f9289a41750ce536ae28c94435213fdda5141236|

Thư mục private: `backups/p1_s12a_20261021_2856ed49e9ba494090e2acae73b41b9a/`. Dump, stdout/stderr/TOCraw và cấu hìnhsecret giữ tại đây, **không Git**. Public chỉ receipt tổng hợp,hash/count,code vàhướng dẫn. MốcUTC bắt đầu/kếtthúc/filemtime ghi trong receipt/postflight; không in mật khẩu/URI.

Đích mới đã kiểm chưa tồn tại: **movielens_btl_restore_20261021_2856ed49**, tạo từtemplate0 đúngencoding/locale nguồn. Khôngdrop/clean/ghiđèđíchcũ; guardchỉchấpnhận đúngtên+marker duy nhất+dumpSHA thuộc run. TOC93entry kiểm không cóDATABASE/DATABASEPROPERTIES/COMMENTDATABASE/ACL DATABASE có thể tác động nguồn. pg_restore **single-transaction + exit-on-error**, không--clean/--create/no-owner/no-acl. Thao tác tạoDB nằmngoàitransactionrestore theo quy tắc PostgreSQL; nếu restorelỗi, giữDBthử/bằngchứng, khôngtựxóa.

Hậu kiểmconnectionmới **READ ONLY**:

- Catalog12bảng,64cột,12view,9FK,27CHECK khớp design; markerclone riêng. Guardproduction `assert_project` vẫn **từ chối clone**, không monkeypatch/làm yếu guard để chạythử.
- Bốn canonicalhash/count khớpG2 trêncảnguồn/clone: users6040,movies3883,movie_genres6408,ratings1000209. Mọi trường12bảng,sequence vàviewdefinition fingerprint khớp;dim_date1040ngày.
- Registrykmeans_k4_seed42active+valid,registered_at2026-10-20T09:00:37.986010Z/model_created_at2026-10-20T08:32:23.015413Z giữ nguyên. User6040/assigned6038/insufficient2NULL; cụm2478/1393/760/1407;72profile/18genre mỗi cụm,tổngmean1. Hai activeviewđúngcùngversion.
- KPI1.000.209rating/tổng3.582.313/6040user/3706phim córating;Top1movie2858,count3428;O4mỗicấp tổngđúng;Q3/2000count324864;Animation2001Q1count1715/prev20068/QoQ−91,454056%/mẫu63335 khớp.
- Source fingerprint vàACL trước/sau khôngđổi. Postflight kiểm lại nguồn sau metadata backup, Superset32objectnghiệpvụkhôngđổi, roleBIđọcclone thực qua container màkhôngGRANTmới.

## Ownership, ACL và những gì không được phục hồi tự động

Không dùng `--no-owner`/`--no-acl`: owner/ACL củabảng,view,sequence vàba schema được giữ nguyên; kiểm source→cloneđạt. Cùngcluster đã có các rolepostgres/movielens_bi_reader, không dump hoặc tạo lại globalroles/password. Restore sangclusterkhác cần chủmáy chuẩn bị cácrole/quyềntối thiểu phùhợp trước; lượt này chưa kiểm đó.

Dump không--create: **database-level ACL/COMMENT/settings không được coi là đã sao chép tự động**. Nguồn có ACL explicit CONNECT choBI; clone dataclNULL dùng defaultPUBLICCONNECT/TEMP, comment riêng làm guard. Lượt này không cấp lại databaseACL; roleBI kết nối/SELECTđúng7view/khôngDML,CREATEtrênclone vẫn false, TEMPtrue. Khôngtuyênbố databaseACLrawgiốngnguồn; defaultPUBLICTEMP còn. Hai DB hiện không códatabase-role settingsriêng. Các khácbiệt được giữ rõ trongreceipt, không cấp quyền để épcheckkhớp.

## Backup metadata Superset khác ZIP và DW dump

`superset_metadata.dump` được tạo bằngpg_dump17.11 **trong container metadata production hiện có**. Đã `pg_restore --list` vàgiảiđọctoànarchive raNUL, không kết nối DBđểthựcthiSQL. **metadata_restore_tested=false**: chưa restoremetadata vào8089,8091 hoặcinstancekhác. Không coi kiểmfile làrestorethànhcông.

Secret/config cần cho phục hồi (SUPERSET_SECRET_KEY, metadata/adminenv,BIenv,compose/config/Dockerfile/init) được sao chép **nguyên byte cục bộ ignored**, không công bố giátrị hoặchashsecretfile. Metadata backup có thôngtin kết nối được mã hóa cần đúngSECRET_KEY nếu sau nàyrestoređượcgiao.

- **DW dump:** dữ liệu+bốtrúc PostgreSQL staging/DW/analytics, không thaymetadataSuperset.
- **Metadata dump:** database nội bộSuperset (dashboard/dataset/config/security/encryptedconnection); không phải dữ liệuDW. Lượt này mớibackup/kiểmarchive.
- **ExportZIP:** cấu hình3dashboard/dependencies cópasswordmask vàUUID; cầncredentiallocal + snapshot/mapping/RESTlayout; khôngphải backupDW hoặcfullmetadata.

Đầu lượt8089/8091web+metadata đều Exited255, chưa xác định nguyênnhân. Chỉ start hai container8089 cósẵn đểbackup/API, khôngrecreate/init/resetvolume, cuốiđãhealthy.8091 giữstopped đểbảotoàn; khônggiảsuytừbằngchứnghômlàđangchạyhômnay. Observation mới trongpostflight ghi riêng.

## Lệnh đã làm sạch bí mật và cách review

Đã chạy từ workspace bằng PythonP1:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.warehouse.test_backup_restore_guards
.\.venv\Scripts\python.exe database/backup_restore.py --apply --date 20261021
.\.venv\Scripts\python.exe tests/warehouse/check_backup_postflight.py --receipt results/warehouse/s12a_prep/backup_restore_2856ed49e9ba494090e2acae73b41b9a.json
```

Scriptmặcđịnh **plan-only**, ghi thật cần--apply. **Không chạy lại--apply chỉđểreview**, vì lầnmới sẽbackup/tạoDBthửmới; databaseclonehiệntạigiữđểđiềuphốikiểm. Postflightchỉđọcđểkiểmmarker/quyền/source/Superset/filebackup; bốncanonical đầyđủ đượcchạytrongrunbackup/restore ởreceipt. Khôngsửacheckerproductionđểchấpnhậnclone.

Lệnhutilitythực tươngđương, mật khẩu chỉ truyềnquaenvprocessmemory; khôngghi URI/password vàoargs/logpublic:

```text
pg_dump --host <host-local> --port <port> --username <owner> --dbname movielens_btl --no-password --format=custom --snapshot <exported-MVCC-snapshot> --verbose --file <private>/dw.dump
pg_restore --list <private>/dw.dump
pg_restore --host <host-local> --port <port> --username <owner> --no-password --dbname movielens_btl_restore_20261021_2856ed49 --exit-on-error --single-transaction --verbose <private>/dw.dump
docker exec btl-movielens-superset-metadata-1 pg_dump -U superset_meta -d superset_metadata --format=custom --no-password --verbose
pg_restore --list <private>/superset_metadata.dump
pg_restore --file NUL --exit-on-error <private>/superset_metadata.dump
```

Không tựchạy commandrời vớiđíchkhác hoặc bỏguardmarker/TOC. Các commanddumpmetadata stdoutbinary được script ghi thẳng vàofileprivate; không inraconsole. Khôngdropdatabase hoặcxóavolumenguồn/thử. Giữdump/DBclone đểreview; script/local logs khôngbịtựcleanup.

## Phần còn chờ trước 12A/G4

[Checklist sơ bộ](../../integration_checklist.md): chờCF/CLI/evaluationcuối/Bước10P2; P2intakeG2NOT_CONFIRMED; chưa kiểm fullrefreshsauS07/G3; chưa chốtrequirements/candidate/G4. Tái lậpend-to-endbao gồm fullrefreshvàkếtquảmodelinvalidate/reload là côngviệc cầnđượcgiao riêng, khôngsuytừclone đãrestoređạt. Chưa gửicandidatechoP2, chưabáocáocuối/slide, chưa commit/push/PRlượtnày.

Giới hạn: restorecùngmáy/PG17.11/roleshiệnhữu, chưa môphỏngmấtmáy/cluster khác; metadataarchive chưarestore; source/hash khôngchứngminhCFđãtíchhợp; backupđanggiữcục bộkhôngcóbằngchứngbackupoff-machine. DW vàmetadata lấyhai snapshot riêng, không phải một distributedtransactionbackup của toànstack. CảnhbáopandasDBAPI UserWarning ghiởreceipt; canonicalserializer vẫnkhớpđúngbyte,hợpđồngP2khôngsửa.
