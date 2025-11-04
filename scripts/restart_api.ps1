# PowerShell Script: Restart API Server
# Usage: Run from backend/scripts/ directory
# This script stops any existing API process and starts a new one
#
# If you see execution policy error, use one of these:
#   1. powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
#   2. Or use: .\restart_api_bypass.ps1 (which bypasses automatically)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Restarting AI Trader API Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find and stop existing API processes on port 8000
Write-Host "[1/3] Checking for existing API processes..." -ForegroundColor Yellow

$portConnections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portConnections) {
    $processIds = $portConnections.OwningProcess | Select-Object -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  Found process: PID $($processId) ($($process.ProcessName))" -ForegroundColor Yellow
            Write-Host "  Stopping process $($processId)..." -ForegroundColor Yellow
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "  ✓ Process $($processId) stopped" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ Failed to stop process $($processId): $_" -ForegroundColor Red
            }
        }
    }
    # Wait a moment for port to be released
    Start-Sleep -Seconds 2
} else {
    Write-Host "  No existing API process found on port 8000" -ForegroundColor Gray
}

# Step 2: Verify port is free
Write-Host ""
Write-Host "[2/3] Verifying port 8000 is free..." -ForegroundColor Yellow
$portStillInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portStillInUse) {
    Write-Host "  ⚠ WARNING: Port 8000 is still in use!" -ForegroundColor Red
    Write-Host "  You may need to manually stop the process or use a different port" -ForegroundColor Yellow
    $continue = Read-Host "  Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "  Exiting..." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "  ✓ Port 8000 is free" -ForegroundColor Green
}

# Step 3: Start new API server
Write-Host ""
Write-Host "[3/3] Starting new API server..." -ForegroundColor Yellow

# Build the command string
$apiCommand = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server (Restarted)'
cd '$BackendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server (Restarted)' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API Address: http://localhost:8000' -ForegroundColor Green
Write-Host 'Current Directory: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Starting server...' -ForegroundColor Cyan
Write-Host ''
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
Write-Host ''
Write-Host 'API server stopped' -ForegroundColor Yellow
Read-Host 'Press Enter to close window'
"@

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
    Write-Host ""
    Write-Host "✓ SUCCESS: API server restarted in new window" -ForegroundColor Green
    Write-Host ""
    Write-Host "To verify:" -ForegroundColor Cyan
    Write-Host "  1. Check the new PowerShell window for server logs" -ForegroundColor White
    Write-Host "  2. Open browser: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  3. Test frontend: http://127.0.0.1:8080/monitor.html" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: The API window must stay open. Close it to stop the API." -ForegroundColor Yellow
} catch {
    Write-Host ""
    Write-Host "✗ ERROR: Failed to start API server: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Run manually in a terminal:" -ForegroundColor Yellow
    Write-Host "  cd $BackendDir" -ForegroundColor White
    Write-Host "  python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Read-Host "Press Enter to continue"

