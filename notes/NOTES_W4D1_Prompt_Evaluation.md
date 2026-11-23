# Notes Week 4 Day 1: Prompt Evaluation (mở đầu)

Nguồn: tài liệu khóa học, hai bài "Prompt evaluation" (mục 1–7) và "A typical eval workflow" (mục 8–9), cùng các slide đi kèm. **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung của mình, cần đối chiếu docs khi áp dụng.

Nối với notes cũ: prompting craft ở `archive/Production-Grade Prompting, Agents & Tool-use.txt` mục 1, benchmark ở [NOTES.md](NOTES.md) mục 2, validate output ở [LAB2.md](../labs/lab2/LAB2.md).

## 1. Prompt Engineering và Prompt Evaluation

| | Prompt Engineering | Prompt Evaluation |
|---|---|---|
| Câu hỏi | **Viết** prompt thế nào cho tốt hơn? | Prompt này **tốt đến đâu**, bản nào tốt hơn? |
| Bản chất | Bộ best practice: multishot, XML tag, v.v. | Kiểm thử tự động để **đo** |
| Việc cụ thể | Sửa prompt | Test với đáp án kỳ vọng, so sánh các phiên bản của cùng một prompt, rà lỗi trong output |

Engineering là công cụ sửa, evaluation là thước đo. Thiếu thước đo thì không biết bản sửa có tốt hơn thật không.

**[ngoài tài liệu]** Slide ghi "unexpected outputs" ở Option 2; ý đúng là người dùng đưa **input** bất ngờ.

## 2. Ba con đường sau khi viết xong prompt

| | Làm gì | Rủi ro | Chi phí |
|---|---|---|---|
| **Option 1** | Thử **một lần**, thấy ổn là xong | Vỡ ở production | Gần 0 |
| **Option 2** | Thử **vài lần**, vá một hai corner case | Người dùng vẫn đưa input chưa từng nghĩ tới | Thấp |
| **Option 3** | Chạy qua **evaluation pipeline**, chấm điểm, rồi lặp lại trên prompt | Thấp nhất | Nhiều công và tiền hơn, đổi lại tin cậy hơn |

- Option 1 và 2 là cái bẫy mọi engineer đều mắc, vì **đánh giá thấp số edge case thực tế**.
- Nối với archive mục 1: "đúng với input mình đưa nhưng vỡ khi gặp biến thể" giống dev chỉ có unit test happy path rồi bị QC và stress test bắt lỗi. Option 3 là bước QC đó làm có hệ thống.

## 3. Evaluation-first cho gì

1. Phát hiện điểm yếu **trước** khi lên production.
2. So sánh các phiên bản prompt **khách quan**.
3. Lặp lại dựa trên mức cải thiện **đo được**.
4. Ứng dụng đáng tin hơn.

Cái giá: đầu tư trước (thời gian, hạ tầng test). Mục tiêu là bắt lỗi ở giai đoạn dev.

## 4. Nối với những gì đã làm trong repo **[ngoài tài liệu]**

| Thành phần của eval | Đã có ở đâu |
|---|---|
| Tập test | 3 prompt `math`, `json`, `bullets` trong `demos/bench_models.py` |
| Chạy | 3 lần × 4 model |
| Chấm điểm tự động | Grader theo code: giờ HH:MM cuối là 11:20; JSON khớp hoàn toàn; đúng 3 dòng `- `, mỗi dòng ≤ 8 từ |
| Điểm tổng | Quality 0–1 mỗi model |

Ba bài học đã tự gặp, và là lý do Option 3 khó hơn Option 1:
- **Tập test quá dễ thì điểm tuyệt đối không nói được gì.** Cả 4 model đạt 1.00 nên không phân biệt được model (xem ISSUES.md, mục "Còn mở"). Tập test cần đủ khó và đa dạng.
- **Grader cũng có bug.** Issue #15 và #16: điểm 0.78 rồi 0.67 sai do grader. Không kiểm tra grader thì tối ưu prompt theo thước đo sai.
- **Một lần chạy không đủ.** Lab 2 kịch bản A chạy hai lần cho hai đường đi khác nhau (3282 và 4662 token). Eval cần nhiều lần chạy và cho ra **tỉ lệ đạt**, không phải đúng hoặc sai một lần.

Quy tắc ở NOTES.md mục 2 ("bắt đầu từ model rẻ nhất, chỉ nâng khi eval của chính tác vụ cho thấy rẻ không đạt") chỉ dùng được khi có eval.

Ánh xạ .NET: Option 1 là chạy tay một lần rồi deploy; Option 2 là vài unit test happy path; Option 3 là test suite trong CI. Khác ở chỗ unit test thường pass hoặc fail, còn eval cho **điểm trên cả tập** vì model không tất định.

## 5. Cost, Complexity, Risk

- **Cost:** chi phí nhân theo số test case × số lần lặp × số model. Giảm bằng Message Batches API (rẻ hơn, chậm hơn, hợp eval hàng loạt; xem NOTES.md mục 1).
- **Complexity:** phải xây tập test, cách chấm và nơi lưu kết quả để so các phiên bản.
- **Risk:** làm ẩu Option 3 còn tệ hơn không làm, vì có con số trông khách quan nhưng có thể sai (grader lỗi, tập test thiên lệch).

## 6. Vị trí của engineering và evaluation trong một hệ thống

Câu hỏi: eval có phải là "train" người dùng viết prompt tốt hơn, hay là tự động biến câu tự nhiên của user thành prompt tốt hơn rồi cho model chạy?

**Trả lời: không phải cả hai.** Eval không nằm ở runtime và không nhắm vào người dùng cuối. Đó là quy trình **của dev, ở giai đoạn phát triển**, để kiểm tra một **prompt template** do dev viết.

### 6.1 Prompt do ai viết

Trong một service, người dùng cuối **không viết prompt**. Dev viết sẵn prompt template (system prompt, hướng dẫn, ví dụ, ràng buộc output), trong đó có chỗ trống cho input của người dùng:

```
<system prompt do dev viết, cố định>
<task>Trích xuất dữ liệu thành JSON theo ví dụ.</task>
<example>...</example>
<doc>{{ input của user }}</doc>      <- chỗ duy nhất đổi theo từng request
```

Ánh xạ .NET **[ngoài tài liệu]**: prompt template giống source code hoặc stored procedure (dev viết, đưa vào version control), input của user giống tham số request. Người dùng đưa tham số, không sửa code.

### 6.2 Hai pha

```
PHA DEV (offline, lặp nhiều vòng)
  viết/sửa prompt template   <- Prompt Engineering
          |
  chạy trên tập test (nhiều input, nhiều lần) -> chấm điểm   <- Prompt Evaluation
          |
  điểm thấp? -> sửa template, chạy lại. Điểm đạt -> chốt phiên bản vN

PHA RUNTIME (online, mỗi request)
  input user -> điền vào template vN -> model -> output -> (validate) -> trả về
```

| | Prompt Engineering | Prompt Evaluation |
|---|---|---|
| Ai làm | Dev | Dev (hoặc pipeline CI) |
| Khi nào | Lúc phát triển | Lúc phát triển, và chạy lại mỗi lần đổi prompt hoặc model |
| Tác động lên | **Nội dung** prompt template | **Quyết định**: bản nào đáng ship, có hồi quy không |
| Người dùng cuối thấy | Chỉ thấy kết quả của template đã chốt | Không thấy gì |

Eval **không train model** (trọng số không đổi) và **không train người dùng**. Nó chỉ cho dev biết template có tốt không.

### 6.3 Còn hai ý bạn nêu

**(a) Tự động chuyển câu tự nhiên của user thành prompt tốt hơn lúc chạy.** Đây là một mẫu thiết kế **khác**, thêm một bước ở runtime: một lần gọi model để viết lại hoặc làm rõ yêu cầu rồi mới đưa vào template (hợp khi user nhập mơ hồ, như tìm kiếm). Hai điểm cần nhớ:
- Nó làm **tăng** chi phí và độ trễ (thêm một lần gọi), và thêm một chỗ có thể sai.
- Bước viết lại này **bản thân cũng là một prompt**, nên cũng phải đo bằng eval. Eval không thay thế nó, mà dùng để biết nó có thật sự giúp không.
- **[ngoài tài liệu]** Mình nhớ Anthropic Console có công cụ cải thiện prompt cho dev (làm ở giai đoạn dev, không phải runtime); cần đối chiếu docs trước khi khẳng định.

**(b) Dùng kết quả eval để tự cải thiện prompt.** Có, nhưng ở pha dev: dev đọc các ca bị điểm thấp rồi sửa template (hoặc nhờ model đề xuất bản sửa, dev xem lại). Điểm eval là thước để chọn bản. **[ngoài tài liệu]** Cách "tự động hoàn toàn" (một vòng lặp model tự sửa prompt dựa trên điểm) có tồn tại nhưng cần tập test đủ tốt, vì nếu tập test thiên lệch thì prompt sẽ bị tối ưu theo điểm số chứ không theo nhu cầu thật.

### 6.4 Eval offline và validate lúc chạy khác nhau

Lab 2 có `jsonschema.validate` và sửa tối đa một lần. Đó là **kiểm tra runtime trên từng output**, bảo vệ từng request. Eval là **kiểm tra offline trên cả tập**, quyết định template có đáng ship không. Hai lớp bổ sung nhau, giống unit test (trước khi deploy) và health check (khi đang chạy).

**[ngoài tài liệu]** Vòng khép kín: lỗi thật ở production (validate fail, user phàn nàn) nên được thêm vào tập test, để lần sau eval bắt được loại lỗi đó trước khi deploy.

## 7. Câu hỏi ôn tập và câu trả lời đã chỉnh

**1. Tại sao "đã thử 5 input và đều ổn" vẫn là Option 2?**
- Các input do chính dev chọn nên thiên về happy case và những ca dev đã nghĩ tới; edge case thật là ca dev chưa nghĩ tới.
- **[ngoài tài liệu]** 5 lần đạt không cho ra một con số. Nếu prompt hỏng 10% số lần thì xác suất 5 lần đều qua là 0.9⁵ ≈ 59%. Với 5/5 đạt chỉ có thể nói tỉ lệ lỗi thực tế không vượt quá khoảng 45% (**cận trên một phía**, mức tin cậy 95%). Nếu dùng khoảng tin cậy hai phía 95% thì cận trên là khoảng 52%.

**2. Engineering và evaluation khác nhau ở câu hỏi nào?**
- Engineering: viết thế nào cho tốt hơn. Evaluation: có thật sự tốt hơn không, tốt hơn bao nhiêu, và có làm hỏng thứ đang chạy tốt không (regression).

**3. Eval cho 1.00 trên mọi phiên bản thì biết gì, không biết gì?**
- Biết: trên tập test này mọi ca đều đạt.
- Không biết: (a) prompt có tốt với input ngoài tập không; (b) phiên bản nào tốt hơn, vì điểm chạm trần nên eval mất khả năng phân biệt (như 4 model trong `bench_models.py`); (c) grader có đúng không, vì grader quá dễ tính hoặc có bug cũng cho 1.00.
- Cách xử lý: thêm test khó hơn, kiểm tra tay vài ca xem grader chấm có đúng không.

**4. Vì sao chạy nhiều lần cho cùng một input? (Lab 2)**
- Để phân biệt **ổn định** với **may mắn**, vì model không tất định.
- Kịch bản A: cùng yêu cầu, hai lần chạy cho 3 vòng, 3282 token và 4 vòng, 4662 token (kết quả cuối giống nhau, chi phí lệch khoảng 40%).
- Kịch bản D (ví dụ về hậu quả của dao động): **thực tế quan sát được** (LAB2.md) là `delete_message` chạy ở vòng cuối được phép (vòng 2), rồi vòng lặp dừng, model không có lượt báo lại, và tin đã bị xoá thật; cả hai lần chạy D đều như vậy. **Biến thể chưa quan sát [ngoài tài liệu]:** nếu model đi đường dài (như lần chạy lại của kịch bản A: tìm, lọc, xoá) thì giới hạn 2 vòng có thể cắt trước khi xoá và trạng thái cuối khác hẳn. LAB2.md cũng ghi biến thể này như một suy luận, chưa tái hiện được. Ý chính vẫn đúng: một lần chạy có thể gây hiểu nhầm về hành vi của cấu hình.
- Báo cáo bằng **tỉ lệ đạt trên n lần chạy** (ví dụ 18/20), không phải đúng hay sai một lần.

**5. Ai viết prompt, ai đưa input, eval chạy ở pha nào?**
- Dev viết prompt template; người dùng chỉ đưa input điền vào chỗ trống. (Chọn template theo loại yêu cầu là **routing**, một mẫu workflow thêm vào chứ không phải mặc định; bước phân loại đó cũng là một prompt cần eval.)
- Eval chạy ở **pha dev, offline**, chạy lại mỗi khi đổi prompt hoặc đổi model, không chạy lúc phục vụ người dùng.

**6. Tình huống: service phân loại ticket có tập test 30 ca do dev viết, mỗi ca chạy một lần, đạt 30/30. Nói gì với đồng nghiệp muốn ship ngay?**
- Không tin con số, vì người viết tập test cũng là người viết prompt nên chung điểm mù, tập dễ toàn happy case (giống dev tự test rồi bị QC bắt bug). Cần một vòng eval với tập test của một role khác.
- Bổ sung thêm một điểm mà câu trả lời đầu chưa nêu: mỗi ca chỉ chạy một lần, nên chưa biết kết quả có ổn định không (xem câu 4).

Cách làm tập test độc lập **[ngoài tài liệu]**:
- **Nguồn:** QA (cố tình viết input lạ), chuyên gia nghiệp vụ (biết ticket thật trông thế nào), dữ liệu thật như ticket cũ và log production (đa dạng nhất).
- **Nhãn đáp án:** người hiểu nghiệp vụ xác nhận. Dev tự gắn nhãn thì định kiến cũ vẫn còn, chỉ chuyển từ input sang nhãn.
- **Phủ:** input rỗng, quá ngắn, quá dài; sai chính tả, trộn tiếng Việt và tiếng Anh; ticket nhiều ý; ticket ngoài phạm vi nhãn; nội dung giống chỉ dẫn ("bỏ qua các quy tắc trên", input không đáng tin).
- **Báo cáo:** điểm tách theo nhóm, không chỉ một số tổng. Ví dụ 95% tổng nhưng 40% ở nhóm "nhiều ý" lộ ra điểm yếu mà trung bình che mất.
- **Tập của dev:** vẫn giữ làm smoke test hoặc một phần tập regression; chỉ là không đủ để quyết định ship.

Câu trả lời mẫu: "30/30 chứng minh prompt xử lý tốt các ca mình đã nghĩ tới, mỗi ca một lần. Chưa biết với input ngoài tập, và chưa biết kết quả có ổn định không. Cần thêm một vòng eval với tập từ QA hoặc dữ liệu thật, chạy mỗi ca nhiều lần, trước khi ship."

## 8. Eval workflow 5 bước

Bài học nói có nhiều cách ghép workflow và nhiều công cụ (open source lẫn trả phí); module này sẽ **tự dựng workflow riêng**, nên các bài sau sẽ có code.

| Bước | Làm gì | Ví dụ trong bài |
|---|---|---|
| 1. Draft a Prompt | Viết prompt template có chỗ trống cho input | `"Please answer the user's question: {question}"` |
| 2. Create an Eval Dataset | Danh sách input mẫu sẽ điền vào chỗ trống; tự viết tay hoặc nhờ Claude sinh; thực tế có thể là hàng chục đến hàng nghìn bản ghi | 3 câu: "What's 2+2?", "How do I make oatmeal?", "How far away is the Moon?" |
| 3. Feed Through Claude | Điền từng input vào template, gửi cho Claude, lấy response | 3 câu trả lời tương ứng |
| 4. Feed Through a Grader | Grader nhìn cả câu hỏi lẫn câu trả lời, cho điểm (thường thang 1–10) | 10, 4, 9, trung bình (10+4+9)/3 = 7.66 |
| 5. Change Prompt and Repeat | Sửa prompt, chạy lại toàn bộ để so điểm | Thêm "Answer the question with ample detail": 7.66 thành 8.7 |

Kết luận của bài: so các phiên bản bằng số, chọn bản điểm cao nhất hoặc lặp tiếp; bỏ việc đoán trong prompt engineering.

Ánh xạ .NET **[ngoài tài liệu]**: bước 1 là code cần test; bước 2 là test fixture; bước 3 là chạy hệ thống cần test; bước 4 là assertion nhưng trả ra điểm chứ không phải pass hoặc fail; bước 5 là sửa code rồi chạy lại cả suite (regression).

### 8.1 `bench_models.py` đã đi qua cả 5 bước **[ngoài tài liệu]**

| Bước | `bench_models.py` |
|---|---|
| Dataset | 3 prompt `math`, `json`, `bullets` |
| Feed Claude | 3 lần × 4 model |
| Grader | Code kiểm đúng sai (11:20, JSON khớp, 3 dòng `- `) |
| Đổi và lặp lại | Đổi model (ở bài này là đổi prompt) |

Khác biệt: grader ở bài này cho điểm chất lượng 1–10, còn grader của `bench_models.py` kiểm đúng sai bằng code. Bài học chưa nói grader chạy bằng gì.

### 8.2 Hai loại grader **[ngoài tài liệu]**

| | Grader bằng code | Grader bằng model (điểm 1–10) |
|---|---|---|
| Hợp với | Đáp án đúng sai kiểm được bằng luật: số, JSON, định dạng | Chất lượng mềm: độ đầy đủ, giọng điệu, độ hữu ích |
| Ưu | Rẻ, ổn định | Chấm được thứ luật không chấm được |
| Nhược | Không chấm được chất lượng mềm; grader quá khắt khe (issue #15, #16) | Tốn thêm lần gọi (khoảng 2N lần cho N ca), cũng dao động, cần tiêu chí rõ |

**Tiêu chí chọn: đáp án có kiểm được bằng luật không?** Nếu có thì dùng code; nếu không thì dùng model kèm barem rõ.

Cách nhớ bằng phép so sánh với chấm điểm (của mình):
- **Toán = grader bằng code.** Đáp án đúng chỉ có một, kiểm được bằng luật. Ví dụ phân loại ticket vào 3 nhãn.
- **Văn = grader bằng model.** Chấm theo tiêu chí (không lạc đề, đủ ý, đa dạng, hiểu bài), không có một đáp án duy nhất. Ví dụ tóm tắt văn bản dài, câu oatmeal.

Hai chỗ chỉnh cho phép so sánh này:
- "Toán không có biến thể" đúng với *đáp án*, chưa đúng với *cách trình bày*: `11:20`, `11h20`, có hoặc không kèm giải thích. Grader bằng code phải **chuẩn hoá** trước khi so (đúng bài học của issue #15 và #16). Chấm lập luận theo bước (bài chứng minh) cần barem, tức grader bằng model.
- Chấm Văn dao động giữa các giám khảo, nên grader bằng model cũng dao động. Cách giảm: viết **barem rõ** (thế nào là 9, thế nào là 4); chấm nhiều lần lấy trung bình; đối chiếu với điểm do người chấm vài bài mẫu; để ý thiên vị (người và model đều dễ mến câu trả lời dài).
- **Grader lai** (thực tế hay dùng): code kiểm ràng buộc cứng (định dạng, độ dài, JSON hợp lệ), model kiểm phần mềm (đủ ý, đúng giọng). Output bị code loại thì khỏi tốn lần gọi grader bằng model.

### 8.3 Ba điều cần đọc phê phán trong ví dụ

1. **7.66 sang 8.7 trên 3 câu hỏi chưa đủ để kết luận v2 tốt hơn.** Chênh có thể chỉ là dao động (model sinh và grader đều không tất định). Cần tập lớn hơn, chạy nhiều lần, so điểm từng ca. (Số học: 23/3 = 7.666, slide cắt thành 7.66, làm tròn là 7.67; không ảnh hưởng ý.)
2. **Điểm có thể tăng mà prompt không tốt hơn.** "Ample detail" làm câu trả lời dài hơn; grader bằng model có xu hướng thiên vị câu dài. Với "What's 2+2?" thì "ample detail" vô nghĩa. Cần tiêu chí chấm rõ (slide cho oatmeal 4 điểm mà không nói vì sao).
3. **Điểm trung bình che mất chi tiết.** Không biết câu nào yếu. Phải xem điểm từng ca và đọc output các ca điểm thấp ("review outputs for errors" ở slide bài 1), và nên yêu cầu grader trả kèm lý do.

### 8.4 Điều kiện để so hai phiên bản hợp lệ

- Cùng **dataset**, cùng **grader** (kể cả sửa barem cũng làm điểm không so được), cùng **model**.
- Mỗi lần chỉ đổi **một thứ** trong prompt, để cô lập nguyên nhân. v2 trong ví dụ chỉ thêm một câu nên làm đúng điều này.
- Chạy nhiều lần, đọc điểm từng ca.

### 8.5 Dataset do Claude sinh

Slide nói dataset có thể do Claude sinh. Nhanh và đủ số lượng, nhưng **[ngoài tài liệu]** Claude có thể chung điểm mù với prompt cũng do Claude viết (giống dev tự test, mục 7 câu 6). Nên trộn với dữ liệu thật hoặc tập từ người khác, và xem lại tay một mẫu. Lặp quá nhiều vòng trên **cùng một tập** thì prompt dần bị tối ưu cho đúng tập đó; nên giữ riêng một tập chưa dùng để kiểm tra lần cuối.

## 9. Câu hỏi ôn tập bài workflow và câu trả lời đã chỉnh

**1. Vì sao cùng dataset, và đổi một thứ mỗi lần?**
- Điểm chỉ có nghĩa so với một dataset cụ thể; đổi dataset thì mỗi phiên bản là một phép đo riêng, không so được.
- Đổi một thứ để cô lập nguyên nhân (thí nghiệm có kiểm soát: một biến đổi, mọi thứ khác giữ cố định). Đổi ba thứ mà điểm tăng thì không biết thứ nào có tác dụng, một thứ giúp và một thứ làm hỏng có thể bù trừ nhau.

**2. v1 7.66, v2 8.7 trên 3 câu: kết luận gì, làm gì thêm?**
- Chỉ nói được "v2 có dấu hiệu tăng", chưa kết luận v2 tốt hơn.
- Lưu ý lý do: không phải "không biết đã đổi gì" (v2 chỉ đổi đúng một câu) mà là **không biết chênh lệch có thật hay chỉ là dao động**.
- Cần thêm: tập lớn và đa dạng hơn, chạy nhiều lần, so điểm từng ca.

**3. Oatmeal 4 điểm, chỉ có điểm trung bình thì thiếu gì?**
- Điểm trung bình che từng ca nên không biết cải tiến có đánh trúng chỗ yếu không. Cần: điểm từng ca, nội dung câu trả lời bị điểm thấp, và lý do grader chấm thấp (yêu cầu grader giải thích).

**4. Grader bằng code hay bằng model hợp với tác vụ nào?**
- Xem mục 8.2 (ánh xạ Toán và Văn).
- Bài tập nhỏ: phân loại ticket 3 nhãn dùng code; tóm tắt văn bản dài dùng model (có thể lai: code kiểm độ dài, model kiểm giữ ý chính).

**5. Hai cách để điểm v2 tăng mà prompt không tốt hơn?**
- **Dao động** giữa các lần chạy (thử lại cũng cho điểm khác).
- **Đổi grader** giữa hai phiên bản (ví dụ từ code sang model, hay sửa barem); quy tắc rộng hơn: grader phải cố định.
- **Thiên vị của grader**, ví dụ mến câu dài (chưa nêu ban đầu).
- **Đổi dataset** giữa hai lần chạy.

## 10. Còn lại và việc cần kiểm tra

- Mới có khung 5 bước (mục 8), chưa có code. Các bài sau sẽ dựng workflow bằng code: cần xem cách tạo dataset (liên quan mục 7 câu 6: nguồn tập test, ai gắn nhãn), cách chạy hàng loạt, cách viết grader bằng model và barem.
- Các điểm ở mục 8.2 và 8.3 về thiên vị độ dài, chấm nhiều lần, đối chiếu với điểm của người là kiến thức ngoài tài liệu, cần đối chiếu khi học phần grader.
- Các con số ở mục 7 câu 1 (0.9⁵ ≈ 59%, cận trên một phía khoảng 45%, hai phía khoảng 52% cho 0 lỗi trên 5 lần) đã tính lại bằng Python ngày 2026-11-23: 0.590, 0.451, 0.522.
- Kiểm tra docs: công cụ cải thiện prompt của Anthropic Console (mục 6.3) có hiện hành và hoạt động thế nào.
- Chưa làm: thêm test khó hơn và nhiều lần lặp hơn cho `bench_models.py` để điểm không còn 1.00 cho mọi model.
