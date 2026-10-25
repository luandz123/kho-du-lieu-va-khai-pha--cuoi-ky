# Kiểm chứng snapshot evaluator LF trên Windows — P2

Ngày 25/10/2026 — **Hồ sơ kiểm LF ban đầu; bản sửa LF đã được điều phối chấp nhận.** Phần dưới giữ kết quả theo từng pha lúc kiểm, không sửa log cũ. Lượt hoàn tất smoke test được phép sau đó có hồ sơ riêng tại [smoke_rehearsal_20261025](smoke_rehearsal_20261025/summary.md). Đây là sửa định dạng checkout và kiểm thử fixture/kiểm tĩnh, không phải một lượt đánh giá Test chính thức mới. Không chạy ETL, mô hình trên dữ liệu thật hoặc evaluator Test chính thức; không đổi snapshot logic, assertion, metric, receipt hoặc checksum kỳ vọng.

## 1. Nền và phối hợp

Nền kiểm: `a2021a9f591c56222f5ae16e169f278bf3cec5a7`, merge [PR31](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/31) đã có trên origin/main khi kiểm Git. Chương 2/5/6 đã được điều phối duyệt. Candidate thực kiểm tích hợp vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`; không gán commit báo cáo vào run evaluator lịch sử. G4 đạt đúng phạm vi; G5 chưa hoàn thành.

Checkout chung đang có công việc P1 trên nhánh codex/p1-s13-final-report, được giữ nguyên. P2 tạo nhánh/checkout riêng `codex/p2-evaluator-lf-verification` để tái hiện trước sửa, rồi checkout detached mới để kiểm sau sửa. Không reset/clean và không sửa file P1.

P1 thêm đúng một dòng trong .gitattributes:

```gitattributes
docs/P2/provenance/eval_original.py text eol=lf
```

P2 đọc và sao chép nguyên byte quy tắc P1 vào checkout kiểm; không tự tạo bản sửa khác, không mở PR trùng. Trạng thái bản sửa tại lúc kiểm: **quy tắc chưa commit/merge**, nằm trong working tree P1. [p1_rule.json](newline_verification_20261025/p1_rule.json) ghi hash/kích thước và nguồn phối hợp, không ghi nhầm là commit mới đã được nghiệm thu.

## 2. Nguyên nhân và kiểm file vật lý

Git blob snapshot đã đúng 32.508 byte LF. Trước quy tắc hẹp, checkout Windows với core.autocrlf=true biến 671 LF thành CRLF, file vật lý thành 33.179 byte. Chuẩn hóa CRLF→LF chỉ được dùng **để chẩn đoán đối chiếu** và nội dung khớp tuyệt đối blob; không đưa chuẩn hóa vào test hoặc đổi checksum kỳ vọng.

| Điểm kiểm | Byte vật lý | CRLF | SHA-256 vật lý | Git blob SHA-1 tính từ byte vật lý |
|---|---:|---:|---|---|
| Trước quy tắc | 33179 | 671 | ce1ea24e752e9cadd2356642f03fa1f553f826cc40f1460f5b32715308124739 | Xem before.json; không bằng checksum LF được chốt |
| Checkout mới có quy tắc, autocrlf=true | 32508 | 0 | e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d | d7c97bae8b6de3449c0306a2f841325f5434f248 |

Nguồn: [before.json](newline_verification_20261025/before.json), [after.json](newline_verification_20261025/after.json). Dòng sau khớp cả byte với Git blob và checksum đã nghiệm thu; có 671 LF. Không kết luận evaluator đã sai logic từ lỗi CRLF này.

Chỉ thêm attribute không tự viết lại file đã có. Một lần checkout-index trên file cũ vẫn giữ CRLF, nên phép kiểm sau sửa dùng **worktree mới chưa xuất file**, đặt .gitattributes P1 trước khi Git checkout. Sau kiểm độc lập, P2 cũng bảo toàn file CRLF cũ ở vùng riêng ngoài Git rồi để Git materialize lại **duy nhất** đường dẫn snapshot trong checkout chung với quy tắc P1; không tự chuyển newline bằng Python để sửa. [shared_checkout_after.json](newline_verification_20261025/shared_checkout_after.json) xác nhận file chung cũng 32.508 byte, 0 CRLF, cùng hai checksum và không có diff nội dung snapshot.

## 3. Lệnh thực hiện và kết quả

Quy ước: lệnh chạy trong PowerShell; $repoRoot là checkout chung, $beforeCheckout/$afterCheckout là hai thư mục mới tách biệt; $testPython là interpreter s12a-venv hiện có ở ngoài hai checkout kiểm. Không dùng venv .venv cũ thiếu pytest và không cài thêm dependency. [environment.json](newline_verification_20261025/environment.json) ghi Windows/Python3.12.14, pytest8.4.2 và thư viện thực dùng; đây là môi trường test sửa newline, không đổi hồ sơ môi trường P2/Windows3.12.6 của lượt tích hợp cũ.

Trình tự Git đã dùng:

```powershell
# Từ repo chung, trước khi thêm attribute vào checkout kiểm:
git -c core.autocrlf=true worktree add -b codex/p2-evaluator-lf-verification $beforeCheckout origin/main
# File trước sửa được giữ ở checkout này.

# Tạo checkout sau sửa, chưa có file tracked được xuất:
git -c core.autocrlf=true worktree add --detach --no-checkout $afterCheckout a2021a9f591c56222f5ae16e169f278bf3cec5a7
# Sao chép nguyên .gitattributes do P1 vừa thêm vào thư mục checkout mới.
Copy-Item -LiteralPath (Join-Path $repoRoot '.gitattributes') -Destination (Join-Path $afterCheckout '.gitattributes')
Set-Location $afterCheckout
git -c core.autocrlf=true checkout HEAD -- .
git -c core.autocrlf=true check-attr text eol -- docs/P2/provenance/eval_original.py
git ls-files --eol docs/P2/provenance/eval_original.py
```

Kết quả Git: text=set, eol=lf, `i/lf w/lf attr/text eol=lf`. Check byte đọc binary không chuẩn hóa; Git blob SHA-1 = SHA1 của header `blob <byte_length>\0` ghép byte vật lý. Snapshot chỉ đọc tĩnh, không import hoặc chạy nó.

Các lệnh test dùng `-q --tb=short --color=no -p no:cacheprovider`. Chạy trong checkout trước/sau tương ứng, interpreter ngoài checkout:

```powershell
& $testPython -m pytest tests/mining/test_cf_test_evaluation.py::test_evaluator_provenance_trace_artifact_integrity -q --tb=short --color=no -p no:cacheprovider
& $testPython -m pytest tests/mining/test_cf.py tests/mining/test_cf_test_evaluation.py tests/mining/test_recommend.py -q --tb=short --color=no -p no:cacheprovider
```

| Pha thực chạy | Kết quả | Log |
|---|---|---|
| Provenance trước quy tắc | 1 FAIL: 33179 != 32508 | [before_provenance_FAIL.txt](newline_verification_20261025/before_provenance_FAIL.txt) |
| Provenance trong checkout mới có quy tắc | 1 PASS | [after_provenance_PASS.txt](newline_verification_20261025/after_provenance_PASS.txt) |
| Nguyên nhóm ba file sau sửa | **29 PASS / 2 FAIL** do thiếu canonical CSV, không phải lỗi checksum | [after_group_DATA_MISSING_FAIL.txt](newline_verification_20261025/after_group_DATA_MISSING_FAIL.txt) |
| Fixture/kiểm tĩnh của ba file, loại tường minh 2 test cần dữ liệu thật | **29 PASS / 2 deselected** | [after_fixture_static_subset_PASS.txt](newline_verification_20261025/after_fixture_static_subset_PASS.txt) |

Hai test cần dữ liệu thật: `test_recommend_evaluation_mode_default_valid_receipt` và `test_recommend_cli_smoke` trong test_recommend.py. Chúng đọc data/processed và fit mô hình suy luận; checkout mới không có CSV, nên dừng tại FileNotFoundError trước fit. P2 không đưa dữ liệu thật vào hoặc mock checksum để ép chúng qua. Không sửa/xóa/skip trong source test. Lệnh subset thêm hai tùy chọn sau vào đúng lệnh nhóm:

```powershell
--deselect=tests/mining/test_recommend.py::test_recommend_evaluation_mode_default_valid_receipt
--deselect=tests/mining/test_recommend.py::test_recommend_cli_smoke
```

Các test evaluator vẫn giữ fixture/mock/guard, assertion LF vật lý và checksum không đổi. 29 test subset gồm fixture tính tay và kiểm đọc artifact tĩnh; không gọi pipeline đánh giá Test trên dữ liệu thật. **Không báo 31/31 hoặc 119/119.** Mốc 118/119 trước đó là thông tin lượt rà điều phối cung cấp; P2 không chạy lại toàn bộ 119 test.

Log raw nguyên byte giữ riêng ngoài Git; bản công bố chỉ che đường dẫn/ID đối số test và chuẩn hóa xuống dòng để đọc, ghi rõ ở từng log. Log FAIL không bị đổi thành PASS; lỗi thiếu CSV sau sửa được giữ riêng. Tên raw của lượt nhóm lúc tạo có chữ PASS theo tên pha dự định, nhưng stdout/exit=1 nguyên vẹn; bản công bố đặt đúng DATA_MISSING_FAIL. Xem [test_results.json](newline_verification_20261025/test_results.json).

## 4. Bảo toàn và phạm vi kết luận

[protected_sources.json](newline_verification_20261025/protected_sources.json) ghi hash blob Git snapshot/evaluator/tests/provenance/receipt/metric. Không thay source/assertion/checksum kỳ vọng, không tạo kết quả mô hình mới hoặc sửa log thực nghiệm cũ. Chỉ thêm bằng chứng kiểm newline có ngày/pha rõ ràng và cập nhật hồ sơ P2.

Quy tắc P1 đã chứng minh giữ đúng byte vật lý trong checkout Windows mới dù core.autocrlf=true. Phạm vi cần review còn lại: P1 tích hợp một bản sửa chung và điều phối xem giới hạn 2 test recommender thực-dữ-liệu chưa PASS trong môi trường tách biệt. Không coi giới hạn này là lý do chạy mô hình thật khi chưa được giao; không tự mở PR hoặc merge.

Sau phần kiểm, đã soạn [24 câu hỏi–đáp Q1/Q2](../defense/qa_q1_q2.md) và [kịch bản CLI evaluation/demo](../defense/cli_evaluation_demo.md) từ artifact đã chốt. Kịch bản chưa chạy mô hình; không tạo slide tổng. Toàn bộ lượt bàn giao đặt **WAITING_REVIEW**.


## 5. Cập nhật sau quyền chạy suy luận — 25/10/2026

Sau khi chấp nhận bản sửa LF và nội dung hỏi–đáp/kịch bản, điều phối cho phép dùng bốn canonical CSV kiểm hash ngoài Git để hoàn tất hai smoke test và tổng duyệt CLI. Hai smoke test đạt 2/2; chạy nguyên ba file test đạt 31/31, không deselect. Đây là lượt sau cấp dữ liệu, khác log 29 PASS/2 FAIL thiếu CSV và subset 29 PASS/2 deselected phía trên; các log/checksum cũ không bị ghi đè.

Bằng chứng mới, lệnh, tổng duyệt CLI và xác nhận không đổi receipt/metric tại [summary.md](smoke_rehearsal_20261025/summary.md). Chỉ dựng mô hình suy luận trong bộ nhớ theo quyền mới, không gọi evaluator Test chính thức, không chạy snapshot kiểm toán. Phối hợp P1 một PR sửa LF, không mở PR trùng; G5 chưa hoàn thành.
