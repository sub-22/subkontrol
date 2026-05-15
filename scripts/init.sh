#!/bin/bash
# Bootstrap Morai identity into ~/.claude/CLAUDE.md
# Called by /morai:init skill. Resolves plugin root from script location.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE="${PLUGIN_ROOT}/.claude-plugin/CLAUDE.md"
DEST="${HOME}/.claude/CLAUDE.md"

if [ ! -f "$SOURCE" ]; then
  echo "ERROR: Morai CLAUDE.md not found at $SOURCE" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"

if [ -f "$DEST" ] && grep -q "# Morai — AI Operator" "$DEST" 2>/dev/null; then
  echo "ALREADY_SETUP"
  exit 0
fi

if [ -f "$DEST" ] && [ -s "$DEST" ]; then
  printf "\n\n---\n\n" >> "$DEST"
  cat "$SOURCE" >> "$DEST"
else
  cp "$SOURCE" "$DEST"
fi

echo "OK"
