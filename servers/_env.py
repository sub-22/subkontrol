"""Shared env resolver — handles unresolved plugin template strings.

When running as an installed Claude plugin, the plugin system interpolates
${user_config.FIELD} before passing env vars to MCP servers.
When running locally (dev mode), those strings arrive un-interpolated.
This module detects the un-interpolated case and falls back to .env.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, find_dotenv


def _dotenv_cache() -> dict[str, str | None]:
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        return dotenv_values(dotenv_path)
    return {}


_DOTENV: dict[str, str | None] | None = None


def _get_dotenv() -> dict[str, str | None]:
    global _DOTENV
    if _DOTENV is None:
        _DOTENV = _dotenv_cache()
    return _DOTENV


def resolve(key: str, default: str = "") -> str:
    """Read env var; fall back to .env if value is an unresolved plugin template."""
    val = os.getenv(key, "")
    if val and not val.startswith("${"):
        return val
    # Unresolved or missing — try .env
    dotenv_val = _get_dotenv().get(key)
    if dotenv_val and not dotenv_val.startswith("${"):
        return dotenv_val
    return default


def resolve_path(key: str, default: str = ".") -> Path:
    return Path(resolve(key, default))
