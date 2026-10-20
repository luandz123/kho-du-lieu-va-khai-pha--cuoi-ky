# 11B-4 — Export thật và restore Superset tách biệt

**Cập nhật công bố toàn11B,20/10/2026:** điều phối đã chấp nhận phạm vi export thật + import chính thức + REST phục hồi layout trên8091/cùngDW. Chỉ ZIP đúng hash dưới đây được phép đưa vàoGit; ngoại lệ `.gitignore` đúng `/dashboard/superset_export.zip`, mọi ZIP khác vẫn chặn. `publication_approval.json` và checkerpolicy phân biệt local trước duyệt với công bố được phép. `export_inventory.json`, `final_observation.json` và report cũ ghi ignored/local là lịch sử nguyên vẹn; `export_publication_audit.json`/`publication_observation.json` ghi quan sát mới.

Bộ tái lập phải có [ZIP](../superset_export.zip) + [snapshot nguồn](evidence/production_before.json) + [mapping UUID/ID](evidence/uuid_mapping.json) + [script REST phục hồi](import_bundle.py). Không coi ZIP import một bước hoàn chỉnh; giới hạn và guard target rỗng bên dưới vẫn áp dụng. Phần11B-4 ban đầu phía dưới giữ lịch sử chờ review; trạng thái công bố hiện hành xem [hồ sơ11B](../../docs/P1/11b_publication.md).

Chỉ môi trường thử `btl-movielens-s11b4-restore`, **127.0.0.1:8091**, Superset **6.1.0**. Không import vào 8089. Metadata PostgreSQL17.11 trong service `metadata` riêng; hai volume `btl-movielens-s11b4-restore_restore_metadata` và `..._restore_home`, network riêng. Cookie phiên riêng, không đè cookie production.

## Gói và dependency

ZIP thật `dashboard/superset_export.zip` lấy nguyên byte từ **GET /api/v1/dashboard/export/?q=!(1,2,3)**. Không đóng ZIP thủ công, không chỉnh YAML trong ZIP, không export dữ liệu. SHA-256:

`b5a9c987e7d1e7f56b21f92785370cdb9089a4d1efc01c128568127d938f6fae`

129.744 byte; 3 dashboard /23 chart /6 dataset /1 database. Inventory `evidence/export_inventory.json`: member SHA/count/UUID và cạnh dashboard→chart/dataset, chart→dataset, dataset→database đều khép kín. Có metadata.yaml; không dump hoặc CSVuser-level.

Rà byte thực với secret cục bộ/token đang dùng; password URI chỉ là mặt nạ; không phát hiện giá trị password/token/private key/SSH hoặc encrypted extra nhạy cảm. URI đầy đủ không được ghi log. Dù audit đạt, **ZIP vẫn ignored và chỉ local, chờ review cho phép đưa vào Git**. Không nới .gitignore.

## Điểm quan trọng khi restore ZIP hiện tại

Bố cục custom nguồn thiếu `meta.uuid` trong 23 ô chart. Superset6.1.0 official exporter giữ các ô cũ rồi tự thêm 23 ô có UUID vào hàng orphan. Vì vậy **HTTP import thành công chưa đủ**: có thể xuất hiện chart lặp hoặc ô cũ trỏ ID sai.

Không sửa production hoặc ZIP để giấu vấn đề. `import_bundle.py` import chính thức vào target rỗng với `overwrite=false`; lập mapping UUID→ID mới, rồi **PUT bố cục trên ba dashboard thử** qua REST API: lấy layout nguồn trong snapshot, remap từng chartId theo UUID, bổ sung UUID và giữ đúng 8/5/10 ô, không giữ hàng orphan. Scope native đã được importer remap và được assert lại; SQL/metric/filter không đổi. Đây là **bước phục hồi bổ sung bắt buộc** của runbook này, không tuyên bố ZIP import một bước đã giữ bố cục đúng hoàn toàn. Sau UI kiểm lại layout/scope parsed JSON, chỉ màu/serialization tự sinh có thể khác.

UUID là khóa đối chiếu, không suy ID giống nhau. Ba dashboard hiện vẫn ID1/2/3, nhưng nhiều chart và dataset đổi ID: ví dụ Tổng rating old1→new3; assigned old14→new19; heatmap old19→new20; O5 datasetold4→new3. Mapping đầy đủ trong `evidence/uuid_mapping.json`.

## Tái lập trên môi trường thử mới, rỗng

Tại workspace với Docker Desktop đang chạy và `.venv` P1 đã có psycopg2/python-dotenv. Image dự án cùng6.1.0 đã có; nếu máy khác chưa có, build từ Dockerfile đã ghim trong `dashboard/superset/` sau khi xác nhận môi trường thiết lập. Không cài PyYAML vào môi trường P1: parser audit dùng PyYAML sẵn trong container Superset.

```powershell
.\.venv\Scripts\Activate.ps1
# Chỉ lần đầu: guard cổng 8091 và tên tài nguyên; tạo .env ignored độc lập.
python dashboard/restore/setup_local.py
docker compose --env-file dashboard/restore/.env -f dashboard/restore/compose.yaml up -d
# Export lần đầu khi chưa có ZIP/baseline. Không chạy lại lên file có sẵn.
python dashboard/restore/export_bundle.py
# Hoặc chỉ kiểm ZIP đang có, không xuất lại / ghi đè:
python dashboard/restore/export_bundle.py --inspect-existing
python dashboard/restore/import_bundle.py
python dashboard/restore/verify_restore.py
```

Các guard chặn tài nguyên/ZIP/baseline/target đã tồn tại. **Instance hiện tại đã import, không chạy lại import hoặc setup.** Nếu cần quan sát lại, dùng UI và checker đọc; giữ report cũ trước khi ghi quan sát mới. `observe.py` yêu cầu năm file AX từ kiểm UI thật, không tự tạo chúng; sau khi tự thao tác UI/screenshot, chạy `python dashboard/restore/observe.py` để kiểm scope, isolation, quyền, snapshot và tài nguyên.

Không dùng lại volume metadata production. Lệnh Compose ở đây chỉ tên project thử, không `down -v`, không thao tác volume ngoài danh sách. Lượt này giữ hai service thử running để điều phối review; chưa xóa tài nguyên.

## Credential cục bộ

`dashboard/restore/.env` chứa secret/admin/metadata password mới, độc lập production; template `.env.example` chỉ placeholder. Admin local `btl_admin`; người kiểm xem mật khẩu **tại máy trong file ignored**, không gửi chat/log hoặc đưa lên Git. Init dùng Superset CLI `db upgrade`/`init` và security manager, không sửa bảng metadata thủ công.

Kết nối DW dùng **movielens_bi_reader hiện có**, cấu hình ignored `dashboard/superset/.env.bi`. Import đọc password vào memory và gửi **multipart `passwords` map** khóa đường dẫn database YAML theo cơ chế API hỗ trợ. Không sửa ZIP, không lưu URI credential, không GRANT thêm hoặc thay firewall. Export giữ host `host.docker.internal` để container đọc PostgreSQL Windows; đây là restore cấu hình UI/metadata trên **cùng DW hiện có**, không phải backup/restore dữ liệu DW.

Máy khác cần DW đúng snapshot G2/G3 và role BI phù hợp đã chuẩn bị riêng; lượt này không chứng minh kết nối P2/hai máy hoặc tự mở DB công khai. Có thể cấu hình endpoint bằng API/UI chính thức với credential local sau khi được giao; không thay hash kỳ vọng hoặc sửa producer/model để ép khớp.

## Kiểm thực tế và URL

- Tổng quan: http://127.0.0.1:8091/superset/dashboard/1/
- Xu hướng: http://127.0.0.1:8091/superset/dashboard/2/
- Sở thích: http://127.0.0.1:8091/superset/dashboard/3/

Run **e4d784ce1cfc4b3ba9b06142de5a395b**,90.218s: 23/23chart/data status success; dataset SQL/cột thời gian và metric/query_context giữ đúng sau remap, importer chỉ thêm annotation_layers=[] rỗng. SQL kỳ vọng độc lập từ fact/bridge/genre/usercluster/registry/dim_user, không lấy chart làm đáp án cho chính nó.

| Kiểm | Kết quả |
|---|---|
|Tổng quan toàn kỳ / UTC Q3/2000|1.000.209 /324.864; kiểm thêm SUM/COUNT, user/phim, sao, Top10 và catalog cố định3883|
|Animation2001Q1|count1715,prev20068,QoQ−91,4540562089%,genreassignmentdenom63335,share2,70782348%,rank1 **giảm ít nhất**; lọc hiển thị không đổi mẫu/rank|
|Sở thích toàn bộ /cụm1,F,25–34|assigned6038/170; baseline6038,insufficient2; heatmap72/18ô, chỉ1filtercluster trong ca3filteruser|
|Bảo toàn production|32object nghiệp vụ, chín bảng staging/DW và toànregistry/user/profile giữ snapshot; API8089 vẫn query/lọc thành công|

UI thực đã nhập time range UTC, quarter/genre và cluster/age/gender, lưu năm AX và ảnh trong evidence. Hai lần điều hướng UI chậm trong lúc kiểm instance một worker được tiếp tục trên chính tab đã tải xong, không tạo dashboard/tab trùng; ghi observation riêng. Chưa xác định nguyên nhân navigation timeout; không coi đó là data-query thất bại hoặc tự kết luận nguyên nhân engine.

## Tài nguyên và giới hạn

Web một worker, giới hạn2CPU/2GiB; metadata1CPU/512MiB; init đã exit0. Snapshot RAM khoảng229MiB+79MiB, metadata volume khoảng67,3MiB, home4KiB; số đo có thể đổi theo tải. Image6.1.0 local đã có, imageID trong setup/final observation; không tạo dịch vụ cloud trả phí. Hai container runninghealthy, hai volume và một network thử giữ để review. Không chia sẻ metadata/home volume hay network với production; DW chỉ đọc chung qua BIreader.

Giữ PUBLIC TEMP mặc định; chưa kiểm full refresh mới với S07/G3; **P2 intakeG2NOT_CONFIRMED**. Restore trên cùng máy/version, không cam kết mọi plugin/version khác hoặc phục hồi backupDW. ZIP chưa được duyệt Git; export/restore code/hồ sơ chưacommit/pushPR. Kết quả **11B-4 WAITING_REVIEW**.
