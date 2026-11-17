# Notes Week 3 Day 2: MCP Servers (tool, resource, prompt)

Nguồn: tài liệu khóa học (phần "Building and configuring an MCP server: transport, scope, and the GitHub server"); hiện có đủ: mở đầu (MCP là gì, 3 thành phần server cung cấp), transport, context cost, scope, permission rule theo từng tool, ví dụ GitHub/Linear và bảng tra cứu setup. Chưa thấy phần hướng dẫn **xây** một server trong đoạn đã nhận. Prompt caching và RAG (cùng trang tài liệu) ghi riêng ở [NOTES_W3D2_Prompt_Caching_RAG.md](NOTES_W3D2_Prompt_Caching_RAG.md). **[docs]** = đối chiếu docs Claude Code (đọc 2026-11-17), **[ngoài tài liệu]** = suy luận hoặc kiến thức bổ sung.

Liên hệ với note trước ([NOTES_W3D2_Packaging_Workflows.md](NOTES_W3D2_Packaging_Workflows.md)): plugin gói skill, hook, subagent **và MCP server** thành một đơn vị cài. Phần này đi sâu vào thành phần MCP server.

## 1. MCP server và khác gì nối tool trực tiếp

- **Nối trực tiếp:** schema và code thực thi của tool nằm trong code của **từng ứng dụng**. Ba ứng dụng cần cùng một dịch vụ ngoài thì có ba bản tích hợp, mỗi bản tự bảo trì.
- **MCP (Model Context Protocol)** tách định nghĩa tool ra khỏi ứng dụng, thành một **tiến trình riêng** gọi là server. Xây một lần, mọi MCP client kết nối đều dùng được mà không viết lại.
- Claude Code có **MCP client tích hợp sẵn**: khi kết nối server, nó khám phá tool server cung cấp rồi gọi được trong session.
- **[ngoài tài liệu]** Hình dung bằng số lượng: N ứng dụng × M dịch vụ cần N×M bản tích hợp nếu nối trực tiếp, còn với MCP là N client + M server. Analogy .NET: nối trực tiếp giống mỗi app tự chép một class library; MCP giống một service riêng có hợp đồng (contract) rõ ràng mà các app cùng gọi. Chỗ khác với REST thông thường: MCP có bước **khám phá** (client hỏi server có gì) và 3 loại thành phần, không chỉ là danh sách endpoint.
- Nối với note Skills: Managed Agents khai báo `MCP servers` ngay trong agent resource cùng với skill (xem NOTES_W3D2_Packaging_Workflows mục 3).

## 2. Ba thứ một MCP server cung cấp

| | Tool | Resource | Prompt |
|---|---|---|---|
| Là gì | Hành động model có thể gọi | Dữ liệu **chỉ đọc**, client lấy và đặt thẳng vào context | Mẫu chỉ dẫn viết sẵn, gọi theo tên |
| Ai kích hoạt **[ngoài tài liệu]** | Model quyết định | Client/người dùng chỉ định | Người dùng gọi |
| Trong Claude Code **[docs]** | Model gọi | `@server:protocol://đường/dẫn` | `/mcp__server__prompt [đối số]` |

### 2.1 Resource
- Client yêu cầu resource bằng **địa chỉ (URI)**, server trả dữ liệu.
- Hai dạng: **direct** (địa chỉ cố định, không tham số, ví dụ danh sách tài liệu có sẵn) và **templated** (địa chỉ có tham số, ví dụ địa chỉ tài liệu nhận một document id).
- **Dùng khi:** muốn dữ liệu đã biết nằm trong context **ngay từ đầu lượt**, và lấy thẳng rẻ hơn, dễ đoán hơn là để model gọi tool đi lấy.
- **Cảnh báo của tài liệu:** hỗ trợ resource **khác nhau giữa các MCP client**; kiểm tra client có cơ chế đưa resource vào context trước khi dựa vào mẫu này.
- **[docs]** Trong Claude Code: gõ `@` để liệt kê resource của mọi server đang kết nối (hiện cùng file trong autocomplete). Cú pháp `@server:protocol://resource/path`, ví dụ `@github:issue://123`, `@postgres:schema://users`; có thể tham chiếu nhiều resource trong một prompt. Resource được tự lấy và đính kèm như attachment.
- **[docs]** Điểm bổ sung: Claude Code còn tự cung cấp **tool để liệt kê và đọc resource** khi server hỗ trợ, nên ngoài đường "người dùng `@`", model cũng đọc được resource qua tool.
- **[docs]** Resource `ui://` (MCP Apps) là trang để host render, không hiện trong gợi ý `@`.

### 2.2 Prompt
- Mẫu chỉ dẫn viết sẵn mà server cung cấp để client gọi **theo tên**, thay vì mỗi người dùng tự viết.
- **Dùng khi:** cần cách diễn đạt cụ thể, một chỉ dẫn được xây kỹ cho kết quả tốt hơn rõ rệt so với người dùng tự gõ, và muốn mọi client nhận chất lượng như nhau. Bảo trì **một chỗ** (trên server), dùng lại ở mọi nơi kết nối.
- **[docs]** Trong Claude Code, prompt hiện là command: danh sách `/` ghi `/servername:promptname (MCP)`; gõ `/mcp__servername__promptname` cũng chạy. Ví dụ `/mcp__github__pr_review 456`. Kết quả được chèn thẳng vào hội thoại.
- **[docs]** Lưu ý: đối số tách theo **khoảng trắng**, mỗi token là một đối số, nên không truyền được một đối số nhiều từ. Tên server có ký tự ngoài `A-Za-z0-9_-` thì được đổi thành `_` trong dạng `/mcp__...`. Tên server `anthropic-skills` bị Claude Code **dành riêng** nên prompt của nó không hiện.
- **So với skill:** cả hai đều là "điểm vào tường minh" gọi bằng `/tên`. Skill là file trong setup của bạn (cập nhật bằng cách đổi file hoặc plugin); MCP prompt do **server** cung cấp, tự khám phá động, cập nhật tập trung ở server.

## 3. Đặt tên và chi phí context của MCP trong Claude Code **[docs]**

- **Tên tool:** dạng `mcp__<server>__<tool>` (suy ra từ dạng của plugin). Với server do **plugin** cung cấp: `mcp__plugin_<tên-plugin>_<tên-server>__<tên-tool>`; ký tự ngoài `A-Za-z0-9_-` đổi thành `_`.
- **Liên hệ với Risk ở note plugin:** tên đầy đủ dùng trong permission rule, `allowed-tools` của skill, `tools` của subagent và hook matcher. Hook matcher viết theo tên server trần (`mcp__database-tools__.*`) **không bao giờ khớp** server do plugin cung cấp. Guardrail nhắm vào tool MCP phải dùng đúng tên đầy đủ.
- **Tool search (mặc định bật):** lúc khởi động chỉ nạp **tên tool và server instructions**, mô tả đầy đủ để sau, nên thêm nhiều server ít ảnh hưởng context. Cùng tư tưởng nạp theo nhu cầu như skill. Không giới hạn cứng số tool mỗi server.
- **Cho người viết server:** `server instructions` đóng vai trò giống `description` của skill: giúp Claude biết khi nào nên tìm tool của bạn. Nên nói rõ: nhóm tác vụ nào, khi nào tìm tool, khả năng chính. Giới hạn 4.096 ký tự cho server instructions và mô tả tool nạp sẵn; 16.384 cho mô tả tool nạp qua tool search. Đặt thông tin quan trọng và từ khóa tìm kiếm **ở đầu**.
- **`list_changed`:** server có thể đổi tool, prompt, resource khi đang kết nối và gửi thông báo; terminal tương tác tự lấy danh sách mới, còn `-p` và Agent SDK chỉ làm mới danh sách tool.
- **Giới hạn output:** cảnh báo khi output MCP vượt 10.000 token, mặc định chặn ở 25.000 (`MAX_MCP_OUTPUT_TOKENS`).

## 4. Đối chiếu với kiến thức API

- Tool trực tiếp ở API là mảng `tools` bạn tự định nghĩa trong request (xem note W3D1, mục 6). MCP là cách chuẩn hóa để **dùng lại** định nghĩa đó giữa nhiều ứng dụng.
- Điểm cần nhớ: tool/resource/prompt khác nhau ở **ai quyết định**: model (tool), client hoặc người dùng (resource), người dùng (prompt).

## 5. Transport: Claude Code nói chuyện với server bằng cách nào

Transport là **kênh giao tiếp** giữa MCP client và MCP server. Chọn theo **server chạy ở đâu**.

| Transport | Cách hoạt động | Dùng khi | Trạng thái |
|---|---|---|---|
| **stdio** | Client chạy server như **tiến trình con** trên cùng máy, giao tiếp qua stdin/stdout | Tool cục bộ, script cá nhân, dev server chạy trên máy bạn | Dùng khi cần. **Không dùng được** cho server muốn chia sẻ cho nhóm hoặc host từ xa |
| **HTTP** | Kết nối qua HTTP chuẩn tới URL; server có thể ở máy khác | Mọi server **không chạy cục bộ**: server dùng chung của nhóm, tích hợp hosted | **Khuyến nghị** |
| **SSE** (Server-Sent Events) | Cách truyền cũ có trước HTTP | Chỉ khi gặp trong cấu hình hay tài liệu cũ | **Legacy**, không khuyến nghị cho server mới |

- Analogy .NET (**[ngoài tài liệu]**): stdio giống chạy một console app con rồi nói chuyện qua stdin/stdout; HTTP giống gọi một web service từ xa.
- **[docs]** Cú pháp đăng ký:
  - HTTP: `claude mcp add --transport http <tên> <url>` (có thể thêm `--header "Authorization: Bearer ..."`; HTTP cũng hỗ trợ OAuth).
  - stdio: `claude mcp add [options] <tên> -- <lệnh> [đối số...]`, ví dụ `--env KEY=... --transport stdio airtable -- npx -y airtable-mcp-server`. Dấu `--` ngăn cờ của chính server (`-y`, `--port`) bị hiểu thành option của Claude Code.
  - SSE: `--transport sse`; docs ghi rõ **deprecated**. Từ v2.1.265, `--transport http` thử HTTP trước rồi tự chuyển sang SSE nếu server không nhận HTTP.
  - Có thêm WebSocket (`type: "ws"`) qua `claude mcp add-json`; cờ `--transport` không nhận `ws`.
- Scope (local, project, user, enterprise): xem mục 7.
- **[docs]** Messages API kết nối MCP qua **URL công khai** (xem mục 6.1), nên chỉ nối trực tiếp được server từ xa; docs ghi rõ stdio cục bộ không nối trực tiếp. Lý do: stdio là tiến trình con trên máy bạn, API server không khởi động được nó.

## 6. Chi phí context của MCP

- Mỗi server đang kết nối đóng góp **định nghĩa tool**. Nếu nạp sẵn thì chiếm cửa sổ context.
- **Mặc định Claude Code hoãn (defer)** các định nghĩa này và dùng một **bước tìm kiếm** để nạp tool liên quan khi tác vụ cần. Chỉ tool được gọi mới vào context.
- **Chế độ opt-in:** nạp sẵn định nghĩa nếu tổng vừa trong khoảng **10% cửa sổ context**; vượt thì mới hoãn.
- Dù chế độ nào, **chỉ kết nối server cần dùng**: mỗi server thêm vào tập định nghĩa mà model phải tính đến.
- **[docs]** Biến `ENABLE_TOOL_SEARCH`:

| Giá trị | Hành vi |
|---|---|
| (không đặt) hoặc `true` | Hoãn mọi tool MCP, nạp theo nhu cầu (nạp sẵn trên model cũ hơn Opus 4 / Sonnet 4 và vài nền tảng khác) |
| `auto` | Chế độ ngưỡng: nạp sẵn khi tổng định nghĩa dưới 10% cửa sổ context; từ 10% trở lên bật tool search |
| `auto:N` | Như `auto` nhưng ngưỡng N% (0-100), ví dụ `auto:5` |
| `false` | Nạp sẵn toàn bộ, không hoãn |

- **[docs]** Ngoại lệ theo server: đặt `alwaysLoad: true` trong cấu hình server để tool của nó luôn nạp sẵn bất kể `ENABLE_TOOL_SEARCH`. Chỉ dùng cho ít tool mà Claude cần ở mọi lượt, vì mỗi tool nạp sẵn tốn context.
- Bước "tìm tool theo nhu cầu" chính là một dạng **agentic search** (xem [NOTES_W3D2_Prompt_Caching_RAG.md](NOTES_W3D2_Prompt_Caching_RAG.md) mục 2).

### 6.1 Messages API kết nối MCP thế nào **[docs: claude-api skill]**

Messages API có "MCP connector": cần **cả hai nửa**: `mcp_servers=[{type:"url", url, name}]` **và** `tools=[{type:"mcp_toolset", mcp_server_name: <cùng name>}]`, kèm beta `mcp-client-2025-11-20`. Chỉ khai báo `mcp_servers` thì bị từ chối (lỗi validation). Tính khả dụng theo nền tảng: xem `shared/platform-availability.md` của skill.

- **[docs] Giới hạn của MCP connector:** trong toàn bộ tính năng MCP, chỉ hỗ trợ **tool call** (không resource, không prompt). Đây là ví dụ cụ thể cho cảnh báo ở mục 2.1 rằng hỗ trợ resource khác nhau giữa các client: Claude Code có `@resource` và prompt thành command, còn connector của API thì không.
- **[docs]** Server phải **công khai qua HTTPS** (Streamable HTTP hoặc SSE). Trường `type` hiện chỉ có `url`, URL phải bắt đầu bằng `https://`. Mỗi `name` server phải được **đúng một** `mcp_toolset` tham chiếu. Tính năng đang beta và không đủ điều kiện ZDR.
- **[docs]** Muốn dùng stdio, resource hay prompt với API thì tự quản lý kết nối MCP client (SDK có helper chuyển kiểu MCP sang kiểu Claude API).

## 7. Scope: ai nạp server

Scope quyết định **người dùng và project nào nạp server**. Mỗi scope ứng với một nơi lưu cấu hình.

| Scope | Lưu ở đâu | Ai thấy | Hợp khi |
|---|---|---|---|
| **Local** (mặc định) | `~/.claude.json`, dưới đường dẫn của project hiện tại | Chỉ project này, **không** chia sẻ với đồng nghiệp | Server gắn với một ngữ cảnh project mà bạn chưa muốn commit, hoặc tool chỉ có nghĩa trong một project |
| **User** | Cài đặt cá nhân (docs: cũng là `~/.claude.json`) | **Mọi project** của bạn; vẫn cá nhân, không vào repo | Tiện ích cá nhân dùng ở mọi codebase (công cụ database cục bộ, script bạn hay dùng) |
| **Project** | `.mcp.json` ở root repo | Mọi người clone repo (khi file được commit) | Server cả nhóm dùng: cấu hình **đi cùng code** |
| **Enterprise** | Cấu hình quản lý tập trung do admin kiểm soát | Mọi người dùng trong tổ chức, không cần cấu hình từng người | Dịch vụ nội bộ dùng chung, công cụ bảo mật, thứ bắt buộc phải có và không thể để từng dev tự cấu hình |

- **Lưu ý của tài liệu về project scope:** server project **chạy từ máy của từng người**. Với server stdio, file đã commit chỉ lưu **lệnh khởi chạy**, mỗi bản clone tự sinh tiến trình con cục bộ, nên **mỗi người phải cài sẵn runtime** (ví dụ Node cho server chạy bằng `npx`).
- Nối với note plugin: plugin cũng có 3 scope user / project / local với cùng ý tưởng.
- **[docs]** Đặt scope bằng `--scope local|project|user`, ví dụ `claude mcp add --transport http stripe --scope project https://mcp.stripe.com`.
- **[docs] Thứ tự ưu tiên** khi cùng một server được định nghĩa ở nhiều nơi: **local, rồi project, rồi user, rồi plugin, rồi claude.ai connectors**. Claude Code dùng **toàn bộ entry** từ nguồn cao nhất, **không gộp từng field**. Ba scope đầu khớp theo **tên**; plugin và connector khớp theo endpoint.
- **[docs] Duyệt server project:** trong phiên tương tác, Claude Code **hỏi duyệt** trước khi dùng server trong `.mcp.json`; reset lựa chọn bằng `claude mcp reset-project-choices`. **Cảnh báo:** trong `claude -p`, Agent SDK và cloud session không hiện được prompt nên server project được nạp **mà không hỏi**. Muốn chặn dùng `disabledMcpjsonServers`, `--setting-sources` hoặc `--strict-mcp-config`. Repo vừa clone không tự duyệt được server của chính nó: `enableAllProjectMcpServers` và `enabledMcpjsonServers` trong `.claude/settings.json` bị bỏ qua ở thư mục chưa trust.
- **[docs] Enterprise:** `managed-mcp.json` và `managedMcpServers` (ưu tiên **trên mọi scope**, cần Claude Code v2.1.259 trở lên); có `allowedMcpServers` và `deniedMcpServers` để giới hạn. Server bị chặn hiện `✘ Blocked by enterprise managed policy`. Chi tiết ở trang managed MCP riêng của docs, mình chưa đọc.

## 8. Permission rule nhắm vào một tool MCP, không phải cả server

- Kết nối server là lộ ra **toàn bộ danh sách tool**, nhưng hiếm khi bạn muốn agent dùng hết mà không hỏi. Lớp permission ở note Permission Modes mở rộng cho tool MCP, và rule có thể nêu **từng tool**.
- Định danh trong rule: `mcp__server__tool`.
  - Allow `mcp__github__create_issue`: tool đó chạy không cần hỏi, các tool khác của server GitHub vẫn hỏi.
  - Deny một tool có thể ghi: chặn tool đó, các tool chỉ đọc cùng server vẫn dùng được.
  - **Deny một tool thắng allow cả server.**
- **[docs] Cú pháp:**

| Rule | Khớp |
|---|---|
| `mcp__puppeteer` hoặc `mcp__puppeteer__*` | Mọi tool của server `puppeteer` |
| `mcp__puppeteer__puppeteer_navigate` | Một tool cụ thể |
| `mcp__github__get_*` | Các tool `get_` của GitHub (glob chỉ hợp lệ sau tiền tố `mcp__<server>__`) |

- **[docs]** Chi tiết cần nhớ:
  - Thứ tự đánh giá **deny, rồi ask, rồi allow**; khớp đầu tiên thắng. Allow **không khoét được ngoại lệ** trong deny (ask cũng thắng allow). Khớp với câu của tài liệu.
  - Allow glob không neo như `mcp__*` bị **bỏ qua** (không tự duyệt gì), nhưng **deny** `mcp__*` dùng được.
  - Rule MCP **không có specifier trong ngoặc**: rule có ngoặc bị bỏ qua khi nạp settings. Muốn khớp tham số của tool MCP chỉ có cách dùng `--disallowedTools`.
  - Tên server có `.` hoặc khoảng trắng đổi thành `_` (`my.server` thành `mcp__my_server__*`); server của plugin viết `mcp__plugin_<plugin>_<server>__*`; connector từ claude.ai là `mcp__claude_ai_<server>__<tool>`.
  - Hook `PreToolUse` **không vượt được** rule: deny hoặc ask vẫn áp dụng dù hook trả `allow` (nối với note W3D1 về hook).
- **Hai loại control khác nhau** (nên dùng chung):

| | Permission rule (Claude Code) | Cờ `enabled` của `mcp_toolset` (API) |
|---|---|---|
| Quyết định | Tool **đã lộ ra** có được **chạy** không | Model có **thấy** tool không |
| Loại control | Governance | Chi phí context và phạm vi |

- **[docs] `mcp_toolset` trong Messages API:** `default_config.enabled` áp cho cả tập tool, `configs.<tên-tool>.enabled` ghi đè từng tool (mặc định `true`). Thứ tự ưu tiên: `configs` > `default_config` > mặc định hệ thống. Mẫu allowlist: `default_config: {"enabled": false}` rồi bật từng tool trong `configs`. Mỗi tool còn có `defer_loading` (mô tả tool không gửi cho model ngay, dùng với tool search; nối với mục 6).
- **Cần kiểm tra trước khi dùng thật** (khóa học dặn): cú pháp rule và beta header. **[docs]** Metadata trang connector ghi hai header: `mcp-client-2025-11-20` và `mcp-client-2026-09-15` (thêm khả năng ghim danh sách tool trong `tools` của toolset); `mcp-client-2025-04-04` đã deprecated. Chưa chạy thử.

## 9. GitHub MCP server: transport, scope, xác thực trong một ví dụ

- Server từ xa do GitHub duy trì: review pull request, mở issue, tìm code... **Transport HTTP** vì host từ xa; đăng ký bằng URL của server.
- **Scope:** project nếu cả nhóm cần cùng công cụ repo; local nếu chỉ mình bạn.
- **Xác thực: Personal Access Token (PAT)** tạo trên GitHub, gửi làm **Bearer token** trong header của cấu hình MCP. Token phải đi qua **biến môi trường** và được tham chiếu trong file cấu hình, **không** ghi thẳng vào `.mcp.json`: token ghi vào file đã commit sẽ vào lịch sử git và **không xóa được bằng cách ghi đè file ở commit sau**.
- **[docs]** URL: `https://api.githubcopilot.com/mcp/`. Lệnh trong docs:
  `claude mcp add --transport http github https://api.githubcopilot.com/mcp/ --header "Authorization: Bearer YOUR_GITHUB_PAT"` (docs dùng fine-grained PAT; `YOUR_GITHUB_PAT` chỉ là chỗ giữ chỗ). Lệnh không kiểm tra credential; xác nhận bằng `/mcp`: dấu ✓ là kết nối được, token sai hiện ✘ kèm HTTP status (ví dụ 401).
- **[docs] Mở rộng biến trong `.mcp.json`:** `${VAR}` và `${VAR:-giá-trị-mặc-định}`, dùng được trong `command`, `args`, `env`, `url`, `headers`. Ví dụ `"Authorization": "Bearer ${API_KEY}"`.
  - Biến chưa đặt và không có mặc định: config vẫn nạp, cảnh báo ở `claude mcp list` và `/mcp`, chuỗi `${VAR}` được dùng nguyên văn. Chuỗi rỗng tính là đã đặt.
  - Một số biến credential (ví dụ `ANTHROPIC_API_KEY`, `NPM_TOKEN`) luôn đọc ra rỗng trong `url` và `headers` từ xa, để `.mcp.json` của một repo không gửi credential của bạn tới server nó chỉ định. Tên như `API_KEY` mở rộng bình thường.
- **[ngoài tài liệu]** Docs không có ví dụ GitHub dùng biến môi trường; dạng `Bearer ${GITHUB_PAT}` là suy ra từ quy tắc mở rộng biến, nên thử rồi kiểm tra bằng `/mcp`.
- **[ngoài tài liệu] Cạm bẫy khi gõ lệnh `claude mcp add`:** nếu ghi `"Bearer ${GITHUB_PAT}"` trong dấu nháy **kép**, shell (bash lẫn PowerShell) có thể mở rộng hoặc làm rỗng biến **trước khi** Claude Code nhận, nên token thật có thể bị ghi vào cấu hình hoặc cấu hình mất tham chiếu. Dùng dấu nháy **đơn**, hoặc sửa `.mcp.json` bằng tay. Nếu lỡ commit token: **thu hồi hoặc đổi token trên GitHub trước**, vì xóa khỏi file không xóa khỏi lịch sử.
- **OAuth** là cơ chế khác, dùng khi dịch vụ xác thực **từng người dùng** qua đăng nhập trên trình duyệt. Ví dụ khóa học: **Linear**: lần đầu kết nối, client chuyển tới trang đăng nhập; sau khi bạn duyệt, token được cấp và lưu tự động, không sao chép tay.
- **[docs]** Cách làm OAuth: thêm server rồi chạy `/mcp` và làm theo đăng nhập trình duyệt (docs dùng **Sentry** làm ví dụ, không có Linear). Token được lưu an toàn và tự làm mới; "Clear authentication" trong menu `/mcp` để thu hồi; từ shell dùng `claude mcp login <tên>` và `claude mcp logout <tên>`. `claude mcp remove` xóa token đã lưu nhưng **không thu hồi tại nhà cung cấp**; muốn thu hồi thì chạy `logout` trước.
- **So sánh:** GitHub MCP dùng **service credential bạn tự tạo và lưu**; Linear MCP **khởi tạo luồng đăng nhập** lo credential giúp bạn. Cả hai là server HTTP từ xa và theo cùng logic transport và scope; chỉ **bước xác thực** khác nhau.
- **[docs] Với API:** connector nhận OAuth token qua `authorization_token`, nhưng **bạn phải tự lo luồng OAuth và làm mới token**. Với Managed Agents: mỗi session cấp credential bằng cách tham chiếu **vault**, nên secret không nằm trong định nghĩa agent.

## 10. Bảng tra cứu setup MCP (theo tài liệu)

| Bối cảnh | Transport | Scope | Nơi cấu hình | Xử lý secret |
|---|---|---|---|---|
| Tool cá nhân chạy cục bộ (chỉ trên máy bạn) | stdio | Local | `~/.claude.json` (entry theo project) | Chỉ biến môi trường, **không** ghi vào file cấu hình |
| Server dùng chung của nhóm (mọi người nối cùng một dịch vụ) | HTTP | Project (`.mcp.json`) | `.mcp.json` commit ở root repo | OAuth hoặc biến môi trường; **không bao giờ** commit API key vào `.mcp.json` |
| Thử nghiệm cá nhân (chưa muốn chia sẻ) | stdio hoặc HTTP | Local | Cài đặt cá nhân của Claude | Chỉ biến môi trường |
| Triển khai toàn tổ chức (do admin quản lý) | HTTP | Enterprise | Managed settings (admin kiểm soát) | Admin quản lý secret; cấu hình khóa để không bị ghi đè |

Cách nhớ: **transport theo nơi server chạy, scope theo ai cần dùng, secret luôn đi bằng biến môi trường hoặc OAuth, không bao giờ nằm trong file đã commit.**

## 11. Còn lại và việc cần kiểm tra

- **Chưa có trong đoạn đã nhận:** hướng dẫn **xây** một MCP server (tiêu đề tài liệu có nhắc "Building"). Bổ sung khi nhận phần tiếp.
- Chưa thực hành: kết nối GitHub MCP (HTTP, token qua biến môi trường), kiểm tra bằng `/mcp`; thử rule `mcp__github__<tool>` allow và deny để thấy deny thắng allow.
- Cần xác nhận khi làm thật: dạng `Bearer ${GITHUB_PAT}` trong `.mcp.json` có mở rộng đúng không; dấu nháy khi gõ `claude mcp add` trên PowerShell.
- Chưa đọc trang managed MCP (`managed-mcp.json`, `managedMcpServers`, `allowedMcpServers`, `deniedMcpServers`) và phần cuối của trang docs MCP.
- Đã giải quyết: tool MCP trong **Messages API** kết nối qua MCP connector (mục 6.1). Còn mở: server MCP đổi danh sách tool giữa chừng (`list_changed`) có làm đổi tiền tố cache không (xem NOTES_W3D2_Prompt_Caching_RAG.md); mình chưa kiểm chứng cách Claude Code xử lý.
- Chưa thực hành: kết nối một MCP server vào Claude Code, thử `@resource` và `/mcp__...prompt`.
