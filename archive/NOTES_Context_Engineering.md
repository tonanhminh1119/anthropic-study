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

**Carry-back không mâu thuẫn với compaction/clearing.** Carry-back chỉ cấm sửa, tóm tắt hoặc xoá lẻ từng thinking block còn nằm trong lịch sử đang gửi. Compaction và clearing đều mở một context mới (khác nhau ở chỗ có mang summary của phần cũ hay không; compaction ở nhiều công cụ vẫn cùng cuộc trò chuyện nhưng lịch sử bị thay bằng summary), nên thinking block cũ không còn trong lịch sử, không có gì để mismatch. Giảm context thì làm ở ranh giới giữa các lượt đã hoàn tất. Không nén hay cắt giữa lượt tool-use đang dở (đã có `tool_use` kèm thinking block, đang chờ `tool_result`), vì block đó vẫn phải được gửi lại nguyên vẹn.

**Thinking block của các lượt cũ có bị API tự bỏ không?** Tuỳ model (tra từ docs Thinking). Sonnet 5.5 thuộc nhóm "giữ tất cả các lượt" (Sonnet 4.6 trở lên): thinking block của các lượt trước vẫn nằm trong context và bị tính như input token, chỉ các model cũ mới tự bỏ. Nên trên Sonnet 5.5 chi phí thinking tích luỹ theo hội thoại (nối với câu 2 của T4). Quy tắc ba mức:
- **Bắt buộc** gửi lại thinking block trong lượt tool-use đang chạy.
- **Khuyến nghị** gửi lại mọi thứ giữa các lượt.
- **Được phép** bỏ thinking của các lượt cũ khi không đang tool use, nhưng không bỏ một block nằm giữa hai block mình giữ.

Muốn đổi mặc định thì dùng chiến lược xoá thinking block `clear_thinking_20251015` trong context editing, do API xử lý chứ không phải mình sửa từng block.

## 4. Workflow và agent

Khác nhau ở **ai quyết định luồng điều khiển**:
- **Workflow:** các bước do code mình định sẵn (như state machine hay pipeline), model chỉ làm việc trong từng bước.
- **Agent:** model tự quyết định bước tiếp theo trong vòng lặp, dựa trên kết quả trung gian.

Với agent, quá trình rất quan trọng (giới hạn số vòng, trace log, kiểm soát chi phí), chỉ là mình không viết sẵn nó.

**Tiêu chí quyết định:**
- Các bước biết trước và lặp lại được: workflow (dễ dự đoán, rẻ hơn, dễ test). Ví dụ: xử lý hoá đơn (trích xuất, kiểm tra, ghi DB).
- Các bước phụ thuộc kết quả trung gian và không liệt kê trước được: agent. Ví dụ: điều tra một bug trong codebase.

**Ví dụ gộp: CI/CD** (chứa cả ba khái niệm trong cùng một hệ thống)

| Khái niệm | Trong CI/CD |
|---|---|
| Workflow | Pipeline build → test → quét bảo mật → deploy staging → deploy prod. Các bước và thứ tự định sẵn trong file YAML; mỗi lần chạy giống nhau, dễ dự đoán, dễ test |
| Agent | Khi pipeline fail và muốn tự động tìm nguyên nhân: đọc log, xem diff của commit, chạy lại một test, kiểm tra config. Bước tiếp theo phụ thuộc kết quả bước trước và không liệt kê trước được |
| Human-in-the-loop | Bước manual approval trước khi deploy prod. Không đặt ở mọi stage, chỉ đặt ở chỗ hành động khó hoàn tác (giống tool xoá) |

Thiết kế thực tế hay gặp là kết hợp: giữ pipeline là workflow, chỉ cắm một agent vào đúng điểm cần suy luận mở (phân tích nguyên nhân fail), còn deploy vẫn do pipeline cố định và có cổng phê duyệt. Nguyên tắc: dùng agent ở chỗ cần khả năng thích nghi, dùng workflow ở chỗ cần tính nhất quán và an toàn.

Lưu ý: ví dụ SQL/NoSQL mình dùng ban đầu chưa đúng, vì chúng khác nhau ở hình dạng dữ liệu (schema chặt hay không), không phải ở luồng điều khiển.

## 5. Checkpoint còn mở

1. Tool result lớn làm context phình: compaction, clearing, subagent hợp tình huống nào, đánh đổi là gì? **Đã trả lời** ở mục 2.
2. Một ví dụ nên dùng workflow và một ví dụ nên dùng agent; tiêu chí quyết định? **Đã trả lời** ở mục 4.
3. Đặt checkpoint con người ở đâu trong agent (liên hệ tool xoá), và vì sao không đặt ở mọi bước? **Đã trả lời** (mục 4 và mục "Human-in-the-loop" trong `Production-Grade Prompting, Agents & Tool-use.txt`): đặt ở chỗ hành động khó hoàn tác (trước tool xoá, sau planning, khi output bất thường); không đặt ở mọi bước vì người sẽ duyệt qua loa và agent mất lợi thế tự động.
4. Khi nào lưu thông tin ra memory ngoài context, chọn scope thế nào, scope sai gây hậu quả gì? **Chưa trả lời.**
5. Nối với T4: khi clearing hoặc compaction, vì sao không được động vào thinking block, và xử lý lịch sử thế nào thay vào đó? **Đã trả lời** ở mục 3: không sửa lẻ block vì signature; giảm context bằng cách thay thế hoặc cắt cả lịch sử ở ranh giới giữa các lượt đã hoàn tất.
