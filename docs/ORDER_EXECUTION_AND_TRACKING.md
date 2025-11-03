# 📊 订单执行策略与成交明细追踪

## 🎯 完整执行流程

### 阶段 1: 开盘前挂单（09:00）

**在 `trading_cycle.py` 中**：
- 生成交易决策（buy_orders / sell_orders）
- 创建限价单：
  - **买入**：限价 = `buy_price_min`（价格范围最低价，低买策略）
  - **卖出**：限价 = `sell_price_max`（价格范围最高价，高卖策略）
- 保存到 `pending_orders.jsonl`
- 记录到每日记忆（`executed_trades` 标记为 `PENDING`）
- 记录初始净值（挂单时的 Portfolio 状态）

### 阶段 2: 收盘后检查成交（16:30）

**在 `check_pending_orders.py` 中**：
- 加载当天的挂单
- 获取当天 High/Low 价格
- 判断是否成交：
  - **买入**：如果 `daily_low <= limit_price` → 成交
  - **卖出**：如果 `daily_high >= limit_price` → 成交
- 执行成交订单：
  - 更新 Portfolio（买入：减少现金，增加持仓；卖出：增加现金，减少持仓）
  - 记录成交明细到 `executed_trades`
  - 更新每日记忆（补充成交明细）
  - **更新每日净值**（成交后的 Portfolio 状态）

---

## 📋 成交明细数据结构

### 买入订单成交明细

```json
{
  "symbol": "NVDA",
  "action": "BUY",
  "price": 147.25,              // 实际成交价格
  "quantity": 10,                // 成交数量
  "amount": 1472.50,            // 总金额 (price * quantity)
  "status": "FILLED",           // 状态: FILLED / REJECTED
  "limit_price": 147.25,        // 限价（buy_price_min）
  "daily_high": 152.00,         // 当天最高价
  "daily_low": 148.50,          // 当天最低价
  "fill_reason": "Daily low $148.50 <= limit $147.25",
  "order_date": "2025-10-21",  // 挂单日期
  "filled_at": "2025-10-21T16:30:00"  // 成交时间
}
```

### 卖出订单成交明细

```json
{
  "symbol": "AAPL",
  "action": "SELL",
  "price": 180.00,              // 实际成交价格
  "quantity": 5,                 // 成交数量
  "amount": 900.00,             // 总金额 (price * quantity)
  "status": "FILLED",           // 状态: FILLED / REJECTED
  "limit_price": 180.00,        // 限价（sell_price_max）
  "daily_high": 182.50,         // 当天最高价
  "daily_low": 175.00,          // 当天最低价
  "fill_reason": "Daily high $182.50 >= limit $180.00",
  "order_date": "2025-10-21",  // 挂单日期
  "filled_at": "2025-10-21T16:30:00"  // 成交时间
}
```

---

## 📈 每日净值追踪

### 记录时间点

1. **开盘前（挂单时）**：
   - 记录初始净值（Portfolio 在挂单前的状态）
   - 此时 `executed_trades` 只包含挂单信息（`status: PENDING`）

2. **收盘后（成交后）**：
   - 记录最终净值（Portfolio 在成交后的状态）
   - 此时 `executed_trades` 包含实际成交明细（`status: FILLED`）
   - **覆盖**开盘前的净值记录（使用成交后的数据）

### 净值记录格式

**在 `equity_history.jsonl` 中**：

```json
{
  "date": "2025-10-21",
  "timestamp": "2025-10-21T16:30:00",
  "cash": 7416.61,
  "equity_value": 2636.11,
  "total_value": 10052.72,
  "total_pnl": 52.72,
  "total_pnl_pct": 0.53,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 152.00,
      "market_value": 1520.00,
      "unrealized_pnl": 17.50,
      "unrealized_pnl_pct": 1.16
    }
  }
}
```

---

## 💾 每日记忆结构

**在 `memory/daily/YYYY-MM-DD.json` 中**：

```json
{
  "date": "2025-10-21",
  "timestamp": "2025-10-21T16:30:00",
  "market_view": {...},
  "market_analysis": {...},
  "discussion": {...},
  "risk_report": {...},
  "decision": {
    "action": "BUY",
    "buy_orders": [...],
    "sell_orders": [...]
  },
  "executed_trades": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "price": 147.25,
      "quantity": 10,
      "status": "FILLED",
      "limit_price": 147.25,
      "daily_high": 152.00,
      "daily_low": 148.50,
      "fill_reason": "Daily low $148.50 <= limit $147.25",
      "order_date": "2025-10-21",
      "filled_at": "2025-10-21T16:30:00"
    }
  ],
  "executed_trades_count": 1,
  "portfolio_snapshot": {
    "cash": 7416.61,
    "total_value": 10052.72,
    "equity_value": 2636.11,
    "total_pnl": 52.72,
    "total_pnl_pct": 0.53,
    "positions_detail": {...}
  }
}
```

---

## 🔄 数据流

```
[09:00] 开盘前
  ↓
execute_daily_trade()
  ├─ 生成交易决策
  ├─ 挂限价单 (OrderManager.place_order)
  ├─ 保存到 pending_orders.jsonl
  ├─ 记录到 daily_memory (executed_trades: PENDING)
  └─ 记录初始净值 (equity_history.jsonl)

[16:30] 收盘后
  ↓
check_pending_orders()
  ├─ 加载 pending_orders.jsonl
  ├─ 检查每个订单是否成交 (check_order_fill)
  ├─ 执行成交订单 (portfolio.buy/sell)
  ├─ 记录成交明细 (executed_trades: FILLED)
  ├─ 更新 daily_memory (补充成交明细)
  └─ 更新净值记录 (equity_history.jsonl - 覆盖)
```

---

## ✅ 关键改进

1. **完整的成交明细**：
   - 包含买入和卖出订单的完整信息
   - 记录限价、实际成交价、当天高低价
   - 记录成交原因和时间戳

2. **每日净值追踪**：
   - 开盘前记录一次（挂单时）
   - 收盘后更新一次（成交后，覆盖）
   - 确保净值反映实际交易结果

3. **每日记忆更新**：
   - 开盘前保存初始记忆（包含挂单信息）
   - 收盘后更新记忆（补充成交明细）
   - 确保每日记忆包含完整的交易历史

4. **数据一致性**：
   - Portfolio 状态在文件中持久化
   - 每日记忆和净值记录同步更新
   - 成交明细可追溯（order_date, filled_at）

