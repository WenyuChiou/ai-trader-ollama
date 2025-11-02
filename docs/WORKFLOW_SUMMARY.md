# 📊 当前工作流程总结

## 🔄 完整的每日交易流程

```
┌─────────────────────────────────────────────────────────┐
│             每日交易工作流程                              │
│  (Yesterday's Close + News → Today's Trading Decision) │
└─────────────────────────────────────────────────────────┘

1. 市场数据收集
   ↓ fetch_market_batch(universe)
   → market_view: {stocks, VIX, indicators}

2. Analyst Discussion (多轮讨论)
   ↓ run_analyst_discussion(enriched_market)
   → 自动调用工具 (news_scan, vix_term, fear_greed)
   → 工具结果注入下一轮
   → 形成共识: final_stance

3. Risk Analyst (风险评估)
   ↓ run_risk_analyst(market_view, positions, discussion_signals)
   → 评估市场风险和仓位风险
   → 生成仓位控管报告

4. Trader Agent (交易决策)
   ↓ run_trader(market, mview, rview, convo, positions)
   → 评估所有候选股票
   → 生成买卖订单 (buy_orders, sell_orders)

5. 执行交易
   ↓ portfolio.buy/sell()
   → 更新持仓
   → trade_logger.log()

6. 返回结果
   → executed_trades, portfolio, P&L, ...
```

---

## 🎯 关键步骤详解

### STEP 1: Market Data Collection
- 抓取 universe 中所有股票的 OHLCV 数据
- 计算技术指标 (RSI, MACD, Bollinger Bands, etc.)
- 附加 VIX 特征

### STEP 2: Analyst Discussion (多轮)
- Round 1: 分析数据，判断需要更多信息 → 调用工具
- Round 2: 基于工具结果推理，形成立场
- Round 3: (可选) 进一步细化

### STEP 3: Risk Analyst
- 评估市场风险
- 评估当前仓位风险（集中度、暴露度）
- 生成仓位控管报告

### STEP 4: Trader Agent
- 评估所有候选股票
- 筛选 potential_buys
- 评估当前持仓
- 生成详细的买卖订单

### STEP 5: Execution
- 执行买入订单
- 执行卖出订单
- 更新 Portfolio
- 记录到 Trade Logger

### STEP 6: Results
- 计算 P&L
- 返回完整结果

---

## 📋 每轮循环展示

详细流程请参考：
- `docs/CURRENT_WORKFLOW.md` - 完整流程说明
- `docs/DISCUSSION_ROUNDS_EXAMPLE.md` - 讨论轮次示例
- `backend/run_detailed_test.py` - 运行详细测试查看每轮过程

