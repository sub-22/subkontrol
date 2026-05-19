# Chunk Types — Reference

Dùng bởi `/morai:architect` (khi lập Chunk Plan) và `/morai:dev` (khi implement).

---

## Thứ tự chunk trong plan (chỉ dùng types cần thiết, bỏ qua types không áp dụng)

| Type | Thứ tự | Khi nào dùng |
|------|--------|--------------|
| `setup` | Đầu tiên (nếu cần) | Chỉ khi project chưa có test infrastructure |
| `types` | Trước logic | Interfaces, enums, structs, DTOs — những gì các chunks sau depend vào |
| `migration` | Trước logic | DB/schema changes — trước khi logic depend vào schema mới |
| `logic` | Core | Business logic và services chính |
| `ripple` | Sau logic | Update files import/call những gì logic chunk vừa thay đổi (L2) |
| `integration` | Sau ripple | Wiring: DI, routing, middleware, service registration |
| `test` | Sau integration | Test files riêng nếu không co-located với logic chunk |
| `config` | Gần cuối | ENV vars, feature flags, deployment config |
| `cleanup` | Cuối cùng | Dead code, renames, doc updates |

---

## Verify command theo chunk type

| Chunk type | Verify command | Giải thích |
|------------|----------------|------------|
| `setup` | `<TEST_CMD> --version` | Chỉ verify test framework install được |
| `types` | `<TYPE_CHECK_CMD>` | Type check toàn bộ — phát hiện type mismatch ngay |
| `migration` | `<RUN_PREFIX> migrate up && <RUN_PREFIX> migrate down` | Verify up/down đều chạy được |
| `logic` / `ripple` | `<TEST_CMD> --testPathPattern=<chunk_files>` | Scoped test — chỉ files của chunk này |
| `integration` | `<LINT_CMD> && <TYPE_CHECK_CMD> && <TEST_CMD>` | Full suite — lint + type + toàn bộ tests |
| `config` | `<TYPE_CHECK_CMD>` + kiểm tra ENV vars có trong `.env.example` | |
| `cleanup` | `<LINT_CMD> && <TEST_CMD>` | Không regression sau cleanup |

> Điền command cụ thể vào Chunk Plan, không để placeholder.
> Ví dụ: `pytest tests/services/filter_test.py -v` thay vì `<TEST_CMD scoped>`.

---

## Test focus theo chunk type

| Chunk type | Test focus tối thiểu |
|------------|----------------------|
| `setup` | Test framework khởi động được, chạy 1 dummy test pass |
| `types` | Valid shape compile; thiếu required field → compile/type error |
| `migration` | Up tạo đúng schema; Down revert sạch; Up lại idempotent |
| `config` | App parse config đúng; thiếu required ENV → startup error |
| `logic` | Happy path; null/empty input; boundary value (max/min/0); error case với exact error type |
| `ripple` | Caller truyền đúng input; response shape không đổi so với trước |
| `integration` | Full flow happy path end-to-end; tính năng lân cận không bị break |
| `cleanup` | — (behavior không đổi, full suite pass là đủ) |

---

## Impact layer theo chunk type

| Chunk type | Impact layer chịu trách nhiệm |
|------------|-------------------------------|
| `types` | L3 Contract — lock interface trước khi logic chunks chạy |
| `migration` | L3 Contract — schema change |
| `logic` | L1 Direct — core files của chunk này |
| `ripple` | L2 Ripple — tất cả callers trong L2 table |
| `integration` | L3 + L4 System — observable contract + ENV/external |
| `config` | L4 System — ENV vars, feature flags |
| `cleanup` | — |
