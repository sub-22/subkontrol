"""Morai MCP server — Telegram integration tools."""

import time

import httpx
from mcp.server.fastmcp import FastMCP

from servers._env import resolve

mcp = FastMCP("morai-telegram")

TELEGRAM_BOT_TOKEN = resolve("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEFAULT_CHAT_ID = resolve("TELEGRAM_CHAT_ID")
_NOT_CONFIGURED = "morai-telegram not configured — set TELEGRAM_BOT_TOKEN in .env"
_API_BASE = "https://api.telegram.org/bot{token}"


def _is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN)


def _call(method: str, **params: object) -> dict:
    url = f"{_API_BASE.format(token=TELEGRAM_BOT_TOKEN)}/{method}"
    resp = httpx.post(url, json=params, timeout=30.0)
    resp.raise_for_status()
    body: dict = resp.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body.get('description', body)}")
    result: dict = body["result"]
    return result


@mcp.tool()
def send_message(chat_id: str = "", text: str = "", reply_to_message_id: int | None = None) -> str:
    """Gửi message đến Telegram chat.

    Args:
        chat_id: Chat ID hoặc @channel_username. Để trống = dùng TELEGRAM_CHAT_ID từ config
        text: Nội dung message (supports Telegram Markdown)
        reply_to_message_id: Message ID để reply vào (optional)
    Returns:
        Message ID hoặc error string
    """
    if not _is_configured():
        return _NOT_CONFIGURED
    target = chat_id or TELEGRAM_DEFAULT_CHAT_ID
    if not target:
        return "TELEGRAM_NO_CHAT: set TELEGRAM_CHAT_ID in plugin config hoặc truyền chat_id vào"
    params: dict[str, object] = {"chat_id": target, "text": text, "parse_mode": "Markdown"}
    if reply_to_message_id:
        params["reply_to_message_id"] = reply_to_message_id
    result = _call("sendMessage", **params)
    return str(result["message_id"])


@mcp.tool()
def get_pending_messages(chat_id: str = "", since_update_id: int | None = None) -> list[dict]:
    """Lấy messages gần nhất gửi tới bot (qua getUpdates long-poll).

    Args:
        chat_id: Lọc theo chat ID — để trống = lấy tất cả chat
        since_update_id: Chỉ lấy updates sau update_id này (optional — dùng để tránh đọc trùng)
    Returns:
        List of {"update_id": int, "message_id": int, "user": str, "text": str, "chat_id": str}
    """
    if not _is_configured():
        return [{"error": _NOT_CONFIGURED}]
    params: dict[str, object] = {"timeout": 0}
    if since_update_id is not None:
        params["offset"] = since_update_id + 1
    updates = _call("getUpdates", **params)
    target = chat_id or TELEGRAM_DEFAULT_CHAT_ID
    out = []
    for upd in updates:
        msg = upd.get("message")
        if not msg or "text" not in msg:
            continue
        msg_chat_id = str(msg["chat"]["id"])
        if target and msg_chat_id != str(target):
            continue
        out.append(
            {
                "update_id": upd["update_id"],
                "message_id": msg["message_id"],
                "user": msg.get("from", {}).get("username", "unknown"),
                "text": msg["text"],
                "chat_id": msg_chat_id,
            }
        )
    return out


@mcp.tool()
def request_approval(
    chat_id: str,
    message: str,
    context: str = "",
    timeout_seconds: int = 300,
) -> str:
    """Gửi approval request lên Telegram kèm nút ✅/❌ và chờ human bấm.

    Post message với inline keyboard, poll callback_query trong timeout.

    Args:
        chat_id: Telegram chat ID để gửi request
        message: Mô tả action cần approve
        context: Context thêm để human quyết định
        timeout_seconds: Thời gian chờ tối đa (default 5 phút)
    Returns:
        "approved" | "rejected" | "timeout" | error string
    """
    if not _is_configured():
        return f"TELEGRAM_NOT_CONFIGURED: Cannot send approval request. Decide manually: {message}"

    text = f"*Approval needed*\n{message}"
    if context:
        text += f"\n\n_{context}_"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve", "callback_data": "approve"},
                {"text": "❌ Reject", "callback_data": "reject"},
            ]
        ]
    }
    sent = _call(
        "sendMessage",
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    sent_message_id = sent["message_id"]

    deadline = time.monotonic() + timeout_seconds
    last_update_id: int | None = None
    while time.monotonic() < deadline:
        remaining = max(1, int(deadline - time.monotonic()))
        params: dict[str, object] = {"timeout": min(20, remaining)}
        if last_update_id is not None:
            params["offset"] = last_update_id + 1
        updates = _call("getUpdates", **params)
        for upd in updates:
            last_update_id = upd["update_id"]
            cq = upd.get("callback_query")
            if not cq or cq.get("message", {}).get("message_id") != sent_message_id:
                continue
            answer = "approve" if cq["data"] == "approve" else "reject"
            _call("answerCallbackQuery", callback_query_id=cq["id"])
            return "approved" if answer == "approve" else "rejected"
    return "timeout"
