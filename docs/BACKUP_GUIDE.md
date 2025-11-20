# 📦 数据备份指南 / Data Backup Guide

**Language**: [中文](#中文版) | [English](#english-version)

---

## 中文版

### 概述

数据备份是长期自动交易系统的重要组成部分。本指南介绍如何使用系统的备份功能来保护您的交易数据。

### 为什么需要备份？

- **数据安全**: 保护持仓、交易记录和净值历史
- **灾难恢复**: 系统故障或数据损坏时可以恢复
- **历史记录**: 保留完整的交易历史用于分析
- **长期运行**: 确保系统可以持续稳定运行

### 备份内容

系统会自动备份以下关键文件：

1. **持仓状态**: `portfolio_state.json` - 当前持仓、现金余额
2. **净值历史**: `equity_history.jsonl` - 净值变化记录
3. **对话记录**: `discussion_actions.jsonl` - Agent 分析和讨论
4. **交易记录**: `filled_orders.jsonl`, `pending_orders.jsonl`, `trades.jsonl`
5. **记忆系统**: `memory/` 目录 - Agent 学习数据

### 备份方式

#### 方式 1: 自动每日备份（推荐）

**设置定时任务**:
```powershell
# 方法 1: 使用批处理文件（推荐）
# 右键点击 scripts\setup_daily_backup_admin.bat
# 选择"以管理员身份运行"

# 方法 2: 直接运行 PowerShell 脚本
powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_backup.ps1
```

**设置步骤**:
1. 右键点击 `scripts\setup_daily_backup.ps1`
2. 选择"以管理员身份运行"
3. 输入备份时间（默认：23:00）
4. 系统会自动创建 Windows 定时任务

**任务名称**: `AITrader-DailyBackup`

**特点**:
- ✅ 每天自动备份（默认 23:00）
- ✅ 自动清理旧备份（保留最近 7 天）
- ✅ 创建备份清单（manifest.json）
- ✅ 无需手动操作

#### 方式 2: 手动备份

**运行备份脚本**:
```powershell
python backend/scripts/daily_backup.py
```

**输出示例**:
```
================================================================================
📦 Daily Backup Script
================================================================================

Logs directory: C:\Users\...\data\logs
Backup directory: C:\Users\...\data\backups\20251120_174635

Backing up critical files...
  ✅ Backed up: portfolio_state.json (1,558 bytes)
  ✅ Backed up: equity_history.jsonl (41,701 bytes)
  ✅ Backed up: discussion_actions.jsonl (2,920,868 bytes)
  ✅ Backed up: filled_orders.jsonl (9,964 bytes)
  ✅ Backed up: pending_orders.jsonl (0 bytes)

Backing up critical directories...
  ✅ Backed up directory: memory

Creating backup manifest...
  ✅ Created backup manifest: manifest.json

Cleaning up old backups (keeping last 7 days)...

================================================================================
✅ Backup Complete!
   Backup location: C:\Users\...\data\backups\20251120_174635
   Files backed up: 5
   Directories backed up: 1
================================================================================
```

#### 方式 3: PowerShell 备份脚本

**使用旧版备份脚本**:
```powershell
.\scripts\backup_data.ps1
```

**特点**:
- 创建时间戳备份目录
- 备份所有关键文件
- 创建备份清单

### 备份位置

**备份目录结构**:
```
data/backups/
├── 20251120_174635/          # 备份目录（时间戳格式：YYYYMMDD_HHMMSS）
│   ├── portfolio_state.json
│   ├── equity_history.jsonl
│   ├── discussion_actions.jsonl
│   ├── filled_orders.jsonl
│   ├── pending_orders.jsonl
│   ├── trades.jsonl
│   ├── memory/               # 记忆系统目录
│   │   ├── daily/
│   │   ├── weekly/
│   │   ├── monthly/
│   │   └── index/
│   └── manifest.json         # 备份清单
├── 20251119_230000/
└── 20251118_230000/
```

### 备份清单（Manifest）

每个备份都包含 `manifest.json` 文件，记录备份信息：

```json
{
  "timestamp": "2025-11-20T17:46:35.123456",
  "date": "2025-11-20 17:46:35",
  "backup_type": "daily",
  "files": [
    "portfolio_state.json",
    "equity_history.jsonl",
    "discussion_actions.jsonl",
    "filled_orders.jsonl",
    "pending_orders.jsonl"
  ],
  "directories": [
    "memory"
  ],
  "backup_location": "data/backups/20251120_174635"
}
```

### 查看备份

**列出所有备份**:
```powershell
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending
```

**查看最新备份内容**:
```powershell
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-ChildItem $latestBackup.FullName
```

**查看备份清单**:
```powershell
$latestBackup = Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-Content "$($latestBackup.FullName)\manifest.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 恢复备份

#### 恢复持仓状态

**使用恢复脚本**:
```powershell
.\scripts\restore_portfolio.ps1
```

**手动恢复**:
```powershell
# 1. 查看可用备份
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending

# 2. 选择备份目录（例如：20251120_174635）
$backupDir = "data\backups\20251120_174635"

# 3. 恢复 portfolio_state.json
Copy-Item "$backupDir\portfolio_state.json" "data\logs\portfolio_state.json" -Force

# 4. 恢复其他文件（可选）
Copy-Item "$backupDir\equity_history.jsonl" "data\logs\equity_history.jsonl" -Force
Copy-Item "$backupDir\discussion_actions.jsonl" "data\logs\discussion_actions.jsonl" -Force
```

#### 恢复记忆系统

```powershell
# 恢复 memory 目录
$backupDir = "data\backups\20251120_174635"
Remove-Item "data\logs\memory" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "$backupDir\memory" "data\logs\memory" -Recurse -Force
```

### 备份管理

#### 清理旧备份

**自动清理**:
- 每日备份脚本会自动清理 7 天前的备份
- 无需手动操作

**手动清理**:
```powershell
# 清理 7 天前的备份
.\scripts\cleanup_backups.ps1

# 清理 30 天前的备份
.\scripts\cleanup_backups.ps1 -KeepDays 30

# 删除所有备份（谨慎使用）
.\scripts\cleanup_backups.ps1 -KeepDays 0
```

#### 管理定时任务

**查看定时任务**:
```powershell
Get-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**运行定时任务**:
```powershell
Start-ScheduledTask -TaskName "AITrader-DailyBackup"
```

**删除定时任务**:
```powershell
Unregister-ScheduledTask -TaskName "AITrader-DailyBackup" -Confirm:$false
```

### 最佳实践

1. **设置自动备份**: 使用定时任务确保每天自动备份
2. **定期检查备份**: 每周检查备份是否正常创建
3. **保留多个备份**: 系统自动保留最近 7 天的备份
4. **重要操作前备份**: 在系统初始化或重大操作前手动备份
5. **验证备份完整性**: 定期检查备份文件是否完整

### 故障排除

**备份失败**:
- 检查磁盘空间是否充足
- 检查文件权限
- 查看错误日志：`data/logs/error_log.jsonl`

**找不到备份**:
- 检查备份目录：`data/backups/`
- 确认备份时间设置正确
- 检查定时任务是否正常运行

**恢复失败**:
- 确认备份文件存在
- 检查文件权限
- 查看错误日志

---

## English Version

### Overview

Data backup is an essential component of long-term auto trading systems. This guide explains how to use the system's backup functionality to protect your trading data.

### Why Backup?

- **Data Security**: Protect positions, trade records, and equity history
- **Disaster Recovery**: Recover from system failures or data corruption
- **Historical Records**: Preserve complete trading history for analysis
- **Long-term Operation**: Ensure continuous stable operation

### What Gets Backed Up

The system automatically backs up the following critical files:

1. **Portfolio State**: `portfolio_state.json` - Current positions, cash balance
2. **Equity History**: `equity_history.jsonl` - Net value change records
3. **Conversations**: `discussion_actions.jsonl` - Agent analysis and discussions
4. **Trade Records**: `filled_orders.jsonl`, `pending_orders.jsonl`, `trades.jsonl`
5. **Memory System**: `memory/` directory - Agent learning data

### Backup Methods

#### Method 1: Automated Daily Backup (Recommended)

**Setup Scheduled Task**:
```powershell
# Method 1: Use batch file (Recommended)
# Right-click scripts\setup_daily_backup_admin.bat
# Select "Run as administrator"

# Method 2: Run PowerShell script directly
powershell -ExecutionPolicy Bypass -File .\scripts\setup_daily_backup.ps1
```

**Setup Steps**:
1. Right-click `scripts\setup_daily_backup.ps1`
2. Select "Run as administrator"
3. Enter backup time (default: 23:00)
4. System automatically creates Windows scheduled task

**Task Name**: `AITrader-DailyBackup`

**Features**:
- ✅ Automatic daily backup (default: 23:00)
- ✅ Auto-cleanup of old backups (keeps last 7 days)
- ✅ Creates backup manifest (manifest.json)
- ✅ No manual intervention required

#### Method 2: Manual Backup

**Run Backup Script**:
```powershell
python backend/scripts/daily_backup.py
```

#### Method 3: PowerShell Backup Script

**Use Legacy Backup Script**:
```powershell
.\scripts\backup_data.ps1
```

### Backup Location

**Backup Directory Structure**:
```
data/backups/
├── 20251120_174635/          # Backup directory (timestamp format: YYYYMMDD_HHMMSS)
│   ├── portfolio_state.json
│   ├── equity_history.jsonl
│   ├── discussion_actions.jsonl
│   ├── filled_orders.jsonl
│   ├── pending_orders.jsonl
│   ├── trades.jsonl
│   ├── memory/               # Memory system directory
│   └── manifest.json         # Backup manifest
├── 20251119_230000/
└── 20251118_230000/
```

### Restore Backup

**Restore Portfolio State**:
```powershell
.\scripts\restore_portfolio.ps1
```

**Manual Restore**:
```powershell
# 1. List available backups
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending

# 2. Select backup directory (e.g., 20251120_174635)
$backupDir = "data\backups\20251120_174635"

# 3. Restore portfolio_state.json
Copy-Item "$backupDir\portfolio_state.json" "data\logs\portfolio_state.json" -Force
```

### Best Practices

1. **Setup Automatic Backup**: Use scheduled tasks to ensure daily automatic backup
2. **Regular Backup Check**: Check weekly that backups are being created
3. **Keep Multiple Backups**: System automatically keeps last 7 days of backups
4. **Backup Before Important Operations**: Manually backup before system initialization or major operations
5. **Verify Backup Integrity**: Regularly check that backup files are complete

---

**Related Documentation**:
- [Portfolio Restore Guide](docs/PORTFOLIO_RESTORE.md) - Detailed restore instructions
- [Long-term Running Guide](docs/LONG_TERM_RUNNING_GUIDE.md) - Long-term operation guide

