# Review Checklist

Dùng bởi `/morai:reviewer` (AI) và human reviewer. Gate 3 trong pipeline.

**Severity:**
- 🔴 CRITICAL — blocks merge, phải fix
- 🟠 MAJOR — nên fix trước merge
- 🟡 MINOR — improve nếu kịp
- 💡 SUGGESTION — non-blocking

---

## Common (mọi platform)

### Context — đọc trước khi review diff

- [ ] Đọc spec (`specs/<id>.md`) để hiểu intent
- [ ] Đọc design doc (`designs/<id>-detail.md`) nếu có
- [ ] Hiểu "why" của change, không chỉ "what"

### Logic

- [ ] Code meet tất cả AC trong spec
- [ ] Không có off-by-one / boundary bugs
- [ ] Edge cases từ spec/analyze được handle
- [ ] Error paths không bị swallow silently
- [ ] Concurrency / race conditions được xem xét (khi áp dụng)

### Tests

- [ ] Tests mới meaningful — không chỉ snapshot, không always-pass
- [ ] Coverage: happy path + edge case + negative
- [ ] Mocks phù hợp — không mock quá nhiều (mock everything = fake test)
- [ ] Tests có thể fail — không có empty test body

### Conventions

- [ ] Naming nhất quán với codebase
- [ ] Không có abstraction mới trừ khi cần thiết
- [ ] Không duplicate logic đã có (DRY ở mức hợp lý)
- [ ] Comments giải thích WHY, không phải WHAT

### Diff size

- [ ] Diff ≤ 1000 lines — nếu lớn hơn, suggest tách PR
- [ ] Không có unrelated refactor trong PR này
- [ ] Không có leftover debug code, commented-out code, junk files

### Security & Data

- [ ] Không có hardcoded credentials, API keys, secrets
- [ ] Input validation tại boundaries (user input, external API)
- [ ] Permission checks không bị bypass
- [ ] PII / sensitive data không bị log ra ngoài

### Performance

- [ ] Không có N+1 queries
- [ ] DB indexes phù hợp với queries mới
- [ ] Heavy I/O chạy async / batching khi cần

---

## Platform-Specific

> Morai tự detect tech stack từ project files trước khi review.
> Chỉ apply section tương ứng với platform được detect.

### Python

- [ ] Không dùng `pickle`/`yaml.load()` với untrusted input (RCE risk)
- [ ] Không có mutable default arguments (`def f(x=[])`)
- [ ] Không có blocking calls trong async context (`time.sleep` trong `async def`)
- [ ] ORM queries không có N+1 (lazy loading trong loop)
- [ ] `subprocess` calls có input sanitization

### Go

- [ ] Không có goroutine leaks (goroutine khởi động nhưng không có exit path)
- [ ] Không dùng `fmt.Sprintf` để build SQL / shell commands
- [ ] Dùng `crypto/rand` cho random cryptographic, không phải `math/rand`
- [ ] Context propagation đúng — không drop context ở giữa call chain
- [ ] Error wrapping rõ ràng (`fmt.Errorf("... %w", err)`)

### Node.js / TypeScript

- [ ] Không có prototype pollution (`obj[userInput] = value`)
- [ ] Unhandled promise rejections được catch
- [ ] JWT: verify signature đúng, không chỉ decode
- [ ] `helmet` middleware được dùng cho Express APIs
- [ ] Không có `eval()` hoặc `new Function()` với user input

### Frontend (React/Vue/Angular)

- [ ] Không có XSS: `dangerouslySetInnerHTML`, `v-html` với user content
- [ ] Re-render không bị trigger thừa (missing deps trong useEffect, wrong memo)
- [ ] Bundle size không tăng bất thường (lazy load khi cần)
- [ ] Stale closure trong event handlers / async callbacks

### Java / Spring

- [ ] Thread safety — shared state có được sync đúng không?
- [ ] Spring layering — business logic không nằm trong Controller
- [ ] JPA: không có N+1 (EAGER fetch trong loop), dùng `@EntityGraph` khi cần
- [ ] Không dùng `BinaryFormatter` / Java serialization với untrusted data

### PHP

- [ ] Không có LFI/RFI: `include`/`require` với user input
- [ ] Không dùng loose comparison (`==` thay vì `===`) với type-sensitive checks
- [ ] `unserialize()` không nhận untrusted input
- [ ] Eloquent: không có N+1 (eager load với `with()`)

---

## AI Review Output Format

```
[SUMMARY]
- Overall: APPROVE | REQUEST CHANGES | NEEDS DISCUSSION
- AC coverage: X/Y ACs implemented
- Test coverage: adequate / insufficient / [X gaps noted]
- Platform: [detected platform]

[CRITICAL — blocks merge]
🔴 [file:line] — mô tả issue và tại sao critical

[MAJOR — nên fix]
🟠 [file:line] — mô tả issue

[MINOR]
🟡 [file:line] — mô tả suggestion

[SUGGESTIONS]
💡 [file:line] — optional improvement

[FILES REVIEWER NÊN XEM KỸ]
- src/foo.py:42-89 — lý do cần xem kỹ
```

Nếu có CRITICAL → fix trước khi merge. Pipeline bị block.
MAJOR → hiển thị nhưng không block (trừ khi strict mode được config).
