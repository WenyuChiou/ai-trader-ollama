# Windows PowerShell 脚本：设置每小时更新实时损益任务
# 使用方法: powershell -ExecutionPolicy Bypass -File scripts\schedule_hourly_update.ps1

$TaskName = "AITraderHourlyPnlUpdate"
$ScriptPath = Join-Path $PSScriptRoot "update_real_time_pnl.py"
$FullScriptPath = (Resolve-Path $ScriptPath).Path
$PythonPath = (Get-Command python).Source
$WorkingDirectory = Split-Path $FullScriptPath -Parent

Write-Host "================================================"
Write-Host "  AI Trader - Hourly P&L Update Task Setup"
Write-Host "================================================"
Write-Host ""
Write-Host "Task Name: $TaskName"
Write-Host "Script Path: $FullScriptPath"
Write-Host "Python Path: $PythonPath"
Write-Host "Working Directory: $WorkingDirectory"
Write-Host "Schedule: Every hour"
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

# 每小时触发（从整点开始，重复每小时）
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours((Get-Date).Hour + 1)
$Trigger.Repetition = @{
    Interval = [TimeSpan]::FromHours(1)
    Duration = [TimeSpan]::MaxValue
}

# 任务设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

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
        -Description "AI Trader - Hourly Real-Time P&L and NAV Update" `
        -ErrorAction Stop
    
    Write-Host "SUCCESS: Task registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:"
    Write-Host "  - Name: $TaskName"
    Write-Host "  - Schedule: Every hour"
    Write-Host "  - Script: $FullScriptPath"
    Write-Host ""
    Write-Host "To test the task manually:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor Yellow
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to register task: $_" -ForegroundColor Red
    exit 1
}

