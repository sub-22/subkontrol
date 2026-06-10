# Changelog

All notable changes to subkontrol (morai) will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [0.12.0] — 2026-06-10

### Phase 10 — Intent Layer (Orchestrator upgrade)

### Added

- **`agents/orchestrator.md`** — section **Intent Layer: Understand → Compose → Confirm → Orchestrate**. Trước khi route, Morai phải hiểu intent thay vì chỉ match keyword:
  - Tiered depth: SKIP (reflex/XS/command tường minh) · QUICK (size S, intent rõ) · FULL (size ≥ M, mơ hồ, `[NOVEL]`)
  - **Understand** — 4 câu hỏi evidence-based: stated goal, underlying goal, success criteria, constraint ngầm (consult `get_episodes()`/`get_preferences()`/pipeline state); underlying goal `[UNKNOWN]` → hỏi đúng 1 câu về mục tiêu
  - **Compose** — ghép plan từ inventory skills/subagents (parallel vs sequential, model per step, gate placement) thay vì tra chain table cứng
  - **Confirm** — GATE 1 enriched: confirm cả cách hiểu, không chỉ plan
  - **Orchestrate + Record** — sau mỗi Confirm ghi `record_episode(type="intent_calibration", outcome="confirmed"|"corrected")` → nguồn real data cho Learning Loop; ≥3 lần `corrected` cùng pattern → candidate cho `update_preference()`/reflex mới

### Changed

- **`agents/orchestrator.md`** — Skill Chaining Protocol bước 1–2 và "Skill Không Tìm Được" trỏ về Intent Layer thay vì classify/sparring độc lập
- **`CLAUDE.md`** + **`.claude-plugin/CLAUDE.md`** — thêm đoạn "Intent Layer trước routing" vào đầu section Auto-routing
- **`.claude-plugin/CLAUDE.md`** — sync drift cũ từ 0.11.0: bổ sung `morai-telegram` vào Degraded Mode table và "MCP Tools có sẵn" (bị sót khi release Telegram)

---

## [0.11.0] — 2026-06-08

### Phase 9 — Telegram Integration

### Added

- `servers/telegram/server.py` (`morai-telegram`) — Telegram integration: `send_message`, `get_pending_messages` (getUpdates long-poll), `request_approval` (inline keyboard ✅/❌ + `callback_query` polling, mirror `morai-slack: request_approval`)
- `tests/test_env_resolver.py` — `test_reads_telegram_from_config` cho 3-level credential fallback (env → .env → `~/.morai/config.json`)

### Changed

- **`.mcp.json`** — đăng ký `morai-telegram` server (env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- **`.claude-plugin/plugin.json`** — thêm userConfig fields `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **`.env.example`** — thêm Telegram credentials block
- **`pyproject.toml`** — thêm `httpx>=0.27.0` (import trực tiếp cho Telegram Bot API; trước đây chỉ là transitive dep qua `mcp`)
- **`servers/_env.py`** — thêm `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` vào `_CONFIG_KEY_MAP` — đảm bảo Telegram đọc credential qua đúng 3-level fallback (env → .env → `~/.morai/config.json`) giống Slack/Jira/Confluence, không bị silent-fail ở tầng config.json
- **`skills/init/SKILL.md`** — guided setup hỏi Telegram (Bot Token qua @BotFather, Chat ID qua @userinfobot), ghi vào `pluginConfigs`
- **`CLAUDE.md`** — `morai-telegram` vào "MCP Tools có sẵn" và "Degraded Mode" fallback table
- **`skills/doctor/SKILL.md`** — thêm `morai-telegram` vào health check (test block, status table `Integrations: 0/4`, hướng dẫn fix khi chưa configure, `$ARGUMENTS` filter, `DOCTOR_RESULT` summary)
- **`skills/{ba,pm,architect,reviewer,security,qa,pr,incident}/SKILL.md`** — thêm hook `> **Telegram (optional):** ...` song song với Slack ở bước notify cuối mỗi pipeline phase (`pr` thêm hẳn `morai-telegram: send_message(...)` trong Bước 8)
- **`README.md`** — env vars table + cấu trúc project

### Fixed

- **Version mismatch** — `pyproject.toml` (kẹt ở 0.8.0 từ commit `08830be`) và `marketplace.json` (kẹt ở 0.9.0 từ commit `4846a22`) bị bỏ rơi mỗi khi `plugin.json` bump tiếp lên 0.10.0 → 0.10.1 một mình. Đồng bộ cả 3 file + README badge về **0.10.1**. Khi bump version sau này — nhớ touch cả 4 chỗ: `pyproject.toml`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (cả `metadata.version` lẫn `plugins[0].version`), README badge

---

## [0.10.0] — 2026-05-19

### Phase 8 — Implementation Rigor (từ workflows)

Adopt các điểm mạnh về quy trình từ `ai-workflows` vào Morai — giữ nguyên infrastructure MCP, tăng độ chặt chẽ của execution flow.

#### Added

- `templates/progress.md` — chunk progress file template: track status (pending/in_progress/done/failed), retries, completed_at per chunk. Source of truth cho chunk implementation, độc lập với MCP pipeline FSM
- `checklists/verify.md` — per-chunk verify checklist trước commit: 4 levels (Code / Test / Logic / Integration). Bắt buộc pass trước khi update progress → done
- `checklists/refactor-verify.md` — refactor checklist sau GREEN phase: code quality + test quality + cleanup. Morai tự evaluate, surface findings qua AskUserQuestion multi-select — user chọn cái nào áp dụng
- `checklists/review.md` — structured review checklist với 6 platform-specific sections: Python, Go, Node.js, Frontend, Java/Spring, PHP. Output format chuẩn với severity CRITICAL/MAJOR/MINOR/SUGGESTION

#### Changed

**`skills/dev/SKILL.md`**
- `Bước 0b` — Progress file check: auto-create nếu session mới, auto-resume nếu tồn tại. Gate check: STOP nếu design doc chưa có
- `2a-pre` — Impact gap cross-check trước chunk đầu tiên: đọc L1–L4 từ design doc, tìm file unassigned, hỏi user [thêm vào chunk hiện tại / tạo chunk mới / bỏ qua]
- `2a` RED phase: confirm FAIL ở assertion stage (không phải compile error)
- `2b` GREEN phase: 3-attempt no-progress detection (fail count + test names giống nhau → mark failed, báo Dev)
- `2d` REFACTOR phase: đọc `checklists/refactor-verify.md`, surface findings với AskUserQuestion multi-select
- `2e` Verify + progress update: chạy `checklists/verify.md`, update chunk → done
- Micro-gate summary: hiển thị progress bảng đầy đủ sau mỗi chunk

**`skills/architect/SKILL.md`**
- `Bước 1`: gate check — STOP + error message nếu `specs/<id>.md` không tồn tại
- `Bước 2b`: L1–L4 Impact Analysis (solution-agnostic, chạy một lần): L3 Contract (grep API spec, ORM models) + L4 System (ENV vars, external consumers)
- `Bước 3`: multi-solution evaluation — số solutions auto-scale theo task size (S/M→2, L→3, XL→4-5); đánh giá 7 criteria mỗi solution (Impact / Tech constraints / Security / Architecture fit / Root cause / Effort & Risk / Trade-offs); single-solution exception cho trivial changes
- `Bước 6`: Readiness Assessment 7 criteria (AC-IDs / file paths / verify commands / open questions / chunk size / risks / migration plan) → 🟢/🟡/🔴; QA parallel trigger reminder

**`skills/ba/SKILL.md`**
- `Bước 4a`: INVEST validation cho từng User Story (Independent / Negotiable / Valuable / Estimable / Small / Testable) — ❌ bất kỳ → BLOCK
- `Bước 4b`: Readiness Status enum: READY_FOR_DESIGN / NEED_CLARIFY / BLOCKED — ghi vào spec để Architect đọc được

**`skills/reviewer/SKILL.md`**
- Flags: `--quick` (chỉ CRITICAL), `--resume N` (tiếp từ category N)
- `Bước 0`: platform detection từ project files — load platform-specific checks từ `checklists/review.md`
- Severity chuẩn: 🔴 CRITICAL (blocks merge) / 🟠 MAJOR / 🟡 MINOR / 💡 SUGGESTION

**`templates/detail_design.md`**
- Section `File Impact`: 4 sub-tables L1 Direct / L2 Ripple / L3 Contract / L4 System
- Section `Chunk Plan`: table đầy đủ với AC-IDs, test files (viết trước), source files (viết sau), verify command, est., impact layer, test focus
- Reference tables: verify command per chunk type + test focus per chunk type
- Section `Readiness State`: 7-criteria checklist với 🟢/🟡/🔴 aggregation

**`templates/ba_spec.md`**
- Section `INVEST Validation`: table 6 criteria per user story
- Section `Readiness Status`: READY_FOR_DESIGN / NEED_CLARIFY / BLOCKED block
- `Open Questions`: chuẩn hóa với ID (Q-1, Q-2...) và cột Blocking?

---

## [0.9.0] — 2026-05-18

### Phase 7 — Credential UX + Multi-provider Git + Context Optimization

#### Added

- `servers/git/_provider.py` — Git provider abstraction: auto-detect GitHub, Bitbucket Cloud, Bitbucket Server từ remote URL. Tools: `list_open_prs`, `get_pr_detail`, `post_pr_comment` cho cả 3 provider
- `skills/pr-review/` — `/morai:pr-review` skill: list open PRs (GitHub + Bitbucket) → chọn → review chi tiết → post comment
- `servers/_env.py` — 3-level credential resolution: env var → `.env` → `~/.morai/config.json`
- `skills/init/skill.md` — guided integration setup: hỏi từng integration (Jira / Confluence / Slack), ghi vào `~/.morai/config.json`
- `tests/test_env_resolver.py` — 16 tests cho 3-level fallback, isolation với real credentials trên máy dev
- `rules/code.md` — 3 sections mới: Coding Practices, Security Boundaries, Database Safety (nội dung từ Lessons Learned cũ, nay load on-demand thay vì per-turn)
- `skills/doctor/SKILL.md` — Context Budget Report: đo token cost của bootstrap files, cảnh báo nếu CLAUDE.md vượt ngưỡng

#### Changed

- **Credential setup UX** — Jira / Confluence / Slack credentials không còn yêu cầu khi `claude plugin install`. Chỉ cần `MORAI_GLOBAL_PATH`. Integrations cấu hình sau qua `/morai:init`
- **`plugin.json` userConfig** — gọn từ 13 fields → 5 fields (MORAI_GLOBAL_PATH + GitHub/Bitbucket)
- **`.mcp.json`** — morai-jira, morai-confluence, morai-slack nhận `MORAI_GLOBAL_PATH` thay vì credentials trực tiếp; credentials đọc từ `~/.morai/config.json` qua `_env.py`
- **Session Start — mode-based loading** — CLAUDE.md định nghĩa 2 modes:
  - *Lightweight* (init/scan/onboard/doctor/query): chỉ CLAUDE.md (~2,400 tokens)
  - *Pipeline* (ba/dev/review/security/...): load thêm `agents/morai.md` + `agents/recall.md`
- **`agents/reflexes.md`** — không còn auto-load khi session start; Active Reflexes đã inline trong CLAUDE.md; load full detail on-demand
- **CLAUDE.md** — slim −15% (cắt Brain Files table, Lessons Learned, North Star); nội dung đã có trong `agents/morai.md` và `rules/code.md`
- **`skills/scan/SKILL.md`** — Bước 2: `list_files()` → `project_summary()` để tránh blow context với project lớn (10k files = 62k tokens → 700 tokens)
- **`skills/doctor/SKILL.md`** — `list_files(".")` → `list_files(".", "*")` (root-level only, bounded)
- **`agents/merge.md`** — `list_files(".", "**/*.py")` → `morai-rag: search()` (RAG đã index)
- **`servers/confluence/server.py`** — auto-detect Cloud vs Server/DC: `atlassian.net` → Basic auth (email + token); else → Bearer PAT
- **`servers/pipeline/server.py`** — atomic writes qua `tempfile + os.replace()` thay vì `write_text()` trực tiếp — tránh corrupt JSON nếu crash giữa chừng
- **`servers/rag/server.py`** — dùng `resolve()` thay vì `os.getenv()` để consistent với các servers khác

#### Fixed

- `servers/_env.py` — thêm `BITBUCKET_BASE_URL` vào `_CONFIG_KEY_MAP` (thiếu → Bitbucket Server detection luôn fail khi dùng config.json)
- `servers/git/_provider.py` — thêm logging cho `_http()`: HTTP errors log với status code + URL; unexpected errors log với full stack trace
- `servers/jira/server.py` — cast fixes cho mypy strict mode

#### Token Budget (sau optimization)

| Session type | Trước | Sau |
|---|---|---|
| Lightweight (init/scan/query) | ~7,967 tokens | ~2,400 tokens (−70%) |
| Pipeline (ba/dev/review) | ~7,967 tokens | ~5,600 tokens (−30%) |

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
