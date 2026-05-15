---
description: Morai Init — thiết lập Morai identity vào ~/.claude/CLAUDE.md để Morai hoạt động đúng personality ở mọi project
---

# Morai Init

Thiết lập Morai identity cho máy này. Chạy một lần sau khi cài plugin.

## Quy trình

### Bước 1 — Tìm script init.sh từ plugin cache

Dùng Bash tool:
```bash
find ~/.claude/plugins/cache/morai -name "init.sh" -path "*/scripts/*" 2>/dev/null | head -1
```

Nếu không tìm được → báo lỗi:
```
Không tìm thấy Morai plugin trong cache. Sếp đã cài plugin chưa ạ?
```

### Bước 2 — Chạy script

```bash
bash <path-tìm-được-ở-bước-1>
```

Script trả về:
- `OK` → thành công
- `ALREADY_SETUP` → identity đã có
- `ERROR: ...` → lỗi, in ra cho user

### Bước 3 — Báo kết quả

Nếu `OK`:
```
Xong sếp. Morai identity đã được lưu vào ~/.claude/CLAUDE.md.
Restart Claude Code để apply — sau đó Morai sẽ hoạt động đúng ở mọi project.
```

Nếu `ALREADY_SETUP`:
```
Morai identity đã có rồi sếp, không cần chạy lại.
```
