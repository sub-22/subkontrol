#!/bin/bash
# Bootstrap / re-sync Morai identity into ~/.claude/CLAUDE.md
# Called by /morai:init skill. Resolves plugin root from script location.
#
# The Morai content block is wrapped in markers tagged with the plugin
# version, so subsequent runs after a plugin update can detect drift and
# re-sync just that block — without touching any user content around it.
#
#   <!-- MORAI:BEGIN vX.Y.Z -->
#   ...content from .claude-plugin/CLAUDE.md...
#   <!-- MORAI:END -->
#
# Output (stdout, single line):
#   OK                        — first-time write
#   ALREADY_SETUP             — block already at current version
#   UPDATED:<old>->v<new>      — existing block re-synced to current version
#   MIGRATED:v<new>            — legacy (unmarked) block converted + synced
#   ERROR: <message>           — failure

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE="${PLUGIN_ROOT}/.claude-plugin/CLAUDE.md"
PLUGIN_JSON="${PLUGIN_ROOT}/.claude-plugin/plugin.json"
DEST="${HOME}/.claude/CLAUDE.md"

if [ ! -f "$SOURCE" ]; then
  echo "ERROR: Morai CLAUDE.md not found at $SOURCE" >&2
  exit 1
fi

SOURCE_VERSION=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])" 2>/dev/null)
if [ -z "$SOURCE_VERSION" ]; then
  echo "ERROR: cannot read plugin version from $PLUGIN_JSON" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"

build_block() {
  printf '%s\n\n' "<!-- MORAI:BEGIN v${SOURCE_VERSION} -->"
  cat "$SOURCE"
  printf '\n%s\n' "<!-- MORAI:END -->"
}

# 1. No existing file (or empty) — first-time write
if [ ! -f "$DEST" ] || [ ! -s "$DEST" ]; then
  build_block > "$DEST"
  echo "OK"
  exit 0
fi

# 2. Already wrapped in markers — compare version, re-sync if stale
DEST_VERSION=$(grep -m1 -oP '<!-- MORAI:BEGIN v\K[0-9][0-9A-Za-z.\-]*(?= -->)' "$DEST")

if [ -n "$DEST_VERSION" ]; then
  if [ "$DEST_VERSION" = "$SOURCE_VERSION" ]; then
    echo "ALREADY_SETUP"
    exit 0
  fi

  if ! python3 - "$DEST" "$SOURCE" "$SOURCE_VERSION" << 'PYEOF'
import re
import sys

dest_path, source_path, version = sys.argv[1:4]
dest = open(dest_path).read()
source = open(source_path).read().rstrip("\n")
new_block = f"<!-- MORAI:BEGIN v{version} -->\n\n{source}\n\n<!-- MORAI:END -->"

pattern = re.compile(r"<!-- MORAI:BEGIN v[^>]* -->.*?<!-- MORAI:END -->", re.DOTALL)
dest, n = pattern.subn(new_block, dest, count=1)
if n == 0:
    sys.exit(1)

open(dest_path, "w").write(dest)
PYEOF
  then
    echo "ERROR: failed to update Morai block in $DEST" >&2
    exit 1
  fi

  echo "UPDATED:v${DEST_VERSION}->v${SOURCE_VERSION}"
  exit 0
fi

# 3. Legacy install (no markers) — migrate if it looks like an old Morai block.
#    Old versions wrote the Morai content as the last section of the file
#    (either the whole file via `cp`, or appended after a `---` separator),
#    so everything from the header line to EOF is the Morai block.
if grep -q "^# Morai — AI Operator" "$DEST"; then
  python3 - "$DEST" "$SOURCE" "$SOURCE_VERSION" << 'PYEOF'
import sys

dest_path, source_path, version = sys.argv[1:4]
lines = open(dest_path).read().splitlines(keepends=True)
idx = next(i for i, l in enumerate(lines) if l.startswith("# Morai — AI Operator"))
prefix = "".join(lines[:idx])
source = open(source_path).read().rstrip("\n")
new_block = f"<!-- MORAI:BEGIN v{version} -->\n\n{source}\n\n<!-- MORAI:END -->\n"
open(dest_path, "w").write(prefix + new_block)
PYEOF
  echo "MIGRATED:v${SOURCE_VERSION}"
  exit 0
fi

# 4. Existing file with unrelated content — append as a new block
{
  printf '\n\n---\n\n'
  build_block
} >> "$DEST"
echo "OK"
