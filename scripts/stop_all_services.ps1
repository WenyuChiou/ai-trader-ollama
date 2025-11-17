# 停止所有 AI Trader 相关服务
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "停止所有 AI Trader 服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 查找并停止 uvicorn 进程（后端 API 服务器）
Write-Host "[1] 查找 uvicorn 进程（后端 API 服务器）..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -and 
    ($_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*server:app*" -or $_.Path -like "*python*")
} | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*uvicorn*" -or $cmdLine -like "*server:app*"
    } catch {
        $false
    }
}

if ($uvicornProcesses) {
    Write-Host "  找到 $($uvicornProcesses.Count) 个 uvicorn 进程" -ForegroundColor Green
    foreach ($proc in $uvicornProcesses) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "  - PID: $($proc.Id) | $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    ✅ 已停止" -ForegroundColor Green
        } catch {
            Write-Host "    ⚠️  停止失败: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ℹ️  未找到 uvicorn 进程" -ForegroundColor Gray
}

Write-Host ""

# 查找并停止 Python HTTP 服务器（前端服务器）
Write-Host "[2] 查找 Python HTTP 服务器（前端服务器）..." -ForegroundColor Yellow
$httpServerProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*"
} | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*http.server*" -or $cmdLine -like "*SimpleHTTPServer*"
    } catch {
        $false
    }
}

if ($httpServerProcesses) {
    Write-Host "  找到 $($httpServerProcesses.Count) 个 HTTP 服务器进程" -ForegroundColor Green
    foreach ($proc in $httpServerProcesses) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "  - PID: $($proc.Id) | $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    ✅ 已停止" -ForegroundColor Green
        } catch {
            Write-Host "    ⚠️  停止失败: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ℹ️  未找到 HTTP 服务器进程" -ForegroundColor Gray
}

Write-Host ""

# 查找并停止所有 Python 进程（更激进的方法）
Write-Host "[3] 查找所有 Python 进程..." -ForegroundColor Yellow
$allPythonProcesses = Get-Process | Where-Object { 
    $_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw" -or $_.ProcessName -like "python*"
}

if ($allPythonProcesses) {
    Write-Host "  找到 $($allPythonProcesses.Count) 个 Python 进程" -ForegroundColor Yellow
    Write-Host "  显示详细信息（不自动停止，请手动确认）:" -ForegroundColor Yellow
    
    foreach ($proc in $allPythonProcesses) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine) {
                $shortCmd = if ($cmdLine.Length -gt 100) { $cmdLine.Substring(0, 100) + "..." } else { $cmdLine }
                Write-Host "  - PID: $($proc.Id) | $shortCmd" -ForegroundColor Gray
            } else {
                Write-Host "  - PID: $($proc.Id) | (无法获取命令行)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "  - PID: $($proc.Id) | (无法获取信息)" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    $confirm = Read-Host "是否停止所有 Python 进程？(y/N)"
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        foreach ($proc in $allPythonProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "  ✅ 已停止 PID: $($proc.Id)" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  停止失败 PID: $($proc.Id): $_" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  ℹ️  已取消" -ForegroundColor Gray
    }
} else {
    Write-Host "  ℹ️  未找到 Python 进程" -ForegroundColor Gray
}

Write-Host ""

# 检查端口占用
Write-Host "[4] 检查常用端口占用..." -ForegroundColor Yellow
$ports = @(8000, 3000, 11434)  # 后端、前端、Ollama
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "  端口 $port 被占用:" -ForegroundColor Yellow
        foreach ($conn in $connections) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "    - PID: $($proc.Id) | $($proc.ProcessName)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  端口 $port: 空闲" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示: 如果还有进程未停止，可以手动使用以下命令:" -ForegroundColor Yellow
Write-Host "  Get-Process | Where-Object { `$_.ProcessName -like '*python*' }" -ForegroundColor Gray
Write-Host "  Stop-Process -Id <PID> -Force" -ForegroundColor Gray
Write-Host ""
