# SELL订单PENDING问题修复

**修复时间**: 2025-11-14  
**问题**: SELL订单显示为PENDING状态，而不是FILLED

---

## 🔍 问题分析

### 问题1: SELL订单未正确标记为FILLED

**发现**:
- 26个SELL订单在市场开放时（9:37 AM）创建
- 所有订单都是PENDING状态
- 所有订单都没有`fill_result`字段
- 说明`mark_order_filled`没有被调用，或者调用失败

**根本原因**:
在`backend/src/orchestrator/trading_cycle.py`第1320行，代码先调用`mark_order_filled`，然后才调用`portfolio.sell`。这导致：
1. `mark_order_filled`被调用时，`realized_pnl`还没有计算
2. 如果`portfolio.sell`抛出异常，订单已经创建但不会被标记为FILLED

**修复**:
- 先执行`portfolio.sell`获取`realized_pnl`
- 然后将`realized_pnl`传递给`mark_order_filled`
- 确保SELL订单正确记录已实现损益

### 问题2: 注释过时（"每5分钟"）

**发现**:
- `frontend/monitor.html`第2966行注释写的是"每5分钟"
- 但实际代码是30分钟（`TRADING_INTERVAL = 30 * 60 * 1000`）

**修复**:
- 更新注释为"每30分钟"

---

## ✅ 修复内容

### 1. SELL订单执行顺序修复

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1311-1324行

**修复前**:
```python
# 立即标记为已成交（市价单保证成交）
fill_result = {...}
order_manager.mark_order_filled(placed_order, fill_result)

# 更新投资组合（立即执行交易）
portfolio.sell(symbol, quantity, current_price)
```

**修复后**:
```python
# 更新投资组合（立即执行交易）- 先执行交易以获取realized_pnl
realized_pnl = portfolio.sell(symbol, quantity, current_price)

# 立即标记为已成交（市价单保证成交）
fill_result = {...}
# CRITICAL FIX: 传递realized_pnl给mark_order_filled，确保SELL订单正确记录已实现损益
order_manager.mark_order_filled(placed_order, fill_result, realized_pnl=realized_pnl)
```

### 2. 注释更新

**位置**: `frontend/monitor.html` 第2966行

**修复前**:
```javascript
// Trading hours: execute trade cycle every 5 minutes
```

**修复后**:
```javascript
// Trading hours: execute trade cycle every 30 minutes
```

---

## 📋 关于现有PENDING订单

**现有26个SELL订单**:
- 这些订单是在修复之前创建的（旧代码）
- 它们应该被清理或手动处理

**建议**:
1. **清理旧订单**: 使用`/api/trading/check-pending-orders`端点检查并结算这些订单
2. **或者**: 等待市场开放时，系统会自动检查并结算这些订单
3. **或者**: 手动清理这些订单（如果确认它们不应该存在）

---

## 🔄 下一步

1. **重启API**: 应用修复后，需要重启API服务器
2. **测试**: 市场开放时，创建新的SELL订单，确认它们立即被标记为FILLED
3. **清理**: 处理现有的26个PENDING SELL订单

---

## ⚠️ 重要说明

### 交易频率

**实际设置**:
- **自动交易**: 每30分钟执行一次（市场开放时）
- **数据刷新**: 每30秒刷新一次（独立于交易循环）
- **订单检查**: 每10秒检查一次pending订单（市场开放时）

**用户看到的"5分钟"**:
- 这是旧的注释，已修复
- 实际交易频率是30分钟，不是5分钟

### SELL订单执行流程

**修复后的流程**:
1. 创建订单（`place_order`）
2. 执行交易（`portfolio.sell`）→ 获取`realized_pnl`
3. 标记为已成交（`mark_order_filled`，传递`realized_pnl`）
4. 订单从pending移动到filled

**确保**:
- ✅ SELL订单立即被标记为FILLED
- ✅ 已实现损益正确记录
- ✅ 订单状态正确更新

