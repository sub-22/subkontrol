# Verify Checklist — Per Chunk (trước commit)

Chạy sau mỗi chunk GREEN. Tất cả phải pass trước khi update progress file sang `done`.

---

## Code Level

- [ ] Lint pass — command từ `.morai/knowledge/ci.json`
- [ ] Type check pass (nếu project có static analysis)
- [ ] Không có debug code: `console.log`, `print()`, `fmt.Println`, `logger.debug`, `pdb.set_trace()`
- [ ] Không có hardcoded secrets, API keys, passwords trong code
- [ ] Không có file rác: `.DS_Store`, `*.tmp`, `__pycache__/` không thuộc project

## Test Level

- [ ] Scoped verify command pass (command từ design doc, chunk này)
- [ ] Regression check pass: full test suite không có test nào bị break
- [ ] Tests có thể fail — không có test always-pass hoặc empty test body
- [ ] Không có test bị skip hoặc comment out mà không có lý do rõ

## Logic Level

- [ ] Mọi AC-ID thuộc chunk này đã được implement (kiểm tra từ progress file)
- [ ] Edge cases từ spec/analyze doc được handle (không bỏ sót silent)
- [ ] Error paths không bị swallow — có log hoặc propagate lên caller
- [ ] Không có TODO còn sót trong code của chunk này

## Integration Level (chỉ cho chunk `integration` hoặc chunk cuối)

- [ ] API contract không bị breaking change ngầm (nếu L3 Contract thay đổi)
- [ ] Migration up/down test nếu có migration chunk
- [ ] ENV vars mới đã có trong `.env.example`
- [ ] Các service/consumers phụ thuộc (L4 System) đã được notify hoặc update

---

> Nếu bất kỳ item nào fail → fix trước, không update progress sang `done`.
> Chunk `cleanup` chỉ cần Code Level + full Test suite pass.
