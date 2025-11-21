# Start API as Windows Service using NSSM (Non-Sucking Service Manager)
# 使用 NSSM 将 API 设置为 Windows 服务
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API - Windows Service Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$serviceName = "AITraderAPI"

# Check if NSSM is available
$nssmPath = Join-Path $ProjectRoot "tools\nssm\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "[INFO] NSSM not found, downloading..." -ForegroundColor Yellow
    
    # Create tools directory
    $toolsDir = Join-Path $ProjectRoot "tools"
    if (-not (Test-Path $toolsDir)) {
        New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
    }
    
    $nssmDir = Join-Path $toolsDir "nssm"
    if (-not (Test-Path $nssmDir)) {
        New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
    }
    
    # Download NSSM (64-bit)
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $zipPath = Join-Path $toolsDir "nssm.zip"
    
    Write-Host "[DOWNLOAD] Downloading NSSM..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $zipPath -UseBasicParsing
        
        # Extract NSSM
        Write-Host "[EXTRACT] Extracting NSSM..." -ForegroundColor Cyan
        Expand-Archive -Path $zipPath -DestinationPath $nssmDir -Force
        
        # Find nssm.exe (it's in win64 subdirectory)
        $nssmExe = Get-ChildItem -Path $nssmDir -Filter "nssm.exe" -Recurse | Select-Object -First 1
        if ($nssmExe) {
            Copy-Item $nssmExe.FullName -Destination $nssmPath -Force
            Write-Host "[OK] NSSM installed: $nssmPath" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Could not find nssm.exe in archive" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
        
        # Clean up
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "[ERROR] Failed to download NSSM: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download NSSM manually:" -ForegroundColor Yellow
        Write-Host "  1. Visit: https://nssm.cc/download" -ForegroundColor Cyan
        Write-Host "  2. Extract nssm.exe to: $nssmPath" -ForegroundColor Cyan
        Write-Host "  3. Run this script again" -ForegroundColor Cyan
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[INFO] Service '$serviceName' already exists" -ForegroundColor Yellow
    Write-Host "  Status: $($existingService.Status)" -ForegroundColor Gray
    Write-Host ""
    $action = Read-Host "  (R)estart, (S)top, (D)elete, or (C)ancel?"
    
    if ($action -eq "R" -or $action -eq "r") {
        Write-Host "[ACTION] Restarting service..." -ForegroundColor Cyan
        Restart-Service -Name $serviceName -Force
        Write-Host "[OK] Service restarted" -ForegroundColor Green
        Start-Sleep -Seconds 2
        $service = Get-Service -Name $serviceName
        Write-Host "  Status: $($service.Status)" -ForegroundColor Gray
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
    Write-Host "[INFO] Using virtual environment Python: $pythonExe" -ForegroundColor Green
} else {
    Write-Host "[INFO] Using system Python: $pythonExe" -ForegroundColor Yellow
}

# Create logs directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$logFile = Join-Path $logDir "api_service.log"
$errorLogFile = Join-Path $logDir "api_service_error.log"

# Install service using NSSM
Write-Host ""
Write-Host "[INSTALL] Installing Windows Service..." -ForegroundColor Cyan
Write-Host "  Service Name: $serviceName" -ForegroundColor Gray
Write-Host "  Python: $pythonExe" -ForegroundColor Gray
Write-Host "  Working Directory: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# NSSM install command
$appPath = $pythonExe
$appArgs = "-m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000"
$appDir = $ProjectRoot

# Install service
& $nssmPath install $serviceName $appPath $appArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install service" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Configure service
Write-Host "[CONFIG] Configuring service..." -ForegroundColor Cyan

# Set working directory (use project root, not Scripts directory)
$projectRoot = $ProjectRoot
& $nssmPath set $serviceName AppDirectory $projectRoot

# Set description
& $nssmPath set $serviceName Description "AI Trader API Server - Multi-Agent Trading System"

# Set display name
& $nssmPath set $serviceName DisplayName "AI Trader API"

# Set startup type (Automatic)
& $nssmPath set $serviceName Start SERVICE_AUTO_START

# Set output files
& $nssmPath set $serviceName AppStdout $logFile
& $nssmPath set $serviceName AppStderr $errorLogFile

# Set output file rotation
& $nssmPath set $serviceName AppRotateFiles 1
& $nssmPath set $serviceName AppRotateOnline 1
& $nssmPath set $serviceName AppRotateSeconds 86400  # Rotate daily
& $nssmPath set $serviceName AppRotateBytes 10485760  # 10MB

# Set restart options
& $nssmPath set $serviceName AppRestartDelay 5000  # 5 seconds delay before restart
& $nssmPath set $serviceName AppExit Default Restart  # Restart on exit

# Set environment variables (if virtual environment)
if (Test-Path $venvPython) {
    $venvPath = Split-Path -Parent (Split-Path -Parent $venvPython)
    & $nssmPath set $serviceName AppEnvironmentExtra "VIRTUAL_ENV=$venvPath"
}

Write-Host "[OK] Service configured" -ForegroundColor Green

# Start service
Write-Host ""
Write-Host "[START] Starting service..." -ForegroundColor Cyan
Start-Service -Name $serviceName

Start-Sleep -Seconds 3

# Check status
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "  Service Installed Successfully!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service Name: $serviceName" -ForegroundColor Gray
    Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Yellow' })
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Cyan
    Write-Host "  Start:   Start-Service -Name $serviceName" -ForegroundColor Gray
    Write-Host "  Stop:    Stop-Service -Name $serviceName" -ForegroundColor Gray
    Write-Host "  Restart: Restart-Service -Name $serviceName" -ForegroundColor Gray
    Write-Host "  Status:  Get-Service -Name $serviceName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Log Files:" -ForegroundColor Cyan
    Write-Host "  Output:  $logFile" -ForegroundColor Gray
    Write-Host "  Errors:  $errorLogFile" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor Cyan
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  Monitor:   file:///$($ProjectRoot.Replace('\', '/'))/frontend/monitor.html" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[ERROR] Service not found after installation" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

