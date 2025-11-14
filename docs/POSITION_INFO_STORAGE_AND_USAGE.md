# 净值与仓位信息存储位置及Agent使用验证

## 1. 净值与仓位信息存储位置

### 主要存储文件

所有文件统一存储在：`C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs`

#### 1.1 `equity_history.jsonl` - 净值历史记录

**位置**：`data/logs/equity_history.jsonl`

**内容**：每日净值快照，包含完整的仓位信息

**数据格式**：
```json
{
  "date": "2025-01-28",
  "timestamp": "2025-01-28T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -2.50,
  "total_pnl_pct": -0.03,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 150.25,
      "market_value": 1502.50,
      "unrealized_pnl": 0.00,
      "unrealized_pnl_pct": 0.00
    }
  }
}
```

**记录时机**：
- 每次交易周期结束后记录（`trading_cycle.py:1792`）
- 每30分钟记录一次（通过 `RealTimeTracker`）

**关键字段**：
- `positions`: 包含所有持仓的详细信息（quantity, avg_cost, current_price, market_value, unrealized_pnl）

---

#### 1.2 `portfolio_state.json` - 当前投资组合状态

**位置**：`data/logs/portfolio_state.json`

**内容**：当前投资组合的实时状态（现金、持仓）

**数据格式**：
```json
{
  "cash": 2197.50,
  "initial_value": 10000.0,
  "total_value": 8497.50,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "total_cost": 1502.50
    }
  },
  "timestamp": "2025-01-28T10:00:00.000Z"
}
```

**更新时机**：
- 每次订单成交后更新（`trading_cycle.py:800, 1694`）
- 每次结算pending订单后更新（`server.py:951, 1077`）

**关键字段**：
- `positions`: 包含所有持仓的数量和成本信息

---

#### 1.3 `real_time_snapshots.jsonl` - 实时快照

**位置**：`data/logs/real_time_snapshots.jsonl`

**内容**：实时投资组合快照（每30分钟记录一次）

**数据格式**：
```json
{
  "timestamp": "2025-01-28T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 150.25,
      "market_value": 1502.50,
      "unrealized_pnl": 0.00,
      "unrealized_pnl_pct": 0.00
    }
  }
}
```

**记录时机**：
- 每30分钟自动记录（`real_time_tracker.py`）
- 通过 `/api/portfolio/real-time` 端点触发

---

#### 1.4 `filled_orders.jsonl` - 已成交订单

**位置**：`data/logs/filled_orders.jsonl`

**内容**：所有已成交的订单记录，包含SELL订单的realized_pnl

**数据格式**：
```json
{
  "order_id": "order_123",
  "symbol": "NVDA",
  "action": "SELL",
  "quantity": 5,
  "limit_price": 150.25,
  "fill_price": 150.25,
  "status": "FILLED",
  "placed_at": "2025-01-28T10:00:00.000Z",
  "filled_at": "2025-01-28T10:00:01.000Z",
  "realized_pnl": 25.00,
  "realized_pnl_pct": 3.33,
  "cost_basis": 751.25,
  "proceeds": 751.25
}
```

---

### 数据流向

```
Portfolio对象 (内存)
    ↓
portfolio_state.json (持久化)
    ↓
current_positions_info (准备给Agent)
    ↓
Trader Agent (使用仓位信息决策)
    ↓
订单执行
    ↓
equity_history.jsonl (记录净值历史)
```

---

## 2. Agent读取仓位信息执行交易验证

### 2.1 仓位信息准备流程

#### Step 1: 从Portfolio对象提取仓位信息

**位置**：`backend/src/orchestrator/trading_cycle.py:910-929`

```python
# 准备完整的持仓信息，包括损益和占比
current_positions_info = {}
if portfolio:
    portfolio_value = portfolio.value(last_prices)
    for symbol, pos in portfolio._positions.items():
        current_price = last_prices.get(symbol, pos.avg_cost)
        market_value = pos.quantity * current_price
        unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
        unrealized_pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
        position_pct = (market_value / portfolio_value * 100.0) if portfolio_value > 0 else 0.0
        
        current_positions_info[symbol] = {
            "quantity": pos.quantity,           # 持仓数量
            "avg_cost": pos.avg_cost,           # 平均成本
            "current_price": current_price,      # 当前价格
            "market_value": market_value,       # 市值
            "unrealized_pnl": unrealized_pnl,   # 未实现损益（金额）
            "unrealized_pnl_pct": unrealized_pnl_pct,  # 未实现损益（百分比）
            "position_pct": position_pct,  # 持仓占比（占组合净值的百分比）
        }
```

**关键信息**：
- ✅ 包含所有持仓的完整信息
- ✅ 包含数量、成本、价格、P&L、占比

---

#### Step 2: 传递给Trader Agent

**位置**：`backend/src/orchestrator/trading_cycle.py:992-1002`

```python
decision = run_trader(
    market=market_view,
    mview=enriched_market,
    rview=risk_report,
    convo=convo,
    last_prices=last_prices,
    current_positions=current_positions_info if current_positions_info else None,  # ✅ 传递仓位信息
    portfolio_value=portfolio_value,
    position_config=position_config,
    available_cash=available_cash_for_trading,  # ✅ 传递可用现金
)
```

**关键信息**：
- ✅ `current_positions` 参数包含完整的仓位信息
- ✅ `available_cash` 参数包含可用现金（用于限制买入）

---

### 2.2 Trader Agent使用仓位信息

#### BUY订单：检查已有持仓

**位置**：`backend/src/agents/trader_agent.py:95-118`

```python
# 检查当前持仓
current_symbol_position = 0.0
current_qty = 0
if current_positions:
    pos_info = current_positions.get(symbol)
    if pos_info:
        if isinstance(pos_info, dict):
            current_qty = pos_info.get("quantity", 0)
            current_price = pos_info.get("current_price", last_price)
        else:
            current_qty = pos_info if isinstance(pos_info, (int, float)) else 0
        
        if current_qty > 0 and current_price > 0:
            current_value = current_qty * current_price
            current_symbol_position = current_value / portfolio_value
            print(f"[TRADER] {symbol}: Already has {current_qty} shares @ ${current_price:.2f}, position_pct={current_symbol_position:.2%}")

# 计算目标仓位（考虑已有持仓）
target_position_pct = dynamic_max_pct
if current_symbol_position >= target_position_pct:
    # 已达到目标仓位
    print(f"[TRADER] {symbol}: Skipping - already at target position")
    return 0  # ✅ 如果已有足够持仓，不生成买入订单

# 计算还需要买入的仓位百分比
remaining_position_pct = target_position_pct - current_symbol_position
```

**验证**：
- ✅ Agent确实读取了 `current_positions` 中的仓位信息
- ✅ 如果已有持仓，会计算当前仓位占比
- ✅ 如果已达到目标仓位，跳过买入（返回0）

---

#### SELL订单：遍历所有持仓

**位置**：`backend/src/agents/trader_agent.py:568-652`

```python
# CRITICAL: 检查所有当前持仓，决定是否需要卖出
# 确保agent知道所有可卖出的持仓及其数量
if current_positions:
    print(f"[TRADER] Checking {len(current_positions)} current positions for sell opportunities...")
    
    for symbol, pos_info in current_positions.items():
        if isinstance(pos_info, dict):
            qty = pos_info.get("quantity", 0)                    # ✅ 读取持仓数量
            avg_cost = pos_info.get("avg_cost", 0.0)            # ✅ 读取平均成本
            current_price = pos_info.get("current_price", ...)  # ✅ 读取当前价格
            unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)  # ✅ 读取未实现损益
            unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)  # ✅ 读取未实现损益百分比
            position_pct = pos_info.get("position_pct", 0.0)    # ✅ 读取持仓占比
        
        print(f"[TRADER] Position {symbol}: {qty} shares @ ${avg_cost:.2f} avg, current ${current_price:.2f}, P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%), position_pct={position_pct:.1f}%")
        
        # 决定卖出数量的逻辑：
        # 1. 基于风险报告的仓位限制检查
        sell_qty_from_risk = 0
        if rview:
            sell_qty_from_risk = _calculate_sell_size(
                symbol, qty, portfolio_value, current_price, rview, current_positions
            )
        
        # 如果风险报告建议卖出，或者有其他卖出信号，生成卖出订单
        if sell_qty > 0:
            # 确保卖出数量不超过持仓数量
            sell_qty = min(sell_qty, qty)  # ✅ 确保不超过实际持仓数量
            
            sell_orders.append({
                "symbol": symbol,
                "quantity": sell_qty,
                "current_position": qty,  # ✅ 记录当前持仓数量（用于验证）
                "avg_cost": avg_cost,      # ✅ 记录平均成本（用于计算realized_pnl）
                "unrealized_pnl": unrealized_pnl,  # ✅ 记录未实现损益（用于参考）
            })
```

**验证**：
- ✅ Agent确实遍历了所有 `current_positions` 中的持仓
- ✅ 读取了每个持仓的完整信息（数量、成本、价格、P&L、占比）
- ✅ 基于仓位信息决定卖出数量
- ✅ 确保卖出数量不超过实际持仓数量（`min(sell_qty, qty)`）

---

### 2.3 执行时再次验证

#### BUY订单执行前检查

**位置**：`backend/src/orchestrator/trading_cycle.py:1203-1260`

```python
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
    portfolio.buy(symbol, quantity, current_price)  # ✅ portfolio.buy()内部也有现金检查
except ValueError as e:
    # 如果portfolio.buy()失败（通常是现金不足），跳过这个订单
    continue
```

**验证**：
- ✅ 执行前多次检查现金
- ✅ `portfolio.buy()` 内部也有现金检查，失败会抛出异常

---

#### SELL订单执行前检查

**位置**：`backend/src/orchestrator/trading_cycle.py:1388-1427`

```python
# 檢查持倉是否足夠
pos = portfolio.get_position(symbol)  # ✅ 从Portfolio对象读取实际持仓
if not pos or pos.quantity < quantity:
    execution_errors.append(f"SELL {symbol}: insufficient position (need {quantity}, have {pos.quantity if pos else 0})")
    continue  # ✅ 如果持仓不足，跳过订单

# CRITICAL FIX: 先检查持仓，再创建订单和执行交易
current_position = portfolio.get_position(symbol)  # ✅ 再次检查
if not current_position or current_position.quantity < quantity:
    available_qty = current_position.quantity if current_position else 0
    execution_errors.append(f"SELL {symbol} skipped: insufficient shares (need {quantity}, have {available_qty})")
    continue  # ✅ 如果持仓不足，跳过订单

# 市价单：立即成交，不挂单
# 先执行交易以获取realized_pnl（在创建订单前）
realized_pnl = portfolio.sell(symbol, quantity, current_price)  # ✅ portfolio.sell()内部也有仓位检查
```

**验证**：
- ✅ 执行前多次检查持仓
- ✅ 从Portfolio对象读取实际持仓数量
- ✅ `portfolio.sell()` 内部也有仓位检查，失败会抛出异常

---

## 3. 完整数据流验证

### 3.1 仓位信息传递链路

```
1. Portfolio对象 (内存)
   └─ portfolio._positions: Dict[str, Position]
      └─ Position: {symbol, quantity, avg_cost, total_cost}

2. 准备current_positions_info (trading_cycle.py:910-929)
   └─ 从Portfolio提取，添加价格、P&L、占比信息
      └─ current_positions_info[symbol] = {
           "quantity": pos.quantity,
           "avg_cost": pos.avg_cost,
           "current_price": current_price,
           "market_value": market_value,
           "unrealized_pnl": unrealized_pnl,
           "unrealized_pnl_pct": unrealized_pnl_pct,
           "position_pct": position_pct,
         }

3. 传递给Trader Agent (trading_cycle.py:998)
   └─ run_trader(current_positions=current_positions_info, ...)

4. Trader Agent使用 (trader_agent.py:570-652)
   ├─ BUY订单：检查已有持仓，避免重复买入
   └─ SELL订单：遍历所有持仓，基于仓位信息决定卖出数量

5. 执行时再次验证 (trading_cycle.py:1388-1427)
   └─ portfolio.get_position(symbol) → 从Portfolio对象读取实际持仓
      └─ 确保卖出数量不超过实际持仓数量
```

---

### 3.2 现金信息传递链路

```
1. Portfolio对象 (内存)
   └─ portfolio.cash: float

2. 计算可用现金 (trading_cycle.py:986-990)
   └─ available_cash_for_trading = max(0, portfolio.cash - required_cash_reserve)

3. 传递给Trader Agent (trading_cycle.py:1001)
   └─ run_trader(available_cash=available_cash_for_trading, ...)

4. Trader Agent使用 (trader_agent.py:130-168)
   ├─ _calculate_position_size(available_cash=remaining_cash, ...)
   └─ 如果 available_cash <= 0，直接返回0（不生成订单）
      └─ 如果 total_cost > available_cash，减少数量或跳过

5. 执行时再次验证 (trading_cycle.py:1203-1260)
   └─ 多次检查 portfolio.cash
      └─ portfolio.buy() 内部也有现金检查
```

---

## 4. 验证总结

### ✅ 已确认

1. **净值信息存储**：
   - `equity_history.jsonl` - 每日净值历史（包含完整仓位信息）
   - `portfolio_state.json` - 当前投资组合状态（现金、持仓）
   - `real_time_snapshots.jsonl` - 实时快照（每30分钟）

2. **仓位信息传递**：
   - ✅ Trading Cycle准备完整的 `current_positions_info`（包含quantity, avg_cost, current_price, market_value, unrealized_pnl, unrealized_pnl_pct, position_pct）
   - ✅ 传递给Trader Agent：`current_positions=current_positions_info`
   - ✅ 传递给Risk Analyst：`current_positions=current_positions_info`

3. **Agent使用仓位信息**：
   - ✅ **BUY订单**：检查已有持仓，避免重复买入；如果已达到目标仓位，跳过买入
   - ✅ **SELL订单**：遍历所有当前持仓，读取每个持仓的完整信息（数量、成本、价格、P&L、占比），基于仓位信息决定卖出数量
   - ✅ **执行时验证**：从Portfolio对象读取实际持仓，确保卖出数量不超过实际持仓数量

4. **现金检查**：
   - ✅ Trader Agent接收 `available_cash` 参数
   - ✅ 如果 `available_cash <= 0`，不生成买入订单
   - ✅ 如果 `total_cost > available_cash`，减少数量或跳过
   - ✅ 执行时多次检查 `portfolio.cash`
   - ✅ `portfolio.buy()` 内部也有现金检查

---

### 关键代码位置

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

---

## 结论

✅ **Agent确实读取了仓位信息执行交易**：
- Trader Agent接收完整的 `current_positions_info`（包含所有持仓的详细信息）
- BUY订单会检查已有持仓，避免重复买入
- SELL订单会遍历所有当前持仓，基于仓位信息（数量、成本、P&L、占比）决定卖出数量
- 执行时会再次从Portfolio对象验证，确保不会超过实际持仓数量

✅ **净值与仓位信息完整存储**：
- `equity_history.jsonl` - 每日净值历史（包含完整仓位信息）
- `portfolio_state.json` - 当前投资组合状态
- `real_time_snapshots.jsonl` - 实时快照

所有数据统一存储在项目根目录的 `data/logs` 中。

