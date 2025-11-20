# Setup Railway Daily Upload Task (PowerShell Script)
# Run this script as Administrator to set up the scheduled task

param(
    [string]$RailwayURL = "https://web-production-b42d6.up.railway.app",
    [string]$Time = "18:00",
    [switch]$WeekdaysOnly = $true
)

$TaskName = "AI-Trader-Railway-Daily-Upload"
$ScriptPath = "scripts\upload_data_to_railway.py"
$WorkingDir = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Railway Daily Upload Task Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or run:" -ForegroundColor Yellow
    Write-Host "  Start-Process powershell -Verb RunAs -ArgumentList '-File', '$PSCommandPath'" -ForegroundColor Gray
    exit 1
}

Write-Host "Task Name: $TaskName" -ForegroundColor Green
Write-Host "Script: $ScriptPath" -ForegroundColor Green
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Green
Write-Host "Railway URL: $RailwayURL" -ForegroundColor Green
Write-Host "Schedule Time: $Time" -ForegroundColor Green
Write-Host "Weekdays Only: $WeekdaysOnly" -ForegroundColor Green
Write-Host ""

# Get Python path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Python Path: $PythonPath" -ForegroundColor Gray
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[INFO] Removed existing task" -ForegroundColor Green
}

# Parse time
try {
    $scheduleTime = [DateTime]::ParseExact($Time.Trim(), "HH:mm", $null)
} catch {
    Write-Host "[ERROR] Invalid time format. Using default: 18:00" -ForegroundColor Red
    $Time = "18:00"
    $scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
}

# Configure Railway URL first
Write-Host "Configuring Railway URL..." -ForegroundColor Cyan
Set-Location $WorkingDir
python scripts\config_railway.py "$RailwayURL" | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Failed to configure Railway URL, but continuing..." -ForegroundColor Yellow
}

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger
if ($WeekdaysOnly) {
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $scheduleTime.ToString("HH:mm")
} else {
    $Trigger = New-ScheduledTaskTrigger -Daily -At $scheduleTime.ToString("HH:mm")
}

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create principal (run as current user)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Limited

# Register task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Upload AI-Trader local data to Railway daily" | Out-Null
    
    Write-Host ""
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule:" -ForegroundColor Cyan
    Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
    Write-Host "  Days: $(if ($WeekdaysOnly) { 'Weekdays (Mon-Fri)' } else { 'Every day' })" -ForegroundColor White
    Write-Host ""
    
    # Verify task
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "[VERIFY] Task verified successfully!" -ForegroundColor Green
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "  State: $($task.State)" -ForegroundColor Gray
        Write-Host "  Next Run: $($taskInfo.NextRunTime)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "To view the task:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host ""
Write-Host "To test manually:" -ForegroundColor Cyan
Write-Host "  python $ScriptPath" -ForegroundColor Gray
Write-Host ""

