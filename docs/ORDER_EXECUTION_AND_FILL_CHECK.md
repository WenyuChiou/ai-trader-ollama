# 📊 订单执行与成交检查机制

## 🎯 成交检查概述

系统实现了**智能成交检查机制**，确保订单只在价格范围内执行，实现**低买高卖**策略。

---

## 🔍 成交检查流程

### 1. **获取实际价格**

在执行订单前，系统会尝试获取实际价格，但有重要限制：

**价格获取策略（按优先级）**：
1. 尝试获取**当天开盘价**（Open price）via yfinance history
2. 如果开盘价不可用，尝试获取**实时价格**（`regularMarketPrice`）via ticker.info
3. 如果实时价格也不可用，fallback 到**昨天的收盘价**（previousClose）
4. 如果都不可用，返回 `None`，使用**价格范围的最优价格**作为执行价格

**重要限制**：
- ⚠️ **系统在 09:00 运行（开盘前）**，此时当天的开盘价可能尚未生成
- ⚠️ **如果市场还未开盘**，yfinance 可能无法获取当天的数据
- ⚠️ **Fallback 策略**：如果无法获取实际价格，系统会使用价格范围边界值执行订单
  - 买入：使用 `buy_price_min`（价格范围最低价）
  - 卖出：使用 `sell_price_max`（价格范围最高价）

```python
# backend/src/data/order_executor.py
actual_price = get_current_or_open_price(symbol, target_date)
# Returns: Open price → regularMarketPrice → previousClose → None
```

**实际执行逻辑**：
```python
if actual_price is None:
    # 无法获取实际价格，使用价格范围边界作为fallback
    execution_price = buy_price_min  # for buy orders
    execution_status = "FILLED"
    execution_reason = "Using price range min (actual price unavailable)"
else:
    # 有实际价格，检查是否在范围内
    execution_check = check_order_execution(order, actual_price, symbol)
```

---

### 2. **价格范围检查**

#### 买入订单检查

```
价格范围: [buy_price_min, buy_price_max]
         [当前价格的98%, 当前价格]

检查逻辑:
├─ 如果 actual_price 在 [buy_price_min, buy_price_max] 内
│   └─ ✅ 成交 (FILLED) - 使用实际价格或 buy_price_min（取较低者）
│
├─ 如果 actual_price < buy_price_min（更便宜）
│   └─ ✅ 成交 (FILLED) - 使用实际价格（更好的价格）
│
└─ 如果 actual_price > buy_price_max（太贵）
    └─ ❌ 拒绝 (REJECTED) - 不执行，价格超出范围
```

**示例**：
- 订单：买入 NVDA，价格范围 [$147, $150]
- 实际开盘价：$148
- 结果：✅ 成交，执行价格 $147（使用 buy_price_min，低买）

---

#### 卖出订单检查

```
价格范围: [sell_price_min, sell_price_max]
         [当前价格的100.5%, 当前价格的102%]

检查逻辑:
├─ 如果 actual_price 在 [sell_price_min, sell_price_max] 内
│   └─ ✅ 成交 (FILLED) - 使用实际价格或 sell_price_max（取较高者）
│
├─ 如果 actual_price > sell_price_max（更贵）
│   └─ ✅ 成交 (FILLED) - 使用实际价格（更好的价格）
│
└─ 如果 actual_price < sell_price_min（太便宜）
    └─ ⏳ 等待 (PENDING) - 不执行，等待更高价格
```

**示例**：
- 订单：卖出 AAPL，价格范围 [$175.88, $178.50]
- 实际开盘价：$174（低于最低卖出价）
- 结果：⏳ 等待 (PENDING) - 价格未达到要求

---

## 📊 成交状态说明

| 状态 | 说明 | 执行结果 |
|------|------|---------|
| **FILLED** | 订单已成功成交 | ✅ 更新 Portfolio，记录交易 |
| **PENDING** | 价格未达到要求，等待中 | ⏳ 不执行，等待下次检查（仅卖出订单） |
| **REJECTED** | 价格超出范围，拒绝执行 | ❌ 不执行，记录错误 |

---

## 💡 执行策略

### 买入订单

- **优先使用**: 实际价格和 `buy_price_min` 中的**较低者**（低买）
- **如果实际价格低于范围**: 使用实际价格（更好的价格）
- **如果实际价格高于范围**: 拒绝执行（REJECTED）

### 卖出订单

- **优先使用**: 实际价格和 `sell_price_max` 中的**较高者**（高卖）
- **如果实际价格高于范围**: 使用实际价格（更好的价格）
- **如果实际价格低于范围**: 等待执行（PENDING）

---

## 📝 执行结果格式

```python
{
  "executed_trades": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "price": 147.25,              # 实际执行价格
      "actual_price": 148.50,       # 实际市场开盘价
      "price_range": {
        "min": 147.25,              # buy_price_min
        "max": 150.25               # buy_price_max
      },
      "quantity": 10,
      "amount": 1472.50,
      "status": "FILLED",            # 成交状态
      "execution_reason": "Price $148.50 within buy range [$147.25, $150.25]"
    }
  ],
  "execution_errors": [
    "BUY MSFT: Price $425.00 above buy_max $420.00",  # 未成交的订单
    "SELL AAPL: Price $174.00 below sell_min $175.88 (waiting for higher price)"  # 等待中的订单
  ]
}
```

---

## 🔧 配置说明

当前价格范围参数是**硬编码**的，未来可以移到 `config.json`：

```json
{
  "order_execution": {
    "buy_price_range": {
      "min_pct": 0.98,    // 最低买入价 = 当前价格的98%
      "max_pct": 1.00     // 最高买入价 = 当前价格的100%
    },
    "sell_price_range": {
      "min_pct": 1.005,   // 最低卖出价 = 当前价格的100.5%
      "max_pct": 1.02     // 最高卖出价 = 当前价格的102%
    }
  }
}
```

---

## ⚠️ 注意事项

1. **实际价格获取**：
   - 如果无法获取实际价格（网络问题、市场未开盘等），系统使用价格范围的最优价格
   - 这是保守策略，确保订单能够执行

2. **等待中的订单**（PENDING）：
   - 仅卖出订单可能出现 PENDING 状态
   - 当前实现不会自动重试，需要在下一次运行中再次检查

3. **未来增强**：
   - 可以实现订单队列（pending orders），定期检查是否可以成交
   - 可以实现部分成交（partial fill）支持

---

## 📚 相关文档

- `docs/TRADING_TIMELINE.md` - 交易时间线说明
- `docs/PRICE_DATA_STRATEGY.md` - 价格数据策略

