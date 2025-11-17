# Windows PowerShell: Setup Daily Upload Only (Simple Version)
# This script sets up a daily task to upload data to Railway ONCE per day
# Usage: powershell -ExecutionPolicy Bypass -File scripts\setup_daily_upload_simple.ps1
# IMPORTANT: Run as Administrator!

$TaskName = "AI-Trader-Daily-Upload-Simple"
$ScriptPath = "scripts\daily_upload_only.ps1"
$WorkingDir = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Daily Upload Setup (Simple)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will create a scheduled task to:" -ForegroundColor Yellow
Write-Host "  ✅ Upload local data to Railway ONCE per day" -ForegroundColor Green
Write-Host "  ❌ NOT update GitHub Pages (to save budget)" -ForegroundColor Yellow
Write-Host "  ❌ NOT run trading cycles" -ForegroundColor Yellow
Write-Host ""
Write-Host "Task Name: $TaskName" -ForegroundColor Green
Write-Host "Script: $ScriptPath" -ForegroundColor Green
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and recreate it? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[INFO] Removed existing task" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Keeping existing task" -ForegroundColor Green
        Write-Host ""
        Write-Host "Current task schedule:" -ForegroundColor Cyan
        Get-ScheduledTask -TaskName $TaskName | Format-List
        exit 0
    }
}

# Get schedule time (default: 18:00, after market close)
Write-Host "Schedule Configuration:" -ForegroundColor Cyan
$timeInput = Read-Host "Enter time (HH:MM format, e.g., 18:00 for 6 PM, default: 18:00)"
if ([string]::IsNullOrWhiteSpace($timeInput)) {
    $timeInput = "18:00"
}

try {
    $scheduleTime = [DateTime]::ParseExact($timeInput, "HH:mm", $null)
} catch {
    Write-Host "[WARN] Invalid time format. Using default: 18:00" -ForegroundColor Yellow
    $timeInput = "18:00"
    $scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
}

Write-Host ""
$daysInput = Read-Host "Run every day? (y/n, default: y)"
$everyDay = ($daysInput -ne "n" -and $daysInput -ne "N")

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger (daily at specified time)
if ($everyDay) {
    $Trigger = New-ScheduledTaskTrigger -Daily -At $scheduleTime.ToString("HH:mm")
    $scheduleDesc = "Every day at $($scheduleTime.ToString('HH:mm'))"
} else {
    # Weekdays only (Monday-Friday)
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $scheduleTime.ToString("HH:mm")
    $scheduleDesc = "Weekdays (Mon-Fri) at $($scheduleTime.ToString('HH:mm'))"
}

# Create settings - IMPORTANT: Prevent multiple instances
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `  # CRITICAL: Ignore new instances if task is already running
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `  # Max 1 hour execution time
    -RestartCount 0  # Don't restart on failure (to prevent budget issues)

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
        -Description "Upload AI-Trader data to Railway daily (ONCE per day, no GitHub Pages update)" | Out-Null
    
    Write-Host ""
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule Details:" -ForegroundColor Cyan
    Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
    Write-Host "  Frequency: $scheduleDesc" -ForegroundColor White
    Write-Host "  Mode: Upload data to Railway ONLY (no GitHub Pages update)" -ForegroundColor White
    Write-Host "  Multiple Instances: Ignored (prevents duplicate runs)" -ForegroundColor White
    Write-Host ""
    Write-Host "Task Management:" -ForegroundColor Cyan
    Write-Host "  View task: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Run now: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Stop: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
    Write-Host "  Remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test manually:" -ForegroundColor Cyan
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\daily_upload_only.ps1" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Manual daily run" -ForegroundColor Yellow
    Write-Host "You can manually run the upload script daily:" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\daily_upload_only.ps1" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Read-Host "Press Enter to exit"
