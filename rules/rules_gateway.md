# Rules Gateway — Morai

## Cách load rules

### Mandatory (luôn apply)
- `rules/governance.md` — autonomy tiers, rule loading protocol
- `rules/quality.md` — 6-gate checklist, regression, 3-phase execution
- `rules/autonomy.md` — ReAct loop, no-skip policy

### Conditional (load theo task type)
| Task type | Load thêm |
|-----------|-----------|
| Viết code | `rules/code.md` |
| Debug/monitor | `rules/observability.md` |
| Review/QA | `rules/quality.md` (full) |
| Architecture | `rules/code.md` + `rules/governance.md` |

## Priority khi conflict
```
Constitution (9 Laws) > governance > quality > code > observability > autonomy
Safety > Correctness > UX > Consistency > Brevity
```

## Rule Format Convention
Mỗi rule file follow cấu trúc:
```
# [Category] Rules
## [Rule Name]
- Trigger: khi nào apply
- Action: làm gì
- Rationale: tại sao
```
