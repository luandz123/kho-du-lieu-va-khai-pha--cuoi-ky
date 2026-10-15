# BTL Kho dữ liệu và Khai phá dữ liệu

MovieLens 1M → PostgreSQL staging/DW → Python ETL → 6 OLAP → K-Means và item-based CF/Popularity Baseline → 3 dashboard Apache Superset. Bảo vệ **27/10/2026**.

## Trạng thái nền G0

Bước 1 đã được người dùng duyệt. **Python 3.12** là dòng phiên bản chung; P2 báo đã có môi trường 3.12.3/Linux, P1 chưa thiết lập 3.12 trong checkout này. `main` là nhánh mặc định. Nhánh G0: `p1-g0-contract`; các nhánh mới không có tiền tố `codex/` theo quyết định nhóm ngày15/10/2026.

G0 đang chuẩn bị cục bộ/chờ duyệt, chưa commit/push/PR/merge. Tài liệu nền không chứng minh ETL, mô hình hoặc dashboard đã chạy. Không cài Docker hoặc làm ETL trong G0.

## Tài liệu cần đọc

- [Đặc tả Q1–Q3 và lịch](docs/project_spec.md)
- [Nghiệm thu nội bộ](docs/acceptance.md) — rubric chính thức chưa xác minh
- [Hợp đồng dữ liệu v2](docs/shared/data_contract.md) và [JSON](docs/shared/data_contract.json)
- [Quy trình GitHub, quyền file và G0–G5](docs/shared/github_workflow.md)

Rating là đánh giá, timestamp là thời điểm đánh giá. Q1 mô tả nhóm sở thích/nhân khẩu học lịch sử; Q2 gợi ý Top5 và đánh giá độc lập; Q3 phân tích count/QoQ theo quý trong dữ liệu. Không suy lượt xem, nhu cầu hiện tại hoặc doanh thu.

## P2 nhận mốc nền sau khi G0 đã merge

Chỉ chạy sau khi xác nhận PR G0 đã merge. Clone vào **thư mục mới chưa tồn tại**, không chép đè checkout đang có thay đổi:

```powershell
git clone https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky.git BTL_MovieLens_P2
cd BTL_MovieLens_P2
git switch main
git pull --ff-only origin main
git log -1 --oneline
```

Nếu P2 đã có checkout riêng (đã có PR môi trường), giữ checkout đó: kiểm tra `git status`, bảo toàn thay đổi trên nhánh P2 rồi fetch/pull hoặc merge `origin/main` khi sạch; không clone đè và không tự reset. Sau đồng bộ, đọc/xác nhận contract2 theo commit G0 đã merge. Chỉ bắt đầu EDA khi contract được cả hai xác nhận và có lệnh giao bước3; tạo nhánh mới, ví dụ `p2-s03-eda`, từ main mới nhất. Giữ nguyên PR môi trường đang chờ review, không tự merge PR đó.

## Cấu hình và dữ liệu cục bộ

`.env.example` chỉ là mẫu không bí mật, chưa dùng để kết nối hoặc tạo database. Việc tạo `.env`/`.venv`, cài dependency và kiểm tra SQL thuộc bước thiết lập được giao sau. Không chuyển nguyên `.venv` giữa máy/checkouts.

Mỗi máy tự tải MovieLens từ nguồn chính thức và đối soát hash theo contract. Không đưa raw/processed, dữ liệu theo user, gói cụm, mô hình lớn, dump, metadata/volume Superset hoặc export có connection URI lên Git/Release/Artifact. `.gitignore` mặc định chặn CSV/ZIP; kết quả tổng hợp và export dashboard chỉ được cho phép có chọn lọc sau rà soát ở mốc liên quan.

## Phân vai và quyền thực hiện

P1: DW/ETL/OLAP/Superset và ghép tổng. P2: EDA/K-Means/CF/baseline/metric/CLI. P2 quản lý `docs/P2/requirements-p2.txt`, không sửa requirements gốc. P1 chỉ hợp nhất dependency tại12A sau kiểm chứng; không sao chép pin P2 thành thư viện đã chạy trên P1.

Sau duyệt và lệnh **Đẩy G0**, commit/push nhánh rồi mở PR vào main. Merge cần xác nhận cụ thể; không push thẳng main, force-push, đổi remote hoặc xóa nhánh. APPROVED chức năng khác PR MERGED.
