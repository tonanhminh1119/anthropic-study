# Notes Week 3 Day 2: Packaging Workflows (Skills, custom commands, plugin, marketplace)

Nguồn: tài liệu khóa học (phần "Packaging a workflow as a plugin: skills, custom commands, and marketplace install"), hiện có đoạn mở đầu, phần Skills và phần "How the skill loads and runs in each" (4 môi trường) phần "Three portability rules", và phần cuối: custom command, plugin, marketplace, bảng quyết định đóng gói. Phần đánh dấu **[docs]** là đối chiếu với docs hiện hành (đọc ngày 2026-11-17), **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung.

Liên hệ với note trước ([NOTES_W3D1_Durable_Project_Context.md](NOTES_W3D1_Durable_Project_Context.md)): note đó nói cách cấu hình `.claude` để agent biết gì và hành xử ra sao trong **một project**. Phần này giải quyết bài toán tiếp theo: đóng gói cấu hình đó để người khác cài trong một bước thay vì chép tay.

## 1. Bài toán: từ `.claude` của một project đến thứ cài được

- CLAUDE.md, rules, hooks, subagents nằm trong `.claude` và được version control cùng project, nên ai clone repo đều có.
- Khi đồng nghiệp muốn dùng cùng workflow ở **project khác hoặc máy khác**, cách cũ là chép file, sửa settings, dán hook bằng tay: dễ sai, khó cập nhật.
- Ba tầng của bài học: **skill** và **custom command** là thành phần; **plugin** là gói đựng chúng; **marketplace** là nơi phân phối gói.

## 2. Skill: workflow nạp theo nhu cầu

- Skill là một file Markdown `SKILL.md` trong `.claude/skills/<ten-skill>/`. **Front matter** nhận diện skill và mô tả khi nào áp dụng; **body** chứa các bước.

```markdown
---
name: review-pr
description: Dùng khi người dùng muốn review một pull request...
---

# Các bước
1. Lấy diff của PR
2. ...
```

- `description` quyết định agent có nạp skill hay không, nên phải nói cả skill **làm gì** và **khi nào dùng**.
- **[docs]** Nạp theo 3 mức (progressive disclosure):

| Mức | Nạp khi nào | Chi phí context |
|---|---|---|
| 1. Metadata (`name`, `description`) | Luôn có từ khởi động | ~100 token mỗi skill |
| 2. Body của `SKILL.md` | Khi skill được kích hoạt | dưới 5k token |
| 3. File đi kèm (`FORMS.md`, `scripts/`...) | Khi được tham chiếu | 0 cho đến khi đọc; script chỉ tốn token của **output** |

- Khác CLAUDE.md (luôn nạp toàn bộ), skill cho phép có nhiều quy trình mà không tốn context cho cái chưa dùng. Đây là nơi chuyển nội dung "không cần luôn nạp" ra khỏi CLAUDE.md, như note W3D1 đã nói.
- **[docs]** Ràng buộc field: `name` tối đa 64 ký tự, chỉ chữ thường, số, dấu gạch ngang, không chứa `anthropic` hay `claude`; `description` không rỗng, tối đa 1.024 ký tự.

## 3. Cùng một file, bốn môi trường

Tài liệu nhấn mạnh: **file `SKILL.md` không đổi**, cái đổi là (1) nó chạy ở đâu, (2) nạp bằng cách nào, (3) được phép đụng vào gì. Dev chỉ quen Claude Code dễ mặc định những điều không đúng trên API.

**[docs]** Bảng đối chiếu:

| | Claude Code / extension | Agent SDK | Messages API |
|---|---|---|---|
| Nơi chạy | Máy của bạn | Máy chạy tiến trình SDK | Container sandbox trên server |
| Nạp skill | Đọc từ `~/.claude/skills/`, `.claude/skills/` | Đọc từ đĩa theo `settingSources`; **không có API đăng ký bằng code** | Khai báo `container.skills` (`type`: `anthropic`/`custom`, `skill_id`, `version`), tối đa 20 skill/request; custom thì upload qua `/v1/skills` |
| Tool bắt buộc | Có sẵn tool Skill | Tool Skill (option `skills` tự thêm vào `allowedTools`) | **Bắt buộc** kèm tool `code_execution` |
| Mạng | Đầy đủ như chương trình trên máy | Như Claude Code | **Không có mạng, không cài thêm package** |
| Phạm vi chia sẻ | Cá nhân hoặc project; chia sẻ qua plugin | Như Claude Code | Cả workspace: mọi thành viên đều dùng được skill đã upload |

- **Skill không đồng bộ giữa các bề mặt.** Upload lên claude.ai không có trên API, skill API không có trên claude.ai, skill Claude Code (dựa trên file) tách riêng khỏi cả hai. Mỗi nơi phải quản lý riêng.
- **[docs]** Tài liệu bảo mật: chỉ dùng skill từ nguồn tin cậy; coi như cài phần mềm. Skill độc hại có thể điều khiển agent gọi tool hoặc chạy code sai mục đích, đặc biệt skill tải dữ liệu từ URL ngoài.

### Theo tài liệu khóa học: nạp thế nào, chạy ở đâu, cần biết gì

Câu hỏi gốc: skill **chạy ở đâu** thì biết nó **đụng được vào gì**. Claude Code và SDK chạy trên máy bạn; Messages API và Managed Agents chạy trong sandbox của Anthropic.

| | Nạp thế nào | Chạy ở đâu | Cần biết |
|---|---|---|---|
| **Claude Code** | Quét `.claude/skills`; kích hoạt khi mô tả khớp hoặc gọi theo tên | Terminal của bạn, file local, **dưới permission mode và deny rule đang bật** | Dựa trên filesystem, chịu sự điều khiển của lớp settings. Skill không phải đường vòng qua deny rule (xem note Permission Modes) |
| **Messages API** | Gửi kèm request, chạy trong container code execution. Tài liệu nói cần beta header cho code execution và skills | Container của Anthropic; filesystem và tool là những gì container cung cấp | Skill giả định file hay tool local sẽ hỏng vì không chạy nơi có chúng |
| **Agent SDK** | Agent do SDK chạy nạp; **settings từ filesystem (CLAUDE.md, skills) do `settingSources` / `setting_sources` quyết định** | Trong tiến trình SDK, tức môi trường của bạn, sau khi bảo nó nạp filesystem | Bẫy thường gặp: skill chạy ở Claude Code nhưng "không làm gì" ở SDK vì chưa đặt `settingSources`. **Luôn đặt tường minh**, đối chiếu mặc định hiện hành với Agent SDK reference khi build |
| **Managed Agents** | Định nghĩa một lần như API resource (model, system prompt, tools, MCP servers, skills); Anthropic nạp skill phía server, không có bước discovery phía bạn | Sandbox do Anthropic cấp; app gửi event và đọc kết quả stream về | Đang public beta, cần header `managed-agents-2026-04-01`. Session lưu phía server nên chưa đủ điều kiện ZDR hay HIPAA BAA. Skill gắn **lúc định nghĩa agent**, không phải lúc tạo session; đổi skill thì sửa định nghĩa agent |

**Đối chiếu với docs [docs], còn lệch cần kiểm tra:**
- **Beta header của Messages API:** tài liệu khóa học nói cần. Trang docs mình đọc (chưa hết trang) có ví dụ chỉ dùng `anthropic-version`, không nhắc beta header. Chưa kết luận được; kiểm tra khi viết code thật.
- **Mặc định của `settingSources`:** docs Agent SDK hiện nói mặc định nạp nguồn `user` và `project`. Lời dặn "đừng dựa vào mặc định" vẫn đúng như thực hành. Bẫy hay gặp khi đặt `settingSources` thủ công mà thiếu `"project"`. **[ngoài tài liệu]** Phiên bản SDK cũ có thể có mặc định khác; chưa kiểm chứng.
- **Managed Agents nạp skill:** docs overview nói attach skill vào mảng `skills` của agent **hoặc** nạp từ repo GitHub gắn vào session; tài liệu khóa học nói gắn lúc định nghĩa agent. Có thể là hai chế độ khác nhau; chưa rõ.
- ZDR: docs overview ghi riêng Agent Skills **không** thuộc ZDR, nên hạn chế này không chỉ có ở Managed Agents.

## 4. Gọi skill chủ động (không chỉ on-demand)

Có hai đường gọi: **model-invoked** (Claude tự chọn theo `description`) và **user-invoked** (bạn chỉ định).

**[docs]** Bảng theo môi trường:

| Môi trường | Gọi trực tiếp | Cách làm |
|---|---|---|
| Claude Code / extension | Có | Gõ `/ten-skill [args]` ở **đầu** tin nhắn |
| Agent SDK | Có | Gửi `"/ten-skill"` trong chuỗi `prompt` của `query()` |
| Messages API | **Không có cơ chế tương đương** | Chỉ chọn skill nào có mặt trong `container.skills` và nhắc tên trong prompt |

- Tên phải ở đầu tin nhắn. `go ahead and /deploy` không chạy trực tiếp, chỉ cấp cho Claude quyền dùng skill khi nó thấy phù hợp.
- Frontmatter kiểm soát ai được gọi:

| Frontmatter | Bạn gọi | Claude tự gọi |
|---|---|---|
| (mặc định) | Có | Có |
| `disable-model-invocation: true` | Có | Không |
| `user-invocable: false` | Không | Có |

- `disable-model-invocation: true` hợp với workflow có tác dụng phụ (ví dụ `/deploy`): bạn tự quyết thời điểm. Description của skill cũng không chiếm context. Nối với ghi chú W3D1 về chi phí context.
- `user-invocable: false` hợp với kiến thức nền, không phải một hành động (ví dụ `legacy-system-context`).
- Argument: `/fix-issue 123` thay `$ARGUMENTS` trong SKILL.md bằng `123`; có cả `$0`, `$1` theo vị trí.

**Lưu ý riêng cho Agent SDK [docs]:**
- Option `skills` (danh sách tên, `"all"`, `[]`) chỉ giới hạn skill nào **Claude** được tự gọi. Gửi `/<name>` vẫn chạy kể cả khi skill không có trong danh sách.
- Nếu đặt `settingSources` thủ công thì phải có `"project"` và `"user"`, nếu không skill không được nạp.
- Gõ sai tên thì `query()` **không báo lỗi**: Claude Code gửi nó cho model như tin nhắn thường kèm ghi chú lệnh không chạy, tốn một lượt gọi model. Kiểm tra `slash_commands` trong message `init` ngay từ đầu session.
- File lệnh cũ trong `.claude/commands/` vẫn chạy, hành vi như skill; skill là bản kế nhiệm được khuyến nghị.

**Ghi chú về độ chắc chắn:** trang API guide (`build-with-claude/skills-guide`) dài hơn 145k ký tự và mình chỉ đọc được 100k đầu. Kết luận "API không có cách ép một skill cụ thể" dựa trên phần đã đọc; phần còn lại chưa kiểm tra.

## 5. Đối chiếu với kiến thức API

- Trong Claude Code, skill chạy với **quyền của bạn** (shell, mạng, file local). Trên Messages API, skill chạy trong sandbox của `code_execution`, nên skill cần gọi API ngoài hoặc cài package sẽ hỏng. Thiết kế skill phải biết nó sẽ chạy ở đâu.
- Giống CLAUDE.md, skill là chỉ dẫn bằng ngôn ngữ: model *cố gắng* làm theo, không bị ép. Muốn cưỡng chế vẫn cần hook hoặc deny rule (note W3D1).
- Skill khác subagent ở chỗ: subagent là **context tách biệt**, skill là **chỉ dẫn nạp vào context hiện tại**. Và nhắc lại từ W3D1: custom subagent không tự thấy skill, phải liệt kê trong front matter.

### Deny rule chặn đọc `.md` có làm skill không nạp được không? **[chưa kiểm chứng]**

Suy luận, chưa thử: **không chặn bước nạp, nhưng chặn các bước skill tự đọc thêm.**

| Phần của skill | Ai nạp | Có qua tool `Read` không |
|---|---|---|
| `name` + `description` (mức 1) | Harness quét `.claude/skills` lúc khởi động | Không |
| Body `SKILL.md` (mức 2) | Tool `Skill` hoặc lệnh `/tên` | Có vẻ không |
| File đi kèm (`FORMS.md`...) | Claude đọc theo chỉ dẫn trong body | **Có**, qua `Read` |
| Script trong `scripts/` | Claude chạy qua `Bash` | Qua `Bash`, chịu rule của Bash |

- **[docs]** Bằng chứng gián tiếp: docs Agent SDK nói skill không nằm trong danh sách `skills` thì "files remain on disk and stay reachable through Read and Bash". Tức `Skill` tool và `Read` là hai đường riêng.
- Hệ quả nếu đúng: deny `Read(**/*.md)` thì skill vẫn kích hoạt, nhưng file `.md` phụ mà skill bảo Claude đọc sẽ bị từ chối. Skill chỉ có body thuần thì chạy bình thường.
- Deny rule thuộc lớp settings của Claude Code, nên **không áp dụng** trên Messages API và Managed Agents (container của Anthropic).
- **[ngoài tài liệu]** Hình như có kiểu rule riêng cho tool `Skill` (dạng `Skill(tên)`); cần kiểm tra trong docs permissions.
- **Cách kiểm chứng:** thêm deny `Read(**/SKILL.md)` vào `settings.local.json`, gọi `/ten-skill`, quan sát. Rồi thử thêm skill có file `.md` phụ để xem bước đọc file phụ có bị chặn không.

### Analogy với vòng đời service trong .NET

| Môi trường | Tương đương .NET | Mức khớp | Chỉnh lại |
|---|---|---|---|
| Claude Code | `appsettings` mặc định, bị override | Tốt | Đúng cả ý nhiều lớp override (managed, user, project, local) |
| Messages API | Scoped theo request | Tốt | Skill upload lên workspace là "đã đăng ký trong catalog"; `container.skills` là "gắn vào request"; container giữ lại giữa các lượt bằng `container.id` |
| Agent SDK | Host tự dựng, đăng ký thủ công | Một nửa | **Không phải singleton cả đời app**: **[docs]** `query()` khởi động một tiến trình Claude Code mới, skill được quét lại mỗi lần. Khớp hơn: Claude Code = `WebApplication.CreateBuilder()` (nối sẵn theo quy ước), SDK = tự dựng `HostBuilder`, `settingSources` = `AddJsonFile(...)` |
| Managed Agents | Config store tập trung trên server | Khá | Không phải "Vault": skill không phải bí mật. Điểm khớp: định nghĩa một lần ở server, áp dụng mọi session, muốn đổi thì sửa định nghĩa agent |

**Giới hạn của analogy:** DI lifetime chỉ trả lời "tồn tại bao lâu, nạp khi nào". Câu hỏi chính của tài liệu là "**chạy ở đâu, đụng được vào gì**". Nên nhớ thêm trục thứ hai:

| | Lifetime (kiểu .NET) | Chạy ở đâu |
|---|---|---|
| Claude Code | appsettings + override | Máy bạn, chịu permission và deny rule |
| Messages API | Scoped / per-request | Container Anthropic, không mạng |
| Agent SDK | Host tự dựng, đăng ký thủ công | Máy bạn |
| Managed Agents | Config store trên server | Sandbox Anthropic |

### Ba quy tắc để skill chạy được ở nhiều môi trường (portability)

Kết luận thực hành của tài liệu: viết skill **một lần** dùng lại được, nhưng phải **thiết kế có chủ đích** cho việc đó.

1. **Viết `description` như tiêu chí khớp.** Model nạp skill bằng cách so yêu cầu với description. Description nói rõ *khi nào áp dụng* thì chạy được ở mọi môi trường; mơ hồ thì không nạp được ở **tất cả** môi trường.
   - Mơ hồ: `Helps with documents`.
   - Rõ: `Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.` (ví dụ từ docs)
   - **[docs]** Lưu ý: description chỉ quan trọng với đường **model tự gọi**. Gọi bằng `/tên` (Claude Code, SDK) không cần khớp. Skill có `disable-model-invocation: true` thì description không vào context nên càng không dùng để khớp.
2. **Đừng giả định có filesystem hay tool local trong body.** Skill gọi lệnh local (`git`, `gh`, `jq`, `dotnet`...) chạy được ở Claude Code nhưng hỏng trên Messages API vì container không có lệnh đó. Giữ các bước trong phạm vi runtime **bảo đảm** có, hoặc **ghi rõ phụ thuộc** (ví dụ một mục "Requirements" trong body).
   - **[docs]** Trên API, container không có mạng và không cài thêm package. Đường dẫn kiểu `src/` cũng giả định có file project, điều chỉ đúng khi chạy trên máy bạn.
3. **Subagent không kế thừa skill.** Subagent bắt đầu trống, nên skill mà agent cha dựa vào phải **liệt kê tường minh** cho subagent, ở mọi runtime có subagent. Nhắc lại từ W3D1: custom subagent khai báo skill trong front matter; built-in agent không có skill nạp sẵn. Cú pháp front matter cụ thể: chưa có trong tài liệu, cần tra docs.

**Chọn công cụ nào [theo tài liệu]:**

| | Nội dung |
|---|---|
| **Làm tốt** | Quy trình theo task, viết một lần dùng lại ở terminal tương tác, tích hợp API và job SDK headless |
| **Thêm độ phức tạp** | Mỗi môi trường nạp và sandbox khác nhau: phải tính beta header trên API và `settingSources` trên SDK |
| **Dùng cách khác** | Chỉ dẫn phải áp dụng cho **mọi session** của project thì vẫn dùng **CLAUDE.md**. Skill dành cho quy trình mang đi được, nạp theo nhu cầu |

Nối với W3D1: CLAUDE.md = luôn nạp, mềm, theo project; skill = nạp theo nhu cầu, mang đi được; hook/deny rule = cưỡng chế bằng code.

## 6. Custom command, plugin, marketplace

Phần cuối của tài liệu: cho workflow một **điểm vào tường minh**, rồi đóng gói thành thứ **cài được**. Phần đánh dấu **[docs]** đã đối chiếu với docs Claude Code (đọc 2026-11-17).

### 6.1 Custom command = skill gọi tường minh

- Tài liệu: skill là định dạng được khuyến nghị cho **cả** gọi tường minh (`/skill-name`) và tự động. Thư mục `.claude/commands/` còn chạy nhưng là **legacy**. Muốn workflow chỉ chạy khi bạn gọi thì dùng skill có `disable-model-invocation: true`.
- **[docs]** Khớp: file `.claude/commands/deploy.md` tạo `/deploy`, hành vi như skill `.claude/skills/deploy/SKILL.md`. Skill là bản kế nhiệm.
- Nối với mục 4: custom command thực chất là một cấu hình của skill, không phải cơ chế riêng.

### 6.2 Namespace của command trong plugin

- Command trong plugin được gắn tiền tố tên plugin: `run-tests` trong plugin `payments` gọi là `/payments:run-tests`. Nhờ vậy hai plugin cùng có `run-tests` không đụng nhau.
- **Tên plugin là một phần của interface**: đổi tên plugin là đổi tên **tất cả** command nó cung cấp.
- **[docs]** Plugin có hai cái tên: `name` trong `plugin.json` (làm tiền tố skill) và `name` của entry trong `marketplace.json` (làm install id `<entry>@<marketplace>`). Hai tên phải **giống nhau**, nếu không cài theo tên manifest sẽ báo `Plugin "..." not found in marketplace`.

### 6.3 Plugin: đơn vị cài đặt

- Plugin gói **skill, hook, subagent, MCP server** thành một đơn vị cài được, có version, kiểm toán được (thay "một trang các bước cài tay").
- **[docs]** Cấu trúc:

| Thành phần | Vị trí trong thư mục plugin |
|---|---|
| Manifest (tên, version, mô tả) | `.claude-plugin/plugin.json` |
| Skill | `skills/<tên>/SKILL.md` |
| Subagent | `agents/*.md` |
| Hook | `hooks/hooks.json` |
| MCP server | `.mcp.json` |

- **[docs]** Dev không cần marketplace: `claude --plugin-dir <thư-mục>` nạp plugin cho một session; sửa xong `/reload-plugins`. Kiểm tra bằng `claude plugin validate`.
- **[docs]** Chi phí context (nối với ghi chú W3D1 về hook): plugin đã bật **nằm trong mọi session**. Name và description của skill, agent, command mà Claude có thể tự gọi luôn trong context mỗi lượt, dù không dùng. MCP server và hook của plugin cũng chạy ở mọi session. Plugin chạy **với quyền của bạn**, nên cần xem xét trước khi cài.

### 6.4 Marketplace: danh mục, không phải kho lưu trữ

- Marketplace là **catalog** các plugin do người khác tạo và chia sẻ. Marketplace chính thức của Anthropic có sẵn khi khởi động; marketplace bên thứ ba lưu trong GitHub repo thêm bằng `/plugin marketplace add <owner/repo>`. Đồng nghiệp chỉ cần một lệnh cài.
- **[docs]** Marketplace là thư mục/repo có `.claude-plugin/marketplace.json` (bắt buộc `name`, `owner`, mảng `plugins`; mỗi entry cần `name` và `source`). Nó chỉ *liệt kê* và chỉ nơi lấy plugin (đường dẫn tương đối, `github`, `git-subdir`, `url`, `npm`...).
- **[docs]** Luồng cài:
  1. `claude plugin marketplace add <owner/repo | ./thư-mục>`
  2. `claude plugin install <plugin>@<marketplace>` (chọn scope: user / project / local)
  3. `claude plugin list` để xác nhận.
- **[docs]** Scope: *user* = bạn ở mọi project; *project* = mọi người trong repo qua `.claude/settings.json` đã commit; *local* = bạn ở repo này.
- **[docs] Cẩn thận với "cài một bước":** `enabledPlugins` trong `.claude/settings.json` của repo **không tự cài** plugin. Mỗi đồng nghiệp vẫn phải chạy `claude plugin install <tên>@<marketplace> --scope project`, và `extraKnownMarketplaces` ở cấp repo chỉ có hiệu lực trong thư mục đã được **trust**.
- **[docs]** Phân biệt: marketplace plugin (`/plugin marketplace add`) khác website Claude Marketplace trên claude.com.

### 6.5 Triển khai toàn tổ chức (enterprise)

| Setting (managed) | Tác dụng | Không làm được |
|---|---|---|
| `strictKnownMarketplaces` | **Allowlist** nguồn marketplace người dùng được thêm; `[]` chặn mọi nguồn kể cả marketplace chính thức | **Không đăng ký** marketplace |
| `extraKnownMarketplaces` | **Đăng ký** marketplace trên mọi máy (khóa theo `name` trong `marketplace.json`); phải qua được allowlist | Không tự cài plugin |
| `enabledPlugins` | `true` ép bật, `false` chặn ở mọi scope và ẩn plugin | Không cài plugin nếu marketplace chưa đăng ký hoặc không được cho phép |
| `blockedMarketplaces` | Blocklist nguồn, kiểm tra **trước** allowlist | Không gỡ marketplace đã đăng ký từ nguồn không khớp |
| `disableSideloadFlags` | Từ chối `--plugin-dir`, `--plugin-url`, option `plugins` của Agent SDK | Không hạn chế `.mcp.json` |

- Tài liệu: allowlist chỉ giới hạn cái người dùng được thêm, **không tự đăng ký**. Muốn đẩy marketplace tới mọi người thì **kết hợp allowlist với `extraKnownMarketplaces`** trong managed settings.
- Ưu tiên: managed settings nằm **trên** user và project trong hệ phân cấp, nên plugin triển khai ở managed scope **không bị người dùng hay file project ghi đè**. **[docs]** Ví dụ: người dùng tắt plugin ở scope của mình, plugin vẫn nạp.
- **[docs]** Ba chi tiết đáng nhớ:
  - Mặc định chỉ **một** nguồn managed có hiệu lực trên một máy (thứ tự: server-managed, MDM, file `managed-settings.json`), trừ khi đặt `managedSourcesBehavior: "merge"`.
  - Đặt allowlist mà thiếu entry `{ "source": "skills-dir" }` thì plugin dạng thư mục trong `.claude/skills/` có `plugin.json` **ngừng nạp**. Skill thuần (chỉ `SKILL.md`, không manifest) không bị ảnh hưởng.
  - Allowlist không chặn `--plugin-dir`; việc đó do `disableSideloadFlags`.
- Alias: `allowedMarketplaces` = `strictKnownMarketplaces`, `additionalMarketplaces` = `extraKnownMarketplaces` (cần v2.1.232 trở lên; fleet nhiều phiên bản nên dùng tên chuẩn).

### 6.6 Bảng quyết định đóng gói (theo tài liệu)

| Lớp | Là gì | Cho ai | Khi nào dùng |
|---|---|---|---|
| **Skill** | File Markdown trong `.claude/skills`, nạp khi description khớp hoặc gọi theo tên | Dev hoặc nhóm dùng Claude Code tương tác | Quy trình theo task cần ở **ngoài context** cho đến khi cần (review PR, checklist deploy) |
| **Custom command** | Lối tắt có tên chạy một quy trình khi gọi tường minh | Dev cần điểm vào rõ ràng, dễ đoán cho việc tần suất cao | Quy trình có tên rõ và muốn kích hoạt trực tiếp thay vì trông vào description khớp |
| **Plugin** | Gói có version gồm skill, hook, subagent, MCP server, phân phối qua marketplace | Nhóm muốn cài một bước một bộ cấu hình dùng chung, có version | Setup đang chạy ổn trên **một máy** và cần chia sẻ, đánh version, giữ nhất quán trong nhóm |

**Cách nhớ:** skill = *nội dung* quy trình; custom command = *cách gọi* (skill với `disable-model-invocation: true`); plugin = *cách phân phối*; marketplace = *nơi phân phối*; managed settings = *cách bắt buộc* ở cấp tổ chức.

### 6.7 Đối chiếu với các mục trước

- **Plugin là khái niệm của Claude Code** (và SDK qua option `plugins`). **[ngoài tài liệu]** Trên Messages API và Managed Agents không có "plugin": skill phải upload riêng qua `/v1/skills` hoặc khai báo trong agent resource. Quy tắc portability (mục 5) vẫn là điều kiện để cùng một skill dùng được cả khi đóng gói plugin lẫn khi upload API.
- Plugin gom đủ bộ cơ chế W3D1 vào một gói: skill (mục 2), subagent, hook (cưỡng chế bằng code), MCP server. Còn CLAUDE.md và rules của project **không** nằm trong danh sách thành phần plugin.
- Lớp bảo mật: plugin chạy với quyền của bạn và hook của nó chạy ở mọi session, nên marketplace allowlist ở cấp managed chính là "deny rule" của khâu phân phối.

### 6.8 Đánh đổi khi đóng gói: Cost, Complexity, Risk

- **Cost:** hai loại chi phí khác nhau.
  - Context: skill đơn lẻ chỉ tốn khi kích hoạt; **[docs]** plugin đã bật thì name và description của skill tự gọi được **luôn nằm trong context mỗi lượt**.
  - Con người: plugin trả setup **một lần** (cộng chi phí làm plugin: version, marketplace, cập nhật); làm tay thì **mỗi người trả lại** và dễ lệch phiên bản. Plugin đáng khi nhóm đủ đông và cấu hình ổn định hoặc hay đổi.
- **Complexity:** đường dẫn tuyệt đối hay giả định môi trường (ví dụ `python` có trên PATH) trong skill hoặc hook sẽ chạy trên máy tác giả và hỏng trên máy khác. **[docs]** Người cài nhận **bản copy trong plugin cache**; dùng `${CLAUDE_PLUGIN_ROOT}/...` cho đường dẫn trong plugin. **[ngoài tài liệu, suy ra]** File ngoài thư mục plugin không đi theo gói.
- **Risk:** plugin chỉ mang theo thành phần nó **khai báo** (skill, subagent, hook, MCP server). Deny rule trong `settings.json` cục bộ **không** nằm trong gói, nên skill dựa vào guardrail đó sẽ mất rào chắn trên máy đồng nghiệp.
  - Cách giảm: đặt guardrail thành **hook trong plugin** (`PreToolUse`, exit code 2); hoặc dùng **managed settings** nếu bắt buộc cho cả tổ chức.
  - **[docs]** Bảng control matrix ghi `allowManagedHooksOnly` "doesn't trust hooks from plugins users enable themselves". Đã đối chiếu (xem [NOTES_W3D3_Enterprise_Integration.md](NOTES_W3D3_Enterprise_Integration.md) mục 8.1): nếu tổ chức bật, hook trong plugin do **người dùng tự bật** bị chặn, còn plugin do admin **ép bật** trong `enabledPlugins` của managed settings thì **vẫn chạy**. Nghĩa là guardrail dạng hook-trong-plugin chỉ ổn định dưới `allowManagedHooksOnly` khi plugin đó do admin ép bật.
  - Skill là chỉ dẫn mềm nên không coi là rào chắn (xem W3D1).

## 7. Còn lại và việc cần kiểm tra

- **PENDING: lab đóng gói plugin** (chờ buổi lab). Kế hoạch dự kiến: plugin `study-tools` trong marketplace cục bộ `labs/lab3/` gồm skill `notes-check` (`disable-model-invocation: true`), skill `explain-doc` (tự gọi), hook `PreToolUse` chặn sửa `.env` bằng `scripts/guard_env.py`. Các bước:
  1. `claude plugin validate`, rồi `--plugin-dir`; kiểm tra tiền tố `/study-tools:notes-check`.
  2. Kiểm tra skill nào tự gọi, skill nào không; đổi `name` plugin, `/reload-plugins` để thấy tiền tố đổi.
  3. Marketplace cục bộ: `marketplace add`, `plugin install <plugin>@<marketplace>`, `plugin list`; thử cố tình để tên entry khác tên manifest.
  4. Thí nghiệm Complexity: hook dùng đường dẫn cứng, mô phỏng "đồng nghiệp" ở thư mục khác để thấy hỏng, rồi sửa bằng `${CLAUDE_PLUGIN_ROOT}`; ghi lại `python` hay `py` trên máy.
  5. Thí nghiệm Risk: deny rule chỉ ở `settings.local.json` của mình, cài plugin vào project sạch để thấy mất rào chắn; rồi đưa hook vào bundle để thấy rào chắn đi theo.
  6. (Tùy chọn) Giả thuyết deny `Read(**/SKILL.md)` và skill (xem mục 5).
  - Chưa chạy lần nào; cú pháp `hooks.json` trong plugin chưa nắm chắc, tra trang Plugin components và Hooks trước khi làm.

- Đã hoàn thành đối chiếu docs về cấu trúc plugin, marketplace và managed settings (mục 6). Chưa thực hành: tự tạo plugin với `claude plugin validate`, `--plugin-dir` rồi cài từ một marketplace cục bộ.
- Chưa kiểm chứng: plugin có thể chứa CLAUDE.md hay rules không (docs danh sách thành phần không thấy). Xác nhận ở trang Plugin components.
- Đọc nốt phần 45k ký tự cuối của skills-guide trên API (kiểm tra header beta, giới hạn kích thước skill, cách upload).
- Tra cú pháp front matter của custom subagent để liệt kê skill (quy tắc portability số 3).
- Chạy thử giả thuyết deny rule và skill (mục 5, phần "Deny rule chặn đọc `.md`"); cập nhật kết quả thật vào note.
- Managed Agents: xác nhận cú pháp khai báo skill trong agent resource và quan hệ với chế độ nạp từ GitHub repo; header beta `managed-agents-2026-04-01` lấy từ tài liệu khóa học, chưa đối chiếu docs.
- Phần "gọi skill chủ động" (mục 4) mới kiểm tra cho Claude Code, SDK và Messages API; chưa biết Managed Agents có cách gọi trực tiếp không.
- Danh sách field frontmatter đầy đủ (ví dụ `allowed-tools`) và thứ tự ưu tiên khi hai skill trùng tên: xem phần Frontmatter reference của docs Claude Code.
