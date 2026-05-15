"""Confluence MCP server — fetch pages, search documentation."""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-confluence")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")

_NOT_CONFIGURED = {
    "error": "morai-confluence not configured — set CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_TOKEN in .env"  # noqa: E501
}


def _is_configured() -> bool:
    return bool(CONFLUENCE_URL and CONFLUENCE_EMAIL and CONFLUENCE_TOKEN)


@mcp.tool()
def get_page(page_id: str) -> dict:
    """Fetch nội dung một Confluence page.

    Args:
        page_id: Confluence page ID hoặc URL
    Returns:
        dict với title, body (text), space, last_updated
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    # TODO: implement Confluence REST API
    return {"error": f"morai-confluence: get_page not yet implemented. page_id={page_id}"}


@mcp.tool()
def search(query: str, space: str | None = None, max_results: int = 10) -> list[dict]:
    """Full-text search trong Confluence.

    Args:
        query: Search keyword
        space: Filter theo space key
        max_results: Giới hạn số kết quả
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    # TODO: implement CQL search
    return [{"error": f"morai-confluence: search not yet implemented. query={query}"}]


@mcp.tool()
def get_children(page_id: str) -> list[dict]:
    """Lấy danh sách child pages của một page.

    Args:
        page_id: Confluence page ID
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    # TODO: implement children fetch
    return [{"error": f"morai-confluence: get_children not yet implemented. page_id={page_id}"}]


if __name__ == "__main__":
    mcp.run()
