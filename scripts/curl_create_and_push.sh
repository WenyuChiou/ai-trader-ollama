#!/usr/bin/env bash
set -euo pipefail

# Usage: GH_USER=<user> GH_TOKEN=<token> ./scripts/curl_create_and_push.sh <repo> [public|private]

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl not found."
  exit 1
fi

REPO="${1:-}"
VIS="${2:-public}"

if [[ -z "${GH_USER:-}" || -z "${GH_TOKEN:-}" ]]; then
  echo "ERROR: Set GH_USER and GH_TOKEN environment variables."
  echo "Token scopes needed: 'repo' (and 'workflow' if using Actions)."
  exit 1
fi

if [[ -z "$REPO" ]]; then
  echo "Usage: GH_USER=<user> GH_TOKEN=<token> $0 <repo> [public|private]"
  exit 1
fi

# Ensure local repo exists
if [ ! -d .git ]; then
  git init -b main
  git add .
  git commit -m "chore: initial commit (LangChain + Ollama AI Trader skeleton)"
fi

VIS_BOOL=false
if [[ "$VIS" == "private" ]]; then VIS_BOOL=true; fi

# Create repo via API
RESP=$(curl -sS -X POST -H "Authorization: token ${GH_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"${REPO}\",\"private\":${VIS_BOOL},\"has_issues\":true,\"has_wiki\":true}")
HTML_URL=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('html_url',''))")
SSH_URL=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('ssh_url',''))")
CLONE_URL=$(echo "$RESP" | python -c "import sys, json; print(json.load(sys.stdin).get('clone_url',''))")

if [[ -z "$HTML_URL" ]]; then
  echo "ERROR creating repo. Response:"
  echo "$RESP"
  exit 1
fi

# Add remote and push
if git remote | grep -q '^origin$'; then
  git remote remove origin
fi

git remote add origin "$CLONE_URL"
git push -u origin main

echo "✅ Created $HTML_URL and pushed 'main'."
