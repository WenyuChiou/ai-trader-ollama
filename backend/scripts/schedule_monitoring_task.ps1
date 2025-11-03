# Windows 定时任务设置脚本（监控和优化）
# 用于每日收盘后（16:30）自动执行监控和优化报告

$TaskName = "AITraderMonitoring"
$ScriptPath = Join-Path $PSScriptRoot "run_monitoring_and_optimization.py"
$FullScriptPath = (Resolve-Path $ScriptPath).Path
$PythonPath = (Get-Command python).Source
$WorkingDirectory = Split-Path $FullScriptPath -Parent

Write-Host "================================================"
Write-Host "  AI Trader - Monitoring Task Setup"
Write-Host "================================================"
Write-Host ""
Write-Host "Task Name: $TaskName"
Write-Host "Script Path: $FullScriptPath"
Write-Host "Python Path: $PythonPath"
Write-Host "Working Directory: $WorkingDirectory"
Write-Host "Schedule: Daily at 4:30 PM"
Write-Host ""

# 检查脚本是否存在
if (-not (Test-Path $FullScriptPath)) {
    Write-Host "ERROR: Script not found at $FullScriptPath" -ForegroundColor Red
    exit 1
}

# 删除旧任务（如果存在）
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 创建定时任务
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$FullScriptPath`"" `
    -WorkingDirectory $WorkingDirectory

# 每日下午 4:30 触发
$Trigger = New-ScheduledTaskTrigger -Daily -At 4:30PM

# 任务设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# 运行权限
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# 注册任务
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "AI Trader - Daily Monitoring & Optimization (Runs at 4:30 PM)" `
        -ErrorAction Stop
    
    Write-Host "SUCCESS: Task registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:"
    Write-Host "  - Name: $TaskName"
    Write-Host "  - Schedule: Daily at 4:30 PM"
    Write-Host "  - Script: $FullScriptPath"
    Write-Host ""
    Write-Host "You can view/edit it in Task Scheduler:" -ForegroundColor Cyan
    Write-Host "  taskschd.msc" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To test the task manually:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor Yellow
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to register task: $_" -ForegroundColor Red
    exit 1
}

