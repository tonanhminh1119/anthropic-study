# Notes Week 4 Day 5: Production hardening (Testing & Tracing, Failure Handling & Model Selection, Cost & Orchestration)

Nguồn hiện có: bài "Testing and tracing" (bốn mức test, tracing, routing giữa hai kiểu retrieval, bảng tham chiếu). Phần B (Failure Handling), Phần C (Model Selection) và Phần D (Cost & Orchestration) nằm ở cuối file. Bài bảo mật (prompt injection, quyền tối thiểu, hook, sandbox) đã tách sang [NOTES_W4D6_Securing_Integration.md](NOTES_W4D6_Securing_Integration.md). **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung của mình, cần đối chiếu docs khi áp dụng.

Nối với notes cũ: eval và judge ở [NOTES_W4D3_Evals_Judges.md](NOTES_W4D3_Evals_Judges.md) mục 3, 4, 12.1; pipeline `run_eval` và chỗ còn thiếu "lưu kết quả để so phiên bản" ở [NOTES_W4D2_Eval_Dataset_Running.md](NOTES_W4D2_Eval_Dataset_Running.md) mục 9, 12; `temperature` và prefill bị 400 ở mục 7 cùng file; trace và lỗi đã gặp ở [LAB2.md](../labs/lab2/LAB2.md) mục 3, 4, 5; kiểm thử MCP ở [LAB3.md](../labs/lab3/mcp-server/LAB3.md) mục 5; classical RAG và agentic search ở [NOTES_W3D2_Prompt_Caching_RAG.md](NOTES_W3D2_Prompt_Caching_RAG.md) mục 2.

## 1. Câu hỏi hướng dẫn và tài liệu đã đủ chưa

Bảy câu hỏi của module, đánh giá theo tài liệu đã có. Cập nhật dần khi có bài mới.

| # | Câu hỏi | Tài liệu | Trạng thái |
|---|---|---|---|
| 1 | Bốn mức test kiểm gì, ví dụ từ Lab 2 hoặc Lab 3 | Bài định nghĩa đủ bốn mức; ví dụ Lab là phần mình ánh xạ | **Đủ** (mục 3, 4) |
| 2 | Trace ghi gì, phân biệt lỗi model với lỗi integration thế nào | Ghi gì: đủ. Cách phân biệt: bài chỉ cho ví dụ, **không nêu quy tắc** | **Đủ một nửa** (mục 5, 6) |
| 3 | Hồi quy là gì, đổi prompt hoặc model thì mức test nào bắt đầu tiên | Bài **không định nghĩa hồi quy** và không nói mức nào bắt đầu tiên | **Thiếu**; mục 7 là suy luận từ notes cũ |
| 4 | Các bài "Watch Out" cảnh báo bẫy nào | Mục Watch Out của khóa là một **case "Why this broke"** cuối bài (xác nhận của bạn). Bản dán đầu chỉ có ba khung "Handles well / Adds cost / Use a different approach"; case gửi bù sau cho **ba trong bốn** bài | **Đủ**, trừ một ngoại lệ do **cấu trúc khóa**: Testing (mục 8.1), Failure Handling (mục 21.2), Cost & Orchestration (mục 44.1) có Watch Out. **Model Selection không có Watch Out riêng**: trong khóa, Failure Handling và Model Selection là một module chung, mục lục chỉ có Watch Out một lần, đặt sau Teaching của Failure Handling (mục 31). Bảng bẫy ngầm ở mục 8, 21, 31, 44 là phần mình suy ra thêm, đứng cạnh case |
| 5 | Retriable và terminal, người dùng nhận gì | Nhóm lỗi: đủ. Người dùng nhận gì: bài chỉ nói "caller" nhận gì, **không nêu thông báo cho người dùng cuối** | **Đủ một nửa** (Phần B, mục 19) |
| 6 | Tiêu chí chọn model; haiku từ chối `temperature`/prefill nói gì | Tiêu chí: đủ. Đổi model làm vỡ gì ngoài chất lượng: bài **không nói**, và còn nói "đổi model không cần viết lại ứng dụng", trái với kết quả thử ở W4D2 | **Đủ một nửa** (Phần C, mục 30) |
| 7 | Đo cost, latency, độ tin cậy khi nhiều agent; khi nào chạy song song; đối chiếu trần ngân sách W4D3 mục 2.2 | Khi nào song song: đủ. Đo: có ba chỉ số mỗi lần gọi và bảng so sánh, **thiếu cách gộp theo từng agent và theo request**. Đối chiếu với trần ngân sách: bài không làm, phần này là của mình | **Đủ phần lớn** (Phần D, mục 41 đến 43) |

---

# Phần A. Testing & Tracing

## 2. Bài này đứng ở đâu

W4D1 đến W4D3 cho ta **một con số** (điểm eval). Bài này nói con số đó chưa đủ, vì hai lý do:

1. Điểm thấp **không nói lỗi nằm ở đâu** ("a failed eval tells you something is wrong but does not tell you where it failed").
2. Điểm đạt **không bảo đảm không có chỗ gãy** trong workflow ("a passing eval hiding a break somewhere in the workflow").

Vì vậy dưới eval cần thêm hai thứ: **test tách theo loại lỗi** (bốn mức) và **trace** cho thấy bước nào sinh ra kết quả xấu.

```
eval (điểm)      -> "tốt đến đâu"
test 4 mức       -> "loại lỗi nào, và mức nào nhìn thấy nó"
trace            -> "bước nào trong lần chạy này sinh ra kết quả xấu"
```

**[ngoài tài liệu]** Vì sao điểm đạt vẫn có thể che lỗi: nếu bước truy xuất hỏng và trả 0 đoạn, model vẫn có thể trả lời từ kiến thức sẵn có và grader vẫn chấm khá. Điểm vẫn ổn trong khi một mắt xích đã gãy; đến khi câu hỏi cần đúng dữ liệu đó mới lộ ra. Chỉ trace (hoặc test ở đúng mối nối) thấy được.

## 3. Bốn mức test **[docs]**

| Mức | Cô lập cái gì | Không bắt được |
|---|---|---|
| **Unit** | Một hàm (parser, tool wrapper) chạy riêng | Mọi thứ về cách các thành phần khớp với nhau |
| **Functional** | Một lần gọi Claude trả về **đúng hình dạng** cho một input: đúng trường, đúng kiểu, parse được | Lỗi ở hệ thống xung quanh lần gọi đó |
| **Integration** | **Mối nối** giữa hai thành phần, ví dụ kết quả retrieval đi vào lần gọi model | Hành vi cả luồng chỉ lộ ra khi chạy trọn vẹn |
| **End-to-end** | Cả luồng như người dùng chạy, từ input đến output | **Chỗ gãy cụ thể**, vì chỉ thấy kết quả cuối; chậm nhất và khó khoanh vùng nhất |

Điểm bài nhấn: **phần lớn lỗi âm thầm ở production nằm ở mức integration**, vì mỗi bên có thể qua test của riêng mình trong khi chỗ nối giữa hai bên đã hỏng.

Ánh xạ .NET **[ngoài tài liệu]**: unit test (xUnit) cho một class; functional ≈ test một endpoint với contract (schema) của response; integration ≈ test có hai thành phần thật nối nhau (ví dụ service + DB hoặc service + service); E2E ≈ UI test hoặc test qua cả gateway. Điểm khác: ở đây có một thành phần **không tất định** (model) trong ba trên bốn mức, nên mục 4.5 và 7 ghi lại những chỗ analogy lệch.

## 4. Ví dụ từ Lab 2 và Lab 3 **[ngoài tài liệu]**

Bài không dùng Lab của mình; phần này là ánh xạ của mình. Lưu ý trước: ở Lab 2 và Lab 3 **chưa có bộ test tự động nào đặt tên theo bốn mức**; các kiểm tra là script chạy tay hoặc quan sát trace. Ánh xạ dưới đây là "kiểm tra đó thuộc mức nào", không phải "test suite đã có".

### 4.1 Unit: một hàm, không gọi API

| Lab | Ví dụ | Vì sao là unit |
|---|---|---|
| Lab 2 mục 4 | Gọi `_run_tool` với một khối giả `delete_message` thiếu `message_id`, nhận `Invalid input: 'message_id' is a required property`, `is_error: True`, và **không hiện câu hỏi y/n** | Một hàm, input giả, không gọi model. Kiểm luôn thứ tự "validate trước HITL" |
| Lab 2 mục 5 | `delete_message` so độ dài danh sách trước và sau khi lọc để không báo `deleted: true` oan | Logic của riêng một tool |
| Lab 3 mục 5.3 | `priority` sai bị **zod chặn trước khi gọi API** | Validate của riêng wrapper |
| W4D2 mục 23 | `validate_json`, `validate_python`, `validate_regex` | Code grader cũng là code, test như code (và issue #15, #16 là bug của grader) |

### 4.2 Functional: một lần gọi Claude, kiểm hình dạng

| Lab | Ví dụ | Kiểm gì |
|---|---|---|
| Lab 2 | `parse_final` và `FINAL_SCHEMA` (`jsonschema.validate`), sai thì sửa tối đa 1 lần | Output cuối của một lần gọi có đúng schema không |
| W4D3 mục 6 | Judge phải trả JSON đủ `strengths`, `weaknesses`, `reasoning`, `score` 1–10 | Hình dạng output của lần gọi judge |
| W4D2 mục 30 | `probe_model_params.py`: gọi `claude-haiku-5-5` với `temperature` và prefill | Lần gọi có được API chấp nhận không (400 hay OK) |

Functional kiểm **hình dạng**, không kiểm "nội dung có hay không" (cái đó của eval).

### 4.3 Integration: mối nối giữa hai thành phần

Đây là mức bài nói chứa phần lớn lỗi âm thầm, và Lab của mình có hai ví dụ rất rõ:

| Lab | Mối nối | Chuyện đã xảy ra | Vì sao không mức nào khác bắt được |
|---|---|---|---|
| **Lab 3 mục 5.2** | Claude Code / Inspector → `index.js` (MCP server) → fake-api | Tool trả `API 401`. fake-api chạy đúng (`curl` với cùng token trả 200), `index.js` cũng đúng; nhưng biến `FAKE_API_TOKEN` **không truyền xuống process con** (danh sách trắng biến môi trường), nên code gửi `Bearer undefined` | Unit test của `index.js` (token đã gán sẵn) pass; test fake-api pass. Chỗ gãy là **cách khởi chạy** nối hai bên |
| **Lab 2 mục 5** | File `sample_data.json` → code tool → model | `open()` không chỉ định encoding, trên Windows thành `HÃ¹ng`, so khớp tên thất bại, và model còn báo "lỗi mã hoá ký tự" | Hàm so khớp tên đúng với chuỗi đúng; file dữ liệu đúng; hỏng ở chỗ **đọc file vào bộ nhớ** |

Hai ví dụ này khớp với câu của bài: "each side can pass its own tests while the handoff between them is broken".

**Test integration có sẵn:** Lab 3 mục 5.3 là một test integration thật: một client MCP thật spawn `index.js` qua stdio, chạy trên bản sao `api.js` ở cổng 4100, rồi gọi lần lượt list, get, create, delete, delete lần hai (404), `priority` sai, token sai (401). Nó kiểm **cả hai mối nối** (client ↔ server qua JSON-RPC, server ↔ API qua HTTP + token).

### 4.4 End-to-end: cả luồng như người dùng chạy

| Lab | Ví dụ | Điều chỉ lộ ra ở mức này |
|---|---|---|
| Lab 2 mục 3 | Bốn kịch bản A, B, C, D từ câu tự nhiên đến `RESULT` và `Linh after` | **Kịch bản D:** tool có tác dụng phụ chạy ở vòng 2 rồi vòng lặp dừng im lặng; tin đã bị xoá thật mà kết quả chỉ nói "dừng". Phát hiện nhờ đối chiếu `Linh after`, không phải nhờ unit test của hàm nào |
| Lab 3 mục 6 | Dùng thật trong Claude Code (permission, hook, skill) | Hành vi của cả khối model + cấu hình quyền |

Đồng thời kịch bản D minh hoạ **điểm yếu của E2E**: nó cho biết "Linh after" sai trạng thái nhưng không nói bước nào gây ra. Phải có trace (mục 5) mới biết đó là vòng 2 và `delete_message`. Đúng câu của bài: "it sees only the final result".

### 4.5 Chỗ analogy lệch khi trong luồng có model **[ngoài tài liệu]**

1. **E2E của agent nên kiểm trạng thái cuối, không kiểm đường đi.** Kịch bản A chạy hai lần cho hai đường khác nhau (3 vòng 3282 token, 4 vòng 4662 token) nhưng cùng kết quả. Test khẳng định "gọi đúng 2 tool theo thứ tự này" sẽ gãy oan; test khẳng định "`Linh after` còn đúng tin `birthday`" thì ổn định.
2. **Functional test nên khẳng định hình dạng, không so chuỗi**, vì cùng input có thể ra chữ khác (W4D3 mục 4.2: exact match giòn).
3. **Unit test không bao giờ gọi model**, nên không bao giờ bắt được thay đổi do đổi prompt hoặc model. Chi tiết ở mục 7.
4. **Làm integration ổn định:** đặt một model giả (trả đáp án ghi sẵn) ở mối nối để kiểm đường dây (retrieval → build prompt → parse) mà không phụ thuộc dao động của model; rồi một bộ nhỏ chạy với model thật để kiểm phần nối với model. Đây là gợi ý của mình, bài không nói.

## 5. Tracing **[docs]**

Test cho biết **có** lỗi; trace cho biết **bước nào** gây ra. Một trace ghi mỗi bước của một lần chạy:

- **prompt** (cái gửi cho model),
- **tool call** (gọi gì, tham số gì),
- **output trung gian** (kết quả từng bước),
- **thời gian** từng bước.

Trace trong bài, đọc như một dòng thời gian:

```
[trace run_id=8f21c]  case: "Where is my refund?"
  step 1  retrieve(query)        ok    42ms   -> 3 chunks
  step 2  build_prompt(chunks)   ok     1ms   -> prompt 1,240 tok
  step 3  model.call(prompt)     ok   980ms   -> answer "..."
  step 4  parse(answer)          FAIL   2ms   -> KeyError: amount
          final score: 0   (failure localized to step 4, the parser)
```

Cái trace làm được:
- Biến "ca này rớt" thành "bước 4: parser ném `KeyError` vì model không trả trường `amount`". Bài so sánh: **sửa trong năm phút** so với **một ngày dò tay** qua workflow.
- Làm thay đổi **review được**: cho thấy **bước nào dịch chuyển**, không chỉ điểm giảm bao nhiêu.

Chi tiết nhỏ rút từ trace mẫu **[ngoài tài liệu]**: tổng thời gian 42 + 1 + 980 + 2 = 1025 ms, trong đó lần gọi model chiếm khoảng 96%. Trace có thời gian từng bước còn trả lời được câu "chậm ở đâu" (dùng ở phần Cost & Orchestration), không chỉ câu "hỏng ở đâu".

### 5.1 So với trace trong Lab 2 **[ngoài tài liệu]**

Lab 2 đã có trace (yêu cầu 7 của đề): `[round N] stop=... tokens=...` mỗi vòng, `tool=... input=... -> ok/ERR` mỗi lần gọi tool.

| | Trace Lab 2 | Trace trong bài |
|---|---|---|
| Bước và kết quả ok/lỗi | Có | Có |
| Tham số của tool call | Có | Có |
| Token | Có (tích lũy theo vòng: 894 → 2049 → 3282) | Có (kích thước prompt) |
| **Thời gian từng bước** | **Không** | Có (ms) |
| **Nội dung prompt và output trung gian** | **Không** (chỉ in `ok`/`ERR`, không in nội dung tool result) | Có |
| Mã chạy (`run_id`) gắn với ca eval | Không | Có |

Trace Lab 2 đủ để thấy kịch bản C thử lại thừa (`'zed'` sau `'Zed'`, tốn thêm khoảng 1100 token), nhưng chưa đủ để thấy **vì sao** model thử lại (nội dung thông báo lỗi tool) hay **chậm ở đâu**.

### 5.2 Hai lưu ý khi dựng trace **[ngoài tài liệu]**

1. **Trace chứa dữ liệu nhạy cảm.** Prompt và output trung gian có thể chứa dữ liệu người dùng, token, secret. Che hoặc cắt trước khi lưu, và coi kho trace như kho log có kiểm soát truy cập (nối W3D3, quản lý secret).
2. **Gắn trace vào bản ghi eval.** W4D2 mục 12 còn treo "lưu kết quả để so giữa các phiên bản". Nếu mỗi bản ghi của `run_eval` mang thêm `run_id`, phiên bản prompt, model và trace các bước, thì ta vừa có chỗ lưu để so, vừa biết ca nào rớt ở bước nào. Đó là hai lỗ hổng được lấp bằng một thay đổi.

## 6. Trace phân biệt "lỗi do model" với "lỗi do integration" thế nào

**Đủ một nửa.** Bài nói trace giúp **khoanh vùng bước**, nhưng **không nêu quy tắc** phân biệt nguyên nhân, và ví dụ của bài còn trộn hai khả năng: triệu chứng nằm ở parser (bước 4), nguyên nhân có thể là model không trả `amount` hoặc parser giả định trường nào cũng có. Trace cho biết **bước nơi lỗi hiện ra**; còn kết luận nguyên nhân là việc của người đọc.

Quy tắc mình rút ra **[ngoài tài liệu]**: với bước bị nghi, đặt **input của nó cạnh output của nó**.

| Quan sát trên trace | Kết luận | Ví dụ trong lab |
|---|---|---|
| **Input của bước đã sai hoặc thiếu**, output sai theo | Lỗi ở **bước trước hoặc mối nối** (integration) | Retrieval trả 0 chunk nên prompt rỗng; `Bearer undefined` ở Lab 3 mục 5.2; `HÃ¹ng` ở Lab 2 |
| **Input đúng và đầy đủ**, model vẫn trả sai | Lỗi ở **model hoặc prompt** | Model xoá khi người dùng chỉ hỏi xem tin (Lab 2 mục 5: `description` của tool bị copy nhầm, sửa ở mô tả tool, tức phía prompt) |
| Output của bước đúng, nhưng **bước sau không đọc được** | Lỗi ở **hợp đồng giữa hai bước** (integration) | Model trả `amount_usd`, parser đòi `amount`: hai bên mỗi bên "đúng" theo cách của mình |
| **Cùng input chạy lại** ra kết quả khác nhau | Phần dao động của **model** (cần chạy nhiều lần, báo tỉ lệ) | Kịch bản A, hai lần ra hai đường đi |

Kiểm chứng nhanh: **chạy lại riêng bước đó với input đã ghi trong trace** (một functional hoặc unit test tạm). Tái hiện được thì lỗi nằm trong bước; không tái hiện thì lỗi nằm ở cách input được tạo ra (mối nối). Lab 3 mục 5.2 làm đúng thế: `curl` thẳng vào fake-api với cùng token để tách "API đúng" khỏi "token không tới nơi".

Một chỗ phân biệt không sạch: **kịch bản C của Lab 2** (thử lại `'zed'`). Quyết định thử lại là của model, nhưng nó bị gợi ý bởi thông báo lỗi do tool trả ("Check the spelling or ask the user"). Nên là **lỗi thiết kế ở mối nối giữa tool và model**, không thuần túy "model dở". Chữa ở tool (so khớp `casefold()`), không phải ở model.

## 7. Hồi quy trong hệ thống có model, và mức test bắt nó đầu tiên

**Tài liệu thiếu**: bài không định nghĩa hồi quy, không nói mức nào bắt đầu tiên. Phần này là suy luận từ notes cũ.

**Định nghĩa.** Hồi quy là đổi một thứ làm **hỏng thứ đang chạy tốt** (W4D1 mục 7 câu 2). Với hệ thống có model có hai điểm khác:
- **Thứ bị đổi không chỉ là code của mình.** Đổi prompt, đổi model, đổi tool description, đổi chunking của retrieval đều là "đổi code". Model nâng phiên bản có thể làm hành vi đổi mà không ai sửa dòng nào (W4D3 mục 12.1b điểm 3).
- **Hỏng thường là hỏng xác suất**: tỉ lệ đạt giảm từ 95% xuống 80%, không phải mọi ca fail.

**Mức nào bắt trước.** Nguyên tắc: chạy từ rẻ đến đắt (cùng tinh thần W4D3 mục 5, "code check mỗi commit, judge theo lịch"). Nhưng **mức nào có thể thấy** phụ thuộc vào cái bị đổi:

| Thay đổi | Lỗi điển hình | Mức bắt **đầu tiên** | Vì sao |
|---|---|---|---|
| **Đổi prompt** | Model thêm lời dẫn, đổi tên trường, bỏ trường | **Functional** (hình dạng output, parse được) | Chạy một lần gọi, rẻ, nói ngay "hình dạng còn đúng không" |
| Đổi prompt | Hình dạng đúng nhưng chất lượng giảm | **Eval** (judge hoặc code grader) | Functional không kiểm nội dung |
| Đổi prompt | Output đổi khuôn, bước sau vỡ | **Integration** | Bước sau đọc output của model |
| **Đổi model** | API từ chối tham số (`temperature`, prefill bị 400 trên `claude-haiku-5-5`) | **Functional** | Lỗi hiện ngay ở **lần gọi thật đầu tiên**; bất kỳ test nào có gọi API đều thấy |
| Đổi model | Giọng, độ dài, mức tuân chỉ dẫn đổi | **Eval** | Cần chấm trên cả tập; độ dài đổi còn ảnh hưởng chi phí |
| Đổi tool, retrieval, chunking | Handoff đổi | **Integration** | Đây là mối nối |

**Hệ quả quan trọng:** **unit test không bao giờ bắt được hồi quy do đổi prompt hoặc model**, vì unit test không gọi model (và nếu mock model thì mock vẫn trả như cũ). Một suite toàn unit test xanh rờ rờ trong khi hệ thống đã hỏng. Bài nói "unit test cho biết một mảnh ổn" nhưng không nói điều này; mình rút ra từ định nghĩa.

**Cách bắt hồi quy có hệ thống:** eval giữ cố định (cùng dataset, cùng grader, W4D1 mục 8.4), chạy lại mỗi lần đổi bất cứ thứ gì kể cả model, so **điểm từng ca** (không chỉ trung bình, W4D3 mục 9.2), và dùng **trace của ca rớt** để biết bước nào dịch chuyển. Đó chính là lời của bài: "show the step that moved rather than just the score that dropped".

## 8. "Watch Out" của từng bài

**Mục Watch Out chính thức của bài này là case ở mục 8.1** (case "Why this broke", gửi bù sau). Bản dán đầu của bài chỉ có ba khung thay thế, và các bảng "bẫy ngầm" dưới đây là phần mình suy ra từ ba khung đó, đứng **cạnh** case chứ không thay case. Ba khung: *Handles well* (khoanh vùng lỗi, ghép mỗi test với lỗi nó thấy), *Adds cost or complexity* (tracing và bốn mức test là hạ tầng phải dựng và bảo trì), *Use a different approach* (tra cứu một sự kiện trong kho ổn định thì fetch-once thắng tìm lặp). Câu hỏi 4 nói "các bài Watch Out" (số nhiều), nhiều khả năng là mục của các bài sau; chỗ này chưa đủ để trả lời, nên ghi những gì **bài này ngầm cảnh báo** và để chỗ trống cho các bài còn lại.

| Bài | Bẫy | Cách tránh |
|---|---|---|
| Testing and tracing | **Chỉ có eval hoặc chỉ có test từng mảnh**: mỗi bên pass riêng, mối nối hỏng âm thầm; điểm eval thấp mà không biết ở bước nào | Test ở **mối nối** (integration) và có **trace** từng bước; mỗi mức test khớp với loại lỗi nó thấy |
| Testing and tracing (routing) | **Mặc định mọi thứ về một kiểu retrieval**: tìm lặp cho mọi câu thì đội chi phí và độ trễ; chỉ dùng chỉ mục tĩnh thì câu trả lời nông ở câu cần nhiều lượt | Router nhỏ phân loại trước; hoặc bỏ router nếu mọi truy vấn cùng một dạng (mục 10) |
| Testing and tracing (chi phí) | **Dựng quá mức**: đủ bốn mức và trace cho mọi thứ là hạ tầng phải nuôi | Chỉ dựng mức nào bắt được lỗi bạn đang thấy; bắt đầu từ trace và integration ở chỗ nối đắt giá |
| Failure Handling | **Retry lỗi terminal** (400, 401...) tốn ngân sách retry và che lỗi thật; **hai tầng retry** (SDK cộng vòng tự viết) nhân số lần thử; **nuốt lỗi tool** nên model coi kết quả rỗng là dữ liệu đúng; **refusal là 200** nên bộ phân loại theo status code không thấy | Phân loại theo status, chưa chắc thì coi là terminal; chọn một nơi đặt retry; trả `is_error: true`; kiểm `stop_reason` (Phần B, mục 21) |
| Model Selection | **Chọn model mạnh nhất làm mặc định** ("lỗi phổ biến và đắt nhất"); **tiết kiệm vài đô bằng model thấp** trong khi lỗi gây thiệt hại lớn phía sau; **đổi model không có điểm đo**; **dựng router cho lưu lượng đồng đều** | Bắt đầu từ Sonnet, nâng hoặc hạ bậc chỉ khi eval cho thấy; tính cả chi phí của lỗi; thăng cấp theo điểm đo trên ca của mình; lưu lượng đồng đều thì ghim một model (Phần C, mục 31) |
| Cost & Orchestration | **Quan sát đến sau** (hóa đơn đến trước lời giải thích); **hành động trên `tool_use` chưa đủ** khi stream chưa đóng; **cache vô hiệu** do đổi tiền tố, hết TTL hoặc quá ngắn; **dùng batch cho yêu cầu người dùng đang chờ**; **multi-agent cho việc gắn chặt hoặc tra cứu đơn** (nhân khoảng 15 lần token); **subagent chạy trốn**; **không xử lý lỗi từng subagent**; **cắt chi phí xuống dưới sàn độ tin cậy** | Instrument từ đầu; chờ stream đóng; giữ tiền tố ổn định và đo `cache_read_input_tokens`; batch chỉ cho việc theo lịch; mặc định một agent; trần token và vòng cho từng subagent; retriable hay terminal cho từng subagent; đặt sàn trước, cổng eval (Phần D, mục 44) |

**[ngoài tài liệu]** Hai bẫy mình tự thêm cho bài này: (1) test functional/E2E khẳng định **đường đi chính xác** của agent sẽ gãy oan vì model không tất định (mục 4.5); (2) trace lưu nguyên prompt và output là rò dữ liệu nhạy cảm (mục 5.2).

### 8.1 Case của bài: các mảnh qua, mối nối vỡ **[docs]**

**Đây là mục Watch Out của bài Testing and tracing** (case "Why this broke", gửi bù sau khi học; bạn xác nhận là mục Watch Out của khóa).

**Chuyện gì xảy ra.** Trace của một lần chạy eval: `test_parser_unit` PASS, `test_extract_shape_functional` PASS, `test_full_flow_e2e` FAIL.

```
step 1 retrieve(q)        ok   -> 3 chunks (list of dicts)
step 2 build_prompt(ctx)  ok   -> ctx inserted as raw list
step 3 model.call(prompt) ok   -> answer ignores the context
step 4 assert answer...   FAIL -> model answered from memory
cause: retrieve() returns [{"content": ...}], build_prompt() expected a plain string
```

Mỗi bên đúng khi đứng riêng. Retrieval trả list các dict, bộ dựng prompt viết để nhận chuỗi thường, nên context đến model sai dạng và model trả lời từ trí nhớ thay vì chính sách đã truy xuất. **Unit không bắt được** vì mỗi đơn vị chạy tốt; **functional không bắt được** vì lần gọi chạy tốt với input đúng dạng. Chỉ test chạy **mối nối retrieval đến model bằng dữ liệu retrieval thật** mới bắt trước người dùng.

**Vì sao vỡ:** hợp đồng định dạng giữa hai bước chưa được định nghĩa và không gì cưỡng chế ranh giới. **Cách tránh của bài:** test integration chạy hai thành phần cùng nhau với dữ liệu thật.

**Đối chiếu [ngoài tài liệu]:**
1. **Đúng kịch bản mình đã dự đoán ở mục 2:** retrieval hỏng, model trả lời từ kiến thức sẵn có, và chỉ lộ ra khi có assertion về nội dung. Ở case, E2E bắt được vì có `assert` kiểm câu trả lời có dùng chính sách. Một eval chỉ chấm "chất lượng chung" có thể vẫn cho điểm khá.
2. **Đọc trace bằng quy tắc mục 6.** Cả bốn bước đều "ok" (span xanh không nói nội dung đúng, mục 11.2 điểm 1). Manh mối nằm ở **output của bước 2** ("ctx inserted as raw list") và **output của bước 3** ("ignores the context"). Input của bước 3 đã sai, nên lỗi ở **mối nối**, đúng hàng 1 của bảng mục 6. Cần trace ghi **nội dung** prompt, không chỉ `ok` và ms (mục 5.1).
3. **E2E cho biết "hỏng", trace cho biết "ở đâu", integration test là thứ viết sau để lỗi không quay lại.** Ba thứ làm ba việc khác nhau (mục 11.4).
4. **Vì sao lỗi im lặng trong Python:** ghép list vào chuỗi không ném lỗi, nó thành `repr` của list, nên prompt vẫn "hợp lệ". Ở .NET, `List<Chunk>` truyền vào tham số `string` là lỗi biên dịch. Với Python cần tự dựng hợp đồng: `Chunk` là dataclass hoặc pydantic, `build_prompt(chunks: list[Chunk]) -> str`, kiểm kiểu bằng mypy, và assertion tại biên (fail fast thay vì nuốt). Bài chỉ nêu integration test; **định nghĩa hợp đồng cộng kiểm tại biên** là phần mình thêm.
5. **Integration này không cần model thật.** Gắn model giả (mục 4.5 điểm 4) rồi khẳng định prompt cuối **chứa văn bản của chunk** và **không chứa** chuỗi kiểu `[{'content'`. Bắt đúng lỗi, chạy mỗi commit. Giữ một bộ nhỏ chạy model thật cho câu "model có dùng context không".
6. **Cách viết assert "không trả lời từ trí nhớ":** dùng tài liệu mà model không thể biết (chính sách tưởng tượng, mã số riêng). Câu trả lời đúng chỉ có thể đến từ chunk. Nếu dùng tài liệu có trong kiến thức chung thì model trả lời đúng dù context hỏng, và case sẽ không bị bắt.
7. Đây là bẫy 1 của bảng mục 8 ("chỉ có eval hoặc chỉ có test từng mảnh") thành ví dụ cụ thể.

### 8.2 Checkpoint của bài Testing and tracing **[docs]** và đối chiếu **[ngoài tài liệu]**

**Đề.** Đọc trace nơi E2E fail còn mọi unit test pass; chỉ ra **chỗ vỡ**, nêu **cơ chế**, chọn **cách sửa trúng đích** và **mức test** sẽ bắt được, trong ba phương án.

```
PASS test_retrieve_unit        returns 3 chunks for a known query
PASS test_model_call_functional returns a well-formed answer string
FAIL test_full_flow_e2e
  step 1 retrieve(q)        ok   -> [{"content": "..."}, ...]
  step 2 build_prompt(chunks) ok -> chunks placed without .content
  step 3 model.call(prompt) ok   -> answer unrelated to the documents
  step 4 assert "30 days"   FAIL -> phrase not in answer
```

| Phương án | Nội dung | Kết quả |
|---|---|---|
| A | Sửa parser (`dateutil.parse`, đã qua unit test của nó) | Sai |
| B | Sửa câu chữ prompt ("Answer carefully and cite the policy") | Sai: "rewords, ignores the seam" |
| **C** | **Căn lại mối nối cộng thêm integration test** trên `retrieve()` đến `build_prompt()`: `context = "\n".join(c["content"] for c in chunks)`, rồi `build_prompt(question, context)`, test mới chạy hai hàm cùng nhau trên chunk thật | **Đúng** |

**Câu trả lời đầy đủ (mình chọn C):**
- **Chỗ vỡ:** mối nối giữa bước 1 và bước 2, tức `retrieve()` đến `build_prompt()`.
- **Cơ chế:** **lệch hợp đồng định dạng ở chỗ giao**. `retrieve()` trả list các dict chunk; `build_prompt()` không bao giờ đọc trường `content`, nên model nhận context sai dạng và trả lời không dựa vào tài liệu.
- **Cách sửa:** trích `content` thành chuỗi, cộng test trên đúng mối nối đó.
- **Mức test:** **integration**.

**Đối chiếu [ngoài tài liệu]:**
1. **Cùng kiểu với case Watch Out ở mục 8.1**, khác ở chỗ checkpoint hỏi cả chuỗi: tìm chỗ vỡ, gọi tên cơ chế, chọn sửa, chọn mức test. Thứ tự đọc trace: tìm **bước đầu tiên có output sai**; ở đây là output của bước 2 ("chunks placed without .content"), không phải bước 4 là nơi assert rơi.
2. **Vì sao A sai:** trace **không có parser nào**, và dòng "đã qua unit test" là manh mối ngược: unit test xanh nghĩa là lỗi **không nằm trong đơn vị đó** (mục 3: unit "không bắt được cách các thành phần khớp nhau"). **Vì sao B sai:** nếu context không tới được model thì không câu chữ nào làm nó "cite the policy", vì nó chưa từng nhận chính sách. Đổi prompt khi chưa đọc trace là cách sửa sai tầng (quy tắc mục 6, hàng 1).
3. **`assert "30 days"` là một assertion tốt**: cụm đó chỉ có trong tài liệu đã truy xuất, nên đúng thì chứng tỏ context đã tới model (mục 8.1 điểm 6: dùng tài liệu model không thể biết). Nó là thứ phân biệt "trả lời từ context" với "trả lời từ trí nhớ".
4. **Chỗ cách sửa C còn có thể làm tốt hơn:** C đặt việc trích `content` ở **bên gọi**, rồi `build_prompt(question, context)` nhận chuỗi. Mọi nơi khác gọi `build_prompt` phải lặp lại bước trích. Giữ **hợp đồng ở một nơi**: hoặc `build_prompt` nhận `list[Chunk]` rồi tự ghép, hoặc kiểm kiểu tại biên (mục 8.1 điểm 4). Bài không nói; đây là gợi ý của mình.
5. **Integration test mới không cần model thật** (mục 4.5 điểm 4): chạy `retrieve` trên chunk thật rồi `build_prompt`, khẳng định prompt cuối **chứa văn bản chunk** và **không chứa** dạng `{'content'`. Bắt đúng lỗi, rẻ, chạy mỗi commit; model thật chỉ cần cho câu "model có dùng context không".

## 9. Ghi trước phần đã biết cho hai chủ đề sau **[ngoài tài liệu]**

Chưa có tài liệu, nên chỉ ghi dữ kiện đã có trong notes cũ, để khi bài tới thì đối chiếu:

- **Câu 6 (đổi model làm vỡ gì ngoài chất lượng; đã có tài liệu, xem Phần C):** đã có một bằng chứng thật: trên `claude-haiku-5-5`, `temperature` bị 400 ở mọi giá trị và prefill bị 400 (W4D2 mục 7, `probe_model_params.py`). Hai thứ đó là **tham số API**, không phải chất lượng. Danh sách ứng viên cần kiểm khi đổi model: tham số được chấp nhận, hỗ trợ prefill, định dạng output (structured outputs), giới hạn context, giá, độ dài output (đổi chi phí), độ trễ. Mức test bắt đầu tiên: functional (mục 7).
- **Câu 5 (retriable và terminal; đã có tài liệu, xem Phần B):** mục 2.4 của W4D3 đã có khung bảng. Lab 2 đã có ba loại lỗi đáng đối chiếu: `is_error` do input sai schema hoặc member không tồn tại (tool trả lỗi, model đọc được), `User declined` (terminal: model không thử lại, B), và giới hạn vòng/ngân sách (D). SDK tự retry 429/529 (NOTES.md mục 1; **chưa tái hiện được lỗi thật**).
- **Câu 7 (nhiều agent; đã có tài liệu, xem Phần D):** LAB2 mục 7 có sẵn tiêu chí "workflow, agent, subagent"; mục 6 có chi phí cộng dồn theo vòng (894 → 2049 → 3282) và ngân sách token mềm. Con số 96% thời gian ở lần gọi model (mục 5) là dữ kiện đầu tiên cho câu "chậm ở đâu".

## 10. Routing giữa hai cách retrieval **[docs]**

Phần này nằm trong bài nhưng **lệch chủ đề** với tiêu đề "Testing and tracing". Có vẻ là đoạn kéo từ bài retrieval sang. Vẫn đáng ghi vì nó là mẫu thiết kế liên quan trực tiếp đến cost.

**Ý của bài:** không cần chọn một chiến lược cho mọi thứ. Một bước **phân loại rẻ** (một lần gọi model nhỏ) đưa truy vấn tra cứu một sự kiện sang **fetch-once** (tìm một lượt trong chỉ mục dựng sẵn), và truy vấn nhiều phần sang **agentic search** (tìm qua nhiều vòng). Chỉ trả tiền cho việc lặp khi truy vấn cần.

```python
def route(query):
    kind = classify(query)        # cheap call: "lookup" hoặc "multi_step"
    if kind == "lookup":
        return fetch_once(query)  # tĩnh, một lượt
    return agentic_search(query)  # tìm qua nhiều vòng
```

| Chọn | Hợp khi | Hỏng khi |
|---|---|---|
| Fetch-once | Tra một sự kiện, kho ổn định | Câu hỏi nhiều bước, kho thay đổi |
| Agentic search | Câu cần nhiều lượt | Tra sự kiện đơn giản: đội chi phí và độ trễ |
| **Router** | **Lưu lượng hỗn hợp** (có cả hai dạng) | Mọi truy vấn cùng một dạng: bỏ router, hardcode đường đi hợp |

Nối với notes cũ:
- W3D2 mục 2: classical RAG (khớp chỉ mục dựng sẵn) và agentic search (tìm lúc cần). Router chọn giữa hai thứ đó.
- LAB2 mục 7: cùng nguyên tắc "đường đi biết trước hay không" (workflow so với agent), và "bắt đầu từ cách đơn giản nhất".
- NOTES.md mục 2: "bắt đầu từ model rẻ nhất, chỉ nâng khi cần". Router là bản của nó ở tầng đường đi.

**Đọc phê phán [ngoài tài liệu]:**
1. **Bước `classify` là một prompt, nên cũng cần eval** (W4D1 mục 6.3a: bước viết lại câu hỏi cũng phải đo). Bài không nói đo thế nào.
2. **Hai kiểu phân loại sai có giá khác nhau.** Câu nhiều bước bị đưa vào fetch-once cho ra **câu trả lời nông, âm thầm** (không lỗi, không exception); câu tra cứu bị đưa vào agentic chỉ **tốn tiền**. Lỗi thứ nhất khó thấy hơn nên nên thiên về an toàn ở chỗ này, và nên đo riêng tỉ lệ từng loại nhầm.
3. **Trace phải có bước `route`** ghi `kind` được chọn, nếu không một câu trả lời nông không khoanh được về router.
4. **"Chi phí phân loại thấp hơn nhiều" cần số.** Bài chưa đưa; cần đo chi phí của `classify` so với chi phí trung bình của hai nhánh, và tỉ lệ lưu lượng mỗi loại, thì mới biết router có lời.
5. **Chưa nói `classify` làm bằng gì.** Có thể là model nhỏ (Haiku theo quy tắc "bắt đầu từ rẻ nhất"), hoặc luật đơn giản (độ dài câu, có "và", có từ so sánh) nếu đủ.

## 11. Đối chiếu cách hiểu của mình, và test, trace chạy khi nào **[ngoài tài liệu]**

Bài không nói test và trace chạy **khi nào**; phần này là suy luận của mình khi trao đổi.

### 11.1 Cách hiểu về bốn mức test

Cách nhìn của mình: bốn mức chia theo **scope** của test case. Đúng ý bài. Thang scope: một hàm, một lần gọi Claude, một mối nối, cả luồng. Scope càng lớn thì càng chậm, đắt và khó khoanh vùng.

| Mức | Cách hiểu của mình | Chỉnh |
|---|---|---|
| Unit | Test một hàm, outcome xác định | Đúng. Thêm: không gọi model |
| Functional | Test cấu trúc, format output, giống code-graded check | **Cùng kỹ thuật, khác vai trò.** Code-graded check là một *grader* trong eval: chấm điểm từng ca trên cả dataset rồi lấy tỉ lệ. Functional là *test*: assert pass hoặc fail trên vài input đại diện, chặn thay đổi hỏng. Cùng một hàm `validate_json` dùng được cho cả hai. Functional còn gồm "API có chấp nhận request không" (400 của `temperature`) |
| Integration | Hai mức trên là mono-service; integration bắt đầu là nhiều service giao tiếp | **Tiêu chí là số thành phần tham gia**, không nhất thiết nhiều service. Lab 3 đúng như bạn nói (client ↔ MCP server ↔ API, ba process). Nhưng integration của Lab 2 (file → code tool → model) nằm gọn trong một process. Nối với model cũng là một mối nối |
| E2E | Một test thực sự do người hoặc bên thứ ba làm như QC | **E2E là chạy cả luồng như người dùng, không quy định ai chạy.** Bốn kịch bản A–D của Lab 2 là E2E tự động. Người chạy tay (QC) là một cách chạy E2E, và gần UAT hoặc grader loại Human hơn (W4D3 mục 12.1c) |

Điểm khác test truyền thống: ba trong bốn mức có model nên không tất định (mục 4.5).

### 11.2 Trace và APM

Trace gần như APM (OpenTelemetry): một lần chạy là một trace, mỗi bước (`retrieve`, `build_prompt`, `model.call`, `parse`) là một span, `run_id` ≈ trace id, thời gian từng bước ≈ duration. Khác ở ba chỗ:

1. **Phải ghi nội dung, không chỉ trạng thái.** `model.call ... ok 980ms` vẫn có thể trả nội dung sai; span xanh không nói câu trả lời đúng hay không. Nên cần prompt và output trung gian (APM thường chỉ ghi tên span, duration, status, vài attribute). Hệ quả: dữ liệu nhạy cảm hơn (mục 5.2).
2. **Token và chi phí** là attribute chính (APM truyền thống không có khái niệm này).
3. **Gắn với ca eval và điểm**: bản ghi eval trỏ tới trace của ca đó.

Mình nhớ OpenTelemetry có quy ước đặt tên thuộc tính cho tác vụ GenAI; **cần đối chiếu docs** trước khi dựa vào.

### 11.3 Test và trace chạy khi nào

**Không phải chỉ khi eval cho kết quả xấu.** Hai thứ có nhịp khác nhau:

| | Khi nào | Lý do |
|---|---|---|
| **Test** | **Chạy trước và song song với eval**, mỗi lần đổi prompt, model, tool, retrieval. Mức rẻ (unit, functional) chạy mỗi lần đổi; integration ở mỗi PR hoặc theo đêm; E2E trước khi ship | Không chờ điểm xấu mới chạy, vì **điểm đạt vẫn có thể che chỗ gãy** (mục 2). Cùng tinh thần "code check mỗi commit, judge theo lịch" (W4D3 mục 5) |
| **Trace** | **Ghi mọi lần chạy** (mọi ca eval, và production có thể lấy mẫu); **đọc khi có ca rớt hoặc nghi ngờ** | Model không tất định nên **chạy lại có thể không tái hiện được lỗi**. Nếu chỉ bật trace sau khi thấy điểm xấu thì lần chạy lỗi đã qua rồi. Giống APM: bật sẵn, mở ra đọc khi sự cố |

Vòng lặp:

```
đổi prompt / model / tool
   -> unit + functional (nhanh, mỗi lần đổi)  -> integration
   -> eval trên cả dataset (ghi trace mọi ca)
        điểm đạt  -> E2E trước khi ship
        điểm xấu  -> đọc trace các ca rớt -> bước nào dịch chuyển?
                  -> sửa đúng chỗ -> thêm test ở mức bắt được lỗi đó -> chạy lại
production: trace lấy mẫu -> lỗi thật -> thêm thành ca eval và test (vòng khép kín, W4D1 mục 6.4)
```

Vậy điểm xấu là **một trong các lý do để đọc trace**, và là lý do để **thêm test** ở mức phù hợp sau khi tìm ra lỗi; không phải lúc duy nhất để chạy test.

### 11.4 Bức tranh tổng: eval, test, trace trong vòng đời một ứng dụng dùng Claude

**Gốc của vấn đề:** ta không sở hữu model. Ta chỉ điều khiển được **prompt, tool, retrieval, chọn model, tham số và code bao quanh**; Anthropic có thể ra model mới hoặc gỡ tham số (như `temperature`, prefill bị 400 trên `claude-haiku-5-5`). Ta không đọc được "code" của model để biết nó làm gì, nên phải **đo hành vi từ bên ngoài**, mỗi lần đổi một trong các thứ trên.

| Câu hỏi | Công cụ | Kết quả | Chạy khi |
|---|---|---|---|
| Code của mình có bug không? | Unit | pass hoặc fail | Mỗi lần đổi code |
| Một lần gọi Claude có được chấp nhận và trả đúng khuôn không? | Functional | pass hoặc fail | Mỗi lần đổi prompt hoặc model |
| Các mảnh nối đúng chưa? | Integration | pass hoặc fail | Mỗi PR hoặc theo đêm |
| Cả luồng có làm đúng việc người dùng cần không? | E2E | pass hoặc fail | Trước khi ship |
| Prompt và model **tốt đến đâu trên cả loại input**, bản nào tốt hơn? | **Eval** | **điểm trên cả tập** (tỉ lệ đạt) | Mỗi lần đổi prompt, model, tool; hoặc theo lịch |
| Bước nào hỏng, vì sao? | Trace | dòng thời gian từng bước | Ghi mọi lần chạy, đọc khi có ca rớt |

**Khác nhau cốt lõi giữa test và eval:** test kiểm **bộ máy** (code, hình dạng, mối nối), kết quả nhị phân, lặp lại được. Eval đo **hành vi của phần không tất định** (prompt cộng model), kết quả là điểm thống kê trên nhiều input. Eval không phải mức thứ năm của kim tự tháp test; nó là một phép đo khác, đặt cạnh chúng.

Ví dụ với bài AWS-code của W4D2 (số liệu minh hoạ, không phải kết quả đo thật):

```
viết design doc: thành công = chỉ trả code, cú pháp hợp lệ, đúng việc
v1 prompt  -> unit test validate_*  -> functional: 1 lần gọi haiku, parse được, stop_reason != max_tokens
           -> eval 30 ca: 6.8/10 (baseline, chưa tốt hay xấu)
đổi MỘT thứ (thêm "chỉ trả code") -> chạy lại eval -> 7.5; xem từng ca, có ca nào tụt không
ca 12 rớt 0 -> đọc trace: bước sinh trả "Here is the regex: ..." -> sửa prompt, thêm ca đó vào dataset
trước khi ship: E2E vài kịch bản; production: trace lấy mẫu, lỗi thật quay lại thành ca eval
Anthropic ra model mới -> chạy lại functional (API còn nhận tham số?) rồi eval (điểm có tụt?)
```

### 11.5 Vòng v1 đến v2: test là cổng chặn, eval để so

Cách hiểu của mình (đã chỉnh): ở v1 chạy test rồi eval để có điểm xuất phát; cải tiến thành v2; chạy lại test và eval để so với v1.

```
v1: test  -> eval  -> baseline (điểm, từng ca, trace các ca rớt)
        |
        v  đọc ca rớt, sửa MỘT thứ
v2: test  -> eval (cùng dataset, cùng grader) -> so với baseline v1
        |
        v  chưa đạt thì lặp: v3 so với v2 (hoặc v1)
```

Hai chỉnh:

1. **v2 không chỉ khởi từ test fail.** Vấn đề ở v1 có thể đến từ test fail (bộ máy hỏng), eval điểm thấp (chất lượng thấp) hoặc đọc trace các ca rớt (biết sửa ở đâu). Cả ba đều dẫn đến "sửa thành v2".
2. **Test chạy trước như cổng chặn, eval chạy sau.** Test fail thì sửa tiếp và **không chạy eval** (tốn tiền, điểm vô nghĩa nếu output không parse được). Test pass thì chạy eval trên cùng dataset, cùng grader.

| | Trả lời | Không trả lời |
|---|---|---|
| Test v2 pass | Không làm vỡ bộ máy (không hồi quy ở mức hình dạng, mối nối) | v2 có **tốt hơn** không |
| Eval v2 so với v1 | Tốt hơn hay tệ hơn, hơn bao nhiêu | Chỗ gãy cụ thể |

Test pass không có nghĩa v2 tốt hơn; eval cao không có nghĩa bộ máy không có chỗ gãy âm thầm. Cần cả hai.

**Điểm của v1 chỉ là baseline.** Con số như 6.8/10 chưa nói "tốt hay tệ" tuyệt đối; nó chỉ có nghĩa khi đặt cạnh một mốc: ngưỡng ghi trong design doc (ví dụ "cần ≥ 8") hoặc điểm của v2 (W4D2 mục 25: baseline không tốt hay xấu tự thân).

**"Hơn bao nhiêu" chỉ tin được khi:**
- Cùng dataset, cùng grader, cùng model, chỉ đổi một thứ (W4D1 mục 8.4).
- Chạy nhiều lần và xem từng ca, vì chênh lệch nhỏ có thể chỉ là dao động (W4D1 mục 9 câu 2: 7.66 lên 8.7 trên 3 câu chưa kết luận được).
- Xem ca nào tụt: trung bình tăng mà vài ca bị hỏng vẫn là hồi quy (W4D3 mục 9.2).

**Điều kiện để so được:** kết quả của v1 phải **được lưu**, kèm phiên bản prompt, model, dataset và điểm từng ca. Không lưu thì đến v2 không có gì để so. Đây là chỗ còn treo từ W4D2 mục 12; mục 5.2 đề xuất lấp bằng `run_id` cộng trace trong bản ghi của `run_eval`.

**Cuối vòng:** ca từng rớt ở v1 (ví dụ ca 12) nên giữ lại trong dataset; nếu lỗi thuộc bộ máy thì thêm một test ở đúng mức, để v3 không âm thầm làm hỏng lại đúng chỗ đó.

## 12. Câu hỏi ôn tập (Phần A)

1. Bốn mức test kiểm gì, mỗi mức **không** bắt được gì? Vì sao nói phần lớn lỗi âm thầm nằm ở integration?
2. Lab 3 trả `API 401` dù fake-api đúng và `index.js` đúng. Lỗi thuộc mức test nào, và `curl` đã làm gì trong lần dò lỗi đó?
3. Kịch bản D của Lab 2 (xoá thật rồi dừng im lặng) được phát hiện ở mức nào, và vì sao mức đó vẫn chưa đủ để khoanh vùng?
4. Trace ghi bốn thứ nào? Trace của Lab 2 thiếu những thứ nào so với trace trong bài?
5. Trace báo "bước 4 FAIL: KeyError: amount". Cần xem thêm gì để quyết định lỗi ở model hay ở parser?
6. Vì sao unit test không bắt được hồi quy khi đổi model? Mức nào bắt đầu tiên khi `claude-haiku-5-5` từ chối `temperature`?
7. Hệ thống có 100% truy vấn tra cứu một sự kiện trong kho ổn định. Có nên dựng router không? Vì sao?
8. Router phân loại nhầm theo hai hướng; hướng nào nguy hiểm hơn và vì sao?

## 13. Còn lại và việc cần kiểm tra (Phần A)

- **Chưa có thí nghiệm nào chạy thật cho bài này.** Mọi ánh xạ Lab và quy tắc ở mục 4, 6, 7 là suy luận từ tài liệu và notes cũ. Chỉ phép tính 42 + 1 + 980 + 2 = 1025 ms (96%) là tính trực tiếp từ trace mẫu của bài.
- **Tài liệu thiếu:** định nghĩa hồi quy, mức test nào bắt đầu tiên (câu 3); mục Watch Out (câu 4; đã nhận sau, xem mục 8.1); quy tắc phân biệt model với integration (câu 2); cách đo `classify`; chưa có Failure Handling, Model Selection, Cost & Orchestration (câu 5, 6, 7).
- **Việc có thể làm ở Lab 4 (nếu làm):** thêm `run_id`, phiên bản prompt, model và trace từng bước vào bản ghi của `run_eval` (lấp chỗ W4D2 mục 12); thêm thời gian từng bước vào trace của `lab2_agent.py` (hiện chỉ có token); viết một functional test nhỏ gọi `claude-haiku-5-5` để bắt tham số bị từ chối ngay khi đổi model.
- Chưa làm: thêm test khó hơn cho `bench_models.py` (từ W4D1).

---

# Phần B. Failure Handling

Nguồn: bài "Failure Handling" (phần "Surviving production failure: tool errors"): retriable hay terminal, SDK đã retry sẵn, tool error phải trả về Claude, bảng quyết định. Chỗ ghi **[SDK]** là mình đã đọc mã nguồn SDK `anthropic` 2.6.0 đang cài trong máy (không phải thử chạy); **[ngoài tài liệu]** là suy luận.

## 14. Bài này đứng ở đâu

Phần A: test cho biết **có** lỗi, trace cho biết **ở đâu**. Bài này hỏi tiếp: **ngay lúc lỗi xảy ra trong lưu lượng thật, hệ thống làm gì**. Prototype ít gặp 429, timeout, kết quả tool hỏng, lỗi mạng chập chờn. Hệ thống chịu được hay giòn tùy vào việc ta **quyết định từ trước** mỗi loại lỗi được xử lý thế nào.

Đây chính là quyết định số 2 của design doc ("failure handling", W4D3 mục 2.1) được cụ thể hoá.

## 15. Câu hỏi đầu tiên: retriable hay terminal **[docs]**

Phép thử: **chờ rồi gửi lại đúng y request thì có khả năng thành công không?** Có thì retriable, không thì terminal. Rate limit tự hết theo thời gian; request sai hình thì lần nào cũng lỗi giống nhau cho đến khi sửa chính request.

| Lỗi | Nhóm | Vì sao |
|---|---|---|
| **429** rate limit | Retriable | Vượt giới hạn theo phút, hết theo thời gian |
| **529** quá tải | Retriable | Phía Anthropic đang tải cao; **không phải tín hiệu rate limit** của bạn |
| **500, 502, 503, 504** | Retriable | Lỗi phía Anthropic, thường tự hết khi thử lại |
| **400** request sai | Terminal | Cùng request sẽ lỗi lại |
| **401** xác thực | Terminal | Key sai hoặc hết hạn |
| **403** quyền | Terminal | Thiếu quyền, thử lại không đổi |
| **404** không có | Terminal | Ví dụ tên model không tồn tại |
| **Timeout** | Thường retriable | Việc có thể chỉ chạy lâu hơn mức chờ; **timeout lặp lại trên request đắt** là tín hiệu phải sửa request, không phải thử tiếp |
| **Refusal** (HTTP 200, `stop_reason: "refusal"`) | Terminal | Model đưa ra quyết định về nội dung, không phải lỗi tạm thời; **bộ phân loại theo status code không thấy** vì là 200 |
| **Lỗi kết quả tool** | Tuỳ tool | Chỉ retry khi nguyên nhân tạm thời |

Mã mẫu của bài:

```python
RETRIABLE = {429, 529, 500, 502, 503, 504}   # rate limit, quá tải, tạm thời
TERMINAL  = {400, 401, 403, 404}             # request sai, xác thực, thiếu

def is_retriable(status):
    return status in RETRIABLE   # mọi thứ khác: thất bại ngay
```

**Vì sao phân biệt này quan trọng:** nó quyết định việc chờ có ích không. Retry lỗi terminal vừa **phí ngân sách retry**, vừa **che lỗi thật sau một bức tường lỗi giống nhau**, vừa tăng độ trễ mà lỗi retriable ở chỗ khác trong luồng có thể cần. Phân loại đúng là giữ ngân sách retry cho lỗi cần nó.

**Mặc định khi chưa chắc: coi là terminal và ném lỗi.** Phân loại nhầm thành terminal thì lỗi lộ ra rõ và được sửa; nhầm thành retriable thì dội liên tục vào dịch vụ và che mất vấn đề thật.

## 16. SDK đã retry sẵn: đặt retry ở đâu **[docs]**

Bài nói: thư viện client của Anthropic tự retry các lỗi tạm thời với độ trễ tăng dần, tối đa một số lần cấu hình được. Cần biết điều này để **không thêm vòng retry của mình chồng lên**: hai vòng bọc quanh cùng một lần gọi **nhân** số lần thử lên thay vì chặn trần. Chọn một trong hai: để SDK lo lỗi tạm thời và chỉ viết code riêng cho fallback của ứng dụng, hoặc **hạ retry của SDK xuống** rồi tự sở hữu cả đường đi. Điều cần tránh: hai tầng cùng retry một lỗi mà tầng nào cũng không biết tầng kia.

Header `retry-after` (có trong phản hồi 429 hoặc 529 theo bài) là **thời gian chờ có thẩm quyền**: chính xác hơn đoán bằng backoff. Quy tắc của bài: **đọc `retry-after` trước, chỉ dùng backoff luỹ thừa khi header vắng**. Tên header và giá trị giới hạn là loại gắn với phiên bản, cần đối chiếu tài liệu tham chiếu lúc build.

**Đối chiếu mã SDK 2.6.0 [SDK]** (đọc `_constants.py` và `_base_client.py`, chưa thử chạy với lỗi thật):

| Hạng mục | Mã SDK |
|---|---|
| Số lần retry mặc định | `DEFAULT_MAX_RETRIES = 2`. Lab 2 đặt `Anthropic(max_retries=3)` |
| Retry khi nào | Header không chuẩn `x-should-retry` nếu có thì **theo header** (`true` hoặc `false`); không có thì retry với **408**, **409**, **429**, và **mọi status ≥ 500** (gồm 529) |
| Không retry | Các mã còn lại, như 400, 401, 403, 404 |
| Chờ bao lâu | Đọc `retry-after-ms`, rồi `retry-after` (giây hoặc ngày); nếu có thì **làm đúng như server nói**. Không có thì backoff: `0.5s × 2^n`, trần 8s, nhân hệ số jitter `1 − 0.25 × random` (tức 75% đến 100%) |
| Trần của `retry-after` | Chỉ bị cắt ở khoảng 4,29 triệu giây (giới hạn nền tảng), **không có trần hợp lý** |

Ba điều rút ra:
1. **Khớp bài:** đúng quy tắc "`retry-after` trước, backoff sau", và 429, 5xx retriable còn 400, 401, 403, 404 thì không.
2. **SDK rộng hơn danh sách tay của bài:** SDK retry cả **408, 409** và mọi 5xx; bộ phân loại `RETRIABLE` của bài không có 408, 409 và chỉ liệt kê 500 đến 504 (hơn nữa nó coi mã nằm ngoài hai tập là "fail fast"). Nếu hạ retry của SDK xuống và tự viết theo danh sách này, bạn thu hẹp hành vi hơn SDK mặc định.
3. **Chưa đọc** hàm `_should_retry_exception` (timeout và lỗi mạng), nên chưa khẳng định SDK xử lý các lỗi đó thế nào.

Ví dụ nhân số lần thử (con số minh hoạ): bọc vòng tự viết 3 lần thử quanh lệnh gọi SDK mặc định (mỗi lần thử gồm 1 request và tối đa 2 retry) thì một thao tác của người dùng có thể thành 3 × 3 = **9 request HTTP**.

**Chỗ còn mở trong ISSUES.md** ("retry 429 và 529 mới là kiến thức từ tài liệu, chưa tái hiện được lỗi thật"): giờ đã có thêm bằng chứng **từ mã SDK** cho hành vi retry; vẫn **chưa quan sát** lỗi thật. Cách tái hiện ở mục 20 điểm 8.

## 17. Lỗi tool phải trả về cho Claude một cách tường minh **[docs]**

Khi tool chạy lỗi, kết quả phải gửi lại cho Claude với **`is_error: true`**, **không** được trả kết quả rỗng một cách im lặng. Có cờ lỗi thì model phản ứng được: thử cách khác, hỏi lại hoặc dừng. Tool nuốt lỗi và trả rỗng sẽ dẫn đến câu trả lời **tự tin nhưng sai**, vì model coi kết quả rỗng là dữ liệu hợp lệ rồi suy luận tiếp trên nền sai. Lỗi nhìn thấy được dễ bắt hơn nhiều so với câu trả lời sai mà tự tin.

```python
def run_tool(tool_use):
    try:
        result = execute(tool_use)
        return {"type": "tool_result", "tool_use_id": tool_use.id, "content": result}
    except Exception as e:
        # đưa lỗi ra để Claude phản ứng, KHÔNG trả rỗng
        return {"type": "tool_result", "tool_use_id": tool_use.id,
                "is_error": True, "content": f"Tool failed: {e}"}
```

Refusal (đoạn thứ hai của bài) kiểm `stop_reason` sau khi gọi, vì HTTP là 200 nên bộ phân loại status không bắt được:

```python
if response.stop_reason == "refusal":
    raise ValueError("Model refused the request. Review input before retrying.")
```

**Nối với Lab 2 [ngoài tài liệu]:**
- Lab 2 đã làm đúng quy tắc: cả bốn nhánh lỗi trong `_run_tool` (tool lạ hoặc sai schema, `User declined`, ngoại lệ của hàm tool) đều trả `tool_result` với `is_error: True`.
- Lab 2 mục 5 đã gặp đúng bẫy "nuốt lỗi": `delete_message` trả `{"deleted": True}` kể cả khi không xoá được gì, và thông báo "không tìm thấy" trả như kết quả thành công. Cách sửa là `raise` để thành `is_error`. Đây là hai ví dụ thật của câu "kết quả sai nhưng tự tin".
- **Chính model cũng là một vòng retry.** Kịch bản C: lỗi "không tìm thấy member" là terminal, nhưng thông báo "Check the spelling or ask the user" mời model thử lại với `'zed'`, tốn khoảng 1100 token vô ích. Kịch bản B thì ngược lại: nhận `"User declined"` model không thử lại. Câu chữ của thông báo lỗi tool **điều khiển hành vi retry của model**. Gợi ý: nói rõ trong thông báo lỗi là nên thử lại hay không (ví dụ "không tìm thấy, đừng thử lại cùng tên").
- Lab 2 mục 6 ghi `except Exception` gom cả bug thật lẫn lỗi nghiệp vụ. Theo bài ("tuỳ tool: retry chỉ khi nguyên nhân tạm thời") nên tách ít nhất ba loại: lỗi nghiệp vụ (terminal, `ValueError`), lỗi tạm thời (timeout, 5xx khi tool gọi dịch vụ ngoài: retriable), và bug (không được giấu).

## 18. Bảng quyết định lỗi **[docs]**

| Loại lỗi | Retriable hay fail fast | Backoff | Fallback |
|---|---|---|---|
| Rate limit (429) | Retriable | Backoff luỹ thừa có jitter, **theo `retry-after`**, **giới hạn số lần** | Hết số lần thì ném lỗi gọn, hoặc chuyển sang kết quả cache hoặc đơn giản hơn |
| Quá tải (529) | Retriable | Backoff; 529 phản ánh tải phía Anthropic, không phải tín hiệu rate limit | Chuyển sang đường dự phòng, hoặc trả lỗi nhẹ nhàng nếu kéo dài |
| Request sai (400) | **Fail fast** | Không retry | Sửa hoặc từ chối input và đưa lỗi cho bên gọi |
| Lỗi kết quả tool | Tuỳ tool | Chỉ retry nếu nguyên nhân tạm thời | Trả cờ lỗi cho Claude, **không bao giờ im lặng** |
| Refusal (200, `refusal`) | **Fail fast** | Không retry | Đưa refusal lên bên gọi, **ghi log**, không retry im lặng và không coi là output hợp lệ |

Ba khung kết bài: *Handles well* (một phản hồi xấu không lan thành sự cố, vì xử lý từng loại lỗi theo tên); *Adds cost or complexity* (mỗi đường lỗi là code phải viết, test và bảo trì thêm); *Use a different approach* (đừng retry lỗi terminal: retry 400 chỉ phí ngân sách).

## 19. Trả lời câu hỏi hướng dẫn 5

**"Lỗi nào thuộc nhóm nào": đủ** (bảng mục 15).

**"Người dùng nhận gì khi không cứu được": đủ một nửa.** Bài chỉ nói **bên gọi** (caller) nhận gì:

| Lỗi | Bài nói gì khi không cứu được |
|---|---|
| 429 | Ném lỗi gọn, hoặc trả kết quả cache hoặc đơn giản hơn |
| 529 | Chuyển đường dự phòng, hoặc trả lỗi nhẹ nhàng |
| 400 | Sửa hoặc từ chối input, đưa lỗi cho bên gọi |
| Refusal | Đưa lên bên gọi và ghi log |
| Tool lỗi | Cờ lỗi trả về cho **Claude** (không phải người dùng) |

"Caller" là code gọi, **không phải người dùng cuối**; bài không nêu nội dung thông báo cho người dùng cuối. Phần dưới là đề xuất của mình.

### 19.1 Đối chiếu LAB2.md

| Lỗi trong Lab 2 | Nhóm | Ai xử lý | Người dùng nhận |
|---|---|---|---|
| Tool lạ, input sai schema | Terminal | `_run_tool` trả `is_error` cho model | Model có thể sửa input; nếu không thì thấy trong `summary` |
| Member không tồn tại (C) | Terminal | Model, sau đó JSON cuối | `summary`: "Không tìm thấy thành viên nào tên 'Zed'... vui lòng kiểm tra lại tên", `deleted: false`, `message_id: null` |
| `User declined` (B) | Terminal (quyết định của người) | Model, không thử lại | `summary`: "bị từ chối nên tin nhắn chưa được xoá" |
| Hết vòng hoặc ngân sách token (D) | Giới hạn cứng | `stopped()` | Chuỗi "(dừng: hết 2 vòng; đã thực thi: delete_message(...))": **nêu cả hành động có tác dụng phụ đã chạy** |
| Output cuối sai schema | Sửa được có giới hạn | `run_with_validation`, sửa tối đa 1 lần | Phần xử lý khi vẫn sai sau lần sửa: LAB2.md mục 2 không nói rõ nên chưa khẳng định |
| **429, 529, 5xx, lỗi mạng** | Retriable | SDK (`max_retries=3`) | **Lab 2 chưa xử lý.** Hết lượt retry, ngoại lệ thoát từ `client.messages.create` (`lab2_agent.py` dòng 92, không có `try` quanh) và chương trình dừng bằng traceback |
| **400, 401** (tên model sai, key sai) | Terminal | Không ai | Traceback |

Nhận xét: Lab 2 xử lý rất kỹ **lỗi ở tầng tool và nghiệp vụ** (người dùng nhận được lời giải thích tiếng Việt, đúng sự việc) nhưng **chưa có gì ở tầng API**. Đúng với phạm vi của một lab; thành vấn đề khi lên production.

### 19.2 Đối chiếu notes W4D3 mục 2.4 (khung failure handling)

Khung đó có ba dòng mẫu:

| Dòng trong W4D3 2.4 | Đối chiếu với bài |
|---|---|
| 429, 529: có, backoff, tối đa N lần | **Khớp.** Bài thêm: theo `retry-after`, có jitter, và fallback sau khi hết số lần |
| Output không parse được: **có (1 lần)**, thử lại kèm lỗi | **Khác bản chất với định nghĩa của bài.** Bài định nghĩa retriable là gửi lại **đúng y** request. "Thử lại kèm lỗi" là request **khác** (có thêm thông báo lỗi), tức **sửa lại** (repair), không phải chờ cho lỗi tạm thời tự hết. Hợp lý vì output không tất định và có phản hồi, nhưng nên là nhóm riêng với trần riêng (Lab 2: 1 lần) **[ngoài tài liệu]** |
| Input vượt giới hạn: không, từ chối | **Khớp** terminal (400) |

Khung đó **còn thiếu** so với bài: 500 đến 504 (retriable), 401, 403, 404 (terminal), timeout, **refusal (200)**, **lỗi kết quả tool**. Khung cập nhật để dùng trong design doc **[ngoài tài liệu]** (đề xuất, chưa sửa file W4D3):

| Lỗi | Nhóm | Hành động | Người dùng nhận (đề xuất) | Ghi log |
|---|---|---|---|---|
| 429 | Retriable | Theo `retry-after`, backoff có jitter, tối đa N lần | Hết N lần: "Hệ thống đang bận, thử lại sau ít phút" hoặc kết quả đơn giản hơn | Mỗi lần retry |
| 529, 500 đến 504 | Retriable | Như trên; kéo dài thì đường dự phòng | Như trên | Mỗi lần retry |
| Timeout | Retriable có điều kiện | Thử lại một lần; lặp lại thì sửa request | "Yêu cầu mất quá nhiều thời gian" | Có |
| 400 do lỗi của ta | Terminal | Không retry | Thông báo chung ("không xử lý được"), **không lộ chi tiết nội bộ** | **Báo động cho dev** |
| 400 do input người dùng không hợp lệ (quá dài...) | Terminal | Từ chối | Nói rõ lỗi của input để người dùng sửa | Có |
| 401, 403 | Terminal | Không retry | Thông báo chung, **không lộ** lý do | **Báo động cho vận hành** |
| Refusal | Terminal | Không retry im lặng | "Không thể xử lý yêu cầu này", gợi ý diễn đạt lại | Có |
| Output không parse được | Sửa lại (repair) | Thử lại một lần kèm lỗi (như Lab 2) | Nếu vẫn sai: lỗi gọn | Có |
| Tool lỗi | Tuỳ tool | `is_error` cho model; retry nếu tạm thời | Model diễn giải (như `summary` của Lab 2) | Có |

## 20. Đọc phê phán **[ngoài tài liệu]**

1. **Retry và hành động có tác dụng phụ (idempotency).** Phép thử của bài chỉ hỏi "thử lại có khả năng thành công không", không hỏi "thử lại có **an toàn** không". Timeout là kết quả mơ hồ: server có thể đã xử lý xong. Lab 3: `create_ticket` (POST) retry sau timeout có thể **tạo trùng**; `delete_ticket` retry sau một lần xoá đã thành công trả **404** (kết quả "delete lần hai (404)" ở LAB3 mục 5.3), tức báo lỗi dù việc đã xong. Cần idempotency key, hoặc chỉ tự động retry thao tác **đọc**; thao tác ghi thì dùng HITL như Lab 2 (LAB2 mục 6: bảo vệ hành động phá hủy là xác nhận của người, không phải retry hay giới hạn vòng).
2. **Nhiều tầng retry chứ không chỉ hai.** SDK (HTTP), vòng tự viết, **model tự gọi lại tool** (kịch bản C của Lab 2), và vòng agent (`MAX_ROUNDS`). Mỗi tầng nhân lên. Cần **một ngân sách retry tổng** ghi ở design doc (mục budget, W4D3 mục 2.1 quyết định 3), không để mỗi tầng tự quyết.
3. **Lỗi HTTP 200 nhưng hỏng không chỉ có refusal.** Danh sách `stop_reason` của SDK 2.6.0 (`types/stop_reason.py`) gồm `end_turn`, `max_tokens`, `stop_sequence`, `tool_use`, `pause_turn`, `refusal`, `model_context_window_exceeded` **[SDK]**. `max_tokens` (output bị cắt, W4D2 mục 13 điểm 7) và `model_context_window_exceeded` cũng là 200 mà bộ phân loại status không thấy. Cần kiểm `stop_reason` trên mọi phản hồi, không chỉ `refusal`. Chưa thử hành vi thực tế của từng giá trị.
4. **Mã mẫu của bài là mảnh trích, không chạy nguyên văn:** `def run_tool(tool_use):` xuất hiện hai lần, đoạn refusal dùng biến `response` mà phạm vi đó không có và thụt lề lệch. Ý đúng: kiểm `response.stop_reason` sau khi gọi, **trước khi** dùng `content`. Ném `ValueError` chung cho refusal cũng dễ bị bộ bắt lỗi rộng nuốt; nên dùng một loại ngoại lệ riêng không nằm trong đường retry.
5. **Danh sách mã cứng (mục 16 điểm 2):** 408 và 409 không thuộc tập nào của bài nhưng SDK retry chúng; mã 5xx ngoài 500 đến 504 cũng vậy. Mặc định "chưa chắc thì terminal" khớp nguyên tắc an toàn của bài, nhưng cần biết nó **khác** SDK.
6. **"Ngân sách retry" bài dùng mà không định nghĩa:** số lần, tổng thời gian chờ hay token? Nên gắn với trần độ trễ p95 của design doc: số lần retry nhân thời gian chờ không được vượt trần đó. Ví dụ: backoff mặc định của SDK với 3 retry là 0.5 + 1 + 2 = **3.5 giây** (chưa tính jitter và thời gian từng request).
7. **`retry-after` không có trần hợp lý trong SDK [SDK]:** nếu server đòi chờ rất lâu, SDK chờ đúng như vậy. Hệ thống cần **deadline riêng** (tổng thời gian cho một yêu cầu) để không treo người dùng. Mới đọc mã, chưa tái hiện.
8. **Đường lỗi cũng cần test (nối Phần A).** Bài nói "mỗi đường lỗi là code phải test". Cách tái hiện lỗi thật cho ISSUES (còn mở): chạy một server giả cục bộ trả 429 hoặc 529 vài lần kèm `retry-after` rồi trả 200, trỏ `base_url` của client vào đó. Đây là functional hoặc integration test cho tầng retry, rẻ và lặp lại được. **Gợi ý, chưa làm.**
9. **Ghi retry vào trace.** Mỗi lần thử lại và status của nó nên có trong trace (Phần A mục 5), để phân biệt "chậm do retry" với "chậm do model". Hiện Lab 2 không thấy được retry của SDK vì SDK retry bên trong lệnh gọi.
10. **Ghi chú về 529 và `retry-after`:** bài nói `retry-after` có trong cả 429 và 529; mình chưa đối chiếu. Bài cũng nhắc tên header và giá trị gắn với phiên bản.

## 21. "Watch Out" của bài Failure Handling

**Mục Watch Out chính thức của bài này là case ở mục 21.2** (gửi bù sau). Bản dán đầu của bài chỉ có ba khung (mục 18); bảng dưới là bẫy ngầm mình suy ra từ ba khung đó, đứng cạnh case, cũng đã gộp vào bảng ở mục 8:

| Bẫy | Cách tránh |
|---|---|
| **Retry lỗi terminal** (400, 401...): phí ngân sách retry, che lỗi thật | Phân loại theo status; chưa chắc thì coi là terminal và ném lỗi |
| **Hai tầng retry nhân số lần thử** | Chọn một nơi đặt retry: để SDK lo lỗi tạm thời, hoặc hạ retry SDK và tự sở hữu |
| **Nuốt lỗi tool, trả kết quả rỗng** | `is_error: true` cùng thông báo rõ |
| **Refusal là 200** nên không qua bộ phân loại theo status | Kiểm `stop_reason`, ném lỗi, ghi log, không retry |

### 21.1 Đối chiếu cách hiểu của mình với pattern retry quen thuộc **[ngoài tài liệu]**

Cách hiểu của mình: error handling ở đây giống pattern lập trình thường thấy. Khi nối tới dịch vụ bên thứ ba như DB thì retry với số lần tối đa cụ thể (thường 3), vượt thì dừng và ném lỗi để xử lý. Bài quy định mã nào retriable (đa số lỗi phía server) và mã nào terminal (thường là lỗi từ phía ứng dụng của ta). **Đúng gần hết**, có hai chỉnh.

**Giống:** đúng là cùng khuôn với retry lỗi tạm thời ở tầng truy cập dữ liệu (kiểu Polly retry có trần số lần). Giống ở: trần số lần, backoff tăng dần, vượt trần thì ném lỗi, lỗi không tạm thời thì không retry, và hai tầng retry chồng nhau thì nhân số lần thử (ví dụ `HttpClient` đã gắn handler retry rồi lại bọc thêm retry ở tầng ứng dụng).

**Chỉnh 1: tiêu chí là "thời gian có giải quyết không", không phải "lỗi do bên nào".**

| Mã | Phía gây lỗi | Nhóm |
|---|---|---|
| 429 | **Phía ta** (gửi quá nhanh, 4xx) | **Retriable** |
| 529, 500 đến 504 | Phía Anthropic | Retriable |
| 400 | Phía ta (request sai) | Terminal |
| 401, 403 | Cấu hình hoặc quyền (key sai, thiếu quyền), thường là vấn đề vận hành chứ không phải bug code | Terminal |
| 404 (tên model sai) | Cấu hình | Terminal |
| Refusal (200) | **Không phải lỗi**: quyết định về nội dung của model | Terminal |

Quy tắc "5xx thì retry, 4xx thì không" là heuristic gần đúng, nhưng 429 là 4xx mà vẫn retriable (và SDK còn retry 408, 409, mục 16). Terminal cũng không nhất thiết là "lỗi do ta ném ra": nó là lỗi mà **lặp lại đúng request thì vẫn lỗi như cũ**.

**Chỉnh 2: ba chỗ khác với retry kiểu DB.**
1. **Lỗi có thể là dữ liệu đưa cho model.** Với DB, lỗi là ngoại lệ ném cho bên gọi. Với tool, lỗi được gửi lại cho Claude (`is_error: true`) và **model quyết định bước tiếp** (thử lại, hỏi lại, dừng). Model là một vòng retry thêm (kịch bản C của Lab 2).
2. **Có lỗi "200 nhưng hỏng"** (refusal, `max_tokens`, `model_context_window_exceeded`) mà bộ phân loại theo mã không thấy, nên phải kiểm `stop_reason`.
3. **Retry tốn tiền và độ trễ hơn**, và output không tất định nên có thêm loại "sửa lại rồi thử" (repair) không có ở DB (mục 19.2).

Hai điều quen thuộc từ DB vẫn áp dụng và bài chưa nói: **idempotency** của thao tác ghi khi retry (mục 20 điểm 1), và **circuit breaker** (khi 529 kéo dài thì ngừng gửi và fail fast thay vì thử mãi). Circuit breaker là gợi ý của mình; bài chỉ nhắc "chuyển đường dự phòng".

### 21.2 Case của bài: lệnh gọi chưa từng lỗi lúc phát triển **[docs]**

**Đây là mục Watch Out của bài Failure Handling** (case "Why this broke", gửi bù sau; bạn xác nhận là mục Watch Out của khóa).

**Chuyện gì xảy ra.** Lúc phát triển, dev gọi endpoint vài chục lần và lần nào cũng sạch, nên không viết đường lỗi. Lưu lượng dev thấp, kết nối ổn, hiếm chạm các điều kiện gây lỗi (rate limit, timeout, rớt mạng, phản hồi hỏng khi tải), nên **code xử lý chúng không bao giờ được viết**. Mã đã ship:

```python
for item in batch:
    resp = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, messages=msg(item))
    results.append(resp.content)    # assumes every call returns 200
```

Ở đỉnh lưu lượng đầu tiên API trả rate limit, ngoại lệ không xử lý bị ném, **cả request hỏng** thay vì chờ rồi thử lại. Với người dùng, tính năng như bị hỏng. Phản xạ đầu của dev: retry ngay trong vòng lặp chặt. **Càng tệ**, vì mỗi lần retry tức thì là thêm một request vào cùng hạn mức. Cách chữa thật là phép phân loại của bài: 429 là **retriable**, nên cần **backoff luỹ thừa, số lần có trần, và đọc `retry-after`** khi phản hồi có.

**Vì sao vỡ:** lỗi retriable gặp code không có đường lỗi, rồi gặp retry dội làm hạn mức sâu thêm. Phân loại lỗi là retriable, rồi backoff có trần, **trước khi** lưu lượng tìm ra lỗ hổng thay bạn.

**Đối chiếu [ngoài tài liệu]:**
1. **Chỗ chưa khớp với SDK (mục 16).** Mã mẫu dùng `client.messages.create` của SDK, mà SDK 2.6.0 mặc định `max_retries=2` với backoff 0,5s × 2^n, có jitter, đọc `retry-after`. Vậy một 429 đơn lẻ **không** làm sập request ngay nếu dùng SDK mặc định; ngoại lệ chỉ bay ra **sau khi hết lượt retry**. Case chỉ khớp nếu (a) đợt quá tải kéo dài hơn khoảng 1,5 giây mà hai lần retry mặc định chờ (0,5 + 1), (b) client được tạo với `max_retries=0`, hoặc (c) không dùng SDK. Bài không nói. Mình chưa quan sát 429 thật nên không khẳng định (mục 24).
2. **"Retry ngay trong vòng chặt" bọc quanh lệnh SDK chính là hai tầng retry nhân số lần** (bẫy 2 ở trên, ví dụ 3 × 3 = 9 request ở mục 16), và còn tệ hơn vì **không có backoff**. Case là ví dụ sống cho mục 16 và mục 20 điểm 2.
3. **Bản sửa của bài chỉ nêu ba thứ** (backoff, trần, `retry-after`). Còn thiếu, đối chiếu mục 20: (a) **hết trần thì làm gì**: fallback hoặc lỗi gọn (mục 18); (b) **mất kết quả một phần**: vòng `for` hỏng ở một item làm mất cả `results` đã gom, cần xử lý lỗi **từng item** và lưu kết quả đã có; (c) **giới hạn tốc độ phía client** (semaphore hoặc token bucket) để không chạm giới hạn rồi mới xin lỗi; (d) **deadline tổng** và ngân sách retry nằm trong trần độ trễ (mục 20 điểm 6, 7; mục 43); (e) **idempotency** nếu thao tác là ghi (mục 20 điểm 1).
4. **Vì sao dev không thấy lỗi lúc phát triển:** đây là lý do cụ thể cho điều "đường lỗi cũng cần test" (mục 20 điểm 8). Nếu không chủ động **tiêm lỗi** (server giả trả 429 vài lần rồi 200), "chưa từng thấy lỗi" sẽ thành "chưa từng viết xử lý". Failure injection biến lỗi hiếm thành thứ thấy mỗi lần chạy test.
5. **Lab 2 đang ở đúng trạng thái "shipped version" của case này, ở tầng API.** Mục 19.1 đã ghi Lab 2 không có `try` quanh `client.messages.create`; có `max_retries=3` của SDK, hết lượt thì traceback. Tầng tool thì xử lý rất kỹ, tầng API thì chưa.

### 21.3 Checkpoint của bài Failure Handling **[docs]** và đối chiếu **[ngoài tài liệu]**

**Đề.** Khối mã có **một lỗi**; nêu lỗi và viết bản đã sửa.

```python
def call_with_retry(make_call, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            return make_call()
        except Exception:
            time.sleep(0)
    raise RetryBudgetExhausted()
```

Đáp án mẫu của khóa nhận sau khi làm; đối chiếu ở cuối mục này ("Đáp án của khóa"). Phần ngay dưới là câu trả lời và bản sửa của mình trước khi xem đáp án.

**Mình trả lời gì, và đối chiếu:**

| Câu trả lời của mình | Nhận xét |
|---|---|
| (1) Bắt mọi lỗi, **không phân loại** retriable hay terminal, cứ retry đến hết ngân sách | **Đúng, là lỗi cốt lõi** của bài (mục 15). Thiếu phần cách lấy `status` từ exception và chỗ cắm `is_retriable` vào vòng lặp |
| Đoạn `is_retriable(status)` | Đúng, nhưng hàm nhận **số status**, còn `except Exception` cho ra **exception**. Cần `status_code` của exception, và quy tắc cho lỗi **không có status** (timeout, mạng, bug) |
| (2) Trả `{"type": "tool_result", ..., "is_error": True}` trong `except` | **Sai tầng**, xem dưới |
| "Chờ đến hết ngân sách rồi tự ném, lúc đó Claude không làm được gì" | Đúng một nửa, xem dưới |

**Lỗi mình bỏ sót, và là lỗi dễ thấy nhất: `time.sleep(0)`.** Vòng lặp **không chờ gì**: không backoff, không jitter, không đọc `retry-after`. Đây đúng là "retry ngay trong vòng chặt" của case ở mục 21.2: mỗi lần thử tức thì là thêm một request vào cùng hạn mức, làm nó sâu hơn. Vậy "một lỗi" của đề có hai mặt: **retry mù (không phân loại)** và **retry không chờ**. Mặt thứ ba nhỏ hơn: `raise RetryBudgetExhausted()` **trống**, mất lỗi gốc (che lỗi thật, mục 15).

**Vì sao (2) sai tầng.** Đoạn `is_error: True` là của **tool runner** (mục 17): tool chạy lỗi thì báo cho Claude biết. Còn `call_with_retry` bọc **một lệnh gọi** (thường là gọi API). Đặt `return {... "is_error": True}` trong `except` sẽ:
- **Kết thúc vòng lặp ngay ở lần lỗi đầu tiên** (vì `return`), biến mọi lỗi retriable thành terminal, tức **phá chức năng retry**; và `tool_use` không tồn tại trong hàm này.
- Nếu `make_call` là chính lệnh gọi Claude (`messages.create`) thì **không có Claude nào để trả lỗi về**: lỗi API không đi qua `tool_result`.

Phân tầng đúng: **tầng retry** thử lại lỗi retriable, hết thì **ném lỗi mô tả rõ** (kèm lỗi gốc); **tầng tool runner ở trên** bắt lỗi đó và chuyển thành `is_error: True` cho Claude. Về câu "Claude không còn làm được gì": chỉ đúng khi **không ai bắt** ngoại lệ (traceback, như Lab 2 ở mục 19.1). Nếu tool runner chuyển thành `is_error` thì Claude **vẫn làm được**: giải thích cho người dùng, thử cách khác, hoặc dừng.

**Bản sửa [đã chạy thử với lỗi giả và với các lớp exception thật của SDK 2.6.0]:**

```python
import time, random, anthropic

RETRIABLE = {429, 529, 500, 502, 503, 504}

class RetryBudgetExhausted(Exception): pass

def is_retriable(exc):
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status in RETRIABLE                     # lỗi có status: theo bảng
    # timeout và lỗi mạng của SDK; mọi thứ khác (kể cả bug) là terminal
    return isinstance(exc, (anthropic.APIConnectionError, TimeoutError, ConnectionError))

def retry_after(exc):                                  # thời gian chờ có thẩm quyền, nếu server gửi
    headers = getattr(getattr(exc, "response", None), "headers", None) or {}
    try:
        return float(headers.get("retry-after"))
    except (TypeError, ValueError):
        return None

def backoff(attempt):                                  # 0,5s x 2^n, trần 8s, jitter 75 đến 100%
    return min(8.0, 0.5 * 2 ** attempt) * (1 - 0.25 * random.random())

def call_with_retry(make_call, max_attempts=5):
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return make_call()
        except Exception as exc:
            if not is_retriable(exc):
                raise                                  # terminal: ném ngay, giữ nguyên lỗi thật
            last_exc = exc
            if attempt == max_attempts - 1:
                break                                  # hết lượt: không ngủ thừa
            time.sleep(retry_after(exc) or backoff(attempt))
    raise RetryBudgetExhausted(f"gave up after {max_attempts} attempts") from last_exc
```

**Kết quả chạy thử (lỗi giả, `time.sleep` được thay để ghi thời gian chờ):**

| Tình huống | Kết quả |
|---|---|
| 429, 429, rồi OK | Trả OK, chờ 0,46s rồi 0,91s |
| 429 kèm `retry-after: 3`, rồi OK | Chờ **đúng 3,0s** (theo header, không theo backoff) |
| 400 | Ném `FakeHTTPError` **ngay**, không chờ lần nào |
| `KeyError` (bug) | Ném **ngay**, không retry |
| 500 liên tục 5 lần | `RetryBudgetExhausted` kèm `__cause__` là lỗi 500; chờ 4 lần (0,43; 0,86; 1,61; 3,38s), **không ngủ sau lần thứ 5** |
| `TimeoutError`, rồi OK | Retry, chờ 0,48s |

Và trên các lớp thật của SDK 2.6.0 (`is_retriable`): `RateLimitError` 429 và `InternalServerError` 500 là retriable; `BadRequestError` 400 và `AuthenticationError` 401 là terminal; `APITimeoutError` và `APIConnectionError` là retriable; `KeyError` là terminal. Header `retry-after` đọc được qua `exc.response.headers`.

**Một phát hiện từ lúc kiểm:** bản đầu mình viết chỉ có `isinstance(exc, (TimeoutError, ConnectionError))` cho lỗi không có status. Kiểm với SDK thì thấy `APITimeoutError` là con của `APIConnectionError` và **không kế thừa `TimeoutError` của Python**, nên bản đầu sẽ xếp timeout thật của SDK vào **terminal**. Đã thêm `anthropic.APIConnectionError`. Đây là cái bẫy mà chỉ chạy với exception thật mới lộ.

**Còn lại, bản sửa vẫn chưa làm [ngoài tài liệu]:**
1. **Chồng với retry của SDK (mục 16).** Nếu `make_call` gọi qua client SDK mặc định (`max_retries=2`), mỗi lần thử là tối đa 3 request, 5 lần thử là tối đa **15 request**. Chọn một nơi retry: hạ `max_retries` của SDK xuống, hoặc bỏ vòng này.
2. **Idempotency** nếu `make_call` là thao tác ghi (mục 20 điểm 1), và **deadline tổng** để `retry-after` lớn không treo yêu cầu (mục 20 điểm 7).
3. **Ghi mỗi lần retry vào trace** (mục 20 điểm 9) để phân biệt "chậm do retry" với "chậm do model".
4. Hàm `retry_after` chỉ đọc dạng **số giây**; header cũng có thể ở dạng ngày HTTP (SDK xử lý cả hai, mục 16).

**Đáp án của khóa [docs].** Lỗi: **không có backoff** (`time.sleep(0)` bắn retry ngay lập tức), và vòng lặp còn **retry mọi exception kể cả terminal như 400**. Với rate limit, mỗi retry tức thì tính thêm một request và làm hạn mức sâu hơn thay vì chờ nó tan. **Ba sửa:** (1) đọc `retry-after` từ header trước, rồi mới lùi về backoff luỹ thừa; (2) khoảng chờ tăng dần giữa các lần, có trần; (3) **fail fast** với terminal (400, 401, 403, 404).

```python
def call_with_retry(make_call, max_attempts=5, cap=30):
    for attempt in range(max_attempts):
        try:
            return make_call()
        except anthropic.RateLimitError as e:
            wait = e.response.headers.get("retry-after")
            if wait is None:
                wait = min(cap, 2 ** attempt) + random.uniform(0, 1)
            time.sleep(float(wait))
        except anthropic.APIStatusError as e:
            if not is_retriable(e.status_code):
                raise                        # fail fast on terminal
            time.sleep(min(cap, 2 ** attempt) + random.uniform(0, 1))
    raise RetryBudgetExhausted()
```

**So khớp với câu trả lời của mình:**

| Ý | Mình | Khóa |
|---|---|---|
| Không phân loại, retry cả lỗi terminal | **Có** (ý đầu của mình) | Có, là sửa (3); khóa dùng chính `is_retriable(status)` mình đã viết |
| **Không backoff (`sleep(0)`)** | **Bỏ sót ở bản đầu** | **Là ý đầu tiên của khóa** (sửa 1 và 2) |
| Đọc `retry-after` trước, backoff sau | Chỉ thêm ở bản sửa | Có, sửa (1) |
| Trần cho khoảng chờ | Chỉ thêm ở bản sửa | Có, sửa (2) |
| Trả `is_error: True` trong `except` | Có | **Không có**: xác nhận đó là **sai tầng**, thuộc tool runner (mục 17), không thuộc hàm retry |

Bản sửa của mình (phía trên) có đủ ba sửa của khóa, cộng ba thứ khóa không có: retry **timeout và lỗi mạng**, giữ **lỗi gốc** (`from last_exc`), và **không ngủ sau lần cuối**.

**Đáp án của khóa là bản tối thiểu cho checkpoint, có chỗ hở.** Mình chạy nguyên văn với exception thật của SDK 2.6.0 (`time.sleep` được thay, không chờ thật):

| Chỗ hở | Kết quả chạy thử |
|---|---|
| **Ngủ sau lần cuối** rồi mới ném lỗi | 429 liên tục 5 lần: ngủ 5 lần `[1,62; 2,57; 4,35; 8,98; 16,98]`. Lần cuối khoảng 17 giây hoàn toàn thừa |
| **`retry-after` không có trần** (`cap` chỉ áp cho backoff) | Header `3600` thì ngủ 3600 giây **mỗi lần**, 5 lần. Cần deadline tổng (mục 20 điểm 7) |
| **`float(wait)` với `retry-after` dạng ngày HTTP** | **`ValueError` rò ra**, che mất lỗi API (SDK xử lý cả hai dạng, mục 16) |
| **Không có nhánh cho timeout và lỗi mạng** | `APITimeoutError` và `APIConnectionError` bị **ném ngay, không retry**, mâu thuẫn với bảng mục 15 (timeout thường retriable) |
| **`RetryBudgetExhausted()` trống, không `from`** | `__cause__` là `None`: **mất lỗi gốc** (che lỗi thật, mục 15) |

Thêm hai điểm không cần chạy: (a) hằng số backoff khác SDK (khóa: 2^n bắt đầu từ 1s, trần 30s, cộng jitter 0 đến 1s; SDK: 0,5s × 2^n, trần 8s, nhân jitter 75 đến 100%, mục 16), cùng ý; (b) khóa không nói chuyện **chồng với retry của SDK** (mục 16): 5 lần thử nhân 3 request là tối đa 15 request.

Điểm đúng của khóa: **thứ tự `except` đúng** (nhánh cụ thể `RateLimitError` trước nhánh chung `APIStatusError`), dùng đúng tên lớp của SDK, và chọn `retry-after` làm nguồn ưu tiên. Kết luận: dùng **khung của khóa** cho checkpoint, nhưng bản dùng thật nên thêm các sửa ở bảng trên.

## 22. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Retriable hay terminal | W4D3 mục 2.1, 2.4 (failure handling của design doc) |
| SDK tự retry 429 và 529, `max_retries` | NOTES.md mục 1 ("Về retry"), ISSUES.md "Còn mở", LAB2 (`max_retries=3`) |
| 400 là terminal: sửa request | W4D2 mục 7: `temperature` và prefill bị 400 trên haiku; thử lại nguyên văn không giúp gì |
| `is_error` cho tool | LAB2 mục 2 (yêu cầu 3), mục 5 (nuốt lỗi), mục 6 (`except Exception`) |
| Refusal, `max_tokens` là 200 | W4D2 mục 7 điểm 4 và mục 13 điểm 7 (`stop_reason == "max_tokens"`) |
| Failure injection, ghi retry vào trace | Phần A mục 4 (mức test) và mục 5 (trace) |
| Ngân sách retry, trần độ trễ | W4D3 mục 2.1, 2.2 (budget), Cost & Orchestration (chủ đề sau) |

## 23. Câu hỏi ôn tập (Phần B)

1. Phép thử để phân biệt retriable và terminal là gì? Xếp 429, 529, 500, 400, 401, 403 vào nhóm và nêu lý do.
2. Vì sao khi chưa chắc nên coi lỗi là terminal? Hai kiểu phân loại nhầm có hậu quả khác nhau thế nào?
3. Bạn bọc vòng retry 3 lần quanh lệnh gọi SDK đang để mặc định. Chuyện gì xảy ra với số request? Hai cách tránh?
4. `retry-after` dùng thế nào so với backoff luỹ thừa? SDK 2.6.0 làm thế nào?
5. Vì sao tool lỗi phải trả `is_error: true` thay vì chuỗi rỗng? Tìm hai ví dụ trong LAB2 mục 5 minh hoạ hậu quả khi không làm vậy.
6. Refusal là HTTP 200. Bộ phân loại theo status có thấy không? Cần làm gì, và vì sao không retry?
7. Vì sao "output không parse được, thử lại kèm lỗi" trong khung W4D3 không hoàn toàn là retriable theo định nghĩa của bài?
8. Vì sao retry `create_ticket` sau timeout nguy hiểm, và `delete_ticket` thì lỗi theo kiểu khác? Giải pháp?
9. Người dùng cuối nhận gì khi 429 hết số lần retry? Bài nói gì, và phần nào là đề xuất của bạn?

## 24. Còn lại và việc cần kiểm tra (Phần B)

- **Chưa chạy thật:** mọi hành vi retry mới ở mức đọc mã SDK; **chưa quan sát** 429 hoặc 529 thật (ISSUES còn mở). Cần thử bằng server giả (mục 20 điểm 8).
- **Chưa đọc:** `_should_retry_exception` (timeout, lỗi mạng); hành vi từng `stop_reason` (`pause_turn`, `model_context_window_exceeded`).
- **Chưa kiểm với docs:** tên header `retry-after` trên 529; bảng mã lỗi chính thức; có tính tiền cho request bị timeout giữa chừng hay không.
- **Khung failure handling** ở mục 19.2 mới là đề xuất; chưa sửa W4D3 mục 2.4.
- **Lab 2** chưa có `try` quanh `client.messages.create`; nếu làm tiếp: bắt lỗi API, phân nhóm, báo người dùng gọn và ghi log.
- **Model Selection** (câu 6): xem Phần C.

---

# Phần C. Model Selection

Nguồn: bài "Model selection in production": họ model và các bậc, đánh đổi chất lượng, độ trễ, chi phí, routing, khi nào nâng hoặc hạ bậc. **[ngoài tài liệu]** là suy luận hoặc tính toán của mình; giá lấy từ NOTES.md mục 2 (bảng giá ghi trong tài liệu SDK), cần đối chiếu trang giá chính thức.

## 25. Bài này đứng ở đâu

Câu mở bài: quản lý chi phí tối ưu chi tiêu **bên trong** một model; chọn model đặt **đường cơ sở** mà việc tối ưu đó xuất phát. Chọn sai bậc thì mọi tối ưu sau đó chỉ cắt tỉa quanh một con số đã sai. Bài còn nhắc "các màn trước giữ hệ thống trong ngân sách sau khi đã chọn model": phần quản lý chi phí đó thuộc chủ đề Cost & Orchestration (chưa có tài liệu); ở đây chỉ học phần chọn model.

## 26. Họ model và các bậc năng lực **[docs]**

| Bậc | Vai trò theo bài |
|---|---|
| **Fable** | Mạnh nhất, cho suy luận, code và việc agent đòi hỏi cao nhất |
| **Opus** | Việc đòi hỏi cao, vượt phạm vi của Sonnet |
| **Sonnet** | **Mặc định cân bằng** cho phần lớn khối lượng production |
| **Haiku** | Nhanh và tiết kiệm, cho việc nằm trong khả năng của nó |

- Các bậc đánh đổi chi phí, độ trễ và năng lực với nhau.
- Bài nói "cùng một prompt chạy trên bất kỳ bậc nào, nên chọn model là một đòn bẩy đặt theo từng workload và đổi được **mà không phải viết lại ứng dụng**". Câu này chỉ đúng một phần (mục 30).
- Bài nhắc xác nhận đội hình và ID model tại platform.claude.com lúc build.

**Ghi chú về repo [ngoài tài liệu]:** bảng ở NOTES.md mục 2 dùng ID `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`. Danh sách model mới nhất mình biết trong phiên này ghi Fable là `claude-fable-5-2`. Nếu cần bảng cập nhật thì chạy lại `bench_models.py` với ID hiện hành.

## 27. Đánh đổi chất lượng, độ trễ, chi phí **[docs]**

- **Nâng bậc:** mua chất lượng bằng giá mỗi token cao hơn và thường độ trễ cao hơn.
- **Hạ bậc:** mua tốc độ và chi phí thấp, đổi lại rủi ro tụt chất lượng.
- **Ngoại lệ:** model bậc cao có thể xử lý một yêu cầu **nhanh hơn và rẻ hơn** nếu nó kết luận bằng **ít token hơn** model bậc thấp.
- **Chi phí của sai lầm phải nằm trong phép tính:** tiết kiệm vài đô mỗi ngày bằng model thấp là không đáng nếu chất lượng tụt gây lỗi kéo theo chi phí lớn phía sau.
- **Không có lựa chọn đúng toàn cục**, chỉ có lựa chọn đúng cho một tác vụ ở một chuẩn chất lượng. Kỷ luật cần có: **làm cho đánh đổi đo được**, đừng mặc định với model mạnh nhất; đây là "lỗi phổ biến và đắt nhất" trong chọn model.

### 27.1 Con số cho các ý trên **[ngoài tài liệu]**

**Tỉ lệ giá (từ NOTES.md mục 2, $/1M token vào và ra):**

| Model | Vào / ra | So với Sonnet |
|---|---|---|
| Haiku | 0.10 / 0.50 | 1/20 |
| Sonnet | 2.00 / 10.00 | 1 |
| Opus | 4.00 / 20.00 | 2 lần |
| Fable | 10.00 / 50.00 | 5 lần |

Điều kiện hoà vốn cho ý "bậc cao có thể rẻ hơn": Opus rẻ hơn Sonnet chỉ khi dùng **ít hơn một nửa** số token; Fable chỉ khi dùng ít hơn **một phần năm**. Chiều ngược lại: Haiku còn rẻ hơn Sonnet ngay cả khi phải dùng đến 20 lần số token. Nên ý "bậc cao rẻ hơn nhờ ít token" có thể xảy ra nhưng đòi mức tiết kiệm token lớn, và **bench của mình chưa thử ý này** (cả 4 model đạt 1.00 và đều ở `effort: low`). Cũng chỉ mới tính giá token, chưa tính retry hay làm lại.

**Chi phí của lỗi (con số minh hoạ, không phải đo thật):**

```
tổng chi phí mỗi tác vụ = chi phí một lần gọi + P(sai) x chi phí một lần sai

Haiku : 0.00003 + 0.10 x 0.50 = 0.05003   (sai 10%, mỗi lỗi tốn 0.50 USD)
Sonnet: 0.00066 + 0.02 x 0.50 = 0.01066   (sai 2%)
```

Chi phí gọi chênh 22 lần nhưng tổng chi phí thì Sonnet rẻ hơn gần 5 lần, vì chi phí lỗi áp đảo chi phí token. Ngược lại nếu lỗi gần như không tốn gì (ví dụ bản nháp có người duyệt) thì Haiku thắng. Mấu chốt: cần **ước lượng P(sai)** (từ eval) và **chi phí một lần sai** (từ nghiệp vụ); cả hai đều không có sẵn trong bài.

## 28. Quy trình chọn: bắt đầu từ Sonnet, nâng hoặc hạ bậc bằng eval **[docs]**

- **Bắt đầu với Sonnet.**
- **Nâng lên Opus (hoặc Fable)** khi eval cho thấy model hiện tại **trượt ở các ca khó nhất** trong lưu lượng của bạn và chi phí của đáp án sai cao.
- **Hạ xuống Haiku** khi eval cho thấy model rẻ hơn **giữ được chuẩn chất lượng ở phần lớn lưu lượng**, giải phóng ngân sách và độ trễ.
- **Cả hai chiều, eval là dụng cụ đo:** thay model được duyệt theo **điểm đo trên các ca của bạn**. Vì thế eval đã dựng ở W4D1 đến W4D3 cũng là **cổng chặn cho quyết định đổi model**.

### 28.1 Đối chiếu với quy tắc trong NOTES.md **[ngoài tài liệu]**

| | Điểm xuất phát | Điều kiện đổi bậc |
|---|---|---|
| NOTES.md mục 2 (mình rút từ bench) | **Model rẻ nhất** | Nâng khi eval cho thấy rẻ không đạt |
| Bài Model Selection | **Sonnet** (mặc định cân bằng) | Nâng khi eval cho thấy trượt ca khó và lỗi đắt; hạ khi eval cho thấy giữ chuẩn |

Hai quy tắc **đồng ý ở điểm cốt lõi** (đừng mặc định mạnh nhất, và eval quyết định) nhưng **khác điểm xuất phát**. Cách hoà giải của mình: khi đã có eval thì chạy cả bậc thang một lần (đúng cách `bench_models.py` đã làm) rồi chọn model rẻ nhất đạt chuẩn; khi chưa có eval thì mặc định Sonnet. **Khi làm bài thi theo khóa học, trả lời theo bài: bắt đầu từ Sonnet.** Quy tắc NOTES.md vẫn đúng tinh thần nhưng nên sửa câu chữ cho khớp (chưa sửa).

**Điều kiện để "nâng bậc" có cơ sở:** tập eval phải **chứa ca khó nhất** của lưu lượng thật. Bench hiện tại cho cả 4 model 1.00 (ba prompt quá dễ), nên không thể dùng nó để chứng minh nâng bậc hay hạ bậc nào (NOTES.md mục 2, ISSUES "Còn mở").

### 28.2 Đối chiếu cách hiểu của mình **[ngoài tài liệu]**

**(a) Bắt đầu từ Sonnet là hợp lý vì nó cân bằng.** Đúng, nhưng có hai chỉnh để lý do chắc hơn:

1. **"Trung bình" tự nó chưa phải tiêu chí.** Tiêu chí vẫn là eval (rẻ nhất đạt chuẩn). Sonnet là **điểm xuất phát mặc định** (bài gọi là "balanced default for most production workloads"), không phải kết luận. Nếu eval cho thấy trượt ca khó thì vẫn phải nâng bậc.
2. **Sonnet không nằm giữa về giá, mà nằm ở "khuỷu" của thang giá.** Từ bảng mục 27.1: Haiku lên Sonnet là 20 lần, Sonnet lên Opus chỉ 2 lần, Opus lên Fable 2,5 lần. Hạ xuống Haiku tiết kiệm rất nhiều nhưng là bước nhảy lớn về rủi ro chất lượng; nâng lên Opus chỉ gấp đôi giá. Nên bắt đầu từ Sonnet và **hạ bậc bằng eval** là thí nghiệm tiết kiệm có kiểm soát, còn bắt đầu từ Haiku thì bước nhảy đầu tiên đã lớn.

**(b) Phép so sánh với stress test hoặc load test để chuẩn bị tài nguyên trước khi deploy.** Đúng một phần: cùng mục đích **chọn cấu hình rẻ nhất đáp ứng yêu cầu trước khi triển khai** (right-sizing, capacity planning). Nhưng **đại lượng đo khác nhau**:

| | Load hoặc stress test | Eval chọn model |
|---|---|---|
| Đo gì | Thông lượng, độ trễ, tỉ lệ lỗi khi **nhiều request đồng thời** | **Chất lượng** (độ đúng) trên các ca có độ khó khác nhau, kèm chi phí và độ trễ mỗi request |
| Biến thay đổi | Số lượng request, mức đồng thời | Bậc model, prompt |
| Câu hỏi | Cần bao nhiêu tài nguyên cho N người dùng | Bậc nào đạt chuẩn chất lượng với chi phí thấp nhất |
| "Capacity" nghĩa là | Sức chịu tải | **Năng lực của model** (độ thông minh), không phải sức chịu tải |
| Thời điểm | Gần cuối, trước deploy | **Sớm**, vì nó đặt đường cơ sở cho ngân sách; chạy lại mỗi khi đổi model |

Phép so sánh sát hơn: chọn cấu hình máy bằng **benchmark độ chính xác** (hoặc so hai thuật toán theo độ đúng và chi phí), với "độ đúng" thay cho "số người dùng chịu được". Hai thứ đứng cạnh nhau, không thay nhau.

**Phần load test vẫn có chỗ riêng** trong bức tranh, ở cuối: chạy tải ở khối lượng dự kiến để (1) nhân chi phí mỗi request với khối lượng thật và so với trần ngân sách (W4D3 mục 2.2), (2) xem hạn mức tốc độ của từng model có bị chạm không (429, Failure Handling; **chưa kiểm** hạn mức theo model), (3) xem độ trễ p95 dưới tải. Phần này thuộc về chủ đề Cost & Orchestration.

Thứ tự trong vòng đời: **chọn model bằng eval (sớm)** → test bộ máy và eval lặp lại → E2E, UAT → **load test để xác nhận ngân sách và hạn mức (muộn)**. Chọn model đi trước vì nó quyết định đường cơ sở mà các bước sau tối ưu từ đó (bài nói câu này ở đầu).

## 29. Routing: model mặc định cộng ghi đè theo tín hiệu **[docs]**

Mẫu phổ biến: **model mặc định có ghi đè**. Đa số lưu lượng đi qua model mặc định cân bằng; các loại yêu cầu cụ thể được đẩy sang model lớn hơn hoặc nhỏ hơn dựa trên một **tín hiệu rẻ** đọc từ yêu cầu: loại tác vụ, độ dài input, hoặc một phân loại độ khó. Cùng ý router ở Phần A mục 10, áp vào chọn model: chỉ trả tiền cho model mạnh ở các yêu cầu cần nó. Nếu mọi yêu cầu cùng một dạng thì **bỏ router, ghim một model**.

| Làm tốt | Thêm chi phí và độ phức tạp | Dùng cách khác |
|---|---|---|
| Ghép mỗi workload với model **rẻ nhất đạt chuẩn**, đo bằng eval chứ không giả định | Router thêm một bước phân loại và một đường model thứ hai phải bảo trì | Lưu lượng đồng đều ở một chuẩn chất lượng: ghim một model, bỏ router |

**Đọc phê phán [ngoài tài liệu]:**
1. **Router chỉ có lời khi tiết kiệm lớn hơn chi phí của nó:** (tỉ lệ yêu cầu chuyển sang model rẻ) × (khoản tiết kiệm mỗi yêu cầu) phải lớn hơn chi phí phân loại cộng chi phí của các lần phân loại nhầm. Cần số liệu lưu lượng thật.
2. **Hai kiểu nhầm có giá khác nhau** (như Phần A mục 10): yêu cầu khó bị đưa sang model nhỏ cho **chất lượng tụt âm thầm**; yêu cầu dễ bị đưa sang model lớn chỉ **tốn tiền**. Nên đo riêng từng loại nhầm.
3. **Bước phân loại là một prompt, nên cũng cần eval.** Và mỗi đường model là một cặp (prompt, model) cần **eval riêng** làm cổng chặn: "đường model thứ hai phải bảo trì" nghĩa là gấp đôi bộ test và eval.
4. **Router cũng là chỗ đặt fallback giữa các model khi lỗi** (Failure Handling: 529 kéo dài thì chuyển đường dự phòng). Model dự phòng cũng phải đã qua eval, không được chọn tạm lúc sự cố.
5. **Tín hiệu rẻ phải thực sự rẻ và dự đoán được độ khó.** Độ dài input là tín hiệu rẻ nhất nhưng chưa chắc phản ánh độ khó (câu ngắn vẫn có thể khó).

### 29.1 Checkpoint của bài Model Selection **[docs]** và đối chiếu **[ngoài tài liệu]**

**Đề.** Mỗi tình huống: chọn bậc model (Opus, Sonnet, Haiku) và nêu **một ràng buộc quyết định**, tức thứ duy nhất làm đáp án đổi. Ảnh gửi dừng ở tình huống 3 (màn 12 trên 23); nếu còn tình huống sau thì gửi bù.

| Tình huống | Đáp án của khóa | Ràng buộc quyết định | Vì sao phương án sai sai |
|---|---|---|---|
| 1. Phân loại khối lượng lớn, hàng triệu tin ngắn mỗi ngày; eval cho thấy **Haiku giữ chuẩn** | **Haiku** | **Chi phí ở khối lượng lớn**, vì eval đã xác nhận ngưỡng chất lượng còn giữ, nên trả cho model lớn hơn **không mua thêm gì** | Opus "độ sâu suy luận" và "nhất quán": mua thứ eval đã cho thấy không cần; Sonnet "cân bằng": trả thêm mà không được thêm |
| 2. Agent nhiều bước lập kế hoạch refactor **phụ thuộc nhau**, sai bước đầu rất đắt; eval cho thấy **Sonnet trượt ở ca khó nhất** | **Opus** | **Chất lượng ở suy luận khó, nơi chi phí của câu sai cao**, và eval cho thấy cần nâng bậc | Sonnet "hiệu quả chi phí" hoặc "độ trễ" và Haiku "tốc độ": tối ưu một trục không phải ràng buộc quyết định |
| 3. Lưu lượng hỗn hợp: đa số tra cứu đơn giản, ít tổng hợp phức tạp | **Route**: Sonnet (hoặc Haiku) mặc định cộng **Opus ghi đè** cho yêu cầu phức tạp | **Lưu lượng hỗn hợp**: một model duy nhất hoặc trả thừa ở việc đơn giản, hoặc yếu ở việc phức tạp | Opus cho tất cả (trả thừa), Haiku cho tất cả (yếu ở phức tạp), Sonnet cho tất cả (một model cho mọi nhu cầu) |

**Cách đọc.** Mỗi đáp án có đủ hai vế: *chọn gì* và *vì ràng buộc nào*. Phương án sai thường **đúng về một trục** (nhanh, rẻ, mạnh) nhưng không phải ràng buộc đang quyết định. Dụng cụ ra quyết định luôn là **eval**: giữ chuẩn thì hạ, trượt thì nâng, lưu lượng không đồng đều thì tách. Đúng quy trình mục 28 và mẫu routing mục 29.

**Đối chiếu [ngoài tài liệu]:**
1. **Tình huống 1 và 2 là hai chiều của cùng một phép đo.** Cùng nguyên tắc "model rẻ nhất đạt chuẩn đo bằng eval": ca dễ kéo xuống, ca khó đẩy lên. Không đáp án nào dựa vào "mạnh nhất cho chắc" (bẫy 1 mục 31).
2. **"Opus vì nhất quán" ở tình huống 1 là bẫy tinh tế.** Nhất quán là thứ **đo** bằng eval chạy lặp, không phải thứ mua bằng bậc model. (Trên `claude-haiku-5-5` còn không đặt được `temperature`, W4D2 mục 7, nên không thể trông vào việc ép tất định.)
3. **Tình huống 2 dùng chi phí của lỗi (mục 27.1).** Việc phụ thuộc nên lỗi bước đầu kéo theo các bước sau, giống phép nhân xác suất ở mục 40.2 điểm 8 (0,99^6 ≈ 94,1% theo giả định độc lập). Và vì việc **gắn chặt**, đáp án là **một agent Opus**, không phải orchestrator: nối với checkpoint Cost ở mục 44.2.
4. **Tình huống 3 viết "Sonnet (hoặc Haiku)" mà không chọn.** Cách chọn là eval trên **nhóm tra cứu đơn giản**: nếu Haiku giữ chuẩn thì Haiku làm mặc định (như tình huống 1). Đáp án cũng không nói điều kiện để router có lời (mục 29 điểm 1: tiết kiệm phải lớn hơn chi phí phân loại cộng chi phí nhầm, cần tỉ lệ lưu lượng thật), và nếu gần như **mọi** yêu cầu đơn giản thì nên ghim một model, bỏ router.
5. **Hai kiểu phân loại nhầm của router** vẫn áp dụng (mục 29 điểm 2): yêu cầu phức tạp bị đưa sang model nhỏ cho chất lượng tụt âm thầm, yêu cầu đơn giản bị đưa sang Opus chỉ tốn tiền.
6. **Kết quả này xác nhận nửa "tiêu chí chọn model" của câu hỏi 6** (mục 30): tiêu chí là đủ. Nửa "đổi model làm vỡ gì ngoài chất lượng" vẫn do mục 30 trả lời, checkpoint không đụng tới.

## 30. Trả lời câu hỏi hướng dẫn 6

**Tiêu chí chọn model trong bài: đủ.** Chọn **model rẻ nhất đạt chuẩn chất lượng của tác vụ, đo bằng eval**, dựa trên ba trục chất lượng, độ trễ, chi phí (kèm chi phí của sai lầm), qua quy trình:

1. Bắt đầu từ Sonnet (mặc định cân bằng).
2. Nâng bậc khi eval cho thấy trượt ca khó và lỗi đắt; hạ bậc khi eval cho thấy giữ chuẩn trên phần lớn lưu lượng.
3. Nếu lưu lượng không đồng đều thì dùng model mặc định cộng ghi đè theo tín hiệu rẻ; đồng đều thì ghim một model.
4. Mọi thay đổi được duyệt theo điểm đo trên ca của mình, không theo cảm tính.

**"Đổi model có thể làm vỡ gì ngoài chất lượng": đủ một nửa, bài không trả lời.** Bài chỉ nói đổi model vì chất lượng, độ trễ và chi phí, và thậm chí nói đổi model "không cần viết lại ứng dụng". Phần này đi từ bằng chứng thật ở W4D2 mục 7.

**Bằng chứng đã thử thật (2026-11-24, `probe_model_params.py` trên `claude-haiku-5-5`):**

| Thử | Kết quả |
|---|---|
| `temperature=1.0` và `0.5` | **400** `temperature: Extra inputs are not permitted` (kể cả giá trị mặc định) |
| Prefill `"```json"` kèm stop sequence | **400** `This model does not support assistant message prefill...` |

Cả hai đều là **tham số hoặc tính năng của API bị từ chối**, không phải chất lượng. Hàm `chat` của khóa học luôn gửi `temperature` nên hỏng ngay ở lần gọi đầu. Theo Failure Handling, đây là **lỗi terminal** (400): thử lại nguyên văn không giúp gì, phải sửa chính request.

**Nên kiểm khi đổi model [ngoài tài liệu]** (hai dòng đầu đã thử thật, các dòng sau là danh sách ứng viên):

| Có thể vỡ | Mức test bắt đầu tiên | Trạng thái |
|---|---|---|
| Tham số bị từ chối (`temperature`) | Functional (lần gọi thật đầu tiên) | **Đã thử thật** |
| Tính năng bị gỡ (prefill) | Functional | **Đã thử thật** |
| Khuôn output đổi (lời dẫn, tên trường, độ dài) làm parser vỡ | Integration | Suy luận |
| Chi phí và độ trễ đổi (token nhiều hơn, giá khác) so với ngân sách | Đo theo ngân sách (design doc) | Suy luận; bench cho thấy chi phí mỗi request gấp khoảng 22 lần (Sonnet) đến 94 lần (Fable) so với Haiku |
| Hành vi tool-use đổi: số vòng, đường đi, tần suất gọi tool (Lab 2 kịch bản A đã dao động 3 đến 4 vòng) | E2E, trace | Suy luận |
| Giới hạn context, output tối đa, và `stop_reason` khác | Functional | Suy luận |
| Hạn mức tốc độ (rate limit) khác nhau giữa các model | Test tải, theo dõi 429 | **Chưa kiểm** |
| Tên model bị ngừng hỗ trợ: 404, terminal | Functional | Suy luận, theo bảng mã lỗi của Failure Handling |

**Nhận định về câu "đổi model không cần viết lại ứng dụng":** đúng cho **văn bản prompt** và phần lớn code gọi API, nhưng **không bảo đảm** hành vi (cần eval) và **không bảo đảm** API chấp nhận cùng tham số (cần functional test). Câu đó chỉ đúng nếu ứng dụng không gắn cứng tham số riêng của một model.

**Hệ quả thiết kế [ngoài tài liệu]:**
1. **Gom tham số riêng của model vào một hồ sơ cấu hình theo model** (có hỗ trợ `temperature` không, prefill không, structured output không...) thay vì gắn cứng trong `chat()`. Điều W4D2 mục 13 điểm 6 đã gợi ý ("chỉ thêm `temperature` khi khác `None`").
2. **Giữ một bộ smoke test tương thích theo model**, chạy mỗi khi đổi model hoặc nâng phiên bản. `probe_model_params.py` chính là bản đầu tiên của nó; chạy trước eval, như test là cổng chặn của eval (Phần A mục 11.5).
3. **Không đổi model chỉ bằng cách sửa một dòng ID** rồi ship: thứ tự đúng là smoke test, eval, so điểm từng ca, so chi phí và độ trễ với ngân sách, rồi mới duyệt.

## 31. "Watch Out" của bài Model Selection

**Bài này không có mục Watch Out riêng** (bạn xác nhận từ mục lục khóa, xem cuối mục). Bản dán đầu chỉ có ba khung (mục 29); bảng dưới là bẫy ngầm mình suy ra từ ba khung đó, đã đưa vào bảng mục 8:

| Bẫy | Cách tránh |
|---|---|
| **Mặc định dùng model mạnh nhất** ("lỗi phổ biến và đắt nhất") | Bắt đầu từ Sonnet, nâng bậc chỉ khi eval cho thấy cần |
| **Tiết kiệm vài đô bằng model thấp** trong khi lỗi gây thiệt hại lớn phía sau | Tính chi phí của sai lầm vào phép chọn (mục 27.1) |
| **Đổi model không có điểm đo** | Duyệt theo điểm eval trên các ca của mình |
| **Dựng router cho lưu lượng đồng đều** | Ghim một model, bỏ router |

**[ngoài tài liệu]** Bẫy mình thêm: tin rằng "đổi model chỉ là đổi một dòng ID" (mục 30), và dùng tập eval quá dễ nên điểm chạm trần, không đủ cơ sở nâng hay hạ bậc (mục 28.1).

**Model Selection không có Watch Out riêng.** Mục lục của khóa (module 04, "Failure Handling & Model Selection") đi theo thứ tự: Teaching, **Watch Out**, Checkpoint, Model Selection, Checkpoint. Chỉ có **một** Watch Out, nằm ngay sau Teaching của Failure Handling (mục 21.2); phần Model Selection chỉ có Teaching và Checkpoint (mục 29.1). Vì vậy không có mục 31.1 để chờ. Hai hệ quả: (1) bẫy ngầm trong bảng trên vẫn là **suy luận của mình**, không có case chính thức nào kiểm; (2) bẫy của Model Selection mà khóa nhấn thật sự nằm ở **Checkpoint** (mục 29.1), nơi mỗi đáp án sai là một bẫy: chọn theo một trục (nhanh, rẻ, mạnh) thay vì ràng buộc quyết định.

## 32. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Chọn model theo chất lượng, độ trễ, chi phí | NOTES.md mục 2 (`bench_models.py`, bảng giá và chi phí mỗi request) |
| "Bắt đầu từ Sonnet" so với "bắt đầu từ rẻ nhất" | NOTES.md mục 2 (mục 28.1) |
| Model bậc cao rẻ hơn nếu ít token | NOTES.md mục 2: "lượng token đầu ra mới là thứ quyết định chi phí thật" |
| Eval là cổng chặn của quyết định đổi model | W4D1 mục 8.4, W4D3 mục 3 và 12.1b (đổi model là đổi "thứ được test") |
| Đổi model làm vỡ tham số | W4D2 mục 7, `probe_model_params.py`; Phần A mục 7 (đổi model, functional bắt trước) |
| Router chọn model | Phần A mục 10 (router retrieval); LAB2 mục 7 (workflow hay agent) |
| Model dự phòng khi 529 | Phần B mục 18 (fallback) |
| Ngân sách quyết định chọn model | W4D3 mục 2.1, 2.2 (cost and latency budget) |

## 33. Câu hỏi ôn tập (Phần C)

1. Bài nói bắt đầu từ model nào? Khi nào nâng lên Opus, khi nào hạ xuống Haiku, và dụng cụ ra quyết định là gì?
2. Vì sao "chọn model mạnh nhất cho chắc" bị gọi là lỗi phổ biến và đắt nhất?
3. Một model bậc cao có thể rẻ hơn model bậc thấp trong trường hợp nào? Với bảng giá đã ghi, Opus cần dùng ít token đến mức nào so với Sonnet để rẻ hơn?
4. Haiku rẻ hơn Sonnet 22 lần mỗi lần gọi nhưng vẫn có thể đắt hơn tổng thể. Giải thích bằng chi phí của sai lầm.
5. Khi nào dùng router chọn model, khi nào ghim một model? Router phải đáp ứng điều kiện gì để có lời?
6. Hai kiểu phân loại nhầm của router (khó sang nhỏ, dễ sang lớn) khác nhau thế nào về hậu quả?
7. Bài nói đổi model không cần viết lại ứng dụng. Kết quả thử trên `claude-haiku-5-5` cho thấy điều gì mâu thuẫn? Đó là lỗi retriable hay terminal, và mức test nào bắt trước?
8. Thứ tự đúng để duyệt một lần đổi model là gì? Vì sao smoke test chạy trước eval?
9. Quy tắc "bắt đầu từ model rẻ nhất" trong NOTES.md và quy tắc của bài khác nhau ở đâu, giống nhau ở đâu?

## 34. Còn lại và việc cần kiểm tra (Phần C)

- **Chưa có thí nghiệm mới** cho bài này. Hai dữ kiện thật dùng ở mục 30 đến từ W4D2 mục 7 (chỉ trên `claude-haiku-5-5`); chưa thử `temperature` và prefill trên Sonnet, Opus, Fable.
- **Chưa kiểm:** hạn mức tốc độ theo model; các giá trị `stop_reason` khác nhau giữa model; đội hình model hiện hành và giá (bài nhắc xác nhận tại platform.claude.com).
- **Bảng giá và ID trong NOTES.md mục 2** (nhất là `claude-fable-5-1`) cần đối chiếu và cập nhật; mục 27.1 dùng bảng giá đó.
- **Chi phí lỗi** ở mục 27.1 là số minh hoạ; cần ước lượng thật từ eval (P(sai)) và từ nghiệp vụ (chi phí một lần sai).
- **Quy tắc NOTES.md mục 2** nên sửa câu chữ cho khớp bài (mục 28.1); chưa sửa.
- **Nếu làm Lab 4:** thêm hồ sơ cấu hình theo model cho `chat()`, một smoke test tương thích chạy trước eval, và một bộ ca khó hơn để bench có thể phân biệt các bậc model.
- Chủ đề **Cost & Orchestration**: xem Phần D.

---

# Phần D. Cost & Orchestration

Nguồn: bài "Cost & Orchestration" (giữ chi phí, độ trễ và độ tin cậy trong ngân sách khi có nhiều agent): quan sát ba chỉ số mỗi lần gọi, các đòn bẩy ngân sách, prompt caching, Batches API, multi-agent, sàn độ tin cậy, bảng tham chiếu. **[SDK]** là mình đã đọc mã SDK `anthropic` 2.6.0 trong máy (chưa chạy); **[ngoài tài liệu]** là suy luận hoặc tính toán của mình. Giá lấy từ NOTES.md mục 2, chưa đối chiếu trang giá chính thức.

## 35. Bài này đứng ở đâu

Phần B giữ hệ thống **đáng tin** (retry, fallback). Bài này nói thêm: hệ thống còn phải **chịu nổi hóa đơn thật** và đủ nhanh. Bài làm bốn việc: (1) **đo** ba chỉ số mỗi lần gọi, (2) liệt kê các **đòn bẩy** ngân sách (có prompt caching và Batches), (3) xử lý mẫu **nhân chi phí nhanh nhất**, là chia việc cho nhiều agent, (4) đặt **sàn độ tin cậy** rồi tối ưu chi phí bên trên sàn.

**Lưu ý về bản dán:** bài có năm tab đòn bẩy (Model selection, Prompt & context size, Number of tool calls, Streamed vs. batched, Streaming with tool use) nhưng bản dán chỉ có văn bản của tab đầu (Model selection) và tab cuối (code streaming với tool use). Hai tab "Prompt & context size" và "Number of tool calls" **không có nội dung** trong bản dán; ý của chúng mình chỉ nối được qua Lab 2 (mục 37).

## 36. Quan sát: ba chỉ số cho mỗi lần gọi **[docs]**

Chi phí và độ trễ **vô hình lúc phát triển nhưng quyết định ở production**: lúc dev chạy vài lần gọi nên không thấy hóa đơn; lên production cùng những lần gọi đó chạy theo khối lượng. Quan sát cho một hệ thống Claude là đo **ba chỉ số mỗi lần gọi**: **token** (vào và ra), **độ trễ**, **tỉ lệ lỗi**. Có đủ ba, ta thấy bước nào đắt hoặc chậm thay vì đoán từ hóa đơn cuối tháng. **Gắn đo từ đầu**: nếu để sau thì "hóa đơn đến trước lời giải thích".

```python
def instrumented_call(make_call, step_name):
    start = time.perf_counter()
    resp = make_call()          # ném lỗi nếu API lỗi
    latency_ms = (time.perf_counter() - start) * 1000
    log_metric(step=step_name,
               input_tokens=resp.usage.input_tokens,
               output_tokens=resp.usage.output_tokens,
               latency_ms=latency_ms)
    return resp
```

Giá trị: đổi câu hỏi từ "vì sao hóa đơn cao" thành "bước nào, ở loại yêu cầu nào, chịu trách nhiệm". Một luồng trông đắt đồng đều thường có **một bước chiếm 90% chi tiêu**, và đó là chỗ mọi đồng tối ưu nên dồn vào. Độ trễ cũng vậy: bước chậm hiếm khi là bước ta đoán; trace cộng thời gian từng lần gọi cho biết bước nào (Phần A mục 5).

**Đọc phê phán wrapper [ngoài tài liệu]:**
1. **Chỉ ghi khi thành công.** `make_call()` ném lỗi thì dòng ghi không bao giờ chạy, nên chỉ số thứ ba (**tỉ lệ lỗi**) không tính được từ wrapper này. Cần `try/except` ghi lại lỗi (mã status, retriable hay terminal, Phần B) rồi ném lại.
2. **Thiếu token cache.** `usage` của SDK 2.6.0 có `cache_creation_input_tokens` và `cache_read_input_tokens` **[SDK]**; `input_tokens` chỉ là phần **không cache** (W3D2 mục 1.3). Khi bật caching, chỉ log hai trường kia mới thấy chi phí thật và tỉ lệ trúng cache. Lab 2 cũng cộng `input_tokens + output_tokens` (`lab2_agent.py` dòng 94), nên sẽ **đếm thiếu** nếu bật cache.
3. **Thiếu khóa để gộp:** `run_id`, `agent_id`, model, phiên bản prompt. Không có thì không gộp được theo yêu cầu, không nối được với trace (Phần A mục 5.2) hay bản ghi eval.
4. Retry bên trong SDK vô hình với wrapper (Phần B mục 20 điểm 9): một "lần gọi" có thể là nhiều request HTTP.
5. Streaming: wrapper đo cả lần gọi, không tách thời gian đến token đầu tiên với tổng thời gian.

## 37. Các đòn bẩy ngân sách **[docs]**

Mọi vấn đề chi phí hay độ trễ gần như luôn quy về một vài thành phần đo được; **xác định đòn bẩy trước khi chỉnh** để tối ưu không thành đoán mò.

| Đòn bẩy | Ý của bài | Nối với notes cũ |
|---|---|---|
| **Model selection** | Dùng model nhỏ, nhanh hơn để giảm chi phí và độ trễ; dành model mạnh nhất cho bước cần nó, việc đơn giản đẩy sang chỗ khác | Phần C |
| **Prompt & context size** | (Bản dán không có nội dung.) | **[ngoài tài liệu]** Lab 2 mục 6: `input_tokens` mỗi vòng gồm cả lịch sử gửi lại nên mỗi vòng đắt hơn vòng trước (894, 2049, 3282 ở kịch bản A) |
| **Number of tool calls** | (Bản dán không có nội dung.) | **[ngoài tài liệu]** Lab 2: cùng yêu cầu chạy 3 vòng (3282 token) hoặc 4 vòng (4662 token); kịch bản C thử lại thừa tốn khoảng 1100 token |
| **Streamed vs. batched** | Streaming làm một phản hồi **cảm giác nhanh** cho người dùng đang chờ; batch làm **hóa đơn thấp** cho việc không ai chờ. Không tranh nhau trên cùng một yêu cầu (hoặc có người chờ, hoặc không) | Mục 39 |
| **Streaming with tool use** | Tích lũy các delta theo `index` đến khi stream đóng rồi mới dựng tool call; **`tool_use` chưa an toàn để hành động cho đến khi stream đóng** và `input_json` đã đủ, vì hành động trên khối dở sẽ tạo input hỏng. Stream đứt giữa chừng là **lỗi tạm thời**: retry **cả request**, không đẩy phần dở xuống dưới | Phần B mục 15 (retriable) |

**Đọc code streaming [ngoài tài liệu]:**
- SDK 2.6.0 có sẵn `stream.get_final_message()` **[SDK]**, nên trong thực tế thường không cần tự tích lũy delta bằng tay như mã mẫu (chưa thử chạy).
- Tool không có tham số có thể cho `input_json` rỗng, khi đó `json.loads("")` lỗi. Cần xử lý trường hợp rỗng (chưa thử).
- Mã mẫu bỏ qua các loại delta khác (như thinking); đây là minh hoạ chứ không phải bản đầy đủ.

## 38. Prompt caching **[docs]**

Chi tiết cơ chế đã có và đã đối chiếu docs ở [NOTES_W3D2_Prompt_Caching_RAG.md](NOTES_W3D2_Prompt_Caching_RAG.md) mục 1; bài này nhắc lại ngắn và nhìn từ góc ngân sách.

| Ý của bài | Đối chiếu với W3D2 |
|---|---|
| Cache lưu công xử lý của một **tiền tố ổn định**; request sau đọc lại thay vì tính lại | Khớp mục 1.1 |
| Ghi cache **1,25×** (TTL 5 phút) hoặc **2×** (TTL 1 giờ); đọc cache **0,1×** giá input | Khớp, nhưng **con số đọc phụ thuộc model**: W3D2 mục 1.2 ghi 0,05× trên Opus 5.5 và Sonnet 5.5, 0,025× trên Fable 5.2. Bài dùng con số chung và nhắc "gắn với phiên bản" |
| "Kinh tế chỉ hợp khi **số lần đọc nhiều hơn số lần ghi**" | **Điều kiện này chặt hơn cần thiết.** Hòa vốn với 5 phút là **2 request** (1,25 + 0,1 = 1,35× so với 2× không cache), với 1 giờ là **ít nhất 3 request** (W3D2 mục 1.2) |
| Chế độ tự động (một cờ ở top-level) hoặc breakpoint tường minh | Khớp mục 1.2 |
| Ba điều kiện: tiền tố **giống hệt**, **tái xuất hiện sớm** (TTL 5 phút làm mới khi trúng), **đủ dài** (ngưỡng tối thiểu theo model) | Khớp mục 1.1, 1.2 |
| Đánh đổi: cache có thể giữ phiên bản **cũ** nếu tiền tố phản ánh dữ liệu đổi; system prompt cố định và schema tool ổn định thì an toàn | Mới ở góc độ "cửa sổ nhất quán"; W3D2 chưa nêu rõ |

**Nối với Phần C [docs qua W3D2 mục 1.3]:** cache **gắn theo model** và "đừng đổi tool hay model giữa hội thoại". Nghĩa là **routing giữa các model có thể làm mất cache** nếu cùng một tiền tố bị chuyển sang model khác; cần cân khoản tiết kiệm của router với khoản cache bị mất.

**Lỗi tốn kém nhất là im lặng:** request vẫn thành công, hóa đơn cao hơn. Đo `cache_read_input_tokens` (mục 36 điểm 2) để biết cache có trúng không.

## 39. Batches API: đổi độ trễ lấy hóa đơn thấp **[docs]**

- Việc không cần trả lời ngay (phân loại qua đêm, bổ sung dữ liệu lớn, báo cáo theo lịch) dùng **Message Batches API**: xử lý bất đồng bộ, **rẻ hơn mỗi request** so với gọi từng cái. Bài gọi đây là **đòn bẩy quyết định** cho việc không gấp và khối lượng lớn.
- Kết quả về trong một **cửa sổ hoàn thành bất đồng bộ**, không tức thì. **Sai** công cụ cho thứ có người đang chờ; **đúng** cho việc chạy theo lịch. Là bản ngược của streaming: streaming tối ưu cảm giác nhanh của một phản hồi, batch tối ưu hóa đơn.
- **Batch cộng gộp với caching** khi một việc không gấp dùng lại cùng ngữ cảnh qua nhiều request: giảm giá mỗi request, và cache giảm chi phí tiền tố lặp bên trong mỗi request.
- Mức giảm giá hiện hành **gắn với phiên bản**; bài **không nêu con số**, nhắc đối chiếu lúc build.

**Nối [ngoài tài liệu]:** NOTES.md mục 1 đã đo độ trễ batch (khoảng 90 đến 150 giây cho 1 và 20 request) và tính chi phí batch bằng mức giảm 50%, **số này vẫn chưa đối chiếu trang giá** (ISSUES "Còn mở"); bài này cũng không cung cấp. Batch hợp với **chạy eval hàng loạt** (W4D2 mục 13 điểm 3) và **lượt chấm judge theo lịch** (W4D3 mục 5). Việc cộng gộp với cache trong batch có hiệu quả thật hay không phụ thuộc vào việc cache có trúng giữa các request trong batch; **chưa kiểm**.

## 40. Multi-agent orchestration **[docs]**

**Mẫu orchestrator-worker:** agent chính (lead) chia việc thành nhiều việc con, giao cho nhiều subagent **chạy song song**, mỗi subagent có cửa sổ context riêng, rồi tổng hợp. Cấu trúc: lập kế hoạch, rẽ nhánh song song, tổng hợp.

```python
async def orchestrate(task):
    plan = await lead.plan(task)                  # lead chia việc
    results = await gather(*[worker.run(s) for s in plan.subtasks])   # song song
    return await lead.synthesize(results)         # lead tổng hợp
```

**Khi nào có ích:** việc lớn chia được thành các phần **độc lập**, ví dụ nghiên cứu trên nhiều nguồn riêng, vì các subagent khám phá cùng lúc thay vì lần lượt. Phép ví dụ của bài: năm nhà nghiên cứu xong một khảo sát rộng nhanh hơn một người, nhưng trả **năm lương**; chỉ "thuê cả nhóm" khi việc chia được và không ai phải chờ ai.

**Số liệu Anthropic (theo bài):**
- Hệ thống nghiên cứu nội bộ dùng Claude Opus 4 làm lead và Claude Sonnet 4 làm subagent cho kết quả **tốt hơn đáng kể** so với một agent Opus 4 trên eval nội bộ.
- Cái giá: khoảng **15 lần số token** của một lượt chat thông thường, vì mỗi subagent tiêu token của riêng nó trên context của riêng nó.
- **Kém hiệu quả với việc gắn chặt** như code (mỗi bước phụ thuộc bước trước, không khám phá song song được).
- Phân tích của Anthropic: **lượng token giải thích phần lớn phương sai hiệu năng**; kiến trúc này hiệu quả chủ yếu vì **mua thêm tính toán song song**.

**Quy tắc:** chỉ dùng khi việc **thật sự cần khám phá song song**. Một agent với ngữ cảnh tốt xử lý phần lớn việc với một phần nhỏ chi phí. Hệ số nhân còn **cộng dồn khi có gì trục trặc**: một subagent chạy mất kiểm soát hoặc một kết quả tool quá lớn có thể vượt xa mốc 15 lần.

**Ước lượng thô của bài:** một agent trả lời câu nghiên cứu trong khoảng 10 nghìn token; bản orchestrator-worker (một lead cộng bốn subagent, mỗi cái đọc một phần nguồn trong context riêng, rồi lead tổng hợp) dùng **15 lần**, tức cỡ 150 nghìn token. Nếu câu hỏi chỉ là **một lần tra cứu khoác áo nghiên cứu** thì trả hệ số nhân vô ích, vì bốn trong năm context làm việc mà tác vụ không cần.

**Chiều kiểm soát mà phép tính chi phí không nắm:** chia việc cho nhiều agent **nhân số chỗ có thể lỗi**. Mỗi subagent cần **cùng** cách xử lý retriable hay terminal, cùng backoff, cùng kỷ luật fallback (Phần B), áp **độc lập**. Một subagent chạm rate limit mà không có backoff có thể làm kẹt cả bước tổng hợp (lead chờ một kết quả không bao giờ về). Orchestration **không thay** công việc failure handling, nó **nhân** công việc đó.

**Chọn model:** dùng model **mạnh hơn làm lead**, model **rẻ hơn cho subagent**, để không trả giá cao nhất trên mọi context song song, giữ chất lượng điều phối ở chỗ cần.

### 40.1 Ví dụ tính chi phí **[ngoài tài liệu]**

Giả định: tỉ lệ 80% token vào và 20% token ra (con số minh hoạ); giá từ NOTES.md mục 2; "15 lần" nhân trên mốc 10 nghìn token của bài, chia đều cho 5 context (mỗi context 30 nghìn) để tính được.

Giá trung bình theo hỗn hợp (USD cho 1 triệu token): Sonnet 0,8 × 2 + 0,2 × 10 = **3,60**; Opus 0,8 × 4 + 0,2 × 20 = **7,20**; Haiku 0,8 × 0,1 + 0,2 × 0,5 = **0,18**.

| Kịch bản | Token | Chi phí mỗi yêu cầu |
|---|---|---|
| A. Một agent Sonnet | 10 nghìn | 10.000 × 3,60 / 1 triệu = **0,036 USD** |
| B. Orchestrator, mọi context đều Sonnet | 150 nghìn | **0,54 USD** (15 lần A) |
| C. Lead Opus (30 nghìn) + 4 subagent Haiku (120 nghìn) | 150 nghìn | 0,216 + 0,0216 = **0,24 USD** |
| D. Lead Sonnet (30 nghìn) + 4 subagent Haiku (120 nghìn) | 150 nghìn | 0,108 + 0,0216 = **0,13 USD** |

Đọc kết quả: cùng 150 nghìn token mà chi phí lệch hơn 4 lần (B so với D) chỉ do chọn model cho từng vai. Tiền dồn ở **lead**, vì lead đắt, nên "lead mạnh, subagent rẻ" cắt mạnh nhất. Nhưng subagent rẻ có thể **kéo chất lượng xuống** (token và chất lượng gắn nhau theo phân tích trên), nên mỗi cấu hình phải **qua eval** (Phần C mục 28).

### 40.2 Đọc phê phán **[ngoài tài liệu]**

1. **Gốc của "15 lần" không nhất quán.** Bài nói 15 lần **lượt chat thường**, nhưng ví dụ tính 10 nghìn rồi 150 nghìn lấy **một agent** làm gốc. Nếu mỗi context dùng 10 nghìn thì 5 context chỉ là 50 nghìn (5 lần), không phải 150 nghìn; muốn ra 15 lần thì mỗi context phải khoảng 30 nghìn. Mình nhớ bài viết gốc của Anthropic nói agent dùng khoảng 4 lần chat và multi-agent khoảng 15 lần chat, tức multi-agent so với một agent chỉ khoảng 3,75 lần; **cần đối chiếu nguồn gốc**, chưa kiểm. Hệ quả: đừng dùng "15 lần" cứng, mà **đo bằng trace của chính mình**.
2. **"Token giải thích phần lớn phương sai" nghĩa là một phần cải thiện chỉ do tiêu thêm token.** So sánh công bằng cần một agent đơn **ngang ngân sách token** (hoặc chạy nhiều lần chọn kết quả tốt nhất); bài không nói baseline có cân bằng token không.
3. **Số liệu thuộc về hệ thống nghiên cứu nội bộ với các model đời cũ (Opus 4, Sonnet 4);** đội hình hiện hành khác (Phần C mục 26). Không suy ra tự động cho tác vụ khác.
4. **Có hai tiêu chí khác nhau cho "subagent".** LAB2 mục 7 đưa lý do dùng subagent là **giữ context gọn** và **tách quyền** (subagent chỉ đọc, agent chính có HITL mới được xoá), không cần song song. Bài này chỉ nêu lý do **song song để tăng tính toán**. Hòa giải: tiêu chí cho "chạy song song" (việc độc lập, cần khám phá nhiều hướng) khác tiêu chí cho "có subagent" (cô lập context hoặc quyền).
5. **Ngân sách mềm nhân lên.** Lab 2 mục 6: ngân sách token chỉ chặn các lần gọi **tiếp theo** (đặt 1000, dừng ở 1753) và tính riêng cho từng `run_agent`. N subagent song song mỗi cái vượt thì tổng vượt N lần. Cần ngân sách **chia theo từng subagent**, bộ đếm chung, và trần vòng cứng.
6. **Rate limit chung.** N request đồng thời dùng chung hạn mức, nên 429 đến sớm hơn lưu lượng tuần tự. Cần giới hạn mức đồng thời (semaphore) và jitter (SDK đã có jitter, Phần B mục 16). Chưa kiểm hạn mức cụ thể.
7. **Subagent treo kéo cả tổng hợp.** Cần **deadline cho từng subagent** và **chính sách kết quả một phần** (tổng hợp với N trừ 1 kết quả, hay thất bại cả yêu cầu); đây là quyết định phải ghi ở mục failure handling của design doc.
8. **Xác suất thành công giảm theo số bước.** Minh hoạ (giả định độc lập): nếu cần cả lead lập kế hoạch, 4 subagent và bước tổng hợp đều thành công, mỗi bước 99%, thì cả yêu cầu khoảng 0,99^6 ≈ **94,1%**. Chỗ này nhân bề mặt lỗi bằng con số.
9. **Mã mẫu `gather(*[...])`:** với `asyncio.gather` mặc định, lỗi đầu tiên được ném ra bên chờ nhưng **các việc còn lại không bị hủy và vẫn chạy**. Cần `return_exceptions=True` hoặc `TaskGroup` để xử lý lỗi từng subagent có chủ đích.

## 41. Đo cost, latency, độ tin cậy khi có nhiều agent (câu 7, phần a)

**Bài cho:** ba chỉ số ở mỗi lần gọi (mục 36), và bảng so sánh một agent với orchestrator-worker:

| Chỉ số | Đo ở đâu | Một agent so với orchestrator-worker |
|---|---|---|
| **Chi phí token** | Mỗi lần gọi, gộp theo yêu cầu và theo luồng | Một agent trả token một lần mỗi bước; orchestrator **nhân** theo số subagent (khoảng 15 lần ở trường hợp Anthropic báo cáo), nhân cả token vào lẫn ra vì mỗi subagent nhận context riêng và sinh output riêng |
| **Độ trễ** | Mỗi lần gọi, kèm trace chỉ ra bước chậm nhất | Subagent song song **giảm thời gian thực** ở việc độc lập, nhưng **thêm độ trễ điều phối** cho lập kế hoạch và tổng hợp |
| **Tỉ lệ lỗi** | Mỗi lần gọi và mỗi dependency | Nhiều agent là nhiều điểm lỗi; mỗi subagent cần cùng xử lý retry và fallback như một agent |

**Bài chưa nói: cách gộp theo từng agent và theo yêu cầu.** Đề xuất của mình **[ngoài tài liệu]**:

- Mỗi lần gọi ghi một bản ghi: `run_id` (cả yêu cầu), `agent_id`, `parent_id`, bước, model, `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, `latency_ms`, trạng thái (ok, retriable, terminal), số lần retry. Cùng `run_id` với trace và bản ghi eval (Phần A mục 5.2).
- **Chi phí yêu cầu = tổng** của lead lập kế hoạch + mọi subagent + tổng hợp (cộng dồn).
- **Độ trễ yêu cầu = đường găng** = lập kế hoạch + **max** thời gian các subagent + tổng hợp (không phải tổng; tổng thời gian subagent chỉ là "chi phí thời gian").
- **Độ tin cậy yêu cầu** = tích xác suất thành công của các bước bắt buộc (mục 40.2 điểm 8), hoặc cao hơn nếu có chính sách chấp nhận kết quả một phần.
- Tách theo **vai** (lead, subagent, tổng hợp) để biết 90% chi tiêu nằm ở đâu.

## 42. Khi nào chạy song song (câu 7, phần b)

**[docs]** Chỉ khi nhiệm vụ **thật sự cần khám phá song song**: chia được thành các phần **độc lập** (không chờ nhau), như nghiên cứu trên nhiều nguồn riêng. **Không** cho việc gắn chặt như code (mỗi bước phụ thuộc bước trước), và **không** cho một tra cứu đơn lẻ. Mặc định: **một agent với ngữ cảnh tốt**, một phần nhỏ chi phí.

Danh sách kiểm trước khi dùng (kết hợp bài và notes cũ) **[ngoài tài liệu]**:

1. Việc chia được thành phần độc lập, và khám phá song song thật sự giúp?
2. Giá trị của đáp án (hoặc thời gian tiết kiệm) bù được chi phí nhân (khoảng 15 lần theo báo cáo, hoặc số đo của riêng bạn)?
3. Eval cho thấy orchestrator **tốt hơn một agent có ngân sách token ngang** (mục 40.2 điểm 2)?
4. Đã có xử lý lỗi, deadline và trần token **cho từng subagent**?
5. Nằm trong trần chi phí, trần độ trễ và sàn độ tin cậy của design doc (mục 43)?

Thang chọn của LAB2 mục 7: một lần gọi, workflow, agent, nhiều agent, **chỉ nâng khi cần**.

## 43. Đối chiếu với trần ngân sách của design doc (câu 7, phần c)

**Bài không làm phần này.** Phần dưới là của mình.

**W4D3 mục 2.2:** đặt ngân sách cứng về chi phí và độ trễ **trước** khi chọn kiến trúc, để kiểm được kiến trúc có vừa **trước khi viết code**. Ví dụ ở đó: ngân sách 2 cent mỗi yêu cầu mà thiết kế cần ba lần gọi model lớn thì loại ngay trên giấy.

**W4D3 mục 2.1, quyết định số 3** đã gồm "sàn độ tin cậy không được đánh đổi". Bài này gọi nó là **reliability floor** và nói rõ cách dùng: **đặt sàn trước, rồi tối ưu chi phí bên trên**. Vậy bài này là bản mở rộng của quyết định số 3.

**Kiểm multi-agent trên giấy (bằng bảng mục 40.1):**

| Điều kiện trong design doc | Kiểm |
|---|---|
| **Trần chi phí mỗi yêu cầu** | Kịch bản A (một agent Sonnet) đã là khoảng 3,6 cent theo giả định ở mục 40.1, nên đã **vượt** ngân sách ví dụ 2 cent; kịch bản B là 54 cent, loại ngay trên giấy; kịch bản D khoảng 13 cent chỉ vừa nếu ngân sách cho phép |
| **Trần độ trễ (p95)** | Tính theo **đường găng** (mục 41), không cộng thời gian các subagent |
| **Sàn độ tin cậy** | Tích xác suất các bước bắt buộc (mục 40.2 điểm 8) |
| **Trần ngân sách tháng** | Chi phí yêu cầu × khối lượng; nhân khối lượng thật bằng load test (Phần C mục 28.2) |

**Hai điều cần nối kỹ:**

1. **Ví dụ của bài (hoàn thành trong 4 giây, retry tối đa 3 lần) mâu thuẫn ngầm.** Backoff mặc định của SDK với 3 retry đã chờ khoảng 0,5 + 1 + 2 = **3,5 giây** (Phần B mục 20 điểm 6), chưa tính thời gian của chính các lần gọi, nên khó vừa 4 giây. Muốn vừa thì retry chỉ áp cho dependency nhanh, hoặc đặt **deadline tổng** làm trần cứng (cắt cả `retry-after`, Phần B mục 20 điểm 7). Kết luận: **ngân sách retry phải nằm bên trong trần độ trễ**: số lần thử × (thời gian một lần + chờ) ≤ trần.
2. **"Sàn độ tin cậy" của bài thực chất là một bộ điều kiện**, và cổng chặn kiểm cả ba: **điểm eval ≥ mốc đã ghim** (chất lượng), **độ trễ p95 ≤ trần**, **tỉ lệ lỗi ≤ ngưỡng**. Bài nói "điểm eval làm sàn kiểm được"; điểm eval chỉ đo **chất lượng**, không đo độ trễ hay tỉ lệ lỗi, nên cần thêm hai chỉ số kia từ mục 36. Mọi thay đổi tiết kiệm chi phí (đổi model, bớt retry, thêm subagent rẻ) phải qua cổng này trước khi ship; khớp cách duyệt đổi model ở Phần C mục 28 và vai trò cổng chặn của test ở Phần A mục 11.5.

**Thứ tự quan trọng:** chi phí "ồn" hơn độ tin cậy (hóa đơn hiện hàng ngày, lỗi hiếm dễ bị coi là nhiễu), nên nếu tối ưu chi phí trước thì áp lực lớn hơn thắng và ta chỉ phát hiện sàn sau khi đã vượt. Đặt sàn trước thì độ tin cậy là ràng buộc cố định còn chi phí là thứ tối ưu bên dưới.

## 44. "Watch Out" của bài Cost & Orchestration

**Mục Watch Out chính thức của bài này là case ở mục 44.1** (gửi bù sau). Bản dán đầu chỉ có ba khung *Handles well* (chi tiêu và độ trễ nhìn thấy theo từng lần gọi, nên vấn đề chi phí quy về một đòn bẩy có tên), *Adds cost or complexity* (subagent song song nhân chi phí token, khoảng 15 lần ở trường hợp báo cáo, **trước khi** cải thiện được câu trả lời nào), *Use a different approach* (việc gắn chặt như code: một agent ngữ cảnh tốt thắng rẽ nhánh). Bẫy ngầm:

| Bẫy | Cách tránh |
|---|---|
| **Quan sát đến sau:** hóa đơn đến trước lời giải thích | Instrument mọi lần gọi từ đầu (ba chỉ số, mục 36) |
| **Hành động trên `tool_use` khi stream chưa đóng:** input hỏng | Chờ stream đóng; stream đứt thì retry cả request |
| **Cache vô hiệu:** đổi một từ trước breakpoint, hết TTL, tiền tố quá ngắn, dữ liệu cũ | Tiền tố ổn định đặt trước; đo `cache_read_input_tokens`; chỉ cache thứ không đổi |
| **Dùng batch cho yêu cầu người dùng đang chờ** | Batch chỉ cho việc theo lịch, không gấp |
| **Multi-agent cho việc gắn chặt hoặc một tra cứu đơn:** trả hệ số nhân vô ích | Mặc định một agent; chỉ dùng khi cần khám phá song song |
| **Subagent chạy mất kiểm soát hoặc kết quả tool quá lớn:** vượt xa mốc 15 lần | Trần token và vòng cho từng subagent, giới hạn kích thước kết quả tool |
| **Không xử lý lỗi từng subagent:** một cái kẹt kéo cả tổng hợp | Retriable hay terminal, backoff, fallback, deadline cho từng subagent |
| **Cắt chi phí xuống dưới sàn độ tin cậy:** đổi chi phí thấy được lấy lỗi im lặng | Đặt sàn trước; mọi thay đổi tiết kiệm phải qua cổng eval và độ trễ |

### 44.1 Case của bài: fan-out song song làm hoá đơn gấp ba **[docs]**

**Đây là mục Watch Out của bài Cost & Orchestration** (case "Why this broke", gửi bù sau; bạn xác nhận là mục Watch Out của khóa).

**Chuyện gì xảy ra.** Một tác vụ chạy chậm, dev chia cho nhiều subagent song song vì nghĩ việc làm cùng lúc thì xong sớm hơn. Độ trễ giảm một chút. Rồi hoá đơn đến, **cao gấp vài lần** bản một agent, mà chất lượng câu trả lời gần như không đổi. Dev hỏi trong kênh nội bộ: "hoá đơn gấp ba, câu trả lời chỉ hơn chút, tôi đang trả tiền cho cái gì?". Senior trả lời: mỗi subagent tiêu token của riêng nó trên cửa sổ context của riêng nó; Anthropic báo cáo hệ thống nghiên cứu multi-agent của họ dùng khoảng **15 lần** token của một lượt chat thường vì đúng lý do đó; hệ số ấy xứng đáng khi việc chia được thành phần **độc lập** (nghiên cứu nhiều nguồn riêng); việc của dev thì mỗi bước phụ thuộc bước trước nên subagent chủ yếu **chờ nhau**, tức trả chi phí fan-out mà không được lợi song song. Dev chuyển về **một agent với context tốt**, giữ nguyên context: hoá đơn giảm, chất lượng giữ.

**Vì sao vỡ:** dùng fan-out song song cho tác vụ không chia thành phần độc lập, nên mỗi subagent chỉ nhân chi phí token mà không thêm giá trị song song. Bài nhấn: không phải orchestration xấu, mà hệ số nhân chỉ mua được thứ gì khi việc **thật sự** chạy song song được.

**Đối chiếu [ngoài tài liệu]:**
1. **Số liệu khớp với cách đọc ở mục 40.2 điểm 1.** "Gấp ba" so với một agent xấp xỉ 15 lần chat chia cho khoảng 4 lần chat của một agent (≈ 3,75). Còn so với một lượt chat thường thì mới là 15 lần. Đây là bằng chứng gián tiếp cho cách đọc đó, nhưng case chỉ nói "gấp vài lần", không phải số đo; nguồn gốc 15 và 4 vẫn **chưa đối chiếu** (mục 47).
2. **Nhận ra sớm "việc này không chia được".** Câu kiểm trước khi dựng: "mình có viết được danh sách các việc con **mà không cần biết kết quả của việc con trước** không?" Nếu không thì tuần tự (mục 42 danh sách điều 1). Sau khi chạy, kiểm bằng trace có thời gian từng bước (mục 5): nếu subagent B chỉ bắt đầu **sau khi** A xong thì đường găng (mục 41) là **tổng** chứ không phải max, tức song song chẳng giảm độ trễ. Phép đo gọn: so **tổng thời gian từng subagent** với **thời gian thực cả yêu cầu**; hai số gần bằng nhau nghĩa là thực chất đang chạy tuần tự.
3. **Vì sao độ trễ vẫn "giảm một chút"?** Case không nói. Đoán của mình: một phần nhỏ việc (ví dụ bước tìm kiếm) độc lập thật, phần còn lại tuần tự; phần tuần tự giới hạn mức giảm (kiểu định luật Amdahl). Phần độc lập nhỏ không bù nổi hệ số nhân chi phí. Chưa kiểm.
4. **Đây là bẫy 1 của mục 44 thành ví dụ:** "hóa đơn đến trước lời giải thích". Nếu đã log từng lần gọi theo `agent_id` ngay từ đầu (mục 41), chi phí nhân lên và subagent đứng chờ sẽ thấy ngay ở lần chạy đầu, không cần chờ hoá đơn.
5. **Cổng eval của mục 42 điều 3** ("orchestrator tốt hơn một agent có ngân sách token ngang?") bắt được case này: chất lượng "barely better" nghĩa là rớt cổng và hệ số nhân không được biện minh.
6. **Chi tiết đáng nhớ: "giữ nguyên context".** Bản sửa không bỏ thông tin nào, chỉ bỏ **sự nhân bản context**. Nếu mỗi subagent nạp lại cùng một phần context chung thì trả nhiều lần. Prompt caching giảm được phần này (mục 38), nhưng cache gắn theo model nên lead và subagent khác model thì không dùng chung (mục 45).

### 44.2 Checkpoint của bài Cost & Orchestration **[docs]** và đối chiếu **[ngoài tài liệu]**

**Đề.** Bốn cấu hình, mỗi cấu hình ghi kiểu agent và đòn bẩy chi phí chính; ghép với bốn tình huống. Kết quả của mình: **đúng cả bốn**.

| Cấu hình | Kiểu agent, đòn bẩy |
|---|---|
| A `orchestrator_worker(lead=LARGE, workers=SMALL, n=5)` | Rẽ nhánh song song |
| B `single_agent(model=SMALL, batch=True, cache=True)` | Message Batches API (khoảng 50% giảm chi phí) cộng prompt caching |
| C `single_agent(model=SMALL, retrieval="fetch_once")` | Chọn model |
| D `single_agent(model=SMALL, stream=True)` | Streaming |

| Tình huống | Đáp án | Vì sao |
|---|---|---|
| 1. Tra cứu một sự kiện trong kho tham chiếu ổn định | **C** | Fetch-once với model nhỏ nhất dùng được. Chọn A là trả hệ số nhân fan-out cho một tra cứu đơn (mục 40, 42) |
| 2. Câu hỏi nghiên cứu rộng, chia được thành phần độc lập, khám phá cùng lúc | **A** | Là việc duy nhất chia độc lập, nên hệ số nhân mua được khám phá song song |
| 3. Yêu cầu người dùng đang chờ, câu trả lời phải có cảm giác tức thì | **D** | Streaming cho cảm giác nhanh |
| 4. Việc nhạy chi phí, không gấp, theo lô | **B** | Batch cộng cache. Chọn đường đồng bộ là bỏ mức giảm khoảng 50% của Batches |

**Đối chiếu [ngoài tài liệu]:**
1. **Đây là bảng đòn bẩy (mục 37) và danh sách "khi nào song song" (mục 42) thành bài tập:** mỗi tình huống ứng với một đòn bẩy có tên; "xác định đòn bẩy trước khi chỉnh". Cả bốn đáp án khớp mục 36 đến 42.
2. **Con số "khoảng 50%" là dữ kiện mới.** Mục 39 ghi bài **không nêu số** và NOTES.md mới chỉ là số tính. Checkpoint ghi "~50% cost reduction" cho Batches: có thêm một nguồn từ khóa, nhưng ở dạng xấp xỉ, **chưa đối chiếu trang giá chính thức** (mục 47).
3. **Streaming không giảm hoá đơn.** Cùng số token; nó đổi **cảm giác độ trễ** (thời gian tới token đầu), không đổi tổng thời gian hay chi phí. Nếu có tool use thì vẫn phải **chờ stream đóng** trước khi hành động (mục 37).
4. **Bài tập đơn giản hoá thành một-một, thực tế đòn bẩy cộng gộp.** B đã cộng hai đòn bẩy (batch và cache); C có thể thêm cache; A có thể stream câu trả lời cuối. "Đòn bẩy chính" không có nghĩa là duy nhất.
5. **Cấu hình ghi `model=SMALL` cho cả bốn, `LARGE` chỉ ở lead của A.** Là chỗ giữ chỗ để khớp tình huống, không thay quy trình mục 28 (bắt đầu từ mặc định rồi nâng hạ theo eval). Cấu hình A cũng chính là kịch bản C và D ở mục 40.1 (lead mạnh, subagent rẻ), vẫn phải qua eval.
6. **Đáp án A của tình huống 2 phụ thuộc vào câu "chia được thành phần độc lập" mà đề đã cho sẵn.** Ngoài đời điều kiện đó phải tự kiểm trước (mục 44.1 điểm 2); đó đúng là chỗ case Watch Out ở trên vỡ.

## 45. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Đo ba chỉ số mỗi lần gọi | Phần A mục 5 (trace, thời gian từng bước); Lab 2 trace chỉ có token; NOTES.md mục 1 (đo độ trễ realtime) |
| Chọn model theo bước, lead mạnh và subagent rẻ | Phần C mục 26 đến 29 (chọn model, routing); NOTES.md mục 2 (bảng chi phí mỗi request) |
| Prompt caching | W3D2 mục 1 (đã đối chiếu docs); cache gắn theo model nên routing có thể làm mất cache |
| Batches API | NOTES.md mục 1 (đo 90 đến 150 giây, mức giảm 50% còn là số tính); W4D2 mục 13 (eval hàng loạt); W4D3 mục 5 (judge theo lịch) |
| Streaming, stream đứt là lỗi tạm thời | Phần B mục 15 (retriable); `stop_reason` |
| Multi-agent, subagent | LAB2 mục 7 (workflow, agent, subagent); LAB2 mục 6 (ngân sách token mềm) |
| Nhân bề mặt lỗi | Phần B mục 20 (retry nhiều tầng), mục 40.2 điểm 8 |
| Sàn độ tin cậy, trần ngân sách | W4D3 mục 2.1, 2.2; Phần C mục 28; Phần A mục 11.5 |
| Load test để xác nhận ngân sách | Phần C mục 28.2 |

## 46. Câu hỏi ôn tập (Phần D)

1. Ba chỉ số cần đo mỗi lần gọi là gì? Vì sao nên gắn đo từ đầu? Wrapper mẫu của bài thiếu những gì để tính được chỉ số thứ ba và để thấy hiệu quả của caching?
2. Một luồng "đắt đồng đều" trên hóa đơn: log theo từng lần gọi giúp trả lời câu hỏi gì mà hóa đơn tổng không trả lời được?
3. Vì sao `tool_use` không an toàn để hành động cho đến khi stream đóng? Stream đứt giữa chừng thì xử lý thế nào, và đó là lỗi retriable hay terminal?
4. Prompt caching có ba điều kiện để có lợi là gì? Với hệ số 1,25 / 2 / 0,1, 5 phút hòa vốn ở mấy request và 1 giờ ở mấy request?
5. Vì sao routing giữa các model có thể làm mất lợi ích của prompt caching?
6. Khi nào dùng Batches API, khi nào dùng streaming? Vì sao hai thứ không bao giờ tranh nhau trên cùng một yêu cầu? Hai thứ cộng gộp với caching khi nào?
7. Orchestrator-worker nhân token khoảng bao nhiêu lần theo báo cáo? Hệ số đó dùng được cho việc nào, và không dùng cho việc nào? Vì sao ví dụ tính 10 nghìn lên 150 nghìn token chưa nhất quán với con số 15 lần?
8. Tính chi phí một yêu cầu cho (A) một agent Sonnet 10 nghìn token và (C) lead Opus cộng 4 subagent Haiku 150 nghìn token theo giả định mục 40.1. Vì sao "lead mạnh, subagent rẻ" cắt mạnh nhất, và rủi ro là gì?
9. Đo độ trễ và chi phí cả yêu cầu của orchestrator thế nào: cộng hay lấy max, và khi nào dùng cái nào?
10. Sàn độ tin cậy là gì, vì sao đặt trước khi tối ưu chi phí, và vì sao ví dụ "4 giây, 3 retry" của bài khó vừa với backoff mặc định của SDK?
11. Vì sao một subagent chạm rate limit không có backoff có thể làm kẹt cả bước tổng hợp? Cần thêm quy tắc nào cho từng subagent?

## 47. Còn lại và việc cần kiểm tra (Phần D, cũng là phần cuối của cả ngày)

- **Chưa chạy thật cho cả Phần D.** Các con số ở mục 40.1 (hỗn hợp 80/20, chia đều 30 nghìn token mỗi context) là giả định minh hoạ; 0,99^6 cũng là giả định độc lập. Hai chỗ đã đọc mã SDK: có `get_final_message()` cho streaming và `usage` có hai trường cache; chưa thử chạy.
- **Chưa đối chiếu:** nguồn gốc con số "15 lần" và mối quan hệ với "4 lần chat" (mục 40.2 điểm 1); mức giảm giá của Batches API (checkpoint ở mục 44.2 ghi "khoảng 50%" nhưng chưa đối chiếu trang giá; NOTES.md vẫn là số tính); hạn mức tốc độ khi chạy song song; hiệu quả cộng gộp batch với cache.
- **Bản dán thiếu** nội dung của hai tab "Prompt & context size" và "Number of tool calls"; nếu có bản đầy đủ thì bổ sung mục 37.
- **Nếu làm Lab 4:** viết một wrapper đo đầy đủ (ghi cả lỗi, hai trường cache, `run_id`, `agent_id`, model); thêm bản ghi thời gian vào `lab2_agent.py`; chạy `bench_models.py` có thêm đo `cache_read_input_tokens`; viết thử một orchestrator nhỏ (lead cộng 2 subagent) và so chi phí, độ trễ, điểm eval với một agent.
- **Ba việc còn treo từ các phần trước:** lưu kết quả eval để so phiên bản (W4D2 mục 12; Phần A mục 5.2), tái hiện 429 và 529 bằng server giả (Phần B mục 20 điểm 8), sửa câu chữ quy tắc "rẻ nhất" trong NOTES.md mục 2 (Phần C mục 28.1).
- **Tổng kết ngày:** mục Watch Out của khóa là case "Why this broke" cuối mỗi bài (bạn đã xác nhận). Đã có cho **Testing** (mục 8.1), **Failure Handling** (mục 21.2) và **Cost & Orchestration** (mục 44.1), nên câu 4 của bảng hướng dẫn trả lời được cho mọi bài **có** Watch Out. **Model Selection không có Watch Out riêng** (cấu trúc khóa: một Watch Out cho cả module Failure Handling & Model Selection, mục 31), nên không còn gì chờ gửi bù; thay vào đó có Checkpoint (mục 29.1). Các bảng bẫy ngầm ở mục 8, 21, 31, 44 vẫn giữ làm phần suy ra thêm. Case của Evals & Judges nằm ở W4D3 mục 8.1, của Security ở W4D6 mục 10.1.
