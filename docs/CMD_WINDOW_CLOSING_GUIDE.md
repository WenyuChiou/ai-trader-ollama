# CMD 窗口关闭指南 / CMD Window Closing Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### ⚠️ 重要：CMD 窗口关闭说明

**问题**：我看到一个 CMD 窗口在运行 API，关闭这个窗口会停止服务吗？

**答案**：取决于您如何启动的 API。

---

## 🔍 如何判断当前运行方式？

### 方法 1: 快速检查脚本

```powershell
.\scripts\check_window_safety.ps1
```

**结果说明**：
- ✅ **SAFE: You can close the window** → 可以安全关闭，服务会继续运行
- ❌ **UNSAFE: Closing window may stop API** → 关闭窗口会停止服务

---

## 📋 三种运行方式对比

| 运行方式 | 关闭窗口的影响 | 如何识别 |
|---------|--------------|---------|
| **Task Scheduler** | ✅ **不会停止** | 检查脚本显示 "Using Task Scheduler" |
| **Windows Service** | ✅ **不会停止** | 检查脚本显示 "Using Windows Service" |
| **开发模式** | ❌ **会停止** | 手动启动，窗口标题显示 uvicorn |

---

## ✅ 情况 1: 使用 Task Scheduler（推荐）

**特征**：
- 检查脚本显示：`OK: Using Task Scheduler`
- 状态：`SAFE: You can close the window`

**说明**：
- ✅ **可以安全关闭 CMD 窗口**
- ✅ API 会继续在后台运行
- ✅ 即使关闭窗口，服务也不会停止

**验证方法**：
1. 关闭 CMD 窗口
2. 等待 5 秒
3. 访问：http://localhost:8000/docs
4. 如果还能访问，说明服务仍在运行 ✅

**为什么会有窗口？**
- Task Scheduler 启动时会打开一个窗口显示日志
- 这个窗口可以安全关闭
- 服务在后台继续运行

---

## ✅ 情况 2: 使用 Windows Service

**特征**：
- 检查脚本显示：`OK: Using Windows Service`
- 状态：`SAFE: You can close the window`

**说明**：
- ✅ **可以安全关闭任何窗口**
- ✅ API 作为系统服务运行
- ✅ 完全独立于任何窗口

---

## ❌ 情况 3: 开发模式（关闭窗口会停止）

**特征**：
- 检查脚本显示：`WARNING: No background running method detected`
- 状态：`UNSAFE: Closing window may stop API`
- 窗口标题可能显示：`uvicorn` 或 `python`

**说明**：
- ❌ **关闭窗口会停止 API**
- ❌ 窗口必须保持打开
- ✅ 适合开发和调试

**如何切换到后台运行？**

**方法 1: 切换到 Task Scheduler（推荐）**
```powershell
# 1. 停止当前 API（关闭窗口或按 Ctrl+C）
# 2. 设置 Task Scheduler
# 右键点击并以管理员身份运行：
scripts\start_api_task_admin.bat
```

**方法 2: 切换到 Windows Service**
```powershell
# 1. 停止当前 API（关闭窗口或按 Ctrl+C）
# 2. 设置 Windows Service
# 右键点击并以管理员身份运行：
scripts\start_api_service_admin.bat
```

---

## 🔧 如何确认当前状态？

### 步骤 1: 运行安全检查

```powershell
.\scripts\check_window_safety.ps1
```

### 步骤 2: 检查 Task Scheduler

```powershell
Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
```

**如果有输出**：使用 Task Scheduler，可以安全关闭窗口 ✅

### 步骤 3: 检查 Windows Service

```powershell
Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue
```

**如果有输出**：使用 Windows Service，可以安全关闭窗口 ✅

### 步骤 4: 测试关闭窗口

1. **记录当前 API 状态**：
   ```powershell
   # 访问 API 文档
   Start-Process "http://localhost:8000/docs"
   ```

2. **关闭 CMD 窗口**

3. **等待 5 秒**

4. **再次访问 API**：
   ```powershell
   Start-Process "http://localhost:8000/docs"
   ```

5. **结果判断**：
   - ✅ **还能访问**：服务仍在运行，可以安全关闭窗口
   - ❌ **无法访问**：服务已停止，需要切换到后台运行

---

## 💡 推荐做法

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

### Q1: 我看到 CMD 窗口，但检查脚本说可以安全关闭？

**A**: 这是正常的。Task Scheduler 启动时会打开一个窗口显示日志，但这个窗口可以安全关闭，服务会在后台继续运行。

**验证**：
1. 关闭窗口
2. 访问 http://localhost:8000/docs
3. 如果还能访问，说明服务仍在运行 ✅

### Q2: 我关闭了窗口，API 真的还在运行吗？

**A**: 验证方法：
```powershell
# 方法 1: 检查端口
netstat -ano | findstr :8000

# 方法 2: 访问 API
Start-Process "http://localhost:8000/docs"

# 方法 3: 检查 Task Scheduler
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

### Q3: 如何确保关闭窗口不会停止？

**A**: 设置后台运行：
```powershell
# 推荐：Task Scheduler
scripts\start_api_task_admin.bat
```

---

## 📚 相关文档

- [后台运行指南](BACKGROUND_RUNNING_GUIDE.md) - 完整的后台运行设置指南
- [Windows Service 故障排除](WINDOWS_SERVICE_TROUBLESHOOTING.md) - Windows Service 问题解决
- [快速设置指南](QUICK_SETUP_GUIDE.md) - 快速设置步骤

---

## English Version

### ⚠️ Important: CMD Window Closing Guide

**Question**: I see a CMD window running the API. Will closing it stop the service?

**Answer**: It depends on how you started the API.

---

## 🔍 How to Determine Current Running Method?

### Method 1: Quick Check Script

```powershell
.\scripts\check_window_safety.ps1
```

**Result Explanation**:
- ✅ **SAFE: You can close the window** → Safe to close, service will continue running
- ❌ **UNSAFE: Closing window may stop API** → Closing window will stop service

---

## 📋 Three Running Methods Comparison

| Running Method | Impact of Closing Window | How to Identify |
|---------------|-------------------------|-----------------|
| **Task Scheduler** | ✅ **Won't Stop** | Check script shows "Using Task Scheduler" |
| **Windows Service** | ✅ **Won't Stop** | Check script shows "Using Windows Service" |
| **Development Mode** | ❌ **Will Stop** | Manually started, window shows uvicorn |

---

## ✅ Case 1: Using Task Scheduler (Recommended)

**Characteristics**:
- Check script shows: `OK: Using Task Scheduler`
- Status: `SAFE: You can close the window`

**Explanation**:
- ✅ **Safe to close CMD window**
- ✅ API continues running in background
- ✅ Service won't stop even if window is closed

**Verification Method**:
1. Close CMD window
2. Wait 5 seconds
3. Visit: http://localhost:8000/docs
4. If still accessible, service is still running ✅

**Why is there a window?**
- Task Scheduler opens a window to display logs when starting
- This window can be safely closed
- Service continues running in background

---

## ✅ Case 2: Using Windows Service

**Characteristics**:
- Check script shows: `OK: Using Windows Service`
- Status: `SAFE: You can close the window`

**Explanation**:
- ✅ **Safe to close any window**
- ✅ API runs as system service
- ✅ Completely independent of any window

---

## ❌ Case 3: Development Mode (Closing Window Will Stop)

**Characteristics**:
- Check script shows: `WARNING: No background running method detected`
- Status: `UNSAFE: Closing window may stop API`
- Window title may show: `uvicorn` or `python`

**Explanation**:
- ❌ **Closing window will stop API**
- ❌ Window must remain open
- ✅ Suitable for development and debugging

**How to Switch to Background Running?**

**Method 1: Switch to Task Scheduler (Recommended)**
```powershell
# 1. Stop current API (close window or press Ctrl+C)
# 2. Setup Task Scheduler
# Right-click and run as administrator:
scripts\start_api_task_admin.bat
```

**Method 2: Switch to Windows Service**
```powershell
# 1. Stop current API (close window or press Ctrl+C)
# 2. Setup Windows Service
# Right-click and run as administrator:
scripts\start_api_service_admin.bat
```

---

## 🔧 How to Confirm Current Status?

### Step 1: Run Safety Check

```powershell
.\scripts\check_window_safety.ps1
```

### Step 2: Check Task Scheduler

```powershell
Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
```

**If output exists**: Using Task Scheduler, safe to close window ✅

### Step 3: Check Windows Service

```powershell
Get-Service -Name "AITraderAPI" -ErrorAction SilentlyContinue
```

**If output exists**: Using Windows Service, safe to close window ✅

### Step 4: Test Closing Window

1. **Record current API status**:
   ```powershell
   # Visit API docs
   Start-Process "http://localhost:8000/docs"
   ```

2. **Close CMD window**

3. **Wait 5 seconds**

4. **Visit API again**:
   ```powershell
   Start-Process "http://localhost:8000/docs"
   ```

5. **Result Judgment**:
   - ✅ **Still accessible**: Service still running, safe to close window
   - ❌ **Not accessible**: Service stopped, need to switch to background running

---

## 💡 Recommended Practices

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

### Q1: I see a CMD window, but check script says it's safe to close?

**A**: This is normal. Task Scheduler opens a window to display logs when starting, but this window can be safely closed, service continues running in background.

**Verification**:
1. Close window
2. Visit http://localhost:8000/docs
3. If still accessible, service is still running ✅

### Q2: I closed the window, is the API really still running?

**A**: Verification methods:
```powershell
# Method 1: Check port
netstat -ano | findstr :8000

# Method 2: Visit API
Start-Process "http://localhost:8000/docs"

# Method 3: Check Task Scheduler
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

### Q3: How to ensure closing window won't stop it?

**A**: Setup background running:
```powershell
# Recommended: Task Scheduler
scripts\start_api_task_admin.bat
```

---

## 📚 Related Documentation

- [Background Running Guide](BACKGROUND_RUNNING_GUIDE.md) - Complete background running setup guide
- [Windows Service Troubleshooting](WINDOWS_SERVICE_TROUBLESHOOTING.md) - Windows Service issue resolution
- [Quick Setup Guide](QUICK_SETUP_GUIDE.md) - Quick setup steps

