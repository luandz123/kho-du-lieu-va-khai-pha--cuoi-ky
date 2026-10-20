# Bàn giao 11C — Dashboard xu hướng, WAITING_REVIEW

## Hiện hành — PR11C OPEN, chờ review PR, 20/10/2026

Đã commit/push p1-s11c-trends và mở [PR #15](https://github.com/luandz123/kho-du-lieu-va-khai-pha--cuoi-ky/pull/15) vào main. GitHub API xác minh OPEN/merged=false, HEAD lúc mở **bdb14fce8deb830999bcb4c17655100a72e6514e**, base **5a42c73c39c00780b2d5442c45662d93bdf0f23b**. Đủ52file của toànPR, gồm checkpoint11A, có SHAblob trong PR và remotetree khớp Gitlocal. Chức năng11C **APPROVED theo điều phối**; PR **WAITING_REVIEW**, chưaMERGED; agent không merge.

Code công bố để tái tạo **bdb14fce8deb830999bcb4c17655100a72e6514e** tách runtimebase52d566a/run8b4eeb54/hash thực chạy. Commit hồ sơ sau mục này chỉ ghi URL/trạng thái/hash; HEAD chứa chính hồ sơ được kiểm Git/API riêng trong bàn giao cuối, không sửa report run để gán commit mới. Snapshot kiểm lúc mở ghi docs/P1/trends_publication.json; OPEN này là quan sát tại thời điểm kiểm, không phải lời duyệtPR.

Không đổiSQL/metric/filter, không chạy ETL/create/đối soátđầyđủ, không11B/G3 hoặc quyền/firewall. Giữ PUBLIC TEMP/chưarestore/P2/hai máy/fullrefreshhelperS07. Ledger43artifact bàn giao và PASS/FAIL là lịch sử nguyên vẹn; hash tài liệu mới có ledger công bố riêng. Kế hoạch ngoài phạm vi giữ untracked. Dừng chờ reviewPR.

---


## Công bố 11C — chức năng được điều phối chấp nhận, 20/10/2026

Nguồn: người dùng chuyển thông báo điều phối chấp nhận chức năng11C và giao commit/push/mở PR vào main. Đây là review chức năng của điều phối, không phải agent tự tạo lời duyệt. Chức năng **APPROVED theo điều phối**; PR chỉ ghi OPEN/MERGED sau khi xác minh. Không tự merge,11B hoặc nạpG3.

Kiểm trước công bố: repository/nhánh đúng, quyền push có, chưa có PR11C;43artifact bàn giao khớp SHA, JSON/Python hợp lệ, không secret/URI chứa credential hoặc dữ liệu theo user, private paths ignored. Rà cả11file checkpoint hậu merge11A đã ghép52d566a, không chỉ code11C. SQL/metric/filter giữ nguyên; không chạy lại ETL, create dashboard hoặc đối soát3khoảng. Report PASS/FAIL và run8b4eeb54/75f00145 giữ nguyên, codehash lúc chạy không gán thành commit công bố.

Ledger bàn giao43artifact là snapshot lịch sử trước duyệt. Tài liệu cập nhật công bố có hash riêng tại docs/P1/trends_publication.json; không sửa report cũ để khớp tài liệu mới. Giữ PUBLIC TEMP/chưa importrestore/P2intakeNOT_CONFIRMED/hai máy/fullrefreshhelperS07. Kế hoạch untracked giữ nguyên. URL/commit/trạng thái thực sẽ bổ sung sau xác minh; các mục WAITING_REVIEW kết quả bên dưới là lịch sử.

---


Nguồn giao việc: điều phối xác nhận PR14 đã merge và chấp nhận công bố11A; giao riêng11C. Chưa có lời duyệt kết quả11C. Không suy nội dung tài liệu Word thành quyền làm11B hoặc export ba dashboard.

## Dashboard và định nghĩa

- URL thực: <http://127.0.0.1:8089/superset/dashboard/2/>; tên “MovieLens1M · Xu hướng đánh giá theo quý”. Database1 MovieLens BTL - BI reader.
- Dataset3 `P1_11C_quarter` (O4 chỉ quý), dataset4 `P1_11C_genre` (O5 sau zero-fill/LAG/share toàn chuỗi, rank toàn bộ genre đủ điều kiện).
- Chart9 tổng duy nhất/quý;10 lượt gắn genre/quý;11 QoQ%;12 tỷ trọng%;13 chi tiết count/quý trước/mẫu số/share/QoQ/rank và trạng thái quý biên, thiếu điều kiện, hạng1 âm.
- SQL, metric, scope filter, layout và IDs tại `dashboard/trends/`. Tất cả tạo qua REST API chính thức; không ghi trực tiếp metadata, không đổi DDL/view PostgreSQL.

Quý là thời điểm đánh giá UTC. Native filter **quý dạng danh mục** buộc chọn trọn quý (nhiều quý liên tiếp tạo khoảng); không hỗ trợ ngày lẻ. Filter này tác động cả5chart sau khi tính full-series. Native genre chỉ tác động charts10–13; chart9 loại khỏi scope. Không tuổi/giới. Share giữ mẫu số toàn bộ18genre cùng quý; QoQ đầu vùng chọn vẫn có quý trước ngoài vùng chọn. MAX metric chỉ cho một ô quý×genre; không cộng phần trăm hoặc cộng genre thành rating duy nhất.

## Kiểm mới và bằng chứng

Run cuối **8b4eeb54e699409aa5ca926f2c4925de**, UTC2026-10-19T15:44:13.799704Z, **32.828 giây**, base/HEAD **52d566a8e13284f707f622049b37a416ba9cd982**. Code11C chưa commit; SHA file thực chạy trong report, không gán commit tương lai cho run này. Run75f00145 trước chỉnh định dạng số nguyên được giữ riêng, không sửa lịch sử.

SQL độc lập từ fact/bridge/dim_genre (không dùng analytics view làm expected), sau đó Python Decimal tính đủ grid/LAG/mẫu số/rank; so với context chart đang lưu thật và API dùng BIengine. Cả5chart trong cả3tổ hợp đạt, sai số số thập phân<1e-9; NULL được giữ riêng với0.

| Tổ hợp | Rating duy nhất hệ thống | Ô genre đã so | Bằng chứng chính |
|---|---:|---:|---|
|Toàn12quý,18genre|1000209, tổng điểm3582313|216|Quý biên và NULL đầu chuỗi;156ô được rank; UI toàn kỳ|
|Comedy,2000Q4–2001Q1|478797|2|Genre thuộc nhiều phim đa thể loại; count159673/11975; share16.907492%/18.907397%, không100%|
|Animation/Horror/Western,2001Q1–2002Q2|82609|18|Animation quý đầu prev20068,count1715,QoQ−91.454056%,share2.707823%,rank1=giảm ít nhất|

Comedy2000Q4 vẫn dùng prev114281 của2000Q3, QoQ39.719638%;2001Q1 QoQ−92.500297%. Hạng của Comedy vẫn7/5 giữa toàn18genre, không bị đổi thành1 do filter. Fixture tính độc lập [10,0,5] cho QoQ [NULL,−100,NULL]; bằng chứng S07 cũ về SQL zero-fill vẫn được kế thừa, không tuyên bố chạy lại fixture PostgreSQL S07.

UI thật đã chọn/apply hai tổ hợp, thấy chart9 chỉ1filter, charts10–13 có2filter; bảng count/share/QoQ/rank khớp API. Ảnh JPEG viewport desktop1280×900, AXsnapshot JSON nguyên bản trong evidence. Sau cùng Clear all, trả toàn kỳ và reset viewport tạm. Có thanh cuộn ngang của bảng chi tiết; panel hẹp chưa tối ưu. Ảnh Comedy sớm có count hiển thị rút gọn, tooltip/AX giữ giá trị chính xác; ảnh cuối ba genre đã hiển thị số nguyên đầy đủ.

11A: snapshot trước/sau của11đối tượng (dashboard1,2dataset,8chart) bằng nhau; native timefilter giữ nguyên. API KPI1000209 và Top1 AmericanBeauty3428, UI11A mở được. Không gọi create_overview, không đổi11A. Bốn file schema/view/contract so Gitmain không đổi; analytics3bảng vẫn0. Không ETL hoặc full refresh.

`final_verification.json`: Supersetengine thật current_user=movielens_bi_reader, TimeZoneUTC; ownership0, sequencewrite0; scoped filters/layout/SQL đúng cấu hình, hai container running/healthy/exit0. Superset tự bổ sung metadata màu khi render; lưu riêng `dashboard_observed.json`, kiểm mọi field nghiệp vụ còn lại chính xác, không coi thay đổi màu là đổi công thức.

## Quyền BI và lỗi giữ lại

Thực thi đúng `dashboard/trends/bi_grants.sql`: USAGEanalytics; SELECT analytics.v_olap_time_rollup và analytics.v_olap_genre_quarter. Không đổi credential. Kiểm từ container sessionreadonly=off: chỉ SELECT4view được phép (2DW cũ+2OLAP), mọi DML/CREATE=false, không membership/admin; UPDATE fact WHEREfalse bị42501. Không cấp SELECTtoànschema hoặc defaultprivileges. PUBLIC TEMP vẫntrue mặc định; không khẳng định toàn server bất biến hoặc P2 đã kết nối.

Giữ3FAIL lịch sử riêng: guard dùng nhầm hàm comment catalog thường cho sharedrole (rollback trước GRANT; sửa shobj_description); sort MIN(record) không hỗ trợ (sửa ROW(MINquarter,MINgenre), không đổi metric dữ liệu); checker metadata phát hiện Superset thêm màu (whitelist4field tự sinh, vẫn so exact nativefilter/layout). Các PASS mới là sau sửa thực tế.

## Git, file và giới hạn

Checkpoint hồ sơ11A gốc **c09ae5b**, main fast-forward **5a42c73c39c00780b2d5442c45662d93bdf0f23b**, tạo **p1-s11c-trends**, cherry-pick chọn lọc checkpoint thành **52d566a8e13284f707f622049b37a416ba9cd982**. Chỉ11file hồ sơ P1 trong checkpoint, không codeETL/P2/kế hoạch. Các OPEN cũ giữ nguyên, quan sát MERGED nằm trong ghi chú mới. Đây là commit hồ sơ11A được phép, **không phải commit11C**. Phần11C vẫn local chưa stage/commit/push/PR.

File mới: `dashboard/trends/` gồm2SQLdataset, GRANTSQL, prepare/create/reconcile/verify, IDs/chart/dashboarddefinitions, README và evidence; tài liệu này, hồ sơ S11/STATE/DECISIONS/REVIEWS/PROMPTS và liên kết README. Ledger `dashboard/trends/evidence/handoff_manifest.json` liệt kê file/SHA cuối. Kế hoạch ngoài phạm vi giữ untracked, SHA256 da37e4a262541ad9f7957ded381cd1347a8e657709f8367fa2ec5ee4cd51d7c7; không sửaP2/nguồn.

Giữ PUBLIC TEMP, chưa import/restoreZIP, P2intakeNOT_CONFIRMED/hai máy chưa kiểm, helperS07 chưa fullrefreshmới. Không export gói ba dashboard, nạpG3,11B, thayfirewall hoặc quyền ngoài phạm vi. Rubric chưa xác minh thêm. Container exit255 lịch sử không suy nguyên nhân; lượt này container đã healthy, không cần restart.

## Ý bảo vệ và nội dung cần review

1. Một rating phim nhiều genre đóng góp nhiều lượt gắn; tổng duy nhất lấy riêng O4, chỉ cấp quý.
2. Lọc hiển thị sau LAG giữ quý trước; mẫu số share và rank không bị co lại theo genre được chọn.
3. NULL là chưa có/mẫu0, khác tăng trưởng0%; quý biên và ngưỡng100 kiểm soát xếp hạng.
4. Hạng1 âm nghĩa giảm ít nhất trong tập đủ điều kiện; không suy nhu cầu hiện tại từ lịch sử đánh giá.
5. Quyền đọc thật kiểm từ BIengine/container, khác session READ ONLY; metadata Superset tách DW.

Cần điều phối review dashboard2, native scope,3tổ hợp, artifacthash/quyền BI và giới hạn. **11C WAITING_REVIEW**, chưa duyệt chức năng/chưa PR. Dừng chờ điều phối.
