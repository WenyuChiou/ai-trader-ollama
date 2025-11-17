# Step 3: Start Services
# 启动后端 API 服务器

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Ollama - Step 3: Start Services" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "[Step 3.1] Checking prerequisites..." -ForegroundColor Yellow

# Check if Ollama is running
Write-Host "[Step 3.1.1] Checking Ollama service..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama is not running or not accessible" -ForegroundColor Yellow
    Write-Host "  Please start Ollama in a separate terminal:" -ForegroundColor White
    Write-Host "    ollama serve" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
}

Write-Host ""

# Check if port 8000 is available
Write-Host "[Step 3.1.2] Checking if port 8000 is available..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[WARN] Port 8000 is already in use" -ForegroundColor Yellow
    Write-Host "  Another process may be using this port." -ForegroundColor White
    Write-Host "  You can:" -ForegroundColor White
    Write-Host "    1. Stop the existing process" -ForegroundColor White
    Write-Host "    2. Or use a different port (modify server.py)" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "[OK] Port 8000 is available" -ForegroundColor Green
}

Write-Host ""

Write-Host "[Step 3.2] Starting API server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Options:" -ForegroundColor Cyan
Write-Host "  1. Quick Start (Development) - Runs in current window" -ForegroundColor White
Write-Host "  2. Background Service (Production) - Runs in background, auto-restart" -ForegroundColor White
Write-Host "  3. Task Scheduler (Long-term) - Runs for weeks/months, survives reboots" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Choose option (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[INFO] Starting API server in development mode..." -ForegroundColor Yellow
        Write-Host "  API will be available at: http://localhost:8000" -ForegroundColor Green
        Write-Host "  API docs at: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host "  Press Ctrl+C to stop" -ForegroundColor Yellow
        Write-Host ""
        
        # Activate virtual environment
        $venvPath = Join-Path $ProjectRoot ".venv"
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            & $activateScript
        }
        
        # Change to backend directory
        $backendDir = Join-Path $ProjectRoot "backend"
        Set-Location $backendDir
        
        # Start server
        python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
    }
    "2" {
        Write-Host ""
        Write-Host "[INFO] Setting up background service..." -ForegroundColor Yellow
        Write-Host "  This will install the API as a Windows Service" -ForegroundColor White
        Write-Host "  Requires administrator privileges" -ForegroundColor Yellow
        Write-Host ""
        $adminScript = Join-Path $ProjectRoot "scripts\start_api_service_admin.bat"
        if (Test-Path $adminScript) {
            Write-Host "  Right-click and run as administrator:" -ForegroundColor White
            Write-Host "    scripts\start_api_service_admin.bat" -ForegroundColor Green
        } else {
            Write-Host "  Run as administrator:" -ForegroundColor White
            Write-Host "    powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1" -ForegroundColor Green
        }
        Write-Host ""
        Read-Host "Press Enter after setting up the service"
    }
    "3" {
        Write-Host ""
        Write-Host "[INFO] Setting up Task Scheduler (recommended for long-term running)..." -ForegroundColor Yellow
        Write-Host "  This will create a scheduled task that runs in background" -ForegroundColor White
        Write-Host "  Requires administrator privileges" -ForegroundColor Yellow
        Write-Host ""
        $adminScript = Join-Path $ProjectRoot "scripts\start_api_task_admin.bat"
        if (Test-Path $adminScript) {
            Write-Host "  Right-click and run as administrator:" -ForegroundColor White
            Write-Host "    scripts\start_api_task_admin.bat" -ForegroundColor Green
        } else {
            Write-Host "  Run as administrator:" -ForegroundColor White
            Write-Host "    powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1" -ForegroundColor Green
        }
        Write-Host ""
        Write-Host "  After setup, the API will:" -ForegroundColor Cyan
        Write-Host "    ✅ Auto-start on system boot" -ForegroundColor Green
        Write-Host "    ✅ Auto-restart on crash" -ForegroundColor Green
        Write-Host "    ✅ Run in background (close CMD and keep running)" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter after setting up the task"
    }
    default {
        Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Step 3 Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "API Server Status:" -ForegroundColor Cyan
Write-Host "  Check API: http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Frontend Access:" -ForegroundColor Cyan
Write-Host "  Local: http://localhost:3000/monitor.html" -ForegroundColor White
Write-Host "  Or open: frontend\monitor.html in your browser" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open frontend/monitor.html in your browser" -ForegroundColor White
Write-Host "  2. Click 'Execute Trade' to run a trading cycle" -ForegroundColor White
Write-Host "  3. View agent conversations and portfolio status" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"

