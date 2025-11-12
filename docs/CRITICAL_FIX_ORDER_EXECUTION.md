# 关键修复：订单执行和净值计算问题

## 问题描述

用户报告了两个严重问题：
1. **净值异常上升到两倍**（从 $10,000 到 $19,300）
2. **没有现金却还能买进**

## 根本原因

### 问题1：恢复持仓时现金未正确扣除

在 `check_pending_orders` 函数中，如果 portfolio 中没有持仓，系统会从 `filled_orders.jsonl` 重新执行订单来恢复持仓。但是：

- **错误做法**：调用 `current_portfolio.buy()` 重新执行订单
  - 这会导致现金被重复扣除（如果 `portfolio_state.json` 中的现金还是初始值）
  - 或者持仓数量翻倍（如果现金已经被扣除过）

### 问题2：订单可能重复执行

- 如果 `check_pending_orders` 被多次调用（前端每10秒调用一次），可能会在订单还没有被标记为 FILLED 之前，多次检查同一个订单
- 虽然 `mark_order_filled` 会将订单从 `pending_orders.jsonl` 中移除，但在并发情况下，可能会重复执行

## 修复方案

### 修复1：正确恢复持仓和现金

**旧逻辑**（错误）：
```python
# 重新执行订单（会导致现金重复扣除）
if action == "BUY":
    current_portfolio.buy(symbol, quantity, fill_price)
```

**新逻辑**（正确）：
```python
# 从 filled_orders 计算正确的现金和持仓，而不是重新执行订单
# 1. 计算总买入成本和总卖出收益
total_buy_cost = sum(quantity * fill_price for BUY orders)
total_sell_proceeds = sum(quantity * fill_price for SELL orders)

# 2. 计算正确的现金
correct_cash = initial_value - total_buy_cost + total_sell_proceeds

# 3. 直接设置持仓（不调用 buy/sell）
current_portfolio.cash = correct_cash
current_portfolio._positions[symbol] = Position(...)
```

### 修复2：防止订单重复执行

**添加检查**：
1. 在执行订单前，检查订单是否已经在 `filled_orders.jsonl` 中
2. 在执行 BUY 订单前，再次检查现金是否足够

```python
# 检查订单是否已经成交
if order_id in filled_orders:
    continue  # 跳过，防止重复执行

# 执行前检查现金
if action == "BUY":
    cost = quantity * fill_price
    if cost > current_portfolio.cash:
        continue  # 跳过，防止现金为负
```

## 修复后的行为

1. **恢复持仓时**：
   - 从 `filled_orders.jsonl` 计算正确的现金和持仓
   - 不会重复扣除现金
   - 不会重复添加持仓

2. **订单执行时**：
   - 检查订单是否已经成交，防止重复执行
   - 检查现金是否足够，防止现金为负
   - 确保每个订单只执行一次

3. **净值计算**：
   - 现金 = 初始现金 - 买入成本 + 卖出收益
   - 净值 = 现金 + 持仓市值
   - 确保现金和持仓正确同步

## 测试建议

1. **测试恢复持仓**：
   - 清空 `portfolio_state.json` 中的持仓
   - 确保 `filled_orders.jsonl` 中有今天的订单
   - 调用 `check_pending_orders`
   - 验证现金和持仓是否正确恢复

2. **测试防止重复执行**：
   - 快速多次调用 `check_pending_orders`
   - 验证每个订单只执行一次
   - 验证现金不会变成负数

3. **测试净值计算**：
   - 执行一些买入订单
   - 验证净值 = 现金 + 持仓市值
   - 验证净值不会异常上升

## 相关文件

- `backend/src/api/server.py` (第 772-945 行)
- `backend/src/data/portfolio.py` (buy/sell 方法)
- `backend/src/data/order_manager.py` (mark_order_filled 方法)

## 注意事项

- 如果 `portfolio_state.json` 中的现金已经是负数，需要手动修复
- 如果持仓数量异常，需要从 `filled_orders.jsonl` 重新计算
- 建议定期备份 `portfolio_state.json` 和 `filled_orders.jsonl`

