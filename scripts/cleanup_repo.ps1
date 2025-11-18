# Cleanup Repository - Remove Unnecessary Files
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_repo.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Repository Cleanup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$removedCount = 0
$removedSize = 0

# 1. Clean old backup files (keep only last 7 days)
Write-Host "[1] Cleaning old backup files..." -ForegroundColor Yellow
$backupFiles = Get-ChildItem -Path "data\logs" -Filter "portfolio_state_backup_*.json" -ErrorAction SilentlyContinue
if ($backupFiles) {
    $cutoffDate = (Get-Date).AddDays(-7)
    $oldBackups = $backupFiles | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    foreach ($file in $oldBackups) {
        $size = $file.Length
        Remove-Item $file.FullName -Force
        $removedCount++
        $removedSize += $size
        Write-Host "  Removed: $($file.Name)" -ForegroundColor Gray
    }
    
    if ($oldBackups.Count -eq 0) {
        Write-Host "  No old backup files to remove (keeping last 7 days)" -ForegroundColor Green
    } else {
        Write-Host "  Removed $($oldBackups.Count) old backup files" -ForegroundColor Green
    }
} else {
    Write-Host "  No backup files found" -ForegroundColor Gray
}

# 2. Clean old log files (keep only last 30 days)
Write-Host ""
Write-Host "[2] Cleaning old log files..." -ForegroundColor Yellow
$logFiles = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue
if ($logFiles) {
    $cutoffDate = (Get-Date).AddDays(-30)
    $oldLogs = $logFiles | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    foreach ($file in $oldLogs) {
        $size = $file.Length
        Remove-Item $file.FullName -Force
        $removedCount++
        $removedSize += $size
        Write-Host "  Removed: $($file.Name)" -ForegroundColor Gray
    }
    
    if ($oldLogs.Count -eq 0) {
        Write-Host "  No old log files to remove (keeping last 30 days)" -ForegroundColor Green
    } else {
        Write-Host "  Removed $($oldLogs.Count) old log files" -ForegroundColor Green
    }
} else {
    Write-Host "  No log files found" -ForegroundColor Gray
}

# 3. Clean __pycache__ directories
Write-Host ""
Write-Host "[3] Cleaning __pycache__ directories..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "*\.venv*" -and $_.FullName -notlike "*\node_modules*" }
if ($pycacheDirs) {
    foreach ($dir in $pycacheDirs) {
        $size = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        Remove-Item $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
        $removedCount++
        $removedSize += $size
        Write-Host "  Removed: $($dir.FullName)" -ForegroundColor Gray
    }
    Write-Host "  Removed $($pycacheDirs.Count) __pycache__ directories" -ForegroundColor Green
} else {
    Write-Host "  No __pycache__ directories found" -ForegroundColor Gray
}

# 4. Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Cleanup Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Files/Directories removed: $removedCount" -ForegroundColor White
Write-Host "  Space freed: $([math]::Round($removedSize / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "✅ Cleanup completed!" -ForegroundColor Green
Write-Host ""

