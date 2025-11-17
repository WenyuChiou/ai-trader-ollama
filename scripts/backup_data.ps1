# Backup Data Script
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\backup_data.ps1

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "data/backups/$timestamp"
$logsDir = "data/logs"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Data Backup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "Created backup directory: $backupDir" -ForegroundColor Green

# Backup critical files
$filesToBackup = @(
    "portfolio_state.json",
    "equity_history.jsonl",
    "discussion_actions.jsonl",
    "filled_orders.jsonl",
    "pending_orders.jsonl"
)

foreach ($file in $filesToBackup) {
    $sourcePath = Join-Path $logsDir $file
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $backupDir $file
        Copy-Item $sourcePath $destPath -Force
        Write-Host "Backed up: $file" -ForegroundColor Green
    } else {
        Write-Host "Not found: $file" -ForegroundColor Yellow
    }
}

# Backup memory directory
$memoryDir = Join-Path $logsDir "memory"
if (Test-Path $memoryDir) {
    $destMemoryDir = Join-Path $backupDir "memory"
    Copy-Item $memoryDir $destMemoryDir -Recurse -Force
    Write-Host "Backed up: memory directory" -ForegroundColor Green
}

# Create backup manifest
$manifest = @{
    timestamp = $timestamp
    date = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    files = $filesToBackup
    backup_dir = $backupDir
}

$manifestPath = Join-Path $backupDir "manifest.json"
$manifest | ConvertTo-Json -Depth 10 | Out-File $manifestPath -Encoding UTF8
Write-Host "Created backup manifest: manifest.json" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Backup Complete!" -ForegroundColor Green
Write-Host "  Backup location: $backupDir" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

