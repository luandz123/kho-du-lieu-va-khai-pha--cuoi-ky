# Bàn giao 11B-4 — WAITING_REVIEW, 20/10/2026

Điều phối đã chấp nhận chức năng11B-3 qua thông báo người dùng chuyển. Checkpoint38file chọn lọc11B-3 tại **4cc9ca8518f55c9e2683d3e8a58f9d9558296fe4** trên **p1-s11b-cluster-intake**; kế hoạch ngoài phạm vi và fileP2 giữ nguyên. Không gán checkpoint mới cho run11B-3 cũ. Export/restore phần mới chưastage/commit/pushPR.

Đã export thật cả3dashboard bằng Superset REST API, ZIP giữ nguyên byte ở `dashboard/superset_export.zip`, **129744byte**, SHA-256 **b5a9c987e7d1e7f56b21f92785370cdb9089a4d1efc01c128568127d938f6fae**. ZIP đọc/CRC đạt; đủ3dashboard,23chart,6dataset,1database, kiểm UUID và dependency closure, băm từng member. Rà secret/token thực local, trườngURI/password/SSH/encryptedextra không phát hiện bí mật; URI passwordmasked. **ZIP vẫnignored/local chờreviewGit**, không đóng giả hoặc sửa YAML.

Đã dựng instance **Superset6.1.0 cổng8091** riêng bằng image trùng production, PostgreSQL17.11 metadata riêng, hai volume/network tách biệt; admin/metadata/secret riêng localignored. Không import vào8089, không chia sẻ metadata volume, không đổi quyềnDB/firewall/DDL, không applyG3/ETL/tạo lại dashboardproduction. Import multipart chính thức, passwordmap chỉmemory từBIconfiglocal, overwrite=false, target banđầu0object.

**Giới hạn export phát hiện và xử lý:** custom layout production thiếuUUIDpernode. Exporter6.1.0 tự thêm23ôUUID gây lặp với23ôlegacy. ZIPnguyênbản khôngsửa. Sauimport đã **PUTlayout vào3dashboardthử quaRESTAPI**, remapIDtheoUUID/loại ôorphanlặp/giữ8–5–10ô và filterđúng. Vì vậy đây là **import+khôi phục bố cục có bướcAPIbổ sung**, không tuyên bố ZIP importmộtbướcđãhoànhảo. Giữ reportFAILcheckerUUID vàobservation lỗihelper/UIchậm đểtruyvết. Nguồn8089 vẫnkhôngđổi.

URLđãrestore: [Tổng quan](http://127.0.0.1:8091/superset/dashboard/1/), [Xu hướng](http://127.0.0.1:8091/superset/dashboard/2/), [Sở thích](http://127.0.0.1:8091/superset/dashboard/3/). UUIDmappingfull `dashboard/restore/evidence/uuid_mapping.json`; IDchart nhiềuđãđổi, không dựa vào tênfile/giả sử IDgiốngnguồn.

Run SQL/API **e4d784ce1cfc4b3ba9b06142de5a395b**,90.218s, base4cc9ca8,codeworkingtree. Hashcode thực chạy trong restore_verification.json; verify_restore.py SHA **4bd8b880cad7f8a4490f46b4d2c50d9427774e83bd1c3772b1de5cbee80ff94c**; common.py SHA **cf4bbef6f557dbe9a766e9f8a9cf626d0b21a5e2de69f07f080d897fca7c22c5**. Import/observation cóhashriêng, không sửareport runtimeđểgánHEADmới.

23/23chart truyvấnthànhcông;6datasetSQL/cộttime và23metric/querycontextđúngsauremap, importerchỉthêmannotation_layersrỗng. SQLđộclậptừbảngnghiệpvụ so API: Tổngquan1000209/324864 (Q32000), KPI/sao/Top10/catalognhấtquán;Animation2001Q1count1715,prev20068,QoQ−91,454056%,mẫu63335,rank1giảmítnhất giữnguyênkhilọc;Sởthích6038/170assigned,baseline6038/insufficient2,heatmap72/18ôđúngscope. UI5catươngứngđạt,cóảnh+AXthật, khôngchỉHTTPimport.

Kiểm cuối sauUI: scopefilter/layoutUUID3dashboardthửđúng;32objectnghiệpvụproductionvàsnapshotstaging/DW/model/registered_at/user/profilekhôngđổi. API8089vẫnlọc/truyvấn;engineSupersetthửthật **movielens_bi_reader/UTC**. TừcontainerthửkiểmquyềnhiệulựcSELECTđúng7viewnhư11B-3,khôngprojectwrite/CREATE/membership/admin. KhôngthayGRANT,sessionREADONLYkhôngthaybằngchứngquyền.

Tàinguyênđanggiữ: web/metadata thửrunninghealthy;initexit0;2volume+1networkriêng. RAMđo khoảng229MiB/79MiB,metadata68884KiB≈67,3MiB/home4KiB;webgiớihạn2CPU2GiB,metadata1CPU512MiB. ChỉDockerlocal,khôngcloudtrảphí;imageđãcó. Chưa tựxóavolumeproductionhoặcthử,giữ8091đểreview. Khôngsuymáyđủmạnhchỉtừcôngcụcài.

Runbook táilập/credentiallocal/cáchmởlọcvàgiới hạn: `dashboard/restore/README.md`. Inventory/memberSHA/importresponse/UUIDmapping/verification/isolation/ảnh tại`dashboard/restore/evidence/`; ledgerbàngiao liệtkêfileSHAcuối, riêngZIPignored ghiSHAmetadata. SourcegóiG3/producer/registrygiữnguyên,chưakhẳngđịnhP2nhậnG2.

Lượt này thêm `dashboard/restore/`, tài liệu bàn giao này vàcậpnhật5hồsơP1; ZIPcục bộignored. KhôngđổiSQLmetricfilterproduction,codeP2,DDL,data hoặcdependencyP1. GiữPUBLIC TEMP/P2intakeG2NOT_CONFIRMED/fullrefreshS07vớiG3chưakiểm. ChưarestoreDWbackup/hai máy/versionkhác. **11B-4 WAITING_REVIEW**, dừngtrướccôngbốtoànbộ11B.

Ý bảo vệ:

- Export configuration quaAPI khác backup dữliệuDW;khôngđưa lịch sửuserhoặccredentialvàoZIPGit.
- UUIDvàdependencyclosure giúprestoređúngkhiIDchart/datasetđổi;đếmfilekhôngđủ.
- HTTPimport200chưachứngminhmetric/filter/bốtục;đãkiểmAPI+SQL+UIvàxửlýlayoutquaAPIriêng.
- Metadata/volume/networktáchbiệtbảovệ8089;DWchỉđọcbằngroleBIhiệulực.
- Baseline6038/insufficient2/profiletínhsẵn vàQoQchuỗiđầyđủgiữnguyênsaurestore,khôngđểfilterđổimẫusố.
