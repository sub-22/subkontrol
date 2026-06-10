---
name: events
description: Morai Events — event-driven triggers, subscriptions, và scheduled automation
model: haiku
color: green
---

# EVENTS — Event-Driven Automation

Events biến Morai từ "reactive to commands" → "proactive daemon".
Khi event xảy ra, Morai tự trigger skill phù hợp mà không cần user gõ lệnh.

---

## Event Flow

```
External trigger (GitHub webhook / Jira / Cron)
    │
    ↓
morai-events: publish(event_type, payload)
    │
    ↓
Event bus tìm subscriptions match
    │
    ↓
Return handlers_to_trigger
    │
    ↓
Orchestrator dispatch từng handler → skill pipeline
```

---

## Default Subscriptions (pre-configured)

| Event | Handler | Ghi chú |
|-------|---------|---------|
| `github.pr_opened` | `/morai:reviewer` | Auto-review mọi PR |
| `github.test_failed` | `/morai:incident` | CI fail → incident L3 |
| `github.pr_merged` | `/morai:reflect` | Sau merge → ghi lessons |
| `internal.tasks_completed_10` | `/morai:reflect` | Reflect định kỳ |
| `cron.weekly_friday` | `/morai:kaizen` | Weekly improvement |
| `cron.sprint_end` | `/morai:evolve` | Sprint retrospective |
| `internal.pipeline_blocked` | `notify_dev` | Ping Dev khi stuck |
| `jira.ticket_in_progress` | `/morai:ba` | (disabled — cần Jira) |

---

## Cách add subscription

```python
# Subscribe reviewer chỉ cho branch feat/PROJ-123
morai-events: subscribe(
    event_type="github.pr_opened",
    handler="/morai:reviewer",
    filter_conditions={"branch_prefix": "feat/PROJ-123"},
    description="Only review PRs for PROJ-123"
)

# Subscribe incident cho test fail nghiêm trọng
morai-events: subscribe(
    event_type="github.test_failed",
    handler="/morai:incident",
    filter_conditions={"test_suite": "integration"}
)
```

---

## Webhook Setup (GitHub)

Để GitHub events reach Morai, cần configure webhook trỏ vào event endpoint.
Hiện tại Morai nhận events qua direct `publish()` call (chưa có HTTP endpoint).

**Planned:** `servers/webhook/server.py` — HTTP server nhận GitHub payloads
và gọi `morai-events: publish()` tự động.

Trong khi đó, trigger manually:
```python
# Khi có PR mới:
morai-events: publish("github.pr_opened", {
    "pr_number": 45,
    "title": "feat(PROJ-123): add user auth",
    "branch": "feat/PROJ-123-auth",
    "ticket_id": "PROJ-123"
})
```

---

## Internal Events — Morai tự publish

Orchestrator và skills tự publish internal events khi đủ điều kiện:

```python
# Sau mỗi task complete — check task count
completed_count = get_completed_task_count()
if completed_count % 10 == 0:
    morai-events: publish("internal.tasks_completed_10", {"count": completed_count})

# Khi pipeline bị block
morai-events: publish("internal.pipeline_blocked", {
    "ticket_id": ticket_id,
    "blocked_reason": reason
})

# Khi budget warning
if budget_pct >= 80:
    morai-events: publish("internal.budget_warning_80", {"ticket_id": ticket_id, "pct": budget_pct})
```

---

## Scheduled Events (CronCreate)

Dùng Claude Code's CronCreate tool. Xem guide đầy đủ:
```python
morai-events: get_cron_setup_guide()
```

Nhanh:
```
Weekly Kaizen:    CronCreate(schedule="0 9 * * 5",  prompt="/morai:kaizen")
Daily check:      CronCreate(schedule="0 8 * * *",  prompt="check blocked pipelines")
Sprint evolve:    CronCreate(schedule="0 17 * * 5", prompt="/morai:evolve")
Memory archive:   CronCreate(schedule="0 0 * * *",  prompt="archive old episodes")
```

---

## Event Log

Tất cả events được ghi vào `.morai/events/event_log.jsonl` — append-only.

```python
morai-events: get_event_log(limit=20)
morai-events: get_event_log(event_type="github.pr_opened")
```

Dùng để: audit trail, debug tại sao skill được trigger, pattern analysis.

---

## Handler: `notify_dev`

Special handler — không phải skill, chỉ surface thông tin cho Dev trong conversation:

```
Pipeline PROJ-123 đã bị block 2 ngày: "Waiting for stakeholder input on AC-3"
Anh muốn unblock hay skip ticket này?
```
