# PowerShell Script: Start Backend + Frontend + Run Demo Loop
# 模拟后端运作，前端展示，且要同步，让用户看到前端有更新
# Usage: powershell -ExecutionPolicy Bypass -File start_demo_sync.ps1

# Encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
try { chcp 65001 | Out-Null } catch { }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Resolve-Path (Join-Path $ScriptDir "..")
$ProjectRoot = Resolve-Path (Join-Path $BackendDir "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"
$API_BASE = "http://127.0.0.1:8000"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader - Demo Sync Mode" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend Dir: $BackendDir" -ForegroundColor Gray
Write-Host "Frontend Dir: $FrontendDir" -ForegroundColor Gray
Write-Host "API Base: $API_BASE" -ForegroundColor Gray
Write-Host ""

# Check if port 8000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "Stopping existing processes..." -ForegroundColor Yellow
    $processes = Get-Process | Where-Object { $_.Path -like "*python*" -or $_.Path -like "*uvicorn*" }
    foreach ($proc in $processes) {
        try {
            $connections = Get-NetTCPConnection -OwningProcess $proc.Id -LocalPort 8000 -ErrorAction SilentlyContinue
            if ($connections) {
                Write-Host "  Stopping process: $($proc.Name) (PID: $($proc.Id))" -ForegroundColor Gray
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    }
    Start-Sleep -Seconds 2
}

# Function to wait for API to be ready
function Wait-APIReady {
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "$API_BASE/api/system/info" -Method GET -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✓ API is ready!" -ForegroundColor Green
                return $true
            }
        } catch {
            $attempt++
            Write-Host "  Waiting for API... ($attempt/$maxAttempts)" -ForegroundColor Yellow -NoNewline
            Write-Host "`r" -NoNewline
            Start-Sleep -Seconds 1
        }
    }
    Write-Host ""
    Write-Host "  ✗ API failed to start" -ForegroundColor Red
    return $false
}

# Start Backend API
Write-Host "[1/5] Starting Backend API..." -ForegroundColor Cyan
$backendCmd = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server'
cd '$BackendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API Address: http://127.0.0.1:8000' -ForegroundColor Green
Write-Host 'Current Directory: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
    Write-Host "  ✓ Backend API starting in new window" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to start backend: $_" -ForegroundColor Red
    exit 1
}

# Wait for API to be ready
Write-Host "[2/5] Waiting for API to be ready..." -ForegroundColor Cyan
if (-not (Wait-APIReady)) {
    Write-Host "Failed to start API. Exiting." -ForegroundColor Red
    exit 1
}

# Start Frontend HTTP Server
Write-Host "[3/5] Starting Frontend Server..." -ForegroundColor Cyan
$frontendCmd = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader Frontend Server'
cd '$FrontendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader Frontend Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Frontend: http://127.0.0.1:8080/monitor.html' -ForegroundColor Green
Write-Host 'Current Directory: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python -m http.server 8080
"@

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
    Write-Host "  ✓ Frontend server starting in new window" -ForegroundColor Green
    Start-Sleep -Seconds 1
} catch {
    Write-Host "  ✗ Failed to start frontend: $_" -ForegroundColor Red
}

# Initialize and run trading loop
Write-Host "[4/5] Initializing system and running trading loop..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

try {
    # Initialize
    Write-Host "  → Initializing system..." -ForegroundColor Yellow
    $initResponse = Invoke-RestMethod -Uri "$API_BASE/api/system/init" -Method POST -ContentType "application/json" -TimeoutSec 30
    if ($initResponse.ok) {
        Write-Host "  ✓ System initialized" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Initialization returned: $($initResponse.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Initialization failed: $_" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

try {
    # Run trading loop
    Write-Host "  → Running trading loop..." -ForegroundColor Yellow
    $loopResponse = Invoke-RestMethod -Uri "$API_BASE/api/trading/run-loop" -Method POST -ContentType "application/json" -TimeoutSec 120
    if ($loopResponse.ok) {
        Write-Host "  ✓ Trading loop completed" -ForegroundColor Green
        if ($loopResponse.message) {
            Write-Host "    Message: $($loopResponse.message)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠ Trading loop returned: $($loopResponse.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Trading loop failed: $_" -ForegroundColor Yellow
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "    Error details: $errorBody" -ForegroundColor Red
    }
}

# Open browser
Write-Host "[5/5] Opening frontend dashboard..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
try {
    Start-Process "http://127.0.0.1:8080/monitor.html"
    Write-Host "  ✓ Browser opened" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Failed to open browser. Please open manually: http://127.0.0.1:8080/monitor.html" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Demo Sync Mode Started Successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend:   http://127.0.0.1:8080/monitor.html" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend will auto-refresh every 30 seconds" -ForegroundColor Gray
Write-Host "You can manually click 'Run Loop' to generate more data" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop:" -ForegroundColor Yellow
Write-Host "  1. Close the backend and frontend PowerShell windows" -ForegroundColor White
Write-Host "  2. Or press Ctrl+C in each window" -ForegroundColor White
Write-Host ""
