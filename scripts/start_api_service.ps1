# Start API as Windows Service (后台运行，关闭CMD也能运行)
# 使用NSSM (Non-Sucking Service Manager) 将API注册为Windows服务
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API - Windows Service Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

# Check if NSSM is installed
$nssmPath = "C:\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "[ERROR] NSSM not found at $nssmPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "NSSM is required to run API as Windows Service." -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Would you like to install NSSM automatically? (Y/N)"
    
    if ($install -eq "Y" -or $install -eq "y") {
        Write-Host ""
        Write-Host "[INSTALL] Installing NSSM..." -ForegroundColor Cyan
        $installScript = Join-Path $ScriptDir "install_nssm.ps1"
        if (Test-Path $installScript) {
            & powershell -ExecutionPolicy Bypass -File $installScript
            # Check again after installation
            if (-not (Test-Path $nssmPath)) {
                Write-Host "[ERROR] NSSM installation failed" -ForegroundColor Red
                Read-Host "Press Enter to exit"
                exit 1
            }
        } else {
            Write-Host "[ERROR] Install script not found: $installScript" -ForegroundColor Red
            Write-Host ""
            Write-Host "Manual installation:" -ForegroundColor Yellow
            Write-Host "  1. Run: powershell -ExecutionPolicy Bypass -File .\scripts\install_nssm.ps1" -ForegroundColor White
            Write-Host "  2. Or download from: https://nssm.cc/download" -ForegroundColor White
            Write-Host "  3. Extract to: C:\nssm\" -ForegroundColor White
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "Manual installation:" -ForegroundColor Yellow
        Write-Host "  1. Run: powershell -ExecutionPolicy Bypass -File .\scripts\install_nssm.ps1" -ForegroundColor White
        Write-Host "  2. Or download from: https://nssm.cc/download" -ForegroundColor White
        Write-Host "  3. Extract to: C:\nssm\" -ForegroundColor White
        Write-Host ""
        Write-Host "Alternative: Use Task Scheduler (no NSSM needed)" -ForegroundColor Cyan
        Write-Host "  Run: powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1" -ForegroundColor White
        Read-Host "Press Enter to exit"
        exit 1
    }
}

$serviceName = "AITraderAPI"

# Check if service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Service '$serviceName' already exists" -ForegroundColor Yellow
    $action = Read-Host "  (R)estart, (S)top, (D)elete, or (C)ancel?"
    
    if ($action -eq "R" -or $action -eq "r") {
        Write-Host "[ACTION] Restarting service..." -ForegroundColor Cyan
        Restart-Service -Name $serviceName -Force
        Write-Host "[OK] Service restarted" -ForegroundColor Green
        exit 0
    } elseif ($action -eq "S" -or $action -eq "s") {
        Write-Host "[ACTION] Stopping service..." -ForegroundColor Cyan
        Stop-Service -Name $serviceName -Force
        Write-Host "[OK] Service stopped" -ForegroundColor Green
        exit 0
    } elseif ($action -eq "D" -or $action -eq "d") {
        Write-Host "[ACTION] Deleting service..." -ForegroundColor Cyan
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        & $nssmPath remove $serviceName confirm
        Write-Host "[OK] Service deleted" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "[CANCEL] No changes made" -ForegroundColor Yellow
        exit 0
    }
}

# Get Python executable
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Get virtual environment Python (if exists)
$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "[INFO] Using virtual environment Python" -ForegroundColor Green
} else {
    Write-Host "[INFO] Using system Python" -ForegroundColor Yellow
}

# Create startup script
$startupScript = Join-Path $ProjectRoot "scripts\api_service_wrapper.bat"
$scriptContent = @"
@echo off
cd /d "$ProjectRoot"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
"@

$scriptContent | Out-File -FilePath $startupScript -Encoding ASCII -Force
Write-Host "[OK] Created startup script: $startupScript" -ForegroundColor Green

# Install service
Write-Host ""
Write-Host "[INSTALL] Installing Windows service..." -ForegroundColor Cyan
& $nssmPath install $serviceName $pythonExe "-m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000"
& $nssmPath set $serviceName AppDirectory $ProjectRoot
& $nssmPath set $serviceName DisplayName "AI Trader API Server"
& $nssmPath set $serviceName Description "AI Trader API Server - Multi-Agent Trading System"
& $nssmPath set $serviceName Start SERVICE_AUTO_START
& $nssmPath set $serviceName AppStdout (Join-Path $ProjectRoot "logs\api_service.log")
& $nssmPath set $serviceName AppStderr (Join-Path $ProjectRoot "logs\api_service_error.log")

# Create logs directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "[OK] Service installed" -ForegroundColor Green
Write-Host ""
Write-Host "[START] Starting service..." -ForegroundColor Cyan
Start-Service -Name $serviceName

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Service Status" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Get-Service -Name $serviceName | Format-Table -AutoSize

Write-Host ""
Write-Host "Service Management:" -ForegroundColor Cyan
Write-Host "  Start:   Start-Service -Name $serviceName" -ForegroundColor White
Write-Host "  Stop:    Stop-Service -Name $serviceName" -ForegroundColor White
Write-Host "  Restart: Restart-Service -Name $serviceName" -ForegroundColor White
Write-Host "  Status:  Get-Service -Name $serviceName" -ForegroundColor White
Write-Host "  Delete:  .\scripts\start_api_service.ps1 (then choose Delete)" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "  Output:  $logDir\api_service.log" -ForegroundColor White
Write-Host "  Errors:  $logDir\api_service_error.log" -ForegroundColor White
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Local:   http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to continue"

