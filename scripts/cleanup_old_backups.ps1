# Cleanup Old Backups Script
# Removes backup directories older than 3 days, keeps the latest 3 backups

$backupDir = "data\backups"
$keepDays = 3

if (-not (Test-Path $backupDir)) {
    Write-Host "Backup directory not found: $backupDir"
    exit 0
}

# Get all backup directories sorted by date (newest first)
$backups = Get-ChildItem -Path $backupDir -Directory | 
    Where-Object { $_.Name -match '^\d{8}_\d{6}$' } |
    Sort-Object Name -Descending

$totalBackups = $backups.Count
Write-Host "Found $totalBackups backup directories"

if ($totalBackups -le $keepDays) {
    Write-Host "Only $totalBackups backups found, keeping all (minimum $keepDays)"
    exit 0
}

# Keep the latest $keepDays backups
$toKeep = $backups | Select-Object -First $keepDays
$toDelete = $backups | Select-Object -Skip $keepDays

Write-Host "Keeping latest $keepDays backups:"
$toKeep | ForEach-Object { Write-Host "  - $($_.Name)" }

Write-Host "`nDeleting $($toDelete.Count) old backups:"
$totalSize = 0
foreach ($backup in $toDelete) {
    $size = (Get-ChildItem -Path $backup.FullName -Recurse -File | 
        Measure-Object -Property Length -Sum).Sum / 1MB
    $totalSize += $size
    Write-Host "  - $($backup.Name) ($([math]::Round($size, 2)) MB)"
    Remove-Item -Path $backup.FullName -Recurse -Force
}

Write-Host "`nCleaned up $([math]::Round($totalSize, 2)) MB of old backups"
Write-Host "Kept $keepDays latest backups"

