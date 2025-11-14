# Start API using Windows Task Scheduler (后台运行，关闭CMD也能运行)
# 使用任务计划程序在后台运行API，即使关闭CMD也能继续运行
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API - Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$taskName = "AITraderAPI"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Task '$taskName' already exists" -ForegroundColor Yellow
    $action = Read-Host "  (R)estart, (D)elete, or (C)ancel?"
    
    if ($action -eq "R" -or $action -eq "r") {
        Write-Host "[ACTION] Restarting task..." -ForegroundColor Cyan
        Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Start-ScheduledTask -TaskName $taskName
        Write-Host "[OK] Task restarted" -ForegroundColor Green
        exit 0
    } elseif ($action -eq "D" -or $action -eq "d") {
        Write-Host "[ACTION] Deleting task..." -ForegroundColor Cyan
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "[OK] Task deleted" -ForegroundColor Green
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
$startupScript = Join-Path $ProjectRoot "scripts\api_task_wrapper.bat"
$scriptContent = @"
@echo off
cd /d "$ProjectRoot"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 >> "$ProjectRoot\logs\api_task.log" 2>&1
"@

$scriptContent | Out-File -FilePath $startupScript -Encoding ASCII -Force
Write-Host "[OK] Created startup script: $startupScript" -ForegroundColor Green

# Create logs directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Create scheduled task action
$action = New-ScheduledTaskAction -Execute $startupScript -WorkingDirectory $ProjectRoot

# Create trigger (at logon)
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

# Create principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Register task
Write-Host ""
Write-Host "[INSTALL] Creating scheduled task..." -ForegroundColor Cyan
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "AI Trader API Server - Runs in background" | Out-Null

Write-Host "[OK] Task created" -ForegroundColor Green
Write-Host ""
Write-Host "[START] Starting task..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName $taskName

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Task Status" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Get-ScheduledTask -TaskName $taskName | Format-List

$taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Task State: $($taskInfo.State)" -ForegroundColor $(if ($taskInfo.State -eq "Running") { "Green" } else { "Yellow" })
Write-Host ""

Write-Host "Task Management:" -ForegroundColor Cyan
Write-Host "  Start:   Start-ScheduledTask -TaskName $taskName" -ForegroundColor White
Write-Host "  Stop:    Stop-ScheduledTask -TaskName $taskName" -ForegroundColor White
Write-Host "  Status:  Get-ScheduledTaskInfo -TaskName $taskName" -ForegroundColor White
Write-Host "  Delete:  .\scripts\start_api_task_scheduler.ps1 (then choose Delete)" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Cyan
Write-Host "  Output:  $logDir\api_task.log" -ForegroundColor White
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Local:   http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Note:" -ForegroundColor Yellow
Write-Host "  * Task runs at logon (starts when you log in)" -ForegroundColor White
Write-Host "  * Task continues running even if you close CMD" -ForegroundColor White
Write-Host "  * To stop: Stop-ScheduledTask -TaskName $taskName" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to continue"

