# Daily Upload Script - Manual Run
# Usage: powershell -ExecutionPolicy Bypass -File .\run_daily_upload.ps1
# Or just double-click this file

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Daily Upload" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Choose script mode
Write-Host "Choose upload mode:" -ForegroundColor Cyan
Write-Host "  1. Full cycle + upload (runs trading cycle, then uploads) - Takes 2-5 minutes" -ForegroundColor White
Write-Host "  2. Upload only (uploads existing data, no trading cycle) - Takes 10-30 seconds" -ForegroundColor White
$modeChoice = Read-Host "Enter choice (1 or 2, default: 2)"

if ($modeChoice -eq "1") {
    $ScriptPath = "scripts\run_cycle_and_upload_to_railway.py"
    Write-Host ""
    Write-Host "Running trading cycle and uploading to Railway..." -ForegroundColor Yellow
    Write-Host "This may take 2-5 minutes..." -ForegroundColor Gray
} else {
    $ScriptPath = "scripts\upload_data_to_railway.py"
    Write-Host ""
    Write-Host "Uploading existing data to Railway..." -ForegroundColor Yellow
    Write-Host "This may take 10-30 seconds..." -ForegroundColor Gray
}
Write-Host ""

try {
    python $ScriptPath
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Daily upload completed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Wait 1-2 minutes for Railway to process" -ForegroundColor White
        Write-Host "  2. Check GitHub Pages:" -ForegroundColor White
        Write-Host "     https://wenyuchiou.github.io/ai-trader-ollama/monitor.html" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "[ERROR] Script failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to run script: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

