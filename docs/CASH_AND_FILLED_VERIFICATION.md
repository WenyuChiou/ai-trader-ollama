# 现金检查和FILLED状态验证

**更新时间**: 2025-11-14  
**问题**: 确认买进和卖出都有考虑现金/持仓，以及市价单都正确标记为FILLED

---

## ✅ 买进订单现金检查

### 检查逻辑

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1185-1194行

**检查流程**:
1. ✅ **使用实际portfolio.cash检查**（不是remaining_cash变量）
2. ✅ **如果现金不足，减少数量或跳过**
3. ✅ **先执行交易（portfolio.buy），成功后再创建订单**
4. ✅ **portfolio.buy()内部也有现金检查**（双重保险）

**代码**:
```python
# CRITICAL: 使用实际portfolio.cash检查，确保现金同步
if estimated_cost > portfolio.cash:
    max_affordable_qty = floor(portfolio.cash / current_price)
    if max_affordable_qty > 0:
        quantity = max_affordable_qty
        estimated_cost = current_price * quantity
        print(f"[MARKET ORDER] Reduced {symbol} quantity to {quantity} due to cash limit")
    else:
        execution_errors.append(f"BUY {symbol} skipped: insufficient cash")
        continue

# CRITICAL: 先执行交易，成功后再创建订单
portfolio.buy(symbol, quantity, current_price)  # 内部也有现金检查
```

**portfolio.buy()内部检查**:
```python
def buy(self, symbol: str, amount: int, price: float) -> None:
    cost = amount * price
    if cost > self.cash:
        raise ValueError(f"Insufficient cash: need {cost:.2f}, have {self.cash:.2f}")
    self.cash -= cost
    # ... 更新持仓
```

**结论**: ✅ **买进订单有双重现金检查**（执行前检查 + portfolio.buy内部检查）

---

## ✅ 卖出订单持仓检查

### 检查逻辑

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1315-1321行

**检查流程**:
1. ✅ **先检查持仓是否足够**
2. ✅ **如果持仓不足，跳过订单**
3. ✅ **先执行交易（portfolio.sell），成功后再创建订单**
4. ✅ **portfolio.sell()内部也有持仓检查**（双重保险）

**代码**:
```python
# CRITICAL FIX: 先检查持仓，再创建订单和执行交易
current_position = portfolio.get_position(symbol)
if not current_position or current_position.quantity < quantity:
    available_qty = current_position.quantity if current_position else 0
    execution_errors.append(f"SELL {symbol} skipped: insufficient shares (need {quantity}, have {available_qty})")
    continue

# 先执行交易以获取realized_pnl（在创建订单前）
realized_pnl = portfolio.sell(symbol, quantity, current_price)
```

**portfolio.sell()内部检查**:
```python
def sell(self, symbol: str, amount: int, price: float) -> Dict[str, float]:
    pos = self._positions.get(symbol)
    if pos is None:
        raise ValueError(f"No position for {symbol}")
    if amount > pos.quantity:
        raise ValueError(f"Insufficient shares: need {amount}, have {pos.quantity}")
    # ... 执行卖出
```

**结论**: ✅ **卖出订单有双重持仓检查**（执行前检查 + portfolio.sell内部检查）

**注意**: 卖出不需要现金检查（卖出是增加现金，不是消耗现金）

---

## ✅ 市价单FILLED状态

### BUY订单FILLED标记

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1217-1226行

**流程**:
1. ✅ 先执行交易（`portfolio.buy()`）
2. ✅ 创建订单记录
3. ✅ **立即标记为FILLED**（`fill_result["filled"] = True`）
4. ✅ 调用`mark_order_filled()`保存到filled_orders.jsonl

**代码**:
```python
# 立即标记为已成交（市价单保证成交）
fill_result = {
    "filled": True,  # ✅ 明确标记为已成交
    "fill_price": current_price,
    "fill_reason": "Market order executed immediately at current price",
    ...
}
order_manager.mark_order_filled(placed_order, fill_result)
```

**结论**: ✅ **BUY订单立即标记为FILLED**

---

### SELL订单FILLED标记

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1339-1349行

**流程**:
1. ✅ 先执行交易（`portfolio.sell()`）
2. ✅ 创建订单记录
3. ✅ **立即标记为FILLED**（`fill_result["filled"] = True`）
4. ✅ 调用`mark_order_filled()`保存到filled_orders.jsonl（包含realized_pnl）

**代码**:
```python
# 立即标记为已成交（市价单保证成交）
fill_result = {
    "filled": True,  # ✅ 明确标记为已成交
    "fill_price": current_price,
    "fill_reason": "Market order executed immediately at current price",
    ...
}
order_manager.mark_order_filled(placed_order, fill_result, realized_pnl=realized_pnl)
```

**结论**: ✅ **SELL订单立即标记为FILLED**

---

## 🔍 潜在问题检查

### 问题1: 如果portfolio.buy()或portfolio.sell()失败？

**当前处理**:
- ✅ 如果`portfolio.buy()`失败（现金不足），会抛出异常
- ✅ 异常被捕获，订单不会创建
- ✅ 如果`portfolio.sell()`失败（持仓不足），会抛出异常
- ✅ 异常被捕获，订单不会创建

**代码位置**: `backend/src/orchestrator/trading_cycle.py` 第1243-1254行（BUY），第1358-1369行（SELL）

**结论**: ✅ **如果交易失败，订单不会创建，不会出现PENDING状态**

---

### 问题2: 如果mark_order_filled()失败？

**当前处理**:
- ⚠️ 如果`mark_order_filled()`失败，订单可能保持PENDING状态
- ⚠️ 但交易已经执行（portfolio已更新）

**潜在问题**:
- 如果`mark_order_filled()`抛出异常，订单会保持PENDING状态
- 但实际交易已经执行（portfolio已更新）

**建议改进**:
- 添加异常处理，确保即使`mark_order_filled()`失败，也能正确处理
- 或者：先创建订单，再执行交易，最后标记为FILLED（但这样如果交易失败，订单会保持PENDING）

**当前设计**:
- 先执行交易，再创建订单，最后标记为FILLED
- 优点：如果交易失败，不会创建订单
- 缺点：如果`mark_order_filled()`失败，订单可能保持PENDING（但交易已执行）

---

## 📋 验证清单

### 买进订单

- [x] **现金检查**: 使用`portfolio.cash`检查（第1186行）
- [x] **双重检查**: `portfolio.buy()`内部也有检查（第103行）
- [x] **执行顺序**: 先执行交易，再创建订单（第1198行）
- [x] **FILLED标记**: 立即标记为FILLED（第1218-1226行）
- [x] **异常处理**: 如果失败，订单不会创建（第1243行）

### 卖出订单

- [x] **持仓检查**: 先检查持仓数量（第1317行）
- [x] **双重检查**: `portfolio.sell()`内部也有检查（第145行）
- [x] **执行顺序**: 先执行交易，再创建订单（第1325行）
- [x] **FILLED标记**: 立即标记为FILLED（第1340-1349行）
- [x] **异常处理**: 如果失败，订单不会创建（第1358行）

### 市价单特性

- [x] **立即成交**: 所有订单都是市价单，立即成交
- [x] **FILLED状态**: 所有订单都立即标记为FILLED
- [x] **不应该有PENDING**: 市价单不应该有PENDING状态

---

## ⚠️ 已知问题

### 问题：如果mark_order_filled()失败

**场景**:
1. 交易执行成功（portfolio已更新）
2. 订单创建成功
3. `mark_order_filled()`失败（例如：文件写入失败）

**结果**:
- 订单保持PENDING状态
- 但实际交易已执行

**解决方案**:
- 添加异常处理和重试机制
- 或者：在订单创建时直接设置status="FILLED"

---

## ✅ 总结

### 买进订单

- ✅ **现金检查**: 双重检查（执行前 + portfolio.buy内部）
- ✅ **FILLED标记**: 立即标记为FILLED
- ✅ **不应该有PENDING**: 市价单立即成交

### 卖出订单

- ✅ **持仓检查**: 双重检查（执行前 + portfolio.sell内部）
- ✅ **FILLED标记**: 立即标记为FILLED
- ✅ **不应该有PENDING**: 市价单立即成交

### 市价单特性

- ✅ **所有订单都是市价单**: 使用当前价格立即成交
- ✅ **所有订单都立即标记为FILLED**: `fill_result["filled"] = True`
- ✅ **不应该有PENDING状态**: 如果出现PENDING，说明有问题

---

**文档创建时间**: 2025-11-14  
**状态**: ✅ 已验证

