# Hợp đồng dữ liệu chung

Cập nhật tài liệu P1-G0-v1: contract_version vẫn **2**, toàn bộ quy ước giữ nguyên. P1 xác nhận theo R-P1-01, nguyên văn người dùng “Duyệt”; P2 **chưa xác nhận**. G0 WAITING_REVIEW/chưa merge. Các nhãn chờ duyệt trong đoạn giới thiệu S01 bên dưới là lịch sử trước R-P1-01.


contract_version: **2**. Phiên bản tài liệu P1-S01-v1, 15/10/2026, **WAITING_REVIEW**. P1/P2 chưa xác nhận bản xuất này; cả hai xác nhận trước 3-P2. Nguồn: phần cùng tên trong tài liệu P1 cập nhật 15/10. Dưới đây chép nguyên văn toàn bộ quy ước, không tự thêm chính sách làm sạch. JSON lưu quy tắc có cấu trúc và toàn văn tương ứng.

Áp dụng cùng một hợp đồng phiên bản 2 trong cả hai tài liệu. P1 tạo docs/shared/data_contract.md và .json ở bước 1; P2 xác nhận trước bước 3. Nếu thay đổi giao diện, hai người chốt phiên bản mới và xác định đầu ra phải chạy lại trước khi merge.

Bốn bảng logic và thứ tự cột: users(user_id int, gender text, age_group text, occupation int); movies(movie_id int, title text, release_year int nullable); movie_genres(movie_id int, genre_name text); ratings(user_id int, movie_id int, rating int, timestamp int64, rated_at UTC). Dùng ID MovieLens gốc; surrogate key chỉ nằm trong DW. timestamp là giây Unix; rated_at tương đương timestamp theo UTC, xuất ISO 8601 dạng YYYY-MM-DDTHH:MM:SSZ.

users và movies có khóa ID duy nhất; movie_genres có khóa (movie_id, genre_name). ratings có grain một bản ghi nguồn; chỉ chốt khóa nghiệp vụ (user_id, movie_id) sau khi EDA xác nhận duy nhất. Nếu phát hiện trùng hoặc lỗi nguồn, dừng chốt chính sách chung, không để hai bên tự làm sạch khác nhau. rating thuộc 1..5; khóa tham chiếu phải tồn tại.

Tuổi dùng nhãn thống nhất: 1→Under 18; 18→18-24; 25→25-34; 35→35-44; 45→45-49; 50→50-55; 56→56+. gender giữ F/M, occupation giữ mã số nguồn. title giữ nguyên chuỗi nguồn; release_year lấy nhóm bốn chữ số trong ngoặc cuối tiêu đề, không khớp thì NULL. Giữ tên genre nguồn. Không dùng ZIP code.

Đọc nguồn Latin-1, phân cách ::; CSV chuẩn UTF-8 không BOM, dấu phẩy, LF, có header, quote theo CSV chuẩn, NULL là ô rỗng; số nguyên không có .0. Sắp users theo user_id, movies theo movie_id, movie_genres theo movie_id rồi genre_name, ratings theo user_id, movie_id, timestamp, rating. Hash SHA-256 byte CSV chuẩn theo từng bảng; cột rated_at phải đúng dạng UTC đã chốt. Cùng một quy tắc tuần tự hóa cho raw, csv và dw.

P2 sở hữu data/source_manifest.json: dataset_version, URL nguồn, ngày tải UTC, encoding, SHA-256 và số dòng từng tệp gốc. P2 xuất results/eda/canonical_manifest.json chứa contract_version, schema, row_count, hash bốn bảng chuẩn và tập mã nguồn. P1 tải riêng từ nguồn chính thức, kiểm tra tệp gốc rồi đối chiếu dữ liệu chuẩn; không chỉ so tổng số dòng hoặc tổng điểm.

P2 bàn giao results/mining/handoff/user_cluster.csv(user_id, cluster_id, status, model_version), cluster_genre_profile.csv(cluster_id, genre_name, mean_preference, n_users) và manifest.json. Một dòng mỗi user; status chỉ assigned hoặc insufficient_evidence. assigned có cluster_id nguyên 0..K-1; insufficient_evidence có cluster_id NULL. model_version là chuỗi cố định cho một lần chạy đã chốt.

mean_preference là trung bình tỷ lệ genre gốc của các user assigned thuộc cụm, trong [0,1]; n_users là số user assigned trong cụm, lặp cùng giá trị trên mọi genre của cụm. Xuất đủ K × số genre dòng, gồm cả tỷ lệ 0. Tổng mean_preference theo genre của mỗi cụm bằng 1 trong sai số 1e-8. Thiếu bằng chứng không tham gia tính trung bình.

manifest.json của gói cụm chứa contract_version, source_hashes, canonical_hashes, model_version, seed, K, preprocessing, genre_order, thư viện và phiên bản, training_config_hash, thời điểm UTC, số dòng và SHA-256 từng CSV. P1 chỉ nhận gói đầy đủ, đúng khóa và cùng dữ liệu DW; nạp transaction, không ghép hai phiên bản. Lưu phiên bản đang hoạt động trong analytics và vô hiệu hóa kết quả cũ nếu nguồn đổi.

Bốn view của P1: dw.v_ml_users, dw.v_ml_movies, dw.v_ml_movie_genres, dw.v_ml_ratings theo đúng thứ tự cột trên. Không nối genre vào ratings. Gói DW G2 có manifest bốn bảng, SQL/view, hướng dẫn chạy và CSV cục bộ tùy chọn; CSV chỉ phục vụ bàn giao, không thay cho xác nhận cuối trên DW.
