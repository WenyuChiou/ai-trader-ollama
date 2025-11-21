# Quick check: Is it safe to close the window?
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Window Close Safety Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$task = Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
$service = Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue

$isSafe = $false
$method = ""

if ($task) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
    $isSafe = $true
    $method = "Task Scheduler"
    Write-Host "OK: Using Task Scheduler" -ForegroundColor Green
    Write-Host "   State: $($task.State)" -ForegroundColor Gray
    if ($taskInfo) {
        Write-Host "   Last Run: $($taskInfo.LastRunTime)" -ForegroundColor Gray
    }
} elseif ($service) {
    $isSafe = $true
    $method = "Windows Service"
    Write-Host "OK: Using Windows Service" -ForegroundColor Green
    Write-Host "   Status: $($service.Status)" -ForegroundColor Gray
} else {
    $isSafe = $false
    $method = "Development Mode (likely)"
    Write-Host "WARNING: No background running method detected" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($isSafe) {
    Write-Host "SAFE: You can close the window" -ForegroundColor Green
    Write-Host "   Running Method: $method" -ForegroundColor Gray
    Write-Host "   API will continue running in background" -ForegroundColor Gray
} else {
    Write-Host "UNSAFE: Closing window may stop API" -ForegroundColor Red
    Write-Host "   Current Method: $method" -ForegroundColor Gray
    Write-Host ""
    Write-Host "TIP: Setup background running" -ForegroundColor Yellow
    Write-Host "   Run: scripts\start_api_task_admin.bat" -ForegroundColor Cyan
    Write-Host "   (Requires administrator privileges)" -ForegroundColor Gray
}
Write-Host "========================================" -ForegroundColor Cyan
