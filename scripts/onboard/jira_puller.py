"""Jira puller — fetch epics, sprint summary, team members."""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)


def _client(jira_url: str, email: str, token: str):
    from atlassian import Jira
    return Jira(url=jira_url, username=email, password=token)


def _format_ticket_row(issue: dict) -> str:
    fields = issue.get("fields", {})
    key = issue["key"]
    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "—")
    return f"| [{key}]({key}) | {summary} | {status} | {assignee} |"


def pull(
    project_key: str,
    output_dir: Path,
    jira_url: str,
    email: str,
    token: str,
) -> dict:
    """Pull Jira project data: epics + sprint summary.

    Returns:
        {"epics": N, "sprint_tickets": N, "team_members": N}
    """
    client = _client(jira_url, email, token)
    stats = {"epics": 0, "sprint_tickets": 0, "team_members": 0}
    onboarding_dir = output_dir / "onboarding"
    onboarding_dir.mkdir(parents=True, exist_ok=True)

    # ── Project info ──────────────────────────────────────────────────────────
    try:
        project = client.project(project_key)
        project_name = project.get("name", project_key)
        project_desc = project.get("description", "")
        project_lead = (project.get("lead") or {}).get("displayName", "")
        project_url = f"{jira_url}/projects/{project_key}"
    except Exception as e:
        log.warning("Could not fetch project info: %s", e)
        project_name = project_key
        project_desc = ""
        project_lead = ""
        project_url = f"{jira_url}/projects/{project_key}"

    # ── Epics ─────────────────────────────────────────────────────────────────
    epics: list[dict] = []
    try:
        result = client.jql(
            f'project = "{project_key}" AND issuetype = Epic ORDER BY created DESC',
            limit=100,
        )
        epics = result.get("issues", [])
        stats["epics"] = len(epics)
        log.info("Found %d epics", len(epics))
    except Exception as e:
        log.warning("Could not fetch epics: %s", e)

    # ── Active sprint ─────────────────────────────────────────────────────────
    sprint_tickets: list[dict] = []
    sprint_name = ""
    try:
        result = client.jql(
            f'project = "{project_key}" AND sprint in openSprints() ORDER BY priority DESC',
            limit=50,
        )
        sprint_tickets = result.get("issues", [])
        stats["sprint_tickets"] = len(sprint_tickets)
        if sprint_tickets:
            sprints_field = sprint_tickets[0].get("fields", {}).get("sprint") or {}
            sprint_name = sprints_field.get("name", "Active Sprint")
    except Exception as e:
        log.warning("Could not fetch sprint: %s", e)

    # ── Team members ──────────────────────────────────────────────────────────
    team: dict[str, str] = {}
    try:
        members = client.get_project_members(project_key)
        for m in members:
            team[m["accountId"]] = m.get("displayName", "")
        stats["team_members"] = len(team)
    except Exception:
        # Fallback: collect từ tickets
        for issue in epics + sprint_tickets:
            fields = issue.get("fields", {})
            for role in ["assignee", "reporter"]:
                person = fields.get(role) or {}
                aid = person.get("accountId", "")
                name = person.get("displayName", "")
                if aid and name:
                    team[aid] = name
        stats["team_members"] = len(team)

    # ── Write PROJECT.md ──────────────────────────────────────────────────────
    epic_rows = "\n".join(_format_ticket_row(e) for e in epics) or "| — | No epics found | — | — |"
    sprint_rows = "\n".join(_format_ticket_row(t) for t in sprint_tickets) or "| — | No active sprint | — | — |"

    project_md = f"""# {project_name}

{project_desc}

**Jira Project:** [{project_key}]({project_url})
**Project Lead:** {project_lead}

---

## Epics ({len(epics)})

| Key | Summary | Status | Assignee |
|-----|---------|--------|----------|
{epic_rows}

---

## Current Sprint: {sprint_name or "—"} ({len(sprint_tickets)} tickets)

| Key | Summary | Status | Assignee |
|-----|---------|--------|----------|
{sprint_rows}
"""
    (output_dir / "PROJECT.md").write_text(project_md, encoding="utf-8")
    log.info("Written PROJECT.md")

    # ── Write onboarding/team.md ──────────────────────────────────────────────
    team_rows = "\n".join(f"| {name} | — | — |" for name in sorted(team.values()))
    team_md = f"""# Team — {project_name}

| Name | Role | Contact |
|------|------|---------|
{team_rows or "| — | — | — |"}

> Update this file manually with roles and contact info.
"""
    (onboarding_dir / "team.md").write_text(team_md, encoding="utf-8")

    # ── Write onboarding/glossary.md nếu chưa có ─────────────────────────────
    glossary_path = onboarding_dir / "glossary.md"
    if not glossary_path.exists():
        glossary_path.write_text(
            f"# Glossary — {project_name}\n\n"
            "| Term | Definition |\n|------|------------|\n| — | — |\n\n"
            "> Add project-specific terms here.\n",
            encoding="utf-8",
        )

    return stats
