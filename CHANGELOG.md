# Changelog

All notable changes to subkontrol (morai) will be documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

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
