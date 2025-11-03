# PowerShell Script: Start API Server in Background Window
# Usage: Double-click or run in PowerShell

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir ".."

Write-Host "================================================"
Write-Host "  Starting AI Trader API Server"
Write-Host "================================================"
Write-Host ""
Write-Host "Working Directory: $BackendDir"
Write-Host "API Address: http://localhost:8000"
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion"
} catch {
    Write-Host "Error: Python not found"
    Write-Host "Please ensure Python is installed and in PATH"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if port is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Warning: Port 8000 is already in use"
    Write-Host "If this is a previous API instance, you can ignore this"
    Write-Host ""
}

# Start API in new window
Write-Host "Starting API server..."
Write-Host ""
Write-Host "Note: API will run in a new window"
Write-Host "      Close that window to stop the API"
Write-Host ""

$apiCommand = @"
cd "$BackendDir"
Write-Host "================================================"
Write-Host "  AI Trader API Server"
Write-Host "================================================"
Write-Host ""
Write-Host "API Address: http://localhost:8000"
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
Write-Host ""
Write-Host "API server stopped"
Read-Host "Press Enter to close window"
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand

Write-Host ""
Write-Host "API server started in background"
Write-Host ""
Write-Host "Verify:"
Write-Host "   1. Open browser: http://localhost:8000"
Write-Host "   2. Or run: curl http://localhost:8000"
Write-Host ""
Read-Host "Press Enter to continue"
