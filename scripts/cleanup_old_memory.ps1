# 清理今天之前的 memory JSON 文件
# 使用方法: powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_old_memory.ps1

Write-Host "Cleaning up old memory files..." -ForegroundColor Cyan
Write-Host ""

python scripts/cleanup_old_memory.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Cleanup completed successfully" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Cleanup failed" -ForegroundColor Red
    exit 1
}

