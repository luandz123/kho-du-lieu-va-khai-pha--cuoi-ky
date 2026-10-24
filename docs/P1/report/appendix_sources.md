# Phụ lục truy vết cho bản thảo P1

24/10/2026 — WAITING_REVIEW cùng chương1/3/4. Phụ lục chứa identity/lệnh dài để thân báo cáo tập trung phương pháp và kết quả. Không thực thi các lệnh dưới đây trong lượt viết.

## A. Các mốc không được đồng nhất

| Mốc | Giá trị | Phạm vi |
|---|---|---|
| Base12A/PR24merge | `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02` | Nền code, không là code thực chạy đãcommit |
| Code công bố12A | `3334ff8388cb0627c1af3d0b0c289f08f7e6e65e` | Commit công bố riêng với run |
| Candidate | `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` | MergePR25, P2 báo tái lập; bằng chứng chờreview/G4 |
| Run12A | `57c1e8e3d3f445c4b3eeddbfc3364709` | Hai chu trình đã chạy trênP1,833.922s |
| Database12A | `movielens_btl_int_20261023_57c1e8e3` | Database thử, khác movielens_btl demo |
| Bundle runtime12A | `3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22` | SHA256 JSON sortkeys của dictionarycode_sha256 trongsummary, code chưacommit lúcchạy |
| PRdàný13A | PR26 / `981be3725dc192875ac361b53a39c13e370de97c` | Không chứa bản thảo các chương |

Nguồn: [summary12A](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json), [code_reference](../12a_publication/code_reference.json), [quan sátP2](../p2_intake_reported_20261024.json). Không sửa report cũ để trỏ commit mới.

## B. Canonical và receipt

| Bảng | Row_count | SHA256 canonical |
|---|---:|---|
| users | 6040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | 3883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | 6408 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | 1000209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

Receipt test chính thức: `test_run_s10b_official_20261022_034458`. File [cf_test_evaluation_receipt.json](../../../results/mining/cf_test_evaluation_receipt.json), SHA256 byte hiện có `57c16c3c45feea756b771d0b206cb6ec957135205736a4ae40cbb25255af4b50`. SHA file này khác trường checksum nội bộ; không thay trường đó để ép tự tham chiếu. Metrics tại metrics_comparison là nguồn chương5/chỉ mục, không đánh giá lại.

GóiG3: producer `bab0b4049d4e0b1724418b8a92d8afbeda4bc775`, model `kmeans_k4_seed42`. Hai CSV frozen lần lượt users `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93`, profile `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d`. Payload theo user không đính kèm báo cáo; provenance giữ nguyên, không đổi theoHEAD mới.

## C. Lệnh và khả năng tái lập

Lệnh từ [integration_runbook.md](../integration_runbook.md), chạy ở root khi có lệnh thực thi riêng và cấu hình cục bộ hợp lệ. Phần trạng thái NOT_CONFIRMED/chưacandidate trong runbook là lịch sử; ghi nhận hiện hànhP2 nằm ởJSONngày24/10. Ví dụ đọc kế hoạch mặc định, không nạp:

```text
python etl/run_integration.py
python etl/recreate_integration_dw.py
```

HelperDW-only tạo DBmới/schema/ETL/đốisoát/OLAP khi được apply; P1đãkiểmplan-only riêng, không tuyên bố apply riêng đãchạy. CoreETL đãđược kiểm tronghai chu trình12A. P2báo tái lậpWindows khác là ghi nhận đangchờreview, khôngthay chứngcứ P1:

```text
python etl/recreate_integration_dw.py --apply --raw-dir <local-ml-1m-dir> --env-file .env --date <YYYYMMDD> --report <new-local-report.json>
```

Các ca CLI thực đã kiểm được mô tả khônggắn userthật:

```text
python -m mining.recommend --source dw --user-id <case-user> --mode evaluation --top-n 5 --output-json <ignored-local-path>
python -m mining.recommend --source dw --user-id <case-user> --mode demo --top-n 5 --output-json <ignored-local-path>
```

PGDATABASE trỏ đúngđíchthử; credential truyền qua cấu hình/environment cục bộ, khôngURI/mật khẩu tronglệnh báo cáo. Không gọi evaluator test để táitạo metric. Windows vàLinux có cúphápvenv/network khác nhau; chỉWindows đãcóbằngchứng như được dẫn.

## D. Nguồn kiểm thử và phục hồi

- ETL6D: [summary](../../../results/warehouse/s06d_summary.json), [rollback](../../../results/warehouse/s06d_rollback_5c9c553454e54e81953fded2d524877c.json).
- OLAP: [reportS07](../../../results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json), [findings](../olap_findings.md).
- Tíchhợp12A: [postflight](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/postflight.json), [environment](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/environment.json), [OLAPhậukiểm](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/olap_all_six.json).
- DWrestore vàmetadata: [runbookchuẩnbị](../integration_prep/README.md); ZIP/RESTlayout: [runbookimport](../../../dashboard/restore/README.md). Không đưa dump/key/privateconfig vào phụ lục.
- Reviewhình: [image_review.json](image_review.json). ẢnhSởthích bịmờ không làhìnhchính; chưa cóchụpmới tronglượtviết.
