---
description: Morai Incident — 5-Why root cause analysis cho bugs nghiêm trọng, không chỉ fix surface
---

# INCIDENT — 5-Why Root Cause Analysis

Dùng khi: bug production, pipeline fail, security issue, data loss risk.
**Không chỉ fix** — phải tìm tận gốc để không tái phát.

## Input
Mô tả incident hoặc ticket ID: $ARGUMENTS

## Severity Classification

| Level | Định nghĩa | Response time |
|---|---|---|
| L1 — Critical | Data loss, security breach, production down | Ngay lập tức |
| L2 — High | Feature broken for all users, payment fail | < 1 giờ |
| L3 — Medium | Feature broken for some users, workaround có | < 4 giờ |
| L4 — Low | Minor bug, cosmetic | Next sprint |

## Quy trình

### Bước 1 — Triage ngay
- Classify severity (L1-L4)
- Nếu L1: notify Slack ngay, stop mọi deploys
- Dùng `morai-git: status` + `morai-git: get_log(10)` → xem recent changes
- Dùng `morai-rag: search(incident description)` → tìm related code

### Bước 2 — 5-Why Analysis

```
Symptom:      [Điều gì đang xảy ra với user?]
    Why 1 →   [Direct cause: technical failure gì?]
    Why 2 →   [Source error: code/logic sai ở đâu?]
    Why 3 →   [Detection gap: tại sao tests không catch được?]
    Why 4 →   [Process gap: tại sao review không catch được?]
    Why 5 →   [Root cause: systemic issue là gì?]
```

### Bước 3 — Fix theo tầng

```
Immediate fix:  patch symptom (ship nhanh nếu L1/L2)
Proper fix:     fix source error (trong sprint này)
Prevention:     fix detection gap (thêm test)
Process fix:    fix process gap (update checklist/reflex)
```

### Bước 4 — 85% Rule check
Tại sao technical bug này lọt qua đến production?
- Unit tests không cover case này? → thêm tests
- Reviewer bỏ qua? → thêm vào reviewer checklist
- Security check thiếu? → thêm reflex

### Bước 5 — Ghi vào Morai memory

```
morai-memory: record_episode(
  event="incident_[L1/L2/L3/L4]",
  outcome="[resolved/ongoing]",
  lesson="[root cause + prevention]",
  signal="[CERTAIN] [HIGH/CRITICAL]",
  apply_next="[concrete checklist item]"
)
```

### Bước 6 — Output Incident Report

Dùng `morai-file: write_file("incidents/<date>-<title>.md", ...)`:

```markdown
# Incident Report — [Title]
**Date**: [date]
**Severity**: L[1-4]
**Status**: Resolved / Ongoing

## Symptom
[Mô tả ngắn gọn]

## 5-Why Analysis
- Symptom: ...
- Why 1: ...
- Why 2: ...
- Why 3: ...
- Why 4: ...
- Why 5 (Root): ...

## Fix Applied
- Immediate: ...
- Proper: ...
- Prevention: ...

## Reflexes/Rules Updated
- [ ] ...
```

### Bước 7 — Notify & Close
- Dùng `morai-slack`: gửi summary + resolution
- Update `agents/context_gateway.md` — remove từ active incidents
