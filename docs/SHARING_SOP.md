# 📋 分享网站 - 标准操作程序 (SOP)

> **完整步骤指南：如何启动并分享 AI Trader 网站**

---

## 🎯 目标

让局域网内的其他设备可以访问你的 AI Trader 前端和 API。

---

## 📋 前置准备

### 1. 检查 Python 环境
```powershell
python --version
# 应该显示 Python 3.10 或更高版本
```

### 2. 确认项目目录
```powershell
# 项目完整路径
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

# 或者如果你在父目录 "LLM AI trader"
cd ai-trader-ollama
```

**⚠️ 重要提示：**
- 脚本必须在**项目根目录**（`ai-trader-ollama`）运行
- 如果当前在 `LLM AI trader` 目录，需要先进入 `ai-trader-ollama` 子目录
- 如果当前在 `frontend` 或 `backend` 目录，先运行 `cd ..` 回到根目录
- 或者使用完整路径（见下方"从任何目录运行"部分）

**检查是否在正确目录：**
```powershell
# 应该看到 scripts 文件夹
dir scripts

# 应该看到 frontend 和 backend 文件夹
dir frontend, backend
```

---

## 🚀 启动步骤

### ⚠️ 重要：确保在项目根目录

**检查当前目录：**
```powershell
# 应该显示项目根目录路径
pwd
# 例如: C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama
```

**如果不在根目录：**
```powershell
# 从 frontend 目录回到根目录
cd ..

# 从 backend 目录回到根目录
cd ..
```

**或者使用完整路径（从任何目录都可以）：**
```powershell
# 从 "LLM AI trader" 目录运行
$projectRoot = "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
powershell -ExecutionPolicy Bypass -File "$projectRoot\scripts\start_api_stable_bypass.ps1"

# 或者使用相对路径（从 "LLM AI trader" 目录）
powershell -ExecutionPolicy Bypass -File .\ai-trader-ollama\scripts\start_api_stable_bypass.ps1
```

---

### 步骤 1: 启动后端 API（必须）

**方法 A: 使用脚本（推荐）**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1
```

**方法 B: 手动启动（推荐 - 直接使用 Python）**
```powershell
# 在项目根目录运行（不需要 cd backend）
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**参数说明：**
- `--host 0.0.0.0`: 允许局域网访问（必须！）
- `--port 8000`: 监听端口 8000
- `--reload`: 代码修改时自动重启（开发模式）

**验证后端是否启动：**
```powershell
# 检查端口 8000
netstat -ano | findstr :8000

# 测试本地访问
curl http://localhost:8000/docs
```

**预期结果：**
- 新窗口打开，显示 API 服务器日志
- 端口 8000 显示 `LISTENING`
- 浏览器访问 `http://localhost:8000/docs` 可以看到 API 文档

---

### 步骤 2: 启动前端服务器（必须）

**⚠️ 注意：必须在项目根目录运行，不是在 frontend 目录！**

**方法 A: 使用脚本（推荐）**
```powershell
# 确保在项目根目录
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

# 然后运行
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
```

**如果当前在 frontend 目录：**
```powershell
# 先回到根目录
cd ..

# 然后运行脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
```

**方法 B: 手动启动（推荐 - 直接使用 Python）**
```powershell
# 在项目根目录运行
cd frontend
python -m http.server 3000 --bind 0.0.0.0
```

**⚠️ 注意：**
- 使用 `--bind 0.0.0.0` 允许局域网访问
- 不使用 `--bind 0.0.0.0` 只能本地访问（localhost）

**验证前端是否启动：**
```powershell
# 检查端口 3000
netstat -ano | findstr :3000

# 测试本地访问
curl http://localhost:3000/monitor.html
```

**预期结果：**
- 新窗口打开（如果使用脚本）
- 端口 3000 显示 `LISTENING`
- 浏览器访问 `http://localhost:3000/monitor.html` 可以看到前端页面

---

### 步骤 3: 设置防火墙（首次需要，只需一次）

**方法 A: 使用脚本（需要管理员权限）**
```powershell
# 右键 PowerShell -> 以管理员身份运行
powershell -ExecutionPolicy Bypass -File .\scripts\setup_firewall.ps1
```

**方法 B: 手动设置（图形界面）**
1. 按 `Win + R`，输入 `wf.msc`，回车
2. 点击"入站规则" → "新建规则"
3. 选择"端口" → 下一步
4. 选择"TCP"，输入端口 `8000` → 下一步
5. 选择"允许连接" → 下一步
6. 勾选所有配置文件（域、专用、公用） → 下一步
7. 名称：`Python API 8000` → 完成
8. 重复步骤 2-7，添加端口 `3000`（名称：`Python HTTP 3000`）

**方法 C: 使用命令行（需要管理员权限）**
```powershell
# 以管理员身份运行
netsh advfirewall firewall add rule name="Python API 8000" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Python HTTP 3000" dir=in action=allow protocol=TCP localport=3000
```

**验证防火墙规则：**
```powershell
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Python*" -or $_.DisplayName -like "*8000*" -or $_.DisplayName -like "*3000*"} | Select-Object DisplayName, Enabled
```

---

### 步骤 4: 获取分享链接

**获取你的 IP 地址和分享链接：**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
```

**或者手动获取 IP：**
```powershell
ipconfig | findstr IPv4
```

**分享链接格式：**
```
前端地址: http://你的IP:3000/monitor.html
API 文档: http://你的IP:8000/docs
```

**示例（IP: 192.168.4.24）：**
```
前端地址: http://192.168.4.24:3000/monitor.html
API 文档: http://192.168.4.24:8000/docs
```

---

## ✅ 验证清单

在分享给其他人之前，确认以下所有项目：

- [ ] 后端 API 正在运行（端口 8000）
- [ ] 前端服务器正在运行（端口 3000）
- [ ] 防火墙规则已设置（端口 8000 和 3000）
- [ ] 本地访问测试成功
  - [ ] `http://localhost:8000/docs` 可以访问
  - [ ] `http://localhost:3000/monitor.html` 可以访问
- [ ] 局域网访问测试成功（在同一台电脑上测试）
  - [ ] `http://你的IP:8000/docs` 可以访问
  - [ ] `http://你的IP:3000/monitor.html` 可以访问

---

## 🔍 故障排除

### 问题 1: 无法访问 `http://你的IP:8000`

**可能原因：**
- 防火墙未设置
- 后端未启动
- IP 地址错误

**解决方法：**
```powershell
# 1. 检查后端是否运行
netstat -ano | findstr :8000

# 2. 检查防火墙规则
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*8000*"}

# 3. 重新获取 IP
ipconfig | findstr IPv4

# 4. 重启后端
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

---

### 问题 2: 无法访问 `http://你的IP:3000`

**可能原因：**
- 前端未启动
- 防火墙未设置
- IP 地址错误

**解决方法：**
```powershell
# 1. 检查前端是否运行
netstat -ano | findstr :3000

# 2. 检查防火墙规则
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*3000*"}

# 3. 重新启动前端
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
```

---

### 问题 3: PowerShell 执行策略错误

**错误信息：**
```
因为這個系統上已停用指令碼執行，所以無法載入...
```

**解决方法：**
```powershell
# 方法 1: 使用 Bypass 参数（推荐）
powershell -ExecutionPolicy Bypass -File .\scripts\脚本名称.ps1

# 方法 2: 临时设置（当前会话）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 方法 3: 永久设置（仅当前用户，不需要管理员）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 问题 4: 其他人无法访问

**检查清单：**
1. ✅ 确认设备在同一 WiFi/局域网
2. ✅ 确认防火墙规则已设置
3. ✅ 确认后端和前端都在运行
4. ✅ 确认 IP 地址正确
5. ✅ 在你自己电脑上测试局域网地址是否可访问

**测试命令：**
```powershell
# 在同一台电脑上测试局域网地址
curl http://你的IP:8000/docs
curl http://你的IP:3000/monitor.html
```

---

## 📝 日常使用流程

### 启动系统（每天第一次）

1. **启动后端 API**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1
   ```
   - 保持窗口打开

2. **启动前端服务器**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
   ```
   - 保持窗口打开

3. **获取分享链接**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
   ```

4. **分享链接给其他人**

---

### 停止系统

1. **停止前端**
   - 在前端窗口按 `Ctrl+C`
   - 或关闭前端 PowerShell 窗口

2. **停止后端**
   - 在后端窗口按 `Ctrl+C`
   - 或关闭后端 PowerShell 窗口

---

## 🔄 快速重启

### 重启后端 API
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

### 重启前端
```powershell
# 停止前端（如果正在运行）
Get-NetTCPConnection -LocalPort 3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# 重新启动
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
```

---

## 📊 状态检查命令

### 检查所有服务状态
```powershell
Write-Host "=== 服务状态检查 ===" -ForegroundColor Cyan

# 检查后端
$api = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'}
if ($api) { Write-Host "[OK] 后端 API 运行中 (8000)" -ForegroundColor Green } 
else { Write-Host "[X] 后端 API 未运行" -ForegroundColor Red }

# 检查前端
$frontend = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'}
if ($frontend) { Write-Host "[OK] 前端服务器运行中 (3000)" -ForegroundColor Green } 
else { Write-Host "[X] 前端服务器未运行" -ForegroundColor Red }

# 获取 IP
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress
Write-Host "`n你的 IP: $ip" -ForegroundColor Cyan
Write-Host "前端: http://$ip:3000/monitor.html" -ForegroundColor Yellow
Write-Host "API: http://$ip:8000/docs" -ForegroundColor Yellow
```

---

## 📌 重要提示

1. **必须保持运行**
   - 后端和前端窗口必须保持打开
   - 关闭窗口会停止对应的服务

2. **防火墙设置**
   - 只需设置一次（除非重装系统）
   - 设置后永久有效

3. **同一网络**
   - 其他设备必须连接到同一个 WiFi/局域网
   - 不同网络无法访问

4. **IP 地址可能变化**
   - 如果 IP 地址改变，需要重新获取并分享新链接
   - 使用 `get_share_link.ps1` 获取最新 IP

---

## 🎯 快速参考

### 一键启动（两个服务）
```powershell
# 终端 1: 启动后端
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1

# 终端 2: 启动前端
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1

# 终端 3: 获取分享链接
powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
```

### 一键检查状态
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
```

---

## 📞 需要帮助？

如果遇到问题：
1. 检查本文档的"故障排除"部分
2. 查看 README.md 的 Troubleshooting 部分
3. 检查 PowerShell 窗口的错误信息

---

**最后更新**: 2025-01-XX  
**版本**: 1.0

