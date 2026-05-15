"""Confluence MCP server — fetch pages, search documentation."""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-confluence")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN", "")

_NOT_CONFIGURED = {
    "error": "morai-confluence not configured — set CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_TOKEN in .env"
}


def _is_configured() -> bool:
    return bool(CONFLUENCE_URL and CONFLUENCE_EMAIL and CONFLUENCE_TOKEN)


def _client():
    from atlassian import Confluence
    return Confluence(url=CONFLUENCE_URL, username=CONFLUENCE_EMAIL, password=CONFLUENCE_TOKEN)


def _html_to_md(html: str) -> str:
    import html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    return h.handle(html).strip()


@mcp.tool()
def get_page(page_id: str) -> dict:
    """Fetch nội dung một Confluence page.

    Args:
        page_id: Confluence page ID (số) hoặc title
    Returns:
        dict với title, body (markdown), space_key, labels, last_updated, url
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    page = _client().get_page_by_id(page_id, expand="body.storage,metadata.labels,version,space")
    labels = [lb["name"] for lb in page.get("metadata", {}).get("labels", {}).get("results", [])]
    return {
        "id": page["id"],
        "title": page["title"],
        "body": _html_to_md(page["body"]["storage"]["value"]),
        "space_key": page["space"]["key"],
        "labels": labels,
        "last_updated": page["version"]["when"],
        "url": f"{CONFLUENCE_URL}/wiki{page['_links']['webui']}",
    }


@mcp.tool()
def search(query: str, space: str | None = None, max_results: int = 10) -> list[dict]:
    """Full-text search trong Confluence bằng CQL.

    Args:
        query: Search keyword hoặc CQL expression
        space: Filter theo space key (optional)
        max_results: Giới hạn số kết quả
    Returns:
        List of {id, title, space_key, excerpt, url}
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    cql = f'text ~ "{query}"'
    if space:
        cql += f' AND space = "{space}"'
    results = _client().cql(cql, limit=max_results).get("results", [])
    return [
        {
            "id": r["content"]["id"],
            "title": r["content"]["title"],
            "space_key": r["resultGlobalContainer"]["title"],
            "excerpt": r.get("excerpt", ""),
            "url": f"{CONFLUENCE_URL}/wiki{r['content']['_links']['webui']}",
        }
        for r in results
    ]


@mcp.tool()
def get_children(page_id: str) -> list[dict]:
    """Lấy danh sách child pages của một page.

    Args:
        page_id: Confluence page ID
    Returns:
        List of {id, title, url}
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    children = _client().get_page_child_by_type(page_id, type="page", limit=50)
    return [
        {
            "id": c["id"],
            "title": c["title"],
            "url": f"{CONFLUENCE_URL}/wiki{c['_links']['webui']}",
        }
        for c in children
    ]


@mcp.tool()
def get_space_pages(space_key: str, label: str | None = None, limit: int = 100) -> list[dict]:
    """Lấy tất cả pages trong một Confluence space, optional filter theo label.

    Args:
        space_key: Space key, e.g. "PROJ"
        label: Filter theo label (optional), e.g. "basic-design"
        limit: Số pages tối đa
    Returns:
        List of {id, title, labels, last_updated, url}
    """
    if not _is_configured():
        return [_NOT_CONFIGURED]
    client = _client()
    if label:
        cql = f'space = "{space_key}" AND label = "{label}" ORDER BY title'
        results = client.cql(cql, limit=limit).get("results", [])
        page_ids = [r["content"]["id"] for r in results]
        pages = [client.get_page_by_id(pid, expand="metadata.labels,version") for pid in page_ids]
    else:
        pages = client.get_all_pages_from_space(space_key, limit=limit, expand="metadata.labels,version")

    return [
        {
            "id": p["id"],
            "title": p["title"],
            "labels": [lb["name"] for lb in p.get("metadata", {}).get("labels", {}).get("results", [])],
            "last_updated": p["version"]["when"],
            "url": f"{CONFLUENCE_URL}/wiki{p['_links']['webui']}",
        }
        for p in pages
    ]


if __name__ == "__main__":
    mcp.run()
