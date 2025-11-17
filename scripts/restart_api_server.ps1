# 重启 API 服务器脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "重启 API 服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 停止所有 uvicorn 进程
Write-Host "[1] 停止所有 uvicorn 进程..." -ForegroundColor Yellow
$uvicornProcesses = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*"
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
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ 已停止 PID: $($proc.Id)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  停止失败 PID: $($proc.Id): $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ℹ️  未找到 uvicorn 进程" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[2] 等待进程完全停止..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[3] 检查端口 8000..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    Write-Host "  ⚠️  端口 8000 仍被占用" -ForegroundColor Yellow
    foreach ($conn in $port8000) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "    - PID: $($proc.Id) | $($proc.ProcessName)" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
} else {
    Write-Host "  ✅ 端口 8000 已释放" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4] 启动新的 API 服务器..." -ForegroundColor Yellow
$backendDir = Join-Path $PSScriptRoot ".." "backend"
$backendDir = Resolve-Path $backendDir -ErrorAction SilentlyContinue

if (-not $backendDir) {
    Write-Host "  ❌ 找不到 backend 目录" -ForegroundColor Red
    exit 1
}

$apiCommand = @"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server'
cd '$backendDir'
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host '当前目录: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host 'API 地址: http://127.0.0.1:8000' -ForegroundColor Green
Write-Host '文档地址: http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host '健康检查: http://127.0.0.1:8000/api/health' -ForegroundColor Green
Write-Host ''
Write-Host '按 Ctrl+C 停止服务器' -ForegroundColor Yellow
Write-Host ''
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
"@

try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
    Write-Host "  ✅ API 服务器已在新窗口启动" -ForegroundColor Green
    Write-Host ""
    Write-Host "等待服务器启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # 测试连接
    Write-Host ""
    Write-Host "[5] 测试 API 连接..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ API 服务器运行正常" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  API 返回状态码: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️  无法连接到 API: $_" -ForegroundColor Yellow
        Write-Host "     请检查新窗口中的错误信息" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 启动失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "手动启动命令:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

