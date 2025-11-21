# API 重启指南 / API Restart Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### 何时需要重启 API？

**需要重启的情况**：
- ✅ 修改了后端 Python 代码（`backend/src/` 目录下的文件）
- ✅ 修改了 API 端点（`backend/src/api/server.py`）
- ✅ 修改了数据处理逻辑（`backend/src/data/` 目录下的文件）
- ✅ 修改了配置文件（`backend/config/` 目录下的文件）

**不需要重启的情况**：
- ❌ 只修改了前端文件（`frontend/` 目录）- 只需刷新浏览器
- ❌ 只修改了文档（`docs/` 目录）
- ❌ 只修改了脚本（`scripts/` 目录）

### 快速重启方法

#### 方法 1: 使用快速重启脚本（推荐）

```powershell
# 从项目根目录运行
.\scripts\restart_api_fast.ps1
```

**功能**：
- ✅ 自动停止占用端口 8000 的进程
- ✅ 自动启动新的 API 服务器（带 `--reload` 参数）
- ✅ 在新窗口中运行（不影响当前终端）

#### 方法 2: 如果使用 Task Scheduler

```powershell
# 重启任务
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"

# 或使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# 选择 (R)estart
```

#### 方法 3: 如果使用 Windows Service

```powershell
# 重启服务
Restart-Service -Name "AITraderAPI"

# 或使用脚本
# 右键点击 scripts\start_api_service_admin.bat → 以管理员身份运行
# 选择 (R)estart
```

#### 方法 4: 手动重启（开发模式）

**步骤 1: 停止当前 API**
- 如果 API 在终端窗口中运行，按 `Ctrl+C` 停止
- 或关闭运行 API 的终端窗口

**步骤 2: 启动新 API**
```powershell
# 激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 进入后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 验证重启成功

**检查 API 状态**：
```powershell
# 方法 1: 使用检查脚本
.\scripts\check_api_status.ps1

# 方法 2: 手动检查
curl http://localhost:8000/api/health
# 应该返回: {"status": "ok"}

# 方法 3: 访问 API 文档
# 浏览器打开: http://localhost:8000/docs
```

**检查端口占用**：
```powershell
netstat -ano | findstr :8000
# 应该显示端口 8000 被占用
```

### 前端刷新

**重启 API 后，前端需要刷新**：
- 按 `F5` 或 `Ctrl+R` 刷新浏览器页面
- 或关闭并重新打开 `frontend/monitor.html`

**注意**：前端代码修改（`frontend/monitor.html`）只需要刷新浏览器，不需要重启 API。

---

## English Version

### When to Restart API?

**Restart Required**:
- ✅ Modified backend Python code (files in `backend/src/` directory)
- ✅ Modified API endpoints (`backend/src/api/server.py`)
- ✅ Modified data processing logic (files in `backend/src/data/` directory)
- ✅ Modified configuration files (files in `backend/config/` directory)

**Restart NOT Required**:
- ❌ Only modified frontend files (`frontend/` directory) - just refresh browser
- ❌ Only modified documentation (`docs/` directory)
- ❌ Only modified scripts (`scripts/` directory)

### Quick Restart Methods

#### Method 1: Use Fast Restart Script (Recommended)

```powershell
# Run from project root directory
.\scripts\restart_api_fast.ps1
```

**Features**:
- ✅ Automatically stops processes using port 8000
- ✅ Automatically starts new API server (with `--reload` parameter)
- ✅ Runs in new window (doesn't affect current terminal)

#### Method 2: If Using Task Scheduler

```powershell
# Restart task
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"

# Or use script
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# Choose (R)estart
```

#### Method 3: If Using Windows Service

```powershell
# Restart service
Restart-Service -Name "AITraderAPI"

# Or use script
# Right-click scripts\start_api_service_admin.bat → Run as administrator
# Choose (R)estart
```

#### Method 4: Manual Restart (Development Mode)

**Step 1: Stop Current API**
- If API is running in terminal window, press `Ctrl+C` to stop
- Or close the terminal window running the API

**Step 2: Start New API**
```powershell
# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Restart Success

**Check API Status**:
```powershell
# Method 1: Use check script
.\scripts\check_api_status.ps1

# Method 2: Manual check
curl http://localhost:8000/api/health
# Should return: {"status": "ok"}

# Method 3: Access API docs
# Open browser: http://localhost:8000/docs
```

**Check Port Usage**:
```powershell
netstat -ano | findstr :8000
# Should show port 8000 is in use
```

### Frontend Refresh

**After restarting API, frontend needs refresh**:
- Press `F5` or `Ctrl+R` to refresh browser page
- Or close and reopen `frontend/monitor.html`

**Note**: Frontend code changes (`frontend/monitor.html`) only require browser refresh, no API restart needed.

