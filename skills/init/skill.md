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

### Bước 2 — Setup integrations (optional)

Hỏi user từng integration — **không hỏi cái không cần**:

```
Sếp setup integrations nhé — cái nào không dùng thì bỏ qua.
```

Hỏi tuần tự, mỗi lần một tool:

**Jira:**
```
Sếp có dùng Jira không ạ? (có / không)
```
Nếu có → hỏi lần lượt:
- Jira URL (e.g. `https://yourorg.atlassian.net`)
- Email đăng nhập Jira
- API Token (tạo tại atlassian.com → Account Settings → Security → API tokens)

**Confluence:**
```
Sếp có dùng Confluence không ạ? (có / không)
```
Nếu có → hỏi:
- Confluence URL (e.g. `https://yourorg.atlassian.net/wiki`)
- Email (thường giống Jira)
- API Token (thường dùng chung với Jira — gợi ý điền lại nếu vừa nhập)

**Slack:**
```
Sếp có dùng Slack không ạ? (có / không)
```
Nếu có → hỏi:
- Bot Token (`xoxb-...` từ api.slack.com/apps)
- App Token (`xapp-...` cần cho Socket Mode — để trống nếu không dùng)
- Default channel (e.g. `#dev-pipeline`)

**Sau khi collect xong** → ghi vào `~/.morai/config.json`:

```bash
python3 << 'PYEOF'
import json, os
from pathlib import Path

global_path = os.environ.get("MORAI_GLOBAL_PATH", str(Path.home() / ".morai"))
config_path = Path(global_path).expanduser() / "config.json"
config_path.parent.mkdir(parents=True, exist_ok=True)

existing = {}
if config_path.exists():
    try:
        existing = json.loads(config_path.read_text())
    except Exception:
        pass

# Replace with actual collected values before running
updates = {
    "jira":       {"url": "<JIRA_URL>", "email": "<JIRA_EMAIL>", "token": "<JIRA_TOKEN>"},
    "confluence": {"url": "<CONFLUENCE_URL>", "email": "<CONFLUENCE_EMAIL>", "token": "<CONFLUENCE_TOKEN>"},
    "slack":      {"bot_token": "<SLACK_BOT_TOKEN>", "app_token": "<SLACK_APP_TOKEN>", "channel": "<SLACK_CHANNEL>"},
}

for section, values in updates.items():
    cleaned = {k: v for k, v in values.items() if v and not v.startswith("<")}
    if cleaned:
        existing.setdefault(section, {}).update(cleaned)

config_path.write_text(json.dumps(existing, indent=2))
print("OK")
PYEOF
```

Nếu user bỏ qua tất cả → không ghi file, thông báo:
```
Okie sếp. Khi nào cần thì chạy /morai:init lại để setup nhé.
```

### Bước 3 — Hỏi về knowledge setup (optional)

Sau khi integrations xong, hỏi user:

```
Sếp muốn setup knowledge cho project hiện tại không ạ?

1. /morai:scan   — quét codebase, hiểu tech stack + architecture (nhanh, không cần tool ngoài)
2. /morai:onboard — tổng hợp từ Confluence + Jira + codebase (đầy đủ hơn, cần credentials)
3. Bỏ qua       — làm sau cũng được
```

### Bước 4 — Thực thi theo lựa chọn

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
