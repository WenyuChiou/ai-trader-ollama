# Simple Daily Upload Setup - Creates task with default settings
# Usage: Run PowerShell as Administrator, then:
# powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_upload_simple.ps1

$TaskName = "AI-Trader-Daily-Upload-Only"
$ScriptPath = "scripts\upload_data_to_railway.py"
$WorkingDir = (Get-Location).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Daily Upload Setup (Simple)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator rights!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the batch file:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup_daily_upload_admin.bat" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Get Python path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Task Name: $TaskName" -ForegroundColor Green
Write-Host "Script: $ScriptPath" -ForegroundColor Green
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Green
Write-Host "Python: $PythonPath" -ForegroundColor Green
Write-Host ""

# Remove existing task if exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Default settings
$scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
$weekdaysOnly = $true

Write-Host "Schedule:" -ForegroundColor Cyan
Write-Host "  Time: 18:00 (6 PM)" -ForegroundColor White
Write-Host "  Days: Weekdays (Mon-Fri)" -ForegroundColor White
Write-Host "  Mode: Upload only (no trading cycle)" -ForegroundColor White
Write-Host ""

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger (weekdays only)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "18:00"

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create principal
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
        -Description "Upload AI-Trader data to Railway daily (upload only, no trading cycle)" | Out-Null
    
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "  Name: $($task.TaskName)" -ForegroundColor White
    Write-Host "  State: $($task.State)" -ForegroundColor White
    if ($task.NextRunTime) {
        Write-Host "  Next Run: $($task.NextRunTime)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Cyan
    Write-Host "  python $ScriptPath" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

