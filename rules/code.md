# Code Rules

## CI Gate — Bắt buộc trước khi commit

**Không commit nếu CI chưa pass.** Áp dụng cho cả Dev lẫn agent/MCP.

CI commands của từng project được detect khi `/morai:scan` và lưu tại:
```
.morai/knowledge/ci.json
```

Trước mỗi commit, đọc file này và chạy đủ 4 nhóm:
```
lint          → e.g. npm run lint | golangci-lint run | uv run ruff check .
format_check  → e.g. npm run format:check | uv run ruff format --check .
typecheck     → e.g. npm run typecheck | uv run mypy . | go vet ./...
test          → e.g. npm test | go test ./... | uv run pytest | cargo test
```

**Flow bắt buộc:**
```
Code done
    ↓
Đọc .morai/knowledge/ci.json → lấy commands
    ↓
Chạy lint → format_check → typecheck → test (theo thứ tự)
    ↓ (nếu bất kỳ bước nào fail → fix, không tiếp tục)
GATE 2 — Confirm commit với Dev
    ↓
git commit
```

**Nếu `.morai/knowledge/ci.json` chưa tồn tại:** chạy `/morai:scan` trước, hoặc hỏi Dev CI commands là gì.

`--no-verify` chỉ dùng khi có lý do cụ thể được Tech Lead approve.

## Single Source of Truth per Domain
- Schema, config, constants → define 1 chỗ, import everywhere
- Không duplicate logic — nếu thấy copy-paste → extract
- Khi restructure → audit tất cả references, không để dangling imports

## File Size Limit — 10KB
- File > 10KB → signal cần tách module
- Exception: generated code, migrations, fixtures
- Ưu tiên nhiều file nhỏ + rõ ràng hơn 1 file lớn

## Modularization Principles
```
Mỗi module có 1 responsibility rõ ràng
Dependencies chỉ đi 1 chiều (no circular)
Public API nhỏ, implementation ẩn
```

## Data-Oriented Design (khi xử lý bulk data)
- Tránh heavy OOP objects cho data processing
- Optimize Big O trước khi optimize constants
- Cache locality quan trọng hơn code elegance ở hot path

## Naming Conventions (language-agnostic)
```
Files:      kebab-case (my-module.py / my-module.ts)
Classes:    PascalCase
Functions:  snake_case (Python) / camelCase (JS/TS)
Constants:  UPPER_SNAKE_CASE
Private:    _underscore prefix
```

Tên phải nói lên **intent**, không nói lên **implementation**:
- ✓ `get_active_users()` — rõ intent
- ✗ `query_db_table_users()` — leak implementation

## File Hygiene Rules
```
✗ Không tạo: file_v2.py, file_FULL.md, file_backup.json
✓ Dùng git branch để version

✗ Brain files (agents/, rules/, .morai/) không bao giờ vào src/ của target project
✓ Mỗi script có 1 mục đích rõ ràng — không multi-purpose script

✓ tmp/ chỉ là scratch pad — dọn sau mỗi sprint
✗ Không để dead code — xóa hẳn, git history giữ lại

✓ Deprecated file → thêm header: <!-- Status: DEPRECATED → see: replacement.md -->
```

## Architect Rules
- Prefer simple over clever — complexity phải justify được
- Design cho change, không design cho perfection
- Every architectural decision → ADR (dùng `/morai:architect`)
- Validate assumption với prototype nhỏ trước khi commit to big design
