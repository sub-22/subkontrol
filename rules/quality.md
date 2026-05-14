# Quality Rules

## 6-Gate Quality Framework
Mọi deliverable phải pass trước khi merge/ship:

```
Gate 1 — Syntax & Standards : lint pass, format đúng, no TODO
Gate 2 — Testing            : unit tests pass, coverage không giảm
Gate 3 — Architecture       : không vi phạm layer boundaries, no circular deps
Gate 4 — Security           : OWASP check (nếu có input/auth/data)
Gate 5 — Performance        : không có N+1, không có blocking ops trong hot path
Gate 6 — Integrity          : không break existing features, migration safe
```

**Judge Agent** enforce gates này tự động trong pipeline.
**85% Rule**: Gate 1–2 phải pass trước khi đến Reviewer/QA. QA chỉ test business logic.

## Regression Protection ≥ 95%
- Khi fix bug hoặc add feature → chạy full test suite
- Không được giảm coverage so với baseline
- Nếu cần xóa test → phải có approval + ghi lý do

## 3-Phase Execution Protocol
Mọi task medium+ phải follow:

```
Phase 1 — PLAN
  - Viết test cases trước khi code
  - Define acceptance criteria
  - Estimate effort + risks
  - Get approval nếu HIGH risk

Phase 2 — EXECUTE
  - Code + unit tests
  - Smoke test locally
  - Self-review (RARV verify)

Phase 3 — CLOSE
  - Quality report ngắn gọn
  - Lessons learned → /morai:reflect
  - Update context_gateway
```

## QA-Specific Rules
- QA test **behavior**, không test implementation
- Test case format: Given / When / Then
- Priority: P0 (smoke), P1 (happy path), P2 (edge), P3 (regression)
- Bug report phải có: steps to reproduce + expected + actual + severity
