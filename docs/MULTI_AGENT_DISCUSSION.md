# 🤖 真正的多 Agent 讨论系统

## 📋 概述

实现了真正的多 Agent 讨论系统，多个独立的 Analyst Agents 进行多轮讨论，最终形成共识。

---

## 🔄 系统架构

### Agents 列表

1. **Technical Analyst（技术分析师）**
   - 专长：技术分析、图表模式、指标、价格行为
   - 工具：vix_term, vix_close, news_scan, fetch_url
   - 关注：RSI, MACD, Bollinger Bands, 趋势分析, 支撑/阻力

2. **Fundamental Analyst（基本面分析师）**
   - 专长：公司基本面、盈利、财务状况、行业趋势
   - 工具：news_scan, plan_and_scan_news, fetch_url, web_search
   - 关注：盈利分析、P/E 比率、收入增长、竞争定位

3. **Risk Analyst (Discussion)（风险分析师 - 讨论版本）**
   - 专长：风险评估、仓位大小、组合风险、市场风险
   - 工具：vix_term, vix_close, fear_greed, news_scan
   - 关注：风险评分、仓位限制、分散化、波动率分析

4. **Sentiment Analyst（情绪分析师）**
   - 专长：市场情绪、投资者心理、新闻情绪、社交情绪
   - 工具：news_scan, plan_and_scan_news, fear_greed, fetch_url
   - 关注：情绪分析、新闻解读、市场情绪、反向信号

---

## 🔄 工作流程

### 1. 每个 Agent 独立分析

每轮讨论中，每个 Agent 独立分析：
- 查看市场数据
- 查看潜在购买股票列表
- 查看之前的讨论记录
- 查看工具结果上下文

### 2. 每个 Agent 可以使用自己的工具

每个 Agent 可以：
- 决定是否需要调用工具
- 选择使用哪个工具
- 传递工具参数
- 获取工具结果

### 3. Agents 进行多轮讨论

每轮讨论：
1. 每个 Agent 独立分析
2. 每个 Agent 可以使用工具获取信息
3. 每个 Agent 输出观点和推荐
4. 所有 Agents 可以看到彼此的讨论

### 4. 最终形成共识

基于所有 Agents 的观点：
- 收集所有观点
- 收集所有信号
- 收集所有推荐
- 形成最终共识

---

## 📊 共识形成机制

### 观点聚合

收集所有 Agents 的观点：
- Technical Analyst: bullish/neutral/bearish
- Fundamental Analyst: bullish/neutral/bearish
- Risk Analyst: cautious/neutral/constructive
- Sentiment Analyst: bullish/neutral/bearish

### 最终立场决定

使用多数决定或优先级机制：
- 优先级：cautious > bearish > neutral > constructive > bullish
- 标准化为：cautious / neutral / constructive

### 共识输出

```json
{
  "final_stance": "cautious" | "neutral" | "constructive",
  "rationale": [...],
  "signals_used": [...],
  "recommendations": [...],
  "agent_viewpoints": {
    "technical": "...",
    "fundamental": "...",
    "risk": "...",
    "sentiment": "..."
  }
}
```

---

## 🔧 配置和使用

### 在 `trading_cycle.py` 中使用

```python
# 使用多 Agent 讨论系统
convo = run_multi_agent_discussion(
    market_view=enriched_market,
    potential_buys=potential_buys,
    current_positions=current_positions_info,
    portfolio_value=portfolio_value,
    rounds=3,  # 讨论轮数
    auto_tools=True,  # 是否自动执行工具
    tool_budget_per_agent=2,  # 每个 Agent 的工具预算
    preferred_domains=preferred_domains,
)

# 获取共识
consensus = convo.get("consensus", {})
final_stance = consensus.get("final_stance", "neutral")
```

### 切换使用

在 `execute_daily_trade` 中：

```python
result = execute_daily_trade(
    # ... 其他参数 ...
    use_multi_agent=True,  # 使用多 Agent 讨论系统（默认 True）
)
```

---

## 🎯 优势

1. **真正的多 Agent 讨论**
   - 多个独立的 Agents 一起讨论
   - 每个 Agent 有自己的观点和工具
   - 可以模拟不同分析师之间的讨论

2. **工具使用灵活性**
   - 每个 Agent 可以使用自己的工具
   - 避免工具调用重复（全局工具上下文）
   - 支持动态工具参数调整

3. **共识形成机制**
   - 基于多个 Agents 的观点
   - 使用多数决定或优先级机制
   - 提供详细的共识信息

4. **向后兼容**
   - 保留了旧的单 Agent 讨论系统
   - 可以通过参数切换使用

---

## 📝 文件结构

```
backend/
├── prompts/
│   ├── technical_analyst.yml          # Technical Analyst prompt
│   ├── fundamental_analyst.yml        # Fundamental Analyst prompt
│   ├── risk_analyst_discussion.yml    # Risk Analyst (Discussion) prompt
│   └── sentiment_analyst.yml          # Sentiment Analyst prompt
├── src/
│   └── agents/
│       └── multi_agent_discussion.py  # 多 Agent 讨论系统实现
└── config/
    └── agents.yaml                    # Agents 配置（包含新的 Agents）
```

---

## 🔄 与旧系统的对比

### 旧系统（单 Agent 讨论）

- 只有 1 个 Discussion Agent
- Agent 综合多个输入源的信息
- 通过多轮迭代形成共识
- 不是真正的多 Agent 讨论

### 新系统（多 Agent 讨论）

- 4 个独立的 Analyst Agents
- 每个 Agent 有自己的观点和工具
- Agents 进行多轮讨论
- 真正的多 Agent 讨论

---

## 🚀 下一步

1. **测试多 Agent 讨论系统**
   - 验证每个 Agent 是否正常工作
   - 验证工具调用是否正确
   - 验证共识形成是否正确

2. **优化共识形成机制**
   - 调整优先级规则
   - 添加加权平均机制
   - 支持更复杂的共识算法

3. **增强 Agent 交互**
   - 添加 Agent 之间的提问机制
   - 支持 Agent 之间的辩论
   - 添加 Agent 之间的投票机制

---

**更新日期**: 2025-11-02

