"""Git MCP server — status, diff, commit, PR operations."""

import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-git")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


@mcp.tool()
def status() -> str:
    """Lấy git status của workspace."""
    return _run(["git", "status", "--short"])


@mcp.tool()
def diff(base: str = "HEAD", target: str = "") -> str:
    """Lấy git diff giữa hai refs.

    Args:
        base: Base ref, e.g. "main" hoặc "HEAD"
        target: Target ref, để trống = working tree
    """
    args = ["git", "diff", base]
    if target:
        args.append(target)
    return _run(args)


@mcp.tool()
def commit(message: str, files: list[str] | None = None) -> str:
    """Stage files và tạo commit.

    Args:
        message: Commit message
        files: List of relative paths cần stage. None = stage tất cả changes
    """
    if files:
        _run(["git", "add"] + files)
    else:
        _run(["git", "add", "-A"])
    return _run(["git", "commit", "-m", message])


@mcp.tool()
def create_branch(branch_name: str) -> str:
    """Tạo và checkout branch mới.

    Args:
        branch_name: Tên branch, e.g. "feat/PROJ-123-add-login"
    """
    return _run(["git", "checkout", "-b", branch_name])


@mcp.tool()
def get_log(max_count: int = 10) -> str:
    """Lấy git log gần nhất.

    Args:
        max_count: Số commits cần lấy
    """
    return _run(["git", "log", f"--max-count={max_count}", "--oneline"])


if __name__ == "__main__":
    mcp.run()
