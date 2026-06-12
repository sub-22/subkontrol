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

## Phase 3 — CI Check + Commit & PR (mỗi step confirm với user)

Mỗi step dưới đây **phải hỏi user trước khi chạy**. Nếu user chọn "không" → **bỏ qua step đó, chuyển sang step tiếp theo** (không stop pipeline). Riêng lỗi thực sự (CI fail, test fail...) thì vẫn STOP như quy định ở từng step.

### Bước 6 — CI Check (bắt buộc trước commit)

```
⛔ Fix + test xong. Sếp cho em chạy CI check (lint → format → typecheck → test) không?
```

- **Có** → đọc `morai-file: read_file(".morai/knowledge/ci.json")`, chạy theo thứ tự `lint → format_check → typecheck → test`.
  - Bất kỳ bước nào fail → **STOP, fix, không tiếp tục.**
  - Nếu `ci.json` chưa tồn tại → STOP, yêu cầu chạy `/morai:scan` trước.
- **Không** → bỏ qua CI check, sang Bước 7.

### Bước 7 — Commit & Push

```
⛔ Sếp cho em commit + push không?
```

- **Có** → `morai-git: commit(message)` — format `fix(<scope>): <mô tả ngắn>`, sau đó `morai-git: push()`.
- **Không** → bỏ qua commit/push, sang Bước 8.

### Bước 8 — Tạo PR

```
⛔ Sếp cho em tạo PR không?
```

- **Có** → dùng template `templates/pr/bugfix.md`, `morai-git: create_pr(title, body, base)`, cập nhật task `status → "done"`, `pr_url → <url>`.
  - Nếu Bước 7 đã bỏ qua (chưa commit/push) → không có gì để tạo PR, báo user và tự skip step này.
- **Không** → bỏ qua tạo PR, sang Bước 9.

### Bước 9 — Update pipeline state + Notify

```
⛔ Sếp cho em update pipeline state không?
```

- **Có**:
  ```
  morai-memory: save_pipeline_state($TICKET_ID, {
    "current_step": "dev",
    "completed_steps": [...previous, "dev"],
    "status": "active",
    "pr_url": <pr_url>
  })
  ```
- **Không** → bỏ qua, sang phần notify.

```
⛔ Notify kênh nào: Slack / Telegram / Cả hai / Không gửi?
```

- **Slack** →
  ```
  morai-slack: send_message(
    channel="#dev-review",
    text="🤖 Auto-fix done: <PR URL>\n<title>\nRoot cause: <root cause ngắn>"
  )
  ```
- **Telegram** →
  ```
  morai-telegram: send_message(
    text="🤖 Auto-fix done: <PR URL>\n<title>\nRoot cause: <root cause ngắn>"
  )
  ```
- **Cả hai** → gửi cả 2 message trên.
- **Không gửi** → bỏ qua.

Nếu kênh được chọn chưa configured → bỏ qua, không báo lỗi.

Xong → sang Bước 10.

### Bước 10 — Báo cáo

Báo cáo cho user: root cause, fix mô tả, các step đã thực hiện/bỏ qua, PR link (nếu có), regression test đã thêm.
