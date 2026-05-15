"""Jira MCP server — fetch tickets, search issues."""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-jira")

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")

_NOT_CONFIGURED = {"error": "morai-jira not configured — set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN in .env"}


def _is_configured() -> bool:
    return bool(JIRA_URL and JIRA_EMAIL and JIRA_TOKEN)


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Fetch chi tiết một Jira ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    Returns:
        dict với summary, description, status, priority, assignee, comments, attachments
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    # TODO: implement Jira REST API call
    return {"error": f"morai-jira: get_ticket not yet implemented. ticket_id={ticket_id}"}


@mcp.tool()
def search_tickets(query: str, project: str | None = None, max_results: int = 10) -> list[dict]:
    """Tìm kiếm tickets bằng JQL hoặc text search.

    Args:
        query: JQL query hoặc keyword
        project: Filter theo project key
        max_results: Giới hạn số kết quả
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    # TODO: implement JQL search
    return [{"error": f"morai-jira: search_tickets not yet implemented. query={query}"}]


@mcp.tool()
def get_ticket_comments(ticket_id: str) -> list[dict]:
    """Lấy toàn bộ comments của một ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    # TODO: implement comments fetch
    return [{"error": f"morai-jira: get_ticket_comments not yet implemented. ticket_id={ticket_id}"}]


if __name__ == "__main__":
    mcp.run()
