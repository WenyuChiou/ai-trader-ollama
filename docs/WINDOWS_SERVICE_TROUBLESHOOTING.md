# Windows Service 故障排除指南 / Troubleshooting Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### ⚠️ 常见问题

#### 问题 1: 服务无法启动 - "无法啟動服務"

**症状**：
```
Start-Service : 無法啟動服務 'AITraderAPI (AITraderAPI)'
```

**可能原因**：
1. 服务配置损坏
2. Python 路径不正确
3. 工作目录设置错误
4. 端口被占用

**解决方法**：

**方法 1: 重新安装服务**
```powershell
# 1. 删除现有服务
scripts\fix_api_service.ps1

# 2. 重新安装
scripts\start_api_service_admin.bat
```

**方法 2: 使用 Task Scheduler（推荐）**
```powershell
# Task Scheduler 更简单可靠
scripts\start_api_task_admin.bat
```

**方法 3: 手动删除服务**
```powershell
# 停止服务
sc.exe stop AITraderAPI

# 删除服务
sc.exe delete AITraderAPI

# 然后重新安装
scripts\start_api_service_admin.bat
```

---

#### 问题 2: 服务状态显示为 "Paused"

**症状**：
- PowerShell 显示服务为 "Running"
- NSSM 显示服务为 "SERVICE_PAUSED"
- 无法启动或恢复服务

**解决方法**：

```powershell
# 1. 强制停止服务
sc.exe stop AITraderAPI

# 2. 删除服务
sc.exe delete AITraderAPI

# 3. 重新安装
scripts\start_api_service_admin.bat
```

---

#### 问题 3: NSSM 无法打开服务

**症状**：
```
Can't open service!
OpenService(): Access Denied
```

**解决方法**：

1. **确保以管理员身份运行**：
   ```powershell
   # 右键点击脚本，选择"以管理员身份运行"
   scripts\start_api_service_admin.bat
   ```

2. **检查服务是否存在**：
   ```powershell
   Get-Service -Name "AITraderAPI"
   ```

3. **使用 sc.exe 删除服务**：
   ```powershell
   sc.exe delete AITraderAPI
   ```

---

#### 问题 4: Python 路径错误

**症状**：
- 服务无法启动
- 日志显示 "Python not found"

**解决方法**：

```powershell
# 1. 检查 Python 路径
python --version

# 2. 检查虚拟环境
Test-Path ".venv\Scripts\python.exe"

# 3. 重新安装服务（会自动检测正确的 Python）
scripts\start_api_service_admin.bat
```

---

#### 问题 5: 端口被占用

**症状**：
- 服务启动失败
- 错误信息提到端口 8000

**解决方法**：

```powershell
# 1. 检查端口占用
netstat -ano | findstr :8000

# 2. 停止占用端口的进程
Stop-Process -Id <PID> -Force

# 3. 重新启动服务
Start-Service -Name "AITraderAPI"
```

---

### 🔧 诊断步骤

#### 步骤 1: 检查服务状态

```powershell
Get-Service -Name "AITraderAPI"
```

#### 步骤 2: 检查服务配置

```powershell
$nssmPath = "tools\nssm\nssm.exe"
& $nssmPath get AITraderAPI Application
& $nssmPath get AITraderAPI AppParameters
& $nssmPath get AITraderAPI AppDirectory
```

#### 步骤 3: 检查日志

```powershell
# 输出日志
Get-Content "logs\api_service.log" -Tail 50

# 错误日志
Get-Content "logs\api_service_error.log" -Tail 50
```

#### 步骤 4: 检查 Windows 事件日志

```powershell
Get-EventLog -LogName Application -Source "AITraderAPI" -Newest 10
```

---

### 💡 推荐解决方案

**如果 Windows Service 持续出现问题，建议使用 Task Scheduler**：

**优点**：
- ✅ 更简单可靠
- ✅ 无需额外软件（NSSM）
- ✅ 配置更直观
- ✅ 更容易调试

**切换方法**：
```powershell
# 1. 删除 Windows Service（如果存在）
scripts\fix_api_service.ps1

# 2. 安装 Task Scheduler
scripts\start_api_task_admin.bat
```

---

### 📋 完整重置步骤

如果所有方法都失败，可以完全重置：

```powershell
# 1. 停止并删除服务
sc.exe stop AITraderAPI
sc.exe delete AITraderAPI

# 2. 删除 Task Scheduler 任务（如果存在）
Unregister-ScheduledTask -TaskName "AITraderAPI" -Confirm:$false

# 3. 重新安装（选择 Task Scheduler 或 Windows Service）
scripts\start_api_task_admin.bat
# 或
scripts\start_api_service_admin.bat
```

---

## English Version

### ⚠️ Common Issues

#### Issue 1: Service Won't Start - "Cannot Start Service"

**Symptoms**:
```
Start-Service : Cannot start service 'AITraderAPI (AITraderAPI)'
```

**Possible Causes**:
1. Service configuration corrupted
2. Incorrect Python path
3. Wrong working directory
4. Port already in use

**Solutions**:

**Method 1: Reinstall Service**
```powershell
# 1. Remove existing service
scripts\fix_api_service.ps1

# 2. Reinstall
scripts\start_api_service_admin.bat
```

**Method 2: Use Task Scheduler (Recommended)**
```powershell
# Task Scheduler is simpler and more reliable
scripts\start_api_task_admin.bat
```

**Method 3: Manual Removal**
```powershell
# Stop service
sc.exe stop AITraderAPI

# Delete service
sc.exe delete AITraderAPI

# Then reinstall
scripts\start_api_service_admin.bat
```

---

#### Issue 2: Service Status Shows "Paused"

**Symptoms**:
- PowerShell shows service as "Running"
- NSSM shows service as "SERVICE_PAUSED"
- Cannot start or resume service

**Solution**:

```powershell
# 1. Force stop service
sc.exe stop AITraderAPI

# 2. Delete service
sc.exe delete AITraderAPI

# 3. Reinstall
scripts\start_api_service_admin.bat
```

---

#### Issue 3: NSSM Cannot Open Service

**Symptoms**:
```
Can't open service!
OpenService(): Access Denied
```

**Solution**:

1. **Ensure running as administrator**:
   ```powershell
   # Right-click script, select "Run as administrator"
   scripts\start_api_service_admin.bat
   ```

2. **Check if service exists**:
   ```powershell
   Get-Service -Name "AITraderAPI"
   ```

3. **Use sc.exe to delete service**:
   ```powershell
   sc.exe delete AITraderAPI
   ```

---

#### Issue 4: Python Path Error

**Symptoms**:
- Service won't start
- Logs show "Python not found"

**Solution**:

```powershell
# 1. Check Python path
python --version

# 2. Check virtual environment
Test-Path ".venv\Scripts\python.exe"

# 3. Reinstall service (will auto-detect correct Python)
scripts\start_api_service_admin.bat
```

---

#### Issue 5: Port Already in Use

**Symptoms**:
- Service startup fails
- Error mentions port 8000

**Solution**:

```powershell
# 1. Check port usage
netstat -ano | findstr :8000

# 2. Stop process using port
Stop-Process -Id <PID> -Force

# 3. Restart service
Start-Service -Name "AITraderAPI"
```

---

### 🔧 Diagnostic Steps

#### Step 1: Check Service Status

```powershell
Get-Service -Name "AITraderAPI"
```

#### Step 2: Check Service Configuration

```powershell
$nssmPath = "tools\nssm\nssm.exe"
& $nssmPath get AITraderAPI Application
& $nssmPath get AITraderAPI AppParameters
& $nssmPath get AITraderAPI AppDirectory
```

#### Step 3: Check Logs

```powershell
# Output log
Get-Content "logs\api_service.log" -Tail 50

# Error log
Get-Content "logs\api_service_error.log" -Tail 50
```

#### Step 4: Check Windows Event Log

```powershell
Get-EventLog -LogName Application -Source "AITraderAPI" -Newest 10
```

---

### 💡 Recommended Solution

**If Windows Service continues to have issues, consider using Task Scheduler**:

**Advantages**:
- ✅ Simpler and more reliable
- ✅ No additional software (NSSM) needed
- ✅ More intuitive configuration
- ✅ Easier to debug

**Switch Method**:
```powershell
# 1. Remove Windows Service (if exists)
scripts\fix_api_service.ps1

# 2. Install Task Scheduler
scripts\start_api_task_admin.bat
```

---

### 📋 Complete Reset Steps

If all methods fail, you can completely reset:

```powershell
# 1. Stop and delete service
sc.exe stop AITraderAPI
sc.exe delete AITraderAPI

# 2. Delete Task Scheduler task (if exists)
Unregister-ScheduledTask -TaskName "AITraderAPI" -Confirm:$false

# 3. Reinstall (choose Task Scheduler or Windows Service)
scripts\start_api_task_admin.bat
# or
scripts\start_api_service_admin.bat
```

