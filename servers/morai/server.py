"""Morai MCP server — Slack integration via Socket Mode."""

import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-slack")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

_NOT_CONFIGURED = "morai-slack not configured — set SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env"


def _is_configured() -> bool:
    return bool(SLACK_BOT_TOKEN and SLACK_APP_TOKEN)


@mcp.tool()
def send_message(channel: str, text: str, thread_ts: str | None = None) -> str:
    """Gửi message đến Slack channel.

    Args:
        channel: Channel ID hoặc name, e.g. "#dev-pipeline" hoặc "C01234"
        text: Nội dung message (supports Slack markdown)
        thread_ts: Thread timestamp nếu muốn reply vào thread
    Returns:
        Message timestamp (ts) hoặc error string nếu chưa configure
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    # TODO: implement Slack WebClient.chat_postMessage
    return f"morai-slack: send_message not yet implemented. channel={channel}"


@mcp.tool()
def request_approval(channel: str, message: str, context: str = "") -> str:
    """Gửi approval request và chờ human react ✅ hoặc ❌.

    Args:
        channel: Slack channel để gửi request
        message: Mô tả action cần approve
        context: Context thêm để human quyết định
    Returns:
        "approved" | "rejected" | error string
    """
    if not _is_configured():
        # Slack not configured — surface to LLM to ask user directly instead
        return f"SLACK_NOT_CONFIGURED: Cannot send approval request. Ask the user directly: {message}"  # noqa: E501
    # TODO: implement approval flow với Block Kit buttons
    return f"morai-slack: request_approval not yet implemented. Ask the user directly: {message}"


@mcp.tool()
def get_thread(channel: str, thread_ts: str) -> list[dict]:
    """Đọc toàn bộ messages trong một Slack thread.

    Args:
        channel: Channel ID
        thread_ts: Thread timestamp
    Returns:
        List of {"user": str, "text": str, "ts": str}
    """
    if not _is_configured():
        return [{"error": _NOT_CONFIGURED}]
    # TODO: implement conversations.replies
    return [{"error": f"morai-slack: get_thread not yet implemented. thread_ts={thread_ts}"}]


@mcp.tool()
def get_pending_messages(channel: str) -> list[dict]:
    """Lấy messages chưa được xử lý từ channel.

    Args:
        channel: Channel ID
    """
    if not _is_configured():
        return [{"error": _NOT_CONFIGURED}]
    # TODO: implement message queue
    return [{"error": f"morai-slack: get_pending_messages not yet implemented. channel={channel}"}]


if __name__ == "__main__":
    mcp.run()
