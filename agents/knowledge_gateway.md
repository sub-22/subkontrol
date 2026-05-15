---
description: Morai Knowledge Gateway — domain knowledge đã học, evolving understanding, không phải static docs
---

# KNOWLEDGE GATEWAY — Morai's Evolving Brain

## Mục đích
Những gì Morai đã học và đang biết về domain, team, và patterns.
**Khác với `docs/`** — đây là knowledge sống, cập nhật theo usage.
**Khác với `memory/episodes.md`** — đây là distilled knowledge, không phải raw log.

```
knowledge_gateway.md = "Morai biết gì về X?" (abstracted, distilled)
episodes.md          = "Morai đã gặp gì?" (raw events)
docs/                = "Reference documents cho humans"
```

## Domain Knowledge Index

### Team & Workflow
```
[Chưa có — sẽ learn qua /morai:scan và usage]
- Team size: ?
- Sprint length: ?
- Review process: ?
- Deployment cadence: ?
```

### Tech Stack Knowledge
```
[Chưa có — sẽ populate sau /morai:scan]
- Primary language: ?
- Framework: ?
- Database: ?
- Key patterns: ?
```

### User Preferences (Distilled)
```
[Link tới .morai/memory/preferences.md]
Xem: morai-memory: get_preferences()
```

### Proven Patterns (từ Reflexes)
```
[Link tới agents/reflexes.md]
Active reflexes: 13 (bootstrap)
Auto-promoted: 0 (chưa có usage data)
```

### Known Gotchas & Landmines
```
[Những thứ hay gây lỗi — populate từ episodes fail]
- Chưa có data
```

## Cách Knowledge Gateway được cập nhật

```
/morai:scan     → cập nhật Tech Stack Knowledge
/morai:evolve   → cập nhật Proven Patterns
/morai:reflect  → distill từ episodes → Known Gotchas
User feedback   → cập nhật User Preferences
```

## Quy tắc citation
Khi dùng knowledge từ đây, luôn cite source:
- `[knowledge_gateway.md — Tech Stack]`
- `[memory/preferences.md:coding_style]`
- `[reflexes.md:R-002]`

Phân biệt rõ:
- `[VERIFIED]` — đã confirm từ codebase/docs thực tế
- `[INFERRED]` — suy luận từ patterns
- `[ESTIMATED]` — chưa verify
