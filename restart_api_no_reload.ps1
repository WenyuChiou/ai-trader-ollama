# One-Click API Restart Script (No Auto-Reload)
# Usage: .\restart_api_no_reload.ps1
# This version runs without --reload to avoid reload errors in logs

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  API Server Restart (No Auto-Reload)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

$backendDir = Join-Path $ProjectRoot "backend"
$venvPath1 = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
$venvPath2 = Join-Path $ProjectRoot "backend\venv\Scripts\Activate.ps1"
$venvPath = $null
if (Test-Path $venvPath1) {
    $venvPath = $venvPath1
} elseif (Test-Path $venvPath2) {
    $venvPath = $venvPath2
}

# Check if backend directory exists
if (-not (Test-Path $backendDir)) {
    Write-Host "[ERROR] Backend directory not found: $backendDir" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Stopping existing API server..." -ForegroundColor Yellow

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
    
    # Wait for port to be released (max 3 seconds)
    $waitCount = 0
    while ($waitCount -lt 6) {
        Start-Sleep -Milliseconds 500
        $inUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if (-not $inUse) { 
            Write-Host "  [OK] Port released" -ForegroundColor Green
            break 
        }
        $waitCount++
    }
    
    if ($waitCount -ge 6) {
        Write-Host "  [WARN] Port may still be in use" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] No running API server found" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] Checking virtual environment..." -ForegroundColor Yellow

# Check virtual environment
if ($venvPath) {
    Write-Host "  [OK] Virtual environment found: $venvPath" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Virtual environment not found, will use system Python" -ForegroundColor Yellow
    Write-Host "    Checked paths:" -ForegroundColor Gray
    Write-Host "      - $venvPath1" -ForegroundColor Gray
    Write-Host "      - $venvPath2" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[3/3] Starting new API server..." -ForegroundColor Yellow

# Build command - must run from backend directory
$backendDirEscaped = $backendDir -replace "'", "''"

$cmd = "cd '$backendDirEscaped'; "
if ($venvPath) {
    $venvPathEscaped = $venvPath -replace "'", "''"
    $cmd += "& '$venvPathEscaped'; "
}
# Set PYTHONPATH to backend directory to ensure src module can be found
$cmd += "`$env:PYTHONPATH='$backendDirEscaped'; "
# NOTE: No --reload flag to avoid reload errors in logs
$cmd += "python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000"

# Start new window
try {
    $argList = @("-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $cmd)
    Start-Process powershell -ArgumentList $argList
    Write-Host "  [OK] API server started in new window (no auto-reload)" -ForegroundColor Green
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
Write-Host "  Monitor: http://127.0.0.1:8000/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "Note: API server runs WITHOUT auto-reload to avoid reload errors." -ForegroundColor Gray
Write-Host "      Use .\restart_api.ps1 if you want auto-reload (with reload errors)." -ForegroundColor Gray
Write-Host ""

