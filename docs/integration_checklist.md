# Checklist tích hợp sơ bộ — chuẩn bị trước 12A, 21/10/2026

## Hiện hành 24/10/2026 — 12B APPROVED, G4 ĐẠT

Điều phối đã nghiệm thu12-P2 sau PR28 và PR29. **P2 intake G2 = CONFIRMED trên máy P2/Windows độc lập.** Các bảng/mục “NOT_CONFIRMED”, “chưa hợp nhất”, “chưa full refresh” bên dưới là snapshot lịch sử chuẩn bị, không phải trạng thái hiện hành. Không sửa report/runtime/receipt cũ.

Nguồn hiện hành: [ma trận12B](P1/integration_acceptance.md) và [audit nguồn](P1/integration_acceptance_sources.json). Candidate thực chạy trênP2 là4546d5b…, khác main nền d20d3bc… và commit công bố hồ sơ12B. Git xác minh main chứa candidate/PR28/PR29; P1 chỉ tổng hợp bằng chứng, không chạy lại pipeline.

- [x] Main chứa candidate4546d5bbd8f9130a420518b77dc3ad894bc7f42b, PR28merge88c5c7b952553523f58e82ed6546179451eb6b65 và PR29merged20d3bc382e603cc219bc4a742814bae793421ab.
- [x] Hai chu trình P1, invalidation/reload/NO-OP, rollback fixture và bốn canonical được đối chiếu artifact.
- [x] P2 dựng DW độc lập, adapter raw/CSV/DW, tái lập hai CSV G3 và ML/CLI từ DW có bằng chứng đã được điều phối nghiệm thu.
- [x] Ba dashboard/BI/restore có bằng chứng P1; phạm vi và giới hạn được giữ trong ma trận.
- [x] Receipt Test giữ nguyên, chỉ tham chiếu; không evaluator/ETL/G3/dump/restore trong12B.
- [x] WindowsP1/Python3.12.14/PG17.11 và WindowsP2/Python3.12.6/PG17.4 được phân biệt; khôngLinux/SupersetP2/toànstackmáymới.
- [x] Điều phối nghiệm thu 12B và xác nhận G4 ĐẠT ngày 24/10/2026, phạm vi I01–I15 và giới hạn công bố; [ghi nhận mới](P1/g4_acceptance_20261024.json).
- [x] PR30 đã MERGED tại `67fd9eb6b98211485b713c99e829291bc3b50f57`, HEAD được duyệt d8caa003…; agent không merge. Candidate thực chạy vẫn4546d5b…; commit hồ sơ không là candidate mới.
- [x] Cập nhật G4 trong README, chương 1/3/4, phụ lục và hồ sơ P1 hiện hành, giữ snapshot lịch sử.
- [x] Nhận chương 2/5/6 P2 được duyệt từ PR31; đã ghép DOCX/PDF 49 trang và được điều phối chấp nhận bản chỉnh 25/10.
- [ ] Slide tổng và gói nộp G5: chỉ được chuẩn bị bản nháp sau công bố, chưa hoàn thành.

Các giới hạn còn lại không được xóa: PUBLIC TEMP, DB-level ACL clone khác nguồn, ZIP cần REST layout, chỉ cùng máy/version khi restoremetadata; không BI hai máy hoặc Linux. Trong phạm vi ma trận I01–I15 chưa phát hiện lỗi chức năng bắt buộc còn mở; xem chi tiết ma trận, không diễn giải thành toàn dự án đã xong.

## Cập nhật12A23/10/2026 — WAITING_REVIEW

PR24 MERGED01d51a2, base12A01d51a2; venv Windowsmới/requirements tổng đã cài/import/pipcheck,88test mục tiêuđạt. Hai chu trình trên DBtíchhợpriêng đã kiểm fullrefresh sauS07/G3,modelinvalidate/reload/NOOP,MLDW/CLI và3dashboard8092; không fullrefresh demo. Hậu kiểmREADONLY nguồn/8089/ACL/guardBIđạt. [Phiếu gói](P1/integration_candidate.md), [runbook](P1/integration_runbook.md), [S12A](agent/steps/P1/S12A.md). Chưa P2intake/tái lậpvenvLinux, candidatecuối/G4 hoặccommit/push/PR12A. Bảng bên dưới là snapshot chuẩn bị cũ, không thay quan sát12A mới.

## Cập nhật chuẩn bị tiếp — 21/10/2026

Phần DW backup/restore đã được điều phối chấp nhận, checkpoint cục bộ d3f00cc6a068868662a7040459a51ff46e49e231. Metadata Superset được restore riêng vào8092 bằng PostgreSQL tools, dùng SECRET_KEY/config backup; kiểm chức năng ở [runbook metadata restore](../dashboard/metadata_restore/README.md). Phần mới WAITING_REVIEW, chưa chốt12A/G4. Các mục đang chờ P2/full refresh/requirements/candidate vẫn giữ nguyên.

Bảng bên dưới giữ snapshot của lượt chuẩn bị DW trước; dòng metadata “chưa restore” là lịch sử, không thay cho quan sát mới tại dashboard/metadata_restore/evidence/.

Tài liệu mới vì file kế hoạch này chưa tồn tại lúc khảo sát. Đây là checklist nội bộ sơ bộ theo lệnh điều phối, **không xác nhận 12A/G4 đủ tiền đề hoặc hoàn thành**; không thay rubric hay chính sách nhóm đã duyệt.

| Hạng mục | Hiện trạng / bằng chứng | Cần chốt trước khi thực hiện 12A |
|---|---|---|
|PR chức năngP1|PR18MERGED0692822…; registry/DW/OLAP/3dashboard đãduyệt phạmvitừngbước|Giữsnapshot/codeproducerđúng, khônggánruntimecũtheocommitmới|
|CF/CLI/evaluationcuốiP2/Bước10|**Đang chờ** người2/điềuphối chốt|Nhận đúngcommit/PR/lệnhchạy/đánhgiá cuối, không tựsửaP2|
|P2intakeG2|**NOT_CONFIRMED**|Xácnhậnthực củaP2 vàbằngchứng, khôngsuytừP1 nhậnG3|
|Requirements tổng|**Chưa hợp nhất**; requirements.txt/P2filesgiữ nguyên|Chỉ hợpnhất sauđủđầuvào vàkiểm môi trường riêng đúngphạmvi đượcgiao|
|Commit ứng viên tích hợp/G4|**Chưa chọn**; main0692822… chỉ làbase làmviệc|Chờđủtiềnđề vàlệnh12A; chưa gửi mốc choP2|
|Backup/restore DW|Chuẩn bị đã làm: pg_dump consistent/clone mới/4hash/catalog/G3/OLAPđạt, chờreview|Reviewreceipt, ownership/DBACLkhácbiệt vàgiới hạn samecluster|
|Fullrefresh tích hợp sauS07/G3|**Chưa kiểm**; clonebackup khôngphải phépkiểmETLrefresh|Cần lệnh riêng vàkếhoạchpreserve/invalidatemodel/reloadgói/táikiểmBI|
|Supersetexport/restore|11B4 đãduyệt: ZIP+snapshot+UUIDmapping+RESTlayout8091/cùngDW|KhôngcoiZIPtựimporthoànchỉnh hoặcDWbackup|
|BackupmetadataSuperset|Đãdump/kiểmarchive, **chưarestoremetadata**|KhôngcoiđạtmetadataDR; khôngimportđè8089/8091|
|Báocáo cuối/slide/demo|Chưa bắtđầu tronglượtnày|Chờcácmốcnghiệmthuvàlệnh riêng|

Chi tiết inventory, commands, dumpSHA vàbằngchứng: [README chuẩn bị](P1/integration_prep/README.md), [inventory JSON](P1/integration_prep/component_inventory.json), [results](../results/warehouse/s12a_prep/). Phần chuẩn bị **WAITING_REVIEW**;12A/G4 vẫn chưađượcchốt.
