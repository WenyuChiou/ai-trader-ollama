# Setup Daily Backup Scheduled Task
# Usage (Recommended): Right-click setup_daily_backup_admin.bat and select "Run as administrator"
# Usage (Manual): powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_backup.ps1

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Daily Backup Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires administrator privileges." -ForegroundColor Yellow
    Write-Host "   Please right-click and select 'Run as administrator'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Get project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonScript = Join-Path $projectRoot "backend\scripts\daily_backup.py"

# Check if Python script exists
if (-not (Test-Path $pythonScript)) {
    Write-Host "❌ Error: Backup script not found: $pythonScript" -ForegroundColor Red
    exit 1
}

# Get Python executable
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "❌ Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "   Please install Python 3.10+ and add it to PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "Project root: $projectRoot" -ForegroundColor Green
Write-Host "Python script: $pythonScript" -ForegroundColor Green
Write-Host "Python executable: $pythonExe" -ForegroundColor Green
Write-Host ""

# Ask for backup time
Write-Host "Enter backup time (HH:MM format, default: 23:00):" -ForegroundColor Cyan
$backupTimeInput = Read-Host "Backup time"
if ([string]::IsNullOrWhiteSpace($backupTimeInput)) {
    $backupTime = "23:00"
} else {
    $backupTime = $backupTimeInput
}

Write-Host ""
Write-Host "Creating scheduled task..." -ForegroundColor Cyan

# Create scheduled task action
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$pythonScript`"" -WorkingDirectory $projectRoot

# Create scheduled task trigger (daily at specified time)
$trigger = New-ScheduledTaskTrigger -Daily -At $backupTime

# Create scheduled task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create scheduled task principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register scheduled task
$taskName = "AITrader-DailyBackup"
try {
    # Remove existing task if exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    }
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Daily backup of AI Trader critical data files" | Out-Null
    
    Write-Host ""
    Write-Host "✅ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host "   Task name: $taskName" -ForegroundColor Cyan
    Write-Host "   Schedule: Daily at $backupTime" -ForegroundColor Cyan
    Write-Host ""
    
    # Test run option
    Write-Host "Would you like to test the backup now? (Y/N):" -ForegroundColor Cyan
    $testRun = Read-Host
    if ($testRun -eq "Y" -or $testRun -eq "y") {
        Write-Host ""
        Write-Host "Running backup test..." -ForegroundColor Cyan
        & $pythonExe $pythonScript
        Write-Host ""
        Write-Host "✅ Backup test completed!" -ForegroundColor Green
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To manage the scheduled task:" -ForegroundColor Cyan
Write-Host "  View: Get-ScheduledTask -TaskName $taskName" -ForegroundColor Yellow
Write-Host "  Run: Start-ScheduledTask -TaskName $taskName" -ForegroundColor Yellow
Write-Host "  Remove: Unregister-ScheduledTask -TaskName $taskName -Confirm:`$false" -ForegroundColor Yellow
Write-Host ""


Read-Host "Press Enter to exit"

