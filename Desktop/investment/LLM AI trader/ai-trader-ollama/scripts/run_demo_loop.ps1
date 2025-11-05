# Demo loop to simulate real-time portfolio updates every 30 seconds
# Usage:
#   powershell -ExecutionPolicy Bypass -File run_demo_loop.ps1 -ApiUrl http://127.0.0.1:8000 -IntervalSeconds 30

param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [int]$IntervalSeconds = 30,
    [int]$VolatilityBps = 15,
    [switch]$WithConversations
)

Write-Host "Starting demo real-time updater..." -ForegroundColor Cyan
Write-Host "API: $ApiUrl | Interval: $IntervalSeconds s | Volatility: $VolatilityBps bps" -ForegroundColor Gray

while ($true) {
    try {
        $url = "$ApiUrl/api/demo/real-time?volatility_bps=$VolatilityBps"
        $resp = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 10
        if ($resp.ok -or $resp.source -eq 'demo') {
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $tv = '{0:N2}' -f $resp.total_value
            $pnl = '{0:N2}' -f $resp.total_pnl
            $pct = '{0:N3}' -f $resp.total_pnl_pct
            Write-Host "[$ts] Demo tick => TotalValue=$tv  PnL=$pnl ($pct%)" -ForegroundColor Green
        } else {
            Write-Host "Demo tick failed: $($resp | ConvertTo-Json -Depth 4)" -ForegroundColor Yellow
        }

        if ($WithConversations) {
            try {
                $convUrl = "$ApiUrl/api/demo/conversation-tick"
                $conv = Invoke-RestMethod -Uri $convUrl -Method POST -TimeoutSec 10
                if ($conv.ok) {
                    Write-Host "   + conversation: $($conv.entry.agent) - $($conv.entry.content)" -ForegroundColor DarkCyan
                }
            } catch {
                Write-Host "Failed to write demo conversation: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    Start-Sleep -Seconds $IntervalSeconds
}


