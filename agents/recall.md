---
description: Morai RECALL — session recovery protocol khi context bị mất
---

# RECALL — Session Recovery

## Khi nào dùng
- Bắt đầu session mới nhưng task còn dang dở
- IDE crash hoặc context window bị reset
- User nói "tiếp tục", "làm tiếp", "đang làm gì vậy"
- Không nhớ rõ đang ở bước nào trong pipeline

## Bootstrap Order (session mới — đọc theo thứ tự bắt buộc)
```
1. agents/morai.md              (identity — PROTECTED)
2. agents/recall.md             (file này — session state)
3. .morai/memory/preferences.md (user preferences)
4. rules/governance.md          (nếu cần deeper context)
→ Declare: "Morai [LLM] — online."
```

## Recovery Sequence (session bị gián đoạt — đọc theo thứ tự)
```
Bước 1 → agents/morai.md              (re-establish identity)
Bước 2 → agents/reflexes.md           (reload fast paths)
Bước 3 → .morai/memory/preferences.md (reload user context)
Bước 4 → .morai/pipeline/             (tìm pipeline đang active)
Bước 5 → Declare ready + report state
```

## Bước 4 — Tìm pipeline active

```python
# Tìm state.json gần nhất chưa complete
states = list_files(".morai/pipeline/*/state.json")
active = [s for s in states if s.status != "complete"]
```

Đọc `state.json` theo format:
```json
{
  "ticket_id": "PROJ-123",
  "current_step": "dev",
  "completed_steps": ["ba", "architect", "pm"],
  "spec_path": "specs/PROJ-123.md",
  "tasks_path": "plans/PROJ-123-tasks.md",
  "started_at": "2026-05-15T10:30:00Z",
  "last_updated": "2026-05-15T14:22:00Z",
  "blocked_reason": null
}
```

## Declaration sau khi recovery

```
Morai [Claude] — đã recall.

Pipeline active: PROJ-123
Completed: BA ✓ → Architect ✓ → PM ✓
Current: DEV (đang implement TASK-2)
Blocked: không

Tiếp tục từ TASK-2?
```

## Nếu không tìm thấy pipeline active

```
Morai [Claude] — online. Không có pipeline dang dở.
Memory loaded: [X] episodes, [Y] preferences.
Sẵn sàng nhận task mới.
```

## Sau khi recover — ghi episode
```
morai-memory: record_episode(
  event="session_recovered",
  outcome="success",
  lesson="Context recovery hoạt động tốt"
)
```
