"""Repo manager — resolve, clone, hoặc create project-design repo."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _repo_name(project_name: str) -> str:
    return f"{project_name.lower().replace(' ', '-')}-design"


def _clone(repo_url: str, output_dir: Path) -> Path:
    log.info("Cloning %s → %s", repo_url, output_dir)
    _run(["git", "clone", repo_url, str(output_dir)])
    return output_dir


def _pull_latest(repo_dir: Path) -> Path:
    log.info("Repo exists at %s — pulling latest", repo_dir)
    _run(["git", "pull", "--rebase"], cwd=repo_dir, check=False)
    return repo_dir


def _init_local(output_dir: Path, project_name: str) -> Path:
    log.info("Creating local repo at %s", output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _run(["git", "init"], cwd=output_dir)
    _run(["git", "checkout", "-b", "main"], cwd=output_dir, check=False)
    (output_dir / ".gitkeep").touch()
    _run(["git", "add", ".gitkeep"], cwd=output_dir)
    _run(["git", "commit", "-m", f"chore: init {project_name}-design"], cwd=output_dir)
    return output_dir


def _create_github_repo(org: str, repo_name: str, token: str) -> str | None:
    import json
    import urllib.error
    import urllib.request

    url = f"https://api.github.com/orgs/{org}/repos"
    data = json.dumps({"name": repo_name, "private": True, "auto_init": False}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["clone_url"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "already exists" in body:
            return f"https://github.com/{org}/{repo_name}.git"
        log.warning("GitHub repo creation failed: %s", body)
        return None


def _check_remote_exists(repo_url: str) -> bool:
    return _run(["git", "ls-remote", repo_url], check=False).returncode == 0


def _run_scan(source_dir: Path, design_dir: Path) -> bool:
    """Chạy /morai:scan trên source_dir, copy kết quả vào design_dir/knowledge/.

    Returns True nếu scan thành công.
    """
    claude_cli = shutil.which("claude")
    if not claude_cli:
        log.warning("claude CLI not found — cannot scan source repo")
        return False

    log.info("Running /morai:scan on %s...", source_dir)
    result = subprocess.run(
        [claude_cli, "-p", f"/morai:scan {source_dir}", "--output-format", "json"],
        cwd=source_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )

    knowledge_src = source_dir / ".morai" / "knowledge"
    if not knowledge_src.exists():
        log.warning("Scan completed but .morai/knowledge/ not found")
        return False

    knowledge_dst = design_dir / "knowledge"
    knowledge_dst.mkdir(parents=True, exist_ok=True)

    for f in knowledge_src.iterdir():
        if f.is_file():
            shutil.copy(f, knowledge_dst / f.name)
            log.info("Copied knowledge: %s", f.name)

    # Copy CLAUDE.md nếu scan sinh ra
    claude_md = source_dir / "CLAUDE.md"
    if claude_md.exists():
        shutil.copy(claude_md, design_dir / "knowledge" / "CLAUDE.source.md")

    log.info("Scan complete — knowledge copied to %s", knowledge_dst)
    return True


def scan_source_repo(source_url: str, design_dir: Path) -> bool:
    """Clone source repo tạm, scan, copy knowledge sang design repo, xóa clone.

    Args:
        source_url: Git URL của source code repo
        design_dir: Path tới design repo đã được init
    Returns:
        True nếu thành công
    """
    with tempfile.TemporaryDirectory(prefix="morai-scan-") as tmp:
        tmp_path = Path(tmp) / "source"
        log.info("Cloning source repo for scan: %s", source_url)
        result = _run(["git", "clone", "--depth=1", source_url, str(tmp_path)], check=False)
        if result.returncode != 0:
            log.error("Failed to clone source repo: %s", result.stderr)
            return False
        return _run_scan(tmp_path, design_dir)


def resolve(
    project_name: str,
    output_dir: Path,
    git_org: str = "",
    git_host: str = "",
) -> tuple[Path, bool]:
    """Resolve design repo: pull nếu exists, tạo mới nếu không.

    Returns:
        (repo_path, is_new) — is_new=True khi vừa tạo mới
    """
    repo_name = _repo_name(project_name)

    if not git_host:
        if os.getenv("GITHUB_TOKEN"):
            git_host = "github"
        elif os.getenv("BITBUCKET_TOKEN"):
            git_host = "bitbucket"

    remote_url = ""
    if git_org and git_host == "github":
        remote_url = f"https://github.com/{git_org}/{repo_name}.git"
    elif git_org and git_host == "bitbucket":
        remote_url = f"https://bitbucket.org/{git_org}/{repo_name}.git"

    # Đã có local → pull
    if (output_dir / ".git").exists():
        return _pull_latest(output_dir), False

    # Clone nếu remote exists
    if remote_url and _check_remote_exists(remote_url):
        return _clone(remote_url, output_dir), False

    # Tạo mới trên GitHub
    if git_org and git_host == "github":
        token = os.getenv("GITHUB_TOKEN", "")
        if token:
            clone_url = _create_github_repo(git_org, repo_name, token)
            if clone_url:
                repo = _init_local(output_dir, project_name)
                _run(["git", "remote", "add", "origin", clone_url], cwd=output_dir)
                _run(["git", "push", "-u", "origin", "main"], cwd=output_dir, check=False)
                log.info("Created GitHub repo: %s", clone_url)
                return repo, True

    log.info("No remote configured — creating local repo only")
    return _init_local(output_dir, project_name), True
