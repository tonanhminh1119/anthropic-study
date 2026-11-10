# Ghi chú: Realtime vs Batch

So sánh gọi `client.messages.create` (realtime, xem `demo.py`) với Message Batches API (xem `demo_batch.py`) cho cùng một tác vụ: 20 request ngắn, model `claude-sonnet-5-5`.

| Tiêu chí | Realtime | Batch |
|---|---|---|
| Độ trễ | _chưa đo_ (thường vài giây mỗi request) | 90–150 giây cho cả 1 và 20 request |
| Chi phí 20 request | ≈ $0.0076 | ≈ $0.0038 (giảm 50% theo bảng giá batch) |
| Thứ tự kết quả | theo thứ tự gọi | không đảm bảo, ghép theo `custom_id` |
| Xử lý lỗi | SDK tự retry | từng request có thể `errored` hoặc `expired` |
| Dùng khi | chat, tương tác | eval, phân loại, tóm tắt hàng loạt |

**Nguồn số liệu**
- Độ trễ batch và chi phí realtime là số đã đo ở các lần chạy trước.
- Chi phí batch là số tính: $0.0076 × 0.5. Mức giảm 50% cần đối chiếu lại với trang giá chính thức trước khi dùng làm kết luận.
- Độ trễ realtime chưa có số đo. Điền vào sau khi chạy `python demo.py chat` (đo thời gian quanh lệnh gọi).

**Nhận xét**
- Batch rẻ hơn khoảng một nửa nhưng độ trễ gần như cố định (cả 1 và 20 request đều mất 90–150 giây), nên chỉ đáng dùng khi không cần câu trả lời ngay.
- Vì thứ tự kết quả không đảm bảo, luôn ghép kết quả với đầu vào qua `custom_id` (`demo_batch.py` đặt `req-<chữ cái>`).
- Mỗi request trong batch có kết quả riêng: `succeeded`, `errored`, `expired` hoặc `canceled`. `demo_batch.py` in loại kết quả cho request không thành công thay vì bỏ qua.

**Về retry**
- Lỗi 429 (quá giới hạn) và 529 (quá tải) được SDK tự retry theo `max_retries` (đang đặt 3).
- Lỗi 400 không retry vì lỗi nằm ở chính request, gửi lại cũng vẫn lỗi.
