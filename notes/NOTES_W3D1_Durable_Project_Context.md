# Notes Week 3 Day 1: Durable Project Context (CLAUDE.md, rules, hooks, subagents)

Nguồn: tài liệu khóa học (phần "Durable project context with CLAUDE.md, rules files, hooks, and subagents"). Phần đánh dấu **[ngoài tài liệu]** là suy luận hoặc kiến thức bổ sung, cần đối chiếu docs.

Liên hệ với note trước ([NOTES_W3D1_Permission_Modes.md](NOTES_W3D1_Permission_Modes.md)): note đó là lớp cấu hình quyết định agent **được phép làm gì**. Phần này là lớp quyết định agent **biết gì và hành xử ra sao**, để quy tắc và ngữ cảnh đặt ra trong session này vẫn còn hiệu lực ở session sau.

## 1. CLAUDE.md: file project nạp vào mọi session

- Mỗi lần Claude Code khởi động trong thư mục project, nó tìm và đọc `CLAUDE.md` ở root. Nội dung được **gắn vào prompt trước khi tin nhắn đầu tiên của bạn đến**, nên mọi quy ước, ràng buộc, lệnh trong đó có mặt ngay từ prompt đầu của mọi session mà không cần nhắc lại.
- `/init` quét codebase và sinh CLAUDE.md khởi đầu. Đây là baseline tốt nhưng **phải kiểm tra lại** trước khi dùng. Nên tinh chỉnh để giữ những quy tắc quyết định kết quả prompt: lệnh test, quy ước framework, đường dẫn không được đụng, quyết định style khác mặc định.
- **Kích thước là lỗi chính.** File cứ phình theo mỗi chỉ dẫn mới thì làm loãng các quy tắc quan trọng: tốn nhiều context hơn, mỗi chỉ dẫn chiếm tỉ lệ nhỏ hơn, giảm khả năng agent làm theo đúng quy tắc chặn được lỗi thật.
- Nguyên tắc: chỉ giữ ràng buộc **thay đổi hành vi**; phần còn lại chuyển sang **Skills** nạp theo nhu cầu.

## 2. Rules files: đặt hướng dẫn đúng chỗ áp dụng

- CLAUDE.md luôn bật; rules file thêm một lớp hẹp hơn lên trên. Chúng nằm ở `.claude/rules/` và có thể giới hạn theo đường dẫn bằng `paths` (glob) trong YAML frontmatter.
- Rule có `paths` chỉ vào context **khi Claude làm việc với file khớp pattern**, nên không làm rối phần còn lại của codebase.
- **Phạm vi do frontmatter quyết định, không phải vị trí file.** Có thể chia thư mục con trong `.claude/rules/` (ví dụ `.claude/rules/database/`) nhưng đó chỉ để tổ chức. Rule **không có `paths`** nạp vô điều kiện lúc khởi động, cùng mức ưu tiên với CLAUDE.md, dù nằm ở đâu.
- Cách chia: ràng buộc phổ quát vào CLAUDE.md, hướng dẫn hẹp theo đường dẫn vào rules.

Ví dụ theo tài liệu:
- "Không bao giờ sửa schema database" áp dụng mọi nơi, nên vào **CLAUDE.md**.
- "Mọi SQL trong module database phải có ranh giới transaction tường minh" vào `.claude/rules/database.md`:

```yaml
---
paths:
  - "src/db/**/*.sql"
---
```

## 3. Hooks: chạy script của bạn tại các điểm cố định trong vòng đời

- Hook chặn và điều khiển tool call trước hoặc sau khi chạy. Ghi "chạy Prettier sau mỗi lần sửa file" vào CLAUDE.md thì agent làm theo **phần lớn thời gian**; hook thì làm **mọi lần, không ngoại lệ**, vì hook kích hoạt độc lập với quyết định của model.
- Hook được định nghĩa trong **settings file** và cấu hình bằng `/hooks`. Mỗi hook gồm: sự kiện vòng đời, matcher (tùy chọn, giới hạn theo loại tool), và command chạy khi sự kiện xảy ra.

| Sự kiện | Chạy khi nào | Dùng cho |
|---|---|---|
| `PreToolUse` | Trước khi tool call chạy | Có thể **chặn** bằng exit code 2, ghi lý do ra stderr để agent thấy. Cách cưỡng chế quyền truy cập ở tầng cấu hình thay vì hy vọng agent tuân theo CLAUDE.md |
| `PostToolUse` | Sau khi tool call xong | **Không chặn được** vì call đã xảy ra. Dùng cho tác dụng phụ tự động: format code sau edit, chạy test sau khi đổi file, ghi audit log |
| `UserPromptSubmit` | Khi bạn gửi prompt, trước khi model xử lý | Chèn thêm context hoặc kiểm tra yêu cầu trước khi bắt đầu việc |
| `Stop` | Khi model trả lời xong | Việc cuối lượt: thông báo, dọn dẹp, commit audit log |
| `Notification` | Khi Claude Code gửi thông báo (cần quyền dùng tool, hoặc rảnh 60 giây) | Đẩy tín hiệu ra kênh ngoài hoặc hệ thống log |
| `SessionStart` | Khi session bắt đầu hoặc tiếp tục | Khởi tạo state, kiểm tra biến môi trường, xác nhận service cần thiết truy cập được |
| `SessionEnd` | Khi session kết thúc | Dọn dẹp, ghi audit cuối, thông báo session đã đóng |

- Hook chặn edit vào đường dẫn cấu hình production bằng `PreToolUse` thì ràng buộc đó được cưỡng chế ở **mọi tool call, mọi session, bất kể permission mode**. Đó là khác biệt giữa **guardrail** và **convention**.
- **[ngoài tài liệu]** Hook cũng là một lựa chọn cưỡng chế bên cạnh deny rule ở note trước: deny rule trả lời "được phép hay không", hook cho phép logic tùy biến (kiểm tra nội dung lệnh, ghi log...).

## 4. Subagents: giao việc cho một context tách biệt

- Subagent là trợ lý chuyên biệt mà Claude Code giao việc cho; mỗi cái chạy trong **context riêng** và chỉ trả về **kết quả**. Nó **không** kế thừa lịch sử hội thoại, file đã tích lũy trong context, hay state session hiện tại: bắt đầu từ trang trắng, làm xong, trả kết quả.
- Các subagent built-in khác nhau ở thứ nạp lúc khởi động, và điều này quyết định quy tắc project có áp dụng hay không (luôn kiểm tra danh sách hiện hành trong docs vì tập agent đã thay đổi theo thời gian):

| Subagent | CLAUDE.md và git status |
|---|---|
| **Explore**, **Plan** | **Bỏ qua** cả hai để nghiên cứu nhanh và rẻ. Quy tắc project trong CLAUDE.md **không có** trong context của chúng |
| **general-purpose** | Nạp **cả hai** |

- Task cần tuân thủ ràng buộc project thì dùng general-purpose, hoặc custom subagent nạp tường minh các quy tắc cần thiết.
- **Custom subagent không tự thấy skill.** Subagent tự định nghĩa trong `.claude/agents` cần skill nào thì phải **liệt kê skill đó trong front matter** của agent. Built-in agent không có skill nạp sẵn; muốn hành vi dựa trên skill thì tạo custom subagent có liệt kê skill.
- **[ngoài tài liệu]** Hệ quả với ý đã ghi ở lượt trước: "ghi kiến trúc vào CLAUDE.md để mất bức tranh codebase giữa các session" vẫn đúng cho session chính, nhưng nếu việc khám phá được giao cho Explore thì CLAUDE.md không đến được với nó.

## 5. Bản đồ cơ chế: cái nào mang kiến thức nào

| Cơ chế | Nạp gì | Chạy khi nào | Chi phí context | Hợp với |
|---|---|---|---|---|
| **CLAUDE.md** | Toàn bộ nội dung, gắn vào đầu context | Mọi session, vô điều kiện | Cố định mỗi session; loãng khi phình to | Ràng buộc phổ quát, lệnh, quyết định framework |
| **Rules file** | Nội dung file; có `paths` thì giới hạn theo glob, không có thì nạp như CLAUDE.md | Khi Claude đọc file khớp `paths`; rule không giới hạn nạp lúc khởi động | Có `paths`: chỉ thêm khi bị kích hoạt. Không `paths`: tốn cố định như CLAUDE.md | Hướng dẫn riêng cho một đường dẫn, sẽ là nhiễu ở chỗ khác |
| **Hook** | Chạy script tại sự kiện, không thêm nội dung vào context | Tại sự kiện cấu hình (`PreToolUse`, `PostToolUse`...) | Tối thiểu: chỉ output của script nếu được trả về cho Claude | Guardrail cưỡng chế, tác dụng phụ tự động, audit log |
| **Subagent** | Chỉ context của task, tách biệt khỏi session chính | Khi session chính giao việc | Trả về bản tóm tắt, không phải toàn bộ lịch sử task | Khám phá, điều tra, task có output làm phình context; việc chia nhỏ để chạy song song |

**Nên dùng cho:** project quay lại qua nhiều session, nơi bộ quy tắc ổn định, biến thể theo thư mục, hoặc guardrail vô điều kiện đáng công setup.
**Nên dùng cách khác:** việc dùng một lần không quay lại; khám phá nhanh codebase lạ thì chi phí setup không đáng.

## 6. Đối chiếu với kiến thức API

CLAUDE.md giống system prompt ở chỗ: chỉ dẫn bền vững có mặt từ đầu mọi lượt, dài quá thì loãng, và là chỉ dẫn bằng ngôn ngữ nên model *cố gắng* theo chứ không bị ép (muốn ép thì cần hook hoặc deny rule). Với API, system prompt phải gửi lại ở mỗi request vì API không lưu trạng thái; Claude Code đọc lại CLAUDE.md và nạp vào mỗi session thay bạn.

Hai điểm cần phân biệt:
- **Chưa chắc nó là system prompt.** Tài liệu chỉ nói nội dung được gắn vào prompt trước tin nhắn của bạn. **[ngoài tài liệu, cần đối chiếu docs]** Claude Code có system prompt riêng không sửa được; CLAUDE.md thường là ngữ cảnh đi kèm đặt lên trên đó.
- **CLAUDE.md không phải ràng buộc của API hay mode model.** Nó chỉ nói về project và cách làm việc. Các thứ ở tầng API tương ứng với cấu hình khác:

| Ở tầng API | Trong Claude Code |
|---|---|
| `system` prompt | CLAUDE.md, rules files (nạp thêm theo đường dẫn) |
| `tools` truyền vào | Tool có sẵn của agent, cộng allow/deny rule và permission mode |
| Chọn model, effort, tham số | Cấu hình model, flag, settings |
| Code bao quanh vòng lặp (giới hạn vòng, HITL, validate output như Lab 2) | Permission mode, hooks (cưỡng chế bằng code) |

Cách nhớ: CLAUDE.md và rules là phần **nói với model** (mềm, có thể bị bỏ sót); settings, deny rule và hooks là phần **code bao quanh model** (cứng, model không lách được).

## 7. Còn lại và việc cần kiểm tra

- Tài liệu nhắc **Skills** (nạp theo nhu cầu) như nơi đặt nội dung ngoài CLAUDE.md, nhưng phần này chưa giải thích Skills; bổ sung khi học tới.
- Chưa có cú pháp cụ thể của hook (định dạng cấu hình, matcher, cách đọc input) và front matter của custom subagent.
- Kiểm tra trong docs: danh sách subagent built-in hiện hành, và danh sách sự kiện hook (tài liệu nói chi tiết như "rảnh 60 giây" có thể thay đổi theo phiên bản).
