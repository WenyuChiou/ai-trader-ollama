# 检查所有正在运行的服务
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查正在运行的服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  重要：检查关闭窗口是否会影响 API 运行" -ForegroundColor Yellow
Write-Host ""

# 0. 检查后台运行方式（Task Scheduler / Windows Service）
Write-Host "[0] 后台运行方式检查:" -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
$service = Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue

$backgroundRunning = $false
if ($task) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
    Write-Host "  ✅ 使用 Task Scheduler 运行" -ForegroundColor Green
    Write-Host "    任务状态: $($task.State)" -ForegroundColor Gray
    if ($taskInfo) {
        Write-Host "    最后运行时间: $($taskInfo.LastRunTime)" -ForegroundColor Gray
        Write-Host "    下次运行时间: $($taskInfo.NextRunTime)" -ForegroundColor Gray
    }
    Write-Host "    ✅ 关闭窗口: 不会停止（后台运行）" -ForegroundColor Green
    $backgroundRunning = $true
} else {
    Write-Host "  ⚠️  未使用 Task Scheduler" -ForegroundColor Yellow
}

if ($service) {
    Write-Host "  ✅ 使用 Windows Service 运行" -ForegroundColor Green
    Write-Host "    服务状态: $($service.Status)" -ForegroundColor Gray
    Write-Host "    ✅ 关闭窗口: 不会停止（后台运行）" -ForegroundColor Green
    $backgroundRunning = $true
} else {
    Write-Host "  ⚠️  未使用 Windows Service" -ForegroundColor Yellow
}

if (-not $backgroundRunning) {
    Write-Host ""
    Write-Host "  ⚠️  警告：当前可能是开发模式" -ForegroundColor Red
    Write-Host "     ❌ 关闭窗口可能会停止 API" -ForegroundColor Red
    Write-Host "     💡 建议：使用 Task Scheduler 设置后台运行" -ForegroundColor Yellow
    Write-Host "        运行: scripts\start_api_task_admin.bat" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "  ✅ 安全：可以关闭窗口，API 会继续运行" -ForegroundColor Green
}

Write-Host ""

# 1. 检查 uvicorn (后端 API 服务器)
Write-Host "[1] 后端 API 服务器 (uvicorn):" -ForegroundColor Yellow
$uvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*uvicorn*" -or $cmdLine -like "*server:app*"
    } catch {
        $false
    }
}

if ($uvicornProcesses) {
    Write-Host "  ✅ 找到 $($uvicornProcesses.Count) 个 uvicorn 进程:" -ForegroundColor Green
    foreach ($proc in $uvicornProcesses) {
        Write-Host "    - PID: $($proc.Id)" -ForegroundColor Gray
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "      命令: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))..." -ForegroundColor Gray
        } catch {
            Write-Host "      路径: $($proc.Path)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ℹ️  没有找到 uvicorn 进程" -ForegroundColor Gray
}

Write-Host ""

# 2. 检查 Python HTTP 服务器 (前端服务器)
Write-Host "[2] 前端服务器 (Python HTTP Server):" -ForegroundColor Yellow
$httpServerProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*http.server*" -or ($cmdLine -like "*3000*" -and $cmdLine -like "*python*")
    } catch {
        $false
    }
}

if ($httpServerProcesses) {
    Write-Host "  ✅ 找到 $($httpServerProcesses.Count) 个 HTTP 服务器进程:" -ForegroundColor Green
    foreach ($proc in $httpServerProcesses) {
        Write-Host "    - PID: $($proc.Id)" -ForegroundColor Gray
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "      命令: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))..." -ForegroundColor Gray
        } catch {
            Write-Host "      路径: $($proc.Path)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ℹ️  没有找到 HTTP 服务器进程" -ForegroundColor Gray
}

Write-Host ""

# 3. 检查所有 Python 进程
Write-Host "[3] 所有 Python 进程:" -ForegroundColor Yellow
$allPythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue

if ($allPythonProcesses) {
    Write-Host "  ✅ 找到 $($allPythonProcesses.Count) 个 Python 进程:" -ForegroundColor Green
    foreach ($proc in $allPythonProcesses) {
        Write-Host "    - PID: $($proc.Id)" -ForegroundColor Gray
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine) {
                $shortCmd = $cmdLine.Substring(0, [Math]::Min(100, $cmdLine.Length))
                Write-Host "      命令: $shortCmd..." -ForegroundColor Gray
            } else {
                Write-Host "      路径: $($proc.Path)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "      路径: $($proc.Path)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ℹ️  没有找到 Python 进程" -ForegroundColor Gray
}

Write-Host ""

# 4. 检查端口占用
Write-Host "[4] 端口占用情况:" -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "  ✅ 端口 8000 被占用 (后端 API)" -ForegroundColor Green
    $proc8000 = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
    if ($proc8000) {
        Write-Host "    进程: PID $($proc8000.Id) - $($proc8000.ProcessName)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ℹ️  端口 8000 未被占用" -ForegroundColor Gray
}

if ($port3000) {
    Write-Host "  ✅ 端口 3000 被占用 (前端服务器)" -ForegroundColor Green
    $proc3000 = Get-Process -Id $port3000.OwningProcess -ErrorAction SilentlyContinue
    if ($proc3000) {
        Write-Host "    进程: PID $($proc3000.Id) - $($proc3000.ProcessName)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ℹ️  端口 3000 未被占用" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

