# 📁 数据存储位置指南

## 数据存储目录

**所有数据统一存储在项目根目录的 `data/logs/` 文件夹**

**完整路径**：
```
C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs\
```

---

## 📊 数据文件说明

### 核心数据文件

| 文件名 | 用途 | 说明 |
|--------|------|------|
| `portfolio_state.json` | **持仓记录** | 当前投资组合状态（现金、持仓、成本） |
| `equity_history.jsonl` | **净值历史** | 净值变化记录（每30分钟记录一次） |
| `discussion_actions.jsonl` | **聊天记录** | 所有 agent 的对话、分析和工具调用记录 |
| `filled_orders.jsonl` | **已成交订单** | 已完成的买卖订单（包含已实现盈亏） |
| `pending_orders.jsonl` | **待处理订单** | 等待执行的订单 |
| `trades.jsonl` | **交易记录** | 所有交易执行历史 |

### 内存系统文件

| 目录 | 用途 |
|------|------|
| `memory/daily/` | 每日市场快照和 agent 讨论记录 |
| `memory/weekly/` | 每周汇总 |
| `memory/monthly/` | 每月汇总 |
| `memory/index/` | 内存索引文件 |

---

## 📋 详细说明

### 1. 持仓记录 (`portfolio_state.json`)

**位置**：`data/logs/portfolio_state.json`

**包含内容**：
- 当前现金余额
- 当前持仓（股票代码、数量、平均成本、总成本）
- 初始价值
- 总价值

**示例**：
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
  }
}
```

---

### 2. 净值历史 (`equity_history.jsonl`)

**位置**：`data/logs/equity_history.jsonl`

**记录频率**：每 30 分钟自动记录一次（市场开市期间）

**包含内容**：
- 日期和时间戳
- 现金余额
- 持仓市值
- 总价值
- 总盈亏（P&L）
- 每个持仓的当前价格和未实现盈亏

**格式**（JSONL - 每行一条记录）：
```json
{
  "date": "2025-11-16",
  "timestamp": "2025-11-16T10:00:00.000Z",
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

---

### 3. 聊天记录 (`discussion_actions.jsonl`)

**位置**：`data/logs/discussion_actions.jsonl`

**包含内容**：
- 所有 agent 的对话和分析
- 工具调用记录
- 讨论轮次（Round 1, 2, 3）
- Agent 类型（MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst, DiscussionCoordinator, RiskAnalyst, TraderAgent）

**格式**：
```json
{
  "timestamp": "2025-11-16T10:00:00Z",
  "date": "2025-11-16",
  "agent": "MarketAnalyst",
  "round": 1,
  "content": "Market analysis...",
  "type": "discussion",
  "summary": "Market shows mixed sentiment...",
  "stance": "NEUTRAL",
  "tools_used": ["get_market_indices", "get_sector_rotation"]
}
```

---

### 4. 已成交订单 (`filled_orders.jsonl`)

**位置**：`data/logs/filled_orders.jsonl`

**包含内容**：
- 已完成的买卖订单
- 卖出订单的已实现盈亏（realized_pnl）
- 成本基础（cost_basis）
- 成交价格和数量

**格式**：
```json
{
  "order_id": "order_123",
  "placed_at": "2025-11-16T10:30:00",
  "symbol": "NVDA",
  "action": "SELL",
  "quantity": 10,
  "fill_price": 155.00,
  "status": "FILLED",
  "realized_pnl": 47.50,
  "realized_pnl_pct": 3.16,
  "cost_basis": 1502.50,
  "proceeds": 1550.00
}
```

---

### 5. 待处理订单 (`pending_orders.jsonl`)

**位置**：`data/logs/pending_orders.jsonl`

**包含内容**：
- 等待执行的订单
- 订单状态（PENDING）
- 订单详情（股票代码、数量、价格范围）

---

### 6. 交易记录 (`trades.jsonl`)

**位置**：`data/logs/trades.jsonl`

**包含内容**：
- 所有交易执行历史
- 交易时间、股票代码、买卖方向、数量、价格

---

## 🔄 系统初始化

### 初始化 API 端点

**端点**：`POST /api/system/init?force=true`

**功能**：
- 删除所有交易数据文件
- 自动备份 `portfolio_state.json`（如果存在）
- 重置系统到初始状态

**删除的文件**：
- `portfolio_state.json`（会先备份）
- `pending_orders.jsonl`
- `filled_orders.jsonl`
- `equity_history.jsonl`
- `discussion_actions.jsonl`

**注意**：
- 需要 `force=true` 参数才能执行
- `portfolio_state.json` 会自动备份为 `portfolio_state_backup_YYYYMMDD_HHMMSS.json`
- **不会删除** `memory/` 目录下的文件

### 初始化代码位置

**文件**：`backend/src/api/server.py`

**函数**：`system_init()`（第 1055-1110 行）

**数据目录获取**：
```python
def _get_project_logs_dir() -> Path:
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir
```

**路径解析**：
- `backend/src/api/server.py` → `backend/` → 项目根目录 → `data/logs/`

---

## 📂 目录结构

```
data/logs/
├── portfolio_state.json          # 持仓记录
├── equity_history.jsonl          # 净值历史
├── discussion_actions.jsonl      # 聊天记录
├── filled_orders.jsonl            # 已成交订单
├── pending_orders.jsonl          # 待处理订单
├── trades.jsonl                  # 交易记录
├── portfolio_state_backup_*.json # 备份文件
├── discussion_actions_backup_*.jsonl # 备份文件
└── memory/
    ├── daily/
    │   └── YYYY-MM-DD.json      # 每日快照
    ├── weekly/
    │   └── YYYY-W##.jsonl       # 每周汇总
    ├── monthly/
    │   └── YYYY-MM.jsonl        # 每月汇总
    └── index/
        └── daily_index.json      # 内存索引
```

---

## 🔍 快速查找

### 查看持仓
```bash
# Windows PowerShell
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 查看聊天记录
```bash
# 查看最后 10 条记录
Get-Content data\logs\discussion_actions.jsonl -Tail 10
```

### 查看净值历史
```bash
# 查看所有净值记录
Get-Content data\logs\equity_history.jsonl
```

### 查看已成交订单
```bash
# 查看所有已成交订单
Get-Content data\logs\filled_orders.jsonl
```

---

## ⚠️ 注意事项

1. **备份重要**：初始化前会自动备份 `portfolio_state.json`，但建议手动备份整个 `data/logs/` 目录
2. **内存文件保留**：初始化不会删除 `memory/` 目录，这些是 agent 的学习数据
3. **文件格式**：
   - `.json` 文件：单个 JSON 对象
   - `.jsonl` 文件：每行一个 JSON 对象（便于追加）
4. **自动创建**：如果目录不存在，系统会自动创建

---

## 📝 相关 API 端点

- `GET /api/portfolio/real-time` - 获取实时持仓和净值
- `GET /api/portfolio/equity-history` - 获取净值历史
- `GET /api/agents/conversations` - 获取聊天记录
- `GET /api/trades/recent` - 获取最近交易
- `POST /api/system/init?force=true` - 系统初始化

