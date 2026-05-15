"""morai-onboard — CLI để bootstrap project-design knowledge repo.

Usage:
    # Dev — full onboard (Confluence + Jira)
    uv run python scripts/onboard.py --role dev --project PROJ --project-name subkontrol

    # Dev — không có Confluence/Jira (base on source code)
    uv run python scripts/onboard.py --role dev --project-name subkontrol

    # Non-dev — pull design repo nếu có, fallback scan source
    uv run python scripts/onboard.py --role non-dev --project-name subkontrol \\
        --source-repo https://github.com/org/subkontrol.git

    # Update (sync content mới)
    uv run python scripts/onboard.py --role dev --project PROJ --project-name subkontrol --update

    # Với GitHub org
    uv run python scripts/onboard.py --role dev --project PROJ --project-name subkontrol \\
        --git-org my-org
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
log = logging.getLogger("morai-onboard")

_DEV_MAPPING_PATH = Path(__file__).parent.parent / "config" / "dev_mapping.json"


def _git(field: str) -> str:
    try:
        return subprocess.check_output(["git", "config", field], text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def _fetch_jira_account_id(email: str) -> str:
    """Try to resolve Jira account ID via /rest/api/3/myself using configured credentials."""
    try:
        import base64
        import urllib.parse
        import urllib.request
        jira_url = os.getenv("JIRA_URL", "").rstrip("/")
        jira_email = os.getenv("JIRA_EMAIL", "")
        jira_token = os.getenv("JIRA_TOKEN", "")
        if not all([jira_url, jira_email, jira_token]):
            return ""
        creds = base64.b64encode(f"{jira_email}:{jira_token}".encode()).decode()
        req = urllib.request.Request(
            f"{jira_url}/rest/api/3/myself",
            headers={"Authorization": f"Basic {creds}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            import json as _json
            data = _json.loads(resp.read())
            return data.get("accountId", "")
    except Exception:
        return ""


def _register_dev_mapping(project_keys: list[str]) -> None:
    """Detect git identity và register vào config/dev_mapping.json."""
    import json as _json

    email = _git("user.email")
    name = _git("user.name")
    if not email:
        log.warning("Không detect được git user.email — bỏ qua dev mapping")
        return

    _DEV_MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapping = _json.loads(_DEV_MAPPING_PATH.read_text()) if _DEV_MAPPING_PATH.exists() else {
        "_comment": "Maps git identity → Jira assignee. Key = git user.email.",
        "devs": {},
        "defaults": {
            "max_tasks": 10,
            "priority_order": ["Blocker", "Critical", "High", "Medium", "Low", "Trivial"],
            "status_filter": ["To Do", "In Progress", "Open"],
            "sprint_only": True,
        },
    }

    if email in mapping.get("devs", {}):
        log.info("Dev mapping đã tồn tại cho %s — bỏ qua", email)
        return

    account_id = _fetch_jira_account_id(email)
    shadow = not account_id
    if shadow:
        account_id = f"TBD-{name.lower().replace(' ', '-')}"
        log.info("Jira chưa configured → account_id placeholder: %s", account_id)
    else:
        log.info("Jira account ID resolved: %s", account_id)

    mapping.setdefault("devs", {})[email] = {
        "git_name": name,
        "jira_account_id": account_id,
        "jira_display_name": name,
        "jira_email": email,
        "project_keys": project_keys,
    }

    _DEV_MAPPING_PATH.write_text(_json.dumps(mapping, indent=2, ensure_ascii=False) + "\n")
    status = "⚠️  shadow (update jira_account_id khi có Jira)" if shadow else "✅ live"
    log.info("Dev mapping registered [%s]: %s → %s", status, email, account_id)


def _has_confluence() -> bool:
    return all(os.getenv(k) for k in ["CONFLUENCE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_TOKEN"])


def _has_jira() -> bool:
    return all(os.getenv(k) for k in ["JIRA_URL", "JIRA_EMAIL", "JIRA_TOKEN"])


def _commit_and_push(repo_dir: Path, message: str) -> None:
    def run(cmd: list[str]) -> None:
        subprocess.run(cmd, cwd=repo_dir, capture_output=True, check=False)

    run(["git", "add", "-A"])
    changed = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo_dir, capture_output=True
    ).returncode != 0
    if changed:
        run(["git", "commit", "-m", message])
        run(["git", "push"])
        log.info("Committed and pushed: %s", message)
    else:
        log.info("No changes to commit")


def _pull_confluence(repo_dir: Path, project: str, confluence_space: str) -> None:
    space_key = confluence_space or project
    if not space_key:
        log.warning("Bỏ qua Confluence — cần --project hoặc --confluence-space")
        return
    log.info("Pulling Confluence space: %s...", space_key)
    from scripts.onboard import confluence_puller
    stats = confluence_puller.pull(
        space_key=space_key,
        output_dir=repo_dir,
        confluence_url=os.getenv("CONFLUENCE_URL", ""),
        email=os.getenv("CONFLUENCE_EMAIL", ""),
        token=os.getenv("CONFLUENCE_TOKEN", ""),
    )
    log.info("Confluence: pulled=%d skipped=%d errors=%d", **stats)


def _pull_jira(repo_dir: Path, project: str) -> None:
    log.info("Pulling Jira project: %s...", project)
    from scripts.onboard import jira_puller
    stats = jira_puller.pull(
        project_key=project,
        output_dir=repo_dir,
        jira_url=os.getenv("JIRA_URL", ""),
        email=os.getenv("JIRA_EMAIL", ""),
        token=os.getenv("JIRA_TOKEN", ""),
    )
    log.info("Jira: epics=%d sprint_tickets=%d team_members=%d", **stats)


def _index_rag(repo_dir: Path, namespace: str) -> None:
    chroma_path = str(repo_dir / ".morai" / "rag")
    try:
        from scripts.onboard import rag_indexer
        stats = rag_indexer.index(repo_dir=repo_dir, namespace=namespace, chroma_path=chroma_path)
        log.info("RAG: indexed=%d skipped=%d deleted=%d", **stats)
    except Exception as e:
        log.warning("RAG indexing failed (non-fatal): %s", e)


def _run_scan_synthesis(repo_dir: Path) -> None:
    import shutil as sh
    claude_cli = sh.which("claude")
    if not claude_cli:
        log.warning("claude CLI not found — skipping synthesis")
        return
    log.info("Running /morai:scan for synthesis...")
    subprocess.run(
        [claude_cli, "-p", f"/morai:scan {repo_dir}", "--output-format", "json"],
        cwd=repo_dir, check=False,
    )


def onboard_dev(args: argparse.Namespace, repo_name: str, output_dir: Path) -> None:
    """Dev flow: pull/tạo design repo → Confluence + Jira nếu có → fallback scan source."""
    from scripts.onboard import repo_manager, generator

    log.info("[Dev] Resolving design repo...")
    repo_dir, is_new = repo_manager.resolve(
        project_name=args.project_name,
        output_dir=output_dir,
        git_org=args.git_org,
        git_host=args.git_host,
    )

    log.info("Generating skeleton...")
    generator.generate_skeleton(
        repo_dir=repo_dir,
        project_name=args.project_name,
        project_key=args.project or args.project_name.upper(),
    )

    project_keys = [args.project] if args.project else [args.project_name.upper()]
    _register_dev_mapping(project_keys)

    has_external = False

    if not args.no_confluence and _has_confluence():
        _pull_confluence(repo_dir, args.project or "", args.confluence_space or "")
        has_external = True
    elif not args.no_confluence:
        log.info("Confluence not configured — skipping")

    if not args.no_jira and _has_jira() and args.project:
        _pull_jira(repo_dir, args.project)
        has_external = True
    elif not args.no_jira:
        log.info("Jira not configured — skipping")

    # Fallback: scan source code nếu không có Confluence/Jira và là repo mới
    if not has_external and is_new:
        source_url = args.source_repo
        if source_url:
            log.info("No external tools — scanning source repo as fallback...")
            repo_manager.scan_source_repo(source_url, repo_dir)
        else:
            log.info("No external tools and no --source-repo — skeleton only")

    if not args.no_rag:
        _index_rag(repo_dir, repo_name)

    if args.synthesize:
        _run_scan_synthesis(repo_dir)

    return repo_dir


def onboard_non_dev(args: argparse.Namespace, repo_name: str, output_dir: Path) -> Path:
    """Non-dev flow: pull design repo nếu có, fallback scan source nếu không."""
    from scripts.onboard import repo_manager, generator

    log.info("[Non-dev] Resolving design repo...")
    repo_dir, is_new = repo_manager.resolve(
        project_name=args.project_name,
        output_dir=output_dir,
        git_org=args.git_org,
        git_host=args.git_host,
    )

    log.info("Generating skeleton...")
    generator.generate_skeleton(
        repo_dir=repo_dir,
        project_name=args.project_name,
        project_key=args.project or args.project_name.upper(),
    )

    if is_new:
        # Thử Confluence/Jira trước
        has_external = False
        if not args.no_confluence and _has_confluence():
            _pull_confluence(repo_dir, args.project or "", args.confluence_space or "")
            has_external = True
        if not args.no_jira and _has_jira() and args.project:
            _pull_jira(repo_dir, args.project)
            has_external = True

        # Fallback: clone source → scan
        if not has_external:
            source_url = args.source_repo
            if not source_url:
                log.warning(
                    "Design repo không tồn tại, không có Confluence/Jira, không có --source-repo.\n"
                    "Thêm --source-repo <git-url> để tự động scan source code."
                )
            else:
                log.info("Fallback: cloning source repo → /morai:scan...")
                ok = repo_manager.scan_source_repo(source_url, repo_dir)
                if not ok:
                    log.warning(
                        "Scan thất bại. Kiểm tra:\n"
                        "  1. Git access vào %s\n"
                        "  2. claude CLI đã cài đặt chưa", source_url
                    )
    else:
        log.info("Design repo đã tồn tại — pulled latest, không cần scan")

    if not args.no_rag:
        _index_rag(repo_dir, repo_name)

    return repo_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap hoặc sync project-design knowledge repo"
    )
    parser.add_argument("--role", choices=["dev", "non-dev"], default="dev",
                        help="dev: full pipeline / non-dev: fallback scan source nếu không có tools")
    parser.add_argument("--project", help="Jira project key, e.g. PROJ")
    parser.add_argument("--project-name", required=True, help="Tên project, e.g. subkontrol")
    parser.add_argument("--source-repo", default="",
                        help="Git URL của source code repo (dùng khi không có Confluence/Jira)")
    parser.add_argument("--confluence-space", help="Confluence space key")
    parser.add_argument("--output", help="Local output path (default: ./{project-name}-design)")
    parser.add_argument("--git-org", default="", help="GitHub org hoặc Bitbucket workspace")
    parser.add_argument("--git-host", default="", choices=["github", "bitbucket", ""])
    parser.add_argument("--no-confluence", action="store_true")
    parser.add_argument("--no-jira", action="store_true")
    parser.add_argument("--no-rag", action="store_true")
    parser.add_argument("--update", action="store_true",
                        help="Chỉ sync content, không tạo repo mới")
    parser.add_argument("--synthesize", action="store_true",
                        help="Chạy /morai:scan để sinh PROJECT.md sau khi pull")
    args = parser.parse_args()

    project_name = args.project_name
    repo_name = f"{project_name.lower().replace(' ', '-')}-design"
    output_dir = Path(args.output) if args.output else Path.cwd() / repo_name

    print(f"\n{'='*55}")
    print(f"  morai-onboard [{args.role}] — {project_name}")
    print(f"  Repo: {output_dir}")
    print(f"{'='*55}\n")

    if args.update:
        if not output_dir.exists():
            log.error("--update specified but %s does not exist", output_dir)
            sys.exit(1)
        log.info("Update mode — syncing content only")
        from scripts.onboard import repo_manager
        repo_dir, _ = repo_manager.resolve(project_name, output_dir)
        if not args.no_confluence and _has_confluence():
            _pull_confluence(repo_dir, args.project or "", args.confluence_space or "")
        if not args.no_jira and _has_jira() and args.project:
            _pull_jira(repo_dir, args.project)
        if not args.no_rag:
            _index_rag(repo_dir, repo_name)
    elif args.role == "dev":
        repo_dir = onboard_dev(args, repo_name, output_dir)
    else:
        repo_dir = onboard_non_dev(args, repo_name, output_dir)

    from datetime import date
    _commit_and_push(repo_dir, f"chore: onboard sync {project_name} — {date.today()}")

    print(f"\n{'='*55}")
    print(f"  Done! Repo: {repo_dir}")
    if args.role == "non-dev":
        print(f"  Chạy local agent:")
        print(f"    python local_agent.py --token <token> --workspace {repo_dir}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
