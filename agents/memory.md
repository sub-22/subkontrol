---
description: Morai Memory System — episodic learning, user preferences, pattern tracking
---

# MEMORY — Morai Long-Term Memory

## Kiến trúc Memory

```
.morai/memory/
├── episodes.md       ← Episodic log: sự kiện + lesson learned
├── preferences.md    ← User preferences: style, format, workflow
├── patterns.md       ← Recurring patterns đã observe
└── reflexes.md       ← Promoted reflexes (≥3 proven successes)
```

## Episodic Memory Format
Mỗi episode ghi vào `episodes.md`:

```markdown
## [DATE] [TICKET-ID] — [Event type]
- **What happened**: mô tả ngắn gọn
- **Outcome**: success / partial / fail
- **Signal**: [CERTAIN/ESTIMATED/UNKNOWN] [LOW/MED/HIGH/CRITICAL]
- **Lesson**: điều gì được học
- **Apply next time**: hành động cụ thể cho lần sau
- **Pattern count**: lần thứ N gặp pattern này
```

## User Preference Tracking
`preferences.md` lưu những gì đã học về user:

```markdown
## Coding Style
- indent: 2 spaces / 4 spaces / tabs
- naming: camelCase / snake_case / PascalCase
- comments: minimal / detailed
- test coverage: unit only / unit+integration / full

## Documentation
- spec format: bullet points / prose / table
- detail level: high-level / detailed / exhaustive
- language: English / Vietnamese / mixed

## Workflow
- approval gates: strict (always ask) / relaxed (ask only HIGH+)
- commit style: conventional commits / free form
- PR size: small + many / large + few
- review cycle: fast (24h) / thorough (72h)

## Slack Notifications
- verbosity: summary only / step-by-step / silent
- channel preference: #dev / #general / DM
```

## Pattern Recognition Rules

### Promote to REFLEX khi:
1. Pattern lặp lại ≥3 lần với cùng outcome thành công
2. Không có exception case nào
3. Không liên quan đến CRITICAL risk

### Demote reflex khi:
- Fail 1 lần → downgrade về `[FAMILIAR]`
- Fail 2 lần → downgrade về `[NOVEL]`, review lại

## Memory Operations

### Ghi memory (sau mỗi task):
```
morai-memory: record_episode(ticket_id, event, outcome, lesson)
```

### Đọc memory (khi bắt đầu task):
```
morai-memory: get_context(topic)      ← relevant episodes
morai-memory: get_preferences()       ← user style
morai-memory: get_reflexes()          ← active reflexes
```

### Update preference (khi nhận feedback):
```
morai-memory: update_preference(key, value, source="user_feedback")
```

## Memory Decay
- Episodes > 90 ngày: archive vào `.morai/memory/archive/`
- Preferences: không decay — chỉ update khi user thay đổi
- Reflexes: không decay — chỉ demote khi fail
