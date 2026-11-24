# Tài liệu

## Sản phẩm nộp

| Tài liệu | Nội dung |
|---|---|
| [report/bao_cao_kho_du_lieu_khai_pha.pdf](report/bao_cao_kho_du_lieu_khai_pha.pdf) ([DOCX](report/bao_cao_kho_du_lieu_khai_pha.docx)) | Báo cáo đầy đủ, 87 trang. Chương 1–4: bản nền tảng; chương 5: bản nâng cấp |
| [slides/movie_platform_nang_cap.pptx](slides/movie_platform_nang_cap.pptx) | Slide trình bày bản nâng cấp (5 phút), lời nói trong phần Notes |
| [movie_platform_dataflow.png](movie_platform_dataflow.png) | Sơ đồ luồng dữ liệu bản nâng cấp (bản SVG: [diagram/](diagram/)) |

## Bản nâng cấp

| Tài liệu | Nội dung |
|---|---|
| [ban_nang_cap.md](ban_nang_cap.md) | So sánh với bản cũ, cách khởi động trước khi trình bày, kịch bản demo 5 phút, câu hỏi thường gặp |
| [demo/kich_ban_video.md](demo/kich_ban_video.md) | Kịch bản video 15 phút (bản cắt 5 phút), mỗi chương kèm câu hỏi thầy có thể hỏi và đáp án; phụ lục câu hỏi khó, bảng số liệu, bảng khái niệm |
| [demo/README.md](demo/README.md) | Các script quay video demo |
| [ke_hoach_chi_tiet.md](ke_hoach_chi_tiet.md) | Kế hoạch từng công đoạn: làm gì, cần hiểu gì, kiểm tra gì |
| [nguon_du_lieu.md](nguon_du_lieu.md) | Khảo sát các nguồn dữ liệu (kiểm tra truy cập thực tế từ Việt Nam) |
| [ke_hoach_nang_cap.md](ke_hoach_nang_cap.md) | Kế hoạch ban đầu (trước khi khảo sát nguồn; TMDB sau đó được thay bằng IMDb và Wikipedia) |

## Báo cáo, slide: mã nguồn dựng

| Thư mục | Nội dung |
|---|---|
| [report/noi_dung/](report/noi_dung/) | Nội dung báo cáo dạng Markdown, mỗi chương một tệp |
| [report/build_report.py](report/build_report.py) | Dựng DOCX và PDF, tự đánh số mục lục, danh mục hình, bảng |
| [report/make_figures.py](report/make_figures.py), [report/make_figures_nang_cap.py](report/make_figures_nang_cap.py) | Vẽ biểu đồ, sơ đồ cho báo cáo |
| [slides/build_slides.js](slides/build_slides.js) | Dựng slide bằng pptxgenjs |
| [diagram/make_dataflow.py](diagram/make_dataflow.py) | Vẽ sơ đồ luồng dữ liệu |

## Bản nền tảng (giai đoạn 1)

| Tài liệu | Nội dung |
|---|---|
| [shared/data_contract.md](shared/data_contract.md) | Hợp đồng dữ liệu giữa phần kho và phần khai phá |
| [project_spec.md](project_spec.md), [acceptance.md](acceptance.md) | Đặc tả và tiêu chí nghiệm thu nội bộ |
| [P1/olap_findings.md](P1/olap_findings.md) | Kết quả OLAP chi tiết |
| [P2/clustering_interpretation.md](P2/clustering_interpretation.md), [P2/evaluation_protocol.md](P2/evaluation_protocol.md) | Diễn giải phân cụm, giao thức đánh giá gợi ý |
| [../database/](../database/) | Từ điển dữ liệu, ánh xạ nguồn – đích, đối soát |

Các thư mục `P1/`, `P2/`, `agent/`, `shared/` và các tệp `integration_checklist.md`, `report_outline.md` là **hồ sơ quá trình làm việc của giai đoạn 1** (bàn giao từng bước, bằng chứng kiểm tra, nhật ký). Chúng được giữ nguyên vì một số chương trình ETL và kiểm thử của bản nền tảng đọc trực tiếp các tệp JSON trong đó (`docs/P1/s04_*.json`, `docs/shared/data_contract.json`, `docs/P2/provenance/`); trạng thái ghi trong các tệp này là trạng thái tại thời điểm viết, không phải hiện tại.
