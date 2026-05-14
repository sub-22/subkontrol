# Code Rules

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
