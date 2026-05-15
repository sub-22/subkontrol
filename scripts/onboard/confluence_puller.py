"""Confluence puller — fetch pages from space, convert to markdown, map to folders."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Label → folder mapping (thứ tự ưu tiên: specific trước, fallback sau)
LABEL_FOLDER_MAP: list[tuple[str, str]] = [
    ("basic-design",  "basic_design"),
    ("detail-design", "detail_design"),
    ("adr",           "decisions"),
    ("decision",      "decisions"),
    ("rfc",           "decisions"),
    ("meeting",       "meetings"),
    ("minutes",       "meetings"),
    ("spec",          "specs"),
    ("prd",           "specs"),
    ("user-story",    "specs"),
]
DEFAULT_FOLDER = "specs"

# Metadata header embedded in pulled files for idempotency
_META_PATTERN = re.compile(r"<!-- confluence page_id:(\w+) updated:([\w:T+-]+) -->")


def _client(confluence_url: str, email: str, token: str):
    from atlassian import Confluence
    return Confluence(url=confluence_url, username=email, password=token)


def _html_to_md(html: str) -> str:
    import html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0
    return h.handle(html).strip()


def _safe_filename(title: str) -> str:
    name = re.sub(r'[^\w\s-]', '', title).strip().lower()
    return re.sub(r'[\s]+', '-', name) + ".md"


def _detect_folder(labels: list[str]) -> str:
    for label, folder in LABEL_FOLDER_MAP:
        if label in labels:
            return folder
    return DEFAULT_FOLDER


def _read_meta(path: Path) -> tuple[str, str] | None:
    """Returns (page_id, updated) from existing file or None."""
    if not path.exists():
        return None
    first_line = path.read_text(encoding="utf-8").splitlines()[0] if path.exists() else ""
    m = _META_PATTERN.match(first_line)
    return (m.group(1), m.group(2)) if m else None


def pull(
    space_key: str,
    output_dir: Path,
    confluence_url: str,
    email: str,
    token: str,
) -> dict[str, int]:
    """Pull all pages from Confluence space into output_dir.

    Args:
        space_key: Confluence space key, e.g. "PROJ"
        output_dir: Root của project-design repo
        confluence_url, email, token: Confluence credentials
    Returns:
        {"pulled": N, "skipped": N, "errors": N}
    """
    client = _client(confluence_url, email, token)
    stats = {"pulled": 0, "skipped": 0, "errors": 0}

    # Fetch all pages in space
    log.info("Fetching pages from Confluence space: %s", space_key)
    try:
        pages = client.get_all_pages_from_space(
            space_key, limit=200, expand="body.storage,metadata.labels,version"
        )
    except Exception as e:
        log.error("Failed to fetch pages: %s", e)
        stats["errors"] += 1
        return stats

    log.info("Found %d pages", len(pages))

    for page in pages:
        page_id = page["id"]
        title = page["title"]
        updated = page["version"]["when"]
        labels = [lb["name"] for lb in page.get("metadata", {}).get("labels", {}).get("results", [])]
        folder = _detect_folder(labels)

        # Determine output path
        folder_path = output_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / _safe_filename(title)

        # Idempotency: skip nếu file đã có và chưa thay đổi
        existing_meta = _read_meta(file_path)
        if existing_meta and existing_meta[0] == page_id and existing_meta[1] == updated:
            log.debug("Skip (unchanged): %s", title)
            stats["skipped"] += 1
            continue

        try:
            body_html = page["body"]["storage"]["value"]
            body_md = _html_to_md(body_html)
            page_url = f"{confluence_url}/wiki{page['_links']['webui']}"

            content = (
                f"<!-- confluence page_id:{page_id} updated:{updated} -->\n"
                f"# {title}\n\n"
                f"> Source: [{page_url}]({page_url})  \n"
                f"> Labels: {', '.join(labels) or 'none'}  \n"
                f"> Last updated: {updated}\n\n"
                f"---\n\n"
                f"{body_md}\n"
            )
            file_path.write_text(content, encoding="utf-8")
            log.info("Pulled [%s] %s → %s/%s", ", ".join(labels) or "no label", title, folder, file_path.name)
            stats["pulled"] += 1
        except Exception as e:
            log.warning("Error pulling page '%s': %s", title, e)
            stats["errors"] += 1

    # Ensure empty folders get .gitkeep
    for folder_name in ["basic_design", "detail_design", "specs", "decisions", "meetings"]:
        folder_path = output_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        gitkeep = folder_path / ".gitkeep"
        if not any(folder_path.glob("*.md")):
            gitkeep.touch()
        elif gitkeep.exists():
            gitkeep.unlink()

    return stats
