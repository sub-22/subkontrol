---
description: Developer (Auto) — full automation cho simple bugs đủ điều kiện. Tự fix, test, commit, PR không cần review từng bước.
---

# Dev Agent — Auto Mode (Simple Bug Only)

Pipeline tự động hoàn toàn: phân tích → fix → test → commit → PR.

**Chỉ dùng khi BUG đủ tiêu chí bên dưới. Nếu fail bất kỳ tiêu chí nào → tự động fall back sang `/morai:dev` (guided mode) và giải thích lý do.**

## Input
Task ID hoặc mô tả bug: $ARGUMENTS

---

## ⛔ Eligibility Gate — Chạy TRƯỚC KHI làm bất cứ gì

Kiểm tra TẤT CẢ các điều kiện sau. **Tất cả phải PASS:**

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| 1 | **Bug, không phải feature** | Task type = `bug` hoặc description là fix/patch |
| 2 | **Scope ≤ 2 files** | Estimate từ spec/task description |
| 3 | **< 30 LOC thay đổi** | Estimate từ root cause analysis |
| 4 | **Root cause rõ ràng** | Không có `[UNKNOWN]` sau khi đọc task + code |
| 5 | **Có existing tests để verify** | Tìm test file liên quan trong codebase |
| 6 | **Không động vào auth/payment/user-data** | Keywords: `auth`, `jwt`, `token`, `payment`, `password`, `session`, `pii` |
| 7 | **Không phải production hotfix L1/L2** | Severity check — L1/L2 → dùng `/morai:incident` thay vì đây |

**Nếu fail bất kỳ tiêu chí nào:**
```
⚠️ Bug này không đủ điều kiện auto. Lý do: [tiêu chí nào fail].
Chuyển sang guided mode (/morai:dev). Anh confirm nhé?
```

---

## Phase 1 — Analyze

### Bước 1 — Load context
- Dùng `morai-file`: đọc task JSON, spec
- Dùng `morai-memory`: load pipeline state
- Cập nhật task `status → "in-progress"`

### Bước 2 — Root cause analysis
- Dùng `morai-rag`: search code liên quan đến bug
- Dùng `morai-git`: xem recent commits có thể gây regression
- Confirm root cause: gắn `[CERTAIN]` khi biết chắc

Nếu root cause vẫn `[UNKNOWN]` sau research → **STOP, fall back guided.**

---

## Phase 2 — Fix & Test

### Bước 3 — Implement fix
- Fix đúng root cause, không patch symptom
- Scope chặt: không sửa code ngoài 2 files đã xác định
- Không thêm feature hay cleanup không liên quan

### Bước 4 — Chạy existing tests
- Xác nhận tests pass sau fix
- Nếu tests fail → **STOP, báo Dev, không tiếp tục**

### Bước 5 — Thêm regression test
- Viết 1 test case đơn giản cover case này để không tái phát

---

## Phase 3 — Commit & PR (tự động)

### Bước 6 — Commit
- Dùng `morai-git: commit(message)` — format: `fix(<scope>): <mô tả ngắn>`
- Dùng `morai-git: push()`

### Bước 7 — Tạo PR
- Dùng template `templates/pr/bugfix.md`
- Dùng `morai-git: create_pr(title, body, base)`
- Cập nhật task: `status → "done"`, `pr_url → <url>`

### Bước 8 — Update pipeline state + Báo cáo

```
morai-memory: save_pipeline_state($TICKET_ID, {
  "current_step": "dev",
  "completed_steps": [...previous, "dev"],
  "status": "active",
  "pr_url": <pr_url>
})
```

Báo cáo cho user: root cause, fix mô tả, PR link, regression test đã thêm.

> **Slack (optional):** Nếu configured → notify reviewer.
