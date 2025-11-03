# Setup all background services for AI-Trader (Windows)
# - Starts API in a background window
# - Schedules daily trading at specified time
# - Schedules hourly (or custom interval) real-time P&L/NAV updates
# Usage:
#   powershell -ExecutionPolicy Bypass -File setup_all.ps1 -DailyHour 9 -DailyMinute 0 -HourlyMinutes 60

param(
    [int]$DailyHour = 9,
    [int]$DailyMinute = 0,
    [int]$HourlyMinutes = 60
)

# Ensure we are in scripts directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "=== AI-Trader Setup (API + Daily + Hourly) ===" -ForegroundColor Cyan
Write-Host "Scripts Dir: $ScriptDir" -ForegroundColor Gray

# 1) Start API in background window
if (Test-Path "$ScriptDir/start_api_background.ps1") {
    Write-Host "[1/3] Starting API in background window..." -ForegroundColor Yellow
    try {
        powershell -ExecutionPolicy Bypass -File "$ScriptDir/start_api_background.ps1" | Out-Null
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "Failed to start API: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "start_api_background.ps1 not found." -ForegroundColor Red
}

# 2) Schedule daily trading
if (Test-Path "$ScriptDir/schedule_daily_task.ps1") {
    Write-Host "[2/3] Scheduling daily trading task at $DailyHour:$('{0:d2}' -f $DailyMinute)..." -ForegroundColor Yellow
    try {
        powershell -ExecutionPolicy Bypass -File "$ScriptDir/schedule_daily_task.ps1" -Hour $DailyHour -Minute $DailyMinute | Out-Null
    } catch {
        Write-Host "Failed to schedule daily task: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "schedule_daily_task.ps1 not found." -ForegroundColor Red
}

# 3) Schedule hourly (or custom) real-time updates
if (Test-Path "$ScriptDir/schedule_hourly_update.ps1") {
    Write-Host "[3/3] Scheduling real-time update every $HourlyMinutes minutes..." -ForegroundColor Yellow
    try {
        powershell -ExecutionPolicy Bypass -File "$ScriptDir/schedule_hourly_update.ps1" -Minutes $HourlyMinutes | Out-Null
    } catch {
        Write-Host "Failed to schedule hourly update: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "schedule_hourly_update.ps1 not found." -ForegroundColor Red
}

# Quick status lines
Write-Host ""; Write-Host "=== Quick Status ===" -ForegroundColor Cyan
try {
    powershell -ExecutionPolicy Bypass -File "$ScriptDir/check_api_status.ps1"
} catch { }

Write-Host ""; Write-Host "Scheduled Tasks (AI-Trader):" -ForegroundColor Gray
try {
    schtasks /Query /FO LIST /V | findstr /I "AI-Trader"
} catch { }

Write-Host ""; Write-Host "Setup complete. The API runs in background, daily trading at $DailyHour:$('{0:d2}' -f $DailyMinute), hourly updates every $HourlyMinutes minutes." -ForegroundColor Green


