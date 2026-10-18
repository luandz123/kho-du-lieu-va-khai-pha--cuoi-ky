# Quyết định P1

## S06 — riêng 6A, 18/10/2026

P1-D52: Điều phối chấp nhận S05 và giao riêng 6A; PR #7 MERGED đúng8de1c7b đã xác minh. Main52dd682 còn PR #8/P2, chỉ kế thừa, không sửa/chạy/duyệt P2. Nhánh p1-s06-etl, không commit/push/PR ở lượt này.

P1-D53: Insert bốn dimension vào target rỗng trong một transaction/khóa advisory chung; khóa staging chống đổi snapshot và target chống ghi cạnh tranh, kiểm toàn field/source/code sets/hashes trước commit. Không truncate/delete/upsert/bootstrap/DDL hoặc nạp bridge/fact/analytics. Trạng thái khác dự kiến thì dừng kiểm nguồn gốc.

P1-D54: Tính hash view phải ORDER BY/stable sort theo contract vì serializer không tự sort. Lần đầu thiếu sort rollback hoàn toàn; giữ FAIL, sửa caller và regression test, không đổi nguồn/DDL/hash kỳ vọng. Loader cuối77d3450b có unit13/fixture/load cùng hash.

P1-D55: Date lịch UTC continuous 1040 ngày lấy min/max Unix giây, generated calendar kiểm từng ngày; NULL năm vẫn giữ. Surrogate chỉ nội bộ, có thể gap sau rollback, không reset hoặc giả bằng ID nguồn. Hai view users/movies đúng không thay G2 đủ bốn view.

P1-D56: Sau 6A không gọi lại load S05 (đòi DW/analytics rỗng), không tự xóa để rerun6A hoặc tuyên bố integrated full refresh. 6D được giao riêng sau các tiền đề. 6A WAITING_REVIEW; 6B/C/D chưa làm.

## Chốt bằng chứng và công bố S05 — 17/10/2026

P1-D51: Push nhánh p1-s05-staging và PR #7 vào main đã thành công, API xác minh OPEN/merged=false ở head mở 2417416/base c3e4f998. Đủ 25 file/blob khớp local, 19+8 kiểm công bố đạt. Giữ code và mọi run cũ; cập nhật hồ sơ kết quả tiếp tục cùng PR. Chưa merge, chưa ETL DW/G2/6A/quyền BI/backup restore.

P1-D48: Điều phối báo review code/bằng chứng và chạy lại 9/9 unit test đạt, chưa phát hiện lỗi chặn PR; giao thêm một load cùng code rồi commit/push/mở PR, chưa merge/6A. Ghi đúng nguồn điều phối, không tạo lời duyệt nguyên văn của người dùng.

P1-D49: Chọn cặp **0f24c3a → f5f11bcd**, cùng code_sha256 04cb9c6082bbe6224d4c2e7e4d33f312140f25dce52c4a8fbc54d2aebdf8e92f; 10.078s → 9.281s, count/hash/field/source_line khớp, chín target rỗng. c122ce2/16.844s là run lịch sử khác code, không bằng chứng cùng phiên bản. Không sửa code giữa cặp run, không sửa báo cáo cũ; summary/handoff sắp theo started_at_utc.

P1-D50: Công bố đúng phạm vi S05/P1 sau đối chiếu bổ sung thành công; bảo toàn kế hoạch untracked, code và raw/P2. Hash artifact làm mới, lịch sử FAIL giữ nguyên. Chưa nghiệm thu ETL DW/G2/quyền BI/backup restore hoặc cho phép merge/chuyển bước.

## S05 — staging, chờ review

P1-D43: Theo lệnh điều phối mới, database riêng **movielens_btl** được chọn/cho phép tạo nếu chưa có và đủ quyền. Đã xác minh target chưa tồn tại, role hiện có được CREATE DATABASE; không đổi credential/quyền quản trị, không dùng postgres chứa nghiệp vụ. Database đã có mà không xác minh marker nguồn gốc thì script dừng giữ nguyên.

P1-D44: Sau xác minh PR #6 MERGED/c3e4f998, fast-forward main và tạo p1-s05-staging, giữ kế hoạch untracked và không sửa P2. S05 chưa được commit/push/PR; code được nhận diện bằng hash working tree và HEAD nền riêng biệt.

P1-D45: Áp dụng nguyên DDL S04 với guard; hoãn COMMIT cuối để so catalog trong cùng transaction. Không đổi mô hình hoặc thêm IF NOT EXISTS. Kiểm lỗi catalog ban đầu rollback toàn DDL; CREATE DATABASE riêng còn rỗng, không drop. Checker đã sửa và catalog thực khớp.

P1-D46: Nguồn độc lập P1 hash lại đúng byte; phiên bản code adapter đối chiếu Git blob LF và xác nhận checkout chỉ khác CRLF. Đây chỉ là nhận diện code, không đổi hash byte nguồn/canonical. Staging giữ source_line và raw text, loại ZIP, ba bảng nạp một transaction và so mọi field trước commit; không full refresh/nạp DW.

P1-D47: Hai lần staging cùng count/hash; fixture malformed tách biệt chứng minh rollback sau đã COPY users/movies. Chỉ dọn bảng/schema fixture vừa tạo, không CASCADE. S05 WAITING_REVIEW; không suy kiểm này thành G2, quyền BI hoặc chấp nhận chức năng ETL DW.

## Công bố S04 v2 — sau review của điều phối

P1-D42: Đẩy/mở PR #6 thành công trên p1-s04-schema → main; API xác minh OPEN/merged=false và 21 blob khớp local ở head công bố 68af045. Giữ checkpoint, không thay DDL hoặc sửa P2. Commit hồ sơ công bố tiếp theo thuộc cùng mốc; PR vẫn chờ review, chưa merge/S05. Kiểm công bố và hash đã cập nhật, không chạy lại 37 kiểm thiết kế hoặc PostgreSQL.

P1-D40: Nguồn ghi nhận **Điều phối chấp nhận S04 v2 ở mức thiết kế**; không gán thành lời duyệt nguyên văn của người dùng. Các phương án D31–D35/D38–D39 được chấp nhận ở phạm vi thiết kế theo danh sách điều phối, không thay DDL trong lượt công bố. Tên database/quyền thực thi và kiểm PostgreSQL thật còn thuộc bước sau.

P1-D41: Được commit/push/mở PR main trên p1-s04-schema, giữ checkpoint aeb41d1 không rewrite, commit phần đang dở trước đồng bộ origin/main. Rà toàn diff kể cả checkpoint; kế hoạch untracked ngoài phạm vi không stage. Không merge PR hoặc thực thi DDL. Lưu kết quả/hashes theo thực tế, không biến 37 kiểm cũ thành lần chạy mới.

## S04-draft-v2 — 16/10/2026 (đề xuất chờ review)

| Mã | Nội dung | Căn cứ/trạng thái |
|---|---|---|
| P1-D36 | Kế thừa v1, tiếp tục hoàn thiện theo đầu vào PR #5 đã merge; không chờ SHA metadata hoặc 8A để thiết kế | Lệnh điều phối mới; không thay lời duyệt G1/3B/S04. Định nghĩa DDL giữ nguyên |
| P1-D37 | Giữ nguyên checkout p1-s04-schema/aeb41d1, đọc snapshot PR #5 qua API/URL commit cố định | Bảo toàn dirty tree, không commit/fetch/pull/merge/reset/stash; không chép hoặc sửa P2 |
| P1-D38 | Đối soát trước commit phải dùng cùng connection/transaction nạp; kiểm adapter P2 trên DW đã commit ở G2 riêng | Bổ sung thiết kế, chưa chạy. Không dùng connection mới để chứng minh dữ liệu chưa commit |
| P1-D39 | Năm không khớp→NULL, không 0; numeric SUM/COUNT; reload full snapshot, PK/UQ chặn trùng; mất kết nối khi commit phải xác minh lại | Bổ sung cách triển khai/đối soát tương lai, không DML hoặc ETL ở S04 |

23/23 là báo cáo điều phối và log bàn giao đã đọc, không phải test P1 chạy mới. Source/canonical checksum không đổi, code sets đủ, ba script hash khớp; source_code_commit còn một SHA sai cần P2 sửa. WAITING_REVIEW thiết kế, chưa quyền áp dụng hoặc đẩy.

## S04-draft-v1 — 16/10/2026 (cập nhật mới; lịch sử giữ nguyên)

| Mã | Nội dung | Trạng thái/căn cứ |
|---|---|---|
| P1-D29 | Điều phối cho viết thiết kế nháp song song khi G1 còn PR sửa adapter/hồ sơ | Lệnh mới có phạm vi; thay việc chờ thiết kế tại D28, không duyệt G1 toàn bộ hoặc S04 |
| P1-D30 | Bảo toàn riêng chín file P1 bằng 2385a7d, main fast-forward b71d439, nhánh p1-s04-schema, kế thừa checkpoint aeb41d1 | Đã thực hiện cục bộ; không reset/stash/ghi P2/push; kế hoạch untracked ngoài phạm vi giữ nguyên |
| P1-D31 | UNIQUE fact user_key–movie_key; bốn dimension, bridge; surrogate nội bộ | Đề xuất cần review, dựa duplicate_pairs=0 và FK/miền/count trong bằng chứng 9299268, không suy từ báo cáo sạch |
| P1-D32 | Fact TIMESTAMPTZ + Unix, ngày UTC generated/FK ghép; view xuất TEXT UTC-Z đúng contract | Đề xuất cần review; không thay contract, không bỏ yêu cầu P2 sửa/test adapter datetime R1 |
| P1-D33 | Hai bảng cụm theo model_version + registry kỹ thuật và hai view active; kiểm toàn gói trước activate | Đề xuất cần review, tối đa một active, thiếu bằng chứng dùng NULL; không tự tạo model hoặc đổi giao diện P2 |
| P1-D34 | Full refresh transaction trong DB dự án riêng; vô hiệu hóa/xóa kết quả cụm, giữ metadata registry, nạp lại sau đối soát hash | Đề xuất cần review; không DROP/CASCADE, lỗi rollback, không hứa DB và file manifest atomic cùng nhau |
| P1-D35 | Tỷ trọng genre BI mặc định theo lượt gán đánh giá–genre; mean rating roll-up bằng SUM/COUNT | Đề xuất cần review, không cộng genre thành số rating duy nhất và không thay công thức vector ML của P2 |

S04 chỉ **WAITING_REVIEW bản nháp**. PR #3/#4 merge đã xác minh; R1–R6 chưa có kết quả sửa được kiểm nhận. Chưa chạy SQL, tạo DB/schema/view, load/ETL, bật Superset, push hoặc PR S04. Quyền viết nháp không phải quyền thực thi.

Phiên bản P1-S01-v1 ngày 15/10/2026. Không thay thế hồ sơ duyệt; đề xuất chưa phải quyết định nhóm đã duyệt.

| Mã | Nội dung và tác động | Trạng thái/căn cứ |
|---|---|---|
| P1-D01 | MovieLens1M/PostgreSQL/Python/6 OLAP/K-Means/CF+baseline+metric/3 Superset/report-slide; giới hạn Q1–Q3 | Ràng buộc Prompt chung, không mở rộng |
| P1-D02 | Checkout hiện tại; giữ bản cũ; S00 đã duyệt, S01 được giao | Xác minh local và “duyệt bước 0”; không phải duyệt S01 |
| P1-D03 | Contract2 nguyên quy ước, MD/JSON/workflow | WAITING_REVIEW, P1/P2 chưa xác nhận |
| P1-D04 | PostgreSQL 17.11 thay15/16 ghi trong nền; SQL/quyền kiểm lại | Đề xuất trình ở S00, cụ thể hóa S01 chờ chốt; không nhập lời duyệt bản cũ |
| P1-D05 | P1 Python 3.14/P2 Linux3.12.3; đề nghị dòng 3.12 chung tại G0 | WAITING_REVIEW; chưa chọn patch/pin hoặc cài P1; P2 tự báo, chưa test |
| P1-D06 | Kế thừa chọn lọc Superset6.1.0/8089, metadata riêng, giữ 8088/dịch vụ khác | WAITING_REVIEW; chưa copy/khởi động/chứng minh chạy hiện tại |
| P1-D07 | Nặng chạy lần lượt, thưa/theo lô, đo tài nguyên | WAITING_REVIEW; không tự đổi K/lọc phim/lấy mẫu Silhouette |
| P1-D08 | Lịch15–26/10, bảo vệ27/10; G0–G5; 12A→12-P2→12B và cụm trước CF | Lịch đề nghị S01 chờ duyệt; hạn bảo vệ là ràng buộc; không bỏ gate |
| P1-D09 | Hồ sơ chung cũ chỉ đọc, chưa ánh xạ/nhận APPROVED | Prompt chung; cần nhóm chốt cách kế thừa trước ánh xạ |
| P1-D10 | Không cần CF thắng baseline, không ngưỡng Silhouette buộc đạt; tính đúng/tái lập | Theo kế hoạch và lệnh S01; chi tiết acceptance chờ duyệt |
| P1-D11 | Remote có lịch sử, G0 qua nhánh/PR | Git local; kiểm quyền/remote thật khi G0 được giao; S01 không đẩy |
| P1-D12 | Rubric/checkout P2/máy bảo vệ chưa xác minh | Giới hạn bằng chứng, không biến tiêu chí nội bộ thành rubric |

Đổi giao diện cần phiên bản mới, chủ file xác nhận và nêu đầu ra phải chạy lại; không tự sửa hoặc tự duyệt bước cũ.

## Cập nhật tại G0 ngày15/10/2026

R-P1-01 duyệt P1-S01-v1; các nhãn đề xuất trong bảng là lịch sử. P1-D03 (phía P1), D04/D06/D07/D08 và phạm vi/nghiệm thu được duyệt; chưa đồng nghĩa runtime đã đạt. P1-D09 tiếp tục giữ hồ sơ cũ nguyên trạng; chưa có lựa chọn ánh xạ cụ thể để thi hành.

| Mã | Quyết định mới | Căn cứ và tác động |
|---|---|---|
| P1-D13 | Dòng Python3.12 chung, main mặc định | Người dùng “Duyệt” sau câu hỏi xác nhận. P1 còn3.14; cài/kiểm chứng3.12 thuộc setup, chưa chốt patch/pin tổng |
| P1-D14 | Nhánh mới không có codex/; G0 p1-g0-contract | Nguyên văn “các nhánh tạo sẽ không có codex đằng trước”. Thay quy ước tên của workflow nguồn; không tự đổi/xóa nhánh của P2 hoặc nhánh cũ |
| P1-D15 | Tám tệp nền G0 stage có chọn lọc; hồ sơ agent cập nhật cục bộ, chưa stage | Bootstrap tối thiểu; không git add .; commit/push/PR chờ Đẩy G0 |
| P1-D16 | P2 báo đã xong2/PR chờ duyệt, Python3.12.3 với các pin | numpy2.0.2/scipy1.14.1/scikit-learn1.5.2/pandas2.3.3/pytest8.4.2 là thông tin do người dùng chuyển, chưa kiểm PR hoặc chạy P1; không ghi requirements P2 |

Remote HEAD/fetch đã xác minh main/b7698b2, main...origin/main=0/0. Quyền đọc đạt; quyền ghi chưa thực kiểm. Không dùng quyền đọc để tuyên bố quyền push.

## Kết quả Đẩy G0

P1-D17, ngày15/10/2026: người dùng “Duyệt và đẩy g0” duyệt bộ G0/cấp quyền commit-push-PR. Commit5c31e80 thành công, push403 vì tài khoản GitHub hungvu205 thiếu quyền ghi repo luandz123/kho-du-lieu-va-khai-pha--cuoi-ky. Giữ commit/remote/nhánh, không tự đổi danh tính hoặc tạo fork. G0 APPROVED chức năng, công bố BLOCKED, PR/MERGED chưa có. Sau bổ sung quyền tiếp tục đúng commit theo quyền đẩy đã có; không cần xin lại duyệt mốc, merge vẫn riêng.

P1-D18, ngày15/10/2026: sau “đã vào push lại”, push5c31e80 thành công và mở PR#1 OPEN vào main. Blocker403 đã giải quyết; giữ nguyên commit/nhánh, không tạo fork/đổi remote. Dừng trước merge; P2 nhận main sau merge và xác nhận contract.

P1-D19, ngày15/10/2026: sau “đã merge”, xác minh GitHub PR#1 MERGED/eff54aee..., đồng bộ main bằng fast-forward, giữ nhánh G0 và hồ sơ cục bộ. Mốc nền sẵn sàng cho P2 pull/xác nhận contract; không tự sang bước2 hoặc gửi tin chat khác.

## S02-P1-v1 ngày15/10/2026

P1-D20: nhánh p1-s02-env không codex/, theo lệnh mới; chỉ setup sau S01 duyệt/G0 merge, chưa đẩy.

P1-D21: dùng Python3.12.14 bundled có sẵn để tạo venv, không cài toàn hệ thống hoặc đổi3.14; ghi base_prefix/cache dependency và nhu cầu tạo lại. P1 pins đã cài/import thực, requirements gốc chỉ include P1, chưa hợp nhất P2 hoặc nhận ML đã chạy.

P1-D22: kế thừa chọn lọc Superset6.1.0/8089, giữ metadata/volume/key/env hiện có. Sao chép secret.env cục bộ không đọc/in/hash; dùng docker start container cũ để tránh reset/recreate; config ghim6.1.0/postgres17.11, chưa rebuild máy sạch.

P1-D23: checker SQL readonly/timeout/SELECT1, .env chỉ đọc khi explicit; container nhận cấu hình qua stdin. Không raw exception/credential log; thiếu/failed là exit2/3. MetadataSQL/TCP không thay SQL Windows. Xác thực hiện lỗi, chờ user sửa, không đoán mật khẩu hoặc tạoDB.

P1-D24: nested.env.example được allowlist, secret.env vẫn ignore. Không có sensitive tracked nên không cần bỏ theo dõi; không sửa lịch sử Git. S02 giữ phạm vi chưa DW/ETL/mining/dashboard.

P1-D25: S02-v2 sau user báo đã sửa, cả host/container SELECT1_PASS17.11/exit0 theo.env thật. Khởi động lại hai container dự án đã dừng, giữ volume/key. Các lỗiSQL trước đã giải quyết; view/roleBI/UI/dashboard còn chưa nghiệm thu. Chờ duyệt S02, không tự chuyển bước/đẩy.

P1-D26: người dùng “duyệt và đẩy bước2” duyệt P1-S02-v2, cấp quyền commit/push/PR, không merge. Fetch trước đẩy thấy origin/main ff87081 đã gộp PR#2/P2, chỉ thêm file P2 không trùng; tích hợp nguyên vẹn sau commit phần P1, không sửa/chạy hoặc tự duyệt sản phẩm P2. Từ S02 đưa hồ sơ P1/tiền đề G0-S00-S01 vào Git để lưu dấu vết; giới hạn8tệp chỉ áp dụng bootstrap G0, không gom file môi trường/dữ liệu/bí mật.

P1-D27: công bố S02-v2 qua commit6ef3a95, tích hợp nguyên main/P2 bằng f761497 không conflict,9file P2 giữ nguyên. Push thành công/mở PR#3 OPEN, chưa MERGED. Commit chỉ cập nhật hồ sơ công bố tiếp theo thuộc cùng mốc; giữ giới hạn DW/BI/ML và dừng trước merge/bước tiếp.

P1-D28: khi nhận bước4, fetch/API cho thấy PR#3 vẫn OPEN và G1/5file EDA chưa có trên main/local. Ghi S04 BLOCKED vì thiếu đầu vào; không đoán UNIQUE/kiểu, không tạoDDL/thiết kế/tải nguồn khi chưa manifest đối chiếu. Không coi lệnh S04 là duyệt S03 hoặc cho phép merge PR. Chỉ cập nhật hồ sơ cục bộ, không đưa S04 vào PR môi trường đang chờ.
