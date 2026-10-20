# Bàn giao 11A — Dashboard Tổng quan

## Quan sát sau công bố — PR14 đã MERGED bên ngoài agent

API xác minh PR14 CLOSED/MERGED lúc **2026-10-19T15:27:06Z**, actor **hungvu205**, merge/main **5a42c73c39c00780b2d5442c45662d93bdf0f23b**. Agent không thực hiện merge. HEAD được merge/công bố **ef82fc4041a1393e942bd533f4e41c17283d0d4c**, base **988874d7b5897a5615acfebdf571c6d55861ddc2**; đủ50file/blob khớp Git của HEAD này. Code tái tạo **5915702d414f0385208b696329a2aed215db8762**. Các mục OPEN phía dưới là trạng thái đã quan sát trước đó, không phải hiện hành.

Phát hiện khi chuẩn bị commit hồ sơ ghi URLPR; guardPR-open dừng trước stage/commit. Không có commit hoặc push tài liệu sau khi PR merge. **Các cập nhật trạng thái đang sửa local chưa thuộc PR đã merge/main**, thêm quan sát docs/P1/overview_post_merge_observation.json. Đã dừng thao tác ghiGitHub, không mở PR bổ sung hoặc tự chuyển11C/11B. Cần điều phối giao riêng cách nhận các hồ sơ local này.

Giữ code/SQL/metric/filter, ảnh/PASS-FAIL/runhash nguyên vẹn. 11A đã được điều phối chấp nhận chức năng; merge quan sát quaAPI không phải lệnh làm bước mới. Dashboard8089 và hai container running/healthy/exit0, health200 ở lần kiểm công bố; nguyênnhânexit255 cũ chưa xácđịnh. PUBLIC TEMP/chưarestore/P2/hai máy/fullrefreshS07 giữ nguyên; chưarerunETL/3khoảng/create/G3/quyềnfirewall.

---

## Hiện hành — PR11A OPEN, WAITING_REVIEW

Đã push p1-s11a-overview và mở [PR #14](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/14) vào main. API xác minh OPEN/merged=false, HEAD lúc mở/kiểm `ef82fc4041a1393e942bd533f4e41c17283d0d4c`, base `988874d7b5897a5615acfebdf571c6d55861ddc2`. Đủ50file/blob remote khớp Git; khôngsecret/ZIP/userdata/kếhoạch ngoài phạmvi. **11A APPROVED chức năng theo điều phối; PR WAITING_REVIEW, chưa MERGED**. Agent không merge.

Code công bố tái tạo5915702d414f0385208b696329a2aed215db8762; runtimebase988874d/runa614b26f/hash thực chạy giữ nguyên. Commit tài liệu sau mục này chỉ bổ sung trạng thái/hash, HEAD chứa chính ledger kiểm riêng bằng Git/API ở bàn giao cuối. Cấu hình SQL/metric/filter/ảnh/PASS-FAIL lịch sử không đổi. KhôngrerunETL/đốisoát3khoảng/create_overview hoặc11C/11B/G3/quyềnfirewall. Giữ PUBLIC TEMP/chưarestore/P2/hai máy/fullrefreshS07. Dashboard http://127.0.0.1:8089/superset/dashboard/1/ ; quan sát mới hai container running/healthy exit0, health200/APIđạt, nguyênnhândừng255 chưa xácđịnh. Các mục chuẩn bị/chưa mở bên dưới là lịch sử.

---

## Hiện hành — 11A đã được điều phối chấp nhận chức năng; chuẩn bị PR

Ngày 19/10/2026, điều phối thông báo chấp nhận sau khi kiểm hồ sơ, hash artifact và cấu hình thực lưu trên Superset; giao commit/push/mở PR p1-s11a-overview vào main. Đây là review của điều phối, không phải lời duyệt nguyên văn do agent tạo. APPROVED chức năng khác với PR review/MERGED; chưa merge và chưa11C/11B.

Điều phối báo hai container đã dừng mã255, được điều phối khởi động lại và kiểm API thành công. Quan sát mới riêng tại dashboard/overview/evidence/publication_observation.json: web/metadata running/healthy, exit0; health200, API đăng nhập thành công,21 đối chiếu cấu hình thực khớp SQL/metric/filter đã review. Không suy đoán nguyên nhân dừng; agent không start/restart trong lượt công bố này. Không chạy ETL/đối soát3khoảng/create_overview.py hoặc thay cấu hình chức năng vì cập nhật hồ sơ.

Giữ mọi report PASS/FAIL, run_id/hash thực chạy và ledger bàn giao45artifact lịch sử. Hash tài liệu mới được ghi ở docs/P1/overview_publication.json riêng. PUBLIC TEMP còn; chưa import/restoreZIP, P2 intake/kết nối hai máy hoặc fullrefreshhelperS07. ZIP và credential tiếp tục localignored. Kế hoạch ngoài phạm vi giữ nguyên. Commitcode/URLPR chỉ ghi sau xác minh; các trạng thái WAITING_REVIEW bàn giao/chưa được giao công bố bên dưới là lịch sử.

---

**WAITING_REVIEW**, ngày 19/10/2026. Dashboard thật: http://127.0.0.1:8089/superset/dashboard/1/ ; slug `movielens-overview`. Superset 6.1.0 của dự án tại 8089, metadata riêng; không phải instance 8088. Chỉ làm 11A.

## Đối tượng và môi trường thực tế

| Đối tượng | Tên | ID |
|---|---|---:|
| Database | MovieLens BTL - BI reader | 1 |
| Dataset rating | P1_11A_ratings | 1 |
| Dataset danh mục | P1_11A_catalog | 2 |
| Dashboard | MovieLens 1M · Tổng quan | 1 |
| Chart | Tổng số đánh giá | 1 |
| Chart | Điểm trung bình · SUM/COUNT | 2 |
| Chart | User có đánh giá | 3 |
| Chart | Phim có đánh giá | 4 |
| Chart | Phim danh mục · cố định mọi thời kỳ | 5 |
| Chart | Tổng điểm đánh giá | 6 |
| Chart | Top 10 phim · số đánh giá, điểm TB, ID | 7 |
| Chart | Phân bố số đánh giá theo mức sao | 8 |

Chart có tiền tố `P1 11A ·`; tên đầy đủ trong evidence/final_verification.json. Instance web/metadata healthy, health/login 200, đã đăng nhập UI và REST bằng tài khoản admin cục bộ hiện có. Quyền tạo database/dataset/chart/dashboard đã chứng minh bằng tạo đối tượng thật. Driver trong container 2.9.13, PostgreSQL Windows 17.11. Chỉ start hai container dự án đang dừng, không recreate/init/reset volume hoặc tác động instance khác. Mọi cấu hình Superset qua API chính thức, không ghi trực tiếp database metadata.

## SQL, grain và metric

`dashboard/overview/ratings_dataset.sql` giữ một dòng cho một user–movie nguồn. Join movies theo ID duy nhất, không join bridge genre. Chuỗi UTC-Z `rated_at` của contract được cast `timestamptz AT TIME ZONE 'UTC'` thành timestamp có kiểu `rated_at_utc`; Superset nhận DATETIME/is_dttm=true. Truy vấn qua engine Superset thật trả role `movielens_bi_reader` và TimeZone `UTC`. Không đổi bảng, DDL hoặc bốn view contract.

Metric trong metrics.json:

- Rating count: `SUM(rating_count)`; mỗi dòng nguồn có rating_count=1.
- Tổng điểm: `SUM(rating_sum)`; mỗi dòng rating_sum=rating.
- Mean: `SUM(rating_sum)::numeric/NULLIF(SUM(rating_count),0)`.
- User/phim có rating: COUNT DISTINCT ID nguồn trong lát thời gian.
- Phim danh mục: dataset riêng không có thời gian, cố định 3.883.

Không lấy trung bình các mean nhóm. Top 10 phá hòa count DESC, mean DESC, movie_id ASC. Builder table Superset dùng một sort metric ở chế độ aggregate; vì vậy dùng:

```sql
ROW(SUM(rating_count),
    SUM(rating_sum)::numeric/NULLIF(SUM(rating_count),0),
    -MIN(movie_id)) DESC
```

Đây là sắp xếp bộ ba từ trái sang phải, không trộn chỉ số bằng hằng số. Sort metric chỉ vào ORDER BY, không xuất như chỉ số kinh doanh. Fixture VALUES tự tạo đã kiểm thứ tự [2,3,9,1] khi count/mean/ID hòa từng cấp. [Builder chính thức Superset 6.1](https://raw.githubusercontent.com/apache/superset/6.1.0/superset-frontend/plugins/plugin-chart-table/src/buildQuery.ts).

## Native filter

`NATIVE_FILTER-UTC-RATED`, tên “Thời điểm đánh giá (UTC)”, áp dụng toàn dashboard **trừ chart 5**. Start inclusive, end exclusive; mặc định No filter. SQL sinh thực đặt WHERE rated_at_utc trước GROUP BY, ORDER BY và LIMIT 10; không lọc view tổng hợp toàn lịch sử sau khi đã chọn Top 10.

Mở filter → Range type Advanced → nhập Start/End → APPLY trong dialog → Apply filters trên dashboard. Clear all để về toàn lịch sử. Chart danh mục ghi rõ không chịu bộ lọc thời gian và giữ 3.883 trong cả ba trường hợp. Warning tại Top 10 đã kiểm trên UI: chạm row limit 10 chủ đích, không phải lỗi SQL.

## Đối soát độc lập

Run `a614b26f902842618b39a35c799d0a77`, 40.219 giây, cả ba trường hợp PASS. Code SHA thực chạy trong evidence/reconciliation.json; base commit `988874d7b5897a5615acfebdf571c6d55861ddc2`, code 11A chưa commit. SQL tham khảo trong reconciliation.sql; SQL thực chạy và tham số trong reconcile.py/report. So KPI, mean, cả năm mức sao và thứ tự cả mười phim.

| Khoảng UTC [start,end) | Rating | Tổng điểm | User có rating | Phim có rating | Mean | Danh mục |
|---|---:|---:|---:|---:|---:|---:|
| Toàn lịch sử | 1000209 | 3582313 | 6040 | 3706 | 3.581564 | 3883 |
| 2000-07-01 → 2000-10-01 | 324864 | 1167669 | 2244 | 3465 | 3.594332 | 3883 |
| 2001-01-01 → 2001-04-01 | 32223 | 114158 | 781 | 2996 | 3.542749 | 3883 |

| Khoảng | Sao 1 | Sao 2 | Sao 3 | Sao 4 | Sao 5 |
|---|---:|---:|---:|---:|---:|
| Toàn lịch sử | 56174 | 107557 | 261197 | 348971 | 226310 |
| Q3/2000 | 17823 | 33819 | 85526 | 112850 | 74846 |
| Q1/2001 | 1523 | 3658 | 9027 | 11837 | 6178 |

Top 1 toàn lịch sử: American Beauty, 3428; Q3/2000: American Beauty, 1102; Q1/2001: Gladiator, 146. Sự thay đổi phim đứng đầu chứng minh không lấy Top 10 toàn lịch sử rồi mới lọc. Final verification kiểm độc lập count dim_movie, phân bố sao chuẩn, user–movie trùng=0 và analytics vẫn [0,0,0].

Ảnh UI thật từ công cụ trả JPEG, giữ nguyên byte và dùng đuôi .jpg. Trong dashboard/overview/evidence/: all_history_viewport.jpg / all_history_charts.jpg; 2000_q3_viewport.jpg / 2000_q3_charts.jpg; 2001_q1_viewport.jpg / 2001_q1_charts.jpg / 2001_q1_filter.jpg. AX snapshots ghi khoảng/KPI/Top10, không chứa lịch sử user. Đã kiểm desktop 1280×900 và reset viewport sau kiểm. Panel rất hẹp làm card co, chưa tối ưu mobile. Ảnh thử hẹp/toàn trang bị thiếu nội dung giữ cục bộ ở tmp/s11a_capture_attempts bị ignore; không dùng làm bằng chứng đạt.

## Quyền BI và bí mật

Role `movielens_bi_reader` ban đầu không tồn tại; đã tạo login mới, mật khẩu ngẫu nhiên mạnh trong `dashboard/superset/.env.bi`, Git ignored, không in/hash. Chỉ cấp CONNECT database dự án, USAGE dw và SELECT dw.v_ml_ratings / dw.v_ml_movies. Không đổi password role có sẵn, membership, quyền quản trị/ghi hoặc quyền sở hữu. Database Superset không cho DML/CTAS/CVAS/upload và không expose SQLLab.

bi_reader.json / bi_reader_final.json xác minh từ container Superset, **session_read_only=off** vẫn SELECT được nhưng UPDATE fact WHERE false bị SQLSTATE 42501. Thuộc tính superuser/createdb/createrole/replication/bypassrls/inherit=false, membership=0. Kiểm 24 relation dự án: chỉ hai view SELECT, không relation có INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER. CREATE trên database và dw/staging/analytics/public=false. Không sở hữu relation hoặc có quyền mutate sequence dự án. Final verification chứng minh chính engine Superset chạy bằng role BI, không phải tài khoản quản trị.

**Giới hạn:** PUBLIC TEMP mặc định vẫn true; không thu hồi quyền PUBLIC của người khác. Role có thể tạo đối tượng tạm của session, không ghi được bảng/view hoặc tạo đối tượng bền vững trong schema dự án. Kết luận chỉ đọc giới hạn ở dữ liệu dự án movielens_btl, không tuyên bố khóa toàn server. Không đổi firewall/pg_hba/listen_address.

Đây là BI tại P1, không phải P2 nhận G2 hoặc kết nối hai máy. P2 intake NOT_CONFIRMED; report/manifest G2 cũ giữ false lịch sử, không sửa thành bằng chứng P2 access.

## Cách mở, kiểm lại và export

Đăng nhập Superset bằng tài khoản hiện có; mật khẩu ở cấu hình cục bộ, không gửi chat. Từ gốc workspace:

```powershell
.\.venv\Scripts\python.exe dashboard/overview/check_bi_reader.py
.\.venv\Scripts\python.exe dashboard/overview/reconcile.py
.\.venv\Scripts\python.exe dashboard/overview/verify_overview.py
```

Checker không refresh ETL hoặc tạo dữ liệu. Không chạy lại create_overview.py trên instance hiện có: script có guard dashboard đã tồn tại. Script cần database/dataset đã đăng ký và mapping object_ids.json, chưa là bootstrap máy sạch hoàn chỉnh.

Export thật bằng GET /api/v1/dashboard/export/?q=!(1), file `dashboard/overview/export/overview_superset.zip` cục bộ/Git ignored. Đã mở ZIP và scan bí mật thật trong bộ nhớ: không có bí mật, URI database dùng password mask; đủ 8 chart/2 dataset/1 dashboard. Hash/thành viên ở evidence/export_check.json. Không tạo ZIP thủ công. **Import/restore chưa kiểm**; cần cung cấp credential BI tại máy đích.

Giữ hai FAIL checker đã sửa: reconcile_failure.json (kiểm vị trí GROUP BY bắt nhầm comment SQL, sửa bỏ comment khi kiểm) và verification_failure.json (planner gọi has_sequence_privilege với nonsequence, sửa CASE). Đều chỉ đọc, không thay dữ liệu; lần chạy sửa PASS. Không xóa bằng chứng hoặc gọi chúng là lỗi dashboard.

Chưa bootstrap/full refresh/cài lại S07, chưa 11B/11C/G3, chưa kiểm full refresh helper S07, tải đồng thời hoặc máy bảo vệ. Rubric chưa xác minh thêm. Published trong Superset không có nghĩa điều phối đã duyệt 11A.

## Ý bảo vệ và nội dung cần duyệt

1. Grain một đánh giá và movie join 1:1 giữ đúng tổng, không qua bridge genre.
2. Mean SUM/COUNT; danh mục tách khỏi phim có rating và khỏi time filter.
3. UTC có kiểu và filter trước aggregate/Top10; ba khoảng có kết quả khác nhau.
4. SQL độc lập khớp UI/API; tài khoản BI bị từ chối ghi dù session không READ ONLY.
5. Metadata tách DW; bí mật cục bộ; export thật đã scan, chưa tuyên bố restore đạt.

Cần điều phối review dashboard thật, phạm vi filter, metric và quyền BI. **11A WAITING_REVIEW**, chưa commit/push/PR, không tự chuyển 11B/11C.
