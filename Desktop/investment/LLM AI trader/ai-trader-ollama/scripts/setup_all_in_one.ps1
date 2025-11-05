# Unified setup for AI-Trader (Backend + Frontend) on Windows
# - Installs Python deps (if needed)
# - Starts FastAPI backend in a new window
# - Serves frontend/monitor.html via Python HTTP server in a new window
# - Optionally schedules daily trading and hourly updates
# - Verifies API and opens the dashboard in default browser
# Usage examples:
#   powershell -ExecutionPolicy Bypass -File setup_all_in_one.ps1
#   powershell -ExecutionPolicy Bypass -File setup_all_in_one.ps1 -DailyHour 9 -DailyMinute 0 -HourlyMinutes 60 -CreateSchedules

param(
    [int]$DailyHour = 9,
    [int]$DailyMinute = 0,
    [int]$HourlyMinutes = 60,
    [switch]$CreateSchedules
)

# Encoding safety
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
try { chcp 65001 | Out-Null } catch { }

# Resolve important paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Resolve-Path (Join-Path $ScriptDir "..")
$ProjectRoot = Resolve-Path (Join-Path $BackendDir "..")
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendReq = Join-Path $BackendDir "requirements.txt"

Write-Host "=== AI-Trader Unified Setup ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Backend Dir : $BackendDir" -ForegroundColor Gray
Write-Host "Frontend Dir: $FrontendDir" -ForegroundColor Gray

function Ensure-PythonDeps {
    if (Test-Path $BackendReq) {
        Write-Host "[Deps] Installing backend requirements..." -ForegroundColor Yellow
        try {
            Push-Location $BackendDir
            python -m pip install --upgrade pip | Out-Null
            python -m pip install -r requirements.txt
        } catch {
            Write-Host "Failed to install backend requirements: $($_.Exception.Message)" -ForegroundColor Red
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[Deps] requirements.txt not found at $BackendReq (skipping)" -ForegroundColor DarkYellow
    }
}

function Start-Backend {
    Write-Host "[Backend] Starting FastAPI (port 8000) in a new window..." -ForegroundColor Yellow
    $cmd = "cd `"$BackendDir`"; python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload"
    Start-Process powershell -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-Command', $cmd) | Out-Null
}

function Start-Frontend {
    if (-not (Test-Path $FrontendDir)) {
        Write-Host "[Frontend] Directory not found: $FrontendDir" -ForegroundColor Red
        return
    }
    Write-Host "[Frontend] Serving monitor.html (port 8080) in a new window..." -ForegroundColor Yellow
    $cmd = "cd `"$FrontendDir`"; python -m http.server 8080"
    Start-Process powershell -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-Command', $cmd) | Out-Null
}

function Test-API {
    Write-Host "[Verify] Checking API status..." -ForegroundColor Cyan
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/system/info" -UseBasicParsing -TimeoutSec 5
        $sw.Stop()
        Write-Host ("[Verify] /api/system/info {0} in {1} ms" -f $resp.StatusCode, $sw.ElapsedMilliseconds) -ForegroundColor Green
    } catch {
        Write-Host "[Verify] API not reachable yet: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Open-Dashboard {
    $url = "http://127.0.0.1:8080/monitor.html"
    Write-Host "[Open] Opening dashboard: $url" -ForegroundColor Cyan
    try { Start-Process $url | Out-Null } catch { }
}

function Create-Schedules {
    $minuteStr = ("{0:D2}" -f $DailyMinute)
    Write-Host "[Schedule] Daily trading at $($DailyHour):$minuteStr and hourly every $HourlyMinutes min" -ForegroundColor Yellow
    $dailyScript = Join-Path $ScriptDir "schedule_daily_task.ps1"
    $hourlyScript = Join-Path $ScriptDir "schedule_hourly_update.ps1"

    if (Test-Path $dailyScript) {
        try {
            powershell -ExecutionPolicy Bypass -File $dailyScript -Hour $DailyHour -Minute $DailyMinute | Out-Null
            Write-Host "[Schedule] Daily trading task created." -ForegroundColor Green
        } catch {
            Write-Host "[Schedule] Failed to create daily task: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "[Schedule] daily script not found: $dailyScript" -ForegroundColor DarkYellow
    }

    if (Test-Path $hourlyScript) {
        try {
            powershell -ExecutionPolicy Bypass -File $hourlyScript -Minutes $HourlyMinutes | Out-Null
            Write-Host "[Schedule] Hourly update task created." -ForegroundColor Green
        } catch {
            Write-Host "[Schedule] Failed to create hourly task: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "[Schedule] hourly script not found: $hourlyScript" -ForegroundColor DarkYellow
    }
}

# Run steps
Ensure-PythonDeps
Start-Backend
Start-Frontend

# Give services a brief moment to start
Start-Sleep -Seconds 2
Test-API
Open-Dashboard

if ($CreateSchedules) {
    Create-Schedules
}

Write-Host ""; Write-Host ("All set. Backend on :8000, dashboard on :8080. Daily at {0}:{1}, hourly every {2} min (if scheduled)." -f $DailyHour, ("{0:D2}" -f $DailyMinute), $HourlyMinutes) -ForegroundColor Green
