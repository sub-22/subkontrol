## Summary

Ticket: [PROJ-XXX] — [Tên ticket]
Task: [TASK-N] — [Tên task]

[Mô tả ngắn: refactor cái gì, từ pattern nào sang pattern nào]

## Motivation

[Tại sao cần refactor — tech debt, performance, maintainability, prerequisite cho feature sắp tới]

## What changed

- [Module / file chính bị thay đổi]
- [Pattern cũ → pattern mới]

## What did NOT change

[Behavior bên ngoài không đổi — reassure reviewer không có logic change ẩn]

## How to verify no regression

- [ ] Existing tests pass
- [ ] [Manual check nếu cần]

## Impact

| Area | Affected | Detail |
|------|----------|--------|
| Modules / services | Yes / No | [Files/modules bị rename, move, xóa] |
| Public API / exports | Yes / No | [Interface thay đổi? Consumers cần update?] |
| Performance | Yes / No | [Cải thiện hay tệ hơn? Benchmark?] |
| Test coverage | Yes / No | [Coverage thay đổi không?] |

## Notes

[Scope cố tình giới hạn ở đâu — refactor còn lại để PR sau]
