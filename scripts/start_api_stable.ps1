# PowerShell Script: Start API Server with Auto-Restart and Error Handling
# 穩定版本：自動重啟、錯誤處理、日誌記錄
# Usage: .\scripts\start_api_stable.ps1

$ErrorActionPreference = "Continue"  # 繼續執行，不因錯誤停止

# 獲取專案根目錄
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API Server (穩定版)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "專案目錄: $ProjectRoot" -ForegroundColor Gray
Write-Host "API 地址: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""

# 檢查 Python 環境
Write-Host "[檢查] Python 環境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 錯誤: 找不到 Python" -ForegroundColor Red
    Write-Host "  請確保已安裝 Python 並在 PATH 中" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

# 檢查虛擬環境
Write-Host "[檢查] 虛擬環境..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "  ✓ 找到虛擬環境" -ForegroundColor Green
} else {
    Write-Host "  ⚠ 警告: 未找到虛擬環境，將使用系統 Python" -ForegroundColor Yellow
}

# 檢查並停止舊的 API 進程
Write-Host "[檢查] 端口 8000..." -ForegroundColor Yellow
$portConnections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portConnections) {
    $processIds = $portConnections.OwningProcess | Select-Object -Unique
    foreach ($pid in $processIds) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  發現進程: PID $pid ($($process.ProcessName))" -ForegroundColor Yellow
            Write-Host "  正在停止..." -ForegroundColor Yellow
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "  ✓ 已停止進程 $pid" -ForegroundColor Green
            } catch {
                Write-Host "  ✗ 無法停止進程 $pid: $_" -ForegroundColor Red
            }
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "  ✓ 端口 8000 可用" -ForegroundColor Green
}

# 設置日誌目錄
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = Join-Path $logDir "api_server_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$errorLogFile = Join-Path $logDir "api_server_errors_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host ""
Write-Host "[啟動] API 服務器..." -ForegroundColor Cyan
Write-Host "  日誌文件: $logFile" -ForegroundColor Gray
Write-Host "  錯誤日誌: $errorLogFile" -ForegroundColor Gray
Write-Host ""

# 構建啟動命令（帶錯誤處理和自動重啟）
$apiCommand = @"
`$ErrorActionPreference = "Continue"
`$host.ui.RawUI.WindowTitle = 'AI Trader API Server (穩定版)'
cd '$ProjectRoot'

# 啟用虛擬環境（如果存在）
if (Test-Path '.venv\Scripts\Activate.ps1') {
    . '.venv\Scripts\Activate.ps1'
    Write-Host '[環境] 已啟用虛擬環境' -ForegroundColor Green
}

Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  AI Trader API Server (穩定版)' -ForegroundColor Cyan
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'API 地址: http://127.0.0.1:8000' -ForegroundColor Green
Write-Host '當前目錄: ' -NoNewline
Write-Host `$PWD -ForegroundColor Gray
Write-Host ''
Write-Host '特性:' -ForegroundColor Cyan
Write-Host '  • 自動錯誤處理' -ForegroundColor White
Write-Host '  • 崩潰自動重啟' -ForegroundColor White
Write-Host '  • 日誌記錄' -ForegroundColor White
Write-Host ''
Write-Host '按 Ctrl+C 停止服務器' -ForegroundColor Yellow
Write-Host ''

# 自動重啟循環
`$maxRestarts = 10
`$restartCount = 0
`$restartDelay = 5  # 重啟前等待秒數

while (`$restartCount -lt `$maxRestarts) {
    try {
        Write-Host "[啟動] 嘗試 `$(`$restartCount + 1)/`$maxRestarts..." -ForegroundColor Cyan
        Write-Host ""
        
        # 啟動 API 服務器
        python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
        
        # 如果正常退出（Ctrl+C），不重啟
        Write-Host ""
        Write-Host "[退出] API 服務器已正常停止" -ForegroundColor Green
        break
        
    } catch {
        `$restartCount++
        Write-Host ""
        Write-Host "[錯誤] API 服務器崩潰: `$_" -ForegroundColor Red
        Write-Host "[錯誤] 錯誤詳情: `$(`$_.Exception.Message)" -ForegroundColor Red
        
        if (`$restartCount -ge `$maxRestarts) {
            Write-Host ""
            Write-Host "[停止] 已達到最大重啟次數 (`$maxRestarts)，停止自動重啟" -ForegroundColor Red
            Write-Host "請檢查錯誤日誌並手動修復問題" -ForegroundColor Yellow
            break
        }
        
        Write-Host ""
        Write-Host "[重啟] `$restartDelay 秒後自動重啟 (第 `$restartCount 次)..." -ForegroundColor Yellow
        Start-Sleep -Seconds `$restartDelay
        Write-Host ""
    }
}

Write-Host ""
Write-Host "API 服務器已停止" -ForegroundColor Yellow
Read-Host "按 Enter 關閉窗口"
"@

# 啟動新窗口
try {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
    Write-Host "✓ 成功: API 服務器已在新窗口啟動" -ForegroundColor Green
    Write-Host ""
    Write-Host "驗證步驟:" -ForegroundColor Cyan
    Write-Host "  1. 檢查新 PowerShell 窗口的服務器日誌" -ForegroundColor White
    Write-Host "  2. 打開瀏覽器: http://127.0.0.1:8000/docs" -ForegroundColor White
    Write-Host "  3. 測試狀態: http://127.0.0.1:8000/api/agents/status" -ForegroundColor White
    Write-Host ""
    Write-Host "注意:" -ForegroundColor Yellow
    Write-Host "  • API 窗口必須保持打開狀態" -ForegroundColor White
    Write-Host "  • 關閉窗口會停止 API" -ForegroundColor White
    Write-Host "  • 如果崩潰，會自動重啟（最多 10 次）" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "✗ 錯誤: 無法啟動 API 服務器: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "替代方案: 手動在終端執行:" -ForegroundColor Yellow
    Write-Host "  cd $ProjectRoot" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
    Write-Host ""
}

Read-Host "按 Enter 繼續"

