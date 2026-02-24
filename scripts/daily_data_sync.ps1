# Daily Data Sync — Commit and push trading data to GitHub
# Keeps GitHub Pages static data fresh for historical charts
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\daily_data_sync.ps1
# Schedule: Task Scheduler daily at 23:59 or via cron

$ErrorActionPreference = "Continue"

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = Join-Path $logDir "daily_sync.log"

function Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] $Message"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry -Encoding UTF8
}

Log "=== Daily data sync started ==="

Push-Location $ProjectRoot
try {
    # Check if there are changes to sync
    $status = git status --porcelain -- data/ frontend/ 2>&1
    if ([string]::IsNullOrWhiteSpace($status)) {
        Log "No changes in data/ or frontend/ — nothing to sync"
        Log "=== Daily data sync finished (no changes) ==="
        return
    }

    Log "Changes detected:"
    $status -split "`n" | ForEach-Object { Log "  $_" }

    # Stage data and frontend files
    git add data/ frontend/ 2>&1 | ForEach-Object { Log $_ }

    # Check if there are staged changes
    $staged = git diff --cached --name-only 2>&1
    if ([string]::IsNullOrWhiteSpace($staged)) {
        Log "No staged changes after git add — nothing to commit"
        Log "=== Daily data sync finished (no staged changes) ==="
        return
    }

    # Commit
    $commitDate = Get-Date -Format "yyyy-MM-dd"
    $commitMsg = "auto: daily data sync $commitDate [skip ci]"
    $commitOutput = git commit -m "$commitMsg" 2>&1
    Log "Commit: $commitOutput"

    if ($LASTEXITCODE -ne 0) {
        Log "ERROR: git commit failed"
        Log "=== Daily data sync finished (commit failed) ==="
        return
    }

    # Push
    Log "Pushing to origin main..."
    $pushOutput = git push origin main 2>&1
    Log "Push: $pushOutput"

    if ($LASTEXITCODE -ne 0) {
        Log "ERROR: git push failed — check authentication or network"
        Log "=== Daily data sync finished (push failed) ==="
        return
    }

    Log "=== Daily data sync completed successfully ==="
} finally {
    Pop-Location
}
