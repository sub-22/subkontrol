# Changelog

All notable changes to subkontrol (morai) will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [0.8.0] — 2026-05-16

### Phase 6 — Morai Identity Distribution

#### Added

- `skills/init/skill.md` — `/morai:init` skill: write Morai identity vào `~/.claude/CLAUDE.md`, apply toàn máy sau một lần chạy
- `.claude-plugin/CLAUDE.md` — Morai identity bundled vào plugin directory
- `.claude-plugin/plugin.json` — thêm `"skills": "../skills"` để `/reload-plugins` đếm đúng số skills

#### Fixed

- Plugin install vào project khác không còn mất Morai identity — user chạy `/morai:init` một lần là đủ

---

## [0.7.0] — 2026-05-15

### Phase 5 — Team Knowledge Sharing + Git Workflow + Plugin Marketplace

#### Added — MCP Servers (fully implemented)

- `servers/jira/server.py` — `get_ticket`, `search_tickets`, `get_ticket_comments`, `get_project_epics`, `get_active_sprint`, `fetch_my_tasks` (với shadow mode khi chưa configure)
- `servers/confluence/server.py` — `get_page`, `search`, `get_children`, `get_space_pages` (filter theo label)
- `servers/morai/server.py` (morai-slack) — `send_message`, `get_thread`, `get_pending_messages`, `request_approval` (reaction polling)
- `servers/test_runner/server.py` (morai-test) — `run_pytest`, `run_coverage`, `detect_test_framework`
- `servers/git/server.py` — thêm `get_pr_template`, `get_open_pr`, `update_pr`
- `servers/file/server.py` — thêm `project_summary`
- `servers/memory/server.py` — thêm `sync_ticket_knowledge` (ghi knowledge vào design repo + re-index RAG + push)

#### Added — morai-onboard CLI

- `scripts/onboard.py` — bootstrap `{project-name}-design` knowledge repo cho non-dev
- `scripts/onboard/` — `repo_manager`, `confluence_puller`, `jira_puller`, `rag_indexer`, `generator`
- Hỗ trợ `--role dev|non-dev`: dev pull Confluence/Jira; non-dev fallback clone source + `/morai:scan`
- Idempotent: chạy lại chỉ update file mới/changed (hash-based)
- Confluece label mapping: `basic-design`→`basic_design/`, `detail-design`→`detail_design/`, `adr`→`decisions/`

#### Added — Skills

- `skills/pr/SKILL.md` — `/morai:pr`: collect context → detect PR type → load template (project first, fallback subkontrol) → fill description → CI gate → push → create/update PR → notify Slack
- `skills/reflect/SKILL.md` — Bước 5: generate `summary.md` + `learnings.md` → `sync_ticket_knowledge`

#### Added — Reflexes

- `R-014` — Task recording: persist to `morai-memory` + `~/.morai/tasks/backlog.md`
- `R-015` — Branch guard: STOP khi chuẩn bị tạo branch → hỏi cả branch name + base branch
- `R-016` — Auto-fetch Jira tasks khi pipeline empty → `fetch_my_tasks` với shadow mode

#### Added — Git Workflow Rules

- Branch naming: `{type}/{TICKET-ID}_{slug}` (underscore separator, ≤35 chars)
- Commit convention detection: Case 1 (project có convention) → follow; Case 2 → `[{PREFIX}-{num}] {type}: {msg}`
- Bước 0 trong `/morai:dev`: check protected branch → propose branch → hỏi base → tạo
- `/morai:pr` Bước 0: detect open PR → update description nếu đã tồn tại

#### Added — Non-dev Profile

- `profiles/non-dev/.mcp.json` — chỉ load: jira, confluence, rag, slack, memory
- `profiles/non-dev/CLAUDE.md` — Morai identity cho BA/PM/QA không có source code

#### Added — Storage Architecture

- `~/.morai/memory/` — global user memory (cross-project)
- `~/.morai/tasks/backlog.md` — global task backlog
- `{WORKSPACE}/.morai/rag/` — per-project vector index
- `{WORKSPACE}/.morai/pipeline/` — per-project FSM state
- `MORAI_DESIGN_REPO` env var — path tới local clone của `{project}-design` repo

#### Added — Dev Identity

- `config/dev_mapping.example.json` — template mapping git email → Jira account
- `servers/jira/server.py: fetch_my_tasks()` — fetch + prioritize tasks của dev hiện tại (Blocker > Critical > High)
- Shadow mode: hiển thị badge `⚠️ SHADOW` khi Jira chưa configure

#### Added — Slack → Skill Routing

- `agents/orchestrator.md` — intent map: `code_review`→`/morai:reviewer`, `security_audit`→`/morai:security`, `analyze_ticket`→`/morai:ba`
- PR ref extraction: GitHub URL, Bitbucket URL, `#number` pattern

#### Added — Public Repo & Marketplace

- `LICENSE` — MIT
- `SECURITY.md` — vulnerability reporting process
- `.claude-plugin/marketplace.json` — marketplace index cho `claude plugin install morai@sub22`
- Branch protection master: require PR + 1 approval + CI pass; no force push; no deletion
- `install.sh` — one-command install script

#### Changed

- `skills/dev/SKILL.md` — Bước 0 branch setup; commit message detection (2 cases); auto-trigger reflect sau GATE 3
- `skills/reviewer/SKILL.md` — trigger reflect sau APPROVE
- `.mcp.json` — fix `MORAI_MEMORY_PATH`/`MORAI_PIPELINE_PATH` paths; add `morai-test`, `MORAI_DESIGN_REPO`
- `agents/reflexes.md` — R-015 extended: require base branch confirm; update R-016

#### Fixed

- `DESIGN_REPO = Path("")` truthy bug → dùng `None` sentinel
- Silent `git push` failure trong `sync_ticket_knowledge` → return error message
- Pipeline tests: add `MORAI_PIPELINE_PATH` fixture
- `plugin.json`: remove unsupported `"secret"` field từ `userConfig`
- `marketplace.json`: thêm required top-level `name` field

#### Security

- Gitignore `config/dev_mapping.json` (chứa real email/account IDs)
- Sanitize `servers/jira/stubs/assigned_tasks.json`: replace real email → `dev@example.com`
- Gitignore `makeingbest.md` (internal notes)

---

## [Unreleased] — v0.6.0

### Phase 4 — Event Triggers + Cost Management

#### Added
- `servers/events/server.py` — Event bus MCP server: subscribe, unsubscribe, publish, event log
- `agents/events.md` — Event protocol: 15 event types, default subscriptions, cron setup guide
- `agents/cost.md` — Model routing table (haiku/sonnet/opus by task size), budget lifecycle, context compression strategy
- `morai-pipeline: record_token_usage()` — Per-skill token tracking with USD estimate
- `morai-pipeline: get_pipeline_cost()` — Cost breakdown by skill and model
- `morai-pipeline: get_cost_summary_all()` — Cross-pipeline cost comparison
- 8 default event subscriptions: PR opened→reviewer, test fail→incident, PR merged→reflect, weekly kaizen, sprint evolve, pipeline blocked→notify
- `morai-events: get_cron_setup_guide()` — CronCreate commands cho scheduled triggers
- `MORAI_BUDGET_TOKENS` env var — configurable per-pipeline token budget (default: 200,000)

#### Changed
- `agents/orchestrator.md` — Added model routing section and event-driven dispatch protocol
- `agents/morai.md` — TIER B now includes `agents/cost.md` and `agents/events.md`
- `.mcp.json` — Registered `morai-events` server

---

### Phase 3 — HITL Gates Standardized

#### Added
- `agents/hitl.md` — HITL gate protocol: 5 gate types (APPROVE/REVIEW/CHOICE/CONFIRM/UNBLOCK), create/resolve/display/expired format
- `morai-pipeline: create_gate()` — Formal gate creation with timeout and lazy expiry
- `morai-pipeline: resolve_gate()` — Record human response, unblock pipeline
- `morai-pipeline: get_gate()` — Read gate with auto-expiry check
- `morai-pipeline: get_pending_gates()` — All pending gates for a ticket
- `morai-pipeline: list_all_pending_gates()` — Global view across all pipelines, sorted by urgency (UNBLOCK first)
- `morai-pipeline: cancel_gate()` — Cancel gate when no longer needed
- Security UNBLOCK gate in `/morai:security` — BLOCK verdict creates gate, pipeline cannot advance to QA until resolved
- `pending_gate_count` field in pipeline state for fast checking

#### Changed
- `skills/dev/SKILL.md` — GATE 1/2/3 now use `create_gate()` instead of informal "DỪNG" text
- `agents/spawner.md` — Wave GATE 1 aggregation uses single REVIEW gate for entire wave
- `agents/recall.md` — Recovery sequence now includes `list_all_pending_gates()` as first step (before pipeline state)
- `agents/morai.md` — TIER B includes `agents/hitl.md`

---

### Phase 2 — Multi-agent Parallelism

#### Added
- `agents/spawner.md` — Parallel agent orchestration protocol: 5 phases (context prep → spawn → GATE 1 aggregate → collect commits → advance wave)
- `agents/merge.md` — Worktree merge protocol: sequential merge strategy, conflict resolution, single PR creation
- `templates/wave_plan.json` — Wave plan template for PM skill
- `morai-pipeline: init_waves()` — Initialize parallel wave plan
- `morai-pipeline: start_wave()` — Start a wave, returns tasks_to_spawn with worktree branches
- `morai-pipeline: update_task_in_wave()` — Track sub-agent progress (approach_ready/committed/blocked)
- `morai-pipeline: get_wave_status()` — Wave status with `all_approaches_ready` and `all_committed` flags
- `morai-pipeline: commit_wave()` — Mark wave committed, advance to next wave
- `morai-pipeline: get_wave_plan()` — Retrieve full wave plan
- FSM states: `DEV_PARALLEL_RUNNING`, `DEV_ALL_COMMITTED`

#### Changed
- `skills/pm/SKILL.md` — Added Bước 5: dependency analysis (topological sort) → wave plan generation
- `agents/orchestrator.md` — Parallel dispatch section: wave plan check → spawn vs sequential decision
- `agents/morai.md` — TIER B includes `agents/spawner.md` and `agents/merge.md`
- `servers/pipeline/server.py` — Extended FSM with parallel path: `PM_DONE → DEV_PARALLEL_RUNNING → DEV_ALL_COMMITTED → REVIEW_RUNNING`

---

### Phase 1 — FSM Pipeline + Permission Model

#### Added
- `servers/pipeline/server.py` — NEW MCP server: FSM pipeline lifecycle management
  - 18 states, validated transitions, pre-condition checks (file existence, PR URL)
  - Tools: `create_pipeline`, `transition`, `get_state`, `list_pipelines`, `block_pipeline`, `get_valid_transitions`
- `permissions.yaml` — Authoritative skill permission matrix: which skill can read/write which zone, which git ops
- `morai-pipeline` registered in `.mcp.json`
- `MORAI_BUDGET_TOKENS` env var in `.mcp.json`
- `.github/workflows/ci.yml` — CI pipeline: ruff lint + format check + mypy + pytest

#### Changed
- `servers/file/server.py` — Zone enforcement:
  - `write_file()` restricted to artifact directories (specs/, plans/, reviews/, etc.)
  - `write_source_file()` NEW — only for source code, Dev skills only
  - `append_file()` restricted to artifact zone
  - `read_file()` now returns error string instead of raising exception
- `skills/qa/SKILL.md` — Bước 4 removed automated test file writing (QA read-only on source code)
- All pipeline skills — Now call `morai-pipeline: transition()` instead of `morai-memory: save_pipeline_state()`

---

## Prior Work — v0.5.0 (Session review + fixes)

### Fixed
- `servers/jira/server.py`, `servers/confluence/server.py`, `servers/morai/server.py` — Stubs no longer raise `NotImplementedError`; return structured error dicts instead
- `servers/file/server.py` — Path traversal check replaced `startswith` with `is_relative_to()`
- `request_approval()` in Slack server — no longer silently auto-approves; surfaces to user
- `agents/reflexes.md`, `agents/knowledge_gateway.md` — Reflex count synced (was 8, now 13)
- `agents/morai.md` — `context_gateway.md` and `knowledge_gateway.md` added to TIER B loading
- `servers/git/server.py` — Added `push()`, `create_pr()`, `get_pr_diff()`, `add_pr_comment()`, `get_current_branch()`
- `servers/file/server.py` — Added `delete_file()`, `append_file()`, `move_file()`
- `servers/memory/server.py` — Added `archive_old_episodes()` for 90-day memory decay

#### Added
- `tests/test_memory_server.py` — 18 tests
- `tests/test_file_server.py` — 16 tests
- `tests/test_git_server.py` — 11 tests
- `README.md` — Added `morai-memory` to server table with status column, added "First run" section

#### Removed
- `sentence-transformers` dependency (unused)
- `asyncio_mode` from pytest config (stale warning)

---

## [0.5.0] — 2026-05-15 (Initial commit)

### Added
- Plugin structure: `plugin.json`, `.mcp.json`, `.env.example`
- Agent brain files: `morai.md`, `orchestrator.md`, `judge.md`, `memory.md`, `reflexes.md`, `recall.md`, `context_gateway.md`, `knowledge_gateway.md`
- Rules: `governance.md`, `code.md`, `quality.md`, `autonomy.md`, `observability.md`, `rules_gateway.md`
- Skills: `scan`, `ba`, `architect`, `pm`, `dev`, `reviewer`, `security`, `qa`, `reflect`, `evolve`, `kaizen`, `sparring`, `incident`
- MCP servers (implemented): `morai-rag`, `morai-file`, `morai-git`, `morai-memory`
- MCP servers (stub): `morai-jira`, `morai-confluence`, `morai-slack`
- Templates: `ba_spec.md`, `detail_design.md`, `pm_tasks.md`, `task.json`, `tasks_index.json`, PR templates
- `CLAUDE.md` — Morai identity, brain files reference, skill pipeline, lessons learned
