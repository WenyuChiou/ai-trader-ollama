# Order Date字段移除说明

**更新时间**: 2025-11-14  
**变更**: 移除`order_date`字段，改用`placed_at`（TIME）的日期部分

---

## 📋 变更内容

### 1. 后端变更

#### `backend/src/data/order_manager.py`

**变更**:
- ✅ `place_order`方法：移除`order_date`参数，从`placed_at`自动提取日期
- ✅ `load_pending_orders`方法：使用`placed_at`的日期部分来过滤，兼容旧的`order_date`字段
- ✅ `cancel_orders`方法：使用`placed_at`的日期部分来过滤，兼容旧的`order_date`字段

**新订单结构**:
```python
{
    "order_id": "...",
    "symbol": "...",
    "action": "BUY" or "SELL",
    "quantity": ...,
    "limit_price": ...,
    "price_range": {...},
    "placed_at": "2025-11-14T09:37:01",  # 包含完整时间戳
    "status": "PENDING"
    # 不再包含order_date字段
}
```

#### `backend/src/orchestrator/trading_cycle.py`

**变更**:
- ✅ 添加`_get_order_date()`辅助函数：从订单中提取日期（优先从`placed_at`提取，兼容旧的`order_date`字段）
- ✅ 所有调用`place_order`的地方：移除`order_date`参数
- ✅ 所有使用`order_date`的地方：改为使用`_get_order_date()`函数

#### `backend/src/api/server.py`

**变更**:
- ✅ 添加`_get_order_date()`辅助函数
- ✅ 所有使用`order_date`的地方：改为使用`_get_order_date()`函数
- ✅ `/api/trades/realized-pnl`端点：使用`placed_at`或`filled_at`的日期部分

### 2. 前端变更

#### `frontend/monitor.html`

**变更**:
- ✅ 移除"Order Date"列显示
- ✅ 所有使用`order_date`的地方：改为从`placed_at`或`filled_at`提取日期
- ✅ 兼容旧的`order_date`字段（向后兼容）

---

## ✅ 兼容性

**向后兼容**:
- ✅ 旧的订单数据（包含`order_date`字段）仍然可以正常读取
- ✅ `_get_order_date()`函数优先从`placed_at`提取日期，如果没有则使用旧的`order_date`字段
- ✅ 前端代码兼容旧的`order_date`字段

**新订单**:
- ✅ 新创建的订单不再包含`order_date`字段
- ✅ 日期信息从`placed_at`字段提取

---

## 🔄 迁移说明

**现有订单**:
- 不需要手动迁移
- 系统自动兼容旧的`order_date`字段
- 新订单会自动使用新的格式

**数据文件**:
- `pending_orders.jsonl`: 兼容新旧格式
- `filled_orders.jsonl`: 兼容新旧格式

---

## 📊 使用示例

### 获取订单日期

**Python (后端)**:
```python
from backend.src.orchestrator.trading_cycle import _get_order_date

order = {...}
order_date = _get_order_date(order)  # 返回 "2025-11-14" 或 None
```

**JavaScript (前端)**:
```javascript
const placedAt = order.placed_at || order.filled_at || '';
const orderDate = placedAt ? new Date(placedAt).toISOString().split('T')[0] : '';
```

---

## ⚠️ 注意事项

1. **时区**: `placed_at`使用ISO格式时间戳，包含时区信息
2. **日期提取**: 从`placed_at`提取日期时，使用本地时区
3. **兼容性**: 系统会优先使用`placed_at`，如果没有则使用旧的`order_date`字段

---

## ✅ 完成状态

- ✅ 后端：`order_manager.py` - 完成
- ✅ 后端：`trading_cycle.py` - 完成
- ✅ 后端：`server.py` - 完成
- ✅ 前端：`monitor.html` - 完成
- ✅ 兼容性：向后兼容旧数据 - 完成

