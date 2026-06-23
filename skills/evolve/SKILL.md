---
description: Morai Self-Evolution — học từ episodes, promote reflexes, nâng cấp chính mình
version: 1.0.0
---

# EVOLVE — Morai Self-Evolution

Chạy skill này sau mỗi sprint hoặc khi nhận được đủ feedback.
**Kết quả:** Morai version mới với reflexes và preferences được cập nhật.

## Input
Khoảng thời gian cần review: $ARGUMENTS (e.g. "last 2 weeks", "sprint 12", để trống = all)

## Quy trình

### Phase 1 — Thu thập dữ liệu
- Dùng `morai-memory: get_episodes(limit=50)` → review recent history
- Dùng `morai-memory: get_pattern_counts()` → xem patterns nào lặp nhiều nhất
- Dùng `morai-memory: get_reflex_candidates(min_count=3)` → candidates sẵn sàng promote

### Phase 2 — Phân tích

**Tìm kiếm:**
- Patterns thành công lặp ≥3 lần → promote thành reflex
- Patterns thất bại lặp → thêm vào ANTIGRAVITY
- Preferences user đã bày tỏ → update preferences.md
- Gaps: task nào Morai hay bị stuck/hỏi nhiều lần → cần skill mới

**Tự đánh giá Morai:**
- Bao nhiêu tasks hoàn thành không cần hỏi lại? (target: >70%)
- Bao nhiêu lần dùng `[UNKNOWN]`? (nếu >20% → cần học thêm)
- Bao nhiêu reflex được trigger? (nếu <30% → reflexes chưa đủ)

### Phase 3 — Promote reflexes
Với mỗi candidate từ Phase 1:
```
morai-memory: promote_to_reflex(
  pattern=<pattern_name>,
  trigger=<khi nào trigger>,
  action=<làm gì tự động>,
  signal=<risk level>
)
```

### Phase 4 — Update preferences
Từ episodes, extract user preferences ẩn:
- Style feedback → update `coding_style.*`
- Format preference → update `documentation.*`
- Workflow patterns → update `workflow.*`

### Phase 5 — Cập nhật agents/reflexes.md
Ghi tóm tắt reflexes mới vào `agents/reflexes.md` để TIER A loading biết.

### Phase 6 — Bump version và báo cáo

Ghi vào `agents/morai.md` phần Reflex Log:
```
Version: x.y.z → x.y.(z+1)
Date: [today]
Changes: +N reflexes, +M preferences
```

Báo cáo cho user:
```markdown
## Morai Evolution Report

### Version: 1.0.x → 1.0.(x+1)

### New Reflexes Added (+N)
- R-XXX: [pattern] → [action]

### Preferences Updated
- [key]: [old] → [new]

### Improvement Metrics
- Task autonomy: X% → Y%
- Unknown rate: A% → B%

### Suggested New Skills
- [Nếu có gap cần skill mới]
```
