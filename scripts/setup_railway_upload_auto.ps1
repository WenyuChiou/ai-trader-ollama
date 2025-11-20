# Auto Setup Railway Daily Upload Task (Non-Interactive)
# This script sets up daily upload task with default settings: 18:00, weekdays only

$TaskName = "AI-Trader-Railway-Daily-Upload"
$ScriptPath = "scripts\upload_data_to_railway.py"
$WorkingDir = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Railway Daily Upload Task Setup (Auto)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Get Python path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python Path: $PythonPath" -ForegroundColor Gray
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Gray
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
    Write-Host "[INFO] Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[INFO] Removed existing task" -ForegroundColor Green
}

# Default settings: 18:00, weekdays only
$scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
$weekdaysOnly = $true

Write-Host "Schedule Configuration:" -ForegroundColor Cyan
Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
Write-Host "  Days: Weekdays (Mon-Fri)" -ForegroundColor White
Write-Host "  Mode: Upload data to Railway only" -ForegroundColor White
Write-Host ""

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger (weekdays only)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $scheduleTime.ToString("HH:mm")

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
        -Description "Upload AI-Trader local data to Railway daily at 18:00 (weekdays only)" | Out-Null
    
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName" -ForegroundColor White
    Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
    Write-Host "  Days: Weekdays (Mon-Fri)" -ForegroundColor White
    Write-Host "  Script: $ScriptPath" -ForegroundColor White
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Cyan
    Write-Host "  python $ScriptPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To remove the task:" -ForegroundColor Cyan
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you're running as Administrator" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

