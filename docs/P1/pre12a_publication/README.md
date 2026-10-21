# Công bố phần chuẩn bị tích hợp trước 12A

Điều phối đã chấp nhận DW backup/restore, kiểm kê và metadata Superset restore riêng, giao commit/push/PR vào main. **Đây là phần chuẩn bị, chưa phải PR chốt 12A hoặc G4.** Chức năng được review khác trạng thái PR/MERGED; agent không tự merge.

## Phạm vi và truy vết

- [DW backup/restore và kiểm kê](../integration_prep/README.md), script `database/backup_restore.py`, test/receipt tổng hợp trong `results/warehouse/s12a_prep/`.
- [Metadata restore riêng 8092](../../../dashboard/metadata_restore/README.md), compose/guard, SQL/API/UI và ảnh gốc. Metadata restore giữ layout/ID/UUID, không dùng ZIP repair.
- [Checklist tích hợp sơ bộ](../../integration_checklist.md), STATE/S12 và hồ sơ P1.
- Checkpoint phần DW đã review: `d3f00cc6a068868662a7040459a51ff46e49e231`. Commit công bố code mới được ghi riêng sau khi tạo thành công; không thay `base_commit` hoặc hash runtime cũ.

Receipt cũ “metadata chưa restore” là lịch sử của lượt backup. Kết quả mới tại `dashboard/metadata_restore/evidence/final_observation.json` xác nhận metadata restore đã kiểm chức năng. DW clone giữ owner/object ACL, nhưng database-level ACL khác nguồn (default PUBLIC CONNECT/TEMP trên clone); không cấp quyền mới để ép raw ACL giống nhau. ZIP vẫn cần quy trình snapshot/UUID mapping/REST layout; không coi ZIP, DW dump và metadata dump là một cơ chế.

## Kiểm công bố

`python tests/warehouse/check_prep_publication.py` kiểm toàn bộ đường dẫn P1 so với merge-base main cùng thay đổi mới: AST/JSON/YAML, ignore, literal secret/URI/password hash, runtime code/dump hash và artifact metadata đã được chấp nhận. PyYAML dùng trong container Superset đang có, không cài thêm dependency. Chạy lại 14/14 test guard thuần Python đạt; không chạy lại dump/restore/UI hoặc ETL để công bố.

`publication_audit.json` ghi phép kiểm mới, `artifact_manifest.json` băm byte working tree hiện tại của file bàn giao. Manifest tự loại chính nó để tránh vòng hash. Ledger/báo cáo runtime cũ giữ nguyên, kể cả PASS/FAIL và code chưa commit lúc chạy. Nếu Git blob dùng LF còn working tree Windows CRLF, đối chiếu biểu diễn text riêng; tuyệt đối không chuẩn hóa byte dữ liệu nguồn/canonical.

Ảnh browser gốc có đuôi lịch sử `.png` nhưng byte thực là JPEG. Checker nhận dạng header thực và ghi rõ loại ảnh; giữ nguyên byte/hash đã review, không chuyển mã ảnh để che khác biệt. FAIL của giả định header cũ được lưu lại. Không có dữ liệu theo user trong ảnh hoặc kết quả công bố.

## Bảo toàn và giới hạn

Dump DW/metadata, SECRET_KEY, env/credential/password hash, config private/raw logs và dữ liệu theo user giữ local ignored. Kế hoạch `docs/KE_HOACH_BTL_MOVIELENS.md` không stage. Không sửa file P2; main mới có PR20/CF10A và baseline fix chỉ được kế thừa, chưa đồng nghĩa nghiệm thu CF/CLI cuối hoặc đủ tiền đề12A.

Giữ DW clone `movielens_btl_restore_20261021_2856ed49`, metadata/web thử8092 cùng hai volume riêng;8089 giữ hoạt động,8091 giữ dừng. Không tạo lại/xóa tài nguyên. Cùng máy/version, dùng DW hiện hữu; chưa phục hồi toàn hệ thống máy mới, chưa full refresh tích hợp sauS07/G3, P2 intakeG2 NOT_CONFIRMED, chưa hợp nhất requirements hoặc chọn/gửi candidate.
