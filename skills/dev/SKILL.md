---
description: Developer (Guided) — pair programming mode. Morai là navigator, Dev review từng bước, commit khi Dev quyết định.
---

# Dev Agent — Guided Mode (Pair Programming)

Morai đóng vai **navigator**: phân tích, đề xuất, viết code theo từng chunk.
Dev đóng vai **reviewer**: xem, phản hồi, quyết định commit khi nào.

**Morai KHÔNG tự commit, KHÔNG tự push, KHÔNG tự tạo PR** trừ khi Dev nói rõ.

> Xem `/morai:dev-auto` nếu task là bug đơn giản đủ điều kiện auto.

## Input
Task ID hoặc mô tả task: $ARGUMENTS

## Điều kiện tiên quyết
- `gh` CLI install và authenticated để tạo PR (khi Dev sẵn sàng)

---

## Phase 1 — Hiểu task (không cần Dev approve)

### Bước 1 — Đọc task & load context
- Dùng `morai-file` MCP: đọc `tasks/<ticket-id>/<task-id>.json`
- Dùng `morai-file` MCP: đọc spec `specs/<ticket-id>.md`
- Dùng `morai-file` MCP: đọc `designs/<ticket-id>-detail.md` nếu có
- Dùng `morai-memory`: load pipeline state
- Cập nhật task `status → "in-progress"`

### Bước 2 — Research codebase
- Dùng `morai-rag` MCP: search patterns liên quan
- Dùng `morai-rag` MCP: tìm existing code có thể tái sử dụng
- Dùng `morai-git` MCP: xem recent changes, current branch

---

## ⛔ GATE 1 — Approach Review (formal gate)

Sau Phase 1, tạo gate và trình bày approach:

```python
gate = morai-pipeline: create_gate(
    ticket_id=$TICKET_ID,
    gate_type="REVIEW",
    question=f"Approach: {task.title}",
    context="""
    Scope: [files cần tạo/sửa]
    Pattern tham chiếu: [existing code tương tự]
    Thứ tự implement: [1. module A — lý do, 2. module B — lý do]
    Tests cần viết: [list test cases]
    Rủi ro: [nếu có]
    """,
    timeout_minutes=120,
)
```

Hiển thị gate cho Dev theo format chuẩn trong `agents/hitl.md`.

**Xử lý response:**
- Dev: "approve" / "ok" → `resolve_gate(response="approve")` → tiếp tục Phase 2
- Dev: "request_changes: X" → adjust approach → tạo gate mới (loop)
- Dev: "abort" → `resolve_gate(response="abort")` → `block_pipeline`
- Gate expired → `block_pipeline(reason="Gate expired")` → báo Dev

---

## Phase 2 — Implement từng chunk

Implement **từng module/file một**, theo thứ tự đã agree.

### Cho mỗi chunk:

**2a — Viết tests trước (TDD)**
- Viết unit test cho behavior của chunk này
- Hiển thị test code cho Dev

**2b — Implement**
- Viết code cho chunk
- Hiển thị diff/code cho Dev
- Giải thích ngắn gọn quyết định design quan trọng (nếu có)

**2c — Chạy tests**
- Báo cáo kết quả: pass/fail + output

**⛔ Micro-gate sau mỗi chunk:**
```
✓ Tests: [X pass / Y fail]
✓ Code: [tóm tắt 1-2 câu những gì vừa làm]

Anh xem thử chunk này, em tiếp sang [chunk tiếp theo] nhé?
```

**DỪNG — Chờ Dev confirm hoặc feedback trước khi sang chunk tiếp theo.**

---

## CI Check — Bắt buộc trước GATE 2

Đọc CI commands của project:
```
morai-file: read_file(".morai/knowledge/ci.json")
```

Nếu file chưa tồn tại → nhắc Dev chạy `/morai:scan` trước, hoặc hỏi trực tiếp CI commands là gì.

Chạy theo thứ tự từ `commands` trong ci.json:
```
lint → format_check → typecheck → test
```

Nếu bất kỳ bước nào fail → fix ngay, không tiếp tục đến GATE 2.

## ⛔ GATE 2 — Commit (formal gate, chỉ khi CI pass)

```python
gate = morai-pipeline: create_gate(
    ticket_id=$TICKET_ID,
    gate_type="CONFIRM",
    question="Ready to commit",
    context=f"CI: ✅ all pass\nFiles changed: {files_changed}\nTests: {test_results}",
    options=["commit", "review more", "abort"],
    timeout_minutes=60,
)
```

Dev respond: "commit" → `resolve_gate` → `morai-git: commit(message, files)`

**Không tự commit dù code đã xong và tests pass — CI phải pass trước.**

---

## ⛔ GATE 3 — Push & PR (formal gate)

```python
gate = morai-pipeline: create_gate(
    ticket_id=$TICKET_ID,
    gate_type="CONFIRM",
    question="Ready to push and create PR",
    context=f"Branch: {branch}\nPR title: {pr_title}\nPR body preview: ...",
    options=["push and create PR", "edit PR body", "abort"],
    timeout_minutes=60,
)
```

Dev respond: "push and create PR" → `resolve_gate` → `morai-git: push()` → `create_pr()`
- Cập nhật task: `status → "done"`, `pr_url → <url>`
- Update pipeline state

> **Slack (optional):** Nếu configured → notify reviewer.
