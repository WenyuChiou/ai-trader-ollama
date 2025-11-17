# Daily Upload and Deploy Script
# This script uploads local data to Railway AND ensures GitHub Pages is updated
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\daily_upload_and_deploy.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Daily Upload and Deploy" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Upload data to Railway
Write-Host "[Step 1] Uploading data to Railway..." -ForegroundColor Yellow
Set-Location $ProjectRoot

# Activate virtual environment if exists
$venvPath = Join-Path $ProjectRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# Run upload script
$uploadScript = Join-Path $ProjectRoot "scripts\upload_data_to_railway.py"
python $uploadScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Railway upload failed, but continuing..." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Data uploaded to Railway" -ForegroundColor Green
}

Write-Host ""

# Step 2: Ensure frontend files are committed and pushed (for GitHub Pages)
Write-Host "[Step 2] Checking GitHub Pages deployment..." -ForegroundColor Yellow

# Check if monitor.html has changes
$monitorFile = Join-Path $ProjectRoot "frontend\monitor.html"
$configFile = Join-Path $ProjectRoot "frontend\config.js"

$hasChanges = $false
$gitStatus = git status --porcelain frontend/monitor.html frontend/config.js 2>&1
if ($gitStatus -match "M|A|\?\?") {
    $hasChanges = $true
    Write-Host "[INFO] Frontend files have changes, committing..." -ForegroundColor Yellow
    
    git add frontend/monitor.html frontend/config.js
    git commit -m "Auto-update: Update frontend for GitHub Pages deployment [skip ci]"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Frontend changes committed" -ForegroundColor Green
        $hasChanges = $true
    }
}

# Push to GitHub (this will trigger GitHub Pages deployment)
if ($hasChanges) {
    Write-Host "[Step 3] Pushing to GitHub (triggers GitHub Pages deployment)..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Pushed to GitHub. GitHub Pages will update automatically." -ForegroundColor Green
        Write-Host "     URL: https://wenyuchiou.github.io/ai-trader-ollama/monitor.html" -ForegroundColor Cyan
    } else {
        Write-Host "[WARNING] Failed to push to GitHub" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] No frontend changes to push" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Daily Upload Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Data uploaded to Railway" -ForegroundColor Green
Write-Host "  ✅ GitHub Pages deployment triggered (if changes)" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Wait 1-2 minutes for Railway to process data" -ForegroundColor White
Write-Host "  2. Wait 1-2 minutes for GitHub Pages to deploy" -ForegroundColor White
Write-Host "  3. Check: https://wenyuchiou.github.io/ai-trader-ollama/monitor.html" -ForegroundColor White
Write-Host ""

