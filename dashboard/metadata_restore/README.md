# Restore metadata Superset riêng — chuẩn bị trước 12A

Instance thử: **http://127.0.0.1:8092/**, project `btl-movielens-s12a-metadata`, Superset **6.1.0**, cùng image ID với production. Metadata PostgreSQL **17.11**, database `superset_metadata` nằm trong container/volume riêng, không phải metadata của 8089 hoặc 8091. Chưa đủ tiền đề để chốt 12A/G4.

## Phân biệt ba cơ chế phục hồi

| Cơ chế | Phạm vi | Bằng chứng / giới hạn |
|---|---|---|
| DW dump/restore | staging, DW, analytics, model và view PostgreSQL | Đã restore vào `movielens_btl_restore_20261021_2856ed49`; không chứa metadata Superset; database thử giữ review |
| Metadata dump/restore — lượt này | Database nội bộ Superset, tài khoản/quyền ứng dụng, dataset/chart/dashboard, native filter/layout và kết nối mã hóa | Restore bằng pg_restore; cần đúng SECRET_KEY đã backup. Giữ nguyên ID/UUID, không sửa layout hoặc bảng metadata |
| Export ZIP/import | Cấu hình ba dashboard và dependency được exporter hỗ trợ | Runbook 11B-4 cần snapshot nguồn + mapping UUID + REST phục hồi layout; không phải backup toàn bộ metadata hay dữ liệu DW |

Metadata restore được kiểm **cùng máy, cùng version, trên DW production hiện hữu**, dùng BI reader chỉ đọc. Chưa chứng minh phục hồi toàn hệ thống trên máy/cluster mới, chưa dùng DW clone làm nguồn BI. Đăng nhập có thể cập nhật thông tin phiên/last-login của tài khoản trên metadata thử theo hành vi ứng dụng; không chỉnh trực tiếp bảng metadata.

## Bản backup và provenance

- Dump metadata gốc 342.955 byte, SHA-256 `43665b8c70c13d295ad7c6f3f9289a41750ce536ae28c94435213fdda5141236`.
- Nguồn private: `backups/p1_s12a_20261021_2856ed49e9ba494090e2acae73b41b9a/superset_metadata.dump` và `superset_private_config/` cạnh đó. Dump/SECRET_KEY/env/config private/raw log không lên Git.
- Checkpoint cục bộ phần trước đã review: `d3f00cc6a068868662a7040459a51ff46e49e231`. Code restore mới còn working tree; hash thực chạy trong receipt, không gán checkpoint như thể đã chứa code này.
- Restore run `301bfdfabc984c2b8ec61cb41ed9e79c`. Log riêng tại `backups/metadata_restore_301bfdfabc984c2b8ec61cb41ed9e79c/`.
- Restore chính thức: 529 TOC entry, 53 bảng metadata public. Không chạy Superset init, db upgrade, ZIP import hoặc REST sửa layout.

## Guard và lệnh

```powershell
# Mặc định chỉ đọc hash và báo kế hoạch, không tạo tài nguyên:
.\.venv\Scripts\python.exe dashboard/metadata_restore/restore_metadata.py
.\.venv\Scripts\python.exe tests/warehouse/test_metadata_restore_guards.py
# Chỉ cho môi trường mới CHƯA tồn tại; lần apply được giao đã thực hiện:
# python dashboard/metadata_restore/restore_metadata.py --apply
```

**Không chạy apply lại trên instance đã restore.** Script từ chối env/project/volume/cổng đã tồn tại. Trước restore kiểm container đúng tên, label purpose/run ID, volume đúng tên và marker database chứa run ID/dump hash; đích phải rỗng. TOC từ chối lệnh DATABASE có thể tác động ngoài đích. Không dùng `--clean`, `--create`, DROP hoặc sửa guard DW production.

Lệnh PostgreSQL thực, không có credential trong args:

```text
docker exec -i btl-movielens-s12a-metadata-metadata-1 pg_restore -U superset_meta -d superset_metadata --single-transaction --exit-on-error --verbose
```

stdin là dump đã kiểm hash; stdout/stderr ghi file private. Database mới do image PostgreSQL tạo trong volume mới; chỉ COMMENT marker thử trước restore, không sửa các bảng metadata ứng dụng. Superset web chỉ được khởi động sau restore. Image Superset dùng config/SECRET_KEY từ bản backup; wrapper public chỉ đổi tên instance và cookie phiên riêng. Không thay kết nối được khôi phục, nên chart truy vấn được chứng minh khả năng giải mã credential cũ.

## Kiểm chức năng và giao diện

`verify_restore.py` kế thừa kiểm SQL độc lập/API của 11B-4 với **identity mapping**, không gọi importer/loader/repair. Tất cả 23 chart truy vấn thành công; engine thực `movielens_bi_reader`, timezone UTC.

| Ca SQL/API/UI | Kết quả yêu cầu |
|---|---|
| Tổng quan toàn kỳ / Q3 2000 | 1.000.209 / 324.864 rating; danh mục cố định 3.883 |
| Animation 2001 Q1 | 1.715; quý trước 20.068; QoQ −91,454056%; mẫu số 63.335; hạng 1 là giảm ít nhất |
| Sở thích toàn bộ | Assigned 6.038; insufficient 2; model `kmeans_k4_seed42` |
| Cụm 1, F, 25–34 | Assigned 170; baseline cố định 6.038; insufficient cố định 2; heatmap chỉ chịu cluster, đủ 18 genre |

URL ba dashboard (ID/UUID giữ nguyên, mapping trong `evidence/uuid_mapping.json`):

- http://127.0.0.1:8092/superset/dashboard/1/
- http://127.0.0.1:8092/superset/dashboard/2/
- http://127.0.0.1:8092/superset/dashboard/3/

Đăng nhập bằng tài khoản đã khôi phục; xem credential **tại máy** trong `.env` ignored, không gửi qua chat. Ảnh UI thật và snapshot AX có trong `evidence/ui_*.png/.json`. `observe.py` yêu cầu bằng chứng UI có sẵn rồi kiểm lại layout/filter/metric/SQL, BI quyền hiệu lực, nguồn DW/model/ACL và production.

## Tài nguyên giữ lại và giới hạn

Giữ hai container thử, network riêng và volume `btl-movielens-s12a-metadata_restore_metadata`, `..._restore_home` để điều phối review. Web giới hạn 2 CPU/2 GiB, metadata 1 CPU/512 MiB; số đo sử dụng thực ở final observation. Không tài nguyên cloud trả phí. Không xóa database/volume; không ghi metadata 8089/8091. Production 8089 tiếp tục hoạt động, 8091 giữ stopped; DW clone trước vẫn giữ nguyên.

Chưa full refresh sau S07/G3, CF/Bước10 P2 chưa chốt, P2 intake G2 vẫn NOT_CONFIRMED. Không hợp nhất requirements, chọn candidate, gửi mốc P2, chốt 12A/G4 hoặc push/PR trong lượt này. **Chuẩn bị tiếp WAITING_REVIEW**; các receipt trước ghi “metadata chưa restore” được giữ làm lịch sử, kết quả mới nằm riêng trong thư mục này.
