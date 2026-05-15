"""Pipeline FSM MCP server — manages pipeline lifecycle with valid state transitions.

Supports both sequential and parallel (wave-based) dev execution.
Includes HITL gate management for formal human-in-the-loop checkpoints.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-pipeline")

PIPELINE_ROOT = Path(os.getenv("MORAI_MEMORY_PATH", ".morai/memory")).parent / "pipeline"

# ── FSM Definition ─────────────────────────────────────────────────────────────

STATES = frozenset({
    "IDLE",
    "BA_RUNNING", "BA_DONE",
    "ARCHITECT_RUNNING", "ARCHITECT_DONE",
    "PM_RUNNING", "PM_DONE",
    # Sequential dev path
    "DEV_RUNNING",
    "DEV_REVIEWING",         # guided: waiting for Dev to review approach/code
    "DEV_COMMITTED",         # single task committed
    # Parallel dev path
    "DEV_PARALLEL_RUNNING",  # wave-based, N agents running in worktrees
    "DEV_ALL_COMMITTED",     # all waves committed, ready for merge + review
    # Review / QA
    "REVIEW_RUNNING", "REVIEW_DONE",
    "SECURITY_RUNNING", "SECURITY_DONE",
    "QA_RUNNING", "QA_DONE",
    "COMPLETE",
    "BLOCKED",
    "FAILED",
})

TRANSITIONS: dict[str, list[str]] = {
    "IDLE":                  ["BA_RUNNING"],
    "BA_RUNNING":            ["BA_DONE", "BLOCKED"],
    "BA_DONE":               ["ARCHITECT_RUNNING", "PM_RUNNING"],
    "ARCHITECT_RUNNING":     ["ARCHITECT_DONE", "BLOCKED"],
    "ARCHITECT_DONE":        ["PM_RUNNING"],
    "PM_RUNNING":            ["PM_DONE", "BLOCKED"],
    # PM_DONE branches: sequential (1 task or sequential mode) vs parallel (wave plan exists)
    "PM_DONE":               ["DEV_RUNNING", "DEV_PARALLEL_RUNNING"],
    # Sequential path
    "DEV_RUNNING":           ["DEV_REVIEWING", "DEV_COMMITTED", "BLOCKED"],
    "DEV_REVIEWING":         ["DEV_COMMITTED", "DEV_RUNNING", "BLOCKED"],
    "DEV_COMMITTED":         ["REVIEW_RUNNING"],
    # Parallel path
    "DEV_PARALLEL_RUNNING":  ["DEV_ALL_COMMITTED", "DEV_RUNNING", "BLOCKED"],
    "DEV_ALL_COMMITTED":     ["REVIEW_RUNNING"],
    # Review
    "REVIEW_RUNNING":        ["REVIEW_DONE", "DEV_RUNNING", "DEV_PARALLEL_RUNNING", "BLOCKED"],
    "REVIEW_DONE":           ["SECURITY_RUNNING", "QA_RUNNING"],
    "SECURITY_RUNNING":      ["SECURITY_DONE", "DEV_RUNNING", "BLOCKED"],
    "SECURITY_DONE":         ["QA_RUNNING"],
    "QA_RUNNING":            ["QA_DONE", "DEV_RUNNING", "BLOCKED"],
    "QA_DONE":               ["COMPLETE"],
    "COMPLETE":              [],
    "BLOCKED":               ["BA_RUNNING", "ARCHITECT_RUNNING", "PM_RUNNING",
                              "DEV_RUNNING", "DEV_PARALLEL_RUNNING",
                              "REVIEW_RUNNING", "SECURITY_RUNNING", "QA_RUNNING"],
    "FAILED":                [],
}

PRECONDITIONS: dict[str, dict] = {
    "BA_DONE":          {"file_exists": "specs/{ticket_id}.md"},
    "PM_DONE":          {"file_exists": "tasks/{ticket_id}/index.json"},
    "DEV_COMMITTED":    {"field_set": "commit_sha_or_pr_url"},
    "DEV_ALL_COMMITTED":{"wave_plan_complete": True},
    "REVIEW_DONE":      {"file_exists": "reviews/{ticket_id}-review.md"},
    "SECURITY_DONE":    {"file_exists": "reviews/{ticket_id}-security.md"},
    "QA_DONE":          {"file_exists": "tests/{ticket_id}-test-plan.md"},
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _pipeline_path(ticket_id: str) -> Path:
    return PIPELINE_ROOT / ticket_id / "state.json"


def _load_state(ticket_id: str) -> dict:
    path = _pipeline_path(ticket_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(ticket_id: str, state: dict) -> None:
    path = _pipeline_path(ticket_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def _check_precondition(
    to_state: str,
    ticket_id: str,
    context: dict,
    workspace_root: str,
    current_state: dict,
) -> str | None:
    cond = PRECONDITIONS.get(to_state)
    if not cond:
        return None

    if "file_exists" in cond:
        rel_path = cond["file_exists"].format(ticket_id=ticket_id)
        if not (Path(workspace_root) / rel_path).exists():
            return f"Precondition failed: file '{rel_path}' chưa tồn tại"

    if "field_set" in cond:
        if cond["field_set"] == "commit_sha_or_pr_url":
            if not context.get("commit_sha") and not context.get("pr_url"):
                return "Precondition failed: cần commit_sha hoặc pr_url"

    if cond.get("wave_plan_complete"):
        wave_plan = current_state.get("wave_plan", {})
        waves = wave_plan.get("waves", [])
        if not waves:
            return "Precondition failed: không có wave plan — gọi init_waves() trước"
        incomplete = [
            w["wave"] for w in waves
            if w.get("status") != "committed"
        ]
        if incomplete:
            return f"Precondition failed: wave(s) {incomplete} chưa committed"

    return None


# ── Core Pipeline Tools ────────────────────────────────────────────────────────

@mcp.tool()
def create_pipeline(ticket_id: str, spec_path: str = "") -> dict:
    """Khởi tạo pipeline mới cho một ticket.

    Args:
        ticket_id: Jira ticket ID, e.g. "PROJ-123"
        spec_path: Path tới spec file nếu đã có
    """
    existing = _load_state(ticket_id)
    if existing and existing.get("status") not in ("complete", "failed", ""):
        return {"ok": False, "error": f"Pipeline '{ticket_id}' đã tồn tại ở state '{existing.get('state')}'"}

    state = {
        "ticket_id": ticket_id,
        "state": "IDLE",
        "status": "active",
        "completed_steps": [],
        "spec_path": spec_path,
        "created_at": _now(),
        "last_updated": _now(),
        "history": [{"state": "IDLE", "at": _now()}],
    }
    _save_state(ticket_id, state)
    return {"ok": True, "state": "IDLE", "ticket_id": ticket_id}


@mcp.tool()
def transition(
    ticket_id: str,
    to_state: str,
    context: dict | None = None,
    workspace_root: str = ".",
) -> dict:
    """Chuyển pipeline sang state mới với validation đầy đủ.

    Args:
        ticket_id: Jira ticket ID
        to_state: Target state
        context: Extra data (commit_sha, pr_url, block_reason, v.v.)
        workspace_root: Root path để check file preconditions
    """
    context = context or {}

    if to_state not in STATES:
        return {"ok": False, "error": f"Unknown state: '{to_state}'. Valid: {sorted(STATES)}"}

    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại. Gọi create_pipeline() trước."}

    from_state = state["state"]
    valid_next = TRANSITIONS.get(from_state, [])
    if to_state not in valid_next:
        return {
            "ok": False,
            "error": f"Invalid transition: {from_state} → {to_state}. Valid: {valid_next}",
        }

    error = _check_precondition(to_state, ticket_id, context, workspace_root, state)
    if error:
        return {"ok": False, "error": error}

    state["state"] = to_state
    state["last_updated"] = _now()
    state["history"].append({"state": to_state, "from": from_state, "at": _now()})

    for k, v in context.items():
        state[k] = v

    step_done = from_state.replace("_RUNNING", "").lower()
    if "_RUNNING" in from_state and step_done not in state.get("completed_steps", []):
        state.setdefault("completed_steps", []).append(step_done)

    if to_state == "COMPLETE":
        state["status"] = "complete"
        state["completed_at"] = _now()
    elif to_state == "FAILED":
        state["status"] = "failed"
    elif to_state == "BLOCKED":
        state["status"] = "blocked"
    else:
        state["status"] = "active"

    _save_state(ticket_id, state)
    return {"ok": True, "from": from_state, "to": to_state}


@mcp.tool()
def get_state(ticket_id: str) -> dict:
    """Lấy current state của pipeline."""
    state = _load_state(ticket_id)
    if not state:
        return {"error": f"Pipeline '{ticket_id}' chưa tồn tại"}
    return state


@mcp.tool()
def list_pipelines(status_filter: str = "") -> list[dict]:
    """Liệt kê tất cả pipelines, optional filter theo status."""
    if not PIPELINE_ROOT.exists():
        return []
    result = []
    for state_file in PIPELINE_ROOT.glob("*/state.json"):
        s = json.loads(state_file.read_text(encoding="utf-8"))
        if status_filter and s.get("status") != status_filter:
            continue
        result.append({
            "ticket_id": s.get("ticket_id"),
            "state": s.get("state"),
            "status": s.get("status"),
            "last_updated": s.get("last_updated"),
            "blocked_reason": s.get("blocked_reason"),
            "current_wave": s.get("wave_plan", {}).get("current_wave"),
        })
    return sorted(result, key=lambda x: x.get("last_updated", ""), reverse=True)


@mcp.tool()
def block_pipeline(ticket_id: str, reason: str) -> dict:
    """Block pipeline với lý do cụ thể."""
    return transition(ticket_id, "BLOCKED", context={"blocked_reason": reason})


@mcp.tool()
def get_valid_transitions(ticket_id: str) -> dict:
    """Lấy danh sách transitions hợp lệ từ state hiện tại."""
    state = _load_state(ticket_id)
    if not state:
        return {"error": f"Pipeline '{ticket_id}' chưa tồn tại"}
    current = state["state"]
    return {"current_state": current, "valid_next": TRANSITIONS.get(current, [])}


# ── Wave Management ────────────────────────────────────────────────────────────

@mcp.tool()
def init_waves(ticket_id: str, waves: list[dict]) -> dict:
    """Khởi tạo wave plan cho parallel execution.

    Args:
        ticket_id: Jira ticket ID
        waves: List of wave definitions:
               [{"wave": 1, "task_ids": ["TASK-1", "TASK-3"], "rationale": "..."},
                {"wave": 2, "task_ids": ["TASK-2"], "rationale": "depends on wave 1"}]
    Returns:
        {"ok": bool, "total_waves": int}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    wave_plan = {
        "total_waves": len(waves),
        "current_wave": None,
        "waves": [
            {
                "wave": w["wave"],
                "task_ids": w["task_ids"],
                "rationale": w.get("rationale", ""),
                "status": "pending",
                "tasks": {tid: {"status": "pending"} for tid in w["task_ids"]},
                "started_at": None,
                "committed_at": None,
            }
            for w in waves
        ],
    }
    state["wave_plan"] = wave_plan
    state["last_updated"] = _now()
    _save_state(ticket_id, state)
    return {"ok": True, "total_waves": len(waves), "wave_plan": wave_plan}


@mcp.tool()
def start_wave(ticket_id: str, wave_num: int) -> dict:
    """Bắt đầu thực thi một wave — spawn agents cho các tasks trong wave này.

    Args:
        ticket_id: Jira ticket ID
        wave_num: Wave number (1-based)
    Returns:
        {"ok": bool, "tasks_to_spawn": list[dict]}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    wave_plan = state.get("wave_plan")
    if not wave_plan:
        return {"ok": False, "error": "Wave plan chưa được init. Gọi init_waves() trước."}

    wave = next((w for w in wave_plan["waves"] if w["wave"] == wave_num), None)
    if not wave:
        return {"ok": False, "error": f"Wave {wave_num} không tồn tại"}

    # Validate previous waves are committed
    for w in wave_plan["waves"]:
        if w["wave"] < wave_num and w["status"] != "committed":
            return {
                "ok": False,
                "error": f"Wave {w['wave']} chưa committed. Phải hoàn thành theo thứ tự.",
            }

    wave["status"] = "running"
    wave["started_at"] = _now()
    wave_plan["current_wave"] = wave_num
    state["last_updated"] = _now()
    _save_state(ticket_id, state)

    tasks_to_spawn = [
        {
            "task_id": tid,
            "worktree_branch": f"feat/{ticket_id}-{tid.lower()}",
        }
        for tid in wave["task_ids"]
    ]
    return {"ok": True, "wave": wave_num, "tasks_to_spawn": tasks_to_spawn}


@mcp.tool()
def update_task_in_wave(
    ticket_id: str,
    wave_num: int,
    task_id: str,
    status: str,
    worktree_branch: str = "",
    commit_sha: str = "",
    approach_summary: str = "",
    files_changed: list[str] | None = None,
    error: str = "",
) -> dict:
    """Cập nhật trạng thái của một task trong wave.

    Args:
        status: "running" | "approach_ready" | "committed" | "blocked" | "failed"
        worktree_branch: Branch name của worktree
        commit_sha: Commit SHA nếu đã committed
        approach_summary: Tóm tắt approach khi ở approach_ready (GATE 1)
        files_changed: List files đã/sẽ thay đổi
    """
    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    wave_plan = state.get("wave_plan", {})
    wave = next((w for w in wave_plan.get("waves", []) if w["wave"] == wave_num), None)
    if not wave:
        return {"ok": False, "error": f"Wave {wave_num} không tồn tại"}

    if task_id not in wave.get("tasks", {}):
        return {"ok": False, "error": f"Task '{task_id}' không có trong wave {wave_num}"}

    task_data = wave["tasks"][task_id]
    task_data["status"] = status
    if worktree_branch:
        task_data["worktree_branch"] = worktree_branch
    if commit_sha:
        task_data["commit_sha"] = commit_sha
    if approach_summary:
        task_data["approach_summary"] = approach_summary
    if files_changed is not None:
        task_data["files_changed"] = files_changed
    if error:
        task_data["error"] = error
    task_data["updated_at"] = _now()

    state["last_updated"] = _now()
    _save_state(ticket_id, state)
    return {"ok": True, "task_id": task_id, "status": status}


@mcp.tool()
def get_wave_status(ticket_id: str, wave_num: int) -> dict:
    """Lấy trạng thái chi tiết của một wave.

    Returns:
        {wave, status, task_summary, pending/approach_ready/committed/blocked counts,
         all_approaches_ready (GATE 1 flag), all_committed (advance flag)}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    wave = next(
        (w for w in state.get("wave_plan", {}).get("waves", []) if w["wave"] == wave_num),
        None,
    )
    if not wave:
        return {"error": f"Wave {wave_num} không tồn tại"}

    tasks = wave.get("tasks", {})
    by_status: dict[str, list[str]] = {}
    for tid, tdata in tasks.items():
        s = tdata.get("status", "pending")
        by_status.setdefault(s, []).append(tid)

    return {
        "wave": wave_num,
        "status": wave["status"],
        "total_tasks": len(tasks),
        "by_status": by_status,
        "all_approaches_ready": all(
            t.get("status") in ("approach_ready", "committed") for t in tasks.values()
        ),
        "all_committed": all(t.get("status") == "committed" for t in tasks.values()),
        "approaches": {
            tid: tdata.get("approach_summary", "")
            for tid, tdata in tasks.items()
            if tdata.get("approach_summary")
        },
    }


@mcp.tool()
def commit_wave(ticket_id: str, wave_num: int) -> dict:
    """Đánh dấu wave đã committed sau khi tất cả tasks committed và merge xong.

    Tự động advance current_wave và check nếu tất cả waves done.

    Returns:
        {"ok": bool, "next_wave": int | None, "all_done": bool}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    wave_plan = state.get("wave_plan", {})
    wave = next((w for w in wave_plan.get("waves", []) if w["wave"] == wave_num), None)
    if not wave:
        return {"ok": False, "error": f"Wave {wave_num} không tồn tại"}

    # Validate all tasks committed
    not_committed = [
        tid for tid, tdata in wave.get("tasks", {}).items()
        if tdata.get("status") != "committed"
    ]
    if not_committed:
        return {
            "ok": False,
            "error": f"Tasks chưa committed trong wave {wave_num}: {not_committed}",
        }

    wave["status"] = "committed"
    wave["committed_at"] = _now()

    # Find next wave
    next_wave = next(
        (w["wave"] for w in wave_plan["waves"] if w["wave"] > wave_num and w["status"] == "pending"),
        None,
    )

    all_done = all(w["status"] == "committed" for w in wave_plan["waves"])
    wave_plan["current_wave"] = next_wave
    state["last_updated"] = _now()
    _save_state(ticket_id, state)

    return {"ok": True, "next_wave": next_wave, "all_done": all_done}


@mcp.tool()
def get_wave_plan(ticket_id: str) -> dict:
    """Lấy toàn bộ wave plan của một pipeline."""
    state = _load_state(ticket_id)
    if not state:
        return {"error": f"Pipeline '{ticket_id}' chưa tồn tại"}
    wave_plan = state.get("wave_plan")
    if not wave_plan:
        return {"error": "Pipeline này không có wave plan (sequential mode)"}
    return wave_plan


# ── HITL Gate Management ───────────────────────────────────────────────────────

GATE_TYPES = frozenset({"APPROVE", "REVIEW", "CHOICE", "CONFIRM", "UNBLOCK"})

# Gates stored in: PIPELINE_ROOT/<ticket_id>/gates/<gate_id>.json


def _gates_dir(ticket_id: str) -> Path:
    return PIPELINE_ROOT / ticket_id / "gates"


def _gate_path(ticket_id: str, gate_id: str) -> Path:
    return _gates_dir(ticket_id) / f"{gate_id}.json"


def _next_gate_id(ticket_id: str) -> str:
    gates_dir = _gates_dir(ticket_id)
    if not gates_dir.exists():
        return f"{ticket_id}-gate-001"
    existing = list(gates_dir.glob("*.json"))
    return f"{ticket_id}-gate-{len(existing) + 1:03d}"


def _expires_at(timeout_minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def _is_expired(gate: dict) -> bool:
    expires_str = gate.get("expires_at", "")
    if not expires_str:
        return False
    try:
        exp = datetime.strptime(expires_str, "%Y-%m-%d %H:%M UTC").replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp
    except ValueError:
        return False


def _load_gate(ticket_id: str, gate_id: str) -> dict:
    path = _gate_path(ticket_id, gate_id)
    if not path.exists():
        return {}
    gate = json.loads(path.read_text(encoding="utf-8"))
    # Lazy expiry check
    if gate.get("status") == "pending" and _is_expired(gate):
        gate["status"] = "expired"
        gate["resolved_by"] = "timeout"
        gate["resolved_at"] = _now()
        path.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
        # Update pipeline pending count
        _decrement_pending_gates(ticket_id)
    return gate


def _increment_pending_gates(ticket_id: str) -> None:
    state = _load_state(ticket_id)
    if state:
        state["pending_gate_count"] = state.get("pending_gate_count", 0) + 1
        state["last_updated"] = _now()
        _save_state(ticket_id, state)


def _decrement_pending_gates(ticket_id: str) -> None:
    state = _load_state(ticket_id)
    if state:
        count = state.get("pending_gate_count", 0)
        state["pending_gate_count"] = max(0, count - 1)
        state["last_updated"] = _now()
        _save_state(ticket_id, state)


@mcp.tool()
def create_gate(
    ticket_id: str,
    gate_type: str,
    question: str,
    context: str = "",
    timeout_minutes: int = 120,
    options: list[str] | None = None,
) -> dict:
    """Tạo một HITL gate — pipeline pause và chờ human respond.

    Args:
        ticket_id: Jira ticket ID
        gate_type: "APPROVE" | "REVIEW" | "CHOICE" | "CONFIRM" | "UNBLOCK"
        question: Câu hỏi hoặc mô tả artifact cần review
        context: Context thêm (approach summary, diff, v.v.)
        timeout_minutes: Thời gian chờ trước khi auto-expire (default: 120 phút)
        options: Cho CHOICE gate — list options Dev có thể chọn
    Returns:
        {"ok": bool, "gate_id": str, "expires_at": str}
    """
    if gate_type not in GATE_TYPES:
        return {"ok": False, "error": f"Invalid gate_type '{gate_type}'. Valid: {sorted(GATE_TYPES)}"}

    pipeline = _load_state(ticket_id)
    if not pipeline:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    gate_id = _next_gate_id(ticket_id)
    expires = _expires_at(timeout_minutes)

    gate = {
        "gate_id": gate_id,
        "ticket_id": ticket_id,
        "gate_type": gate_type,
        "status": "pending",
        "question": question,
        "context": context,
        "options": options or [],
        "pipeline_state_at_creation": pipeline.get("state"),
        "created_at": _now(),
        "timeout_minutes": timeout_minutes,
        "expires_at": expires,
        "response": None,
        "resolved_by": None,
        "resolved_at": None,
    }

    _gates_dir(ticket_id).mkdir(parents=True, exist_ok=True)
    _gate_path(ticket_id, gate_id).write_text(
        json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _increment_pending_gates(ticket_id)

    return {"ok": True, "gate_id": gate_id, "expires_at": expires, "gate_type": gate_type}


@mcp.tool()
def resolve_gate(ticket_id: str, gate_id: str, response: str, resolved_by: str = "user") -> dict:
    """Resolve một gate — pipeline có thể tiếp tục.

    Args:
        ticket_id: Jira ticket ID
        gate_id: Gate ID trả về từ create_gate()
        response: Phản hồi của human (e.g. "approve", "request_changes: X", option đã chọn)
        resolved_by: "user" | "system" | "timeout"
    Returns:
        {"ok": bool, "gate_id": str, "response": str, "pipeline_state": str}
    """
    gate = _load_gate(ticket_id, gate_id)
    if not gate:
        return {"ok": False, "error": f"Gate '{gate_id}' không tồn tại"}

    if gate["status"] == "expired":
        return {"ok": False, "error": f"Gate '{gate_id}' đã expired. Tạo gate mới."}
    if gate["status"] in ("resolved", "cancelled"):
        return {"ok": False, "error": f"Gate '{gate_id}' đã {gate['status']} rồi"}

    gate["status"] = "resolved"
    gate["response"] = response
    gate["resolved_by"] = resolved_by
    gate["resolved_at"] = _now()

    _gate_path(ticket_id, gate_id).write_text(
        json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _decrement_pending_gates(ticket_id)

    pipeline = _load_state(ticket_id)
    return {
        "ok": True,
        "gate_id": gate_id,
        "response": response,
        "pipeline_state": pipeline.get("state", "unknown"),
    }


@mcp.tool()
def get_gate(ticket_id: str, gate_id: str) -> dict:
    """Lấy chi tiết một gate (với lazy expiry check).

    Args:
        ticket_id: Jira ticket ID
        gate_id: Gate ID
    """
    gate = _load_gate(ticket_id, gate_id)
    if not gate:
        return {"error": f"Gate '{gate_id}' không tồn tại"}
    return gate


@mcp.tool()
def get_pending_gates(ticket_id: str) -> list[dict]:
    """Lấy tất cả gates đang pending của một ticket.

    Tự động expire các gates đã quá timeout.

    Args:
        ticket_id: Jira ticket ID
    Returns:
        List of gate dicts (sorted by created_at, oldest first)
    """
    gates_dir = _gates_dir(ticket_id)
    if not gates_dir.exists():
        return []

    pending = []
    for gate_file in gates_dir.glob("*.json"):
        gate_id = gate_file.stem
        gate = _load_gate(ticket_id, gate_id)  # lazy expiry inside
        if gate.get("status") == "pending":
            pending.append(gate)

    return sorted(pending, key=lambda g: g.get("created_at", ""))


@mcp.tool()
def list_all_pending_gates() -> list[dict]:
    """Liệt kê tất cả gates pending trên mọi pipelines — dùng cho session recovery.

    Returns:
        List of {ticket_id, gate_id, gate_type, question, created_at, expires_at, pipeline_state}
        sorted by urgency (UNBLOCK first, then CONFIRM, then by age)
    """
    if not PIPELINE_ROOT.exists():
        return []

    all_pending = []
    for gates_dir in PIPELINE_ROOT.glob("*/gates"):
        ticket_id = gates_dir.parent.name
        for gate_file in gates_dir.glob("*.json"):
            gate = _load_gate(ticket_id, gate_file.stem)
            if gate.get("status") == "pending":
                all_pending.append({
                    "ticket_id": ticket_id,
                    "gate_id": gate["gate_id"],
                    "gate_type": gate["gate_type"],
                    "question": gate["question"],
                    "created_at": gate.get("created_at", ""),
                    "expires_at": gate.get("expires_at", ""),
                    "pipeline_state": gate.get("pipeline_state_at_creation", ""),
                })

    # Sort: UNBLOCK > CONFIRM > APPROVE > REVIEW > CHOICE, then by age (oldest first)
    urgency = {"UNBLOCK": 0, "CONFIRM": 1, "APPROVE": 2, "REVIEW": 3, "CHOICE": 4}
    all_pending.sort(key=lambda g: (urgency.get(g["gate_type"], 9), g["created_at"]))
    return all_pending


@mcp.tool()
def cancel_gate(ticket_id: str, gate_id: str, reason: str = "") -> dict:
    """Huỷ một gate (khi không còn cần thiết nữa).

    Args:
        ticket_id: Jira ticket ID
        gate_id: Gate ID
        reason: Lý do huỷ
    """
    gate = _load_gate(ticket_id, gate_id)
    if not gate:
        return {"ok": False, "error": f"Gate '{gate_id}' không tồn tại"}
    if gate["status"] not in ("pending",):
        return {"ok": False, "error": f"Chỉ có thể cancel gate đang pending, not '{gate['status']}'"}

    gate["status"] = "cancelled"
    gate["resolved_by"] = "system"
    gate["resolved_at"] = _now()
    if reason:
        gate["cancel_reason"] = reason

    _gate_path(ticket_id, gate_id).write_text(
        json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _decrement_pending_gates(ticket_id)
    return {"ok": True, "gate_id": gate_id}


# ── Cost Tracking ─────────────────────────────────────────────────────────────

DEFAULT_BUDGET_TOKENS = int(os.getenv("MORAI_BUDGET_TOKENS", "200000"))

# Approximate cost per 1M tokens (USD) for budget estimation
_MODEL_COST_PER_1M: dict[str, dict] = {
    "haiku":  {"input": 0.80,  "output": 4.00},
    "sonnet": {"input": 3.00,  "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
}


@mcp.tool()
def record_token_usage(
    ticket_id: str,
    skill_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    """Ghi token usage cho một skill call trong pipeline.

    Gọi sau mỗi LLM call quan trọng để track cost.

    Args:
        ticket_id: Jira ticket ID
        skill_name: Tên skill, e.g. "ba", "dev", "reviewer"
        model: "haiku" | "sonnet" | "opus"
        input_tokens: Số input tokens
        output_tokens: Số output tokens
    Returns:
        {"ok": bool, "budget_used_pct": float, "alert": str}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"ok": False, "error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    cost_data = state.setdefault("cost", {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "budget_tokens": DEFAULT_BUDGET_TOKENS,
        "by_skill": {},
        "estimated_usd": 0.0,
    })

    # Update totals
    cost_data["total_input_tokens"] += input_tokens
    cost_data["total_output_tokens"] += output_tokens

    # Update by_skill
    skill_data = cost_data["by_skill"].setdefault(skill_name, {
        "input_tokens": 0, "output_tokens": 0, "calls": 0, "model": model,
    })
    skill_data["input_tokens"] += input_tokens
    skill_data["output_tokens"] += output_tokens
    skill_data["calls"] += 1
    skill_data["model"] = model  # last model used for this skill

    # Estimate cost USD
    rates = _MODEL_COST_PER_1M.get(model, _MODEL_COST_PER_1M["sonnet"])
    call_cost = (input_tokens / 1_000_000) * rates["input"] + \
                (output_tokens / 1_000_000) * rates["output"]
    cost_data["estimated_usd"] = round(cost_data.get("estimated_usd", 0) + call_cost, 4)

    total_tokens = cost_data["total_input_tokens"] + cost_data["total_output_tokens"]
    budget = cost_data["budget_tokens"]
    used_pct = round(total_tokens / budget * 100, 1) if budget > 0 else 0

    alert = ""
    if used_pct >= 95:
        alert = "CRITICAL: Budget 95% used — pause and compress context"
    elif used_pct >= 80:
        alert = "WARNING: Budget 80% used — consider compressing old context"

    state["last_updated"] = _now()
    _save_state(ticket_id, state)

    return {"ok": True, "budget_used_pct": used_pct, "alert": alert}


@mcp.tool()
def get_pipeline_cost(ticket_id: str) -> dict:
    """Lấy cost summary của một pipeline.

    Returns:
        {total_tokens, budget_tokens, budget_used_pct, estimated_usd, by_skill, alert}
    """
    state = _load_state(ticket_id)
    if not state:
        return {"error": f"Pipeline '{ticket_id}' chưa tồn tại"}

    cost = state.get("cost", {})
    if not cost:
        return {"ticket_id": ticket_id, "total_tokens": 0, "budget_used_pct": 0.0, "by_skill": {}}

    total = cost.get("total_input_tokens", 0) + cost.get("total_output_tokens", 0)
    budget = cost.get("budget_tokens", DEFAULT_BUDGET_TOKENS)
    used_pct = round(total / budget * 100, 1) if budget > 0 else 0

    alert = ""
    if used_pct >= 95:
        alert = "CRITICAL: Budget 95% used"
    elif used_pct >= 80:
        alert = "WARNING: Budget 80% used"

    return {
        "ticket_id": ticket_id,
        "total_input_tokens": cost.get("total_input_tokens", 0),
        "total_output_tokens": cost.get("total_output_tokens", 0),
        "total_tokens": total,
        "budget_tokens": budget,
        "budget_used_pct": used_pct,
        "estimated_usd": cost.get("estimated_usd", 0.0),
        "by_skill": cost.get("by_skill", {}),
        "alert": alert,
    }


@mcp.tool()
def get_cost_summary_all() -> list[dict]:
    """Lấy cost summary của tất cả pipelines — dùng để phân tích which skills are expensive.

    Returns:
        List sorted by total_tokens desc
    """
    if not PIPELINE_ROOT.exists():
        return []

    summaries = []
    for state_file in PIPELINE_ROOT.glob("*/state.json"):
        s = json.loads(state_file.read_text(encoding="utf-8"))
        cost = s.get("cost", {})
        total = cost.get("total_input_tokens", 0) + cost.get("total_output_tokens", 0)
        summaries.append({
            "ticket_id": s.get("ticket_id"),
            "state": s.get("state"),
            "total_tokens": total,
            "estimated_usd": cost.get("estimated_usd", 0.0),
            "budget_used_pct": round(total / cost.get("budget_tokens", DEFAULT_BUDGET_TOKENS) * 100, 1)
            if total > 0 else 0.0,
        })

    return sorted(summaries, key=lambda x: x["total_tokens"], reverse=True)


if __name__ == "__main__":
    mcp.run()
