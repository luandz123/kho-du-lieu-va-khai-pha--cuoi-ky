# Bộ hỏi–đáp Q1/Q2 phục vụ bảo vệ — P2

Ngày 25/10/2026 — **Nội dung hỏi–đáp được điều phối chấp nhận**. Biên soạn từ kết quả đã chốt, không tính lại metric Test hoặc tạo slide tổng. Điều phối sau đó cho phép smoke test và tổng duyệt suy luận; kết quả mới được tách trong hồ sơ bổ sung. Nội dung chương 2/5/6 đã được điều phối duyệt; [PR31](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/31) đã merge tại `a2021a9f591c56222f5ae16e169f278bf3cec5a7`. Candidate thực kiểm tích hợp vẫn `4546d5bbd8f9130a420518b77dc3ad894bc7f42b`. G4 đạt trong phạm vi đã nghiệm thu, G5 chưa hoàn thành.

## Q1 — feature, phân cụm và diễn giải

**1. Q1 giải quyết việc gì?**
Mô tả các nhóm tỷ lệ thể loại trong lịch sử đánh giá tích cực của snapshot MovieLens; sau đó mô tả cơ cấu tuổi/giới trong từng nhóm. Nhãn cụm không phải chân lý về sở thích hay động cơ xem. Nguồn: [chương 5, mục 5.1–5.3](../report/chapter_05.md).

**2. Vì sao feature có 18 chiều và mẫu số nào?**
Giữ 18 genre gốc, thứ tự A–Z. Với rating ≥4, mỗi phim đóng góp 1 vào từng genre của nó; C(u,g) là số liên kết genre tích cực, S(u)=tổng C trên 18 genre, p(u,g)=C(u,g)/S(u). Tổng vector bằng 1 trong tolerance 10⁻⁸. Không chia trực tiếp cho số phim hoặc số rating. Nguồn: [features.py](../../../mining/features.py), [chương 2, mục 2.4](../report/chapter_02.md).

**3. Minh họa phim nhiều genre mà không dùng người thật?**
Fixture tự tạo: phim A (Action, Comedy) được 5 sao và phim B (Comedy) được 4 sao. Có 3 lượt gắn genre tích cực: Action 1, Comedy 2, vector tương ứng 1/3 và 2/3; các genre khác 0. Hai rating không được nhầm với 3 rating. Đây là ví dụ tính tay, không là thực nghiệm mới.

**4. Vì sao chỉ 6.038 vector thay vì 6.040?**
Hai hồ sơ không có bằng chứng tích cực theo ngưỡng, S(u)=0; status insufficient_evidence và cluster_id NULL, không fit vector rỗng. Không có nghĩa hai người không có rating. Gói user_cluster vẫn giữ đủ 6.040 dòng. Không công bố ID cụ thể. Nguồn: [summary](../../../results/mining/clustering_summary.json).

**5. Có dùng tuổi/giới để tạo cụm không?**
Không. Feature chỉ là tỷ lệ genre tích cực. Nhân khẩu học được ghép sau phân cụm để mô tả. Baseline là đúng 6.038 assigned, không dùng 6.040; tỷ lệ trong cụm chia quy mô cụm. Chưa điều chỉnh yếu tố gây nhiễu hoặc kiểm định nhân quả. Nguồn: bảng 5.4 chương 5.

**6. Đã thử bao nhiêu cấu hình?**
14 cấu hình: K=2..8 × raw/StandardScaler, fit trên đủ 6.038 vector. Seed42, n_init=10; inertia/quy mô trên toàn tập, Silhouette chỉ trong cùng mẫu cố định 2.000. Không gọi Silhouette mẫu là metric toàn tập. Nguồn: experiments_summary trong summary, bảng 5.1.

**7. K=4 có Silhouette tốt nhất không?**
Không. Raw K2=0,2233 và K3=0,2211 cao hơn K4=0,1860. Chọn K4 theo cân bằng khả năng diễn giải bốn profile, quy mô và ổn định đã kiểm. Elbow hỗ trợ lựa chọn, không chứng minh tối ưu duy nhất. Không nói K4 thắng mọi cấu hình chỉ bằng Silhouette.

**8. SSE raw nhỏ hơn scaled có chứng minh raw tốt hơn không?**
Không. Hai không gian có thang đo khác, nên không so trực tiếp độ lớn SSE. StandardScaler thay trọng số khoảng cách; trong lưới đã công bố scaled có Silhouette thấp hơn và K8 tạo cụm 5 người. Kết luận giới hạn ở lưới này, không là quy tắc mọi dữ liệu. Nguồn: bảng 5.1 chương 5.

**9. Độ ổn định được đo bằng gì?**
ARI trên cùng 6.038 người khi đổi seed: 42 so 0 đạt 0,9949; 42 so 7 đạt 0,9763. ARI so phân vùng, bất biến hoán vị nhãn; không phải accuracy với ground truth. Chỉ hai cặp trong summary được dùng, không suy mọi seed đều ổn định.

**10. Bốn nhóm và mẫu số profile là gì?**
Cụm0 đa dạng: 2.478; cụm1 Drama/tình cảm: 1.393; cụm2 Comedy: 760; cụm3 Action/Sci-Fi/Thriller: 1.407. Tỷ trọng quy mô chia 6.038. Profile là trung bình tỷ lệ genre gốc của từng người trong cụm; không là % người thích genre và không trọng số theo số rating mỗi người. Nguồn: bảng 5.3, summary.

**11. Có thể khẳng định tuổi/giới quyết định sở thích không?**
Không. Ví dụ tỷ lệ nữ ở cụm2 là 44,9% so baseline assigned 28,3% chỉ là cơ cấu mô tả snapshot. Nguồn là dữ liệu người tự tham gia, tuổi tĩnh; không theo dõi cùng người già đi và thay đổi sở thích. Không suy nhân quả hay tính đại diện dân số.

**12. Vì sao không trình bày hình PCA trong bản chính?**
Tỷ lệ phương sai trên ảnh gốc và văn bản diễn giải cũ mâu thuẫn, chưa xác minh nguyên nhân. Theo chỉ đạo biên tập, ảnh/tỷ lệ tạm bỏ khỏi bản chính, giữ nguồn và ghi chú [editorial_notes](../report/editorial_notes.md). Không sửa artifact hoặc fit lại để tạo số mới; PCA không dùng để chọn không gian fit của cấu hình đã chốt.

## Q2 — giao thức, mô hình và kết quả

**13. Vì sao chia theo thời gian?**
Huấn luyện từ lịch sử được phép rồi đánh giá kỳ sau, giảm rò rỉ thông tin tương lai của snapshot. t₁=974862386 (2000-11-22T03:06:26Z), t₂=976422051 (2000-12-10T04:20:51Z). Train t≤t₁:700.148 rating; validation t₁<t≤t₂:150.029; Test t>t₂:150.032. Timestamp hòa cùng phía. Feature/nhãn Q1 toàn lịch sử không tham gia Q2. Nguồn: [split manifest](../../../results/mining/split_manifest.json).

**14. Ai được đánh giá và so mô hình có công bằng không?**
Cần ≥5 rating trong lịch sử huấn luyện và ≥1 phim rating≥4 trong kỳ đánh giá. Validation 471 người, Test 1.154 người; trong từng kỳ CF/baseline cùng cohort và candidate universe. Candidate = catalog huấn luyện trừ mọi phim đã đánh giá; không negative sampling. Mẫu đủ điều kiện không đại diện toàn người dùng. Nguồn: bảng 5.6.

**15. Phim mới có bị xóa khỏi Recall không?**
Không. Relevant gồm mọi phim tích cực của người trong kỳ, cả phim mới ngoài catalog huấn luyện. Số phim mới tích cực distinct trong cohort là 3 validation, 16 Test; đây không phải tổng mẫu số macro Recall. Mô hình không thể đề xuất item ngoài catalog lịch sử nhưng vẫn chịu miss đó. “Mới” ở đây nghĩa chưa xuất hiện trong catalog huấn luyện, không nhất thiết mới phát hành.

**16. Cosine được tính thế nào và score có phải sao dự đoán?**
Ma trận phim×người chứa rating 1..5, ô thiếu bằng 0; chuẩn hóa L2 theo hàng rồi tích vô hướng, không trừ trung bình. Cosine đường chéo đặt 0, chỉ giữ similarity>0. Score(u,i)=tổng similarity từ các seed rating≥4 mà i nằm trong top neighbor_k của seed đó. Không nhân thêm sao seed, không chia tổng similarity. Score có thể >1, là điểm xếp hạng, không trực tiếp một cosine hay sao dự đoán. Nguồn: [cf.py](../../../mining/cf.py), công thức chương 2.

**17. Top-k láng giềng theo hướng nào và xử lý hòa ra sao?**
Lấy tối đa neighbor_k láng giềng của từng phim seed; cắt top-k làm quan hệ có thể bất đối xứng. Hòa láng giềng: similarity giảm, movie_id tăng. Hòa điểm gợi ý: score giảm, popularity lịch sử giảm, movie_id tăng; loại mọi phim đã đánh giá trong lịch sử cho phép. Xếp trước khi làm tròn score xuất ra.

**18. Baseline khác fallback ở đâu?**
Baseline là mô hình đối chứng xếp phim theo số **mọi rating** huấn luyện, không chỉ positive; loại lịch sử, hòa count thì movie_id tăng. Fallback là bổ sung từ bảng đó nếu CF có dưới 5 mục điểm dương, loại mục đã chọn. Dòng fallback có score_type=popularity_fallback, score None, hiển thị N/A; không cộng count popularity vào float score CF.

**19. Vì sao k40 mà không k80? Có đổi tiêu chí sau Test không?**
Chọn Recall@5 validation chưa làm tròn cao nhất trong CF {20,40,80}, hòa chọn k nhỏ. Recall lần lượt 0.02856536704222439 / 0.03007556334371585 / 0.02866586314500013. K80 có Precision/hits cao hơn nhưng không thắng tiêu chí đã khóa. Không dùng Test chọn lại. K=4 là số cụm, neighbor_k=40 là số láng giềng, Top-N=5 là đầu ra. Nguồn: [validation CF](../../../results/mining/cf_validation_experiments.json).

**20. CF có thắng baseline trên validation không?**
Precision k40 cao hơn (0,180042 so 0,169851), nhưng Recall thấp hơn (0,03007556 so 0,031261). Tổng hits 424 so 400 không bắt buộc macro Recall cao hơn vì mẫu số relevant từng người khác nhau. Phải nêu kết quả này cùng Test, không chọn riêng số thuận lợi.

**21. Precision/Recall macro có mẫu số nào?**
P@5(u)=hits(u)/5 kể cả trả thiếu; R@5(u)=hits(u)/số relevant kỳ đánh giá, gồm phim mới. Lấy trung bình theo người trong cohort, mỗi người trọng số ngang nhau. Recall không phải catalog coverage. Fixture giả: 2 hits/5 mục và 4 relevant cho P=0,4, R=0,5; không là dữ liệu cá nhân thực. Nguồn: [evaluation.py](../../../mining/evaluation.py).

**22. Test chính thức cho kết quả gì?**
Cùng 1.154 người, Top5: baseline P=0.201733, R=0.02712408, hits=1.164; CF k40 P=0.231023, R=0.03530289, hits=1.333. CF dùng fallback ở 2/1.154 người (0,1733%). Chép nguyên [receipt](../../../results/mining/cf_test_evaluation_receipt.json), run test_run_s10b_official_20261022_034458; không phải lần Test mới từ DW. Trong lượt Test này CF cao hơn baseline, chưa kiểm định ý nghĩa thống kê hoặc ưu thế tổng quát.

**23. Evaluation và demo có phải đều đánh giá Test không?**
Không. Evaluation CLI dựng suy luận với cutoff t₂ và cấu hình đóng băng, model item_based_cf_k40_eval_v1; demo dùng toàn lịch sử, model item_based_cf_k40_DEMO_full_history_v1. Cả hai CLI không sinh metric Test chính thức. Demo không dùng lấy metric offline. Việc gọi CLI vẫn fit ma trận/láng giềng trong bộ nhớ. Bản chuẩn bị ban đầu chưa chạy; lượt bổ sung hiện được điều phối cho phép tổng duyệt với canonical CSV kiểm hash, không gọi evaluator Test chính thức. Kết quả mới được ghi riêng trong hồ sơ smoke/rehearsal, không biến thành metric Test mới. Nguồn: [recommend.py](../../../mining/recommend.py), [CLI summary lịch sử](../../../results/mining/integration_p2/cli_verification_summary.json).

**24. Đã tái lập gì trên hai máy và chưa kiểm gì?**
Hai môi trường tích hợp là Windows: P1 Python3.12.14/PostgreSQL17.11; P2 Python3.12.6/PostgreSQL17.4. P2 kiểm DW-only, raw/CSV/DW, Q1/G3 và ba ca CLI; BI/restore kiểm ở P1. Chỉ hai CSV G3 đã đối chiếu byte-identical, không toàn môi trường/manifest. Không tuyên bố Linux hoặc Superset/restore trên P2 đã kiểm. G4 đạt không đồng nghĩa G5/gói nộp hoàn thành.

## Cách dùng khi bảo vệ

Trả lời trực tiếp bằng ý chính, chỉ mở nguồn bảng/công thức khi cần chứng minh. Không hiện user ID, lịch sử hoặc danh sách phim của từng người. Không mở snapshot evaluator để chạy; nó chỉ phục vụ kiểm toán tĩnh. Với câu hỏi ngoài bằng chứng, nêu là giới hạn/đề xuất thay vì tạo thực nghiệm hoặc đổi metric trong lúc trả lời. Kịch bản CLI tại [cli_evaluation_demo.md](cli_evaluation_demo.md).


## Lưu ý cấu hình và lượt tổng duyệt bổ sung

Kịch bản CLI ghi rõ source=csv dùng canonical CSV đã kiểm; source=dw cần PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD cấu hình riêng cho adapter. Không mặc định mining.recommend tự đọc .env và không công bố mật khẩu/URI hoặc output theo user. Lượt tổng duyệt suy luận được phép không thay tiêu chí k40 hoặc metric/receipt Test; xem [hồ sơ bổ sung](../provenance/smoke_rehearsal_20261025/summary.md).
