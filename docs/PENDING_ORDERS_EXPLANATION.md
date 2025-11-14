# PENDING订单说明

## 概述

系统采用**市价交易**模式，理论上**不应该有PENDING订单**。但在某些边缘情况下，仍可能出现PENDING订单。

---

## 理论上不应该有PENDING订单

### ✅ 正常流程

1. **市场开放时**：
   - 创建订单（初始状态为PENDING）
   - 立即标记为FILLED（市价单保证成交）
   - 订单从pending_orders.jsonl移动到filled_orders.jsonl

2. **市场关闭时**：
   - 不创建订单（Trader Agent检查市场状态）
   - 自动清理今天的pending订单

---

## 可能存在的边缘情况

### 1. 系统异常中断

**情况**：订单创建后，在标记为FILLED之前系统崩溃或异常中断

**结果**：订单可能停留在pending_orders.jsonl中

**处理**：
- 系统重启后，市场关闭时会自动清理今天的pending订单
- 市场开放时，`check-pending-orders` API会尝试结算这些订单

### 2. mark_order_filled() 失败

**情况**：`mark_order_filled()` 调用失败，且手动处理也失败

**代码位置**：`trading_cycle.py:1296-1338`

```python
try:
    order_manager.mark_order_filled(placed_order, fill_result)
    placed_order["status"] = "FILLED"
except Exception as e:
    # 手动处理：从pending中移除并写入filled
    # 如果这里也失败，订单可能仍留在pending中
```

**处理**：
- 有错误恢复机制（手动从pending移除）
- 如果恢复也失败，订单可能留在pending中

### 3. 旧数据遗留

**情况**：系统升级前遗留的pending订单

**处理**：
- 市场关闭时自动清理
- 可以手动清理

---

## 现有的清理机制

### 1. 市场关闭时自动清理

**位置**：`trading_cycle.py:632-638`

```python
if len(existing_pending_orders) > 0:
    print(f"[TRADING CYCLE] Market is closed. Immediately cancelling {len(existing_pending_orders)} today's pending orders...")
    cancelled_count = order_manager.cancel_orders(order_date=today)
```

**时机**：
- 市场关闭时（收盘后）
- 每次运行交易周期时检查

### 2. 市场关闭时不创建订单

**位置**：`trader_agent.py:341-398`

```python
if not is_market_open:
    # 市场关闭时，不生成任何订单
    return {
        "buy_orders": [],
        "sell_orders": [],
        ...
    }
```

**效果**：市场关闭时不会创建新的pending订单

---

## 改进建议

### 方案1：改进place_order()支持直接创建FILLED订单

```python
def place_order(
    self,
    symbol: str,
    action: str,
    quantity: int,
    limit_price: float,
    price_range: Dict[str, float],
    status: str = "PENDING",  # 新增：允许指定初始状态
) -> Dict[str, Any]:
    order = {
        ...
        "status": status,  # 使用传入的状态
    }
```

**优点**：市价单可以直接创建为FILLED状态

**缺点**：需要修改多个调用点

### 方案2：确保mark_order_filled()的可靠性

**当前**：有try-except和手动恢复机制

**改进**：增加重试机制和更详细的日志

### 方案3：定期清理pending订单

**建议**：在系统启动时或定期检查并清理旧的pending订单

---

## 检查pending订单的方法

### 1. 查看pending_orders.jsonl

```bash
cat data/logs/pending_orders.jsonl
```

### 2. 使用API检查

```bash
curl http://localhost:8000/api/trading/check-pending-orders
```

### 3. 前端显示

前端会显示pending订单数量（如果有）

---

## 清理pending订单的方法

### 1. 自动清理（推荐）

系统会在市场关闭时自动清理今天的pending订单

### 2. 手动清理

```python
from src.data.order_manager import OrderManager
from datetime import date

order_manager = OrderManager()
today = date.today().isoformat()
cancelled_count = order_manager.cancel_orders(order_date=today)
print(f"Cancelled {cancelled_count} pending orders")
```

### 3. 直接删除文件（不推荐）

```bash
# 备份后删除
cp data/logs/pending_orders.jsonl data/logs/pending_orders.jsonl.backup
echo "" > data/logs/pending_orders.jsonl
```

---

## 总结

### ✅ 正常情况下

- **不应该有pending订单**：市价单立即成交，市场关闭时不创建订单

### ⚠️ 边缘情况

- **可能存在的pending订单**：
  1. 系统异常中断
  2. mark_order_filled()失败
  3. 旧数据遗留

### 🛡️ 保护机制

- **自动清理**：市场关闭时自动清理今天的pending订单
- **错误恢复**：mark_order_filled()失败时有手动恢复机制
- **状态检查**：Trader Agent检查市场状态，不创建订单

---

## 建议

1. **定期检查**：定期检查pending_orders.jsonl，确保没有遗留订单
2. **监控日志**：关注`[MARKET ORDER] WARNING`日志，及时发现异常
3. **系统重启**：系统重启后，市场关闭时会自动清理pending订单

---

## 相关文档

- `docs/MARKET_ORDER_LOGIC.md` - 市价交易逻辑说明
- `docs/POSITION_UPDATE_LOGIC.md` - 持仓更新逻辑说明

