# Quick Setup Script for API Connection Monitor
# 快速设置API连接监控
# Usage: powershell -ExecutionPolicy Bypass -File scripts\setup_api_monitor.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader - API Monitor Quick Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$MonitorScript = Join-Path $ProjectRoot "scripts\monitor_api_connection.ps1"

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Monitor Script: $MonitorScript" -ForegroundColor Gray
Write-Host ""

# Check if monitor script exists
if (-not (Test-Path $MonitorScript)) {
    Write-Host "[ERROR] Monitor script not found: $MonitorScript" -ForegroundColor Red
    exit 1
}

Write-Host "Setup Options:" -ForegroundColor Yellow
Write-Host "  1. Start monitoring now (in current window)" -ForegroundColor White
Write-Host "  2. Start monitoring in background window" -ForegroundColor White
Write-Host "  3. Setup as scheduled task (auto-start on login)" -ForegroundColor White
Write-Host "  4. Setup as scheduled task + start now" -ForegroundColor White
Write-Host "  5. Test monitor first" -ForegroundColor White
Write-Host "  0. Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Select option (0-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[INFO] Starting monitor in current window..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
        Write-Host ""
        & $MonitorScript
    }
    
    "2" {
        Write-Host ""
        Write-Host "[INFO] Starting monitor in background window..." -ForegroundColor Yellow
        $monitorArgs = "-ExecutionPolicy Bypass -File `"$MonitorScript`""
        Start-Process powershell -ArgumentList $monitorArgs
        Write-Host "[OK] Monitor started in background window" -ForegroundColor Green
        Write-Host "[INFO] Check the new PowerShell window for monitoring status" -ForegroundColor Gray
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "3" {
        Write-Host ""
        Write-Host "[INFO] Setting up scheduled task..." -ForegroundColor Yellow
        Write-Host "[WARN] This requires administrator privileges" -ForegroundColor Yellow
        Write-Host ""
        
        $TaskName = "AITrader-ConnectionMonitor"
        
        # Check if task already exists
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
            $response = Read-Host "Remove and recreate? (Y/N)"
            if ($response -eq "Y" -or $response -eq "y") {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Host "[OK] Removed existing task" -ForegroundColor Green
            } else {
                Write-Host "[INFO] Keeping existing task" -ForegroundColor Gray
                exit 0
            }
        }
        
        # Create task action
        $Action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-ExecutionPolicy Bypass -File `"$MonitorScript`"" `
            -WorkingDirectory $ProjectRoot
        
        # Create trigger (at logon)
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        
        # Create settings
        $Settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable
        
        # Create principal
        $Principal = New-ScheduledTaskPrincipal `
            -UserId "$env:USERDOMAIN\$env:USERNAME" `
            -LogonType Interactive `
            -RunLevel Limited
        
        # Register task
        try {
            Register-ScheduledTask `
                -TaskName $TaskName `
                -Action $Action `
                -Trigger $Trigger `
                -Settings $Settings `
                -Principal $Principal `
                -Description "AI Trader - API Connection Monitor (Auto-start on login)" | Out-Null
            
            Write-Host "[SUCCESS] Scheduled task created successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Task Details:" -ForegroundColor Cyan
            Write-Host "  Name: $TaskName" -ForegroundColor White
            Write-Host "  Trigger: At logon" -ForegroundColor White
            Write-Host "  Script: $MonitorScript" -ForegroundColor White
            Write-Host ""
            Write-Host "To start manually:" -ForegroundColor Cyan
            Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
            Write-Host ""
            Write-Host "To remove:" -ForegroundColor Cyan
            Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor White
            Write-Host ""
        } catch {
            Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
            Write-Host "[INFO] You may need to run as administrator" -ForegroundColor Yellow
            Write-Host ""
        }
        
        Read-Host "Press Enter to exit"
    }
    
    "4" {
        Write-Host ""
        Write-Host "[INFO] Setting up scheduled task and starting monitor..." -ForegroundColor Yellow
        
        # First setup scheduled task (same as option 3)
        $TaskName = "AITrader-ConnectionMonitor"
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Host "[WARN] Task '$TaskName' already exists" -ForegroundColor Yellow
            $response = Read-Host "Remove and recreate? (Y/N)"
            if ($response -eq "Y" -or $response -eq "y") {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Host "[OK] Removed existing task" -ForegroundColor Green
            }
        }
        
        $Action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-ExecutionPolicy Bypass -File `"$MonitorScript`"" `
            -WorkingDirectory $ProjectRoot
        
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        
        $Settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable
        
        $Principal = New-ScheduledTaskPrincipal `
            -UserId "$env:USERDOMAIN\$env:USERNAME" `
            -LogonType Interactive `
            -RunLevel Limited
        
        try {
            Register-ScheduledTask `
                -TaskName $TaskName `
                -Action $Action `
                -Trigger $Trigger `
                -Settings $Settings `
                -Principal $Principal `
                -Description "AI Trader - API Connection Monitor (Auto-start on login)" | Out-Null
            
            Write-Host "[OK] Scheduled task created" -ForegroundColor Green
            
            # Start the task now
            Write-Host "[INFO] Starting monitor now..." -ForegroundColor Yellow
            Start-ScheduledTask -TaskName $TaskName
            Write-Host "[OK] Monitor started via scheduled task" -ForegroundColor Green
            Write-Host ""
            Write-Host "Monitor is now running in background" -ForegroundColor Cyan
            Write-Host "Check Task Scheduler to see status" -ForegroundColor Gray
            Write-Host ""
        } catch {
            Write-Host "[ERROR] Failed to setup: $_" -ForegroundColor Red
            Write-Host "[INFO] Trying to start monitor in background window instead..." -ForegroundColor Yellow
            $monitorArgs = "-ExecutionPolicy Bypass -File `"$MonitorScript`""
            Start-Process powershell -ArgumentList $monitorArgs
            Write-Host "[OK] Monitor started in background window" -ForegroundColor Green
        }
        
        Read-Host "Press Enter to exit"
    }
    
    "5" {
        Write-Host ""
        Write-Host "[INFO] Running test script..." -ForegroundColor Yellow
        $testScript = Join-Path $ProjectRoot "scripts\test_monitor_api.ps1"
        if (Test-Path $testScript) {
            & $testScript
        } else {
            Write-Host "[ERROR] Test script not found: $testScript" -ForegroundColor Red
        }
        Write-Host ""
        Read-Host "Press Enter to return to setup menu"
        # Re-run setup
        & $MyInvocation.MyCommand.Path
    }
    
    "0" {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "[ERROR] Invalid choice" -ForegroundColor Red
        exit 1
    }
}

