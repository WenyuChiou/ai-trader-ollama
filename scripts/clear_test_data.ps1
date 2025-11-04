# 清空所有测试文件和记录
# 使用方法: .\scripts\clear_test_data.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "清空测试文件和记录" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 切换到backend目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = if ($scriptPath -match "backend") { $scriptPath } else { Join-Path $scriptPath "backend" }
Set-Location $backendDir

# 运行Python脚本
python scripts\clear_test_data.py

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

