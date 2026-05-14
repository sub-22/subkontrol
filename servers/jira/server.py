"""Jira MCP server — fetch tickets, search issues."""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-jira")

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Fetch chi tiết một Jira ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    Returns:
        dict với summary, description, status, priority, assignee, comments, attachments
    """
    # TODO: implement Jira REST API call
    raise NotImplementedError


@mcp.tool()
def search_tickets(query: str, project: str | None = None, max_results: int = 10) -> list[dict]:
    """Tìm kiếm tickets bằng JQL hoặc text search.

    Args:
        query: JQL query hoặc keyword
        project: Filter theo project key
        max_results: Giới hạn số kết quả
    """
    # TODO: implement JQL search
    raise NotImplementedError


@mcp.tool()
def get_ticket_comments(ticket_id: str) -> list[dict]:
    """Lấy toàn bộ comments của một ticket.

    Args:
        ticket_id: e.g. "PROJ-123"
    """
    # TODO: implement comments fetch
    raise NotImplementedError


if __name__ == "__main__":
    mcp.run()
