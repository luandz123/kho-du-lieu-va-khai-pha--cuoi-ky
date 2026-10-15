# Báo Cáo Bước 0: Khảo Sát Hiện Trạng Máy Người 2 (P2)

- **Mã bước**: `P2-S00`
- **Thời gian thực hiện**: 2026-10-15 16:38:39 +07:00
- **Trạng thái**: `APPROVED` (Phê duyệt lúc 16:42:29 ngày 15/10/2026)

---

## 1. Kết Quả Khảo Sát Kỹ Thuật

- **Hệ điều hành**: Linux Ubuntu 24.04.1 LTS, Kernel `6.14.0-37-generic` x86_64
- **Thư mục làm việc thực tế**: `/home/luan/kho-du-lieu-va-khai-pha--cuoi-ky`
- **Phiên bản Python & Công cụ**:
  - Python: `3.12.3` (`/usr/bin/python3`)
  - Pip: `24.0` (`/usr/bin/pip3`)
  - Git: Nhánh `main`, remote `origin` trỏ về `https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky`
  - PostgreSQL: Client v18.3, daemon đang chạy tại cổng 5432 (chấp nhận kết nối)
- **Tài nguyên phần cứng**:
  - CPU: 13th Gen Intel Core i7-13620H (16 vCPUs)
  - RAM: 15 GiB (Khả dụng: 7.1 GiB)
  - Ổ cứng: Phân vùng `/home` ban đầu có 188GB nhưng chỉ còn trống **771MB** (100% full) do 33GB tệp rác bị giữ trong `~/.local/share/Trash`.

---

## 2. Đánh Giá Khả Năng Xử Lý Ma Trận MovieLens 1M

1. **K-Means (Q1)**: Ma trận hồ sơ người dùng theo thể loại ($6{,}040 \times 18$) chiếm chưa đến $1\text{ MB}$ RAM, thuật toán hội tụ dưới 2 giây.
2. **Item-based CF (Q2)**: Ma trận đánh giá User-Item ($6{,}040 \times 3{,}900$) dạng thưa (sparse) tốn $\sim 16\text{ MB}$; ma trận tương đồng Item-Item ($3{,}900 \times 3{,}900$) dạng dense `float32` tốn $\sim 60.8\text{ MB}$.
3. **Kết luận**: Phần cứng máy Người 2 hoàn toàn vượt mức yêu cầu cho tính toán 100% trong RAM, không gặp hiện tượng tràn bộ nhớ.

---

## 3. Rào Cản & Phương Án Khắc Phục Đã Chốt

- **Rào cản duy nhất**: Đĩa trống 771MB không đủ an toàn để cài đặt thư viện và lưu trữ artifact.
- **Biện pháp khắc phục**: Đã dọn sạch thư mục Thùng rác sau khi nhận được sự đồng ý của người dùng, giải phóng 33GB, nâng dung lượng trống lên ~34GB.
