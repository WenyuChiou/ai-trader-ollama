# 📊 当前工作流程 (Current Workflow)

## 🔄 完整的每日交易工作流程

### 概述

系统执行以下流程：分析昨日收盘数据 + 昨日/今日新闻 → 做出今日交易决策 → 执行交易 → 更新持仓

### 详细流程

```
┌─────────────────────────────────────────────────────────────────┐
│                   每日交易工作流程                                │
│      (Yesterday's Close + News → Today's Trading Decision)     │
└─────────────────────────────────────────────────────────────────┘

STEP 1: 市场数据收集 (Market Data Collection)
├─ fetch_market_batch(universe)
│  ├─ 抓取 universe 中所有股票的 OHLCV 数据
│  ├─ 计算技术指标：
│  │  ├─ RSI14 (相对强弱指标)
│  │  ├─ MACD (移动平均收敛散度)
│  │  ├─ Bollinger Bands (布林带)
│  │  ├─ MA20, MA50 (移动平均)
│  │  └─ signal_score (综合信号评分)
│  └─ 附加 VIX 特征：
│     ├─ VIX level (波动率水平)
│     ├─ VIX change_1d (单日变化)
│     └─ VIX zscore (标准化分数)
│
└─ Output: market_view
   {
     "stocks": {
       "NVDA": {price, change_pct, rsi14, macd, bb_pos, signal_score, ...},
       "MSFT": {...},
       ...
     },
     "VIX": {level, chg_1d, zscore}
   }

         ↓

STEP 2: 准备 Enriched Market View
├─ 提取股票列表和 Top 信号
├─ 准备 enriched_market 给讨论层
└─ Output: enriched_market
   {
     "symbols": ["NVDA", "MSFT", ...],
     "stocks": {...},
     "vix": {...},
     "signal_score_top": [("NVDA", 5.0), ...],
     "vix_term": None,  # 将在 Discussion 中获取
     "fear_greed": None,  # 将在 Discussion 中获取
     "news": None  # 将在 Discussion 中获取
   }

         ↓

STEP 3: Analyst Discussion (多轮讨论 + 自动工具调用)
├─ run_analyst_discussion(enriched_market, rounds=3, tool_budget=2)
│
│  ROUND 1:
│  ├─ Discussion Agent 分析市场数据
│  ├─ 判断是否需要更多信息
│  ├─ 如果需要 → 调用工具：
│  │  ├─ news_scan: 扫描相关新闻
│  │  ├─ vix_term: 获取 VIX 期限结构
│  │  └─ fear_greed: 获取恐惧贪婪指数
│  ├─ 工具结果注入到 [TOOLS CONTEXT]
│  └─ 输出 JSON: {stance, rationale, tool_calls, actions}
│
│  ROUND 2:
│  ├─ Discussion Agent 接收上一轮的工具结果
│  ├─ 被明确告知：不要重复调用已执行过的工具
│  ├─ 基于工具结果进行推理和反思
│  └─ 输出更新的 JSON: {stance, rationale, ...}
│
│  ROUND 3: (可选，如果 rounds > 2)
│  └─ 进一步细化和确认立场
│
└─ Output: convo
   {
     "final_stance": "bullish" | "bearish" | "neutral",
     "rounds": 3,
     "transcript": ["Round 1 output", "Round 2 output", ...],
     "actions": [{"action": "consider_probe"}, ...],
     "tool_context": [
       "news_scan: 15 hits, queries=['NVDA'], ...",
       "vix_term: VIX=16.5, VIX3M=19.0, ratio=1.15",
       ...
     ]
   }

         ↓

STEP 4: Risk Analyst (风险评估)
├─ run_risk_analyst(
│    market_json=market_view,
│    current_positions=current_positions_info,
│    portfolio_value=portfolio_value,
│    discussion_risk_signals=discussion_risk_signals
│  )
│  ├─ 评估市场风险（基于股票指标）
│  ├─ 评估当前仓位风险：
│  │  ├─ position_concentration (仓位集中度，使用 HHI)
│  │  ├─ single_stock_exposure (单股暴露度)
│  │  └─ overall_exposure (总仓位暴露度)
│  ├─ 综合 Discussion 的风险信号
│  └─ 生成仓位控管报告：
│     ├─ recommended_position_sizes (推荐仓位大小)
│     ├─ position_limit_checks (仓位限制检查)
│     └─ rebalancing_suggestions (再平衡建议)
│
└─ Output: risk_report
   {
     "overall_risk_level": "low" | "medium" | "high",
     "risk_score": 5.5,
     "max_position_size": {
       "per_stock": 0.15,  # 单股最大 15%
       "total_equity": 0.60  # 总仓位最大 60%
     },
     "risk_warnings": ["AAPL risk=6.5"],
     "current_position_risk": {
       "position_concentration": 0.35,
       "single_stock_exposure": {...},
       "overall_exposure": 0.45
     },
     "position_control_report": {
       "recommended_position_sizes": {...},
       "position_limit_checks": [...]
     }
   }

         ↓

STEP 5: Trader Agent (交易决策)
├─ run_trader(
│    market=market_view,
│    mview=enriched_market,
│    rview=risk_report,
│    convo=convo,
│    last_prices=last_prices,
│    current_positions=current_positions_info,
│    portfolio_value=portfolio_value
│  )
│  ├─ 分析市场立场（来自 Discussion）
│  ├─ 考虑风险报告（来自 Risk Analyst）
│  ├─ 评估所有候选股票：
│  │  ├─ 计算综合评分 (0-10)
│  │  ├─ 评估趋势 (uptrend/downtrend/sideways)
│  │  ├─ 评估风险评分
│  │  └─ 生成推荐 (BUY/HOLD/SELL)
│  ├─ 筛选 potential_buys (score >= 3.0, recommendation="BUY")
│  ├─ 评估当前持仓：
│  │  ├─ holdings_to_sell: 需要卖出的持仓
│  │  ├─ holdings_to_hold: 需要持有的持仓
│  │  └─ holdings_to_increase: 需要增持的持仓
│  ├─ 计算买入数量（考虑风险限制）
│  ├─ 计算卖出数量（考虑风险限制）
│  └─ 生成详细的买卖订单
│
└─ Output: decision
   {
     "action": "BUY" | "SELL" | "HOLD",
     "targets": [
       {"symbol": "NVDA", "action": "BUY", "price": 150.0, "quantity": 10}
     ],
     "buy_orders": [
       {
         "symbol": "NVDA",
         "buy_price": 150.0,
         "quantity": 10,
         "total_cost": 1500.0
       }
     ],
     "sell_orders": [
       {
         "symbol": "AAPL",
         "sell_price": 180.0,
         "quantity": 5,
         "total_proceeds": 900.0
       }
     ],
     "potential_buys": [
       {
         "symbol": "NVDA",
         "score": 8.5,
         "trend": "uptrend",
         "risk_score": 4.5,
         "recommendation": "BUY",
         "reasons": ["Strong momentum", "Positive news"]
       }
     ],
     "position_adjustments": [
       {
         "symbol": "AAPL",
         "action": "REDUCE",
         "current_quantity": 20,
         "recommended_quantity": 10,
         "reason": "Position exceeds risk limit"
       }
     ],
     "rationale": "买入理由：技术指标显示强势，市场情绪乐观...",
     "stance": "bullish",
     "vix_risk": 5.2,
     "risk_compliance": {
       "position_limits_ok": True,
       "diversification_ok": True,
       "warnings": []
     }
   }

         ↓

STEP 6: Trade Execution (执行交易)
├─ 执行买入订单 (buy_orders)
│  ├─ 对于每个 buy_order:
│  │  ├─ portfolio.buy(symbol, quantity, buy_price)
│  │  │  ├─ 更新现金余额
│  │  │  ├─ 更新持仓（加权平均成本计算）
│  │  │  └─ 记录交易历史
│  │  └─ trade_logger.log(
│  │       symbol, action="BUY", price, quantity, amount,
│  │       status="SUCCESS", rationale, stance, vix_risk
│  │     )
│  └─ 记录 executed_trades
│
├─ 执行卖出订单 (sell_orders)
│  ├─ 对于每个 sell_order:
│  │  ├─ portfolio.sell(symbol, quantity, sell_price)
│  │  │  ├─ 更新现金余额
│  │  │  ├─ 更新持仓（部分卖出时保持平均成本）
│  │  │  └─ 记录交易历史
│  │  └─ trade_logger.log(
│  │       symbol, action="SELL", price, quantity, amount,
│  │       status="SUCCESS", rationale, stance, vix_risk
│  │     )
│  └─ 记录 executed_trades
│
└─ 错误处理
   └─ 如果执行失败，记录 execution_errors

         ↓

STEP 7: Portfolio Status (计算持仓状态)
├─ 计算当前持仓 P&L
│  ├─ portfolio.get_all_positions_pnl(last_prices)
│  │  └─ 每个持仓的盈亏
│  ├─ portfolio.total_pnl(last_prices)
│  │  └─ 总盈亏（未实现盈亏）
│  └─ portfolio.total_pnl_pct(last_prices)
│     └─ 总盈亏百分比（相对于初始投资）
│
├─ 计算组合价值
│  ├─ portfolio.value(last_prices)
│  │  └─ 总净值（现金 + 持仓市值）
│  └─ portfolio.equity_value(last_prices)
│     └─ 持仓市值
│
└─ Output: portfolio_info
   {
     "cash": 8200.0,
     "positions": {
       "NVDA": {
         "quantity": 10,
         "avg_cost": 150.0,
         "current_price": 152.0,
         "market_value": 1520.0
       }
     },
     "total_value": 9720.0,
     "equity_value": 1520.0,
     "total_pnl": 20.0,
     "total_pnl_pct": 0.20,
     "positions_pnl": {
       "NVDA": 20.0
     }
   }

         ↓

STEP 8: Return Results (返回结果)
└─ 返回完整的交易循环结果
   {
     "stance": "bullish",
     "decision": {...},  # Trader Agent 决策
     "risk_report": {...},  # Risk Analyst 报告
     "discussion": {
       "final_stance": "bullish",
       "rounds": 3,
       "transcript": [...],  # 完整的讨论记录
       "actions": [...],  # 讨论动作
       "tool_context": [...]  # 工具使用历史
     },
     "rounds": 3,
     "symbols": ["NVDA", "MSFT", ...],
     "top_signals": [("NVDA", 5.0), ...],
     "executed_trades": [...],  # 实际执行的交易
     "execution_errors": [],  # 执行错误
     "portfolio": {...}  # Portfolio 状态
   }
```

---

## 🎯 关键 Agents 及其职责

### 1. **Discussion Agent** (讨论代理)
- **职责**: 分析市场数据，使用工具补充信息，形成市场立场
- **工具**: 
  - `news_scan`: 扫描相关新闻
  - `vix_term`: 获取 VIX 期限结构
  - `fear_greed`: 获取恐惧贪婪指数
  - `web_search`, `fetch_url`: 搜索和获取网页内容
- **输出**: 
  - `final_stance`: 市场立场（bullish/bearish/neutral）
  - `transcript`: 完整的讨论记录
  - `tool_context`: 工具使用历史
  - `rationale`: 推理过程

### 2. **Risk Analyst** (风险分析师)
- **职责**: 评估市场风险和当前仓位风险，提供仓位控管建议
- **输入**:
  - `market_json`: 市场数据
  - `current_positions`: 当前持仓
  - `portfolio_value`: 组合净值
  - `discussion_risk_signals`: 来自 Discussion 的风险信号
- **输出**:
  - `overall_risk_level`: 整体风险等级
  - `risk_score`: 风险评分
  - `current_position_risk`: 当前仓位风险
  - `position_control_report`: 仓位控管报告

### 3. **Trader Agent** (交易代理)
- **职责**: 基于所有信息做出最终交易决策
- **输入**:
  - `market`: 市场数据
  - `mview`: enriched market view
  - `rview`: 风险报告
  - `convo`: 讨论共识
  - `last_prices`: 最新价格
  - `current_positions`: 当前持仓
  - `portfolio_value`: 组合净值
- **输出**:
  - `action`: BUY/SELL/HOLD
  - `buy_orders`: 买入订单列表（包含价格、数量、总成本）
  - `sell_orders`: 卖出订单列表（包含价格、数量、总收益）
  - `potential_buys`: 潜在购买股票列表
  - `position_adjustments`: 持仓调整建议
  - `rationale`: 决策理由

---

## 🔄 数据流

### 输入数据流

```
config.json (universe, date_range)
    ↓
fetch_market_batch(universe, start, end)
    ↓
market_view {stocks, VIX, indicators}
    ↓
enriched_market {stocks, symbols, vix, signal_top}
    ↓
run_analyst_discussion(enriched_market)
    ↓
convo {final_stance, transcript, tool_context}
    ↓
run_risk_analyst(market_view, current_positions, discussion_risk_signals)
    ↓
risk_report {overall_risk_level, position_control_report, ...}
    ↓
run_trader(market, mview, rview, convo, last_prices, current_positions)
    ↓
decision {buy_orders, sell_orders, rationale, ...}
    ↓
Execute trades (portfolio.buy/sell, trade_logger.log)
    ↓
Calculate portfolio status (P&L, positions, value)
    ↓
Return complete results
```

### 工具调用流程 (Discussion Agent)

```
ROUND 1:
  Discussion Agent
    ↓
  分析市场数据 → 判断需要更多信息
    ↓
  调用工具: news_scan, vix_term, fear_greed
    ↓
  工具结果注入 [TOOLS CONTEXT]
    ↓
  基于工具结果推理
    ↓
  输出: {stance, rationale, tool_calls}

ROUND 2:
  Discussion Agent
    ↓
  接收 [TOOLS CONTEXT]（上一轮的工具结果）
    ↓
  被明确告知：不要重复调用已执行过的工具
    ↓
  基于工具结果进行深度推理和反思
    ↓
  输出更新的: {stance, rationale}

ROUND 3: (可选)
  进一步细化和确认立场
    ↓
  finalize: {final_stance, ...}
```

---

## 📋 每日最终输出

每天执行完成后，系统会输出：

### 1. **执行结果** (`executed_trades`)
```json
[
  {
    "symbol": "NVDA",
    "action": "BUY",
    "price": 150.0,
    "quantity": 10,
    "amount": 1500.0,
    "status": "SUCCESS"
  }
]
```

### 2. **交易决策** (`decision`)
```json
{
  "action": "BUY",
  "buy_orders": [...],
  "sell_orders": [...],
  "potential_buys": [...],
  "position_adjustments": [...],
  "rationale": "...",
  "stance": "bullish",
  "vix_risk": 5.2,
  "risk_compliance": {...}
}
```

### 3. **风险评估** (`risk_report`)
```json
{
  "overall_risk_level": "medium",
  "risk_score": 5.5,
  "current_position_risk": {...},
  "position_control_report": {...}
}
```

### 4. **讨论记录** (`discussion`)
```json
{
  "final_stance": "bullish",
  "rounds": 3,
  "transcript": [
    "Round 1: ...",
    "Round 2: ...",
    "Round 3: ..."
  ],
  "tool_context": [
    "news_scan: 15 hits, ...",
    "vix_term: VIX=16.5, ..."
  ]
}
```

### 5. **Portfolio 状态** (`portfolio`)
```json
{
  "cash": 8200.0,
  "positions": {...},
  "total_value": 9720.0,
  "equity_value": 1520.0,
  "total_pnl": 20.0,
  "total_pnl_pct": 0.20,
  "positions_pnl": {...}
}
```

---

## 🔄 Feedback Loop 状态

### ✅ 已实现的基本循环
- Market Data Collection
- Analyst Discussion (自动工具调用)
- Risk Analyst (风险评估)
- Trader Agent (交易决策)
- Trade Execution (执行)
- Trade Logger (记录)

### ⏳ 尚未实现的 Feedback Loop
- **Performance Agent**: 分析历史交易记录，计算绩效指标
- **Feedback Loop**: 将历史绩效反馈到下一轮决策

---

## 🚀 运行工作流程

### 运行完整交易循环

```bash
cd backend
python run.py
```

### 运行详细测试查看每轮过程

```bash
cd backend
python run_detailed_test.py
```

### 运行 Agent 验证测试

```bash
cd backend
python test_all_agents.py
```

---

## 📝 关键特性

### 1. **自动工具调用**
- Discussion Agent 可以根据需要自动调用工具
- 工具结果会自动注入到下一轮讨论中
- 避免重复调用已执行过的工具

### 2. **多轮讨论机制**
- 支持多轮讨论（默认 3 轮）
- 每轮可以调用工具补充信息
- 连续 2 轮无新工具时提前结束

### 3. **风险评估集成**
- Risk Analyst 评估市场风险和仓位风险
- 提供详细的仓位控管报告
- Trader Agent 根据风险报告调整仓位大小

### 4. **详细的交易决策**
- Trader Agent 生成详细的买卖订单
- 包含价格、数量、总成本/收益
- 提供决策理由和风险合规检查

### 5. **完整的交易记录**
- 所有交易记录保存到 Trade Logger
- 包含交易详情、理由、市场立场、VIX 风险等
- 支持查询和统计分析

---

**更新日期**: 2025-11-02

