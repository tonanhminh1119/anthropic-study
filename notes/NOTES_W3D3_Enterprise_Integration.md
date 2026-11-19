# Notes Week 3 Day 3: Enterprise Integration (xác thực, secret, vận hành trong môi trường có quy định)

Nguồn: tài liệu khóa học "Connecting Claude to enterprise systems and authenticating it securely" ([archive/Enterprise Integration.txt](../archive/Enterprise%20Integration.txt)), đủ 6 mục. Chưa đối chiếu docs Claude Code trong lần ghi này. **[ngoài tài liệu]** = suy luận hoặc kiến thức bổ sung của mình, không phải của khóa học.

Liên hệ với note trước: [NOTES_W3D2_MCP_Servers.md](NOTES_W3D2_MCP_Servers.md) (transport, scope, GitHub PAT và Linear OAuth, enterprise managed MCP ở mục 7 và 9) và [NOTES_W3D1_Permission_Modes.md](NOTES_W3D1_Permission_Modes.md) (deny rule, hook). Note này không lặp lại các phần đó mà chỉ thêm lớp "production, có quy định".

## 1. Prototype khác tích hợp doanh nghiệp ở đâu

Prototype chỉ trả lời "kết nối có chạy không?". Tích hợp doanh nghiệp phải trả lời thêm:

1. Model đang hành động **dưới danh nghĩa ai**, và danh tính đó có audit được không?
2. Model truy cập **dữ liệu nào**, dữ liệu **đi đâu**?
3. Admin có **khóa được cấu hình** để dev không đổi phần xác thực không?
4. Truy cập có **log** đủ cho kiểm toán không?

Đây là yêu cầu identity, access, compliance quen thuộc; việc cần làm là đưa chúng vào thiết kế ngay từ đầu.

## 2. Ba kiểu xác thực theo loại dịch vụ

| Loại | Xác thực | Cách hoạt động |
|---|---|---|
| Remote, **danh tính người dùng** (SaaS, cloud) | **OAuth** | Server trả `401`; client mở trình duyệt cho người dùng đăng nhập và đồng ý; token được cấp và lưu tự động. Ví dụ: Linear |
| Remote, **danh tính dịch vụ** (API nội bộ, CI/Agent SDK) | **API key qua biến môi trường** | Key đại diện service account; không bao giờ commit vào config; CI runner inject như secret |
| **Local**, truy cập file system | **stdio, không xác thực mạng** | Ranh giới bảo mật là quyền file system; lớp quản trị là deny rule trong settings |

Tiêu chí chọn: dịch vụ **chạy ở đâu** và hỗ trợ **mô hình danh tính nào**. GitHub MCP (PAT qua header) là trường hợp lai: credential gắn với một người nhưng không đi qua luồng OAuth.

## 3. Ba nguyên tắc quản lý secret

Vụ rò rỉ key MCP trong khóa học không phải do chọn sai phương thức xác thực, mà do **credential nằm sai chỗ** (inline trong file đã commit) và không dọn được khi đã lan.

1. **Tách biệt:** config chỉ chứa **tên biến tham chiếu**, giá trị ở nơi khác. Lý do cơ học: config bị commit, share, clone; giá trị inline đi theo mọi bản sao và nằm lại trong lịch sử git, ghi đè không xóa được.
2. **Nơi lưu giá trị:**
   - **Biến môi trường:** secret cục bộ, ngắn hạn (CI runner đặt secret, config đọc theo tên, không ghi đĩa).
   - **Secret store:** secret dùng chung hoặc cần audit. Trả secret cho bên được phép lúc runtime, ghi lại **ai đọc gì**, rotate một lần là cập nhật mọi nơi dùng.
3. **Rotation:** đổi theo lịch và **ngay khi nghi lộ**; key đã lộ không thể làm bí mật lại. Credential đọc qua tên biến thì rotate mà không sửa code; credential nằm cứng trong code đã commit thì không rotate gọn được (giá trị cũ còn trong history, mọi consumer hardcode sẽ hỏng).

Hai thói quen rẻ: **scope hẹp nhất** cho từng credential (lộ thì chỉ ảnh hưởng một tích hợp) và **ghi lại service nào dùng credential nào** (rotate không bị bất ngờ). Rotation chỉ giúp phục hồi khi hai nguyên tắc đầu được giữ.

## 4. Ngành có quy định thêm gì

| Câu hỏi của khách | Công cụ |
|---|---|
| Admin khóa cấu hình được không? | **Enterprise managed configuration**: cấu hình do admin triển khai, người dùng không ghi đè |
| Truy cập được log thế nào? | **Hook `PostToolUse`** ghi mọi tool call và tham số vào audit store; chạy xác định, model không bỏ qua được |
| Dữ liệu xử lý ở đâu? | **Data residency**: server dùng HTTP endpoint ở vùng cụ thể + nền tảng triển khai ghim xử lý theo vùng; người kiểm toán có câu trả lời kiểm chứng được |

Hạ tầng và nền tảng chọn ở các phần trước có tác dụng ở lúc **audit**, không chỉ lúc build.

## 5. Ví dụ: code modernization

Rủi ro: blast radius lớn, phụ thuộc khó đoán, khó hoàn tác. Công cụ đã học xử lý từng rủi ro: **plan mode** (giữ ở đọc, duyệt đề xuất trước khi sửa file nào), **hook** (chặn path nhạy cảm theo giai đoạn), **CLAUDE.md** (quy ước pattern đích, tránh agent trôi về pattern cũ). Ba câu hỏi chốt **trước khi bắt đầu** (áp dụng cho mọi tác vụ agentic rủi ro cao): blast radius là gì; thay đổi được audit thế nào (PostToolUse có đủ cho người review?); ai duyệt từng giai đoạn (plan mode tạo ranh giới, nhưng **quy trình duyệt do mình định nghĩa và ghi lại trước**).

## 6. Checklist

| Loại | Xác thực | Secret ở đâu | Log | Ai khóa config |
|---|---|---|---|---|
| Remote, user | OAuth | Token do provider cấp, client lưu | PostToolUse → audit log | Admin, managed settings |
| Remote, service | API key trong env var | Chỉ env, không commit | PostToolUse → audit log | Admin, managed settings |
| Local | Quyền file system | Không cần credential; deny rule giới hạn path | PostToolUse → audit log | Deny rule trong managed settings |

Nhận xét: hai cột cuối **giống nhau ở cả ba hàng**. Log và khóa config là lớp quản trị chung, không thuộc riêng kiểu xác thực nào (xem mục 7.1).

---

## 7. Đối chiếu cách hiểu của mình (tự suy luận từ góc nhìn authentication provider)

Hướng nhìn "giống một authentication provider" là **hữu ích**: các mối quan tâm (danh tính, secret, rotation, cấu hình tập trung, audit) đúng là cùng một họ. Chỗ cần chỉnh là **vai trò**: trong bài học, Claude Code và MCP là phía **dùng** xác thực (client, và server xác minh credential), không phải provider phát hành danh tính. Nhiều chỗ lệch bên dưới xuất phát từ việc đặt mình ở phía provider.

| Ý | Đánh giá |
|---|---|
| 7.1 Ba loại xác thực = ba tầng của provider | **Đúng một phần**: ý map được, nhưng "tầng" không chính xác; nên map theo **luồng/kiểu danh tính** |
| 7.2 Secret: env/vault, không để trong file, rotation, refresh token | **Đúng phần lớn**, cần tách hai loại key và làm rõ refresh token |
| 7.3 Managed config = cấu hình chung do admin đặt | **Đúng**, so sánh với TLS/CORS/cookie/endpoint provider là hợp lý; chỉ khác hướng cưỡng chế (server áp lên client so với admin đẩy xuống từng client) |
| 7.4 Data residency giống lưu trace APM/OTEL | **Sai**: khác khái niệm, nhưng có liên hệ thú vị |

### 7.1 Ba loại xác thực

**Bạn hiểu:** Local = tầng system/admin; Remote-service = tầng ứng dụng trỏ tới provider lấy JWK, phân quyền mức service không quan tâm user; Remote-user = xác thực trực tiếp với user, không qua bên thứ ba, mọi quyền cần user đồng ý.

**Đúng:**
- Remote-service: phân quyền ở mức **service**, danh tính là service account, không phải người. Khớp bài.
- Remote-user: mọi quyền phải có **sự đồng ý của người dùng** (bước duyệt trong luồng OAuth). Khớp bài.
- Hệ quả đáng giữ: với remote-service, log chỉ thấy "service X", không thấy người nào. Muốn truy ra người thì phải ghi thêm ở nơi khác. Đây là lý do câu hỏi "model hành động dưới danh nghĩa ai" của mục 1 quan trọng. **[ngoài tài liệu]**

**Cần chỉnh:**
- **Local không phải "tầng admin".** Local nghĩa là **không có giao thức xác thực**; niềm tin dựa vào hệ điều hành (ai chạy được tiến trình và đọc được file thì dùng được). "Admin có thể khóa cấu hình" là cột **cuối của bảng checklist**, áp dụng cho **cả ba loại** như đã nêu ở mục 6. Nên tách hai trục: *xác thực* (3 loại) và *quản trị* (managed config, deny rule, hook), đừng gộp.
- **Remote-user không "không qua bên thứ ba".** OAuth có **ba bên**: người dùng (cấp quyền), Claude Code (client hành động thay mặt người dùng), và dịch vụ (vừa là authorization server hiển thị trang đăng nhập, vừa là resource server giữ dữ liệu). Đặc điểm của OAuth là **ủy quyền (delegation)**: token cho Claude Code quyền hạn chế thay mặt người dùng, **không** để Claude Code biết mật khẩu. Ý đúng của bạn là "người dùng phải đồng ý", không phải "không có bên thứ ba".
- **JWK không phải thứ Claude Code lấy ở loại remote-service.** Bài nói loại này dùng **API key tĩnh** trong biến môi trường. JWK (JSON Web Key Set) là cách bên **nhận** token lấy public key để xác minh chữ ký JWT; nó xuất hiện ở phía MCP server khi server xác minh token, không phải bước bạn cấu hình trong Claude Code. **[ngoài tài liệu]**
- "Việc xác định user là của service, không liên quan provider hay Anthropic": đúng tinh thần (Claude Code nói chuyện thẳng với dịch vụ, Anthropic không đứng giữa luồng này), nhưng bài không nêu thẳng câu này; mình chỉ suy luận. **[ngoài tài liệu]**

**Cách map chính xác hơn** **[ngoài tài liệu]** (so với thuật ngữ OAuth/OIDC bạn đang dùng):

| Kiểu trong bài | Gần với | Danh tính | Ai xác minh |
|---|---|---|---|
| Remote, user | Authorization Code flow (ủy quyền) | Một người cụ thể, qua consent | Authorization server của dịch vụ |
| Remote, service | Client Credentials / API key | Service account | MCP server kiểm key |
| Local (stdio) | Không có giao thức xác thực | Tài khoản OS chạy tiến trình | Hệ điều hành (quyền file) |

(API key đơn giản hơn Client Credentials: key tĩnh, không có bước đổi lấy token. "Gần với" chỉ để định vị.)

**Local không map vào OAuth, và không phải Implicit Flow.** **[ngoài tài liệu]**
- Implicit Flow vẫn là luồng **ủy quyền cho người dùng**: có redirect qua trình duyệt, có consent, có token (trả thẳng trong URL fragment). Nó ứng với hàng "Remote, user", chỉ là biến thể cũ và kém an toàn, đã bị OAuth 2.1 bỏ.
- OAuth sinh ra để **ủy quyền truy cập giữa các bên qua mạng**. stdio là tiến trình con trên cùng máy, không có bên thứ hai, không có token, không có grant nào cả, nên đúng ra **không có tương đương trong OAuth**.
- Khái niệm gần nhất là **ambient authority** (quyền mặc nhiên): tiến trình thừa hưởng quyền của tài khoản OS chạy nó, giống Windows Integrated Auth hoặc peer credentials của Unix socket. Xác thực "đã xong" ở lúc đăng nhập vào máy; phần còn lại là **phân quyền**, mà ở bài chính là **deny rule** giới hạn path.
- **Kết luận:** trong ba loại của bài, chỉ hai loại thuộc OAuth (Remote user = Authorization Code, Remote service ≈ Client Credentials/API key). Local nằm ngoài OAuth và quản trị hoàn toàn bằng deny rule. Vì vậy cách chia "ba tầng của một provider" không khớp hẳn: đây là ba **mô hình tin cậy** khác nhau, không phải ba tầng của một hệ thống.

### 7.2 Secret và rotation

**Đúng:**
- Không nên để secret trong file; nên dùng biến môi trường hoặc secret vault. Khớp bài.
- Rotation là chu kỳ quan trọng cho mọi credential. Khớp bài.
- Phân biệt khi nào dùng env hay vault: bài nói env cho secret **cục bộ, ngắn hạn**; vault khi secret **dùng chung hoặc cần audit** (ghi ai đọc gì, rotate một chỗ cập nhật mọi consumer). Bạn mới nêu "env hoặc vault", nên bổ sung tiêu chí này.

**Cần chỉnh:**
- **Lý do không để trong file không phải "tránh bị phát hiện khi code bị lộ".** Lý do là cơ học: config bị commit, share, clone; giá trị inline đi theo mọi bản sao và **nằm lại trong lịch sử git** dù sau này ghi đè. Tức là không có chuyện "giấu cho kín" mà là "giá trị không được nằm ở nơi dễ bị sao chép". Hệ quả: một khi đã vào history thì chỉ còn cách **rotate**.
- **Hai loại key khác vai trò.** Secret key của provider để **ký/giải mã token** (thường là cặp khóa: private giữ kín, public công bố qua JWKS) là một loại. Credential trong bài (API key, PAT, client secret) là loại **bearer secret phía consumer**: đưa ra để chứng minh "tôi là service này". Quy tắc bảo quản (env/vault, rotate) giống nhau, nhưng bạn trong bài ở vai **consumer**. **[ngoài tài liệu]** Điểm trùng hay: provider rotate signing key bằng cách để **nhiều key cùng tồn tại** trong JWKS (phân biệt bằng `kid`) để consumer không gãy; còn ở bài, rotate không đụng code vì code **tham chiếu theo tên**. Cả hai đều là "gián tiếp hóa để thay giá trị mà không phá consumer".
- **Refresh token là so sánh tốt nhưng không đồng nhất với rotation của bài.** Access token sống ngắn rồi được đổi bằng refresh token là cơ chế **tự động** theo giao thức, cùng tinh thần "credential ngắn hạn giới hạn thiệt hại". Rotation của bài là **thay credential gốc** (API key, PAT) theo lịch hoặc khi nghi lộ, thường do người hoặc quy trình chủ động. Ngoài ra refresh token tự nó là credential **dài hạn** cần bảo vệ (và thu hồi khi cần, xem `logout` ở note MCP mục 9). **[ngoài tài liệu]**

### 7.3 Enterprise managed configuration

**Đúng:** là cấu hình do **admin** đặt cho toàn tổ chức, người dùng không ghi đè được, nên xác thực nhất quán và không phụ thuộc vào file settings của từng dev. Khớp bài. Ở note MCP (mục 7) mình đã ghi cơ chế cụ thể: scope enterprise ưu tiên **trên mọi scope khác**.

**Cần chỉnh (ví dụ so sánh):**
- **Ý của bạn là đúng:** endpoint của provider (`openid-configuration`, `jwks_uri`), TLS, CORS, cookie là cấu hình **dùng chung, do bên vận hành đặt, client và người dùng cuối không đổi được**. Đó chính là tinh thần của managed config. (Lần đầu mình đọc lệch thành "tác dụng của JWK".)
- **Chỗ khác nhau duy nhất là hướng cưỡng chế** **[ngoài tài liệu]**: TLS/CORS/cookie do **server** áp lên mọi client kết nối tới nó. Managed config do admin **đẩy xuống từng máy client** (Claude Code của từng dev) và đè lên cấu hình cá nhân. Vì Claude Code chạy trên máy dev, nên cần cơ chế "đẩy chính sách xuống endpoint" như Group Policy/MDM, tức là ghi đè theo thứ tự ưu tiên, chứ không thể chỉ dựa vào server. Phần `openid-configuration` còn là metadata *mô tả* endpoint; việc cưỡng chế nằm ở cấu hình server phía sau nó.
- **Logging không thuộc managed config** theo bài. Log do **hook `PostToolUse`** đảm nhiệm, và bài chỉ ngầm ý (cột "ai khóa" trong checklist) là cấu hình cần được khóa; tài liệu không nói cách khóa hook. Chưa kiểm chứng, xem mục 8.

### 7.4 Data residency

**Bạn hiểu:** giống lưu trace HTTP request bởi APM/OTEL, nhưng không chắc.

**Đánh giá: không đúng, đây là hai thứ khác nhau.**
- **Data residency** = dữ liệu được **xử lý và lưu ở đâu về mặt địa lý/pháp lý** (vùng, quốc gia), thường do luật hoặc hợp đồng quy định (ví dụ dữ liệu của khách EU phải ở EU). Nó là **ràng buộc về vị trí**, không phải cơ chế ghi nhận.
- **APM/OTEL trace** = **quan sát** (observability): ghi lại điều gì đã xảy ra, mất bao lâu. Nó trả lời "chuyện gì xảy ra", không trả lời "dữ liệu nằm ở đâu".
- Trong bài, residency được thực hiện bằng **hai mảnh**: endpoint HTTP của server đặt ở vùng cụ thể + nền tảng triển khai ghim xử lý vào vùng đó. Kết quả là người kiểm toán có thể **kiểm chứng** "dữ liệu đi đâu". Tương tự khi chọn region cho một dịch vụ cloud (Azure/AWS) trong .NET. **[ngoài tài liệu]**
- **Liên hệ thú vị:** trace và audit log **cũng chứa dữ liệu**, và hook `PostToolUse` ghi **tham số của tool call**, có thể gồm dữ liệu nhạy cảm. Vậy chính **audit store và hệ thống trace cũng phải tuân thủ residency**. Đây là nơi hai khái niệm giao nhau, nhưng chúng vẫn không phải một. **[ngoài tài liệu]**

## 8. Còn lại và việc cần kiểm tra

- Chưa kiểm chứng: hook `PostToolUse` có được **khóa qua managed settings** không và bằng cơ chế nào (bài chỉ ngầm ý qua bảng checklist). Cần đọc docs trước khi khẳng định.
- Bài nhắc "nền tảng triển khai ghim vùng" và "infrastructure requirement ở phần trước của module" nhưng đoạn đã nhận không nêu cụ thể nền tảng nào. Bổ sung khi nhận phần đó.
- Chưa thực hành: thử một MCP server OAuth (Linear/Sentry) và `claude mcp login/logout` để thấy luồng consent; thử hook `PostToolUse` ghi log ra file.
- Câu hỏi mở của mình: với remote-service (một service account chung), làm sao vẫn truy ra **người** đứng sau mỗi tool call khi audit? Bài chỉ nêu "danh tính có audit được không" mà chưa trả lời cho trường hợp này.

---

## 9. Key Takeaways của cả module (7 ý)

Nguồn: phần "Key takeaways" cuối tài liệu khóa học, mỗi mục một ý, nối các phần của module lại với nhau. Dưới đây là bản tóm tắt bằng tiếng Việt, kèm chỗ để xem chi tiết trong notes. Phần "Mình rút ra" là diễn giải của mình **[ngoài tài liệu]**.

| # | Takeaway | Chi tiết ở |
|---|---|---|
| 1 | **Permission mode là quyết định về rủi ro, không phải về tốc độ.** | [W3D1 Permission Modes](NOTES_W3D1_Permission_Modes.md) |
| 2 | **Kết quả AI code review là danh sách phát hiện để phân loại, không phải phán quyết để áp dụng.** | Chưa có note riêng |
| 3 | **Skill mang đi được, nhưng "chạy ở đâu cũng được" là thứ phải thiết kế.** | [W3D2 Packaging Workflows](NOTES_W3D2_Packaging_Workflows.md) |
| 4 | **Context bền vững cần đúng cơ chế cho từng vấn đề.** | [W3D1 Durable Project Context](NOTES_W3D1_Durable_Project_Context.md) |
| 5 | **Setup chia sẻ được cần thành phần di động (portable).** | [W3D2 Packaging Workflows](NOTES_W3D2_Packaging_Workflows.md) |
| 6 | **Transport và scope là hai quyết định độc lập nhưng hệ quả phụ thuộc nhau.** | [W3D2 MCP Servers](NOTES_W3D2_MCP_Servers.md) mục 5, 7, 10 |
| 7 | **Tích hợp doanh nghiệp phải xác định yêu cầu bảo mật trước khi triển khai.** | Note này, mục 1–6 |

### 1. Permission mode là quyết định rủi ro
- Các mode chạy từ "hỏi mọi thứ" đến "không hỏi gì". Chọn mode theo **hồ sơ rủi ro của công việc và môi trường**, không theo mong muốn ít prompt hơn.
- Mode bypass trên máy dev với codebase thật là bỏ **mọi chốt chặn** giữa agent và file của bạn.
- **Deny rule** trên đường dẫn không được đụng, đặt ở cấp project hoặc enterprise, lấp khoảng hở mà mode một mình không lấp được.
- Mình rút ra: mode chỉnh *mức hỏi*, deny rule chỉnh *ranh giới cứng*; hai thứ bổ sung nhau chứ không thay nhau.

### 2. Code review của AI là danh sách để triage
- Tin những phát hiện reviewer **chứng minh được từ chính diff** (thiếu kiểm tra null, resource không đóng), và **xác nhận trên đúng dòng nó trích dẫn**.
- Mọi khẳng định về **hành vi lúc chạy** hoặc **hệ thống khác** là **giả thuyết cần kiểm tra**, vì reviewer nói mà không có bằng chứng cần thiết.
- Đặt **cổng người duyệt** tại điểm phát hiện biến thành hành động **khó hoàn tác**.
- Tăng độ chính xác bằng cách đưa cho reviewer **quy ước** mà nếu không nó phải đoán.
- Lưu ý: notes hiện **chưa có phần code review**; ý này mới có từ phần tóm tắt, cần bổ sung khi học phần tương ứng.

### 3. Skill portable nhưng phải thiết kế
- Cùng một `SKILL.md` chạy được trên Claude Code, Messages API và Agent SDK, nhưng mỗi nơi nạp và cô lập khác nhau: **khám phá qua file system** (Claude Code), **beta header + container chạy code** (API), **`settingSources`** (SDK).
- Skill có `description` rõ ràng và **không giả định môi trường cục bộ** thì mang đi tốt; skill giả định terminal của tác giả thì không.
- Ở mọi runtime, **subagent bắt đầu sạch**: không tự nạp sẵn skill.

### 4. Bốn cơ chế cho bốn vấn đề
| Cơ chế | Giải quyết |
|---|---|
| CLAUDE.md | Bộ nhớ project bền qua session, nhưng **loãng khi phình to** |
| Rules file | Giới hạn chỉ dẫn đúng chỗ áp dụng |
| Hook | Guardrail **xác định (deterministic)**, không xác suất |
| Subagent | Giữ việc khám phá ra khỏi context chính |

Nhồi cả bốn vào CLAUDE.md cho ra một file **khó bảo trì và dễ bị bỏ qua**.

### 5. Setup chia sẻ cần thành phần portable
- Plugin tham chiếu **đường dẫn tuyệt đối** tới thư mục home của tác giả sẽ cài được trên một máy và hỏng trên mọi máy khác.
- Skill, hook, component sẽ chia sẻ phải dùng **đường dẫn tương đối theo root project**; yêu cầu biến môi trường phải **được ghi lại hoặc kiểm tra lúc cài**.
- **Thử cài trên máy sạch** trước khi phát hành.

### 6. Transport và scope
- **stdio** cho server chạy trên máy bạn; **HTTP** cho mọi thứ host từ xa hoặc nhiều dev dùng.
- **Local scope** giữ server ở mức cá nhân; **project scope** chia sẻ qua `.mcp.json` trong repo.
- Tổ hợp phải khớp ý định triển khai: server dùng chung của nhóm cần **HTTP + project hoặc enterprise scope**.
- **Bẫy:** server stdio trong `.mcp.json` là cấu hình **trông như chia sẻ được nhưng không phải** (mỗi người phải tự cài runtime, xem note MCP mục 7).

### 7. Tích hợp doanh nghiệp
Khách có quy định hỏi về danh tính, data residency, log truy cập, kiểm soát cấu hình. Đáp án tương ứng:

| Yêu cầu | Đáp án |
|---|---|
| Danh tính (dịch vụ theo người dùng) | OAuth |
| Credential dịch vụ | Biến môi trường (hoặc secret store, xem mục 3) |
| Log truy cập | Hook `PostToolUse` |
| Khóa cấu hình | Enterprise managed settings |
| Vị trí xử lý dữ liệu | Data residency (endpoint theo vùng + nền tảng ghim vùng) |

Không cái nào khó làm, nhưng **tất cả đều khó vá sau khi** triển khai production đã trượt kiểm tra bảo mật.

### Sợi chỉ chung xuyên module **[ngoài tài liệu]**
- **Mode và deny rule, hook và CLAUDE.md, transport và scope, xác thực và quản trị:** lần nào cũng là hai lớp, một lớp *chọn mức* (mềm, theo ngữ cảnh) và một lớp *ranh giới cứng* (không ghi đè được). Chọn đúng lớp cho đúng vấn đề là điểm chung của cả bảy ý.
- Ba ý cuối (4, 5, 7) cùng nhắc một bài học: thiết kế cho môi trường **không phải của mình** (máy khác, người khác, kiểm toán) ngay từ đầu, vì sửa sau rất đắt.
