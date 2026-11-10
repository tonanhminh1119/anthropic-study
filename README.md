# Demo Claude API

Các script nhỏ minh hoạ cách dùng Claude API qua Python SDK `anthropic`.

## Chuẩn bị

1. Cài thư viện: `pip install anthropic python-dotenv`
2. Sao chép `.env.example` thành `.env` rồi điền API key:
   ```
   ANTHROPIC_API_KEY=<key của bạn>
   ```
3. **Không bao giờ commit `.env` hoặc API key.** `.env` đã nằm trong `.gitignore`.
   Nếu key từng xuất hiện trong lịch sử git, coi như đã lộ: thu hồi và tạo key mới tại console.anthropic.com.

## Cách chạy

```
python demo.py           # chạy chat, streaming, caching (bỏ qua image)
python demo.py chat      # chỉ chạy một thí nghiệm: chat | streaming | caching
python demo.py image duong_dan_anh.jpg   # thí nghiệm ảnh, cần truyền đường dẫn ảnh
python demo_batch.py     # Message Batches API
```

## Mỗi file chứng minh điều gì

| File | Nội dung |
|---|---|
| `demo.py` | Bốn thí nghiệm, mỗi cái là một hàm: **chat** nhiều lượt (tự quản lý lịch sử `messages`), **image** (gửi ảnh base64 kèm câu hỏi), **streaming** (in từng đoạn khi model sinh ra), **caching** (prompt caching với `cache_control`, xem `cache_write`/`cache_read` trong dòng usage; lượt 2 đọc từ cache nên rẻ hơn). |
| `demo_batch.py` | Gửi 20 request cùng lúc bằng Message Batches API, poll đến khi xong rồi in kết quả. Xử lý bất đồng bộ nên rẻ hơn nhưng chậm hơn. |

Thí nghiệm `caching` dùng văn bản dài trong `archive/Building with the Claude API.txt`. Thư mục `archive/` chỉ để lưu tài liệu tham khảo.
