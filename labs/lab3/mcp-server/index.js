// MCP server "tickets" — cầu nối giữa Claude và fake-api (../fake-api/api.js).
// Tools: list_tickets, get_ticket, create_ticket, delete_ticket.
// Lưu ý: log bằng console.error (stderr), KHÔNG dùng console.log (stdout là kênh giao thức).

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API = process.env.FAKE_API_URL ?? "http://127.0.0.1:4000";
const TOKEN = process.env.FAKE_API_TOKEN;
const server = new McpServer({ name: "tickets", version: "0.1.0" });

const text = (t, isError = false) => ({ isError, content: [{ type: "text", text: t }] });

// Helper: gọi fake-api (kèm Bearer token) và đổi kết quả thành định dạng tool result của MCP.
async function callApi(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      ...(body !== undefined && { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    // Kèm lý do từ API (vd. "priority phải là một trong: ...") để Claude tự sửa tham số.
    const reason = (await res.json().catch(() => null))?.error;
    return text(reason ? `API ${res.status}: ${reason}` : `API ${res.status}`, true);
  }
  if (res.status === 204) return text("OK (204 No Content)"); // DELETE không có body
  return text(JSON.stringify(await res.json()));
}

const ticketId = z.number().int().positive().describe("Ticket id");

server.registerTool(
  "list_tickets",
  { description: "List tickets, optionally filtered by status",
    inputSchema: { status: z.enum(["open", "closed"]).optional() },
    annotations: { readOnlyHint: true } },
  async ({ status }) => {
    console.error("[list_tickets]", status);          // stderr, KHÔNG console.log
    return callApi(`/tickets${status ? `?status=${status}` : ""}`);
  });

server.registerTool(
  "get_ticket",
  { description: "Get a single ticket by id",
    inputSchema: { id: ticketId },
    annotations: { readOnlyHint: true } },
  async ({ id }) => {
    console.error("[get_ticket]", id);
    return callApi(`/tickets/${id}`);
  });

server.registerTool(
  "create_ticket",
  { description: "Create a new ticket (status starts as open)",
    inputSchema: {
      title: z.string().min(1).describe("Ticket title"),
      priority: z.enum(["low", "medium", "high"]),
    } },
  async ({ title, priority }) => {
    console.error("[create_ticket]", title, priority);
    return callApi("/tickets", { method: "POST", body: { title, priority } });
  });

server.registerTool(
  "delete_ticket",
  { description: "Permanently delete a ticket by id",
    inputSchema: { id: ticketId },
    annotations: { destructiveHint: true } },
  async ({ id }) => {
    console.error("[delete_ticket]", id);
    return callApi(`/tickets/${id}`, { method: "DELETE" });
  });

await server.connect(new StdioServerTransport());