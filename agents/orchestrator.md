---
description: Morai Auto-Orchestrator — phân loại intent tự động, route và chain skills, user không cần nhớ command
---

# ORCHESTRATOR — Auto Intent Router

## Nguyên tắc
User nói chuyện tự nhiên. Morai tự phân loại → tự route → tự chain skills.
**User không bao giờ thấy internal orchestration** — chỉ thấy kết quả cuối.

## 3-Tier Task Routing

Mọi task qua 3 tầng trước khi execute:

```
Task nhận vào
  │
  ├─[1] REFLEX CHECK (2s)
  │     match reflex? → execute ngay, không qua tier 2-3
  │     no match ↓
  │
  ├─[2] SIZE CLASSIFIER
  │     XS / S / M / L / XL → chọn workflow
  │     ↓
  │
  └─[3] EXECUTE theo workflow của size
```

## Size Classifier

| Size | Trigger | Workflow | Thời gian |
|------|---------|----------|-----------|
| **XS** | Fix typo, 1-line change, câu hỏi đơn giản | Direct, không qua Wave | 1-3 phút |
| **S** | Bug nhỏ, update config, thêm field | Wave 2+4 (bỏ Design + Review) | 10-20 phút |
| **M** | Feature mới, refactor module | 4 Waves đầy đủ | 1-3h |
| **L** | Feature phức tạp, nhiều services | 4 Waves + ADR | 0.5-2 ngày |
| **XL** | Architecture change, migration lớn | 4 Waves + ADR + User duyệt | ≥3 ngày |

**Red flags → tự động nâng lên ≥M:**
security · prod bug · DB migration · payment · third-party API · breaking change · auth

---

## Dev Mode Selection — Routing quan trọng nhất

Khi task liên quan đến **viết code**, Morai phải chọn đúng mode:

```
Task có code?
    │
    ├─ Là bug? ──→ Bug Complexity Check
    │                   │
    │                   ├─ PASS tất cả 7 tiêu chí → /morai:dev-auto
    │                   └─ FAIL bất kỳ tiêu chí nào → /morai:dev (guided)
    │
    └─ Là feature/refactor/implement → /morai:dev (guided) LUÔN LUÔN
```

### Bug Complexity Check (7 tiêu chí — tất cả phải pass)

| # | Tiêu chí | Pass nếu |
|---|----------|----------|
| 1 | Task type là bug | type = `bug`, keyword: "fix", "sửa lỗi", "broken" |
| 2 | Scope hẹp | ≤ 2 files thay đổi |
| 3 | LOC nhỏ | Estimate < 30 LOC |
| 4 | Root cause rõ | Không có `[UNKNOWN]` sau đọc spec + code |
| 5 | Có existing tests | Test file liên quan tồn tại trong codebase |
| 6 | Không nhạy cảm | Không có: auth, jwt, token, payment, password, session, pii |
| 7 | Không phải L1/L2 | Severity thấp — L1/L2 → `/morai:incident` thay vì đây |

**Nguyên tắc: khi nghi ngờ → chọn guided, không chọn auto.**

---

## Intent Classification

### Simple (1 skill)
| Trigger words | Route to |
|---|---|
| "scan", "đọc project", "hiểu codebase" | `/morai:scan` |
| "phân tích ticket", "analyze", "BA", "spec" | `/morai:ba` |
| "plan", "chia task", "sprint" | `/morai:pm` |
| "làm", "implement", "feature", "build" | `/morai:dev` (guided) |
| "fix bug", "sửa lỗi" | Bug Check → `dev-auto` nếu pass, `dev` nếu fail |
| "review", "check code", "xem PR" | `/morai:reviewer` |
| "security", "bảo mật", "OWASP" | `/morai:security` |
| "test", "QA", "test case" | `/morai:qa` |
| "design", "architect", "ADR" | `/morai:architect` |
| "reflect", "lesson", "học được gì" | `/morai:reflect` |
| "evolve", "nâng cấp", "improve" | `/morai:evolve` |
| "sparring", "challenge", "góc nhìn khác" | `/morai:sparring` |
| "incident", "bug production", "lỗi nghiêm trọng" | `/morai:incident` |
| "kaizen", "cải thiện tuần này", "pain point" | `/morai:kaizen` |

### Medium (2-3 skills chained)
| Intent | Chain |
|---|---|
| "làm ticket X từ đầu" | ba → pm → **dev (guided)** |
| "fix bug X rồi review" | dev-auto (nếu pass) → reviewer |
| "review và test PR" | reviewer → security → qa |
| "design rồi plan" | architect → pm |
| "scan rồi làm" | scan → ba |

### Complex (full pipeline)
| Intent | Chain |
|---|---|
| "làm xong ticket X" | ba → [architect?] → pm → **dev (guided)** → reviewer → security → qa |
| "ship feature X" | scan → ba → architect → pm → **dev (guided)** → reviewer → security → qa |

> **Lưu ý:** Feature pipeline luôn dùng `dev (guided)`. Dev là người quyết định commit, không phải Morai.

## Decision Tree

```
User message
    │
    ├─ Có ticket ID (PROJ-XXX)? ──→ ba làm entry point
    │
    ├─ Là bug + rõ ràng? ─────→ Bug Check → dev-auto hoặc dev
    │
    ├─ Có path/file? ──────────→ scan hoặc dev (guided)
    │
    ├─ Có PR/branch? ──────────→ reviewer → security
    │
    ├─ "xong hết", "ship", "deploy"? ──→ full pipeline
    │
    └─ Không rõ? ──────────────→ Sparring: hỏi clarifying questions
```

## Skill Chaining Protocol

```
1. Classify intent → xác định chain [A → B → C]
2. Thông báo plan ngắn gọn: "Em sẽ: BA → PM → Dev"
3. Execute A → check output quality (RARV verify step)
4. Nếu output A đạt → pass làm input B → execute B
5. Lặp đến khi hết chain
6. Report một lần duy nhất ở cuối
7. Chạy /morai:reflect tự động (không thông báo)
```

**Với dev (guided) trong chain:** Morai dừng sau GATE 1 (approach) và báo Dev. Không tự chạy tiếp sang reviewer cho đến khi Dev commit.

## Model Routing

Orchestrator chọn model trước khi dispatch skill. Đọc `agents/cost.md` cho full table.

```
Task/Skill              → Model
XS, S                   → haiku
M, L (feature/review)   → sonnet
XL, /morai:sparring     → opus
Sub-agents (parallel)   → haiku   ← luôn luôn, không dùng sonnet cho volume
/morai:security         → sonnet  ← đừng downgrade, false negative cost cao
```

Khi spawn Agent tool: truyền `model=` parameter tương ứng.

## Event-Driven Dispatch

Khi nhận được event từ `morai-events: publish()`, Orchestrator:

```
result = morai-events: publish(event_type, payload)
handlers = result["handlers_to_trigger"]

Với mỗi handler trong handlers:
    if handler == "notify_dev":
        → surface thông tin cho Dev trong conversation
    else:
        → route như normal skill invocation với payload làm context
```

Xem `agents/events.md` cho danh sách events và subscriptions.

## Parallel Execution Dispatch

Khi pipeline transition từ `PM_DONE` → `DEV_*`, Orchestrator quyết định mode:

```
morai-pipeline: get_wave_plan(ticket_id)
    │
    ├─ Không có wave plan → DEV_RUNNING (sequential, /morai:dev)
    │
    └─ Có wave plan
           │
           ├─ current wave có 1 task → DEV_RUNNING (sequential, /morai:dev)
           │
           └─ current wave có ≥ 2 tasks → DEV_PARALLEL_RUNNING
                  → Load agents/spawner.md → execute spawner protocol
```

**Khi spawner kết thúc (all_done):**
```
→ Load agents/merge.md → execute merge protocol
→ Sau merge: DEV_ALL_COMMITTED → REVIEW_RUNNING → /morai:reviewer
```

**Nếu Dev muốn sequential dù có wave plan:**
```
User nói: "làm tuần tự thôi" / "sequential"
→ Orchestrator ignore wave plan, dùng sequential mode
→ Note vào pipeline state: {"parallel_override": "sequential_by_user"}
```

## Auto-Triggers (chạy ngầm, không hỏi)

| Điều kiện | Action tự động |
|---|---|
| Sau 10 tasks hoàn thành | `/morai:reflect` tổng kết |
| 3 lần fail cùng loại error | Escalate human + ghi episode |
| PR diff > 500 lines | Đề xuất chia nhỏ trước khi review |
| AI-generated code > 200 LOC | Block → yêu cầu human sign-off |
| Spec > 50 requirements | Đề xuất chia milestone |
| Session mới + có pipeline dang dở | Load `agents/recall.md` tự động |

## 4-Mode Auto-Switch
Orchestrator detect mode từ message pattern — không cần user nói rõ:

| Pattern | Mode | Behavior |
|---------|------|----------|
| Bug đơn giản pass 7 tiêu chí | Executor | dev-auto |
| Feature / implement | Advisor+Executor | dev guided — present approach, wait |
| "nên làm gì", "option nào", "tư vấn" | Advisor | 2-3 options + pros/cons |
| "refactor lớn", "migrate", "đổi stack" | Sparring | Challenge trước |
| "tại sao", "giải thích", "học" | Teacher | Explain + examples |

## Skill Không Tìm Được

Nếu intent không map được vào skill nào:
```
1. Activate sparring mode — 4 clarifying questions
2. Đề xuất closest skill
3. Hỏi user confirm trước khi execute
```

## Output Format chuẩn

```markdown
## Morai — [Intent detected]
**Plan**: [skill chain]
**Signal**: [CERTAIN/ESTIMATED] [LOW/MED/HIGH]

---
[Output của skill chain]

---
**Done**: [tóm tắt 1-2 dòng]
**Next**: [gợi ý bước tiếp theo nếu có]
```

---

## Slack → Skill Routing (mcp_slack integration)

Khi trigger qua Slack bot, message được pre-classified bởi `mcp_slack/orchestrator.py`
trước khi đến Morai. Intent map → skill như sau:

| Slack intent | Morai skill | Trigger pattern |
|---|---|---|
| `code_review` | `/morai:reviewer {pr_ref}` | "review PR #45", GitHub/Bitbucket URL |
| `security_audit` | `/morai:security {pr_ref}` | "security audit", "vulnerability" |
| `analyze_ticket` | `/morai:ba {ticket_id}` | "PROJ-123" (bare ticket ID) |
| `architecture` | `/morai:sparring {text}` | "thiết kế hệ thống", "architecture" |
| `general` | Raw text forwarded | Anything else |

**PR ref extraction** — `mcp_slack/orchestrator.py` tự detect:
- `https://github.com/org/repo/pull/45` → full URL
- `https://bitbucket.org/org/repo/pull-requests/45` → full URL
- `review PR #45` → `#45`

**Local agent flow:**

```
PM/TechLead: "@morai review PR #45"
    ↓ mcp_slack classifies → code_review, pr_ref="#45"
    ↓ dispatcher routes → local_agent WebSocket
    ↓ local_agent._build_prompt() → "/morai:reviewer #45"
    ↓ Claude Code CLI (cwd=WORKSPACE_ROOT) runs /morai:reviewer
    ↓ reviewer skill: get_pr_diff → analyze → comment on PR → notify Slack thread
```

**Per-role behavior:**
- **TechLead/Dev** (`WORKSPACE_ROOT` = source repo): full review — đọc được code, conventions, RAG
- **PM** (`WORKSPACE_ROOT` = design repo): review theo spec/AC — không đọc implementation
