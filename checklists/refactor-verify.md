# Refactor-Verify Checklist — Sau GREEN Phase

Chạy sau khi verify command GREEN. Mục tiêu: improve code mà không thay đổi behavior.
Morai tự evaluate toàn bộ checklist trước khi hỏi user.

---

## KHÔNG được làm trong refactor

- [ ] Không đổi test assertions — chỉ refactor test setup/helpers
- [ ] Không thêm behavior mới — để vào chunk tiếp theo
- [ ] Không extract abstraction sớm — rule of 3: chờ đến lần xuất hiện thứ 3

---

## Code Quality

- [ ] Tên biến/hàm express intent rõ — tránh `data`, `result`, `tmp`, `obj`, `res`, `val`
- [ ] Mỗi function làm đúng 1 việc — nếu cần comment để hiểu tên → rename
- [ ] Không nesting > 3 levels — extract nếu vượt
- [ ] Magic numbers/strings → named constants
- [ ] Logic trùng lặp ≥ 3 lần → extract shared function (rule of 3)

## Test Quality

- [ ] Test names mô tả scenario rõ: `"given X, when Y, then Z"` hoặc `method(input) → output`
- [ ] Không có shared mutable state giữa các tests
- [ ] Setup trùng lặp → `beforeEach` / fixture

## Cleanup

- [ ] Xóa `console.log`, `print()`, debug code còn sót
- [ ] Xóa unused imports
- [ ] Không còn TODO từ chunk này — nếu có, ghi vào chunk tiếp theo trong progress file

---

## Instructions cho Morai

Sau GREEN phase, Morai tự evaluate checklist trên.

**Không có findings:** Báo ngắn → tiếp tục update progress file.
```
Refactor: clean — no changes needed.
```

**Có findings:** Format findings với file:line reference, rồi surface cho user:

```
🔍 Refactor findings — chunk N ([type])

[1] Ambiguous variable name
    src/services/filter.py:42  →  `data` nên đổi thành `booking_list`
    src/services/filter.py:67  →  `res` nên đổi thành `paginated_result`

[2] Magic number
    src/services/filter.py:88  →  `100` nên extract thành `MAX_PAGE_SIZE`

[3] Duplicated logic (rule of 3 chưa đủ — optional)
    src/services/filter.py:55–60 và :91–96 giống nhau
    Xuất hiện 2 lần — chưa đủ rule of 3.
```

Sau đó dùng AskUserQuestion với multi-select:
- Header: `"Refactor chunk N"`
- Question: `"Chọn refactor nào áp dụng cho chunk N ([type]):"`
- Options (tối đa 4):
  - `[1] Rename variables` — mô tả ngắn file:line
  - `[2] Extract constant` — mô tả ngắn
  - `[3] Extract helper (optional)` — kèm note "rule of 3 chưa đủ"
  - `Skip all` — giữ nguyên, tiếp tục
- multiSelect: true

Sau khi apply selected items:
1. Re-run verify command của chunk → confirm GREEN
2. Nếu verify fail sau refactor → revert refactor item đó → fix root cause → re-run
3. Update progress file: chunk → `done`
