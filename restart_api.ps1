# 一键重启 API 服务器
# 使用方法：在项目根目录运行: .\restart_api.ps1
# 或在 PowerShell 中: powershell -ExecutionPolicy Bypass -File .\restart_api.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  API 服务器重启脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取项目根目录（脚本所在目录）
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

$backendDir = Join-Path $ProjectRoot "backend"
$venvPath = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"

# 检查 backend 目录是否存在
if (-not (Test-Path $backendDir)) {
    Write-Host "[错误] 找不到 backend 目录: $backendDir" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] 停止现有 API 服务器..." -ForegroundColor Yellow

# 查找并停止占用 8000 端口的进程
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($pids) {
    foreach ($pid in $pids) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  停止进程 PID: $pid ($($proc.ProcessName))" -ForegroundColor Gray
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # 忽略错误
        }
    }
    
    # 等待端口释放（最多等待 3 秒）
    $waitCount = 0
    while ($waitCount -lt 6) {
        Start-Sleep -Milliseconds 500
        $inUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if (-not $inUse) { 
            Write-Host "  ✓ 端口已释放" -ForegroundColor Green
            break 
        }
        $waitCount++
    }
    
    if ($waitCount -ge 6) {
        Write-Host "  ⚠ 警告: 端口可能仍被占用" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ 没有运行中的 API 服务器" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] 检查虚拟环境..." -ForegroundColor Yellow

# 检查虚拟环境
if (Test-Path $venvPath) {
    Write-Host "  ✓ 找到虚拟环境: $venvPath" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 警告: 未找到虚拟环境，将使用系统 Python" -ForegroundColor Yellow
    Write-Host "    虚拟环境路径: $venvPath" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[3/3] 启动新的 API 服务器..." -ForegroundColor Yellow

# 构建启动命令
$cmd = @"
cd '$backendDir'
if (Test-Path '$venvPath') { 
    & '$venvPath'
}
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@

# 启动新窗口
try {
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $cmd
    Write-Host "  ✓ API 服务器已在新窗口启动" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 启动失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  API 服务器重启完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  • API 文档: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  • 监控页面: http://127.0.0.1:8000/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "提示: API 服务器在新窗口运行，关闭该窗口即可停止服务器" -ForegroundColor Gray
Write-Host ""

