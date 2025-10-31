#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

param(
  [Parameter(Mandatory=$true)][string]$Owner,
  [Parameter(Mandatory=$true)][string]$Repo,
  [ValidateSet("public","private")][string]$Visibility = "public"
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "GitHub CLI 'gh' not found. Install: https://cli.github.com/"
  exit 1
}

# Ensure local repo exists
if (-not (Test-Path ".git")) {
  git init -b main
  git add .
  git commit -m "chore: initial commit (LangChain + Ollama AI Trader skeleton)"
}

# Auth if needed
try {
  gh auth status | Out-Null
} catch {
  Write-Host "Logging into GitHub..."
  gh auth login
}

gh repo create "$Owner/$Repo" --source . --remote origin --$Visibility --push --disable-issues=false --disable-wiki=false

Write-Host "✅ Created https://github.com/$Owner/$Repo and pushed 'main'."
