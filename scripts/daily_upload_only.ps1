# Daily Upload Only Script (No GitHub Pages Update)
# This script ONLY uploads local data to Railway, does NOT update GitHub Pages
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\daily_upload_only.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Daily Upload to Railway (Data Only)" -ForegroundColor Cyan
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

# Run upload script (ONLY uploads data, no GitHub Pages update)
$uploadScript = Join-Path $ProjectRoot "scripts\upload_data_to_railway.py"
python $uploadScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Railway upload failed" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[OK] Data uploaded to Railway successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Daily Upload Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Data uploaded to Railway" -ForegroundColor Green
Write-Host "  ℹ️  GitHub Pages NOT updated (to save budget)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: This script only uploads data. GitHub Pages updates are skipped." -ForegroundColor Gray
Write-Host ""

