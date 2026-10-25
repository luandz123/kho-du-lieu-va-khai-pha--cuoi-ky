# Phụ lục truy vết cho phần báo cáo P1

Phụ lục tập hợp identity, hash, nguồn kiểm chứng và lệnh dài của chương 1, 3, 4. Lệnh được trích để tái lập khi có cấu hình và phạm vi thực thi hợp lệ, không là bằng chứng đã chạy trong lượt biên tập. Hồ sơ review và trạng thái công bố tách tại [editorial_notes.md](editorial_notes.md).

## A. Các mốc không được đồng nhất

| Mốc | Giá trị | Phạm vi |
|---|---|---|
| Base12A / PR24 merge | `01d51a2db91ea4e4b390da23f9c9ca2f0aebfc02` | Nền code trước lượt thực thi12A |
| Code công bố12A | `3334ff8388cb0627c1af3d0b0c289f08f7e6e65e` | Commit công bố, khác hash code working tree lúc chạy |
| Candidate | `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` | Merge PR25, candidate thực chạy đã được P2 kiểm nhận; điều phối nghiệm thu G4 ngày 24/10/2026, phạm vi I01–I15 |
| Run12A | `57c1e8e3d3f445c4b3eeddbfc3364709` | Hai chu trình trên P1,833.922giây |
| Database12A | `movielens_btl_int_20261023_57c1e8e3` | Database thử, khác movielens_btl demo |
| Bundle runtime12A | `3114721fd957a9c98da89b0bfcf615500ae6d6833bfdae31ad58111d23424e22` | SHA256 JSON sortkeys của dictionary code_sha256 trong summary; code chưa commit lúc chạy |
| Dàn ý13A | PR26, merge `dad848eedcd11230559acfc01ee103be718289a2` | Dàn ý đã merge, khác PR phần chương |

Nguồn: [summary12A](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json), [code_reference](../12a_publication/code_reference.json), [ghi nhận P2](../p2_intake_reported_20261024.json). Không gán commit công bố vào report runtime cũ.

## B. Canonical và receipt

| Bảng | Row_count | SHA256 canonical |
|---|---:|---|
| users | 6040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | 3883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | 6408 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | 1000209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

Receipt Test chính thức: `test_run_s10b_official_20261022_034458`. File [cf_test_evaluation_receipt.json](../../../results/mining/cf_test_evaluation_receipt.json), SHA256 byte `57c16c3c45feea756b771d0b206cb6ec957135205736a4ae40cbb25255af4b50`. SHA byte file khác trường checksum nội bộ; không thay trường nội bộ để ép tự tham chiếu. Metrics tại metrics_comparison là nguồn chương5/chỉ mục, không phải kết quả đánh giá lại từ DW12A.

GóiG3 dùng producer `bab0b4049d4e0b1724418b8a92d8afbeda4bc775`, model `kmeans_k4_seed42`. Hai CSV frozen:

- user_cluster.csv: `5812d961fab8cab72f3e9f2589b66619ba2b6a11f2b3f20d9e00ead2f7ab3b93`.
- cluster_genre_profile.csv: `59f9237ee12e02992d09add9cb940808902a247fcefeda9dbcd72808c9ad533d`.

Payload theo user không đính kèm báo cáo. Provenance giữ nguyên, không đổi theo HEAD công bố mới.

## C. Lệnh và khả năng tái lập

Lệnh dưới trích từ [integration_runbook.md](../integration_runbook.md), chạy ở root với cấu hình cục bộ hợp lệ. Các trạng thái cũ trong runbook được đối chiếu ghi nhận hiện hành ngày24/10, không dùng làm xác nhận mới của P2. Hai lệnh mặc định chỉ lập kế hoạch:

```text
python etl/run_integration.py
python etl/recreate_integration_dw.py
```

Helper DW-only tạo database mới, schema, ETL, đối soát và OLAP khi được apply. Trên P1, lệnh riêng này mới được kiểm plan-only; không mô tả apply riêng đã chạy. Lõi ETL đã được kiểm trong hai chu trình12A. P2 tái lập Windows bằng đường DW-only là nguồn riêng đã được điều phối nghiệm thu sau PR28/PR29, không phải lần apply riêng trên P1. Nguồn hiện hành: [ma trận 12B](../integration_acceptance.md), [ghi nhận G4](../g4_acceptance_20261024.json). Lệnh tái lập:

```text
python etl/recreate_integration_dw.py --apply --raw-dir <local-ml-1m-dir> --env-file .env --date <YYYYMMDD> --report <new-local-report.json>
```

Các ca CLI được ghi dưới dạng không gắn user thật:

```text
python -m mining.recommend --source dw --user-id <case-user> --mode evaluation --top-n 5 --output-json <ignored-local-path>
python -m mining.recommend --source dw --user-id <case-user> --mode demo --top-n 5 --output-json <ignored-local-path>
```

PGDATABASE trỏ đúng đích thử. Credential truyền qua cấu hình/environment cục bộ, không đưa URI có mật khẩu vào lệnh hoặc báo cáo. Không gọi evaluator Test để tái tạo metric. Khác biệt cú pháp venv/network giữa Windows và Linux phải được kiểm trên máy tương ứng; không có bằng chứng Linux trong phạm vi hiện tại.

## D. Nguồn kiểm thử và phục hồi

- ETL6D: [summary](../../../results/warehouse/s06d_summary.json), [rollback](../../../results/warehouse/s06d_rollback_5c9c553454e54e81953fded2d524877c.json).
- OLAP: [reportS07](../../../results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json), [findings](../olap_findings.md).
- Tích hợp12A: [postflight](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/postflight.json), [environment](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/environment.json), [hậu kiểm OLAP](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/olap_all_six.json).
- DW restore/metadata: [runbook chuẩn bị](../integration_prep/README.md); ZIP và REST layout: [runbook import](../../../dashboard/restore/README.md). Dump/key/private config không nằm trong phụ lục.
- Tài liệu ngoài repository: [references.md](references.md), phân biệt nguồn chính thức/nghiên cứu gốc với artifact nội bộ.
