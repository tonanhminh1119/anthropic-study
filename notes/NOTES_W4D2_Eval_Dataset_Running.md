# Notes Week 4 Day 2: Eval dataset và chạy eval (bước 1–3 của workflow)

Nguồn: hai bài "Generating test datasets" và "Running the eval", cùng các slide đi kèm (Goal + Prompt v1, Sample Dataset, Feed Through Claude, Feed Through a Grader). **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung của mình, cần đối chiếu docs khi áp dụng.

Nối với notes cũ: khung 5 bước ở [NOTES_W4D1_Prompt_Evaluation.md](NOTES_W4D1_Prompt_Evaluation.md) mục 8; Realtime và Batch ở [NOTES.md](NOTES.md) mục 1; prefill + stop_sequences ở `archive/Building with the Claude API.txt` dòng 74; tham số sampling ở `archive/MSO Foundations.txt` dòng 44.

## 1. Câu hỏi hướng dẫn của module (mục tiêu chính)

Bốn bài của module, mỗi bài có một câu hỏi cần trả lời được sau khi học. Bảng cập nhật dần khi có tài liệu mới.

| Bài | Câu hỏi | Trạng thái |
|---|---|---|
| Generating test datasets | Dataset sinh bằng cách nào, prompt sinh dữ liệu yêu cầu gì, có kiểm lại tay không | Đã trả lời (mục 6) |
| Running the eval | Cách ghép template với từng input, cách lưu kết quả để so giữa các phiên bản | Ý 1 đủ, ý 2 chỉ đủ một nửa (mục 11, 12) |
| Model based grading | Prompt của grader (có barem không), đầu ra là điểm hay điểm kèm lý do, định dạng đầu ra | Đã trả lời đủ (mục 18) |
| Code based grading | Kiểm tra gì bằng code (định dạng, regex, JSON hợp lệ), và khi nào code không đủ | Đã trả lời, đủ ý chính, có hai chỗ tài liệu không nói rõ (mục 26) |

---

# Phần A. Generating test datasets (bước 1 và 2)

## 2. Bài toán xuyên suốt của module

Viết prompt giúp người dùng viết **Python, JSON config hoặc Regex** cho các tác vụ **riêng về AWS**.

| | Nội dung |
|---|---|
| Input | Người dùng mô tả một tác vụ cụ thể |
| Output | Python, JSON hoặc regex, **không kèm giải thích, header, footer** |

Prompt v1 (cố ý đơn giản, làm mốc để so):

```python
prompt = f"""
Please provide a solution to the following task:
{task}
"""
```

Đây là **bước 1 (Draft a Prompt)**: một template có đúng một chỗ trống `{task}`.

**[ngoài tài liệu]** v1 không hề nói "không giải thích", trong khi yêu cầu của bài toán là chỉ trả code. Nên dự đoán v1 sẽ hay thêm lời dẫn và giải thích, và đó là điểm các phiên bản sau sẽ sửa. Eval sinh ra để đo đúng việc này.

## 3. Eval dataset là gì

Một mảng JSON, mỗi object có thuộc tính `task` sẽ được **trộn vào** chỗ `{task}` của prompt:

```json
[
  { "task": "Create a Python function to extract the AWS account ID from an ARN" },
  { "task": "Write a JSON policy document that allows read-only access to a specific S3 bucket" }
]
```

Với mỗi cặp (prompt, input) ta chạy prompt rồi phân tích kết quả. Có thể tự viết tay hoặc nhờ Claude sinh; nếu dùng Claude thì **nên dùng Haiku** vì sinh dữ liệu test là việc đơn giản, không cần model đắt.

Ánh xạ .NET **[ngoài tài liệu]**: `dataset.json` là file test fixture; `generate_dataset()` giống script sinh seed data (kiểu Bogus/Faker nhưng do model viết).

## 4. Hàm hỗ trợ trong bài

```python
def add_user_message(messages, text): ...        # append {"role": "user", ...}
def add_assistant_message(messages, text): ...   # append {"role": "assistant", ...}

def chat(messages, system=None, temperature=1.0, stop_sequences=[]):
    params = {"model": model, "max_tokens": 1000,
              "messages": messages, "temperature": temperature}
    if system: params["system"] = system
    if stop_sequences: params["stop_sequences"] = stop_sequences
    response = client.messages.create(**params)
    return response.content[0].text
```

Ba hàm này chỉ gom việc lặp lại (dựng `messages`, gọi API, lấy text). `model` và `client` là biến toàn cục đã tạo ở trên.

## 5. Hàm `generate_dataset()` và chỗ bài thiếu

Prompt sinh dataset (cấu trúc đáng học):
- Nói rõ **mục đích**: dataset dùng để eval prompt sinh Python/JSON/Regex cho tác vụ AWS.
- Cho **định dạng output mẫu** (mảng object có `task`).
- Ràng buộc **độ khó**: tác vụ giải được bằng **một hàm Python, một object JSON hoặc một regex**, ít code.
- Nêu **số lượng**: `Please generate 3 objects.`

**Chỗ tài liệu bị thiếu:** bài viết "để parse JSON ta dùng prefilling và stop sequences", nhưng đoạn code kèm theo chỉ có phần đầu hàm (khai báo `prompt`) rồi nhảy sang `dataset = generate_dataset()`. Thân hàm không có trong bản văn bản. Bản tái dựng của mình theo đúng kỹ thuật archive đã ghi **[ngoài tài liệu]**:

```python
def generate_dataset():
    prompt = """..."""                      # prompt như trên
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")      # prefill: ép bắt đầu bằng khối json
    text = chat(messages, stop_sequences=["```"])   # dừng ngay khi model đóng khối
    return json.loads(text)                         # text đã sạch, parse được luôn
```

Vì sao hai thứ đi cùng nhau: prefill làm model **bắt đầu thẳng vào JSON** (không có lời dẫn), stop sequence làm nó **dừng trước dấu đóng ```** (không có lời kết). Phần còn lại chỉ là JSON, `json.loads` được ngay.

Lưu file để dùng lại:

```python
with open('dataset.json', 'w') as f:
    json.dump(dataset, f, indent=2)
```

**[ngoài tài liệu]** Lưu file còn có một lý do quan trọng: điều kiện so hai phiên bản hợp lệ là **cùng dataset** (W4D1 mục 8.4). Nếu mỗi lần chạy lại sinh dataset mới thì mỗi lần là một phép đo khác nhau, không so được. Sinh một lần, lưu, rồi dùng lại.

## 6. Trả lời câu hỏi hướng dẫn: Generating test datasets

**Dataset sinh bằng cách nào?**
- Một lần gọi Claude **Haiku** (model nhanh, rẻ) với một prompt sinh dữ liệu; tài liệu cũng nói có thể viết tay.
- Ép output thành JSON sạch bằng prefill + stop sequence (thân hàm bị thiếu trong tài liệu, mục 5 là bản tái dựng), rồi `json.loads` thành list.
- Lưu ra `dataset.json` để các lần eval sau dùng lại.

**Prompt sinh dữ liệu yêu cầu gì?**
1. Mục đích: dataset dùng để eval prompt sinh Python, JSON hoặc Regex cho tác vụ AWS.
2. Định dạng output: mảng object, mỗi object có `task` (kèm ví dụ).
3. Độ khó: giải được bằng **một** hàm Python, **một** object JSON hoặc **một** regex; ít code.
4. Số lượng: 3 object (demo).

Prompt **không** yêu cầu: đa dạng giữa ba loại, độ khó khác nhau, ca biên hoặc ca lạ. Vì vậy dataset sinh ra thiên về ca "sạch", giống ví dụ ARN và S3 trên slide.

**Kết luận sau khi đối chiếu tài liệu:**
- Dataset có thể **viết tay** hoặc **nhờ chính model sinh** (nên dùng Haiku). Tài liệu **không đặt quy định cụ thể** nào về cách làm; yêu cầu duy nhất là thành phẩm **đúng định dạng và cấu trúc**: mảng JSON, mỗi object có thuộc tính `task`.
- Các ràng buộc trong prompt sinh (một hàm, một object, một regex, ít code) chỉ là yêu cầu về nội dung mẫu cho bài này, không phải quy tắc chung của dataset.

**Có kiểm lại tay không?**
- **Tài liệu chưa có phần kiểm tra dataset.** Hiện chỉ có `print(dataset)` rồi **so bằng mắt** ("ra ba ca đúng ba loại"). Nếu các bài sau có thêm cách kiểm thì bổ sung vào đây.
- **[ngoài tài liệu]** Gợi ý của mình, chỉ dùng khi muốn kỹ hơn, không phải yêu cầu của khóa học. Nên kiểm trước khi dùng: (a) đọc hết hoặc một mẫu, xem tác vụ có hợp lý và đúng AWS không; (b) đếm cân bằng giữa Python/JSON/Regex; (c) loại ca trùng ý; (d) thêm tay vài ca khó mà Haiku không tự nghĩ ra. Lý do: Claude sinh dataset cho prompt cũng do Claude viết, dễ chung điểm mù (W4D1 mục 8.5).

## 7. Những chỗ cần cẩn thận khi dùng code của bài **[ngoài tài liệu]**

1. **`temperature` có thể gây lỗi 400.** Hàm `chat` luôn gửi `temperature`. Notes cũ (`MSO Foundations`, `Production-Grade Prompting`) ghi các model Claude mới nhất không nhận tham số sampling khác mặc định và trả 400. Với `claude-haiku-5-5` cần bỏ tham số này (chỉ thêm khi không phải `None`), hoặc kiểm tra bằng một lần gọi thật trước khi tin.
2. **Prefill có thể không còn được hỗ trợ** trên model mới. Đây là thứ mình **chưa kiểm chứng** với model đang dùng; cần thử một lần gọi hoặc đối chiếu docs. Nếu không dùng được thì thay bằng: yêu cầu trong prompt "chỉ trả JSON", dùng structured output, hoặc cắt khối ```json bằng code rồi `json.loads`.
3. **Prompt mẫu có dấu phẩy thừa** (`"task": "Description of task",` rồi `},`). Chỗ mẫu đó không phải JSON hợp lệ (trailing comma ở object). Model thường vẫn trả JSON đúng, nhưng ví dụ trong prompt nên chính xác.
4. **`json.loads` có thể fail.** Hai nguyên nhân thường gặp: model bỏ qua prefill/thêm chữ; output bị cắt do `max_tokens=1000` khi sinh nhiều object (kiểm tra `response.stop_reason == "max_tokens"`). Cần validate và thử lại, đúng tinh thần Lab 2.
5. **Sinh 3 object không đủ cho eval thật**, đây chỉ là demo (slide ghi "...many more..."). Dataset thật cần hàng chục tới hàng trăm ca.
6. **Không bảo đảm cân bằng giữa ba loại** (Python/JSON/Regex). Yêu cầu "3 objects" có thể cho 3 ca Python. Cách xử lý: sinh riêng theo từng loại, hoặc thêm trường `format` cho mỗi ca.
7. **Một lần gọi sinh nhiều ca dễ lặp ý.** Với dataset lớn: gọi nhiều lần, mỗi lần nhắm một nhóm dịch vụ AWS khác (S3, IAM, Lambda, EC2, CloudWatch...), rồi loại trùng.

## 8. Đọc phê phán dataset

- **Dataset này chỉ có input, không có đáp án đúng.** Mỗi ca chỉ có `task`. Nên bước chấm sau này phải dựa trên **tiêu chí** (chạy được không, đúng định dạng không, có kèm giải thích không), không so với đáp án mẫu. Đây là nơi hai loại grader ở W4D1 mục 8.2 phát huy:
  - Grader bằng code hợp với phần kiểm được bằng luật: Python `ast.parse` được không, JSON `json.loads` được không, regex `re.compile` được không, output có bị lời dẫn bao quanh không.
  - Grader bằng model hợp với phần mềm: lời giải có thật sự làm đúng tác vụ AWS không.
  - Thêm trường `format` ("python" / "json" / "regex") vào mỗi ca sẽ cho grader biết dùng bộ kiểm tra nào (gợi ý của mình ở bài này; bài Code based grading sau đó làm đúng như vậy, xem mục 24).
- **Claude sinh tập test cho prompt cũng do Claude viết**: nguy cơ chung điểm mù (W4D1 mục 8.5). Ví dụ Haiku có thể sinh toàn tác vụ "đẹp" như ví dụ ARN, thiếu ca khó (tác vụ mơ hồ, tác vụ không phải AWS, yêu cầu giải thích). Nên trộn thêm ca viết tay từ người hiểu AWS và ca từ câu hỏi thật.
- **Dùng Haiku để sinh là đúng hướng** và khớp quy tắc cost ở NOTES.md mục 2: việc đơn giản, bắt đầu từ model rẻ nhất.

---

# Phần B. Running the eval (bước 3)

## 9. Pipeline gồm ba hàm

Ba hàm, mỗi hàm một trách nhiệm, gọi lồng nhau:

```
run_eval(dataset)                  duyệt từng ca, gom kết quả vào list
  └─ run_test_case(test_case)      chạy một ca rồi chấm điểm
       └─ run_prompt(test_case)    ghép template + input, gọi Claude, trả output
```

| Hàm | Việc làm | Ánh xạ .NET **[ngoài tài liệu]** |
|---|---|---|
| `run_prompt` | Ghép prompt template với `test_case["task"]`, gọi `chat`, trả text | Hệ thống cần test (SUT) |
| `run_test_case` | Gọi `run_prompt`, chấm điểm, trả một bản ghi | Một test method (act + assert) |
| `run_eval` | Duyệt cả dataset, gọi `run_test_case`, gom vào list | Test runner |

Điểm thiết kế đáng nhớ **[ngoài tài liệu]**: grader sẽ được cắm vào **một chỗ duy nhất** là `run_test_case`; muốn đổi prompt thì chỉ sửa `run_prompt`; `run_eval` không đổi. Nhờ vậy mỗi lần chỉ đổi một thứ, đúng điều kiện so phiên bản ở W4D1 mục 8.4.

Hiện tại grader là chỗ giữ chỗ: `score = 10` cố định, chỉ để thử luồng chạy.

Chạy:

```python
with open("dataset.json", "r") as f:
    dataset = json.load(f)
results = run_eval(dataset)
print(json.dumps(results, indent=2))
```

Tài liệu nói chạy lần đầu mất khoảng 30 giây ngay cả với Haiku cho một dataset nhỏ, và sẽ có phần tối ưu sau.

## 10. Slide Feed Through Claude và Feed Through a Grader

- Slide 1–2: ba ô prompt (template + từng câu hỏi) đi qua Claude cho ra ba câu trả lời. Đây là bước 3.
- Slide 3: grader nhận **cả câu hỏi lẫn câu trả lời** rồi cho điểm (10, 4, 9). Đây là bước 4, chưa có code; mới là phần giữ chỗ `score = 10` ở trên.
- Slide dùng biến `{question}` còn code dùng `test_case["task"]`; chỉ khác tên trường, cấu trúc như nhau.

## 11. Trả lời câu hỏi hướng dẫn: cách ghép template với từng input

**Đủ để trả lời.**

- Template là một f-string nằm **trong** `run_prompt`, có đúng một chỗ trống, là `{test_case["task"]}`.
- Mỗi ca trong dataset (một object có `task`) được truyền vào `run_prompt`, f-string điền `task` vào chỗ trống, ra một prompt hoàn chỉnh.
- Prompt đó được bọc thành một message `user` (qua `add_user_message`), gửi bằng `chat`, nhận lại text.
- Vòng lặp trong `run_eval` làm việc này **lần lượt cho từng ca**, mỗi ca là một lần gọi API độc lập (không có lịch sử chung giữa các ca, vì `messages = []` được tạo mới trong mỗi lần gọi).

## 12. Trả lời câu hỏi hướng dẫn: cách lưu kết quả để so giữa các phiên bản

**Chỉ đủ một nửa.** Tài liệu cho biết **cấu trúc** của kết quả, nhưng **chưa có cách lưu và cách so giữa các phiên bản**.

Tài liệu có:
- Kết quả là **list các dict**, mỗi dict ứng với một ca, có ba trường:

  | Trường | Nội dung |
  |---|---|
  | `output` | Toàn bộ câu trả lời của Claude |
  | `test_case` | Ca gốc (object có `task`) |
  | `score` | Điểm (hiện là 10 cố định) |

- Xem kết quả bằng `print(json.dumps(results, indent=2))`.
- Vì mỗi bản ghi mang theo cả `test_case` lẫn `output`, nên mỗi bản ghi **tự mô tả đủ** (ca nào, trả lời gì, điểm bao nhiêu). Đây là điều cần cho việc xem điểm từng ca, không chỉ điểm trung bình (W4D1 mục 8.3 ý 3).

Tài liệu **không có**:
- Ghi kết quả ra file (khác với bước dataset, nơi có `json.dump` ra `dataset.json`).
- Cách đánh dấu **phiên bản prompt** nào đã tạo ra kết quả đó.
- Cách so điểm hai lần chạy.

**[ngoài tài liệu]** Gợi ý để so được giữa các phiên bản (chỉ làm khi bài sau chưa có cách riêng):
- Mỗi lần chạy ghi ra một file riêng (ví dụ `results_v1.json`), kèm metadata: tên hoặc nội dung template, model, thời điểm chạy.
- Giữ nguyên `dataset.json` giữa các lần, để so được ca với ca.
- So **điểm từng ca** giữa v1 và v2, không chỉ điểm trung bình.

## 13. Đọc phê phán pipeline **[ngoài tài liệu]**

1. **`score = 10` cố định thì pipeline chưa đo được gì.** Mọi ca đều 10, giống bảng `bench_models.py` toàn 1.00. Mục đích chỉ là kiểm tra luồng chạy (đã được thay bằng grader thật ở mục 17).
2. **Prompt trong `run_prompt` khác chữ so với v1** ở mục 2: v1 là "Please provide a solution to the following task:", còn ở đây là "Please solve the following task:". Khi so các phiên bản, **chốt rõ văn bản của v1** để không vô tình đổi hai thứ (W4D1 mục 8.4: mỗi lần chỉ đổi một thứ).
3. **Vòng lặp tuần tự, một ca một lần gọi.** Với dataset hàng trăm ca thì chậm; hướng giảm: gọi song song hoặc Batch API (NOTES.md mục 1). Nếu dùng Batch thì thứ tự kết quả không bảo đảm, phải ghép theo `custom_id`; vòng lặp tuần tự thì thứ tự giữ nguyên nên chưa cần.
4. **Không có xử lý lỗi.** Một ca bị lỗi API (429, 529, hết thời gian) thì cả `run_eval` dừng, mất kết quả các ca trước. SDK có retry (NOTES.md mục 1), nhưng khi dataset lớn nên bắt lỗi theo từng ca và ghi nhận ca đó fail.
5. **Mỗi ca chạy một lần.** Chưa phản ánh dao động giữa các lần chạy (W4D1 mục 7 câu 4). Muốn có tỉ lệ đạt cần chạy mỗi ca nhiều lần.
6. **`chat` vẫn gửi `temperature` mặc định 1.0.** Nếu model mới trả 400 với tham số này thì pipeline lỗi ngay ca đầu (xem mục 7 điểm 1).
7. **`max_tokens` = 1000 trong `chat`** có thể cắt cụt câu trả lời dài (ví dụ prompt chưa có chỉ dẫn ngắn gọn, output rất dài). Kết quả bị cắt có thể làm grader chấm sai; nên để ý `stop_reason`.

## 14. Nối với những gì đã làm trong repo **[ngoài tài liệu]**

| Thành phần | Ở bài này | Ở `bench_models.py` |
|---|---|---|
| Duyệt các ca | `run_eval` | vòng lặp prompt × lần chạy × model |
| Chạy một ca | `run_prompt` | một lần gọi `messages.create` |
| Chấm điểm | placeholder `score = 10` | grader bằng code (11:20, JSON khớp, 3 dòng `- `) |
| Ghi nhận | list dict `output/test_case/score` | bảng quality, latency, cost |

Khác biệt: `bench_models.py` đổi **model** giữa các lần chạy còn bài này sẽ đổi **prompt**; và `bench_models.py` có grader thật từ đầu, còn bài này để grader cho bài sau.

---

# Phần C. Model based grading (bước 4)

## 15. Ba loại grader

Grader nhận output của model và trả về một tín hiệu đo được, thường là số từ 1 đến 10 (10 là tốt, 1 là kém). Slide "Graders" chia ba loại:

| | Code | Model | Human |
|---|---|---|---|
| Cách làm | Đánh giá bằng logic code tự viết | Nhờ một model cho điểm, hoặc **so hai phiên bản** | Nhờ người cho điểm, hoặc so hai phiên bản |
| Hợp với | Độ dài output; có hoặc không chứa từ nào đó; kiểm cú pháp (JSON, Python, regex); điểm dễ đọc | Chất lượng câu trả lời; mức làm theo chỉ dẫn; độ đầy đủ; tính hữu ích; an toàn | Chất lượng chung; độ toàn diện; chiều sâu; độ súc tích; mức liên quan |
| Ưu và nhược | Chỉ cần code trả được một tín hiệu dùng được | Rất linh hoạt | Linh hoạt nhất nhưng tốn thời gian và nhàm |

Khớp với W4D1 mục 8.2 (grader bằng code và bằng model). Loại **Human** là mới ở bài này. Slide còn nhắc **so hai phiên bản** (pairwise) như một cách chấm bằng model hoặc người, bên cạnh chấm điểm từng output; bài chưa đi sâu vào cách này.

## 16. Tiêu chí đánh giá trước, grader sau

Bài nhấn mạnh phải có tiêu chí rõ trước khi viết grader. Câu hỏi của slide: "làm sao biết prompt tạo ra output tốt?". Với prompt sinh code AWS có ba tiêu chí:

| Tiêu chí | Nội dung | Grader |
|---|---|---|
| **Format** | Chỉ trả Python, JSON hoặc Regex, không giải thích | Code |
| **Valid Syntax** | Python, JSON, regex sinh ra phải đúng cú pháp | Code |
| **Task Following** | Trả lời trực tiếp, rõ ràng yêu cầu của người dùng; code sinh ra phải chính xác | Model |

Lý do chia: hai tiêu chí đầu kiểm được bằng luật; tiêu chí thứ ba cần sự linh hoạt của model.

Đây là đúng "tiêu chí chọn" ở W4D1 mục 8.2 (đáp án có kiểm được bằng luật không), và slide cuối chính là **grader lai** (code kiểm ràng buộc cứng, model kiểm phần mềm). Hai tiêu chí đầu được làm ở Phần D (Code based grading); tiêu chí thứ ba ở Phần C này.

## 17. Grader bằng model: code trong bài

```python
def grade_by_model(test_case, output):
    eval_prompt = f"""
    You are an expert code reviewer. Evaluate this AI-generated solution.

    Task: {test_case["task"]}
    Solution: {output}

    Provide your evaluation as a structured JSON object with:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement
    - "reasoning": A concise explanation of your assessment
    - "score": A number between 1-10
    """
    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    eval_text = chat(messages, stop_sequences=["```"])
    return json.loads(eval_text)
```

Cấu trúc prompt của grader:
1. **Vai:** "expert code reviewer".
2. **Dữ liệu cần chấm:** `Task` (đề bài từ test case) và `Solution` (output của prompt đang eval). Grader nhìn **cả đề lẫn bài làm**, giống slide "Feed Through a Grader".
3. **Định dạng trả về:** JSON với bốn trường.
4. **Ép JSON sạch:** prefill "```json" + stop sequence "```", rồi `json.loads`, cùng kỹ thuật của `generate_dataset()` ở mục 5.

Gắn vào pipeline (thay chỗ `score = 10` ở mục 9):

```python
def run_test_case(test_case):
    output = run_prompt(test_case)
    model_grade = grade_by_model(test_case, output)
    return {"output": output, "test_case": test_case,
            "score": model_grade["score"], "reasoning": model_grade["reasoning"]}

def run_eval(dataset):
    results = [run_test_case(tc) for tc in dataset]      # bài viết bằng vòng for + append
    average_score = mean([r["score"] for r in results])  # from statistics import mean
    print(f"Average score: {average_score}")
    return results
```

Bản ghi kết quả giờ có bốn trường: `output`, `test_case`, `score`, `reasoning`. Lần đầu có một **con số trung bình** để theo dõi khi lặp prompt.

## 18. Trả lời câu hỏi hướng dẫn: Model based grading

**Đủ để trả lời.**

**Prompt của grader có barem không?**
- **Không có barem.** Prompt không nói thế nào là 9 điểm, thế nào là 4 hay 1; chỉ nói "A number between 1-10".
- Prompt cũng **không nêu tiêu chí cụ thể** (Task Following) mà chỉ nói chung "Evaluate this AI-generated solution". Tiêu chí nằm ở thiết kế (mục 16), chưa nằm trong chữ của prompt.
- Cái có: vai chuyên gia review code, đề bài, bài làm, và yêu cầu liệt kê điểm mạnh, điểm yếu, lập luận trước khi cho điểm.
- **[ngoài tài liệu]** Barem rõ (mô tả từng mức điểm, nêu tiêu chí cần xét) là cách giảm dao động mình đã ghi ở W4D1 mục 8.2; bài này chưa làm.

**Đầu ra là điểm hay điểm kèm lý do?**
- **Điểm kèm lý do**: `strengths` (1–3 ý), `weaknesses` (1–3 ý), `reasoning` (giải thích ngắn) và `score` (1–10).
- Bài gọi đây là "key insight": nếu không bắt model nêu điểm mạnh, điểm yếu và lập luận thì model hay **mặc định chấm quanh 6** (tuyên bố của khóa học, mình chưa tự kiểm).
- `run_test_case` chỉ giữ `score` và `reasoning` trong kết quả; `strengths` và `weaknesses` bị bỏ.

**Định dạng đầu ra?**
- **JSON object** có bốn trường trên, ép bằng prefill + stop sequence rồi `json.loads`.
- `score` là số; bài không kiểm tra kiểu hay khoảng 1–10.

## 19. Điều bài này làm thay đổi so với bài Running the eval

- `score = 10` giữ chỗ đã được thay bằng điểm thật từ grader, nên pipeline lần đầu **đo được** (mục 13 điểm 1 không còn đúng).
- Kết quả có thêm `reasoning`, nên khi một ca điểm thấp có thể đọc lý do ngay trong bản ghi (đúng điều W4D1 mục 8.3 ý 3 khuyên).
- **Vẫn chưa có**: lưu kết quả ra file, và so giữa các phiên bản (mục 12). `run_eval` chỉ `print` điểm trung bình rồi trả list.
- Mỗi ca giờ tốn **hai lần gọi API** (một để sinh, một để chấm), nên N ca là khoảng 2N lần gọi, như W4D1 mục 8.2 đã ghi.

## 20. Đọc phê phán grader bằng model **[ngoài tài liệu]**

1. **"Objective metric" là nói hơi quá.** Chính bài cũng thừa nhận "model graders can be somewhat capricious". Điểm chỉ là một **đường cơ sở nhất quán** nếu grader (prompt, model) được giữ cố định giữa các phiên bản (W4D1 mục 8.4); đổi một chữ trong prompt của grader là đổi thước đo.
2. **Không có barem** nên điểm dao động và dễ thiên vị (ví dụ mến câu dài, W4D1 mục 8.3). Cách giảm: viết barem, chấm nhiều lần lấy trung bình, đối chiếu điểm của người với vài mẫu.
3. **Grader chưa biết các tiêu chí Format và Syntax đã được code chấm**. Nếu output có lời giải thích thừa, grader bằng model có thể phạt hoặc không phạt tuỳ ý. Nên nói rõ trong prompt grader tiêu chí nào nó phải chấm (Task Following) để không chấm chồng.
4. **Model tự chấm bài của mình:** nếu `chat` dùng chung một `model` cho cả prompt đang eval và grader thì model chấm bài của chính nó. Có thể thiên vị bài của mình; nên cân nhắc dùng model khác hoặc mạnh hơn làm grader.
5. **`chat` vẫn gửi `temperature=1.0`** nên điểm dao động theo mỗi lần gọi (và có thể bị 400 ở model mới, xem mục 7 điểm 1). Vì model mới không cho chỉnh sampling, cách giảm dao động còn lại là chấm nhiều lần và lấy trung bình.
6. **Parse có thể lỗi.** `json.loads` fail nếu grader thêm chữ hoặc bị cắt; `score` có thể là chuỗi hoặc ngoài 1–10. Cần validate (như Lab 2) và thử lại.
7. **Điểm trung bình che chi tiết.** Cần xem điểm từng ca và đọc `reasoning` của các ca thấp, đừng chỉ nhìn một số.
8. **Giữ cả `strengths` và `weaknesses`** trong kết quả sẽ có thêm dữ liệu để rà lỗi; hiện bị bỏ.
9. **Thứ tự trường trong JSON:** `reasoning` đặt trước `score` nên model viết lập luận rồi mới ra điểm. Có thể là lý do điểm ít bị "mặc định" hơn; bài không nói rõ, mình chưa kiểm chứng.

## 21. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Ba loại grader, chọn theo kiểm được bằng luật hay không | W4D1 mục 8.2 (code = Toán, model = Văn) |
| Slide cuối: code grader cho Format + Syntax, model grader cho Task Following | W4D1 mục 8.2: grader lai |
| Grader quá khắt khe hoặc sai chuẩn hoá | ISSUES.md #15, #16 (grader trong `bench_models.py`) |
| Model grader dao động, không phải con số "khách quan" tuyệt đối | W4D1 mục 8.3 và 8.4 |
| 2N lần gọi cho N ca | NOTES.md mục 1 (Batch API giúp rẻ hơn khi chạy hàng loạt) |

---

# Phần D. Code based grading (bước 4, tiếp)

Nguồn: bài "Code based grading" và hai slide (phân vai grader, ba hàm validate). Bài mở đầu ghi "The notebooks for this course aren't available here", nghĩa là không có notebook để đối chiếu code (xem thêm mục 5, thân hàm `generate_dataset()` bị thiếu).

## 22. Code grader làm gì

Nhắc lại phân vai ở mục 16: **Format** và **Valid Syntax** do code grader chấm, **Task Following** do model grader chấm; ghép hai điểm lại thì có đánh giá "toàn diện".

| Tiêu chí | Ý nghĩa | Bài đưa ra cách kiểm bằng code? |
|---|---|---|
| Format | Chỉ trả đúng loại code (Python, JSON hoặc Regex), không giải thích | **Không có hàm riêng.** Chỉ có chỉ dẫn trong prompt, prefill và gián tiếp qua việc parse (mục 25) |
| Valid Syntax | Code sinh ra parse được đúng ngôn ngữ | **Có**, ba hàm validate (mục 23) |

## 23. Ba hàm validate

```python
import ast, json, re

def validate_json(text):
    try:
        json.loads(text.strip());  return 10
    except json.JSONDecodeError:   return 0

def validate_python(text):
    try:
        ast.parse(text.strip());   return 10
    except SyntaxError:            return 0

def validate_regex(text):
    try:
        re.compile(text.strip());  return 10
    except re.error:               return 0
```

| Hàm | Cách kiểm | Lỗi nghĩa là |
|---|---|---|
| `validate_json` | Parse thành JSON | Output không hợp lệ |
| `validate_python` | Parse thành **cây cú pháp trừu tượng (AST)**, không chạy code | Output không hợp lệ |
| `validate_regex` | **Biên dịch** thành regex | Output không hợp lệ |

Quy ước: parse được thì **10**, lỗi thì **0**. Thang 0 hoặc 10 cùng thang với điểm của model grader (1–10), nên cộng hoặc lấy trung bình được. Dùng `.strip()` để bỏ khoảng trắng và xuống dòng hai đầu.

Điểm đáng nhớ: `ast.parse` chỉ **phân tích cú pháp**, không thực thi. An toàn khi chấm output chưa tin cậy.

## 24. Trường `format` trong dataset

Để code grader biết dùng validator nào, mỗi ca phải khai báo định dạng mong đợi:

```json
{ "task": "Create a Python function to validate an AWS IAM username", "format": "python" }
```

Bài nói có thể sửa prompt sinh dataset để tự thêm trường `format` vào ví dụ output (không đưa code). Bản mình viết **[ngoài tài liệu]**: đổi ví dụ trong prompt sinh thành `{"task": "...", "format": "python" | "json" | "regex"}` và nêu rõ ba giá trị hợp lệ.

Điều này khớp gợi ý ở mục 8 và giải quyết vấn đề "không cân bằng giữa ba loại" ở mục 7 điểm 6: có `format` thì đếm được từng loại.

## 25. Làm prompt rõ hơn, và ghép điểm

**Làm rõ prompt (chủ yếu để đạt tiêu chí Format):**
- Thêm chỉ dẫn: "Respond only with Python, JSON, or a plain Regex" và "Do not add any comments or commentary or explanation".
- Dùng prefill kèm stop sequence để model trả code thô:

```python
add_assistant_message(messages, "```code")
output = chat(messages, stop_sequences=["```"])
```

Prefill "```code" mở một khối code **không nêu ngôn ngữ**, nên không cần biết trước là Python, JSON hay Regex; stop sequence cắt trước dấu đóng. Kết quả là chỉ còn code, không lời dẫn, không dấu ```.

**Chọn validator theo `format`:**

```python
def grade_syntax(output, test_case):
    if test_case["format"] == "json":   return validate_json(output)
    if test_case["format"] == "python": return validate_python(output)
    return validate_regex(output)
```

**Ghép điểm trong `run_test_case`:**

```python
model_grade = grade_by_model(test_case, output)
model_score = model_grade["score"]
syntax_score = grade_syntax(output, test_case)
score = (model_score + syntax_score) / 2
```

Trọng số bằng nhau cho chất lượng nội dung và độ đúng kỹ thuật; bài nói có thể chỉnh trọng số theo nhu cầu.

**Baseline:** chạy eval để có điểm xuất phát. Điểm đó **không tốt hay xấu tự thân**; điều quan trọng là có cải thiện được nó bằng cách sửa prompt hay không. Đây là cách đo tiến bộ bằng số thay vì cảm tính.

## 26. Trả lời câu hỏi hướng dẫn: Code based grading

**Đủ ý chính. Có hai chỗ tài liệu không nói rõ** (đánh dấu bên dưới).

**Kiểm tra gì bằng code?**
- **JSON hợp lệ:** `json.loads` parse được.
- **Python hợp lệ:** `ast.parse` parse được.
- **Regex hợp lệ:** `re.compile` biên dịch được.
- Validator được chọn theo trường `format` của từng ca; kết quả là 10 hoặc 0.
- **Định dạng (không có giải thích):** tài liệu xếp tiêu chí này cho code grader nhưng **không có hàm kiểm riêng** (chỗ không nói rõ thứ nhất). Định dạng được lo bằng chỉ dẫn trong prompt, prefill + stop sequence, và gián tiếp bằng việc parse: lời dẫn lẫn trong output thường làm JSON hoặc Python parse lỗi, nên bị 0.

**Khi nào code không đủ?**
- Khi cần đánh giá **Task Following**: output có **trả lời đúng yêu cầu** không, code có **chính xác** không. Code grader chỉ biết "cú pháp hợp lệ", không biết "làm đúng việc". Một hàm Python parse được vẫn có thể làm sai đề, và vẫn được 10.
- Những chỗ đó giao cho **model grader** (mục 17), rồi ghép hai điểm.
- Chỗ không nói rõ thứ hai: tài liệu **không có đoạn riêng** liệt kê "khi nào code không đủ"; mình rút ra từ cách chia tiêu chí (hai tiêu chí cho code, một cho model) và câu "together, they provide a comprehensive evaluation".

## 27. Đọc phê phán code grader **[ngoài tài liệu]**

1. **`validate_regex` rất dễ tính.** `re.compile` chấp nhận hầu hết chuỗi văn bản thường, kể cả câu giải thích tiếng Anh. Output "Here is the regex: ^a$" vẫn biên dịch được và được 10. Nên Format không được bảo vệ ở loại regex. Cách tăng: kiểm output là một dòng, không có khoảng trắng và chữ thường như lời dẫn, hoặc thử regex trên vài chuỗi mẫu.
2. **Format không có kiểm riêng.** Với JSON và Python thì parse lỗi có thể bắt được lời dẫn, nhưng với regex thì không (điểm 1). Có thể thêm hàm kiểm: output không chứa dấu ```, không bắt đầu bằng câu tiếng Anh, độ dài hợp lý.
3. **Cú pháp đúng không có nghĩa là đúng việc.** `ast.parse("x")` là hợp lệ; `validate_json("5")` cũng hợp lệ dù đề bài cần một policy document. Chỉ model grader (hoặc chạy test) mới bắt được. Đúng ý của bài, nhưng cần nhớ khi đọc điểm 10.
4. **`grade_syntax` mặc định rơi về regex.** Nếu `format` thiếu hoặc gõ sai (ví dụ "yaml", "Python"), hàm im lặng dùng `validate_regex`, mà hàm này gần như luôn cho 10. Nên báo lỗi khi `format` không thuộc ba giá trị.
5. **Trung bình hai điểm che mất lỗi.** Điểm cú pháp 0 mà model chấm 9 cho ra 4.5, trông như "tạm được", dù output không dùng được. Hai cách: lưu hai điểm riêng trong kết quả (không chỉ điểm gộp), hoặc **gác cổng**: cú pháp sai thì cho 0 luôn và **bỏ qua lần gọi model grader**, đỡ tốn tiền (grader lai, W4D1 mục 8.2).
6. **Hai điểm 0 hoặc 10 trộn với thang 1–10 của model.** Chỉ hợp lệ vì cùng thang; nhưng cú pháp là nhị phân còn điểm model là thang liên tục nên trọng số bằng nhau chưa chắc phản ánh mức quan trọng.
7. **Làm hai thứ một lúc.** "Làm rõ prompt" gồm hai thay đổi (chỉ dẫn "chỉ trả code" và prefill). Nếu áp cả hai vào v2 thì không biết thứ nào có tác dụng (W4D1 mục 8.4: mỗi lần chỉ đổi một thứ). Nên đưa vào từng cái một.
8. **Prefill vẫn là điểm chưa kiểm chứng** với model hiện tại (mục 7 điểm 2); "```code" và `grade_by_model` đều dựa vào nó.
9. **Bắt ngoại lệ hẹp.** Mỗi hàm chỉ bắt một loại lỗi. Đầu vào lạ (ví dụ chuỗi có ký tự null với `ast.parse`, hoặc regex quá phức tạp) có thể ném lỗi khác và làm cả `run_eval` dừng. Nên bắt rộng hơn rồi trả 0.
10. **Baseline không nói "tốt hay xấu" là đúng**, nhưng khi so v1 với v2 vẫn cần chạy nhiều lần và xem điểm từng ca để biết chênh lệch có thật hay chỉ là dao động (W4D1 mục 9 câu 2).

## 28. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Validate JSON, regex bằng code | Lab 2: `jsonschema.validate` kiểm output lúc chạy (W4D1 mục 6.4) |
| Chọn grader theo "kiểm được bằng luật không" | W4D1 mục 8.2; code = Toán, model = Văn |
| Ghép code + model | W4D1 mục 8.2: grader lai |
| Grader có thể có bug, chuẩn hoá trước khi so | ISSUES.md #15, #16 (mục 27 điểm 1, 4) |
| Prefill + stop sequence để ép output sạch | `archive/Building with the Claude API.txt` dòng 74 |

Toàn bộ pipeline sau bốn bài:

```
dataset (task + format)  ->  run_prompt  ->  output
        output + task  ->  grade_by_model  ->  score model (1-10) + reasoning
        output + format ->  grade_syntax   ->  score cú pháp (0 hoặc 10)
                          score = trung bình hai điểm  ->  mean trên cả dataset
```

---

# Phần E. Ôn tập và việc còn lại

## 29. Câu hỏi ôn tập

**Về dataset**
1. Vì sao prompt v1 là mốc tốt dù nó "dở"? (Gợi ý: bước 5 cần một điểm xuất phát để so; v1 chưa có ràng buộc "chỉ code".)
2. Prefill + stop sequence cùng giải quyết vấn đề gì? Bỏ một trong hai thì output hỏng ở đâu?
3. Vì sao lưu `dataset.json` thay vì sinh mới mỗi lần chạy eval?
4. Bạn sinh 100 tác vụ bằng một lần gọi Haiku. Kể ba rủi ro về chất lượng dataset và cách giảm.
5. Dataset trong bài không có đáp án mẫu. Chấm output thế nào, bằng code hay bằng model?

**Về chạy eval**
6. Template được ghép với input ở hàm nào, và vì sao mỗi ca là một lần gọi API độc lập?
7. Muốn đổi prompt v1 thành v2, chỉ cần sửa hàm nào? Muốn đổi cách chấm, sửa hàm nào? Vì sao tách như vậy là hợp lý?
8. Mỗi bản ghi kết quả có ba trường nào, và vì sao nên giữ cả `test_case` trong bản ghi?
9. Để so v1 và v2, tài liệu đã cho biết gì và còn thiếu gì? Bạn sẽ lưu thêm gì?
10. Với `score = 10` cố định thì nên kết luận gì về pipeline?

**Về model based grading**
11. Ba loại grader là gì, mỗi loại hợp với việc gì?
12. Với ba tiêu chí Format, Valid Syntax, Task Following, tiêu chí nào giao cho code, tiêu chí nào giao cho model, và vì sao?
13. Vì sao bài yêu cầu grader trả `strengths`, `weaknesses`, `reasoning` chứ không chỉ `score`?
14. Prompt grader trong bài thiếu gì so với một barem? Nêu hai hậu quả.
15. Điểm trung bình tăng từ v1 lên v2. Cần kiểm gì về grader trước khi tin?

**Về code based grading**
16. Ba hàm validate kiểm gì, và vì sao trả 10 hoặc 0?
17. Vì sao test case cần trường `format`? Nếu thiếu thì `grade_syntax` làm gì, và vì sao đó là rủi ro?
18. Một hàm Python parse được nhưng làm sai đề sẽ được bao nhiêu điểm từ code grader? Chỗ nào bắt được lỗi đó?
19. `validate_regex` có bắt được output có lời giải thích kèm theo không? Vì sao?
20. Điểm cú pháp 0, điểm model 9, trung bình 4.5: vì sao đây là vấn đề, và có hai cách xử lý nào?

## 30. Còn lại và việc cần kiểm tra

- Thân hàm `generate_dataset()` trong bài thiếu; bản ở mục 5 là mình tái dựng, chưa chạy. Code của bài Running the eval cũng chưa chạy; các điểm ở mục 13 là suy luận.
- Kiểm tra bằng một lần gọi thật với `claude-haiku-5-5`: (a) `temperature` có bị 400 không; (b) prefill `"```json"` còn được chấp nhận không; (c) stop sequence hoạt động ra sao.
- Tài liệu chưa nói cách **lưu kết quả ra file** và **so giữa các phiên bản**; xem các bài sau (grader, tối ưu) có bổ sung không.
- Code của bài Model based grading cũng chưa chạy. Cần thử: grader có trả JSON đúng với prefill không, và claim "model hay mặc định chấm khoảng 6 nếu không có lý do" có đúng với model đang dùng không.
- Code của bài Code based grading cũng chưa chạy. Cần thử: `validate_regex` với output có lời dẫn (mục 27 điểm 1), và prefill "```code" với model hiện tại.
- Bốn bài của module đã có đủ tài liệu. Bài sau (nếu có) chắc là chạy eval thật, sửa prompt v2 và so điểm; bổ sung tại đây, đặc biệt cách lưu kết quả và so giữa các phiên bản (mục 12).
- Chưa làm: thêm test khó hơn cho `bench_models.py` (từ W4D1).
