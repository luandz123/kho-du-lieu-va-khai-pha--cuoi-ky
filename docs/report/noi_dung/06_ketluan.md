@chapter KẾT LUẬN

## 1. Kết quả đạt được

Đề tài đã xây dựng một hệ thống phân tích hoàn chỉnh trên bộ dữ liệu MovieLens 1M, kết hợp kho dữ liệu, phân tích OLAP và khai phá dữ liệu trên cùng một nền dữ liệu đã được đối soát, sau đó nâng cấp thành một nền tảng dữ liệu nhiều nguồn cập nhật gần thời gian thực. Các kết quả chính gồm:

- **Về kho dữ liệu:** thiết kế lược đồ sao với grain một lượt đánh giá, bảng cầu nối phim – thể loại, chiều thời gian chuẩn hóa UTC và hệ thống ràng buộc toàn vẹn; quy trình ETL nạp toàn bộ trong một giao dịch, đối soát nhiều chỉ số (số dòng, tổng điểm, phân bố, khóa, mã băm) trước khi xác nhận; kết quả lặp lại giống hệt nhau qua nhiều lần chạy và trên hai máy khác nhau.
- **Về OLAP và trực quan hóa:** sáu truy vấn OLAP minh họa đầy đủ các thao tác roll-up, drill-down, slice, dice và pivot với nguyên tắc tính trung bình có trọng số; ba dashboard Tổng quan, Xu hướng và Sở thích trên Apache Superset, được đối chiếu với SQL độc lập và truy cập bằng tài khoản chỉ đọc.
- **Về khai phá dữ liệu:** phân cụm K-Means chia người dùng thành bốn nhóm sở thích ổn định; mô hình item-based CF vượt mô hình cơ sở theo độ phổ biến trên tập kiểm tra, trong một quy trình đánh giá không rò rỉ dữ liệu tương lai; mô hình lai và tìm phim bằng câu tiếng Việt dựa trên embedding đa ngôn ngữ.
- **Về nền tảng dữ liệu (bản nâng cấp):** tích hợp bảy nguồn với bốn kiểu nạp (tệp, API, CDC, streaming) và ghép được 98% phim MovieLens với IMDb; CDC bằng Debezium đọc WAL, truyền qua Kafka với consumer at-least-once; data lake MinIO ba tầng xử lý bằng DuckDB; kho nạp tăng dần bằng watermark và upsert, có SCD loại 2, xóa mềm, bốn loại bảng sự kiện và chín kiểm tra chất lượng; Airflow điều phối ba DAG; ứng dụng web và dashboard tự làm mới mỗi 60 giây.

Bốn câu hỏi nghiên cứu được trả lời như sau:

- **Q1:** Người dùng được chia thành bốn nhóm sở thích: đánh giá đa dạng (41,0%), thiên về Drama và tình cảm (23,1%), thiên về hài (12,6%) và thiên về hành động, viễn tưởng (23,3%). Nhóm hành động, viễn tưởng có tỷ lệ nam 87,4%, trong khi nhóm Drama và tình cảm có tỷ lệ nữ và người từ 56 tuổi trở lên cao hơn rõ rệt so với mặt bằng chung.
- **Q2:** Item-based CF với 40 láng giềng đạt Precision@5 = 0,231 và Recall@5 = 0,0353 trên 1.154 người dùng của tập test, cao hơn Popularity Baseline (0,202 và 0,0271); trung bình mỗi danh sách 5 phim có khoảng 1,15 phim người dùng thực sự yêu thích sau đó.
- **Q3:** Hoạt động đánh giá tập trung trong năm 2000 (đỉnh 446.574 lượt ở quý 4) rồi giảm mạnh từ năm 2001. Animation tăng mạnh nhất quý 4 năm 2000 (+53,17%); từ năm 2001, chỉ Western và Horror có quý tăng trưởng dương. Kết quả cho thấy thứ hạng tăng trưởng luôn cần được đọc kèm dấu, giá trị tuyệt đối và tỷ trọng.
- **Q4:** Bằng CDC dựa trên log, Kafka, data lake ba tầng và nạp tăng dần có upsert, một lượt chấm điểm trên ứng dụng đi vào kho dữ liệu sau khoảng 40 giây, không trùng lặp dù consumer có thể ghi lặp; thao tác xóa và đổi thông tin người dùng được phản ánh đúng bằng xóa mềm và SCD loại 2, được kiểm chứng bởi chín kiểm tra chất lượng. Các nguồn mới còn đem lại giá trị cho khai phá: mô hình gợi ý chỉ dùng mô tả phim từ Wikipedia và IMDb đạt Precision@5 = 0,2175, vượt mô hình cơ sở theo độ phổ biến; mô hình lai ngang với CF trên chỉ số offline.

Qua đề tài, nhóm đã vận dụng được kiến thức của cả hai phần môn học vào một bài toán thực tế, đồng thời rèn luyện kỹ năng làm việc nhóm qua Git và GitHub, kiểm thử tự động và đối soát kết quả.

## 2. Hạn chế

Bên cạnh các kết quả đạt được, đề tài còn một số hạn chế:

- **Về dữ liệu:** MovieLens 1M là dữ liệu lịch sử từ năm 2000 đến 2003 của những người tự nguyện tham gia, phân bố thời gian rất không đều; các kết quả mang tính mô tả trên bộ dữ liệu này và không đại diện cho thị trường phim hiện nay.
- **Về phân cụm:** hệ số Silhouette của cấu hình được chọn ở mức thấp (0,186), cho thấy ranh giới giữa các nhóm sở thích không rõ ràng tuyệt đối; các khác biệt nhân khẩu học chưa được kiểm định thống kê.
- **Về gợi ý:** mô hình lai chưa cải thiện được chỉ số offline so với CF; quy trình chỉ đánh giá trên một cách chia dữ liệu, chưa có kiểm định ý nghĩa thống kê, chưa đo các tiêu chí như độ đa dạng, độ mới của gợi ý. Người dùng có ít lịch sử (dưới 5 lượt) không nằm trong tập đánh giá.
- **Về nền tảng dữ liệu:** toàn bộ dịch vụ chạy trên một máy bằng Docker Compose, chưa có cơ chế sẵn sàng cao; `fact_rating` giữ trạng thái hiện tại nên chưa lưu lịch sử từng lần chấm lại; dữ liệu của ứng dụng xem phim là thao tác thử nghiệm của nhóm, quy mô nhỏ; micro-batch 10 giây sinh nhiều tệp nhỏ ở tầng bronze, chưa có bước gộp tệp; replication slot giữ WAL khi Debezium dừng lâu, cần giám sát độ trễ để tránh đầy ổ đĩa.

## 3. Hướng phát triển

Trong thời gian tới, đề tài có thể được mở rộng theo các hướng:

- Áp dụng cho bộ dữ liệu lớn hơn và mới hơn như MovieLens 25M; bổ sung bảng sự kiện giao dịch lưu mọi lần chấm điểm từ CDC.
- Thử nghiệm thêm các thuật toán phân cụm khác (Gaussian Mixture, phân cụm phân cấp) và các thuật toán gợi ý khác (phân rã ma trận, mô hình lai kết hợp thông tin thể loại để giải quyết vấn đề phim mới).
- Đánh giá gợi ý trên nhiều mốc chia thời gian, bổ sung khoảng tin cậy và các chỉ số độ phủ, độ đa dạng.
- Khai phá luật kết hợp giữa các thể loại hoặc các phim được yêu thích cùng nhau.
- Triển khai nền tảng trên nhiều máy (Kafka nhiều broker, lưu trữ đối tượng phân tán), bổ sung giám sát độ trễ replication slot và consumer lag, gộp tệp nhỏ định kỳ ở data lake; chuyển tầng silver, gold sang định dạng bảng mở (Apache Iceberg, Delta Lake) để có giao dịch và du hành thời gian trên data lake.

@chapter TÀI LIỆU THAM KHẢO

[1] F. M. Harper and J. A. Konstan, “The MovieLens datasets: History and context,” *ACM Transactions on Interactive Intelligent Systems*, vol. 5, no. 4, Art. 19, 2015.

[2] GroupLens Research, “MovieLens 1M Dataset,” University of Minnesota. [Trực tuyến]. https://grouplens.org/datasets/movielens/1m/

[3] R. Kimball and M. Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling*, 3rd ed. Indianapolis, IN, USA: Wiley, 2013.

[4] W. H. Inmon, *Building the Data Warehouse*, 4th ed. Indianapolis, IN, USA: Wiley, 2005.

[5] J. Han, M. Kamber, and J. Pei, *Data Mining: Concepts and Techniques*, 3rd ed. Waltham, MA, USA: Morgan Kaufmann, 2011.

[6] The PostgreSQL Global Development Group, “PostgreSQL 17 Documentation.” [Trực tuyến]. https://www.postgresql.org/docs/17/

[7] E. F. Codd, S. B. Codd, and C. T. Salley, “Providing OLAP (On-Line Analytical Processing) to user-analysts: An IT mandate,” E. F. Codd & Associates, White paper, 1993.

[8] J. Gray, S. Chaudhuri, A. Bosworth, A. Layman, D. Reichart, M. Venkatrao, F. Pellow, and H. Pirahesh, “Data cube: A relational aggregation operator generalizing group-by, cross-tab, and sub-totals,” *Data Mining and Knowledge Discovery*, vol. 1, no. 1, pp. 29–53, 1997.

[9] C. Shearer, “The CRISP-DM model: The new blueprint for data mining,” *Journal of Data Warehousing*, vol. 5, no. 4, pp. 13–22, 2000.

[10] J. MacQueen, “Some methods for classification and analysis of multivariate observations,” in *Proc. 5th Berkeley Symposium on Mathematical Statistics and Probability*, vol. 1, 1967, pp. 281–297.

[11] D. Arthur and S. Vassilvitskii, “k-means++: The advantages of careful seeding,” in *Proc. 18th Annual ACM-SIAM Symposium on Discrete Algorithms (SODA)*, 2007, pp. 1027–1035.

[12] P. J. Rousseeuw, “Silhouettes: A graphical aid to the interpretation and validation of cluster analysis,” *Journal of Computational and Applied Mathematics*, vol. 20, pp. 53–65, 1987.

[13] L. Hubert and P. Arabie, “Comparing partitions,” *Journal of Classification*, vol. 2, no. 1, pp. 193–218, 1985.

[14] F. Ricci, L. Rokach, and B. Shapira, Eds., *Recommender Systems Handbook*, 3rd ed. New York, NY, USA: Springer, 2022.

[15] B. Sarwar, G. Karypis, J. Konstan, and J. Riedl, “Item-based collaborative filtering recommendation algorithms,” in *Proc. 10th International Conference on World Wide Web (WWW)*, 2001, pp. 285–295.

[16] G. Linden, B. Smith, and J. York, “Amazon.com recommendations: Item-to-item collaborative filtering,” *IEEE Internet Computing*, vol. 7, no. 1, pp. 76–80, 2003.

[17] P. Cremonesi, Y. Koren, and R. Turrin, “Performance of recommender algorithms on top-N recommendation tasks,” in *Proc. 4th ACM Conference on Recommender Systems (RecSys)*, 2010, pp. 39–46.

[18] J. L. Herlocker, J. A. Konstan, L. G. Terveen, and J. T. Riedl, “Evaluating collaborative filtering recommender systems,” *ACM Transactions on Information Systems*, vol. 22, no. 1, pp. 5–53, 2004.

[19] P. G. Campos, F. Díez, and I. Cantador, “Time-aware recommender systems: A comprehensive survey and analysis of existing evaluation protocols,” *User Modeling and User-Adapted Interaction*, vol. 24, no. 1–2, pp. 67–119, 2014.

[20] F. Pedregosa *et al.*, “Scikit-learn: Machine learning in Python,” *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.

[21] The Apache Software Foundation, “Apache Superset Documentation.” [Trực tuyến]. https://superset.apache.org/docs/

[22] M. Kleppmann, *Designing Data-Intensive Applications*. Sebastopol, CA, USA: O’Reilly Media, 2017.

[23] Debezium Community, “Debezium Documentation – PostgreSQL Connector.” [Trực tuyến]. https://debezium.io/documentation/

[24] J. Kreps, N. Narkhede, and J. Rao, “Kafka: A distributed messaging system for log processing,” in *Proc. 6th International Workshop on Networking Meets Databases (NetDB)*, 2011.

[25] The Apache Software Foundation, “Apache Kafka Documentation.” [Trực tuyến]. https://kafka.apache.org/documentation/

[26] M. Armbrust, A. Ghodsi, R. Xin, and M. Zaharia, “Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics,” in *Proc. 11th Conference on Innovative Data Systems Research (CIDR)*, 2021.

[27] Databricks, “What is the medallion lakehouse architecture?” [Trực tuyến]. https://docs.databricks.com/en/lakehouse/medallion.html

[28] The Apache Software Foundation, “Apache Parquet Documentation.” [Trực tuyến]. https://parquet.apache.org/docs/

[29] M. Raasveldt and H. Mühleisen, “DuckDB: An embeddable analytical database,” in *Proc. 2019 International Conference on Management of Data (SIGMOD)*, 2019, pp. 1981–1984.

[30] The Apache Software Foundation, “Apache Airflow Documentation.” [Trực tuyến]. https://airflow.apache.org/docs/

[31] L. Wang, N. Yang, X. Huang, L. Yang, R. Majumder, and F. Wei, “Multilingual E5 text embeddings: A technical report,” arXiv:2402.05672, 2024.

[32] A. Kane, “pgvector: Open-source vector similarity search for Postgres.” [Trực tuyến]. https://github.com/pgvector/pgvector

[33] Y. A. Malkov and D. A. Yashunin, “Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs,” *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 42, no. 4, pp. 824–836, 2020.

@chapter PHỤ LỤC

## Phụ lục A. Cấu trúc mã nguồn

Mã nguồn của đề tài được lưu tại kho GitHub `luandz123/kho-du-lieu-va-khai-pha--cuoi-ky`. Các thư mục chính:

@table Bảng A.1. Cấu trúc thư mục mã nguồn
@widths 4,12
| Thư mục | Nội dung |
| database/ | Lược đồ kho dữ liệu (schema.sql), khung nhìn OLAP (views.sql), từ điển dữ liệu, ánh xạ nguồn – đích, sao lưu phục hồi |
| etl/ | Chương trình ETL: nạp staging, bảng chiều, bảng cầu nối, bảng sự kiện, nạp toàn bộ trong một giao dịch, nạp kết quả phân cụm |
| olap/ | Sáu truy vấn OLAP và chương trình chạy |
| mining/ | Đọc dữ liệu, phân tích khám phá, đặc trưng, K-Means, chia dữ liệu, item-based CF, baseline, đánh giá, công cụ gợi ý |
| dashboard/ | SQL các dataset, tệp xuất ba dashboard, hướng dẫn cài đặt và phục hồi Superset |
| tests/ | 225 ca kiểm thử tự động cho phần kho dữ liệu và phần khai phá |
| results/ | Kết quả EDA, đối soát, OLAP, thực nghiệm phân cụm và gợi ý |
| sources/ | Bản nâng cấp: thu thập MovieLens, IMDb, Wikidata, lượt xem và tóm tắt Wikipedia vào tầng bronze |
| cdc/ | Cấu hình Debezium, consumer Kafka → bronze |
| streaming/ | Producer đọc Wikimedia EventStreams |
| transform/ | Bronze → silver → gold bằng DuckDB |
| warehouse/ | Lược đồ kho mới, nạp tăng dần, chín kiểm tra chất lượng |
| orchestration/ | Image và ba DAG Airflow |
| ai/ | Embedding, mô hình lai, đánh giá |
| app/, app_source/ | Ứng dụng Streamlit và cơ sở dữ liệu giao dịch của ứng dụng |
| docs/ | Đặc tả, hợp đồng dữ liệu, sơ đồ, kịch bản demo, báo cáo |

## Phụ lục B. Hướng dẫn chạy lại hệ thống

Yêu cầu: Python 3.12, PostgreSQL 17, Docker (cho Superset). Các bước chính (chạy tại thư mục gốc của mã nguồn):

@code
# 1. Tạo môi trường và cài thư viện
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Tải MovieLens 1M và kiểm tra mã băm
python -m mining.source_fetcher

# 3. Tạo lược đồ kho dữ liệu (cấu hình kết nối trong tệp .env)
python -m etl.s05_staging bootstrap --env-file .env

# 4. Chạy ETL nạp toàn bộ và kiểm tra kho
python -m etl.run_etl refresh --env-file .env --raw-dir data/raw/ml-1m
python tests/warehouse/check_warehouse.py --env-file .env

# 5. Tạo và chạy sáu truy vấn OLAP
python -m olap.run_olap install --env-file .env
python -m olap.run_olap run --env-file .env

# 6. Gợi ý 5 phim cho một người dùng
python -m mining.recommend --source dw --user-id 1 --mode demo --top-n 5

# 7. Chạy kiểm thử tự động
python -m pytest tests/mining
python -m unittest discover -s tests/warehouse -p "test_*.py"
@endcode

Hướng dẫn chi tiết cho từng bước (thực nghiệm phân cụm, nạp kết quả phân cụm, cài đặt Superset và nhập dashboard) được trình bày trong tệp README.md và các tệp README của từng thư mục.

Bản nâng cấp chạy bằng Docker Compose. Các bước khởi động (thông tin kết nối và mật khẩu khai báo trong tệp `.env`):

@code
# 1. Khởi động kho, Postgres của ứng dụng, Kafka, Debezium, MinIO, Airflow, consumer, producer
docker compose up -d

# 2. Khởi động Superset (compose riêng)
docker compose -f dashboard/superset/compose.yaml --env-file dashboard/superset/.env up -d

# 3. Nạp toàn bộ lần đầu: kích hoạt DAG movie_bootstrap trên Airflow (http://localhost:8081),
#    sau đó tạo embedding phim (cần PyTorch, chạy trên máy)
python -m ai.embeddings

# 4. Chạy ứng dụng web (http://localhost:8501)
streamlit run app/streamlit_app.py
@endcode

Các giao diện quan sát: Kafka UI (cổng 8080), MinIO Console (cổng 9001), Airflow (cổng 8081), Superset (cổng 8089).
