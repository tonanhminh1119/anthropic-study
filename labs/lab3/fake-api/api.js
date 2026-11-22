// Fake ticket API cho lab3 — chỉ dùng module `http` của Node, không phụ thuộc gói ngoài.
//
// Chạy:
//   PowerShell:  $env:FAKE_API_TOKEN = "dev-token"; node server.js
//   Bash:        FAKE_API_TOKEN=dev-token node server.js
//
// Token KHÔNG được hardcode: đọc từ biến môi trường FAKE_API_TOKEN.
//
// Cấu trúc (giống Minimal API / Express / Gin / FastAPI):
//   1. Route table  : danh sách { method, path, handler }
//   2. Handlers     : mỗi endpoint một hàm, trả về { status, body, headers }
//   3. Dispatcher   : auth -> match route -> gọi handler -> ghi response

const http = require("node:http");
const { timingSafeEqual } = require("node:crypto");

const HOST = "127.0.0.1";
const PORT = 4000;
const TOKEN = process.env.FAKE_API_TOKEN;

if (!TOKEN) {
  console.error("Thiếu biến môi trường FAKE_API_TOKEN. Server không khởi động.");
  process.exit(1);
}

const PRIORITIES = ["low", "medium", "high"];
const STATUSES = ["open", "closed"];
const MAX_BODY_BYTES = 64 * 1024;

// ---------------------------------------------------------------------------
// Dữ liệu in-memory, mất khi tắt server.
// ---------------------------------------------------------------------------
const tickets = [
  { id: 1, title: "Không đăng nhập được", priority: "high", status: "open" },
  { id: 2, title: "Đổi mật khẩu bị lỗi", priority: "medium", status: "open" },
  { id: 3, title: "Cập nhật ảnh đại diện", priority: "low", status: "closed" },
];
let nextId = tickets.length + 1;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// Throw trong handler -> dispatcher đổi thành response lỗi (như exception middleware).
class HttpError extends Error {
  constructor(status, message, headers = {}) {
    super(message);
    this.status = status;
    this.headers = headers;
  }
}

function isAuthorized(req) {
  const match = /^Bearer (.+)$/.exec(req.headers["authorization"] || "");
  if (!match) return false;
  const given = Buffer.from(match[1]);
  const expected = Buffer.from(TOKEN);
  // So sánh hằng-thời-gian; độ dài khác nhau thì từ chối luôn.
  return given.length === expected.length && timingSafeEqual(given, expected);
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new HttpError(413, "Body quá lớn"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "null"));
      } catch {
        reject(new HttpError(400, "JSON không hợp lệ"));
      }
    });
    req.on("error", reject);
  });
}

function parseId(raw) {
  const id = Number(raw);
  if (!Number.isInteger(id) || id < 1) {
    throw new HttpError(400, "id phải là số nguyên dương");
  }
  return id;
}

function findTicketIndex(id) {
  const index = tickets.findIndex((t) => t.id === id);
  if (index === -1) throw new HttpError(404, "Ticket không tồn tại");
  return index;
}

// ---------------------------------------------------------------------------
// Handlers — mỗi endpoint một hàm.
// ctx = { req, params, query, readBody }  ->  trả { status, body?, headers? }
// ---------------------------------------------------------------------------

function listTickets({ query }) {
  const status = query.get("status");
  if (status !== null && !STATUSES.includes(status)) {
    throw new HttpError(400, `status phải là một trong: ${STATUSES.join(", ")}`);
  }
  const result = status ? tickets.filter((t) => t.status === status) : tickets;
  return { status: 200, body: result };
}

function getTicket({ params }) {
  const index = findTicketIndex(parseId(params.id));
  return { status: 200, body: tickets[index] };
}

async function createTicket({ readBody }) {
  const body = await readBody();
  const title = typeof body?.title === "string" ? body.title.trim() : "";
  const priority = body?.priority;
  if (!title) {
    throw new HttpError(400, "title là bắt buộc");
  }
  if (!PRIORITIES.includes(priority)) {
    throw new HttpError(400, `priority phải là một trong: ${PRIORITIES.join(", ")}`);
  }
  const ticket = { id: nextId++, title, priority, status: "open" };
  tickets.push(ticket);
  return { status: 201, body: ticket, headers: { Location: `/tickets/${ticket.id}` } };
}

function deleteTicket({ params }) {
  const index = findTicketIndex(parseId(params.id));
  tickets.splice(index, 1);
  return { status: 204 };
}

// ---------------------------------------------------------------------------
// Route table — tương đương app.MapGet/MapPost/... của .NET.
// ---------------------------------------------------------------------------
const routes = [
  { method: "GET", path: "/tickets", handler: listTickets },
  { method: "GET", path: "/tickets/:id", handler: getTicket },
  { method: "POST", path: "/tickets", handler: createTicket },
  { method: "DELETE", path: "/tickets/:id", handler: deleteTicket },
];

// Biên dịch "/tickets/:id" thành regex một lần lúc khởi động.
for (const route of routes) {
  const names = [];
  const source = route.path
    .split("/")
    .map((seg) => {
      if (seg.startsWith(":")) {
        names.push(seg.slice(1));
        return "([^/]+)";
      }
      return seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    })
    .join("/");
  route.regex = new RegExp(`^${source}$`);
  route.paramNames = names;
}

// Tìm route khớp. Trả về { route, params } hoặc throw 404 / 405.
function matchRoute(method, pathname) {
  const sameMethodAllowed = [];
  for (const route of routes) {
    const m = route.regex.exec(pathname);
    if (!m) continue;
    if (route.method !== method) {
      sameMethodAllowed.push(route.method);
      continue;
    }
    const params = {};
    route.paramNames.forEach((name, i) => {
      params[name] = decodeURIComponent(m[i + 1]);
    });
    return { route, params };
  }
  if (sameMethodAllowed.length > 0) {
    throw new HttpError(405, "Method not allowed", { Allow: sameMethodAllowed.join(", ") });
  }
  throw new HttpError(404, "Not found");
}

// ---------------------------------------------------------------------------
// Dispatcher — chạy cho MỌI request: auth -> route -> handler -> response.
// ---------------------------------------------------------------------------
function writeResponse(res, { status, body, headers = {} }) {
  const payload = body === undefined ? "" : JSON.stringify(body);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(payload),
    ...headers,
  });
  res.end(payload);
}

async function dispatch(req, res) {
  try {
    if (!isAuthorized(req)) {
      throw new HttpError(401, "Unauthorized", { "WWW-Authenticate": "Bearer" });
    }
    const url = new URL(req.url, `http://${HOST}:${PORT}`);
    const { route, params } = matchRoute(req.method, url.pathname);
    const result = await route.handler({
      req,
      params,
      query: url.searchParams,
      readBody: () => readJsonBody(req),
    });
    writeResponse(res, result);
  } catch (err) {
    if (res.headersSent) return res.end();
    if (err instanceof HttpError) {
      return writeResponse(res, {
        status: err.status,
        body: { error: err.message },
        headers: err.headers,
      });
    }
    console.error(err);
    writeResponse(res, { status: 500, body: { error: "Internal error" } });
  }
}

// ---------------------------------------------------------------------------
// Khởi động. listen() giữ process sống đến khi bị tắt (Ctrl+C / SIGTERM).
// ---------------------------------------------------------------------------
const server = http.createServer(dispatch);

server.listen(PORT, HOST, () => {
  console.log(`fake-api đang nghe tại http://${HOST}:${PORT}`);
});

// Tắt êm: ngừng nhận kết nối mới, chờ request đang chạy xong rồi mới thoát.
function shutdown(signal) {
  console.log(`\nNhận ${signal}, đang tắt server...`);
  server.close(() => process.exit(0));
  server.closeIdleConnections?.();
}
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
