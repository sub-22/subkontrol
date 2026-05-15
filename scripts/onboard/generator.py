"""Generator — tạo skeleton files: CLAUDE.md, .mcp.json, .env.example, onboarding/README.md."""

from __future__ import annotations

import shutil
from pathlib import Path

_PROFILES_DIR = Path(__file__).parent.parent.parent / "profiles" / "non-dev"


def _write_if_missing(path: Path, content: str) -> bool:
    """Write file chỉ khi chưa tồn tại. Returns True nếu đã write."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def generate_skeleton(repo_dir: Path, project_name: str, project_key: str) -> None:
    """Tạo tất cả skeleton files trong repo_dir."""

    # CLAUDE.md — copy từ non-dev profile, overwrite
    claude_src = _PROFILES_DIR / "CLAUDE.md"
    claude_dst = repo_dir / "CLAUDE.md"
    if claude_src.exists():
        shutil.copy(claude_src, claude_dst)

    # .mcp.json — copy từ non-dev profile, overwrite
    mcp_src = _PROFILES_DIR / ".mcp.json"
    mcp_dst = repo_dir / ".mcp.json"
    if mcp_src.exists():
        shutil.copy(mcp_src, mcp_dst)

    # .env.example
    _write_if_missing(repo_dir / ".env.example", f"""\
# Jira
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_TOKEN=your-jira-api-token

# Confluence
CONFLUENCE_URL=https://your-org.atlassian.net
CONFLUENCE_EMAIL=your@email.com
CONFLUENCE_TOKEN=your-confluence-api-token

# Slack (optional — for notifications)
SLACK_BOT_TOKEN=xoxb-...

# Morai Hub (for local agent connection)
MORAI_HUB_URL=ws://your-morai-server:8765
""")

    # .gitignore
    _write_if_missing(repo_dir / ".gitignore", """\
.env
.env.local
.morai/rag/
__pycache__/
*.pyc
""")

    # tickets/ skeleton
    tickets_dir = repo_dir / "tickets"
    tickets_dir.mkdir(exist_ok=True)
    _write_if_missing(tickets_dir / ".gitkeep", "")
    _write_if_missing(tickets_dir / "README.md", f"""\
# Ticket Knowledge — {project_name}

Mỗi folder tương ứng một ticket. Được tạo tự động sau khi Dev hoàn thành task qua Morai pipeline.

## Format

```
tickets/
└── {project_key}-123/
    ├── summary.md    ← what was built, decisions, files changed
    └── learnings.md  ← gotchas, edge cases (optional)
```
""")

    # onboarding/README.md
    onboarding_dir = repo_dir / "onboarding"
    onboarding_dir.mkdir(exist_ok=True)
    _write_if_missing(onboarding_dir / "README.md", f"""\
# {project_name} — Setup Guide for Non-Dev

Repo này là knowledge base của dự án **{project_name}** dành cho BA, PM, QA, QC.

## Prerequisites

1. [Claude Code CLI](https://claude.ai/code) đã cài đặt
2. Token nhận từ Dev Lead (qua `/morai admin generate-token @you` trên Slack)

## Setup

```bash
# 1. Clone repo này
git clone <repo-url>
cd {project_name.lower().replace(' ', '-')}-design

# 2. Copy và điền credentials
cp .env.example .env
# Điền JIRA_TOKEN, CONFLUENCE_TOKEN vào .env

# 3. Chạy local agent
python /path/to/mcp_slack/local_agent.py \\
  --token <your-token> \\
  --hub ws://morai-server:8765 \\
  --workspace .
```

## Cách dùng

Sau khi agent chạy, mention bot trên Slack:
```
@morai PROJ-123
@morai sprint report
@morai tìm spec authentication flow
```

## Cấu trúc repo

| Folder | Nội dung |
|--------|---------|
| `basic_design/` | High-level design documents |
| `detail_design/` | Detail design, API specs |
| `specs/` | User stories, PRDs |
| `decisions/` | ADRs, tech decisions |
| `meetings/` | Meeting notes |
| `tickets/` | Knowledge tích lũy theo ticket |
""")
