# PROMPTS_P2 - Nhật Ký Lệnh & Prompt Của Người 2

Tài liệu này lưu lại các yêu cầu, chỉ thị và ngữ cảnh nhận được từ người dùng để đảm bảo bám sát yêu cầu môn học và vai trò Người 2.

---

## 1. Khởi tạo & Bước 0 (Khảo sát hiện trạng)
- **Thời gian**: 2026-10-15 16:38:39 +07:00
- **Nội dung chính**:
  - Nhận hợp đồng dữ liệu chung phiên bản 2 và quy trình GitHub chung.
  - Phân định rõ quyền sở hữu: P2 sở hữu `mining/`, `tests/mining/`, `results/eda/`, `results/mining/`, `docs/P2/`, `docs/agent/steps/P2/`, `*_P2.md` và `data/source_manifest.json`.
  - Thực hiện khảo sát hệ thống, đánh giá năng lực máy đối với MovieLens 1M (K-Means và Item-based CF). Không tạo file ở Bước 0.

---

## 2. Phê duyệt Bước 0 & Chuyển sang Bước 2-P2
- **Thời gian**: 2026-10-15 16:42:29 +07:00
- **Lệnh**:
  > "Tôi đã kiểm tra và duyệt Bước 0 của P2. Ghi nguyên lời duyệt vào REVIEWS_P2.md, cập nhật APPROVED. Đã giải phóng dung lượng ổ cứng. Hãy chuyển sang thực hiện Bước 2 P2: Thiết lập môi trường độc lập."
- **Nhiệm vụ thực hiện trong Bước 2-P2**:
  - Ghi lời duyệt vào `REVIEWS_P2.md`, cập nhật `STATE_P2.md`.
  - Giải quyết nút thắt dung lượng đĩa (đã giải phóng 33GB từ Thùng rác).
  - Tạo nhánh `codex/p2-s02-env`.
  - Thiết lập môi trường ảo `.venv` độc lập với Python 3.12.3.
  - Định nghĩa `docs/P2/requirements-p2.txt` và cài đặt các thư viện khoa học dữ liệu.
  - Viết bài kiểm thử khói (smoke tests) trong `tests/mining/test_env.py` và chạy xác nhận.
  - Viết tài liệu bước `docs/agent/steps/P2/S00_survey.md` và `docs/agent/steps/P2/S02_env_setup.md`.
