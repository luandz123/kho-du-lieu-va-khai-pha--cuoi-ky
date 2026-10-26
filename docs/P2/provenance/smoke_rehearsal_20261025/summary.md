# Hoàn tất smoke test và tổng duyệt CLI suy luận — P2

Ngày 25/10/2026 — **WAITING_REVIEW kết quả bổ sung**. Điều phối đã chấp nhận bản sửa LF và nội dung hỏi–đáp/kịch bản, sau đó cho phép sử dụng canonical CSV đã kiểm hash ngoài Git để chạy hai smoke test và dựng mô hình suy luận trong bộ nhớ cho tổng duyệt CLI. Không thực thi evaluator Test chính thức hoặc snapshot eval_original.py; không tính lại metric Test, tune k, sửa receipt hoặc mock checksum/assertion.

## 1. Nền, dữ liệu và môi trường

- Commit nền: `a2021a9f591c56222f5ae16e169f278bf3cec5a7` (PR31 đã merge). Candidate thực kiểm tích hợp giữ nguyên `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`.
- Checkout thử Windows tách biệt đã có quy tắc P1 `docs/P2/provenance/eval_original.py text eol=lf`, core.autocrlf=true. Snapshot vật lý vẫn 32.508 byte, 0 CRLF; SHA-256 `e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d`, blob SHA-1 `d7c97bae8b6de3449c0306a2f841325f5434f248`.
- Bốn canonical CSV từ dữ liệu cục bộ sẵn có được kiểm SHA-256 nguyên byte theo canonical_manifest, sao chép nguyên byte vào data/processed của checkout thử, kiểm hash lại và xác nhận cả bốn được Git ignore. Không chạy ETL hoặc sinh lại nguồn. [input_verification.json](input_verification.json) ghi hash/kích thước.
- Interpreter hiện có ở venv ngoài checkout thử: Windows/Python3.12.14, pytest8.4.2, numpy2.0.2, pandas2.3.3, scipy1.14.1, scikit-learn1.5.2. Không cài/nâng cấp dependency. Đây là môi trường smoke mới, không đổi hồ sơ lượt tích hợp P2/Python3.12.6. [Môi trường kiểm LF](../newline_verification_20261025/environment.json).

## 2. Hai smoke test và nguyên nhóm đầy đủ

Thư mục làm việc: root checkout LF đã có bốn CSV đúng hash. $testPython là interpreter venv ngoài checkout; không dùng venv .venv thiếu pytest. Lệnh thực chạy:

```powershell
& $testPython -m pytest tests/mining/test_recommend.py::test_recommend_evaluation_mode_default_valid_receipt tests/mining/test_recommend.py::test_recommend_cli_smoke -q --tb=short --color=no -p no:cacheprovider
& $testPython -m pytest tests/mining/test_cf.py tests/mining/test_cf_test_evaluation.py tests/mining/test_recommend.py -q --tb=short --color=no -p no:cacheprovider
```

| Lượt chạy mới sau khi cấp canonical CSV | Kết quả thật | Thời gian pytest | Log |
|---|---|---:|---|
| Hai smoke test còn thiếu | 2 passed, 0 failed | 30.67 giây | [two_smoke_tests.txt](two_smoke_tests.txt) |
| Đầy đủ nhóm ba file, không deselect | **31 passed, 0 failed, 0 deselected** | 54.85 giây | [full_31_group.txt](full_31_group.txt) |

Nguồn: stdout/exit code mới, chi tiết [test_results.json](test_results.json). Test/fixture/guard được giữ nguyên. Nhóm có import module evaluator để kiểm guard/fixture, không gọi evaluator đánh giá Test chính thức trên dữ liệu thật; snapshot kiểm toán chỉ được đọc binary để kiểm hash. Không suy kết quả nhóm 31 thành full suite119.

[Log 29 PASS/2 FAIL thiếu CSV trước đó](../newline_verification_20261025/after_group_DATA_MISSING_FAIL.txt) và [log 29 PASS/2 deselected](../newline_verification_20261025/after_fixture_static_subset_PASS.txt) giữ nguyên. Chúng thuộc pha chưa được phép cấp dữ liệu/chạy suy luận, không bị sửa thành PASS. [Log provenance trước/sau LF](../windows_newline_verification.md) vẫn tách biệt với lượt smoke này.

## 3. Tổng duyệt CLI evaluation/demo

Gọi **mining.recommend** qua CLI bằng source=csv trong cùng checkout thử; tham số mỗi ca là --mode evaluation/demo, --top-n 5, --user-id lấy cục bộ và --output-json trỏ thư mục riêng ngoài Git. Không dùng skip_manifest_verification hoặc receipt giả. Evaluation xác minh canonical hashes theo receipt thật; demo có identity/disclaimer riêng và bốn tệp nguồn được kiểm hash trước chạy.

Mẫu lệnh (ID và đường dẫn riêng tư không công bố):

```powershell
& $testPython -m mining.recommend --source csv --user-id $caseUser --mode evaluation --top-n 5 --output-json $privateCaseJson
& $testPython -m mining.recommend --source csv --user-id $caseUser --mode demo --top-n 5 --output-json $privateCaseJson
```

Mỗi ca dùng tên tệp riêng, không ghi đè output trước. Chọn ca cục bộ theo điều kiện có seed evaluation, fallback evaluation và demo; không xuất ID, số seed/rating, lịch sử hoặc danh sách phim gợi ý theo người dùng. Raw stdout/stderr và JSON đầy đủ giữ riêng ngoài Git; hồ sơ công bố chỉ là [cli_aggregate.json](cli_aggregate.json).

| Ca tổng hợp | Mode / nguồn | Model identity | Trả/yêu cầu | Duy nhất, loại đúng lịch sử | Score type | Exit / kết quả |
|---|---|---|---|---|---|---|
| Evaluation có seed | evaluation / csv | item_based_cf_k40_eval_v1 | 5/5 | Có / cutoff t₂ | cf | 0 / PASS |
| Evaluation fallback | evaluation / csv | item_based_cf_k40_eval_v1 | 5/5 | Có / cutoff t₂ | popularity_fallback, score None/N/A | 0 / PASS |
| Demo | demo / csv | item_based_cf_k40_DEMO_full_history_v1 | 5/5 | Có / toàn lịch sử | cf | 0 / PASS |

Nguồn: ba lần gọi CLI thật và kiểm output riêng. Đơn vị bảng là ca kiểm, số mục trên danh sách yêu cầu5; không phải tỷ lệ thành công trên toàn user. Evaluation giữ t₂=976422051 và scope850.177 rating; demo toàn lịch sử, cấm dùng lấy metric offline. Model suy luận chỉ trong bộ nhớ, không lưu model binary. Đây là kiểm chức năng suy luận, không là Test evaluation mới hoặc bằng chứng ưu thế metric mới.

## 4. Cấu hình DW trong kịch bản

Tổng duyệt mới **không truy vấn DW**, dùng source=csv đã kiểm hash. Đã sửa [kịch bản CLI](../../defense/cli_evaluation_demo.md): với source=dw, phải cấu hình riêng PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD cho tiến trình adapter. mining.recommend không tự nạp .env; không suy đúng database/credential chỉ vì tệp .env tồn tại. Không ghi giá trị thật, mật khẩu, URI hoặc output theo user vào hồ sơ. Bằng chứng source=dw trong integration_p2 vẫn là lượt lịch sử, không sửa thành lượt mới.

## 5. Bảo toàn và đóng gói chung với P1

Hash byte vật lý trước/sau của receipt, metrics, validation, snapshot và tests giữ nguyên theo test_results.json/cli_aggregate.json. Diff không có thay đổi mining/, tests/, results/ hoặc logic snapshot. Giữ toàn bộ bằng chứng thiếu dữ liệu ban đầu; [manifest.json](manifest.json) của lượt bổ sung tách manifest lịch sử. Rà link, whitespace và dữ liệu riêng tư trước bàn giao.

Bản sửa LF thuộc quy tắc hẹp của P1; P2 gửi evidence/hồ sơ cho P1 đóng gói **một PR chung**, không tạo PR trùng, không tự merge. Hỏi–đáp và kịch bản đã được chấp nhận; kết quả smoke/tổng duyệt mới chờ điều phối review. G4 giữ đúng phạm vi nghiệm thu, G5/gói nộp và slide tổng chưa hoàn thành.
