# Công bố PR11A Tổng quan

Ngày19/10/2026, điều phối chấp nhận chức năng11A sau kiểm hồ sơ/hash/cấu hình Superset thực, giao commit/push/PR. Đây là review điều phối, không phải agent tạo lời duyệt nguyên văn người dùng. PR chưa mở tại thời điểm ghi phần chuẩn bị; URL/HEAD/base sẽ được cập nhật sau xác minh. Chưa merge/11C/11B.

Dashboard thật http://127.0.0.1:8089/superset/dashboard/1/ ; database1/datasets1–2/charts1–8/dashboard1. UTCtypedfilter trước aggregate/Top10, khônggenreduplicate; meanSUM/COUNT, catalogchart5 cốđịnh. Tài khoảnBI chỉ SELECT2view; kết quả ba khoảng đãreview ở handoff/report, không chạy lại vì công bố.

Điều phối báo hai container từng dừng exit255, đã khởi động lại và kiểm API thành công. Không xác định nguyên nhân. Quan sát mới riêng publication_observation.json: hai container running/healthy,exit0; health200, loginAPI đạt,21cấuhình thực khớp SQL/metric/filter. Agent không restart trong lượt công bố.

Runtimebase988874d7b5897a5615acfebdf571c6d55861ddc2/run a614b26f902842618b39a35c799d0a77 vàhashcode/report giữ nguyên. Commitcode công bố ghi riêng saucommit; không sửa report để gán commit mới cho run cũ. Ledger handoff45artifact là snapshotreview, hash tài liệu mới ở overview_publication.json; các PASS/FAIL/ảnh/runtime giữ nguyên.

Giới hạn: PUBLIC TEMP mặcđịnh, chưaimportrestoreZIP, P2intake/hai máy hoặc fullrefreshhelperS07. ZIPexport/credential chỉlocalignored; khôngraw/userhistory/URIcredential lênGit. Kế hoạchngoàiphạmvi giữ nguyên. Phạmvi chỉcôngbố11A, khôngrerunETL/3khoảng/create hoặc thaySQL/metric/filter/quyền/firewall.

Danh sách toànPR/hashes/checks/URL/HEAD tại JSONcùngtên. Không tự ghi SHA của chính commit chứa ledger vào chínhfile; HEADcuối kiểm riêng bằng Git/API và bàn giao.

Hai snapshot AX nguyên bản có dấu trắng cuối dòng do UI. .gitattributes chỉ trong evidence và chỉ hai tệp này giữ nguyên byte, bỏ kiểm blank-at-eol cho dữ liệu capture; không tắt kiểm whitespace của code hoặc tài liệu khác. Cached diff ban đầu phát hiện đúng vấn đề này, không sửa bằng chứng đã review.
