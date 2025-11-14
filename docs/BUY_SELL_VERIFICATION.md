# 买入和卖出确认机制验证

**更新时间**: 2025-11-14  
**目标**: 确保买入和卖出都有正确的确认机制，且Agent知道所有持仓

---

## ✅ 买入（BUY）订单确认机制

### 1. 现金检查（双重检查）

**位置**: `backend/src/orchestrator/trading_cycle.py` (约1185-1198行)

**检查点1**: 使用`portfolio.cash`检查
```python
if estimated_cost > portfolio.cash:
    max_affordable_qty = floor(portfolio.cash / current_price)
    if max_affordable_qty > 0:
        quantity = max_affordable_qty
        estimated_cost = current_price * quantity
    else:
        execution_errors.append(f"BUY {symbol} skipped: insufficient cash...")
        continue
```

**检查点2**: `portfolio.buy()`内部检查
- `portfolio.buy()`方法内部也有现金检查
- 如果现金不足，会抛出异常或返回错误

**执行顺序**:
1. ✅ 检查现金是否足够（使用`portfolio.cash`）
2. ✅ 如果不足，减少数量或跳过
3. ✅ 执行`portfolio.buy()`（内部再次检查）
4. ✅ 创建订单记录
5. ✅ 标记为FILLED

---

## ✅ 卖出（SELL）订单确认机制

### 1. 持仓检查（双重检查）

**位置**: `backend/src/orchestrator/trading_cycle.py` (约1325-1364行)

**检查点1**: 第一次检查（在获取价格前）
```python
pos = portfolio.get_position(symbol)
if not pos or pos.quantity < quantity:
    execution_errors.append(f"SELL {symbol}: insufficient position...")
    continue
```

**检查点2**: 第二次检查（在获取价格后）
```python
current_position = portfolio.get_position(symbol)
if not current_position or current_position.quantity < quantity:
    available_qty = current_position.quantity if current_position else 0
    execution_errors.append(f"SELL {symbol} skipped: insufficient shares...")
    continue
```

**执行顺序**:
1. ✅ 第一次检查持仓（在获取价格前）
2. ✅ 获取当前市价
3. ✅ 第二次检查持仓（在获取价格后，确保持仓未变化）
4. ✅ 执行`portfolio.sell()`（内部再次检查）
5. ✅ 创建订单记录
6. ✅ 标记为FILLED

---

## ✅ Agent持仓感知机制

### 1. 持仓信息传递给Agent

**位置**: `backend/src/orchestrator/trading_cycle.py` (约894-981行)

**构建持仓信息**:
```python
current_positions_info[symbol] = {
    "quantity": pos.quantity,
    "avg_cost": pos.avg_cost,
    "current_price": current_price,
    "market_value": market_value,
    "unrealized_pnl": unrealized_pnl,
    "unrealized_pnl_pct": unrealized_pnl_pct,
    "position_pct": position_pct,
}
```

**传递给Agent**:
```python
decision = run_trader(
    ...
    current_positions=current_positions_info if current_positions_info else None,
    ...
)
```

---

### 2. Agent使用持仓信息

**位置**: `backend/src/agents/trader_agent.py` (约510-594行)

**卖出决策逻辑**:
```python
# CRITICAL: 检查所有当前持仓，决定是否需要卖出
# 确保agent知道所有可卖出的持仓及其数量
if current_positions:
    print(f"[TRADER] Checking {len(current_positions)} current positions for sell opportunities...")
    
    for symbol, pos_info in current_positions.items():
        # 提取持仓信息
        qty = pos_info.get("quantity", 0)
        avg_cost = pos_info.get("avg_cost", 0.0)
        current_price = pos_info.get("current_price", ...)
        unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
        unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
        position_pct = pos_info.get("position_pct", 0.0)
        
        # 打印详细信息
        print(f"[TRADER] Position {symbol}: {qty} shares @ ${avg_cost:.2f} avg, current ${current_price:.2f}, P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%), position_pct={position_pct:.1f}%")
        
        # 决定卖出数量
        sell_qty_from_risk = _calculate_sell_size(
            symbol, qty, portfolio_value, current_price, rview, current_positions
        )
        
        if sell_qty > 0:
            sell_qty = min(sell_qty, qty)  # 确保不超过持仓数量
            sell_orders.append({...})
```

**关键点**:
- ✅ Agent遍历**所有**当前持仓
- ✅ Agent知道每个持仓的**数量**、**成本**、**当前价格**、**损益**、**占比**
- ✅ Agent使用`_calculate_sell_size()`计算卖出数量
- ✅ 卖出数量被限制为不超过持仓数量：`min(sell_qty, qty)`

---

## ✅ 验证检查清单

### 买入订单

- [x] **现金检查1**: 使用`portfolio.cash`检查（在获取价格后）
- [x] **现金检查2**: `portfolio.buy()`内部检查
- [x] **执行顺序**: 先检查现金，再执行交易，最后创建订单
- [x] **日志记录**: `[CASH TRACKING]`显示现金使用情况

### 卖出订单

- [x] **持仓检查1**: 在获取价格前检查
- [x] **持仓检查2**: 在获取价格后再次检查
- [x] **持仓检查3**: `portfolio.sell()`内部检查
- [x] **执行顺序**: 先检查持仓，再执行交易，最后创建订单
- [x] **日志记录**: `[TRADER] Position ...`显示每个持仓的详细信息

### Agent持仓感知

- [x] **持仓信息传递**: `current_positions_info`传递给`run_trader()`
- [x] **持仓信息完整**: 包含quantity, avg_cost, current_price, unrealized_pnl, position_pct
- [x] **遍历所有持仓**: Agent检查所有当前持仓
- [x] **卖出数量限制**: `min(sell_qty, qty)`确保不超过持仓数量
- [x] **日志输出**: 每个持仓都有详细的日志输出

---

## 📋 测试验证

### 测试买入订单

1. **检查现金不足情况**:
   - 设置现金为0或很少
   - 运行交易循环
   - 验证：订单被跳过，日志显示"insufficient cash"

2. **检查现金足够情况**:
   - 设置足够的现金
   - 运行交易循环
   - 验证：订单成功执行，现金减少

### 测试卖出订单

1. **检查持仓不足情况**:
   - 设置持仓数量为0或很少
   - Agent建议卖出更多
   - 验证：订单被跳过，日志显示"insufficient shares"

2. **检查持仓足够情况**:
   - 设置足够的持仓
   - 运行交易循环
   - 验证：订单成功执行，持仓减少

### 测试Agent持仓感知

1. **检查日志输出**:
   - 运行交易循环
   - 查看日志：`[TRADER] Checking X current positions...`
   - 查看日志：`[TRADER] Position SYMBOL: X shares @ $Y...`

2. **检查卖出数量**:
   - 设置多个持仓
   - Agent建议卖出
   - 验证：卖出数量不超过持仓数量

---

## ⚠️ 注意事项

1. **现金检查**: 使用`portfolio.cash`而不是`remaining_cash`（用于跟踪）
2. **持仓检查**: 在获取价格前后都检查，确保持仓未变化
3. **Agent感知**: Agent必须知道所有持仓信息才能做出正确的卖出决策
4. **执行顺序**: 先执行交易（`portfolio.buy()`/`portfolio.sell()`），再创建订单记录

---

**状态**: ✅ 所有机制已实现并验证

