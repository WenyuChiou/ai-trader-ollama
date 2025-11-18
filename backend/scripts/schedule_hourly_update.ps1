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

# 使用schtasks命令创建每小时重复任务（更可靠的方法）
$NextHour = (Get-Date).Date.AddHours((Get-Date).Hour + 1)
$StartTime = $NextHour.ToString("HH:mm")

# 删除旧任务（如果存在）
$ExistingTask = schtasks /Query /TN $TaskName 2>$null
if ($ExistingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F | Out-Null
}

# 使用schtasks创建每小时重复任务
# 注意：schtasks需要正确的参数格式
$EscapedScriptPath = $FullScriptPath -replace '"', '""'
$Command = "schtasks /Create /TN `"$TaskName`" /TR `"`"$PythonPath`" `"`"$EscapedScriptPath`"`"`" /SC HOURLY /MO 1 /ST $StartTime /F /RL HIGHEST"
Write-Host "Creating task..." -ForegroundColor Gray

try {
    $Result = cmd /c $Command 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Task registered successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Task Details:"
        Write-Host "  - Name: $TaskName"
        Write-Host "  - Schedule: Every hour starting at $StartTime"
        Write-Host "  - Script: $FullScriptPath"
        Write-Host ""
        Write-Host "To test the task manually:" -ForegroundColor Cyan
        Write-Host "  schtasks /Run /TN `"$TaskName`"" -ForegroundColor Yellow
        Write-Host ""
    } else {
        throw "schtasks command failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "ERROR: Failed to register task: $_" -ForegroundColor Red
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    
    # 备用方法：使用PowerShell cmdlets（不带重复）
    $Trigger = New-ScheduledTaskTrigger -Once -At $NextHour
    $Settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable
    $Principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest
    
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "AI Trader - Hourly Real-Time P&L and NAV Update" | Out-Null
    
    Write-Host "Task created (without repetition - will need manual setup in Task Scheduler)" -ForegroundColor Yellow
    Write-Host "Please manually configure repetition in Task Scheduler GUI" -ForegroundColor Yellow
}

