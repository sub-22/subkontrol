---
description: Morai Reflect — ghi lesson learned sau task/sprint, feed vào memory và sync design repo
version: 1.1.0
---

# REFLECT — Post-Task Learning

Chạy ngay sau khi hoàn thành một task hoặc pipeline.
**Kết quả:** Episode ghi vào local memory + sync lên design repo để cả team học.

## Input
Ticket ID hoặc mô tả task vừa xong: $ARGUMENTS

## Quy trình

### Bước 1 — Đọc lại những gì đã làm
- Dùng `morai-file: read_file("specs/$ARGUMENTS.md")` nếu có
- Dùng `morai-memory: get_pipeline_state($ARGUMENTS)` nếu có
- Dùng `morai-git: get_log(max_count=5)` để xem commits

### Bước 2 — Retrospective 5 câu hỏi

1. **Went well**: Điều gì thực sự hiệu quả trong lần này?
2. **Went wrong**: Điều gì tốn thời gian hoặc gây confusion?
3. **Surprised**: Có điều gì unexpected không? Tại sao?
4. **Would do differently**: Nếu làm lại, thay đổi gì?
5. **Pattern**: Đây có phải lần đầu gặp situation này không?

### Bước 3 — Ghi episodes

Với mỗi insight quan trọng:
```
morai-memory: record_episode(
  ticket_id=$ARGUMENTS,
  event=<tên pattern ngắn gọn>,
  outcome="success|partial|fail",
  lesson=<điều học được>,
  signal=<[CERTAIN/ESTIMATED] [LOW/MED/HIGH]>,
  apply_next=<hành động cụ thể lần sau>
)
```

### Bước 4 — Update pipeline state

Dùng FSM transition (không phải save_pipeline_state):
```
morai-pipeline: get_state($ARGUMENTS)
```
Nếu state là `DEV_RUNNING` và tất cả chunks done → transition qua `DEV_COMMITTED` (cần `commit_sha` trong context).
Nếu đã là `DEV_COMMITTED` hoặc sau đó → skip.

Lấy commit SHA từ branch tương ứng:
```bash
git log --oneline -1 <branch-name>
```

### Bước 5 — Sync knowledge lên design repo (team sharing)

Tổng hợp từ Bước 1–4 để tạo 2 files cho design repo:

**summary.md** — factual, dành cho team member sau cần context:
```markdown
# {TICKET-ID} — {ticket title}

## What was built
[1-2 câu mô tả]

## Key decisions
- [Tại sao chọn X thay vì Y — lý do thực tế]

## Files changed
- `path/to/file.py` — [vai trò]

## How to verify
- [Steps để verify feature/fix vẫn hoạt động]

## Linked docs
- [spec, ADR, design page nếu có]
```

**learnings.md** — gotchas và insights, dành cho Morai và dev sau:
```markdown
# {TICKET-ID} — Learnings

## Gotchas
- [Điều gì không obvious, tốn thời gian debug]

## Edge cases
- [Case đặc biệt phải xử lý]

## Apply next time
- [Hành động cụ thể để tránh lặp lại issue]
```

Sau đó sync:
```
morai-memory: sync_ticket_knowledge(
  ticket_id=$ARGUMENTS,
  summary=<nội dung summary.md>,
  learnings=<nội dung learnings.md>
)
```

Nếu `MORAI_DESIGN_REPO` chưa set → vẫn tiếp tục, chỉ skip sync (không báo lỗi).

### Bước 6 — Tạo follow-up tasks từ findings

Scan Bước 2 để tìm action items chưa được track:
- Deferred chunks (security hoặc non-security)
- Open questions chưa trả lời
- Bugs phát hiện nhưng chưa fix
- Technical debt cần address

Với mỗi item:
```
morai-memory: record_task(
  title=<tên ngắn gọn>,
  description=<mô tả + acceptance criteria>,
  ticket_id=<ticket gốc nếu có>,
  priority="high|medium|low"
)
```
Security-related deferred items → luôn `priority="high"`.

### Bước 7 — Archive episodes cũ
```
morai-memory: archive_old_episodes(days=90)
```
Dọn episodes > 90 ngày vào archive/. Chạy mỗi lần reflect để giữ memory sạch.

### Bước 8 — Check reflex candidates
```
morai-memory: get_reflex_candidates(min_count=3)
```
Nếu có candidates → thông báo cho user:
```
Pattern "[X]" đã lặp N lần. Chạy /morai:evolve để promote thành reflex.
```

### Bước 9 — Báo cáo ngắn

```markdown
## Reflect — [TICKET-ID]

**Outcome**: ✓ success / ⚠ partial / ✗ fail
**Duration**: [estimated]

**Went well**: ...
**To improve**: ...
**Episodes ghi**: N
**Follow-up tasks created**: N (list titles)
**Episodes archived**: N
**Patterns detected**: [list]
**Design repo sync**: ✓ synced / ⚠ MORAI_DESIGN_REPO not set
```
