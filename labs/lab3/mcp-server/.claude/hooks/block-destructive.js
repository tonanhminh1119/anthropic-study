#!/usr/bin/env node
// PreToolUse hook (bản đơn giản): chỉ chặn `rm -rf`, `git push --force` và `Remove-Item -Recurse -Force`.
// Đây là denylist: chỉ chặn những dạng viết đã liệt kê, nên luôn còn cách lách (xem LAB3.md mục 6.4).
//
// Claude Code gọi script này và đưa JSON qua stdin, dạng:
//   { "tool_name": "Bash", "tool_input": { "command": "rm -rf /tmp/x" }, ... }
//
// Exit code:  0 = cho qua  |  2 = CHẶN (stderr được gửi lại cho Claude)  |  khác = lỗi không chặn
//
// Lưu ý: package.json của dự án có "type": "module", nên file .js này chạy theo ES module
// (dùng `import`, không dùng `require`/`__dirname`).

// `let` (không phải `const`) để đoạn đọc JSON ở bên dưới có thể gán lại khi được bật.
let RULES = [
  {
    name: "rm -rf",
    // rm có cả cờ recursive (-r/-R/--recursive) lẫn force (-f/--force), thứ tự bất kỳ: -rf, -fr, -r -f...
    // [^;&|\n]* giữ việc tìm cờ trong cùng một lệnh (dừng ở ; & | hoặc xuống dòng).
    pattern:
      /(?:^|[;&|(\s])rm\b(?=[^;&|\n]*\s(?:-[a-z]*r|--recursive))(?=[^;&|\n]*\s(?:-[a-z]*f|--force))/i,
    reason: "xóa đệ quy không hỏi (rm -rf) có thể mất dữ liệu không khôi phục được",
  },
  {
    name: "git push --force",
    // git push kèm --force, --force-with-lease hoặc -f
    pattern: /\bgit\s+push\b[^;&|\n]*\s(?:--force(?:-with-lease)?|-f)(?=\s|$)/i,
    reason: "force push ghi đè lịch sử trên remote",
  },
  {
    name: "Remove-Item -Recurse -Force",
    // PowerShell: Remove-Item (hoặc alias ri) kèm cả -Recurse lẫn -Force, thứ tự bất kỳ.
    pattern: /\b(?:Remove-Item|ri)\b(?=[^;&|\n]*\s-Recurse\b)(?=[^;&|\n]*\s-Force\b)/i,
    reason: "Remove-Item -Recurse -Force xóa đệ quy không hỏi",
  },
];

// ---------------------------------------------------------------------------
// (TÙY CHỌN) Dùng bộ luật rộng hơn từ file JSON thay cho RULES ở trên.
//
// Bộ luật rộng hơn (rm -rf, git push --force, git reset --hard, git clean -f, SQL DROP/TRUNCATE/
// DELETE không WHERE, lệnh Windows, mkfs/dd...) nằm ở `destructive-rules.json` cùng thư mục.
// Mỗi luật trong JSON là chuỗi: { name, pattern, flags, reason } — JSON không lưu được RegExp
// nên `pattern` là chuỗi regex và `flags` là cờ ("i"); đoạn code dưới đây dựng lại thành RegExp.
//
// Cách bật: bỏ dấu `//` ở 4 dòng dưới (2 dòng import + lệnh gán RULES). Nếu không bật,
// script vẫn chỉ chặn 2 lệnh ở trên.
// `import.meta.dirname` cần Node >= 20.11; nếu thiếu file JSON, script sẽ lỗi (exit 1, không chặn).
//
// import { readFileSync } from "node:fs";
// import { join } from "node:path";
// RULES = JSON.parse(readFileSync(join(import.meta.dirname, "destructive-rules.json"), "utf8"))
//   .rules.map(({ pattern, flags, ...rest }) => ({ ...rest, pattern: new RegExp(pattern, flags) }));
// ---------------------------------------------------------------------------

// Gộp dòng nối bằng "\" hoặc "`" cuối dòng để lệnh nhiều dòng vẫn được kiểm tra như một.
const normalize = (cmd) => cmd.replace(/[\\`]\r?\n\s*/g, " ");

function readStdin() {
  return new Promise((resolve, reject) => {
    const chunks = [];
    process.stdin.on("data", (c) => chunks.push(c));
    process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    process.stdin.on("error", reject);
  });
}

async function main() {
  let input;
  try {
    const raw = (await readStdin()).replace(/^﻿/, ""); // bỏ BOM nếu có (Windows)
    input = JSON.parse(raw);
  } catch (err) {
    // Không đọc được input thì không biết lệnh là gì: báo lỗi (exit 1, không chặn).
    console.error(`[block-destructive] Không đọc được JSON từ stdin: ${err.message}`);
    process.exit(1);
  }

  const command = input?.tool_input?.command;
  if (typeof command !== "string" || command.trim() === "") process.exit(0);

  const text = normalize(command);
  const hit = RULES.find((rule) => rule.pattern.test(text));
  if (hit) {
    console.error(
      `[block-destructive] Đã chặn "${hit.name}": ${hit.reason}.\n` +
        `Lệnh: ${command.length > 200 ? `${command.slice(0, 200)}…` : command}\n` +
        `Hãy dùng cách an toàn hơn (chỉ định đúng đường dẫn, bỏ cờ force) hoặc nhờ người dùng tự chạy.`
    );
    process.exit(2);
  }
  process.exit(0);
}

main();
