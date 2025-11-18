# API Connection Monitor with Windows Toast Notification
# 监控API连接状态，断线时发送通知并询问是否重启
# Usage: powershell -ExecutionPolicy Bypass -File scripts\monitor_api_connection.ps1

param(
    [int]$CheckInterval = 30,  # 检查间隔（秒）
    [int]$RetryCount = 3,      # 连续失败次数才判定为断线
    [string]$ApiUrl = "http://localhost:8000/api/health"
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader - API Connection Monitor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring API: $ApiUrl" -ForegroundColor Gray
Write-Host "Check Interval: $CheckInterval seconds" -ForegroundColor Gray
Write-Host "Retry Count: $RetryCount failures before alert" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"

# 检查是否安装了BurntToast模块（用于Windows Toast通知）
$hasBurntToast = $false
try {
    Import-Module BurntToast -ErrorAction Stop
    $hasBurntToast = $true
    Write-Host "[OK] BurntToast module loaded" -ForegroundColor Green
} catch {
    Write-Host "[INFO] BurntToast module not found, will use alternative notification method" -ForegroundColor Yellow
    Write-Host "  To install: Install-Module -Name BurntToast -Scope CurrentUser" -ForegroundColor Gray
}

# 状态变量
$failureCount = 0
$lastStatus = $true
$isMonitoring = $true

# 发送Windows Toast通知的函数
function Send-ToastNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Icon = "Warning"
    )
    
    if ($hasBurntToast) {
        # 使用BurntToast模块
        try {
            New-BurntToastNotification `
                -Text $Title, $Message `
                -AppId "AI Trader" `
                -Sound "Default" `
                -ErrorAction Stop | Out-Null
            return $true
        } catch {
            Write-Host "[WARN] Failed to send toast notification: $_" -ForegroundColor Yellow
            return $false
        }
    } else {
        # 使用Windows Runtime API（Windows 10+）
        try {
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            
            $toastXml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode($Title)) | Out-Null
            $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode($Message)) | Out-Null
            
            $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
            $toast.ExpirationTime = [DateTimeOffset]::Now.AddMinutes(5)
            
            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AI Trader")
            $notifier.Show($toast)
            return $true
        } catch {
            # 如果Toast API不可用，使用系统声音和消息框
            Write-Host "[WARN] Toast API not available, using alternative method" -ForegroundColor Yellow
            [System.Media.SystemSounds]::Exclamation.Play()
            
            # 使用PowerShell的Show-Command或Out-GridView作为替代
            # 但最简单的是使用msg命令（如果可用）或直接显示在控制台
            Write-Host ""
            Write-Host "================================================" -ForegroundColor Red
            Write-Host "  $Title" -ForegroundColor Red
            Write-Host "================================================" -ForegroundColor Red
            Write-Host "$Message" -ForegroundColor Yellow
            Write-Host "================================================" -ForegroundColor Red
            Write-Host ""
            return $false
        }
    }
}

# 检查API状态的函数
function Test-ApiConnection {
    param([string]$Url)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# 重启API服务器的函数
function Restart-ApiServer {
    Write-Host ""
    Write-Host "[RESTART] Attempting to restart API server..." -ForegroundColor Yellow
    
    # 检查是否有Python进程在运行API服务器（通过端口8000）
    $portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($portInUse) {
        $processIds = $portInUse | Select-Object -ExpandProperty OwningProcess -Unique
        $apiProcesses = $processIds | ForEach-Object {
            Get-Process -Id $_ -ErrorAction SilentlyContinue
        } | Where-Object { $_.ProcessName -eq "python" }
    } else {
        $apiProcesses = @()
    }
    
    if ($apiProcesses) {
        Write-Host "[INFO] Found running API processes, stopping them..." -ForegroundColor Gray
        $apiProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
    
    # 检查端口8000是否被占用
    $portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "[INFO] Port 8000 is still in use, killing process..." -ForegroundColor Gray
        $portInUse | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
    
    # 启动API服务器
    try {
        $venvPath = Join-Path $ProjectRoot ".venv"
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        
        if (-not (Test-Path $activateScript)) {
            Write-Host "[ERROR] Virtual environment not found at: $venvPath" -ForegroundColor Red
            return $false
        }
        
        # 创建启动命令
        $apiCommand = @"
Set-Location `"$BackendDir`"
& `"$activateScript`"
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@
        
        # 在新窗口中启动API服务器
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand
        
        Write-Host "[OK] API server restart initiated in new window" -ForegroundColor Green
        Write-Host "[INFO] Waiting 10 seconds for server to start..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
        
        # 验证服务器是否启动成功
        if (Test-ApiConnection -Url $ApiUrl) {
            Write-Host "[SUCCESS] API server is now running!" -ForegroundColor Green
            Send-ToastNotification -Title "API Server Restarted" -Message "API server has been successfully restarted and is now online." -Icon "Info"
            return $true
        } else {
            Write-Host "[WARN] API server may still be starting, please check manually" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "[ERROR] Failed to restart API server: $_" -ForegroundColor Red
        return $false
    }
}

# 显示重启确认对话框
function Show-RestartDialog {
    $title = "API Server Disconnected"
    $message = "The API server appears to be offline.`n`nWould you like to restart it automatically?"
    $yes = New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "Restart the API server automatically"
    $no = New-Object System.Management.Automation.Host.ChoiceDescription "&No", "Do not restart (monitoring will continue)"
    $options = [System.Management.Automation.Host.ChoiceDescription[]]($yes, $no)
    $result = $host.UI.PromptForChoice($title, $message, $options, 0)
    
    return ($result -eq 0)
}

# 主监控循环
Write-Host "[START] Starting monitoring loop..." -ForegroundColor Green
Write-Host ""

while ($isMonitoring) {
    try {
        $isOnline = Test-ApiConnection -Url $ApiUrl
        
        if ($isOnline) {
            if ($failureCount -gt 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [RECOVERED] API server is back online" -ForegroundColor Green
                Send-ToastNotification -Title "API Server Recovered" -Message "The API server connection has been restored." -Icon "Info"
                $failureCount = 0
            } else {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [OK] API server is online" -ForegroundColor Gray
            }
            $lastStatus = $true
        } else {
            $failureCount++
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [WARN] API server check failed ($failureCount/$RetryCount)" -ForegroundColor Yellow
            
            if ($failureCount -ge $RetryCount) {
                if ($lastStatus) {
                    # 首次检测到断线
                    Write-Host ""
                    Write-Host "[ALERT] API server appears to be offline!" -ForegroundColor Red
                    Write-Host ""
                    
                    # 发送Toast通知
                    Send-ToastNotification `
                        -Title "API Server Disconnected" `
                        -Message "The AI Trader API server appears to be offline. Would you like to restart it?" `
                        -Icon "Warning"
                    
                    # 等待一下让用户看到通知
                    Start-Sleep -Seconds 2
                    
                    # 显示确认对话框
                    $shouldRestart = Show-RestartDialog
                    
                    if ($shouldRestart) {
                        $restartSuccess = Restart-ApiServer
                        if ($restartSuccess) {
                            $failureCount = 0
                            $lastStatus = $true
                        } else {
                            Write-Host "[ERROR] Failed to restart API server automatically" -ForegroundColor Red
                            Write-Host "[INFO] You can manually restart using: .\scripts\setup_step3_start_services.ps1" -ForegroundColor Yellow
                        }
                    } else {
                        Write-Host "[INFO] User chose not to restart. Monitoring will continue..." -ForegroundColor Yellow
                        Write-Host "[INFO] You can manually restart using: .\scripts\setup_step3_start_services.ps1" -ForegroundColor Gray
                    }
                    Write-Host ""
                } else {
                    # 持续断线状态
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] [OFFLINE] API server is still offline" -ForegroundColor Red
                }
                $lastStatus = $false
            }
        }
        
        # 等待下一次检查
        Start-Sleep -Seconds $CheckInterval
        
    } catch {
        Write-Host "[ERROR] Monitoring error: $_" -ForegroundColor Red
        Start-Sleep -Seconds $CheckInterval
    }
}

Write-Host ""
Write-Host "[STOP] Monitoring stopped" -ForegroundColor Yellow

