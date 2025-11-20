# 实时数据不一致问题分析

## 问题描述

用户报告：有时候有实时数据，有时候没有。

## 数据流分析

### 1. 前端数据获取流程

```
前端每30秒刷新
  ↓
调用 /api/portfolio/real-time
  ↓
获取 portfolio 对象（包含 positions_detail）
  ↓
每30分钟记录净值
  ↓
调用 recordEquityToBackend(latestPoint)
  ↓
POST /api/portfolio/record-equity
  ↓
equity_tracker.record_daily_equity()
```

### 2. 后端价格获取流程

`/api/portfolio/real-time` 端点：
1. 加载 `portfolio_state.json`
2. 获取持仓列表
3. **尝试获取实时价格**（可能失败）
4. 构建 `positions_detail` 对象
5. 返回给前端

### 3. 问题根源

#### 问题1: 价格获取可能失败

在 `server.py` 的 `/api/portfolio/real-time` 端点中：

```python
# 尝试多种方法获取价格
try:
    # 方法1: yfinance history
    # 方法2: yfinance info
    # 方法3: fetch_market_batch
except:
    # 如果失败，使用 avg_cost 作为占位符
    last_prices[symbol] = portfolio._positions[symbol].avg_cost
```

**问题**：如果价格获取失败，`positions_detail` 中可能：
- 没有 `current_price` 字段
- 或者 `current_price` = `avg_cost`（占位符）

#### 问题2: 前端记录时使用不完整数据

前端在 `refreshData()` 中构建 `latestPoint`：

```javascript
const latestPoint = {
    date: today,
    timestamp: timestamp,
    value: portfolio.total_value,
    total_value: portfolio.total_value,
    cash: portfolio.cash || 0,
    equity_value: portfolio.equity_value || 0,
    total_pnl: portfolio.total_pnl || 0,
    total_pnl_pct: portfolio.total_pnl_pct || 0,
    positions: portfolio.positions || {},  // ⚠️ 可能缺少 current_price
};
```

**问题**：`latestPoint.positions` 可能：
- 使用 `portfolio.positions`（旧格式，只有数量）
- 或者 `portfolio.positions_detail` 中某些持仓缺少 `current_price`

#### 问题3: 后端记录时价格获取逻辑

虽然我在 `equity_tracker.py` 中添加了价格获取逻辑，但：

```python
# 检查 positions 是否缺少价格
if current_price is None or (current_price == avg_cost and avg_cost > 0):
    # 获取实时价格
```

**问题**：如果前端传递的 `positions` 是旧格式（只有数量），这个检查可能无法正确工作。

## 解决方案

### 方案1: 前端传递完整的 positions_detail

修改前端 `latestPoint` 构建逻辑：

```javascript
const latestPoint = {
    // ... 其他字段
    positions: portfolio.positions_detail || portfolio.positions || {},
    // 确保传递 positions_detail（包含完整信息）
};
```

### 方案2: 后端记录时强制获取价格

在 `equity_tracker.record_daily_equity()` 中：
- 如果 `positions` 是旧格式（只有数量），从 `portfolio_state.json` 加载持仓
- 强制获取所有持仓的实时价格
- 重新构建完整的 `positions_detail`

### 方案3: API 端点确保返回完整数据

在 `/api/portfolio/real-time` 中：
- 确保所有持仓都有 `current_price`
- 如果价格获取失败，明确标记（而不是使用占位符）
- 添加重试机制

## 推荐方案

**组合方案1和方案2**：
1. 前端确保传递 `positions_detail`（包含完整信息）
2. 后端记录时验证并补充缺失的价格信息
3. 添加日志记录价格获取状态

## 实施步骤

1. ✅ 后端：`equity_tracker.py` 已添加价格获取逻辑
2. ⏳ 前端：修改 `latestPoint` 构建，使用 `positions_detail`
3. ⏳ 后端：改进价格获取失败时的处理逻辑
4. ⏳ 添加日志记录，便于调试

---

**最后更新**: 2025-01-28

