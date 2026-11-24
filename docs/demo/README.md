# Video demo

Các script quay hệ thống thật bằng Playwright. Trước khi chạy cần bật đủ Docker, Superset và app Streamlit ở cổng 8501 (xem README gốc). Video (`*.mp4`) và tệp trung gian không lưu trên Git.

| Script | Kết quả | Ghi chú |
|---|---|---|
| [make_video.py](make_video.py) | `movie_platform_demo_longtieng.mp4` (~5′45″) | Giọng đọc tiếng Việt (edge-tts), phụ đề khớp từng câu, nhãn chương, tự cắt đoạn chờ. `--remux`: ghép lại từ bản quay thô mà không quay lại |
| [record_demo.py](record_demo.py) | `movie_platform_demo.mp4` (~4′) | Chỉ có phụ đề, không tiếng |
| [generate_video_5min.py](generate_video_5min.py) | `movie_platform_demo_5min.mp4` | Bản do Antigravity dựng theo kịch bản |

[kich_ban_video.md](kich_ban_video.md): kịch bản chi tiết và bộ câu hỏi ôn bảo vệ.

Lời thoại của `make_video.py` nằm trong biến `LINES`; tốc độ đọc chỉnh bằng `SPEED`. Script tạo một người dùng mới trên app, chấm 2 phim và chạy pipeline, nên mỗi lần quay thêm dữ liệu thật vào hệ thống.
