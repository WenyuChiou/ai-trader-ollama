# 🎯 Agent 工作环节优化计划

## 📋 优化目标

专注于完善 Agent 工作环节，确保：
1. **Agent 之间数据流清晰**
2. **每个 Agent 发挥应有作用**
3. **输出结构化且可复用**
4. **决策逻辑更智能**

## 🔍 当前问题分析

### 问题 1: Market Agent & Market Analyst 未使用

**现状**:
- `trading_cycle.py` 直接调用 `fetch_market_batch`，跳过 Market Agent
- Market Agent 和 Market Analyst 存在但未被使用

**影响**:
- Agent 系统不完整
- 缺少 LLM 对市场数据的分析

**解决方案**:
- **方案 A**: 在 `trading_cycle.py` 中调用 Market Agent 和 Market Analyst
- **方案 B**: 让它们输出结构化 JSON，便于后续使用
- **方案 C**: 整合它们的功能到 Discussion Agent

**推荐**: 方案 A + B（使用并结构化）

### 问题 2: Risk Analyst 未集成

**现状**:
- `trading_cycle.py` 中 `rview=None`
- Risk Analyst 未调用
- Trader Agent 未考虑风险分析

**影响**:
- 缺少风险评估
- 交易决策不考虑风险

**解决方案**:
- 在 `trading_cycle.py` 中调用 `run_risk_analyst`
- 将风险分析结果传递给 Discussion Agent 和 Trader Agent

**优先级**: 🔴 高

### 问题 3: Trader Agent 逻辑简单

**现状**:
- 仅检查 VIX 风险和 stance
- 未使用 LLM 推理
- 未考虑 Risk Analyst 输出

**影响**:
- 交易决策过于简单
- 未充分利用可用信息

**解决方案**:
- **方案 A**: 增强规则逻辑（考虑更多因素）
- **方案 B**: 转换为 LLM-based Trader Agent
- **方案 C**: 结合规则 + LLM

**推荐**: 方案 C（结合规则和 LLM）

## 📝 优化任务列表

### Phase A: 数据流修复（高优先级）

#### Task A1: Risk Analyst 集成
**文件**: `backend/src/orchestrator/trading_cycle.py`
**任务**:
1. 调用 `run_risk_analyst(market_view)`
2. 将 `risk_view` 传递给 Discussion Agent
3. 将 `risk_view` 传递给 Trader Agent

**预期结果**:
```python
risk_view = run_risk_analyst(market_view)
convo = run_analyst_discussion(enriched_market, risk_view=risk_view, ...)
decision = run_trader(..., rview=risk_view, ...)
```

#### Task A2: Market Agent & Market Analyst 集成
**文件**: `backend/src/orchestrator/trading_cycle.py`
**任务**:
1. 决定是否使用 Market Agent（或直接使用 fetch_market_batch）
2. 调用 Market Analyst 分析市场数据
3. 将分析结果整合到 enriched_market

**预期结果**:
```python
# 选项 1: 使用 Market Agent
market_raw = run_market_agent(symbols, start, end)
market_analysis = run_market_analyst(market_raw)

# 选项 2: 直接使用 fetch_market_batch（当前方式）
market_view = fetch_market_batch(...)
market_analysis = run_market_analyst(market_view)
```

### Phase B: 输出结构化（中优先级）

#### Task B1: Market Agent 结构化输出
**文件**: `backend/src/agents/market_agent.py`, `backend/prompts/market_agent.yml`
**任务**:
1. 修改 prompt 要求 JSON 输出
2. 修改 `run_market_agent` 使用 `expect_json=True`
3. 定义输出 schema

**预期输出**:
```json
{
  "market_summary": "...",
  "key_observations": [...],
  "recommendations": [...]
}
```

#### Task B2: Market Analyst 结构化输出
**文件**: `backend/src/agents/market_analyst.py`, `backend/prompts/market_analyst.yml`
**任务**:
1. 修改 prompt 要求 JSON 输出
2. 修改 `run_market_analyst` 使用 `expect_json=True`
3. 定义输出 schema

**预期输出**:
```json
{
  "market_sentiment": "cautious|neutral|constructive",
  "recommended_stocks": [...],
  "key_observations": [...],
  "signals": [...]
}
```

### Phase C: Trader Agent 增强（中优先级）

#### Task C1: Trader Agent 逻辑增强
**文件**: `backend/src/agents/trader_agent.py`
**任务**:
1. 考虑 Risk Analyst 输出
2. 考虑更多市场信号
3. 改进决策逻辑

#### Task C2: Trader Agent LLM 化（可选）
**文件**: `backend/src/agents/trader_agent.py`, `backend/prompts/trader_agent.yml`
**任务**:
1. 创建 Trader Agent prompt
2. 使用 LLM 进行交易决策
3. 保持规则逻辑作为后备

### Phase D: Discussion Agent 优化（低优先级）

#### Task D1: 反馈循环优化
**文件**: `backend/src/agents/analyst_discussion.py`
**任务**:
1. 改进工具结果摘要
2. 优化 prompt 中的工具上下文
3. 改进早退逻辑

## 🎯 实施顺序

### 第一步: Risk Analyst 集成（最重要）
1. ✅ 分析当前 Risk Analyst 实现
2. ⏳ 在 `trading_cycle.py` 中调用
3. ⏳ 传递风险分析结果
4. ⏳ 测试验证

### 第二步: Market Agent & Analyst 明确角色
1. ⏳ 决定是否使用它们
2. ⏳ 如果使用，结构化输出
3. ⏳ 如果不使用，明确文档说明

### 第三步: Trader Agent 增强
1. ⏳ 考虑 Risk Analyst 输出
2. ⏳ 增强决策逻辑
3. ⏳ 测试验证

### 第四步: Discussion Agent 优化
1. ⏳ 优化反馈循环
2. ⏳ 改进工具调用
3. ⏳ 测试验证

## 📊 成功标准

每个优化完成时：
- ✅ 功能正常工作
- ✅ 测试通过
- ✅ 文档更新
- ✅ 代码审查通过

## 🔄 与 Phase 3 的关系

- **当前**: 专注于 Agent 工作环节优化
- **Phase 3**: 事件系统集成（可并行或后续进行）
- **建议**: 完成 Agent 优化后，再集成事件系统

---

**当前状态**: 优化计划已制定，等待实施  
**优先级**: Agent 工作环节 > Phase 3 事件系统

