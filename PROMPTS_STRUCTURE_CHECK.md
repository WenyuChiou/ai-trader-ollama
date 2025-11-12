# Prompts 结构和功能检查报告

## ✅ 已检查的功能

### 1. **Analysis 字段（100-150 字要求）**
- ✅ **market_analyst.yml**: 包含 "approximately 100-150 words" 要求
- ✅ **technical_analyst.yml**: 包含 "approximately 100-150 words" 要求
- ✅ **fundamental_analyst.yml**: 包含 "approximately 100-150 words" 要求
- ✅ **sentiment_analyst.yml**: 包含 "approximately 100-150 words" 要求
- ✅ **risk_analyst.yml**: 包含 "approximately 100-150 words" 要求

### 2. **新闻分析要求（MANDATORY）**
- ✅ **所有 analyst prompts**: 都包含 "MANDATORY: If you used news_scan or other news tools, you MUST explicitly mention and analyze news content"
- ✅ 包含详细的新闻分析格式要求（Title, 50-100 word summary, Impact assessment）

### 3. **工具调用要求（至少 2 个）**
- ✅ **所有 analyst prompts**: 都包含 "MANDATORY: Your tool_calls array MUST contain at least 2 tool calls"
- ✅ 包含 "CRITICAL: You MUST call at least 2-3 tools" 的说明

### 4. **当前仓位信息（CRITICAL）**
- ✅ **所有 analyst prompts**: 都包含 "⚠️ CRITICAL: Current Positions and Available Cash Information" 部分
- ✅ 详细说明仓位信息的字段（quantity, avg_cost, current_price, market_value, unrealized_pnl, position_pct）
- ✅ 包含使用这些信息的指导原则

### 5. **可用现金信息**
- ✅ **所有 analyst prompts**: 都包含 "Available Cash (after reserve)" 说明
- ✅ 包含 "CRITICAL: Respect available cash limits" 的要求

### 6. **Recommendations 字段**
- ✅ **所有 analyst prompts**: 输出格式中都包含 `"recommendations": ["<action 1>", "<action 2>"]`

### 7. **Stance 字段**
- ✅ **所有 analyst prompts**: 输出格式中都包含 `"stance": "bullish" | "bearish" | "neutral"`

### 8. **反向 ETF 信息**
- ✅ **所有 analyst prompts**: 都包含 "Available Inverse ETFs" 部分
- ✅ 列出所有可用的反向 ETF（SQQQ, SPXU, SH, PSQ, SDS, DOG, SOXS）

### 9. **杠杆 ETF 信息**
- ✅ **所有 analyst prompts**: 都包含 "Available Leveraged ETFs" 部分
- ✅ 列出所有可用的杠杆 ETF（TQQQ, SPXL, UPRO）

## 📄 特定 Prompt 检查

### trader_agent.yml
- ✅ **Position Size Guidelines**: 包含完整的仓位大小指导原则部分
- ✅ **Max position per stock**: 包含 `{max_position_per_stock}` 变量
- ✅ **Max total position**: 包含 `{max_total_position}` 变量
- ✅ **Min position per stock**: 包含 `{min_position_per_stock}` 变量
- ✅ **Available cash**: 包含 `${available_cash:,.2f}` 变量
- ✅ **Portfolio value**: 包含 `${portfolio_value:,.2f}` 变量
- ✅ **Decision Authority**: 说明 agent 可以根据信号强度等因素灵活调整仓位
- ✅ **Position Size Calculation Examples**: 包含具体的仓位计算示例

### discussion_agent.yml
- ⚠️ **格式不同**: 使用不同的输出格式（rationale, signals_used, actions, to_agent_notes）
- ✅ **Stance 字段**: 包含 stance 字段
- ⚠️ **Summary 字段**: 没有明确的 summary 字段（但有 rationale）
- ⚠️ **Recommended stocks**: 没有明确的 recommended_stocks 字段

## ⚠️ 发现的问题

### 1. **discussion_agent.yml 格式不一致**
- 其他 analyst prompts 使用统一的格式（stance, analysis, tool_calls, recommendations）
- discussion_agent.yml 使用不同的格式（rationale, signals_used, actions, to_agent_notes）
- **建议**: 统一格式，或确认这是设计意图

### 2. **discussion_agent.yml 缺少 summary 字段**
- 代码中可能期望有 summary 字段
- **建议**: 检查代码是否真的需要 summary 字段，或者 rationale 是否足够

## ✅ 总体评估

### 优点
1. ✅ **所有 analyst prompts 都包含最新的功能要求**：
   - 100-150 字的分析要求
   - 新闻分析强制要求
   - 工具调用强制要求（至少 2 个）
   - 当前仓位和可用现金信息
   - 反向和杠杆 ETF 信息

2. ✅ **trader_agent.yml 包含完整的仓位限制指导**：
   - 仓位大小指导原则
   - 决策权限说明
   - 具体的计算示例

3. ✅ **所有 prompts 都包含详细的工具说明**：
   - 优先级工具列表
   - 工具使用指导

### 需要确认
1. ⚠️ **discussion_agent.yml 的格式**：是否应该与其他 analyst prompts 统一？
2. ⚠️ **discussion_agent.yml 的字段**：是否需要添加 summary 字段？

## 📝 建议

1. **保持当前结构**：所有 analyst prompts 的结构和功能要求都是最新的
2. **检查 discussion_agent.yml**：确认其格式差异是否是设计意图
3. **验证代码兼容性**：确保代码能够正确处理所有 prompt 的响应格式

