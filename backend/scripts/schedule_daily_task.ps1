# Windows PowerShell 脚本：设置每日自动交易任务
# 使用方法: powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_task.ps1

$TaskName = "AI-Trader-Daily-Trading"
$ScriptPath = "scripts\run_daily_trading.py"
$WorkingDir = $PSScriptRoot  # scripts/ -> backend/

# 获取 Python 路径
$PythonPath = (Get-Command python).Path
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Python path: $PythonPath" -ForegroundColor Green
Write-Host "[INFO] Working directory: $WorkingDir" -ForegroundColor Green
Write-Host "[INFO] Script path: $ScriptPath" -ForegroundColor Green

# 检查任务是否已存在
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

# 创建任务操作
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument $ScriptPath -WorkingDirectory $WorkingDir

# 创建触发器（每个工作日早上 9:00）
$Trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
# 设置为只在工作日运行（周一到周五）
$Trigger.DaysOfWeek = [System.DayOfWeek]::Monday, [System.DayOfWeek]::Tuesday, [System.DayOfWeek]::Wednesday, [System.DayOfWeek]::Thursday, [System.DayOfWeek]::Friday

# 创建设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# 注册任务
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Run AI-Trader daily trading cycle" | Out-Null
    Write-Host "[SUCCESS] Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "[INFO] Task will run every weekday at 9:00 AM" -ForegroundColor Cyan
    
    # 显示任务信息
    Write-Host "`n[INFO] Task details:" -ForegroundColor Cyan
    Get-ScheduledTask -TaskName $TaskName | Format-List
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[INFO] To test the task, run:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "`n[INFO] To remove the task, run:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor White

