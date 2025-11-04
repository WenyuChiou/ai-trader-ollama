# 清空测试数据指南

## 概述

此功能用于清空所有测试文件和记录，将系统重置为初始状态，便于开始新的实时交易测试。

## 使用方法

### 方法1: Python脚本（推荐）

```powershell
cd backend
python scripts\clear_test_data.py
```

### 方法2: PowerShell脚本

```powershell
cd backend
.\scripts\clear_test_data.ps1
```

## 清空的内容

### 1. JSONL日志文件
- ✅ `discussion_actions.jsonl` - Agent对话记录
- ✅ `trades.jsonl` - 交易记录
- ✅ `filled_orders.jsonl` - 已成交订单
- ✅ `pending_orders.jsonl` - 待处理订单
- ✅ `real_time_snapshots.jsonl` - 实时快照
- ✅ `equity_history.jsonl` - 净值历史
- ✅ `events.jsonl` - 事件记录

### 2. 投资组合状态
- ✅ `portfolio_state.json` - 重置为初始状态
  - 现金: $10,000
  - 初始价值: $10,000
  - 持仓: 空

### 3. 交易日锁定
- ✅ `last_trade_date.txt` - 删除，解除锁定

### 4. 记忆文件
- ✅ `memory/daily/*.json` - 删除所有每日记忆
- ✅ `memory/weekly/*.jsonl` - 删除所有每周记忆
- ✅ `memory/index/daily_index.json` - 重置索引

### 5. 演示数据
- ✅ `demo_prices.json` - 删除演示价格数据

### 6. 执行日志
- ✅ `api_execution.log` - 保留最后100行（作为备份）

## 重置后的状态

清空完成后，系统将处于以下状态：

```
投资组合:
  - 现金: $10,000
  - 持仓: 无
  - 总价值: $10,000

交易记录:
  - 无交易记录
  - 无订单记录

对话记录:
  - 无Agent对话记录

记忆:
  - 无历史记忆
  - 索引已重置

锁定:
  - 交易日锁定已解除
```

## 注意事项

⚠️ **警告**: 清空操作**不可逆**，所有测试数据将被永久删除！

建议：
- 在清空前，如果需要保留数据，请先备份 `backend/data/logs` 目录
- 清空后，系统将从零开始，适合进行新的实时交易测试

## 备份数据（可选）

如果需要备份数据，可以运行：

```powershell
# 创建备份目录
$backupDir = "backend\data\logs_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir

# 复制所有文件
Copy-Item -Path "backend\data\logs\*" -Destination $backupDir -Recurse -Force

Write-Host "备份完成: $backupDir"
```

## 验证清空结果

清空后可以验证：

```powershell
# 检查portfolio状态
Get-Content backend\data\logs\portfolio_state.json

# 检查日志文件是否为空
Get-ChildItem backend\data\logs\*.jsonl | ForEach-Object {
    $lines = (Get-Content $_.FullName -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
    Write-Host "$($_.Name): $lines lines"
}
```

## 开始新的实时交易

清空完成后，可以：

1. 重启后端API（如果正在运行）
2. 打开前端页面
3. 点击 "▶️ Start Trading" 开始实时交易
4. 系统将使用 yfinance 当前数据进行交易

