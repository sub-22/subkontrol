# Analyze Quality Gate

> Checklist để verify output của `/morai:ba` trước khi sang Architect/PM.
> Reviewer: Dev tự-check, Tech Lead, hoặc AI trước khi handoff.

---

## Quality Gate Checklist

| #  | Tiêu chí | Pass? | Evidence | Note |
|----|----------|-------|----------|------|
| 1  | Input classification rõ ràng — ghi rõ inputs nào có và thiếu | Yes/No | Metadata section | |
| 2  | Facts không chứa assumptions — chỉ thông tin từ input thực tế | Yes/No | Facts section | |
| 3  | Mỗi assumption có lý do và risk nếu assumption sai | Yes/No | Assumptions section | |
| 4  | Open questions có owner rõ (BA/PO/Dev/QA/Stakeholder) | Yes/No | Open Questions | |
| 5  | Blocking questions được mark `Blocking = Yes` | Yes/No | Open Questions | |
| 6  | Scope được định nghĩa rõ — in-scope và out-of-scope | Yes/No | Scope section | |
| 7  | Out-of-scope có ít nhất 1 item cụ thể | Yes/No | Scope section | |
| 8  | AC có ít nhất 3 testable criteria (Given/When/Then hoặc checklist cụ thể) | Yes/No | AC section | |
| 9  | Mỗi AC có priority và testable flag | Yes/No | AC section | |
| 10 | Business rules tách riêng khỏi AC | Yes/No | Business Rules | |
| 11 | Edge cases gồm ít nhất 3 scenario (empty state, max limit, permission boundary) | Yes/No | Edge Cases | |
| 12 | Risks có ít nhất 2 entries với severity | Yes/No | Risks section | |
| 13 | Readiness status nhất quán với blocking questions | Yes/No | Readiness section | |
| 14 | Status không phải `READY_FOR_DESIGN` khi vẫn còn blocking question | Yes/No | Readiness section | |
| 15 | Output không chứa technical design (API schema, DB schema, UI components) | Yes/No | Full doc | |
| 16 | Output không chứa implementation plan hoặc chunk plan | Yes/No | Full doc | |
| 17 | Handoff note đủ để Architect/Dev bắt đầu (confirmed reqs, constraints, risks) | Yes/No | Handoff Note | |
| 18 | Ngôn ngữ nhất quán trong toàn doc — không mix tiếng Việt/Anh tùy tiện | Yes/No | Full doc | |
| 19 | Readiness status dùng đúng enum: `READY_FOR_DESIGN` / `NEED_CLARIFY` / `BLOCKED` | Yes/No | Readiness section | |
| 20 | Metadata đầy đủ (ticket ID, date, status, input type) | Yes/No | Metadata section | |

---

## Pass Threshold

| Kết quả | Điều kiện |
|---------|----------|
| ✅ **Pass** | Tất cả 20 tiêu chí pass |
| ⚠️ **Pass with note** | 1–2 tiêu chí non-blocking fail, ghi rõ lý do; không có tiêu chí blocking nào fail |
| 🚫 **Fail** | Bất kỳ tiêu chí blocking nào fail |

---

## Blocking Criteria — auto-Fail nếu vi phạm

| # | Tại sao blocking |
|---|-----------------|
| 3  | Assumption không có risk → không đánh giá được impact nếu assumption sai |
| 5  | Blocking question không được mark → Architect/Dev có thể proceed với assumption sai |
| 8  | AC không testable → không verify được feature khi xong |
| 13 | Readiness status sai → gây lỗi cascade cho toàn pipeline |
| 14 | READY_FOR_DESIGN dù vẫn còn blocking question → design sẽ có gap |
| 15 | Chứa technical design → vi phạm phase boundary, gây confusion cho Dev |
| 16 | Chứa implementation plan → BA không phải role làm việc này |
| 17 | Handoff note không đủ → Architect không thể bắt đầu |

> Exception cho tiêu chí #8 và #11: không blocking khi `Readiness Status = BLOCKED`
> (AC và edge cases không thể hoàn chỉnh khi spec chính còn bị block).

---

## Reviewer Sign-off

| Field | Value |
|-------|-------|
| Reviewed by | |
| Date | |
| Result | Pass / Pass with note / Fail |
| Failing criteria | |
| Note | |
