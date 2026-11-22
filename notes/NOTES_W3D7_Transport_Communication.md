# Notes Week 3 Day 7: MCP nâng cao, Transport và Communication (message, stdio, Streamable HTTP, state)

Nguồn: tài liệu khóa học phần Advanced MCP, gồm 5 đoạn: "JSON message types", "The STDIO transport", "The StreamableHTTP transport", "StreamableHTTP in depth", "State and the StreamableHTTP transport", kèm các slide minh họa (chưa lưu vào `archive/`). Bản đầu chưa đối chiếu docs Claude Code hay spec MCP; sau đó đã bổ sung theo một bản review ngoài (do bạn gửi) và tra cứu trang spec 2026-07-28 (ngày 2026-11-22). Mình chưa tự đọc toàn văn spec. **[ngoài tài liệu]** = suy luận hoặc kiến thức bổ sung của mình, không phải của khóa học. **[spec]** = đã đối chiếu spec MCP theo cách vừa nêu. **[kiểm tra]** = chỗ cần đối chiếu lại với spec hoặc thực hành.

Liên hệ với note trước: [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) mục 5 đã có bảng transport (stdio, HTTP, SSE legacy) và cú pháp `claude mcp add`; mục 7 có scope; mục 6.1 có MCP connector của Messages API. [NOTES_W3D3_Enterprise_Integration.md](NOTES_W3D3_Enterprise_Integration.md) mục 9 (ý 6) tóm tắt "transport và scope". Note này đi sâu vào **tầng giao thức**: message trông thế nào, đi qua kênh nào, và vì sao HTTP khó hơn stdio.

## 1. Message trong MCP

### 1.1 Tất cả là message JSON

- Mọi giao tiếp giữa MCP client và MCP server là **message JSON**. Ví dụ trong khóa học: client gửi `tools/call` với `name: "add"`, `arguments: {a: 5, b: 3}`; server trả `content: [{type: "text", text: "8"}]` và `isError: false`.
- **[ngoài tài liệu]** Khuôn `"jsonrpc": "2.0"` trong ví dụ là **JSON-RPC 2.0**. Khóa học không gọi tên chuẩn này, nhưng MCP đứng trên nó. Đây là format **duy nhất** ở mức giao thức: dữ liệu nhị phân như ảnh cũng được mã hóa base64 **bên trong JSON**.
- **Transport chỉ đổi cách "gói"** message (stdio: mỗi message một dòng; HTTP: body của POST hoặc sự kiện SSE), không đổi nội dung. Cách nhớ: **JSON-RPC là nội dung thư, transport là phong bì**. Tự viết transport mới được, miễn là vẫn chở đúng message JSON-RPC.
- **Spec là nguồn chuẩn**: repo `modelcontextprotocol/modelcontextprotocol` định nghĩa cách client và server hành xử và mọi message hợp lệ. Nó tách khỏi các repo SDK (Python, TypeScript). Kiểu message viết bằng TypeScript **chỉ để mô tả cấu trúc dữ liệu**, không phải code chạy; server vẫn viết bằng .NET hay Python được.

### 1.2 Hai nhóm message

| | Request → Result | Notification |
|---|---|---|
| Có `id` | Có | Không |
| Có phản hồi | Có, luôn | Không |
| Dùng để | Hỏi hoặc ra lệnh | Báo sự kiện |
| Ví dụ trong bài | Call Tool, List Prompts, Read Resource, Initialize | Progress, Logging Message, Tool List Changed, Resource Updated |

- Request và Result ghép với nhau bằng **cùng một `id`**. Nhờ vậy gửi nhiều request cùng lúc vẫn ghép đúng khi kết quả về lộn thứ tự.
- Cách nhận biết message **[ngoài tài liệu]**: tên bài là "loại message", còn trên đường truyền phân biệt bằng nội dung JSON:

| JSON có | Là gì |
|---|---|
| `method` + `id` | **Request** (chờ phản hồi) |
| `method`, không `id` | **Notification** |
| `result` hoặc `error` + `id` | **Response** của một request trước đó |

- Mỗi bên có không gian `id` **riêng** (id 1 của client không đụng id 1 của server khi server gửi request ngược lại).
- Analogy .NET **[ngoài tài liệu]**: Request giống `Invoke` (chờ giá trị trả về), Notification giống `Send` (gửi rồi thôi).

### 1.3 Tên `method` trên đường truyền **[ngoài tài liệu]**, khớp spec theo bản review

Sơ đồ khóa học dùng tên kiểu TypeScript; tên thật trong JSON là `method`:

| Tên trong bài | `method` trên đường truyền |
|---|---|
| Initialize | `initialize` |
| Initialized Notification | `notifications/initialized` |
| Call Tool | `tools/call` |
| List Tools (bài không liệt kê) | `tools/list` |
| List Prompts | `prompts/list` |
| Read Resource | `resources/read` |
| Create Message (sampling) | `sampling/createMessage` |
| List Roots | `roots/list` |
| Progress | `notifications/progress` |
| Logging Message | `notifications/message` |
| Cancelled | `notifications/cancelled` |
| Tool List Changed | `notifications/tools/list_changed` |
| Resource Updated | `notifications/resources/updated` |

### 1.4 Hai loại lỗi khác nhau **[ngoài tài liệu]**

- **Lỗi giao thức** (method không tồn tại, tham số sai): trả object `error` của JSON-RPC.
- **Lỗi trong lúc chạy tool**: vẫn là một Result bình thường nhưng đặt `isError: true`. Đó là lý do ví dụ có field `isError`. Model thấy được lỗi và tự xử lý, không làm hỏng kết nối.

### 1.5 Hai chiều

MCP là giao thức **hai chiều**: client gửi request cho server, và **server cũng chủ động gửi request hoặc notification cho client**. Đây là ý quan trọng nhất của phần này, vì nó quyết định việc chọn transport (mục 5 và 6).

## 2. MCP đứng ở đâu: ai là client, ai là server

### 2.1 "Client" và "server" chỉ có nghĩa trên một kết nối

Một app có thể là server ở kết nối này và client ở kết nối khác (ASP.NET app là server với trình duyệt, client với SQL Server). Claude Code nằm giữa **hai kết nối khác nhau**:

```
                  (1) Claude API                 (2) MCP
 Server của   <------------------>  Claude Code  <---------->  MCP server
 Anthropic       Claude Code là                  Claude Code là   (GitHub, Linear,
 (Messages API)  API CLIENT                      MCP CLIENT        script của bạn)
```

| | Kết nối (1) | Kết nối (2) |
|---|---|---|
| Hai đầu | App ↔ **server Anthropic** | App ↔ **MCP server** |
| Giao thức | Messages API (HTTP, `messages`, `tools`...) | MCP (JSON-RPC) |
| Ai là server | Anthropic | Server bạn hoặc bên thứ ba dựng |
| Ai là client | App/Claude Code | Phần "MCP client" bên **trong** app |

### 2.2 Vai trò từng thành phần

| Thành phần | Vai trò | Ghi chú |
|---|---|---|
| **Server Anthropic** | Cung cấp **model** (suy luận, quyết định gọi tool nào) | Không chạy tool, không biết MCP server (trừ MCP connector) |
| **MCP** | **Giao thức chuẩn** để app tiếp cận tài nguyên và khả năng bên ngoài (hành động, dữ liệu, mẫu chỉ dẫn) | Độc lập với Anthropic và model. Đầu client của nó nằm **trong app**; đầu server là tiến trình riêng |
| **MCP server** | **Cổng/adapter** đứng trước tài nguyên thật (GitHub API, DB) | Thường không phải nơi lưu dữ liệu |
| **App (host)** | **Điều phối và gác cổng**: gọi cả model lẫn MCP để hoàn thành một task | Nơi đặt permission rule, hook, scope (W3D1, W3D2 mục 7 và 8) |

> Server Anthropic cho **bộ não** (model), MCP là **đường nối** tới tài nguyên bên ngoài, MCP server là **cổng** trước tài nguyên đó, app là **người điều phối và gác cổng**.

- **Model không nói MCP.** Model chỉ trả block `tool_use`; app dịch thành `tools/call` gửi tới MCP server, rồi đưa kết quả lại cho model dưới dạng `tool_result`.
- **Phép thử:** bỏ MCP thì app vẫn gọi được Claude (tool tự định nghĩa trong mảng `tools`). Đổi sang LLM khác thì MCP server vẫn dùng được. Cả hai cho thấy MCP không thuộc "đường đi tới Anthropic".
- **Ngoại lệ**: MCP connector của Messages API ([NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) mục 6.1): server Anthropic tự đóng vai **MCP client** và kết nối thẳng tới MCP server qua URL công khai. Vì vậy server phải có HTTPS công khai và stdio không dùng được.
- Analogy **[ngoài tài liệu]**: MCP giống ODBC/ADO.NET provider, một chuẩn để app nói chuyện với nhiều nguồn dữ liệu theo cùng một cách.

### 2.3 Flow một lượt tool call (stdio)

```
Lúc kết nối (một lần, trước mọi task):
 0. App khởi chạy MCP server như tiến trình con.
    Bắt tay 3 message, rồi gửi tools/list để biết server có tool nào.
    Danh sách này được đưa cho model.

Mỗi task:
 1. User giao task cho app.
 2. App gửi prompt + danh sách tool lên Claude API.
 3. Model trả block tool_use.
 4. App (MCP client) GHI tools/call vào STDIN của server.
 5. Server ĐỌC từ stdin, chạy tool.
 6. Server GHI Call Tool Result ra STDOUT.
 7. App ĐỌC từ stdout của server, ghép bằng id với request ở bước 4.
 8. App gửi kết quả về Claude API dưới dạng tool_result.
 9. Model dùng kết quả để trả lời tiếp (hoặc gọi tool khác, lặp lại 3 đến 8).
```

Bước 3 và 8 là Claude API; bước 4 đến 7 là MCP. Kết quả MCP **chưa phải câu trả lời cho user**: app phải đưa nó quay lại model.

## 3. Bắt tay và bảng message theo hướng

### 3.1 Bắt tay 3 message

Mọi kết nối MCP phải bắt đầu bằng:

```
Client  --Initialize Request-->        Server
Client  <--Initialize Result---        Server   (server trả capabilities)
Client  --Initialized Notification-->  Server   (client xác nhận, không có phản hồi)
```

Chỉ sau đó mới gửi được `tools/call`, `prompts/list`... Với Streamable HTTP, Initialize Result còn mang header `mcp-session-id` (mục 5.3).

**[ngoài tài liệu]** Trong hai message đầu hai bên **thương lượng capabilities** và phiên bản giao thức. Bên nào không khai báo một capability thì bên kia không được gửi loại message đó. Đây là cơ chế đằng sau câu "hỗ trợ khác nhau giữa các MCP client" ở [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) mục 2.1.

### 3.2 Message theo hướng

| Hướng | Request / Result | Notification |
|---|---|---|
| **Client → Server** | Call Tool, List Prompts, Read Resource, Initialize | Initialized, Cancelled |
| **Server → Client** | **Create Message** (sampling), **List Roots** | Progress, Logging |

- Cặp Request/Result **không cố định hướng**: Create Message Request do server gửi, nên Create Message **Result** do client trả.
- **Server không có model.** Khi cần model, nó nhờ client (Create Message), và client dùng kết nối Claude API của chính nó.
- **[ngoài tài liệu]** Ngoài slide còn: `elicitation/create` (server hỏi thêm người dùng), `ping` (hai chiều), Tool List Changed, Resource Updated, Roots List Changed.

### 3.3 Ví dụ tình huống thực tế

**Request: client → server**

| Message | Tình huống |
|---|---|
| Initialize | Vừa khởi chạy server, bắt tay |
| List Tools **[ngoài tài liệu]** | App hỏi server có tool nào để đưa cho model |
| **Call Tool** | Model muốn tạo issue GitHub, truy vấn DB, cộng 5 + 3 |
| **List Prompts** | Người dùng gõ `/` và app hiện danh sách prompt của server |
| Get Prompt **[ngoài tài liệu]** | Người dùng chọn `/mcp__github__pr_review 456`, app lấy nội dung prompt |
| **Read Resource** | Người dùng gõ `@github:issue://123` để đính kèm issue |

**Request: server → client**

| Message | Tình huống |
|---|---|
| **Create Message** | Server có log dài cần tóm tắt hoặc cần phân loại văn bản, nhờ client gọi LLM |
| **List Roots** | Server filesystem hỏi client cho phép làm việc trong những thư mục nào |
| Elicitation **[ngoài tài liệu]** | Server cần hỏi người dùng chọn repo nào hoặc xác nhận một thao tác |

**Notification: client → server**

| Message | Tình huống |
|---|---|
| **Initialized** | Kết thúc bắt tay, báo "tôi sẵn sàng" |
| **Cancelled** | Tool chạy lâu, người dùng nhấn Esc, client báo server hủy request đó |
| Roots List Changed **[ngoài tài liệu]** | Người dùng mở thư mục project khác |

**Notification: server → client**

| Message | Tình huống |
|---|---|
| **Progress** | Tool import 10.000 dòng, báo "đã được 40%" (cần `progressToken` trong `_meta` của request gốc **[ngoài tài liệu]**) |
| **Logging** | Server báo "đã kết nối DB" hoặc "cảnh báo: sắp chạm rate limit" |
| Tool List Changed | Sau khi đăng nhập hoặc bật plugin, server có thêm tool; client gọi lại `tools/list` (chính là `list_changed` ở W3D2 mục 3) |
| Resource Updated **[ngoài tài liệu]** | Resource client đã đăng ký theo dõi vừa thay đổi |

Slide xếp Cancelled ở phía client. **[spec]** Spec cho phép **cả hai phía** hủy request mình đã gửi; ví dụ phổ biến là client hủy khi người dùng bấm dừng.

## 4. Stdio transport

### 4.1 Cách hoạt động

- **Client khởi chạy MCP server như tiến trình con** trên cùng máy.
- Client ghi message vào **stdin** của server; server ghi message ra **stdout**.
- **Bên nào cũng gửi được bất cứ lúc nào** (hai ống độc lập, mỗi ống một chiều).
- **Chỉ dùng được khi client và server ở cùng máy.** Khớp bảng transport ở W3D2 mục 5 và cái bẫy "stdio trong `.mcp.json` trông như chia sẻ được nhưng không" (W3D2 mục 7, W3D3 mục 9 ý 6).
- Dùng cho phát triển và thử nghiệm. Có thể thử trực tiếp từ terminal: chạy `uv run server.py` rồi dán JSON vào, terminal đóng vai client.

### 4.2 Hai ống và tên stdin/stdout

stdin/stdout **luôn là của tiến trình bị gọi (server)**, không phải của app. Mô hình chính xác là **hai ống một chiều**, mỗi ống có hai đầu:

```
        Phía APP                                     Phía SERVER

   (đầu GHI của app)  ==== Ống A ====>   stdin   (đầu ĐỌC của server)
   (đầu ĐỌC của app)  <==== Ống B ====   stdout  (đầu GHI của server)
```

- "stdin" và "stdout" chỉ là nhãn của hai đầu **phía server**. App dùng hai đầu còn lại.
- stdin/stdout **thật của app** (fd 0 và 1) vẫn nối với terminal của người dùng, không phải hai đầu ống này.
- Đối chiếu .NET (nguồn gây nhầm vì cùng một chữ "input/output" đổi vai theo người nhìn):

| Ở phía app (.NET) | Là đầu nào |
|---|---|
| `process.StandardInput` | Đầu **ghi** của ống A (tiến trình con đọc bằng `Console.ReadLine()`) |
| `process.StandardOutput` | Đầu **đọc** của ống B (tiến trình con `Console.WriteLine()` thì app đọc ở đây) |

> **Client ghi vào stdin của server, đọc từ stdout của server.**

### 4.3 Bốn mẫu giao tiếp

Mọi transport phải làm được bốn mẫu:

| Mẫu | Stdio làm thế nào |
|---|---|
| Client → Server **request** | Client ghi vào stdin |
| Server → Client **response** | Server ghi ra stdout |
| Server → Client **request** | Server ghi ra stdout |
| Client → Server **response** | Client ghi vào stdin |

- Ống **cố định theo hướng**: client → server luôn là stdin, server → client luôn là stdout. **Chỗ làm việc không liên quan đến ống.** Ví dụ sampling: việc gọi LLM do app làm, nhưng Create Message Request vẫn ra stdout của server, và client trả Result bằng cách ghi vào stdin.
- Cùng một ống chở cả request lẫn response, phân biệt bằng **nội dung JSON** (mục 1.2), không bằng ống.
- Stdio là trường hợp **"lý tưởng"**: hai chiều đối xứng, cả bốn mẫu đều làm được. Nó là mốc để so sánh với HTTP.

### 4.4 Lưu ý khi viết server stdio **[ngoài tài liệu]**

- **Không in log ra stdout**: stdout là kênh giao thức, một dòng `print` thừa làm hỏng luồng JSON. Log phải đi qua **stderr** hoặc qua Logging Notification của MCP.
- **Khung message:** mỗi message JSON nằm trên **một dòng**, không chứa xuống dòng bên trong.
- **Kết thúc:** client đóng stdin để báo dừng (nếu server không thoát thì client ép dừng). Tiến trình server sống và chết theo client.
- Ví dụ thử thủ công (minh họa, `protocolVersion` tùy SDK):

```
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
```

Dòng 2 là notification (không `id`, không phản hồi). Dòng 1 và 3 có `id`, result về mang đúng `id` đó.

## 5. Streamable HTTP transport

### 5.1 Là gì và vì sao khó

- Cho phép client nối tới MCP server **chạy ở máy khác** qua HTTP, ví dụ `https://mcp-server.com/mcp`. Khác stdio: không còn tiến trình con, không còn ràng buộc cùng máy, mở ra server công khai cho nhiều người. Trong note W3D2 đây là transport `http` được khuyến nghị.
- **Gốc của hạn chế nằm ở HTTP nói chung, không riêng MCP:**
  - Client → server **dễ**: server có URL cố định.
  - Server → client **khó**: client không có URL cố định (NAT, firewall, không lắng nghe cổng nào), server không biết gọi tới đâu.
- Hình dung với hai ống (**[ngoài tài liệu]**): ở stdio, hai ống tồn tại sẵn suốt phiên. Ở HTTP thường, mỗi cặp request/response là một "ống" ngắn do **client mở**, hết response là đóng, server không còn đường nào để nói trước.
- **Bảo mật khi mở server HTTP** **[spec, theo bản review]**: server Streamable HTTP phải **validate header `Origin`** (chống DNS rebinding), **bind `127.0.0.1`** khi chạy cục bộ, và có **authentication**. Bài chưa nhắc nhưng liên quan trực tiếp khi chuyển từ stdio sang HTTP.

### 5.2 Đối chiếu bốn mẫu: stdio và HTTP thường

| Mẫu | Stdio | HTTP thường |
|---|---|---|
| Client → Server **request** | ✓ | ✓ (client POST tới URL) |
| Server → Client **response** | ✓ | ✓ (trong response của chính POST đó) |
| Server → Client **request** | ✓ | ✗ (server không biết địa chỉ client) |
| Client → Server **response** | ✓ | **?** (cần server nhớ state để ghép với request nó đã hỏi) |

Streamable HTTP có một cách giải "khéo léo" nhưng có điều kiện kèm theo (mục 5.3 và 6). Ô "?" là chỗ khó nhất khi scale ngang, xem suy luận ở mục 10.

Bài liệt kê các message khó thực hiện với HTTP thuần: **server-initiated request** (Create Message, List Roots) và **notification** (Progress, Logging, **Initialized, Cancelled**). Lý do của Initialized có lời giải ở mục 6.2; **lý do của Cancelled bài chưa nói** (xem mục 10).

### 5.3 Cách Streamable HTTP giải bài toán: session id và SSE

**Ý tưởng:** để **client mở kết nối**, rồi **giữ mở** để server đẩy message về lúc nào cũng được. Server không cần biết địa chỉ client vì kết nối do client khởi tạo. Kỹ thuật là **SSE (Server-Sent Events)**: một HTTP response không đóng, server ghi từng sự kiện vào theo thời gian (analogy **[ngoài tài liệu]**: giống endpoint stream `text/event-stream`, ý tưởng gần SignalR nhưng một chiều).

**Bước 1: bắt tay và nhận session id**

```
Client --Initialize Request-->                                     Server
Client <--Initialize Result (header: mcp-session-id: 7089d4160bbb4d)-- Server
Client --Initialized Notification (header: mcp-session-id: 7089...)--> Server
```

- Server cấp **`mcp-session-id`** trong **header của response** ở Initialize Result.
- **Mọi request sau đều phải kèm header này.** Nó định danh client.

**Bước 2: mở kênh chính**

```
Client --GET mcp-server.com/mcp/ (mcp-session-id)--> Server
Client <==== SSE response, giữ mở lâu tùy ý ==== Server
```

SSE này là thứ cho phép **server gửi request tới client**.

**GET là tùy chọn** **[spec, theo bản review]**: client "MAY" mở GET, và server có thể trả **405** nếu không cung cấp stream này. Đừng coi bước 2 là luôn có.

**Bước 3: mỗi lần gọi tool tạo thêm một kênh tạm**

```
Client --POST (Call Tool Request, mcp-session-id)--> Server
Client <== SSE riêng cho lần gọi này, đóng khi Call Tool Result đã gửi ==
```

**Hai kênh SSE và phân luồng (theo khóa học):**

| Kênh | Mở bằng | Sống bao lâu | Dùng cho |
|---|---|---|---|
| **Kênh chính** | GET | Mở lâu | Request từ server → client; **Progress Notification** |
| **Kênh theo từng tool call** | POST của lần gọi | Đóng khi Call Tool Result đã gửi | **Logging Message Notification**, **Call Tool Result** |

**Về Progress, khóa học tự mâu thuẫn**: đoạn "in depth" xếp Progress vào kênh chính, còn đoạn "State" nói `json_response=True` (tắt streaming của POST) làm mất progress, tức progress cũng đi trong luồng POST. **[spec, theo bản review]** Spec quy định:
- Message server gửi trên stream của **POST**: "SHOULD relate to the originating client request".
- Message trên stream **GET**: "SHOULD be unrelated to any concurrently-running request".

Progress luôn gắn với một request (qua `progressToken`), nên **theo spec nó đi trên stream của POST**; Logging gắn với request cũng vậy. Kênh GET dành cho message không gắn request nào (ví dụ `list_changed`, `resources/updated`). Slide về scale vẽ Create Message Request nằm trong POST SSE cũng nhất quán với cách đọc này.

**Cho kỳ thi: giữ nguyên phát biểu của khóa học** (Progress → kênh chính). Phần spec ở trên là ghi chú riêng để hiểu đúng cơ chế.

**So với stdio:**

| Stdio | Streamable HTTP |
|---|---|
| Ống A (client → server, bền) | Các **POST** (mỗi cái ngắn, gắn nhau bằng session id) |
| Ống B (server → client, bền) | **Kênh chính SSE** (GET giữ mở) |
| (không có) | Thêm **kênh SSE tạm** cho mỗi tool call |

Stdio có ống sẵn do OS tạo; HTTP phải **tự dựng** bằng session id và SSE, nên phức tạp và dễ hỏng hơn.

## 6. State, scale ngang và hai cờ

### 6.1 Bài toán scale

- Ban đầu một server phục vụ vài client. Khi đông lên thì chạy **nhiều instance phía sau load balancer** (scale ngang).
- Nhưng client dùng hai loại kết nối: **GET SSE** và **POST**. Load balancer có thể gửi chúng tới **hai instance khác nhau**. Ví dụ: GET SSE nằm ở server A, POST gọi tool rơi vào server B. Tool ở B cần sampling (Create Message Request) nhưng kênh nối tới client lại ở A, nên hai server phải phối hợp.

### 6.2 `stateless_http=True`

- Client **không nhận session id**, server không theo dõi từng client. Mỗi request độc lập, instance nào xử lý cũng được.
- Không có session id thì **server không ghép được đường GET SSE với request đang tới**, nên GET SSE không dùng được nữa.
- **Mất:** server → client request, sampling, progress, subscription (Resource Updated...).
- **Nuance** **[spec, theo bản review]**: **spec không có khái niệm "stateless mode"**; session id chỉ là MAY. `stateless_http` là **quy ước của Python SDK** (mỗi request dùng một transport/session mới). Tài liệu SDK xếp long-running tool và progress là **hạn chế**, không phải tắt hẳn. Tóm lại: **theo khóa học, stateless thì mất progress; thực tế phụ thuộc SDK.**
- **Được:** scale ngang dễ, ít overhead kết nối, và **không cần bước khởi tạo (handshake)**: client gọi thẳng request. **[ngoài tài liệu, suy luận]** Đây có lẽ là lý do Initialized Notification nằm trong danh sách "bị ảnh hưởng" ở mục 5.2.

### 6.3 `json_response=True`

- POST được trả bằng **một cục JSON cuối cùng** thay vì nhiều sự kiện SSE.
- **Mất:** progress và log giữa chừng. Chỉ còn kết quả tool.
- **[spec, theo bản review]** Spec cho phép server trả **một object JSON thay vì SSE**, nên mất progress và log giữa chừng là hệ quả tất yếu.

### 6.4 Hai cờ tắt hai thứ khác nhau

Cả hai mặc định là `false`. Cú pháp trong SDK Python: `FastMCP("mcp-server", stateless_http=True, json_response=True)`.

| Cờ | Tắt cái gì | Mất |
|---|---|---|
| `stateless_http` | **Session và kênh GET SSE** | Server → client request, sampling, progress, subscription |
| `json_response` | **Streaming của phản hồi POST** | Progress và log giữa chừng |

| Dùng | Khi (theo bài) |
|---|---|
| `stateless_http=True` | Cần scale ngang qua load balancer; không cần server → client; tool không cần sampling; muốn ít overhead kết nối |
| `json_response=True` | Không cần streaming; muốn phản hồi đơn giản; tích hợp hệ thống cần JSON thuần |

**Dev và production:** nếu dev bằng stdio mà deploy bằng HTTP thì hành vi giữa stateful và stateless có thể khác lớn. **Test bằng đúng transport và cấu hình sẽ dùng ở production.** Dấu hiệu nhận biết: chạy tốt với stdio ở local nhưng hỏng khi lên HTTP thì nghi hai cờ này.

### 6.5 Bối cảnh phiên bản spec: 2025 và 2026-07-28

Toàn bộ note này (và khóa học) mô tả MCP **thời kỳ spec 2025**: bắt tay `initialize`, `mcp-session-id`, kênh GET SSE. **[spec]** Bản spec **2026-07-28** (đã tra trang spec và changelog) thay đổi đáng kể phần Streamable HTTP:

| Thay đổi | Nội dung |
|---|---|
| Bỏ handshake | Không còn `initialize` / `notifications/initialized`. Phiên bản giao thức và client capabilities đi trong `_meta` của **mỗi request**; có method mới `server/discover` để client lấy capabilities của server trước |
| Bỏ session mức giao thức | Header `Mcp-Session-Id` bị **bỏ qua**, server không cấp và không lặp lại id |
| Bỏ stream GET | GET hoặc DELETE tới endpoint MCP trả **405** |
| Bỏ resumability | Không còn `Last-Event-ID` và id sự kiện SSE; stream đứt thì request đang chạy mất, client phải gửi lại với request id mới |
| Server → client request | Sampling, elicitation, roots trả dưới dạng **input request trong `InputRequiredResult`**, không còn là request riêng trên một stream |
| Thông báo thay đổi | Qua request `subscriptions/listen`, trả một SSE response dài |
| Header bắt buộc | `Mcp-Method`, `Mcp-Name` trên POST; server từ chối nếu header và body không khớp |

- **Hỗ trợ tùy SDK**: ví dụ Go SDK chỉ nhận 2026-07-28 qua HTTP khi đặt `Stateless = true`, còn muốn giữ session thì client sẽ thương lượng xuống 2025-11-25.
- **[kiểm tra]** Một bài blog gọi bản này là release candidate trong khi trang spec trình bày như bản đã phát hành; xem trạng thái hiện tại trước khi dựa vào.
- **Đề thi bám khóa học** (spec 2025). Phần này chỉ là **bối cảnh**: các khái niệm session id, GET SSE, hai cờ ở trên là đúng cho thế hệ 2025, và có thể không còn nguyên vẹn ở thế hệ mới.
- Nguồn tra cứu: [Streamable HTTP, spec 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http), [Key Changes, spec 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog), [The 2026-07-28 Specification (blog)](https://blog.modelcontextprotocol.io/posts/2026-07-28/).

## 7. Tổng hợp: so sánh transport và điều cần nhớ cho kỳ thi

### 7.1 Stdio và Streamable HTTP

| | Stdio | Streamable HTTP |
|---|---|---|
| Vị trí server | Tiến trình con, **cùng máy** | Máy khác, qua URL |
| Hai chiều | Trọn vẹn, đối xứng | Phải dựng bằng SSE và session id |
| State | Không cần (ống do OS giữ) | Session id; hoặc bỏ bằng `stateless_http` |
| Scale ngang | Không áp dụng | Cần cân nhắc state (mục 6) |
| Hợp khi | Dev, tool cá nhân | Server dùng chung, hosted |

### 7.2 Cần nhớ cho kỳ thi

1. MCP là message JSON (thực chất JSON-RPC 2.0). Request có `id`, result mang lại `id` đó; **notification không có `id`, không có phản hồi**. Spec là nguồn chuẩn, viết bằng TypeScript chỉ để mô tả kiểu.
2. MCP **hai chiều**: server cũng khởi tạo được giao tiếp (Create Message, List Roots, Progress, Logging).
3. **Bắt tay 3 message**: Initialize Request, Initialize Result, Initialized Notification (do client gửi, không phản hồi). Chưa bắt tay xong thì chưa gửi request khác.
4. **Stdio**: client khởi chạy server làm tiến trình con; client ghi vào **stdin** của server, đọc từ **stdout** của server; **chỉ cùng máy**; hỗ trợ trọn vẹn bốn mẫu giao tiếp.
5. **HTTP thường** chỉ chắc chắn làm tốt: client → server request và server → client response. Server không chủ động gọi client được vì client không có URL cố định.
6. **Streamable HTTP** dựng hai chiều bằng: header **`mcp-session-id`** (cấp ở Initialize Result, kèm mọi request sau), **GET SSE** (kênh chính, giữ mở, cho server → client request), và **POST SSE** (mỗi tool call, đóng khi có Call Tool Result).
7. Phân luồng theo khóa học: **Progress → kênh chính**; **Logging và Call Tool Result → kênh của tool call**.
8. **`stateless_http=True`**: không session id, mất server → client request, sampling, progress, subscription; được scale ngang và không cần handshake. **`json_response=True`**: tắt streaming của POST, mất progress và log giữa chừng. Mặc định cả hai `false`.
9. Scale ngang + load balancer làm GET SSE và POST rơi vào hai instance khác nhau.
10. Test bằng đúng transport production.

---

## 8. Đối chiếu cách hiểu của mình

Các ý dưới đây là cách mình hiểu trong lúc học, kèm đánh giá. Hướng chung: mình có xu hướng gắn mọi thứ vào một hệ thống cụ thể, trong khi khóa học mô tả **vai trò từng thành phần**.

| Ý | Đánh giá |
|---|---|
| 8.1 MCP là layer giao tiếp, đang nói riêng về server chứ chưa phải server Anthropic | **Đúng** |
| 8.2 JSON là format chính, chưa biết có duy nhất không | **Đúng, bổ sung**: duy nhất ở mức giao thức (JSON-RPC 2.0) |
| 8.3 `id` giống key trong NoSQL key-value | **Giống một nửa** |
| 8.4 MCP là cầu nối giữa server Anthropic và app | **Sai**, nhưng có chỗ đúng |
| 8.5 MCP là tầng độc lập; MCP là cầu nối tới tài nguyên của cả hệ thống Anthropic-client | **Đúng một phần**, cần chỉnh hai chỗ |
| 8.6 Vai trò: Anthropic cung cấp Model, MCP cung cấp tài nguyên, App gọi cả hai | **Đúng**, chỉnh nhẹ |
| 8.7 Flow tool call qua stdin/stdout | **Đúng tổng thể, đảo hai chỗ** |
| 8.8 Server → client: việc làm ở app nên stdin/stdout nằm ở app | **Sai** |
| 8.9 Hai "chiều không gian" với hai cổng | **Gần đúng, cần sửa nhãn** |
| 8.10 Sticky session hay state chung đều biến app thành stateful; stateless tối ưu khi scale lớn | **Đúng cho trường hợp phổ biến**, chỉnh hai chỗ về mức độ |

### 8.1 MCP là layer giao tiếp, chưa phải server Anthropic

Đúng. MCP là giao thức giữa **MCP client** và **MCP server**; server ở đây là tiến trình bất kỳ bạn viết (GitHub, Linear, script cục bộ), không phải server Anthropic. Phần mô tả message chưa nhắc gì đến Anthropic hay Claude API.

### 8.2 JSON có phải duy nhất

Bài chỉ nói "JSON messages". **[ngoài tài liệu]** Ở mức giao thức đây là format duy nhất (JSON-RPC 2.0, UTF-8, nhị phân qua base64 trong JSON). Cái đổi theo transport là **cách gói** (mục 1.1).

### 8.3 `id` có giống key NoSQL không

**Giống một nửa.**

| | Key trong DynamoDB/Firebase | `id` trong MCP |
|---|---|---|
| Trả lời câu hỏi | "Bản ghi nào?" (địa chỉ dữ liệu) | "Result này trả lời request nào?" |
| Sống bao lâu | Bền, tồn tại trong DB | Chỉ trong **một phiên kết nối** |
| Ai đặt | Thường bạn thiết kế | **Bên gửi request** tự đặt |
| Có lưu không | Có | Không, giữ tạm đến khi nhận kết quả |

Id là **correlation id** (mã đối chiếu). Trực giác key-value vẫn đúng ở một chỗ **[ngoài tài liệu]**: phía client thường giữ một bảng tra trong RAM, ví dụ `Dictionary<id, TaskCompletionSource>`; gửi request thì thêm mục, result về thì tra id và hoàn tất. Thứ đóng vai "key chỉ tới dữ liệu" trong MCP là **URI** của `resources/read` và **`name`** của `tools/call`.

### 8.4 MCP là cầu nối Anthropic ↔ app

**Sai.** MCP nằm **ở phía bên kia của app**, nối app với các hệ thống bên ngoài. Giao thức giữa app và Anthropic là Claude API (mục 2.1); message gửi lên Anthropic **không phải** message MCP. Hình dung dễ nhầm vì trong một lượt tool call cả hai đường đều được dùng, nhưng **app** mới là điểm nối hai đường, không phải MCP. Cách nhớ: **Claude API: app ↔ model. MCP: app ↔ tool/data.**

### 8.5 MCP độc lập và là cầu nối tới tài nguyên

- **Với Anthropic: độc lập thật.** **Với client: không tách rời**, vì đầu client của MCP nằm **bên trong app**, đầu server là tiến trình riêng. Nên MCP là hợp đồng độc lập với Anthropic, không phải một khối nằm riêng giữa các thành phần.
- Hai bên không "hỗ trợ lẫn nhau" ngang hàng mà **liên kết qua app**: app dùng Claude API để hỏi model, dùng MCP để chạy tool.
- Chữ "resource" ở đây mình dùng nghĩa đen (tài nguyên). **Khác với Resource trong khóa học**, vốn chỉ là một trong ba thứ server cung cấp (dữ liệu chỉ đọc, gọi bằng URI; không chỉ là file). Nghĩa đen bao gồm cả Tool và Prompt.
- MCP server thường **không phải nơi lưu dữ liệu** mà là adapter/cổng đứng trước hệ thống thật (GitHub MCP server gọi GitHub API).

### 8.6 Vai trò từng thành phần

Cách nhìn theo vai trò là hợp lý và tốt hơn gom thành một hệ thống. Chỉnh dòng MCP: MCP **không "cung cấp"** tài nguyên mà là **đường dẫn tới** tài nguyên; thứ cung cấp là MCP server, tài nguyên thật nằm ở hệ thống phía sau. Bổ sung dòng App: ngoài gọi hai bên, app là **nơi đặt kiểm soát** (permission rule, hook, scope), vì mọi thứ model làm với bên ngoài đều đi qua app. Bảng đã ghi ở mục 2.2.

### 8.7 Flow tool call và stdin/stdout

Flow tổng thể đúng, nhưng hai câu bị đảo:

| Mình viết | Sửa thành |
|---|---|
| "server nhận thông tin từ **stdout**" | server nhận từ **stdin** của nó |
| "app (MCP client) nhận ở đầu **stdin**" | client nhận bằng cách **đọc stdout của server** |

Gốc của sự nhầm: stdin/stdout tính theo góc nhìn của **tiến trình sở hữu** chúng (mục 4.2). Mình cũng bỏ sót hai bước: bước 0 (bắt tay và `tools/list` diễn ra lúc kết nối, không mỗi task) và bước 8 (kết quả MCP phải được đưa lại cho model), xem mục 2.3.

### 8.8 Server → client: IO nằm ở đâu

Mình đoán: vì việc được làm ở app nên input/output nằm ở app và server gửi vào "stdin của app". **Sai.** Hai ống thuộc server **bất kể việc làm ở đâu**. Client **tự nối** hai ống vào stdin/stdout của server khi khởi chạy nó; stdin/stdout của app vẫn nối với terminal, nên server ghi vào đó là gõ vào terminal của người dùng. Bảng:

| Hướng | Luôn đi qua |
|---|---|
| Client → Server (request hay response) | ghi vào **stdin của server** |
| Server → Client (request hay response) | ghi ra **stdout của server** |

Ví dụ rõ nhất là sampling (mục 4.3). Phần "app chỉ cung cấp tham số nên IO ở server" đúng về kết quả nhưng sai lý do: lý do là server là tiến trình con và hai ống là của server.

### 8.9 Hình dung "hai chiều không gian" với hai cổng

Mình hình dung app và server là hai chiều không gian, nối bằng một ống vô hình với hai cổng cố định. Chỉnh:
- **Cả stdin và stdout đều thuộc phía server**; app có hai đầu **đối diện** của hai ống. Là **hai ống một chiều**, mỗi ống hai đầu (mục 4.2), không phải một ống với hai cổng.
- Việc "app chỉ dùng đầu của chính mình, không chạm vào cổng của server" là **đúng**.
- Mình đề xuất gán nhãn theo vai trò đầu ống: đầu ghi là "out", đầu đọc là "in", nên nhãn phụ thuộc ống và hướng chứ không phụ thuộc "chiều không gian". Điều này **đúng về logic** và là công cụ nhớ hướng tốt, nhưng **không phải tên thật**: stdin/stdout là tên của fd 0 và 1 của một tiến trình, và các đầu ống ở phía app là descriptor khác. Nhãn đó còn **đảo ngược với .NET**: đầu ghi của app tên là `StandardInput`. **Khi đọc tài liệu và code, stdin/stdout luôn là của server**; ở phía app gọi là "đầu ghi tới server" và "đầu đọc từ server".

### 8.10 Stateful, stateless và scale

Mình cho rằng sticky session hay state chung đều biến app thành stateful và không nên khi scale lớn; kinh nghiệm Blazor Server (chuyển từ web proxy sang long polling dẫn tới flood API; vượt capacity chỉ scale up được) cuối cùng phải chuyển về MVC API và HTML thuần.

**Đúng:**
- Với MCP server dùng chung, stateless là mặc định hợp lý, và khóa học cũng xếp "cần scale ngang qua load balancer" vào điều kiện dùng `stateless_http=True`.
- Hướng chuyển Blazor Server → MVC API là **đưa state ra khỏi server**, cùng tinh thần `stateless_http`.
- **[ngoài tài liệu, suy luận]** SSE cũng là kết nối giữ mở lâu giống WebSocket/SignalR của Blazor, nên vấn đề nhiều lớp proxy (buffer, cắt kết nối rảnh) có thể lặp lại. Với máy sau proxy công ty thì stateless hoặc `json_response` còn đáng cân nhắc hơn.

**Cần chỉnh:**
- **"Stateful thì chỉ scale up được" hơi mạnh.** Sticky session hay state chung (Redis, backplane) vẫn scale ngang được, chỉ đắt và phức tạp hơn: tải lệch, mất instance thì mất state, thêm dependency. Blazor Server đặc biệt khó vì mỗi người dùng giữ một kết nối liên tục cộng state lớn trong RAM nên trần nằm ở số kết nối và bộ nhớ mỗi instance. Chỉnh lại: **stateful làm scale ngang khó và tốn kém hơn nhiều**, stateless là cách đơn giản nhất.
- **"Stateless" ở MCP chỉ là state của kết nối, không phải dữ liệu nghiệp vụ.** `stateless_http` bỏ session (không `mcp-session-id`, không GET SSE); dữ liệu thật vẫn ở DB hoặc dịch vụ phía sau. Mất mát nằm ở **tính năng** (sampling, progress, subscription), không ở dữ liệu.

## 9. Quyết định thiết kế **[ngoài tài liệu]**

Câu hỏi thực tế: **tool có cần server → client không?** Đây là suy luận của mình, chưa thực hành.

| Tình huống | Hướng xử lý |
|---|---|
| MCP server bọc API ngoài (GitHub, Linear, truy vấn DB), chỉ cần request/response | **`stateless_http=True`**, scale ngang qua load balancer |
| Cần báo tiến độ nhưng vẫn muốn stateless | **Mẫu job bất đồng bộ**: tool khởi chạy việc và trả `job_id` ngay; tool khác (ví dụ `get_status`) cho model hỏi lại. Đúng tinh thần "alternative communication patterns" bài nhắc, và là cách client hỏi lại thay vì server đẩy |
| Thật sự cần sampling hoặc subscription | Chấp nhận stateful và tính trước chi phí scale: sticky session (định tuyến theo header `mcp-session-id`) hoặc state chung (pub/sub để instance nào xử lý POST cũng đẩy được qua instance giữ GET SSE); hoặc dùng stdio nếu chỉ chạy cục bộ |

Đây cũng là cùng một đánh đổi trong kinh nghiệm Blazor: **tính năng thời gian thực với kết nối bền** đổi lấy **khả năng scale đơn giản**. Nếu thử trên Kubernetes thì cần hỏi trước khi đụng vào cấu hình Redis hoặc load balancer (guardrail).

## 10. Còn lại và việc cần kiểm tra

- **Đã kiểm chứng theo bản review ngoài** (mình chưa tự đọc toàn văn spec): stdio (message cách nhau bằng xuống dòng, không chứa xuống dòng bên trong; log qua stderr; client đóng stdin để dừng); hai nhóm request/notification phân biệt bằng `id`; hai loại lỗi (JSON-RPC `error` và `isError: true`); session id cấp trong InitializeResult và kèm mọi request sau (spec viết `MCP-Session-Id`, HTTP không phân biệt hoa thường); `json_response`; Cancelled hủy được từ cả hai phía; bảng tên `method`.
- **Đường đi của Progress**: đã có đáp án từ spec (mục 5.3): đi trên stream của POST vì gắn với request. Với đề thi vẫn giữ phát biểu của khóa học (kênh chính).
- **Initialized** (suy luận, khớp thông tin tra được): stateless cho phép bỏ qua handshake nên Initialized không còn. **Cancelled** (suy luận, **[ngoài tài liệu]**, chưa kiểm chứng): khi scale ngang, POST chứa Cancelled có thể tới một instance **không biết request đang chạy** ở instance khác, nên hủy không có tác dụng.
- **Ô "?" ở mục 5.2** (suy luận, **[ngoài tài liệu]**, chưa kiểm chứng): server gửi Create Message qua một stream, nhưng client trả Result bằng **một POST mới**, và POST đó có thể rơi vào instance **không giữ request đang chờ**. Nếu đúng thì đây là lý do stateless không làm sampling được, và là chỗ khó nhất của scale ngang.
- Bối cảnh spec 2026-07-28 xem mục 6.5. Các bản SDK hiện tại hỗ trợ bản nào, và `stateless_http` của SDK Python thay đổi ra sao, chưa kiểm tra.
- Các message ngoài slide (`tools/list`, `prompts/get`, `elicitation/create`, `ping`, Roots List Changed, Resource Updated) và tên `method` ở mục 1.3 lấy từ kiến thức spec của mình, chưa đối chiếu lại.
- Ánh xạ hai cờ vào cơ chế (mục 6.4) khớp slide, nhưng chi tiết SDK (ví dụ `stateless_http` có kéo theo `json_response` hay không) chưa kiểm chứng.
- Windows: mình nhớ docs Claude Code có lưu ý server stdio chạy bằng `npx` trên Windows native cần bọc `cmd /c`. **Chưa đối chiếu**; kiểm tra khi thực hành.
- Chưa thực hành: chạy một server stdio và dán tay ba dòng JSON ở mục 4.4; dựng server Streamable HTTP rồi thử bật/tắt `stateless_http` và `json_response` để thấy progress, log, sampling thay đổi; thử `claude mcp add --transport http` tới server tự dựng.
- Chưa có trong đoạn đã nhận: hướng dẫn **xây** MCP server (đã ghi ở [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) mục 11). Phần này bổ sung hai cờ cấu hình (`stateless_http`, `json_response`) của FastMCP.
