# 📊 完整信息流分析

## 🔄 当前信息流

### 优化后的完整流程

```
1. Market Data Collection
   fetch_market_batch(universe)
   → market_data: {stocks, VIX, indicators}
   ↓
2. Stock Selection Agent (NEW) 🔴
   run_stock_selection_agent(market_data, universe)
   → potential_buys: [{symbol, score, trend, recommendation, ...}]
   → stock_rankings: [sorted by score]
   ↓
3. Market Analysis (Optional)
   run_market_analyst(market_data)
   → market_analysis: {sentiment, recommended_stocks}
   ↓
4. Enriched Market View
   enriched_market = {
       ...market_data,
       potential_buys: potential_buys,  # NEW: 来自 Stock Selection Agent
       stock_rankings: stock_rankings,
   }
   ↓
5. Analyst Discussion (ENHANCED) 🔴
   run_analyst_discussion(enriched_market, potential_buys)
   → 讨论股票选择（potential_buys）
   → consensus: {final_stance, stock_discussion, risk_signals}
   ↓
6. Risk Analysis
   run_risk_analyst(market_data, positions, discussion_risk_signals)
   → risk_report: {risk_level, position_control_report}
   ↓
7. Trading Decision
   run_trader(market, mview, rview, convo, all_candidates)
   → decision: {
       buy_orders, sell_orders,
       potential_buys,  # 已包含在 convo 中讨论过的
       position_adjustments,
   }
   ↓
8. Execution
   execute_trades(decision)
   → portfolio.update()
   → trade_logger.log()
   ↓
9. Performance Analysis (TODO: 中优先级)
   run_performance_agent(portfolio, trade_logger)
   → performance_metrics, improvement_suggestions
   ↓
10. Feedback Loop (TODO: 中优先级)
    → 反馈给下一轮决策
```

## 📋 已添加的组件

### ✅ 已完成（高优先级）

#### 1. **Stock Selection Agent** ✅

**文件**: `backend/src/agents/stock_selection_agent.py`

**功能**:
- 评估所有候选股票（从 `config.json` 的 `universe`）
- 生成 `potential_buys` 列表（评分 >= 3.0，推荐 BUY）
- 生成 `stock_rankings`（所有股票按评分排序）
- 输出 `selection_summary`（统计数据）

**集成位置**: Trading Cycle → Market Data → Stock Selection Agent → Discussion Agent

**输出**:
```python
{
    "recommended_stocks": ["NVDA", "MSFT", ...],
    "stock_rankings": [
        {"symbol": "NVDA", "score": 5.0, "trend": "uptrend", ...},
        ...
    ],
    "potential_buys": [
        {"symbol": "NVDA", "score": 5.0, "recommendation": "BUY", ...},
        ...
    ],
    "selection_summary": {
        "total_evaluated": 100,
        "buy_candidates": 15,
        "hold_candidates": 60,
        "sell_candidates": 5,
        "top_score": 5.0,
        "avg_score": 2.5,
    },
}
```

#### 2. **Discussion Agent Enhancement** ✅

**文件**: `backend/src/agents/analyst_discussion.py`

**增强**:
- 添加 `potential_buys` 参数
- 将 `potential_buys` 格式化为可读文本
- 包含在讨论上下文中
- 更新 prompt 指导讨论股票选择

**集成位置**: Stock Selection Agent → Discussion Agent (with potential_buys)

#### 3. **Trading Cycle Integration** ✅

**文件**: `backend/src/orchestrator/trading_cycle.py`

**集成**:
- 在 Market Data 之后调用 Stock Selection Agent
- 将 `potential_buys` 传递给 Discussion Agent
- 在返回数据中包含 `stock_selection` 结果

**流程**:
```
Market Data → Stock Selection Agent → enriched_market (with potential_buys) → Discussion Agent
```

---

## 🎯 待添加的组件（中优先级）

### 🟡 Phase 2: Event Bus Integration

#### 4. **Event Bus Integration** 🟡

**文件**: `backend/src/core/event_bus.py` (已存在)

**需要**:
- 在所有 agent 调用中集成 Event Bus
- 记录所有决策过程
- 支持实时监控和调试

**集成位置**:
- Market Agent
- Market Analyst
- Stock Selection Agent
- Discussion Agent
- Risk Analyst
- Trader Agent

---

### 🟡 Phase 3: Performance Agent + Feedback Loop

#### 5. **Performance Agent** 🟡

**文件**: `backend/src/agents/performance_agent.py` (待创建)

**功能**:
- 分析历史交易记录
- 计算绩效指标（收益率、夏普比率、最大回撤等）
- 评估持仓表现
- 提供绩效改进建议

**集成位置**: Execution → Performance Agent → Feedback Loop

#### 6. **Feedback Loop** 🟡

**文件**: `backend/src/orchestrator/trading_cycle.py` (待修改)

**功能**:
- 将 Performance Agent 的输出反馈给 Trader Agent
- 将交易执行结果反馈给 Discussion Agent
- 形成闭环学习

**集成位置**: Performance Agent → Feedback → Next Round

---

## 📊 信息流组件总结

### 当前组件（已实现）

| 组件 | 状态 | 优先级 | 功能 |
|------|------|--------|------|
| Market Data Collection | ✅ | 必需 | 获取市场数据 |
| Stock Selection Agent | ✅ | 🔴 高 | 评估所有候选股票，生成 potential_buys |
| Market Analyst | ✅ | 必需 | 分析市场情绪 |
| Discussion Agent (Enhanced) | ✅ | 🔴 高 | 讨论股票选择和市场趋势 |
| Risk Analyst | ✅ | 必需 | 评估风险 |
| Trader Agent | ✅ | 必需 | 交易决策 |
| Portfolio | ✅ | 必需 | 持仓管理 |
| Trade Logger | ✅ | 必需 | 交易记录 |

### 待添加组件

| 组件 | 状态 | 优先级 | 功能 |
|------|------|--------|------|
| Event Bus Integration | ⏳ | 🟡 中 | 事件追踪 |
| Performance Agent | ⏳ | 🟡 中 | 绩效分析 |
| Feedback Loop | ⏳ | 🟡 中 | 闭环学习 |

---

## 🔄 数据流详情

### Stock Selection → Discussion → Trader 数据流

```
1. Stock Selection Agent
   输入: market_data, universe, last_prices, vix_risk
   输出: potential_buys, stock_rankings
   ↓
2. Discussion Agent
   输入: enriched_market, potential_buys
   处理: 讨论 potential_buys 中的股票选择
   输出: consensus (包含 stock_discussion)
   ↓
3. Trader Agent
   输入: market, mview (包含 potential_buys), rview, convo (包含 stock_discussion)
   处理: 使用讨论过的 potential_buys 做最终决策
   输出: buy_orders, sell_orders, position_adjustments
```

### potential_buys 在讨论中的使用

**在 Discussion Agent 中**:
- `potential_buys` 被格式化为可读文本
- 包含在 prompt 变量 `{potential_buys}` 中
- Agents 可以讨论这些股票的选择
- 输出 `consensus` 可能包含 `stock_discussion`

**在 Trader Agent 中**:
- Trader Agent 可以访问讨论过的 `potential_buys`
- 优先考虑在 Discussion 中讨论过的股票
- 最终决策会考虑讨论结果

---

## 🎯 下一步工作

### Phase 2: Event Bus Integration (中优先级)

1. 在所有 agent 调用中添加 Event Bus 记录
2. 记录所有决策过程
3. 支持实时监控

### Phase 3: Performance Agent + Feedback Loop (中优先级)

1. 创建 Performance Agent
2. 分析历史表现
3. 实现 Feedback Loop

---

**更新日期**: 2025-11-02

