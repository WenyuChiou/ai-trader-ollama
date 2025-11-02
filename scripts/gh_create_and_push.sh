#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI 'gh' not found. Install: https://cli.github.com/"
  exit 1
fi

# Usage: ./scripts/gh_create_and_push.sh <owner> <repo> [public|private]
OWNER="${1:-}"
REPO="${2:-}"
VIS="${3:-public}"

if [[ -z "$OWNER" || -z "$REPO" ]]; then
  echo "Usage: $0 <owner> <repo> [public|private]"
  exit 1
fi

# Ensure repo is initialized locally
if [ ! -d .git ]; then
  git init -b main
  git add .
  git commit -m "chore: initial commit (LangChain + Ollama AI Trader skeleton)"
fi

# Auth (interactive if not logged in)
if ! gh auth status >/dev/null 2>&1; then
  echo "Logging into GitHub..."
  gh auth login
fi

# Create remote repo and push
gh repo create "$OWNER/$REPO" --source . --remote origin --"$VIS" --push --disable-issues=false --disable-wiki=false

echo "✅ Created https://github.com/$OWNER/$REPO and pushed 'main'."
