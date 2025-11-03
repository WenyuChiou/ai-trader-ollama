# 🔄 保持后端 API 持续运行

有几种方式可以让后端 API 在后台持续运行，即使关闭终端窗口也不影响。

---

## 🪟 Windows 方法

### 方法 1: 使用 Windows 任务计划程序（推荐）

创建一个定时任务，系统启动时自动运行 API：

```powershell
cd backend\scripts

# 创建启动脚本
@"
@echo off
cd /d "%~dp0.."
call python -m venv venv
call venv\Scripts\activate
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
"@ | Out-File -Encoding UTF8 start_api.ps1
```

**然后创建 Windows 服务**：

```powershell
# 需要管理员权限
New-Service -Name "AITraderAPI" `
    -BinaryPathName "powershell.exe -File C:\path\to\backend\scripts\start_api.ps1" `
    -StartupType Automatic `
    -DisplayName "AI Trader API Server"
```

### 方法 2: 使用 NSSM (Non-Sucking Service Manager)（简单）

1. **下载 NSSM**: https://nssm.cc/download
2. **安装服务**:

```powershell
# 进入 NSSM 目录
cd C:\path\to\nssm\win64

# 创建服务
.\nssm.exe install AITraderAPI

# 在弹出的窗口中设置:
# Path: C:\path\to\python.exe
# Startup directory: C:\path\to\ai-trader-ollama\backend
# Arguments: -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# 启动服务
.\nssm.exe start AITraderAPI
```

### 方法 3: 使用 PowerShell 后台作业（临时）

```powershell
cd backend

# 创建后台作业
$job = Start-Job -ScriptBlock {
    cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
    uvicorn src.api.server:app --host 0.0.0.0 --port 8000
}

# 查看作业状态
Get-Job

# 查看作业输出
Receive-Job -Job $job

# 停止作业
Stop-Job -Job $job
Remove-Job -Job $job
```

### 方法 4: 使用 pm2 (Node.js 进程管理器)

即使这是 Python 应用，也可以使用 pm2：

```powershell
# 安装 pm2
npm install -g pm2

# 创建配置文件: backend/ecosystem.config.js
cd backend
```

创建 `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'ai-trader-api',
    script: 'python',
    args: '-m uvicorn src.api.server:app --host 0.0.0.0 --port 8000',
    cwd: 'C:/Users/wenyu/Desktop/investment/LLM AI trader/ai-trader-ollama/backend',
    interpreter: 'python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
```

```powershell
# 启动
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs ai-trader-api

# 停止
pm2 stop ai-trader-api

# 设置开机自启
pm2 startup
pm2 save
```

---

## 🐧 Linux/Mac 方法

### 方法 1: 使用 systemd (Linux) / launchd (Mac)

**Linux systemd**:

创建 `/etc/systemd/system/ai-trader-api.service`:

```ini
[Unit]
Description=AI Trader API Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/ai-trader-ollama/backend
ExecStart=/path/to/python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl start ai-trader-api

# 开机自启
sudo systemctl enable ai-trader-api

# 查看状态
sudo systemctl status ai-trader-api

# 查看日志
sudo journalctl -u ai-trader-api -f
```

**Mac launchd**:

创建 `~/Library/LaunchAgents/com.ai-trader.api.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-trader.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/python</string>
        <string>-m</string>
        <string>uvicorn</string>
        <string>src.api.server:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/ai-trader-ollama/backend</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
# 加载服务
launchctl load ~/Library/LaunchAgents/com.ai-trader.api.plist

# 启动
launchctl start com.ai-trader.api

# 停止
launchctl stop com.ai-trader.api
```

### 方法 2: 使用 screen / tmux

```bash
# 使用 screen
screen -S ai-trader-api
cd backend
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
# 按 Ctrl+A 然后按 D 来 detach

# 重新连接
screen -r ai-trader-api

# 使用 tmux
tmux new -s ai-trader-api
cd backend
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
# 按 Ctrl+B 然后按 D 来 detach

# 重新连接
tmux attach -t ai-trader-api
```

### 方法 3: 使用 nohup

```bash
cd backend
nohup uvicorn src.api.server:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# 查看进程
ps aux | grep uvicorn

# 查看日志
tail -f api.log

# 停止
pkill -f "uvicorn src.api.server"
```

---

## 🎯 推荐方案

### Windows 用户（推荐）

1. **开发/测试**: 使用 PowerShell 后台作业或 pm2
2. **生产环境**: 使用 NSSM 或 Windows 服务

### Linux/Mac 用户（推荐）

1. **开发/测试**: 使用 screen/tmux
2. **生产环境**: 使用 systemd (Linux) 或 launchd (Mac)

---

## 🔍 验证 API 是否运行

```bash
# 测试 API
curl http://localhost:8000/

# 或使用浏览器打开
http://localhost:8000/
```

应该看到 API 的 JSON 响应。

---

## 🛠️ 故障排除

### API 无法启动

1. **检查端口占用**:
   ```powershell
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

2. **检查 Python 路径**:
   ```bash
   which python
   python --version
   ```

3. **检查依赖**:
   ```bash
   pip list | grep uvicorn
   ```

### API 启动后立即停止

查看日志文件或输出，常见问题：
- 端口已被占用
- 依赖缺失
- 配置文件错误

---

## 📝 快速启动脚本

创建 `backend/scripts/start_api_background.ps1` (Windows):

```powershell
$apiScript = @"
cd `"$PSScriptRoot\..`"
uvicorn src.api.server:app --host 0.0.0.0 --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiScript
```

双击运行即可在独立窗口中启动 API。

