# Morai Skills Index

Quick reference cho tất cả `/morai:*` commands.

---

## PIPELINE — Software Development Flow

```
scan → ba → [architect] → pm → dev → pr → reviewer → security → qa
```

| Command | Trigger tự nhiên | Mô tả |
|---------|-----------------|-------|
| `/morai:scan` | "scan project", "đọc codebase", "hiểu project" | Index codebase → sinh CLAUDE.md + knowledge docs |
| `/morai:ba` | "phân tích ticket", "analyze PROJ-123" | Jira/Confluence → spec.md |
| `/morai:architect` | "design solution", "cần ADR", "architecture" | spec → Architecture Decision Record |
| `/morai:pm` | "plan sprint", "chia task", "làm plan" | spec → sprint plan + tasks.md |
| `/morai:dev` | "làm ticket", "implement", "feature", "build" | Guided — pair programming, Dev giữ quyền commit |
| `/morai:dev-auto` | "fix bug X" (simple, pass 7 tiêu chí) | Auto — fix → test → commit → PR không cần review từng bước |
| `/morai:pr` | "tạo PR", "push và tạo PR", "xong rồi tạo PR" | Push branch → fill template → tạo PR → notify Slack |
| `/morai:reviewer` | "review PR", "check code" | PR → review comments (từ phía dev, local branch) |
| `/morai:pr-review` | "list PR", "review PR #42", "có PR nào cần review" | TL/PM — list open PRs → pick → review → post comment (GitHub + Bitbucket) |
| `/morai:security` | "security check", "bảo mật" | PR → OWASP + STRIDE audit |
| `/morai:qa` | "test", "QA", "viết test case" | spec → test plan + test report |

> `[architect]` optional — chỉ cần cho feature phức tạp cần design trước.

---

## LEARNING — Self-Improvement Loop

```
reflect (sau task) → evolve (sau sprint) → kaizen (weekly)
```

| Command | Khi nào | Mô tả |
|---------|---------|-------|
| `/morai:reflect` | Sau mỗi task/ticket hoàn thành | Ghi lesson learned → feed memory |
| `/morai:evolve` | Sau sprint hoặc khi đủ data | Promote patterns → reflexes, bump version |
| `/morai:kaizen` | Mỗi tuần | Chọn 1 pain point → measure → improve |

---

## SUPPORT — Problem Solving & Strategy

| Command | Khi nào | Mô tả |
|---------|---------|-------|
| `/morai:routine` | Đầu ngày / đầu session | Digest sáng: backlog + PRs + gates + CI → Telegram + chọn việc |
| `/morai:sparring` | Trước quyết định lớn | 4-layer challenge: clarify → alternatives → assumptions → stress test |
| `/morai:incident` | Bug production, lỗi nghiêm trọng | 5-Why root cause → L1-L4 severity → fix + prevent |

---

## SETUP — Cài đặt ban đầu

| Command | Khi nào | Mô tả |
|---------|---------|-------|
| `/morai:init` | Sau khi cài plugin lần đầu | Setup identity → hỏi scan hoặc onboard project ngay |
| `/morai:onboard` | Project mới có Confluence/Jira | Preflight check → pull docs + tickets → index RAG |
| `/morai:doctor` | Debug kết nối, trước khi onboard | Health check tất cả MCP servers, hướng dẫn fix |

---

## Auto-routing (không cần gõ command)

Orchestrator tự route khi user nói tự nhiên:

```
"làm xong PROJ-123"        → ba → architect? → pm → dev → pr → reviewer → security → qa
"review và test PR #45"    → reviewer → security → qa
"refactor toàn bộ auth"    → sparring trước → architect → dev
"có bug production"        → incident
"tuần này cải thiện gì"    → kaizen
"routine sáng" / "hôm nay có gì" → routine
```

---

## Cadence gợi ý

```
Mỗi task     → /morai:reflect (auto, không cần gõ)
Mỗi sprint   → /morai:evolve
Mỗi tuần     → /morai:kaizen
Khi có bug   → /morai:incident
Mỗi project  → /morai:scan (1 lần đầu)
```
