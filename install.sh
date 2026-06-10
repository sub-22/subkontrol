#!/usr/bin/env bash
# Morai — one-command install (global, chạy 1 lần trên máy)
#
# Cách dùng:
#
#   GitHub public:
#     curl -fsSL https://raw.githubusercontent.com/sub-22/subkontrol/master/install.sh | bash
#
#   GitHub / Bitbucket private — clone trước, rồi chạy:
#     git clone <repo-url> /tmp/subkontrol
#     bash /tmp/subkontrol/install.sh
#
#   Hoặc chạy trực tiếp từ thư mục đã clone:
#     bash install.sh
#
# Sau khi install xong — onboard từng project (chạy trong project đó):
#     /morai:scan
#
# Update Morai lên version mới:
#     bash install.sh          (từ thư mục đã git pull)
#     claude plugin update morai   (nếu cài qua GitHub marketplace)

set -e

# ── Detect plugin directory ───────────────────────────────────────────────────
# Hỗ trợ cả `bash install.sh` và `curl ... | bash`
if [ -n "${BASH_SOURCE[0]}" ] && [ "${BASH_SOURCE[0]}" != "bash" ]; then
  PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  PLUGIN_DIR="$(pwd)"
fi

SETTINGS="$HOME/.claude/settings.json"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         Morai — AI Operator              ║"
echo "║         One-time global install          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Source : $PLUGIN_DIR"
echo "  Target : ~/.claude/plugins/ (global)"
echo ""

# ── 1. Prerequisites ──────────────────────────────────────────────────────────

if ! command -v claude &>/dev/null; then
  echo "❌ Claude Code CLI not found."
  echo "   Install: https://claude.ai/code"
  exit 1
fi

if ! command -v uv &>/dev/null; then
  echo "❌ uv not found."
  echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo "✅ Prerequisites OK"

# ── 2. Marketplace registration (GitHub only) ─────────────────────────────────

mkdir -p "$(dirname "$SETTINGS")"
if [ ! -f "$SETTINGS" ]; then
  echo "{}" > "$SETTINGS"
fi

REMOTE_URL=""
if git -C "$PLUGIN_DIR" remote get-url origin &>/dev/null 2>&1; then
  REMOTE_URL=$(git -C "$PLUGIN_DIR" remote get-url origin 2>/dev/null || echo "")
fi

if echo "$REMOTE_URL" | grep -q "github.com"; then
  python3 - << 'PYEOF'
import json, os

settings_path = os.path.expanduser("~/.claude/settings.json")
with open(settings_path) as f:
    data = json.load(f)

if "sub22" not in data.get("extraKnownMarketplaces", {}):
    data.setdefault("extraKnownMarketplaces", {})["sub22"] = {
        "source": {"source": "github", "repo": "sub-22/subkontrol"}
    }
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("✅ Marketplace 'sub22' registered — future updates via: claude plugin update morai")
else:
    print("✅ Marketplace 'sub22' already registered")
PYEOF
else
  echo "ℹ️  Private/local repo — skipping marketplace registration"
  echo "   Update: git pull && bash install.sh"
fi

# ── 3. Install plugin globally ────────────────────────────────────────────────

echo ""
echo "Installing plugin globally..."

# Register local directory as a marketplace (idempotent — CLI appends .claude-plugin/marketplace.json automatically)
if ! claude plugin marketplace list 2>/dev/null | grep -q "^  ❯ morai"; then
  claude plugin marketplace add "$PLUGIN_DIR" --scope user
fi

claude plugin install morai

# ── 4. Configure MORAI_GLOBAL_PATH (after install — plugin install resets pluginConfigs) ──

DEFAULT_MORAI_PATH="$HOME/.morai"

python3 - "$DEFAULT_MORAI_PATH" << 'PYEOF'
import json, os, sys

default_path = sys.argv[1]
settings_path = os.path.expanduser("~/.claude/settings.json")

with open(settings_path) as f:
    data = json.load(f)

existing = data.get("pluginConfigs", {}).get("morai@morai", {}).get("MORAI_GLOBAL_PATH", "")

if existing:
    print(f"✅ MORAI_GLOBAL_PATH already set: {existing}")
else:
    data.setdefault("pluginConfigs", {}).setdefault("morai@morai", {})["MORAI_GLOBAL_PATH"] = default_path
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.makedirs(os.path.join(default_path, "memory"), exist_ok=True)
    os.makedirs(os.path.join(default_path, "tasks"), exist_ok=True)
    print(f"✅ MORAI_GLOBAL_PATH set: {default_path}")
PYEOF

# ── 5. Apply Morai identity globally ─────────────────────────────────────────

echo ""
INIT_SCRIPT="$PLUGIN_DIR/scripts/init.sh"

if [ -f "$INIT_SCRIPT" ]; then
  read -r -p "  Apply Morai identity globally? (~/.claude/CLAUDE.md) [Y/n] " REPLY
  REPLY="${REPLY:-Y}"
  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    RESULT=$(bash "$INIT_SCRIPT")
    case "$RESULT" in
      ALREADY_SETUP)
        echo "✅ Morai identity already up to date globally"
        ;;
      OK)
        echo "✅ Morai identity written to ~/.claude/CLAUDE.md"
        echo "   Restart Claude Code to apply."
        ;;
      UPDATED:*|MIGRATED:*)
        echo "✅ Morai identity re-synced in ~/.claude/CLAUDE.md (${RESULT#*:})"
        echo "   Restart Claude Code to apply."
        ;;
      *)
        echo "⚠️  Identity setup failed: $RESULT"
        ;;
    esac
  else
    echo "ℹ️  Skipped — run /morai:init inside any project to set up later."
  fi
else
  echo "⚠️  scripts/init.sh not found — skipping identity setup"
fi

# ── 6. Done ───────────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ Morai installed successfully!        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Morai có mặt trong mọi project trên máy này."
echo ""
echo "  Bước tiếp — onboard từng project (chạy trong project đó):"
echo ""
echo "    cd /path/to/your-project"
echo "    claude     ← mở Claude Code"
echo "    /morai:init và /morai:scan  ← index codebase, tạo CLAUDE.md"
echo ""
echo "  Hoặc nếu project đã có CLAUDE.md:"
echo "    Mở Claude Code là Morai tự nhận diện project."
echo ""
