# Checklist P1 kiểm nhận G1

Phiên bản G1-intake-v1, ngày 16/10/2026, Asia/Bangkok. Đây là danh sách chuẩn bị kiểm nhận, **không phải xác nhận đã nhận G1, duyệt P2/3B hoặc mở S04**. Lượt này không tải nguồn, sửa adapter, tạo DDL hoặc chạy ETL.

## 1. Nguồn thông tin và tình trạng hiện tại

- Qua báo cáo P2 được điều phối chuyển ngày 16/10: P2 báo đã xác nhận contract v2 tại 3A, đã tạo canonical/manifest tại 3B; đầu ra chưa push, chưa PR G1, còn thiếu adapter/báo cáo đầy đủ. **P1 chưa kiểm chứng bằng file/commit/PR**; không ghi3B/P2 APPROVED.
- Contract v2 của P1 đã có MD/JSON; trường P2 approval trong bản cục bộ vẫn null. Giữ nguyên bản này; khi có chứng cứ mới phải ghi nguồn/phiên bản, không tự tạo lời duyệt thay P2.
- PR#3 P1 vừa xác minh OPEN, chưa merge. Bộ prompt P1 yêu cầu2-P1 và G1 duyệt/merge trước thiết kế S04. S04 chưa mở trong lượt này.
- Kết quả EDA số dòng, tính duy nhất và checksum chưa được P1 kiểm nhận; không lấy số kỳ vọng MovieLens làm số đo thật.
- Rào cản Git đã kiểm: `.gitignore` quy tắc `*.csv` chặn `results/eda/data_profile.csv`. Khi được giao sửa cấu hình, P1 cần cho phép **riêng đường dẫn này** sau kiểm nội dung chỉ là thống kê tổng hợp; không bỏ chặn toàn bộ CSV hoặc dữ liệu theo user. Lượt này chưa sửa `.gitignore`.

## 2. Hồ sơ và đầu vào cần nhận

Tất cả ô dưới đây để trống cho tới khi P1 có bằng chứng thực tế.

| Kiểm | Đầu vào | Bằng chứng cần ghi |
|---|---|---|
| [ ] | Xác nhận contract v2 của P2 tại 3A | Nguyên văn xác nhận, người xác nhận, phiên bản/hash contract, hồ sơ/commit tham chiếu; phân biệt xác nhận hợp đồng với duyệt 3B/S03 |
| [ ] | `docs/agent/steps/P2/S03.md` | Phạm vi3A–3B và phần tiếp theo, lệnh đã chạy/kết quả/giới hạn, lời duyệt thật của S03 hoặc hồ sơ tương đương có ánh xạ rõ |
| [ ] | `docs/P2/data_understanding.md` | Nguồn, số liệu EDA thật, ý nghĩa trường, lỗi/thiếu/trùng/FK, UTC, phim đa thể loại, chính sách xử lý |
| [ ] | `results/eda/data_profile.csv` | Thống kê tổng hợp, schema của profile được mô tả; không chứa hàng rating hoặc định danh theo user; nằm trong PR thực tế |
| [ ] | `data/source_manifest.json` | dataset_version, URL chính thức, ngày tảiUTC, encoding, SHA-256/số dòng từng tệp gốc; P2 sở hữu |
| [ ] | `results/eda/canonical_manifest.json` | contract_version2, schema/thứ tự cột, row_count/hash4 bảng, tập mã nguồn |
| [ ] | Adapter raw/csv/dw cùng CLI/tài liệu | Đường dẫn module/API, cách chọn nguồn, quy tắc không làm sạch khác nhau, chế độ DW chưa có được ghi rõ |
| [ ] | Test/fixture của adapter và chuẩn hóa | Lệnh chạy, phiên bản runtime/dependency, kết quả thật, test fixture nhỏ tự tạo không phải dữ liệu MovieLens theo user |
| [ ] | PR/commit G1 | URL, head SHA đã review, main merge SHA, trạng thái API; không dùng merge_commit_sha dự kiến của PR OPEN làm chứng cứ đã merge |

Không yêu cầu P2 chép toàn bộ data/raw, data/processed, .venv hoặc docs đè workspace P1. Không yêu cầu đưa canonical theo user hoặc gói cụm lên GitHub.

## 3. Kiểm schema và chuẩn hóa theo contract v2

| Bảng logic | Thứ tự cột bắt buộc | Điều kiện |
|---|---|---|
| users | user_id, gender, age_group, occupation | ID nguyên duy nhất; F/M; nhóm tuổi đúng mapping; occupation giữ mã số nguồn |
| movies | movie_id, title, release_year | ID nguyên duy nhất; title giữ nguyên; năm bốn chữ số trong ngoặc cuối, không khớp thì NULL |
| movie_genres | movie_id, genre_name | Khóa(movie_id,genre_name) duy nhất, genre giữ tên nguồn, tham chiếu movie tồn tại |
| ratings | user_id, movie_id, rating, timestamp, rated_at | Grain một hàng nguồn; rating nguyên1..5; timestamp int64 giâyUnix/rated_at cùng thời điểmUTC; không join genre vào ratings |

- [ ] So tên cột, **thứ tự**, kiểu logical/nullability với cả MD và JSON; nếu bất nhất dừng chốt chung, không tự sửa contract.
- [ ] Xác minh nhãn tuổi:1→Under18 (chuỗi chuẩn là `Under 18`),18→18-24,25→25-34,35→35-44,45→45-49,50→50-55,56→56+; không dùng ZIP code.
- [ ] Kiểm toàn bộ rated_at là ISO8601 `YYYY-MM-DDTHH:MM:SSZ`, tương đương timestamp giâyUnix; không chuyển sang local time rồi tính quý.
- [ ] Nguồn Latin-1, phân cách `::`; quy tắc tách title/genre giữ Unicode nguồn đúng; không trim/đổi chữ hoặc gộp khác contract âm thầm.
- [ ] NULL năm phát hành xuất ô rỗng; số nguyên không có `.0`; gender/occupation/mã tuổi/tập genre được đối chiếu manifest và profile.

## 4. Row count, serializer và hash

- [ ] Phân biệt số dòng tệp nguồn (không header) với số bản ghi CSV chuẩn (không header); không tự bù số kỳ vọng khi sai lệch.
- [ ] CSV chuẩn UTF-8 không BOM, dấu phẩy, LF, header, quoteCSV chuẩn, NULL ô rỗng. Dữ liệu chuẩn được sinh bằng serializer xác định; không để Git autocrlf quyết định byte hash.
- [ ] Sort users:user_id; movies:movie_id; movie_genres:movie_id,genre_name; ratings:user_id,movie_id,timestamp,rating.
- [ ] Hash SHA-256 **byte CSV chuẩn** từng bảng; so row_count/schema/hash của raw-adapter và csv-adapter với canonical_manifest. Không dùng pandas hash, hash object Python hoặc chỉ tổng số dòng/tổng điểm để thay thế.
- [ ] Kiểm các tập mã nguồn trong manifest; nguồn/hash4 bảng/version cùng một lần chạy, không trộn manifest cũ với CSV mới.
- [ ] Quy tắc quoting chi tiết phải tái lập từ adapter/fixture; nếu “CSV chuẩn” vẫn cho nhiều cách tuần tự hóa có byte khác nhau, trình hai bên chốt cách hiện thực trước đối chiếu, không tự đổi hợp đồng.
- [ ] Chạy test adapter/serializer khi được giao kiểm nhận thật; ghi runtime, commit, lệnh/exitcode và kết quả. Ghi rõ test DW chưa thể chạy khi chưa có DW, không đánh dấu PASS giả.

## 5. EDA nào quyết định thiết kế DW

| Kết quả cần kiểm | Quyết định thiết kế bị ảnh hưởng |
|---|---|
| Trùng hoàn toàn và số cặp user–movie lặp/xung đột rating/timestamp | Có được đặt UNIQUE(user_id,movie_id) trên khóa nguồn tương ứng hay không; grain vẫn là hàng đánh giá nguồn. Nếu có trùng/lỗi, chờ chính sách chung, không tự deduplicate |
| ID user/movie duy nhất, null/kiểu và min-max ID | Khóa tự nhiên, ánh xạ surrogate, kiểu integer phù hợp và kiểm mất bản ghi |
| RatingFK→user/movie, genre FK→movie, khóa mồ côi | FK/load order, chính sách reject/rollback; không loại mồ côi âm thầm |
| Miền rating, null và ký tự sai | SMALLINT/CHECK1..5/not-null nếu có căn cứ; lỗi nguồn làm pipeline dừng hay reject phải được chốt |
| Bộ mã gender/age/occupation và giá trị lạ | Kiểu/check/nullability và mapping có nguồn; không thêm dimension không có dữ liệu |
| Phim nhiều genre, cặp movie–genre trùng, số genre/phim | Bridge PK/FK, quan hệ1:N, count theo genre không cộng thành rating duy nhất |
| Min-max timestamp/rated_at, biên ngày/quý, giá trị thời gian bất thường | TIMESTAMPTZ/UTC, phạm vi dim_date, biên quan sát và kiểm QoQ; không suy thời lượng xem |
| Tách năm cuối title và số nămNULL | release_year nullable, quy tắc transform và ca biên |
| Row count/hash chuẩn4 bảng và tập mã | Mốc đối soát nguồn→staging→DW, giao diện4 view và tái lập full refresh |

Chỉ chốt khóa/kiểu/ràng buộc sau xem số đo thật và test; không dùng bản canonical chỉ báo đã tạo để kết luận nguồn sạch.

## 6. P1 tải độc lập và đối chiếu

- [ ] Sau nhận manifest/được giao kiểm nhận, P1 tự tải MovieLens1M từ GroupLens chính thức, không lấy dữ liệu đã làm sạch của máy P2 làm nguồn gốc.
- [ ] Lưu ZIP/tệp nguồn trong data/raw cục bộ bị ignore; không commit/Release/Artifact. Giữ bản đang có, không xóa/ghi đè dữ liệu khác.
- [ ] Đối chiếu danh sách tệp, SHA-256 tệp gốc/encoding/số dòng với source_manifest P2; hash ZIP và hash dat nếu có phải phân biệt rõ.
- [ ] Nếu hash khác: dừng kiểm nhận, xác định khác phiên bản/tệp/encoding; không sửa manifest P2 hoặc làm sạch cho khớp.
- [ ] Dùng adapter tại **commit G1 đã review** để tạo/đọc4 bảng chuẩn và đối chiếu canonical hash trên P1; script output canonical theo user chỉ cục bộ.
- [ ] Ghi phiên bản nguồn,contract,adapter và bằng chứng kiểm nhận vào hồ sơP1 khi được giao; không sao chép toàn docs P2 hoặc ghi trạng tháiP2.

## 7. Điều kiện đủ để bắt đầu S04

- [ ] S02-P1 có lời duyệt thật và PR môi trường đã merge theo bộ prompt; kiểm trạng thái GitHub, không suy APPROVED=MERGED.
- [ ] Xác nhận contract v2 P2 có nguồn kiểm chứng; hồ sơ S03 cho thấy phạm vi hoàn tất và lời duyệt thật, không tự gán3B APPROVED.
- [ ] PR G1 đã review/merge, đủ hồ sơ/understanding/profile/2 manifest/adapter/test; bất kỳ thiếu sót nào được ghi cụ thể và xử lý trước chốt thiết kế.
- [ ] P1 kiểm hash nguồn/canonical, schema và kết quả EDA ảnh hưởng PK/FK/UNIQUE; không còn xung đột dữ liệu/chính sách làm sạch.
- [ ] Người dùng giao/cho tiếp tục S04; bảo toàn dirty files trước thao tác Git ở lượt được phép. Nhánh tương lai p1-s04-schema không codex/.

Đầu ra khi mở S04: ERD, từ điển, ánh xạ, index/full-refresh/UTC, schema.sql nháp,4 view chuẩn và2 bảng analytics cụm; **không chạy DDL ở S04**. Lượt lập checklist này chưa mở S04.

## 8. Những phần chỉ xác minh được khi có DW

- [ ] Adapter mode DW đọc4 view thật, đúng cột/IDnguồn và hashcanonical; CSV không thay xác nhận cuối trên DW.
- [ ] G2-P2 đối soát độc lập count/hash/tập mã/UTC và không nhân rating theo genre.
- [ ] PK/FK/CHECK/UNIQUE thực thi, transaction/rollback/idempotence qua load thật ở bước triển khai.
- [ ] Tài khoản BI đọc view thật từ container với quyền tối thiểu; SELECT1 không chứng minh role chỉ đọc.
- [ ] Gói cụmG3/source_hashes/canonical_hashes/model_version phù hợp DW/analytics trước11B; không là tiền đề phải chờ để làm S04.

## 9. Mẫu kết luận kiểm nhận về sau

Ghi riêng: file đã nhận; commit/PR/head/mergeSHA; contract confirmation; nguồn/hash đã so; adapter modes/tests đã chạy; hạn chế DW chưa thể kiểm; quyết định cần người dùng duyệt. Không tick PASS theo im lặng hoặc báo cáo qua điều phối. Những ô chưa kiểm giữ nguyên chưa đánh dấu.

## 10 Kiểm nhận thực tế ngày 16 tháng 10 năm 2026

Phần 1–9 phía trên là bản chuẩn bị lịch sử. Cập nhật này thay thông tin cũ về trạng thái PR và đầu vào đã nhận, không tạo lời duyệt.

- [x] GitHub API xác nhận PR3 môi trường đã merge; PR4 G1 cũng đã merge trước lượt kiểm nhận, merge SHA b71d439fa2cc3ee84c40f4a28dc6fe00c8326d42.
- [x] Review G1 head 9299268278900814f939e0e4214d23a31e09ef64 tại snapshot tạm; không thay checkout chính.
- [x] Nhận đủ hồ sơ S03/S03A/S03B, báo cáo, profile, manifest, adapter, test và sáu PNG. Đã thấy lời duyệt 3A, chưa tạo lời duyệt toàn S03.
- [x] Tải nguồn độc lập, so bốn hash nguồn và số dòng với manifest P2.
- [x] Tái tạo bốn bảng canonical, row_count/hash khớp manifest gốc, raw/csv tương đương.
- [x] Kiểm khóa, FK, rating, năm và UTC; xác minh cục bộ đúng hai user thiếu đánh giá tích cực.
- [x] Chạy bộ test trong môi trường tách biệt trên Windows: 18/18 đạt; không dùng test này để khẳng định PostgreSQL DW thật đã đạt.
- [ ] Nghiệm thu toàn bộ G1: còn lỗi R1–R6 trong g1_review_2026-10-16.md. PR đã merge nên sửa qua PR tiếp theo.
- [ ] Metadata canonical đủ tập mã và provenance phiên bản code sinh dữ liệu.
- [ ] Đầu ra Git chỉ tổng hợp: profile/báo cáo hiện có ID và lịch sử từng user cần sửa theo quy ước.
- [ ] Adapter DW chuẩn hóa datetime UTC và xử lý lỗi an toàn; chưa xác minh DW thật.
- [ ] Mở S04: chưa thực hiện trong lượt kiểm nhận này.

Bằng chứng: g1_verification_9299268.json, g1_pytest_9299268.txt và g1_review_2026-10-16.md trong docs/P1. Không sửa P2, không commit/push hoặc đăng review.
