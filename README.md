# Demo Claude API

Các script nhỏ minh hoạ cách dùng Claude API qua Python SDK `anthropic`.

## Chuẩn bị

1. Cài thư viện: `pip install -r requirements.txt`
2. Sao chép `.env.example` thành `.env` rồi điền API key:
   ```
   ANTHROPIC_API_KEY=<key của bạn>
   ```
3. **Không bao giờ commit `.env` hoặc API key.** `.env` đã nằm trong `.gitignore`.
   Nếu key từng xuất hiện trong lịch sử git, coi như đã lộ: thu hồi và tạo key mới tại console.anthropic.com.

## Cấu trúc repo

| Thư mục | Nội dung |
|---|---|
| `demos/` | Script minh hoạ Claude API và benchmark (`demo*.py`, `bench_*.py`) |
| `labs/lab2/` | Lab 2: agent xoá tin nhắn, kèm dữ liệu, định nghĩa tool và báo cáo ([LAB2.md](labs/lab2/LAB2.md)) |
| `notes/` | Ghi chú học tập ([NOTES.md](notes/NOTES.md), ghi chú Week 3 Day 1) |
| `archive/` | Tài liệu khoá học gốc và các ghi chú cũ đã lưu trữ |

Các lệnh dưới đây chạy từ thư mục gốc của repo.

## Cách chạy

```
python demos/demo.py           # chạy chat, streaming, caching (bỏ qua image)
python demos/demo.py chat      # chỉ chạy một thí nghiệm: chat | streaming | caching
python demos/demo.py image duong_dan_anh.jpg   # thí nghiệm ảnh, cần truyền đường dẫn ảnh
python demos/demo_batch.py     # Message Batches API
python demos/bench_realtime.py # đo độ trễ và chi phí 20 request realtime
python demos/bench_models.py   # benchmark 4 model (tốn tiền thật, vài cent)
python labs/lab2/lab2_agent.py # Lab 2, xem labs/lab2/LAB2.md
```

## Mỗi file chứng minh điều gì

| File | Nội dung |
|---|---|
| `demos/demo.py` | Bốn thí nghiệm, mỗi cái là một hàm: **chat** nhiều lượt (tự quản lý lịch sử `messages`), **image** (gửi ảnh base64 kèm câu hỏi), **streaming** (in từng đoạn khi model sinh ra), **caching** (prompt caching với `cache_control`, xem `cache_write`/`cache_read` trong dòng usage; lượt 2 đọc từ cache nên rẻ hơn). |
| `demos/demo_batch.py` | Gửi 20 request cùng lúc bằng Message Batches API, poll đến khi xong rồi in kết quả. Xử lý bất đồng bộ nên rẻ hơn nhưng chậm hơn. |
| `demos/bench_realtime.py` | Gửi 20 request tuần tự giống batch, đo độ trễ và chi phí để so với `demo_batch.py`. |
| `demos/bench_models.py` | Chạy 3 prompt trên 4 model, đo latency, cost và chấm quality tự động (kết quả trong `notes/NOTES.md`). |

Thí nghiệm `caching` dùng văn bản dài trong `archive/Building with the Claude API.txt`. Thư mục `archive/` chỉ để lưu tài liệu tham khảo.

So sánh realtime và batch: xem [notes/NOTES.md](notes/NOTES.md).

Danh sách issue đã gặp và đã sửa: xem [ISSUES.md](ISSUES.md).
