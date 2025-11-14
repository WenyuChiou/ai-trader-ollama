# 市价交易逻辑说明

## 概述

系统采用**市价交易（Market Order）**模式，所有订单应该**立即成交**，不应该出现PENDING状态。

---

## 市价交易的特点

### ✅ 应该的行为

1. **立即成交**: 市价单在创建时就应该立即成交
2. **状态为FILLED**: 所有市价单的状态应该是`FILLED`，而不是`PENDING`
3. **无pending订单**: 在市场开放时，不应该有pending订单（除非是系统错误）

### ❌ 不应该的行为

1. **PENDING状态**: 市价单不应该保持PENDING状态
2. **收盘后pending**: 市场关闭后，不应该有今天的pending订单（因为市价单应该在市场开放时立即成交）

---

## 代码实现

### 1. 订单创建流程（`trading_cycle.py`）

```python
# 市价单：立即成交，不挂单
# 创建订单记录（标记为已成交）
placed_order = order_manager.place_order(
    symbol=symbol,
    action="BUY",
    quantity=quantity,
    limit_price=current_price,  # 市价单：使用当前价格
    price_range={
        "min": current_price,
        "max": current_price,
    },
)

# 立即标记为已成交（市价单保证成交）
fill_result = {
    "filled": True,
    "fill_price": current_price,
    "fill_reason": "Market order executed immediately at current price",
    ...
}

# CRITICAL: 确保订单标记为FILLED（市价单必须立即成交）
try:
    order_manager.mark_order_filled(placed_order, fill_result)
    placed_order["status"] = "FILLED"
except Exception as e:
    # 如果mark_order_filled失败，手动设置状态为FILLED
    placed_order["status"] = "FILLED"
    # 手动从pending中移除并写入filled
    ...
```

### 2. 订单管理器（`order_manager.py`）

**问题**: `place_order()` 方法默认创建PENDING状态的订单：

```python
def place_order(...) -> Dict[str, Any]:
    order = {
        ...
        "status": "PENDING",  # ⚠️ 默认状态是PENDING
    }
```

**解决方案**: 在`trading_cycle.py`中，创建订单后立即调用`mark_order_filled()`来标记为FILLED。

---

## 保护机制

### 1. 市场关闭时清理pending订单

```python
# CRITICAL FIX: 市场关闭时，立即清理今天的pending订单
# 因为市场订单不应该有pending状态
if len(existing_pending_orders) > 0:
    print(f"[TRADING CYCLE] Market is closed. Immediately cancelling {len(existing_pending_orders)} today's pending orders...")
    cancelled_count = order_manager.cancel_orders(order_date=today)
```

### 2. 市场关闭时不创建订单

```python
# CRITICAL FIX: 市场关闭时，不允许创建订单
should_create_orders = False
if end is not None:
    should_create_orders = True
elif is_market_open_for_simulation:
    # 只有在市场开放时才创建订单
    ...
else:
    should_create_orders = False
    print(f"[TRADING CYCLE] Market is closed. Skipping order creation (should_create_orders=False).")
```

### 3. 市场关闭时不执行订单

```python
# CRITICAL FIX: 市价交易 - 获取当前价格并立即成交
# 只在市场开盘时执行市价交易
if not is_market_open_for_simulation:
    execution_errors.append(f"BUY {symbol} skipped: market is closed (market orders only execute during trading hours)")
    continue
```

---

## 表格显示逻辑

### Execution Details 表格

根据文档（`FRONTEND_TABLES_GUIDE.md`），表格应该显示：

| 列名 | 说明 | 示例 |
|------|------|------|
| Time | 交易时间 | `11/14, 16:22:57` |
| Symbol | 股票代码 | `AAPL`, `TSLA` |
| Side | 买卖方向 | `BUY`（绿色）或 `SELL`（红色） |
| Qty | 交易数量 | `10`, `25` |
| Price | 成交价格 | `$150.00` |
| Realized P&L | 已实现损益 | `+$50.00 (+3.33%)` 或 `-` |
| Status | 订单状态 | `FILLED`（绿色）或 `PENDING`（黄色） |

### 显示逻辑

- **如果有FILLED订单**: 只显示FILLED订单
- **如果没有FILLED订单**: 显示PENDING订单（包括明日挂单）

**注意**: 对于市价交易，理论上不应该有PENDING订单，所以应该只显示FILLED订单。

---

## 当前状态检查

从图片看，现在显示的是：
- **32 trades (32 filled)** ✅ 正确
- 所有订单状态都是 **FILLED** ✅ 正确
- Symbol列只显示股票代码（如 `SQQQ`, `ROST`）✅ 正确（已修复日期问题）

---

## 潜在问题

### 如果出现PENDING订单

可能的原因：
1. **市场关闭时创建的订单**: 应该在市场关闭时被自动清理
2. **mark_order_filled()失败**: 有错误恢复机制，手动设置状态为FILLED
3. **旧数据**: 可能是之前遗留的订单

### 解决方案

1. **自动清理**: 市场关闭时自动清理今天的pending订单
2. **错误恢复**: 如果`mark_order_filled()`失败，手动设置状态并写入filled文件
3. **手动清理**: 可以运行清理脚本删除pending订单

---

## 总结

✅ **表格格式**: 与文档一致（7列：Time, Symbol, Side, Qty, Price, Realized P&L, Status）

✅ **市价交易逻辑**: 
- 订单创建后立即标记为FILLED
- 市场关闭时自动清理pending订单
- 市场关闭时不创建新订单

✅ **当前状态**: 32个FILLED订单，符合市价交易逻辑

---

## 建议

如果将来出现PENDING订单，检查：
1. 订单的`placed_at`时间是否在市场开放时间内
2. `mark_order_filled()`是否成功执行
3. 是否有错误日志

