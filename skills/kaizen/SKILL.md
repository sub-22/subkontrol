---
description: Morai Kaizen — weekly improvement cadence, chọn 1 pain point, measure, promote nếu đủ evidence
version: 1.0.0
---

# KAIZEN — Weekly Improvement Loop

Chạy mỗi tuần (hoặc sau mỗi sprint). Khác với `/morai:evolve` (promote reflexes từ data),
Kaizen focus vào **pain points thực tế** mà team đang cảm nhận.

## Input
Sprint/tuần cần review: $ARGUMENTS (e.g. "sprint 12", "tuần này", để trống = tuần hiện tại)

## Quy trình

### Bước 1 — Identify Pain Points
- Dùng `morai-memory: get_episodes(limit=30)` → tìm episodes có outcome "fail" hoặc "partial"
- Tìm tasks tốn > 30 phút hoặc gây > 1 bug
- Hỏi: "Tuần này điều gì tốn thời gian nhất? Điều gì gây frustration?"

Ưu tiên pain points:
```
P0: Tái phát ≥ 2 lần trong 2 tuần → promote ngay
P1: Tốn > 30 phút + có thể automate
P2: Gây bug > 1 lần
P3: Minor friction
```

### Bước 2 — Chọn 1 pain point để tackle

**Chỉ 1** — đừng ôm nhiều. Kaizen là incremental, không phải revolution.

Measure baseline:
```
Trước: tốn bao lâu? / xảy ra bao nhiêu lần? / impact là gì?
```

### Bước 3 — Thiết kế improvement

Options theo thứ tự ưu tiên:
1. **Thêm reflex** — nếu là pattern lặp lại có action rõ ràng
2. **Thêm skill** — nếu cần multi-step workflow
3. **Thêm rule** — nếu là convention cần enforce
4. **Update checklist** — nếu là bước hay bị bỏ qua
5. **Document** — nếu chỉ cần clarity

### Bước 4 — Implement nhỏ

Implement improvement nhỏ nhất có thể verify được.
Không over-engineer.

### Bước 5 — Measure after

```
Sau: tốn bao lâu? / xảy ra bao nhiêu lần?
Delta: cải thiện bao nhiêu %?
```

### Bước 6 — Promote nếu đủ evidence

```
Nếu: lặp ≥ 2 lần trong 2 tuần + improvement rõ ràng
Then: promote thành rule/skill/reflex chính thức
Else: theo dõi thêm 1 tuần nữa
```

### Bước 7 — Ghi Kaizen log

```
morai-memory: record_episode(
  event="kaizen_[topic]",
  outcome="improved|no_change|needs_more_data",
  lesson="[what was changed + measured delta]",
  signal="[CERTAIN] [LOW]"
)
```

### Bước 8 — Kaizen Report

```markdown
## Kaizen — [Sprint/Week]

### Pain Point Tackled
[Mô tả]

### Baseline vs After
- Before: [metric]
- After: [metric]
- Delta: [+X% improvement]

### Change Made
[reflex/skill/rule/doc được thêm]

### Promoted to permanent?
Yes / No (tracking thêm)

### Next week candidate
[Pain point tiếp theo để xem xét]
```
