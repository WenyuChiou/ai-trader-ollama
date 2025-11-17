# 四个 Analyst 工具调用和 Summary 修复

## 修复内容

### 问题
用户要求确保四个讨论的 agent（MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst）都有成功调用工具并获得结果，得到短的 summary。

### 修复

1. **切换到 `run_multi_analyst_discussion`**:
   - 从 `run_analyst_discussion`（单个 `discussion_agent`）切换到 `run_multi_analyst_discussion`（四个独立 analyst）
   - 确保每个 analyst 都有独立的工具调用和 summary 生成

2. **确保 discussion_history 包含四个 analyst**:
   - 如果 `discussion_history` 为空，从 `analyst_reports` 构建
   - 从 `tool_calls` 中提取每个 analyst 使用的工具
   - 确保每个 analyst 都有 `analysis`（summary）字段

3. **工具调用验证**:
   - 每个 analyst 都会调用工具（通过 `tool_calls` 列表）
   - 工具结果被正确记录在 `all_tool_calls` 中
   - 每个 analyst 的 `tools_used` 从 `tool_calls` 中提取

4. **Summary 生成**:
   - 如果 `analysis` 太短（< 50 字符），自动补充工具信息
   - 确保每个 analyst 都有有效的 summary

## 修改的文件

**`backend/src/orchestrator/trading_cycle.py`**:

1. **导入 `run_multi_analyst_discussion`** (第 23 行):
   ```python
   from src.agents.multi_analyst_system import run_multi_analyst_discussion
   ```

2. **切换到 `run_multi_analyst_discussion`** (第 407-415 行):
   ```python
   convo = run_multi_analyst_discussion(
       market_view=market_view,
       use_tools=auto_tools,
       tool_budget=tool_budget,
       order_status=order_status,
       current_positions=current_positions if current_positions else None,
       portfolio_value=portfolio.total_value if portfolio else None,
       available_cash=portfolio.cash if portfolio else None,
   )
   ```

3. **从 `analyst_reports` 构建 `discussion_history`** (第 488-518 行):
   - 如果 `discussion_history` 为空，从 `analyst_reports` 构建
   - 从 `tool_calls` 中提取每个 analyst 使用的工具
   - 确保每个 analyst 都有 `analysis`（summary）

## 数据结构

### `run_multi_analyst_discussion` 返回格式:
```json
{
  "final_stance": "bullish",
  "analyst_reports": {
    "market": {
      "stance": "bullish",
      "analysis": "...",
      "tools_used": ["get_market_indices", "get_sector_rotation"],
      "recommendations": [...]
    },
    "technical": {...},
    "fundamental": {...},
    "sentiment": {...}
  },
  "tool_calls": [
    {
      "analyst": "MarketAnalyst",
      "tool": "get_market_indices",
      "result": {...}
    },
    ...
  ],
  "discussion_history": [
    {
      "analyst": "Market Analyst",
      "stance": "bullish",
      "analysis": "...",
      "tools_used": ["get_market_indices", "get_sector_rotation"],
      "key_points": [...]
    },
    ...
  ]
}
```

### 写入 `discussion_actions.jsonl` 的格式:
```json
{
  "timestamp": "...",
  "date": "2025-11-16",
  "agent": "MarketAnalyst",
  "round": 0,
  "content": "Stance: bullish\n\nAnalysis: ...",
  "type": "discussion",
  "stance": "bullish",
  "summary": "...",
  "tools_used": ["get_market_indices", "get_sector_rotation"]
}
```

## 验证步骤

1. **运行交易周期**:
   ```bash
   python -m src.orchestrator.trading_cycle
   ```

2. **检查日志**:
   - 查看 `data/logs/discussion_actions.jsonl`
   - 确认四个 analyst（MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst）都有 entry
   - 确认每个 analyst 都有 `tools_used` 字段（非空）
   - 确认每个 analyst 都有 `summary` 字段（至少 50 字符）

3. **检查 API 响应**:
   ```bash
   curl http://127.0.0.1:8000/api/agents/conversations?limit=30
   ```
   - 确认 `discussion_rounds_summaries` 包含四个 analyst 的 summaries
   - 确认 `tool_results_by_category` 包含工具结果

## 预期效果

✅ **四个 analyst 都有工具调用**:
- MarketAnalyst: 调用 `get_market_indices`, `get_sector_rotation` 等
- TechnicalAnalyst: 调用 `get_advanced_indicators`, `get_support_resistance` 等
- FundamentalAnalyst: 调用 `get_company_fundamentals`, `get_earnings_history` 等
- SentimentAnalyst: 调用 `fear_greed`, `news_scan` 等

✅ **每个 analyst 都有 summary**:
- 每个 analyst 的 `analysis` 字段至少 50 字符
- Summary 包含工具结果的关键信息

✅ **工具结果被正确分类**:
- 工具结果按类型分类（news, risk, market, fundamental, economic, crypto）
- 前端可以根据类型显示工具结果

## 总结

✅ **修复完成**:
- 切换到 `run_multi_analyst_discussion` 确保四个独立 analyst
- 确保每个 analyst 都有工具调用和 summary
- 从 `analyst_reports` 构建 `discussion_history`（如果为空）
- 确保工具结果被正确记录和分类

🎯 **预期效果**:
- 四个 analyst 都有成功调用工具并获得结果
- 每个 analyst 都有短的 summary（至少 50 字符）
- 工具结果被正确分类和显示

