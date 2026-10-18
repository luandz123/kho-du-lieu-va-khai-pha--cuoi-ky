# Thiết kế kho MovieLens — nháp S04

**Cập nhật 6A:** chỉ bốn dimension đã được nạp từ staging, 6040/3883/18/1040 dòng; staging giữ nguyên, bridge/fact/ba analytics vẫn rỗng. Hai view user/movie đã khớp canonical; chưa G2 đủ bốn view. DDL giữ nguyên, không bootstrap lại. [Bàn giao 6A](../docs/P1/s06a_handoff.md), WAITING_REVIEW. Không chạy lại load S05 hoặc coi full refresh6D đã có. Các cập nhật S05/S04 dưới đây giữ lịch sử từng thời điểm.

**Cập nhật S05:** PR #6 đã merge; DDL này đã được thực thi trên database riêng movielens_btl trong phạm vi Bước 5, catalog khớp thiết kế. Chỉ staging được nạp; DW và analytics vẫn rỗng. Xem [bàn giao S05](../docs/P1/s05_handoff.md). Các nhãn “chưa chạy DDL” bên dưới mô tả lịch sử S04 tại thời điểm review, không phải trạng thái hiện tại của S05. SQL/thiết kế giữ nguyên.

**P1-S04-draft-v2, 16/10/2026: điều phối chấp nhận ở mức thiết kế. Chưa chạy DDL.**

Nguồn ghi nhận: **Điều phối chấp nhận S04 v2 ở mức thiết kế**, theo thông báo/giao đẩy của điều phối. Đây không phải lời duyệt nguyên văn của người dùng. Chấp nhận grain, UNIQUE user–movie theo EDA, bốn dimension/bridge, view UTC-Z, registry cho hai bảng cụm, full refresh nguyên tử/đối soát cùng connection và tỷ trọng gán genre. Giữ nguyên DDL; PR S04 là bước review công bố riêng, chưa có quyền merge hoặc thực thi SQL.

Đã công bố [PR #6 — S04](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/6), nhánh p1-s04-schema → main; **OPEN, chưa MERGED**. Đã rà toàn bộ 21 file, gồm checkpoint; lịch sử kiểm công bố nằm tại docs/P1/s04_publication_checks.json. Không chạy DDL.

<a id="cap-nhat-v2"></a>

## Cập nhật v2 — kế thừa v1, không tạo lại thiết kế

Điều phối giao hoàn thiện S04 sau PR #5 sửa G1 đã merge. API xác nhận PR #3/#4/#5 MERGED; PR #5 head `b73c8e2bc3bc98ff8576f75c02416cf2582bdc73`, merge `a8d2615df1e5aa522b2cceaaa073336d61013b83`. Đọc đầu vào sửa từ snapshot commit cố định qua GitHub, không pull/merge hoặc ghi file P2 vào checkout đang dở.

Bốn canonical hash, số dòng và hash nguồn không đổi. Manifest sửa đã bổ sung tập mã; ba hash script trong provenance khớp byte script ở merge PR #5. Một trường `source_code_commit` vẫn khác `provenance.original_commit_g1`/commit gốc thật; P2 đang sửa theo điều phối. Lưu dấu vết tại [snapshot đầu vào P1](../docs/P1/s04_inputs_pr5.json), không tự sửa metadata P2.

Điều phối báo đã kiểm độc lập và 23/23 test đạt; log `results/eda/test_evidence.txt` ở PR #5 ghi 23 passed. Đây là bằng chứng bàn giao đã đọc, không phải P1 chạy pytest mới trong S04. Adapter DW thật/raw–csv–DW vẫn chờ G2. Những mục chờ PR sửa R1–R6 ở phần lịch sử v1 bên dưới đã được cập nhật bằng đầu vào này; không tiếp tục dùng chúng để chặn thiết kế. Chưa tạo xác nhận APPROVED toàn bộ G1 hoặc S04.

Giữ nguyên toàn bộ định nghĩa DDL của v1 (chỉ bổ sung chú thích phiên bản/căn cứ). V2 làm rõ xử lý năm NULL, đếm rating đa genre, nạp lại không trùng và dùng cùng connection khi kiểm trước commit. Kiểm tra mới đối chiếu cả kiểu/null/PK/FK/index giữa các tài liệu, không thực thi SQL. Xem [báo cáo hoàn thiện](../docs/P1/s04_review_v2.md) và [bằng chứng kiểm tĩnh v2](../docs/P1/s04_design_checks_v2.json).

## Căn cứ khởi tạo v1 — giữ để truy vết

Điều phối cho phép thiết kế nháp song song khi các lỗi adapter/hồ sơ G1 đang được P2 sửa. Đây là điều chỉnh thứ tự so với điều kiện nghiệm thu G1 toàn bộ; không phải lời duyệt S04 hoặc lời duyệt thay P2. Chỉ các bằng chứng kỹ thuật đã đối soát được dùng để đề xuất khóa/kiểu.

| Tài liệu | Mục đích |
|---|---|
| [schema.sql](schema.sql) | DDL nháp, có guard database riêng; tuyệt đối chưa áp dụng ở lượt này |
| [erd.md](erd.md) | ERD Mermaid có PK/FK, quan hệ 1:N và ví dụ phim đa thể loại |
| [data_dictionary.md](data_dictionary.md) | Kiểu, nullability, khóa, nguồn, biến đổi và ý nghĩa từng trường |
| [source_to_target.md](source_to_target.md) | Ánh xạ nguồn→staging→DW→bốn view, schema/kiểu giao tiếp |
| [refresh_and_reconciliation.md](refresh_and_reconciliation.md) | Index, transaction/full refresh, lỗi/rollback, đối soát và nạp cụm |

## Căn cứ đã chốt để soạn nháp

- Contract v2: `docs/shared/data_contract.md/.json`, không sửa nội dung contract trong S04.
- PR#3 môi trường đã merge: `9846219eb0944e75e57f349e1bcfc88c7d1e8088`.
- PR#4 G1 head được review: `9299268278900814f939e0e4214d23a31e09ef64`; mã G1 chính ở `7a284b9`, merge main `b71d439fa2cc3ee84c40f4a28dc6fe00c8326d42`.
- Bằng chứng P1: `docs/P1/g1_review_2026-10-16.md`, `g1_verification_9299268.json`, `g1_pytest_9299268.txt`. Các file này được bảo toàn trong commit cục bộ riêng trước đồng bộ, không trộn vào commit thiết kế.
- Người kiểm nhận đã tải nguồn độc lập trong snapshot tạm; bốn tệp nguồn và bốn bảng canonical khớp hash. Lượt thiết kế này đọc/đối chiếu manifest và bằng chứng, **không tải/chạy EDA hoặc hash lại toàn bộ nguồn**.

| Bảng | Dòng canonical đã đối soát | SHA-256 CSV chuẩn |
|---|---:|---|
| users | 6040 | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | 3883 | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | 6408 | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | 1000209 | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

Kiểm nhận P1 ghi duplicate_pairs=0, rating ngoài 1..5=0, orphan user/movie/genre=0; mọi rated_at khớp timestamp UTC. Đây là căn cứ đề xuất UNIQUE(user_key,movie_key), không suy từ câu “100% sạch”. Grain vẫn là **một đánh giá nguồn**, không phải phiên xem hoặc toàn bộ lịch sử sửa đánh giá.

## Những quyết định thiết kế — đã được điều phối chấp nhận trong v2

1. Bốn dimension, bridge và fact; surrogate key chỉ trong DW, view trả ID MovieLens gốc. UNIQUE fact user–movie theo bằng chứng hiện tại; nếu nguồn khác/trùng xuất hiện phải dừng và chốt lại, không tự bỏ dòng.
2. Staging ba bảng raw-field text, có source_line để truy vết, không trường ZIP; chưa ép kiểu/ràng buộc nghiệp vụ để tránh mất lỗi trước đối soát.
3. `rated_at` trong fact là TIMESTAMPTZ; view xuất TEXT chuẩn UTC-Z. Cột ngày UTC sinh tự động và FK ghép bảo vệ khớp dim_date.
4. Ngoài **hai bảng kết quả cụm**, thêm `analytics.model_registry` là bảng kỹ thuật và hai view chỉ đọc model active; không thêm dimension/nghiên cứu mới. Chốt giao thức nạp/đổi active nguyên tử và vô hiệu hóa sau refresh DW.
5. Full refresh nguyên tử trong database dự án riêng; không DROP database, không dùng database quản trị `postgres` đã dùng kiểm kết nối S02. Tên database/quyền áp dụng sẽ được chốt ở bước thực thi, chưa tự đặt tên hoặc tạo database.
6. Phân biệt ràng buộc SQL với kiểm liên bảng/cả gói: K, mean profile, tổng bằng 1 trong sai số 1e-8, n_users, checksum và đầy đủ cohort phải kiểm trước activate, không giả CHECK SQL làm được tất cả.

## Phụ thuộc PR sửa G1 — lịch sử v1

**Đoạn dưới chỉ giữ diễn biến của v1. PR #5 đã MERGED**, không còn đang chờ mở PR sửa G1. Đọc [cập nhật v2](#cap-nhat-v2) và báo cáo v2 để biết căn cứ hiện hành; một SHA metadata P2 còn sửa không chặn thiết kế, adapter DW thật vẫn chờ G2.

R1: adapter DW chuẩn hóa datetime UTC-Z; R2: sửa phân vị q95/q99 và quy tắc làm tròn; R3: loại định danh/lịch sử theo user khỏi đầu ra Git và script sinh; R4: bổ sung tập mã/provenance đúng mã nguồn; R5: lọc exception DW; R6: CLI mismatch/lỗi trả mã khác 0. Đọc báo cáo P1 để có chi tiết.

P2/điều phối báo các sửa này không đổi count/bốn canonical hash; vẫn phải kiểm lại khi PR sửa có commit/merge cụ thể. Chưa có PR sửa OPEN trong lần API được kiểm cho lượt này; không suy đã hoàn tất. Không dùng trường source_code_commit=020ec90 trong manifest cũ làm phiên bản adapter đã chạy: báo cáo đã phát hiện SHA đó đứng trước script G1.

Việc sửa R1 vẫn phải làm dù view nháp chọn TEXT UTC-Z; cần test datetime thực và cuối cùng raw/csv/DW byte-equivalence trên PostgreSQL thật ở G2. Chưa nghiệm thu toàn bộ G1, chưa chạy DDL/schema/load/BI/ML hoặc bật Superset.
