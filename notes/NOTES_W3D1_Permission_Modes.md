# Notes Week 3 Day 1: Permission Modes & Human Gates (Claude Code)

Nguồn: tài liệu khóa học (phần "Claude Code agent loop, permission modes, settings, and where a human gate goes"). Phần đánh dấu **[ngoài tài liệu]** là kiến thức bổ sung, cần đối chiếu docs chính thức của phiên bản đang dùng.

## 1. Claude Code = agent loop + lớp phân quyền

- Cùng vòng lặp agent ở Module 2 (model gọi tool, nhận kết quả, lặp đến khi xong), chạy trong terminal, thêm một **hệ thống permission** chặn mọi hành động agent muốn làm.
- **[ngoài tài liệu]** Lớp permission là code của harness, không phải model tự giác: model chỉ *xin* gọi tool, harness quyết định cho chạy, hỏi hay từ chối. Ngoại lệ là mode `auto`, nơi quyết định do một classifier riêng đưa ra.
- Human gate là một **dải liên tục** từ duyệt từng bước đến không có người; việc của người dùng là chọn điểm đặt gate theo độ rủi ro và khả năng hoàn tác.

## 2. Explore → Plan → Code

| Giai đoạn | Làm gì |
|---|---|
| Explore | Đọc file, lần theo logic, dựng bức tranh về codebase. Chưa sửa gì. |
| Plan | Mô tả có cấu trúc các chỉnh sửa định làm. |
| Code | Chỉ sau khi người dùng duyệt plan mới viết và thực thi. |

Lý do: (1) output tốt hơn vì ít đoán mò và bắt được tác động hạ nguồn; (2) đây là chỗ permission mode cắm vào, ví dụ plan mode giữ ở Explore.

**[ngoài tài liệu] "Bức tranh về codebase" thực chất là gì**
- Không có sơ đồ file hay route map dựng sẵn và lưu lại. Đó là nội dung trong context window, được tạo ra từ kết quả các tool khám phá (Glob, Grep, Read), giống dev đọc code: xem cấu trúc, tìm điểm vào, lần theo luồng gọi hàm.
- Cuộc hội thoại mới thì mất, trừ khi ghi vào CLAUDE.md hoặc memory (kiến trúc, lệnh build/test, quy ước). Khám phá rộng có thể giao cho subagent để không làm đầy context chính.

**[ngoài tài liệu] Plan có bắt buộc không?**
- Không. Chỉ plan mode **ép** bằng cơ chế (chặn edit và shell cho đến khi duyệt). Ở mode khác, plan xuất hiện khi prompt, CLAUDE.md hoặc skill yêu cầu, hoặc khi model tự chia bước với task lớn.

## 3. Sáu permission mode

| Mode | Tự động duyệt | Vẫn chặn | Giới hạn / dùng khi |
|---|---|---|---|
| `default` | Chỉ đọc | Mọi edit và shell command | An toàn nhưng chậm. Mức nền cho project mới hoặc codebase lạ. |
| `acceptEdits` | Đọc, sửa file, lệnh filesystem thông dụng (`mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, `sed`) **trong working directory** | Shell command khác; ghi ngoài working directory; ghi vào protected paths | Việc local đáng tin cậy mà shell vẫn cần người xem. Không hợp nếu agent phải chạy script. |
| `plan` | Chỉ đọc; nghiên cứu và đề xuất, không sửa | Mọi edit và shell cho đến khi duyệt plan | Khám phá và lập kế hoạch trên codebase nhạy cảm hoặc lạ. Không hợp task phải ghi output. |
| `auto` | Mọi thứ, nhưng một **classifier riêng** xét từng hành động, chặn cái leo thang vượt yêu cầu, nhắm hạ tầng lạ, hoặc có vẻ bị nội dung độc hại điều khiển | Mặc định chặn: production deploy và migration, xóa hàng loạt, đánh cắp credential, force-push lên main | Giảm prompt nhưng **không đảm bảo an toàn**; là research preview. Tùy plan, phiên bản model và admin settings; luôn kiểm tra yêu cầu hiện hành trước khi dùng. |
| `dontAsk` | Chỉ tool nằm trong **allow rule** đã duyệt trước, cộng lệnh read-only | Mọi tool call ngoài allow list bị **từ chối**, không có hàng đợi xác nhận | Dành cho CI và script khóa chặt. Không phải cách giảm ma sát khi làm việc tương tác local. |
| `bypassPermissions` | Mọi tool call, không prompt, không kiểm tra an toàn | Gần như không gì; chỉ lệnh xóa thảm họa như `rm -rf /`, `rm -rf ~` còn prompt cuối cùng | Chỉ trong container hoặc VM cô lập, dùng một lần rồi bỏ. Không bao giờ trên máy dev với codebase thật. |

Gom theo cách kiểm soát:
- **Người duyệt từng bước:** `default`, `acceptEdits`, `plan`.
- **Máy duyệt thay người:** `auto`.
- **Không có người:** `dontAsk` (allow-list cứng, từ chối phần còn lại), `bypassPermissions` (không chặn gì).

Tiêu chí chọn (theo tài liệu): mức độ quen codebase và việc thay đổi có dễ hoàn tác không.

### Hiểu nhầm hay gặp

**"Năm mode ngoài `auto` chỉ là mức tự chủ tăng dần"**: đúng với `default`, `acceptEdits`, `bypassPermissions`, nhưng:
- `plan` là trạng thái khác (chỉ đọc và đề xuất, khóa cứng giai đoạn Explore), không phải mức tự chủ thấp hơn `default`.
- `dontAsk` không tự chủ hơn mà là **từ chối** mọi thứ ngoài allow-list, thay vì hỏi.

**"Mode chưa nói gì về phạm vi local hay global"**: `acceptEdits` có phạm vi: chỉ tự duyệt trong working directory; ghi ngoài đó hoặc vào protected paths vẫn bị chặn. **[ngoài tài liệu]** Mode chỉ là một lớp: phạm vi thư mục thêm, allow/deny rule, sandbox thuộc phần settings (chưa học). Mode không cô lập ở mức hệ điều hành: lệnh đã duyệt chạy với quyền của người dùng. Muốn cô lập thật phải dùng container hoặc VM.

**"`auto` chỉ còn chặn thứ phi đạo đức"**: classifier chặn theo ba tiêu chí, phần lớn không phải đạo đức:

| Tiêu chí | Bản chất |
|---|---|
| Leo thang vượt quá yêu cầu | So khớp ý định và hành động (nhờ A mà làm A + B) |
| Nhắm hạ tầng không nhận ra | Phạm vi và an toàn vận hành |
| Bị nội dung độc hại hoặc không phù hợp điều khiển | An ninh (kiểu prompt injection) |

Danh sách chặn mặc định (production deploy và migration, xóa hàng loạt, đánh cắp credential, force-push lên main) cũng là rủi ro vận hành và bảo mật. Ngược lại, `auto` **không** chặn lỗi nằm trong phạm vi yêu cầu (xóa nhầm file khi được nhờ dọn thư mục, sửa bug theo hướng sai) nên vẫn cần người review. Classifier là model nên có thể sai cả hai chiều; tài liệu ghi rõ là research preview, không đảm bảo an toàn.

## 4. Chuyển từ plan sang thực thi

**[ngoài tài liệu]**
- Claude **không tự thoát** plan mode. Khi plan xong, nó trình plan (qua tool `ExitPlanMode`); **người dùng duyệt** thì mới thoát. Đó là human gate, khớp câu "until you approve a plan" trong tài liệu.
- Khi duyệt, người dùng thường chọn luôn mode để chạy tiếp (`default` duyệt từng edit, `acceptEdits` cho sửa file tự chạy, `auto` để classifier lo). Các lựa chọn cụ thể có thể khác theo phiên bản.
- Người chọn mode, Claude không tự nâng quyền. Muốn "tự plan rồi tự chạy" thì đặt sẵn mode khác `plan` và dặn lập plan trong prompt, nhưng mất cơ chế chặn cứng của plan mode.

## 5. Settings: cấu hình nằm ở đâu, áp dụng cho ai

| Cấp | File | Áp dụng cho | Dùng cho |
|---|---|---|---|
| User | `~/.claude/settings.json` | Mọi project trên máy | Sở thích đi theo bạn, ví dụ mode mặc định cho việc khám phá |
| Project | `.claude/settings.json` (commit vào repo) | Mọi người clone repo | Quy ước cả team, allow rule cho tool của project, deny rule cho đường dẫn không được đụng |
| Local project | `.claude/settings.local.json` (tự git-ignore) | Riêng bạn, riêng project này | Ghi đè cá nhân không muốn commit cho cả team |
| Enterprise | `managed-settings.json` (admin đặt) | Toàn tổ chức | Kiểm soát an ninh: cấm sửa file env, chặn một số shell command. User và project file **không ghi đè được** |

- Allow và deny rule **xếp chồng lên mode** đang chọn.
- **Deny luôn thắng allow**, bất kể mode nào.
- Kiểm soát bền nhất là **deny rule ở cấp enterprise**: không dev nào gỡ được, và vẫn có hiệu lực khi đang bật bypass mode.
- Đây là lớp thứ hai đã nhắc ở phần 3: mode là mặc định cho cả session, rule là phần tinh chỉnh theo từng tool hoặc đường dẫn.

### Settings khác CLAUDE.md: trục chính là chức năng, không phải phạm vi

Cả hai đều phân cấp (user, project, local), chỉ khác việc chúng làm:

| | CLAUDE.md | settings.json |
|---|---|---|
| Là gì | Hướng dẫn: quy ước code, kiến trúc, lệnh build/test, working ethic | Quyền hạn: mode, allow/deny rule (cộng hooks, env) |
| Ai thực thi | Model đọc trong context và cố gắng tuân theo; có thể sai hoặc bỏ sót | Harness cưỡng chế bằng code, model không lách được |
| Phân cấp | **[ngoài tài liệu]** user, project (commit), local (không commit) | user, project, local, enterprise (theo tài liệu) |

- **[ngoài tài liệu]** `.claude/` ở repo không chỉ chứa settings mà còn skill, agent...
- Mode là chính sách mặc định cho cả session (khi nào dừng hỏi); allow/deny là ngoại lệ chi tiết cho từng tool, lệnh, đường dẫn. Cả hai chỉ trả lời "được chạy, phải hỏi, hay bị cấm", không nói gì về code nên viết thế nào.
- Quy tắc chọn nơi đặt: muốn agent **làm theo cách nào** (ví dụ project A legacy dùng sync) thì đặt vào CLAUDE.md; muốn agent **không được làm hoặc không cần hỏi** (cấm sửa `.env`, cho tự chạy `dotnet test`) thì đặt vào settings. Điều không được phép sai thì không chỉ dựa vào CLAUDE.md mà phải thêm deny rule.

Ví dụ đúng cho từng cấp:
- **User:** mode mặc định cho việc khám phá, thói quen cá nhân.
- **Project:** allow rule cho tool của project, deny rule cho đường dẫn không được đụng, chung cho cả team.
- **Local project:** ghi đè cá nhân cho một project, ví dụ cho tự chạy một script chỉ trên máy mình. Nếu quy tắc áp dụng cho cả team thì thuộc cấp project.
- **Enterprise:** deny sửa file env, chặn shell command nhất định, trên mọi project và máy của tổ chức. (Khung giờ deploy là việc của CI/CD, không phải của Claude Code.)

### Nhiều cấp cùng đặt thì ai thắng?

Tài liệu chỉ nói rõ: enterprise không bị ghi đè; deny luôn thắng allow, bất kể mode.

**[ngoài tài liệu, cần đối chiếu docs]** Thứ tự ưu tiên giảm dần: enterprise > tham số dòng lệnh (ví dụ `--permission-mode`) > local project > project > user. Hai loại thiết lập xử lý khác nhau:

| Loại | Khi nhiều cấp cùng đặt |
|---|---|
| Mode (một giá trị cho cả session) | Chỉ một mode có hiệu lực; cấp ưu tiên cao hơn thắng. Trong session vẫn đổi tay được (ví dụ Shift+Tab). |
| Allow/deny rule (danh sách) | Gộp từ các cấp; rule deny và allow cùng khớp thì deny thắng. |

Ví dụ: user đặt `plan`, project đặt `acceptEdits`, local không đặt thì mode hiệu lực là `acceptEdits`. User deny đọc `.env` mà project allow đọc `.env` thì deny vẫn thắng. Có thể kiểm tra cấu hình hiệu lực bằng `/status` hoặc `/permissions` (cũng ngoài tài liệu, cần thử trên bản đang dùng).

## 6. Đặt human gate theo chi phí xấu nhất

Mode và deny rule quyết định agent **làm được gì mà không hỏi**. Chúng không quyết định chỗ nào **người vẫn phải xem** trước khi hành động có hiệu lực. Câu hỏi duy nhất: *nếu hành động này chạy mà không ai kiểm, kết quả xấu nhất là gì?* Chi phí sai càng thấp thì càng thả được; càng cao và càng khó hoàn tác thì càng cần gate trước khi chạy. Câu hỏi này áp dụng cả khi agent viết code lẫn khi chạy không người trông (ví dụ bot comment hoặc chặn pull request).

| Loại hành động | Đặt gate? | Cơ chế |
|---|---|---|
| Rủi ro thấp, hoàn tác được (sửa format, sửa trong working directory) | Không gate | `acceptEdits` |
| Khó hoàn tác hoặc chạm đường dẫn nhạy cảm (ghi ngoài working directory, shell command phá hủy, sửa file bảo mật hoặc protected) | Cần chặn hoặc gate (xem phân biệt bên dưới) | **Deny rule** nếu không có ca nào đáng cho phép; `default` hoặc `plan` (hoặc rule dạng ask nếu bản đang dùng có) nếu cần người quyết định từng lần |
| Thay đổi code team đã đánh dấu nhạy cảm | **Agent không bao giờ là gate duy nhất**: người phải review trước khi merge, dù agent hoặc phần tự review của nó nghe tự tin đến đâu | Review của người (agent chỉ là đầu vào cho quyết định của người) |

**Deny rule không phải human gate.** Deny là chặn cứng, không có người trong vòng quyết định. Gate đúng nghĩa là chỗ agent **dừng và hỏi người**. Hai trường hợp khác nhau:
- "Không bao giờ xóa file": **deny**, vì không có ca nào đáng để người duyệt.
- "Ghi ra ngoài working directory": nên **hỏi** (`default`, hoặc rule dạng ask **[ngoài tài liệu, cần kiểm tra bản đang dùng]**), vì có ca hợp lệ mà người cần xem.

(Tài liệu gộp cả hai trong một câu: deny cưỡng chế chắc chắn, `default` hoặc `plan` giữ prompt. Phân biệt trên là cách đọc cho rõ.)

**Chọn mode và đặt gate là cùng một quyết định nhìn từ hai phía:** mode đặt mặc định cho cả session, gate là chỗ ghi đè mặc định đó cho một hành động có chi phí quá cao để phó mặc.

## 7. Cost, Complexity, Risk

- **Cost:** chạy `default` trên việc đáng tin cậy thêm độ trễ prompt cho mọi tool call, cộng dồn trên refactor dài.
- **Complexity:** nhiều cấp settings và file với thứ bậc ghi đè đòi hỏi cẩn thận nhất quán. Deny rule enterprise mâu thuẫn với allow rule project là điều mọi người bảo trì config phải hiểu.
- **Risk:** dùng sai mode cho bối cảnh. Ví dụ bật bypass vì sốt ruột trên máy không cô lập sẽ gỡ mọi prompt an toàn giữa agent và file thật, và (khác các mode khác) **gỡ cả protected-path guard**. Điểm này bổ sung cho bảng ở phần 3: ở bypass chỉ còn prompt cuối cho lệnh xóa thảm họa như `rm -rf /`.

## 8. Còn lại và việc cần kiểm tra

- Cú pháp cụ thể của allow/deny rule chưa có trong đoạn đã học. Hooks đã học ở [NOTES_W3D1_Durable_Project_Context.md](NOTES_W3D1_Durable_Project_Context.md).
- Tài liệu chỉ nói enterprise không bị ghi đè và deny thắng allow; **thứ tự ưu tiên giữa user, project và local** chưa được nêu. Thứ tự ghi ở phần 5 là kiến thức ngoài tài liệu, cần đối chiếu docs chính thức và thử bằng `/status` hoặc `/permissions`.
- Kiểm tra trong phiên bản đang dùng: các lựa chọn hiện ra khi duyệt plan, và điều kiện khả dụng của `auto`.
