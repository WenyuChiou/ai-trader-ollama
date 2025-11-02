#!/usr/bin/env bash
set -euo pipefail

# Initialize git repo with main branch, add files, make first commit, and set up pre-commit

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git not found in PATH."
  exit 1
fi

# Optional: user identity (uncomment and edit)
# git config --global user.name "Your Name"
# git config --global user.email "you@example.com"

git init -b main
git add .
git commit -m "chore: initial commit (LangChain + Ollama AI Trader skeleton)"

# Optional remote (uncomment and set):
# git remote add origin <YOUR_REPO_URL>
# git push -u origin main

# Pre-commit setup (optional)
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
  echo "pre-commit installed. Running hooks on all files..."
  pre-commit run --all-files || true
else
  echo "Tip: install pre-commit for auto-format/lint:  pip install pre-commit"
fi

echo "✅ Git repo initialized on branch 'main'."
