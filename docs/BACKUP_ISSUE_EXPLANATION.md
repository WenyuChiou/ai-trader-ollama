# 备份问题说明

## 问题发现

用户发现恢复的持仓（CSCO, CRWD, AZN, PLTR, MSFT, GILD, MU, AMAT, PEP, PANW, TSLA, NVDA, AVGO, CEG, AMGN）不是今天的持仓。

## 问题原因

### 1. 备份机制的限制

**备份只在以下情况创建**：
- 调用 `/api/system/init?force=true` 时
- 不会在每次交易后自动备份

**问题**：
- 如果今天没有调用 `init`，就不会有今天的备份
- 恢复时只能找到旧的备份文件（11月16-17日）
- 恢复的是旧数据，不是今天的持仓

### 2. 备份文件时间戳

检查发现：
- 最新备份：`portfolio_state_backup_20251116_192432.json`（11月17日的数据）
- 恢复前的状态：`portfolio_state_backup_before_restore_20251118_185826.json`（空的，没有持仓）
- **没有11月18日的备份文件**

### 3. 正确的数据源

**`equity_history.jsonl` 包含正确的持仓信息**：
- 每30分钟自动记录一次（市场开盘时）
- 包含完整的持仓信息（symbol, quantity, avg_cost, total_cost）
- 11月18日的记录显示持仓是：**PSQ, BKR, MAR, SPXL, NVDA, AMZN, TQQQ, TSLA, AAPL, SQQQ**

## 解决方案

### 方案1: 从equity_history恢复（推荐）

使用新创建的脚本：
```powershell
# 恢复最新持仓
powershell -ExecutionPolicy Bypass -File .\scripts\restore_from_equity_history.ps1

# 恢复指定日期的持仓
powershell -ExecutionPolicy Bypass -File .\scripts\restore_from_equity_history.ps1 -Date "2025-11-18"
```

### 方案2: 改进备份机制

**建议改进**：
1. 每次保存 `portfolio_state.json` 时自动创建备份
2. 或者每天自动备份一次
3. 保留最近7天的备份

## 恢复的持仓（11月18日）

从 `equity_history.jsonl` 恢复的正确持仓：
- **PSQ**: 36 shares @ $31.03
- **BKR**: 22 shares @ $47.90
- **MAR**: 3 shares @ $282.86
- **SPXL**: 5 shares @ $206.63
- **NVDA**: 5 shares @ $183.32
- **AMZN**: 4 shares @ $228.35
- **TQQQ**: 10 shares @ $100.16
- **TSLA**: 2 shares @ $402.94
- **AAPL**: 4 shares @ $268.35
- **SQQQ**: 78 shares @ $15.21

**现金**: $13.20  
**总价值**: $9,997.48

## 预防措施

1. **定期检查备份**：确保有最新的备份文件
2. **使用equity_history恢复**：如果备份丢失，可以从equity_history恢复
3. **改进备份机制**：建议实现自动备份功能

## 相关文件

- `scripts/restore_from_equity_history.ps1` - 从equity_history恢复持仓
- `scripts/restore_portfolio.ps1` - 从备份文件恢复持仓
- `data/logs/equity_history.jsonl` - 净值历史记录（包含持仓信息）

