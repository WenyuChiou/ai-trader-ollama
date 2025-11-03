# PowerShell 脚本：在后台启动 API 服务器
# 使用方法: 双击运行或在 PowerShell 中运行

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir ".."

Write-Host "================================================"
Write-Host "  启动 AI Trader API 服务器"
Write-Host "================================================"
Write-Host ""
Write-Host "工作目录: $BackendDir"
Write-Host "API 地址: http://localhost:8000"
Write-Host ""

# 检查 Python 是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion"
} catch {
    Write-Host "❌ 错误: 无法找到 Python"
    Write-Host "   请确保 Python 已安装并在 PATH 中"
    Read-Host "按 Enter 退出"
    exit 1
}

# 检查端口是否被占用
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  警告: 端口 8000 已被占用"
    Write-Host "   如果这是之前的 API 实例，可以忽略"
    Write-Host ""
}

# 在新窗口中启动 API
Write-Host "正在启动 API 服务器..."
Write-Host ""
Write-Host "提示: API 将在新窗口中运行"
Write-Host "     关闭新窗口即可停止 API"
Write-Host ""

$apiCommand = @"
cd "$BackendDir"
Write-Host "================================================"
Write-Host "  AI Trader API Server"
Write-Host "================================================"
Write-Host ""
Write-Host "API 地址: http://localhost:8000"
Write-Host "按 Ctrl+C 停止服务器"
Write-Host ""
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
Write-Host ""
Write-Host "API 服务器已停止"
Read-Host "按 Enter 关闭窗口"
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand

Write-Host ""
Write-Host "✅ API 服务器已在后台启动"
Write-Host ""
Write-Host "验证:"
Write-Host "   1. 打开浏览器: http://localhost:8000"
Write-Host "   2. 或运行: curl http://localhost:8000"
Write-Host ""

