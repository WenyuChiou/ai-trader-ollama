# ✅ 信息流组件清单

## 📋 当前信息流组件

### ✅ 已实现的组件

#### 1. **Market Data Collection** ✅
- **组件**: `fetch_market_batch`
- **功能**: 获取市场数据（OHLCV + 指标）
- **位置**: `backend/src/tools/market_tools.py`

#### 2. **Stock Selection Agent** ✅ NEW
- **组件**: `run_stock_selection_agent`
- **功能**: 评估所有候选股票，生成 potential_buys
- **位置**: `backend/src/agents/stock_selection_agent.py`
- **输出**: `potential_buys`, `stock_rankings`, `selection_summary`

#### 3. **Market Analyst** ✅
- **组件**: `run_market_analyst`
- **功能**: 分析市场情绪和趋势
- **位置**: `backend/src/tools/market_analyst.py`
- **输出**: `market_sentiment`, `recommended_stocks`

#### 4. **Discussion Agent (Enhanced)** ✅ NEW
- **组件**: `run_analyst_discussion`
- **功能**: 讨论市场趋势和**股票选择**（NEW）
- **位置**: `backend/src/agents/analyst_discussion.py`
- **增强**: 接受 `potential_buys` 参数，在讨论中包含股票选择
- **输出**: `consensus`, `final_stance`, `stock_discussion`

#### 5. **Risk Analyst** ✅
- **组件**: `run_risk_analyst`
- **功能**: 评估当前仓位风险
- **位置**: `backend/src/agents/risk_analyst.py`
- **输出**: `risk_report`, `position_control_report`

#### 6. **Trader Agent** ✅
- **组件**: `run_trader`
- **功能**: 交易决策（买入、卖出、持仓调整）
- **位置**: `backend/src/agents/trader_agent.py`
- **输出**: `buy_orders`, `sell_orders`, `potential_buys`, `position_adjustments`

#### 7. **Portfolio** ✅
- **组件**: `Portfolio`
- **功能**: 持仓管理和 P&L 计算
- **位置**: `backend/src/data/portfolio.py`
- **功能**: 成本价格记录、盈亏计算、持仓占比

#### 8. **Trade Logger** ✅
- **组件**: `TradeLogger`
- **功能**: 交易记录和统计
- **位置**: `backend/src/data/trade_log.py`
- **功能**: 记录交易、查询交易历史、统计计算

---

## 🔄 当前信息流

### 完整流程

```
Input: config.json (universe, date_range, ...)
   ↓
1. Market Data Collection
   fetch_market_batch(universe)
   → market_data: {stocks, VIX, indicators}
   ↓
2. Stock Selection Agent (NEW) ✅
   run_stock_selection_agent(market_data, universe)
   → potential_buys: [{symbol, score, trend, recommendation, ...}]
   → stock_rankings: [sorted by score]
   ↓
3. Enriched Market View
   enriched_market = {
       ...market_data,
       potential_buys: potential_buys,  # NEW
       stock_rankings: stock_rankings,   # NEW
   }
   ↓
4. Discussion Agent (ENHANCED) ✅
   run_analyst_discussion(enriched_market, potential_buys)
   → 讨论股票选择（potential_buys）  # NEW
   → consensus: {final_stance, stock_discussion, risk_signals}
   ↓
5. Risk Analyst
   run_risk_analyst(market_data, positions, discussion_risk_signals)
   → risk_report: {risk_level, position_control_report}
   ↓
6. Trader Agent
   run_trader(market, mview, rview, convo, all_candidates)
   → decision: {
       buy_orders, sell_orders,
       potential_buys,  # 已包含在 convo 中讨论过的
       position_adjustments,
   }
   ↓
7. Execution
   execute_trades(decision)
   → portfolio.update()
   → trade_logger.log()
   ↓
8. Return Results
   → stock_selection,  # NEW
   → decision,
   → risk_report,
   → portfolio (P&L, positions),
   → executed_trades,
```

---

## 🎯 待添加的组件（中优先级）

### 🟡 Phase 2: Event Bus Integration

#### 9. **Event Bus Integration** 🟡

**状态**: ⏳ 待实现

**文件**: `backend/src/core/event_bus.py` (已存在)

**需要**:
- 在所有 agent 调用中集成 Event Bus
- 记录所有决策过程
- 支持实时监控和调试

**集成位置**:
- Market Agent
- Stock Selection Agent
- Discussion Agent
- Risk Analyst
- Trader Agent
- Execution

**功能**:
- 记录 agent 开始/结束时间
- 记录工具调用
- 记录决策结果
- 支持实时监控（WebSocket）

---

### 🟡 Phase 3: Performance Agent + Feedback Loop

#### 10. **Performance Agent** 🟡

**状态**: ⏳ 待创建

**文件**: `backend/src/agents/performance_agent.py` (待创建)

**功能**:
- 分析历史交易记录
- 计算绩效指标：
  - 总收益率
  - 年化收益率
  - 夏普比率
  - 最大回撤
  - 胜率（盈利交易占比）
  - 平均盈亏比
- 评估持仓表现
- 提供绩效改进建议

**集成位置**: Execution → Performance Agent → Feedback

**输出**:
```python
{
    "performance_metrics": {
        "total_return": 15.5,
        "annualized_return": 12.3,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.5,
        "win_rate": 0.65,
        "avg_profit_loss_ratio": 1.5,
    },
    "position_performance": {
        "NVDA": {"return": 20.0, "days_held": 30, ...},
        ...
    },
    "improvement_suggestions": [
        "Consider reducing position in high-risk stocks",
        "Diversify portfolio to reduce concentration risk",
        ...
    ],
}
```

#### 11. **Feedback Loop** 🟡

**状态**: ⏳ 待实现

**文件**: `backend/src/orchestrator/trading_cycle.py` (待修改)

**功能**:
- 将 Performance Agent 的输出反馈给 Trader Agent
- 将交易执行结果反馈给 Discussion Agent
- 形成闭环学习

**集成位置**: Performance Agent → Feedback → Next Round

**反馈内容**:
- 绩效指标（影响 Trader Agent 的决策）
- 交易执行结果（影响 Discussion Agent 的讨论）
- 改进建议（影响下一轮决策）

---

## 📊 信息流组件状态总结

### ✅ 已实现（必需 + 高优先级）

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

### ⏳ 待实现（中优先级）

| 组件 | 状态 | 优先级 | 功能 |
|------|------|--------|------|
| Event Bus Integration | ⏳ | 🟡 中 | 事件追踪 |
| Performance Agent | ⏳ | 🟡 中 | 绩效分析 |
| Feedback Loop | ⏳ | 🟡 中 | 闭环学习 |

---

## 🔄 当前信息流完整性

### ✅ 核心流程（100% 完成）

1. ✅ Market Data Collection
2. ✅ Stock Selection Agent
3. ✅ Discussion Agent (with potential_buys)
4. ✅ Risk Analyst
5. ✅ Trader Agent
6. ✅ Execution
7. ✅ Portfolio Management
8. ✅ Trade Logging

### ⏳ 增强功能（待实现）

9. ⏳ Event Bus Integration
10. ⏳ Performance Agent
11. ⏳ Feedback Loop

---

## 📝 下一步工作

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

