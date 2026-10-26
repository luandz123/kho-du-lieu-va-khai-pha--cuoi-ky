# Bàn giao chỉnh trước nộp và chuẩn bị demo

Ngày 25/10/2026 — **WAITING_REVIEW**. G4 giữ ĐẠT trong phạm vi I01–I15 và các giới hạn nghiệm thu; G5 chưa hoàn thành.

## Demo 8089

- Đã xác minh hai container metadata/web dừng exit255, OOMKilled=false; Docker Desktop/backend và engine29.1.5 phản hồi. Chưa có bằng chứng xác định nguyên nhân dừng.
- Khởi động đúng hai container hiện hữu bằng docker start; sau đó running/healthy, HTTPhealth200, đăng nhậpAPI thành công và UI mở đủ ba dashboard.
- Run chỉ đọc `3ca533f8a35648e69245fb145f55c271` PASS: Tổng quan toàn kỳ/Q3-2000; Animation2001Q1; Sở thích toàn bộ/cụm1-F-25–34. Engine thực là movielens_bi_reader; SQL độc lập dùng READ ONLY vào movielens_btl.
- Native filter UI đã áp 2001Q1/Animation và cụm1/F/25–34, thấy count1715/prev20068 và assigned170/baseline6038/insufficient2. Cấu hình nghiệp vụ23chart/3dashboard giữ cùng hash trước/sau cả lượt UI. Không Save/Edit.
- Runbook: [demo_preflight.md](demo_preflight.md). Receipt/ảnh/UI observation/completion: [thư mục bằng chứng](../../results/warehouse/demo_preflight_20261025/). Ảnh ở pane hẹp chỉ minh họa; số chính xác từ SQL/API và AX. Log thô ở tmp ignored, không công bố.
- Không recreate/build/upgrade, xóa volume, thay cấu hình/quyền/firewall/dữ liệu, tác động8091/8092 hoặc ETL/restore để chữa UI.

## Báo cáo tổng

Đã tái tạo [DOCX](../report/bao_cao_tong_hop.docx) và [PDF](../report/bao_cao_tong_hop.pdf), **49trang**, 6chương,9hình,25bảng đánh số,15nguồnR. Ba mục lục tự động được cập nhật;40/40mục chương/hình/bảng khớp số trang. Bìa giữ nhãn và dòng trống theo trả lời người dùng nguyên văn “Cứ để trống”; không tự điền trường/khoa, giảng viên, tên/MSSV/lớp.

- Bảng5.5 dùng t₁/t₂; t₁=974862386 và t₂=976422051, kèm UTC tương ứng, được giữ dưới bảng.
- Bảng5.7 bỏ cột dài khỏi bảng chính; ba Recall chưa làm tròn giữ nguyên ở phụ lụcG: 0.02856536704222439 /0.03007556334371585 /0.02866586314500013. Không thay tiêu chí chọnk hoặc giá trị công bố.
- Nguồn chương riêng, công thức, metric và receipt giữ nguyên. Rà caption/thuật ngữ/nguồn; README hiện hành xác nhận đã ghép, không còn câu chờ phầnP2 như trạng thái hiện tại.
- Giữ snapshot24/10 tại docs/report/review_history/ và bản DOCX/PDF trước sửa cục bộ ở tmp/pre_submit_20261025/report_before/.
- Render bằng Word/Poppler; so49ảnh trang:44trang giống pixel bản đã kiểm,5trang đổi1/5/37/38/46 đã xem lại (gồm các trang dồn theo). [Layoutreview](../report/layout_review.json), [staticchecks](../report/static_checks.json). Công cụ render_docx.py vẫn thiếu LibreOffice trênPATH; không cài hệ thống.

Nguồn tạo và cách tái lập ở [docs/report/README.md](../report/README.md). Không chạy ETL/G3/evaluatorTest để biên tập.

## Phối hợp LF với P2

P1 thêm duy nhất dòng `.gitattributes`:

```gitattributes
docs/P2/provenance/eval_original.py text eol=lf
```

P2 phụ trách checkout Windows mới core.autocrlf=true và test. Hồ sơ [windows_newline_verification.md](../P2/provenance/windows_newline_verification.md) và [test_results.json](../P2/provenance/newline_verification_20261025/test_results.json) ghi rõ từng pha, giữ FAIL/PASS lịch sử. P1 đọc hồ sơ và kiểm file chung32508byte,0CRLF,SHA256 `e3fa2efff659de9b248e19d0cda526802113cf9b1ddb438cbad78c109ff5252d`, không diff snapshot. Không sửa checksum/assertion hoặc chuẩn hóa hàng loạt.

Pha nhận đầu: provenance riêng1PASS; nhóm31 có29PASS/2FAIL thiếuCSV; subset fixture/static29PASS/2deselected. Không trình bày pha đó là31/31. P2 sau đó báo nhận lệnh riêng hoàn thiện hai smoke test với canonicalCSV ngoàiGit; kết quả mới phải ghi riêng khi có, không sửa pha FAIL cũ thành PASS. P1 không chạy mô hình hoặc evaluatorTest chính thức. Chỉ có một bản sửa attribute dùng chung, không PRtrùng.

## Diff và Git

Nhánh giữ `codex/p1-s13-final-report`; HEAD `a2021a9f591c56222f5ae16e169f278bf3cec5a7`. Không đổi nhánh/HEAD, stage/commit/push/PR trong lượt sửa. Kế hoạch ngoài phạm vi và công việc P2 song song giữ nguyên.

Thay đổi riêng P1:

- `.gitattributes` (một rule), `dashboard/demo_preflight.py` (hậu kiểm chỉ đọc).
- `docs/P1/demo_preflight.md`, bàn giao này và [diff bản tổng](pre_submit_report_changes_20261025.diff).
- `docs/report/build_report.py`, `check_report.py`, nguồnMD/DOCX/PDF, README, manifest/check/layout JSON; review_history24/10 được giữ.
- README gốc và cập nhật hiện hành trong STATE/DECISIONS/REVIEWS/PROMPTS_P1, S13.
- Bằng chứng tổng hợp/ảnh mới trong results/warehouse/demo_preflight_20261025/.

Các file docs/P2/provenance/defense và bốn hồ sơP2 đang thay đổi doP2 thực hiện, không thuộc diff tác giả P1. Không gom chúng bằng git add toàn workspace. Danh sách/hash chi tiết của lượt P1 được ghi ở audit bàn giao; không đồng nhất diff soHEAD với diff riêng lượt sửa vì đã có công việc G4/bản tổng chưa commit từ trước.

Chưa nộp/chốtG5/tạo slide. Dừng chờ điều phối review.

### Bổ sung nhận bằng chứng P2 ngày 25/10

P1 đã đọc sáu artifact trong `docs/P2/provenance/smoke_rehearsal_20261025/` và đối chiếu SHA-256 với manifest: 6/6 khớp; tám file nguồn/test/receipt được bảo vệ cũng khớp hash P2 ghi. Log mới do P2 chạy ghi 2/2 smoke PASS (30,67 giây), nhóm đầy đủ 31/31 PASS (54,85 giây), không deselect. Aggregate CLI do P2 cung cấp ghi ba ca CSV (evaluation seed, fallback, demo) PASS; không phải lượt DW mới hoặc đánh giá Test chính thức. Đây là kiểm bằng chứng do P2 cung cấp, P1 không chạy lại test/mô hình. Pha thiếu CSV 29 PASS/2 FAIL cũ vẫn được giữ nguyên. Canonical CSV và output theo user giữ ngoài Git. Phần bổ sung này cũng WAITING_REVIEW; chưa có quyền commit/push/PR mới.
