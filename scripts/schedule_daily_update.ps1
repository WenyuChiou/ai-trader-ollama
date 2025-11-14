# Windows PowerShell: Schedule Daily Update Task
# Usage: powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_update.ps1

$TaskName = "AI-Trader-Daily-Update"
# Choose script: run_cycle_and_upload_to_railway.py (runs cycle + upload) or upload_data_to_railway.py (upload only)
$ScriptPath = "scripts\run_cycle_and_upload_to_railway.py"
$WorkingDir = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Daily Update Task Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Name: $TaskName" -ForegroundColor Green
Write-Host "Script: $ScriptPath" -ForegroundColor Green
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Green
Write-Host ""

# Get Python path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python Path: $PythonPath" -ForegroundColor Gray
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and recreate it? (y/n)"
    if ($response -eq "y") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[INFO] Removed existing task" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Keeping existing task" -ForegroundColor Green
        exit 0
    }
}

# Get schedule time
Write-Host "Schedule Configuration:" -ForegroundColor Cyan
$timeInput = Read-Host "Enter time (HH:MM format, e.g., 18:00 for 6 PM)"
# Trim whitespace from input
$timeInput = $timeInput.Trim()
try {
    $scheduleTime = [DateTime]::ParseExact($timeInput, "HH:mm", $null)
} catch {
    Write-Host "[ERROR] Invalid time format. Using default: 18:00" -ForegroundColor Red
    $scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
}

Write-Host ""
Write-Host "Choose upload mode:" -ForegroundColor Cyan
Write-Host "  1. Full cycle + upload (runs trading cycle, then uploads) - Recommended" -ForegroundColor White
Write-Host "  2. Upload only (uploads existing data, no trading cycle) - Faster" -ForegroundColor White
$modeChoice = Read-Host "Enter choice (1 or 2, default: 1)"
if ($modeChoice -eq "2") {
    $ScriptPath = "scripts\upload_data_to_railway.py"
    Write-Host "[INFO] Selected: Upload only mode" -ForegroundColor Green
} else {
    $ScriptPath = "scripts\run_cycle_and_upload_to_railway.py"
    Write-Host "[INFO] Selected: Full cycle + upload mode" -ForegroundColor Green
}

Write-Host ""
$daysInput = Read-Host "Run on weekdays only? (y/n, default: y)"
$weekdaysOnly = ($daysInput -ne "n")

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger
if ($weekdaysOnly) {
    # Weekdays only (Monday-Friday)
    # Use Weekly trigger with specific days instead of Daily
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $scheduleTime.ToString("HH:mm")
} else {
    # Every day
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
# Use RunLevel Limited to avoid permission issues, or Highest if user has admin rights
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Limited

# Register task
try {
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "[WARNING] Not running as administrator. Task registration may fail." -ForegroundColor Yellow
        Write-Host "To fix: Right-click PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
        Write-Host ""
    }
    
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Run AI-Trader trading cycle and upload data to Railway daily" | Out-Null
    
    Write-Host ""
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule:" -ForegroundColor Cyan
    Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
    Write-Host "  Days: $(if ($weekdaysOnly) { 'Weekdays (Mon-Fri)' } else { 'Every day' })" -ForegroundColor White
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To remove the task:" -ForegroundColor Cyan
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Cyan
    Write-Host "  python $ScriptPath" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Manual daily run" -ForegroundColor Yellow
    Write-Host "You can manually run the upload script daily:" -ForegroundColor White
    Write-Host "  python $ScriptPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or use the simplified script:" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\run_daily_upload.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

