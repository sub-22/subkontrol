"""Shared env resolver — handles unresolved plugin template strings.

When running as an installed Claude plugin, the plugin system interpolates
${user_config.FIELD} before passing env vars to MCP servers.
When running locally (dev mode), those strings arrive un-interpolated.
This module detects the un-interpolated case and falls back to .env,
then ~/.morai/config.json (written by /morai:init guided setup).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import dotenv_values, find_dotenv

# Maps env var name → (section, field) in ~/.morai/config.json
_CONFIG_KEY_MAP: dict[str, tuple[str, str]] = {
    "JIRA_URL": ("jira", "url"),
    "JIRA_EMAIL": ("jira", "email"),
    "JIRA_TOKEN": ("jira", "token"),
    "CONFLUENCE_URL": ("confluence", "url"),
    "CONFLUENCE_EMAIL": ("confluence", "email"),
    "CONFLUENCE_TOKEN": ("confluence", "token"),
    "SLACK_BOT_TOKEN": ("slack", "bot_token"),
    "SLACK_APP_TOKEN": ("slack", "app_token"),
    "SLACK_CHANNEL": ("slack", "channel"),
    "GITHUB_TOKEN": ("github", "token"),
    "BITBUCKET_USERNAME": ("bitbucket", "username"),
    "BITBUCKET_TOKEN": ("bitbucket", "token"),
    "BITBUCKET_BASE_URL": ("bitbucket", "base_url"),
}

_DOTENV: dict[str, str | None] | None = None
_CONFIG: dict | None = None


def _get_dotenv() -> dict[str, str | None]:
    global _DOTENV
    if _DOTENV is None:
        dotenv_path = find_dotenv(usecwd=True)
        _DOTENV = dotenv_values(dotenv_path) if dotenv_path else {}
    return _DOTENV


def _get_config() -> dict:
    global _CONFIG
    if _CONFIG is None:
        global_path = os.getenv("MORAI_GLOBAL_PATH", str(Path.home() / ".morai"))
        config_path = Path(global_path).expanduser() / "config.json"
        if config_path.exists():
            try:
                _CONFIG = json.loads(config_path.read_text())
            except (json.JSONDecodeError, OSError):
                _CONFIG = {}
        else:
            _CONFIG = {}
    return _CONFIG


def resolve(key: str, default: str = "") -> str:
    """Read env var; fall back to .env then ~/.morai/config.json."""
    val = os.getenv(key, "")
    if val and not val.startswith("${"):
        return val
    dotenv_val = _get_dotenv().get(key)
    if dotenv_val and not dotenv_val.startswith("${"):
        return dotenv_val
    if key in _CONFIG_KEY_MAP:
        section, field = _CONFIG_KEY_MAP[key]
        config_val = _get_config().get(section, {}).get(field, "")
        if config_val:
            return str(config_val)
    return default


def resolve_path(key: str, default: str = ".") -> Path:
    return Path(resolve(key, default))


def project_name() -> str:
    """Derive project name from CLAUDE_PROJECT_DIR, fallback to cwd name."""
    project_dir = os.getenv("CLAUDE_PROJECT_DIR", "")
    return Path(project_dir).name if project_dir else Path.cwd().name


def resolve_project_path(subdir: str) -> Path:
    """Return path for subdir, with per-subdir override support.

    Resolution order:
      1. MORAI_{SUBDIR}_PATH env var or .env (direct override — used in tests)
      2. {MORAI_GLOBAL_PATH}/{subdir}-{project_name()} (default)
    """
    override = resolve(f"MORAI_{subdir.upper()}_PATH", "")
    if override:
        return Path(override)
    base = resolve("MORAI_GLOBAL_PATH", str(Path.home() / ".morai"))
    return Path(base) / f"{subdir}-{project_name()}"
