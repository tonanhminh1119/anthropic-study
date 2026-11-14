# Notes T5: Tool use và Schema Design

Script thực hành: `demo_tools.py` (tool `get_member_messages`, dữ liệu giả `FAKE_DB`), model `claude-sonnet-5-5`.

## 1. Tool use là gì, và nó không phải gì

- Với tool tự định nghĩa (loại khoá này tập trung), Claude **không chạy gì cả**. Nó chỉ trả về block `tool_use` (có `id`, `name`, `input`) kèm `stop_reason: "tool_use"`. Code của mình chạy hàm rồi gửi kết quả lại bằng block `tool_result`.
- Có ba loại tool (đã đối chiếu docs):
  1. Tool tự định nghĩa: mình viết schema và mình chạy (loại khoá này tập trung).
  2. Tool Anthropic định nghĩa nhưng mình chạy: bash, text_editor, memory, computer use.
  3. Server tool do Anthropic chạy: web_search, code_execution, web_fetch.
- Claude không biết repo hay service nào của mình. Nó chỉ thấy schema trong `tools=[...]`. Hàm xử lý bên trong gọi DB, HTTP hay dữ liệu giả đều được.

## 2. Ánh xạ từ backend (.NET)

Ban đầu mình tưởng schema là gateway điều hướng request. Cách hiểu đúng hơn: schema giống file OpenAPI/Swagger, còn model mới là "router".

| Controller .NET | Tool definition |
|---|---|
| Tên action, route (`GetByMember`) | `name` |
| Tham số `memberId:int`, query, body | `input_schema` (JSON Schema) |
| Kiểu trả về `List<PersonalizedMessage>` | nội dung gửi lại trong `tool_result` |
| Comment `<summary>` | `description` |

Khác biệt với gateway:

| | Gateway backend | Tool use |
|---|---|---|
| Ai chọn route | code, theo rule cố định | model, theo xác suất |
| Dựa vào đâu | route table | `name`, `description`, `input_schema` |
| Ai thực thi | service sau gateway | code của mình (model chỉ yêu cầu) |
| Sai thì sao | 404 rõ ràng | có thể chọn sai tool hoặc điền sai tham số |

Điểm dễ nhầm nhất: XML comment trong C# xoá đi chương trình vẫn chạy y nguyên, còn `description` được model đọc lúc chạy và quyết định chọn tool. Nó là một phần logic, không phải chú thích.

## 3. Vòng lặp 5 bước

1. Gọi `messages.create` kèm `tools=[...]` và câu hỏi người dùng.
2. Claude trả về câu trả lời thường, hoặc block `tool_use` với `stop_reason: "tool_use"`.
3. Code tìm hàm theo `name` (`HANDLERS[b.name]`) và chạy với `input`.
4. Gửi kết quả về ở lượt user tiếp theo bằng block `tool_result`, `tool_use_id` khớp với `id` của `tool_use`.
5. Lặp lại cho đến khi `stop_reason` khác `tool_use` (thường là `end_turn`) thì in câu trả lời cuối. Nên đặt giới hạn số vòng (`for _ in range(5)`) để tránh lặp vô hạn.

Hệ quả: một câu hỏi tốn tối thiểu hai lần gọi API, và mỗi lần gửi lại toàn bộ lịch sử cùng định nghĩa tool, đều tính vào `input_tokens`.

**Quy tắc `tool_result`:** phải đứng ngay sau tin nhắn assistant có `tool_use`. Trong tin nhắn user đó, các block `tool_result` đứng trước, text (nếu có) đứng sau. Sai thứ tự thì API trả lỗi 400.

Carry-back: `messages.append({"role": "assistant", "content": resp.content})` gắn nguyên lượt trả lời của model (cả các block khác như thinking) vào lịch sử, không sửa.

## 4. Vai trò từng thuộc tính

- **`name`**: định danh tool, nên ngắn, đơn giản nhưng phân biệt được với tool khác. `get` quá chung, `get_personalized_messages_by_member` rõ. Phần bối cảnh để trong `description`, không nhét vào tên. Theo docs Define tools, tên phải khớp regex `^[a-zA-Z0-9_-]{1,128}$` (chữ, số, `_`, `-`, tối đa **128** ký tự). Docs còn gợi ý tiền tố theo dịch vụ, ví dụ `github_list_prs`. (Lúc đầu mình nhớ nhầm là 64 ký tự.)
- **`description`**: routing metadata. Nên nói khi nào dùng (và khi nào không), từng tham số nghĩa là gì và định dạng ra sao, tool trả về gì, giới hạn của tool. Docs khuyên ít nhất 3–4 câu; description hai câu trong `demo_tools.py` hơi ngắn. Mô tả mơ hồ thì model chọn nhầm hoặc không gọi. Mô tả sai thì hành vi sai.
- **`input_schema`**: JSON Schema của tham số (`type`, `properties`, `required`, `enum`). Mảng cần `items` để nói phần tử kiểu gì.
- **`required`**: tham số bắt buộc, model phải điền. Tham số không có trong `required` là tuỳ chọn, model có thể bỏ qua. Tham số bắt buộc cũng là lý do model hỏi lại người dùng thay vì đoán (xem thí nghiệm 2).
- **`enum`**: dùng khi tham số chỉ nhận một tập giá trị cố định (ví dụ loại sự kiện `birthday`, `welcome`), để model không bịa giá trị ngoài danh sách. Phần này mình chưa thử trong `demo_tools.py`.

Khi **không** bật `strict: true`, schema chỉ hướng dẫn model sinh đúng kiểu, không bảo đảm. Với strict tool use, input luôn khớp schema; trên Sonnet 5.5 docs khuyên dùng `tool_choice: auto` kèm `strict`. Dù vậy vẫn phải validate nghiệp vụ trong code (member có tồn tại không, có quyền truy cập không), vì tham số do model sinh ra là input không tin cậy, như request từ ngoài vào. Tool nguy hiểm (ví dụ xoá) nên hỏi xác nhận trước.

## 5. Báo lỗi tool cho model

Nếu hàm lỗi, đừng để chương trình chết. Gửi `tool_result` với `"is_error": True` và nội dung là thông báo lỗi để model biết và xử lý tiếp (xin lỗi, thử cách khác, hỏi lại). Trong `demo_tools.py` đó là nhánh `except`. Thông báo nên nói **nên làm gì tiếp** (ví dụ "member_id không tồn tại, hãy hỏi người dùng ID khác"), không chỉ "failed". Tên field `tool_use_id`, `content`, `is_error` đã đối chiếu docs, đúng như trong code.

**An toàn:** nội dung `tool_result` thường là dữ liệu từ ngoài (web, email, API) nên có thể chứa hướng dẫn độc hại (indirect prompt injection). Không coi nó là chỉ thị. Sẽ học kỹ ở tuần 4.

## 6. Bài tập thiết kế: hàm `random_char` làm tool

Bản đầu của mình có bốn lỗi, trong đó hai lỗi nặng:
1. **Description không khớp code.** Hàm kiểm tra `"req-" + c not in used_ids`, tức `used_ids` phải chứa ID đầy đủ như `"req-a"`, nhưng mình mô tả là "list of used character". Model sẽ truyền `["a", "b"]`, hàm không thấy trùng và trả về chữ đã dùng.
2. **Tên quá dài để đọc** (khoảng 77 ký tự). Tên này vẫn hợp lệ vì giới hạn là 128 ký tự, nhưng nên ngắn và phân biệt được: `pick_unused_batch_letter`.
3. **Thiếu `items`** cho mảng (`"items": {"type": "string"}`).
4. Lỗi chính tả trong description.

Thêm một lỗi ở phía hàm: nếu đủ 26 ID thì `while True` không thoát và treo. Với tool, input không tin cậy nên phải kiểm tra trước và trả lỗi (`is_error: true`) thay vì treo.

Hàm này **không nên là tool** trong demo vì code luôn gọi nó theo thứ tự cố định. Quy tắc: tool dành cho việc cần model quyết định có gọi hay không, khi nào, với tham số gì (tra DB, gọi API, hành động có tác dụng phụ).

## 7. Kết quả hai thí nghiệm

**Thí nghiệm 1: "Compare the messages of member 1 and member 2"**
```
stop_reason: tool_use
model asks: get_member_messages {'member_id': 1}
model asks: get_member_messages {'member_id': 2}
usage: input_tokens=424, output_tokens=101, thinking_tokens=0
stop_reason: end_turn
Member 1 has two messages, and member 2 has none. ...
```
- Một response chứa **hai block `tool_use`**: gọi song song. Vòng lặp duyệt qua mọi block nên xử lý được.
- **Quy tắc:** tất cả `tool_result` của cùng một lượt phải gửi lại trong **một tin nhắn user duy nhất**, mỗi cái khớp `tool_use_id` của nó.
- Member 2 rỗng thì model nói rõ chỉ thấy kết quả tra cứu rỗng, không biết lý do, và không bịa thêm.
- `input_tokens=424` cho một câu hỏi vài chục token: API thêm system prompt tool use (286 token cho Sonnet 5.5) cộng khoảng 140 token cho định nghĩa tool và câu hỏi. Cả hai bị tính ở mỗi lượt.

**Thí nghiệm 2: "What messages does Linh have?"**
```
stop_reason: end_turn
I can only look up messages by numeric member ID, and I can't search by name. I don't have an ID for Linh yet.
What is Linh's member ID? ...
```
- Model **không gọi tool, không đoán ID**, mà hỏi lại người dùng. Nguyên nhân chính: `description` ghi rõ không tìm theo tên và `member_id` là bắt buộc.
- Hành vi này không được bảo đảm tuyệt đối vì model chọn theo xác suất, nên code vẫn phải validate input.
- Thiết kế tốt hơn: thêm tool thứ hai `find_member_by_name` để model tự nối hai tool (tìm ID, rồi lấy tin nhắn). Mình chưa thử.

## 8. Phần học sau tool use (tóm tắt, chi tiết ở file khác)

Mỗi chủ đề chỉ giữ ở một nơi, ở đây chỉ nhắc ý chính và trỏ sang.

- **Context engineering** (pruning, compaction, clearing, subagent handoff; carry-back không mâu thuẫn với compaction/clearing; thinking block cũ trên Sonnet 5.5 vẫn bị giữ và tính token): xem [NOTES_Context_Engineering.md](NOTES_Context_Engineering.md), mục 2 và 3.
- **Workflow vs agent, CI/CD, human-in-the-loop** (đặt checkpoint ở chỗ rủi ro đủ lớn, không đặt ở mọi bước): xem [NOTES_Context_Engineering.md](NOTES_Context_Engineering.md), mục 4, và mục "Human-in-the-loop" trong `Production-Grade Prompting, Agents & Tool-use.txt`.
- **Agent construction** (3 wiring path: raw loop, Agent SDK, Managed Agents; 4 bước wiring chung; `settingSources` phải set tường minh): xem mục 4 trong `Production-Grade Prompting, Agents & Tool-use.txt`.
- **Agent memory và Skills** (4 scope in-context, external storage, summarized, stateless; chọn scope lúc thiết kế; Skill nạp theo description, subagent không tự thừa hưởng Skills): xem mục 5 trong `Production-Grade Prompting, Agents & Tool-use.txt`.

## 9. Còn lại và việc cần kiểm tra

- Chưa thử `enum`, `strict: true`, tool thứ hai nối với tool đầu, chưa thử nhánh `is_error` bằng lỗi thật.
- Việc cần làm trong code: nới description của `get_member_messages` lên 3–4 câu (nêu cả khi nào không dùng), cân nhắc bật `strict: true`.
- Các mục "cần kiểm tra" trước đây (giới hạn `name`, tên field, phí token, ba loại tool) đã được đối chiếu docs và cập nhật ở trên.
- Phần ở mục 8 ghi theo tài liệu khoá học, chưa đối chiếu docs chính thức. Cần kiểm tra lại: beta header của Managed Agents và Skills, mặc định của `settingSources` (đến tuần 3 khi học Claude Code và Agent SDK sẽ kiểm lại). Riêng việc thinking block cũ có bị bỏ không đã tra docs Thinking, ghi ở mục 3 của `NOTES_Context_Engineering.md`.
