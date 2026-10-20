# Công bố toàn bộ 11B — chức năng được điều phối chấp nhận

Đã mở [PR #18](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/18), **OPEN, WAITING_REVIEW**, chưa merge. Code tái lập **050b601c916b7b4f6be476640673c9978e0ba979**, base mởPR **9fae38b2f69d75d0bb5861fb0a8bc0dbfd38aa48**. 116file/blob lúc mở khớp GitHub PR/tree và remote ZIP byteSHA đúng; snapshot lúc mở trong 11b_publication_remote.json. Commit hồ sơ tiếp theo chỉ ghi quan sát này; không gán commit mới cho runtime cũ. Toànfile/blob và HEAD sau hồ sơ được kiểm riêng trước bàn giao. Danh sách file cuối trong 11b_pr_files.json.

Nếu tái lập G3 sau này, dùng checkout producer đã duyệt bab0b404… và môi trường/đầu vào đã chốt; không chạy exporter HEAD mới để tạo metadata khác dưới version active cũ. Lượt này không tái tạo gói hoặc đổi producer.

Nguồn: người dùng chuyển điều phối chấp nhận11B-4 theo đúng phạm vi **export thật + import chính thức + phục hồi layout bằng REST trên instance riêng8091, cùngDW hiện có**, rồi giao commit/push/mởmộtPRmain toàn11B. Đây là review điều phối/ủy quyền công bố, không phải agent tạo lời duyệt người dùng hoặc tựmerge. URL/HEAD/base chỉ bổ sung sau xác minhGitHub thật.

Toàn PR gồm11B-1 intake/dryrun (checkpoint17e9d56),11B-2 dispatchertransaction/apply+NOOP (f663dcb),11B-3 dashboard (4cc9ca8) và11B-4 export/restore+mapping/snapshot/API/runbook. ReportPASS/FAIL và hash runtime/base cũ giữ nguyên; commit code công bố ghi riêng. Không stage kế hoạchuntracked/P2/privateG3 hoặc mọi file workspace.

Chỉ `dashboard/superset_export.zip` được phép đưaGit, SHA-256 **b5a9c987e7d1e7f56b21f92785370cdb9089a4d1efc01c128568127d938f6fae**,129744byte. Audit mới kiểm CRC/memberhash/UUIDclosure3dash23chart6dataset1db vàsecret thực/URIpassword/token/SSH đạt. ZIP không sửa, ngoại lệ đúng một đường dẫn; JSONapproval+policy chặn payload/pathkhác hoặc mở mọiZIP. Báo cáo local/ignored cũ giữ lịch sử; audit công bố ghi riêng tại dashboard/restore/evidence/export_publication_audit.json.

**Tái lập nhiều bước:** ZIP + dashboard/restore/evidence/production_before.json + uuid_mapping.json + import_bundle.py + README. Exporter giữ23ôlegacy thiếuUUID vàthêm23ôorphan; import trêninstanceTHỬrỗng, mapUUID→IDmới rồi PUTlayoutquaAPI đểgiữ8/5/10ô. Không sửaZIP/metadataSQL/8089. Không tuyên bố ZIP tựimport hoàn chỉnh, backupDW hoặc portability đãkiểmhai máy.8091/volume đanggiữreview, BIreader7view, PUBLIC TEMP/P2intakeG2NOT_CONFIRMED/fullrefreshhelperS07G3 chưa kiểm vẫn giữ.

## Tương thích main mới — phát hiện lỗi và sửa guard P1

Main fetch **9fae38b2f69d75d0bb5861fb0a8bc0dbfd38aa48**, gồm PR16/17P2. P2 chỉnh docstring/comment `mining/clustering.py` vềkhôngnguyêntửtoànbộ3os.replace, khôngđổiquytắc dữliệu. GuardP1 cũ so provenance vớiHEAD làm gói active bịtừchối **P2_CODE_PROVENANCE**. Đãxácminhthậttrongcheckoutdetachedriêng `tmp/compat_11b_20261020`, giữ workspace/P2nguyênvẹn; reportFAILtrước sửa được công bố đểtruyvết.

Sửa chỉP1: provenance đối chiếu blob **producer được duyệt bab0b4049d4e0b1724418b8a92d8afbeda4bc775** còntrongancestry; chấpnhận LF/CRLF của **code** từblobđó, khôngchuẩnhóadữliệuCSV. Vẫnyêucầu localP2khớpHEADđãcommit, hashkhác hoặcproducerkhôngtronglịchsửbịchặn. Không thay manifest/provenance/registry hoặc tái tạo active model. Gói thực giữhai frozenCSVhash vàmanifest630453….

41unit liênquan (31cũ+10regression) đạttrongcheckout đãghépmain vàP1fix. Lầnđầu checkoutthiếu góiignoredlàm1testbáoPACKAGE_INCOMPLETE,đãgiữgiớihạnnày; testchỉđịnhpackagepathcũquaBTL_G3_TEST_PACKAGE rồi41/41đạt,khôngcopy/táitạogói. Khôngchạyintegrationđòianalyticsrỗng hoặcapply/ETL/importlại. Chi tiết FAIL→PASS, hashes và base trong 11b_publication_checks.json.

## Bằng chứng công bố

41unit/provenancehistoricalpackagecheck, JSON/Python/Compose, audit toànfilePR/ignore/secret+artifacthash vàbảotoàndữliệu. Quan sát mới publication_observation.json chỉđọc, kiểm production32object/snapshotnguồnmodelkhôngđổi,8091healthy/mountsbiệtlập/scopesUIđãkiểm. Không chạy lại23chart/5caUI chỉvìcôngbố; run e4d784ce…/90.218s và2apply cũgiữnguyên.

Chưa12A/fullrefresh/quyềnfirewall/merge. Phần PRURL/fullHEAD/base/từngblobđược ghi sau xuất bản tại 11b_publication_remote.json; đó là quan sát GitHub, không thay báo cáo run thành commit công bố.
