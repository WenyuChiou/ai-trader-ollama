# Setup Long-Term Running System (Weeks/Months)
# This script sets up the system for continuous running with automatic maintenance
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\setup_long_term_running.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Long-Term Running Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Setup API Server (Task Scheduler)
Write-Host "[1] Setting up API Server (Task Scheduler)..." -ForegroundColor Yellow
$taskExists = Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
if ($taskExists) {
    Write-Host "  Task already exists, skipping..." -ForegroundColor Gray
} else {
    Write-Host "  Running setup script..." -ForegroundColor Gray
    & ".\scripts\start_api_task_scheduler.ps1"
}

# 2. Setup Daily Upload (Simple - once per day)
Write-Host ""
Write-Host "[2] Setting up daily upload task..." -ForegroundColor Yellow
$uploadTaskExists = Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Simple" -ErrorAction SilentlyContinue
if ($uploadTaskExists) {
    Write-Host "  Upload task already exists, skipping..." -ForegroundColor Gray
} else {
    Write-Host "  Running setup script..." -ForegroundColor Gray
    & ".\scripts\setup_daily_upload_simple.ps1"
}

# 3. Create maintenance script (weekly cleanup)
Write-Host ""
Write-Host "[3] Creating weekly maintenance task..." -ForegroundColor Yellow
$maintenanceScript = @"
# Weekly Maintenance Script
# Runs every Sunday at 2 AM to clean up old files

Write-Host "[Maintenance] Starting weekly cleanup..." -ForegroundColor Cyan

# Clean old backup files (keep last 7 days)
& ".\scripts\cleanup_repo.ps1"

# Clean old memory files (keep last 30 days)
python scripts\cleanup_old_memory.py

# Check disk space
`$dataSize = (Get-ChildItem -Path "data\logs" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "[Maintenance] Data directory size: `$([math]::Round(`$dataSize, 2)) GB" -ForegroundColor Yellow

if (`$dataSize -gt 5) {
    Write-Host "[Maintenance] WARNING: Data directory exceeds 5 GB. Consider archiving old data." -ForegroundColor Red
}

Write-Host "[Maintenance] Weekly maintenance completed!" -ForegroundColor Green
"@

$maintenancePath = "scripts\weekly_maintenance.ps1"
if (-not (Test-Path $maintenancePath)) {
    $maintenanceScript | Out-File -FilePath $maintenancePath -Encoding UTF8
    Write-Host "  Created: $maintenancePath" -ForegroundColor Green
} else {
    Write-Host "  Maintenance script already exists" -ForegroundColor Gray
}

# 4. Setup weekly maintenance task
Write-Host ""
Write-Host "[4] Setting up weekly maintenance task..." -ForegroundColor Yellow
$maintenanceTaskName = "AI-Trader-Weekly-Maintenance"
$maintenanceTaskExists = Get-ScheduledTask -TaskName $maintenanceTaskName -ErrorAction SilentlyContinue

if ($maintenanceTaskExists) {
    Write-Host "  Maintenance task already exists, skipping..." -ForegroundColor Gray
} else {
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$PSScriptRoot\weekly_maintenance.ps1`"" `
        -WorkingDirectory (Split-Path $PSScriptRoot -Parent)
    
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "02:00"
    
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)
    
    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Limited
    
    try {
        Register-ScheduledTask `
            -TaskName $maintenanceTaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Weekly maintenance for AI-Trader (cleanup old files, check disk space)" | Out-Null
        
        Write-Host "  Created weekly maintenance task (runs every Sunday at 2 AM)" -ForegroundColor Green
    } catch {
        Write-Host "  Failed to create maintenance task: $_" -ForegroundColor Red
        Write-Host "  You can manually run: powershell -ExecutionPolicy Bypass -File scripts\weekly_maintenance.ps1" -ForegroundColor Yellow
    }
}

# 5. Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ API Server: Task Scheduler configured" -ForegroundColor Green
Write-Host "✅ Daily Upload: Once per day (saves budget)" -ForegroundColor Green
Write-Host "✅ Weekly Maintenance: Automatic cleanup every Sunday at 2 AM" -ForegroundColor Green
Write-Host ""
Write-Host "System is ready for long-term running!" -ForegroundColor Green
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Cyan
Write-Host "  Check API status: Get-ScheduledTaskInfo -TaskName AITraderAPI" -ForegroundColor Gray
Write-Host "  View API logs: Get-Content logs\api_task.log -Tail 50" -ForegroundColor Gray
Write-Host "  Manual cleanup: powershell -ExecutionPolicy Bypass -File scripts\cleanup_repo.ps1" -ForegroundColor Gray
Write-Host ""

