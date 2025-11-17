# One-Click API Restart Script
# Usage: .\restart_api.ps1
# Or: powershell -ExecutionPolicy Bypass -File .\restart_api.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  API Server Restart" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

$backendDir = Join-Path $ProjectRoot "backend"
$venvPath = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"

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
    foreach ($pid in $pids) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Stopping process PID: $pid ($($proc.ProcessName))" -ForegroundColor Gray
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
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
if (Test-Path $venvPath) {
    Write-Host "  [OK] Virtual environment found: $venvPath" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Virtual environment not found, will use system Python" -ForegroundColor Yellow
    Write-Host "    Virtual env path: $venvPath" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[3/3] Starting new API server..." -ForegroundColor Yellow

# Build command
$backendDirEscaped = $backendDir -replace "'", "''"
$venvPathEscaped = $venvPath -replace "'", "''"

$cmd = "cd '$backendDirEscaped'; "
if (Test-Path $venvPath) {
    $cmd += "& '$venvPathEscaped'; "
}
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
Write-Host "  Monitor: http://127.0.0.1:8000/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "Note: API server runs in new window. Close that window to stop the server." -ForegroundColor Gray
Write-Host ""
