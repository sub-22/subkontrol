"""Morai MCP server — Slack integration tools."""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from servers._env import resolve

mcp = FastMCP("morai-slack")

SLACK_BOT_TOKEN = resolve("SLACK_BOT_TOKEN")
SLACK_DEFAULT_CHANNEL = resolve("SLACK_CHANNEL")
_NOT_CONFIGURED = "morai-slack not configured — set SLACK_BOT_TOKEN in .env"


def _client() -> "Any":
    from slack_sdk import WebClient

    return WebClient(token=SLACK_BOT_TOKEN)


def _is_configured() -> bool:
    return bool(SLACK_BOT_TOKEN)


@mcp.tool()
def send_message(channel: str = "", text: str = "", thread_ts: str | None = None) -> str:
    """Gửi message đến Slack channel hoặc thread.

    Args:
        channel: Channel ID hoặc name, e.g. "#dev-pipeline". Để trống = dùng SLACK_CHANNEL từ config.
        text: Nội dung message (supports Slack mrkdwn)
        thread_ts: Thread timestamp để reply vào thread (optional)
    Returns:
        Message timestamp (ts) hoặc error string
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    target = channel or SLACK_DEFAULT_CHANNEL
    if not target:
        return "SLACK_NO_CHANNEL: set SLACK_CHANNEL in plugin config hoặc truyền channel vào"
    kwargs: dict = {"channel": target, "text": text}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    resp = _client().chat_postMessage(**kwargs)
    return str(resp["ts"])


@mcp.tool()
def get_thread(channel: str, thread_ts: str) -> list[dict]:
    """Đọc toàn bộ messages trong một Slack thread.

    Args:
        channel: Channel ID
        thread_ts: Thread timestamp (ts của message gốc)
    Returns:
        List of {"user": str, "text": str, "ts": str}
    """
    if not _is_configured():
        return [{"error": _NOT_CONFIGURED}]
    resp = _client().conversations_replies(channel=channel, ts=thread_ts)
    return [
        {
            "user": m.get("user", m.get("bot_id", "unknown")),
            "text": m.get("text", ""),
            "ts": m["ts"],
        }
        for m in resp.get("messages", [])
    ]


@mcp.tool()
def get_pending_messages(channel: str, since_ts: str | None = None) -> list[dict]:
    """Lấy messages gần nhất từ channel.

    Args:
        channel: Channel ID
        since_ts: Chỉ lấy messages sau timestamp này (optional)
    Returns:
        List of {"user": str, "text": str, "ts": str}
    """
    if not _is_configured():
        return [{"error": _NOT_CONFIGURED}]
    kwargs: dict = {"channel": channel, "limit": 20}
    if since_ts:
        kwargs["oldest"] = since_ts
    resp = _client().conversations_history(**kwargs)
    return [
        {
            "user": m.get("user", m.get("bot_id", "unknown")),
            "text": m.get("text", ""),
            "ts": m["ts"],
        }
        for m in resp.get("messages", [])
        if not m.get("bot_id")
    ]


@mcp.tool()
def request_approval(
    channel: str,
    message: str,
    context: str = "",
    timeout_seconds: int = 300,
) -> str:
    """Gửi approval request lên Slack và chờ human react ✅ hoặc ❌.

    Post message với hướng dẫn react, poll reactions trong timeout.

    Args:
        channel: Slack channel để gửi request
        message: Mô tả action cần approve
        context: Context thêm để human quyết định
        timeout_seconds: Thời gian chờ tối đa (default 5 phút)
    Returns:
        "approved" | "rejected" | "timeout" | error string
    """
    if not _is_configured():
        return f"SLACK_NOT_CONFIGURED: Cannot send approval request. Decide manually: {message}"

    client = _client()
    body = f"*Approval required*\n{message}"
    if context:
        body += f"\n\n_{context}_"
    body += "\n\nReact ✅ to approve or ❌ to reject."

    post_resp = client.chat_postMessage(channel=channel, text=body)
    msg_ts = post_resp["ts"]

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        time.sleep(5)
        react_resp = client.reactions_get(channel=channel, timestamp=msg_ts)
        reactions = {
            r["name"]: r["count"] for r in react_resp.get("message", {}).get("reactions", [])
        }
        if reactions.get("white_check_mark", 0) > 0:
            return "approved"
        if reactions.get("x", 0) > 0:
            return "rejected"

    return "timeout"


if __name__ == "__main__":
    mcp.run()
