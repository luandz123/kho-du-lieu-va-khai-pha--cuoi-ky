# Bàn giao 6A — nạp bốn dimension, WAITING_REVIEW

Ngày 18/10/2026, Asia/Bangkok. Điều phối chấp nhận S05 và giao riêng 6A; PR #7 đã API xác minh MERGED, merge 8de1c7b9c39a7fe7aa0ec6bc671eec1ce490f6d6. Đây là nguồn review điều phối, không tạo lời duyệt nguyên văn của người dùng. Main mới nhất còn có PR #8/P2, nên HEAD nền thực dùng **52dd682920e0587f3a474fe284b9bf5635ab6aac**, nhánh **p1-s06-etl**. Chỉ kế thừa P2, không sửa hoặc tự duyệt công việc P2.

## File và phiên bản

| File | Vai trò |
|---|---|
| [etl/s06a_dimensions.py](../../etl/s06a_dimensions.py) | Chỉ đọc staging và insert bốn dimension rỗng trong một transaction, không bootstrap/truncate/delete/upsert |
| [test_s06a_dimensions.py](../../tests/warehouse/test_s06a_dimensions.py) | 13 unit tests với dữ liệu tự tạo, gồm hồi quy thứ tự canonical và năm NULL |
| [check_s06a_rollback.py](../../tests/warehouse/check_s06a_rollback.py) | Fixture DB trong schema UUID riêng; lỗi dimension cuối rollback toàn bộ bốn bảng |
| [check_s06a_dimensions.py](../../tests/warehouse/check_s06a_dimensions.py) | Kiểm sau nạp bằng connection read-only, không gọi load/DDL |
| [s06a_summary.json](../../results/warehouse/s06a_summary.json) | Index các bằng chứng, hash code thực chạy và giới hạn |
| [S06.md](../agent/steps/P1/S06.md) | Hồ sơ 6A và các phần chưa làm |

Code thực chạy **77d3450b1c7f7e207984ec7f376a0af268ef8b83ddfb38f69e82553ab7f3d7a2**, chưa commit; HEAD nền không được coi là đã chứa code 6A. Không sửa module S05 hoặc DDL được duyệt. Giữ nguyên plan untracked và báo cáo lịch sử, raw/P2 chỉ đọc.

## Lệnh đã chạy và lệnh xem lại

Từ workspace PowerShell, dùng đúng `.venv` Python 3.12.14 đã có:

```powershell
# Lệnh nạp đã thực hiện; KHÔNG chạy lại khi dimension đang có dữ liệu.
.\.venv\Scripts\python.exe -X utf8 -m etl.s06a_dimensions --env-file .env

# Có thể kiểm lại bằng read-only, không nạp lại:
.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_s06a_dimensions.py --env-file .env

# Unit tests chỉ fixture trong bộ nhớ:
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests/warehouse -p test_s06a_dimensions.py -v

# Integration fixture tách biệt, chạy khi được giao kiểm chứng:
.\.venv\Scripts\python.exe -X utf8 tests/warehouse/check_s06a_rollback.py --env-file .env
```

Không in/đổi .env, password, URI hoặc role. Database vẫn **movielens_btl**, không bootstrap lại. Lệnh load S05 đòi DW/analytics rỗng, **không chạy sau 6A**. Lệnh 6A cũng chỉ nhận trạng thái dimension rỗng; không tự xóa/truncate để vượt guard. Chưa có pipeline full refresh tích hợp/chạy lại 6D.

## Kiểm tiền đề chỉ đọc

Marker/catalog khớp S04; ba staging đủ và so **mọi field/source_line** với raw/hash nguồn, đúng snapshot S05 run f5f11bcd. Bốn source hash/line_count còn khớp manifest. Trước nạp, cả bốn dimension, bridge, fact và ba bảng analytics đều rỗng. Bằng chứng [preflight](../../results/warehouse/s06a_preflight.json). Không dựa COUNT để bỏ qua kiểm nội dung.

## Kết quả thực sau commit

| Dimension | Dòng | Đối soát |
|---|---:|---|
| dim_user | 6040 | user_id gốc, F/M, đủ bảy nhãn tuổi, occupation nguồn; so mọi field với staging và hash v_ml_users |
| dim_movie | 3883 | movie_id/title nguyên vẹn, năm cuối bốn chữ số hoặc NULL; hash v_ml_movies khớp |
| dim_genre | 18 | Tập tên đúng manifest và chuỗi nguồn, không đổi tên; một dòng mỗi genre là grain dimension |
| dim_date | 1040 | Liên tục 2000-04-25 đến 2003-02-28 UTC, không lặp/thiếu; mọi cột year/quarter/month/day sinh tự động đều đúng |

Timestamp min/max **956703932 / 1046454590**, tương ứng **2000-04-25T23:05:32Z / 2003-02-28T17:49:50Z**. Lịch dựng bằng UTC explicit, không dùng timezone máy. Bốn dimension cùng transaction, cùng khóa advisory (20261027,1), staging được SHARE-lock để không đổi trong lúc nạp. Các bảng đích được khóa chống ghi cạnh tranh; mọi ép kiểu/NULL/miền/code set/khóa duy nhất và kiểm hash đều trước COMMIT.

Hai hash view qua serializer đã chốt, sau sort contract:

- users: `7fd7a662d8fd243983382ad87d83fa8be70dfe9f77c4a521b322ffbd585bbe6f`.
- movies: `154219ea4c70227bb993568931ee79ea788eca8c860624d3f5729b81c033245b`.

Đây chỉ là **hai view**. v_ml_movie_genres và v_ml_ratings vẫn 0 vì bridge/fact chưa nạp, không ghi G2 đạt. Bridge, fact và cả ba bảng analytics đều 0. Kiểm sau commit bằng read-only xác nhận dữ liệu thật, staging giữ nguyên, không còn schema fixture.

## Test, rollback và lỗi đã sửa

13/13 unit tests phiên bản cuối PASS. Fixture DB dùng cùng hash loader, kiểm bảy mapping tuổi, title é/comma/quote, năm NULL, sát ngày/năm UTC trong session Asia/Bangkok, cột lịch generated. Cố ý lặp full_date tại bảng cuối gây SQLSTATE 23505 sau khi users/movies/genre đã insert; cả bốn bảng fixture rollback về 0. Sau đó nạp fixture hợp lệ và so toàn bộ trường; production/staging không đổi, schema thử dọn bằng DROP tường minh không CASCADE.

Lần nạp production đầu ab42f286 (code c231e8c5) bị chặn ở hash: caller đọc view thiếu sort, trong khi serializer không tự sort và view không đảm bảo thứ tự. Transaction đã rollback cả bốn dimension; thao tác đọc xác nhận cả chín bảng vẫn 0. Không truncate/reset hoặc sửa nguồn/hash kỳ vọng. Đã sửa P1 caller ORDER BY + sắp frame theo contract, thêm regression test byte CSV gồm NULL/Unicode/quote; giữ DDL và code P2. Unit/fixture chạy lại bằng cùng code cuối 77d3450b trước nạp thành công run **3b6f0cda57a5454ba52bc8674c18b953**, 4.625 giây. Giữ nguyên report FAIL và bằng chứng phiên bản đầu.

Rollback có thể làm sequence surrogate nhảy số; không tự reset để làm đẹp và không giả surrogate bằng ID nguồn. Hai hash logical view chứng minh ID nguồn vẫn giữ đúng. Tham chiếu bridge ở bước sau phải lookup key, không dùng trực tiếp movie_id làm movie_key.

## Giới hạn, duyệt và năm ý bảo vệ

**6A WAITING_REVIEW**. Chưa bridge 6B, fact 6C, full refresh 6D, G2 đủ bốn view, OLAP/dashboard, quyền BI hoặc backup restore. Chưa chứng minh full pipeline chạy lại được. Không commit/push/PR trong lượt này; các báo cáo chỉ thống kê, hash và fixture, không dữ liệu cá nhân thật. Cần điều phối review code, tiền đề, hai hash view, code sets/genre/lịch và rollback trước giao bước tiếp.

1. ID MovieLens giữ ở cột nghiệp vụ và view; surrogate chỉ là liên kết nội bộ, không cần liên tiếp sau rollback.
2. Tuổi là nhãn lịch sử đúng mapping; không suy cùng người đổi sở thích theo tuổi.
3. Năm thiếu là NULL có nghĩa, giữ title nguyên vẹn và serialize số nguyên không .0.
4. UTC explicit và lịch liên tục bảo vệ tổng hợp theo ngày/quý khỏi lệch timezone.
5. Một transaction + kiểm trước commit bảo vệ bốn dimension khỏi nạp dở; hai view đúng chưa đồng nghĩa G2 hoàn thành.
