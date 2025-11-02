# 📋 Agent 清单

## 🎯 当前系统中的所有 Agent

### ✅ 核心 Agent（已实现并在使用）

#### 1. **Market Agent** - 市场数据抓取
**文件**: `backend/src/agents/market_agent.py`  
**配置**: `backend/config/agents.yaml` → `market_agent`  
**Prompt**: `backend/prompts/market_agent.yml`

**职责**: 负责抓取当日股票数据

**输入**:
- `symbols`: 股票代码列表
- `start`: 开始日期
- `end`: 结束日期

**输出**:
- `raw`: 原始输出文本
- `inputs`: 输入参数记录

**状态**: ✅ 已实现（但目前在 trading_cycle 中直接使用 `fetch_market_batch`）

---

#### 2. **Market Analyst** - 市场分析
**文件**: `backend/src/agents/market_analyst.py`  
**配置**: `backend/config/agents.yaml` → `market_analyst`  
**Prompt**: `backend/prompts/market_analyst.yml`

**职责**: 负责分析市场数据，评估市场情绪

**输入**:
- `market_view`: 市场数据（来自 Market Agent 或 fetch_market_batch）

**输出**:
- `raw`: 原始分析文本
- `inputs`: 输入参数记录

**功能**:
- 分析技术面指标
- 评估市场情绪
- 推荐股票

**状态**: ✅ 已实现（但目前在 trading_cycle 中直接使用 `tools/market_analyst.py`）

---

#### 3. **Stock Selection Agent** - 股票筛选 🔴 NEW
**文件**: `backend/src/agents/stock_selection_agent.py`  
**配置**: ❌ 未在 agents.yaml 中配置（纯函数实现）  
**Prompt**: ❌ 无（使用规则逻辑）

**职责**: 评估所有候选股票，生成潜在购买公司列表

**输入**:
- `market_data`: 市场数据（包含 stocks）
- `universe`: 所有候选股票列表（来自 config.json）
- `last_prices`: 最新价格
- `vix_risk`: VIX 风险评分
- `min_score`: 最小评分阈值（默认 3.0）
- `top_n`: 返回前 N 名（默认 20）

**输出**:
- `recommended_stocks`: 推荐的股票列表（带评分）
- `stock_rankings`: 所有候选股票的排名（按评分降序）
- `potential_buys`: 潜在购买公司列表（评分 >= min_score，推荐 BUY）
- `selection_summary`: 选择摘要（统计信息）

**功能**:
- 评估所有候选股票（从 config.json 的 universe）
- 基于 signal_score、trend、risk_score 计算综合评分
- 生成 potential_buys 列表供 Discussion Agent 讨论

**状态**: ✅ 已实现并集成到 trading_cycle

---

#### 4. **Discussion Agent** - 分析师讨论 ✅ ENHANCED
**文件**: `backend/src/agents/analyst_discussion.py`  
**配置**: `backend/config/agents.yaml` → `discussion_agent`  
**Prompt**: `backend/prompts/discussion_agent.yml`

**职责**: 负责多轮讨论，形成共识，**讨论股票选择**（NEW）

**输入**:
- `market_view`: enriched market view
- `potential_buys`: 潜在购买公司列表（NEW）
- `rounds`: 讨论轮数（默认 3）
- `auto_tools`: 是否自动使用工具（默认 True）
- `tool_budget`: 工具调用预算（默认 3）
- `preferred_domains`: 优先域名列表

**输出**:
- `final_stance`: 最终市场立场（cautious/neutral/constructive）
- `rationale`: 理由列表
- `signals_used`: 使用的信号列表
- `transcript`: 讨论记录
- `actions`: 行动列表
- `rounds`: 实际讨论轮数
- `stock_discussion`: 股票选择讨论摘要（NEW）

**功能**:
- 通过多轮讨论，整合市场分析
- **讨论股票选择**（potential_buys）（NEW）
- 自动使用工具补充信息（news_scan, vix_term, etc.）
- 形成最终共识

**工具支持**:
- `news_scan`: 新闻扫描
- `vix_term`: VIX 期限结构
- `vix_close`: VIX 收盘价
- `fear_greed`: 恐慌贪婪指数
- `plan_and_scan_news`: 计划并扫描新闻
- `fetch_url`: 获取 URL 内容

**状态**: ✅ 已实现并增强（已集成 potential_buys 讨论）

---

#### 5. **Risk Analyst** - 风险评估 ✅ ENHANCED
**文件**: `backend/src/agents/risk_analyst.py`  
**配置**: `backend/config/agents.yaml` → `risk_analyst`  
**Prompt**: `backend/prompts/risk_analyst.yml`

**职责**: 评估当前仓位风险，提出仓位控管报告

**输入**:
- `market_json`: 市场数据（包含 stocks）
- `current_positions`: 当前持仓 {symbol: {quantity, avg_cost, ...}}（NEW）
- `portfolio_value`: 当前组合净值（NEW）
- `discussion_risk_signals`: 来自 Analyst Discussion 的风险信号（NEW）

**输出**:
- `overall_risk_level`: 整体风险等级（high/medium/low）
- `risk_score`: 风险评分
- `max_position_size`: 最大仓位限制
- `risk_warnings`: 风险警告列表
- `safe_stocks`: 安全股票列表
- `high_risk_stocks`: 高风险股票列表
- `diversification_advice`: 分散化建议
- `current_position_risk`: 当前仓位风险评估（NEW）
  - `position_concentration`: 仓位集中度（HHI）
  - `single_stock_exposure`: 单股暴露度
  - `overall_exposure`: 总仓位暴露度
  - `recommended_adjustments`: 推荐调整
- `position_control_report`: 仓位控管报告（NEW）
  - `recommended_position_sizes`: 推荐仓位大小
  - `position_limit_checks`: 仓位限制检查
  - `rebalancing_suggestions`: 再平衡建议

**功能**:
- 评估市场风险（基于技术指标）
- **评估当前仓位风险**（NEW）
- 计算仓位集中度（HHI）
- 检查单股暴露度
- 生成仓位控管报告

**状态**: ✅ 已实现并增强（已集成仓位风险评估）

---

#### 6. **Trader Agent** - 交易决策 ✅ ENHANCED
**文件**: `backend/src/agents/trader_agent.py`  
**配置**: `backend/config/agents.yaml` → `trader_agent`  
**Prompt**: `backend/prompts/trader_agent.yml`

**职责**: 决定是否买卖（包含买卖那些公司、部位、买进价格、卖出价格等）

**输入**:
- `market`: 市场数据
- `mview`: enriched market view
- `rview`: risk view（来自 Risk Analyst，包含仓位控管报告）
- `convo`: discussion consensus（来自 Analyst Discussion）
- `last_prices`: 最新价格
- `current_positions`: 当前持仓（可选）（NEW）
- `portfolio_value`: 当前组合净值（可选）（NEW）
- `all_candidates`: 所有候选股票列表（可选，如果提供则评估所有候选股票）（NEW）

**输出**:
- `action`: BUY / SELL / HOLD
- `buy_orders`: 买进订单列表（NEW）
  - `symbol`: 股票代码
  - `buy_price`: 买进价格
  - `quantity`: 买进数量
  - `total_cost`: 总成本
  - `action`: NEW / INCREASE（NEW）
- `sell_orders`: 卖出订单列表（NEW）
  - `symbol`: 股票代码
  - `sell_price`: 卖出价格
  - `quantity`: 卖出数量
  - `total_proceeds`: 总收益
  - `sell_reason`: 卖出理由（over_limit / downtrend / stop_loss）（NEW）
- `targets`: 目标股票列表（向后兼容）
- `potential_buys`: 潜在购买公司列表（NEW）
  - 包含评估信息（score, trend, risk_score, recommendation, reasons）
- `position_adjustments`: 持仓调整建议（NEW）
  - `action`: NEW / INCREASE / HOLD / SELL
  - `quantity`: 数量
  - `reason`: 理由
- `rationale`: 决策理由
- `stance`: 市场立场
- `vix_risk`: VIX 风险评分
- `risk_compliance`: 风险合规检查

**功能**:
- **评估所有候选股票**（从 config.json 的 universe）（NEW）
- 综合所有信息做出最终交易决策
- 决定买卖哪些公司
- 决定买卖部位大小（考虑 Risk Analyst 的仓位控管建议）
- 决定买进/卖出价格
- 考虑当前持仓（避免过度集中）
- 遵守风险限制（来自 Risk Analyst）
- **支持持仓调整**（部分卖出、全部卖出、持有、增持）（NEW）

**状态**: ✅ 已实现并大幅增强

---

### ⏳ 已配置但未完全集成

#### 7. **Performance Agent** - 绩效分析
**文件**: ❌ 待创建 `backend/src/agents/performance_agent.py`  
**配置**: `backend/config/agents.yaml` → `performance_agent`  
**Prompt**: `backend/prompts/performance_agent.yml`

**职责**: 分析历史表现，评估交易策略效果

**输入**: 
- 历史交易记录（Trade Logger）
- 当前持仓（Portfolio）
- 历史市场数据

**输出**:
- `performance_metrics`: 绩效指标
  - 总收益率
  - 年化收益率
  - 夏普比率
  - 最大回撤
  - 胜率（盈利交易占比）
  - 平均盈亏比
- `position_performance`: 持仓表现分析
- `improvement_suggestions`: 改进建议

**功能**:
- 分析历史交易记录
- 计算绩效指标
- 评估持仓表现
- 提供绩效改进建议

**状态**: ⏳ 已配置但未实现（中优先级）

---

#### 8. **Sandbox Agent** - 沙盒测试
**文件**: ❌ 未创建  
**配置**: `backend/config/agents.yaml` → `sandbox_agent`  
**Prompt**: `backend/prompts/sandbox_agent.yml`

**职责**: 用于测试和实验（宽松的 prompt）

**状态**: ⏳ 已配置但未实现（低优先级）

---

## 📊 Agent 使用情况

### ✅ 正在使用的 Agent

| Agent | 状态 | 在交易周期中使用 | 优先级 |
|-------|------|----------------|--------|
| Stock Selection Agent | ✅ 已实现 | ✅ 是（NEW） | 🔴 高 |
| Discussion Agent | ✅ 已实现 | ✅ 是 | 🔴 高 |
| Risk Analyst | ✅ 已实现 | ✅ 是 | 🔴 高 |
| Trader Agent | ✅ 已实现 | ✅ 是 | 🔴 高 |

### ⏳ 已配置但未使用的 Agent

| Agent | 状态 | 在交易周期中使用 | 优先级 |
|-------|------|----------------|--------|
| Market Agent | ✅ 已实现 | ❌ 否（直接使用 fetch_market_batch） | 🟡 中 |
| Market Analyst | ✅ 已实现 | ❌ 否（直接使用 tools/market_analyst.py） | 🟡 中 |
| Performance Agent | ⏳ 待创建 | ❌ 否 | 🟡 中 |
| Sandbox Agent | ⏳ 未创建 | ❌ 否 | 🟢 低 |

---

## 🔄 Agent 在交易周期中的使用

### 当前完整流程

```
1. Market Data Collection
   fetch_market_batch(universe)  # 直接使用工具，跳过 Market Agent
   ↓
2. Stock Selection Agent ✅ NEW
   run_stock_selection_agent(market_data, universe)
   → potential_buys, stock_rankings
   ↓
3. Discussion Agent ✅
   run_analyst_discussion(enriched_market, potential_buys)
   → consensus, stock_discussion
   ↓
4. Risk Analyst ✅
   run_risk_analyst(market_data, positions, discussion_risk_signals)
   → risk_report, position_control_report
   ↓
5. Trader Agent ✅
   run_trader(market, mview, rview, convo, all_candidates)
   → buy_orders, sell_orders, position_adjustments
   ↓
6. Execution
   Portfolio + Trade Logger
   ↓
7. Performance Agent ⏳ (待实现)
   run_performance_agent(portfolio, trade_logger)
   → performance_metrics
```

---

## 📝 Agent 功能总结

### 核心功能 Agent（4 个）

1. **Stock Selection Agent** - 股票筛选（NEW）
   - 评估所有候选股票
   - 生成 potential_buys 列表
   
2. **Discussion Agent** - 分析师讨论
   - 多轮讨论形成共识
   - 讨论股票选择（NEW）
   - 自动使用工具补充信息

3. **Risk Analyst** - 风险评估
   - 评估市场风险
   - 评估当前仓位风险（NEW）
   - 生成仓位控管报告

4. **Trader Agent** - 交易决策
   - 从所有候选股票中选择（NEW）
   - 决定买入、卖出、持有
   - 支持持仓调整（部分/全部卖出、增持）（NEW）

### 辅助功能 Agent（2 个）

5. **Market Agent** - 市场数据抓取
   - 已实现但未在 trading_cycle 中使用
   - 目前直接使用 `fetch_market_batch` 工具

6. **Market Analyst** - 市场分析
   - 已实现但未在 trading_cycle 中使用
   - 目前直接使用 `tools/market_analyst.py`

### 待实现 Agent（2 个）

7. **Performance Agent** - 绩效分析
   - 已配置但未实现
   - 中优先级

8. **Sandbox Agent** - 沙盒测试
   - 已配置但未实现
   - 低优先级

---

## 🎯 建议

### 高优先级（建议实现）

1. **Performance Agent** - 用于分析交易策略效果
2. **Event Bus Integration** - 用于追踪所有决策过程

### 中优先级（可选）

3. **Market Agent 集成** - 使用 LLM 分析市场数据
4. **Market Analyst 集成** - 使用 LLM 做市场分析

### 低优先级（可选）

5. **Sandbox Agent** - 用于测试和实验

---

**更新日期**: 2025-11-02

