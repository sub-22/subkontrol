---
description: Morai Init — thiết lập Morai identity và hướng dẫn setup knowledge cho project
version: 1.0.0
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

Nếu kết quả `ALREADY_SETUP` → thông báo identity đã up-to-date và tiếp tục sang Bước 2.

Nếu kết quả `OK` → thông báo:
```
Morai identity đã được lưu vào ~/.claude/CLAUDE.md.
Restart Claude Code để apply identity — sau đó Morai sẽ hoạt động đúng ở mọi project.
```

Nếu kết quả `UPDATED:vOLD->vNEW` hoặc `MIGRATED:vNEW` → thông báo:
```
Morai identity trong ~/.claude/CLAUDE.md đã được re-sync lên vNEW.
Restart Claude Code để apply.
```

Nếu `ERROR: ...` → in lỗi và dừng.

### Bước 2 — Setup integrations (optional)

Hỏi user từng integration — **không hỏi cái không cần**:

```
Sếp setup integrations nhé — cái nào không dùng thì bỏ qua.
```

Hỏi tuần tự, mỗi lần một tool:

**Global path (bắt buộc):**
```
Morai lưu memory và tasks ở đâu ạ? (default: ~/.morai — Enter để dùng default)
```

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

**Git provider:**
```
Sếp dùng GitHub hay Bitbucket ạ? (github / bitbucket / không dùng)
```
Nếu **github** → hỏi: GitHub Personal Access Token (tạo tại github.com → Settings → Developer settings → Tokens)

Nếu **bitbucket** → hỏi:
- Bitbucket Username
- App Password (tạo tại bitbucket.org → Personal settings → App passwords)
- Bitbucket Server URL nếu dùng self-hosted (e.g. `https://git.mycompany.com` — để trống nếu dùng Cloud)

**Slack:**
```
Sếp có dùng Slack không ạ? (có / không)
```
Nếu có → hỏi:
- Bot Token (`xoxb-...` từ api.slack.com/apps)
- App Token (`xapp-...` — để trống nếu không dùng Socket Mode)
- Default channel (e.g. `#dev-pipeline`)

**Telegram:**
```
Sếp có dùng Telegram không ạ? (có / không)
```
Nếu có → hỏi:
- Bot Token (tạo bot qua [@BotFather](https://t.me/BotFather): `/newbot` → nhận token dạng `123456:ABC-DEF...`)
- Default Chat ID (nhắn thử cho bot rồi lấy `chat.id` qua [@userinfobot](https://t.me/userinfobot), hoặc gọi `getUpdates`)

**Sau khi collect xong** — detect plugin key từ `settings.json` rồi ghi vào đúng chỗ:

```bash
python3 << 'PYEOF'
import json
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)

settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except Exception:
        pass

# Detect plugin key — tìm key có prefix "morai@" trong pluginConfigs
plugin_configs = settings.get("pluginConfigs", {})
plugin_key = next((k for k in plugin_configs if k.startswith("morai@")), "morai@morai")

# Replace placeholder values with actual collected values before running
new_options = {
    "MORAI_GLOBAL_PATH":  "<MORAI_GLOBAL_PATH>",
    "JIRA_URL":           "<JIRA_URL>",
    "JIRA_EMAIL":         "<JIRA_EMAIL>",
    "JIRA_TOKEN":         "<JIRA_TOKEN>",
    "CONFLUENCE_URL":     "<CONFLUENCE_URL>",
    "CONFLUENCE_EMAIL":   "<CONFLUENCE_EMAIL>",
    "CONFLUENCE_TOKEN":   "<CONFLUENCE_TOKEN>",
    "GITHUB_TOKEN":       "<GITHUB_TOKEN>",
    "BITBUCKET_USERNAME": "<BITBUCKET_USERNAME>",
    "BITBUCKET_TOKEN":    "<BITBUCKET_TOKEN>",
    "BITBUCKET_BASE_URL": "<BITBUCKET_BASE_URL>",
    "SLACK_BOT_TOKEN":    "<SLACK_BOT_TOKEN>",
    "SLACK_APP_TOKEN":    "<SLACK_APP_TOKEN>",
    "SLACK_CHANNEL":      "<SLACK_CHANNEL>",
    "TELEGRAM_BOT_TOKEN": "<TELEGRAM_BOT_TOKEN>",
    "TELEGRAM_CHAT_ID":   "<TELEGRAM_CHAT_ID>",
}

# Only write non-empty, non-placeholder values
cleaned = {k: v for k, v in new_options.items() if v and not v.startswith("<")}

plugin_cfg = settings.setdefault("pluginConfigs", {}).setdefault(plugin_key, {})
plugin_cfg.setdefault("options", {}).update(cleaned)

settings_path.write_text(json.dumps(settings, indent=2))
print(f"OK — wrote to pluginConfigs[{plugin_key}]")
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
