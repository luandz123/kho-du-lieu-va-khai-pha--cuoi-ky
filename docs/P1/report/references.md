# Danh mục tài liệu tham khảo chung

Danh mục dùng cho chương 1, 3, 4 và để P2 bổ sung cho chương 2, 5, 6. Mã R là nguồn bên ngoài; mã I và E là tài liệu, bằng chứng nội bộ. Ngày tra cứu nguồn trực tuyến: 24/10/2026. Chưa áp một thể thức trích dẫn bắt buộc khi chưa nhận mẫu chính thức.

## A. Nguồn dữ liệu và nghiên cứu gốc

**R01.** GroupLens Research. *MovieLens 1M Dataset*. [Trang bộ dữ liệu](https://grouplens.org/datasets/movielens/1m/); [README chính thức](https://files.grouplens.org/datasets/movielens/ml-1m-README.txt). Dùng để xác định nguồn, ngữ nghĩa trường và điều kiện sử dụng. README được truy cập; trang giới thiệu được tìm thấy nhưng lần mở trực tiếp bị timeout. Số liệu snapshot chính xác trong báo cáo đối chiếu manifest/EDA của dự án, không thay bằng con số xấp xỉ trên trang giới thiệu.

**R02.** Harper, F. Maxwell và Konstan, Joseph A. (2015). *The MovieLens Datasets: History and Context*. ACM Transactions on Interactive Intelligent Systems, 5(4), Article 19. [DOI:10.1145/2827872](https://doi.org/10.1145/2827872); [bản tác giả tại GroupLens](https://files.grouplens.org/papers/harper-tiis2015.pdf). Tài liệu nền về lịch sử và bối cảnh sử dụng MovieLens. Bản tác giả có metadata xuất bản tạm; không sao chép DOI placeholder của PDF. Không dùng bài này làm bằng chứng metric do nhóm đo.

**R03.** Sarwar, Badrul; Karypis, George; Konstan, Joseph; Riedl, John (2001). *Item-Based Collaborative Filtering Recommendation Algorithms*. Proceedings of WWW10. [Bản tại GroupLens](https://files.grouplens.org/papers/www10_sarwar.pdf); [bản proceedings HTML](https://www.ra.ethz.ch/CDstore/www10/papers/519/). Tài liệu nền cho hướng item-based CF; không đồng nhất mọi lựa chọn similarity, split hoặc metric trong bài gốc với cấu hình cụ thể của đồ án.

## B. Tài liệu chính thức của phần mềm

**R04.** scikit-learn developers. *KMeans — scikit-learn 1.5.2 documentation*. [Tài liệu lớp KMeans](https://scikit-learn.org/1.5/modules/generated/sklearn.cluster.KMeans.html). Dùng tra tham số và hành vi thư viện đúng dòng phiên bản; K/seed/n_init thực dùng lấy từ cấu hình và artifact P2.

**R05.** scikit-learn developers. *silhouette_score — scikit-learn 1.5.2 documentation*. [Tài liệu silhouette_score](https://scikit-learn.org/1.5/modules/generated/sklearn.metrics.silhouette_score.html). Dùng tra định nghĩa/tham số metric; mẫu 2.000 user và giá trị thực nghiệm phải dẫn artifact P2, không suy từ ví dụ tài liệu.

**R06.** PostgreSQL Global Development Group. *PostgreSQL 17 Documentation, 3.4 Transactions*. [Tài liệu transaction](https://www.postgresql.org/docs/17/tutorial-transactions.html). Nguồn khái niệm transaction; kết quả rollback/full refresh của dự án dẫn I03/I05.

**R07.** PostgreSQL Global Development Group. *PostgreSQL 17 Documentation: pg_dump*. [Tài liệu pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html). Dùng tra phạm vi backup và tùy chọn; phiên bản công cụ, snapshot và checksum dump thực nằm trong receipt nội bộ.

**R08.** PostgreSQL Global Development Group. *PostgreSQL 17 Documentation: pg_restore*. [Tài liệu pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html). Dùng tra phục hồi archive và transaction; không thay bằng chứng restore đã chạy hoặc kết luận ACL của clone.

**R09.** Apache Software Foundation. *Apache Superset — Dashboards API*. [API dashboard](https://superset.apache.org/developer-docs/api/dashboards/). Nguồn giao diện API chính thức, gồm export/import. Tài liệu website là bản cập nhật liên tục, không được gọi là snapshot tài liệu 6.1.0.

**R10.** Apache Software Foundation. *Apache Superset — Importing and Exporting Datasources*. [Tài liệu import/export](https://superset.apache.org/admin-docs/configuration/importing-exporting-datasources/). Website hiển thị Version: Next tại lần tra cứu; chỉ dùng tham khảo cơ chế chung. Instance thực dùng Superset 6.1.0 và kết quả ZIP/REST layout, metadata restore được dẫn artifact nội bộ, không suy từ tài liệu Next rằng bản đang chạy hỗ trợ mọi tính năng mới.

## C. Tài liệu và artifact nội bộ

Các mục dưới do nhóm tạo trong repository, không phải nguồn học thuật độc lập hoặc yêu cầu chính thức của giảng viên.

**I01.** Nhóm đồ án. [Đặc tả](../../project_spec.md), [tiêu chí nghiệm thu nội bộ](../../acceptance.md), [hợp đồng dữ liệu v2](../../shared/data_contract.md), [quy trình GitHub](../../shared/github_workflow.md). Căn cứ phạm vi và giao diện. Các dòng trạng thái cũ đọc theo cập nhật hiện hành, không sửa lịch sử để tạo xác nhận mới.

**I02.** P2. [Source manifest](../../../data/source_manifest.json), [canonical manifest](../../../results/eda/canonical_manifest.json), [data profile](../../../results/eda/data_profile.csv), [data understanding](../../P2/data_understanding.md). Bằng chứng nguồn và EDA, tương ứng E02–E04.

**I03.** P1. [Schema](../../../database/schema.sql), [ERD](../../../database/erd.md), [summary6D](../../../results/warehouse/s06d_summary.json), [OLAP findings](../olap_findings.md) và report được dẫn. Tài liệu thiết kế và kiểm chứng DW/ETL/OLAP, tương ứng E05–E11.

**I04.** P2. [Clustering summary](../../../results/mining/clustering_summary.json), [split manifest](../../../results/mining/split_manifest.json), [receipt Test chính thức](../../../results/mining/cf_test_evaluation_receipt.json). Kết quả Q1/Q2 đã công bố; không chạy lại evaluator để viết báo cáo, tương ứng E12–E16.

**I05.** P1. [Chỉ mục E01–E20](../report_evidence_index.md), [phụ lục truy vết](appendix_sources.md), [summary12A](../../../results/warehouse/s12a/57c1e8e3d3f445c4b3eeddbfc3364709/summary.json), [ghi nhận P2 qua điều phối](../p2_intake_reported_20261024.json). Phân biệt kết quả P1, thông tin P2 báo cáo và G4 chưa nghiệm thu.

## D. Quy tắc dùng trong bản tổng

Nguồn R hỗ trợ khái niệm, nguồn dữ liệu và cơ chế phần mềm; không chứng minh số liệu đo của nhóm. Bảng/hình/số liệu thực nghiệm phải dẫn I/E và artifact/run tương ứng. Chỉ đưa các mục thực sự dùng vào bản tổng; P2 bổ sung nguồn phương pháp cho chương của mình qua phần được giao, P1 không sửa file P2. Danh mục này chưa phải xác nhận báo cáo tổng đã hoàn thành.
