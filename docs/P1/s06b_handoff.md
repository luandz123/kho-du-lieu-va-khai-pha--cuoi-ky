# Bàn giao 6B — bridge phim và thể loại

18/10/2026, Asia/Bangkok. **6B WAITING_REVIEW**. 6A được điều phối chấp nhận sau review và chạy lại 13/13 unit test theo thông báo điều phối; đây không phải lời duyệt nguyên văn do agent tạo. Chưa 6C/6D, G2, OLAP hoặc dashboard.

## Mốc và đầu vào

Giữ nhánh `p1-s06-etl`. Sau rà diff, chữ ký bí mật, allowlist 23 file P1 và hash artifact 6A, đã tạo checkpoint cục bộ **cfed2c848e196bee73fcb61ec5fd017cc9dbaf98** trên nền 52dd682. Không push/PR/fetch/merge/switch/reset/stash. Kế hoạch ngoài phạm vi `docs/KE_HOACH_BTL_MOVIELENS.md` vẫn untracked, SHA-256 da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7.

Nguồn đầu vào: contract v2, schema/mapping/refresh S04, source_manifest và canonical_manifest đã kiểm nhận, staging snapshot S05 f5f11bcd, dimension 6A. Nguồn raw cục bộ `data/raw/p1_s05/ml-1m`, tải độc lập trước S05. Không sửa P2, dữ liệu nguồn, manifest, DDL hoặc code S05/6A.

Preflight chỉ đọc xác minh đúng `movielens_btl`, marker và catalog đã duyệt; bốn hash/count nguồn, từng field/source_line ba staging khớp S05. Bốn dimension chính xác (6040/3883/18/1040), lịch UTC 2000-04-25..2003-02-28 và mọi cột generated, hai hash users/movies khớp. Bridge/fact/ba analytics đều 0 trước nạp. Bằng chứng `s06b_preflight_6abb1f4165f0473ca86a76e9e1f502b1.json`.

## Cách nạp và kiểm

Code `etl/s06b_bridge.py` đọc movies_raw, tách `|` giữ nguyên tên; lập ánh xạ movie_id→movie_key và genre_name→genre_key, kiểm từng khóa tồn tại duy nhất. Thiếu/ambiguous mapping, phim hoặc cặp trùng, genre lạ/NULL/rỗng đều dừng; không deduplicate hoặc inner join bỏ khóa lỗi. Surrogate không giả bằng ID nguồn.

Một transaction và advisory lock (20261027,1), SHARE-lock staging; SHARE ROW EXCLUSIVE-lock các target để bảo vệ snapshot trong cả kiểm và insert. Chỉ INSERT bridge, đòi bridge rỗng. Kiểm bằng **cùng connection trước commit**: toàn bộ cặp surrogate và cặp ID nguồn/genre, PK không trùng, LEFT JOIN phát hiện orphan, số genre từng phim, cột/thứ tự view, sort movie_id/genre_name rồi dùng serializer G1 đã review. So lại staging, toàn bộ trường vật lý dimension gồm surrogate, hai hash users/movies, lịch UTC và target còn lại. Không sửa staging/dimension/fact/analytics, không TRUNCATE/DELETE/upsert/bootstrap/DDL production.

## Kết quả thực tế

| Chỉ tiêu | Kết quả |
|---|---|
| dw.bridge_movie_genre | **6408** dòng |
| Số phim được đối soát / phim nhiều genre | **3883 / 1858** |
| Cặp trùng / FK mồ côi | **0 / 0** |
| Toàn bộ cặp nguồn và số genre từng phim | Khớp chính xác |
| v_ml_movie_genres | Đúng cột movie_id, genre_name; 6408 dòng |
| Canonical SHA-256 | **9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf** |
| Staging và mọi trường dimension/surrogate | Giữ nguyên |
| v_ml_users / v_ml_movies | Hai canonical hash vẫn khớp |
| Fact / v_ml_ratings / ba analytics | Đều **0** |

Loader thực chạy SHA-256 **6ef72d126c2274780c3638744a95d58ffedf0a35d38c30d1cd4ae2b99ddcecd5**; code 6B còn working tree, không gán code mới cho checkpoint 6A. Run **691f5ae7935d43988ca05254cd5ba5f1**, bắt đầu 2026-10-18T12:27:22.159279+00:00, **10.719 giây**, PASS/COMMITTED. Preflight, unit, fixture và load/verify cùng loader hash; không sửa loader giữa các lần này.

Hậu kiểm riêng **READ ONLY / REPEATABLE READ** run 03911484445047ebbfa19d579b73e4d1 PASS. So với baseline trước nạp trong report load thành công, không chỉ so COUNT. G2 chưa hoàn thành: mới ba view có dữ liệu, ratings/fact chưa nạp và adapter DW đầy đủ chưa kiểm.

## Test và lỗi đã giữ

- **15/15 unit test** đạt: mapping thiếu/không duy nhất/surrogate sai; phim/cặp trùng; genre lạ/rỗng/không trim; phim nhiều genre; sort/header/CSV bytes và namespace.
- Fixture PostgreSQL tự tạo trong schema `s06b_test_<UUID>`, surrogate khác ID nguồn: 2 phim/2 genre→3 cặp, dim_movie vẫn **2** dòng, không tăng khi phim có 2 genre.
- Mapping thiếu và cặp nguồn trùng bị từ chối; sau insert 3 cặp thử, cố ý vi phạm FK **23503** và PK **23505**, từng transaction rollback về **0** cặp. Fixture hợp lệ sau đó đạt, production giữ nguyên; schema thử đã dọn đúng tên, không CASCADE.
- Report fixture đầu 9ac28776 FAIL do gọi catalog strict trước khi dọn bảng thử. Đã sửa **script fixture** để dọn trước kiểm catalog cuối, không đổi loader/DDL/checker cũ; report a88cc394 PASS. Giữ nguyên FAIL để truy vết, không che lỗi hay sửa report cũ.
- Không chạy lại load S05/6A. Không sửa bất cứ report/hash code thực chạy 6A cũ; ledger 6A mô tả snapshot tại checkpoint, các hồ sơ P1 cập nhật sau đó có hash mới trong summary 6B.

## Chạy và xem

PowerShell tại thư mục dự án, dùng môi trường đã có:

```powershell
.\.venv\Scripts\Activate.ps1
python -X utf8 -m unittest discover -s tests/warehouse -p test_s06b_bridge.py -v
python -X utf8 -m etl.s06b_bridge verify --env-file .env
```

Lệnh hậu kiểm không ghi DB; chỉ lưu report tổng hợp mới vào results/warehouse. Lệnh **đã dùng** khi bridge còn rỗng: `python -X utf8 -m etl.s06b_bridge preflight --env-file .env` rồi `python -X utf8 -m etl.s06b_bridge load --env-file .env`. **Không dùng lại preflight/load sau 6B** để kiểm: guard bridge rỗng sẽ từ chối. Không xóa bridge để vượt guard. Checker 6A cũ cũng đòi bridge rỗng nên không phù hợp trạng thái mới; dùng `verify` của 6B kiểm bảo toàn dimension riêng. Script fixture `tests/warehouse/check_s06b_rollback.py --env-file .env` chỉ cho lần kiểm thử có chủ đích, không phải hậu kiểm chỉ đọc.

Code/test: `etl/s06b_bridge.py`, `tests/warehouse/test_s06b_bridge.py`, `tests/warehouse/check_s06b_rollback.py`. Bằng chứng: [summary](../../results/warehouse/s06b_summary.json) và sáu report run được index trong đó. Hồ sơ [S06](../agent/steps/P1/S06.md), STATE/DECISIONS/REVIEWS/PROMPTS P1 và hướng dẫn README/etl/database cập nhật; kế hoạch không thuộc thay đổi 6B.

## Giới hạn và nội dung cần review

Chờ điều phối review code 6B, transaction/khóa bảo vệ snapshot, cặp/hash view, bảo toàn dimension và fixture rollback. Chưa push/PR; checkpoint 6A chỉ local, không có PR 6A/6B riêng. Chưa fact6C, full refresh6D, đánh giá pipeline chạy lại, G2/adapter DW đầy đủ, BI/dashboard hoặc backup/restore.

Ý bảo vệ:

1. Phim nhiều genre cần bridge N:N; 6408 cặp không có nghĩa 6408 phim.
2. Giữ ID nguồn qua view; ánh xạ surrogate tường minh vì identity có thể nhảy sau rollback.
3. So toàn bộ cặp, số genre từng phim và hash CSV chuẩn mạnh hơn so COUNT đơn lẻ.
4. Transaction và kiểm cùng connection bảo đảm không công bố bridge dở dang khi lỗi.
5. Genre là nhãn gán nhiều lần; khi phân tích rating không cộng lượt gán genre thành tổng đánh giá duy nhất, phải dùng định nghĩa tỷ trọng đã chốt.
