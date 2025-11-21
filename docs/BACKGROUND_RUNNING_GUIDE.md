# 后台运行指南 / Background Running Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### ⚠️ 重要：关闭窗口的影响

**关键问题**：如果意外关闭运行 API 的窗口，系统会停止吗？

**答案取决于启动方式**：

| 启动方式 | 关闭窗口的影响 | 后台运行 |
|---------|--------------|---------|
| **开发模式**（手动启动） | ❌ **会停止** | ❌ 否 |
| **Task Scheduler**（任务计划程序） | ✅ **不会停止** | ✅ 是 |
| **Windows Service**（Windows 服务） | ✅ **不会停止** | ✅ 是 |

---

## 🎯 推荐：使用 Task Scheduler（最简单）

### 为什么推荐？

- ✅ **无需安装额外软件**（Windows 自带）
- ✅ **关闭窗口不会停止**（后台运行）
- ✅ **系统重启后自动启动**
- ✅ **崩溃后自动重启**

### 快速设置

**步骤 1: 设置后台运行**
```powershell
# 右键点击并以管理员身份运行：
scripts\start_api_task_admin.bat
```

**步骤 2: 按照提示操作**
- 选择 `(I)nstall` 安装定时任务
- 选择 `(S)tart` 立即启动

**完成！** 现在关闭窗口也不会停止 API。

### 验证设置

```powershell
# 检查任务状态
Get-ScheduledTask -TaskName "AITraderAPI"

# 查看任务信息
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**预期输出**：
```
TaskName     State
--------     -----
AITraderAPI  Running
```

### 管理命令

```powershell
# 启动服务
Start-ScheduledTask -TaskName "AITraderAPI"

# 停止服务
Stop-ScheduledTask -TaskName "AITraderAPI"

# 重启服务
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"

# 查看状态
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

---

## 🔧 方法 2: Windows Service（更稳定）

### 为什么选择 Windows Service？

- ✅ **更稳定**（系统级服务）
- ✅ **更好的日志管理**
- ✅ **关闭窗口不会停止**
- ✅ **系统重启后自动启动**

### 快速设置

**步骤 1: 设置 Windows Service**
```powershell
# 右键点击并以管理员身份运行：
scripts\start_api_service_admin.bat
```

**步骤 2: 按照提示操作**
- 脚本会自动安装 NSSM（如果未安装）
- 按照提示安装 Windows 服务

**完成！** 现在关闭窗口也不会停止 API。

### 管理命令

```powershell
# 启动服务
Start-Service -Name "AITraderAPI"

# 停止服务
Stop-Service -Name "AITraderAPI"

# 重启服务
Restart-Service -Name "AITraderAPI"

# 查看状态
Get-Service -Name "AITraderAPI"
```

---

## ⚠️ 方法 3: 开发模式（不推荐用于长期运行）

### 特点

- ❌ **关闭窗口会停止 API**
- ❌ **系统重启后不会自动启动**
- ✅ **适合开发和调试**

### 如何识别开发模式？

如果看到这样的启动命令：
```powershell
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

这就是开发模式，**关闭窗口会停止 API**。

### 切换到后台运行

如果当前是开发模式，切换到后台运行：

**方法 1: 切换到 Task Scheduler**
```powershell
# 1. 停止当前 API（关闭窗口或按 Ctrl+C）
# 2. 设置 Task Scheduler
scripts\start_api_task_admin.bat
```

**方法 2: 切换到 Windows Service**
```powershell
# 1. 停止当前 API（关闭窗口或按 Ctrl+C）
# 2. 设置 Windows Service
scripts\start_api_service_admin.bat
```

---

## 🔍 如何检查当前运行方式？

### 检查 Task Scheduler

```powershell
Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
```

**如果有输出**：使用 Task Scheduler，关闭窗口不会停止 ✅

### 检查 Windows Service

```powershell
Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue
```

**如果有输出**：使用 Windows Service，关闭窗口不会停止 ✅

### 检查端口占用

```powershell
$pid = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -First 1 -Unique
if ($pid) {
    $proc = Get-Process -Id $pid
    Write-Host "API 进程 PID: $pid"
    Write-Host "进程名: $($proc.ProcessName)"
    Write-Host "启动时间: $($proc.StartTime)"
}
```

**如果进程名是 `python` 且没有 Task/Service**：可能是开发模式，关闭窗口会停止 ⚠️

---

## 📋 快速检查脚本

运行以下脚本检查当前状态：

```powershell
.\scripts\check_running_services.ps1
```

这会显示：
- ✅ 当前运行方式（Task Scheduler / Windows Service / 开发模式）
- ✅ 是否可以安全关闭窗口
- ✅ 如何切换到后台运行

---

## 🎯 推荐配置

### 长期运行（数周/数月）

**推荐**：使用 Task Scheduler
```powershell
# 右键点击并以管理员身份运行：
scripts\start_api_task_admin.bat
```

**优点**：
- ✅ 关闭窗口不会停止
- ✅ 系统重启后自动启动
- ✅ 崩溃后自动重启
- ✅ 无需安装额外软件

### 开发调试

**推荐**：使用开发模式
```powershell
& .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**注意**：关闭窗口会停止，适合开发时使用。

---

## ❓ 常见问题

### Q1: 我关闭了窗口，API 还在运行吗？

**检查方法**：
```powershell
# 方法 1: 检查端口
netstat -ano | findstr :8000

# 方法 2: 检查 API 状态
.\scripts\check_api_status.ps1

# 方法 3: 访问 API 文档
# 浏览器打开: http://localhost:8000/docs
```

**如果 API 还在运行**：说明使用了 Task Scheduler 或 Windows Service ✅

**如果 API 已停止**：说明是开发模式，需要切换到后台运行 ⚠️

### Q2: 如何确保关闭窗口不会停止？

**设置 Task Scheduler**（推荐）：
```powershell
scripts\start_api_task_admin.bat
```

**或设置 Windows Service**：
```powershell
scripts\start_api_service_admin.bat
```

### Q3: 我已经在开发模式下运行，如何切换到后台？

**步骤**：
1. **停止当前 API**（关闭窗口或按 `Ctrl+C`）
2. **设置后台运行**：
   ```powershell
   scripts\start_api_task_admin.bat
   ```
3. **验证**：关闭窗口后检查 API 是否还在运行

---

## 📚 相关文档

- [快速设置指南](QUICK_SETUP_GUIDE.md) - 完整的设置步骤
- [API 重启指南](API_RESTART_GUIDE.md) - 如何重启 API
- [长期运行指南](LONG_TERM_RUNNING_GUIDE.md) - 长期运行配置

---

## English Version

### ⚠️ Important: Impact of Closing Window

**Key Question**: If you accidentally close the window running the API, will the system stop?

**Answer depends on how it was started**:

| Startup Method | Impact of Closing Window | Background Running |
|---------------|-------------------------|-------------------|
| **Development Mode** (Manual) | ❌ **Will Stop** | ❌ No |
| **Task Scheduler** | ✅ **Won't Stop** | ✅ Yes |
| **Windows Service** | ✅ **Won't Stop** | ✅ Yes |

---

## 🎯 Recommended: Use Task Scheduler (Easiest)

### Why Recommended?

- ✅ **No additional software needed** (built into Windows)
- ✅ **Closing window won't stop it** (runs in background)
- ✅ **Auto-starts after system reboot**
- ✅ **Auto-restarts on crash**

### Quick Setup

**Step 1: Setup Background Running**
```powershell
# Right-click and run as administrator:
scripts\start_api_task_admin.bat
```

**Step 2: Follow Prompts**
- Choose `(I)nstall` to install scheduled task
- Choose `(S)tart` to start immediately

**Done!** Now closing the window won't stop the API.

### Verify Setup

```powershell
# Check task status
Get-ScheduledTask -TaskName "AITraderAPI"

# View task info
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**Expected Output**:
```
TaskName     State
--------     -----
AITraderAPI  Running
```

### Management Commands

```powershell
# Start service
Start-ScheduledTask -TaskName "AITraderAPI"

# Stop service
Stop-ScheduledTask -TaskName "AITraderAPI"

# Restart service
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"

# View status
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

---

## 🔧 Method 2: Windows Service (More Stable)

### Why Choose Windows Service?

- ✅ **More stable** (system-level service)
- ✅ **Better log management**
- ✅ **Closing window won't stop it**
- ✅ **Auto-starts after system reboot**

### Quick Setup

**Step 1: Setup Windows Service**
```powershell
# Right-click and run as administrator:
scripts\start_api_service_admin.bat
```

**Step 2: Follow Prompts**
- Script will auto-download and install NSSM (Non-Sucking Service Manager) if not found
- Follow prompts to install Windows service
- Service will be configured with automatic restart on failure
- Logs will be saved to `logs/api_service.log`

**Done!** Now closing the window won't stop the API.

**Note**: First-time setup may take a few minutes as NSSM needs to be downloaded (~2MB).

### Management Commands

```powershell
# Start service
Start-Service -Name "AITraderAPI"

# Stop service
Stop-Service -Name "AITraderAPI"

# Restart service
Restart-Service -Name "AITraderAPI"

# View status
Get-Service -Name "AITraderAPI"
```

---

## ⚠️ Method 3: Development Mode (Not Recommended for Long-term)

### Characteristics

- ❌ **Closing window will stop API**
- ❌ **Won't auto-start after system reboot**
- ✅ **Suitable for development and debugging**

### How to Identify Development Mode?

If you see this startup command:
```powershell
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

This is development mode, **closing the window will stop the API**.

### Switch to Background Running

If currently in development mode, switch to background running:

**Method 1: Switch to Task Scheduler**
```powershell
# 1. Stop current API (close window or press Ctrl+C)
# 2. Setup Task Scheduler
scripts\start_api_task_admin.bat
```

**Method 2: Switch to Windows Service**
```powershell
# 1. Stop current API (close window or press Ctrl+C)
# 2. Setup Windows Service
scripts\start_api_service_admin.bat
```

---

## 🔍 How to Check Current Running Method?

### Check Task Scheduler

```powershell
Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
```

**If output exists**: Using Task Scheduler, closing window won't stop ✅

### Check Windows Service

```powershell
Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue
```

**If output exists**: Using Windows Service, closing window won't stop ✅

### Check Port Usage

```powershell
$pid = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -First 1 -Unique
if ($pid) {
    $proc = Get-Process -Id $pid
    Write-Host "API Process PID: $pid"
    Write-Host "Process Name: $($proc.ProcessName)"
    Write-Host "Start Time: $($proc.StartTime)"
}
```

**If process name is `python` and no Task/Service**: Likely development mode, closing window will stop ⚠️

---

## 📋 Quick Check Script

Run this script to check current status:

```powershell
.\scripts\check_running_services.ps1
```

This will show:
- ✅ Current running method (Task Scheduler / Windows Service / Development Mode)
- ✅ Whether it's safe to close window
- ✅ How to switch to background running

---

## 🎯 Recommended Configuration

### Long-term Running (Weeks/Months)

**Recommended**: Use Task Scheduler
```powershell
# Right-click and run as administrator:
scripts\start_api_task_admin.bat
```

**Advantages**:
- ✅ Closing window won't stop
- ✅ Auto-starts after system reboot
- ✅ Auto-restarts on crash
- ✅ No additional software needed

### Development & Debugging

**Recommended**: Use Development Mode
```powershell
& .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Note**: Closing window will stop, suitable for development use.

---

## ❓ FAQ

### Q1: I closed the window, is the API still running?

**Check Method**:
```powershell
# Method 1: Check port
netstat -ano | findstr :8000

# Method 2: Check API status
.\scripts\check_api_status.ps1

# Method 3: Access API docs
# Open browser: http://localhost:8000/docs
```

**If API is still running**: Using Task Scheduler or Windows Service ✅

**If API stopped**: Development mode, need to switch to background running ⚠️

### Q2: How to ensure closing window won't stop it?

**Setup Task Scheduler** (Recommended):
```powershell
scripts\start_api_task_admin.bat
```

**Or Setup Windows Service**:
```powershell
scripts\start_api_service_admin.bat
```

### Q3: I'm running in development mode, how to switch to background?

**Steps**:
1. **Stop current API** (close window or press `Ctrl+C`)
2. **Setup background running**:
   ```powershell
   scripts\start_api_task_admin.bat
   ```
3. **Verify**: After closing window, check if API is still running

---

## 📚 Related Documentation

- [Quick Setup Guide](QUICK_SETUP_GUIDE.md) - Complete setup steps
- [API Restart Guide](API_RESTART_GUIDE.md) - How to restart API
- [Long-term Running Guide](LONG_TERM_RUNNING_GUIDE.md) - Long-term running configuration

