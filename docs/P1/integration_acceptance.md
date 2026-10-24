# Tổng hợp nghiệm thu tích hợp 12B

Ngày 24/10/2026, phiên bản P1-12B-v1. **12B = WAITING_REVIEW**. **Đề xuất G4 đạt trong phạm vi tích hợp đã kiểm; chưa xác nhận G4 hoàn thành và không tự merge.** Lượt này chỉ đọc Git/artifact, kiểm hash và tổng hợp bằng chứng; không chạy lại ETL/G3/evaluator/dump/restore hoặc truy vấn hệ thống demo.

## 1. Căn cứ và các mốc phải phân biệt

Nguồn giao việc là thông điệp điều phối qua người dùng: “Điều phối nghiệm thu 12-P2 sau khi kiểm PR28 và bản sửa PR29.” Theo xác nhận này và hồ sơ đã merge, **P2 intake G2 = CONFIRMED trên máy P2/Windows độc lập**. Đây không phải lời duyệt 12B/G4; trạng thái hai mốc đó vẫn chờ review của điều phối.

| Mốc | Commit | Ý nghĩa |
|---|---|---|
| Candidate kỹ thuật đã P2 chạy | `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` | MergePR25, checkout riêng trên P2; không thay bằng main mới |
| PR28 đã merge | `88c5c7b952553523f58e82ed6546179451eb6b65` | Công bố hồ sơ12-P2 và artifact tổng hợp |
| PR29 đã merge | `d20d3bc382e603cc219bc4a742814bae793421ab` | Bản sửa hồ sơ12-P2 đã được điều phối kiểm; main nền của12B |
| PR27 báo cáo P1 đã merge | `03d9bc9932f7919c5eb5d04075f0235a1e0448fc` | Tài liệu/hình/checklist P1, không phải một lượt chạy tích hợp mới |
| Code công bố12A của P1 | `3334ff8388cb0627c1af3d0b0c289f08f7e6e65e` | Commit công bố code; khác working-tree hash thực chạy |
| Run tích hợp P1 | `57c1e8e3d3f445c4b3eeddbfc3364709` | Base lúc chạy `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02` và code chưa commit; bundle SHA giữ nguyên |

API xác minh các PR nêu trên MERGED; `git merge-base --is-ancestor` xác minh cả candidate, PR28 và PR29 là tổ tiên của main nền12B. Quan sát và hash nguồn tại [integration_acceptance_sources.json](integration_acceptance_sources.json). Commit công bố tài liệu12B được ghi riêng khi xuất bản; **không gán commit đó vào run P1 hoặc P2 đã xảy ra trước**.

## 2. Phạm vi môi trường và cách đọc kết quả

| Bên / nguồn | Môi trường đã có bằng chứng | Phạm vi thực chạy | Không được suy rộng |
|---|---|---|---|
| P1 — [environment12A](../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/environment.json), [summary12A](../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json) | Windows, Python 3.12.14, PostgreSQL 17.11; Superset 6.1.0 trong môi trường/container riêng | Hai chu trình DB thử, ML/CLI qua DW, OLAP, G3 và dashboard8092; BI/restore ở các mốc P1 được dẫn | Không là bằng chứng Linux hoặc phục hồi cả stack trên máy mới |
| P2 — [environment](../../results/mining/integration_p2/environment.json), [báo cáo đã sửa](../P2/integration_report.md) | Máy Windows 11 độc lập, Python 3.12.6, PostgreSQL 17.4 | Checkout candidate, venv mới, requirements/pip check; DW-only apply, adapter raw/CSV/DW, Q1/G3 và CLI | Không chạy Superset, không nạp analytics G3 trên P2; không Linux |

Hai môi trường có khác patch Python/PostgreSQL và một số dependency chuyển tiếp. `pip check` không phát hiện xung đột được khai báo, không chứng minh tương thích tuyệt đối. Tái lập ở đây là kết quả trong hai phạm vi Windows đã nêu, không tuyên bố môi trường byte-identical.

Kết quả “đạt” trong ma trận là kết luận tổng hợp từ artifact và review đã có. P1 không chạy lại trên máy P2 trong lượt 12B. Receipt lịch sử có thể còn `NOT_CONFIRMED`, `WAITING_REVIEW` hoặc `candidate_selected=false` tại thời điểm được tạo; cập nhật hiện hành nằm ở tài liệu này, không sửa ngược các receipt đó.

## 3. Ma trận yêu cầu → bằng chứng → kết quả → giới hạn

Các tiêu chí dựa [đặc tả](../project_spec.md), [acceptance nội bộ](../acceptance.md) và [contract v2](../shared/data_contract.md). G4 là mốc nghiệm thu tích hợp; hoàn thiện sáu chương/slide/gói nộp thuộc nhánh tài liệu/G5, chưa được đánh dấu hoàn thành trong 12B.

| Mã / yêu cầu | Bằng chứng P1 | Bằng chứng P2 | Kết quả tổng hợp | Giới hạn cần giữ |
|---|---|---|---|---|
| I01 — đúng candidate và môi trường | Environment/summary12A, code_reference trong [công bố12A](12a_publication/code_reference.json) | environment.json và integration_report.md, checkout candidate | Đạt trong hai môi trường đã ghi | Không Linux; commit tài liệu khác commit chạy |
| I02 — nguồn/contract thống nhất | [G2 manifest](../../results/warehouse/dw_manifest.json), source/canonical hashes trong summary12A | [source_equivalence](../../results/mining/integration_p2/source_equivalence.json), báo cáo nguồn bốn tệp | Đạt: contract v2, bốn bảng logic thống nhất | Không tự đổi hash/serializer để ép khớp; ZIP code không dùng |
| I03 — schema/staging/DW đúng grain, khóa, UTC | [S05](../agent/steps/P1/S05.md), [S06](../agent/steps/P1/S06.md), [postflight12A](../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/postflight.json) | [dw_reconstruction](../../results/mining/integration_p2/dw_reconstruction.json), bốn view/column order và UTC trong source_equivalence | Đạt theo kiểm P1 và giao diện tái lập P2 | Không coi count đơn lẻ là đủ hoặc claim mọi catalog test đã chạy lại trên P2 |
| I04 — full refresh nguyên tử và chạy lại | Hai cycle_etl và checkpoint trước model của 12A; summary ghi hai COMMITTED, cùng bốn hash/count | P2 DW-only tạo DB mới, COMMITTED | Đạt: P1 kiểm hai chu trình, P2 kiểm đường tái tạo độc lập | P2 có một lượt DW-only được công bố, không gọi đó là hai chu trình P2 |
| I05 — rollback phục hồi snapshot/model | [summary6D](../../results/warehouse/s06d_summary.json), [rollback fixture](../../results/warehouse/s06d_rollback_5c9c553454e54e81953fded2d524877c.json) | Unit tests P2 không thay bằng chứng rollback DB P1 | Đạt các ca fixture đã nghiệm thu | Không thử lỗi trên nguồn thật; không chứng minh mọi sự cố phần cứng/COMMIT mất kết nối |
| I06 — G2 thật qua adapter | [adapter6D](../../results/warehouse/s06d_adapter_c75f9cb0ceb04d74bfa36e140d812754.json), postflight12A | RAW/CSV/DW tương đương bốn view; p2_intake_g2=CONFIRMED | **Đạt; intake P2 CONFIRMED,12-P2 được điều phối nghiệm thu** | CSV không thay DW; đây là P2 xác nhận trên DB của máy P2, không nối hai máy trực tiếp |
| I07 — Q1/G3 tái lập từ DW | Gói frozen được kiểm/nạp tại [11B2](../../results/warehouse/s11b2/handoff_summary.json), model/count/profile | [g3_reproduction](../../results/mining/integration_p2/g3_reproduction.json) từ DW, hai frozen CSV khớp | Đạt:6.038 assigned / 2 insufficient, bốn cụm và72 profile | Byte-identical chỉ hai CSV, không áp toàn manifest/môi trường |
| I08 — registry/invalidation/reload/NO-OP | cycle1_g3,cycle2_g3 và postflight12A; active/valid/registered_at được đối soát | dw_reconstruction ghi g3_loaded=false; P2 tái tạo gói, không nạp analytics | Đạt tại P1, đúng phân công | Không tuyên bố loader/active views đã chạy trên máy P2 |
| I09 — Q2 có baseline và Test đóng băng | [official_test_metrics_reference12A](../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/official_test_metrics_reference.json) | [receipt chính thức](../../results/mining/cf_test_evaluation_receipt.json), protocol và hồ sơ10B/12-P2 | Đạt: giữ receipt/cutoff/k40 ; 12B không đánh giá lại | Metric là tham chiếu lượt Test đã chốt, không phải metric mới từ DW tích hợp |
| I10 — ML/CLI đọc DW thật | Sáu ca qua hai chu trình, seed/cutoff/Top 5/unseen theo postflight12A | [CLI summary](../../results/mining/integration_p2/cli_verification_summary.json): có seed, fallback, demo;31 unit tests trong [log](../../results/mining/integration_p2/test_suite_log.txt) | Đạt các ca đã công bố | Unit test guard không phải rerun evaluator Test trên dữ liệu thật; không đưa output theo user vào Git |
| I11 — sáu OLAP và ngữ nghĩa chỉ số | [reportS07](../../results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json), [findings](olap_findings.md), [OLAP hậu kiểm12A](../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/olap_all_six.json) | Helper DW-only có bước tạo view; không có bảng đo O1–O6 mới của P2 trong gói | Đạt theo bằng chứng P1 | SUM/COUNT; không cộng genre/cấp thời gian; QoQ zero-fill/NULL/quý biên/prev≥100 |
| I12 — ba dashboard/filter và BI reader | Reconciliation [Tổng quan](../../dashboard/overview/evidence/reconciliation.json), [Xu hướng](../../dashboard/trends/evidence/reconciliation.json), [Sở thích](../../dashboard/preferences/evidence/reconciliation.json);12A8092; [BI role](../../dashboard/overview/evidence/bi_reader_final.json) | Không cài/kiểm Superset trên P2 | Đạt tại P1: SQL/API/UI theo các mốc, engine/role/view permissions có kiểm thực | Session READ ONLY không đủ; PUBLIC TEMP còn; không hứa BI đã kiểm trên P2 |
| I13 — backup/restore DW | [backup/restore receipt](../../results/warehouse/s12a_prep/backup_restore_2856ed49e9ba494090e2acae73b41b9a.json), [postflight](../../results/warehouse/s12a_prep/postflight.json) | P2 dựng DW từ nguồn, không cần nhận dump | Đạt restore clone tại P1 | Database-level ACL clone khác nguồn, cùng cluster/roles; không off-machine toàn stack |
| I14 — metadata restore và ZIP import | [metadata final](../../dashboard/metadata_restore/evidence/final_observation.json), [ZIP restore final](../../dashboard/restore/evidence/final_observation.json), [runbook](../../dashboard/restore/README.md) | Không Superset/metadata restore trên P2 | Đạt trong phạm vi P1 được nghiệm thu | ZIP cần snapshot/UUID mapping/REST layout; metadata restore là cơ chế khác, cùng máy/version/DW hiện hữu |
| I15 — truy vết/hygiene | Hash code/runtime/manifest, report PASS/FAIL giữ nguyên, role/dữ liệu nguồn bảo toàn theo receipt | manifest của 6 artifact đã rà và khớp blob Git | Đạt đối chiếu tệp công bố; không thấy lỗi bắt buộc còn mở qua ma trận | Tệp text CRLF trong checkout khác byte blobLF; không dùng nhận xét này để chuẩn hóa nguồn/canonical/G3 |
| I16 — báo cáo/slide và G5 | PR27 nội dung P1/hình/checklist đã merge | Phần chương P2 chờ bàn giao được duyệt riêng | Ngoài điều kiện chốt tích hợp12B; chưa hoàn thành G5 | Không ghép DOCX/slide hoặc coi dự án hoàn tất trong lượt này |

## 4. Bốn canonical hash/count và hai checksum G3

Bảng dưới được đối chiếu giữa canonical manifest, G2 manifest, hai chu trình P1, postflight12A, P2 DW reconstruction và source_equivalence. Không chạy serializer hoặc đọc lại dữ liệu DW trong 12B.

| Bảng logic | Count dữ liệu ở P1/P2 | SHA256 canonical |
|---|---:|---|
| users | 6.040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | 3.883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | 6.408 cặp phim–genre | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | 1.000.209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

6.408 là số cặp movie–genre, không phải số thể loại; tập genre có 18 tên. Đối với ratings, timestamp int64 và rated_at UTC-Z biểu diễn cùng thời điểm, thứ tự cột theo contract; không nối bridge vào view ratings. Count không tính header CSV.

| Tệp G3 | Count dữ liệu | SHA256 frozen, P1 đã nhận và P2 tái lập khớp |
|---|---:|---|
| user_cluster.csv | 6.040 | `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93` |
| cluster_genre_profile.csv | 72 | `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d` |

Model `kmeans_k4_seed42`, K=4, preprocessing raw, seed42, n_init=10. Assigned 6.038, insufficient_evidence 2; quy mô cụm0..3 là 2.478 / 1.393 / 760 / 1.407. P1 giữ gói/provenance producer frozen đã kiểm; P2 tái tạo hai CSV từ DW trong thư mục mới. Không ghi đè model active P1 hoặc yêu cầu toàn bộ manifest P2 có byte giống manifest P1.

## 5. Hai chu trình P1 và tái lập độc lập P2

P1 dùng database thử `movielens_btl_int_20261023_57c1e8e3`, tách demo. Hai chu trình cùng code/config trong run 57c1e8e3… có full refresh COMMITTED và bốn canonical khớp. Checkpoint sau ETL không được gọi là kết quả sau nạp G3:

| Điểm kiểm | Chu trình 1 | Chu trình 2 |
|---|---|---|
| Sau ETL | Registry 0; active 0 / valid 0, kết quả cụm rỗng | Giữ 1 registry; active 0 / valid 0, user_cluster/profile rỗng |
| Nạp G3 | INSERT_NEW_VERSION → COMMITTED | RELOAD_IDENTICAL_INVALIDATED_VERSION → COMMITTED |
| Sau G3 | Registry 1 active/valid; user 6.040 / profile 72 | Cùng identity và counts; registered_at giữ nguyên |
| Apply kiểm lặp | COMMITTED_NO_OP | COMMITTED_NO_OP |

Nguồn: cycle1_etl.json,cycle2_etl.json,cycle1_g3.json,cycle2_g3.json và summary/postflight trong thư mục run12A đã liên kết. Rollback snapshot/model được chứng minh bởi fixture6D đã nghiệm thu, không tạo ca lỗi mới trong 12B.

P2 tái tạo DW bằng helper DW-only trên database riêng `movielens_btl_int_20261023_e7b2219c`, run `e7b2219c75e847e38005de5d0e2509a9`, transaction COMMITTED. `source_equivalence.json` ghi raw/csv/dw cùng count/hash và column order; intake G2 CONFIRMED. P2 tiếp tục feature Q1/G3 từ DW và ba ca CLI, gồm evaluation cóseed, evaluation fallback và demo full-history. Không cài Superset hoặc nạp analytics G3 trên P2; các phần đó được kiểm tại P1 theo ma trận.

P1 có 88 test mục tiêu được ghi trong environment12A; P2 có 31 unit tests gồm 7 evaluator guard, 15 recommender và 9 CF. Các con số là kết quả lịch sử theo artifact, không là số test vừa được chạy trong lượt tổng hợp này.

## 6. Metrics Test: chỉ tham chiếu receipt chính thức

Nguồn duy nhất cho bảng này là `metrics_comparison` trong [receipt Test](../../results/mining/cf_test_evaluation_receipt.json), run `test_run_s10b_official_20261022_034458`, k40, Top 5, cùng cohort 1.154. 12B không gọi evaluator, không thay receipt/metric hoặc coi CLI demo là metric offline.

| Mô hình | macro Precision@5 | macro Recall@5 | Hits | User fallback |
|---|---:|---:|---:|---:|
| Popularity Baseline | 0.201733 | 0.02712408 | 1.164 | 0 |
| Item-based CF k40 | 0.231023 | 0.03530289 | 1.333 | 2 |

Đây là kết quả lượt Test đã chốt, không phải phép đánh giá lại từ DW tích hợp/P2. Không suy tính vượt trội mọi bối cảnh hoặc ý nghĩa thống kê khi chưa kiểm định. Receipt file giữ nguyên; SHA byte được ghi trong audit nguồn, phân biệt với checksum nội bộ của chính receipt.

## 7. Phạm vi BI/phục hồi và giới hạn không phải lỗi chức năng còn mở

- Ba dashboard đã kiểm ở P1 theo SQL/API/UI;12A kiểm engine8092 thực kết nối DB tích hợp bằng BIreader, tám view SELECT cần thiết, không có DML/CREATE trên object dự án. PUBLIC TEMP còn là giới hạn được công bố, không gọi session READ ONLY thành chứng minh mọi quyền đều chỉ đọc.
- Tổng quan toàn kỳ/Q3/2000 có 1.000.209 / 324.864 rating; Animation 2001Q1 có 1.715, prev 20.068, QoQ−91,454056%; Sở thích toàn bộ/lọc cụm1-F-25–34 có 6.038 / 170 assigned, baseline 6.038 và insufficient 2 theo bằng chứng P1. Không chạy lại chart trong 12B.
- DWclone restore, metadata restore riêng8092 và ZIP import8091 đã được kiểm theo các receipt P1. ZIP cần bước REST phục hồi layout; metadata restore dùng key/config cục bộ và giữ bố cục theo cơ chế khác. Không có chứng minh phục hồi toàn stack trên máy mới.
- Không kiểm Linux, Superset trên máy P2, kết nối BI từ máy P2 sang P1, hoặc mọi cấu hình/version có thể có. Tái lập độc lập P2 bằng nguồn/candidate là phạm vi đã nghiệm thu, không phải kiểm mạng giữa hai máy.
- Bằng chứng P2 công bố là thống kê tổng hợp; user-level output, góiCSV/model/dump/key ở cục bộ. P1 đối chiếu artifact đã merge và xác nhận điều phối, không tuyên bố đã quan sát trực tiếp mọi thao tác trên máy P2.

## 8. Kiểm tệp công bố, đề xuất và điểm cần duyệt

Manifest P2 chứa hash/kích thước của 6 artifact công bố. Cả 6 khớp chính xác blob Git tại main đã chứa PR29. Working tree Windows của P1 dùng CRLF nên hash/size byte cục bộ khác; audit ghi riêng raw working copy/Git blob và xác nhận chỉ khác xuống dòng. Đây là kiểm tệp văn bản chứng cứ, **không sửa file P2, manifest, nguồn MovieLens, canonical CSV hoặc hai CSV G3 để ép hash**. Hash canonical/G3 ở trên giữ đúng byte chuẩn đã chốt.

Sau đối chiếu, **không phát hiện lỗi chức năng bắt buộc còn mở trong phạm vi ma trận I01–I15**. Đề xuất điều phối duyệt12B và chốt G4 đạt cho phạm vi Windows P1/P2 cùng BI/phục hồi ở P1 đã mô tả. Các giới hạn ở mục 7 và công việc tài liệu/G5 không bị xóa hoặc đổi thành đã hoàn thành.

**Trạng thái hiện hành:**12-P2 đã được điều phối nghiệm thu; P2 intake G2 CONFIRMED ; 12B = WAITING_REVIEW; G4 được đề xuất đạt nhưng **chưa được tự đánh dấu hoàn thành**. PR hồ sơ12B cũng phải phân biệt OPEN/APPROVED/MERGED. Chờ điều phối review và lệnh tiếp theo; không tự merge, tag hoặc ghép báo cáo tổng.
