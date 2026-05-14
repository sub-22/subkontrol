---
description: Morai Reflect — ghi lesson learned sau task/sprint, feed vào memory
---

# REFLECT — Post-Task Learning

Chạy ngay sau khi hoàn thành một task hoặc pipeline.
**Kết quả:** Episode được ghi vào memory, patterns được track.

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
```
morai-memory: save_pipeline_state($ARGUMENTS, {
  "status": "complete",
  "current_step": "done",
  ...
})
```

### Bước 5 — Check reflex candidates
```
morai-memory: get_reflex_candidates(min_count=3)
```
Nếu có candidates → thông báo cho user:
```
💡 Pattern "[X]" đã lặp 3 lần. Chạy /morai:evolve để promote thành reflex.
```

### Bước 6 — Báo cáo ngắn

```markdown
## Reflect — [TICKET-ID]

**Outcome**: ✓ success / ⚠ partial / ✗ fail
**Duration**: [estimated]

**Went well**: ...
**To improve**: ...
**Episodes ghi**: N
**Patterns detected**: [list]
```
