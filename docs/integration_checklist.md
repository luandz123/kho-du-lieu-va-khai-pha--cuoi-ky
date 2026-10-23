# Checklist tích hợp sơ bộ — chuẩn bị trước 12A, 21/10/2026

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
