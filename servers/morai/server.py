"""Morai MCP server — Slack integration via Socket Mode."""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-slack")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")


@mcp.tool()
def send_message(channel: str, text: str, thread_ts: str | None = None) -> str:
    """Gửi message đến Slack channel.

    Args:
        channel: Channel ID hoặc name, e.g. "#dev-pipeline" hoặc "C01234"
        text: Nội dung message (supports Slack markdown)
        thread_ts: Thread timestamp nếu muốn reply vào thread
    Returns:
        Message timestamp (ts)
    """
    # TODO: implement Slack WebClient.chat_postMessage
    raise NotImplementedError


@mcp.tool()
def request_approval(channel: str, message: str, context: str = "") -> str:
    """Gửi approval request và chờ human react ✅ hoặc ❌.

    Args:
        channel: Slack channel để gửi request
        message: Mô tả action cần approve
        context: Context thêm để human quyết định
    Returns:
        "approved" | "rejected"
    """
    # TODO: implement approval flow với Block Kit buttons
    raise NotImplementedError


@mcp.tool()
def get_thread(channel: str, thread_ts: str) -> list[dict]:
    """Đọc toàn bộ messages trong một Slack thread.

    Args:
        channel: Channel ID
        thread_ts: Thread timestamp
    Returns:
        List of {"user": str, "text": str, "ts": str}
    """
    # TODO: implement conversations.replies
    raise NotImplementedError


@mcp.tool()
def get_pending_messages(channel: str) -> list[dict]:
    """Lấy messages chưa được xử lý từ channel.

    Args:
        channel: Channel ID
    """
    # TODO: implement message queue
    raise NotImplementedError


if __name__ == "__main__":
    mcp.run()
