# Agents Registered 和存储路径验证报告

## 1. Agents Registered 问题分析

### 问题描述
前端显示 "Agents Registered: 1"，但 `agents.yaml` 中定义了8个agents。

### 原因分析
前端从 `/api/agents/status` 获取agents数量：
```javascript
// frontend/monitor.html:3367
const agentCount = Object.keys(agentStatus).length;
```

API端点逻辑：
1. 首先尝试从 `event_bus.get_all_agents_status()` 获取状态
2. 如果为空，从 `agents.yaml` 加载agents
3. 如果 `agents.yaml` 加载失败或路径错误，返回空对象 `{}`

### 解决方案
检查 `/api/agents/status` 端点是否正确加载 `agents.yaml`：

**agents.yaml 位置**：`backend/config/agents.yaml`
**定义的agents**：
- market_agent
- risk_analyst
- market_analyst
- technical_analyst
- fundamental_analyst
- sentiment_analyst
- discussion_agent
- trader_agent

**预期显示**：Agents Registered: 8

### 验证步骤
1. 访问 `http://localhost:8000/api/agents/status` 查看返回的agents数量
2. 检查后端日志是否有 `[API] Loaded X agents from agents.yaml` 消息
3. 如果只显示1个，检查 `agents.yaml` 文件路径是否正确

---

## 2. 存储路径确认

### 所有数据文件统一存储在项目根目录的 `data/logs`

**存储路径**：`C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs`

### 文件列表

| 文件 | 用途 | 路径 |
|------|------|------|
| `portfolio_state.json` | 投资组合状态（现金、持仓） | `data/logs/portfolio_state.json` |
| `equity_history.jsonl` | 净值历史记录 | `data/logs/equity_history.jsonl` |
| `filled_orders.jsonl` | 已成交订单 | `data/logs/filled_orders.jsonl` |
| `pending_orders.jsonl` | 待处理订单 | `data/logs/pending_orders.jsonl` |
| `real_time_snapshots.jsonl` | 实时快照 | `data/logs/real_time_snapshots.jsonl` |
| `discussion_actions.jsonl` | 对话记录 | `data/logs/discussion_actions.jsonl` |
| `trades.jsonl` | 交易记录 | `data/logs/trades.jsonl` |

### 路径统一机制

**API Server** (`backend/src/api/server.py`):
```python
def get_project_logs_dir() -> Path:
    """Get the project root data/logs directory path."""
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
```

**Trading Cycle** (`backend/src/orchestrator/trading_cycle.py`):
```python
def _get_project_logs_dir() -> Path:
    """Get the project root data/logs directory path."""
    _backend_dir = Path(__file__).resolve().parent.parent.parent  # backend/
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
```

**验证**：所有路径都使用这些辅助函数，确保统一指向项目根目录的 `data/logs`。

---

## 3. 现金和仓位检查验证

### BUY订单现金检查

#### 多层检查机制

1. **Trader Agent 层面** (`backend/src/agents/trader_agent.py`):
   - `_calculate_position_size()` 函数接收 `available_cash` 参数
   - 检查 `available_cash <= 0` 时直接返回0（不生成订单）
   - 检查 `total_cost > available_cash` 时减少数量或跳过

2. **Trading Cycle 层面** (`backend/src/orchestrator/trading_cycle.py`):
   - 计算可用现金：`available_cash_for_trading = max(0, portfolio.cash - required_cash_reserve)`
   - 传递给 Trader Agent：`available_cash=available_cash_for_trading`
   - 执行前检查：`if estimated_cost > portfolio.cash` → 减少数量或跳过
   - 执行前检查：`if actual_cost > portfolio.cash` → 减少数量或跳过
   - 执行时检查：`portfolio.buy()` 内部也有现金检查，如果失败会抛出 `ValueError`

#### 关键代码位置

```python
# backend/src/orchestrator/trading_cycle.py:1203-1247
# CRITICAL: 使用实际portfolio.cash检查，确保现金同步
if estimated_cost > portfolio.cash:
    # 减少数量或跳过
    ...

# CRITICAL FIX: 在调用portfolio.buy()之前，再次使用实际计算值检查现金
actual_cost = quantity * current_price
if actual_cost > portfolio.cash:
    # 再次减少数量或跳过
    ...

# CRITICAL: 先执行交易，成功后再创建订单
try:
    portfolio.buy(symbol, quantity, current_price)
except ValueError as e:
    # 如果portfolio.buy()失败（通常是现金不足），跳过这个订单
    continue
```

### SELL订单仓位检查

#### 多层检查机制

1. **Trader Agent 层面** (`backend/src/agents/trader_agent.py`):
   - `run_trader()` 函数接收 `current_positions` 参数
   - 遍历所有当前持仓，检查每个持仓的数量和P&L
   - `_calculate_sell_size()` 函数基于风险报告和当前持仓计算卖出数量
   - 确保 `sell_qty <= current_qty`

2. **Trading Cycle 层面** (`backend/src/orchestrator/trading_cycle.py`):
   - 准备完整的持仓信息：`current_positions_info`（包含quantity, avg_cost, current_price, unrealized_pnl, position_pct）
   - 传递给 Trader Agent：`current_positions=current_positions_info`
   - 执行前检查：`pos = portfolio.get_position(symbol)` → 检查持仓是否足够
   - 执行前检查：`if not pos or pos.quantity < quantity` → 跳过订单
   - 执行时检查：`portfolio.sell()` 内部也有仓位检查，如果失败会抛出 `ValueError`

#### 关键代码位置

```python
# backend/src/orchestrator/trading_cycle.py:1388-1392
# 檢查持倉是否足夠
pos = portfolio.get_position(symbol)
if not pos or pos.quantity < quantity:
    execution_errors.append(f"SELL {symbol}: insufficient position (need {quantity}, have {pos.quantity if pos else 0})")
    continue

# backend/src/orchestrator/trading_cycle.py:1421-1427
# CRITICAL FIX: 先检查持仓，再创建订单和执行交易
current_position = portfolio.get_position(symbol)
if not current_position or current_position.quantity < quantity:
    available_qty = current_position.quantity if current_position else 0
    execution_errors.append(f"SELL {symbol} skipped: insufficient shares (need {quantity}, have {available_qty})")
    continue
```

### 仓位信息传递流程

1. **准备持仓信息** (`trading_cycle.py:910-929`):
   ```python
   current_positions_info = {}
   if portfolio:
       for symbol, pos in portfolio._positions.items():
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

2. **传递给 Trader Agent** (`trading_cycle.py:998`):
   ```python
   decision = run_trader(
       ...
       current_positions=current_positions_info if current_positions_info else None,
       available_cash=available_cash_for_trading,
       ...
   )
   ```

3. **Trader Agent 使用** (`trader_agent.py:570-598`):
   ```python
   if current_positions:
       for symbol, pos_info in current_positions.items():
           qty = pos_info.get("quantity", 0)
           avg_cost = pos_info.get("avg_cost", 0.0)
           current_price = pos_info.get("current_price", ...)
           unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
           position_pct = pos_info.get("position_pct", 0.0)
           # 基于这些信息决定卖出数量
   ```

---

## 总结

### ✅ 已确认

1. **存储路径**：所有数据文件统一存储在项目根目录的 `data/logs`
2. **现金检查**：BUY订单有多层现金检查，确保不会超过可用现金
3. **仓位检查**：SELL订单有多层仓位检查，确保不会卖出超过持有的数量
4. **仓位信息传递**：完整的持仓信息（包括数量、成本、P&L、占比）都正确传递给 Trader Agent

### ⚠️ 需要检查

1. **Agents Registered**：如果只显示1个，需要检查 `/api/agents/status` 是否正确加载 `agents.yaml`（应该有8个agents）

### 建议

1. 检查后端日志，确认 `agents.yaml` 是否被正确加载
2. 访问 `http://localhost:8000/api/agents/status` 查看实际返回的agents数量
3. 如果只显示1个，检查 `backend/config/agents.yaml` 文件路径和格式是否正确

