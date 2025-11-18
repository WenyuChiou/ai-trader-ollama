# 持仓恢复指南

## 问题
如果持仓被测试或初始化操作清空，可以使用备份文件恢复。

## 自动备份
系统在以下情况会自动创建备份：
1. **初始化时**：调用 `/api/system/init?force=true` 时会自动备份 `portfolio_state.json`
2. **恢复前**：使用恢复脚本时会先备份当前状态

## 备份文件位置
```
data/logs/portfolio_state_backup_YYYYMMDD_HHMMSS.json
```

## 恢复方法

### 方法 1: 使用恢复脚本（推荐）

```powershell
# 恢复最新备份
powershell -ExecutionPolicy Bypass -File .\scripts\restore_portfolio.ps1

# 恢复指定备份
powershell -ExecutionPolicy Bypass -File .\scripts\restore_portfolio.ps1 -BackupFile "portfolio_state_backup_20251116_192432.json"
```

### 方法 2: 手动恢复

1. **查看可用备份**：
```powershell
Get-ChildItem -Path "data/logs" -Filter "*portfolio_state_backup*.json" | Sort-Object LastWriteTime -Descending
```

2. **备份当前状态**（可选但推荐）：
```powershell
Copy-Item "data/logs/portfolio_state.json" "data/logs/portfolio_state_backup_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
```

3. **恢复备份**：
```powershell
Copy-Item "data/logs/portfolio_state_backup_20251116_192432.json" "data/logs/portfolio_state.json" -Force
```

## 恢复的持仓信息

从最新备份恢复的持仓包含：
- **现金**: $3,253.42
- **总价值**: $10,000.00
- **持仓数量**: 15 只股票

### 持仓列表
- CSCO: 7 shares @ $78.00
- CRWD: 1 share @ $537.55
- AZN: 6 shares @ $89.10
- PLTR: 3 shares @ $174.01
- MSFT: 1 share @ $510.18
- GILD: 4 shares @ $125.02
- MU: 2 shares @ $246.83
- AMAT: 2 shares @ $226.01
- PEP: 3 shares @ $145.85
- PANW: 2 shares @ $205.25
- TSLA: 1 share @ $404.35
- NVDA: 2 shares @ $190.17
- AVGO: 1 share @ $342.46
- CEG: 1 share @ $338.52
- AMGN: 1 share @ $336.74

## 验证恢复

恢复后，检查 `portfolio_state.json`：
```powershell
Get-Content "data/logs/portfolio_state.json" | ConvertFrom-Json | Select-Object cash, total_value, @{Name='positions_count';Expression={($_.positions.PSObject.Properties.Count)}}
```

## 注意事项

1. **备份时机**：系统会在初始化前自动备份，但建议重要操作前手动备份
2. **数据一致性**：恢复后，净值历史记录可能不匹配，这是正常的
3. **价格更新**：恢复后，持仓价格会在下次API调用时更新为最新价格
4. **测试环境**：建议在测试环境使用独立的备份，避免影响生产数据

## 预防措施

1. **定期备份**：使用 `scripts/backup_data.ps1` 定期备份
2. **测试隔离**：测试时使用独立的测试数据目录
3. **版本控制**：重要状态变更前提交到Git（如果适用）

