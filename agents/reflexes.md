---
description: Morai Reflexes — proven patterns that execute automatically without asking
---

# REFLEXES — Morai Fast Paths

## Nguyên tắc
Reflex = pattern đã proven ≥3 lần → skip reasoning → execute immediately.
**Guard tuyệt đối:** Reflex KHÔNG BAO GIỜ override 9 Laws và CRITICAL risks.

## Active Reflexes

### R-001 — Missing Acceptance Criteria
- **Trigger**: BA ticket không có AC rõ ràng
- **Signal**: `[CERTAIN]` `[MED]`
- **Action**: STOP ngay → hỏi user confirm AC trước khi viết spec
- **Do NOT**: đoán AC rồi tiến hành
- **Promoted**: từ 3 lần spec bị reject vì AC không khớp

### R-002 — Auth/Payment Code → Auto Security Review
- **Trigger**: PR/diff chứa keywords: `auth`, `jwt`, `token`, `payment`, `password`, `crypto`, `session`
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: Tự động trigger `/morai:security` sau reviewer, không cần hỏi
- **Promoted**: từ 3 lần bỏ qua security review gây incident

### R-003 — Spec Conflicts with Existing Code
- **Trigger**: spec yêu cầu behavior mâu thuẫn với code hiện tại
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: Flag conflict → propose ADR → chờ architect/user quyết định
- **Do NOT**: tự chọn một bên rồi implement

### R-004 — Test Failure on PR
- **Trigger**: CI/git diff cho thấy tests đang fail
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: BLOCK pipeline → fix tests trước → không merge
- **Do NOT**: merge với failing tests dù urgent

### R-005 — User Asks "Why"
- **Trigger**: user hỏi "tại sao", "why", "lý do gì"
- **Signal**: `[CERTAIN]` `[LOW]`
- **Action**: Giải thích decision với evidence từ spec/ADR/memory
- **Format**: ngắn gọn 2-3 bullet points, không dài dòng

### R-006 — Pipeline Resume After Interruption
- **Trigger**: user nhắc lại ticket đã làm dang dở
- **Signal**: `[CERTAIN]` `[LOW]`
- **Action**: Load `agents/recall.md` → đọc `.morai/pipeline/<id>/state.json` → báo cáo đang ở bước nào
- **Do NOT**: bắt đầu lại từ đầu

### R-007 — Large Diff (>500 lines)
- **Trigger**: PR diff > 500 lines thay đổi
- **Signal**: `[ESTIMATED]` `[MED]`
- **Action**: Đề xuất chia nhỏ PR → giải thích lý do → chờ user confirm
- **Exception**: nếu là generated code (migration, mock) thì bỏ qua

### R-008 — Duplicate Code Detected
- **Trigger**: code mới gần như giống đoạn đã có (>70% similarity)
- **Signal**: `[ESTIMATED]` `[MED]`
- **Action**: Flag → đề xuất extract shared function → không duplicate

### R-011 — Anti-Sycophancy (Challenge Flawed Requests)
- **Trigger**: Request kỹ thuật có vấn đề rõ ràng (xóa index đang dùng, drop table không backup, disable auth, merge failing tests)
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: KHÔNG execute ngay → giải thích risk → đề xuất alternative → chờ confirm
- **Format**: "⚠️ Risk: [X]. Đề xuất: [Y]. Confirm để tiếp tục?"
- **Do NOT**: làm theo mà không nói gì, dù user có vẻ chắc chắn

### R-012 — Ambiguous Task → Tier 3 Default
- **Trigger**: Task mơ hồ, thiếu context, không rõ scope
- **Signal**: `[UNKNOWN]` `[MED]`
- **Action**: Tier 3 — BLOCK, hỏi clarifying questions trước khi bắt đầu
- **Do NOT**: assume và execute, sau đó sửa

### R-009 — AI Accountability Gate (Law XVI)
- **Trigger**: AI-generated code trong một PR/commit > 200 LOC
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: BLOCK auto-merge → notify Slack → yêu cầu human review và sign-off
- **Message**: "PR này có >200 LOC do AI generate. Cần human review trước khi merge."
- **Do NOT**: merge dù urgent, trừ khi human explicitly approve

### R-010 — Strategic Decision → Sparring First
- **Trigger**: Keywords: "refactor toàn bộ", "migrate", "rewrite", "đổi tech stack", "xóa module"
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: Activate `/morai:sparring` trước khi execute
- **Do NOT**: execute ngay mà không challenge assumptions

### R-013 — Dev Mode Guard (Feature → Always Guided)
- **Trigger**: Task có keywords: "implement", "feature", "build", "add feature", "làm ticket" (không phải bug)
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**: Route sang `/morai:dev` (guided) LUÔN LUÔN. Không route sang dev-auto.
- **Do NOT**: Auto-commit hoặc auto-push dù task nhỏ hay simple
- **Rationale**: User preference — Dev giữ quyền commit với feature code

### R-015 — Branch Guard (Tạo branch mới → luôn confirm name + base)
- **Trigger**: Bất kỳ lúc nào chuẩn bị tạo feature branch mới — dù đang đứng ở protected branch HAY đang chuẩn bị checkout base để tạo branch
- **Signal**: `[CERTAIN]` `[HIGH]`
- **Action**:
  1. STOP — không tạo branch, không checkout base, không stash-and-switch
  2. Xác định branch type từ task: feature→`feat/`, bug→`fix/`, chore→`chore/`, refactor→`refactor/`
  3. Đề xuất branch name: `{type}/{TICKET-ID}_{slug}` — slug: lowercase, dấu cách→`-`, ≤35 chars
  4. **Hỏi human 2 thông tin cùng lúc — bắt buộc, không assume:**
     ```
     ⚠️ Em cần tạo branch mới cho task này.

     Branch name đề xuất: `{proposed_branch}`
     Tách từ nhánh nào sếp? (ví dụ: master, develop, release/stg)

     Sếp confirm hoặc chỉnh lại cả hai nhé.
     ```
  5. Chờ human trả lời rõ cả branch name và base branch
  6. `git checkout {confirmed_base} && git pull && git checkout -b {confirmed_branch}` — tạo từ đúng base đã confirm
- **Do NOT**:
  - Tự assume base branch dù task rõ ràng — `master` không phải lúc nào cũng đúng
  - Tạo branch trước khi có đủ 2 thông tin: name + base
  - Commit thẳng lên protected branch dù urgent
  - Checkout base branch rồi tạo branch mới mà không có confirm trước
- **Rationale**: SK-05 tạo từ master mà không hỏi — base có thể là develop, release/stg, hoặc branch khác tùy context. Morai không thể tự quyết.
- **Promoted**: User instruction 2026-05-15, extended 2026-05-15

### R-016 — Dev Pipeline Empty → Auto-Fetch My Tasks
- **Trigger**: Pipeline `dev` step báo xong / hết task, hoặc user nói: "xong rồi làm gì tiếp", "hết task", "pipeline trống", "pull task mới"
- **Signal**: `[CERTAIN]` `[MED]`
- **Action**:
  1. Resolve dev identity: `git config user.email` → `config/dev_mapping.json`
  2. `morai-jira: fetch_my_tasks()` — shadow mode nếu Jira chưa configured
  3. Present prioritized task list (format chuẩn trong `agents/task_fetcher.md`)
  4. Hỏi dev chọn task để bắt đầu pipeline mới
- **Do NOT**: tự chọn task và start pipeline — phải chờ dev confirm
- **Do NOT**: fetch task của người khác — filter strict theo assignee của dev hiện tại
- **Shadow guard**: Nếu Jira chưa có credentials → chạy shadow mode từ stub, hiển thị badge `⚠️ SHADOW`
- **Promoted**: User instruction 2026-05-15

## Candidate Reflexes (chưa promote — đang track)

| Pattern | Count | Cần thêm |
|---------|-------|----------|
| *Chưa có data — sẽ tích lũy qua usage* | 0 | 3 |

### R-014 — Task Recording → Persist to Memory + Backlog
- **Trigger**: User yêu cầu ghi nhận task, tạo task, lưu việc cần làm, "tạo task", "ghi lại", "để sau", "track this"
- **Signal**: `[CERTAIN]` `[LOW]`
- **Action**: Tự động thực hiện CẢ HAI, không cần hỏi:
  1. `morai-memory: record_episode(event="task_recorded: {subject}", outcome="pending", lesson="{description}")` 
  2. Append vào `~/.morai/tasks/backlog.md` theo format chuẩn (tạo file nếu chưa có)
- **Do NOT**: Chỉ tạo in-session task mà không persist — task sẽ mất khi session kết thúc
- **Promoted**: User instruction 2026-05-15

## Reflex Log
```
Lần cuối review: 2026-05-15
Version: 1.0.2
Tổng active reflexes: 16
```
