# 简单版本：强制停止所有 Python 进程
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "强制停止所有 Python 进程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 查找所有 Python 进程
$pythonProcesses = Get-Process | Where-Object { 
    $_.ProcessName -eq "python" -or 
    $_.ProcessName -eq "pythonw" -or 
    $_.ProcessName -like "python*"
}

if ($pythonProcesses) {
    Write-Host "找到 $($pythonProcesses.Count) 个 Python 进程，正在停止..." -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "停止进程: PID $($proc.Id) ($($proc.ProcessName))" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ 已停止" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  停止失败: $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "✅ 所有 Python 进程已停止" -ForegroundColor Green
} else {
    Write-Host "ℹ️  未找到 Python 进程" -ForegroundColor Gray
}

Write-Host ""
Write-Host "检查端口占用情况..." -ForegroundColor Yellow
$ports = @(8000, 3000, 11434)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "  ⚠️  端口 $port 仍被占用" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 端口 $port 已释放" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green


