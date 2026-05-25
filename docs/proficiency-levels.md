# 7 AI Proficiency Levels

Framework đánh giá mức độ sử dụng AI của từng thành viên trong team.

## Overview

| Level | Tên | Mô tả ngắn |
|-------|-----|-----------|
| 1 | Ad-hoc | Dùng AI tuỳ tiện, không kiểm soát |
| 2 | Basic | Task nhỏ, cá nhân |
| 3 | Context-aware | Cung cấp context, lên kế hoạch, verify kết quả |
| 4 | Workflow | Có workflow chuẩn hoá, tái sử dụng được |
| 5 | Tool-integrated | Kết nối với tools thực tế (Jira, repo, DB) |
| 6 | AI Operator | Orchestrate AI cho project lớn, multi-phase |
| 7 | System Designer | Autonomous loop với guardrails |

> **Mục tiêu team:** đưa toàn bộ đến Level 4 — Workflow.

---

## Chi tiết từng level

### Level 1 — Ad-hoc

**Dấu hiệu:** prompt vague, copy-paste output mà không check, hỏi cùng một câu nhiều lần.

**Ví dụ:** paste error log + "fix it for me".

Phải vượt qua level này trước khi thảo luận về chuẩn hoá.

---

### Level 2 — Basic

**Dấu hiệu:** dùng AI giải thích code, viết draft text, refactor nhỏ. Đọc output trước khi dùng.

**Ví dụ:** "Giải thích hàm `calculateTotal()`, đề xuất tên biến rõ hơn."

Hầu hết Dev hiện tại đang ở level này.

---

### Level 3 — Context-aware

**Dấu hiệu:** cung cấp đủ context, yêu cầu AI lên plan trước khi thay đổi bất cứ thứ gì, hỏi về assumptions + edge cases + risks, verify output bằng tests.

**Ví dụ:** "Checkout chậm trên mobile. Đừng thay đổi API. Đọc `checkout.tsx`, list 2–3 nguyên nhân có thể, đề xuất fix plan và tests cần verify — chưa cần viết code."

**Target cá nhân:** mọi Dev nên đạt level này.

---

### Level 4 — Workflow

**Dấu hiệu:** có CLAUDE.md, slash commands, checklists, templates tái sử dụng. Cập nhật workflow khi vấn đề lặp lại.

**Ví dụ:** dùng `/morai:reviewer` → tạo PR theo template → handoff cho QA.

**Đây là level mục tiêu cho toàn team.**

---

### Level 5 — Tool-integrated

**Dấu hiệu:** dùng MCP/tool integration để đọc Jira, repo, docs. Read/write permissions được scope rõ ràng. Risky actions phải được approve trước.

**Ví dụ:** AI đọc ticket SK-42 → mở file liên quan → tạo draft PR → update Jira sau khi user approve.

Áp dụng khi team đã ổn định ở Workflow level.

---

### Level 6 — AI Operator

**Dấu hiệu:** orchestrate AI cho project lớn multi-phase, dùng sub-agents (research/implement/review/test), aggregate kết quả trước khi merge.

**Ví dụ:** pipeline loyalty point với 4 sub-agents chạy song song + aggregation sau mỗi wave.

Phù hợp cho Tech Lead / Architect. **Đây là level Morai đang hoạt động.**

---

### Level 7 — System Designer

**Dấu hiệu:** thiết kế autonomous loop với guardrails — PRD, AC, max iterations, stop conditions, audit logs, scope limits, human gates.

**Ví dụ:** "Gen tests cho payment module, tối đa 5 attempts, không deploy, không sửa schema, dừng khi phát hiện security finding."

Mục tiêu dài hạn — chỉ thực hiện khi team đã ở Level 5+.

---

## Cách đánh giá

Một người đạt Level N khi:
- Thể hiện ≥ 3/4 dấu hiệu của level đó **VÀ**
- Đã đạt level dưới (không skip)

**Cadence:** self-assessment + peer review qua 1-1 với Tech Lead mỗi 3 tháng.
