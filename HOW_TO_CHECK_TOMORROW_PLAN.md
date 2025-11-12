# 如何判断隔日计划

## 判断逻辑

系统通过以下步骤判断是否已有隔日计划：

### 1. 计算下一个交易日

```python
from src.utils.trading_days import get_next_trading_day
next_trading_day = get_next_trading_day(date.today(), days_ahead=1)
tomorrow_str = next_trading_day.isoformat()  # 例如: "2025-11-12"
```

**说明**：
- 使用 `get_next_trading_day()` 计算下一个交易日
- 自动排除周末和节假日
- 返回日期格式：`YYYY-MM-DD`

### 2. 加载该日期的待处理订单

```python
order_manager = OrderManager(root="data/logs")
existing_orders = order_manager.load_pending_orders(order_date=tomorrow_str)
```

**`load_pending_orders()` 方法**：
- 从 `data/logs/pending_orders.jsonl` 文件读取所有订单
- 过滤出 `order_date` 等于指定日期的订单
- 返回订单列表

**订单文件格式** (`pending_orders.jsonl`):
```json
{"order_id": "AAPL_BUY_2025-11-12_1234567890", "symbol": "AAPL", "action": "BUY", "quantity": 10, "limit_price": 150.0, "order_date": "2025-11-12", "status": "PENDING", ...}
{"order_id": "MSFT_BUY_2025-11-12_1234567891", "symbol": "MSFT", "action": "BUY", "quantity": 5, "limit_price": 300.0, "order_date": "2025-11-12", "status": "PENDING", ...}
```

### 3. 判断是否有计划

```python
if existing_orders:
    # 已有计划：返回消息，不执行新计划
    return {
        "ok": True,
        "message": f"Market closed. Already have {len(existing_orders)} pending orders for tomorrow ({tomorrow_str}). No new planning needed.",
        "result": {
            "placed_orders": [],
            "conversations_count": 0,
            "is_planning": True,
            "order_date": tomorrow_str
        }
    }
else:
    # 没有计划：执行计划
    result = execute_daily_trade(...)
    return {
        "ok": True,
        "message": f"Planning completed for tomorrow ({tomorrow_str})",
        "result": result
    }
```

## 判断标准

### ✅ 有计划的判断条件

1. **订单文件存在**：`pending_orders.jsonl` 文件存在
2. **有匹配的订单**：存在 `order_date` 等于下一个交易日的订单
3. **订单状态**：订单状态为 `PENDING`（待处理）

### ❌ 没有计划的判断条件

1. **订单文件不存在**：`pending_orders.jsonl` 文件不存在
2. **没有匹配的订单**：没有 `order_date` 等于下一个交易日的订单
3. **订单已被处理**：所有订单状态为 `FILLED` 或 `REJECTED`

## 订单文件位置

**文件路径**：`backend/data/logs/pending_orders.jsonl`

**文件格式**：每行一个 JSON 对象（JSONL 格式）

**订单字段**：
```json
{
  "order_id": "AAPL_BUY_2025-11-12_1234567890",
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "limit_price": 150.0,
  "price_range": {"min": 149.0, "max": 151.0},
  "order_date": "2025-11-12",  // 关键字段：用于判断
  "status": "PENDING",          // PENDING / FILLED / REJECTED
  "placed_at": "2025-11-11T16:30:00"
}
```

## 代码实现

### 后端判断逻辑（`server.py`）

```python
@app.post("/api/trading/execute-trade")
async def execute_trade_direct():
    # 检查市场是否开盘
    is_market_open = check_market_open(now)
    
    if not is_market_open:
        # 计算下一个交易日
        next_trading_day = get_next_trading_day(date.today(), days_ahead=1)
        tomorrow_str = next_trading_day.isoformat()
        
        # 加载该日期的待处理订单
        order_manager = OrderManager(root="data/logs")
        existing_orders = order_manager.load_pending_orders(order_date=tomorrow_str)
        
        if existing_orders:
            # 已有计划：返回消息
            return {
                "ok": True,
                "message": f"Already have {len(existing_orders)} pending orders for tomorrow",
                "result": {
                    "is_planning": True,
                    "order_date": tomorrow_str
                }
            }
        else:
            # 没有计划：执行计划
            result = execute_daily_trade(...)
            return {
                "ok": True,
                "message": f"Planning completed for tomorrow",
                "result": result
            }
```

### `OrderManager.load_pending_orders()` 实现

```python
def load_pending_orders(self, order_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    加载待处理订单
    
    参数:
    - order_date: 订单日期 (YYYY-MM-DD)，如果为 None，返回所有订单
    
    返回:
    - 订单列表
    """
    if not self.pending_orders_file.exists():
        return []
    
    orders = []
    with self.pending_orders_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                order = json.loads(line)
                # 如果指定了 order_date，只返回匹配的订单
                if order_date is None or order.get("order_date") == order_date:
                    # 只返回 PENDING 状态的订单
                    if order.get("status") == "PENDING":
                        orders.append(order)
            except json.JSONDecodeError:
                continue
    
    return orders
```

## 前端判断逻辑

前端通过 API 响应判断：

```javascript
const response = await fetch('/api/trading/execute-trade', ...);
const data = await response.json();

if (data.ok) {
    const message = data.message || '';
    
    // 判断是否有计划
    if (message.includes('Already have') || 
        message.includes('already planned') || 
        message.includes('No new planning needed')) {
        // 已有计划
        console.log('Tomorrow is already planned');
    } else if (data.result?.is_planning) {
        // 刚完成计划
        console.log('Planning completed');
    }
}
```

## 判断流程图

```
市场休市
  ↓
计算下一个交易日
  (get_next_trading_day)
  ↓
加载该日期的待处理订单
  (load_pending_orders(order_date=tomorrow))
  ↓
判断订单列表
  ├─ 有订单 (len > 0)
  │   └─ 返回: "Already have X orders"
  │
  └─ 没有订单 (len == 0)
      └─ 执行计划
          └─ 返回: "Planning completed"
```

## 关键点

1. **日期计算**：使用 `get_next_trading_day()` 自动排除周末和节假日
2. **订单过滤**：只检查 `order_date` 等于下一个交易日的订单
3. **状态检查**：只考虑 `status == "PENDING"` 的订单
4. **文件位置**：订单存储在 `backend/data/logs/pending_orders.jsonl`

## 测试方法

可以通过以下方式测试判断逻辑：

```python
from src.data.order_manager import OrderManager
from src.utils.trading_days import get_next_trading_day
from datetime import date

# 计算下一个交易日
next_trading_day = get_next_trading_day(date.today(), days_ahead=1)
tomorrow_str = next_trading_day.isoformat()

# 加载订单
order_manager = OrderManager(root="data/logs")
existing_orders = order_manager.load_pending_orders(order_date=tomorrow_str)

# 判断
if existing_orders:
    print(f"已有 {len(existing_orders)} 个隔日计划")
else:
    print("没有隔日计划")
```

## 总结

系统通过以下方式判断隔日计划：
1. ✅ 计算下一个交易日（排除周末和节假日）
2. ✅ 从订单文件中加载该日期的待处理订单
3. ✅ 如果订单列表不为空，表示已有计划
4. ✅ 如果订单列表为空，表示没有计划，需要执行计划

