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
Bước 4a → morai-pipeline: list_all_pending_gates()  (gates trước pipeline state)
Bước 4b → morai-pipeline: list_pipelines(status_filter="active")
Bước 5 → Declare ready + report
```

## Bước 4a — Pending Gates (ưu tiên cao nhất)

Gọi `morai-pipeline: list_all_pending_gates()` trước khi báo pipeline state.

Nếu có pending gates → hiển thị ngay:

```markdown
## ⚠️ Pending Gates — cần Dev resolve trước khi tiếp tục

| Gate ID | Type | Question | Expires |
|---------|------|----------|---------|
| PROJ-123-gate-001 | REVIEW | Approach: TASK-1 Add auth | 2026-05-15 12:30 UTC |
| PROJ-456-gate-002 | UNBLOCK | Security BLOCK on PR #45 | 2026-05-15 17:00 UTC |

Anh muốn resolve gate nào trước?
```

Sau khi Dev resolve gate → tiếp tục pipeline từ điểm bị pause.

## Bước 4b — Tìm pipeline active

Gọi `morai-pipeline: list_pipelines(status_filter="active")` → đọc state chi tiết
của pipeline gần nhất.

```json
{
  "ticket_id": "PROJ-123",
  "state": "DEV_PARALLEL_RUNNING",
  "current_wave": 1,
  "pending_gate_count": 1
}
```

## Declaration sau khi recovery

```
Morai [Claude] — đã recall.

[Nếu có pending gates]
⚠️ 2 gates đang chờ: PROJ-123-gate-001 (REVIEW), PROJ-456-gate-002 (UNBLOCK)

[Pipeline summary]
Pipeline active: PROJ-123 | State: DEV_PARALLEL_RUNNING
Wave 1: TASK-1 (approach_ready), TASK-3 (running)
Completed: BA ✓ → PM ✓

Anh muốn resolve gates hay có việc mới?
```

## Nếu không tìm thấy pipeline active và không có pending gates

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
