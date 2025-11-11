# 🔄 完整交易系统 Workflow 文档

## 📋 目录
1. [系统概览](#系统概览)
2. [完整交易周期流程](#完整交易周期流程)
3. [订单管理流程](#订单管理流程)
4. [对话/聊天流程](#对话聊天流程)
5. [执行流程](#执行流程)
6. [数据流](#数据流)

---

## 🎯 系统概览

这是一个基于多Agent的AI交易系统，包含以下核心组件：

- **Market Agent**: 获取市场数据和指标
- **Multi-Analyst System**: 多个专门的分析师（Market, Technical, Fundamental, Sentiment）
- **Risk Analyst**: 评估仓位风险
- **Trader Agent**: 生成交易决策
- **Order Manager**: 管理订单（pending/filled）
- **Portfolio**: 管理持仓和现金
- **Frontend Monitor**: 实时监控界面

---

## 🔄 完整交易周期流程

### 阶段 1: 市场数据收集 (Market Data Collection)

**触发**: 用户点击 "Start Trading" 或 "Plan Tomorrow" 按钮

**API端点**: `POST /api/trading/execute-trade`

**代码位置**: `backend/src/orchestrator/trading_cycle.py::execute_daily_trade()`

**流程**:
```
1. 加载配置 (config.json)
   ├─ universe: 股票列表（100+ 股票）
   ├─ tool_budget: 工具调用预算（默认8）
   └─ rounds: 讨论轮数（默认3）

2. 确定交易日期
   ├─ 如果市场开盘: 使用今天日期
   └─ 如果市场收盘: 使用下一个交易日

3. 获取市场数据 (fetch_market_batch)
   ├─ 输入: symbols, start_date, end_date
   ├─ 获取: OHLCV数据（通过yfinance）
   ├─ 计算: 技术指标（RSI14, MACD, Bollinger Bands, MA20/50）
   ├─ 计算: signal_score (0-10综合评分)
   └─ 输出: market_view (包含所有股票的数据)
```

**输出**: `market_view` 字典，包含所有股票的完整数据

---

### 阶段 2: 订单状态检查 (Order Status Check)

**代码位置**: `backend/src/orchestrator/trading_cycle.py::execute_daily_trade()` (行202-247)

**流程**:
```
1. 初始化 OrderManager
   └─ 路径: data/logs/

2. 确定订单日期
   ├─ 如果 end 参数存在: 使用 end
   ├─ 如果市场开盘: 使用今天
   └─ 如果市场收盘: 使用下一个交易日

3. 加载订单
   ├─ pending_orders: 从 pending_orders.jsonl 加载
   └─ filled_orders: 从 filled_orders.jsonl 加载

4. 准备订单状态
   └─ order_status = {
        "pending_count": len(pending_orders),
        "filled_count": len(filled_orders),
        "pending_orders": [...],
        "filled_orders": [...],
        "order_date": order_date
      }
```

**输出**: `order_status` 字典，包含当前订单状态

---

### 阶段 3: 仓位信息准备 (Position Info Preparation)

**代码位置**: `backend/src/orchestrator/trading_cycle.py::execute_daily_trade()` (行255-274)

**流程**:
```
1. 获取当前持仓信息
   ├─ 从 Portfolio 对象获取
   ├─ 计算每个持仓的当前价格
   └─ 计算每个持仓的市场价值

2. 计算可用现金
   ├─ 读取 MIN_CASH_RESERVE_RATIO (默认20%)
   ├─ 计算: required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
   └─ 计算: available_cash = max(0, cash - required_cash_reserve)

3. 准备仓位信息
   └─ preliminary_positions_info = {
        "SYMBOL": {
          "quantity": 100,
          "avg_cost": 150.0,
          "current_price": 155.0,
          "market_value": 15500.0
        },
        ...
      }
```

**输出**: `preliminary_positions_info`, `preliminary_portfolio_value`, `preliminary_available_cash`

---

### 阶段 4: 多分析师讨论 (Multi-Analyst Discussion)

**代码位置**: `backend/src/agents/multi_analyst_system.py::run_multi_analyst_discussion()`

**触发**: `execute_daily_trade()` 调用 (行276-284)

**流程**:
```
1. 初始化多个分析师
   ├─ MarketAnalyst: 市场趋势分析
   ├─ TechnicalAnalyst: 技术指标分析
   ├─ FundamentalAnalyst: 基本面分析
   └─ SentimentAnalyst: 情绪分析

2. 准备提示词变量
   ├─ market_prompt_vars: 市场数据摘要
   ├─ technical_prompt_vars: 技术指标摘要
   ├─ fundamental_prompt_vars: 基本面数据摘要
   └─ sentiment_prompt_vars: 情绪数据摘要
   
   每个提示词包含:
   - current_positions: 当前持仓信息
   - portfolio_value: 组合净值
   - available_cash: 可用现金
   - order_status: 订单状态

3. 多轮讨论 (rounds=3)
   For each round:
     a. 每个分析师独立分析
        ├─ 生成 stance (bullish/bearish/neutral)
        ├─ 生成 analysis (100-150字摘要)
        └─ 可能调用工具 (tools)
     
     b. 工具调用 (如果启用)
        ├─ news_scan: 新闻扫描（自动填充keywords）
        ├─ vix_term: VIX期限结构
        ├─ fear_greed: 恐惧贪婪指数
        ├─ get_support_resistance: 支撑阻力位
        └─ 其他技术/基本面工具
     
     c. Coordinator 统整
        ├─ 综合所有分析师观点
        ├─ 生成最终 stance
        └─ 生成综合摘要 (100-150字)

4. 写入对话记录
   ├─ 每个分析师的分析 → discussion_actions.jsonl
   ├─ Coordinator 摘要 → discussion_actions.jsonl
   └─ 工具调用记录 → discussion_actions.jsonl
```

**输出**: `convo` 字典，包含:
- `final_stance`: 最终立场
- `discussion_history`: 讨论历史
- `tool_calls`: 工具调用记录
- `coordinator_summary`: Coordinator 摘要

**对话记录格式** (`discussion_actions.jsonl`):
```json
{
  "timestamp": "2025-01-28T10:00:00Z",
  "date": "2025-01-28",
  "agent": "MarketAnalyst",
  "round": 0,
  "content": "Stance: bullish\n\nAnalysis: ...",
  "type": "discussion",
  "stance": "bullish",
  "tools_used": ["news_scan", "vix_term"]
}
```

---

### 阶段 5: 风险分析 (Risk Analysis)

**代码位置**: `backend/src/agents/risk_analyst_llm.py::run_risk_analyst_llm()`

**触发**: `execute_daily_trade()` 调用 (行430-450)

**流程**:
```
1. 准备风险分析提示词
   ├─ 当前持仓信息
   ├─ 市场波动性 (VIX)
   ├─ 组合集中度
   └─ 现金水平

2. LLM 生成风险报告
   ├─ 评估当前风险水平
   ├─ 建议仓位调整
   └─ 建议现金保留比例

3. 输出风险报告
   └─ risk_report = {
        "risk_level": "medium",
        "recommendations": [...],
        "position_limits": {...}
      }
```

**输出**: `risk_report` 字典

---

### 阶段 6: 交易决策 (Trading Decision)

**代码位置**: `backend/src/agents/trader_agent.py::run_trader()`

**触发**: `execute_daily_trade()` 调用 (行452-470)

**流程**:
```
1. 准备交易决策提示词
   ├─ market_view: 市场数据
   ├─ consensus: 分析师共识
   ├─ risk_report: 风险报告
   ├─ current_positions: 当前持仓
   ├─ available_cash: 可用现金
   └─ order_status: 订单状态

2. LLM 生成交易决策
   ├─ 评估每个推荐股票
   ├─ 考虑 VIX 风险水平
   ├─ 应用风险报告的仓位限制
   ├─ 计算仓位大小（考虑可用现金）
   └─ 生成买入/卖出订单

3. 订单生成逻辑
   ├─ 买入订单:
   │   ├─ 价格范围: [98% * current_price, current_price]
   │   └─ 数量: 根据 available_cash 计算
   │
   └─ 卖出订单:
       ├─ 价格范围: [100.5% * current_price, 102% * current_price]
       └─ 数量: 根据当前持仓计算

4. 现金检查
   ├─ 如果 available_cash <= 0: 不生成买入订单
   └─ 确保总买入成本 <= available_cash
```

**输出**: `decision` 字典，包含:
- `orders`: 订单列表
- `reasoning`: 决策理由

**订单格式**:
```json
{
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "price_range": [147.0, 150.0],
  "limit_price": 150.0,
  "order_date": "2025-01-28"
}
```

---

### 阶段 7: 订单去重和放置 (Order Deduplication & Placement)

**代码位置**: `backend/src/data/order_manager.py::place_order()`

**触发**: `execute_daily_trade()` 调用 (行472-520)

**流程**:
```
1. 订单去重
   ├─ 检查是否有相同 symbol + action + order_date 的订单
   └─ 如果有，先删除旧订单

2. 放置订单
   ├─ 写入 pending_orders.jsonl
   └─ 格式:
       {
         "order_id": "uuid",
         "symbol": "NVDA",
         "action": "BUY",
         "quantity": 10,
         "limit_price": 150.0,
         "order_date": "2025-01-28",
         "status": "PENDING",
         "placed_at": "2025-01-28T10:00:00Z"
       }

3. 更新订单状态
   └─ 如果市场开盘且是实时模式: 立即检查订单是否可成交
```

**输出**: 订单写入 `pending_orders.jsonl`

---

### 阶段 8: 订单结算 (Order Settlement)

**代码位置**: `backend/src/orchestrator/trading_cycle.py::execute_daily_trade()` (行522-600)

**流程**:
```
1. 检查市场是否开盘
   ├─ 如果市场开盘: 实时模式
   └─ 如果市场收盘: 模拟模式（使用历史数据）

2. 订单结算逻辑
   ├─ 对于每个 pending 订单:
   │   ├─ 获取当日 High/Low 价格
   │   ├─ 买入订单: 如果 Low <= limit_price，则成交
   │   └─ 卖出订单: 如果 High >= limit_price，则成交
   │
   └─ 如果成交:
       ├─ 计算成交价格 (使用 limit_price 或实际价格)
       ├─ 更新 Portfolio
       ├─ 写入 filled_orders.jsonl
       └─ 从 pending_orders.jsonl 删除

3. 更新 Portfolio
   ├─ 买入: 减少现金，增加持仓
   └─ 卖出: 增加现金，减少持仓
```

**输出**: 
- 更新的 `Portfolio` 对象
- `filled_orders.jsonl` 更新
- `pending_orders.jsonl` 更新

---

### 阶段 9: 订单检查 (Order Check) - 实时模式

**API端点**: `POST /api/trading/check-pending-orders`

**代码位置**: `backend/src/api/server.py::check_pending_orders()` (行1800-1950)

**触发**: 前端每10秒自动调用（如果市场开盘）

**流程**:
```
1. 加载 pending 订单
   └─ 从 pending_orders.jsonl 读取

2. 检查每个订单
   ├─ 获取实时价格（通过 yfinance）
   ├─ 买入订单: 如果 current_price <= limit_price，则成交
   └─ 卖出订单: 如果 current_price >= limit_price，则成交

3. 如果订单成交
   ├─ 更新 Portfolio
   ├─ 写入 filled_orders.jsonl
   ├─ 从 pending_orders.jsonl 删除
   └─ 写入 execution 类型对话记录
```

**输出**: 
- 更新的订单状态
- 对话记录（execution 类型）

**执行对话记录格式**:
```json
{
  "timestamp": "2025-01-28T10:05:00Z",
  "date": "2025-01-28",
  "agent": "OrderManager",
  "round": 0,
  "content": "Executed: BUY 10 NVDA @ $150.00",
  "type": "execution"
}
```

---

### 阶段 10: 数据持久化 (Data Persistence)

**代码位置**: `backend/src/orchestrator/trading_cycle.py::execute_daily_trade()` (行600-700)

**流程**:
```
1. 保存 Portfolio 状态
   └─ portfolio_state.json

2. 记录净值历史
   └─ equity_history.jsonl
      {
        "date": "2025-01-28",
        "value": 10046.35,
        "pnl": 46.35
      }

3. 保存每日记忆
   └─ memory/daily/2025-01-28.json
      {
        "market_view": {...},
        "discussion": {...},
        "risk_report": {...},
        "trading_decisions": {...},
        "portfolio_snapshot": {...}
      }
```

---

## 📦 订单管理流程

### 订单生命周期

```
1. 订单生成 (Trader Agent)
   └─ 生成订单对象
      ├─ symbol, action, quantity, price_range, limit_price
      └─ order_date

2. 订单放置 (OrderManager.place_order)
   └─ 写入 pending_orders.jsonl
      ├─ status: "PENDING"
      └─ placed_at: timestamp

3. 订单检查 (实时模式)
   ├─ 前端每10秒调用 /api/trading/check-pending-orders
   └─ 后端检查价格是否满足条件

4. 订单成交
   ├─ 更新 Portfolio
   ├─ 写入 filled_orders.jsonl
   │   ├─ status: "FILLED"
   │   ├─ fill_price: 实际成交价
   │   └─ filled_at: timestamp
   │
   └─ 从 pending_orders.jsonl 删除

5. 订单过期 (可选)
   └─ 如果订单在当日未成交，保留在 pending_orders.jsonl
      └─ 可以在下一个交易日继续检查
```

### 订单去重逻辑

**代码位置**: `backend/src/data/order_manager.py::place_order()` (行80-100)

**规则**:
```
在放置新订单前:
1. 查找相同 symbol + action + order_date 的订单
2. 如果找到，删除旧订单
3. 放置新订单

目的: 避免同一股票、同一操作、同一日期的重复订单
```

---

## 💬 对话/聊天流程

### 对话记录结构

**文件**: `data/logs/discussion_actions.jsonl`

**类型**:
1. **discussion**: 分析师讨论
2. **tool**: 工具调用
3. **execution**: 订单执行

### Discussion 类型

**生成时机**: 多分析师讨论阶段

**格式**:
```json
{
  "timestamp": "2025-01-28T10:00:00Z",
  "date": "2025-01-28",
  "agent": "MarketAnalyst",
  "round": 0,
  "content": "Stance: bullish\n\nAnalysis: 市场整体趋势向上...",
  "type": "discussion",
  "stance": "bullish",
  "tools_used": ["news_scan", "vix_term"],
  "analysis": "市场整体趋势向上，建议关注科技股..."
}
```

### Tool 类型

**生成时机**: 分析师调用工具时

**格式**:
```json
{
  "timestamp": "2025-01-28T10:01:00Z",
  "date": "2025-01-28",
  "agent": "TechnicalAnalyst",
  "round": 1,
  "content": "Tool: get_support_resistance\nResult: {...}",
  "type": "tool",
  "tool": "get_support_resistance",
  "result": {...}
}
```

### Execution 类型

**生成时机**: 订单成交时

**格式**:
```json
{
  "timestamp": "2025-01-28T10:05:00Z",
  "date": "2025-01-28",
  "agent": "OrderManager",
  "round": 0,
  "content": "Executed: BUY 10 NVDA @ $150.00",
  "type": "execution"
}
```

### 前端显示逻辑

**代码位置**: `frontend/monitor.html::renderConversationsOverview()`

**流程**:
```
1. 读取 discussion_actions.jsonl
2. 过滤: 只显示 type="discussion" 的条目
3. 提取工具信息:
   ├─ 从 tools_used 字段获取工具列表
   └─ 从 tool 类型条目获取工具结果摘要
4. 生成对话显示:
   ├─ 显示分析师名称和时间
   ├─ 显示 stance
   ├─ 显示 analysis (100-150字摘要)
   └─ 显示使用的工具和简要结果
```

---

## ⚙️ 执行流程

### 实时模式 (市场开盘)

**触发**: 市场开盘时，用户点击 "Start Trading"

**流程**:
```
1. 执行交易周期
   └─ 生成订单 → 写入 pending_orders.jsonl

2. 前端启动订单检查
   └─ 每10秒调用 /api/trading/check-pending-orders

3. 订单检查
   ├─ 获取实时价格
   ├─ 检查是否满足成交条件
   └─ 如果成交，更新 Portfolio 和订单状态

4. 前端刷新
   └─ 每5秒刷新数据（portfolio, orders, conversations）
```

### 规划模式 (市场收盘)

**触发**: 市场收盘时，用户点击 "Plan Tomorrow"

**流程**:
```
1. 执行交易周期
   ├─ 使用下一个交易日作为 order_date
   ├─ 生成订单 → 写入 pending_orders.jsonl
   └─ 订单状态: PENDING (等待下一个交易日)

2. 前端显示
   ├─ 显示 "TOMORROW" 标记
   └─ 显示订单详情（但不执行）
```

### 自动交易模式 (Auto Trading)

**触发**: 用户勾选 "Auto Trade" 复选框

**流程**:
```
1. 市场开盘时
   ├─ 自动调用 /api/trading/execute-trade
   └─ 执行完整交易周期

2. 市场收盘时
   ├─ 自动调用 /api/trading/execute-trade
   └─ 规划下一个交易日

3. 市场状态监控
   └─ 每30秒检查市场状态
      ├─ 如果从 "closed" 变为 "open"
      └─ 自动重启 Auto Trading
```

---

## 📊 数据流

### 数据流向图

```
┌─────────────────┐
│   Frontend      │
│  (monitor.html) │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│   FastAPI       │
│   (server.py)   │
└────────┬────────┘
         │
         ├──► execute_daily_trade()
         │    │
         │    ├──► fetch_market_batch()
         │    │    └──► market_view
         │    │
         │    ├──► run_multi_analyst_discussion()
         │    │    ├──► MarketAnalyst
         │    │    ├──► TechnicalAnalyst
         │    │    ├──► FundamentalAnalyst
         │    │    ├──► SentimentAnalyst
         │    │    └──► DiscussionCoordinator
         │    │         └──► discussion_actions.jsonl
         │    │
         │    ├──► run_risk_analyst_llm()
         │    │    └──► risk_report
         │    │
         │    ├──► run_trader()
         │    │    └──► orders
         │    │
         │    └──► OrderManager.place_order()
         │         └──► pending_orders.jsonl
         │
         └──► check_pending_orders()
              ├──► 检查价格
              ├──► 更新 Portfolio
              └──► filled_orders.jsonl
```

### 数据文件

```
data/
├── logs/
│   ├── discussion_actions.jsonl    # 对话记录
│   ├── pending_orders.jsonl        # 待执行订单
│   ├── filled_orders.jsonl         # 已执行订单
│   └── equity_history.jsonl        # 净值历史
│
├── portfolio_state.json            # Portfolio 状态
│
└── memory/
    └── daily/
        └── YYYY-MM-DD.json         # 每日记忆
```

---

## 🔍 关键配置

### config.json

```json
{
  "universe": ["NVDA", "MSFT", "AAPL", ...],  // 100+ 股票
  "tool_budget": 8,                            // 工具调用预算
  "rounds": 3,                                 // 讨论轮数
  "min_cash_reserve_ratio": 0.20,              // 最小现金保留比例
  "max_position_per_stock": 0.15,              // 单股最大仓位
  "max_total_position": 0.80                   // 总仓位上限
}
```

---

## 📝 总结

### 完整流程时间线

```
09:00 (市场开盘前)
  ├─ 用户点击 "Start Trading"
  ├─ 执行交易周期
  │   ├─ 获取市场数据
  │   ├─ 多分析师讨论
  │   ├─ 风险分析
  │   ├─ 交易决策
  │   └─ 放置订单
  │
  └─ 订单写入 pending_orders.jsonl

09:30 (市场开盘)
  ├─ 前端开始订单检查（每10秒）
  ├─ 后端检查订单价格
  └─ 如果满足条件，订单成交

16:00 (市场收盘)
  ├─ 用户点击 "Plan Tomorrow"
  ├─ 执行交易周期（使用下一个交易日）
  └─ 订单写入 pending_orders.jsonl（标记为 TOMORROW）

次日 09:30
  └─ 订单检查机制继续检查昨日订单
```

### 关键点

1. **订单去重**: 同一股票、同一操作、同一日期只保留一个订单
2. **现金检查**: 买入订单必须确保有足够现金
3. **持仓信息**: 所有Agent都能看到当前持仓和可用现金
4. **对话记录**: 所有分析、工具调用、订单执行都记录在 discussion_actions.jsonl
5. **实时检查**: 市场开盘时，前端每10秒检查订单状态
6. **自动交易**: 支持自动交易模式，市场开盘时自动执行

---

**文档生成时间**: 2025-01-28
**系统版本**: v1.0

