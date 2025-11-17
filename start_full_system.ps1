# PowerShell Script: Start Full System (API + Frontend)
# Usage: Double-click or run in PowerShell from project root

$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Trader Full System" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path (Join-Path $ProjectRoot "README.md"))) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    Write-Host "Current directory: $ProjectRoot" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if port 8000 is in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "WARNING: Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "API may already be running. Continuing..." -ForegroundColor Yellow
    Write-Host ""
} else {
    # Start API Server
    Write-Host "Starting API Server..." -ForegroundColor Cyan
    $apiCommand = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server'
cd '$BackendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API Address: http://localhost:8000' -ForegroundColor Green
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
    Write-Host "API Server started in background window" -ForegroundColor Green
    Write-Host ""
    
    # Wait a bit for API to start
    Write-Host "Waiting for API to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

# Check if port 3000 is in use
$frontendPortInUse = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (-not $frontendPortInUse) {
    # Start Frontend Server
    Write-Host "Starting Frontend Server..." -ForegroundColor Cyan
    $frontendCommand = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader Frontend Server'
cd '$FrontendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader Frontend Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Frontend Address: http://localhost:3000/monitor.html' -ForegroundColor Green
Write-Host ''
Write-Host 'Press Ctrl+C to stop the server' -ForegroundColor Yellow
Write-Host ''
python -m http.server 3000
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand
    Write-Host "Frontend Server started in background window" -ForegroundColor Green
    Write-Host ""
    
    # Wait a bit for frontend to start
    Start-Sleep -Seconds 2
    
    # Open browser
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000/monitor.html"
} else {
    Write-Host "Frontend server may already be running on port 3000" -ForegroundColor Yellow
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:3000/monitor.html"
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  System Started Successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Server: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:3000/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "To stop:" -ForegroundColor Yellow
Write-Host "  - Close the API server window (port 8000)" -ForegroundColor White
Write-Host "  - Close the Frontend server window (port 3000)" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"

