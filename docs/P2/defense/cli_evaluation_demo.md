# Kịch bản trình bày CLI evaluation/demo — P2

Cập nhật 25/10/2026. Điều phối đã chấp nhận nội dung hỏi–đáp/kịch bản và cho phép tổng duyệt suy luận bằng bốn canonical CSV kiểm hash, ngoài Git, trong checkout Windows có quy tắc LF của P1. Đây **không phải đánh giá lại Test chính thức**. Kết quả kỹ thuật lượt bổ sung ghi riêng tại [smoke_rehearsal_20261025](../provenance/smoke_rehearsal_20261025/summary.md); không tạo slide tổng. Bản chuẩn bị trước đây chỉ rà code/chưa chạy CLI, không bị ghi lại thành một lần chạy đã có từ trước.

Nguồn: [chương 5 mục 5.7](../report/chapter_05.md), [CLI aggregate tích hợp lịch sử](../../../results/mining/integration_p2/cli_verification_summary.json), [receipt Test](../../../results/mining/cf_test_evaluation_receipt.json), [recommend.py](../../../mining/recommend.py), [adapter data_io.py](../../../mining/data_io.py).

## 1. Lời dẫn và phạm vi

“CLI minh họa suy luận Top5 qua adapter dữ liệu. Evaluation cố định lịch sử đến t₂, demo dùng toàn lịch sử và có model_version riêng. Kết quả đánh giá Test trong báo cáo là receipt đã khóa, không đo lại bằng thao tác demo này. Score CF là điểm xếp hạng tổng hợp từ similarity, không phải sao dự đoán.”

CLI fit ma trận và similarity trong bộ nhớ khi được gọi, không chỉ đọc model binary. Lượt tổng duyệt hiện tại được phép thực hiện suy luận, không gọi cf_test_evaluation.py hoặc eval_original.py, không tune neighbor_k, không tính metric Test hoặc sửa receipt. Ngữ cảnh hai nguồn cần phân biệt: tổng duyệt mới dùng **source=csv** đã kiểm hash; source=dw có bằng chứng lịch sử riêng, không tự nhận đã chạy DW mới chỉ vì đổi tài liệu cấu hình.

## 2. Chuẩn bị dữ liệu và cấu hình adapter

Thư mục làm việc là root checkout có mining/ và receipt đã công bố; interpreter venv có thể nằm ngoài checkout. Bốn canonical CSV đặt ở data/processed ngoài Git và phải khớp canonical_manifest trước chạy. Với source=csv, adapter không cần thông tin PostgreSQL.

**Với source=dw, cấu hình riêng biến môi trường của tiến trình:** PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD. `mining.recommend`/adapter không tự đọc `.env`; việc có tệp .env trong thư mục không đồng nghĩa các biến PG* đã được nạp. Adapter dùng os.getenv và truyền thông tin cho psycopg2. Không dựa vào giá trị mặc định host/port/database/user trong code để đoán đúng DB demo. Nếu dùng launcher nạp cấu hình riêng, phải chỉ rõ bước nạp trước khi gọi CLI, và không echo mật khẩu/URI.

Ví dụ PowerShell để cấu hình DW khi được phép dùng đúng database có sẵn; đây là mẫu, không công bố giá trị cấu hình thật:

```powershell
$env:PGHOST = Read-Host 'PGHOST của DW đã kiểm'
$env:PGPORT = Read-Host 'PGPORT của DW đã kiểm'
$env:PGDATABASE = Read-Host 'PGDATABASE của DW đã kiểm'
$env:PGUSER = Read-Host 'PGUSER chỉ đọc phù hợp'
$secret = Read-Host 'PGPASSWORD' -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $secret).Password
# Không in biến môi trường, connection URI hoặc mật khẩu vào log trình chiếu.
```

Các giá trị chỉ tồn tại cục bộ trong phiên demo, không đưa vào Git/báo cáo. Sau demo, khôi phục cấu hình phiên trước hoặc xóa biến mật khẩu riêng nếu đã tạo cho phiên này. Nếu CSV/DW chưa sẵn, dùng phương án dự phòng; không chạy ETL/restore để chữa tại chỗ. BI do P1 chuẩn bị, không thuộc CLI P2.

## 3. Lệnh trình bày và bảo vệ dữ liệu riêng tư

Đặt $checkoutRoot, $testPython theo máy chạy. Biến $caseUser chọn cục bộ, không ghi ID vào tài liệu/Git; $privateOutputRoot là thư mục riêng ngoài Git. Tổng duyệt mới dùng $source='csv'; chỉ chuyển 'dw' sau khi cấu hình đủ PG* và được phép dùng DW tương ứng. Không dùng receipt giả hoặc bỏ kiểm manifest với dữ liệu thật.

```powershell
Set-Location $checkoutRoot
$source = 'csv'  # Tổng duyệt 25/10 dùng canonical CSV đã kiểm hash.
& $testPython -m mining.recommend --source $source --user-id $caseUser --mode evaluation --top-n 5 --output-json (Join-Path $privateOutputRoot 'evaluation.json') *> (Join-Path $privateOutputRoot 'evaluation_console.log')
& $testPython -m mining.recommend --source $source --user-id $caseUser --mode demo --top-n 5 --output-json (Join-Path $privateOutputRoot 'demo.json') *> (Join-Path $privateOutputRoot 'demo_console.log')
```

Evaluation dùng cho cả ca có seed và fallback với hồ sơ cục bộ phù hợp; chọn tệp output khác nhau cho từng ca/lần chạy, không ghi đè log đã lưu. Hai lệnh xuất nội dung user-level nên terminal/JSON giữ riêng. Chỉ trình bày thống kê đã rà: mode, nguồn, model_version, cutoff và Top5 duy nhất/loại lịch sử, score type. Không trình chiếu ID, số seed/rating hoặc tên phim gợi ý gắn người dùng.

## 4. Trình tự thuyết trình và tiêu chí đối chiếu

1. **Evaluation có seed:** cutoff t₂=976422051, training scope 850.177 rating; model item_based_cf_k40_eval_v1, neighbor_k=40, Top5. Kiểm 5/5, score_type cf, duy nhất và đã loại lịch sử đến cutoff.
2. **Evaluation fallback:** cùng model/cutoff. Khi thiếu seed phù hợp hoặc không đủ ứng viên CF dương thì bổ sung popularity. Với ca tổng duyệt chọn phù hợp, kiểm 5/5 popularity_fallback, score N/A; không gộp count rating vào score CF.
3. **Demo:** model item_based_cf_k40_DEMO_full_history_v1, toàn lịch sử. Kiểm 5/5, duy nhất và loại toàn bộ lịch sử. Không tính Precision/Recall từ output demo hoặc so danh sách demo với Test để tạo metric.
4. **Kết thúc:** mở bảng 5.8/receipt nhắc Test đã chốt trên cohort1.154, kết quả CF/baseline. Không gọi evaluator hoặc tùy chọn --force để “minh họa” đánh giá lại.

Các tiêu chí theo ca không bảo đảm mọi hồ sơ đều có 5 mục CF. Nếu thực chạy khác dự kiến, giữ output riêng và giải thích mode/cutoff/candidate; không sửa receipt hoặc chọn lại k. [Kết quả tổng duyệt mới](../provenance/smoke_rehearsal_20261025/cli_aggregate.json) tách [bằng chứng tích hợp DW lịch sử](../../../results/mining/integration_p2/cli_verification_summary.json); không đổi nguồn của lượt cũ.

## 5. Phương án dự phòng

Nếu không có môi trường phù hợp, trình bày công thức tổng similarity, fixture tự tạo chương 2, bảng 5.9 và JSON tổng hợp đã công bố. Nói rõ đó là giải thích từ bằng chứng có sẵn. Lỗi LF/CRLF là định dạng checkout của snapshot kiểm toán tĩnh; smoke test suy luận thành công không tạo metric mô hình mới. G4 giữ đúng phạm vi, G5 và gói nộp chưa hoàn thành.
