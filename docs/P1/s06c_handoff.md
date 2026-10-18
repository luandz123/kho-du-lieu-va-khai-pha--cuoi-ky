# Bàn giao 6C — nạp fact_rating

18/10/2026, Asia/Bangkok. **6C WAITING_REVIEW**. Điều phối chấp nhận 6B sau review code, chạy lại 15/15 unit test và kiểm bằng chứng/hash theo thông báo điều phối; không ghi thành lời duyệt nguyên văn do agent tạo. Chỉ 6C được triển khai, chưa 6D hoặc xuất gói G2.

## Mốc, đầu vào và tiền đề

Giữ nhánh `p1-s06-etl`. Đã rà diff, từng đường dẫn P1, hash artifact và chữ ký secret, stage đúng 19 file 6B rồi tạo checkpoint **d698d8eab4bd8fbf828ffa23e434ddf52ba9eebe**, trên checkpoint 6A cfed2c8. Checkpoint chỉ cục bộ; không push/PR/fetch/merge/reset/stash/chuyển nhánh. Giữ nguyên report PASS/FAIL cũ và kế hoạch ngoài phạm vi untracked. Code 6C còn working tree, không gán nó cho checkpoint 6B.

Đã đọc STATE/S06, S04/S05, schema/mapping/refresh, contract v2, manifest và đoạn 6C trong Word Người 1. Dữ liệu đầu vào là `staging.ratings_raw`, nguồn độc lập cục bộ `data/raw/p1_s05/ml-1m` và dimension/bridge đã kiểm nhận. Không sửa file P2, nguồn, manifest, DDL hoặc code S05/6A/6B.

Preflight chỉ đọc **c0c750144d8a420ab25fefcab3b5433e** PASS: đúng movielens_btl/marker/catalog, bốn byte hash/count nguồn; từng field/source_line staging khớp snapshot S05 f5f11bcd; 6040/3883/18/1040 dimension và mọi surrogate khớp fingerprints 6B. Bridge 6408 cặp khớp nguồn/hash; fact/view ratings/ba analytics rỗng. Không gọi lại loader cũ hoặc xóa dữ liệu để vượt guard.

## Cách thực hiện

`etl/s06c_fact.py` đọc staging theo lô, parse ID/rating/int64 nghiêm ngặt; rating thuộc 1..5, phát hiện trùng user–movie xuyên các lô. Tra user_id→user_key, movie_id→movie_key, ngày UTC→date_key từ ánh xạ đã kiểm duy nhất; thiếu mapping thì dừng, không inner join để bỏ khóa lỗi. Instant có timezone UTC được tính từ Unix giây, không dùng timezone máy. Chỉ insert user_key/movie_key/date_key/rating/rating_timestamp/rated_at; rated_date do PostgreSQL sinh theo UTC.

Một transaction, advisory lock (20261027,1), SHARE-lock ba staging và SHARE ROW EXCLUSIVE-lock các target trong suốt kiểm/nạp. Bridge/genre không tham gia luồng insert fact. Không UPSERT/deduplicate/bỏ dòng; target fact phải rỗng. Không ghi staging/dimension/bridge/analytics, không bootstrap/TRUNCATE/DELETE hoặc đổi DDL production.

Trước COMMIT, cùng connection kiểm PK/UNIQUE/FK/rating/epoch/ngày UTC; LEFT JOIN kiểm orphan không làm rơi dòng. So **mọi trường logic của view với staging đã khớp nguồn**, theo user_id,movie_id,timestamp,rating, đồng thời đối chiếu count, tổng điểm, phân bố sao, user/phim có rating và biên UTC. Serializer G1 đã review chạy theo chunk có đúng một header CSV, UTF-8/LF; test hồi quy chứng minh byte hash bằng serialize nguyên bảng. So hash cả bốn view và mọi trường dimension/surrogate, cặp bridge vật lý, staging/nguồn trước và sau. Chỉ công bố COMMITTED khi transaction thành công.

## Kết quả thực tế

Run **bba59cc0f59b45b0897144a5268e111f**, bắt đầu **2026-10-18T12:52:33.606883+00:00**, **149.016 giây**, PASS/COMMITTED. Loader SHA-256 **18ce72f9f9a53a3dae078f2174a5014368dd4a5d7c88de82e2b698e6378ba5e1**. Preflight, unit, fixture, load và hậu kiểm dùng cùng loader; không sửa loader giữa các lần này. Bằng chứng giữ hash helper S05/6A/6B riêng và commit nền d698d8e.

| Chỉ tiêu | Kết quả nguồn và DW khớp |
|---|---|
| fact_rating / v_ml_ratings | **1000209 / 1000209** |
| Tổng điểm rating | **3582313** |
| Rating 1 / 2 / 3 / 4 / 5 | **56174 / 107557 / 261197 / 348971 / 226310** |
| User / phim có rating | **6040 / 3706** |
| Cặp user–movie trùng / FK mồ côi / rating sai miền | **0 / 0 / 0** |
| Sai epoch, rated_at hoặc ngày UTC | **0** |
| Min / max Unix giây | **956703932 / 1046454590** |
| Min / max rated_at UTC | **2000-04-25T23:05:32Z / 2003-02-28T17:49:50Z** |

| View | Canonical SHA-256 khớp contract/manifest |
|---|---|
| users | `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f` |
| movies | `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b` |
| movie_genres | `9a6b012d0df0929ddd2eac199f2419fc0c36d2b64a1c0317302067470e379dbf` |
| ratings | `06860cbf2d36881c8eae37db14b5a32cfbfdfd2c384258603e720143291407cf` |

Đây là **đối soát sau 6C**, chưa nghiệm thu pipeline full refresh hoặc G2. Staging giữ nguyên snapshot S05; mọi trường/surrogate của bốn dimension và toàn bridge giữ nguyên. Ba bảng analytics vẫn **0**, không có phiên bản cụm được nạp. Có 3883 phim trong dimension và 3706 phim có rating, không làm mất phim chưa được đánh giá.

## Kiểm thử và hậu kiểm

**17/17 unit test** PASS, report 39e473d3dbf7404d9c271d0e511748a5: missing user/movie/date, mapping không duy nhất, rating/ID/int64 sai miền, cặp trùng, ánh xạ surrogate khác ID nguồn, UTC hai phía nửa đêm/epoch âm, không nhân rating theo genre, canonical chunk/empty header và namespace.

Fixture PostgreSQL **db3ea77cfc7d4daebc471e8aa2354c16** PASS trong schema `s06c_test_<UUID>` tự tạo. Mỗi ca đã insert **1000** rating thử trước khi gây lỗi, rollback về **0**: thiếu user/movie/date mapping, rating sai miền, cặp trùng, SQL CHECK23514 và UNIQUE23505. Dùng đúng hàm insert theo lô của loader; không chỉ giả lập exception trước khi ghi.

Fixture hợp lệ dùng session timezone **Asia/Bangkok**: UTC 1999-12-31 và 2000-01-01 mỗi ngày 500 rating, epoch/rated_at/rated_date/date_key đúng; một phim hai genre vẫn đúng 1000 rating, dimension movie vẫn 1 dòng. Schema thử được dọn đúng tên, không CASCADE; production trước/sau không đổi. Toàn bộ fixture là dữ liệu tự tạo.

Hậu kiểm bằng `tests/warehouse/check_warehouse.py` cố định action verify, transaction **READ ONLY / REPEATABLE READ**, kiểm lại mọi trường/hashes/tổng hợp và bảo toàn so baseline load thành công. Run **0dd850a11b604999ae9ff1f87d3cd317** **PASS**, được index trong [summary](../../results/warehouse/s06c_summary.json). Không dùng lại checker 6B đòi fact rỗng, không sửa checker/bằng chứng cũ để che trạng thái mới. Các report 6C hiện không có FAIL; report PASS/FAIL 6A/6B vẫn giữ nguyên byte. Ledger cũ là snapshot tại checkpoint tương ứng; hồ sơ P1 cập nhật nay có hash mới trong summary 6C.

## Chạy và xem

PowerShell tại thư mục dự án:

```powershell
.\.venv\Scripts\Activate.ps1
python -X utf8 -m unittest discover -s tests/warehouse -p test_s06c_fact.py -v
python -X utf8 tests/warehouse/check_warehouse.py --env-file .env
```

Checker chỉ đọc database và ghi report tổng hợp mới, không có action load/refresh. Cũng có thể dùng `python -X utf8 -m etl.s06c_fact verify --env-file .env`. `.env` chỉ đọc cục bộ, không gửi mật khẩu/URI vào chat hoặc Git.

Lệnh **đã dùng** khi fact còn rỗng: `python -X utf8 -m etl.s06c_fact preflight --env-file .env`, sau đó `python -X utf8 -m etl.s06c_fact load --env-file .env`. **Không chạy lại load S05/6A/6B/6C hoặc checker 6B nguyên trạng** trên dữ liệu hiện tại. Không xóa bảng để vượt guard. Script fixture `tests/warehouse/check_s06c_rollback.py --env-file .env` dành cho kiểm có chủ đích, không phải hậu kiểm chỉ đọc.

Code/test mới: `etl/s06c_fact.py`, `tests/warehouse/test_s06c_fact.py`, `tests/warehouse/check_s06c_rollback.py`, `tests/warehouse/check_warehouse.py`. Bằng chứng tổng hợp: `results/warehouse/s06c_summary.json` và năm report preflight/unit/fixture/load/verify. Hướng dẫn README/etl/database và hồ sơ S06/STATE/DECISIONS/REVIEWS/PROMPTS P1 được cập nhật; danh sách/hash file trong summary. Kế hoạch ngoài phạm vi không được stage/sửa.

## Giới hạn, cần review và ý bảo vệ

Chờ review riêng 6C: mapping/grain/UTC, transaction/bảo vệ snapshot, toàn trường/bốn hash/tổng hợp, fixture rollback và hậu kiểm. Chưa commit phần 6C/push/PR; checkpoint 6B chỉ local. Chưa tích hợp full refresh6D, chạy lại toàn pipeline, xuất gói/kiểm nhận adapter DW G2 đầy đủ, OLAP/dashboard, nạp cụm, quyền BI hoặc backup/restore. Không tự chuyển bước sau khi bàn giao.

1. Grain là một đánh giá nguồn, không phải lượt xem; UNIQUE user–movie dựa trên EDA đã xác minh.
2. ID nguồn dùng ở view; surrogate chỉ nội bộ và phải tra mapping, không giả hai loại ID bằng nhau.
3. Unix giây, instant và ngày UTC phải đồng nhất để tổng hợp theo quý không lệch do timezone.
4. Không join genre vào luồng fact: một phim nhiều thể loại vẫn chỉ một dòng cho mỗi đánh giá nguồn.
5. So từng trường và hash cùng tổng hợp trong transaction giúp phát hiện sai mà COUNT đơn lẻ bỏ sót; rollback giữ atomicity tiểu bước, chưa chứng minh full refresh6D.
