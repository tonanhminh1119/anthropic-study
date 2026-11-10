# Nhật ký issue

Các vấn đề gặp phải trong quá trình dọn repo và làm benchmark, cách đã xử lý, và việc còn mở.

## Đã sửa

| # | Vấn đề | Nguyên nhân | Cách sửa |
|---|---|---|---|
| 1 | `demo.py` khó đọc, khó chạy riêng từng thí nghiệm | Các dòng comment bật/tắt, mọi thứ chạy ở cấp module | Mỗi thí nghiệm là một hàm (`demo_chat`, `demo_image`, `demo_streaming`, `demo_caching`), chọn qua `python demo.py <tên>` |
| 2 | Prompt caching có thể không hoạt động đúng, log có dòng thừa | Ký tự `"C"` thừa ở đầu `long_text`, `print(type(message))` còn sót | Bỏ cả hai |
| 3 | `demo.py` chỉ chạy được trên máy gốc | Đường dẫn cứng `D:\Study\Claude\...` | Dùng đường dẫn tương đối từ vị trí file; ảnh nhận qua tham số dòng lệnh |
| 4 | `demo_batch.py` tốn tiền chỉ vì import file | Không có `if __name__ == "__main__":` | Đưa logic vào `main()` |
| 5 | Prompt batch sai chính tả | `stating` thay vì `starting` | Sửa |
| 6 | Request batch lỗi bị bỏ qua im lặng | `if entry.result.type == "succeeded"` không có `else` | Thêm nhánh `else` in loại kết quả (`errored`, `expired`, `canceled`) |
| 7 | Dòng usage luôn hiện trước dòng kết quả | `printContent` vừa in usage vừa trả text trong lúc dựng f-string | Hàm chỉ trả text (`message_text`), usage in trong vòng lặp |
| 8 | Nhãn thời gian thiếu đơn vị | `after 30` | `after 30s` |
| 9 | Hàm thừa | `add_assistant_message` trong `demo_batch.py` không dùng | Xoá |
| 10 | Chưa có file phụ thuộc | Thiếu `requirements.txt` | Thêm `anthropic`, `python-dotenv`; README dùng `pip install -r` |
| 11 | Khó đổi model khi benchmark | `chat()` dùng biến `model` toàn cục | Thêm tham số `model=model` vào chữ ký |
| 12 | Nguy cơ lộ API key | `key.txt` chứa key cạnh `.env` | Xoá `key.txt`; `.gitignore` có `.env`; `.env.example` chỉ có tên biến; kiểm tra bằng `git status` và `git check-ignore` trước khi commit |
| 13 | `SyntaxError: unterminated string literal` trong `demo.py` (hai lần) | Khi sinh file bằng heredoc, `\n` trong f-string bị biến thành xuống dòng thật | Sửa bằng công cụ Edit thành `\n` đúng nghĩa; kiểm tra bằng `ast.parse` sau mỗi lần sửa |
| 14 | `UnicodeEncodeError` khi chạy `bench_realtime.py` | Console Windows dùng cp1252 không in được tiếng Việt; lỗi xảy ra sau khi đã gọi API nên mất kết quả và tốn tiền chạy lại | `sys.stdout.reconfigure(encoding="utf-8")` ở đầu `main()` của cả hai script benchmark |
| 15 | Điểm quality 0.78 rồi 0.67 sai lệch | Grader `math` đòi trả lời đúng "11:20" không kèm giải thích, trong khi model trả lời đúng nhưng có giải thích | Chấm theo giờ HH:MM cuối cùng trong câu trả lời |
| 16 | Điểm vẫn 0.67 dù model trả đúng `11:20` | Khi sửa file, `\b` trong regex thành ký tự backspace nên regex không bao giờ khớp | Viết lại regex `(?<!\d)\d{1,2}:\d{2}(?!\d)`, tự kiểm tra bằng ba chuỗi mẫu trước khi chạy lại |
| 17 | NOTES.md ghi số liệu chưa trung thực | "Đã đo ở các lần chạy trước" cho chi phí vốn là số tính; độ trễ realtime ghi "chưa đo"; retry không nói rõ chưa có bằng chứng | Đo realtime thật (median 1.44s, $0.0082); ghi rõ chi phí batch là số tính từ token lần chạy batch; ghi rõ chưa tái hiện lỗi 429/529 |

## Còn mở

- **Quality chưa phân biệt được model.** Cả 4 model đạt 1.00 vì 3 prompt quá dễ. Cần thêm prompt khó hơn và nhiều lần lặp hơn mới so sánh được.
- **Mức giảm 50% của Batch API** dùng để tính chi phí batch (≈ $0.0038) chưa được đối chiếu với trang giá chính thức.
- **Retry 429/529** mới là kiến thức từ tài liệu, chưa tái hiện được lỗi thật.
- **Email commit** đang là `minhta11@fpt.com` (cấu hình git trên máy), khác email GitHub `tonanhminh1119@gmail.com`, nên commit có thể không gắn với tài khoản GitHub.
- **Key cũ:** nếu key trong `.env` từng bị dán vào chat hoặc file chia sẻ, nên tạo key mới và thu hồi key cũ.
- **Cảnh báo LF/CRLF** của git trên Windows: vô hại, có thể thêm `.gitattributes` nếu muốn thống nhất.
