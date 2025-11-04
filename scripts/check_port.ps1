# PowerShell Script: Check and kill process using port 8000
# Usage: .\check_port.ps1

$port = 8000

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Checking Port $port Usage" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if port is in use
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    $processId = $connection.OwningProcess | Select-Object -Unique
    Write-Host "Port $port is in use!" -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($pid in $processId) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Process ID: $pid" -ForegroundColor White
            Write-Host "Process Name: $($process.ProcessName)" -ForegroundColor White
            Write-Host "Command Line:" -ForegroundColor White
            try {
                $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $pid").CommandLine
                if ($cmdLine) {
                    Write-Host "  $cmdLine" -ForegroundColor Gray
                }
            } catch {
                Write-Host "  (Cannot retrieve command line)" -ForegroundColor Gray
            }
            Write-Host ""
        }
    }
    
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Kill the process(es) using port $port" -ForegroundColor White
    Write-Host "  2. Use a different port (e.g., 8001)" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Kill process(es)? (Y/N)"
    
    if ($choice -eq "Y" -or $choice -eq "y") {
        foreach ($pid in $processId) {
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "Process $pid killed successfully" -ForegroundColor Green
            } catch {
                Write-Host "Failed to kill process $pid : $_" -ForegroundColor Red
            }
        }
        Write-Host ""
        Write-Host "Port $port should now be available" -ForegroundColor Green
        Write-Host "You can now start the API server" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "To use a different port, modify the startup command:" -ForegroundColor Yellow
        Write-Host "  python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8001" -ForegroundColor White
    }
} else {
    Write-Host "Port $port is available" -ForegroundColor Green
    Write-Host "You can start the API server now" -ForegroundColor Green
}

Write-Host ""
Read-Host "Press Enter to exit"

