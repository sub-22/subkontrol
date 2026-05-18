"""Jira MCP server — fetch tickets, search issues."""

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from servers._env import resolve

mcp = FastMCP("morai-jira")

JIRA_URL = resolve("JIRA_URL")
JIRA_EMAIL = resolve("JIRA_EMAIL")
JIRA_TOKEN = resolve("JIRA_TOKEN")

_REPO_ROOT = Path(__file__).parent.parent.parent
_DEV_MAPPING_PATH = _REPO_ROOT / "config" / "dev_mapping.json"
_STUBS_PATH = Path(__file__).parent / "stubs" / "assigned_tasks.json"

_PRIORITY_ORDER = ["Blocker", "Critical", "High", "Medium", "Low", "Trivial"]

_NOT_CONFIGURED = {
    "error": "morai-jira not configured — set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN in .env"
}


def _is_configured() -> bool:
    return bool(JIRA_URL and JIRA_TOKEN)


def _client() -> "Any":
    from atlassian import Jira

    # PAT on Jira Server/Data Center uses Bearer token (not Basic auth)
    return Jira(url=JIRA_URL, token=JIRA_TOKEN)


def _format_ticket(issue: dict) -> dict:
    fields = issue.get("fields", {})
    assignee = fields.get("assignee") or {}
    reporter = fields.get("reporter") or {}
    return {
        "id": issue["key"],
        "summary": fields.get("summary", ""),
        "description": fields.get("description", "") or "",
        "status": fields.get("status", {}).get("name", ""),
        "priority": fields.get("priority", {}).get("name", ""),
        "issue_type": fields.get("issuetype", {}).get("name", ""),
        "assignee": assignee.get("displayName", ""),
        "reporter": reporter.get("displayName", ""),
        "labels": fields.get("labels", []),
        "created": fields.get("created", ""),
        "updated": fields.get("updated", ""),
        "url": f"{JIRA_URL}/browse/{issue['key']}",
    }


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Fetch chi tiết một Jira ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    Returns:
        dict với summary, description, status, priority, assignee, issue_type, labels, url
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    issue = _client().issue(ticket_id)
    return _format_ticket(issue)


@mcp.tool()
def search_tickets(query: str, project: str | None = None, max_results: int = 10) -> list[dict]:
    """Tìm kiếm tickets bằng JQL hoặc text search.

    Args:
        query: JQL query (e.g. 'status = "In Progress"') hoặc keyword
        project: Filter theo project key (optional)
        max_results: Giới hạn số kết quả
    Returns:
        List of ticket dicts
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    jql = query
    if project and "project" not in query.lower():
        jql = f'project = "{project}" AND ({query})'
    results = _client().jql(jql, limit=max_results)
    return [_format_ticket(issue) for issue in results.get("issues", [])]


@mcp.tool()
def get_ticket_comments(ticket_id: str) -> list[dict]:
    """Lấy toàn bộ comments của một ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    Returns:
        List of {author, body, created}
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    comments = _client().issue(ticket_id, fields="comment")
    return [
        {
            "author": c.get("author", {}).get("displayName", ""),
            "body": c.get("body", ""),
            "created": c.get("created", ""),
        }
        for c in comments.get("fields", {}).get("comment", {}).get("comments", [])
    ]


@mcp.tool()
def get_project_epics(project_key: str, max_results: int = 50) -> list[dict]:
    """Lấy tất cả epics của một Jira project.

    Args:
        project_key: e.g. "PROJ"
        max_results: Giới hạn số epics
    Returns:
        List of {id, summary, status, url}
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    jql = f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC'
    results = _client().jql(jql, limit=max_results)
    return [_format_ticket(issue) for issue in results.get("issues", [])]


@mcp.tool()
def get_active_sprint(project_key: str) -> dict:
    """Lấy thông tin sprint đang active của project.

    Args:
        project_key: e.g. "PROJ"
    Returns:
        dict với sprint name, dates, và danh sách tickets
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    jql = f'project = "{project_key}" AND sprint in openSprints() ORDER BY priority DESC'
    results = _client().jql(jql, limit=50)
    issues = results.get("issues", [])
    if not issues:
        return {"sprint": None, "tickets": []}
    # Extract sprint name from first issue
    sprint_info = {}
    sprints = issues[0].get("fields", {}).get("sprint") if issues else None
    if sprints:
        sprint_info = {"name": sprints.get("name", ""), "end_date": sprints.get("endDate", "")}
    return {
        "sprint": sprint_info,
        "ticket_count": len(issues),
        "tickets": [_format_ticket(i) for i in issues],
    }


def _resolve_dev_identity() -> dict[str, Any] | None:
    """Resolve current dev: dev_mapping.json (dev mode) → env vars (plugin mode)."""
    try:
        email = subprocess.check_output(["git", "config", "user.email"], text=True).strip()
    except subprocess.CalledProcessError:
        email = ""

    if _DEV_MAPPING_PATH.exists():
        mapping: dict[str, Any] = json.loads(_DEV_MAPPING_PATH.read_text())
        dev = mapping.get("devs", {}).get(email)
        if dev:
            return cast(dict[str, Any], dev)

    # Plugin mode fallback: use JIRA_EMAIL from env/userConfig
    if JIRA_EMAIL:
        return {
            "git_name": email.split("@")[0] if email else "",
            "jira_email": JIRA_EMAIL,
            "project_keys": [],
        }

    return None


def _priority_rank(priority_name: str) -> int:
    try:
        return _PRIORITY_ORDER.index(priority_name)
    except ValueError:
        return len(_PRIORITY_ORDER)


def _fetch_from_stub(dev: dict, max_results: int) -> list[dict]:
    if not _STUBS_PATH.exists():
        return []
    data = json.loads(_STUBS_PATH.read_text())
    dev_email = dev["jira_email"].lower()
    issues = [
        i
        for i in data.get("issues", [])
        if (i.get("fields", {}).get("assignee") or {}).get("emailAddress", "").lower() == dev_email
    ]
    return issues[:max_results]


def _prioritize(issues: list[dict]) -> list[dict]:
    def sort_key(issue: dict) -> tuple:
        f = issue.get("fields", {})
        priority = f.get("priority", {}).get("name", "Trivial")
        points = f.get("story_points", 99)
        return (_priority_rank(priority), points)

    return sorted(issues, key=sort_key)


def _format_task_list(issues: list[dict], jira_url: str, shadow: bool) -> dict:
    tasks = []
    for i, issue in enumerate(issues, 1):
        f = issue.get("fields", {})
        url = f"{jira_url}/browse/{issue['key']}" if jira_url else f"[shadow] {issue['key']}"
        tasks.append(
            {
                "rank": i,
                "id": issue["key"],
                "summary": f.get("summary", ""),
                "priority": f.get("priority", {}).get("name", ""),
                "type": f.get("issuetype", {}).get("name", ""),
                "status": f.get("status", {}).get("name", ""),
                "story_points": f.get("story_points"),
                "labels": f.get("labels", []),
                "url": url,
            }
        )
    return {
        "shadow_mode": shadow,
        "total": len(tasks),
        "tasks": tasks,
    }


def _fetch_assigned_issues(client: "Any", dev: dict, max_results: int) -> list[dict]:
    """Try assignee = currentUser(), fallback to project-based search if field is restricted."""
    # Primary: currentUser() — works when PAT has Browse Users & Groups permission
    try:
        jql = (
            "assignee = currentUser()"
            ' AND status in ("To Do","In Progress","Open")'
            " ORDER BY created DESC"
        )
        results = client.jql(jql, limit=max_results)
        return cast(list[dict[str, Any]], results.get("issues", []))
    except Exception as primary_err:
        if "assignee" not in str(primary_err).lower():
            raise

    # Fallback: project-based search, filter by email client-side
    project_keys = dev.get("project_keys") or []
    jira_email = dev.get("jira_email", "").lower()
    if not project_keys:
        return []

    projects_jql = ", ".join(f'"{k}"' for k in project_keys)
    jql = (
        f"project in ({projects_jql})"
        ' AND status in ("To Do","In Progress","Open")'
        " ORDER BY created DESC"
    )
    results = client.jql(jql, limit=max_results * 5)
    issues = results.get("issues", [])

    if jira_email:
        issues = [
            i
            for i in issues
            if (i.get("fields", {}).get("assignee") or {}).get("emailAddress", "").lower()
            == jira_email
        ]

    return cast(list[dict[str, Any]], issues[:max_results])


@mcp.tool()
def fetch_my_tasks(max_results: int = 10) -> dict:
    """Fetch và prioritize tasks được assign cho dev hiện tại.

    Tự động resolve identity từ git config → config/dev_mapping.json.
    Shadow mode: đọc từ servers/jira/stubs/assigned_tasks.json khi Jira chưa configured.

    Args:
        max_results: Số task tối đa trả về
    Returns:
        dict với shadow_mode, total, tasks (đã sort theo priority + story_points)
    """
    dev = _resolve_dev_identity()
    if dev is None:
        return {
            "error": (
                "Cannot resolve dev identity. "
                "Check git config user.email và config/dev_mapping.json."
            )
        }

    cfg: dict[str, Any] = {}
    if _DEV_MAPPING_PATH.exists():
        cfg = json.loads(_DEV_MAPPING_PATH.read_text()).get("defaults", {})
    max_results = min(max_results, cfg.get("max_tasks", 10))

    shadow = not _is_configured()

    if shadow:
        issues = _fetch_from_stub(dev, max_results)
    else:
        client = _client()
        issues = _fetch_assigned_issues(client, dev, max_results)

    prioritized = _prioritize(issues)
    return _format_task_list(prioritized, JIRA_URL, shadow)


if __name__ == "__main__":
    mcp.run()
