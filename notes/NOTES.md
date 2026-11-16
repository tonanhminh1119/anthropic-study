# Ghi chú: Realtime vs Batch, và chọn model

## 1. Realtime vs Batch

So sánh gọi `client.messages.create` (realtime) với Message Batches API (`demo_batch.py`) cho cùng tác vụ: 20 request ngắn, model `claude-sonnet-5-5`, prompt `Create one word starting with this character: <chữ cái>`.

| Tiêu chí | Realtime (`bench_realtime.py`) | Batch (`demo_batch.py`) |
|---|---|---|
| Độ trễ | median 1.44s/request (min 1.02s, max 2.70s); 20 request tuần tự hết 32.8s | 90–150 giây cho cả 1 và 20 request |
| Chi phí 20 request | $0.0082 (đo từ `usage` của 20 request) | ≈ $0.0038 (tính, xem dưới) |
| Thứ tự kết quả | theo thứ tự gọi | không đảm bảo, ghép theo `custom_id` |
| Xử lý lỗi | SDK tự retry | từng request có thể `errored` hoặc `expired` |
| Dùng khi | chat, tương tác | eval, phân loại, tóm tắt hàng loạt |

**Nguồn số liệu**
- Cột Realtime: đo trực tiếp bằng `time.perf_counter()` quanh `client.messages.create`, chạy một lần ngày 2026-11-10.
- Độ trễ batch: đo ở lần chạy batch trước đó.
- Chi phí batch không phải số đo trực tiếp. Mình lấy chi phí tính từ token đo ở lần chạy batch (≈ $0.0076 theo giá chuẩn của model) rồi nhân 0.5 theo mức giảm 50% của Batch API, ra ≈ $0.0038. Mức giảm 50% cần đối chiếu lại với trang giá chính thức.
- Chênh lệch $0.0082 so với $0.0076 là do hai lần chạy cho ra câu trả lời dài ngắn khác nhau, không phải do giá.

**Nhận xét**
- Batch rẻ hơn khoảng một nửa nhưng chậm hơn rất nhiều: khoảng 90–150s so với 33s cho cả 20 request tuần tự. Vì thế chỉ dùng batch khi không cần câu trả lời ngay.
- Thời gian chờ của batch gần như cố định theo số request, nên càng nhiều request thì batch càng có lợi so với gọi tuần tự.
- Luôn ghép kết quả với đầu vào qua `custom_id`, không dựa vào thứ tự.
- Mỗi request trong batch có kết quả riêng: `succeeded`, `errored`, `expired` hoặc `canceled`. `demo_batch.py` in loại kết quả cho request không thành công thay vì bỏ qua.

**Về retry**
- Lỗi 429 (quá giới hạn) và 529 (quá tải) được SDK tự retry theo `max_retries` (đang đặt 3). Lỗi 400 không retry vì lỗi nằm ở chính request.
- Đây là kiến thức từ tài liệu SDK, chưa có bằng chứng thực nghiệm: mình chưa tái hiện được lỗi 429/529 thật nên chưa quan sát được hành vi retry.

## 2. Chọn model: quality, latency, cost

Script `bench_models.py` chạy 3 prompt × 3 lần × 4 model, `effort: low` cho mọi model, rồi chấm điểm tự động:
- `math`: bài toán giờ tàu, đúng nếu giờ HH:MM cuối cùng trong câu trả lời là 11:20.
- `json`: trích xuất `name`, `amount_usd`, `date` từ một câu, đúng nếu JSON khớp hoàn toàn.
- `bullets`: đúng nếu có đúng 3 dòng bắt đầu bằng `- `, mỗi dòng không quá 8 từ.

| Model | Giá in/out ($/1M token) | Quality (0–1) | Latency median (s) | Cost / request ($) |
|---|---|---|---|---|
| `claude-haiku-5-5` | 0.10 / 0.50 | 1.00 | 1.2 | 0.00003 |
| `claude-sonnet-5-5` | 2.00 / 10.00 | 1.00 | 1.5 | 0.00066 |
| `claude-opus-5-5` | 4.00 / 20.00 | 1.00 | 1.5 | 0.00121 |
| `claude-fable-5-1` | 10.00 / 50.00 | 1.00 | 1.5 | 0.00281 |

**Đọc kết quả cho đúng**
- Cả 4 model đạt 1.00, tức 3 prompt này quá dễ để phân biệt chất lượng. Bảng chỉ chứng minh rằng với tác vụ đơn giản như vậy, model rẻ nhất cũng đủ.
- Vì vậy bảng không cho biết model đắt hơn tốt hơn bao nhiêu trên tác vụ khó. Muốn so sánh chất lượng cần thêm prompt khó hơn (suy luận nhiều bước, code, ngữ cảnh dài) và nhiều lần lặp hơn.
- Mẫu nhỏ (9 lần chạy mỗi model, một đợt) nên latency chênh nhau 0.1–0.3s chưa đáng tin; chỉ nên kết luận độ trễ cùng cỡ vài giây.
- Giá lấy từ bảng giá Anthropic ghi trong tài liệu SDK; cost tính từ `usage.input_tokens` và `usage.output_tokens` (output đã gồm thinking).

**Đánh đổi khi chọn model**
- Chi phí chênh rất lớn: so với Haiku, mỗi request của Sonnet đắt gấp khoảng 22 lần, Opus khoảng 40 lần, Fable khoảng 94 lần, trong khi độ trễ gần như như nhau trên các prompt này.
- Quy tắc thực dụng: bắt đầu từ model rẻ nhất, chỉ nâng model khi eval của chính tác vụ cho thấy rẻ không đạt.
- Lượng token đầu ra (cả thinking) mới là thứ quyết định chi phí thật; giữ `effort` thấp cho tác vụ đơn giản.
