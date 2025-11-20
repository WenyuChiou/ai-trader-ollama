# Quick Railway Upload Setup - Direct Execution
# This script directly sets up daily upload without exposing Railway URL

$TaskName = "AI-Trader-Railway-Daily-Upload"
$ScriptPath = "scripts\upload_data_to_railway.py"
$WorkingDir = (Resolve-Path (Split-Path $PSScriptRoot -Parent)).Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Railway Daily Upload Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway URL is configured
try {
    $null = python -c "from scripts.config_railway import get_railway_url; url = get_railway_url(); exit(0 if url else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Railway URL not configured. Configuring now..." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Please enter your Railway URL:" -ForegroundColor Cyan
        $railwayUrl = Read-Host "Railway URL"
        if ($railwayUrl) {
            python scripts\config_railway.py $railwayUrl
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] Failed to configure Railway URL" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "[ERROR] Railway URL is required" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "[WARN] Could not check Railway URL configuration" -ForegroundColor Yellow
}

# Get Python path
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[INFO] Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Get schedule time
Write-Host ""
Write-Host "Schedule Configuration:" -ForegroundColor Cyan
$timeInput = Read-Host "Enter upload time (HH:MM format, e.g., 18:00 for 6 PM)"
if (-not $timeInput) {
    $timeInput = "18:00"
    Write-Host "[INFO] Using default time: 18:00" -ForegroundColor Yellow
}

try {
    $scheduleTime = [DateTime]::ParseExact($timeInput.Trim(), "HH:mm", $null)
} catch {
    Write-Host "[ERROR] Invalid time format. Using default: 18:00" -ForegroundColor Red
    $timeInput = "18:00"
    $scheduleTime = [DateTime]::ParseExact("18:00", "HH:mm", $null)
}

Write-Host ""
$daysInput = Read-Host "Run on weekdays only? (y/n, default: y)"
$weekdaysOnly = ($daysInput -ne "n")

# Create task action
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Create trigger
if ($weekdaysOnly) {
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $scheduleTime.ToString("HH:mm")
} else {
    $Trigger = New-ScheduledTaskTrigger -Daily -At $scheduleTime.ToString("HH:mm")
}

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create principal
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Limited

# Register task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Upload AI-Trader local data to Railway daily" | Out-Null
    
    Write-Host ""
    Write-Host "[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule:" -ForegroundColor Cyan
    Write-Host "  Time: $($scheduleTime.ToString('HH:mm'))" -ForegroundColor White
    Write-Host "  Days: $(if ($weekdaysOnly) { 'Weekdays (Mon-Fri)' } else { 'Every day' })" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host "Make sure you're running as Administrator" -ForegroundColor Yellow
    exit 1
}

