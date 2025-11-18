# Snapshot 字段说明

## 什么是 Snapshot 字段？

`snapshot` 是 `portfolio_state.json` 中的一个**快照字段**，用于存储**已经计算好的净值数据**，避免重复计算，并在价格获取失败时作为备用数据。

## 数据结构

```json
{
  "cash": 10000.0,
  "initial_value": 10000.0,
  "total_value": 10000.0,
  "positions": {...},
  "timestamp": "2025-11-18T23:44:28.699242Z",
  "snapshot": {
    "cash": 10000.0,
    "total_value": 10000.0,
    "equity_value": 0.0,
    "positions_count": 0
  }
}
```

## 为什么需要 Snapshot？

### 1. **避免重复计算**
- 在交易循环结束时，已经计算好了 `total_value` 和 `equity_value`
- 将这些值保存到 `snapshot` 中，避免后续 API 调用时重复计算

### 2. **价格获取失败时的备用数据**
- 当市场收盘或价格 API 失败时，无法获取实时价格
- `snapshot` 中存储的是**最后一次成功计算的值**，可以作为备用数据
- 确保前端始终能显示净值数据，即使价格获取失败

### 3. **数据一致性验证**
- `snapshot` 中的 `total_value` 应该等于 `snapshot.cash + snapshot.equity_value`
- 可以用来验证数据的准确性

## 使用场景

### 场景 1: 交易循环结束时保存
```python
# trading_cycle.py
portfolio_state = {
    "cash": portfolio.cash,
    "initial_value": portfolio.initial_value,
    "total_value": total_value,
    "positions": {...},
    "snapshot": {
        "cash": portfolio.cash,
        "total_value": total_value,
        "equity_value": equity_value,
        "positions_count": len(portfolio._positions),
    }
}
```

### 场景 2: API 获取实时数据时使用
```python
# server.py - /api/portfolio/real-time
# 如果价格获取失败，且 snapshot 内部一致，使用 snapshot 的值
if all_prices_equal_avg_cost and snapshot_consistent:
    total_value = snapshot_total_value
    equity_value = snapshot_equity_value
```

### 场景 3: 记录净值历史时使用
```python
# equity_tracker.py
# 优先使用 snapshot 字段的值
snapshot = portfolio_snapshot.get("snapshot", {})
if snapshot:
    current_value = float(snapshot.get("total_value", ...))
    current_equity = float(snapshot.get("equity_value", ...))
```

## Snapshot 字段内容

| 字段 | 说明 | 计算方式 |
|------|------|----------|
| `cash` | 现金余额 | `portfolio.cash` |
| `total_value` | 总净值 | `cash + equity_value` |
| `equity_value` | 持仓市值 | `sum(quantity * current_price)` |
| `positions_count` | 持仓数量 | `len(portfolio._positions)` |

## 注意事项

1. **数据一致性**: `snapshot.total_value` 应该等于 `snapshot.cash + snapshot.equity_value`
2. **优先级**: 当 `snapshot` 字段存在时，优先使用 `snapshot` 的值
3. **更新时机**: `snapshot` 在交易循环结束时更新，包含最新的计算结果
4. **备用机制**: 当价格获取失败时，`snapshot` 提供最后已知的准确值

## 修复历史

- **2025-01-XX**: 修复 `equity_tracker.py` 正确处理 `snapshot` 字段
  - 之前：只读取顶层字段，忽略 `snapshot`
  - 现在：优先使用 `snapshot` 字段的值

