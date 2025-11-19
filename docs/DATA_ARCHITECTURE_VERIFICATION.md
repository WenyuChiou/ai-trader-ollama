# 📊 数据架构验证报告 - Performance Analysis 准备

## ✅ 验证结果：数据架构统一且可访问

**所有 Agent 产生的订单、持仓、交易数据都统一存储在 `data/logs/` 目录，并通过标准 API 访问。**

---

## 📁 统一数据存储架构

### 核心数据文件位置

所有数据统一存储在：`{project_root}/data/logs/`

| 数据类型 | 文件名 | 格式 | 用途 | 访问方式 |
|---------|--------|------|------|---------|
| **持仓状态** | `portfolio_state.json` | JSON | 当前投资组合快照 | `/api/portfolio/real-time` |
| **净值历史** | `equity_history.jsonl` | JSONL | 净值变化时间序列 | `/api/portfolio/equity-history` |
| **已成交订单** | `filled_orders.jsonl` | JSONL | 所有已执行的订单 | `/api/trades/recent` |
| **待处理订单** | `pending_orders.jsonl` | JSONL | 等待执行的订单 | `OrderManager.load_pending_orders()` |
| **交易记录** | `trades.jsonl` | JSONL | 完整交易执行历史 | `TradeLogger.get_trades()` |
| **对话记录** | `discussion_actions.jsonl` | JSONL | Agent 分析和决策记录 | `/api/agents/conversations` |

---

## 🔄 数据流程和记录时机

### 1. 订单创建流程

```
Trader Agent 生成订单
    ↓
order_manager.place_order()
    ↓
写入 pending_orders.jsonl
    ↓
订单执行（市价单立即成交）
    ↓
order_manager.mark_order_filled()
    ↓
写入 filled_orders.jsonl（包含 realized_pnl）
```

**关键代码位置**：
- `backend/src/orchestrator/trading_cycle.py` 第2145行：创建 BUY 订单
- `backend/src/orchestrator/trading_cycle.py` 第2319行：创建 SELL 订单
- `backend/src/data/order_manager.py`：订单管理

### 2. 持仓更新流程

```
订单成交
    ↓
portfolio.buy() / portfolio.sell()
    ↓
更新 portfolio._positions
    ↓
保存到 portfolio_state.json
    ↓
记录到 equity_history.jsonl（每30分钟）
```

**关键代码位置**：
- `backend/src/data/portfolio.py`：Portfolio 类
- `backend/src/orchestrator/trading_cycle.py` 第2181行：保存 portfolio_state.json
- `backend/src/api/server.py` 第763行：自动记录 equity_history（每小时）

### 3. Agent 分析记录流程

```
Agent 执行分析
    ↓
写入 discussion_actions.jsonl
    ↓
包含：agent, round, content, summary, stance, tools_used, recommended_stocks
```

**关键代码位置**：
- `backend/src/orchestrator/trading_cycle.py` 多处：写入 discussion_actions.jsonl

---

## 📊 统一数据格式

### 1. 订单数据格式（filled_orders.jsonl）

```json
{
  "order_id": "NVDA_BUY_2025-11-19_1234567890",
  "placed_at": "2025-11-19T10:30:00.000Z",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "fill_price": 150.25,
  "status": "FILLED",
  "realized_pnl": null,  // BUY 订单为 null
  "realized_pnl_pct": null,
  "fill_result": {
    "filled_at": "2025-11-19T10:30:00.000Z",
    "fill_price": 150.25,
    "fill_quantity": 10
  }
}
```

**SELL 订单额外字段**：
```json
{
  "realized_pnl": 47.50,
  "realized_pnl_pct": 3.16,
  "cost_basis": 1502.50,
  "proceeds": 1550.00
}
```

### 2. 持仓数据格式（portfolio_state.json）

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
  "timestamp": "2025-11-19T10:00:00Z"
}
```

### 3. 净值历史格式（equity_history.jsonl）

```json
{
  "date": "2025-11-19",
  "timestamp": "2025-11-19T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -1502.50,
  "total_pnl_pct": -15.03,
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

---

## 🔌 API 访问接口

### 1. 实时持仓数据

**端点**：`GET /api/portfolio/real-time`

**返回**：
```json
{
  "ok": true,
  "portfolio": {
    "cash": 2197.50,
    "total_value": 8497.50,
    "positions": {...},
    "positions_detail": {...},
    "positions_pnl": {...}
  }
}
```

### 2. 净值历史

**端点**：`GET /api/portfolio/equity-history?start_date=2025-11-01&end_date=2025-11-19`

**返回**：
```json
{
  "ok": true,
  "history": [
    {
      "date": "2025-11-19",
      "timestamp": "2025-11-19T10:00:00.000Z",
      "total_value": 8497.50,
      ...
    }
  ]
}
```

### 3. 交易记录

**端点**：`GET /api/trades/recent?limit=100`

**返回**：
```json
{
  "ok": true,
  "trades": [
    {
      "order_id": "...",
      "symbol": "NVDA",
      "action": "BUY",
      "fill_price": 150.25,
      ...
    }
  ]
}
```

### 4. 性能统计

**端点**：`GET /api/performance/statistics?start_date=2025-11-01&end_date=2025-11-19`

**返回**：
```json
{
  "ok": true,
  "statistics": {
    "initial_value": 10000.0,
    "current_value": 8497.50,
    "total_return": -1502.50,
    "total_return_pct": -15.03,
    "annualized_return_pct": -45.09,
    "max_drawdown": 2000.00,
    "max_drawdown_pct": 20.00,
    "win_rate": 60.0,
    "total_trades": 10,
    "winning_trades": 6,
    "losing_trades": 4,
    "total_realized_pnl": 500.00,
    "avg_trade_return": 50.00,
    "sharpe_ratio": 0.85,
    "trading_days": 15,
    "data_points": 120
  },
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-19"
  }
}
```

---

## 📈 Performance Analysis 数据源

### 1. 净值曲线分析

**数据源**：`equity_history.jsonl`

**计算指标**：
- Total Return（总收益）
- Annualized Return（年化收益）
- Maximum Drawdown（最大回撤）
- Sharpe Ratio（夏普比率）

**代码位置**：`backend/src/api/performance.py` 第168-337行

### 2. 交易表现分析

**数据源**：`filled_orders.jsonl`

**计算指标**：
- Win Rate（胜率）
- Average Trade Return（平均交易收益）
- Total Realized P&L（总已实现盈亏）
- Winning/Losing Trades（盈利/亏损交易数）

**代码位置**：`backend/src/api/performance.py` 第275-285行

### 3. 持仓分析

**数据源**：`portfolio_state.json` + `equity_history.jsonl`

**计算指标**：
- Position Concentration（持仓集中度）
- Unrealized P&L（未实现盈亏）
- Position P&L by Symbol（按股票分类的盈亏）

**代码位置**：`backend/src/api/server.py` 第698-850行

---

## ✅ 数据完整性验证

### 1. 时间戳统一性

✅ **所有数据使用 ISO 8601 格式，UTC 时区**：
- `placed_at`: `"2025-11-19T10:30:00.000Z"`
- `timestamp`: `"2025-11-19T10:00:00.000Z"`
- `filled_at`: `"2025-11-19T10:30:00.000Z"`

### 2. 数据一致性

✅ **订单和持仓数据一致**：
- `filled_orders.jsonl` 中的订单 → 更新 `portfolio_state.json`
- `portfolio_state.json` 中的持仓 → 记录到 `equity_history.jsonl`

### 3. 数据可追溯性

✅ **完整的数据链路**：
- Agent 分析 → `discussion_actions.jsonl`
- 交易决策 → `discussion_actions.jsonl` (TraderAgent)
- 订单执行 → `filled_orders.jsonl`
- 持仓变化 → `portfolio_state.json` + `equity_history.jsonl`

---

## 🔧 数据访问工具

### Python 直接访问

```python
import json
from pathlib import Path

# 读取持仓状态
portfolio_file = Path("data/logs/portfolio_state.json")
with portfolio_file.open("r") as f:
    portfolio = json.load(f)

# 读取净值历史（JSONL）
equity_file = Path("data/logs/equity_history.jsonl")
equity_records = []
with equity_file.open("r") as f:
    for line in f:
        if line.strip():
            equity_records.append(json.loads(line))

# 读取已成交订单（JSONL）
filled_file = Path("data/logs/filled_orders.jsonl")
filled_orders = []
with filled_file.open("r") as f:
    for line in f:
        if line.strip():
            filled_orders.append(json.loads(line))
```

### API 访问

```javascript
// 获取实时持仓
const portfolio = await fetch('/api/portfolio/real-time').then(r => r.json());

// 获取净值历史
const history = await fetch('/api/portfolio/equity-history?start_date=2025-11-01&end_date=2025-11-19')
    .then(r => r.json());

// 获取交易记录
const trades = await fetch('/api/trades/recent?limit=100').then(r => r.json());

// 获取性能统计
const stats = await fetch('/api/performance/statistics?start_date=2025-11-01&end_date=2025-11-19')
    .then(r => r.json());
```

---

## 📋 Performance Analysis 准备清单

### ✅ 已完成

1. ✅ **统一数据存储位置**：所有数据存储在 `data/logs/`
2. ✅ **统一数据格式**：JSON/JSONL 格式，ISO 8601 时间戳
3. ✅ **完整的数据记录**：订单、持仓、净值历史、交易记录
4. ✅ **标准 API 接口**：RESTful API 访问所有数据
5. ✅ **性能分析模块**：`backend/src/api/performance.py`
6. ✅ **已实现指标**：
   - Total Return / Annualized Return
   - Maximum Drawdown
   - Win Rate
   - Sharpe Ratio
   - Average Trade Return
   - Total Realized P&L

### 🎯 可用于 Performance Analysis 的数据

1. **净值曲线**：`equity_history.jsonl` → 计算收益率、回撤
2. **交易记录**：`filled_orders.jsonl` → 计算胜率、平均收益
3. **持仓分析**：`portfolio_state.json` → 分析持仓集中度、未实现盈亏
4. **Agent 决策**：`discussion_actions.jsonl` → 分析决策质量

---

## 🚀 后续 Performance Analysis 扩展建议

### 1. 新增指标

- **Sortino Ratio**：下行风险调整收益
- **Calmar Ratio**：最大回撤调整收益
- **Win/Loss Ratio**：盈亏比
- **Average Holding Period**：平均持仓时间
- **Turnover Rate**：换手率

### 2. 按股票分析

- 每个股票的盈亏表现
- 持仓时间分布
- 买入/卖出时机分析

### 3. 按 Agent 分析

- 每个 Agent 推荐股票的后续表现
- Agent 决策质量评估
- Agent 工具使用效果

### 4. 时间序列分析

- 每日/每周/每月收益分布
- 收益波动性分析
- 市场环境下的表现（牛市/熊市）

---

## 📝 总结

✅ **数据架构统一**：所有数据存储在 `data/logs/`，格式统一（JSON/JSONL）

✅ **数据可访问**：通过标准 API 和直接文件访问两种方式

✅ **数据完整**：订单、持仓、净值历史、交易记录全部记录

✅ **Performance Analysis 就绪**：已有基础性能分析模块和指标计算

✅ **可扩展性**：数据结构支持后续添加更多分析指标

---

## 📚 相关文档

- [Data Storage Guide](DATA_STORAGE_GUIDE.md) - 数据存储位置说明
- [Data Format](DATA_FORMAT.md) - 详细数据格式规范
- [API Reference](../README.md#-api-endpoints) - API 端点文档
- [Performance Analysis](../README.md#-historical-performance-analysis) - 性能分析说明

