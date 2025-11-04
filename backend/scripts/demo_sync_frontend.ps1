# PowerShell Script: Demo Backend + Frontend Sync
# 運行交易循環並同步更新前端顯示
# Usage: .\demo_sync_frontend.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$FrontendDir = Join-Path (Split-Path -Parent $BackendDir) "frontend"
$API_BASE = "http://127.0.0.1:8000"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Backend + Frontend Sync Demo" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if API is running
Write-Host "[1/5] Checking Backend API..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/api/system/info" -Method GET -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Backend API is running" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ Backend API is not running!" -ForegroundColor Red
    Write-Host "  Please start the backend API first:" -ForegroundColor Yellow
    Write-Host "    cd backend\scripts" -ForegroundColor White
    Write-Host "    .\start_api_background.ps1" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Start Frontend HTTP Server
Write-Host "[2/5] Starting Frontend HTTP Server..." -ForegroundColor Cyan
if (-not (Test-Path $FrontendDir)) {
    Write-Host "  ✗ Frontend directory not found: $FrontendDir" -ForegroundColor Red
    exit 1
}

$frontendCmd = @"
`$host.ui.RawUI.WindowTitle = 'Frontend HTTP Server'
cd '$FrontendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  Frontend HTTP Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Frontend URL: http://localhost:8080/monitor.html' -ForegroundColor Green
Write-Host 'Current Directory: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python -m http.server 8080
"@

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
    Write-Host "  ✓ Frontend server starting on port 8080" -ForegroundColor Green
    Start-Sleep -Seconds 2
} catch {
    Write-Host "  ✗ Failed to start frontend: $_" -ForegroundColor Red
    exit 1
}

# Open browser
Write-Host "[3/5] Opening browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 1
Start-Process "http://localhost:8080/monitor.html"
Write-Host "  ✓ Browser opened" -ForegroundColor Green

# Initialize if needed
Write-Host "[4/5] Initializing system..." -ForegroundColor Cyan
try {
    $initResponse = Invoke-RestMethod -Uri "$API_BASE/api/system/init" -Method POST -ContentType "application/json" -TimeoutSec 30
    if ($initResponse.ok) {
        Write-Host "  ✓ System initialized" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Initialization returned: $($initResponse.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Initialization failed: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] Running trading loops..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  This will run trading cycles every 30 seconds" -ForegroundColor Gray
Write-Host "  Watch the frontend for updates!" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$loopCount = 0
$maxLoops = 10  # Run 10 loops or until stopped

while ($loopCount -lt $maxLoops) {
    $loopCount++
    Write-Host "[Loop $loopCount] Running trading cycle..." -ForegroundColor Cyan
    
    try {
        $runResponse = Invoke-RestMethod -Uri "$API_BASE/api/trading/run-loop" -Method POST -ContentType "application/json" -TimeoutSec 60
        
        if ($runResponse.ok) {
            Write-Host "  ✓ Trading cycle completed" -ForegroundColor Green
            if ($runResponse.orders_placed) {
                Write-Host "    Orders placed: $($runResponse.orders_placed)" -ForegroundColor Gray
            }
            if ($runResponse.conversations_generated) {
                Write-Host "    Conversations: $($runResponse.conversations_generated)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ⚠️  Trading cycle returned: $($runResponse.error)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ✗ Trading cycle failed: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "  Waiting 30 seconds before next cycle..." -ForegroundColor Gray
    Write-Host "  (Frontend auto-refreshes every 30 seconds)" -ForegroundColor Gray
    Write-Host ""
    
    if ($loopCount -lt $maxLoops) {
        Start-Sleep -Seconds 30
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Demo Complete" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend URL: http://localhost:8080/monitor.html" -ForegroundColor Green
Write-Host "Backend API:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend will continue to auto-refresh every 30 seconds" -ForegroundColor Gray
Write-Host "You can manually refresh or run more trading cycles" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"

