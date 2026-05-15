"""Morai Memory MCP server — long-term memory: episodes, preferences, reflexes."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-memory")

MEMORY_ROOT = Path(os.getenv("MORAI_MEMORY_PATH", ".morai/memory"))


def _ensure_dirs() -> None:
    for d in ["", "archive"]:
        (MEMORY_ROOT / d).mkdir(parents=True, exist_ok=True)


def _read_md(filename: str) -> str:
    path = MEMORY_ROOT / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _append_md(filename: str, content: str) -> None:
    _ensure_dirs()
    path = MEMORY_ROOT / filename
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n{content}\n")


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


# ── Episodes ──────────────────────────────────────────────────────────────────


@mcp.tool()
def record_episode(
    event: str,
    outcome: str,
    lesson: str,
    ticket_id: str = "",
    signal: str = "[ESTIMATED] [LOW]",
    apply_next: str = "",
) -> str:
    """Ghi một episode vào long-term memory.

    Args:
        event: Mô tả sự kiện xảy ra
        outcome: "success" | "partial" | "fail"
        lesson: Điều được học từ episode này
        ticket_id: Ticket liên quan (optional)
        signal: Internal signal tag, e.g. "[CERTAIN] [MED]"
        apply_next: Hành động cụ thể cho lần sau
    """
    tag = f"[{ticket_id}] " if ticket_id else ""
    entry = f"""## {_now()} {tag}— {event}
- **Outcome**: {outcome}
- **Signal**: {signal}
- **Lesson**: {lesson}
- **Apply next**: {apply_next or "N/A"}
"""
    _append_md("episodes.md", entry)

    # Track pattern count
    patterns = _load_patterns()
    patterns[event] = patterns.get(event, 0) + 1
    _save_patterns(patterns)

    return f"Episode recorded. Pattern '{event}' count: {patterns[event]}"


@mcp.tool()
def get_episodes(limit: int = 10, filter_event: str = "") -> str:
    """Lấy recent episodes từ memory.

    Args:
        limit: Số episodes gần nhất cần lấy
        filter_event: Filter theo event type (optional)
    """
    content = _read_md("episodes.md")
    if not content:
        return "Chưa có episodes nào."

    blocks = [b.strip() for b in content.split("##") if b.strip()]
    if filter_event:
        blocks = [b for b in blocks if filter_event.lower() in b.lower()]

    return "## " + "\n\n## ".join(blocks[-limit:]) if blocks else "Không tìm thấy episodes."


# ── Preferences ───────────────────────────────────────────────────────────────


@mcp.tool()
def get_preferences() -> str:
    """Lấy toàn bộ user preferences đã học."""
    content = _read_md("preferences.md")
    return content if content else "Chưa có preferences. Sẽ học dần qua usage."


@mcp.tool()
def update_preference(key: str, value: str, source: str = "user_feedback") -> str:
    """Cập nhật hoặc thêm một user preference.

    Args:
        key: Preference key, e.g. "coding_style.indent"
        value: Giá trị mới
        source: Nguồn thay đổi: "user_feedback" | "observed" | "inferred"
    """
    _ensure_dirs()
    path = MEMORY_ROOT / "preferences.md"

    content = path.read_text(encoding="utf-8") if path.exists() else "# Morai — User Preferences\n"

    entry = f"\n### {key}\n- **Value**: {value}\n- **Source**: {source}\n- **Updated**: {_now()}\n"

    # Replace existing entry if key exists
    marker = f"### {key}"
    if marker in content:
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if line.strip() == marker:
                skip = True
                new_lines.append(entry)
            elif skip and line.startswith("### "):
                skip = False
                new_lines.append(line)
            elif not skip:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        content += entry

    path.write_text(content, encoding="utf-8")
    return f"Preference updated: {key} = {value}"


# ── Patterns & Reflexes ───────────────────────────────────────────────────────


def _load_patterns() -> dict[str, int]:
    path = MEMORY_ROOT / "patterns.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_patterns(patterns: dict[str, int]) -> None:
    _ensure_dirs()
    (MEMORY_ROOT / "patterns.json").write_text(json.dumps(patterns, indent=2, ensure_ascii=False))


@mcp.tool()
def get_pattern_counts() -> dict[str, int]:
    """Lấy số lần xuất hiện của các patterns."""
    patterns = _load_patterns()
    return dict(sorted(patterns.items(), key=lambda x: x[1], reverse=True))


@mcp.tool()
def get_reflex_candidates(min_count: int = 3) -> list[dict]:
    """Tìm patterns đủ điều kiện promote thành reflex (≥ min_count lần).

    Args:
        min_count: Ngưỡng tối thiểu để promote
    """
    patterns = _load_patterns()
    reflexes_content = _read_md("reflexes.md")

    candidates = []
    for event, count in patterns.items():
        if count >= min_count and event not in reflexes_content:
            candidates.append({"pattern": event, "count": count, "status": "ready_to_promote"})

    return candidates


@mcp.tool()
def promote_to_reflex(
    pattern: str, trigger: str, action: str, signal: str = "[ESTIMATED] [MED]"
) -> str:
    """Promote một pattern thành reflex chính thức.

    Args:
        pattern: Tên pattern
        trigger: Điều kiện kích hoạt reflex
        action: Hành động tự động khi trigger
        signal: Signal level của reflex này
    """
    patterns = _load_patterns()
    count = patterns.get(pattern, 0)

    entry = f"""
### R-AUTO — {pattern}
- **Trigger**: {trigger}
- **Signal**: {signal}
- **Action**: {action}
- **Promoted**: {_now()} (after {count} occurrences)
- **Source**: auto-promoted by evolve
"""
    _append_md("reflexes.md", entry)
    record_episode(
        event="reflex_promoted",
        outcome="success",
        lesson=f"Pattern '{pattern}' promoted to reflex after {count} occurrences",
        signal="[CERTAIN] [LOW]",
    )
    return f"Reflex promoted: {pattern}"


@mcp.tool()
def get_reflexes() -> str:
    """Lấy toàn bộ reflexes đã được promote."""
    content = _read_md("reflexes.md")
    return content if content else "Chưa có auto-promoted reflexes."


# ── Pipeline State ────────────────────────────────────────────────────────────


@mcp.tool()
def save_pipeline_state(ticket_id: str, state: dict) -> str:
    """Lưu trạng thái pipeline cho một ticket.

    Args:
        ticket_id: Jira ticket ID
        state: Dict với current_step, completed_steps, paths, etc.
    """
    pipeline_dir = Path(".morai/pipeline") / ticket_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    state["last_updated"] = _now()
    state["ticket_id"] = ticket_id

    (pipeline_dir / "state.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return f"Pipeline state saved: {ticket_id} @ {state.get('current_step', 'unknown')}"


@mcp.tool()
def get_pipeline_state(ticket_id: str) -> dict:
    """Lấy trạng thái pipeline của một ticket.

    Args:
        ticket_id: Jira ticket ID
    """
    path = Path(".morai/pipeline") / ticket_id / "state.json"
    if not path.exists():
        return {"error": f"Không tìm thấy pipeline state cho {ticket_id}"}
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def list_active_pipelines() -> list[dict]:
    """Liệt kê tất cả pipelines đang active (chưa complete)."""
    pipeline_root = Path(".morai/pipeline")
    if not pipeline_root.exists():
        return []

    active = []
    for state_file in pipeline_root.glob("*/state.json"):
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("status") != "complete":
            active.append(
                {
                    "ticket_id": state.get("ticket_id"),
                    "current_step": state.get("current_step"),
                    "last_updated": state.get("last_updated"),
                    "blocked_reason": state.get("blocked_reason"),
                }
            )

    return sorted(active, key=lambda x: x.get("last_updated", ""), reverse=True)


# ── Memory Decay ─────────────────────────────────────────────────────────────


@mcp.tool()
def archive_old_episodes(days: int = 90) -> str:
    """Archive episodes cũ hơn `days` ngày vào thư mục archive/.

    Args:
        days: Số ngày tối đa giữ episode (default: 90)
    Returns:
        Số episodes đã archive
    """
    _ensure_dirs()
    content = _read_md("episodes.md")
    if not content:
        return "Không có episodes để archive."

    cutoff = datetime.now(UTC) - timedelta(days=days)
    # Episode header format: "## YYYY-MM-DD HH:MM UTC ..."
    date_pattern = re.compile(r"^## (\d{4}-\d{2}-\d{2})")

    blocks = [b for b in content.split("##") if b.strip()]
    keep: list[str] = []
    archive: list[str] = []

    for block in blocks:
        match = date_pattern.match(block.strip())
        if match:
            try:
                ep_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
                if ep_date < cutoff:
                    archive.append(block)
                    continue
            except ValueError:
                pass
        keep.append(block)

    if not archive:
        return f"Không có episodes nào cũ hơn {days} ngày."

    # Write archive
    archive_filename = f"archive/episodes_{datetime.now(UTC).strftime('%Y%m%d')}.md"
    archive_content = "## " + "\n\n## ".join(archive)
    _ensure_dirs()
    (MEMORY_ROOT / archive_filename).write_text(archive_content, encoding="utf-8")

    # Rewrite episodes.md with only kept entries
    (MEMORY_ROOT / "episodes.md").write_text(
        "## " + "\n\n## ".join(keep) if keep else "", encoding="utf-8"
    )

    return f"Archived {len(archive)} episodes → {archive_filename}. Kept {len(keep)}."


if __name__ == "__main__":
    mcp.run()
