# PowerShell Script: Start API Server in Background Window
# Usage: Double-click or run in PowerShell
# IMPORTANT: This script must be run from backend/scripts/ directory

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Trader API Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Script Directory: $ScriptDir"
Write-Host "Backend Directory: $BackendDir"
Write-Host "API Address: http://localhost:8000"
Write-Host ""

# Check if backend directory exists
if (-not (Test-Path $BackendDir)) {
    Write-Host "ERROR: Backend directory not found: $BackendDir" -ForegroundColor Red
    Write-Host "Please run this script from backend/scripts/ directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if src directory exists in backend
$srcDir = Join-Path $BackendDir "src"
if (-not (Test-Path $srcDir)) {
    Write-Host "ERROR: src directory not found in: $BackendDir" -ForegroundColor Red
    Write-Host "Please ensure you're in the correct project directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if port is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    $processId = $portInUse.OwningProcess | Select-Object -Unique
    Write-Host "WARNING: Port 8000 is already in use!" -ForegroundColor Red
    Write-Host ""
    foreach ($pid in $processId) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  Process ID: $pid ($($process.ProcessName))" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    Write-Host "To fix this:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\check_port.ps1 (in this directory)" -ForegroundColor White
    Write-Host "  2. Or kill manually: taskkill /PID <PID> /F" -ForegroundColor White
    Write-Host "  3. Or use different port: --port 8001" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (may fail) (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""
}

# Start API in new window
Write-Host "Starting API server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: API will run in a new window" -ForegroundColor Yellow
Write-Host "      Close that window to stop the API" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend directory: $BackendDir" -ForegroundColor Gray
Write-Host ""

# Build the command string with proper escaping
$apiCommand = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server'
cd '$BackendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server' -ForegroundColor Cyan
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

# Start new PowerShell window
try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
    Write-Host ""
    Write-Host "SUCCESS: API server started in background window" -ForegroundColor Green
    Write-Host ""
    Write-Host "To verify:" -ForegroundColor Cyan
    Write-Host "  1. Check the new PowerShell window for server logs" -ForegroundColor White
    Write-Host "  2. Open browser: http://localhost:8000" -ForegroundColor White
    Write-Host "  3. Or run: curl http://localhost:8000" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to start API server: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Run manually in a terminal:" -ForegroundColor Yellow
    Write-Host "  cd $BackendDir" -ForegroundColor White
    Write-Host "  python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to continue"
