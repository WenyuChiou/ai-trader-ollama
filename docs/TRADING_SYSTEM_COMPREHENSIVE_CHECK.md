# 交易系统全面检查报告

**检查时间**: 2025-11-14  
**检查范围**: 订单逻辑、损益计算、订单执行、历史订单处理

---

## ✅ 1. 订单管理逻辑

### 1.1 订单创建 (`place_order`)

**位置**: `backend/src/data/order_manager.py` 第 26-83 行

**逻辑**:
- ✅ 创建订单时自动移除同一日期、同一symbol和action的旧订单（确保唯一性）
- ✅ 订单状态初始为 `PENDING`
- ✅ 记录 `placed_at` 时间戳
- ✅ 使用 `order_date` 参数（今天或指定日期）

**关键字段**:
```python
{
    "order_id": f"{symbol}_{action}_{order_date}_{timestamp}",
    "symbol": symbol,
    "action": "BUY" or "SELL",
    "quantity": quantity,
    "limit_price": limit_price,
    "price_range": {"min": ..., "max": ...},
    "order_date": order_date,  # YYYY-MM-DD
    "placed_at": datetime.now().isoformat(),
    "status": "PENDING"
}
```

**状态**: ✅ **正确**

---

### 1.2 订单成交检查 (`check_order_fill`)

**位置**: `backend/src/data/order_manager.py` 第 99-400 行

**逻辑**:
- ✅ **市场关闭时**: 不检查订单，返回 `filled=False`
- ✅ **市场开放时**: 使用实时价格检查订单是否成交
- ✅ **历史订单**: 使用历史高低价检查订单是否成交
- ✅ **过去日期的订单**: 如果市场已收盘，不检查（应该已在目标日期处理）

**关键逻辑**:
```python
# 如果目标日期是今天但市场已收盘，且use_realtime=True，不应该检查订单
if is_today and not is_market_open_now and use_realtime:
    return {
        "filled": False,
        "fill_reason": "Market is closed. Orders cannot be filled after market close."
    }

# 如果目标日期是过去的日期，且市场已收盘，不应该检查订单
if target_dt < date.today() and not is_market_open_now:
    return {
        "filled": False,
        "fill_reason": "Order date is in the past and market is closed."
    }
```

**状态**: ✅ **正确**

---

### 1.3 订单标记为已成交 (`mark_order_filled`)

**位置**: `backend/src/data/order_manager.py` 第 490-550 行

**逻辑**:
- ✅ **市场未开盘**: 订单保持为PENDING状态，不标记为FILLED
- ✅ **SELL订单**: 记录已实现损益（`realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`）
- ✅ **保存完整信息**: 保存 `fill_result` 对象，包含所有成交信息
- ✅ **从pending移除**: 订单标记为FILLED后，从pending文件移除，添加到filled文件

**关键逻辑**:
```python
# 检查市场是否开盘
if not fill_result.get("filled", False):
    fill_reason = fill_result.get("fill_reason", "")
    if "Market is closed" in fill_reason:
        # 市场未开盘，保持PENDING状态
        return

# 如果是SELL订单且有已实现损益，记录到订单中
if order.get("action") == "SELL" and realized_pnl:
    order["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
    order["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
    order["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
    order["proceeds"] = realized_pnl.get("proceeds", 0.0)
```

**状态**: ✅ **正确**

---

### 1.4 订单取消 (`cancel_orders`)

**位置**: `backend/src/data/order_manager.py` 第 552-600 行

**逻辑**:
- ✅ 支持按日期取消订单
- ✅ 支持按订单ID取消订单
- ✅ 从pending文件移除订单

**状态**: ✅ **正确**

---

### 1.5 旧订单清理

**位置**: `backend/src/orchestrator/trading_cycle.py` 第 620-656 行

**逻辑**:
- ✅ **自动清理旧订单**: 清理所有昨天的pending订单
- ✅ **市场关闭时清理**: 清理今天的pending订单（市场订单不应该有pending状态）
- ✅ **防止订单堆积**: 自动清理机制防止pending订单无限累积

**关键逻辑**:
```python
# 自动清理前几个交易日遗留的订单
stale_dates = sorted({
    o.get("order_date")
    for o in all_pending_orders
    if o.get("order_date") and o.get("order_date") < today_str
})
for stale_date in stale_dates:
    cancelled = order_manager.cancel_orders(order_date=stale_date)
    if cancelled > 0:
        print(f"[TRADING CYCLE] Removed {cancelled} stale pending orders from {stale_date}")

# 如果市场关闭，清理今天的pending订单
if not is_market_open_for_simulation and len(today_orders) > 0:
    cancelled_count = order_manager.cancel_orders(order_date=today_str)
```

**状态**: ✅ **正确**

---

## ✅ 2. 损益计算逻辑

### 2.1 未实现损益 (Unrealized P&L)

**位置**: `backend/src/data/portfolio.py` 第 42-88 行

**计算公式**:
```python
# 单个持仓的未实现损益
unrealized_pnl = (current_price - avg_cost) * quantity
unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0

# 总未实现损益
total_pnl = sum((current_price - pos.avg_cost) * pos.quantity for all positions)
```

**逻辑**:
- ✅ 使用平均成本 (`avg_cost`) 计算
- ✅ 支持单个持仓和总持仓的未实现损益
- ✅ 计算持仓占比 (`position_pct`)

**状态**: ✅ **正确**

---

### 2.2 已实现损益 (Realized P&L)

**位置**: `backend/src/data/portfolio.py` 第 131-177 行

**计算公式**:
```python
# 卖出时的已实现损益
cost_basis = pos.avg_cost * amount  # 卖出部分的成本
proceeds = amount * price  # 卖出收入
realized_pnl = proceeds - cost_basis  # 已实现损益
realized_pnl_pct = (realized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
```

**逻辑**:
- ✅ **使用平均成本**: 使用持仓的平均成本计算已实现损益
- ✅ **部分卖出**: 部分卖出时，平均成本保持不变
- ✅ **全部卖出**: 全部卖出时，删除持仓
- ✅ **返回完整信息**: 返回 `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`

**关键逻辑**:
```python
def sell(self, symbol: str, amount: int, price: float) -> Dict[str, float]:
    # 计算已实现损益（使用平均成本）
    cost_basis = pos.avg_cost * amount
    proceeds = amount * price
    realized_pnl = proceeds - cost_basis
    realized_pnl_pct = (realized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
    
    # 更新持仓
    new_qty = pos.quantity - amount
    if new_qty == 0:
        # 全部卖出，删除持仓
        self._positions.pop(symbol)
    else:
        # 部分卖出，保留持仓（平均成本不变）
        self._positions[symbol] = Position(
            quantity=new_qty,
            avg_cost=pos.avg_cost,  # 平均成本保持不变
            total_cost=pos.avg_cost * new_qty,
        )
    
    return {
        "realized_pnl": realized_pnl,
        "realized_pnl_pct": realized_pnl_pct,
        "cost_basis": cost_basis,
        "proceeds": proceeds,
    }
```

**状态**: ✅ **正确**

---

### 2.3 买入时的成本计算

**位置**: `backend/src/data/portfolio.py` 第 97-129 行

**逻辑**:
- ✅ **加权平均法**: 使用加权平均法计算平均成本
- ✅ **已有持仓**: 新买入时，平均成本 = (旧总成本 + 新成本) / (旧数量 + 新数量)
- ✅ **新持仓**: 新持仓时，平均成本 = 买入价格

**计算公式**:
```python
# 已有持仓：加权平均
total_qty = existing.quantity + amount
total_cost = existing.total_cost + cost
avg_cost = total_cost / total_qty
```

**状态**: ✅ **正确**

---

### 2.4 已实现损益记录

**位置**: `backend/src/data/order_manager.py` 第 525-535 行

**逻辑**:
- ✅ **SELL订单**: 记录已实现损益到订单中
- ✅ **双重保存**: 同时保存到订单根级别和 `fill_result` 中
- ✅ **完整信息**: 保存 `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`

**状态**: ✅ **正确**

---

## ✅ 3. 订单执行逻辑

### 3.1 市场订单执行

**位置**: `backend/src/orchestrator/trading_cycle.py` 第 1134-1217 行 (BUY), 第 1264-1332 行 (SELL)

**逻辑**:
- ✅ **获取当前市价**: 使用 yfinance 获取实时价格
- ✅ **立即成交**: 市场订单保证成交，立即标记为FILLED
- ✅ **更新投资组合**: 立即更新portfolio（买入/卖出）
- ✅ **计算已实现损益**: SELL订单时计算并记录已实现损益
- ✅ **市场关闭检查**: 市场关闭时跳过订单执行

**关键逻辑**:
```python
# 只在市场开盘时执行市价交易
if not is_market_open_for_simulation:
    execution_errors.append(f"BUY {symbol} skipped: market is closed")
    continue

# 获取当前市价
current_price = info.get("lastPrice") or info.get("regularMarketPrice")

# 创建订单并立即标记为已成交
placed_order = order_manager.place_order(...)
fill_result = {"filled": True, "fill_price": current_price, ...}
order_manager.mark_order_filled(placed_order, fill_result)

# 更新投资组合
portfolio.buy(symbol, quantity, current_price)  # 或 portfolio.sell(...)
```

**状态**: ✅ **正确**

---

### 3.2 订单结算逻辑

**位置**: `backend/src/orchestrator/trading_cycle.py` 第 1400-1499 行

**逻辑**:
- ✅ **检查pending订单**: 检查今天的pending订单
- ✅ **检查成交**: 使用 `check_order_fill` 检查订单是否成交
- ✅ **执行交易**: 如果订单已成交，执行交易并更新portfolio
- ✅ **计算已实现损益**: SELL订单时计算并记录已实现损益
- ✅ **标记为已成交**: 调用 `mark_order_filled` 标记订单为FILLED

**状态**: ✅ **正确**

---

## ✅ 4. 订单日期和时间逻辑

### 4.1 订单日期设置

**位置**: `backend/src/orchestrator/trading_cycle.py` 第 280-289 行, 第 1186 行, 第 1308 行

**逻辑**:
- ✅ **市场开放时**: `order_date = date.today().isoformat()`（今天）
- ✅ **订单创建时**: 使用 `order_date=today`（今天的日期）
- ✅ **不会使用明天**: 所有订单都使用今天的日期

**状态**: ✅ **正确**

---

### 4.2 时间戳记录

**逻辑**:
- ✅ **placed_at**: 订单创建时间（ISO格式）
- ✅ **filled_at**: 订单成交时间（ISO格式）
- ✅ **order_date**: 订单日期（YYYY-MM-DD格式）

**状态**: ✅ **正确**

---

## ✅ 5. 历史订单处理

### 5.1 历史订单查询

**位置**: `backend/src/api/server.py` 第 2463-2564 行

**API端点**: `GET /api/trades/realized-pnl`

**功能**:
- ✅ 查询历史已实现损益记录
- ✅ 支持按日期查询（`date`, `start_date`, `end_date`）
- ✅ 支持限制返回数量（`limit`）
- ✅ 返回完整的已实现损益信息

**状态**: ✅ **正确**

---

### 5.2 订单历史记录

**数据文件**:
- ✅ `pending_orders.jsonl`: 待处理订单
- ✅ `filled_orders.jsonl`: 已成交订单（包含已实现损益）
- ✅ `trades.jsonl`: 交易记录

**状态**: ✅ **正确**

---

## ✅ 6. 潜在问题和建议

### 6.1 已解决的问题 ✅

1. ✅ **市场关闭时创建订单**: 已修复，市场关闭时不创建订单
2. ✅ **订单日期错误**: 已修复，所有订单使用今天的日期
3. ✅ **旧订单堆积**: 已修复，自动清理旧订单
4. ✅ **市场关闭时pending订单**: 已修复，自动清理并返回空列表

### 6.2 需要关注的点

1. **平均成本计算**: 
   - ✅ 使用加权平均法，正确
   - ✅ 部分卖出时平均成本保持不变，正确

2. **已实现损益计算**:
   - ✅ 使用平均成本计算，正确
   - ✅ SELL订单时正确记录，正确

3. **未实现损益计算**:
   - ✅ 使用当前价格和平均成本计算，正确

4. **订单状态管理**:
   - ✅ PENDING → FILLED/REJECTED，正确
   - ✅ 市场关闭时不标记为FILLED，正确

---

## 📋 检查总结

### ✅ 所有检查点通过

1. **订单管理**: ✅ 正确
2. **损益计算**: ✅ 正确
3. **订单执行**: ✅ 正确
4. **订单日期**: ✅ 正确
5. **历史订单**: ✅ 正确
6. **自动清理**: ✅ 正确

### 🔍 关键逻辑确认

**订单创建**:
- ✅ 市场开放时：创建市场订单并立即成交
- ✅ 市场关闭时：不创建订单

**损益计算**:
- ✅ 未实现损益：使用平均成本和当前价格
- ✅ 已实现损益：使用平均成本和卖出价格

**订单管理**:
- ✅ 自动清理旧订单
- ✅ 市场关闭时清理今天的pending订单
- ✅ 正确记录已实现损益

---

## ✅ 结论

**所有逻辑检查通过，系统应该正常工作。**

**建议**:
1. 定期检查 `filled_orders.jsonl` 中的已实现损益记录
2. 确认 `portfolio_state.json` 中的持仓成本正确
3. 验证未实现损益计算是否准确

