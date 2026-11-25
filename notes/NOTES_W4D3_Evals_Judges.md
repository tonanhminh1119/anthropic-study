# Notes Week 4 Day 3: Evals & Judges (design doc, eval, chọn grader, judge có hiệu chuẩn)

Nguồn: bài "Evals & Judges" (mở đầu phần production hardening), gồm các đoạn: Defining done before you ship, Write the design document, An eval is the test set, Matching the grading method, Building and calibrating the judge, Coverage matters more than perfection, cùng bảng chọn grader đi kèm. **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung của mình, cần đối chiếu docs khi áp dụng.

Nối với notes cũ: khung 5 bước và hai loại grader ở [NOTES_W4D1_Prompt_Evaluation.md](NOTES_W4D1_Prompt_Evaluation.md) mục 8; pipeline `run_eval` và code grader ở [NOTES_W4D2_Eval_Dataset_Running.md](NOTES_W4D2_Eval_Dataset_Running.md) mục 9, 17, 23; hook `PreToolUse` ở [LAB3.md](../labs/lab3/mcp-server/LAB3.md) mục 6.4; kịch bản lỗi và retry ở [LAB2.md](../labs/lab2/LAB2.md).

## 1. Bài này đứng ở đâu

W4D1 và W4D2 dạy eval như **kỹ thuật** (workflow 5 bước, dựng dataset, viết grader). Bài này đặt eval vào một vai trò lớn hơn: **định nghĩa của "xong"** trước khi ship, và là cột sống của cả module production hardening phía sau.

Mạch của bài:

```
Tin bằng cảm giác ("thử vài lần thấy ổn")  ->  không theo dõi được
        |
Design document: ghi ra "xong" nghĩa là gì (4 quyết định)      [mục 2]
        |
Eval: biến tiêu chí thành điểm trên một tập ca cố định          [mục 3]
        |
Chọn grader theo hình dạng output (match / code / judge)        [mục 4, 5]
        |
Judge phải được hiệu chuẩn mới tin được                         [mục 6, 7]
        |
Độ phủ quan trọng hơn độ hoàn hảo; mỗi lần đổi một thứ          [mục 8, 9]
```

Câu mở đầu của bài: "Your success metric is simple: the code works correctly." Các agent và tool ở module trước (Lab 2, Lab 3) trả lời đúng khi thử tay. Chỗ thiếu: "thử vài lần thấy ổn" không phải tín hiệu theo dõi được. Eval biến cảm giác thành **một con số theo dõi được** khi prompt, tool hoặc model thay đổi.

## 2. Design document: ghi "xong, an toàn, chịu nổi chi phí" ra giấy

Design document là một file ngắn (thường một trang markdown), viết **trước khi viết code production**. Nó tồn tại để bạn **định nghĩa cái đúng** thay vì hợp thức hóa bất cứ thứ gì model sinh ra sau này (cùng tinh thần "viết eval trước feature" ở mục 3).

### 2.1 Bốn quyết định

| # | Quyết định | Trả lời câu hỏi | Ví dụ cụ thể (theo bài) | Lớp phía sau dùng nó |
|---|---|---|---|---|
| 1 | **Success criteria** (tiêu chí thành công) | Feature phải cho ra **cái gì**, đủ cụ thể để chấm | Mơ hồ: "tóm tắt thread". Cụ thể: "bản tóm tắt hai câu, liệt kê **mọi** action item và người phụ trách" | Các ca và tiêu chí của **eval** |
| 2 | **Failure handling** (xử lý lỗi) | Hệ thống phải **sống sót** qua lỗi nào, làm gì với từng lỗi | Liệt kê lỗi production sẽ ném ra, đánh dấu **retriable** (thử lại được) hay **terminal** (dứt khoát), và người dùng nhận gì khi không cứu được | Phần **error handling** (ca retriable, ca terminal) |
| 3 | **Cost and latency budget** (ngân sách) | **Trần** chi phí/độ trễ và **sàn** độ tin cậy không được đánh đổi | Ngân sách mỗi request, trần chi phí hàng tháng, mục tiêu độ trễ, độ tin cậy tối thiểu | Phần **đo đạc (instrument)** theo ngân sách |
| 4 | **Trust boundary** (ranh giới tin cậy) | Input nào **không đáng tin**, hệ thống **được phép làm gì** | Ghi rõ nội dung agent đọc mà người khác viết được, và tập hành động/quyền truy cập **nhỏ nhất** feature cần | Input coi là **dữ liệu**; hành động nguy hiểm gác bằng **hook** |

Ý then chốt của bài: viết bốn quyết định này **một lần, trước khi build**, để các lớp sau **nhất quán với nhau** thay vì mỗi lớp giải một bài toán khác. Mỗi quyết định phải đủ cụ thể để ai đó **kiểm được hệ thống đã build** so với nó.

### 2.2 Vì sao đặt ngân sách trước kiến trúc

Bài nói: đặt **ngân sách cứng về chi phí và độ trễ trước khi chọn kiến trúc**. Lý do: có con số rồi thì kiểm được kiến trúc có vừa ngân sách **trước khi viết dòng code nào**. Ví dụ **[ngoài tài liệu]**: nếu mỗi request có ngân sách 2 cent mà thiết kế cần ba lần gọi model lớn thì loại ngay trên giấy, khỏi phải build rồi mới thấy.

### 2.3 Với công cụ lập trình agent

Bài nói thêm: nếu bạn dùng một agentic coding tool, design doc cũng là thứ **nộp trước khi nó viết gì**: lập kế hoạch, ghi ra thành tài liệu, rồi mới cài đặt theo tài liệu. Tool có tiêu chí rõ và ràng buộc tường minh thì **ít phải đoán** và cho ra code kiểm được so với bản đã thống nhất.

**[ngoài tài liệu]** Nối với việc đang làm: chính các file `LAB2.md`, `LAB3.md` có mục "Mục tiêu" và "Việc còn lại" đã là phiên bản nhẹ của design doc. Ánh xạ chi tiết sang PRD, SRS và QC test ở mục 12.1. Chuyển nghĩa sang .NET: design doc giống ADR hoặc spec trước khi code; success criteria là acceptance criteria; failure handling là phân loại lỗi tạm thời (transient, thử lại như Polly) và lỗi vĩnh viễn; ngân sách là SLO; trust boundary là threat model cộng nguyên tắc đặc quyền tối thiểu.

### 2.4 Khung design doc để dùng lại **[ngoài tài liệu]**

Bài chỉ nói doc "ngắn, một trang". Khung dưới đây là gợi ý của mình, không phải mẫu của khóa học:

```markdown
# Design: <tên feature>

## 1. Success criteria
- Với input loại A, output phải: <mô tả đủ để chấm: định dạng, độ dài, nội dung bắt buộc>
- Ví dụ 3-5 ca đại diện (đầu vào -> đầu ra mong đợi). Đây là hạt giống của eval.

## 2. Failure handling
| Lỗi | Retriable? | Hành động | Người dùng nhận |
|---|---|---|---|
| 429 / 529 | có | backoff, tối đa N lần | ... |
| output không parse được | có (1 lần) | thử lại kèm lỗi | ... |
| input vượt giới hạn | không | từ chối | thông báo rõ |

## 3. Budget
- Mỗi request: <= $X | Mỗi tháng: <= $Y | Độ trễ p95: <= Z giây | Độ tin cậy tối thiểu: >= N%

## 4. Trust boundary
- Input không tin cậy: <...>
- Quyền tối thiểu: <tool/hành động được phép> ; <hành động bị chặn bằng hook>
```

## 3. Eval là gì

Ẩn dụ của bài: eval là **nhiệt kế**. Nó không làm bệnh nhân khỏe hơn, nó chỉ cho một con số tin được. Trước khi có eval, "xong" là cảm giác. Sau khi có, "xong" là **một điểm trên một tập ca cố định**.

Ba thành phần: (1) tập **ca đầu vào**, (2) với mỗi ca, **hành vi mong đợi**, (3) **điểm** chấm output so với hành vi mong đợi. Cả bộ ba đó là eval.

Vì sao viết eval **trước** feature: ép bạn định nghĩa thành công trước khi cài đặt; nếu không, bạn sẽ có xu hướng **biện minh cho bất cứ output nào model đưa ra** (cùng ý với design doc ở mục 2). **[ngoài tài liệu]** Giống TDD: viết test trước, test fail trước, rồi mới làm cho pass.

Pipeline tối thiểu (cùng khuôn W4D2 mục 9):

```python
def run_test_case(test_case):
    """Chạy một ca qua feature, rồi chấm."""
    output = run_prompt(test_case)
    score = grade(test_case, output)        # cách chấm: xem mục 4
    return {"output": output, "test_case": test_case, "score": score}

def run_eval(dataset):
    """Chạy mọi ca và báo điểm trung bình."""
    results = [run_test_case(c) for c in dataset]
    average = sum(r["score"] for r in results) / len(results)
    print(f"Average score: {average}")
    return results
```

Điểm cần nhớ:
- **Điểm tự thân không tốt hay xấu.** Lần đầu được 2 hoặc 3 trên 10 là bình thường. Cái quan trọng là con số có **tăng** khi bạn đổi prompt, tool hoặc model không. (Khớp W4D2 mục 25: "baseline không tốt hay xấu tự thân".)
- **Mỗi lần đổi một thứ**, để biết thứ nào gây ra cải thiện (khớp W4D1 mục 8.4). Eval biến thay đổi từ chuyện ý kiến thành chuyện đo được.

Khung này **trùng với W4D2 mục 9**; `grade` ở đây chỉ là tên gọi chung cho bất kỳ grader nào ở mục 4 (match, code check hoặc judge).

## 4. Ba cách chấm: chọn theo hình dạng output

Grader biến output thành tín hiệu, thường là số từ 1 đến 10. Bài nói **chọn sai cách chấm là chỗ phí công nhất** của eval.

### 4.1 Bảng chọn grader (bảng trong ảnh bạn gửi)

> "Of the three methods listed below, the judge is the only one you must build and tune, so it gets its own treatment here."

| Loại tác vụ | Cách chấm | Bắt được gì | Chỗ không đáng tin |
|---|---|---|---|
| Một nhãn hoặc giá trị đúng duy nhất | **Exact / string match** (khớp chính xác) | Đáp án sai khi chỉ có **đúng một** đáp án, không mơ hồ, chi phí gần 0 | Trượt mọi cách diễn đạt hoặc **thứ tự khác** vẫn đúng, nên **sai** với mọi thứ mở |
| Output có cấu trúc hoặc là code | **Code-graded check** (kiểm bằng code) | JSON hỏng, code không parse được, số ngoài khoảng, thiếu trường bắt buộc | Không nói gì về **nội dung có tốt không**, chỉ nói **đúng khuôn** |
| Chất lượng mở | **LLM-as-judge** (model làm giám khảo) | Độ trung thực (faithfulness), làm đúng chỉ dẫn, độ đầy đủ, giọng điệu: những thứ **không luật code nào diễn tả được** | **Nhiễu, đắt**, và cho ra con số **trông tự tin nhưng vô nghĩa** cho đến khi được hiệu chuẩn |

Quy tắc rút gọn: **một dạng đúng thì dùng match; một luật cấu trúc thì dùng code; chất lượng mở thì dùng judge.**

Chỗ này là bản chi tiết của W4D1 mục 8.2 (code = Toán, model = Văn): thêm loại thứ ba **exact match** ở đầu thang (rẻ nhất, giòn nhất), và thêm cột "chỗ không đáng tin".

### 4.2 Ví dụ so sánh của bài

**Ví dụ 1: feature phải trả ba thủ đô của một vùng dưới dạng mảng JSON.** Một lần chạy trả mảng đúng ba thủ đô nhưng **khác thứ tự** so với chuỗi tham chiếu.

| Cách chấm | Kết quả | Vì sao |
|---|---|---|
| Exact match | **0** (sai oan) | Ký tự không khớp, dù đáp án đúng |
| Code grader (parse JSON, kiểm thành viên) | **Tốt** | Cả ba thủ đô có mặt và cấu trúc hợp lệ |

**Ví dụ 2: feature phải trả một đoạn lập luận cho một đề xuất.**

| Cách chấm | Kết quả | Vì sao |
|---|---|---|
| Code grader | Gần như **vô giá trị** | Chỉ xác nhận là chuỗi không rỗng |
| Exact match | **Vô vọng** | Không có hai lập luận tốt nào dùng cùng chữ |
| Judge | **Duy nhất dùng được** | Chỉ judge mới nói được lập luận có trung thực và đầy đủ không |

**[ngoài tài liệu]** Chú ý chỗ lỏng trong ví dụ 1: "kiểm thành viên" chỉ bảo đảm ba thủ đô **có mặt**. Muốn chặt hơn cần so **tập hợp** (set) với tập tham chiếu: không thừa phần tử, không thiếu, không trùng. Nếu không, mảng có thêm một thành phố sai vẫn được điểm tốt.

### 4.3 Code grader chỉ là một lần parse

Code grader thường chỉ là **thử parse**: parse được thì điểm tốt, ném lỗi thì điểm 0. Bài đưa hai hàm (cùng ý W4D2 mục 23; ở đây chưa có `validate_regex`):

```python
import json, ast

def validate_json(text):
    try:
        json.loads(text.strip())
        return 10          # parse được là JSON
    except json.JSONDecodeError:
        return 0           # hỏng, ca này rớt

def validate_python(text):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0
```

Cả một lớp lỗi định dạng được bắt rẻ bằng cách này, thứ mà người rất chán khi phải kiểm tay. Những giới hạn của loại này (`validate_regex` quá dễ tính, cú pháp đúng không là đúng việc) đã ghi ở W4D2 mục 27, không lặp lại ở đây.

## 5. Chi phí và tần suất chạy

Bài nói điều mà bảng "hơi nói nhẹ": có **chiều chi phí** nữa.

| | Exact match, code check | LLM judge |
|---|---|---|
| Chạy ở đâu | Cục bộ | Một lần gọi model **cho mỗi ca** |
| Chi phí mỗi ca | Gần 0 | Tiền thật + độ trễ |
| Chạy được bao nhiêu lần | Hàng nghìn ca, **mỗi lần đổi code** | Phù hợp chạy **định kỳ**, lãng phí nếu làm vòng lặp trong cùng |

Ví dụ của bài: eval 1000 ca chấm bằng judge = **1000 lần gọi API thêm** mỗi lần chạy. Hợp lý cho một lượt đánh giá đầy đủ theo định kỳ, **lãng phí** nếu là vòng lặp chặt.

Thực tế nhiều đội: **chấm định dạng và cấu trúc bằng code ở mỗi commit**, **dành judge cho một lượt chấm chất lượng chậm hơn, theo lịch**. Chọn grader là chọn một phần theo **tín hiệu** và một phần theo **tần suất bạn chịu nổi**.

**[ngoài tài liệu]** Ánh xạ .NET: giống kim tự tháp test. Unit test nhanh chạy mỗi commit trong CI; integration test chậm, đắt chạy hàng đêm. Thêm một điểm nối với notes cũ: chạy judge hàng loạt hợp với **Batch API** (rẻ hơn, chậm hơn, NOTES.md mục 1), vì lượt chấm theo lịch không cần kết quả tức thì. Trong W4D2 mục 19 mình đã tính 2N lần gọi cho N ca khi có model grader; ở đây là cùng con số nhìn từ góc chi phí.

## 6. Xây judge: một lần gọi model có barem

Judge là **một lần gọi model thứ hai**, dẫn dắt bằng một barem (rubric) rõ ràng.

```python
def grade_by_model(task, solution):
    eval_prompt = f"""
    You are an expert reviewer. Evaluate the solution for the task.
    Task: {task}
    Solution: {solution}
    Return JSON with:
      "strengths":  array of 1-3 points
      "weaknesses": array of 1-3 points
      "reasoning":  a one to two sentence explanation, 50 words maximum
      "score":      a number from 1 to 10
    """
    messages = [{"role": "user", "content": eval_prompt}]
    result = chat(messages)        # trả về JSON ở trên
    return json.loads(result)
```

**Điểm làm cho judge dùng được:** bắt nó trả **điểm mạnh, điểm yếu và lập luận cùng với điểm**, không chỉ điểm. Không làm vậy thì model **trôi về một con số an toàn ở giữa, thường quanh 6**, bất kể chất lượng thật. Bài nói yêu cầu lập luận **trước** là cái neo điểm vào một chi tiết cụ thể.

So với `grade_by_model` ở W4D2 mục 17:

| | W4D2 mục 17 | Bài này |
|---|---|---|
| Ép JSON sạch | prefill "```json" + stop sequence (**bị 400** trên `claude-haiku-5-5`) | **Không dùng prefill**, gọi `chat` rồi `json.loads` |
| Độ dài `reasoning` | "concise" (không giới hạn) | "1-2 câu, tối đa **50 từ**" |
| Thứ tự trường | strengths, weaknesses, reasoning, score | Giống |

Bản mới không dựa vào prefill nên **không vướng lỗi 400** ở W4D2 mục 7 điểm 2. Nhưng nó **mong model trả JSON thuần**: nếu model bọc trong khối ```json thì `json.loads` vẫn lỗi (xem mục 11 điểm 4). Còn điểm "model hay mặc định quanh 6" và "lập luận trước neo được điểm" là **tuyên bố của khóa học, mình chưa tự kiểm** (khớp ghi chú ở W4D2 mục 18 và mục 20 điểm 9; bài này nói rõ hơn nhưng vẫn chưa có thí nghiệm).

## 7. Hiệu chuẩn judge: đo độ đồng thuận với người

Bài nói **đa số người bỏ qua bước này, và chính nó làm judge đáng tin hay không.** Judge chưa hiệu chuẩn thì điểm của nó là "con số trông chặt chẽ nhưng không có giá trị".

Cách làm (đúng như bài):

```
1. Lấy một tập ca đã được NGƯỜI gắn nhãn sẵn
2. Chạy judge trên đúng các ca đó
3. Đo judge đồng ý với người bao nhiêu phần trăm
4. Nếu thấp -> sửa barem: nêu rõ từng mức điểm nghĩa là gì,
   thêm một ví dụ câu trả lời tốt và một ví dụ tệ, rồi đo lại
```

Một judge **bất đồng với nhãn người một nửa số lần** thì cho ra con số vô dụng. Đo sự đồng thuận trước khi dựa vào điểm là thứ biến judge **từ phỏng đoán thành bằng chứng bảo vệ được**.

### 7.1 Tính độ đồng thuận **[ngoài tài liệu]**

Bài không đưa code đo, chỉ nói "đo xem đồng ý bao nhiêu lần". Đây là bản tối thiểu của mình (đã chạy thử, kết quả ở dưới):

```python
def agreement(human, judge, tol=0):
    """Tỉ lệ ca mà điểm judge lệch người không quá tol."""
    return sum(abs(h - j) <= tol for h, j in zip(human, judge)) / len(human)

human = [9, 2, 7, 4, 8, 3, 9, 5]
judge = [8, 2, 6, 6, 8, 5, 9, 6]
agreement(human, judge)            # 0.375  khớp tuyệt đối 3/8
agreement(human, judge, tol=1)     # 0.75   lệch không quá 1 điểm, 6/8
# chuyển về nhị phân (>= 7 là đạt)
hp = [h >= 7 for h in human]; jp = [j >= 7 for j in judge]
agreement(hp, jp)                  # 0.875  đạt/không đạt, 7/8
```

Ba điều rút ra từ ví dụ trên:
- **Cùng một dữ liệu, ba con số khác nhau** (0.375, 0.75, 0.875) tùy bạn định nghĩa "đồng ý" thế nào. Phải chốt định nghĩa trước khi nói "judge đồng ý 80%".
- Thang 1–10 rất khó khớp tuyệt đối (người cũng chấm lệch nhau). Thực tế hay ép về **đạt/không đạt** hoặc thang ngắn 1–5 để đo dễ và đáng tin hơn.
- Độ đồng thuận thô còn bị **may rủi** thổi phồng (nếu 90% ca là "đạt", judge luôn nói "đạt" cũng được 90%). Khi đó cần chỉ số hiệu chỉnh theo may rủi như Cohen's kappa hoặc tương quan hạng, hoặc xem riêng nhóm ca khó.

### 7.2 Các cách giảm nhiễu và thiên vị **[ngoài tài liệu]**

| Vấn đề | Cách giảm |
|---|---|
| Judge dao động giữa hai lần chấm | **Chấm nhiều lần, lấy trung vị hoặc trung bình.** Trên `claude-haiku-5-5` không chỉnh được `temperature` (400, W4D2 mục 7 điểm 1), nên đây là cách còn lại |
| Thiên vị câu dài | Nêu trong barem "độ dài không phải tiêu chí"; đưa cặp ví dụ ngắn-đúng và dài-sai |
| Model tự chấm bài của chính nó | Dùng model **khác** hoặc **mạnh hơn** làm judge (W4D2 mục 20 điểm 4) |
| Sửa barem cho khớp rồi tin luôn | Chia nhãn người thành **hai nhóm**: nhóm để sửa barem, nhóm **giữ riêng** để kiểm lại; không thì bạn chỉ khớp riêng với tập đã dùng để chỉnh |

Cả bảng này là **ngoài khóa học**: bài chỉ nêu "sửa barem rồi đo lại".

## 8. Độ phủ quan trọng hơn sự hoàn hảo

Bài khẳng định: một tập eval **lớn hơn với chấm tự động hơi nhiễu** thường cho thấy nhiều hơn tập nhỏ chấm tay kỹ. Mục tiêu của eval là **đủ độ phủ để bắt hồi quy**, không phải làm barem hoàn hảo.

- **20 ca có cả input lạ và ca biên bắt được lỗi mà 3 ca chọn kỹ chưa chạm tới.**
- Cần thêm ca: nhờ Claude **sinh thêm từ một tập nhỏ đã gắn nhãn**, rồi **kiểm lại bằng mắt một mẫu** để tập không bị lệch. (Cùng ý W4D2 mục 6: sinh bằng Haiku, kiểm tay.)
- Độ phủ đến từ **số lượng**.

**[ngoài tài liệu]** Hai lưu ý đối chiếu notes cũ:
1. **Sinh được input, nhưng nhãn đáp án thì sao?** Hạt giống có nhãn do người; ca Claude sinh thêm nếu cũng do Claude gắn nhãn thì dính điểm mù chung (W4D1 mục 8.5). Nên để người xem lại nhãn của một mẫu, nhất là ca khó.
2. **Độ phủ không phải số lượng thuần.** 20 ca cùng một kiểu không bằng 20 ca đa dạng. Những loại ca biên nên có: input rỗng, quá ngắn, quá dài, sai chính tả, trộn tiếng Việt và tiếng Anh, nhiều ý, ngoài phạm vi, và nội dung giống chỉ dẫn (kiểm trust boundary ở mục 2). Danh sách này là mở rộng từ W4D1 mục 7 câu 6.

## 9. Vòng lặp cải tiến

```
đặt mục tiêu -> viết prompt đầu -> chạy eval -> đọc chỗ hỏng
      -> áp dụng MỘT thay đổi prompt-engineering -> chạy eval lại
      (lặp hai bước cuối đến khi điểm đạt mức cần)
```

### 9.1 Mỗi lần đổi một đòn bẩy

Bài nêu đúng hậu quả: viết lại prompt, thêm hai ví dụ **và** đổi model trong một lượt, điểm nhích lên thì bạn **không học được gì** về thứ nào gây ra. Quy trình: đổi một thứ, chạy lại, đọc kết quả từng ca, **chỉ giữ thay đổi nếu điểm tăng.** Một lượt chậm hơn nhưng cả vòng đời feature **nhanh hơn nhiều**, vì bạn biết cái gì điều khiển điểm. (Đúng W4D1 mục 8.4 và mục 9 câu 1.)

### 9.2 Xem từng ca, không chỉ trung bình

Điểm trung bình đứng yên có thể **che** một thay đổi sửa được 3 ca và làm hỏng 3 ca khác. Bảng từng ca lộ ra ngay, trung bình thì giấu.

### 9.3 Điểm thấp là thông tin để hành động

Câu hỏi quan trọng không phải "ca này có rớt không" mà là **"vì sao rớt"**. Bài đưa ba mẫu:

| Triệu chứng | Chỉ về đâu |
|---|---|
| Lỗi **định dạng** | **Chỉ dẫn về output** của prompt |
| Lỗi **sự kiện** trên nội dung được truy xuất | Bước **truy xuất** (retrieval) |
| Lỗi chỉ xuất hiện với **input dài** | Cách xử lý **ngữ cảnh** (context) |

Eval cho biết ca nào rớt; **output từng ca cho biết nhóm lỗi**; nhóm lỗi biến vòng lặp sau thành **sửa có chủ đích** thay vì đoán.

**[ngoài tài liệu]** Gợi ý ghi thêm vào bản ghi kết quả một trường **nhóm lỗi** (`failure_category`) do người hoặc judge gắn khi đọc ca điểm thấp, để đếm được "bao nhiêu ca rớt do định dạng". Khớp việc tách điểm theo nhóm ở W4D1 mục 7 câu 6.

## 10. Khi nào dùng, khi nào không (tóm tắt của bài)

| | Nội dung |
|---|---|
| **Làm tốt** | Biến "trông đúng" thành điểm theo dõi được, bảo vệ được, và đổi từng thay đổi có chủ đích một lần |
| **Thêm chi phí hoặc độ phức tạp** | Soạn ca và hiệu chuẩn judge là công việc thật **trước** khi ship được feature nào |
| **Dùng cách khác** | Output **một định dạng cố định duy nhất** thì **chỉ cần code check**. **Bỏ judge hoàn toàn** |

Dòng cuối rất đáng nhớ: đừng dựng judge theo phản xạ. Nếu một hàm code kiểm được thì dừng ở đó (mục 5: judge thêm chi phí và nhiễu mà không thêm giá trị).

## 11. Đọc phê phán **[ngoài tài liệu]**

1. **Bài đặt "judge chưa hiệu chuẩn thì vô nghĩa" nhưng không nói cần bao nhiêu ca nhãn người, và đạt mức đồng thuận nào thì đủ.** Với 8 ca (ví dụ ở mục 7.1) một ca sai đã đổi tỉ lệ 12.5 điểm phần trăm. Cần đủ ca (ít nhất vài chục) và nên báo kèm độ bất định, không chỉ một phần trăm.
2. **Ngưỡng "đủ tốt" nên gắn với quyết định.** Judge dùng để chặn ship cần chặt hơn judge dùng để xếp hạng sơ bộ hai phiên bản. Design doc (mục 2) là chỗ ghi ngưỡng này.
3. **Con số "quanh 6" và "lập luận trước neo điểm" là tuyên bố chưa kiểm.** Thí nghiệm nhỏ để kiểm với model đang dùng: chấm cùng 10 ca có và không có `reasoning`, so phân bố điểm.
4. **`json.loads(result)` giòn.** Model hay bọc JSON trong khối ```json hoặc thêm lời dẫn. Cần bóc khối code, validate (điểm trong khoảng 1–10, đủ trường) và thử lại, như Lab 2. Đây cũng là một lớp "code check" áp lên chính judge.
5. **`reasoning` giới hạn 50 từ là cân bằng giữa chi phí và độ rõ.** Ngắn quá thì lập luận không neo được điểm; dài thì tốn token cho mỗi ca (nhân với N ca).
6. **Judge và feature dùng cùng một model** thì có thể thiên vị bài của mình (W4D2 mục 20 điểm 4); bài này chưa nói tới.
7. **Hai nhân tố làm điểm nhảy mà không phải do prompt:** đổi judge (barem, model) giữa hai lần chạy, và đổi tập ca. Hiệu chuẩn xong thì **đóng băng** judge như đóng băng dataset (W4D1 mục 8.4).
8. **Code check (0 hoặc 10) và judge (1–10) khác bản chất, nên ghép bằng trung bình là không khéo.** Xem W4D2 mục 27 điểm 5, 6: **gác cổng** (code rớt thì bỏ qua lần gọi judge) hợp lý hơn trung bình đơn giản, và khớp ý bài "code check mỗi commit, judge theo lịch".
9. **Design doc bài mô tả như thứ làm một lần, nhưng thực tế nó sống.** Lỗi thật ở production nên quay lại cập nhật ca eval và cả mục failure handling (nối vòng khép kín ở W4D1 mục 6.4).
10. **Bài gọi 4 quyết định là "nền" cho các lớp sau, nhưng module này mới dạy lớp eval.** Ba quyết định còn lại (failure, budget, trust boundary) sẽ được dạy tiếp, nên đừng coi mục 2 là đủ để làm chúng.

## 12. Nối với notes cũ **[ngoài tài liệu]**

| Ý của bài | Nối với |
|---|---|
| Eval = "xong" là điểm, không phải cảm giác | W4D1 mục 2, 3: ba con đường sau khi viết prompt |
| `run_test_case` / `run_eval` | W4D2 mục 9 (pipeline ba hàm) |
| Ba cách chấm; chọn theo hình dạng output | W4D1 mục 8.2 (code = Toán, model = Văn); W4D2 mục 15, 16 |
| `validate_json`, `validate_python` | W4D2 mục 23 (thêm `validate_regex`) |
| Judge trả strengths, weaknesses, reasoning, score | W4D2 mục 17, 18 |
| Judge cần hiệu chuẩn | **Mới ở bài này.** W4D2 mục 20 chỉ nói "cần đối chiếu điểm của người với vài mẫu" |
| Coverage > hoàn hảo; sinh thêm ca từ tập nhỏ | W4D2 mục 6 (dataset sinh bằng Haiku, kiểm tay) |
| Mỗi lần đổi một thứ; xem từng ca | W4D1 mục 8.4, 9 |
| Chi phí judge theo số ca; chạy định kỳ | NOTES.md mục 1 (Batch API), W4D2 mục 19 |
| Failure handling retriable/terminal | LAB2.md (vòng lặp agent, lỗi, giới hạn vòng) |
| Trust boundary, hook gác hành động | LAB3.md mục 6.4 (hook `PreToolUse` là denylist) |

Toàn bộ vòng đời sau bài này:

```
design doc (4 quyết định)
   |-> success criteria -> eval dataset (ca + nhãn người)
   |                          |-> grader theo hình dạng output:
   |                          |     match / code check (mỗi commit)  |  judge (theo lịch)
   |                          |-> judge: hiệu chuẩn bằng nhãn người, đóng băng barem
   |-> failure handling -> ca retriable, ca terminal
   |-> budget           -> đo chi phí, độ trễ theo ngân sách
   '-> trust boundary   -> input = dữ liệu, hành động gác bằng hook
```

### 12.1 Ánh xạ sang PRD, SRS và QC test **[ngoài tài liệu]**

Phần này là cách ánh xạ của mình, rút ra khi trao đổi. Bài không nhắc tới PRD, SRS hay QC test.

**a) Design doc so với PRD và SRS**

Design doc **không phải PRD thuần**. Nó là **PRD cộng SRS cộng một chút thiết kế kỹ thuật**, rút gọn còn một trang.

| Mục trong design doc | Thuộc về | Mục tương ứng |
|---|---|---|
| Success criteria | PRD và SRS | Acceptance criteria (PRD); functional requirements (SRS) |
| Failure handling | SRS | Reliability, error handling, recovery |
| Cost, latency budget, reliability floor | SRS | Performance, quality attributes, constraints (NFR, SLO) |
| Trust boundary | SRS | Security requirements, threat model |

- Phần "vì sao làm" và đối tượng người dùng của PRD thì design doc **gần như không có**. Nó chỉ lấy phần "hệ thống phải làm và phải chịu được gì" của hai tài liệu.
- **Điểm chung quan trọng nhất: yêu cầu phải kiểm chứng được (testable).** SRS chuẩn đòi mỗi requirement kiểm được; bài cũng đòi mỗi quyết định đủ cụ thể để ai đó kiểm hệ thống đã build so với nó ("tóm tắt hai câu, đủ action item và owner" kiểm được, "tóm tắt thread" thì không).
- **Bảng truy vết yêu cầu (requirements traceability matrix)** nối requirement với test case. Eval chính là bộ test case đó: mỗi tiêu chí thành công nên có ít nhất vài ca eval trỏ về nó.
- Design doc **lấn sang thiết kế**: SRS nói *làm gì*, còn bài ghi cả *làm bằng cách nào* ("gác hành động bằng hook", "phân loại retriable hoặc terminal"). Vì vậy mới có "một chút thiết kế kỹ thuật" ở trên.
- Hai chỗ khác SRS truyền thống khi làm với model: yêu cầu độ tin cậy ở đây mang tính **thống kê** ("đạt trên 90% số ca eval", không phải "luôn đúng"); và "input không tin cậy được coi là dữ liệu, không phải lệnh" là loại yêu cầu bảo mật mà SRS thông thường chưa có.

**b) Eval so với unit test và QC test**

Quy trình gần như giống nhau: lấy tiêu chí, viết ca kèm hành vi mong đợi, chạy, chấm. Eval gần **QC test** hơn unit test, vì nó kiểm hành vi của cả khối prompt cộng model như một hộp đen, dựa trên yêu cầu.

| Trong eval | Giống gì ở QA | Ghi chú |
|---|---|---|
| Code check (JSON hợp lệ, đủ trường, số trong khoảng) | Unit test trong CI, kiểm **rule đặc biệt** | Rẻ, chạy mỗi commit |
| Judge (trung thực, đủ ý, giọng điệu) | Lượt QC chạy theo lịch, kiểm **chất lượng mềm** | Đắt, chạy định kỳ |
| Kiểm chuỗi tool call có đi đúng đường không | Kiểm **đúng flow** | Lab 2 đã làm kiểu này; bài chưa nhắc tới |
| Người viết ca và nhãn không phải người viết prompt | QC tách khỏi dev | W4D1 mục 7 câu 6: dev tự viết tập test thì chung điểm mù |

Ba chỗ analogy lệch:
1. **Kết quả là điểm trên cả tập, không phải pass hoặc fail từng ca.** Model không tất định nên cùng một ca có thể khác nhau giữa hai lần; báo tỉ lệ đạt trên nhiều lần chạy.
2. **Người chấm cũng là một model và cần được kiểm.** Với output mở không có kết quả mong đợi cụ thể để so, nên cần judge. Judge giống QC junior mà bạn phải đối chiếu với nhãn của QC senior (hiệu chuẩn, mục 7). Unit test không có khâu này.
3. **Đổi model hoặc prompt là đổi "thứ được test".** Model nâng phiên bản có thể làm hành vi đổi mà không ai sửa dòng nào, nên eval phải chạy lại mỗi khi đổi bất cứ thứ gì, kể cả model.

**c) Ba cách chấm so với ba loại test của một hệ thống SSO** (ánh xạ do bạn đề xuất, mình chỉnh thêm)

| Cách chấm | Loại test tương ứng | Ví dụ SSO | Chỗ cần chỉnh |
|---|---|---|---|
| Exact match | Test có **outcome cố định** | Login thành công hay thất bại; user tồn tại hay không | SSO là deterministic nên `401` không bao giờ "đúng nhưng viết khác". Output của model thì cùng một ý có thể đổi chữ hoặc thứ tự, nên exact match giòn hơn nhiều; so tập hợp thay vì so chuỗi là đã chuyển sang code check |
| Code grader | Test **contract / schema API** | Init phải có `login_challenge`; flow `authorization_code` thì result phải có `code` | Điều kiện kiểu "flow X thì phải có trường Y" là schema có điều kiện (`if/then`), cùng loại `jsonschema.validate` ở Lab 2. Có trường `code` chỉ chứng minh đúng khuôn, không chứng minh code đổi được token (cái đó là test flow/integration) |
| Judge | **UAT** do PO làm | PO kiểm UX và câu chữ | Chính xác hơn là hai thứ ghép: **phán quyết của PO ≈ nhãn người để hiệu chuẩn judge** (mục 7); **judge ≈ bản tự động thay PO**, chạy được mỗi lần đổi prompt. Khác UAT ở chỗ judge **phải được đối chiếu với PO**, còn PO thì không cần ai kiểm lại |

Cùng một cách chia tần suất ở mục 5: exact match và code check chạy mỗi commit như test API trong CI; judge giống UAT, đắt và chạy trước mốc quan trọng, nên chạy định kỳ. Nối với W4D2 mục 15: UAT ≈ loại grader **Human** ("linh hoạt nhất nhưng tốn thời gian"), và judge là bản rẻ hơn của nó.

## 13. Câu hỏi ôn tập

**Về design document**
1. Bốn quyết định trong design doc là gì? Mỗi quyết định sau này trở thành lớp nào của hệ thống?
2. Vì sao "tóm tắt thread" không phải một tiêu chí thành công tốt, và viết lại thế nào cho chấm được?
3. Vì sao phải đặt ngân sách chi phí và độ trễ **trước** khi chọn kiến trúc?
4. Retriable và terminal khác nhau ra sao? Cho mỗi loại một ví dụ trong hệ thống của bạn.
4b. Design doc khác PRD ở đâu, giống SRS ở đâu? Vì sao nói "yêu cầu kiểm chứng được" là điểm chung, và eval nằm ở đâu trong bảng truy vết yêu cầu? (mục 12.1)

**Về eval và chọn grader**
5. Vì sao bài viết eval trước feature? Điều gì xảy ra nếu viết sau?
6. Điểm đầu tiên là 2/10. Kết luận gì? Cái gì mới quan trọng?
7. Chọn grader cho ba tác vụ: (a) phân loại ticket vào 3 nhãn; (b) trả JSON có đủ ba trường; (c) tóm tắt một báo cáo có trung thực không. Giải thích.
8. Feature phải trả ba thủ đô dạng mảng JSON; mảng đúng nhưng khác thứ tự. Exact match và code check chấm ra sao, và code check cần chặt thêm gì để không cho điểm oan?
9. Vì sao bài khuyên chấm cấu trúc bằng code ở mỗi commit và chỉ chạy judge theo lịch?
10. Khi nào bỏ hẳn judge?

**Về judge**
11. Vì sao judge phải trả strengths, weaknesses, reasoning cùng score? Nếu chỉ trả score thì xu hướng gì xảy ra?
12. Hiệu chuẩn judge gồm các bước nào? Nếu độ đồng thuận thấp thì làm gì?
13. Tám ca có nhãn người, judge khớp tuyệt đối 3/8 nhưng lệch không quá 1 điểm là 6/8. Nên báo con số nào, và vì sao cần nói rõ cách định nghĩa?
14. Sửa barem cho judge khớp với nhãn người trên **cùng một tập**. Rủi ro gì, cách giảm?

**Về độ phủ và vòng lặp**
15. Vì sao 20 ca có ca biên tốt hơn 3 ca chọn kỹ?
16. Dùng Claude sinh thêm ca từ tập nhỏ có nhãn: kiểm gì trước khi dùng?
17. Đổi prompt, thêm ví dụ và đổi model trong một lượt, điểm tăng. Học được gì? Vì sao xem từng ca quan trọng như xem trung bình?
18. Một ca rớt vì định dạng; một ca rớt vì sự kiện trên nội dung truy xuất; một ca rớt chỉ khi input dài. Mỗi ca chỉ về đâu?

## 14. Còn lại và việc cần kiểm tra

- **Chưa có thí nghiệm nào chạy thật cho bài này.** Mọi đoạn code của bài đều là mô phỏng khóa học, chưa gọi API. Chỉ có hàm `agreement` ở mục 7.1 là mình tự viết và chạy thử (kết quả 0.375, 0.75, 0.875).
- **Các tuyên bố của khóa học chưa kiểm:** judge không có lập luận thì trôi về khoảng 6; yêu cầu lập luận trước neo được điểm; lần đầu 2–3/10 là bình thường. Cần thử với model đang dùng (mục 11 điểm 3).
- **Bài chưa nói:** cần bao nhiêu ca nhãn người để hiệu chuẩn, mức đồng thuận nào là đủ, cách đo (mục 7.1 là gợi ý của mình), và cách lưu kết quả để so giữa các phiên bản (còn thiếu từ W4D2 mục 12).
- **Hướng dẫn thực hành tiếp theo (nếu làm Lab 4):** viết design doc một trang cho eval AWS-code ở W4D2 (success criteria = ba tiêu chí Format, Valid Syntax, Task Following); thêm bước bóc khối ``` và validate trước `json.loads` cho judge; gắn nhãn tay khoảng 20 ca để đo độ đồng thuận.
- Ba quyết định còn lại của design doc (failure handling, budget, trust boundary) sẽ được dạy ở các bài sau của module; bổ sung tại đây khi có tài liệu.
- Task cuối module (theo bài): "harden a system against all four at once" (cumulative task), nên mục 2 sẽ được dùng lại khi đó.
- Chưa làm: thêm test khó hơn cho `bench_models.py` (từ W4D1).
