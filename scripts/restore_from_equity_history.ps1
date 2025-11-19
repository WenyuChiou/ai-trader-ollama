# Restore Portfolio from Equity History
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\restore_from_equity_history.ps1 [date]

param(
    [string]$Date = ""  # YYYY-MM-DD format, empty = latest
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Restore Portfolio from Equity History" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$logsDir = "data/logs"
$equityFile = Join-Path $logsDir "equity_history.jsonl"
$portfolioFile = Join-Path $logsDir "portfolio_state.json"

if (-not (Test-Path $equityFile)) {
    Write-Host "Equity history file not found: $equityFile" -ForegroundColor Red
    exit 1
}

# Read equity history
$equityRecords = Get-Content $equityFile | ForEach-Object {
    try {
        $_ | ConvertFrom-Json
    } catch {
        Write-Warning "Failed to parse line: $_"
    }
}

if ($equityRecords.Count -eq 0) {
    Write-Host "No equity records found!" -ForegroundColor Red
    exit 1
}

# Find target record
$targetRecord = $null
if ([string]::IsNullOrEmpty($Date)) {
    # Use latest record
    $targetRecord = $equityRecords | Sort-Object { 
        if ($_.timestamp) { [DateTime]::Parse($_.timestamp) } 
        else { [DateTime]::Parse($_.date) } 
    } -Descending | Select-Object -First 1
    Write-Host "Using latest equity record:" -ForegroundColor Yellow
} else {
    # Find record for specific date
    $targetRecord = $equityRecords | Where-Object { 
        $_.date -eq $Date -or $_.timestamp -like "$Date*" 
    } | Sort-Object { 
        if ($_.timestamp) { [DateTime]::Parse($_.timestamp) } 
        else { [DateTime]::Parse($_.date) } 
    } -Descending | Select-Object -First 1
    
    if (-not $targetRecord) {
        Write-Host "No equity record found for date: $Date" -ForegroundColor Red
        Write-Host "Available dates:" -ForegroundColor Yellow
        $equityRecords | Select-Object -Unique -Property date | ForEach-Object {
            Write-Host "  - $($_.date)" -ForegroundColor Gray
        }
        exit 1
    }
    Write-Host "Using equity record for date: $Date" -ForegroundColor Yellow
}

Write-Host "  Date: $($targetRecord.date)" -ForegroundColor Green
Write-Host "  Timestamp: $($targetRecord.timestamp)" -ForegroundColor Gray
Write-Host "  Cash: $($targetRecord.cash)" -ForegroundColor Green
Write-Host "  Equity Value: $($targetRecord.equity_value)" -ForegroundColor Green
Write-Host "  Total Value: $($targetRecord.total_value)" -ForegroundColor Green
Write-Host "  Positions: $($targetRecord.positions.PSObject.Properties.Count)" -ForegroundColor Green
Write-Host ""

if ($targetRecord.positions.PSObject.Properties.Count -eq 0) {
    Write-Host "No positions found in this record!" -ForegroundColor Red
    exit 1
}

Write-Host "Position Details:" -ForegroundColor Magenta
$targetRecord.positions.PSObject.Properties | ForEach-Object {
    $pos = $_.Value
    $symbol = $_.Name
    $quantity = $pos.quantity
    $avgCost = $pos.avg_cost
    $totalCost = if ($pos.total_cost) { $pos.total_cost } else { $avgCost * $quantity }
    Write-Host "  $symbol : $quantity shares @ avg_cost $avgCost (total_cost: $totalCost)" -ForegroundColor Gray
}
Write-Host ""

# Backup current portfolio_state.json
if (Test-Path $portfolioFile) {
    $backupName = "portfolio_state_backup_before_equity_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $backupPath = Join-Path $logsDir $backupName
    Copy-Item $portfolioFile $backupPath -Force
    Write-Host "Backed up current portfolio_state.json to: $backupName" -ForegroundColor Yellow
    Write-Host ""
}

# Reconstruct portfolio_state.json
$portfolioState = @{
    cash = [double]$targetRecord.cash
    initial_value = 10000.0  # Default, can be adjusted
    total_value = [double]$targetRecord.total_value
    positions = @{}
    timestamp = if ($targetRecord.timestamp) { $targetRecord.timestamp } else { (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffffZ") }
    snapshot = @{
        cash = [double]$targetRecord.cash
        total_value = [double]$targetRecord.total_value
        equity_value = [double]$targetRecord.equity_value
        positions_count = $targetRecord.positions.PSObject.Properties.Count
    }
}

# Add positions
foreach ($prop in $targetRecord.positions.PSObject.Properties) {
    $pos = $prop.Value
    $symbol = $prop.Name
    $quantity = $pos.quantity
    $avgCost = $pos.avg_cost
    $totalCost = if ($pos.total_cost) { $pos.total_cost } else { $avgCost * $quantity }
    
    $portfolioState.positions[$symbol] = @{
        quantity = $quantity
        avg_cost = [double]$avgCost
        total_cost = [double]$totalCost
    }
}

# Try to get initial_value from previous records
$initialValueRecords = $equityRecords | Where-Object { $_.total_pnl -ne $null } | Select-Object -First 1
if ($initialValueRecords) {
    # Calculate initial_value from total_pnl
    $totalPnl = $initialValueRecords.total_pnl
    $currentValue = $initialValueRecords.total_value
    $calculatedInitial = $currentValue - $totalPnl
    if ($calculatedInitial > 0) {
        $portfolioState.initial_value = [double]$calculatedInitial
        Write-Host "Calculated initial_value from equity history: $calculatedInitial" -ForegroundColor Gray
    }
}

# Save portfolio_state.json
$portfolioJson = $portfolioState | ConvertTo-Json -Depth 10
$portfolioJson | Out-File -FilePath $portfolioFile -Encoding UTF8 -NoNewline

Write-Host "Portfolio restored successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Restored Portfolio:" -ForegroundColor Yellow
Write-Host "  Cash: $($portfolioState.cash)" -ForegroundColor Green
Write-Host "  Total Value: $($portfolioState.total_value)" -ForegroundColor Green
Write-Host "  Positions: $($portfolioState.positions.Count)" -ForegroundColor Green
Write-Host "  Position Symbols: $($portfolioState.positions.Keys -join ', ')" -ForegroundColor Magenta
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Restore Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

