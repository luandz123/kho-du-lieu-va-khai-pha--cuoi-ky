# REVIEWS_P2 - Nhật Ký Duyệt Của Người 2

Tài liệu này lưu trữ nguyên văn mọi phản hồi, phê duyệt từ Người dùng cho vai trò Người 2 (P2 - Khai phá dữ liệu & EDA). Tuyệt đối không tự tạo hoặc chỉnh sửa lời duyệt.

---

## 1. Duyệt Bước 0: Khảo sát hiện trạng

- **Thời điểm**: 2026-10-15 16:42:29 +07:00
- **Trạng thái**: `APPROVED`
- **Lời duyệt nguyên văn**:
> "Tôi đã kiểm tra và duyệt Bước 0 của P2. Ghi nguyên lời duyệt vào REVIEWS_P2.md, cập nhật APPROVED. Đã giải phóng dung lượng ổ cứng. Hãy chuyển sang thực hiện Bước 2 P2: Thiết lập môi trường độc lập."
- **Hành động tiếp theo**:
  - Xác nhận giải phóng 33GB đĩa từ Thùng rác (`~/.local/share/Trash`), nâng dung lượng khả dụng lên ~34GB.
  - Khởi tạo bộ hồ sơ agent cho P2 (`STATE_P2.md`, `DECISIONS_P2.md`, `REVIEWS_P2.md`, `PROMPTS_P2.md`).
  - Chuyển sang Bước 2-P2: Thiết lập môi trường ảo `.venv`, tạo `docs/P2/requirements-p2.txt`, cài đặt dependencies và kiểm thử smoke test.

---

## 2. Duyệt Bước 2-P2: Thiết lập môi trường độc lập

- **Thời điểm**: 2026-10-15 17:21:25 +07:00
- **Trạng thái**: `APPROVED`
- **Lời duyệt nguyên văn**:
> "Tôi đã kiểm tra và duyệt Bước 2-P2. Ghi nguyên văn lời duyệt này vào REVIEWS_P2.md, cập nhật Bước 2 thành APPROVED trong STATE_P2.md.
> 
> Đẩy mốc Bước 2-P2 theo docs/shared/github_workflow.md trên main:
> 1. Kiểm tra git status, git remote -v; xác nhận đang ở nhánh codex/p2-s02-env (giữ nguyên tên nhánh này, không đổi tên, không force-push).
> 2. Chạy lại pytest tests/mining/test_env.py, xem git diff.
> 3. Stage từng đường dẫn thuộc quyền P2, không dùng git add . Xem git diff --cached và danh sách file; đảm bảo không có .venv, data, .env.
> 4. Commit, push -u origin codex/p2-s02-env, mở PR vào main.
> 5. Chỉ ghi link PR và commit vào hồ sơ S02 sau khi lệnh thành công. Nếu lỗi xác thực, báo rõ thiếu gì.
> 
> Không merge, không đẩy thẳng main. Đặt WAITING_REVIEW cho việc merge PR và dừng."
- **Hành động tiếp theo**:
  - Cập nhật trạng thái Bước 2-P2 thành `APPROVED` (chức năng).
  - Thực hiện quy trình đẩy mốc Git: kiểm tra trạng thái, chạy lại pytest, stage từng file thuộc P2, commit, push nhánh `codex/p2-s02-env` và tạo PR vào `main`.
  - Cập nhật commit SHA và PR link vào `S02_env_setup.md`.
  - Đặt trạng thái `WAITING_REVIEW` cho việc merge PR và dừng.

---

## 3. Duyệt Bước 3A-P2: Nhận mốc G0 và xác nhận Hợp đồng dữ liệu v2

- **Thời điểm**: 2026-10-15 17:38:48 +07:00
- **Trạng thái**: `APPROVED`
- **Lời duyệt nguyên văn**:
> "Tôi đã kiểm tra và duyệt Bước 3A, hợp đồng dữ liệu v2 đã được P2 xác nhận. Ghi nguyên văn lời duyệt này vào REVIEWS_P2.md, cập nhật 3A thành APPROVED trong STATE_P2.md.
> 
> Chuyển sang Bước 3B-P2: tải nguồn, source_manifest và EDA, trên nhánh p2-s03-eda. Chỉ làm 3B, không tự chuyển bước.
> 
> A. Tải MovieLens 1M từ GroupLens vào data/raw (không commit). Tính SHA-256 và số dòng từng tệp. Tạo data/source_manifest.json: dataset_version, URL nguồn, ngày tải UTC, encoding, SHA-256, số dòng.
> 
> B. EDA theo hợp đồng v2: ID duy nhất của users/movies, khóa (movie_id, genre_name), trùng (user_id, movie_id) trong ratings, rating thuộc 1..5, khóa tham chiếu tồn tại, parse release_year, ánh xạ age_group, rated_at theo UTC ISO 8601.
> Nếu phát hiện trùng hoặc lỗi nguồn: DỪNG, báo cáo, không tự chọn chính sách làm sạch.
> 
> C. Nếu dữ liệu sạch: xuất bốn bảng chuẩn ra data/processed theo đúng quy tắc tuần tự hóa và thứ tự sắp xếp; tạo results/eda/canonical_manifest.json (contract_version, schema, row_count, hash bốn bảng, tập mã nguồn). Mã trong mining/, test trong tests/mining/, kết quả tổng hợp trong results/eda/.
> 
> D. Ghi quyết định "genre_order theo thứ tự A–Z" vào DECISIONS_P2.md. Ghi hồ sơ S03B, cập nhật STATE_P2. Bàn giao: việc đã làm, file, cách chạy, kiểm tra và bằng chứng thật, lỗi và giới hạn, 3–5 ý bảo vệ, nội dung cần duyệt. Đặt WAITING_REVIEW và dừng."
- **Hành động tiếp theo**:
  - Cập nhật Bước 3A thành `APPROVED` trong `STATE_P2.md`.
  - Bổ sung quyết định `[DEC-P2-007]` vào `DECISIONS_P2.md`.
  - Triển khai Bước 3B-P2 trên nhánh `p2-s03-eda`.


## Nghiệm thu 12B / G4 và giao 13-P2 — 24/10/2026

Nguồn: thông điệp điều phối do người dùng chuyển trong phiên giao Bước 13-P2. Lời nghiệm thu nguyên văn:

> Điều phối đã nghiệm thu 12B và chốt G4 ĐẠT ngày 24/10/2026
> trong phạm vi đã kiểm. Giao thực hiện Bước 13-P2:
> viết chương 2, 5, 6 theo docs/report_outline.md.

Ghi nhận G4 ĐẠT đúng phạm vi ma trận P1/P2 đã kiểm. Trạng thái Git kiểm riêng: origin/main đã chứa PR30 merge tại `67fd9eb6b98211485b713c99e829291bc3b50f57`. Không thay candidate `4546d5bbd8f9130a420518b77dc3ad894bc7f42b` hoặc sửa ngược receipt/snapshot P1.

Phạm vi giao 13-P2: bản thảo chương 2/5/6 và references, cập nhật hồ sơ P2, WAITING_REVIEW; chưa commit/push/PR; không pipeline/evaluator, không thay receipt, không sửa phần P1, không DOCX tổng. G5/gói nộp chưa hoàn thành. Chưa có lời duyệt bản thảo 13-P2.


## Chấp nhận nội dung 13-P2 và giao chỉnh biên tập/công bố — 24/10/2026

Nguồn: thông điệp điều phối do người dùng chuyển trong phiên tiếp nối. Trích nguyên văn:

> Điều phối chấp nhận nội dung chính chương 2/5/6.
> Giao chỉnh biên tập và công bố PR phần báo cáo P2.

Lệnh hiện hành cho phép commit/push nhánh `codex/p2-s13-report` và mở PR vào main sau chỉnh biên tập; không tự merge. Tạm bỏ PCA/tỷ lệ phương sai khỏi bản chính, giữ ảnh và mâu thuẫn trong editorial_notes; chuyển nhật ký review/trạng thái/việc ghép ra hồ sơ; sửa nhãn cohort; bỏ so sánh biểu diễn chưa có hỗ trợ. Không đổi công thức, metric, receipt, artifact, nguồn dẫn hoặc phần P1, không chạy mô hình/evaluator. G4 đạt đúng phạm vi, G5 chưa hoàn thành. Nội dung chính được chấp nhận không đồng nghĩa PR đã merge hoặc G5 hoàn thành.


## Giao kiểm snapshot LF trên Windows và chuẩn bị hỏi–đáp — 25/10/2026

Nguồn: điều phối qua thông điệp người dùng. Lượt rà điều phối báo 118/119 test, lỗi test_evaluator_provenance_trace_artifact_integrity do CRLF; snapshot LF blob được nghiệm thu không sai nội dung. P1 được giao thêm attribute đúng đường dẫn, P2 kiểm fresh checkout autocrlf=true và test fixture/mock, giữ log trước/sau, không đổi logic/assertion/checksum/receipt/metric. Không ETL/mô hình dữ liệu thật/evaluator Test chính thức hoặc PR trùng.

Người dùng xác nhận phần chương 2/5/6 đã được điều phối duyệt; trạng thái merge kiểm riêng từ Git: PR31 đã merge tại `a2021a9f591c56222f5ae16e169f278bf3cec5a7`. P2 ghi hiện hành APPROVED / PR31 MERGED, không sửa lịch sử thành lượt thực nghiệm mới. Phần LF/CRLF và hỏi–đáp/CLI hiện WAITING_REVIEW, chưa có lời nghiệm thu mới; G4 đạt trong phạm vi đã kiểm, G5 chưa hoàn thành.


## Chấp nhận LF / hỏi–đáp và giao smoke test, tổng duyệt suy luận — 25/10/2026

Nguồn: thông điệp điều phối do người dùng chuyển. Trích nguyên văn:

> Điều phối chấp nhận bản sửa LF và nội dung hỏi–đáp/kịch bản CLI.

Điều phối cho phép dùng bốn canonical CSV đã kiểm hash ngoài Git trong checkout LF để chạy hai test còn thiếu, được dựng mô hình suy luận trong bộ nhớ và tổng duyệt CLI evaluation/demo. Đây không phải đánh giá lại Test chính thức. Không gọi cf_test_evaluation.py/eval_original.py làm evaluator, không tính metric Test, tune k, sửa receipt/assertion hoặc mock checksum. Giữ log thiếu dữ liệu trước; chỉ báo 31/31 sau khi chạy đủ và đạt thật. Kịch bản DW phải ghi rõ PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD cấu hình riêng cho adapter, không tự đọc .env, không công bố bí mật/output theo user.

LF và nội dung hỏi–đáp/kịch bản đã được chấp nhận. Kết quả thực chạy bổ sung được ghi riêng tại docs/P2/provenance/smoke_rehearsal_20261025/ để điều phối review, không sửa log/checkpoint cũ. Phối hợp P1 một PR chung, P2 không mở PR trùng hoặc tạo slide tổng. G4 đạt đúng phạm vi, G5 chưa hoàn thành.
