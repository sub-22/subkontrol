# subkontrol — Morai

**Morai** là AI Operator cho team phát triển phần mềm, chạy trên Claude Code.  
Không phải chatbot. Không phải tool. Thành viên thực sự của team.

Plugin name: `morai` → tất cả commands có dạng `/morai:<skill>`

[![CI](https://github.com/sub-22/subkontrol/actions/workflows/ci.yml/badge.svg)](https://github.com/sub-22/subkontrol/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.9.0-green.svg)](.claude-plugin/plugin.json)

---

## Cài đặt

### Yêu cầu

- [Claude Code CLI](https://claude.ai/code)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `gh` CLI — để tạo PR (`brew install gh` hoặc [cli.github.com](https://cli.github.com))

---

### Cách 1 — Qua marketplace (khuyên dùng)

**Bước 1** — Thêm subkontrol vào `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "sub22": {
      "source": {
        "source": "github",
        "repo": "sub-22/subkontrol"
      }
    }
  }
}
```

**Bước 2** — Install plugin:

```bash
claude plugin install morai@sub22
```

Claude Code sẽ tự clone repo, cài dependencies và hỏi config.

---

### Cách 2 — Install trực tiếp từ GitHub

```bash
claude plugin install github:sub-22/subkontrol
```

---

### Cách 3 — Clone local (cho contributor)

```bash
git clone https://github.com/sub-22/subkontrol
cd subkontrol
uv sync
claude plugin install .
```

---

### Config sau khi install

Claude Code chỉ hỏi 2 fields khi install:

| Field | Bắt buộc | Ví dụ |
|-------|----------|-------|
| `MORAI_GLOBAL_PATH` | **Có** | `/home/user/.morai` |
| `GITHUB_TOKEN` | Không | GitHub PAT — nếu dùng GitHub |
| `BITBUCKET_USERNAME` | Không | Username Bitbucket |
| `BITBUCKET_TOKEN` | Không | App password (Cloud) hoặc PAT (Server) |
| `BITBUCKET_BASE_URL` | Không | `https://git.mycompany.com` — chỉ cần cho Bitbucket Server |

**Jira / Confluence / Slack** — cấu hình sau khi install qua guided flow:

```
/morai:init
```

Morai hỏi từng integration (dùng thì điền, không dùng thì bỏ qua) và lưu vào `~/.morai/config.json`. Chạy lại bất cứ lúc nào để thêm integration mới.

> **Jira identity:** Morai tự resolve từ `git config user.email` + `currentUser()` — không cần mapping file.

### Verify

Mở Claude Code trong project của bạn và thử:

```
Morai đây anh — [tên project].
Anh cần em làm gì ạ?
```

Nếu thấy greeting trên → install thành công.

---

## Bắt đầu với project mới

### Dev

```bash
/morai:scan /absolute/path/to/your/project
```

Tạo ra:
- `CLAUDE.md` tại project root
- `.morai/knowledge/` — architecture, tech-stack, conventions, api, database docs
- RAG index — toàn bộ codebase được index để search

### Non-dev (BA / PM / QA / QC)

```bash
# Tạo project-knowledge repo — pull Confluence + Jira nếu có, fallback scan source
uv run python scripts/onboard.py \
  --role non-dev \
  --project-name my-project \
  --source-repo https://github.com/org/my-project.git

# Clone repo vừa tạo về máy và chạy local agent
cd my-project-design
python /path/to/mcp_slack/local_agent.py --token <token> --workspace .
```

Sau đó mention bot trong Slack: `@morai PROJ-123` hoặc `@morai sprint report`

---

## Commands

### Pipeline — Software Development Flow

```
scan → ba → [architect] → pm → dev / dev-auto → pr → reviewer → security → qa
```

| Command | Trigger tự nhiên | Input | Output | Ai dùng |
|---------|-----------------|-------|--------|---------|
| `/morai:scan` | "scan project", "đọc codebase" | Path to project | `CLAUDE.md` + `.morai/knowledge/` | Tech Lead / Dev |
| `/morai:ba` | "phân tích PROJ-123", "analyze ticket" | Ticket ID hoặc mô tả | `specs/<id>.md` | BA / PM |
| `/morai:architect` | "design solution", "cần ADR" | Spec path hoặc ticket ID | `docs/adr/<id>.md` | Tech Lead |
| `/morai:pm` | "plan sprint", "chia task" | Spec path hoặc ticket ID | `plans/<id>-tasks.md` + wave plan | PM |
| `/morai:dev` | "làm ticket", "implement", "build feature" | Task ID | Code + GATE reviews | **Dev** |
| `/morai:dev-auto` | "fix bug X" *(simple bugs only)* | Task ID | Code + commit tự động | Morai (auto) |
| `/morai:pr` | "tạo PR", "xong rồi tạo PR" | Branch / ticket ID | CI check → push → PR → Slack notify | Dev |
| `/morai:reviewer` | "review PR", "check code" | PR URL / branch | `reviews/<id>-review.md` + PR comment | Reviewer |
| `/morai:pr-review` | "list PR", "review PR #42", "có PR nào cần review" | PR ID (optional) | List open PRs → review → post comment | Tech Lead / PM |
| `/morai:security` | "security check", "bảo mật PR" | PR URL / branch | `reviews/<id>-security.md` | Security |
| `/morai:qa` | "viết test case", "QA ticket" | Spec path hoặc ticket ID | `tests/<id>-test-plan.md` | QA |

> **`/morai:architect`** — optional, chỉ cần khi feature thay đổi DB schema, API mới, hoặc multi-service.

#### `/morai:dev` vs `/morai:dev-auto`

| | `dev` (guided) | `dev-auto` |
|-|----------------|-----------|
| Dùng cho | Feature, refactor, mọi implement | Bug đơn giản |
| Commit | Dev quyết định — Morai hỏi trước | Tự động |
| PR | Qua `/morai:pr` | Tự động |
| GATE 1 (approach) | Có — Morai trình bày plan, chờ approve | Không |
| Fail-safe | Không apply | Fail 1 trong 7 tiêu chí → fallback sang guided |

**7 tiêu chí để `dev-auto` được chạy** (tất cả phải pass):
1. Task type là bug (không phải feature)
2. Scope ≤ 2 files
3. Ước tính < 30 LOC thay đổi
4. Root cause rõ ràng
5. Có existing tests để verify
6. Không động vào auth / payment / user data
7. Không phải L1/L2 incident

#### `/morai:pr` — CI gate trước khi push

```
Thu thập context → Xác định PR type → Load template (project → subkontrol fallback)
  → Fill description từ diff + ticket + spec → CI check (lint → format → typecheck → test)
      ↓ fail → báo lỗi + hỏi confirm, KHÔNG tự push
      ↓ pass → push → create PR → notify Slack
```

PR template lookup order:
1. `.github/PULL_REQUEST_TEMPLATE.md` của project
2. `.github/PULL_REQUEST_TEMPLATE/*.md`
3. `docs/pull_request_template.md`
4. Fallback → `templates/pr/feature|bugfix|refactor.md` của subkontrol

---

### Learning — Self-Improvement Loop

```
reflect (sau mỗi task) → evolve (sau sprint) → kaizen (hàng tuần)
```

| Command | Khi nào chạy | Output |
|---------|-------------|--------|
| `/morai:reflect` | Sau mỗi task/ticket xong | Episodes trong memory |
| `/morai:evolve` | Sau sprint hoặc khi đủ data | Updated `agents/reflexes.md` |
| `/morai:kaizen` | Mỗi tuần | Kaizen log trong memory |

---

### Support — Problem Solving & Strategy

| Command | Khi nào chạy | Làm gì |
|---------|-------------|--------|
| `/morai:sparring` | Trước quyết định lớn | 4-layer challenge: clarify → alternatives → assumptions → stress test |
| `/morai:incident` | Bug production, lỗi nghiêm trọng | 5-Why root cause → L1–L4 severity → fix + prevention |

---

### Auto-routing — Không cần nhớ commands

```
"làm xong PROJ-123"         → ba → [architect] → pm → dev → pr → reviewer → security → qa
"fix bug login crash"        → dev-auto check (7 tiêu chí) → dev hoặc dev-auto
"tạo PR"                     → pr (CI check → push → create PR)
"review PR #45"              → reviewer → security
"có PR nào cần review"       → pr-review (list → pick → review → comment)
"refactor toàn bộ auth"      → sparring → architect → dev
"production down"            → incident
"tuần này cải thiện gì"      → kaizen
```

---

## MCP Servers

| Server | Tools | Dùng bởi |
|--------|-------|---------|
| `morai-pipeline` | FSM 18 states, gates, waves, cost tracking | Tất cả skills |
| `morai-memory` | episodes, preferences, reflexes, patterns | Tất cả skills |
| `morai-rag` | scan_project, index_documents, search, get_context | scan, ba, dev, reviewer, qa |
| `morai-file` | read/write (zone-enforced), project_summary | Tất cả skills |
| `morai-git` | status, diff, commit, push, create_pr, get_pr_template, list_open_prs, get_pr_detail, post_pr_comment | dev, pr, reviewer, pr-review |
| `morai-test` | run_pytest, run_coverage, detect_test_framework | pr, dev, qa |
| `morai-jira` | get_ticket, search_tickets, get_project_epics, get_active_sprint | ba, pm, onboard |
| `morai-confluence` | get_page, search, get_space_pages (label filter) | ba, onboard |
| `morai-slack` | send_message, get_thread, request_approval | pr, dev, incident |
| `morai-events` | subscribe, publish, event_log, cron_setup | Orchestrator |

---

## Onboarding non-dev (`morai-onboard`)

Script tạo `{project-name}-design` repo — knowledge base cho BA/PM/QA/QC.

```bash
# Dev — có Jira + Confluence
uv run python scripts/onboard.py --role dev --project PROJ --project-name myapp

# Dev — không có tools, dùng source code
uv run python scripts/onboard.py --role dev --project-name myapp \
  --source-repo https://github.com/org/myapp.git

# Non-dev — pull design repo hoặc fallback scan source
uv run python scripts/onboard.py --role non-dev --project-name myapp \
  --source-repo https://github.com/org/myapp.git

# Sync định kỳ
uv run python scripts/onboard.py --role dev --project PROJ --project-name myapp --update
```

Repo structure được tạo ra:

```
myapp-design/
├── CLAUDE.md              ← non-dev profile
├── .mcp.json              ← jira + confluence + rag + slack + memory only
├── basic_design/          ← pulled từ Confluence (label: basic-design)
├── detail_design/         ← pulled từ Confluence (label: detail-design)
├── specs/                 ← Confluence pages khác
├── decisions/             ← label: adr, decision, rfc
├── meetings/              ← label: meeting, minutes
├── knowledge/             ← generated bởi /morai:scan (nếu fallback source)
├── tickets/               ← knowledge tích lũy theo ticket (tự động sau)
└── onboarding/README.md   ← setup guide cho non-dev
```

---

## Roles

| Role | Responsibility | Commands thường dùng |
|------|---------------|---------------------|
| **CTO / Tech Lead** | Approve architecture, sparring | `/morai:sparring`, `/morai:architect` |
| **BA / PM** | Phân tích requirements, chia tasks | `/morai:ba`, `/morai:pm` |
| **Dev** | Implement, tạo PR | `/morai:dev`, `/morai:pr` |
| **Reviewer** | Review code quality | `/morai:reviewer` |
| **Security** | Audit bảo mật | `/morai:security` |
| **QA** | Test plan, verify business logic | `/morai:qa` |
| **BA/PM/QA (non-dev)** | Hỏi về project qua Slack | Slack bot → `local_agent` → Morai |

---

## GATE system

| GATE | Trigger | Người cần làm |
|------|---------|--------------|
| GATE 1 — Approach | Trước khi implement | Dev approve approach |
| GATE 2 — Commit | Code + tests xong | Dev nói "commit" |
| GATE 3 — PR | Sau commit | Dev chạy `/morai:pr` |
| CI GATE | Trong `/morai:pr` | Tự động — block nếu fail |
| Security BLOCK | Sau reviewer | Fix trước khi QA |

---

## Storage

```
~/.morai/               ← Global (tất cả projects)
├── memory/             ← Episodes, preferences, patterns
└── tasks/              ← Backlog.md

{WORKSPACE_ROOT}/.morai/  ← Per-project (gitignored)
├── rag/                ← Vector index (ChromaDB)
├── pipeline/           ← Ticket FSM state
└── knowledge/          ← Generated docs từ /morai:scan
```

---

## Environment variables

| Variable | Bắt buộc | Mô tả |
|----------|----------|-------|
| `WORKSPACE_ROOT` | **Có** | Absolute path tới project đang làm việc |
| `MORAI_GLOBAL_PATH` | **Có** | Path lưu global memory/tasks (e.g. `~/.morai`) |
| `ANTHROPIC_API_KEY` | **Có** | Anthropic API key |
| `MORAI_PIPELINE_PATH` | Không | Override pipeline storage (default: `$WORKSPACE_ROOT/.morai/pipeline`) |
| `MORAI_BUDGET_TOKENS` | Không | Token budget per pipeline (default: `200000`) |
| `JIRA_URL` | Không | Jira instance URL |
| `JIRA_EMAIL` | Không | Jira account email |
| `JIRA_TOKEN` | Không | Jira API token |
| `CONFLUENCE_URL` | Không | Confluence URL |
| `CONFLUENCE_EMAIL` | Không | Confluence account email |
| `CONFLUENCE_TOKEN` | Không | Confluence API token |
| `SLACK_BOT_TOKEN` | Không | Slack bot token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Không | Slack app token (`xapp-...`) |
| `SLACK_CHANNEL` | Không | Default channel nhận notifications (e.g. `#dev-pipeline`) |
| `GITHUB_TOKEN` | Không | GitHub Personal Access Token — cho PR review |
| `BITBUCKET_USERNAME` | Không | Bitbucket username |
| `BITBUCKET_TOKEN` | Không | Bitbucket App password (Cloud) hoặc PAT (Server) |
| `BITBUCKET_BASE_URL` | Không | Bitbucket Server URL (e.g. `https://git.mycompany.com`) |

---

## Cấu trúc project

```
subkontrol/
├── agents/                     # Brain files
│   ├── morai.md                # Identity, 9 laws (PROTECTED)
│   ├── orchestrator.md         # Intent routing
│   ├── judge.md                # Pipeline self-correction
│   ├── memory.md               # Memory architecture
│   ├── reflexes.md             # 14 active reflexes
│   ├── recall.md               # Session recovery
│   └── ...
├── rules/                      # Operational rules
├── skills/                     # 1 SKILL.md per command
│   ├── scan/ ba/ architect/ pm/
│   ├── dev/ dev-auto/
│   ├── pr/                     # CI check → push → PR → Slack
│   ├── reviewer/ security/ qa/
│   ├── reflect/ evolve/ kaizen/
│   ├── sparring/ incident/
│   └── _index.md
├── servers/                    # MCP servers
│   ├── pipeline/ memory/ rag/
│   ├── file/ git/ events/
│   ├── jira/ confluence/       # Implemented
│   ├── morai/                  # Slack (implemented)
│   └── test_runner/            # pytest + coverage
├── scripts/
│   ├── onboard.py              # CLI entry point
│   └── onboard/                # confluence_puller, jira_puller,
│                               # rag_indexer, repo_manager, generator
├── profiles/
│   └── non-dev/                # .mcp.json + CLAUDE.md cho BA/PM/QA
├── templates/
│   ├── ba_spec.md detail_design.md pm_tasks.md
│   └── pr/feature.md bugfix.md refactor.md
├── tests/                      # 160 tests
├── .morai/tasks/backlog.md     # Task backlog (tracked)
├── .mcp.json
├── .env.example
└── pyproject.toml
```
