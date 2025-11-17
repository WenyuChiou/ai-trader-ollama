# 🚀 长期运行指南（数周/数月）

本指南说明如何让 AI-Trader API 服务器在后台持续运行数周甚至数月，包括自动启动、崩溃恢复、日志记录等功能。

---

## 📋 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Task Scheduler** | ✅ 无需额外软件<br>✅ Windows 内置<br>✅ 自动启动<br>✅ 崩溃自动重启 | ⚠️ 需要管理员权限 | ⭐⭐⭐⭐⭐ **最推荐** |
| **Windows Service (NSSM)** | ✅ 专业稳定<br>✅ 系统级服务<br>✅ 自动启动<br>✅ 崩溃自动重启 | ⚠️ 需要安装 NSSM<br>⚠️ 需要管理员权限 | ⭐⭐⭐⭐ |
| **Stable Script** | ✅ 简单易用<br>✅ 自动重启 | ❌ 需要窗口保持打开<br>❌ 系统重启后需手动启动 | ⭐⭐ |

**推荐方案：Task Scheduler（任务计划程序）**

---

## 🎯 方案 1：Task Scheduler（推荐）

### 特点
- ✅ **无需额外软件**：使用 Windows 内置的任务计划程序
- ✅ **自动启动**：系统重启后自动启动
- ✅ **崩溃恢复**：进程崩溃后自动重启
- ✅ **后台运行**：关闭 CMD 后继续运行
- ✅ **日志记录**：自动记录运行日志

### 安装步骤

**步骤 1：以管理员身份运行安装脚本**

**方法 A（最简单）**：
```
1. 找到文件：scripts\start_api_task_admin.bat
2. 右键点击 → "以管理员身份运行"
```

**方法 B（PowerShell）**：
```powershell
# 以管理员身份打开 PowerShell，然后运行：
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
```

**步骤 2：确认安装**

脚本会自动：
- 创建任务计划
- 配置自动启动
- 配置崩溃自动重启
- 设置日志记录

**步骤 3：验证运行**

```powershell
# 检查任务状态
Get-ScheduledTaskInfo -TaskName AITraderAPI

# 检查 API 是否运行
curl http://localhost:8000/api/health
```

### 管理命令

**启动任务**：
```powershell
Start-ScheduledTask -TaskName AITraderAPI
```

**停止任务**：
```powershell
Stop-ScheduledTask -TaskName AITraderAPI
```

**重启任务**：
```powershell
Stop-ScheduledTask -TaskName AITraderAPI
Start-ScheduledTask -TaskName AITraderAPI
```

**查看任务状态**：
```powershell
Get-ScheduledTaskInfo -TaskName AITraderAPI
```

**查看日志**：
```powershell
# 查看最近的日志（最后 50 行）
Get-Content logs\api_task.log -Tail 50

# 查看错误日志
Get-Content logs\api_task_error.log -Tail 50
```

**删除任务**（如果需要）：
```powershell
Unregister-ScheduledTask -TaskName AITraderAPI -Confirm:$false
```

### 配置说明

任务计划程序会自动配置：
- **触发器**：系统启动时自动启动
- **操作**：运行 API 服务器
- **条件**：如果任务失败，立即重新启动（最多 3 次，间隔 1 分钟）
- **设置**：允许任务按需运行，如果任务正在运行则不启动新实例

### 日志位置

- **标准输出日志**：`logs\api_task.log`
- **错误日志**：`logs\api_task_error.log`

---

## 🎯 方案 2：Windows Service (NSSM)

### 特点
- ✅ **系统级服务**：作为 Windows 服务运行
- ✅ **自动启动**：系统启动时自动启动
- ✅ **崩溃恢复**：进程崩溃后自动重启
- ✅ **后台运行**：完全后台运行，无窗口
- ✅ **日志记录**：自动记录运行日志

### 安装步骤

**步骤 1：安装 NSSM（如果未安装）**

```powershell
# 自动安装 NSSM
powershell -ExecutionPolicy Bypass -File .\scripts\install_nssm.ps1
```

或手动安装：
1. 下载 NSSM：https://nssm.cc/download
2. 解压到 `C:\nssm\`

**步骤 2：以管理员身份运行安装脚本**

**方法 A（最简单）**：
```
1. 找到文件：scripts\start_api_service_admin.bat
2. 右键点击 → "以管理员身份运行"
```

**方法 B（PowerShell）**：
```powershell
# 以管理员身份打开 PowerShell，然后运行：
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
```

**步骤 3：验证运行**

```powershell
# 检查服务状态
Get-Service -Name AITraderAPI

# 检查 API 是否运行
curl http://localhost:8000/api/health
```

### 管理命令

**启动服务**：
```powershell
Start-Service -Name AITraderAPI
```

**停止服务**：
```powershell
Stop-Service -Name AITraderAPI
```

**重启服务**：
```powershell
Restart-Service -Name AITraderAPI
```

**查看服务状态**：
```powershell
Get-Service -Name AITraderAPI
```

**查看日志**：
```powershell
# 查看最近的日志（最后 50 行）
Get-Content logs\api_service.log -Tail 50

# 查看错误日志
Get-Content logs\api_service_error.log -Tail 50
```

**删除服务**（如果需要）：
```powershell
# 先停止服务
Stop-Service -Name AITraderAPI

# 删除服务
C:\nssm\nssm.exe remove AITraderAPI confirm
```

### 日志位置

- **标准输出日志**：`logs\api_service.log`
- **错误日志**：`logs\api_service_error.log`

---

## 📊 监控和维护

### 日常检查

**检查 API 是否运行**：
```powershell
# 方法 1：检查服务/任务状态
Get-ScheduledTaskInfo -TaskName AITraderAPI  # Task Scheduler
Get-Service -Name AITraderAPI                # Windows Service

# 方法 2：检查 API 响应
curl http://localhost:8000/api/health

# 方法 3：检查端口占用
netstat -ano | findstr :8000
```

**检查日志**：
```powershell
# 查看最近的日志
Get-Content logs\api_task.log -Tail 50        # Task Scheduler
Get-Content logs\api_service.log -Tail 50     # Windows Service

# 查看错误日志
Get-Content logs\api_task_error.log -Tail 50  # Task Scheduler
Get-Content logs\api_service_error.log -Tail 50 # Windows Service
```

### 自动监控脚本

创建一个简单的监控脚本（可选）：

```powershell
# scripts/check_api_status.ps1
$response = try {
    Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5
} catch {
    $null
}

if ($response -and $response.StatusCode -eq 200) {
    Write-Host "[OK] API is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] API is not responding" -ForegroundColor Red
    # 可以添加自动重启逻辑
}
```

### 定期维护

**每周检查**：
1. 检查日志文件大小（如果太大，考虑清理）
2. 检查磁盘空间
3. 检查 API 响应时间

**每月检查**：
1. 检查系统资源使用（CPU、内存）
2. 检查数据文件大小（`data/logs/`）
3. 备份重要数据

---

## 🔧 故障排除

### 问题 1：任务/服务无法启动

**检查**：
```powershell
# 检查 Python 是否可用
python --version

# 检查项目路径是否正确
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
```

**解决**：
- 确保 Python 已安装并在 PATH 中
- 确保项目路径正确
- 检查虚拟环境（如果使用）

### 问题 2：API 响应慢或无响应

**检查**：
```powershell
# 检查进程
Get-Process python | Where-Object {$_.Path -like "*ai-trader*"}

# 检查端口占用
netstat -ano | findstr :8000
```

**解决**：
- 重启服务/任务
- 检查系统资源（CPU、内存）
- 检查日志中的错误信息

### 问题 3：日志文件过大

**清理日志**：
```powershell
# 备份当前日志
Copy-Item logs\api_task.log logs\api_task_backup_$(Get-Date -Format 'yyyyMMdd').log

# 清空日志（保留文件）
Clear-Content logs\api_task.log
```

### 问题 4：系统重启后服务未启动

**检查**：
```powershell
# Task Scheduler
Get-ScheduledTask -TaskName AITraderAPI | Select-Object State, Settings

# Windows Service
Get-Service -Name AITraderAPI | Select-Object Status, StartType
```

**解决**：
- 确保任务/服务配置为自动启动
- 重新运行安装脚本

---

## 📝 最佳实践

### 1. 定期备份

```powershell
# 备份数据目录
$backupDir = "backups\$(Get-Date -Format 'yyyyMMdd')"
New-Item -ItemType Directory -Path $backupDir -Force
Copy-Item -Path "data\logs\*" -Destination $backupDir -Recurse -Force
```

### 2. 监控磁盘空间

```powershell
# 检查数据目录大小
$dataSize = (Get-ChildItem -Path "data\logs" -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Data directory size: $([math]::Round($dataSize, 2)) GB"
```

### 3. 设置日志轮转

定期清理旧日志，避免占用过多磁盘空间。

### 4. 定期重启

虽然系统会自动重启，但建议每月手动重启一次，确保系统健康。

```powershell
# 重启 Task Scheduler
Stop-ScheduledTask -TaskName AITraderAPI
Start-Sleep -Seconds 5
Start-ScheduledTask -TaskName AITraderAPI

# 或重启 Windows Service
Restart-Service -Name AITraderAPI
```

---

## 🎯 推荐配置（长期运行）

### 最小配置（推荐）

1. **使用 Task Scheduler**（最简单，无需额外软件）
2. **启用自动启动**（系统重启后自动运行）
3. **启用崩溃恢复**（进程崩溃后自动重启）
4. **定期检查日志**（每周一次）

### 完整配置（生产环境）

1. **使用 Windows Service**（更稳定）
2. **启用自动启动**
3. **启用崩溃恢复**
4. **设置日志轮转**（避免日志文件过大）
5. **定期备份数据**（每天或每周）
6. **监控系统资源**（CPU、内存、磁盘）
7. **设置告警**（API 无响应时通知）

---

## 📚 相关文档

- [README.md](../README.md) - 主文档
- [API Server Start Guide](API_SERVER_START_GUIDE.md) - API 服务器启动指南
- [Data Storage Guide](DATA_STORAGE_GUIDE.md) - 数据存储位置指南

---

## ❓ 常见问题

**Q: 系统重启后服务会自动启动吗？**  
A: 是的，如果使用 Task Scheduler 或 Windows Service，系统重启后会自动启动。

**Q: 进程崩溃后会自动重启吗？**  
A: 是的，两种方案都配置了自动重启功能。

**Q: 如何查看运行日志？**  
A: 日志文件位于 `logs\` 目录：
- Task Scheduler: `logs\api_task.log` 和 `logs\api_task_error.log`
- Windows Service: `logs\api_service.log` 和 `logs\api_service_error.log`

**Q: 如何停止服务？**  
A: 
- Task Scheduler: `Stop-ScheduledTask -TaskName AITraderAPI`
- Windows Service: `Stop-Service -Name AITraderAPI`

**Q: 可以同时运行多个实例吗？**  
A: 不建议，可能会导致端口冲突。任务计划程序已配置为"如果任务正在运行则不启动新实例"。

---

**推荐方案：Task Scheduler（任务计划程序）** - 最简单、最稳定、无需额外软件。

