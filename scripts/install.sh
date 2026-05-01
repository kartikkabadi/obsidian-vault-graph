#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/kartikkabadi/obsidian-vault-graph.git"
INSTALL_SKILL=0
VAULT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-skill)
      INSTALL_SKILL=1
      shift
      ;;
    --vault)
      VAULT_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if command -v pipx >/dev/null 2>&1; then
  pipx install "git+$REPO" --force
else
  python3 -m pip install --user "git+$REPO"
fi

if [[ -n "$VAULT_PATH" ]]; then
  mkdir -p "$HOME/.config/obsidian-vault-graph"
  cat > "$HOME/.config/obsidian-vault-graph/env" <<EOF
export OBSIDIAN_VAULT_PATH="$VAULT_PATH"
EOF
  echo "Wrote $HOME/.config/obsidian-vault-graph/env"
  echo "Load it with: source $HOME/.config/obsidian-vault-graph/env"
fi

if [[ "$INSTALL_SKILL" == "1" ]]; then
  SKILL_DIR="$HOME/.hermes/skills/note-taking/obsidian-knowledge-graph"
  mkdir -p "$SKILL_DIR"
  curl -fsSL "https://raw.githubusercontent.com/kartikkabadi/obsidian-vault-graph/main/skills/obsidian-knowledge-graph/SKILL.md" -o "$SKILL_DIR/SKILL.md"
  echo "Installed Hermes skill: $SKILL_DIR/SKILL.md"
fi

echo "Installed vault-graph. Try: vault-graph --help"
