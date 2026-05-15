---
description: Morai Onboard — bootstrap knowledge repo từ Confluence + Jira + codebase cho project mới
---

# Morai Onboard

Tổng hợp knowledge cho project: pull docs từ Confluence, tickets từ Jira, index vào RAG.
Dùng khi bắt đầu làm việc với project mới có đầy đủ tooling.

## Input
$ARGUMENTS — tên project (optional, sẽ hỏi nếu không có)

## Quy trình

### Bước 1 — Collect thông tin

Hỏi lần lượt (bỏ qua nếu $ARGUMENTS đã có):

1. **Tên project** (bắt buộc): dùng để tạo `{project-name}-design` repo
2. **Jira project key** (optional, ví dụ: PROJ): để trống nếu không dùng Jira
3. **Confluence space key** (optional, ví dụ: MYSPACE): để trống nếu không dùng Confluence
4. **Git org** (optional, ví dụ: my-github-org): để trống nếu không push lên git

### Bước 2 — Tìm onboard.py trong plugin cache

```bash
find ~/.claude/plugins/cache/morai -name "onboard.py" -path "*/scripts/*" 2>/dev/null | head -1
```

Nếu không tìm được → báo lỗi:
```
Không tìm thấy Morai plugin cache. Sếp thử /reload-plugins rồi chạy lại nhé.
```

Xác định plugin root:
```bash
dirname $(dirname <path-onboard.py>)
```

### Bước 3 — Build và chạy lệnh

Build args dựa trên thông tin đã collect:
- Có Jira key → thêm `--project <key>`, không có → `--no-jira`
- Có Confluence key → thêm `--confluence-space <key>`, không có → `--no-confluence`
- Có git org → thêm `--git-org <org>`
- Luôn thêm `--synthesize` để scan codebase sau khi onboard

```bash
uv run --project <plugin-root> python <path-onboard.py> \
  --project-name <tên> \
  [--project <jira-key>] \
  [--confluence-space <space>] \
  [--no-confluence] [--no-jira] \
  [--git-org <org>] \
  --synthesize
```

### Bước 4 — Báo kết quả

Khi xong:
```
Onboard xong sếp. Knowledge repo đã được tạo tại ./{project-name}-design/
Morai đã index codebase + docs — sẵn sàng làm việc.
```

Nếu lỗi credentials (Jira/Confluence 401) → nhắc:
```
Lỗi authentication. Sếp kiểm tra JIRA_TOKEN / CONFLUENCE_TOKEN trong .env nhé.
```
