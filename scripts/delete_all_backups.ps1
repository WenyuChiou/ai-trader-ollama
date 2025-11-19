# Delete All Backup Files Script
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\delete_all_backups.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Delete All Backup Files" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$logsDir = "data/logs"
if (-not (Test-Path $logsDir)) {
    Write-Host "Data directory not found: $logsDir" -ForegroundColor Red
    exit 1
}

# 查找所有备份文件
$backupFiles = Get-ChildItem -Path $logsDir -Filter "*backup*.json"

if ($backupFiles.Count -eq 0) {
    Write-Host "No backup files found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($backupFiles.Count) backup files:" -ForegroundColor Yellow
foreach ($file in $backupFiles) {
    Write-Host "  - $($file.Name) ($($file.Length) bytes, $($file.LastWriteTime.ToString('yyyy-MM-dd HH:mm')))" -ForegroundColor Gray
}
Write-Host ""

$confirm = Read-Host "⚠️  Delete ALL $($backupFiles.Count) backup files? (yes/no)"
if ($confirm -ne 'yes' -and $confirm -ne 'YES' -and $confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# 删除所有备份
$deleted = 0
foreach ($file in $backupFiles) {
    try {
        Remove-Item $file.FullName -Force
        Write-Host "✅ Deleted: $($file.Name)" -ForegroundColor Green
        $deleted++
    } catch {
        Write-Host "❌ Failed to delete: $($file.Name) - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Deleted: $deleted / $($backupFiles.Count) files" -ForegroundColor Green

