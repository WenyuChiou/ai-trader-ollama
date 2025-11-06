# 测试与数据保留指南

## 📋 概述

本文档说明系统的数据保留策略和开盘/未开盘逻辑的测试方法。

---

## 🔒 数据保留策略

### ✅ 必须保留的数据（除了初始化外，永远不删除）

1. **交易记录** (`trades.jsonl`)
   - 所有已执行的交易
   - 记录：symbol, action, price, quantity, status, timestamp

2. **持仓记录** (`portfolio_state.json`)
   - 当前现金余额
   - 所有持仓（symbol, quantity, avg_cost, total_cost）
   - 总价值和P&L

3. **净值记录** (`equity_history.jsonl`)
   - 每日净值快照
   - 用于图表显示和历史分析

4. **对话记录** (`discussion_actions.jsonl`)
   - AI Agent的对话内容
   - **作为Memory保留**，用于后续分析

5. **订单记录**
   - `filled_orders.jsonl`: 已成交订单
   - `pending_orders.jsonl`: 挂单

### ❌ 唯一会删除数据的地方

**只有 `/api/system/init` 会删除数据**（这是正常的初始化功能）

- 位置：`backend/src/api/server.py:1275`
- 用途：重置系统到初始状态
- 会删除：所有日志文件、memory文件、持仓状态

---

## ⏰ 开盘/未开盘逻辑

### 市场时间定义

- **开盘时间**: 周一至周五 9:30 AM - 4:00 PM（本地时间）
- **判断逻辑**: 
  ```python
  is_weekday = now.weekday() < 5  # 0-4 = 周一到周五
  market_open_time = time(9, 30)
  market_close_time = time(16, 0)
  is_market_open = is_weekday and (market_open_time <= now.time() <= market_close_time)
  ```

### 未开盘时的行为

**API (`/api/portfolio/real-time`)**:
- ✅ 返回 `source: "static_after_hours"`
- ✅ **不调用** `RealTimeTracker`（避免无效的API调用）
- ✅ 使用 `portfolio_state.json` 中的保存数据
- ✅ 使用保存的 `current_price`（如果没有，使用 `avg_cost`）
- ✅ 可以记录净值，但**只记录一次**（如果今天还没有记录）

**交易周期 (`execute_daily_trade`)**:
- ✅ 订单日期设为**明天**（或下一个交易日）
- ✅ 创建**限价单**，不立即执行
- ✅ 保存到 `pending_orders.jsonl`
- ✅ **不更新持仓**（等待明天开盘后执行）
- ✅ 如果明天已有订单，跳过创建新订单

### 开盘时的行为

**API (`/api/portfolio/real-time`)**:
- ✅ 返回 `source: "realtime"` 或 `"fallback_realtime"`
- ✅ **调用** `RealTimeTracker` 更新实时价格
- ✅ 如果 `RealTimeTracker` 失败，使用 `fetch_market_batch` 手动获取价格
- ✅ 定期记录净值（每30秒或净值变化超过0.5%）
- ✅ 返回实时计算的P&L

**交易周期 (`execute_daily_trade`)**:
- ✅ 订单日期设为**今天**
- ✅ **先检查今天的pending订单**，如果满足成交条件就执行
- ✅ 执行新订单（**市价单**，立即成交）
- ✅ **立即更新持仓和现金**
- ✅ 保存到 `portfolio_state.json`

---

## 🧪 测试计划

### 测试1: 数据保留

**目标**: 确认除了初始化外，所有记录都不被删除

**测试步骤**:
1. 运行交易周期，生成一些数据
2. 检查关键文件是否存在：
   - `portfolio_state.json`
   - `filled_orders.jsonl`
   - `discussion_actions.jsonl`
   - `equity_history.jsonl`
   - `trades.jsonl`
3. **不调用** `/api/system/init`
4. 再次运行交易周期
5. 验证所有记录都**保留**（新记录追加，旧记录不删除）

**预期结果**:
- ✅ 所有文件都存在
- ✅ 记录数量**增加**（不是减少或清零）

### 测试2: 开盘/未开盘逻辑

**目标**: 确认不同市场状态下的行为差异

**测试步骤**:

#### 2.1 未开盘时测试
1. 在非交易时段（例如晚上8点）运行
2. 调用 `/api/portfolio/real-time`
3. 检查返回的 `source` 字段
4. 检查是否调用 `RealTimeTracker`
5. 运行交易周期，检查订单日期

**预期结果**:
- ✅ `source: "static_after_hours"`
- ✅ **不调用** `RealTimeTracker`
- ✅ 订单日期是明天

#### 2.2 开盘时测试
1. 在交易时段（例如中午12点）运行
2. 调用 `/api/portfolio/real-time`
3. 检查返回的 `source` 字段
4. 检查是否调用 `RealTimeTracker`
5. 运行交易周期，检查订单日期和执行

**预期结果**:
- ✅ `source: "realtime"` 或 `"fallback_realtime"`
- ✅ **调用** `RealTimeTracker` 或 `fetch_market_batch`
- ✅ 订单日期是今天
- ✅ 订单立即执行

### 测试3: 交易周期行为

**目标**: 确认开盘时立即执行，未开盘时创建限价单

**测试步骤**:

#### 3.1 未开盘时
1. 在非交易时段运行交易周期
2. 检查 `pending_orders.jsonl` 是否有新订单
3. 检查订单的 `order_date` 是否为明天
4. 检查 `portfolio_state.json` 是否**未更新**持仓

**预期结果**:
- ✅ 创建限价单到 `pending_orders.jsonl`
- ✅ `order_date` 是明天
- ✅ 持仓**未更新**

#### 3.2 开盘时
1. 在交易时段运行交易周期
2. 检查是否有pending订单被执行
3. 检查新订单是否立即执行
4. 检查 `portfolio_state.json` 是否**已更新**持仓

**预期结果**:
- ✅ Pending订单如果满足条件会被执行
- ✅ 新订单立即执行（市价单）
- ✅ 持仓**已更新**

### 测试4: API响应差异

**目标**: 确认API在不同市场状态下的响应差异

**测试步骤**:
1. 在未开盘时调用 `/api/portfolio/real-time`
2. 记录响应中的 `source`、`positions`、`cash`
3. 在开盘时调用 `/api/portfolio/real-time`
4. 对比两次响应的差异

**预期结果**:
- ✅ 未开盘：`source: "static_after_hours"`，使用保存的价格
- ✅ 开盘：`source: "realtime"`，使用实时价格
- ✅ 开盘时的价格可能与未开盘时不同（如果市场有变化）

### 测试5: Memory（对话）保留

**目标**: 确认对话记录作为Memory保留

**测试步骤**:
1. 运行交易周期，生成对话
2. 检查 `discussion_actions.jsonl` 是否有记录
3. 再次运行交易周期（**不调用init**）
4. 检查对话记录是否**保留**（追加，不删除）

**预期结果**:
- ✅ 对话记录**保留**
- ✅ 新对话**追加**到文件
- ✅ 旧对话**不删除**

---

## 🚀 运行测试

```bash
# 运行综合测试
cd backend/scripts
python test_comprehensive.py
```

---

## 📝 关键代码位置

### 开盘/未开盘判断
- `backend/src/api/server.py:419-424` - API判断逻辑
- `backend/src/orchestrator/trading_cycle.py:574-579` - 交易周期判断逻辑
- `backend/src/data/order_manager.py:85-108` - OrderManager判断逻辑

### 数据保留
- `backend/src/api/server.py:1275-1323` - 唯一会删除数据的地方（`/api/system/init`）
- 所有其他代码都使用**追加模式**（`open("a")`）或**覆盖单个文件**（不删除历史）

### 净值记录
- `backend/src/api/server.py:698-795` - 净值记录逻辑
  - 未开盘：只记录一次（如果今天还没有记录）
  - 开盘：每30秒或净值变化超过0.5%时记录

---

## ✅ 总结

1. **数据保留**: ✅ 除了 `/api/system/init`，所有记录都保留
2. **开盘/未开盘逻辑**: ✅ 已正确区分
   - 未开盘：静态快照，创建限价单
   - 开盘：实时数据，立即执行
3. **Memory保留**: ✅ 对话记录作为Memory保留
4. **测试覆盖**: ✅ 已创建综合测试脚本

