"""Git MCP server — status, diff, commit, branch, push, PR operations."""

import os
import subprocess
from pathlib import Path
from typing import cast

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("morai-git")

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))


def _run(cmd: list[str], check: bool = True) -> dict:
    """Run a shell command and return structured result."""
    result = subprocess.run(
        cmd,
        cwd=WORKSPACE_ROOT,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        return {
            "ok": False,
            "error": result.stderr.strip() or f"Command failed: {' '.join(cmd)}",
            "stdout": result.stdout.strip(),
            "returncode": result.returncode,
        }
    return {
        "ok": result.returncode == 0,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else "",
        "returncode": result.returncode,
    }


def _run_str(cmd: list[str]) -> str:
    """Run a command and return stdout string (raises on failure)."""
    result = _run(cmd)
    if not result["ok"]:
        raise RuntimeError(cast(str, result["error"]))
    return cast(str, result["output"])


@mcp.tool()
def status() -> str:
    """Lấy git status của workspace."""
    return _run_str(["git", "status", "--short"])


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
    return _run_str(args)


@mcp.tool()
def commit(message: str, files: list[str] | None = None) -> dict:
    """Stage files và tạo commit.

    Args:
        message: Commit message
        files: List of relative paths cần stage. None = stage tất cả tracked changes
    Returns:
        {"ok": bool, "output": str, "error": str}
    """
    if files:
        result = _run(["git", "add"] + files)
    else:
        result = _run(["git", "add", "-u"])  # only tracked files, not untracked
    if not result["ok"]:
        return result
    return _run(["git", "commit", "-m", message])


@mcp.tool()
def create_branch(branch_name: str) -> dict:
    """Tạo và checkout branch mới.

    Args:
        branch_name: Tên branch, e.g. "feat/PROJ-123-add-login"
    Returns:
        {"ok": bool, "output": str, "error": str}
    """
    return _run(["git", "checkout", "-b", branch_name])


@mcp.tool()
def get_current_branch() -> str:
    """Lấy tên branch hiện tại."""
    return _run_str(["git", "rev-parse", "--abbrev-ref", "HEAD"])


@mcp.tool()
def get_log(max_count: int = 10) -> str:
    """Lấy git log gần nhất.

    Args:
        max_count: Số commits cần lấy
    """
    return _run_str(["git", "log", f"--max-count={max_count}", "--oneline"])


@mcp.tool()
def push(branch: str = "", force: bool = False) -> dict:
    """Push branch lên remote.

    Args:
        branch: Tên branch cần push. Để trống = current branch
        force: Force push (chỉ dùng cho feature branches chưa merge)
    Returns:
        {"ok": bool, "output": str, "error": str}
    """
    target = branch or _run_str(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    args = ["git", "push", "--set-upstream", "origin", target]
    if force:
        args.append("--force-with-lease")
    return _run(args)


@mcp.tool()
def create_pr(
    title: str,
    body: str,
    base: str = "main",
    draft: bool = False,
) -> dict:
    """Tạo Pull Request trên GitHub (requires `gh` CLI).

    Args:
        title: PR title
        body: PR description (markdown)
        base: Target branch để merge vào (default: main)
        draft: Tạo draft PR
    Returns:
        {"ok": bool, "url": str, "error": str}
    """
    args = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    if draft:
        args.append("--draft")

    result = _run(args, check=False)
    if result["ok"]:
        return {"ok": True, "url": result["output"], "error": ""}
    return {"ok": False, "url": "", "error": result["error"]}


@mcp.tool()
def get_pr_template() -> dict:
    """Đọc PR template của project, fallback về subkontrol templates.

    Lookup order:
      1. .github/PULL_REQUEST_TEMPLATE.md
      2. .github/pull_request_template.md
      3. .github/PULL_REQUEST_TEMPLATE/*.md (trả về tất cả)
      4. docs/pull_request_template.md
      5. Fallback: subkontrol templates (feature / bugfix / refactor)

    Returns:
        {
          "source": "project" | "subkontrol",
          "templates": {"<name>": "<content>", ...}
        }
    """
    # Project template locations
    candidates = [
        WORKSPACE_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md",
        WORKSPACE_ROOT / ".github" / "pull_request_template.md",
        WORKSPACE_ROOT / "docs" / "pull_request_template.md",
    ]
    for path in candidates:
        if path.exists():
            return {"source": "project", "templates": {"default": path.read_text(encoding="utf-8")}}

    # Multi-template directory
    multi_dir = WORKSPACE_ROOT / ".github" / "PULL_REQUEST_TEMPLATE"
    if multi_dir.is_dir():
        templates = {f.stem: f.read_text(encoding="utf-8") for f in sorted(multi_dir.glob("*.md"))}
        if templates:
            return {"source": "project", "templates": templates}

    # Fallback: subkontrol built-in templates
    subkontrol_tpl = Path(__file__).parent.parent.parent / "templates" / "pr"
    templates = {}
    if subkontrol_tpl.is_dir():
        for f in sorted(subkontrol_tpl.glob("*.md")):
            templates[f.stem] = f.read_text(encoding="utf-8")
    return {"source": "subkontrol", "templates": templates}


@mcp.tool()
def get_pr_diff(pr_number: int | None = None) -> str:
    """Lấy diff của PR hiện tại hoặc một PR cụ thể.

    Args:
        pr_number: PR number. None = PR của current branch
    """
    if pr_number:
        return _run_str(["gh", "pr", "diff", str(pr_number)])
    return _run_str(["gh", "pr", "diff"])


@mcp.tool()
def add_pr_comment(body: str, pr_number: int | None = None) -> dict:
    """Comment lên PR.

    Args:
        body: Nội dung comment (markdown)
        pr_number: PR number. None = PR của current branch
    """
    args = ["gh", "pr", "comment", "--body", body]
    if pr_number:
        args.append(str(pr_number))
    return _run(args)


if __name__ == "__main__":
    mcp.run()
