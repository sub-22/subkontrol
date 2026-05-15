---
description: Morai Init — thiết lập Morai identity và hướng dẫn setup knowledge cho project
---

# Morai Init

Guided onboarding sau khi cài Morai plugin. Chạy một lần trên máy mới.

## Quy trình

### Bước 1 — Setup Morai identity

Tìm script init.sh trong plugin cache:
```bash
find ~/.claude/plugins/cache/morai -name "init.sh" -path "*/scripts/*" 2>/dev/null | head -1
```

Nếu không tìm được → báo lỗi và dừng:
```
Không tìm thấy Morai plugin trong cache. Sếp đã cài plugin chưa ạ?
```

Chạy script:
```bash
bash <path-script>
```

Nếu kết quả `ALREADY_SETUP` → thông báo identity đã có và tiếp tục sang Bước 2.

Nếu kết quả `OK` → thông báo:
```
Morai identity đã được lưu vào ~/.claude/CLAUDE.md.
Restart Claude Code để apply identity — sau đó Morai sẽ hoạt động đúng ở mọi project.
```

Nếu `ERROR` → in lỗi và dừng.

### Bước 2 — Hỏi về knowledge setup (optional)

Sau khi identity xong, hỏi user:

```
Sếp muốn setup knowledge cho project hiện tại không ạ?

1. /morai:scan   — quét codebase, hiểu tech stack + architecture (nhanh, không cần tool ngoài)
2. /morai:onboard — tổng hợp từ Confluence + Jira + codebase (đầy đủ hơn, cần credentials)
3. Bỏ qua       — làm sau cũng được
```

### Bước 3 — Thực thi theo lựa chọn

**Nếu chọn scan:**
Chạy skill `/morai:scan` với project directory hiện tại (`$CLAUDE_PROJECT_DIR` hoặc dùng `pwd`).

**Nếu chọn onboard:**
Hỏi lần lượt để collect thông tin cần thiết:
- Tên project (bắt buộc)
- Có Confluence không? Nếu có → space key
- Có Jira không? Nếu có → project key
- Git org (để push design repo lên, optional)

Sau đó build và chạy lệnh:
```bash
find ~/.claude/plugins/cache/morai -name "onboard.py" -path "*/scripts/*" 2>/dev/null | head -1
```

```bash
uv run --project <plugin-root> python <path-onboard.py> \
  --project-name <tên> \
  [--project <jira-key>] \
  [--confluence-space <space>] \
  [--no-confluence] [--no-jira] \
  [--git-org <org>] \
  --synthesize
```

`<plugin-root>` = dirname của dirname của path onboard.py tìm được.

**Nếu chọn bỏ qua:**
```
Okie sếp. Khi nào cần thì chạy /morai:scan hoặc /morai:onboard nhé.
```
