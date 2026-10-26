# Tái lập và kiểm tích hợp 12A

Đích thử riêng, không chạy trên `movielens_btl` demo hoặc clone backup. Base lúc chạy12A là `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02` cộng code working tree tại thời điểm đó; hash thực chạy giữ trong `results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/`. Candidate thực chạy trên P2 là `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. Điều phối đã nghiệm thu12B/G4 ngày24/10/2026, phạm vi I01–I15; P2 intakeG2CONFIRMED. [Nguồn hiện hành](integration_acceptance.md), [ghi nhận G4](g4_acceptance_20261024.json). Không gán commit hồ sơ mới cho lần chạy cũ.

## 1. Môi trường và nguồn

Windows đã chạy Python3.12.14 trong venv mới ignored, không thay venv demo:

```powershell
.\.venv\Scripts\python.exe -m venv tmp/s12a-venv
.\tmp\s12a-venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

P1 requirements và thư viện ML được hợp nhất trong requirements.txt, phiên bản cài thật/freeze lưu trong environment.json. Superset6.1.0 vẫn chạy trong container riêng. Parquet/pyarrow là tùy chọn, không cần cho CSV/DW. Linux dùng `python3.12 -m venv tmp/s12a-venv` và `source tmp/s12a-venv/bin/activate`; lượt này chỉ kiểm mới trên Windows, không tuyên bố đã kiểm bộ requirements tổng trên Linux.

Tải MovieLens1M từ URL chính thức trong data/source_manifest.json; giải nén cục bộ ignored. Đối chiếu SHA-256 và số dòng của users.dat/movies.dat/ratings.dat/README, Latin-1 và :: theo contract2. Không sửa nguồn/manifest để làm khớp; không chép raw/canonical từ máy P2 lên Git. Nguồn đang dùng nằm dưới data/raw/p1_s05; script tìm duy nhất ratings.dat nếu không có data/raw/ml-1m.

Điền kết nối quản trị cục bộ tại `.env` theo `.env.example`; không gửi mật khẩu trong chat. Tài khoản phải có quyền tạo DB riêng. Dùng credential hiện có, không tự tăng quyền. BI reader dùng file ignored dashboard/superset/.env.bi; không chia sẻ credential quản trị cho P2.

## 2. Schema → staging/ETL → kiểm DW

Orchestrator mới mặc định dry-run:

```powershell
python etl/run_integration.py
# Lần apply được giao đã chạy trên DB thử mới; không chạy lại chỉ để xem kết quả:
# python etl/run_integration.py --apply --date 20261023
```

Apply tạo tên `movielens_btl_int_<date>_<run-prefix>`, kiểm chưa tồn tại, marker gắn run/schemaSHA và owner. Context IntegrationConnection chỉ chấp nhận permit hợp lệ; ordinary connection vẫn dùng guard production gốc. Không monkeypatch/fixture bypass hoặc mở guard cho mọi DB. **CLI sản xuất S05/ETL/G3 vẫn dành riêng production; chỉ đổi POSTGRES_DB trong env không biến chúng thành công cụ tích hợp.** Dùng entry point mới để tránh tác động nhầm demo.

Schema.sql được chạy một lần với btl.target_database đúng đích, không chạy bootstrap demo hoặc IF NOT EXISTS che sai lệch. Mỗi chu trình staging→dimension→bridge→fact có một transaction/connection/advisory lock chung. TRUNCATE tường minh, giữ model_registry, vô hiệu hóa flags trước nạp; kiểm đủ hash/khóa/count/UTC trước COMMIT. Không suy snapshot tương đương từ surrogate hoặc mean nhóm.

Evidence `cycleN_etl.json` và `cycleN_dw_before_model.json` là **sau ETL, trước G3**, không phải model active. Chu trình2 phải giữ identity registry, tắt active/valid và xóa các dòng kết quả cũ theo đúng full refresh; không xóa registry để né conflict. Sau COMMIT loader mới được xét active.

## 3. OLAP → ML qua DW

Sáu view OLAP được cài trên DB thử từ database/views.sql, không sửa công thức hoặc bốn view contract. Đối soát KPI nền, O4 quý và O5 denominator/QoQ bằng API với force refresh.

CLI P2 đã merge được chạy bằng chính interpreter venv mới, `--source dw`, PGDATABASE là DB thử; PGUSER là BI reader và PGOPTIONS bật READ ONLY/UTC. Không dùng P2 evaluator test chính thức. Ba ca: evaluation có seed, evaluation fallback khi không có seed trong cutoff, demo full history. Lệnh thực tương ứng:

```text
python -m mining.recommend --source dw --user-id <case-user> --mode evaluation --top-n 5 --output-json <ignored-local-path>
python -m mining.recommend --source dw --user-id <case-user> --mode demo --top-n 5 --output-json <ignored-local-path>
```

PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD được truyền trong process environment, không URI/password args/logpublic. Evaluation dùng receipt/config k40, cutoff976422051; demo version riêng, không phát hành metric offline. Canonical hash kiểm trước fit. Hậu kiểm SQL đối chiếu history/seed/cutoff và gợi ý duy nhất/chưa đánh giá; output/history/seed theo user và log giữ local ignored.

Metric test trong official_test_metrics_reference.json được **trích báo cáo/receipt P2 đã nghiệm thu**, có nguồn/hash/runID; không trình bày như vừa đo lại. Không gọi mining/cf_test_evaluation.py hoặc snapshot evaluator để tái tạo provenance.

## 4. G3 → Superset

Dùng nguyên gói local đã kiểm `data/processed/p1_g3_20261020_intake`, producer frozen bab0b4049d4e0b1724418b8a92d8afbeda4bc775, model kmeans_k4_seed42 và hai CSV hash frozen. Không tái tạo hoặc đổi manifest/library/provenance theo HEAD mới. Snapshot gói được kiểm trước ghi; transaction dùng chính đường production_transaction đã kiểm, với context đích tích hợp hẹp. Cùng version khác payload/config/provenance bị từ chối; dữ liệu/registry/active state kiểm trước COMMIT.

Sau loader, cycleN_g3.json và summary phân biệt INSERT_NEW_VERSION, RELOAD_IDENTICAL_INVALIDATED_VERSION, NO-OP. Registered_at phải giữ nguyên qua refresh/reload/NO-OP. Bốn hash DW,6040user/6038assigned/2insufficient,2478/1393/760/1407,72profile và active views phải đúng.

8092 được chụp snapshot business config và database config private trước đổi kết nối bằng API chính thức sang DB thử. Chỉ GRANT CONNECT/USAGE/SELECT tám view cần cho ML/BI trên DB thử; không quyền ghi/CREATE/admin, không đổi production/firewall. Sau ETL/G3 các query force refresh cache, scope filter theo thiết kế11A/B/C. Hậu kiểm engine thực xác nhận current_database/role/UTC, không chỉ dựa số liệu giống demo.

8089 phục vụ demo, config/DW/model/ACL bảo toàn;8091 vẫn dừng. 8092 giữ kết nối DB tích hợp để review; không import ZIP, restore metadata hoặc sửa trực tiếp metadata trong12A. Các backup/clone/volume trước giữ nguyên.

## 5. P2 tự tái tạo DW khi không nhận backup

Checkout candidate kỹ thuật `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`, tạo venv từ requirements tổng và điền env cục bộ. Tải nguồn chính thức, so source_manifest. Không cần dump hoặc Superset để dựng riêng DW:

```text
python etl/recreate_integration_dw.py
python etl/recreate_integration_dw.py --apply --raw-dir <local-ml-1m-dir> --env-file .env --date 20261023 --report <new-local-report.json>
```

Entry point DW-only dùng cùng permit/transaction/serializer, tạo DB mới, schema→staging/fullrefresh→bốn hash→OLAP; không nạp G3 hoặc truy cập8092. Default plan-only đã kiểm; đường apply DW-only riêng chưa được chạy thêm trên máy P1, các core transaction được kiểm trong hai chu trình chính. P2 đã lưu report tái lập độc lập và được điều phối nghiệm thu sau PR28/PR29; intake G2 hiện CONFIRMED. Đây là nguồn riêng của P2, không đổi kết quả plan-only của P1. Thiếu CREATEDB thì chủ máy chuẩn bị quyền/DB phù hợp trước; không gửi mật khẩu vào chat.

Linux cần endpoint PostgreSQL/driver thực phù hợp; host.docker.internal trong Compose trên Windows không mặc nhiên dùng được trên Linux. Superset cần mạng/service hoặc host-gateway do chủ máy xác minh khi được giao; không đổi firewall tự động. Không yêu cầu P2 có Superset để kiểm DW/ML.

## 6. Backup/restore và giới hạn

[DW backup/restore](integration_prep/README.md) khác [metadata restore](../../dashboard/metadata_restore/README.md); ZIP import còn cần snapshot/UUID mapping/REST layout riêng. Clone DW cũ có database-level ACL khác nguồn dù owner/object ACL được giữ, không dùng thay bằng chứng full refresh12A.

Thư viện pandas cảnh báo DBAPI2 ngoài SQLAlchemy; lần chạy thực vẫn kiểm đủ canonical byte, không coi warning là lỗi dữ liệu. Hai chu trình không thay thuật toán/receipt/metric P2; same-host Windows/PG17.11/Superset6.1.0, P2 đã kiểm DW/adapter/ML/CLI trên Windows độc lập/Python3.12.6/PG17.4. Không kiểm Linux, Superset trên P2 hoặc phục hồi toàn stack máy mới. G4 đã đạt phạm vi I01–I15; báo cáo/slide/gói nộp G5 chưa hoàn thành.
