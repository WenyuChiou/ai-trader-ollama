# 📋 Agent 角色定义与工作流程

## 🎯 Agent 角色定义

### 前端 Agent（交易决策流程）

#### 1. **Market Agent** - 市场数据抓取
**职责**: 负责抓取当日股票数据
- 输入: symbols, start, end
- 输出: 当日股票数据（OHLCV、指标等）
- 功能: 获取市场基础数据

#### 2. **Market Analyst** - 市场分析
**职责**: 负责分析市场数据
- 输入: market_view (来自 Market Agent 或 fetch_market_batch)
- 输出: 市场分析结果（情绪、信号、推荐等）
- 功能: 分析技术面、情绪面、推荐股票

#### 3. **Analyst Discussion** - 分析师讨论
**职责**: 负责多轮讨论，形成共识
- 输入: market_view, risk_view (可选)
- 输出: 
  - `final_stance`: 最终市场立场
  - `rationale`: 理由
  - `signals_used`: 使用的信号
  - `transcript`: 讨论记录
- 功能: 通过多轮讨论，整合市场分析，形成最终共识

#### 4. **Risk Analyst** - 风险评估
**职责**: 负责评估当前仓位风险，并基于 Market Analyst 和 Analyst Discussion 的结果提出仓位控管报告
- 输入: 
  - market_json (市场数据)
  - current_positions (当前持仓 - 来自 Portfolio)
  - analyst_discussion 的风险结果 (来自 Analyst Discussion 的 risk signals)
  - portfolio_value (当前组合净值)
- 输出: 
  - `overall_risk_level`: 整体风险等级
  - `risk_score`: 风险评分
  - `max_position_size`: 最大仓位限制（单股/总仓位）
  - `risk_warnings`: 风险警告
  - `safe_stocks`: 安全股票列表
  - `high_risk_stocks`: 高风险股票列表
  - `diversification_advice`: 分散化建议
  - `current_position_risk`: 当前仓位风险评估
    - `position_concentration`: 仓位集中度
    - `single_stock_exposure`: 单股暴露度
    - `overall_exposure`: 总仓位暴露度
    - `recommended_adjustments`: 推荐调整
  - **仓位控管报告**: 基于风险结果的仓位管理建议
    - `recommended_position_sizes`: 推荐仓位大小
    - `position_limit_checks`: 仓位限制检查
    - `rebalancing_suggestions`: 再平衡建议
- 功能: 
  - 评估**当前仓位风险**（基于 Portfolio.positions）
  - 基于市场分析和讨论结果进行风险评估
  - 提出仓位控管建议（基于当前仓位状况）

#### 5. **Trader Agent** - 交易决策
**职责**: 决定是否买卖（包含买卖那些公司、部位、买进价格、卖出价格等）
- 输入: 
  - market_view (市场数据)
  - mview (enriched market view)
  - rview (risk view - 来自 Risk Analyst，包含仓位控管报告)
  - convo (discussion consensus - 来自 Analyst Discussion)
  - last_prices (最新价格)
  - current_positions (当前持仓 - 来自 Portfolio，可选)
  - portfolio_value (当前组合净值，可选)
- 输出:
  - `action`: BUY / SELL / HOLD
  - `targets`: 目标股票列表
    - `symbol`: 股票代码
    - `action`: BUY / SELL
    - `price`: 价格（买进/卖出价格）
    - `quantity`: 数量/部位
    - `value`: 交易金额 (price * quantity)
  - `buy_orders`: 买进订单列表（详细）
    - `symbol`: 股票代码
    - `buy_price`: 买进价格
    - `quantity`: 买进数量
    - `total_cost`: 总成本
  - `sell_orders`: 卖出订单列表（详细）
    - `symbol`: 股票代码
    - `sell_price`: 卖出价格
    - `quantity`: 卖出数量
    - `total_proceeds`: 总收益
  - `rationale`: 决策理由
  - `stance`: 市场立场
  - `vix_risk`: VIX 风险评分
  - `risk_compliance`: 风险合规检查
    - `position_limits_ok`: 是否遵守仓位限制
    - `diversification_ok`: 是否遵守分散化建议
- 功能: 
  - 综合所有信息做出最终交易决策
  - 决定买卖哪些公司
  - 决定买卖部位大小（考虑 Risk Analyst 的仓位控管建议）
  - 决定买进/卖出价格
  - 考虑当前持仓（避免过度集中）
  - 遵守风险限制（来自 Risk Analyst）

## 🔄 工作流程（前端）

### 完整交易决策流程

```
1. Market Agent
   ↓ (抓取当日股票数据)
   
2. Market Analyst
   ↓ (分析市场数据)
   
3. Analyst Discussion
   ↓ (多轮讨论，形成共识)
   
4. Risk Analyst
   ↓ (评估仓位风险 + 提出仓位控管报告)
   输入: market_json + analyst_discussion 的风险结果
   
5. Trader Agent
   ↓ (最终交易决策)
   输出: 
   - action: BUY/SELL/HOLD
   - targets: 买卖股票列表
   - buy_prices: 买进价格
   - sell_prices: 卖出价格
   - quantity: 部位大小
```

### 数据流

```
Market Data (fetch_market_batch)
    ↓
Market Analyst → market_analysis
    ↓
Analyst Discussion → consensus (包含风险信号)
    ↓
Portfolio (当前持仓) + market_json + consensus 风险结果
    ↓
Risk Analyst → risk_view + 仓位控管报告
    (包含当前仓位风险评估)
    ↓
Trader Agent (market_view + risk_view + consensus + current_positions)
    ↓
trading_decision (buy/sell orders with prices and quantities)
    ↓
Portfolio 更新 (buy/sell 执行)
    ↓
Trade Logger 记录交易
```

## 🔧 后端功能

### 后端职责

**根据持仓部位净值与当前市场价格，进行：**

1. **损益展示**
   - 实时计算持仓盈亏
   - 展示总盈亏、单股盈亏
   - 盈亏分布图表

2. **交易纪录展示**
   - 历史交易记录
   - 买卖时间、价格、数量
   - 交易执行状态

3. **相关展示**
   - 持仓明细
   - 仓位分布
   - 风险指标
   - 绩效统计

## 📊 完整系统架构

### 前端 → 后端数据流

```
前端 Agent 决策流程
    ↓
Trader Agent 输出交易决策
    ↓
执行交易 → 更新持仓
    ↓
后端展示系统
    ↓
- 损益展示
- 交易纪录展示
- 持仓展示
- 绩效展示
```

## 🔑 关键概念

### Risk Analyst 的关键角色

**Risk Analyst 的特殊性**:
1. 不仅评估市场风险，还评估**当前仓位风险**
2. 基于 **Market Analyst** 和 **Analyst Discussion** 的风险结果
3. 提出 **仓位控管报告**，用于：
   - 限制仓位大小
   - 风险分散建议
   - 仓位调整建议

### Trader Agent 的完整输出

**Trader Agent 需要输出**:
- 决策动作 (BUY/SELL/HOLD)
- 目标股票列表
- **买卖价格**（买进价格、卖出价格）
- **部位大小**（每个股票的仓位）
- 决策理由

### 后端展示需求

**后端需要展示**:
- 基于持仓的实时盈亏
- 交易历史记录
- 仓位状态
- 绩效指标

## 📝 当前实现状态

### ✅ 已实现

1. **Analyst Discussion** - ✅ 完整实现
   - 多轮讨论
   - 工具调用
   - 反馈循环

2. **Market Agent** - ✅ 存在但未完全集成
   - 可抓取市场数据
   - 输出未结构化
   - 文件: `backend/src/agents/market_agent.py`

3. **Market Analyst** - ✅ 存在但未完全集成
   - 可分析市场数据
   - 输出未结构化
   - 文件: `backend/src/agents/market_analyst.py`

4. **Risk Analyst** - ✅ 基本实现，需要增强
   - 风险评估逻辑完整
   - 输出仓位限制建议
   - **当前问题**: 
     - 未评估**当前仓位风险**（只评估市场风险）
     - 未集成到交易周期（rview=None）
     - 未基于 Analyst Discussion 的风险结果
   - 文件: `backend/src/agents/risk_analyst.py`

5. **Trader Agent** - ⚠️ 基本实现，需要增强
   - 逻辑较简单
   - 未考虑 Risk Analyst
   - 输出不完整（缺少买卖价格、部位大小）
   - 文件: `backend/src/agents/trader_agent.py`

6. **Portfolio 管理** - ✅ 已实现
   - 持仓管理 (buy/sell)
   - 净值计算
   - 文件: `backend/src/data/portfolio.py`

7. **交易记录** - ✅ 已实现
   - 交易日志记录
   - 文件: `backend/src/data/trade_log.py`

8. **交易工具** - ✅ 已实现
   - buy/sell/portfolio_status 工具
   - 文件: `backend/src/tools/trading_tools.py`

### ⚠️ 需要实现/优化

1. **Risk Analyst 增强** - 🔴 优先级最高
   - **评估当前仓位风险**（基于 Portfolio.positions）
   - 在交易周期中调用
   - 基于 Analyst Discussion 风险结果
   - 输出仓位控管报告（基于当前仓位）

2. **Trader Agent 增强** - 🔴 优先级最高
   - 输出买卖价格（buy_prices, sell_prices）
   - 输出部位大小（quantity/size）
   - 考虑 Risk Analyst 的仓位控管建议
   - 决定买卖哪些公司（已部分实现）
   - 考虑当前持仓（基于 Portfolio）

3. **Market Agent & Analyst 集成** - 🟡 优先级中等
   - 集成到交易周期
   - 结构化输出

4. **后端展示系统** - 🟡 优先级中等
   - 持仓损益计算（基于持仓与当前价格）
   - 交易记录展示
   - 仓位分布展示
   - 风险指标展示
   - 绩效统计展示

---

**文档状态**: ✅ 概念已记录  
**更新日期**: 2025-11-02

