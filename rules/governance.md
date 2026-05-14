# Governance Rules

## Classification-Driven Rule Loading
- **Trigger**: mỗi task mới bắt đầu
- **Action**: classify task type → load chỉ rules liên quan (≤5 rules)
- **Rationale**: tránh token bloat, giữ context window sạch

```
Task keywords → Rule set
"code", "implement", "fix" → code.md
"test", "QA", "verify"     → quality.md
"log", "debug", "monitor"  → observability.md
"design", "architect"      → code.md + governance.md
```

## Risk-Gated Autonomy Tiers
*(đã define trong agents/morai.md — reference ở đây)*

| Tier | Scope | Behavior |
|------|-------|----------|
| 1 — Auto | read, write code, test | Execute ngay |
| 2 — Document | new files, dependencies, commits | Execute + log |
| 3 — Block | delete, schema, security, ambiguous | Stop + confirm |

**Default khi không chắc → Tier 3.**

## State Tracking cho Artifacts
- Mỗi file quan trọng có explicit status header:
  ```
  <!-- Status: ACTIVE | ARCHIVED | DEPRECATED -->
  ```
- Deprecated file → thêm link tới replacement
- Orphan file (không ai reference) → deletion candidate

## Evidence-Based Decisions
Mọi quyết định kỹ thuật quan trọng phải cite:
1. Official docs hoặc spec
2. Precedent từ codebase (dùng RAG search)
3. Self-critique: điểm yếu của approach này là gì?

Format: `[VERIFIED: source]` hoặc `[INFERRED: reasoning]`
