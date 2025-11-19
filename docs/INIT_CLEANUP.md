# 初始化清理说明

## 问题

初始化后，`data/logs` 目录下可能还有残留的非文件夹文件：
- 备份文件 (`portfolio_state_backup_*.json`)
- `.gitkeep` 文件（应该保留）

## 初始化逻辑

### 删除的文件

初始化时会删除以下文件：
- `portfolio_state.json` - 持仓状态
- `pending_orders.jsonl` - 待处理订单
- `filled_orders.jsonl` - 已成交订单
- `equity_history.jsonl` - 净值历史
- `discussion_actions.jsonl` - 对话记录

### 保留的文件/目录

以下内容会被保留：
- `memory/` 目录 - Agent学习数据（重要！）
- `.gitkeep` 文件 - Git占位文件（应该保留）
- **备份文件** - 默认保留（但会清理7天前的旧备份）

### 备份文件清理

**自动清理**：
- 初始化时自动删除**所有旧的备份文件**
- 只保留刚创建的新备份（如果有持仓的话）
- 确保初始化后目录干净，只保留最新的备份

**手动清理**：

**方法1: 删除所有备份（最简单）**
```powershell
# 删除所有备份文件
powershell -ExecutionPolicy Bypass -File .\scripts\delete_all_backups.ps1
```

**方法2: 按天数清理备份**
```powershell
# 清理7天前的备份（默认）
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1

# 清理30天前的备份
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1 -KeepDays 30

# 删除所有备份（KeepDays=0）
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_backups.ps1 -KeepDays 0
```

## 备份文件说明

### 备份文件类型

1. **自动备份** (`portfolio_state_backup_YYYYMMDD_HHMMSS.json`)
   - 调用 `/api/system/init?force=true` 时自动创建
   - 备份当前的 `portfolio_state.json`

2. **恢复前备份** (`portfolio_state_backup_before_restore_*.json`)
   - 使用恢复脚本时自动创建
   - 备份恢复前的状态

3. **恢复前备份（equity）** (`portfolio_state_backup_before_equity_restore_*.json`)
   - 从equity_history恢复时自动创建

### 备份文件用途

- **恢复持仓**: 如果持仓被意外清空，可以从备份恢复
- **数据安全**: 提供数据恢复的保障
- **历史记录**: 保留历史状态快照

## 清理建议

### 何时清理

1. **定期清理**: 每月清理一次旧备份（>30天）
2. **空间不足**: 如果磁盘空间不足，可以清理旧备份
3. **初始化后**: 初始化时会自动清理7天前的备份

### 清理策略

- **保留最近7天**: 默认策略（自动）
- **保留最近30天**: 如果需要更长的历史记录
- **全部清理**: 不推荐，除非确定不需要恢复

## 注意事项

1. **不要删除 `.gitkeep`**: 这是Git占位文件，应该保留
2. **不要删除 `memory/` 目录**: 包含Agent学习数据，删除会影响Agent性能
3. **备份文件有用**: 在需要恢复数据时很有用，不要全部删除
4. **检查备份时间**: 删除前检查备份文件的时间，确保不会删除有用的备份

## 相关脚本

- `scripts/cleanup_backups.ps1` - 手动清理备份文件
- `scripts/restore_portfolio.ps1` - 从备份恢复持仓
- `scripts/restore_from_equity_history.ps1` - 从equity_history恢复持仓

