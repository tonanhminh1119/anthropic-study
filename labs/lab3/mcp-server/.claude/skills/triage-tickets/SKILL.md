---
name: triage-tickets
description: Phân loại và sắp thứ tự xử lý các ticket đang mở. Dùng khi người dùng muốn triage, phân loại, ưu tiên hoặc "nên làm ticket nào trước" trong hệ thống tickets (MCP server `tickets`). Không dùng để tạo, sửa hay xóa ticket.
---

# Triage tickets

1. Gọi tool `list_tickets` với `status="open"` (chỉ lấy ticket đang mở).
2. Nếu không có ticket open nào thì nói rõ điều đó và dừng, không bịa dữ liệu.
3. Nhóm ticket theo `priority`: high → medium → low.
4. Trong mỗi nhóm, đề xuất thứ tự xử lý kèm lý do ngắn (ví dụ ảnh hưởng đăng nhập hay thanh toán thì làm trước).
5. Chỉ đọc dữ liệu: **không gọi `delete_ticket`**, và không gọi `create_ticket` nếu người dùng không yêu cầu.
6. Xuất kết quả đúng mẫu bảng cố định dưới đây, không thêm hay bớt cột:

| Thứ tự | ID | Tiêu đề | Priority | Lý do xử lý |
|---|---|---|---|---|
| 1 | <id> | <tiêu đề> | high | <lý do ngắn> |

7. Kết thúc bằng một câu tóm tắt số ticket theo từng priority (ví dụ: "2 high, 1 medium, 0 low").
