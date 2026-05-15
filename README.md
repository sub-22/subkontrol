# subkontrol — Morai

**Morai** là AI Operator cho team phát triển phần mềm, chạy trên Claude Code.  
Không phải chatbot. Không phải tool. Thành viên thực sự của team.

Plugin name: `morai` → tất cả commands có dạng `/morai:<skill>`

---

## Cài đặt

### Yêu cầu

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Claude Code CLI
- `gh` CLI (để tạo PR — `brew install gh` hoặc từ [cli.github.com](https://cli.github.com))

### Setup

```bash
git clone https://github.com/your-org/subkontrol
cd subkontrol

cp .env.example .env
# Chỉnh sửa .env — WORKSPACE_ROOT là bắt buộc

uv sync

# Verify
uv run pytest tests/ -q   # 144 tests, phải pass hết
```

### Cài vào Claude Code

```bash
claude plugin install .
```

Sau khi install, Claude Code hỏi 5 fields:

| Field | Bắt buộc | Ví dụ |
|-------|----------|-------|
| Workspace root | **Có** | `/absolute/path/to/your/project` |
| Jira URL | Không | `https://yourorg.atlassian.net` |
| Confluence URL | Không | `https://yourorg.atlassian.net/wiki` |
| Slack channel | Không | `#dev-pipeline` |
| Memory path | Không | `.morai/memory` (default) |

> Jira, Confluence, Slack là optional — Morai vẫn hoạt động đầy đủ mà không cần.

---

## Bắt đầu với project mới

```bash
/morai:scan /absolute/path/to/your/project
```

Tạo ra:
- `CLAUDE.md` tại project root — context cho tất cả agents
- `.morai/knowledge/` — architecture, tech-stack, conventions, api, database docs
- RAG index — toàn bộ codebase được index để search

Chạy 1 lần duy nhất khi bắt đầu. Từ đó các skills khác có đủ context.

---

## Commands

### Pipeline — Software Development Flow

```
scan → ba → [architect] → pm → dev / dev-auto → reviewer → security → qa
```

| Command | Trigger tự nhiên | Input | Output | Ai dùng |
|---------|-----------------|-------|--------|---------|
| `/morai:scan` | "scan project", "đọc codebase" | Path to project | `CLAUDE.md` + `.morai/knowledge/` | Tech Lead / Dev |
| `/morai:ba` | "phân tích PROJ-123", "analyze ticket" | Ticket ID hoặc mô tả | `specs/<id>.md` | BA / PM |
| `/morai:architect` | "design solution", "cần ADR" | Spec path hoặc ticket ID | `docs/adr/<id>.md` + `designs/<id>-detail.md` | Tech Lead |
| `/morai:pm` | "plan sprint", "chia task" | Spec path hoặc ticket ID | `plans/<id>-tasks.md` + `tasks/<id>/*.json` + wave plan | PM |
| `/morai:dev` | "làm ticket", "implement", "build feature" | Task ID | Code + GATE reviews + PR (khi Dev approve) | **Dev** |
| `/morai:dev-auto` | "fix bug X" *(simple bugs only)* | Task ID | Code + commit + PR tự động | Morai (auto) |
| `/morai:reviewer` | "review PR", "check code" | PR URL / branch / ticket ID | `reviews/<id>-review.md` + PR comment | Reviewer |
| `/morai:security` | "security check", "bảo mật PR" | PR URL / branch / ticket ID | `reviews/<id>-security.md` | Security |
| `/morai:qa` | "viết test case", "QA ticket" | Spec path hoặc ticket ID | `tests/<id>-test-plan.md` | QA |

> **`/morai:architect`** — optional, chỉ cần khi feature thay đổi DB schema, API mới, hoặc multi-service.

#### `/morai:dev` vs `/morai:dev-auto`

| | `dev` (guided) | `dev-auto` |
|-|----------------|-----------|
| Dùng cho | Feature, refactor, mọi implement | Bug đơn giản |
| Commit | Dev quyết định — Morai hỏi trước | Tự động |
| PR | Dev quyết định — Morai hỏi trước | Tự động |
| GATE 1 (approach) | Có — Morai trình bày plan, chờ approve | Không |
| Khi nào auto fail-safe | Không apply | Fail 1 trong 7 tiêu chí → fallback sang guided |

**7 tiêu chí để `dev-auto` được chạy** (tất cả phải pass):
1. Task type là bug (không phải feature)
2. Scope ≤ 2 files
3. Ước tính < 30 LOC thay đổi
4. Root cause rõ ràng
5. Có existing tests để verify
6. Không động vào auth / payment / user data
7. Không phải L1/L2 incident

---

### Learning — Self-Improvement Loop

```
reflect (sau mỗi task) → evolve (sau sprint) → kaizen (hàng tuần)
```

| Command | Khi nào chạy | Làm gì | Output |
|---------|-------------|--------|--------|
| `/morai:reflect` | Sau mỗi task/ticket xong | 5-question retrospective → ghi lessons | Episodes trong memory |
| `/morai:evolve` | Sau sprint hoặc khi đủ data | Promote patterns → reflexes, cập nhật preferences | Updated `agents/reflexes.md` |
| `/morai:kaizen` | Mỗi tuần | Chọn 1 pain point → measure → implement cải thiện nhỏ | Kaizen log trong memory |

> `/morai:reflect` chạy tự động (ngầm) sau mỗi 10 tasks — không cần gọi tay.

---

### Support — Problem Solving & Strategy

| Command | Khi nào chạy | Làm gì |
|---------|-------------|--------|
| `/morai:sparring` | Trước quyết định lớn (refactor, migrate, đổi stack) | 4-layer challenge: clarify → alternatives → assumptions → stress test |
| `/morai:incident` | Bug production, lỗi nghiêm trọng | 5-Why root cause → L1–L4 severity → immediate fix + prevention |

---

### Auto-routing — Không cần nhớ commands

Morai hiểu ngôn ngữ tự nhiên và tự route:

```
"làm xong PROJ-123"         → ba → [architect] → pm → dev → reviewer → security → qa
"fix bug login crash"        → dev-auto check (7 tiêu chí) → dev hoặc dev-auto
"review PR #45"              → reviewer → security
"refactor toàn bộ auth"      → sparring → architect → dev
"production down"            → incident
"tuần này cải thiện gì"      → kaizen
```

---

## MCP Servers

Morai giao tiếp với các tools bên ngoài qua MCP servers.

### Implemented

| Server | Tools | Dùng bởi |
|--------|-------|---------|
| `morai-pipeline` | `create_pipeline`, `transition` (FSM 18 states), `create_gate`, `resolve_gate`, `list_all_pending_gates`, `record_token_usage`, `init_waves`, `start_wave`, `update_task_in_wave`, `commit_wave` | Tất cả skills |
| `morai-memory` | `record_episode`, `get_episodes`, `get_preferences`, `update_preference`, `promote_to_reflex`, `archive_old_episodes` | reflect, evolve, kaizen, tất cả skills |
| `morai-rag` | `scan_project`, `index_documents`, `search`, `get_context` | scan, ba, architect, dev, reviewer, security, qa, sparring |
| `morai-file` | `read_file`, `write_file` (artifacts), `write_source_file` (source — dev only), `append_file`, `delete_file`, `list_files` | Tất cả skills |
| `morai-git` | `status`, `diff`, `commit`, `push`, `create_branch`, `create_pr`, `get_pr_diff`, `add_pr_comment`, `get_current_branch` | dev, reviewer, security, qa, incident |
| `morai-events` | `subscribe`, `publish`, `get_subscriptions`, `get_event_log`, `get_cron_setup_guide` | Orchestrator, scheduled triggers |

### Stubs (chưa implement — graceful fallback)

| Server | Dùng bởi | Khi chưa configure |
|--------|---------|-------------------|
| `morai-jira` | ba, pm | Skip fetch, dùng input từ user |
| `morai-confluence` | ba | Skip fetch, dùng input từ user |
| `morai-slack` | Tất cả skills (optional) | Skip notify, báo cáo trực tiếp trong chat |

---

## Roles

### Ai làm gì trong pipeline

| Role | Responsibility | Commands thường dùng |
|------|---------------|---------------------|
| **CTO / Tech Lead** | Approve architecture decisions, sparring trước quyết định lớn | `/morai:sparring`, `/morai:architect` |
| **BA / PM** | Phân tích requirements, chia tasks, plan sprint | `/morai:ba`, `/morai:pm` |
| **Dev** | **Review approach (GATE 1)**, implement với Morai dẫn dắt, **quyết định khi nào commit/push** | `/morai:dev` |
| **Reviewer** | Review code quality, logic, conventions | `/morai:reviewer` |
| **Security** | Audit bảo mật trước khi merge (bắt buộc với auth/payment/data) | `/morai:security` |
| **QA** | Viết và review test plan, verify business logic | `/morai:qa` |

### Morai làm gì

Morai **không phải người dùng** — Morai là agent điều phối:

- Phân tích requirements từ Jira/Confluence (hoặc input trực tiếp)
- Nghiên cứu codebase qua RAG trước khi đề xuất approach
- Trình bày approach plan → **chờ Dev approve** (GATE 1)
- Implement từng chunk, show diff sau mỗi chunk → **chờ Dev confirm**
- Commit / push / tạo PR **chỉ khi Dev nói rõ**
- Track pipeline state, ghi lesson learned, tự cải thiện qua reflex system

### GATE system — Human luôn là gate cuối

| GATE | Trigger | Dev cần làm |
|------|---------|-------------|
| GATE 1 — Approach | Trước khi Morai bắt đầu implement | Review approach, approve / request changes |
| GATE 2 — Commit | Code đã xong, tests pass | Nói "commit" để Morai commit |
| GATE 3 — PR | Sau commit | Nói "tạo PR" để Morai push và tạo PR |
| Security BLOCK | Khi security review = BLOCK | Fix issues trước khi QA được chạy |

Gates persist across sessions — nếu session bị ngắt, Morai recall pending gates khi session mới bắt đầu.

---

## Pipeline state & Parallel execution

### Pipeline states

```
IDLE → BA_RUNNING → BA_DONE
     → [ARCHITECT_RUNNING → ARCHITECT_DONE]
     → PM_RUNNING → PM_DONE
     → DEV_RUNNING → DEV_REVIEWING → DEV_COMMITTED       (sequential)
     → DEV_PARALLEL_RUNNING → DEV_ALL_COMMITTED           (parallel waves)
     → REVIEW_RUNNING → REVIEW_DONE
     → [SECURITY_RUNNING → SECURITY_DONE]
     → QA_RUNNING → QA_DONE → COMPLETE
     → BLOCKED (bất kỳ bước nào)
```

### Parallel execution (wave-based)

Khi PM tạo task breakdown với nhiều tasks độc lập, PM tự động sinh **wave plan**:

```
Wave 1: [TASK-1, TASK-3, TASK-5]  ← chạy song song (3 sub-agents)
Wave 2: [TASK-2]                   ← sau Wave 1
Wave 3: [TASK-4]                   ← sau Wave 2
```

- Mỗi sub-agent chạy trong isolated git worktree
- GATE 1 được aggregate: 1 review cho toàn bộ wave thay vì N reviews riêng lẻ
- Orchestrator merge sau khi tất cả tasks committed → 1 PR duy nhất

---

## Cấu trúc project

```
subkontrol/
├── .claude-plugin/plugin.json      # Plugin manifest
├── agents/                         # Brain files — loaded by Morai
│   ├── morai.md                    # Identity, 9 laws, TIER A/B loading (PROTECTED)
│   ├── orchestrator.md             # Intent routing, model routing, parallel dispatch
│   ├── judge.md                    # Pipeline self-correction, quality gates
│   ├── spawner.md                  # Parallel agent orchestration protocol
│   ├── merge.md                    # Worktree merge protocol
│   ├── hitl.md                     # Human-in-the-loop gate protocol
│   ├── cost.md                     # Model routing table, budget management
│   ├── events.md                   # Event types, subscriptions, cron setup
│   ├── memory.md                   # Memory architecture
│   ├── reflexes.md                 # 13 active fast-path reflexes
│   ├── recall.md                   # Session recovery protocol
│   ├── context_gateway.md          # Active pipelines, system state
│   └── knowledge_gateway.md        # Domain knowledge, proven patterns
├── rules/                          # Operational rules
│   ├── governance.md               # Autonomy tiers, evidence-based decisions
│   ├── code.md                     # Coding conventions, modularization
│   ├── quality.md                  # 6-gate quality framework
│   ├── autonomy.md                 # ReAct loop, no-skip policy
│   ├── observability.md            # Logging, correlation ID, debugging
│   └── rules_gateway.md            # Which rules to load per task type
├── skills/                         # Skill definitions — 1 file per command
│   ├── scan/SKILL.md
│   ├── ba/SKILL.md
│   ├── architect/SKILL.md
│   ├── pm/SKILL.md
│   ├── dev/SKILL.md                # Guided mode (pair programming)
│   ├── dev-auto/SKILL.md           # Auto mode (simple bugs only)
│   ├── reviewer/SKILL.md
│   ├── security/SKILL.md
│   ├── qa/SKILL.md
│   ├── reflect/SKILL.md
│   ├── evolve/SKILL.md
│   ├── kaizen/SKILL.md
│   ├── sparring/SKILL.md
│   ├── incident/SKILL.md
│   └── _index.md                   # Quick reference tất cả commands
├── servers/                        # MCP servers
│   ├── pipeline/server.py          # FSM + gates + cost tracking ✓
│   ├── memory/server.py            # Episodes, preferences, reflexes ✓
│   ├── rag/server.py               # Vector search (ChromaDB) ✓
│   ├── file/server.py              # File R/W with zone enforcement ✓
│   ├── git/server.py               # Git + GitHub CLI ops ✓
│   ├── events/server.py            # Event bus + subscriptions ✓
│   ├── jira/server.py              # stub
│   ├── confluence/server.py        # stub
│   └── morai/server.py             # Slack stub
├── templates/                      # Output templates
│   ├── ba_spec.md                  # BA spec template
│   ├── detail_design.md            # Architecture detail design
│   ├── pm_tasks.md                 # Sprint plan (human-readable)
│   ├── task.json                   # Task machine-readable format
│   ├── tasks_index.json            # Tasks index per ticket
│   ├── wave_plan.json              # Parallel wave plan template
│   └── pr/                         # PR description templates
│       ├── feature.md
│       ├── bugfix.md
│       └── refactor.md
├── tests/                          # 144 tests
│   ├── test_pipeline_server.py     # FSM transitions + preconditions
│   ├── test_pipeline_waves.py      # Wave management
│   ├── test_hitl_gates.py          # Gate lifecycle
│   ├── test_cost_tracker.py        # Token tracking + budget alerts
│   ├── test_events_server.py       # Event bus + subscriptions
│   ├── test_file_server.py         # Zone enforcement
│   ├── test_git_server.py          # Git operations
│   └── test_memory_server.py       # Memory operations
├── permissions.yaml                # Skill permission matrix
├── CHANGELOG.md
├── .mcp.json                       # MCP server registrations
├── .env.example
└── pyproject.toml
```

---

## Environment variables

| Variable | Bắt buộc | Mô tả |
|----------|----------|-------|
| `WORKSPACE_ROOT` | **Có** | Absolute path tới project đang làm việc |
| `ANTHROPIC_API_KEY` | **Có** | Anthropic API key |
| `MORAI_MEMORY_PATH` | Không | Path lưu memory (default: `.morai/memory`) |
| `CHROMA_PATH` | Không | Path lưu vector store (default: `.morai/rag`) |
| `MORAI_BUDGET_TOKENS` | Không | Token budget per pipeline (default: `200000`) |
| `JIRA_URL` | Không | Jira instance URL |
| `JIRA_EMAIL` | Không | Jira account email |
| `JIRA_TOKEN` | Không | Jira API token |
| `CONFLUENCE_URL` | Không | Confluence URL |
| `CONFLUENCE_EMAIL` | Không | Confluence account email |
| `CONFLUENCE_TOKEN` | Không | Confluence API token |
| `SLACK_BOT_TOKEN` | Không | Slack bot token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Không | Slack app token (`xapp-...`) |
