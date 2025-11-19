# Fast API Restart Script
# Usage: .\scripts\restart_api_fast.ps1
# Or: powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
# 
# This script quickly restarts the API server by:
# 1. Stopping any process on port 8000
# 2. Starting the API server in a new window with auto-reload

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fast API Server Restart" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}
# If running from scripts/ directory, go up one level
if ($ProjectRoot.Name -eq "scripts" -or (Split-Path -Leaf $ProjectRoot) -eq "scripts") {
    $ProjectRoot = Split-Path $ProjectRoot -Parent
}

$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPath = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

# Check if backend directory exists
if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] Backend directory not found: $BackendDir" -ForegroundColor Red
    exit 1
}

Write-Host "[1/2] Stopping existing API server..." -ForegroundColor Yellow

# Find and stop processes using port 8000
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($pids) {
    foreach ($processId in $pids) {
        try {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Stopping process PID: $processId ($($proc.ProcessName))" -ForegroundColor Gray
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Ignore errors
        }
    }
    
    # Wait briefly for port to be released
    Start-Sleep -Seconds 1
    Write-Host "  [OK] Port released" -ForegroundColor Green
} else {
    Write-Host "  [OK] No running API server found" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/2] Starting new API server..." -ForegroundColor Yellow

# Build command - must run from backend directory
$BackendDirEscaped = $BackendDir -replace "'", "''"

$cmd = "cd '$BackendDirEscaped'; "
if (Test-Path $VenvPath) {
    $VenvPathEscaped = $VenvPath -replace "'", "''"
    $cmd += "& '$VenvPathEscaped'; "
}
# Set PYTHONPATH to backend directory to ensure src module can be found
$cmd += "`$env:PYTHONPATH='$BackendDirEscaped'; "
$cmd += "python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload"

# Start new window
try {
    $argList = @("-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $cmd)
    Start-Process powershell -ArgumentList $argList
    Write-Host "  [OK] API server started in new window" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to start: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  API Server Restart Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  Monitor: file:///$($ProjectRoot.Replace('\', '/'))/frontend/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "Note: API server runs in new window. Close that window to stop the server." -ForegroundColor Gray
Write-Host ""

