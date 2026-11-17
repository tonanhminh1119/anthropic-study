# Notes Week 3 Day 2: Prompt Caching và RAG

Nguồn: tài liệu khóa học (hai phần "Prompt caching: paying once for reusable requests" và "Retrieval-augmented generation", nối tiếp phần "Context cost" của MCP, xem [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md)). **[docs]** = đối chiếu tài liệu API hiện hành qua skill `claude-api` (file `shared/prompt-caching.md`, cache ngày 2026-11-03; đọc 2026-11-17). **[ngoài tài liệu]** = suy luận hoặc kiến thức bổ sung.

Hai phần cùng giải một bài toán: **đừng trả tiền (và chiếm context) cho cùng một nội dung nhiều lần**. Caching giảm chi phí **xử lý lại** nội dung giống hệt; RAG giảm **lượng** nội dung phải đưa vào.

## 1. Prompt caching

### 1.1 Cơ chế (theo tài liệu khóa học)
- Mỗi request xử lý lại toàn bộ input từ đầu, kể cả phần giống hệt request trước, nên bạn trả tiền lại mỗi lần (MCP tool definitions là ví dụ: khối lớn, ổn định).
- Caching lưu **kết quả xử lý của một tiền tố ổn định**. Request đầu **ghi** tiền tố vào cache; request sau gửi nội dung **giống hệt** tới cùng điểm thì dùng lại với chi phí thấp hơn nhiều.
- **Phải khớp chính xác:** đổi một ký tự trước điểm cache là cache đó mất, phải ghi lại. Vì vậy ứng viên tốt nhất là phần ít đổi: system prompt dài, bộ tool definition lớn, tài liệu tham chiếu bạn hỏi nhiều câu.
- **Bật bằng cách đánh dấu breakpoint** (không có công tắc toàn cục): Messages API thêm field `cache_control` kiểu `ephemeral` vào **block cuối** muốn cache; cache mọi thứ **tới và gồm** block đó. Tối đa **4** breakpoint.
- Thứ tự xử lý cố định: **tools, system prompt, messages**. Breakpoint sau tools thì cache tool definitions mà phần messages vẫn động.
- **Thời hạn:** mặc định **5 phút** kể từ lần đọc cuối (mỗi lần đọc đặt lại đồng hồ). Opt-in **1 giờ** bằng `ttl: "1h"`. 5 phút hợp với hội thoại qua lại; 1 giờ hợp với khoảng nghỉ dài (agent dừng giữa các bước). Hết hạn trước request kế thì bạn **trả lại chi phí ghi mà không được lợi ích đọc**.
- **Ngưỡng tối thiểu:** prompt ngắn dưới ngưỡng thì **không cache** dù có đặt breakpoint.

### 1.2 Đối chiếu với tài liệu API hiện hành **[docs]**

| Ý trong tài liệu khóa học | Đối chiếu |
|---|---|
| Không có công tắc toàn cục, phải đánh dấu breakpoint | **Đúng ở mức tài khoản, nhưng có caching tự động cấp request:** field `cache_control: {type: "ephemeral"}` ở **top-level** của `messages.create()` tự đặt breakpoint trên block cuối cùng cache được và dời theo khi hội thoại dài ra. Nó chiếm 1 trong 4 slot. Hợp hội thoại nhiều lượt; dùng breakpoint tường minh khi prompt kết thúc bằng nội dung riêng của từng request hoặc các phần đổi với tần suất khác nhau |
| Tối đa 4 breakpoint | Khớp |
| Thứ tự tools, system, messages | Khớp |
| 5 phút mặc định, `ttl: "1h"` opt-in | Khớp. Chi tiết thêm: đọc cache **không tốn thêm** và đặt lại đồng hồ; thời hạn tính từ **lúc bắt đầu** request ghi hoặc đọc, nên thời gian sinh output cũng ăn vào 5 phút |
| Ngưỡng tối thiểu **1.024 token cho hầu hết model hiện tại** | **Lệch / phụ thuộc model.** 512 trên các model mới nhất (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable/Mythos 5.x; nguồn ghi "kiểm tra docs trước khi dựa vào"), 1.024 trên Opus 4.8 / Sonnet 5 / Sonnet 4.6, 2.048 trên Opus 4.7, 4.096 trên Opus 4.6 / 4.5 / Haiku 4.5. **Không đơn điệu** theo thế hệ. Prompt dưới ngưỡng thì **im lặng không cache**: không có lỗi, chỉ có `cache_creation_input_tokens: 0` |

**Chi phí [docs]:** đọc cache ≈ **0,1×** giá input (0,05× trên Opus 5.5 và Sonnet 5.5; 0,025× trên Fable 5.2); ghi cache **1,25×** (TTL 5 phút) hoặc **2×** (TTL 1 giờ). Hòa vốn với 5 phút: 2 request (1,25 + 0,1 = 1,35× so với 2× không cache); với 1 giờ: ít nhất 3 request. Chọn TTL theo **khoảng cách giữa các lần bắt đầu request** dùng chung tiền tố: dưới 5 phút dùng 5 phút (mỗi request tự làm mới); 5-60 phút mới đáng dùng 1 giờ.

### 1.3 Kiểm chứng cache có chạy không **[docs]**
- Đọc `usage` của response: `cache_creation_input_tokens` (đã ghi), `cache_read_input_tokens` (đọc từ cache), `input_tokens` (**chỉ phần không cache**; tổng prompt = cả ba cộng lại).
- `cache_read_input_tokens` bằng 0 qua nhiều request có tiền tố giống nhau nghĩa là có **"silent invalidator"**: `datetime.now()` hoặc UUID trong system prompt, `json.dumps` không `sort_keys`, danh sách tool thay đổi theo người dùng, v.v.
- Lỗi tốn kém nhất là **im lặng**: request vẫn thành công, hóa đơn cao hơn. Kiểm tra lại sau mỗi lần sửa code dựng prompt, hoặc đặt một kiểm tra thường trực (request thứ hai giống hệt phải có `cache_read_input_tokens > 0`).
- Nguyên tắc thiết kế: phần **ổn định ở trước**, phần **biến động ở sau** breakpoint cuối; **đừng đổi tool hay model giữa hội thoại** (tool render ở vị trí đầu; cache gắn theo model).

### 1.4 Nối với MCP và Claude Code
- **[docs]** Bộ tool definition là khối lớn, ổn định, đúng loại nên cache; đó cũng là lý do bài học đặt caching ngay sau "context cost" của MCP.
- **[ngoài tài liệu, chưa kiểm chứng]** Server MCP có thể đổi danh sách tool khi đang kết nối (`list_changed`). Nếu danh sách tool gửi đi thay đổi giữa hội thoại thì theo nguyên tắc ở 1.3 tiền tố cache có thể bị ảnh hưởng; mình chưa biết Claude Code xử lý thế nào (tool search có thể giảm ảnh hưởng này).
- **[ngoài tài liệu]** Mình nhớ Claude Code tự áp dụng caching (bạn không tự đặt `cache_control`), nhưng chưa xác nhận trong docs; ở API trực tiếp thì **bạn phải chủ động**.
- Ý tưởng thực hành (chưa làm): thêm đo `cache_read_input_tokens` vào script bench trong repo để thấy caching hoạt động hoặc không.

## 2. RAG (Retrieval-Augmented Generation)

### 2.1 Vấn đề và ý tưởng
- Model đọc **mọi thứ trong cửa sổ context** ở mỗi request. Nạp hết tài liệu từ đầu thì tốn context, còn ít chỗ cho công việc.
- RAG: lưu tài liệu **ngoài** context, **tìm phần liên quan nhất** với yêu cầu hiện tại, và chỉ đưa phần đó vào lúc request. Model trả lời từ **lát cắt** được lấy về, không phải cả thư viện.

### 2.2 Hai dạng

| | Classical RAG | Agentic search |
|---|---|---|
| Làm việc nặng khi nào | **Trước**: chia tài liệu thành chunk, biến mỗi chunk thành **embedding** (bộ số mô tả ý nghĩa), lưu vào database | **Không lập chỉ mục trước** |
| Khi có câu hỏi | Biến câu hỏi thành embedding cùng loại, tìm các chunk có số gần nhất | Model tự xác định cần gì rồi **đi lấy**: tìm nguồn trực tiếp, đọc tài liệu theo nhu cầu, lấy kết quả dần khi tác vụ diễn ra |
| Hình dung | Thủ thư đã đọc hết sách và viết thẻ tóm tắt từng chương từ trước khi thư viện mở cửa | Nhà nghiên cứu tự đi tìm câu trả lời |

- Cả hai làm cùng một việc cơ bản (tìm lát cắt liên quan rồi sinh câu trả lời từ đó); khác nhau ở **thời điểm tìm**: classical khớp với chỉ mục dựng sẵn, agentic tìm ngay lúc cần.
- **Ví dụ bạn đã gặp agentic search:** (1) Claude Code với nhiều MCP server không nạp hết tool definition mà chỉ nạp tool cần; (2) Claude.ai Projects khi knowledge base lớn hơn cửa sổ thì chỉ lấy các đoạn liên quan nhất.
- **[docs]** Lưu ý: tool search ở Messages API có hai biến thể là **regex** và **BM25** (`tool_search_tool_regex_20251119`, `tool_search_tool_bm25_20251119`), tức tìm theo **từ khóa**, không phải embedding. Nên "retrieval" không đồng nghĩa với "embedding" hay "vector database".

### 2.3 Hai tính chất cần hiểu trước khi dùng
1. **Mở rộng được (scale):** nguồn lớn lên mà chi phí mỗi request **gần như phẳng**, vì model chỉ nhận lát cắt liên quan. Kho hàng nghìn tài liệu, một câu hỏi vẫn lấy về lượng văn bản tương đương.
   - **[ngoài tài liệu]** "Phẳng" chỉ nói về lượng văn bản gửi cho model. Vẫn có chi phí khác: dựng embedding và chỉ mục (classical, và phải cập nhật khi nguồn đổi), hoặc nhiều lượt gọi tool và độ trễ cao hơn (agentic).
2. **Chỉ tốt bằng thứ nó tìm được:** model suy luận trên lát cắt nhận về. Nếu bước tìm bỏ sót tài liệu cần thiết thì model **không bao giờ thấy nó**. Vì vậy cách tổ chức nguồn rất quan trọng: tên mơ hồ (`notes_final_v3.pdf`) khó tìm hơn tên mô tả (`Q3 refund policy, updated August 2024`); nhóm các file liên quan lại cũng giúp.

### 2.4 Mối nối với những gì đã học
- Cùng một nguyên tắc ở nhiều nơi: **thứ được tìm phải tự mô tả rõ**. Với skill là `description` (quy tắc portability số 1, xem [NOTES_W3D2_Packaging_Workflows.md](NOTES_W3D2_Packaging_Workflows.md)); với MCP là server instructions và mô tả tool (từ khóa tìm kiếm nên ở đầu, xem [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) mục 3); với tài liệu là tên file.
- Nạp 3 mức của skill (metadata luôn có, body khi kích hoạt, file phụ khi cần) và tool search của MCP đều là **agentic retrieval** thu nhỏ.

### 2.5 Caching hay RAG? **[ngoài tài liệu]**

| | Prompt caching | RAG |
|---|---|---|
| Giải quyết | Trả tiền lại để **xử lý lại cùng nội dung** | **Quá nhiều nội dung** cho cửa sổ context |
| Nội dung vẫn vào context? | Có, toàn bộ (rẻ hơn khi đọc cache) | Chỉ lát cắt liên quan |
| Hợp khi | Một khối tham chiếu vừa phải, ổn định, hỏi nhiều lần | Kho lớn, mỗi câu hỏi chỉ cần một phần nhỏ |
| Rủi ro | Cache bị vô hiệu im lặng | Bước tìm bỏ sót tài liệu cần |

Hai cách bổ sung nhau: cache phần cố định (system prompt, tool definitions), RAG cho phần nội dung thay đổi theo câu hỏi.

## 3. Còn lại và việc cần kiểm tra

- Ngưỡng cache tối thiểu cho các model bạn dùng trong repo (Sonnet 5.5, Haiku 5.5): nguồn ghi "kiểm tra docs prompt caching trước khi dựa vào"; xác nhận trước khi tin con số 512.
- Thử thực nghiệm: gửi hai request giống hệt có `cache_control` và xem `usage` (và một trường hợp prompt dưới ngưỡng để thấy việc không cache im lặng).
- Chưa rõ: khóa học không nói dùng mô hình embedding nào cho classical RAG.
- Kiểm tra xem Claude Code xử lý `list_changed` của MCP và cache thế nào (mục 1.4).
