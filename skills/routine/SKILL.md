---
description: Morai Routine — digest sáng. Gom backlog, PRs, pending gates, CI status → gửi Telegram + present trong session → user chọn việc.
version: 1.0.0
---

# ROUTINE — Morning Digest

Chạy đầu ngày (hoặc đầu session). Gom mọi việc đang chờ thành 1 digest gọn,
gửi Telegram, present trong session, để user duyệt và chọn việc trong ~10 phút.

**Phạm vi hiện tại: in-session** — user mở session và gọi skill này.
Always-on (cron tự chạy) cố ý chưa làm — chờ Layer 3/4 enforce xong.

## Input

`$ARGUMENTS` (optional): filter — "prs", "backlog", "ci" để chỉ lấy 1 nguồn. Để trống = full digest.

## Quy trình

### Bước 1 — Gom 4 nguồn (degraded-tolerant)

Nguồn nào unavailable → skip + note 1 dòng trong digest, KHÔNG fail cả routine.

| # | Nguồn | Tool | Lấy gì |
|---|-------|------|--------|
| 1 | **Backlog** | Theo `agents/task_fetcher.md` source resolution (REAL/LOCAL/SHADOW) | Tasks `status: todo` + `doing`, sorted by priority |
| 2 | **PRs** | `morai-git: list_open_prs()` | PR đang open, ai chờ review |
| 3 | **Gates** | `morai-pipeline: list_all_pending_gates()` | Quyết định đang chờ user |
| 4 | **CI** | `.github/workflows/` tồn tại → `gh run list --limit 3`; không có → `morai-test: run_pytest()` quick; cả hai fail → skip | Status xanh/đỏ |

### Bước 2 — Compose digest

```
🌅 Morai Routine — {YYYY-MM-DD}

📋 Backlog [📁 LOCAL]: {N} todo · {M} doing
   #1 [High] SK-101 — ...
   #2 [Medium] SK-102 — ...
   (top 5 — còn lại ghi "+K nữa")

🔀 PRs open: {N}
   #12 fix/auth-refresh — chờ review {X} ngày

🚧 Gates pending: {N}
   GATE 2 (commit) — SK-101, từ hôm qua

✅ CI: pass ({last run}) | ❌ CI: fail — {job} đỏ

→ Đề xuất hôm nay: {1-2 câu — việc gì trước, vì sao}
```

Nguồn trống → 1 dòng "✓ không có gì chờ". Digest tối đa ~20 dòng — đây là digest, không phải báo cáo.

### Bước 3 — Gửi + Present

1. `morai-telegram: send_message(digest)` — unavailable → log warning, tiếp tục
2. Present digest trong session
3. Hỏi: "Sếp muốn bắt đầu việc nào?" — **chờ user chọn, không tự start**

### Bước 4 — Record

```
morai-memory: record_episode(
  event   = "routine_digest: {N} backlog, {M} PRs, {K} gates, CI {status}",
  outcome = "success",
  lesson  = "{gì đáng chú ý — vd: PR #12 treo 3 ngày}",
  signal  = "[CERTAIN] [LOW]"
)
```

User chọn việc → route qua Intent Layer (`agents/orchestrator.md`) như request bình thường.

## Constraints

- **Read-only** — routine chỉ đọc và báo, không execute việc nào, không sửa file, không commit
- Không chạy lại trong cùng ngày trừ khi user yêu cầu rõ ("routine lại đi")
- Tổng thời gian mục tiêu < 2 phút — nguồn nào chậm quá 30s → skip + note
