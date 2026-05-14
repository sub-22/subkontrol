# subkontrol

Claude Code plugin cung cấp bộ AI agent pipeline cho team phát triển phần mềm: BA, Architect, PM, Dev, Reviewer, Security, QA.

Plugin name: **morai** → commands: `/morai:ba`, `/morai:dev`, ...

## Skills

| Command | Mô tả |
|---|---|
| `/morai:scan` | Scan project, sinh CLAUDE.md + knowledge docs, index vào RAG |
| `/morai:ba` | Fetch Jira/Confluence → phân tích requirements → spec.md |
| `/morai:architect` | Thiết kế giải pháp kỹ thuật → Architecture Decision Record |
| `/morai:pm` | spec.md → sprint plan + task breakdown |
| `/morai:dev` | Task → implement → PR |
| `/morai:reviewer` | PR → code review (quality, logic, conventions) |
| `/morai:security` | PR → security review (OWASP Top 10, STRIDE) |
| `/morai:qa` | Spec → test cases → test report |

## MCP Servers

| Server | Mô tả |
|---|---|
| `morai-rag` | Vector search — index và search documents/codebase |
| `morai-jira` | Fetch/search Jira tickets |
| `morai-confluence` | Fetch/search Confluence pages |
| `morai-slack` | Gửi messages, request approval qua Slack |
| `morai-file` | Đọc/ghi files trong workspace |
| `morai-git` | Git status, diff, commit, branch |

## Cài đặt

### Yêu cầu
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Claude Code CLI

### Setup

```bash
git clone https://github.com/your-org/subkontrol
cd subkontrol

cp .env.example .env
# Điền API keys vào .env

uv sync
```

### Cài plugin vào Claude Code

```bash
# Test local
claude --plugin-dir ./subkontrol

# Hoặc install
claude plugin install .
```

### Cấu hình khi enable plugin

Sau khi install, Claude Code sẽ hỏi:

| Field | Ví dụ |
|---|---|
| Jira URL | `https://yourorg.atlassian.net` |
| Confluence URL | `https://yourorg.atlassian.net/wiki` |
| Slack channel | `#dev-pipeline` |
| Workspace root | `/path/to/your/project` |

## Bắt đầu với project mới

```
/morai:scan /path/to/project
```

Skill này sẽ index toàn bộ codebase và sinh ra:
- `CLAUDE.md` tại project root
- `.morai/knowledge/` — architecture, tech-stack, conventions, api, database docs

Sau đó các agents khác đã có đủ context để hoạt động.

## Workflow tiêu chuẩn

```
/morai:ba PROJ-123
    ↓ specs/PROJ-123.md

/morai:architect PROJ-123     ← nếu feature phức tạp
    ↓ docs/adr/PROJ-123.md

/morai:pm PROJ-123
    ↓ plans/PROJ-123-tasks.md

/morai:dev TASK-1
    ↓ code + PR

/morai:reviewer PROJ-123
/morai:security PROJ-123      ← bắt buộc với auth/payment/user data
    ↓ reviews/

/morai:qa PROJ-123
    ↓ tests/PROJ-123-test-plan.md
```

## Cấu trúc project

```
subkontrol/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/                  # Claude Code slash commands
│   ├── scan/SKILL.md
│   ├── ba/SKILL.md
│   ├── architect/SKILL.md
│   ├── pm/SKILL.md
│   ├── dev/SKILL.md
│   ├── reviewer/SKILL.md
│   ├── security/SKILL.md
│   └── qa/SKILL.md
├── servers/                 # MCP servers
│   ├── rag/server.py        ✓ implemented
│   ├── file/server.py       ✓ implemented
│   ├── git/server.py        ✓ implemented
│   ├── jira/server.py       stub
│   ├── confluence/server.py stub
│   └── morai/server.py      stub
├── .mcp.json                # MCP server registrations
├── pyproject.toml
└── .env.example
```

## Environment variables

| Variable | Mô tả |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `JIRA_URL` | Jira instance URL |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_TOKEN` | Jira API token |
| `CONFLUENCE_URL` | Confluence URL |
| `CONFLUENCE_EMAIL` | Confluence account email |
| `CONFLUENCE_TOKEN` | Confluence API token |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Slack app token (`xapp-...`) |
| `CHROMA_PATH` | Path lưu vector store (default: `.morai/rag`) |
