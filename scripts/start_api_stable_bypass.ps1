# PowerShell Script: Start API Server (Stable Version with Bypass)
# Stable version: Auto-restart, error handling (bypass execution policy)
# Usage: .\scripts\start_api_stable_bypass.ps1

$ErrorActionPreference = "Continue"

# Get project root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"

# Get local IP address for sharing
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress
if (-not $localIP) {
    $localIP = "YOUR_IP_ADDRESS"
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API Server (Stable Version)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project Directory: $ProjectRoot" -ForegroundColor Gray
Write-Host ""
Write-Host "Local Access:" -ForegroundColor Cyan
Write-Host "  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Share with others (same network):" -ForegroundColor Cyan
Write-Host "  http://$localIP:8000/docs" -ForegroundColor Yellow
Write-Host ""

# Check Python environment
Write-Host "[Check] Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "  [OK] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found" -ForegroundColor Red
    Write-Host "  Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check virtual environment
Write-Host "[Check] Virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "  [OK] Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Virtual environment not found, will use system Python" -ForegroundColor Yellow
}

# Check and stop old API processes
Write-Host "[Check] Port 8000..." -ForegroundColor Yellow
$portConnections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portConnections) {
    $processIds = $portConnections.OwningProcess | Select-Object -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  Found process: PID $processId ($($process.ProcessName))" -ForegroundColor Yellow
            Write-Host "  Stopping..." -ForegroundColor Yellow
            try {
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Host "  [OK] Process $processId stopped" -ForegroundColor Green
            } catch {
                $errorMsg = $_.Exception.Message
                Write-Host "  [ERROR] Failed to stop process $processId : $errorMsg" -ForegroundColor Red
            }
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  [OK] Port 8000 is available" -ForegroundColor Green
}

# Create logs directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host ""
Write-Host "[Start] API server..." -ForegroundColor Cyan
Write-Host ""

# Build startup command (with error handling and auto-restart)
$apiCommand = @"
`$ErrorActionPreference = "Continue"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server (Stable)'
cd '$ProjectRoot'

# Activate virtual environment (if exists)
if (Test-Path '.venv\Scripts\Activate.ps1') {
    . '.venv\Scripts\Activate.ps1'
    Write-Host '[ENV] Virtual environment activated' -ForegroundColor Green
}

Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server (Stable)' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Local Access: http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host 'Share Link: http://' + '$localIP' + ':8000/docs' -ForegroundColor Yellow
Write-Host 'Current Directory: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host 'Features:' -ForegroundColor Cyan
Write-Host '  * Auto error handling' -ForegroundColor White
Write-Host '  * Auto restart on crash' -ForegroundColor White
Write-Host '  * Logging' -ForegroundColor White
Write-Host ''
Write-Host 'Press Ctrl+C to stop server' -ForegroundColor Yellow
Write-Host ''

# Auto-restart loop
`$maxRestarts = 10
`$restartCount = 0
`$restartDelay = 5

while (`$restartCount -lt `$maxRestarts) {
    try {
        Write-Host "[Start] Attempt `$(`$restartCount + 1)/`$maxRestarts..." -ForegroundColor Cyan
        Write-Host ""
        
        # Start API server
        python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
        
        # If normal exit (Ctrl+C), don't restart
        Write-Host ""
        Write-Host "[Exit] API server stopped normally" -ForegroundColor Green
        break
        
    } catch {
        `$restartCount++
        Write-Host ""
        Write-Host "[ERROR] API server crashed: `$_" -ForegroundColor Red
        Write-Host "[ERROR] Error details: `$(`$_.Exception.Message)" -ForegroundColor Red
        
        if (`$restartCount -ge `$maxRestarts) {
            Write-Host ""
            Write-Host "[STOP] Max restarts reached (`$maxRestarts), stopping auto-restart" -ForegroundColor Red
            Write-Host "Please check error logs and fix issues manually" -ForegroundColor Yellow
            break
        }
        
        Write-Host ""
        Write-Host "[RESTART] Restarting in `$restartDelay seconds (attempt `$restartCount)..." -ForegroundColor Yellow
        Start-Sleep -Seconds `$restartDelay
        Write-Host ""
    }
}

Write-Host ""
Write-Host "API server stopped" -ForegroundColor Yellow
Read-Host "Press Enter to close window"
"@

# Start new window (with Bypass execution policy)
try {
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $apiCommand
    Write-Host "[OK] API server started in new window" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verification steps:" -ForegroundColor Cyan
    Write-Host "  1. Check the new PowerShell window for server logs" -ForegroundColor White
    Write-Host "  2. Open browser: http://127.0.0.1:8000/docs" -ForegroundColor White
    Write-Host "  3. Test status: http://127.0.0.1:8000/api/agents/status" -ForegroundColor White
    Write-Host ""
    Write-Host "Note:" -ForegroundColor Yellow
    Write-Host "  * API window must stay open" -ForegroundColor White
    Write-Host "  * Closing window will stop API" -ForegroundColor White
    Write-Host "  * Auto-restart on crash (max 10 times)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start API server: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Run manually in terminal:" -ForegroundColor Yellow
    Write-Host "  cd $ProjectRoot" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to continue"
