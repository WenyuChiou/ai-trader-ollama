# Setup Auto-Start for AI Trader (Backend + Cloudflare Tunnel)
# Creates Task Scheduler tasks for both services to start at logon
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\setup_autostart.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader - Auto-Start Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

# Create logs directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# ── Helper: Register or Manage Task ──────────────────────────────────────────

function Setup-ScheduledTask {
    param(
        [string]$TaskName,
        [string]$WrapperScript,
        [string]$Description
    )

    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "Task: $TaskName" -ForegroundColor Cyan
    Write-Host "  Script: $WrapperScript" -ForegroundColor White
    Write-Host ""

    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "[INFO] Task '$TaskName' already exists" -ForegroundColor Yellow
        $action = Read-Host "  (R)estart, (D)elete and recreate, or (S)kip?"

        if ($action -eq "S" -or $action -eq "s") {
            Write-Host "[SKIP] Keeping existing task" -ForegroundColor Yellow
            Write-Host ""
            return
        } elseif ($action -eq "R" -or $action -eq "r") {
            Write-Host "[ACTION] Restarting task..." -ForegroundColor Cyan
            Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Start-ScheduledTask -TaskName $TaskName
            Write-Host "[OK] Task restarted" -ForegroundColor Green
            Write-Host ""
            return
        } else {
            Write-Host "[ACTION] Deleting existing task..." -ForegroundColor Cyan
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
    }

    # Verify wrapper script exists
    if (-not (Test-Path $WrapperScript)) {
        Write-Host "[ERROR] Wrapper script not found: $WrapperScript" -ForegroundColor Red
        Write-Host ""
        return
    }

    # Create scheduled task
    $taskAction = New-ScheduledTaskAction -Execute $WrapperScript -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask -TaskName $TaskName -Action $taskAction -Trigger $trigger -Settings $settings -Principal $principal -Description $Description | Out-Null
    Write-Host "[OK] Task '$TaskName' created" -ForegroundColor Green

    # Start immediately
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2

    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($taskInfo) {
        Write-Host "[OK] Status: $($taskInfo.LastTaskResult)" -ForegroundColor Green
    }
    Write-Host ""
}

# ── Task 1: AITraderAPI ──────────────────────────────────────────────────────

Write-Host "[1/2] Setting up Backend API task..." -ForegroundColor Cyan
Write-Host ""

$apiWrapper = Join-Path $ProjectRoot "scripts\api_task_wrapper.bat"

# Create api_task_wrapper.bat if it doesn't exist
if (-not (Test-Path $apiWrapper)) {
    Write-Host "[INFO] Creating api_task_wrapper.bat..." -ForegroundColor Yellow

    # Get Python executable
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Host "[INFO] Using virtual environment Python" -ForegroundColor Green
    }

    $apiScriptContent = @"
@echo off
cd /d "$ProjectRoot"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 >> "$ProjectRoot\logs\api_task.log" 2>&1
"@
    $apiScriptContent | Out-File -FilePath $apiWrapper -Encoding ASCII -Force
    Write-Host "[OK] Created $apiWrapper" -ForegroundColor Green
}

Setup-ScheduledTask -TaskName "AITraderAPI" -WrapperScript $apiWrapper -Description "AI Trader API Server - Runs FastAPI backend in background"

# ── Task 2: AITraderTunnel ───────────────────────────────────────────────────

Write-Host "[2/2] Setting up Cloudflare Tunnel task..." -ForegroundColor Cyan
Write-Host ""

$tunnelWrapper = Join-Path $ProjectRoot "scripts\tunnel_task_wrapper.bat"

# Check if named tunnel is configured
$tunnelConfig = Join-Path $ProjectRoot "config\tunnel_config.json"
if (-not (Test-Path $tunnelConfig)) {
    Write-Host "[WARN] Named tunnel not configured yet." -ForegroundColor Yellow
    Write-Host "  Run setup_cloudflare_tunnel.ps1 first for a stable URL." -ForegroundColor Yellow
    Write-Host "  The tunnel task will use ad-hoc mode until configured." -ForegroundColor Yellow
    Write-Host ""
}

Setup-ScheduledTask -TaskName "AITraderTunnel" -WrapperScript $tunnelWrapper -Description "AI Trader Cloudflare Tunnel - Exposes backend to internet"

# ── Summary ──────────────────────────────────────────────────────────────────

Write-Host "================================================" -ForegroundColor Green
Write-Host "  Auto-Start Setup Complete" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tasks registered:" -ForegroundColor White
Write-Host "  AITraderAPI    — Backend API server" -ForegroundColor White
Write-Host "  AITraderTunnel — Cloudflare Tunnel" -ForegroundColor White
Write-Host ""
Write-Host "Both tasks will auto-start at logon with:" -ForegroundColor Cyan
Write-Host "  - Auto-restart on failure (3 retries, 1-min interval)" -ForegroundColor White
Write-Host "  - No execution time limit" -ForegroundColor White
Write-Host "  - Run even on battery power" -ForegroundColor White
Write-Host ""
Write-Host "Management:" -ForegroundColor Cyan
Write-Host "  View:    Get-ScheduledTask -TaskName AITrader*" -ForegroundColor White
Write-Host "  Stop:    Stop-ScheduledTask -TaskName AITraderAPI" -ForegroundColor White
Write-Host "  Start:   Start-ScheduledTask -TaskName AITraderAPI" -ForegroundColor White
Write-Host "  Delete:  Unregister-ScheduledTask -TaskName AITraderAPI" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "  API:     $logDir\api_task.log" -ForegroundColor White
Write-Host "  Tunnel:  $logDir\tunnel_task.log" -ForegroundColor White
Write-Host ""
Write-Host "Verification:" -ForegroundColor Cyan
Write-Host "  1. Reboot your computer" -ForegroundColor White
Write-Host "  2. Wait 30 seconds after login" -ForegroundColor White
Write-Host "  3. Open: http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  4. Check tunnel URL from your phone" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"
