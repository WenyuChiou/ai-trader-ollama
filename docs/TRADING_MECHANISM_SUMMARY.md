# 交易机制统整文档

## 1. 交易流程概览

### 1.1 完整交易周期流程

```
1. 市场数据获取 (Market Data)
   ↓
2. 多分析师讨论 (Multi-Analyst Discussion)
   - Market Analyst: 市场整体趋势分析
   - Technical Analyst: 技术指标分析
   - Fundamental Analyst: 基本面分析
   - Sentiment Analyst: 市场情绪分析
   - Discussion Coordinator: 综合讨论协调
   ↓
3. 风险评估 (Risk Analyst)
   - 评估当前仓位风险
   - 检查仓位限制
   - 生成仓位控管报告
   ↓
4. 交易决策 (Trader Agent)
   - 基于讨论结果和风险报告
   - 生成BUY/SELL订单
   - 考虑现金和仓位限制
   ↓
5. 订单执行 (Order Execution)
   - 市价单：立即执行
   - 更新Portfolio状态
   - 记录P&L
```

---

## 2. 仓位信息管理

### 2.1 仓位信息存储位置

**统一存储路径**：`C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs`

#### 主要文件：

1. **`portfolio_state.json`** - 当前投资组合状态
   - 包含：`cash`, `positions`（数量、成本）
   - 更新时机：每次订单成交后

2. **`equity_history.jsonl`** - 净值历史记录
   - 包含：`cash`, `equity_value`, `total_value`, `total_pnl`, `positions`（完整仓位信息）
   - 记录时机：每次交易周期结束后，每30分钟记录一次

3. **`real_time_snapshots.jsonl`** - 实时快照
   - 包含：完整的投资组合快照
   - 记录时机：每30分钟自动记录

4. **`filled_orders.jsonl`** - 已成交订单
   - 包含：SELL订单的 `realized_pnl` 信息

### 2.2 仓位信息传递链路

```
Portfolio对象 (内存)
    ↓
current_positions_info (准备完整仓位信息)
    ├─ quantity: 持仓数量
    ├─ avg_cost: 平均成本
    ├─ current_price: 当前价格
    ├─ market_value: 市值
    ├─ unrealized_pnl: 未实现损益（金额）
    ├─ unrealized_pnl_pct: 未实现损益（百分比）
    └─ position_pct: 持仓占比（占组合净值的百分比）
    ↓
传递给 Trader Agent 和 Risk Analyst
    ↓
Agent使用仓位信息决策
    ↓
执行时再次验证
```

---

## 3. 现金检查机制

### 3.1 多层现金检查

#### 第一层：Trader Agent 内部检查

**位置**：`backend/src/agents/trader_agent.py`

```python
# _calculate_position_size() 函数
- 检查 available_cash 参数
- 如果 available_cash <= 0，直接返回0（不生成订单）
- 计算目标市值，确保不超过 available_cash
- 如果 total_cost > available_cash，减少数量或跳过
```

#### 第二层：Trading Cycle 执行前检查

**位置**：`backend/src/orchestrator/trading_cycle.py:1203-1260`

```python
# 多次现金检查
1. 使用 portfolio.cash 检查 estimated_cost
2. 在调用 portfolio.buy() 之前，再次使用 actual_cost 检查
3. 如果 actual_cost > portfolio.cash，减少数量或跳过
4. 更新 remaining_cash 使用 actual_cost 确保同步
```

#### 第三层：Portfolio 内部检查

**位置**：`backend/src/data/portfolio.py:97-115`

```python
# portfolio.buy() 方法
- 内部检查：if amount * price > self.cash: raise ValueError
- 确保不会超过可用现金
```

### 3.2 现金储备机制

```python
# 计算可用现金（考虑现金储备要求）
MIN_CASH_RESERVE_RATIO = 0.20  # 保留20%现金
required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
available_cash_for_trading = max(0, portfolio.cash - required_cash_reserve)
```

---

## 4. 仓位检查机制

### 4.1 SELL订单仓位检查

#### 第一层：Trader Agent 内部检查

**位置**：`backend/src/agents/trader_agent.py:568-652`

```python
# run_trader() 函数
- 遍历所有 current_positions
- 读取每个持仓的完整信息（数量、成本、价格、P&L、占比）
- 基于仓位信息决定卖出数量
- 确保卖出数量不超过实际持仓数量：sell_qty = min(sell_qty, qty)
```

#### 第二层：Trading Cycle 执行前检查

**位置**：`backend/src/orchestrator/trading_cycle.py:1388-1427`

```python
# 多次仓位检查
1. 从Portfolio对象读取实际持仓：pos = portfolio.get_position(symbol)
2. 检查持仓是否足够：if not pos or pos.quantity < quantity: 跳过订单
3. 再次检查：current_position = portfolio.get_position(symbol)
4. 如果持仓不足，跳过订单
```

#### 第三层：Portfolio 内部检查

**位置**：`backend/src/data/portfolio.py:117-140`

```python
# portfolio.sell() 方法
- 内部检查：if pos.quantity < amount: raise ValueError
- 确保不会卖出超过实际持仓的数量
```

---

## 5. 订单执行机制

### 5.1 市价单执行

**位置**：`backend/src/orchestrator/trading_cycle.py:1200-1450`

#### BUY订单执行流程：

```python
1. 检查现金（多次验证）
2. 执行交易：portfolio.buy(symbol, quantity, current_price)
3. 创建订单记录
4. 立即标记为FILLED（市价单）
5. 记录到filled_orders.jsonl
```

#### SELL订单执行流程：

```python
1. 检查仓位（多次验证）
2. 执行交易：portfolio.sell(symbol, quantity, current_price)
   - 返回realized_pnl信息
3. 创建订单记录（包含realized_pnl）
4. 立即标记为FILLED（市价单）
5. 记录到filled_orders.jsonl
```

### 5.2 订单状态管理

- **PENDING**: 市场关闭时不应该有pending订单（市场订单）
- **FILLED**: 市价单立即标记为FILLED
- **CANCELLED**: 市场关闭时自动取消今天的pending订单

---

## 6. P&L计算机制

### 6.1 未实现损益（Unrealized P&L）

**位置**：`backend/src/data/portfolio.py:42-56`

```python
# 计算方式
unrealized_pnl = (current_price - avg_cost) * quantity
unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0)
```

**记录位置**：
- `current_positions_info` - 传递给Agent
- `equity_history.jsonl` - 净值历史记录

### 6.2 已实现损益（Realized P&L）

**位置**：`backend/src/data/portfolio.py:117-140`

```python
# 计算方式（SELL时）
realized_pnl = (sell_price - avg_cost) * quantity
realized_pnl_pct = ((sell_price - avg_cost) / avg_cost * 100.0)
cost_basis = avg_cost * quantity
proceeds = sell_price * quantity
```

**记录位置**：
- `filled_orders.jsonl` - SELL订单记录
- `portfolio_state.json` - 投资组合状态（通过total_value变化体现）

### 6.3 加权平均成本

**位置**：`backend/src/data/portfolio.py:97-115`

```python
# BUY时计算加权平均成本
if symbol in self._positions:
    # 已有持仓：加权平均
    old_pos = self._positions[symbol]
    total_cost = old_pos.total_cost + (amount * price)
    total_quantity = old_pos.quantity + amount
    new_avg_cost = total_cost / total_quantity
else:
    # 新持仓：直接使用买入价格
    new_avg_cost = price
```

---

## 7. 市场状态检查

### 7.1 市场开放检查

**位置**：`backend/src/utils/trading_days.py`

```python
# 时区处理
- 转换为 America/New_York 时区（EST/EDT）
- 检查交易日（排除周末和节假日）
- 检查交易时间（9:30 AM - 4:00 PM ET）
```

### 7.2 交易限制

- **市场关闭时**：
  - 可以运行对话和分析（AI分析）
  - 不执行交易
  - 自动取消今天的pending订单

- **市场开放时**：
  - 执行交易
  - 市价单立即成交
  - 每30分钟执行一次交易周期

---

## 8. 订单日期逻辑

### 8.1 订单日期确定

**位置**：`backend/src/orchestrator/trading_cycle.py:600-639`

```python
# 使用 placed_at 时间戳的日期部分
- 市场开放时：使用今天日期
- 市场关闭时：不创建订单（只运行分析）
- 多日模拟时：使用 end 参数指定的日期
```

### 8.2 订单时间戳

- **`placed_at`**: ISO 8601格式，包含时区信息
- **`filled_at`**: 订单成交时间（市价单立即等于placed_at）

---

## 9. 初始化机制

### 9.1 初始化会清空的文件

**位置**：`backend/src/api/server.py:2287-2396`

清空以下文件：
- `equity_history.jsonl` - 净值历史（会重新创建初始记录）
- `filled_orders.jsonl` - 已成交订单
- `pending_orders.jsonl` - 待处理订单
- `trades.jsonl` - 交易记录
- `real_time_snapshots.jsonl` - 实时快照
- `discussion_actions.jsonl` - 对话记录（会重新创建空文件）
- `portfolio_state.json` - 投资组合状态（会重置为初始状态）
- 所有 `memory_*.jsonl` 文件

### 9.2 初始化后的状态

- 现金：$10,000
- 持仓：无
- 净值历史：只有一条初始记录（$10,000）
- 所有交易历史：清空
- 所有对话记录：清空

### 9.3 初始化后的交易行为

- **第一次交易必须手动触发**（不会自动执行）
- 自动交易会在第一次手动交易后恢复正常

---

## 10. 关键验证点

### 10.1 现金检查验证

✅ **三层检查确保不会超买**：
1. Trader Agent内部检查 `available_cash`
2. Trading Cycle执行前检查 `portfolio.cash`
3. Portfolio内部检查（`buy()`方法）

### 10.2 仓位检查验证

✅ **三层检查确保不会超卖**：
1. Trader Agent内部检查 `current_positions`
2. Trading Cycle执行前检查 `portfolio.get_position()`
3. Portfolio内部检查（`sell()`方法）

### 10.3 订单执行验证

✅ **市价单立即成交**：
- BUY订单：检查现金 → 执行交易 → 立即标记FILLED
- SELL订单：检查仓位 → 执行交易 → 立即标记FILLED（包含realized_pnl）

### 10.4 数据一致性验证

✅ **所有数据统一存储**：
- 所有文件统一存储在项目根目录的 `data/logs` 中
- 使用 `get_project_logs_dir()` 确保路径一致性
- Portfolio状态、净值历史、订单记录保持同步

---

## 11. 交易频率

- **交易周期**：每30分钟执行一次（仅市场开放时）
- **净值记录**：每30分钟记录一次
- **实时快照**：每30分钟记录一次

---

## 12. 关键代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| 准备仓位信息 | `trading_cycle.py` | 910-929 |
| 传递给Trader Agent | `trading_cycle.py` | 998 |
| BUY订单检查已有持仓 | `trader_agent.py` | 95-118 |
| SELL订单遍历持仓 | `trader_agent.py` | 570-652 |
| BUY执行前现金检查 | `trading_cycle.py` | 1203-1260 |
| SELL执行前仓位检查 | `trading_cycle.py` | 1388-1427 |
| 记录净值历史 | `trading_cycle.py` | 1792 |
| 更新portfolio状态 | `trading_cycle.py` | 800, 1694 |
| 加权平均成本计算 | `portfolio.py` | 97-115 |
| 已实现损益计算 | `portfolio.py` | 117-140 |

---

## 总结

### 核心机制：

1. **多层验证**：现金和仓位都有三层检查，确保不会超买或超卖
2. **市价单执行**：所有订单都是市价单，立即成交
3. **完整仓位信息**：Agent接收完整的仓位信息（数量、成本、价格、P&L、占比）
4. **统一数据存储**：所有数据统一存储在项目根目录的 `data/logs` 中
5. **市场状态检查**：市场关闭时不执行交易，只运行分析
6. **P&L计算**：支持未实现和已实现损益的完整计算

### 安全保障：

- ✅ 不会超买（三层现金检查）
- ✅ 不会超卖（三层仓位检查）
- ✅ 市价单立即成交（不会pending）
- ✅ 市场关闭时自动取消pending订单
- ✅ 数据一致性（统一存储路径）

