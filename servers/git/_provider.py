"""Git provider abstraction — auto-detect GitHub, Bitbucket Cloud, or Bitbucket Server."""

from __future__ import annotations

import base64
import json
import logging
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from servers._env import resolve

_log = logging.getLogger(__name__)

GITHUB_TOKEN = resolve("GITHUB_TOKEN")
BITBUCKET_USERNAME = resolve("BITBUCKET_USERNAME")
BITBUCKET_TOKEN = resolve("BITBUCKET_TOKEN")

# Required for Bitbucket Server (self-hosted). e.g. https://git.mycompany.com
BITBUCKET_BASE_URL = resolve("BITBUCKET_BASE_URL").rstrip("/")


def _parse_remote(workspace_root: Path) -> dict:
    """Parse git remote URL → provider + identifiers.

    Returns:
        GitHub:            {"provider": "github",    "owner": str, "repo": str}
        Bitbucket Cloud:   {"provider": "bitbucket", "owner": str, "repo": str}
        Bitbucket Server:  {"provider": "bitbucket-server", "project": str, "repo": str,
                            "base_url": str}
    """
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=workspace_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"provider": "github", "owner": "", "repo": ""}

    url = result.stdout.strip()

    # Bitbucket Server — match against BITBUCKET_BASE_URL host
    if BITBUCKET_BASE_URL:
        server_host = urlparse(BITBUCKET_BASE_URL).hostname or ""
        if server_host and server_host in url:
            # HTTPS: https://git.mycompany.com/scm/PROJECT/repo.git
            # SSH:   ssh://git@git.mycompany.com/scm/PROJECT/repo.git
            #        git@git.mycompany.com:scm/PROJECT/repo.git
            match = re.search(r"scm[/:]([^/]+)/([^/]+?)(?:\.git)?$", url)
            if match:
                return {
                    "provider": "bitbucket-server",
                    "project": match.group(1).upper(),
                    "repo": match.group(2),
                    "base_url": BITBUCKET_BASE_URL,
                }
            return {
                "provider": "bitbucket-server",
                "project": "",
                "repo": "",
                "base_url": BITBUCKET_BASE_URL,
            }

    # Bitbucket Cloud
    if "bitbucket.org" in url:
        match = re.search(r"bitbucket\.org[:/](.+?)/(.+?)(?:\.git)?$", url)
        if match:
            return {"provider": "bitbucket", "owner": match.group(1), "repo": match.group(2)}
        return {"provider": "bitbucket", "owner": "", "repo": ""}

    # GitHub (default)
    if "github.com" in url:
        match = re.search(r"github\.com[:/](.+?)/(.+?)(?:\.git)?$", url)
        if match:
            return {"provider": "github", "owner": match.group(1), "repo": match.group(2)}

    return {"provider": "github", "owner": "", "repo": ""}


# ── HTTP helpers ───────────────────────────────────────────────────────────────


def _basic_auth_header(username: str, token: str) -> str:
    return "Basic " + base64.b64encode(f"{username}:{token}".encode()).decode()


def _bearer_header(token: str) -> str:
    return f"Bearer {token}"


def _http(
    url: str, method: str = "GET", payload: bytes | None = None, headers: dict | None = None
) -> dict:
    req = urllib.request.Request(url, data=payload, method=method)
    req.add_header("Accept", "application/json")
    if payload:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return {"ok": True, "data": json.loads(body) if body else {}}
    except urllib.error.HTTPError as e:
        _log.warning("HTTP %s %s → %d %s", method, url, e.code, e.reason)
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        _log.exception("Unexpected error calling %s %s", method, url)
        return {"ok": False, "error": str(e)}


def _cloud_headers() -> dict:
    return {"Authorization": _basic_auth_header(BITBUCKET_USERNAME, BITBUCKET_TOKEN)}


def _server_headers() -> dict:
    return {"Authorization": _bearer_header(BITBUCKET_TOKEN)}


# ── List open PRs ──────────────────────────────────────────────────────────────


def list_open_prs(workspace_root: Path) -> list[dict]:
    info = _parse_remote(workspace_root)
    if info["provider"] == "bitbucket-server":
        return _list_prs_server(info)
    if info["provider"] == "bitbucket":
        return _list_prs_cloud(info)
    return _list_prs_github(workspace_root)


def _list_prs_github(workspace_root: Path) -> list[dict]:
    import os

    env = {**os.environ, "GH_TOKEN": GITHUB_TOKEN} if GITHUB_TOKEN else None
    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,author,url,headRefName,createdAt",
        ],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        return [{"error": result.stderr.strip()}]
    try:
        return [
            {
                "id": pr["number"],
                "title": pr["title"],
                "author": pr.get("author", {}).get("login", ""),
                "branch": pr["headRefName"],
                "url": pr["url"],
                "created_at": pr["createdAt"],
                "provider": "github",
            }
            for pr in json.loads(result.stdout)
        ]
    except Exception as e:
        return [{"error": str(e)}]


def _list_prs_cloud(info: dict) -> list[dict]:
    owner, repo = info["owner"], info["repo"]
    url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests?state=OPEN"
    resp = _http(url, headers=_cloud_headers())
    if not resp["ok"]:
        return [{"error": resp["error"]}]
    return [
        {
            "id": pr["id"],
            "title": pr["title"],
            "author": pr.get("author", {}).get("display_name", ""),
            "branch": pr["source"]["branch"]["name"],
            "url": pr["links"]["html"]["href"],
            "created_at": pr["created_on"],
            "provider": "bitbucket",
        }
        for pr in resp["data"].get("values", [])
    ]


def _list_prs_server(info: dict) -> list[dict]:
    base, project, repo = info["base_url"], info["project"], info["repo"]
    url = f"{base}/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests?state=OPEN"
    resp = _http(url, headers=_server_headers())
    if not resp["ok"]:
        return [{"error": resp["error"]}]
    return [
        {
            "id": pr["id"],
            "title": pr["title"],
            "author": pr.get("author", {}).get("user", {}).get("displayName", ""),
            "branch": pr["fromRef"]["displayId"],
            "url": pr["links"]["self"][0]["href"],
            "created_at": pr.get("createdDate", ""),
            "provider": "bitbucket-server",
        }
        for pr in resp["data"].get("values", [])
    ]


# ── Get PR detail ──────────────────────────────────────────────────────────────


def get_pr_detail(pr_id: int | str, workspace_root: Path) -> dict:
    info = _parse_remote(workspace_root)
    if info["provider"] == "bitbucket-server":
        return _detail_server(pr_id, info)
    if info["provider"] == "bitbucket":
        return _detail_cloud(pr_id, info)
    return _detail_github(pr_id, workspace_root)


def _detail_github(pr_id: int | str, workspace_root: Path) -> dict:
    import os

    env = {**os.environ, "GH_TOKEN": GITHUB_TOKEN} if GITHUB_TOKEN else None
    meta = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            str(pr_id),
            "--json",
            "number,title,author,url,body,headRefName,baseRefName",
        ],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        env=env,
    )
    diff = subprocess.run(
        ["gh", "pr", "diff", str(pr_id)],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        env=env,
    )
    m: dict = json.loads(meta.stdout) if meta.returncode == 0 else {}
    return {
        "id": pr_id,
        "title": m.get("title", ""),
        "author": m.get("author", {}).get("login", ""),
        "branch": m.get("headRefName", ""),
        "base": m.get("baseRefName", "main"),
        "url": m.get("url", ""),
        "description": m.get("body", ""),
        "diff": diff.stdout if diff.returncode == 0 else diff.stderr,
        "provider": "github",
    }


def _detail_cloud(pr_id: int | str, info: dict) -> dict:
    owner, repo = info["owner"], info["repo"]
    base = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests/{pr_id}"
    meta = _http(base, headers=_cloud_headers())
    diff = _http(f"{base}/diff", headers=_cloud_headers())
    m = meta["data"] if meta["ok"] else {}
    return {
        "id": pr_id,
        "title": m.get("title", ""),
        "author": m.get("author", {}).get("display_name", ""),
        "branch": m.get("source", {}).get("branch", {}).get("name", ""),
        "base": m.get("destination", {}).get("branch", {}).get("name", "main"),
        "url": m.get("links", {}).get("html", {}).get("href", ""),
        "description": m.get("description", ""),
        "diff": diff["data"] if diff["ok"] else diff.get("error", ""),
        "provider": "bitbucket",
    }


def _detail_server(pr_id: int | str, info: dict) -> dict:
    base, project, repo = info["base_url"], info["project"], info["repo"]
    pr_url = f"{base}/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}"
    meta = _http(pr_url, headers=_server_headers())
    diff = _http(f"{pr_url}/diff", headers=_server_headers())
    m = meta["data"] if meta["ok"] else {}
    return {
        "id": pr_id,
        "title": m.get("title", ""),
        "author": m.get("author", {}).get("user", {}).get("displayName", ""),
        "branch": m.get("fromRef", {}).get("displayId", ""),
        "base": m.get("toRef", {}).get("displayId", "main"),
        "url": m.get("links", {}).get("self", [{}])[0].get("href", ""),
        "description": m.get("description", ""),
        "diff": diff["data"] if diff["ok"] else diff.get("error", ""),
        "provider": "bitbucket-server",
    }


# ── Post comment ───────────────────────────────────────────────────────────────


def post_pr_comment(pr_id: int | str, body: str, workspace_root: Path) -> dict:
    info = _parse_remote(workspace_root)
    if info["provider"] == "bitbucket-server":
        return _comment_server(pr_id, body, info)
    if info["provider"] == "bitbucket":
        return _comment_cloud(pr_id, body, info)
    return _comment_github(pr_id, body, workspace_root)


def _comment_github(pr_id: int | str, body: str, workspace_root: Path) -> dict:
    import os

    env = {**os.environ, "GH_TOKEN": GITHUB_TOKEN} if GITHUB_TOKEN else None
    result = subprocess.run(
        ["gh", "pr", "comment", str(pr_id), "--body", body],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        env=env,
    )
    return {"ok": result.returncode == 0, "error": result.stderr.strip()}


def _comment_cloud(pr_id: int | str, body: str, info: dict) -> dict:
    owner, repo = info["owner"], info["repo"]
    url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests/{pr_id}/comments"
    payload = json.dumps({"content": {"raw": body}}).encode()
    resp = _http(url, method="POST", payload=payload, headers=_cloud_headers())
    return {"ok": resp["ok"], "error": resp.get("error", "")}


def _comment_server(pr_id: int | str, body: str, info: dict) -> dict:
    base, project, repo = info["base_url"], info["project"], info["repo"]
    url = f"{base}/rest/api/1.0/projects/{project}/repos/{repo}/pull-requests/{pr_id}/comments"
    payload = json.dumps({"text": body}).encode()
    resp = _http(url, method="POST", payload=payload, headers=_server_headers())
    return {"ok": resp["ok"], "error": resp.get("error", "")}
