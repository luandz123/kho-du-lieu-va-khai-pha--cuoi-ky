# Kết quả OLAP S07 — WAITING_REVIEW

## Cập nhật công bố, 19/10/2026

Điều phối đã chấp nhận kết quả S07 sau review SQL/code,73unit/37artifact vàQ3. Số liệu, SQL/code và report thực chạy phía dưới không đổi. Đang thực hiện công bố PR theo lệnh riêng, chưamerge/dashboard. Mục WAITING_REVIEW trong tiêu đề và bàn giao ban đầu phía dưới là lịch sử trước chấp nhận; trạng thái PR/codecommit/URL mới xem docs/P1/s07_publication.md tính từ repository. Không chạy lại OLAP/ETL/installview để cập nhật hồ sơ; giữ giới hạn fullrefreshhelper/account/P2intake.

---

Nguồn chính: PostgreSQL `movielens_btl`, snapshot G2 run `6501a547065246869b98b6ab6531190e`. Run OLAP `af6dbc20b40d4a47aa3ea71bde6fd107`, UTC 2026-10-18T15:43:00.452371+00:00, 7.016 giây. Code chưa commit; base `59ed6eddae4981b2c90e8ec8b1cad036270baf9c`; SHA từng file trong report. Không gán commit công bố ETL cho lần chạy OLAP.

## Định nghĩa và kết quả O1–O6

| Truy vấn | Grain, metric và bộ lọc đã chạy | Kết quả |
|---|---|---|
| O1 | Toàn snapshot; count rating duy nhất từ fact, SUM/COUNT | 6040 user và 3883 phim danh mục; 6040 user / 3706 phim có rating; 1000209 rating; tổng 3582313; mean 3.5815644530293169 |
| O2 | Một phim đã được đánh giá; count giảm, mean giảm, movie_id tăng khi hòa | 10 phim; đứng đầu American Beauty (1999), 3428 đánh giá, mean 4.317386 |
| O3 | Genre × nhóm tuổi, slice F; thêm bản mọi giới và dice F + tuổi 18–24 + Comedy/Drama | 126 ô/bản đầy đủ; Comedy dice 19136, mean 3.423965; Drama dice 15977, mean 3.631157; pivot F 18 hàng × 7 nhóm tuổi |
| O4 | Năm → quý → tháng UTC; từng cấp SUM/COUNT, không cộng các cấp với nhau | 51 hàng = 4 năm + 12 quý + 35 tháng; mỗi cấp độc lập tổng 1000209 / 3582313 |
| O5 | Genre × quý UTC; mọi giới/tuổi/genre; lưới đầy đủ và LAG sau điền 0 | 18 × 12 = 216 hàng; 156 hàng đủ điều kiện xếp hạng trong 9 quý; chi tiết bên dưới |
| O6 | Tháng × phim; Comedy, tuổi 18–24, mọi giới, [2000-07-01, 2001-01-01) | 5032 hàng tổng hợp; 53541 đánh giá, tổng 185726; khớp truy vấn fact độc lập |

Danh sách Top 10 đầy đủ:

| ID | Phim | Số đánh giá | Mean |
|---|---|---:|---:|
| 2858 | American Beauty (1999) | 3428 | 4.317386 |
| 260 | Star Wars: Episode IV - A New Hope (1977) | 2991 | 4.453694 |
| 1196 | Star Wars: Episode V - The Empire Strikes Back (1980) | 2990 | 4.292977 |
| 1210 | Star Wars: Episode VI - Return of the Jedi (1983) | 2883 | 4.022893 |
| 480 | Jurassic Park (1993) | 2672 | 3.763847 |
| 2028 | Saving Private Ryan (1998) | 2653 | 4.337354 |
| 589 | Terminator 2: Judgment Day (1991) | 2649 | 4.058513 |
| 2571 | Matrix, The (1999) | 2590 | 4.315830 |
| 1270 | Back to the Future (1985) | 2583 | 3.990321 |
| 593 | Silence of the Lambs, The (1991) | 2578 | 4.351823 |

## Q3: so sánh genre theo quý trong thời kỳ nguồn

Timestamp là thời điểm đánh giá. Nguồn quan sát 2000-04-25T23:05:32Z đến 2003-02-28T17:49:50Z. Q2/2000 và Q1/2003 là quý biên thiếu quan sát; không dùng chúng hoặc cặp quý có quý trước là biên để xếp hạng giữa các quý đầy đủ. Quý nội bộ có đủ biên lịch trong nguồn; điều này không chứng minh việc thu thập bao phủ toàn bộ thị trường.

QoQ = 100 × (n_t − n_prev)/n_prev. Quý trước 0 hoặc chưa có trả NULL/N/A. Ngưỡng cố định trước khi xem kết quả: n_prev ≥ 100 đánh giá thuộc genre. Xếp hạng QoQ giảm, n_t giảm, tên genre tăng. Không đổi ngưỡng sau quan sát. Các hàng không đủ điều kiện vẫn hiển thị count/share và QoQ mô tả nếu mẫu số khác 0, nhưng growth_rank là NULL.

Tỷ trọng = số lượt gắn genre / tổng lượt gắn tất cả genre cùng quý × 100. Một đánh giá phim Comedy|Drama góp 1 vào mỗi genre, vì thế không cộng count genre để lấy tổng rating hệ thống. O5 hiện không slice genre/tuổi/giới; nếu mở rộng bộ lọc sau này, tử và mẫu phải cùng kỳ và cùng bộ lọc. O6 chọn nhiều genre theo hợp (EXISTS), mỗi rating chỉ tính một lần.

| Quý | Genre hạng 1 đủ điều kiện | n_prev | n_t | QoQ % | Tỷ trọng % |
|---|---|---:|---:|---:|---:|
| 2000 Q4 | Animation | 13102 | 20068 | 53.17 | 2.12 |
| 2001 Q1 | Animation | 20068 | 1715 | -91.45 | 2.71 |
| 2001 Q2 | Comedy | 11975 | 5812 | -51.47 | 19.92 |
| 2001 Q3 | Western | 179 | 189 | 5.59 | 0.78 |
| 2001 Q4 | Film-Noir | 159 | 151 | -5.03 | 0.93 |
| 2002 Q1 | Horror | 514 | 697 | 35.60 | 4.39 |
| 2002 Q2 | Musical | 306 | 268 | -12.42 | 2.20 |
| 2002 Q3 | Thriller | 1007 | 1004 | -0.30 | 9.76 |
| 2002 Q4 | Romance | 733 | 711 | -3.00 | 8.88 |

Ví dụ tăng dương đủ điều kiện: Animation Q4/2000 từ 13102 lên 20068 (+53.17%); Western Q3/2001 từ 179 lên 189 (+5.59%); Horror Q1/2002 từ 514 lên 697 (+35.60%). Hạng 1 các quý còn lại trong bảng là giảm ít nhất trong tập đủ điều kiện, không phải tăng dương. Không suy rằng một thể loại dẫn đầu bền vững hoặc nhu cầu hiện tại tăng.

O4 ghi tổng hệ thống Q3/2000 = 324864, Q4/2000 = 446574, Q1/2001 = 32223. Sự thay đổi phản ánh số đánh giá trong tập lịch sử; không phải lượt xem, doanh thu hoặc nhu cầu hiện tại. Tỷ trọng thay đổi còn chịu ảnh hưởng cơ cấu phim nhiều thể loại và hoạt động đóng góp dữ liệu.

## Thao tác OLAP bằng ví dụ đã chạy

- Roll-up: cộng count/sum theo tháng thành quý, quý thành năm trong O4; mean luôn SUM(score)/SUM(count). Mỗi cấp đã đối soát về tổng fact.
- Drill-down: từ năm 2000 vào quý/tháng trong O4; O6 đi tiếp tới tháng/phim trong lát Comedy + tuổi 18–24.
- Slice: O3 cố định giới F; không suy cơ cấu giới dân số từ mẫu MovieLens.
- Dice: O3 chọn F, tuổi 18–24 và hai genre Comedy/Drama; O6 kết hợp genre/tuổi/thời kỳ với khoảng ngày nửa mở.
- Pivot: O3_pivot_F.csv đổi nhóm tuổi thành cột, genre thành hàng; mỗi ô giữ count và mean, không lấy trung bình đơn giản các mean ô.

## Kiểm chứng, lỗi và giới hạn

73/73 unit test đạt (bao gồm hồi quy ETL và 8 test S07). Fixture PostgreSQL tự tạo kiểm phim nhiều genre, hai nhóm count 202/1 để phát hiện mean sai, quý trống, quý trước 0, ngưỡng 100, quý biên, bộ lọc kết hợp và bảo toàn production. Schema fixture được rollback, không còn đối tượng thử. Sáu view analytics đã COMMITTED; bốn view contract và bảng nghiệp vụ không đổi. Các truy vấn báo cáo chạy trong session READ ONLY; dedicated_read_only_account_verified=false, P2 intake NOT_CONFIRMED.

Lần xuất đầu thất bại do Decimal không serialize JSON. Giữ observation FAIL và CSV cục bộ; đã sửa exporter riêng OLAP, thêm hai unit test, chạy lại fixture và run thành công. Báo cáo cũ không sửa để thành PASS. Decimal trong report JSON là chuỗi để giữ độ chính xác, CSV giữ giá trị numeric đầy đủ.

Catalog G2 trước đây chỉ nhận đúng 6 view nên cần mở allowlist cho bộ 6 view OLAP đầy đủ (tổng 12); vẫn từ chối view lạ, thiếu contract hoặc bộ OLAP chưa đủ. Không đổi bảng, ràng buộc, hợp đồng hoặc quy tắc chuẩn hóa ETL. SHA helper mới được ghi riêng, không sửa bundle/run 6D lịch sử. Chưa chạy lại full refresh và không tuyên bố đã kiểm full refresh với bản helper S07; hậu kiểm tích hợp chỉ đọc được chạy riêng.

Rubric giảng viên chưa được xác minh thêm; đây là kiểm nội bộ theo đặc tả/acceptance hiện có. Chưa dashboard/BI/G3/CF, chưa thay quyền hoặc kết nối hai máy. Hiệu năng mới đo một run khoảng 7 giây trên snapshot hiện tại, chưa benchmark tải đồng thời.

## File và cách xem

- Kết quả và SHA từng CSV: `results/olap/s07_af6dbc20b40d4a47aa3ea71bde6fd107/report.json` (đường dẫn tính từ repository).
- SQL/view: `olap/queries.sql`, `database/views.sql`; lệnh chạy và tham số xem `olap/README.md`.
- Hồ sơ thực thi và quyết định: `docs/agent/steps/P1/S07.md`; ledger bằng chứng: `results/olap/s07_summary.json`.

## Ý bảo vệ

1. Grain một đánh giá nguồn giúp tổng hệ thống không bị nhân khi phim có nhiều genre.
2. Điểm trung bình luôn tính từ tổng điểm và số đánh giá; fixture count 202/1 cho thấy mean các mean có thể sai.
3. Lưới genre × quý phải điền 0 trước LAG để QoQ so đúng quý liền trước.
4. QoQ đi kèm count, mẫu số, ngưỡng 100 và cờ quý biên; hạng cao có thể vẫn là giảm.
5. OLAP mô tả hành vi đánh giá lịch sử và cung cấp dataset tổng hợp cho BI sau này; không suy lượt xem/doanh thu/nhu cầu hiện tại.

Cần điều phối review định nghĩa chỉ số, quy tắc quý biên/xếp hạng và kết quả O1–O6. S07 WAITING_REVIEW; chưa commit/push/PR cho phần OLAP.
