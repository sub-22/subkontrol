"""Morai Events MCP server — event bus, subscription registry, scheduled triggers."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-events")

EVENTS_ROOT = Path(os.getenv("MORAI_MEMORY_PATH", ".morai/memory")).parent / "events"
SUBSCRIPTIONS_FILE = EVENTS_ROOT / "subscriptions.json"
EVENT_LOG_FILE = EVENTS_ROOT / "event_log.jsonl"

# ── Known event types ──────────────────────────────────────────────────────────

EVENT_TYPES = {
    # External: GitHub webhooks
    "github.pr_opened": "PR được mở — trigger reviewer",
    "github.pr_merged": "PR được merge — trigger reflect",
    "github.pr_closed": "PR bị close/reject",
    "github.test_failed": "CI test fail — trigger incident L3",
    "github.push": "Push lên branch",
    # External: Jira webhooks
    "jira.ticket_created": "Ticket mới được tạo",
    "jira.ticket_in_progress": "Ticket chuyển sang In Progress — trigger ba→pm",
    "jira.ticket_done": "Ticket done",
    # Scheduled (via CronCreate)
    "cron.daily_morning": "Mỗi ngày 8:00 — check blocked pipelines",
    "cron.weekly_friday": "Thứ Sáu mỗi tuần — trigger kaizen",
    "cron.sprint_end": "Cuối sprint — trigger evolve",
    # Internal: Morai-generated
    "internal.tasks_completed_10": "10 tasks hoàn thành — trigger reflect",
    "internal.same_error_x3": "Cùng lỗi lặp 3 lần — escalate human",
    "internal.pipeline_blocked": "Pipeline bị block — notify Dev",
    "internal.pipeline_idle_2d": "Pipeline idle 2 ngày — ping Dev",
    "internal.budget_warning_80": "Budget 80% used — compress context",
    "internal.budget_critical_95": "Budget 95% used — pause pipeline",
}

# Default subscriptions — pre-configured at install time
DEFAULT_SUBSCRIPTIONS = [
    {
        "subscription_id": "default-001",
        "event_type": "github.pr_opened",
        "handler": "/morai:reviewer",
        "filter": {},
        "description": "Auto-trigger reviewer khi PR được mở",
        "active": True,
    },
    {
        "subscription_id": "default-002",
        "event_type": "github.test_failed",
        "handler": "/morai:incident",
        "filter": {"severity": "L3"},
        "description": "Auto-trigger incident khi CI fail",
        "active": True,
    },
    {
        "subscription_id": "default-003",
        "event_type": "github.pr_merged",
        "handler": "/morai:reflect",
        "filter": {},
        "description": "Auto-trigger reflect sau khi PR merge",
        "active": True,
    },
    {
        "subscription_id": "default-004",
        "event_type": "internal.tasks_completed_10",
        "handler": "/morai:reflect",
        "filter": {},
        "description": "Auto-reflect sau 10 tasks hoàn thành",
        "active": True,
    },
    {
        "subscription_id": "default-005",
        "event_type": "cron.weekly_friday",
        "handler": "/morai:kaizen",
        "filter": {},
        "description": "Weekly kaizen mỗi thứ Sáu",
        "active": True,
    },
    {
        "subscription_id": "default-006",
        "event_type": "cron.sprint_end",
        "handler": "/morai:evolve",
        "filter": {},
        "description": "Evolve sau mỗi sprint",
        "active": True,
    },
    {
        "subscription_id": "default-007",
        "event_type": "internal.pipeline_blocked",
        "handler": "notify_dev",
        "filter": {},
        "description": "Notify Dev khi pipeline bị block",
        "active": True,
    },
    {
        "subscription_id": "default-008",
        "event_type": "jira.ticket_in_progress",
        "handler": "/morai:ba",
        "filter": {},
        "description": "Auto-trigger BA khi ticket In Progress (nếu Jira configured)",
        "active": False,  # disabled by default — needs Jira configured
    },
]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _ensure_dirs() -> None:
    EVENTS_ROOT.mkdir(parents=True, exist_ok=True)


def _load_subscriptions() -> list[dict]:
    if not SUBSCRIPTIONS_FILE.exists():
        _ensure_dirs()
        _save_subscriptions(DEFAULT_SUBSCRIPTIONS)
        return DEFAULT_SUBSCRIPTIONS
    return json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))


def _save_subscriptions(subs: list[dict]) -> None:
    _ensure_dirs()
    SUBSCRIPTIONS_FILE.write_text(json.dumps(subs, indent=2, ensure_ascii=False), encoding="utf-8")


def _next_sub_id(subs: list[dict]) -> str:
    existing = [s["subscription_id"] for s in subs if s["subscription_id"].startswith("sub-")]
    return f"sub-{len(existing) + 1:03d}"


def _append_event_log(event: dict) -> None:
    _ensure_dirs()
    with EVENT_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ── Tools ──────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_event_types() -> dict[str, str]:
    """Liệt kê tất cả event types được hỗ trợ."""
    return EVENT_TYPES


@mcp.tool()
def subscribe(
    event_type: str,
    handler: str,
    filter_conditions: dict | None = None,
    description: str = "",
) -> dict:
    """Đăng ký một handler cho một event type.

    Args:
        event_type: Event type từ list_event_types()
        handler: Skill command, e.g. "/morai:reviewer" hoặc "notify_dev"
        filter_conditions: Điều kiện lọc, e.g. {"branch_prefix": "feat/", "ticket_id": "PROJ-123"}
        description: Mô tả subscription này làm gì
    Returns:
        {"ok": bool, "subscription_id": str}
    """
    if event_type not in EVENT_TYPES:
        return {
            "ok": False,
            "error": f"Unknown event_type '{event_type}'. Call list_event_types() để xem options.",
        }

    subs = _load_subscriptions()
    sub_id = _next_sub_id(subs)
    new_sub = {
        "subscription_id": sub_id,
        "event_type": event_type,
        "handler": handler,
        "filter": filter_conditions or {},
        "description": description,
        "active": True,
        "created_at": _now(),
    }
    subs.append(new_sub)
    _save_subscriptions(subs)
    return {"ok": True, "subscription_id": sub_id}


@mcp.tool()
def unsubscribe(subscription_id: str) -> dict:
    """Huỷ một subscription.

    Args:
        subscription_id: ID từ subscribe() hoặc list_subscriptions()
    """
    subs = _load_subscriptions()
    for sub in subs:
        if sub["subscription_id"] == subscription_id:
            sub["active"] = False
            _save_subscriptions(subs)
            return {"ok": True, "subscription_id": subscription_id}
    return {"ok": False, "error": f"Subscription '{subscription_id}' không tồn tại"}


@mcp.tool()
def get_subscriptions(event_type: str = "", active_only: bool = True) -> list[dict]:
    """Lấy danh sách subscriptions.

    Args:
        event_type: Filter theo event type (để trống = tất cả)
        active_only: Chỉ lấy active subscriptions
    """
    subs = _load_subscriptions()
    if active_only:
        subs = [s for s in subs if s.get("active", True)]
    if event_type:
        subs = [s for s in subs if s["event_type"] == event_type]
    return subs


@mcp.tool()
def publish(
    event_type: str,
    payload: dict | None = None,
    source: str = "internal",
) -> dict:
    """Publish một event — tìm tất cả subscriptions match và trả về handlers cần trigger.

    Args:
        event_type: Event type
        payload: Event data (pr_number, ticket_id, branch, v.v.)
        source: Nguồn event: "github" | "jira" | "internal" | "cron"
    Returns:
        {"ok": bool, "event_id": str, "handlers_to_trigger": list[dict]}
    """
    payload = payload or {}

    event_id = f"evt-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "source": source,
        "payload": payload,
        "published_at": _now(),
    }
    _append_event_log(event)

    # Find matching active subscriptions
    subs = _load_subscriptions()
    handlers = []
    for sub in subs:
        if not sub.get("active", True):
            continue
        if sub["event_type"] != event_type:
            continue
        # Check filter conditions
        f = sub.get("filter", {})
        match = True
        for key, val in f.items():
            if key == "branch_prefix":
                if not payload.get("branch", "").startswith(val):
                    match = False
                    break
            elif key == "ticket_id":
                if payload.get("ticket_id") != val:
                    match = False
                    break
            elif payload.get(key) != val:
                match = False
                break
        if match:
            handlers.append(
                {
                    "subscription_id": sub["subscription_id"],
                    "handler": sub["handler"],
                    "description": sub.get("description", ""),
                }
            )

    return {
        "ok": True,
        "event_id": event_id,
        "event_type": event_type,
        "handlers_to_trigger": handlers,
    }


@mcp.tool()
def get_event_log(limit: int = 20, event_type: str = "") -> list[dict]:
    """Lấy recent events từ event log.

    Args:
        limit: Số events gần nhất
        event_type: Filter theo event type (để trống = tất cả)
    """
    if not EVENT_LOG_FILE.exists():
        return []

    lines = EVENT_LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
    events = [json.loads(line) for line in lines if line.strip()]

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]

    return events[-limit:]


@mcp.tool()
def get_cron_setup_guide() -> str:
    """Hướng dẫn setup scheduled events bằng Claude Code CronCreate tool.

    Returns:
        Markdown guide với CronCreate commands cho từng scheduled event.
    """
    return """# Scheduled Events Setup — CronCreate Guide

Dùng Claude Code's CronCreate tool để schedule Morai's auto-triggers.

## Weekly Kaizen (Friday 9:00 AM)
```
CronCreate(
  schedule="0 9 * * 5",
  prompt="/morai:kaizen weekly trigger"
)
```

## Daily Pipeline Check (8:00 AM every day)
```
CronCreate(
  schedule="0 8 * * *",
  prompt="check blocked pipelines and gates, notify dev if any"
)
```

## Sprint End Evolve (Friday 5:00 PM, bi-weekly)
```
CronCreate(
  schedule="0 17 * * 5/2",
  prompt="/morai:evolve sprint end"
)
```

## Daily Memory Archive (midnight)
```
CronCreate(
  schedule="0 0 * * *",
  prompt="run morai-memory archive_old_episodes to clean up episodes older than 90 days"
)
```

## Notes
- CronCreate là built-in tool của Claude Code — không cần setup thêm
- Schedule format: cron expression (minute hour day month weekday)
- Prompt: được pass vào Morai như normal user message
- Xem active crons: CronList()
- Xoá cron: CronDelete(id)
"""


if __name__ == "__main__":
    mcp.run()
