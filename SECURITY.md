# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.5.x (current) | ✅ |
| < 0.5 | ❌ |

## Reporting a Vulnerability

**Do not report security vulnerabilities via GitHub Issues.**

Please report security issues via email or GitHub Security Advisories:
- GitHub: [Security Advisories](https://github.com/sub-22/subkontrol/security/advisories/new)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

Response time: within 72 hours.

## Security Design Notes

### Credentials
- All credentials (Jira, Confluence, Slack, Anthropic API key) are loaded from environment variables only — never hardcoded
- `.env` files are gitignored
- `config/dev_mapping.json` is gitignored — use `config/dev_mapping.example.json` as template

### File Access
- `morai-file` server enforces workspace boundary — cannot read/write outside `WORKSPACE_ROOT`
- Source code writes require `write_source_file()` (dev skills only), not `write_file()`

### MCP Servers
- All MCP servers are local stdio processes — no network exposure
- Credentials passed via environment variables, not CLI arguments

### AI-Generated Code Gate
- R-009 reflex blocks auto-merge of AI-generated code > 200 LOC
- Human sign-off required before merging large AI-generated diffs
