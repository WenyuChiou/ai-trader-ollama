# Cleanup Backup Files Script
# Usage: 
#   powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1 [keep_days]
#   powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1 -KeepDays 0  # 删除所有备份
#   powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1 -KeepDays 1  # 只保留今天

param(
    [int]$KeepDays = 7,  # 保留最近N天的备份，默认7天。设为0删除所有备份
    [switch]$All = $false  # 如果设置，删除所有备份（忽略KeepDays）
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Backup Files" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$logsDir = "data/logs"
if (-not (Test-Path $logsDir)) {
    Write-Host "Data directory not found: $logsDir" -ForegroundColor Red
    exit 1
}

# 查找所有备份文件
$backupFiles = Get-ChildItem -Path $logsDir -Filter "*backup*.json" | Sort-Object LastWriteTime -Descending

if ($backupFiles.Count -eq 0) {
    Write-Host "No backup files found." -ForegroundColor Green
    exit 0
}

Write-Host "Found $($backupFiles.Count) backup files" -ForegroundColor Yellow

# 如果设置了-All参数，删除所有备份
if ($All) {
    Write-Host "Mode: Delete ALL backups" -ForegroundColor Red
    $toKeep = @()
    $toDelete = $backupFiles
} elseif ($KeepDays -eq 0) {
    Write-Host "Mode: Delete ALL backups (KeepDays=0)" -ForegroundColor Red
    $toKeep = @()
    $toDelete = $backupFiles
} else {
    Write-Host "Mode: Keep backups from last $KeepDays days" -ForegroundColor Yellow
    Write-Host ""
    
    # 计算截止日期
    $cutoffDate = (Get-Date).AddDays(-$KeepDays)
    
    # 分类文件
    $toKeep = @()
    $toDelete = @()
    
    foreach ($file in $backupFiles) {
        if ($file.LastWriteTime -ge $cutoffDate) {
            $toKeep += $file
        } else {
            $toDelete += $file
        }
    }
}

Write-Host "Files to keep ($($toKeep.Count)):" -ForegroundColor Green
foreach ($file in $toKeep) {
    Write-Host "  - $($file.Name) ($($file.LastWriteTime.ToString('yyyy-MM-dd')))" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Files to delete ($($toDelete.Count)):" -ForegroundColor Yellow
foreach ($file in $toDelete) {
    Write-Host "  - $($file.Name) ($($file.LastWriteTime.ToString('yyyy-MM-dd')))" -ForegroundColor Gray
}

if ($toDelete.Count -eq 0) {
    Write-Host ""
    Write-Host "No files to delete." -ForegroundColor Green
    exit 0
}

Write-Host ""
$confirm = Read-Host "Delete $($toDelete.Count) old backup files? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# 删除旧备份
$deleted = 0
foreach ($file in $toDelete) {
    try {
        Remove-Item $file.FullName -Force
        Write-Host "Deleted: $($file.Name)" -ForegroundColor Green
        $deleted++
    } catch {
        Write-Host "Failed to delete: $($file.Name) - $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Deleted: $deleted files" -ForegroundColor Green
Write-Host "Kept: $($toKeep.Count) files" -ForegroundColor Green

