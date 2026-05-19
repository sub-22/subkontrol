# [Ticket ID] — [Title]

## Metadata

| Field       | Value                                   |
| ----------- | --------------------------------------- |
| Ticket      | [PROJ-XXX]                              |
| Jira Link   | [URL]                                   |
| Priority    | Critical \| High \| Medium \| Low       |
| Sprint      |                                         |
| Reporter    |                                         |
| Assignee    |                                         |
| Stakeholder |                                         |
| Status      | Draft \| Review \| Approved             |
| Date        |                                         |

---

## Business Context

**Problem:** [Vấn đề hiện tại là gì? Ai đang bị ảnh hưởng và như thế nào?]

**Goal:** [Feature này giải quyết vấn đề đó bằng cách nào?]

**Success Metric:** [Đo lường thành công bằng gì? VD: tỉ lệ lỗi giảm X%, thời gian xử lý < Xs]

---

## User Stories

| # | As a       | I want to  | So that    |
| - | ---------- | ---------- | ---------- |
| 1 | [user role] | [action]  | [benefit]  |
| 2 |            |            |            |

---

## Acceptance Criteria

> Mỗi AC phải: cụ thể, đo được, không mơ hồ. QA phải viết test case được từ đây.

- [ ] **AC1:** [Điều kiện — kết quả mong đợi]
- [ ] **AC2:** [Điều kiện — kết quả mong đợi]
- [ ] **AC3:** [Điều kiện — kết quả mong đợi]

---

## Business Rules

> Các ràng buộc nghiệp vụ, logic validation, quy tắc tính toán.

| # | Rule                          | Ghi chú         |
| - | ----------------------------- | --------------- |
| 1 |                               |                 |
| 2 |                               |                 |

---

## Edge Cases & Error Handling

| Scenario                  | Expected Behavior              |
| ------------------------- | ------------------------------ |
| [Trường hợp đặc biệt 1]   | [Hệ thống phải làm gì]         |
| [Input không hợp lệ]      | [Thông báo lỗi / fallback]     |
| [Service phụ thuộc lỗi]   | [Xử lý graceful như thế nào]   |

---

## Out of Scope

> Liệt kê rõ những gì KHÔNG thuộc yêu cầu này để tránh scope creep.

- [Item 1]
- [Item 2]

---

## Non-functional Requirements

| Category    | Requirement                            |
| ----------- | -------------------------------------- |
| Performance | [VD: API response < 500ms ở p99]       |
| Security    | [VD: Cần auth, data phải mã hoá]       |
| Compliance  | [VD: Tuân theo GDPR, không lưu PII]    |
| Availability| [VD: Uptime 99.9%, có fallback]        |

*Bỏ qua nếu không có yêu cầu cụ thể.*

---

## Dependencies

| Loại              | Tên / Ticket           | Ghi chú                          |
| ----------------- | ---------------------- | -------------------------------- |
| Ticket liên quan  | PROJ-XXX               | Phải merge trước                 |
| External service  | [Service name]         | Cần API key / contract mới       |
| Team khác         | [Team name]            | Cần confirm trước khi implement  |

---

## References

- Confluence: [URL]
- Figma / Mockup: [URL]
- PRD / BRD: [URL]

---

## INVEST Validation

Per user story. Status: ✅ Pass / ⚠️ Caution / ❌ Fail (❌ bất kỳ → BLOCKED trước khi handoff Architect)

| Story | I — Independent | N — Negotiable | V — Valuable | E — Estimable | S — Small | T — Testable | Notes |
|-------|----------------|----------------|--------------|---------------|-----------|--------------|-------|
| US-1  |                |                |              |               |           |              |       |

---

## Readiness Status

```
READINESS: READY_FOR_DESIGN | NEED_CLARIFY | BLOCKED

Status    : [điền một trong 3 giá trị trên]
Lý do     : [1 câu giải thích tại sao status này]
Blocking  : [Q-1, Q-2, ... / None]
```

---

## Open Questions

| ID  | Question | Owner | Blocking? | Status |
| --- | -------- | ----- | --------- | ------ |
| Q-1 |          |       | Yes / No  | Open   |

---

## Change Log

| Date | Author | Change |
| ---- | ------ | ------ |
|      |        | Initial draft |
