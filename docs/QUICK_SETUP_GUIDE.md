# 🚀 快速设置指南 / Quick Setup Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### 📋 目录

1. [系统安装](#1-系统安装)
2. [后台运行设置](#2-后台运行设置)
3. [数据备份设置](#3-数据备份设置)
4. [验证设置](#4-验证设置)
5. [常见问题](#5-常见问题)

---

## 1. 系统安装

### 前置要求

- ✅ Python 3.10+ 已安装
- ✅ Ollama 已安装并运行
- ✅ 管理员权限（用于设置定时任务）

### 快速安装（3步）

**步骤 1: 安装依赖**
```powershell
# 从项目根目录运行
.\scripts\setup_step1_install_dependencies.ps1
```

**步骤 2: 配置系统**
```powershell
.\scripts\setup_step2_configure.ps1
```

**步骤 3: 启动服务（开发模式）**
```powershell
.\scripts\setup_step3_start_services.ps1
```

**或一键安装所有步骤**:
```powershell
.\scripts\setup_all_steps.ps1
```

---

## 2. 后台运行设置

### 🎯 目标

让系统在后台持续运行，即使关闭命令行窗口也能继续工作。

### 方法 1: Task Scheduler（推荐 - 最简单）

**优点**:
- ✅ 无需安装额外软件
- ✅ 自动启动（系统重启后）
- ✅ 自动重启（崩溃后）
- ✅ 后台运行（关闭窗口仍运行）

**设置步骤**:

1. **右键点击** `scripts\start_api_task_admin.bat`
2. **选择** "以管理员身份运行"
3. **按照提示操作**:
   - 选择 `(I)nstall` 安装定时任务
   - 选择 `(S)tart` 立即启动
   - 选择 `(R)estart` 重启服务

**验证**:
```powershell
# 检查任务状态
Get-ScheduledTask -TaskName "AITraderAPI"

# 查看任务信息
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**管理命令**:
```powershell
# 启动服务
Start-ScheduledTask -TaskName "AITraderAPI"

# 停止服务
Stop-ScheduledTask -TaskName "AITraderAPI"

# 重启服务
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"
```

### 方法 2: Windows Service（更稳定，需要 NSSM）

**优点**:
- ✅ 更稳定
- ✅ 系统级服务
- ✅ 更好的日志管理

**设置步骤**:

1. **右键点击** `scripts\start_api_service_admin.bat`
2. **选择** "以管理员身份运行"
3. 脚本会自动安装 NSSM（如果未安装）
4. 按照提示安装 Windows 服务

**管理命令**:
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

### 方法 3: 开发模式（需要保持窗口打开）

**适用场景**: 开发和调试

```powershell
# 激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 进入后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**注意**: 关闭窗口会停止服务。

---

## 3. 数据备份设置

### 🎯 目标

自动备份关键数据文件，防止数据丢失。

### 快速设置（推荐）

**步骤**:

1. **右键点击** `scripts\setup_daily_backup_admin.bat`
2. **选择** "以管理员身份运行"
3. **输入备份时间**（默认：23:00）
4. **选择是否测试备份**（Y/N）

**完成！** 系统将每天自动备份。

### 手动备份

**运行备份脚本**:
```powershell
python backend/scripts/daily_backup.py
```

### 备份内容

系统会自动备份以下文件：
- ✅ `portfolio_state.json` - 持仓状态
- ✅ `equity_history.jsonl` - 净值历史
- ✅ `discussion_actions.jsonl` - Agent 对话
- ✅ `filled_orders.jsonl` - 已成交订单
- ✅ `pending_orders.jsonl` - 待处理订单
- ✅ `trades.jsonl` - 交易记录
- ✅ `memory/` 目录 - Agent 学习数据

### 备份位置

```
data/backups/
├── 20251120_174635/    # 备份目录（时间戳格式）
│   ├── portfolio_state.json
│   ├── equity_history.jsonl
│   ├── discussion_actions.jsonl
│   ├── filled_orders.jsonl
│   ├── pending_orders.jsonl
│   ├── trades.jsonl
│   ├── memory/         # 记忆系统目录
│   └── manifest.json   # 备份清单
└── ...
```

### 查看备份

```powershell
# 列出所有备份
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending

# 查看最新备份内容
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-ChildItem $latestBackup.FullName
```

### 恢复备份

```powershell
# 使用恢复脚本
.\scripts\restore_portfolio.ps1

# 或手动恢复
$backupDir = "data\backups\20251120_174635"
Copy-Item "$backupDir\portfolio_state.json" "data\logs\portfolio_state.json" -Force
```

### 备份管理

**自动清理**: 系统自动保留最近 7 天的备份

**手动清理**:
```powershell
# 清理 7 天前的备份
.\scripts\cleanup_backups.ps1

# 清理 30 天前的备份
.\scripts\cleanup_backups.ps1 -KeepDays 30
```

---

## 4. 验证设置

### 检查 API 服务

```powershell
# 检查 API 状态
.\scripts\check_api_status.ps1

# 或手动检查
curl http://localhost:8000/api/health
```

**预期输出**: `{"status": "ok"}`

### 检查定时任务

```powershell
# 查看所有 AI Trader 相关任务
Get-ScheduledTask | Where-Object { $_.TaskName -like 'AITrader*' }

# 查看备份任务
Get-ScheduledTask -TaskName "AITrader-DailyBackup"

# 查看 API 任务
Get-ScheduledTask -TaskName "AITraderAPI"
```

### 检查备份

```powershell
# 查看备份目录
Get-ChildItem -Path "data\backups" -Directory

# 查看最新备份清单
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-Content "$($latestBackup.FullName)\manifest.json" | ConvertFrom-Json
```

### 测试备份

```powershell
# 手动运行备份
python backend/scripts/daily_backup.py

# 验证备份文件
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Test-Path "$($latestBackup.FullName)\portfolio_state.json"
```

---

## 5. 常见问题

### Q1: 如何确认 API 在后台运行？

**方法 1: 检查任务状态**
```powershell
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**方法 2: 检查端口**
```powershell
.\scripts\check_port.ps1
# 或
netstat -ano | findstr :8000
```

**方法 3: 访问 API**
- 浏览器打开: http://localhost:8000/docs
- 应该看到 Swagger UI

### Q2: 备份任务没有运行？

**检查任务是否存在**:
```powershell
Get-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**手动运行测试**:
```powershell
Start-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**查看任务历史**:
1. 打开"任务计划程序"（`taskschd.msc`）
2. 找到 `AITrader-DailyBackup`
3. 点击"历史记录"标签

### Q3: 如何停止后台服务？

**Task Scheduler 方式**:
```powershell
Stop-ScheduledTask -TaskName "AITraderAPI"
```

**Windows Service 方式**:
```powershell
Stop-Service -Name "AITraderAPI"
```

**或使用脚本**:
```powershell
.\scripts\stop_all_services.ps1
```

### Q4: 如何查看服务日志？

**Task Scheduler 日志**:
```powershell
Get-Content logs\api_task.log -Tail 50
```

**Windows Service 日志**:
```powershell
Get-Content logs\api_service.log -Tail 50
```

**错误日志**:
```powershell
Get-Content data\logs\error_log.jsonl -Tail 10 | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

### Q5: 系统重启后服务会自动启动吗？

**Task Scheduler**: ✅ 是，如果设置为"登录时运行"

**Windows Service**: ✅ 是，服务会自动启动

**验证**:
```powershell
# 重启后检查
Get-ScheduledTask -TaskName "AITraderAPI"
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

---

## 📚 相关文档

- [备份指南](BACKUP_GUIDE.md) - 详细的备份和恢复说明
- [长期运行指南](LONG_TERM_RUNNING_GUIDE.md) - 长期运行配置
- [故障排除指南](TROUBLESHOOTING.md) - 常见问题解决

---

## English Version

### 📋 Table of Contents

1. [System Installation](#1-system-installation)
2. [Background Running Setup](#2-background-running-setup)
3. [Data Backup Setup](#3-data-backup-setup)
4. [Verify Setup](#4-verify-setup)
5. [FAQ](#5-faq)

---

## 1. System Installation

### Prerequisites

- ✅ Python 3.10+ installed
- ✅ Ollama installed and running
- ✅ Administrator privileges (for scheduled tasks)

### Quick Installation (3 Steps)

**Step 1: Install Dependencies**
```powershell
# Run from project root directory
.\scripts\setup_step1_install_dependencies.ps1
```

**Step 2: Configure System**
```powershell
.\scripts\setup_step2_configure.ps1
```

**Step 3: Start Services (Development Mode)**
```powershell
.\scripts\setup_step3_start_services.ps1
```

**Or run all steps at once**:
```powershell
.\scripts\setup_all_steps.ps1
```

---

## 2. Background Running Setup

### 🎯 Goal

Run the system in the background continuously, even after closing the command window.

### Method 1: Task Scheduler (Recommended - Easiest)

**Advantages**:
- ✅ No additional software needed
- ✅ Auto-start (after system reboot)
- ✅ Auto-restart (after crash)
- ✅ Background running (continues after closing window)

**Setup Steps**:

1. **Right-click** `scripts\start_api_task_admin.bat`
2. **Select** "Run as administrator"
3. **Follow prompts**:
   - Choose `(I)nstall` to install scheduled task
   - Choose `(S)tart` to start immediately
   - Choose `(R)estart` to restart service

**Verify**:
```powershell
# Check task status
Get-ScheduledTask -TaskName "AITraderAPI"

# View task info
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**Management Commands**:
```powershell
# Start service
Start-ScheduledTask -TaskName "AITraderAPI"

# Stop service
Stop-ScheduledTask -TaskName "AITraderAPI"

# Restart service
Stop-ScheduledTask -TaskName "AITraderAPI"
Start-ScheduledTask -TaskName "AITraderAPI"
```

### Method 2: Windows Service (More Stable, Requires NSSM)

**Advantages**:
- ✅ More stable
- ✅ System-level service
- ✅ Better log management

**Setup Steps**:

1. **Right-click** `scripts\start_api_service_admin.bat`
2. **Select** "Run as administrator"
3. Script will auto-install NSSM if not found
4. Follow prompts to install Windows service

**Management Commands**:
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

### Method 3: Development Mode (Requires Window Open)

**Use Case**: Development and debugging

```powershell
# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Note**: Closing the window will stop the service.

---

## 3. Data Backup Setup

### 🎯 Goal

Automatically backup critical data files to prevent data loss.

### Quick Setup (Recommended)

**Steps**:

1. **Right-click** `scripts\setup_daily_backup_admin.bat`
2. **Select** "Run as administrator"
3. **Enter backup time** (default: 23:00)
4. **Choose whether to test backup** (Y/N)

**Done!** System will automatically backup daily.

### Manual Backup

**Run Backup Script**:
```powershell
python backend/scripts/daily_backup.py
```

### Backup Contents

System automatically backs up:
- ✅ `portfolio_state.json` - Portfolio state
- ✅ `equity_history.jsonl` - Equity history
- ✅ `discussion_actions.jsonl` - Agent conversations
- ✅ `filled_orders.jsonl` - Filled orders
- ✅ `pending_orders.jsonl` - Pending orders
- ✅ `trades.jsonl` - Trade records
- ✅ `memory/` directory - Agent learning data

### Backup Location

```
data/backups/
├── 20251120_174635/    # Backup directory (timestamp format)
│   ├── portfolio_state.json
│   ├── equity_history.jsonl
│   ├── discussion_actions.jsonl
│   ├── filled_orders.jsonl
│   ├── pending_orders.jsonl
│   ├── trades.jsonl
│   ├── memory/         # Memory system directory
│   └── manifest.json   # Backup manifest
└── ...
```

### View Backups

```powershell
# List all backups
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending

# View latest backup contents
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-ChildItem $latestBackup.FullName
```

### Restore Backup

```powershell
# Use restore script
.\scripts\restore_portfolio.ps1

# Or manually restore
$backupDir = "data\backups\20251120_174635"
Copy-Item "$backupDir\portfolio_state.json" "data\logs\portfolio_state.json" -Force
```

### Backup Management

**Auto-cleanup**: System automatically keeps last 7 days of backups

**Manual Cleanup**:
```powershell
# Cleanup backups older than 7 days
.\scripts\cleanup_backups.ps1

# Cleanup backups older than 30 days
.\scripts\cleanup_backups.ps1 -KeepDays 30
```

---

## 4. Verify Setup

### Check API Service

```powershell
# Check API status
.\scripts\check_api_status.ps1

# Or manually check
curl http://localhost:8000/api/health
```

**Expected Output**: `{"status": "ok"}`

### Check Scheduled Tasks

```powershell
# View all AI Trader related tasks
Get-ScheduledTask | Where-Object { $_.TaskName -like 'AITrader*' }

# View backup task
Get-ScheduledTask -TaskName "AITrader-DailyBackup"

# View API task
Get-ScheduledTask -TaskName "AITraderAPI"
```

### Check Backups

```powershell
# View backup directory
Get-ChildItem -Path "data\backups" -Directory

# View latest backup manifest
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-Content "$($latestBackup.FullName)\manifest.json" | ConvertFrom-Json
```

### Test Backup

```powershell
# Manually run backup
python backend/scripts/daily_backup.py

# Verify backup files
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Test-Path "$($latestBackup.FullName)\portfolio_state.json"
```

---

## 5. FAQ

### Q1: How to confirm API is running in background?

**Method 1: Check Task Status**
```powershell
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

**Method 2: Check Port**
```powershell
.\scripts\check_port.ps1
# Or
netstat -ano | findstr :8000
```

**Method 3: Access API**
- Open browser: http://localhost:8000/docs
- Should see Swagger UI

### Q2: Backup task not running?

**Check if task exists**:
```powershell
Get-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**Manually test run**:
```powershell
Start-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**View task history**:
1. Open "Task Scheduler" (`taskschd.msc`)
2. Find `AITrader-DailyBackup`
3. Click "History" tab

### Q3: How to stop background service?

**Task Scheduler Method**:
```powershell
Stop-ScheduledTask -TaskName "AITraderAPI"
```

**Windows Service Method**:
```powershell
Stop-Service -Name "AITraderAPI"
```

**Or use script**:
```powershell
.\scripts\stop_all_services.ps1
```

### Q4: How to view service logs?

**Task Scheduler Logs**:
```powershell
Get-Content logs\api_task.log -Tail 50
```

**Windows Service Logs**:
```powershell
Get-Content logs\api_service.log -Tail 50
```

**Error Logs**:
```powershell
Get-Content data\logs\error_log.jsonl -Tail 10 | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

### Q5: Will service auto-start after system reboot?

**Task Scheduler**: ✅ Yes, if configured to run on logon

**Windows Service**: ✅ Yes, service auto-starts

**Verify**:
```powershell
# Check after reboot
Get-ScheduledTask -TaskName "AITraderAPI"
Get-ScheduledTaskInfo -TaskName "AITraderAPI"
```

---

## 📚 Related Documentation

- [Backup Guide](BACKUP_GUIDE.md) - Detailed backup and restore instructions
- [Long-term Running Guide](LONG_TERM_RUNNING_GUIDE.md) - Long-term running configuration
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issue resolution

