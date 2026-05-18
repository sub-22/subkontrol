---
description: Morai Doctor — kiểm tra kết nối tất cả MCP servers, báo trạng thái và hướng dẫn fix nếu có vấn đề
---

# Morai Doctor

Preflight health check cho tất cả MCP servers. Dùng trước khi onboard hoặc khi debug kết nối.

## Input
$ARGUMENTS — optional filter: `jira`, `confluence`, `slack`, `all` (default: all)

## Quy trình

### Bước 1 — Test từng MCP

Test theo nhóm bằng cách gọi tool thật và quan sát response:

**morai-jira:**
Gọi `morai-jira: fetch_my_tasks()`.
- Response có `shadow_mode: true` → ⚠️ chưa configure credentials
- Response có data → ✅ connected
- Tool không respond / error → ❌ server lỗi

**morai-confluence:**
Gọi `morai-confluence: search(query="", limit=1)`.
- Response có `"not configured"` → ⚠️ chưa configure credentials
- Response có data → ✅ connected
- Tool không respond / error → ❌ server lỗi

**morai-slack:**
Gọi `morai-slack: get_pending_messages()`.
- Response có `"not configured"` → ⚠️ chưa configure credentials
- Response có data → ✅ connected
- Tool không respond / error → ❌ server lỗi

**morai-memory:**
Gọi `morai-memory: list_episodes(limit=1)`.
- Response có data (kể cả empty list) → ✅ working
- Error → ❌ server lỗi

**morai-pipeline:**
Gọi `morai-pipeline: get_state()`.
- Response có data → ✅ working
- Error → ❌ server lỗi

**morai-rag:**
Gọi `morai-rag: list_namespaces()`.
- Response có data (kể cả empty) → ✅ working
- Error → ❌ server lỗi

**morai-git / morai-file / morai-test:**
Gọi lần lượt:
- `morai-git: git_status()`
- `morai-file: list_files(".")`
- `morai-test: detect_test_framework()`
- Response có data → ✅ working
- Error → ❌ server lỗi

### Bước 2 — Hiển thị kết quả

In bảng trạng thái:

```
Morai Doctor — Health Check
──────────────────────────────────────────
  morai-memory     ✅ connected
  morai-pipeline   ✅ connected
  morai-rag        ✅ connected
  morai-file       ✅ connected
  morai-git        ✅ connected
  morai-test       ✅ connected
  morai-jira       ⚠️  shadow mode — chưa configure credentials
  morai-confluence ⚠️  shadow mode — chưa configure credentials
  morai-slack      ⚠️  shadow mode — chưa configure credentials
──────────────────────────────────────────
Core: 6/6 ✅   Integrations: 0/3 ⚠️
```

### Bước 3 — Hướng dẫn fix cho ⚠️ và ❌

Với mỗi MCP chưa configure, in hướng dẫn cụ thể:

**morai-jira ⚠️:**
```
Jira chưa configure. Sếp vào Plugin Settings → morai để điền:
  • JIRA_URL   : https://yourorg.atlassian.net
  • JIRA_EMAIL : email đăng nhập Jira
  • JIRA_TOKEN : Atlassian Account → Security → API tokens
```

**morai-confluence ⚠️:**
```
Confluence chưa configure. Plugin Settings → morai:
  • CONFLUENCE_URL   : https://yourorg.atlassian.net/wiki
  • CONFLUENCE_EMAIL : email đăng nhập Confluence
  • CONFLUENCE_TOKEN : dùng chung Atlassian API token với Jira
```

**morai-slack ⚠️:**
```
Slack chưa configure. Plugin Settings → morai:
  • SLACK_BOT_TOKEN : xoxb-... từ api.slack.com/apps
  • SLACK_APP_TOKEN : xapp-... cần cho Socket Mode
```

Với ❌ server lỗi:
```
[tên-mcp] không khởi động được. Thử /reload-plugins rồi chạy lại.
Nếu vẫn lỗi, sếp check: uv run --project <plugin-path> python -m servers.<name>.server
```

### Bước 4 — Return trạng thái (khi được gọi từ skill khác)

Sau khi hiển thị xong, return object tóm tắt để skill gọi doctor có thể dùng:

```
DOCTOR_RESULT:
  jira: ok | shadow | error
  confluence: ok | shadow | error
  slack: ok | shadow | error
  core: ok | error
```
