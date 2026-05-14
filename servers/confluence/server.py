"""Confluence MCP server — fetch pages, search documentation."""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-confluence")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")


@mcp.tool()
def get_page(page_id: str) -> dict:
    """Fetch nội dung một Confluence page.

    Args:
        page_id: Confluence page ID hoặc URL
    Returns:
        dict với title, body (text), space, last_updated
    """
    # TODO: implement Confluence REST API
    raise NotImplementedError


@mcp.tool()
def search(query: str, space: str | None = None, max_results: int = 10) -> list[dict]:
    """Full-text search trong Confluence.

    Args:
        query: Search keyword
        space: Filter theo space key
        max_results: Giới hạn số kết quả
    """
    # TODO: implement CQL search
    raise NotImplementedError


@mcp.tool()
def get_children(page_id: str) -> list[dict]:
    """Lấy danh sách child pages của một page.

    Args:
        page_id: Confluence page ID
    """
    # TODO: implement children fetch
    raise NotImplementedError


if __name__ == "__main__":
    mcp.run()
