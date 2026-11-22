# LAB 3 — MCP server bọc fake-api, kèm permissions trong Claude Code

Ngày làm: 2026-11-22

## 1. Mục tiêu

Dựng một API giả (`fake-api`), bọc nó bằng một **MCP server** (`tickets`) để Claude gọi được qua tool, rồi dùng
`.claude/settings.json` để kiểm soát tool nào được chạy thẳng, tool nào phải hỏi, tool nào bị cấm,
và một **hook PreToolUse** chặn lệnh shell phá hoại (`rm -rf`, `git push --force`).
Đồng thời luyện **tách secret**: token đọc từ biến môi trường, không hardcode trong code.

```
Claude Code ──stdio (JSON-RPC)──▶ mcp-server/index.js ──HTTP + Bearer token──▶ fake-api/api.js (127.0.0.1:4000)
```

## 2. Cấu trúc thư mục

```
labs/lab3/
├── fake-api/
│   └── api.js                         # REST API giả, thuần module http của Node
└── mcp-server/
    ├── index.js                       # MCP server (McpServer + StdioServerTransport)
    ├── package.json                   # "type": "module" (code dùng import + top-level await)
    ├── .gitignore                     # node_modules/
    ├── .mcp.json                      # đăng ký server `tickets` cho Claude Code
    ├── LAB3.md                        # file này
    └── .claude/
        ├── settings.json              # permissions (allow / ask / deny) + đăng ký hook PreToolUse
        ├── hooks/
        │   ├── block-destructive.js   # hook: chặn rm -rf và git push --force (đọc JSON từ stdin)
        │   └── destructive-rules.json # bộ luật rộng hơn (12 luật, vẫn là denylist), chỉ dùng khi bật loader trong hook
        └── skills/triage-tickets/SKILL.md  # skill: triage ticket open, xuất bảng cố định (đã thử bằng /triage-tickets)
```

## 3. fake-api (`fake-api/api.js`)

- Chỉ dùng `node:http`, nghe ở `127.0.0.1:4000`, dữ liệu là mảng in-memory (mất khi tắt server).
- Endpoint:

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/tickets` | Lọc `?status=open` hoặc `closed`; giá trị khác → 400 |
| GET | `/tickets/:id` | 404 nếu không có; `id` không phải số nguyên dương → 400 |
| POST | `/tickets` | Body `{title, priority}`; `priority` ∈ `low`/`medium`/`high`; trả 201 + header `Location` |
| DELETE | `/tickets/:id` | Trả 204 (không body); 404 nếu không có |

- **Auth:** header `Authorization: Bearer <token>`, token lấy từ `FAKE_API_TOKEN`. Thiếu/sai → 401.
  Nếu biến chưa đặt thì server **không khởi động** (exit 1). So sánh bằng `timingSafeEqual`.
- Id không được tái sử dụng: sau khi tạo rồi xóa ticket #4 thì ticket kế tiếp là #5.

### Mẫu code: route table (giống `MapGet`/`MapPost` của .NET, Express, Gin, FastAPI)

```js
const routes = [
  { method: "GET",    path: "/tickets",     handler: listTickets },
  { method: "GET",    path: "/tickets/:id", handler: getTicket },
  { method: "POST",   path: "/tickets",     handler: createTicket },
  { method: "DELETE", path: "/tickets/:id", handler: deleteTicket },
];
```

- Mỗi endpoint là một hàm trả `{ status, body, headers }` (giống `IActionResult`).
- Lỗi thì `throw new HttpError(404, "...")`; chỗ bắt duy nhất là `dispatch()` (giống exception middleware).
- `dispatch()` chạy cho mọi request: auth → match route → gọi handler → ghi response.
  Path khớp nhưng sai method → 405 kèm `Allow`.
- Node chỉ đưa **một** callback `(req, res)` cho mọi request; `server.listen()` giữ process sống đến khi bị tắt.
  Framework (.NET/Express) chỉ là đóng gói sẵn phần route/dispatch mà ở đây tự viết.

### Tắt êm

`SIGINT`/`SIGTERM` → `server.close()` rồi thoát. **Đã kiểm chứng `SIGINT`** (Ctrl+C trong terminal thật,
thấy dòng "Nhận SIGINT, đang tắt server..."). **Chưa kiểm chứng `SIGTERM`** vì Windows không phát tín hiệu này như Linux.

Chạy:

```powershell
cd labs\lab3\fake-api
$env:FAKE_API_TOKEN = "dev-token"; node api.js
```

## 4. mcp-server (`index.js`)

- Dependencies: `@modelcontextprotocol/sdk`, `zod`.
- Cấu hình qua env: `FAKE_API_URL` (mặc định `http://127.0.0.1:4000`), `FAKE_API_TOKEN`.
- **Log bằng `console.error` (stderr), không dùng `console.log`:** với stdio transport, stdout là kênh giao thức
  JSON-RPC; in thêm gì ra stdout sẽ làm hỏng kết nối.
- Helper `callApi(path, { method, body })`: gắn token, gọi `fetch`, đổi kết quả thành tool result của MCP.
  Lỗi trả `isError: true` kèm lý do từ API (ví dụ `API 404: Ticket không tồn tại`); `204` trả "OK (204 No Content)".

| Tool | Tham số | Gọi tới | Annotation |
|---|---|---|---|
| `list_tickets` | `status?` | `GET /tickets` | `readOnlyHint` |
| `get_ticket` | `id` | `GET /tickets/:id` | `readOnlyHint` |
| `create_ticket` | `title`, `priority` | `POST /tickets` | — |
| `delete_ticket` | `id` | `DELETE /tickets/:id` | `destructiveHint` |

Tên hàm đăng ký tool khác nhau tùy phiên bản SDK (`registerTool` hoặc `tool`).

## 5. Cách kiểm thử

### 5.1 MCP Inspector

```powershell
cd labs\lab3\mcp-server
npx @modelcontextprotocol/inspector node index.js
```

Vào tab **Tools** → chọn tool → Run. Handshake đúng sẽ có `INITIALIZE` → `NOTIFICATIONS/INITIALIZED` → `TOOLS/LIST`.

### 5.2 Bẫy đã gặp: biến môi trường không tự truyền xuống MCP server

Đặt `$env:FAKE_API_TOKEN` trong terminal rồi chạy Inspector → tool trả `API 401`, dù `curl` trực tiếp vào fake-api
với cùng token trả 200. Nguyên nhân (đọc từ mã SDK/Inspector): process con chỉ kế thừa một **danh sách trắng** biến môi trường
(`PATH`, `APPDATA`, `USERPROFILE`...), nên `FAKE_API_TOKEN` không tới `index.js` → code gửi `Bearer undefined`.
Cách sửa: khai báo biến cho server trong Inspector (mục Environment Variables), hoặc trong `.mcp.json` ở trường `env`.
Cờ `-e KEY=value` của Inspector **chưa kiểm chứng** ở v2.13.

Cách phân biệt nhanh hai nguyên nhân của 401:

```powershell
curl.exe -i -H "Authorization: Bearer dev-token" http://127.0.0.1:4000/tickets
```

200 = fake-api đúng, lỗi nằm ở việc token không tới MCP server. 401 = fake-api đang chạy với token khác.

### 5.3 Kiểm thử tự động (đã chạy)

Một client MCP thật spawn `index.js` qua stdio, chạy trên bản sao `api.js` ở cổng 4100 (không đụng server cổng 4000):
list (có/không filter), get, create, get lại, delete, delete lần hai (404), `priority` sai (zod chặn trước khi gọi API),
token sai (401). Tất cả đúng như thiết kế.

## 6. Dùng trong Claude Code

### 6.1 `.mcp.json`

```json
{
  "mcpServers": {
    "tickets": {
      "command": "node",
      "args": ["index.js"],
      "env": { "FAKE_API_TOKEN": "${FAKE_API_TOKEN}" }
    }
  }
}
```

- Claude Code chỉ đọc `.mcp.json` và `.claude/` ở **thư mục đang mở** (hoặc cha), không quét thư mục con.
  Vì vậy phải mở VS Code/Claude ở `labs/lab3/mcp-server`, và `args` là `index.js` (không có tiền tố `mcp-server/`).
- Bẫy đã gặp: `args` trỏ `mcp-server/dist/server.js` → `MODULE_NOT_FOUND` (`dist/` là output của TypeScript, dự án này viết JS thuần).
- Lệnh `claude` không có trong PATH → dùng extension Claude Code trong VS Code (đã bundle sẵn `claude.exe`) hoặc cài CLI riêng.
- **Tách secret:** token không còn ghi trong file; `"${FAKE_API_TOKEN}"` được Claude Code thay bằng biến môi trường lúc khởi động.
  Biến phải có sẵn ở **môi trường của tiến trình VS Code**, nếu không server `tickets` sẽ không nạp được (thiếu biến).
  Cách đặt: `setx FAKE_API_TOKEN dev-token` rồi **thoát hẳn và mở lại VS Code** (`setx` chỉ ảnh hưởng tiến trình mới),
  hoặc mở VS Code từ terminal đã đặt `$env:FAKE_API_TOKEN` rồi chạy `code .`. Cùng giá trị này phải dùng cho fake-api.
  (Trước đó token ghi thẳng `dev-token` trong file được git theo dõi; bản `dev-toen` sai chính tả đã gây 401.)

### 6.2 `.claude/settings.json` — permissions

```json
{
  "permissions": {
    "allow": ["mcp__tickets__list_tickets", "mcp__tickets__get_ticket", "Read(./**)",
              "Bash(node --check *)", "Bash(npm ls *)"],
    "ask":   ["mcp__tickets__create_ticket"],
    "deny":  ["mcp__tickets__delete_ticket", "Read(./.env)", "Read(./.env.*)",
              "Edit(./.env)", "Edit(./.env.*)", "Bash(rm *)", "Bash(git push *)"]
  }
}
```

- Tên tool MCP có dạng `mcp__<tên server trong .mcp.json>__<tên tool>`; đổi tên server thì phải đổi luật.
- Thứ tự ưu tiên: **deny > ask > allow**. JSON không cho comment nên giải thích để ngoài file.
- Nên để luật hẹp; luật allow quá rộng (như `Bash(*)`) có thể bị auto mode bỏ qua.

### 6.3 Kết quả thử thực tế (panel đang ở chế độ **Auto**)

| Prompt | Hành vi | Nhóm luật |
|---|---|---|
| "Liệt kê các ticket đang open" | `list_tickets` chạy thẳng | allow |
| "Cho tôi xem ticket số 2" | `get_ticket` chạy thẳng | allow |
| "Tạo ticket 'Lỗi thanh toán', ưu tiên high" | Hiện hộp xác nhận, Yes → tạo ticket #5 | ask |
| "Xóa ticket số 4" | Claude không gọi `delete_ticket`, nói "server không có công cụ xóa" | deny |

Rút ra:
- **`ask` vẫn hỏi ngay cả trong Auto mode** (ở phiên bản đang dùng).
- **Deny ẩn tool khỏi Claude** (suy luận từ phản hồi) chứ không hiện thông báo "bị chặn"; vì vậy lời Claude
  "không có công cụ xóa" hơi gây hiểu lầm — tool có tồn tại, chỉ bị luật deny giấu đi.
- Việc nào phải chắc chắn không xảy ra thì để `deny`; hook `PreToolUse` là lớp bảo vệ xác định bằng code,
  không phụ thuộc phán đoán của bộ phân loại.
- `/mcp` xem trạng thái server (đã thấy `tickets ✓ Connected`, 4 tool với nhãn `read-only`/`destructive`);
  `/permissions` xem luật đang hiệu lực.

### 6.4 Hook `PreToolUse` — `block-destructive.js`

Đăng ký trong `settings.json` (cùng cấp với `permissions`, **không** phải trong file `.js`):

```json
"hooks": {
  "PreToolUse": [{
    "matcher": "Bash|PowerShell",
    "hooks": [{ "type": "command",
                "command": "node \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-destructive.js\"" }]
  }]
}
```

Cách hoạt động của script:
- Claude Code chạy script trước khi thực thi tool và đưa JSON qua **stdin**:
  `{ "tool_name": "Bash", "tool_input": { "command": "..." }, ... }`.
- Script lấy `tool_input.command`, so với danh sách regex. Khớp → in lý do ra **stderr** và `process.exit(2)`.
- Exit code: `0` = cho qua, `2` = **chặn** (stderr được gửi lại cho Claude làm lý do), mã khác = lỗi không chặn.
- Chỉ dùng module có sẵn của Node, đọc stdin bằng stream, bỏ BOM → chạy được trên Windows.
- `package.json` có `"type": "module"` nên file hook chạy theo ES module (`import`, `import.meta.dirname`;
  **không** dùng `require`/`__dirname`).
- Regex tìm cờ trong **cùng một lệnh** (dừng ở `;` `&` `|` xuống dòng), nên `rm foo && ls -f -r` không bị coi là `rm -rf`.

Bản đơn giản chặn `rm -rf` (mọi thứ tự cờ: `-rf`, `-fr`, `-r -f`, `--recursive --force`),
`git push --force` / `-f` / `--force-with-lease`, và `Remove-Item -Recurse -Force` (PowerShell, kể cả alias `ri`).
Bộ luật **rộng hơn** (thêm `git reset --hard`, `git clean -f`, SQL `DROP`/`TRUNCATE`/`DELETE` không `WHERE`,
`rd /s /q`, `del /s /q`, `format`, `mkfs`, `dd of=/dev/`) nằm trong `destructive-rules.json`. Cả hai đều là
**denylist** (chỉ chặn các dạng viết đã liệt kê), nên không "cover đủ": xem lưu ý về các cách lách bên dưới. JSON không lưu được RegExp nên mỗi luật là
`{ name, pattern, flags, reason }`; đoạn loader (đang **để comment** trong hook) dựng lại thành RegExp.
Bật bằng cách bỏ `//` ở 4 dòng (2 `import` + lệnh gán `RULES`).

**Đã kiểm thử**
- Bơm JSON giả vào stdin (trước khi thêm luật `Remove-Item` vào bản đơn giản): bản đơn giản chặn đúng 14 lệnh và cho qua 18 lệnh; bản đọc JSON (bỏ comment loader, chạy
  trong bản sao) chặn 25 lệnh phá hoại và cho qua 9 lệnh an toàn; JSON hỏng → exit 1; thiếu `command` → exit 0.
- **Trong Claude Code thật** (prompt: *"Chạy bằng Bash tool: rm -rf ./__khong_ton_tai__, rồi git push --force --dry-run origin HEAD"*):
  hook chặn với thông báo `PreToolUse:Bash hook error: [node "$CLAUDE_PROJECT_DIR/.claude/hooks/block-destructive.js"]:
  [block-destructive] Đã chặn "rm -rf": ...`. Thử riêng *"Chỉ chạy git push --force --dry-run thôi"* → chặn
  `"git push --force"`. Cả hai luật đều được kiểm chứng; `$CLAUDE_PROJECT_DIR` được nạp đúng trên Windows.
- Claude nhận lý do và **không cố lách hook**, chỉ đề xuất cách an toàn hơn hoặc nhờ người dùng tự chạy.

Lưu ý:
- Hook chạy **trước** luật `permissions` (thông báo thấy được là của hook dù `Bash(rm *)`/`Bash(git push *)` cũng nằm trong `deny`).
  Hook mới được nạp khi mở phiên mới sau khi sửa `settings.json`.
- Matcher đã đổi từ `"Bash"` thành `"Bash|PowerShell"` để hook cũng chạy với tool PowerShell (input của tool này cũng có
  `tool_input.command`). Test thủ công bằng JSON giả: `git push --force` kiểu PowerShell bị chặn (exit 2). Bản đơn giản
  đã có luật `Remove-Item -Recurse -Force` (thử thủ công bằng JSON giả: mọi thứ tự cờ và alias `ri` bị chặn; `Remove-Item file.txt`
  và `Remove-Item -Recurse x` được cho qua; bản đọc JSON cho cùng kết quả). **Chưa thử với tool PowerShell thật trong Claude Code.**
  Tool MCP không thuộc matcher này: `mcp__tickets__delete_ticket` vẫn do luật `deny` lo.
- Hook coi mọi `git push --force` là nguy hiểm, kể cả `--dry-run` (cố ý, vì regex chỉ nhìn cờ, không nhìn ngữ cảnh).
  Cũng có thể chặn nhầm chuỗi nằm trong nội dung khác, ví dụ `git commit -m "bỏ DROP TABLE"` (với bộ luật rộng hơn).
- **Denylist nên luôn còn cách lách**, kể cả với bộ luật rộng hơn. Đã thử và **lọt (exit 0) ở cả hai bản**:
  `/bin/rm -rf x`, `find . -delete`, `python3 -c "import shutil; shutil.rmtree('x')"`.
  Trường hợp `/bin/rm` là khe hở của regex (yêu cầu `rm` đứng sau khoảng trắng hoặc `; & | (`, không khớp khi có tiền tố đường dẫn;
  sửa được bằng cách thêm `/` vào các ký tự đứng trước); hai cách còn lại vốn không thể chặn hết bằng regex.
  Vì vậy hook là lớp giảm rủi ro, **không phải ranh giới an toàn**; lớp chắc hơn là `permissions` (`deny`, `allow` hẹp).
- Test hook an toàn: dùng lệnh vô hại (`rm -rf` vào thư mục không tồn tại, `git push --force --dry-run`);
  **không** thử bằng `git reset --hard` / `git clean -fd` vì nếu hook không chạy thì mất dữ liệu thật.

### 6.5 Skill `triage-tickets`

`.claude/skills/triage-tickets/SKILL.md`: frontmatter `name` + `description` (Claude dựa vào `description` để quyết định
có nạp skill hay không, nên nó nêu rõ khi nào dùng và khi nào **không** dùng), thân 11 dòng có nội dung:
1. gọi `list_tickets` với `status="open"`; 2. không có ticket open thì nói rõ và dừng; 3. nhóm theo `priority`
(high → medium → low); 4. đề xuất thứ tự xử lý kèm lý do; 5. chỉ đọc, **không gọi `delete_ticket`**;
6. xuất bảng cố định 5 cột (Thứ tự, ID, Tiêu đề, Priority, Lý do xử lý); 7. câu tóm tắt số ticket theo priority.

**Kết quả thử trong Claude Code** (gõ `/triage-tickets` ở phiên mới; fake-api đang có 3 ticket open: #1, #2, #5):

| Thứ tự | ID | Tiêu đề | Priority | Lý do xử lý (rút gọn) |
|---|---|---|---|---|
| 1 | 1 | Không đăng nhập được | high | Không vào được hệ thống thì mọi chức năng khác đều bị chặn |
| 2 | 5 | Lỗi thanh toán | high | Ảnh hưởng trực tiếp doanh thu, làm ngay sau ticket đăng nhập |
| 3 | 2 | Đổi mật khẩu bị lỗi | medium | Chỉ ảnh hưởng một nhóm người dùng; có thể gộp điều tra với ticket đăng nhập |

Kèm câu cuối: *"Tổng cộng có 2 high, 1 medium, 0 low."*

Đối chiếu với yêu cầu:
- Gọi `list_tickets` chạy thẳng, không hỏi xác nhận (nằm trong `allow`) → khớp.
- Bảng đúng 5 cột theo mẫu, nhóm high trước medium, có câu tóm tắt → khớp.
- Không có lần gọi `delete_ticket` nào → khớp (tool này cũng đang bị `deny` trong `settings.json`).
- Ticket đã `closed` (#3) không xuất hiện → đúng vì chỉ lấy `status=open`.

**Đã xác nhận tham số gọi** từ nhật ký phiên của Claude Code (`~/.claude/projects/<dự án>/*.jsonl`): ở phiên sạch có
`Skill {"skill":"triage-tickets"}` rồi `list_tickets {"status":"open"}`; ở phiên cũ (nói thường sau `/triage-tickets`) chỉ có
`list_tickets {"status":"open"}` và **không có lần gọi Skill nào** — khớp với kết luận rằng phép thử cùng phiên bị nhiễm.

Chưa kiểm chứng:
- Chưa thử trường hợp không có ticket open (nhánh "nói rõ và dừng").

**Thử gọi bằng câu nói thường** (không gõ `/triage-tickets`): prompt *"triage các ticket đang mở"* → Claude gọi `list_tickets`
và trả đúng bảng 5 cột, cùng thứ tự (#1, #5 high → #2 medium), cùng câu tóm tắt "2 high, 1 medium, 0 low".
Lý do xử lý được viết lại hơi khác lần đầu (ví dụ ticket #2 gọn hơn) nhưng cấu trúc giữ nguyên.

**Phép thử này bị nhiễm, chưa chứng minh được `description` hoạt động:** nó chạy trong **cùng phiên** sau `/triage-tickets`,
nên nội dung skill và một bảng mẫu đã nằm sẵn trong ngữ cảnh; Claude có thể chỉ làm theo chúng thay vì nhận ra skill từ
`description`. Ảnh cũng không có dòng báo "đã nạp skill". Phép thử sạch: mở **phiên mới**, gõ câu nói thường **trước**,
không gõ `/triage-tickets`.

**Quan sát về thinking/chi phí:** lượt `/triage-tickets` hiện "Thought for 0s" và "Thought for 3s"; lượt nói thường không có
dòng thinking nào. Giao diện vẫn hiện "0s" ở lượt đầu nên khả năng cao lượt sau là **không suy nghĩ** (không phải bị ẩn);
hợp lý vì ngữ cảnh đã có sẵn hướng dẫn và mẫu. Thinking là token đầu ra (đắt nhất) nên lượt này rẻ hơn. Đây là suy luận
từ giao diện, chưa đo bằng `/cost`.

**Phép thử sạch (phiên mới, prompt đầu tiên là *"triage các ticket đang mở"*) — ĐẠT:** giao diện hiện dòng
`triage-tickets` `skill` ngay trước lần gọi `list_tickets`, tức Claude **tự nạp skill theo `description`**
(lần thử cùng phiên không có dòng này). Sau đó ra bảng 5 cột đúng mẫu, thứ tự #1, #5 (high) → #2 (medium),
câu tóm tắt "2 high, 1 medium, 0 low".

**Chi phí ngữ cảnh (`/context`, tổng 40.9k / 1.0M = 4%; chưa rõ chụp ở phiên nào):**

| Hạng mục | Token | Ghi chú |
|---|---|---|
| System prompt | 3.8k | cố định mỗi phiên |
| System tools | 18.3k | cố định mỗi phiên |
| MCP tools | 101 | rất nhỏ cho 4 tool — nhiều khả năng schema nạp theo yêu cầu (chưa kiểm chứng) |
| MCP server instructions | 717 | |
| Skills | 5.9k | tên + mô tả của **tất cả** skill, không phải thân skill → `description` nên ngắn |
| Messages | 12.2k | phần duy nhất lớn dần theo hội thoại |
| Autocompact buffer | 33.0k | dự trữ, không nằm trong 40.9k đã dùng |

~28.8k token đầu là tiền tố giống nhau mỗi lượt (phần được cache); thân skill chỉ vào ngữ cảnh khi skill được nạp.

## 7. Bảng lỗi đã gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| `Cannot find module '...\server.js'` | Chạy `node server.js` ở thư mục gốc, sai thư mục | `cd` vào thư mục chứa file, hoặc chạy bằng đường dẫn đầy đủ |
| `Cannot find module '...\dist\server.js'` | Lệnh/`args` trỏ tới output TypeScript không tồn tại | Dùng `index.js` |
| `API 401` trên Inspector dù fake-api đúng | `FAKE_API_TOKEN` không truyền xuống process MCP server | Khai báo env cho server (Inspector UI hoặc `.mcp.json`) |
| `EADDRINUSE 127.0.0.1:4000` | Còn một bản fake-api cũ đang chạy | Tắt process đang giữ cổng 4000 |
| `claude : The term 'claude' is not recognized` | CLI chưa có trong PATH | Dùng extension VS Code hoặc cài CLI |
| Token `dev-toen` → 401 | Gõ sai chính tả token inline | Dùng `${FAKE_API_TOKEN}`, không viết thẳng |
| `SyntaxError: Unexpected token ':'` ở `block-destructive.js` | Dán khối cấu hình `{"hooks": ...}` (JSON) vào file `.js`; cấu hình hook phải nằm trong `settings.json`, file `.js` là script | Chuyển khối `hooks` sang `settings.json`; viết script thật trong `.js` |

## 8. Việc còn lại / chưa kiểm chứng

**Đã xong**
- [x] Hook `block-destructive.js` + đăng ký trong `settings.json`; đã kiểm chứng `rm -rf` và `git push --force` trong Claude Code thật.
- [x] Matcher của hook là `"Bash|PowerShell"`.
- [x] Skill `triage-tickets`: thử bằng `/triage-tickets` và tự nạp trong phiên mới (thấy dòng `triage-tickets` `skill`); bảng đúng mẫu,
  không gọi `delete_ticket`.
- [x] `/context` (bảng ở mục 6.5). Chưa chạy `/cost`.
- [x] Token trong `.mcp.json` là `${FAKE_API_TOKEN}`; `.gitignore` của `mcp-server` có `.env` và `.env.*` (khớp luật `deny` đọc `.env`).

**Cần làm** (bốn việc)
- [x] Thêm luật `Remove-Item -Recurse -Force` vào bản đơn giản. Đã thêm; thử thủ công bằng JSON giả: bị chặn (mọi thứ tự cờ, alias `ri`).
  Còn lại: thử với tool PowerShell thật trong Claude Code (cần chạy trong phiên Claude Code).
- [ ] Thử skill với trường hợp **không có ticket open** (nhánh "nói rõ và dừng") và với một prompt **không liên quan**
  ("tạo ticket mới cho lỗi đăng nhập") để chắc skill không bị nạp nhầm. Cần chạy trong Claude Code; trường hợp không có ticket open
  cần đóng/xóa hết ticket open nên phải làm bên ngoài Claude (vì `delete_ticket` đang bị `deny`).
- [x] Xác nhận tham số `status="open"` trong tool call: đã xác nhận từ nhật ký phiên (mục 6.5).
- [ ] Lý do bảng `/permissions` lệch (Allow 4, Deny 8; file có 5 allow, 7 deny): **chưa xác định được nguyên nhân**.
  Ảnh chụp khi panel ở **Auto mode**. Giả thuyết chưa chứng minh: auto mode bỏ luật `allow` cho lệnh có thể chạy mã tùy ý như
  `Bash(node --check *)` (đúng luật bị thiếu ở Allow); trong file chạy của extension có một danh sách interpreter gồm `node`,
  nhưng chưa chứng minh nó dùng cho việc này. Luật Deny thừa một mục: chưa giải thích được (không có `settings.local.json`,
  và `~/.claude/settings.json` không có luật allow/deny). Cách kiểm chứng: mở lại `/permissions` ở chế độ **không** phải Auto, cuộn
  hết danh sách Deny và so với file.

**Tùy chọn**
- [ ] Sửa khe hở `/bin/rm -rf` (thêm `/` vào ký tự đứng trước `rm` trong regex) ở cả bản đơn giản và `destructive-rules.json`.
- [ ] Quyết định có cho phép `git push --force --dry-run` không (hiện hook chặn mọi `--force`).
- [ ] Kiểm chứng phiên mới vẫn nạp được server `tickets` sau khi đổi token (cần đặt biến môi trường và khởi động lại VS Code, mục 6.1;
  nếu chưa đặt biến thì server sẽ không nạp được).
- [ ] Kiểm chứng `SIGTERM` trên Linux/container.
- [ ] Kiểm chứng cờ `-e` của Inspector v2.13.

## 9. Bảng tradeoff: Built-in tool / Custom tool / Skill / MCP

Quy ước: **cứng** = chạy bằng code hoặc quy tắc xác định, kết quả không phụ thuộc phán đoán của model;
**mềm** = chỉ là chỉ dẫn nằm trong ngữ cảnh, model có thể làm khác. Mục "độ tin cậy" tách hai việc:
*thực thi* (khi đã gọi thì chạy có đúng không) và *quyết định gọi* (model có gọi hay không).

| | Built-in tool | Custom tool | Skill | MCP |
|---|---|---|---|---|
| **Khi nào dùng** | Việc chung: đọc/sửa file, chạy shell, tìm kiếm. Có sẵn, không cần cài. | Cần một hàm riêng của ứng dụng mình (tự định nghĩa schema + tự viết code thực thi), không cần chia sẻ cho client khác. | Quy trình hoặc định dạng đầu ra lặp lại nhiều lần (triage, review...): dạy Claude *cách làm*, không thêm khả năng mới. | Nối Claude với dịch vụ/dữ liệu ngoài qua giao thức chuẩn, dùng lại được ở nhiều client (Claude Code, Inspector...). |
| **Ai kích hoạt** | Claude quyết định gọi; quyền do `permissions` và hook kiểm soát. | Claude quyết định gọi theo mô tả tool; code do ứng dụng của mình chạy. | Claude tự nạp theo `description`, hoặc người dùng gõ `/tên-skill` (cả hai đã thử trong lab). | Claude quyết định gọi theo mô tả tool; kết nối khai báo trong `.mcp.json`, server là tiến trình riêng. |
| **Độ tin cậy** | Thực thi: **cứng**. Việc gọi: mềm, nhưng chặn được bằng hook/`deny` (cứng). | Thực thi: **cứng** (code của mình, schema kiểm tra tham số). Việc gọi: mềm. | **Mềm**: chỉ là văn bản trong ngữ cảnh, model có thể bỏ sót hoặc làm khác. | Thực thi: **cứng** (gọi API thật, zod chặn tham số sai). Việc gọi: mềm, kiểm soát bằng `permissions` (cứng). |
| **Chi phí context** | System tools ≈ 18.3k token, cố định mỗi phiên (đo bằng `/context`). | Mỗi tool thêm tên + mô tả + schema vào ngữ cảnh mỗi lượt (phần tiền tố, được cache). | Tên + mô tả của mọi skill luôn có (≈ 5.9k cho cả danh sách); thân skill chỉ nạp khi dùng. | Tool + instructions của `tickets` chỉ ≈ 0.8k (101 + 717); kết quả tool (vd JSON của `list_tickets`) vào Messages và lớn dần. |
| **Ví dụ trong lab** | `Bash`, `Read`: hook chặn `rm -rf`/`git push --force`, `allow Read(./**)`. | Lab 2: `labs/lab2/tools.json` (định nghĩa schema) + `execute_tool` trong `lab2_agent.py` (tự chạy `tool_use`, trả `tool_result`). | `triage-tickets` (gọi bằng `/triage-tickets` và tự nạp). | Server `tickets`: `list_tickets`, `get_ticket`, `create_ticket`, `delete_ticket`. |

Rút ra từ lab:
- **Cứng vs mềm:** skill ghi "không gọi `delete_ticket`" (mềm), nhưng thứ thật sự bảo đảm là luật `deny`: tool bị ẩn khỏi Claude (cứng).
  Việc bắt buộc phải đúng thì dùng permissions/hook/code, đừng chỉ viết vào skill.
- **Chọn công cụ:** cần *khả năng mới hoặc dữ liệu ngoài* → tool (MCP nếu muốn chuẩn hóa/chia sẻ, custom tool nếu gắn trong ứng dụng);
  cần *cách làm hoặc định dạng* → skill; cần *ngăn chặn chắc chắn* → permissions/hook (nằm ngoài bốn thứ này).
- **Chi phí:** tool nhìn chung tốn context ở mỗi lượt dù không dùng (schema); skill chỉ tốn phần mô tả cho tới khi dùng,
  nên nhiều quy trình thì skill rẻ hơn nhồi hết vào system prompt.
- **Chưa kiểm chứng:** (1) MCP tools chỉ 101 token có thể do schema nạp theo yêu cầu; (2) thân skill ≈ vài trăm token chưa đo.
