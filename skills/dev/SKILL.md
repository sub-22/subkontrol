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

## Bước 0 — Branch Setup (trước tất cả)

```
morai-git: get_current_branch()
```

**Protected branches** (không được commit trực tiếp):
`master`, `main`, `develop`, `staging`, `production`, `release/*`

**Branch naming convention** (áp dụng mọi lúc, không chỉ khi switch):

```
{type}/{ticket_id}_{what_it_does}

feat/PROJ-123_add-user-authentication
fix/PROJ-456_resolve-null-payment
chore/PROJ-789_update-deps
refactor/PROJ-101_extract-auth-middleware
```

| Task type | Prefix |
|-----------|--------|
| Feature / story / epic | `feat/` |
| Bug / fix / hotfix | `fix/` |
| Chore / config / ci / docs | `chore/` |
| Refactor | `refactor/` |

Rules:
- Separator giữa ticket_id và description: `_` (underscore)
- Description: lowercase, dấu cách → `-`, **tối đa 35 ký tự**, tự detect ý nghĩa ngắn gọn từ task title
- Không viết tắt khó hiểu — "add-jwt-auth" tốt hơn "ajwta"

**Nếu đang ở protected branch:**
1. Xác định type từ task (bảng trên)
2. Đề xuất branch name theo format trên
3. **Hỏi human cả 2 thứ cùng lúc — bắt buộc:**
   ```
   ⚠️ Đang ở branch protected: {current_branch}

   Branch name đề xuất: `{proposed_branch}`
   Tách từ nhánh nào sếp? (ví dụ: develop, main, release/stg)

   Sếp confirm hoặc chỉnh lại cả hai nhé.
   ```
4. Chờ human trả lời đủ **branch name + base branch**
5. Checkout base branch → `morai-git: create_branch({confirmed_branch})`

> Không tự assume base branch. Bug trên stg có thể cần tách từ `release/stg` (hotfix) hoặc `develop` (backport) — khác nhau hoàn toàn.

**Nếu đang ở đúng feature/fix branch** → tiếp tục Bước 0b.

---

## Bước 0b — Progress File (session continuity)

Sau khi branch đã xác định, trước khi bắt đầu Phase 1:

```
morai-file: file_exists("docs/progress/<ticket-id>.md")
```

**Nếu file tồn tại (resume session):**
```
morai-file: read_file("docs/progress/<ticket-id>.md")
```
- Hiển thị bảng trạng thái chunks hiện tại
- Tìm chunk đầu tiên có status `pending` hoặc `in_progress`
- Warn nếu có chunk `failed` mà chunk sau depend vào (cùng loại types/migration)
- Hỏi Dev: "Em thấy còn [X chunk pending / chunk N đang dở]. Tiếp từ đó hay bắt đầu lại?"
- Nếu tiếp → skip Phase 1 Research nếu context đã có, nhảy thẳng vào Phase 2 chunk tiếp theo

**Nếu file chưa tồn tại (session mới):**

Gate check — verify design doc tồn tại trước:
```
morai-file: file_exists("designs/<ticket-id>-detail.md")
```
Nếu không tồn tại → STOP, in:
```
❌ Design doc không tìm thấy: designs/<ticket-id>-detail.md
   Chạy /morai:architect <ticket-id> trước để tạo design.
```

Nếu tồn tại → đọc design doc để lấy danh sách chunks:
- Đọc design doc `designs/<ticket-id>-detail.md` để lấy danh sách chunks
- Tạo progress file từ template `templates/progress.md`:
  - Populate bảng chunks từ design doc (type, tên, AC-IDs)
  - Tất cả status = `pending`, retries = 0
- `morai-file: write_file("docs/progress/<ticket-id>.md", content)`
- Tiếp tục Phase 1 bình thường

> Progress file là source of truth cho chunk implementation. MCP pipeline FSM vẫn là
> source of truth cho pipeline-level transitions (BA→PM→DEV→REVIEW). Hai tầng không conflict.

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

Implement **từng chunk một** theo thứ tự trong progress file. Pick chunk đầu tiên có
status `pending` hoặc `in_progress`.

### Cho mỗi chunk:

**Trước khi bắt đầu chunk:** Update progress file → `in_progress`.

**2a-pre — Impact gap cross-check (chỉ chạy cho chunk đầu tiên của session)**

Đọc phần File Impact (L1–L4) trong `designs/<ticket-id>-detail.md`.
Với mỗi file trong các bảng L1–L4: kiểm tra file đó có xuất hiện trong cột "Source files" của bất kỳ chunk nào trong progress file không.

Nếu có file unassigned → STOP, hỏi user:
```
⚠️ File impact gap — <file> (<layer>) chưa được assign vào chunk nào.

Xử lý thế nào?
[A] Thêm vào chunk hiện tại (chunk N)
[B] Tạo chunk riêng sau chunk này
[C] Design doc sai — bỏ qua file này
```

Sau khi user chọn → ghi vào bảng "Impact Gaps Resolved" trong progress file:
| File | Layer | Resolution | Chunk Assigned | Resolved At |

Resolve hết gaps trước khi viết bất kỳ dòng code nào.

**2a — Viết tests trước (RED phase)**
- Viết unit/integration test cho behavior của chunk này
- Test focus: dựa trên AC-IDs của chunk (từ progress file) + edge cases từ spec
- Chạy verify command → confirm FAIL (assertion stage, không phải compile error)
- Hiển thị test code cho Dev

**2b — Implement (GREEN phase)**
- Viết code cho chunk
- Chạy verify command → phải GREEN
- **Retry nếu FAIL:** tối đa 3 attempts không có progress (fail count + failing test names giống nhau)
  - Có progress (số lỗi giảm hoặc test names thay đổi) → tiếp tục retry
  - 3 attempts không progress → update progress: `failed`, increment retries → báo Dev, STOP chunk này
- Hiển thị diff/code cho Dev
- Giải thích ngắn gọn quyết định design quan trọng (nếu có)

**2c — Chạy full regression check**
- Chạy full test suite (không chỉ scoped)
- Nếu có regression → fix trước khi tiếp tục

**2d — REFACTOR phase**
- Đọc `checklists/refactor-verify.md` và tự evaluate từng item
- Nếu không có findings → báo "Refactor: clean" và tiếp tục
- Nếu có findings → surface cho Dev qua AskUserQuestion multi-select (xem format trong checklist)
- Sau khi apply selected items → re-run verify → confirm vẫn GREEN

**2e — Verify checklist + Update progress**
- Chạy `checklists/verify.md` — tất cả items phải pass
- Update progress file: chunk → `done`, fill `completed_at` = today (YYYY-MM-DD)

**⛔ Micro-gate sau mỗi chunk:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  <ticket-id> — Chunk N ([type]) done ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅ Chunk 1 — types
  ...
  ✅ Chunk N — [type]    ← vừa xong
  ▶  Chunk N+1 — [type]  ← tiếp theo
  ⬜ Chunk N+2 — [type]

  X chunks còn lại.
  Tests: [X pass] | Refactor: [clean / N items applied]

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

## Commit Message — Detect Convention Trước Khi Commit

Trước khi tạo commit message, detect convention của project:

```
morai-git: get_log(max_count=20)          ← đọc pattern commit gần nhất
morai-file: read_file("CONTRIBUTING.md")  ← nếu tồn tại
morai-file: read_file(".commitlintrc.json") ← hoặc .commitlintrc.yml / .commitlintrc.js
```

**Case 1 — Project có convention riêng** (detect được từ git log hoặc config):
- Follow đúng format của project
- Ví dụ: `[PROJ-123] Add JWT authentication` hoặc `PROJ-123 | feat | add auth`
- Không override convention của dự án

**Case 2 — Không detect được convention nào** (git log không có pattern rõ ràng):
- Dùng format chuẩn của Morai:
  ```
  [{ticket_id}] {ticket_type}: {commit message mô tả task}

  # Ví dụ:
  [PROJ-123] feat: add JWT authentication middleware
  [PROJ-456] fix: resolve null pointer in payment flow
  [PROJ-789] refactor: extract auth logic to middleware
  [PROJ-101] chore: update dependencies to latest stable
  ```
- `ticket_type`: feat / fix / refactor / chore / docs / test
- `commit message`: tiếng Anh, imperative mood, ≤72 ký tự, mô tả WHAT không phải HOW

**Quan trọng — detect đúng format ticket trong prefix:**
- Nếu git log dùng `[SK] feat:` → project không có ticket number → giữ `[SK]`
- Nếu git log dùng `[SK-03] feat:` → project có ticket number trong prefix → dùng `[{PREFIX}-{ticket_num}]`
- Luôn ưu tiên format có ticket number khi có ticket ID cụ thể

**Hiển thị commit message đề xuất cho Dev xem trước khi commit.**

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

**Auto-trigger reflect sau khi PR created:**
```
/morai:reflect $TICKET_ID
```
Không cần dev gọi tay — chạy ngay sau khi PR tạo xong để capture knowledge khi còn fresh.

> **💡 Context:** Bước Dev xong → `/compact` trước khi chạy `/morai:pr`.
