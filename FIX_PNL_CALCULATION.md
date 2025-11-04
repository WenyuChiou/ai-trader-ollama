# 未实现损益（Unrealized P&L）计算修复

## 问题描述

未实现损益显示错误：**Unrealized P&L = Market Value**，而不是正确的 **Market Value - Cost Basis**。

## 根本原因

1. **`portfolio_state.json` 缺少 `total_cost` 字段**
   - 保存时只保存了 `quantity`、`avg_cost`、`current_value`
   - 没有保存 `total_cost`（总成本）

2. **恢复持仓时 `total_cost = 0`**
   - 从 `portfolio_state.json` 恢复时，`total_cost` 为 0 或缺失
   - 导致 `cost_basis = total_cost = 0`
   - 所以 `unrealized_pnl = market_value - 0 = market_value`

## 修复方案

### 1. 后端保存时添加 `total_cost`

**文件**: `backend/src/api/server.py`
- `execute_trade_direct()`: 保存时添加 `total_cost`
- `settle_orders()`: 保存时添加 `total_cost`
- `trading_cycle.py`: 保存时添加 `total_cost`

### 2. 后端恢复时计算 `total_cost`

**文件**: `backend/src/api/server.py`
- `get_real_time_portfolio()`: 如果 `total_cost <= 0`，从 `avg_cost * quantity` 计算

### 3. 实时追踪器使用正确的 `cost_basis`

**文件**: `backend/src/data/real_time_tracker.py`
- `calculate_real_time_portfolio()`: 如果 `total_cost <= 0`，从 `avg_cost * quantity` 计算

### 4. 修复现有数据

运行修复脚本：
```powershell
python backend/scripts/fix_portfolio_total_cost.py
```

或手动修复：
```python
import json
from pathlib import Path

p = Path("data/logs/portfolio_state.json")
state = json.load(p.open())

for pos_info in state.get("positions", {}).values():
    if isinstance(pos_info, dict) and pos_info.get("total_cost", 0) <= 0:
        pos_info["total_cost"] = pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0)

p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
```

## 计算公式

### 正确的公式
```
cost_basis = total_cost = avg_cost × quantity
market_value = current_price × quantity
unrealized_pnl = market_value - cost_basis
unrealized_pnl_pct = (unrealized_pnl / cost_basis) × 100%
```

### 示例
假设：
- 买入 7 股 NVDA，平均成本 $200.07
- 当前价格 $199.77

计算：
- `cost_basis = 200.07 × 7 = $1,400.49`
- `market_value = 199.77 × 7 = $1,398.39`
- `unrealized_pnl = 1,398.39 - 1,400.49 = -$2.10`（亏损）
- `unrealized_pnl_pct = (-2.10 / 1,400.49) × 100% = -0.15%`

## 验证

修复后，刷新前端页面，检查：
1. Unrealized P&L 应该 = Market Value - Cost Basis
2. P&L % 应该反映实际的盈亏百分比
3. 如果当前价格 > 平均成本：P&L 为正（绿色）
4. 如果当前价格 < 平均成本：P&L 为负（红色）

## 修改的文件

1. ✅ `backend/src/api/server.py`
   - `get_real_time_portfolio()`: 恢复时计算 `total_cost`
   - `execute_trade_direct()`: 保存时包含 `total_cost`
   - `settle_orders()`: 保存时包含 `total_cost`

2. ✅ `backend/src/data/real_time_tracker.py`
   - `calculate_real_time_portfolio()`: 使用正确的 `cost_basis`

3. ✅ `backend/src/orchestrator/trading_cycle.py`
   - 保存时包含 `total_cost`

4. ✅ `backend/scripts/fix_portfolio_total_cost.py`
   - 修复现有数据的脚本

