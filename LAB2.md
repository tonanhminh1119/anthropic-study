# Lab 2 — Agent xoá tin nhắn (vòng lặp tool use thủ công)

Code: [lab2_agent.py](lab2_agent.py) · Dữ liệu: [sample_data.json](sample_data.json) · Định nghĩa tool: [tools.json](tools.json)
Model: `claude-sonnet-5-5` · SDK: `anthropic` (Messages API, vòng lặp tự viết, không dùng Tool Runner)

## 1. Bài toán và cách chạy

Agent nhận yêu cầu bằng ngôn ngữ tự nhiên về tin nhắn của các member (xem, lọc theo loại, xoá). Có 3 tool:

| Tool | Tham số | Tác dụng |
|---|---|---|
| `find_member_by_name` | `name` | Trả về **chỉ `id` và `name`** của member (so khớp chính xác, phân biệt hoa thường) |
| `get_member_messages` | `member_id`, `event_type` (tuỳ chọn) | Trả về tin của member, có thể lọc theo loại |
| `delete_message` | `member_id`, `message_id` | Xoá một tin. **Tool duy nhất có tác dụng phụ** |

```powershell
py .\lab2_agent.py        # chạy lần lượt A, B, C, D
py .\lab2_agent.py A      # chỉ chạy một kịch bản (có thể: A C)
```

Mỗi kịch bản nạp lại `sample_data.json` nên độc lập với nhau. Kịch bản A, B tự trả lời bước xác nhận (`y` / `n`, in dòng `[auto]`) để trace chạy lại được. Chạy tay không có kịch bản thì bước xác nhận hỏi bằng `input()`.

## 2. Thiết kế theo từng yêu cầu của đề

| # | Yêu cầu | Hiện thực trong code |
|---|---|---|
| 1 | Vòng lặp giữ nguyên `resp.content`, gom `tool_result` trong một message | `run_agent`: gắn nguyên `resp.content` vào lượt assistant; mọi `tool_use` của một lượt được xử lý rồi trả về trong **một** message `user` |
| 2 | Dừng theo số vòng và ngân sách token, in rõ lý do | `MAX_ROUNDS`, `TOKEN_BUDGET`; `used` cộng `input_tokens + output_tokens` mỗi vòng; hàm `stopped()` tạo thông báo dừng |
| 3 | Lỗi lạ, tool lạ, input sai schema, member không tồn tại | `_run_tool`: kiểm tra tên tool, `jsonschema.validate` theo `input_schema` trong `tools.json`, hàm tool `raise ValueError` với thông báo chỉ cách làm tiếp → trả `is_error: true` |
| 4 | Kiểm tra `message_id` thuộc `member_id` | `delete_message` chỉ tìm trong danh sách tin của đúng member đó, so độ dài trước/sau, không xoá được thì báo lỗi |
| 5 | Human-in-the-loop trước khi xoá | `ask_user()` gọi trong `_run_tool` ngay trước `delete_message`; trả lời khác `y` thì `tool_result` là `"User declined"` + `is_error` |
| 6 | Validate output cuối bằng JSON schema, sửa tối đa 1 lần | `FINAL_SCHEMA`, `parse_final`, `run_with_validation` (system prompt yêu cầu JSON; sai thì gửi đúng 1 lượt yêu cầu sửa) |
| 7 | Trace từng bước | `[round N] stop=... tokens=...` mỗi vòng, `tool=... input=... -> ok/ERR` mỗi lần gọi tool |

Thứ tự kiểm tra trong `_run_tool`: tool lạ → sai schema → xác nhận của người dùng → chạy. Validate nằm **trước** HITL để không hỏi người dùng xác nhận một lệnh xoá mà input vốn đã không hợp lệ.

## 3. Trace bốn kịch bản

Dữ liệu ban đầu của Linh (member id 3): `[(1, 'birthday'), (2, 'welcome')]`.

### A — Xoá tin welcome của Linh, trả lời `y`

```
Linh before: [(1, 'birthday'), (2, 'welcome')]
[round 1] stop=tool_use tokens=894
  tool=find_member_by_name input={'name': 'Linh'} -> ok
[round 2] stop=tool_use tokens=2049
Xóa message 2 của member 3? (y/n) y   [auto]
  tool=delete_message input={'member_id': 3, 'message_id': 2} -> ok
[round 3] stop=end_turn tokens=3282
RESULT: {"deleted": true, "message_id": 2, "summary": "Đã xoá tin nhắn welcome (id 2) của Linh."}
Linh after:  [(1, 'birthday')]
```

Xoá đúng một tin. Ở trace này model bỏ qua `get_member_messages` vì kết quả của `find_member_by_name` đã chứa danh sách tin kèm `type`, nên chỉ cần 2 vòng tool. JSON cuối hợp lệ ngay lần đầu.

> **Lưu ý:** kết quả không lặp lại hoàn toàn giữa các lần chạy. Ở lần chạy lại, model gọi thêm `get_member_messages(member_id=3, event_type='welcome')` trước khi xoá (4 vòng, 4662 token thay vì 3 vòng, 3282 token). Kết quả cuối giống nhau.

### B — Cùng yêu cầu, trả lời `n`

```
[round 1] stop=tool_use tokens=894
  tool=find_member_by_name input={'name': 'Linh'} -> ok
[round 2] stop=tool_use tokens=2051
Xóa message 2 của member 3? (y/n) n   [auto]
  tool=delete_message input={'member_id': 3, 'message_id': 2} -> ERR
[round 3] stop=end_turn tokens=3298
RESULT: {"deleted": false, "message_id": 2, "summary": "Yêu cầu xoá tin nhắn welcome (id 2) của Linh đã bị từ chối nên tin nhắn chưa được xoá."}
Linh after:  [(1, 'birthday'), (2, 'welcome')]
```

Không xoá gì. Model nhận `"User declined"`, **không thử xoá lại**, và báo lại đúng sự việc. Lưu ý: `message_id` là `2` dù `deleted` là `false`, vì model hiểu trường này là "tin được nhắm tới". Xem mục 6.

### C — Xoá tin welcome của Zed (member không tồn tại)

```
[round 1] stop=tool_use tokens=894
  tool=find_member_by_name input={'name': 'Zed'} -> ERR
[round 2] stop=tool_use tokens=1873
  tool=find_member_by_name input={'name': 'zed'} -> ERR
[round 3] stop=end_turn tokens=2962
RESULT: {"deleted": false, "message_id": null, "summary": "Không tìm thấy thành viên nào tên 'Zed' nên chưa xoá tin nhắn nào; vui lòng kiểm tra lại tên."}
Linh after:  [(1, 'birthday'), (2, 'welcome')]
```

Không bịa ID, không gọi `delete_message`. Thông báo lỗi của tool ("Check the spelling or ask the user") khiến model thử lại một lần với `'zed'` viết thường rồi mới báo cho người dùng. Vì `find_member_by_name` so khớp phân biệt hoa thường nên lần thử lại này không giúp được gì và tốn thêm khoảng 1100 token.

### D — Giới hạn `max_rounds=2`

```
[round 1] stop=tool_use tokens=894
  tool=find_member_by_name input={'name': 'Linh'} -> ok
[round 2] stop=tool_use tokens=2060
Xóa message 2 của member 3? (y/n) y   [auto]
  tool=delete_message input={'member_id': 3, 'message_id': 2} -> ok
RESULT: "(dừng: hết 2 vòng; đã thực thi: delete_message({\"member_id\": 3, \"message_id\": 2}))"
Linh after:  [(1, 'birthday')]
```

Vòng lặp dừng đúng ở 2 vòng, không treo, không im lặng. Nhưng **tin đã bị xoá thật** trước khi vòng lặp dừng: `delete_message` chạy ở vòng 2 (vòng cuối được phép) rồi mới hết lượt, nên model không có lượt nào để báo lại. Phiên bản đầu của code chỉ trả `"(dừng: hết 2 vòng)"`, người gọi không biết việc xoá đã xảy ra. Sau khi sửa, thông báo dừng liệt kê các hành động có tác dụng phụ đã thực thi (xem mục 5).

> **Lưu ý:** trạng thái cuối của D phụ thuộc đường đi model chọn trong lần chạy đó. Cả hai lần chạy D đều xoá ở vòng 2, nhưng nếu model đi theo đường dài như lần chạy lại của A (tìm → lọc → xoá) thì giới hạn 2 vòng sẽ cắt **trước khi xoá** và `Linh after` còn nguyên. Cùng một cấu hình có thể cho hai trạng thái cuối khác nhau.

## 4. Kiểm tra bổ sung

- **Validate input** (không gọi API): gọi `_run_tool` với một khối giả `delete_message` thiếu `message_id`:
  ```
  {'type': 'tool_result', 'tool_use_id': 't1', 'content': "Invalid input: 'message_id' is a required property", 'is_error': True}
  ```
  Không hiện câu hỏi `y/n`, đúng thứ tự validate trước HITL.
- **Yêu cầu mơ hồ** ("Delete a message of Minh"): model tìm Minh, liệt kê 3 tin và hỏi lại tin nào, **không** gọi `delete_message`.
- **Hội thoại nhiều lượt** (dùng chung một `messages`, trả lời "tin số 2", rồi `n` ở bước xác nhận): lượt hai không gọi lại `find_member_by_name` vì model nhớ ngữ cảnh; sau khi từ chối, model báo tin vẫn còn nguyên.

## 5. Lỗi đã gặp và cách sửa

| Lỗi | Cách phát hiện | Cách sửa |
|---|---|---|
| `"type": "enum"` không phải JSON Schema hợp lệ | Đọc code | `{"type": "string", "enum": [...]}` |
| Tên tool, schema và hàm Python lệch nhau (tham số `name` / `member_id` bị đảo giữa hai tool) | Đọc code | Thống nhất tên, tham số, `HANDLERS` |
| `description` của tool bị copy nhầm; ở `delete_message` còn khiến model có thể xoá khi người dùng chỉ hỏi xem tin | Đọc code | Viết lại: "Use only when the user explicitly asks to delete a message" |
| `open()` không chỉ định encoding, trên Windows dùng `cp1252` nên "Hùng" thành `HÃ¹ng` (so khớp tên thất bại, model còn nhận xét "lỗi mã hoá ký tự") | Chạy thật (câu trả lời của model) rồi kiểm chứng bằng cách đọc file hai kiểu | `encoding='utf-8'` |
| Lỗi `list index out of range` mơ hồ; model gọi lại đúng lệnh vừa lỗi | Chạy thật (trace câu hỏi về Linh khi chưa có dữ liệu) | Hàm tool `raise ValueError` với thông báo rõ và chỉ cách làm tiếp |
| Thông báo "không tìm thấy" viết cứng chữ `'Linh'` và trả như kết quả thành công | Đọc code | Dùng `{name}` thật, `raise` để thành `is_error` |
| `delete_message` trả `{"deleted": True}` kể cả khi không xoá được gì | Đọc code | So độ dài danh sách trước và sau khi lọc |
| `used += ...` trong hàm nhưng `used` khai báo ngoài hàm (`UnboundLocalError`), và nếu để toàn cục thì ngân sách cộng dồn qua các câu hỏi | Đọc code | Đặt `used = 0` đầu `run_agent` |
| Dữ liệu mẫu của Linh chưa có tin `welcome`, kịch bản A, B không có gì để xoá | Đối chiếu đề với dữ liệu | Thêm một tin `welcome` cho Linh |
| Kịch bản D: tool có tác dụng phụ chạy ở vòng cuối rồi vòng lặp dừng im lặng | Chạy thật (`Linh after` thay đổi dù kết quả là "dừng") | Thêm `SIDE_EFFECT_TOOLS` và `done`; `stopped()` đưa các hành động đã thực thi vào thông báo dừng |

## 6. Quyết định thiết kế và hạn chế đã biết

- **Ngân sách token là ngân sách "mềm".** Chi phí của một lần gọi chỉ biết sau khi gọi xong, nên ngân sách chỉ chặn các lần gọi **tiếp theo**. Trong thử nghiệm với `TOKEN_BUDGET = 1000`, agent dừng ở 1753 token. Ngoài ra `input_tokens` mỗi vòng gồm cả lịch sử gửi lại, nên mỗi vòng sau đắt hơn vòng trước (894 → 2049 → 3282 ở kịch bản A). Ngân sách tính riêng cho từng lần gọi `run_agent`, không cộng dồn qua các lượt hội thoại.
- **Ngân sách và số vòng không thay thế HITL.** Tool chạy xong rồi mới kiểm tra giới hạn (kịch bản D). Bảo vệ cho hành động phá hủy là bước xác nhận của người dùng, không phải giới hạn vòng lặp.
- **`message_id` khi không xoá được gì** hiện model tự diễn giải (B trả `2`, C trả `null`). Nếu muốn nhất quán thì định nghĩa trong system prompt: "ID của tin đã xoá, hoặc `null` nếu không xoá tin nào".
- **`find_member_by_name` phân biệt hoa thường** (xem kịch bản C). Dùng `casefold()` sẽ bỏ được vòng thử lại.
- **Câu hỏi xác nhận chỉ hiện ID** ("Xoá message 2 của member 3?"). Người dùng không thấy nội dung tin. Nên tra `FAKE_DB` để hiển thị tên và nội dung tin trước khi hỏi, vì ID do model sinh ra không hoàn toàn đáng tin.
- **Lỗi tool được gom bởi `except Exception`**, nên bug thật trong code (ví dụ `TypeError`) cũng bị gửi cho model như một lỗi bình thường. Nên tách `ValueError` (lỗi nghiệp vụ) khỏi lỗi khác.
- **Structured outputs** (`output_config.format`) có thể ép định dạng JSON cuối ngay từ phía server và bỏ được bước sửa lỗi; bài này tự validate bằng `jsonschema` đúng theo yêu cầu của đề.

## 7. Khi nào dùng workflow, agent, subagent (áp vào bài này)

| | Là gì | Dùng khi | Với bài xoá tin nhắn |
|---|---|---|---|
| **Workflow** | Code quyết định thứ tự các bước; model chỉ được gọi ở những điểm cố định | Quy trình đã biết trước và luôn giống nhau; cần chi phí và hành vi dễ dự đoán | Nếu mọi yêu cầu đều là "xoá tin loại X của member Y" thì làm workflow: code tự gọi `find_member_by_name` → hỏi xác nhận → `delete_message`; model chỉ trích xuất `name` và `event_type` từ câu hỏi và viết tóm tắt. Rẻ hơn (không có vòng lặp mở) và không thể "đi lạc" |
| **Agent** | Model tự chọn tool kế tiếp trong vòng lặp cho đến khi xong | Số bước không biết trước; yêu cầu đa dạng; cần tự xử lý lỗi và hỏi lại | Bài này chọn agent vì yêu cầu đa dạng (xem, lọc, xoá, mơ hồ, member không tồn tại). Trace cho thấy lợi ích: ở A model tự bỏ qua `get_member_messages`; ở C tự đổi cách thử; với "Delete a message of Minh" thì tự hỏi lại. Cái giá: khó dự đoán (C thử lại thừa) và cần các lớp bảo vệ ngoài model (HITL, validate, giới hạn vòng/token) |
| **Subagent** | Một agent phụ có context riêng, nhận một việc con và chỉ trả về bản tóm tắt cho agent chính | Việc con tạo nhiều context nhiễu hoặc chạy song song được; hoặc cần tách quyền hạn | **Chưa cần** ở bài này: 3 tool nhỏ, cả hội thoại chỉ ~3k token. Nên dùng nếu mở rộng sang "dọn các tin welcome trùng nội dung của hàng nghìn member": một subagent chỉ-đọc quét và trả danh sách ứng viên, agent chính (có HITL) mới được xoá. Cách này giữ context của agent chính gọn và tách quyền xoá khỏi quyền đọc |

**Nhận xét về workflow.** Workflow phù hợp khi các yêu cầu có cùng một dạng và **đường đi xử lý biết trước**, ví dụ "xoá tin loại X của member Y". Code cố định chuỗi: tìm member → lọc tin theo loại → xác nhận → xoá; LLM chỉ dùng một lần để trích `member_name` và `event_type` từ câu tự nhiên (nếu đầu vào đã có cấu trúc sẵn như form hay API thì không cần LLM). So với agent, workflow rẻ hơn (1 lần gọi thay vì 3–4 vòng, khoảng 3.3k–4.7k token ở kịch bản A), dễ đoán hơn (đường đi cố định nên không dao động giữa các lần chạy như agent, xem lưu ý ở kịch bản A và D) và đảm bảo bước xác nhận luôn chạy, nhưng kém linh hoạt với yêu cầu ngoài khuôn (mơ hồ, nhiều tin cùng loại khớp, member không tồn tại), và phải tự viết quy tắc cho từng trường hợp đó. Tiêu chí quyết định không phải là "đơn giản" mà là đường đi có biết trước hay không.

Quy tắc chọn ngắn gọn: bắt đầu từ cách đơn giản nhất đáp ứng được bài toán (một lần gọi → workflow → agent → nhiều agent), và chỉ nâng cấp khi thật sự cần sự linh hoạt hoặc cô lập context.
