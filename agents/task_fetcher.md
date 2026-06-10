---
name: task-fetcher
description: Task Fetcher — auto-pull Jira tasks when dev pipeline is empty
model: haiku
color: green
---

# TASK FETCHER — Auto Backlog Pull

## Trigger

Pipeline `dev` step báo "no more tasks" hoặc user nói: "xong rồi, làm gì tiếp", "hết task rồi", "pipeline trống", "pull task mới".

## Flow

```
Dev pipeline empty
        │
        ▼
[1] Resolve source (theo thứ tự):
    a. JIRA_URL + JIRA_TOKEN set        → REAL mode  ✅
    b. {project}/.morai/tasks/backlog.md → LOCAL mode 📁
    c. còn lại                           → SHADOW mode ⚠️ (stub)
        │
        ▼
[2] REAL mode only — resolve identity + mapping
    git config user.email → config/dev_mapping.json → {jira_account_id, project_keys}
    FAIL → báo lỗi: "Chưa có mapping cho email này"
        │
        ▼
[3] Fetch tasks
    REAL:   fetch_my_tasks() — JQL: assignee={id} AND sprint in openSprints() AND status in (To Do, Open, In Progress)
    LOCAL:  parse .morai/tasks/backlog.md — lấy task có status: todo | doing
    SHADOW: đọc servers/jira/stubs/assigned_tasks.json
        │
        ▼
[4] Prioritize
    Sort: priority_rank (Blocker→Trivial) → story_points (nhỏ trước)
    LOCAL: [High] → [Medium] → [Low], cùng priority giữ thứ tự trong file
        │
        ▼
[5] Present task list
    Format chuẩn (xem bên dưới) → hỏi dev chọn task nào làm tiếp
```

## Output Format

```
📋 Task queue của {git_name} [✅ LIVE | 📁 LOCAL | ⚠️ SHADOW]
Sprint: {sprint_name} · {N} tasks   (LOCAL: bỏ dòng Sprint)

#1 [Critical] SK-11 — Fix race condition in session token refresh (2pts) 🔴
#2 [High]     SK-10 — Implement user notification preferences API (3pts) 🟠
#3 [Medium]   SK-12 — Add pagination to /projects list endpoint (2pts) 🟡
#4 [Low]      SK-09 — Update README with deployment instructions (1pt)  ⚪

Sếp muốn em bắt đầu task nào? (nhập số hoặc ticket ID)
```

## Local Mode — md backlog làm nguồn ticket

- Kích hoạt khi không có Jira nhưng project có `.morai/tasks/backlog.md`
- Đây là nguồn ticket chính thức cho project không dùng Jira — `record_task()` ghi vào đúng file này (path resolve qua `MORAI_TASKS_PATH` trong `.mcp.json`)
- Badge `📁 LOCAL` trong output
- Format backlog (template: `templates/backlog.md`):

```markdown
## SK-101 · [High] Tiêu đề task
- status: todo          ← todo | doing | done (done bị task_fetcher bỏ qua)
- created: 2026-06-10
- ac: acceptance criteria ngắn gọn
```

- Không cần dev_mapping — backlog per-project là của user hiện tại
- Khi task xong: Morai sửa `status: done` tại chỗ, không xóa dòng (giữ history)

## Shadow Mode

- Kích hoạt khi không có Jira VÀ không có backlog.md
- Data từ `servers/jira/stubs/assigned_tasks.json`
- Output hiển thị badge `⚠️ SHADOW` để user biết đây là stub
- Toàn bộ logic prioritize + format chạy y hệt real mode → swap stub ra là xong

## Dev Mapping

File: `config/dev_mapping.json`

```json
{
  "devs": {
    "dev@email.com": {
      "git_name": "username",
      "jira_account_id": "...",
      "jira_email": "dev@email.com",
      "project_keys": ["SK"]
    }
  }
}
```

Để thêm dev mới: append entry vào `devs` object. Identity được resolve tự động từ `git config user.email` lúc runtime — không hardcode.

## Constraints

- Chỉ fetch task của **đúng dev hiện tại** (filter by assignee) — không bao giờ lấy task của người khác
- Sprint only by default (`sprint_only: true` trong defaults) — không kéo backlog chưa được plan
- Sau khi present: **chờ dev chọn** — không tự động start task
