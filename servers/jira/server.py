"""Jira MCP server — fetch tickets, search issues."""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-jira")

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")

_NOT_CONFIGURED = {
    "error": "morai-jira not configured — set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN in .env"
}


def _is_configured() -> bool:
    return bool(JIRA_URL and JIRA_EMAIL and JIRA_TOKEN)


def _client():
    from atlassian import Jira
    return Jira(url=JIRA_URL, username=JIRA_EMAIL, password=JIRA_TOKEN)


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


if __name__ == "__main__":
    mcp.run()
