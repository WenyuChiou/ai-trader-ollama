# 🔄 AI Trader Agent System - Information Chart

## 📊 完整系统流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI TRADER AGENT SYSTEM                              │
│                        Multi-Agent Trading Decision Flow                      │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │         GOAL: Daily Trading           │
                    │      "Make trading decisions"         │
                    │    (BUY/SELL/HOLD with positions)     │
                    └──────────────┬─────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │     1. MARKET DATA COLLECTION         │
                    │         (Market Agent)                │
                    │                                        │
                    │  ┌──────────────────────────────┐   │
                    │  │ Fetch:                        │   │
                    │  │ • Stock prices (OHLCV)       │   │
                    │  │ • Market indicators          │   │
                    │  │ • VIX data                  │   │
                    │  │ • Technical signals          │   │
                    │  └──────────────────────────────┘   │
                    └──────────────┬─────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │    2. MARKET ANALYSIS & INSIGHTS      │
                    │        (Market Analyst)               │
                    │                                        │
                    │  ┌──────────────────────────────┐   │
                    │  │ Analyze:                      │   │
                    │  │ • Technical patterns          │   │
                    │  │ • Market sentiment            │   │
                    │  │ • Recommended stocks          │   │
                    │  │ • Key observations            │   │
                    │  └──────────────────────────────┘   │
                    └──────────────┬─────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │             3. COLLABORATIVE DISCUSSION                          │
        │               (Analyst Discussion)                                │
        │              "Multi-Round Consensus Building"                      │
        │                                                                   │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │                    Round 1, 2, 3... N                   │    │
        │  │                                                          │    │
        │  │  ┌──────────┐    ┌──────────┐    ┌──────────┐         │    │
        │  │  │ Market    │◄───►│ Analyst  │◄───►│ Discussion│        │    │
        │  │  │ Analyst   │    │ Discussion│    │ Consensus │        │    │
        │  │  └──────────┘    └──────────┘    └──────────┘         │    │
        │  │                                                          │    │
        │  │  Tools Used:                                             │    │
        │  │  • news_scan     • vix_term                             │    │
        │  │  • fear_greed    • fetch_url                             │    │
        │  │  • plan_and_scan_news                                    │    │
        │  │                                                          │    │
        │  │  Output:                                                 │    │
        │  │  • final_stance (bullish/neutral/bearish)              │    │
        │  │  • rationale (reasoning)                                 │    │
        │  │  • signals_used                                         │    │
        │  │  • risk_signals (for Risk Analyst)                      │    │
        │  └─────────────────────────────────────────────────────────┘    │
        └──────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │           4. RISK ASSESSMENT & POSITION CONTROL                   │
        │                    (Risk Analyst)                                │
        │                                                                   │
        │  Inputs:                                                          │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • Market data (from Market Agent)                      │    │
        │  │ • Analysis results (from Market Analyst)               │    │
        │  │ • Discussion consensus (from Analyst Discussion)      │    │
        │  │ • Risk signals (from Analyst Discussion)               │    │
        │  │ • Current positions (from Portfolio)                   │    │
        │  │ • Portfolio value                                       │    │
        │  └─────────────────────────────────────────────────────────┘    │
        │                                                                   │
        │  Assessment:                                                       │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • Market risk evaluation                                │    │
        │  │ • Current position risk evaluation                     │    │
        │  │ • Position concentration analysis                       │    │
        │  │ • Single stock exposure analysis                        │    │
        │  └─────────────────────────────────────────────────────────┘    │
        │                                                                   │
        │  Output:                                                          │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • overall_risk_level                                    │    │
        │  │ • risk_score                                            │    │
        │  │ • max_position_size (per_stock / total)                │    │
        │  │ • current_position_risk                                 │    │
        │  │ • Position Control Report:                              │    │
        │  │   - recommended_position_sizes                         │    │
        │  │   - position_limit_checks                               │    │
        │  │   - rebalancing_suggestions                             │    │
        │  └─────────────────────────────────────────────────────────┘    │
        └──────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │                 5. TRADING DECISION                               │
        │                      (Trader Agent)                               │
        │                                                                   │
        │  Inputs:                                                          │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • market_view (from Market Agent)                      │    │
        │  │ • market_analysis (from Market Analyst)                │    │
        │  │ • discussion_consensus (from Analyst Discussion)        │    │
        │  │ • risk_view (from Risk Analyst)                        │    │
        │  │ • current_positions (from Portfolio)                    │    │
        │  │ • last_prices (current market prices)                   │    │
        │  └─────────────────────────────────────────────────────────┘    │
        │                                                                   │
        │  Decision Process:                                               │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • Evaluate all inputs                                     │    │
        │  │ • Consider risk constraints                              │    │
        │  │ • Check position limits                                  │    │
        │  │ • Determine BUY/SELL/HOLD                                │    │
        │  │ • Select target stocks                                   │    │
        │  │ • Calculate position sizes                               │    │
        │  │ • Set buy/sell prices                                    │    │
        │  └─────────────────────────────────────────────────────────┘    │
        │                                                                   │
        │  Output:                                                          │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • action: BUY / SELL / HOLD                             │    │
        │  │ • buy_orders: [                                        │    │
        │  │     {symbol, buy_price, quantity, total_cost}        │    │
        │  │   ]                                                    │    │
        │  │ • sell_orders: [                                       │    │
        │  │     {symbol, sell_price, quantity, total_proceeds}    │    │
        │  │   ]                                                    │    │
        │  │ • rationale                                             │    │
        │  │ • risk_compliance (position_limits_ok, etc.)          │    │
        │  └─────────────────────────────────────────────────────────┘    │
        └──────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │                 6. EXECUTION & PORTFOLIO UPDATE                  │
        │                                                                   │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ • Execute buy orders                                     │    │
        │  │ • Execute sell orders                                    │    │
        │  │ • Update Portfolio positions                             │    │
        │  │ • Update Portfolio cash                                  │    │
        │  │ • Log trades to TradeLogger                               │    │
        │  └─────────────────────────────────────────────────────────┘    │
        └──────────────┬───────────────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │                   7. BACKEND DISPLAY SYSTEM                       │
        │              "Portfolio & Trade History Display"                  │
        │                                                                   │
        │  ┌─────────────────────────────────────────────────────────┐    │
        │  │ A. Profit & Loss Display                                 │    │
        │  │    • Real-time P&L calculation                           │    │
        │  │    • Portfolio net value                                  │    │
        │  │    • Per-stock P&L details                               │    │
        │  │    • P&L distribution charts                             │    │
        │  │                                                           │    │
        │  │ B. Trade History Display                                 │    │
        │  │    • Trade records list                                  │    │
        │  │    • Trade statistics                                     │    │
        │  │    • Execution status                                    │    │
        │  │                                                           │    │
        │  │ C. Position Display                                      │    │
        │  │    • Position distribution                               │    │
        │  │    • Position status                                     │    │
        │  │                                                           │    │
        │  │ D. Risk Metrics Display                                 │    │
        │  │    • Risk indicators                                     │    │
        │  │    • Risk warnings                                        │    │
        │  │                                                           │    │
        │  │ E. Performance Display                                   │    │
        │  │    • Performance metrics                                 │    │
        │  │    • Performance trends                                 │    │
        │  └─────────────────────────────────────────────────────────┘    │
        └───────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │      8. EVALUATION & FEEDBACK          │
                    │                                        │
                    │  ┌──────────────────────────────┐   │
                    │  │ • Compare results vs goal     │   │
                    │  │ • Analyze performance         │   │
                    │  │ • Generate feedback           │   │
                    │  │ • Update for next cycle       │   │
                    │  └──────────────────────────────┘   │
                    └──────────────────────────────────────┘
                                   │
                                   │ (Feedback Loop)
                                   │
                                   ▼
                    ┌──────────────────────────────────────┐
                    │      NEXT TRADING CYCLE               │
                    │     (Return to Market Data)          │
                    └──────────────────────────────────────┘
```

## 🔄 详细轮次示例（类似图片底部）

### Round 1: Market Data Collection
```
┌──────────────────────────────────────────────────────────┐
│  Roles:                                                  │
│  • Market Agent (Data Collector)                        │
│                                                          │
│  State:                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Raw Market Data]                              │    │
│  │ • NVDA: $150.00                                │    │
│  │ • MSFT: $380.00                                │    │
│  │ • AAPL: $175.00                                │    │
│  │ • VIX: 15.2                                    │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Round 2: Analysis & Discussion
```
┌──────────────────────────────────────────────────────────┐
│  Roles:                                                  │
│  • Market Analyst (Technical Analysis)                   │
│  • Analyst Discussion (Multi-round Consensus)            │
│                                                          │
│  State:                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Analysis + Discussion Consensus]              │    │
│  │ • Recommended: NVDA, MSFT                      │    │
│  │ • Stance: constructive                         │    │
│  │ • Signals: RSI14, MACD, VIX term              │    │
│  │ • Risk signals: low                            │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Round 3: Risk Assessment
```
┌──────────────────────────────────────────────────────────┐
│  Roles:                                                  │
│  • Risk Analyst (Position Risk Evaluation)              │
│                                                          │
│  State:                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Risk Assessment + Position Control Report]    │    │
│  │ • Overall risk: medium                         │    │
│  │ • Current positions: NVDA (20%), MSFT (15%)     │    │
│  │ • Max per stock: 15%                           │    │
│  │ • Recommendation: add MSFT, reduce NVDA        │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Round 4: Trading Decision
```
┌──────────────────────────────────────────────────────────┐
│  Roles:                                                  │
│  • Trader Agent (Final Decision)                        │
│                                                          │
│  State:                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Trading Decision]                             │    │
│  │ • Action: BUY                                  │    │
│  │ • Buy: MSFT @ $380.00, qty: 50 shares         │    │
│  │ • Sell: NVDA @ $150.00, qty: 10 shares        │    │
│  │ • Rationale: Diversification + risk control    │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Round 5: Execution & Display
```
┌──────────────────────────────────────────────────────────┐
│  Roles:                                                  │
│  • Portfolio Manager (Execution)                        │
│  • Backend Display (P&L, Trade History)               │
│                                                          │
│  State:                                                  │
│  ┌────────────────────────────────────────────────┐    │
│  │ [Portfolio Updated + Display]                   │    │
│  │ • Positions: NVDA (10%), MSFT (20%)            │    │
│  │ • Total P&L: +$250.00 (+2.5%)                  │    │
│  │ • Trades logged: 2 (1 buy, 1 sell)             │    │
│  │ • Risk compliance: ✓                           │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## 🔑 关键流程说明

### 主循环 (Main Loop)
1. **Goal**: 每日交易决策
2. **Market Data Collection**: Market Agent 收集数据
3. **Market Analysis**: Market Analyst 分析数据
4. **Collaborative Discussion**: Analyst Discussion 多轮讨论
5. **Risk Assessment**: Risk Analyst 评估风险并生成仓位控管报告
6. **Trading Decision**: Trader Agent 做出最终交易决策
7. **Execution**: 执行交易并更新 Portfolio
8. **Backend Display**: 后端展示损益、交易记录等
9. **Evaluation**: 评估结果并反馈
10. **Next Cycle**: 进入下一个交易周期

### 反馈机制
- **Reward Feedback**: 从结果反馈到下一轮的市场数据收集
- **Position Feedback**: 从 Portfolio 反馈到 Risk Analyst
- **Performance Feedback**: 从后端展示反馈到 Trading Decision

---

**文档状态**: ✅ 流程图已创建  
**更新日期**: 2025-11-02

