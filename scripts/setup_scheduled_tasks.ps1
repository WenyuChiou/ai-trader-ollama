# Unified Scheduled Tasks Setup Script
# 统一的定时任务设置脚本
# Usage: powershell -ExecutionPolicy Bypass -File scripts\setup_scheduled_tasks.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Ollama - Scheduled Tasks Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"

# Get Python path
$PythonPath = (Get-Command python).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Python Path: $PythonPath" -ForegroundColor Gray
Write-Host ""

# Task configuration
Write-Host "Available Scheduled Tasks:" -ForegroundColor Yellow
Write-Host "  1. Auto Trading Cycle (自动交易周期)" -ForegroundColor White
Write-Host "  2. Equity Recording (净值记录 - 每30分钟)" -ForegroundColor White
Write-Host "  3. Data Update (数据更新 - 每小时)" -ForegroundColor White
Write-Host "  4. Daily Report Generation (每日报告生成)" -ForegroundColor White
Write-Host "  5. Setup All Tasks (设置所有任务)" -ForegroundColor Cyan
Write-Host "  0. Exit (退出)" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Select task to configure (0-5)"

# Function to create hourly task
function Create-HourlyTask {
    param(
        [string]$TaskName,
        [string]$ScriptPath,
        [string]$Description,
        [int]$IntervalMinutes = 60
    )
    
    $FullScriptPath = Join-Path $ProjectRoot $ScriptPath
    if (-not (Test-Path $FullScriptPath)) {
        Write-Host "[ERROR] Script not found: $FullScriptPath" -ForegroundColor Red
        return $false
    }
    
    $FullScriptPath = (Resolve-Path $FullScriptPath).Path
    $WorkingDirectory = Split-Path $FullScriptPath -Parent
    
    # Remove existing task
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "[INFO] Removing existing task: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create task action
    $Action = New-ScheduledTaskAction `
        -Execute $PythonPath `
        -Argument "`"$FullScriptPath`"" `
        -WorkingDirectory $WorkingDirectory
    
    # Create trigger (every N minutes)
    $NextRun = (Get-Date).AddMinutes($IntervalMinutes)
    $Trigger = New-ScheduledTaskTrigger -Once -At $NextRun
    $Trigger.Repetition = @{
        Interval = [TimeSpan]::FromMinutes($IntervalMinutes)
        Duration = [TimeSpan]::MaxValue
    }
    
    # Create settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable
    
    # Create principal
    $Principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Principal $Principal `
            -Description $Description | Out-Null
        
        Write-Host "[SUCCESS] Task '$TaskName' created successfully!" -ForegroundColor Green
        Write-Host "  Schedule: Every $IntervalMinutes minutes" -ForegroundColor Gray
        Write-Host "  Script: $FullScriptPath" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host "[ERROR] Failed to create task: $_" -ForegroundColor Red
        return $false
    }
}

# Function to create daily task
function Create-DailyTask {
    param(
        [string]$TaskName,
        [string]$ScriptPath,
        [string]$Description,
        [string]$Time = "09:00",
        [switch]$WeekdaysOnly
    )
    
    $FullScriptPath = Join-Path $ProjectRoot $ScriptPath
    if (-not (Test-Path $FullScriptPath)) {
        Write-Host "[ERROR] Script not found: $FullScriptPath" -ForegroundColor Red
        return $false
    }
    
    $FullScriptPath = (Resolve-Path $FullScriptPath).Path
    $WorkingDirectory = Split-Path $FullScriptPath -Parent
    
    # Remove existing task
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "[INFO] Removing existing task: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create task action
    $Action = New-ScheduledTaskAction `
        -Execute $PythonPath `
        -Argument "`"$FullScriptPath`"" `
        -WorkingDirectory $WorkingDirectory
    
    # Create trigger
    $Trigger = New-ScheduledTaskTrigger -Daily -At $Time
    if ($WeekdaysOnly) {
        $Trigger.DaysOfWeek = [System.DayOfWeek]::Monday, [System.DayOfWeek]::Tuesday, [System.DayOfWeek]::Wednesday, [System.DayOfWeek]::Thursday, [System.DayOfWeek]::Friday
    }
    
    # Create settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable
    
    # Create principal
    $Principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Principal $Principal `
            -Description $Description | Out-Null
        
        Write-Host "[SUCCESS] Task '$TaskName' created successfully!" -ForegroundColor Green
        Write-Host "  Schedule: Daily at $Time" -ForegroundColor Gray
        if ($WeekdaysOnly) {
            Write-Host "  Days: Weekdays only (Mon-Fri)" -ForegroundColor Gray
        }
        Write-Host "  Script: $FullScriptPath" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host "[ERROR] Failed to create task: $_" -ForegroundColor Red
        return $false
    }
}

# Function to create API call task (using curl/PowerShell)
function Create-APICallTask {
    param(
        [string]$TaskName,
        [string]$APIEndpoint,
        [string]$Description,
        [int]$IntervalMinutes = 30
    )
    
    # Create PowerShell script to call API
    $ScriptContent = @"
# Auto-generated script for $TaskName
`$apiUrl = "http://localhost:8000$APIEndpoint"
try {
    `$response = Invoke-RestMethod -Uri `$apiUrl -Method POST -ContentType "application/json" -TimeoutSec 10
    Write-Host "[$TaskName] Success: `$response"
} catch {
    Write-Host "[$TaskName] Error: `$_"
}
"@
    
    $ScriptPath = Join-Path $ProjectRoot "scripts" "temp_$TaskName.ps1"
    $ScriptContent | Out-File -FilePath $ScriptPath -Encoding UTF8
    
    # Create task using PowerShell script
    $WorkingDirectory = Split-Path $ScriptPath -Parent
    
    # Remove existing task
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "[INFO] Removing existing task: $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create task action
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" `
        -WorkingDirectory $WorkingDirectory
    
    # Create trigger
    $NextRun = (Get-Date).AddMinutes($IntervalMinutes)
    $Trigger = New-ScheduledTaskTrigger -Once -At $NextRun
    $Trigger.Repetition = @{
        Interval = [TimeSpan]::FromMinutes($IntervalMinutes)
        Duration = [TimeSpan]::MaxValue
    }
    
    # Create settings
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable
    
    # Create principal
    $Principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Principal $Principal `
            -Description $Description | Out-Null
        
        Write-Host "[SUCCESS] Task '$TaskName' created successfully!" -ForegroundColor Green
        Write-Host "  Schedule: Every $IntervalMinutes minutes" -ForegroundColor Gray
        Write-Host "  API Endpoint: $APIEndpoint" -ForegroundColor Gray
        return $true
    } catch {
        Write-Host "[ERROR] Failed to create task: $_" -ForegroundColor Red
        return $false
    }
}

# Handle user choice
switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Setting up Auto Trading Cycle..." -ForegroundColor Yellow
        Write-Host ""
        $time = Read-Host "Enter trading time (HH:MM, default: 09:30)"
        if ([string]::IsNullOrWhiteSpace($time)) { $time = "09:30" }
        
        $weekdaysOnly = Read-Host "Weekdays only? (Y/N, default: Y)"
        if ([string]::IsNullOrWhiteSpace($weekdaysOnly)) { $weekdaysOnly = "Y" }
        
        $result = Create-DailyTask `
            -TaskName "AITrader-AutoTrading" `
            -ScriptPath "backend\scripts\run_daily_trading.py" `
            -Description "AI Trader - Automatic Trading Cycle" `
            -Time $time `
            -WeekdaysOnly:($weekdaysOnly -eq "Y")
        
        if ($result) {
            Write-Host ""
            Write-Host "To test: Start-ScheduledTask -TaskName 'AITrader-AutoTrading'" -ForegroundColor Cyan
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "Setting up Equity Recording (every 30 minutes)..." -ForegroundColor Yellow
        Write-Host ""
        
        # Create Python script for equity recording
        $ScriptContent = @"
# Auto-generated equity recording script
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import requests
import json
from datetime import datetime

try:
    # Get current portfolio
    response = requests.get("http://localhost:8000/api/portfolio/real-time", timeout=10)
    if response.status_code == 200:
        portfolio = response.json()
        if portfolio.get("ok"):
            # Record equity
            equity_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat() + "Z",
                "cash": portfolio.get("cash", 0),
                "equity_value": portfolio.get("equity_value", 0),
                "total_value": portfolio.get("total_value", 0),
                "total_pnl": portfolio.get("total_pnl", 0),
                "total_pnl_pct": portfolio.get("total_pnl_pct", 0),
                "positions_detail": portfolio.get("positions_detail", {})
            }
            
            record_response = requests.post(
                "http://localhost:8000/api/portfolio/record-equity",
                json=equity_data,
                timeout=10
            )
            
            if record_response.status_code == 200:
                print(f"[EQUITY RECORD] Successfully recorded: ${equity_data['total_value']:.2f}")
            else:
                print(f"[EQUITY RECORD] Failed: {record_response.status_code}")
        else:
            print(f"[EQUITY RECORD] API returned error: {portfolio.get('error', 'Unknown')}")
    else:
        print(f"[EQUITY RECORD] API unavailable: {response.status_code}")
except Exception as e:
    print(f"[EQUITY RECORD] Error: {e}")
"@
        
        $ScriptPath = Join-Path $ProjectRoot "scripts" "record_equity_auto.py"
        $ScriptContent | Out-File -FilePath $ScriptPath -Encoding UTF8
        
        $result = Create-HourlyTask `
            -TaskName "AITrader-EquityRecording" `
            -ScriptPath "scripts\record_equity_auto.py" `
            -Description "AI Trader - Automatic Equity Recording (every 30 minutes)" `
            -IntervalMinutes 30
        
        if ($result) {
            Write-Host ""
            Write-Host "To test: Start-ScheduledTask -TaskName 'AITrader-EquityRecording'" -ForegroundColor Cyan
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "Setting up Data Update (every hour)..." -ForegroundColor Yellow
        Write-Host ""
        
        $result = Create-HourlyTask `
            -TaskName "AITrader-DataUpdate" `
            -ScriptPath "scripts\update_real_time_pnl.py" `
            -Description "AI Trader - Automatic Data Update (every hour)" `
            -IntervalMinutes 60
        
        if ($result) {
            Write-Host ""
            Write-Host "To test: Start-ScheduledTask -TaskName 'AITrader-DataUpdate'" -ForegroundColor Cyan
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "Setting up Daily Report Generation..." -ForegroundColor Yellow
        Write-Host ""
        $time = Read-Host "Enter report generation time (HH:MM, default: 18:00)"
        if ([string]::IsNullOrWhiteSpace($time)) { $time = "18:00" }
        
        $result = Create-DailyTask `
            -TaskName "AITrader-DailyReport" `
            -ScriptPath "backend\scripts\generate_daily_report.py" `
            -Description "AI Trader - Daily Report Generation" `
            -Time $time `
            -WeekdaysOnly
        
        if ($result) {
            Write-Host ""
            Write-Host "To test: Start-ScheduledTask -TaskName 'AITrader-DailyReport'" -ForegroundColor Cyan
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "Setting up ALL scheduled tasks..." -ForegroundColor Yellow
        Write-Host ""
        
        $results = @()
        
        # 1. Auto Trading (9:30 AM weekdays)
        Write-Host "[1/4] Setting up Auto Trading..." -ForegroundColor Gray
        $results += Create-DailyTask `
            -TaskName "AITrader-AutoTrading" `
            -ScriptPath "backend\scripts\run_daily_trading.py" `
            -Description "AI Trader - Automatic Trading Cycle" `
            -Time "09:30" `
            -WeekdaysOnly
        
        # 2. Equity Recording (every 30 minutes)
        Write-Host "[2/4] Setting up Equity Recording..." -ForegroundColor Gray
        $ScriptContent = @"
# Auto-generated equity recording script
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import requests
import json
from datetime import datetime

try:
    response = requests.get("http://localhost:8000/api/portfolio/real-time", timeout=10)
    if response.status_code == 200:
        portfolio = response.json()
        if portfolio.get("ok"):
            equity_data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now().isoformat() + "Z",
                "cash": portfolio.get("cash", 0),
                "equity_value": portfolio.get("equity_value", 0),
                "total_value": portfolio.get("total_value", 0),
                "total_pnl": portfolio.get("total_pnl", 0),
                "total_pnl_pct": portfolio.get("total_pnl_pct", 0),
                "positions_detail": portfolio.get("positions_detail", {})
            }
            
            record_response = requests.post(
                "http://localhost:8000/api/portfolio/record-equity",
                json=equity_data,
                timeout=10
            )
            
            if record_response.status_code == 200:
                print(f"[EQUITY RECORD] Success: ${equity_data['total_value']:.2f}")
            else:
                print(f"[EQUITY RECORD] Failed: {record_response.status_code}")
        else:
            print(f"[EQUITY RECORD] API error: {portfolio.get('error', 'Unknown')}")
    else:
        print(f"[EQUITY RECORD] API unavailable: {response.status_code}")
except Exception as e:
    print(f"[EQUITY RECORD] Error: {e}")
"@
        $ScriptPath = Join-Path $ProjectRoot "scripts" "record_equity_auto.py"
        $ScriptContent | Out-File -FilePath $ScriptPath -Encoding UTF8
        
        $results += Create-HourlyTask `
            -TaskName "AITrader-EquityRecording" `
            -ScriptPath "scripts\record_equity_auto.py" `
            -Description "AI Trader - Automatic Equity Recording (every 30 minutes)" `
            -IntervalMinutes 30
        
        # 3. Data Update (every hour)
        Write-Host "[3/4] Setting up Data Update..." -ForegroundColor Gray
        $results += Create-HourlyTask `
            -TaskName "AITrader-DataUpdate" `
            -ScriptPath "scripts\update_real_time_pnl.py" `
            -Description "AI Trader - Automatic Data Update (every hour)" `
            -IntervalMinutes 60
        
        # 4. Daily Report (6:00 PM weekdays)
        Write-Host "[4/4] Setting up Daily Report..." -ForegroundColor Gray
        $results += Create-DailyTask `
            -TaskName "AITrader-DailyReport" `
            -ScriptPath "backend\scripts\generate_daily_report.py" `
            -Description "AI Trader - Daily Report Generation" `
            -Time "18:00" `
            -WeekdaysOnly
        
        Write-Host ""
        Write-Host "================================================" -ForegroundColor Green
        Write-Host "  Setup Complete!" -ForegroundColor Green
        Write-Host "================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Created Tasks:" -ForegroundColor Cyan
        Write-Host "  ✅ AITrader-AutoTrading (Daily at 09:30, weekdays)" -ForegroundColor Green
        Write-Host "  ✅ AITrader-EquityRecording (Every 30 minutes)" -ForegroundColor Green
        Write-Host "  ✅ AITrader-DataUpdate (Every hour)" -ForegroundColor Green
        Write-Host "  ✅ AITrader-DailyReport (Daily at 18:00, weekdays)" -ForegroundColor Green
        Write-Host ""
        Write-Host "To view all tasks:" -ForegroundColor Yellow
        Write-Host "  Get-ScheduledTask | Where-Object { `$_.TaskName -like 'AITrader-*' }" -ForegroundColor White
        Write-Host ""
        Write-Host "To test a task:" -ForegroundColor Yellow
        Write-Host "  Start-ScheduledTask -TaskName 'AITrader-AutoTrading'" -ForegroundColor White
        Write-Host ""
        Write-Host "To remove a task:" -ForegroundColor Yellow
        Write-Host "  Unregister-ScheduledTask -TaskName 'AITrader-AutoTrading' -Confirm:`$false" -ForegroundColor White
    }
    
    "0" {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Read-Host "Press Enter to exit"

