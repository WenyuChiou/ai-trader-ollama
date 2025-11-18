# Restore Portfolio Script
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\restore_portfolio.ps1 [backup_filename]

param(
    [string]$BackupFile = ""
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Portfolio Restore Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$logsDir = "data/logs"
$portfolioFile = Join-Path $logsDir "portfolio_state.json"

# Find backup files
$backupFiles = Get-ChildItem -Path $logsDir -Filter "*portfolio_state_backup*.json" | Sort-Object LastWriteTime -Descending

if ($backupFiles.Count -eq 0) {
    Write-Host "No backup files found!" -ForegroundColor Red
    exit 1
}

# If backup file not specified, use the latest one
if ([string]::IsNullOrEmpty($BackupFile)) {
    $selectedBackup = $backupFiles[0]
    Write-Host "No backup file specified, using latest:" -ForegroundColor Yellow
} else {
    $selectedBackup = $backupFiles | Where-Object { $_.Name -eq $BackupFile }
    if (-not $selectedBackup) {
        Write-Host "Backup file '$BackupFile' not found!" -ForegroundColor Red
        Write-Host "Available backups:" -ForegroundColor Yellow
        $backupFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
        exit 1
    }
}

Write-Host "Selected backup: $($selectedBackup.Name)" -ForegroundColor Green
Write-Host "Backup date: $($selectedBackup.LastWriteTime)" -ForegroundColor Gray
Write-Host ""

# Show backup contents
$backupContent = Get-Content $selectedBackup.FullName | ConvertFrom-Json
Write-Host "Backup Contents:" -ForegroundColor Yellow
Write-Host "  Cash: $($backupContent.cash)" -ForegroundColor Green
Write-Host "  Total Value: $($backupContent.total_value)" -ForegroundColor Green
Write-Host "  Positions: $($backupContent.positions.PSObject.Properties.Count)" -ForegroundColor Green
if ($backupContent.positions.PSObject.Properties.Count -gt 0) {
    Write-Host "  Position Symbols: $($backupContent.positions.PSObject.Properties.Name -join ', ')" -ForegroundColor Magenta
}
Write-Host ""

# Backup current portfolio_state.json if it exists
if (Test-Path $portfolioFile) {
    $currentBackupName = "portfolio_state_backup_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $currentBackupPath = Join-Path $logsDir $currentBackupName
    Copy-Item $portfolioFile $currentBackupPath -Force
    Write-Host "Backed up current portfolio_state.json to: $currentBackupName" -ForegroundColor Yellow
    Write-Host ""
}

# Restore from backup
Write-Host "Restoring portfolio from backup..." -ForegroundColor Cyan
Copy-Item $selectedBackup.FullName $portfolioFile -Force

# Verify restoration
if (Test-Path $portfolioFile) {
    $restoredContent = Get-Content $portfolioFile | ConvertFrom-Json
    Write-Host "Restoration successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Restored Portfolio:" -ForegroundColor Yellow
    Write-Host "  Cash: $($restoredContent.cash)" -ForegroundColor Green
    Write-Host "  Total Value: $($restoredContent.total_value)" -ForegroundColor Green
    Write-Host "  Positions: $($restoredContent.positions.PSObject.Properties.Count)" -ForegroundColor Green
    if ($restoredContent.positions.PSObject.Properties.Count -gt 0) {
        Write-Host "  Position Details:" -ForegroundColor Magenta
        $restoredContent.positions.PSObject.Properties | ForEach-Object {
            $pos = $_.Value
            Write-Host "    $($_.Name): $($pos.quantity) shares @ avg_cost $($pos.avg_cost)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "Restoration failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Restore Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

