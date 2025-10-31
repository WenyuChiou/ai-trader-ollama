#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "ERROR: git not found in PATH."
  exit 1
}

# Optional: user identity
# git config --global user.name "Your Name"
# git config --global user.email "you@example.com"

git init -b main
git add .
git commit -m "chore: initial commit (LangChain + Ollama AI Trader skeleton)"

# Optional remote:
# git remote add origin <YOUR_REPO_URL>
# git push -u origin main

if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
  pre-commit install
  Write-Output "pre-commit installed. Running hooks on all files..."
  pre-commit run --all-files
} else {
  Write-Output "Tip: install pre-commit:  pip install pre-commit"
}

Write-Output "✅ Git repo initialized on branch 'main'."
