# 持仓、未实现损益和持仓价值更新逻辑

## 概述

系统采用**市价交易**模式，所有订单在**盘中成交后立即更新持仓**。持仓、未实现损益和持仓价值的变动**只在订单成交后**才会记录和更新。

---

## 更新时机

### ✅ 只在订单成交后更新

1. **持仓更新**：订单成交后，立即调用 `portfolio.buy()` 或 `portfolio.sell()` 更新持仓
2. **未实现损益计算**：基于当前持仓和实时价格计算（每次查询时计算，不保存）
3. **持仓价值计算**：基于当前持仓数量和实时价格计算（每次查询时计算，不保存）

### ❌ 不会更新的情况

1. **订单创建时**：只创建订单记录，不更新持仓
2. **订单PENDING时**：订单保持PENDING状态，不更新持仓
3. **市场关闭时**：不创建订单，不更新持仓

---

## 详细流程

### 1. 买入订单成交流程

```python
# 1. 创建订单（PENDING状态）
placed_order = order_manager.place_order(...)

# 2. 立即标记为FILLED（市价单保证成交）
order_manager.mark_order_filled(placed_order, fill_result)

# 3. 执行交易，更新持仓
portfolio.buy(symbol, quantity, current_price)
# - 更新现金：cash -= cost
# - 更新持仓：_positions[symbol] = Position(...)
# - 使用加权平均法计算平均成本

# 4. 保存portfolio状态到portfolio_state.json
portfolio_state = {
    "cash": portfolio.cash,
    "positions": {
        symbol: {
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "total_cost": pos.total_cost,
        }
    }
}
```

### 2. 卖出订单成交流程

```python
# 1. 先执行交易（获取realized_pnl）
realized_pnl = portfolio.sell(symbol, quantity, current_price)
# - 计算已实现损益：realized_pnl = proceeds - cost_basis
# - 更新现金：cash += proceeds
# - 更新持仓：减少数量或删除持仓

# 2. 创建订单记录（标记为FILLED）
placed_order = order_manager.place_order(...)
order_manager.mark_order_filled(placed_order, fill_result, realized_pnl=realized_pnl)

# 3. 保存portfolio状态
```

### 3. 未实现损益计算

未实现损益**不保存在portfolio_state.json中**，而是**每次查询时实时计算**：

```python
# 在trading_cycle.py中，交易执行后重新计算
portfolio_pnl = portfolio.get_all_positions_pnl(last_prices)
# 返回：
# {
#     symbol: {
#         "unrealized_pnl": (current_price - avg_cost) * quantity,
#         "unrealized_pnl_pct": ((current_price - avg_cost) / avg_cost) * 100,
#         "market_value": quantity * current_price,
#         ...
#     }
# }
```

### 4. 持仓价值计算

持仓价值**不保存在portfolio_state.json中**，而是**每次查询时实时计算**：

```python
# 在trading_cycle.py中，交易执行后重新计算
equity_value = portfolio.equity_value(last_prices)
# = sum(quantity * current_price for all positions)

total_value = portfolio.value(last_prices)
# = cash + equity_value
```

---

## 保存的数据

### portfolio_state.json（持久化保存）

```json
{
  "cash": 10000.0,
  "initial_value": 10000.0,
  "total_value": 15000.0,  // 计算值，用于一致性
  "positions": {
    "AAPL": {
      "quantity": 10,
      "avg_cost": 150.00,
      "total_cost": 1500.00
    }
  },
  "timestamp": "2025-11-14T16:30:00Z"
}
```

**注意**：
- ✅ 保存：现金、持仓数量、平均成本、总成本
- ❌ 不保存：未实现损益、持仓价值（这些是实时计算的）

### 实时计算的数据（不保存）

1. **未实现损益**：`(current_price - avg_cost) * quantity`
2. **持仓价值**：`quantity * current_price`
3. **总净值**：`cash + equity_value`

这些数据在以下时机计算：
- 交易执行后（`trading_cycle.py`）
- API查询时（`/api/portfolio/real-time`）
- 前端刷新时（使用最新价格）

---

## 更新频率

### 持仓更新

- **时机**：订单成交后立即更新
- **频率**：每次交易执行时
- **保存**：立即保存到 `portfolio_state.json`

### 未实现损益更新

- **时机**：每次查询时实时计算
- **频率**：
  - 交易执行后（使用交易时的价格）
  - API查询时（使用实时价格）
  - 前端刷新时（使用实时价格）
- **保存**：不保存，实时计算

### 持仓价值更新

- **时机**：每次查询时实时计算
- **频率**：
  - 交易执行后（使用交易时的价格）
  - API查询时（使用实时价格）
  - 前端刷新时（使用实时价格）
- **保存**：不保存，实时计算

---

## 示例

### 场景：买入10股AAPL @ $150

**1. 订单创建**（不更新持仓）
```python
placed_order = order_manager.place_order(...)  # PENDING状态
# portfolio_state.json 不变
```

**2. 订单成交**（立即更新持仓）
```python
portfolio.buy("AAPL", 10, 150.00)
# - cash: 10000 -> 8500
# - _positions["AAPL"]: Position(quantity=10, avg_cost=150.00, total_cost=1500.00)

# 保存到portfolio_state.json
portfolio_state = {
    "cash": 8500.0,
    "positions": {
        "AAPL": {
            "quantity": 10,
            "avg_cost": 150.00,
            "total_cost": 1500.00
        }
    }
}
```

**3. 查询未实现损益**（实时计算）
```python
current_price = 155.00  # 实时价格
unrealized_pnl = (155.00 - 150.00) * 10 = 50.00
unrealized_pnl_pct = (50.00 / 1500.00) * 100 = 3.33%
market_value = 10 * 155.00 = 1550.00
```

---

## 总结

### ✅ 只在成交后更新

1. **持仓**：订单成交后立即更新并保存
2. **现金**：订单成交后立即更新并保存
3. **平均成本**：订单成交后立即更新并保存

### ✅ 实时计算（不保存）

1. **未实现损益**：每次查询时基于当前价格计算
2. **持仓价值**：每次查询时基于当前价格计算
3. **总净值**：每次查询时基于当前价格计算

### ❌ 不会更新的情况

1. **订单创建时**：只创建订单，不更新持仓
2. **订单PENDING时**：订单保持PENDING，不更新持仓
3. **市场关闭时**：不创建订单，不更新持仓

---

## 关键点

1. **持仓更新是原子操作**：订单成交后立即更新，确保数据一致性
2. **未实现损益是实时计算**：基于最新价格，不保存在文件中
3. **持仓价值是实时计算**：基于最新价格，不保存在文件中
4. **系统采用市价交易**：订单立即成交，不存在PENDING状态（市场关闭时除外）

