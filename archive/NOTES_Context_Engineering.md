# Notes: Context Engineering

Nguồn: mục 3 trong `Production-Grade Prompting, Agents & Tool-use.txt` (ghi chú khoá học của mình), sắp xếp lại cho dễ ôn. Nối với [NOTES_T5_tool_use.md](NOTES_T5_tool_use.md) và carry-back ở T4.

## 1. Vấn đề cần giải quyết

- **Context window** là số token tối đa model xử lý được trong một request, tính cả input lẫn output.
- Trong một cuộc hội thoại, mỗi request phải gửi lại toàn bộ câu hỏi và response trước đó, nên context chỉ tăng. Tool result lớn làm nó phình nhanh hơn nữa.
- Khi vượt hạn mức, model trả output đã tạo được tới lúc đó kèm `stop_reason: model_context_window_exceeded` và cuộc trò chuyện dừng ở đây.
- Context engineering là chọn cách giữ, bỏ hoặc chuyển thông tin để context không chạm trần mà vẫn đủ cho task đang làm.

## 2. Bốn giải pháp

| | Làm gì | Hợp khi | Mất gì | Ví dụ ánh xạ |
|---|---|---|---|---|
| **Pruning** | Quay lại một message trước đó và tiếp tục từ đó, bỏ mọi thứ sau nó | Claude đã đi sai hướng, các lượt debug tới lui tích lũy mà không giúp ích cho task sau | Mọi thứ sau message được chọn, kể cả những gì Claude đã tìm hiểu; muốn có lại thì phải học lại | `git reset` về commit tốt rồi làm lại |
| **Compaction** | Tóm toàn bộ cuộc hội thoại thành bản cô đặc, chỉ giữ thông tin quan trọng | Gần chạm ngưỡng nhưng vẫn muốn làm tiếp feature hiện tại và giữ kiến thức đã tích lũy | Chi tiết không nằm trong bản tóm tắt | Build thư viện ra DLL: gọn, nhẹ nhưng không đọc lại được code bên trong |
| **Clearing** | Bắt đầu cuộc hội thoại mới hoàn toàn, không mang gì theo | Task kế tiếp không liên quan task cũ | Toàn bộ context session trước; muốn giữ gì phải cố định ở nơi khác như `CLAUDE.md` | Mở một project mới |
| **Subagent handoff** | Giao task cụ thể cho subagent có context window riêng; nó chỉ trả về một summary | Subagent tự cung tự cấp được; việc khám phá làm rối context chính nhưng kết quả trả về ngắn | Không thấy được quá trình, chỉ thấy lúc bắt đầu và kết quả tóm tắt | Giao cho một service riêng, chỉ nhận response |

Quy tắc chọn nhanh:
- Đi sai hướng: **pruning**.
- Gần đầy mà vẫn làm tiếp việc cũ: **compaction**.
- Việc mới hoàn toàn: **clearing**.
- Việc khám phá nhiều, kết quả ít: **subagent**.

## 3. Nối với carry-back (T4)

- Thinking block phải được gắn lại nguyên vẹn trong lịch sử. Sửa hoặc xoá thì signature không còn khớp và request tiếp theo bị từ chối.
- Vì vậy khi context phình, không xử lý bằng cách cắt thinking block khỏi lịch sử. Cách đúng là dùng các giải pháp ở mục 2, tức quản lý ở cấp cuộc hội thoại chứ không sửa từng block.
- Chi tiết "compaction/clearing xử lý thinking block cụ thể ra sao" mình chưa học, cần tra docs.

## 4. Workflow và agent

Cách mình đang hiểu (cần kiểm chứng): hai bên giống nhau ở input và output, khác nhau ở quá trình. Workflow đi theo pattern và constraint định sẵn xuyên suốt. Agent chỉ cần biết input và output, còn quá trình do model quyết định. Mình ví với SQL (schema và rule định nghĩa trước) và NoSQL (lưu thẳng object, append dần).

Chưa có ví dụ cụ thể và tiêu chí quyết định rõ ràng, phần này cần làm tiếp.

## 5. Checkpoint còn mở

1. Tool result lớn làm context phình: compaction, clearing, subagent hợp tình huống nào, đánh đổi là gì? **Đã trả lời** ở mục 2.
2. Một ví dụ nên dùng workflow và một ví dụ nên dùng agent; tiêu chí quyết định? **Mới trả lời một phần** (mục 4), chưa có ví dụ.
3. Đặt checkpoint con người ở đâu trong agent (liên hệ tool xoá), và vì sao không đặt ở mọi bước? **Chưa trả lời.**
4. Khi nào lưu thông tin ra memory ngoài context, chọn scope thế nào, scope sai gây hậu quả gì? **Chưa trả lời.**
5. Nối với T4: khi clearing hoặc compaction, vì sao không được động vào thinking block, và xử lý lịch sử thế nào thay vào đó? **Chưa trả lời đầy đủ** (xem mục 3).
