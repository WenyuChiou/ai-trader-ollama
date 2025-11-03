# 📋 挂单策略（Pending Order Strategy）

## 🎯 策略概述

**挂单策略**：开盘前挂限价单，收盘后根据当天的 High/Low 判断是否成交。

这个策略解决了之前"无法获取实时价格"的问题：

- ✅ **开盘前（09:00）**：系统挂限价单（不立即执行）
- ✅ **收盘后（16:00）**：根据当天的高低价格范围判断订单是否成交
- ✅ **成交价格**：使用价格范围的最优价格（低买高卖）

---

## 📅 执行流程

### Step 1: 开盘前挂单（09:00）

**在 `trading_cycle.py` 中**：

```python
from src.data.order_manager import OrderManager

order_manager = OrderManager(root="data/logs")

# 买入订单：使用 buy_price_min 作为限价（低买策略）
for order in buy_orders:
    placed_order = order_manager.place_order(
        symbol=symbol,
        action="BUY",
        quantity=quantity,
        limit_price=buy_price_min,  # 限价：使用价格范围最低价
        price_range={"min": buy_price_min, "max": buy_price_max},
        order_date=today,
    )

# 卖出订单：使用 sell_price_max 作为限价（高卖策略）
for order in sell_orders:
    placed_order = order_manager.place_order(
        symbol=symbol,
        action="SELL",
        quantity=quantity,
        limit_price=sell_price_max,  # 限价：使用价格范围最高价
        price_range={"min": sell_price_min, "max": sell_price_max},
        order_date=today,
    )
```

**挂单结果**：
- 订单保存到 `data/logs/pending_orders.jsonl`
- 状态标记为 `PENDING`
- **不立即执行**，等待收盘后检查

---

### Step 2: 收盘后检查成交（16:00 之后）

**运行脚本 `backend/scripts/check_pending_orders.py`**：

```bash
cd backend
python scripts/check_pending_orders.py --date 2024-01-15 --state-file data/logs/portfolio_state.json
```

**检查逻辑**：

#### 买入订单

```
如果 当天的 Low <= 限价 (buy_price_min)
  → 订单成交（FILLED）
  → 成交价格：max(price_range["min"], daily_low)（低买策略）
  
如果 当天的 Low > 限价
  → 订单未成交（REJECTED）
  → 价格未达到要求
```

**示例**：
- 限价：$150.00（buy_price_min）
- 当天 Low：$148.50
- 当天 High：$152.00
- **结果**：✅ 成交，成交价格 $148.50（比限价更便宜）

---

#### 卖出订单

```
如果 当天的 High >= 限价 (sell_price_max)
  → 订单成交（FILLED）
  → 成交价格：min(price_range["max"], daily_high)（高卖策略）
  
如果 当天的 High < 限价
  → 订单未成交（REJECTED）
  → 价格未达到要求
```

**示例**：
- 限价：$180.00（sell_price_max）
- 当天 Low：$175.00
- 当天 High：$182.50
- **结果**：✅ 成交，成交价格 $180.00（使用限价，高卖策略）

---

### Step 3: 执行成交订单

**如果订单成交**：
1. 更新 Portfolio（买入：减少现金，增加持仓；卖出：增加现金，减少持仓）
2. 记录交易日志
3. 标记订单为 `FILLED`
4. 从 `pending_orders.jsonl` 移除，移到 `filled_orders.jsonl`

**如果订单未成交**：
1. 标记订单为 `REJECTED`
2. 从 `pending_orders.jsonl` 移除，移到 `filled_orders.jsonl`
3. **不更新 Portfolio**

---

## 📊 订单数据结构

### 挂单信息

```json
{
  "order_id": "NVDA_BUY_2024-01-15_1705320000.123",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "limit_price": 147.25,  // 限价（buy_price_min 或 sell_price_max）
  "price_range": {
    "min": 147.25,  // buy_price_min 或 sell_price_min
    "max": 150.25   // buy_price_max 或 sell_price_max
  },
  "order_date": "2024-01-15",
  "placed_at": "2024-01-15T09:00:00",
  "status": "PENDING"
}
```

### 成交结果

```json
{
  "order_id": "NVDA_BUY_2024-01-15_1705320000.123",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "limit_price": 147.25,
  "fill_price": 148.50,  // 实际成交价格
  "daily_high": 152.00,
  "daily_low": 148.50,
  "status": "FILLED",  // 或 "REJECTED"
  "fill_reason": "Daily low $148.50 <= limit $147.25",
  "filled_at": "2024-01-15T16:30:00"
}
```

---

## 🔄 自动化流程

### 每日运行计划

1. **09:00（开盘前）**：
   - 运行 `scripts/run_daily_trading.py`
   - 系统分析昨天数据，生成交易决策
   - 挂限价单（保存到 `pending_orders.jsonl`）
   - 不立即执行交易

2. **16:30（收盘后）**：
   - 运行 `scripts/check_pending_orders.py`
   - 检查前一天的挂单是否成交
   - 执行成交的订单，更新 Portfolio
   - 保存 Portfolio 状态

### Windows 任务计划

**任务 1：开盘前挂单**
- 名称：`AI-Trader Daily Trading (Place Orders)`
- 时间：每天 09:00
- 命令：`python backend/scripts/run_daily_trading.py`

**任务 2：收盘后检查成交**
- 名称：`AI-Trader Check Pending Orders`
- 时间：每天 16:30
- 命令：`python backend/scripts/check_pending_orders.py`

---

## 💡 优势

1. **解决实时价格问题**：
   - 不再需要在开盘前获取实时价格
   - 使用收盘后的 High/Low 数据判断成交

2. **更真实的交易模拟**：
   - 限价单更符合真实交易场景
   - 成交价格基于实际市场数据

3. **低买高卖策略**：
   - 买入：限价设为价格范围最低价（buy_price_min）
   - 卖出：限价设为价格范围最高价（sell_price_max）
   - 成交时使用当天最优价格

4. **订单追踪**：
   - 所有挂单都有唯一 `order_id`
   - 完整的成交历史记录在 `filled_orders.jsonl`

---

## ⚠️ 注意事项

1. **订单检查时机**：
   - 必须在收盘后运行 `check_pending_orders.py`
   - 如果当天还未收盘，需要等到第二天再检查

2. **价格范围策略**：
   - 买入订单：使用 `buy_price_min` 作为限价（可能更便宜）
   - 卖出订单：使用 `sell_price_max` 作为限价（可能更贵）
   - 实际成交价格可能比限价更好（更便宜买入，更贵卖出）

3. **现金和持仓检查**：
   - 挂单时检查现金/持仓是否充足
   - 成交时再次检查（如果现金/持仓不足，会减少数量或拒绝订单）

4. **订单状态**：
   - `PENDING`：挂单中，等待收盘后检查
   - `FILLED`：已成交
   - `REJECTED`：未成交（价格未达到要求或现金/持仓不足）

---

## 📝 相关文件

- `backend/src/data/order_manager.py` - 挂单管理器
- `backend/src/orchestrator/trading_cycle.py` - 交易循环（挂单逻辑）
- `backend/scripts/check_pending_orders.py` - 收盘后检查成交脚本
- `data/logs/pending_orders.jsonl` - 待处理订单
- `data/logs/filled_orders.jsonl` - 已成交/已拒绝订单

