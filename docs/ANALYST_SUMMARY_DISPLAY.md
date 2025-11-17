# 四个 Analyst Summary 显示修复

## 修复内容

### 问题
用户要求确保四个讨论的 agent（MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst）会根据得到的工具信息生成一个简短的 summary，并且网页也应该显示那个 summary。

### 修复

1. **后端确保生成 Summary**:
   - `run_multi_analyst_discussion` 中每个 analyst 都会调用 `_generate_analysis_from_tools` 生成 summary
   - Summary 存储在 `analysis` 字段中，至少 200 字符（约 50 字），目标 100-150 字（400-600 字符）
   - Summary 基于工具结果生成，包含具体的数据和洞察

2. **API 返回 discussion_rounds_summaries**:
   - `/api/agents/conversations` 端点返回 `discussion_rounds_summaries`
   - 按 round 和 agent 分组，每个 agent 包含 `summary`, `stance`, `tools_used`

3. **前端显示四个 Analyst 的 Summary**:
   - 新增 "📊 Analyst Summaries" 区域，显示四个 analyst 的 summary
   - 优先使用 `discussion_rounds_summaries` 中的数据
   - 每个 analyst 显示：图标、名称、stance（颜色标签）、使用的工具、summary

4. **优先使用 summary 字段**:
   - 在显示 conversation entry 时，优先使用 `summary` 字段
   - 如果 `summary` 不存在，才从 `content` 中提取

## 修改的文件

**`frontend/monitor.html`**:

1. **`renderConversations` 函数** (第 3583 行):
   - 添加 `discussionRoundsSummaries` 参数
   - 从 `discussionRoundsSummaries` 提取四个 analyst 的 summary
   - 新增 "📊 Analyst Summaries" 区域显示

2. **显示四个 Analyst 的 Summary** (第 3679-3705 行):
   ```javascript
   if (Object.keys(analystSummaries).length > 0) {
       html += `<div style="...">📊 Analyst Summaries</div>`;
       // 按固定顺序显示四个 analyst
       const analystOrder = ['MarketAnalyst', 'TechnicalAnalyst', 'FundamentalAnalyst', 'SentimentAnalyst'];
       for (const agentName of analystOrder) {
           // 显示每个 analyst 的 summary, stance, tools_used
       }
   }
   ```

3. **优先使用 summary 字段** (第 4058-4081 行):
   - 在显示 conversation entry 时，优先使用 `summary` 字段
   - 如果 `summary` 不存在，才从 `content` 中提取

4. **传递 discussion_rounds_summaries** (第 3464-3469 行):
   - 在调用 `renderConversations` 时传递 `discussion_rounds_summaries`

## 数据结构

### API 返回格式:
```json
{
  "ok": true,
  "conversations": [...],
  "discussion_rounds_summaries": {
    "1": [
      {
        "agent": "MarketAnalyst",
        "summary": "Market analysis shows...",
        "stance": "bullish",
        "tools_used": ["get_market_indices", "get_sector_rotation"]
      },
      {
        "agent": "TechnicalAnalyst",
        "summary": "Technical indicators suggest...",
        "stance": "neutral",
        "tools_used": ["get_advanced_indicators"]
      },
      ...
    ],
    "2": [...],
    "3": [...]
  }
}
```

### 前端显示格式:
- **Analyst Summaries 区域**:
  - 标题: "📊 Analyst Summaries"
  - 每个 analyst 显示在一个卡片中：
    - Agent 图标和名称
    - Stance 标签（颜色：bullish=绿色, bearish=红色, neutral=灰色）
    - 使用的工具列表
    - Summary 文本（完整显示，不截断）

- **Conversation Entry**:
  - 优先使用 `summary` 字段
  - 如果 `summary` 不存在，从 `content` 中提取

## Summary 生成逻辑

### 后端 (`multi_analyst_system.py`):

1. **工具调用**:
   - 每个 analyst 调用相关工具（MarketAnalyst: `get_market_indices`, `get_sector_rotation` 等）
   - 工具结果被收集到 `tool_results_summary`

2. **生成 Summary**:
   - 调用 `_generate_analysis_from_tools` 函数
   - 基于工具结果生成 100-150 字的分析
   - 包含具体数据、洞察和结论

3. **存储 Summary**:
   - 存储在 `analysis` 字段中
   - 写入 `discussion_history`
   - 通过 API 返回给前端

### Summary 内容要求:
- **长度**: 至少 200 字符（约 50 字），目标 100-150 字（400-600 字符）
- **内容**: 
  - 基于工具结果的具体分析
  - 包含具体数字和观察
  - 清晰的结论和立场
  - 如果包含新闻数据，必须分析新闻内容

## 验证步骤

1. **运行交易周期**:
   ```bash
   python -m src.orchestrator.trading_cycle
   ```

2. **检查日志**:
   - 查看 `data/logs/discussion_actions.jsonl`
   - 确认四个 analyst 都有 entry
   - 确认每个 analyst 都有 `summary` 字段（至少 200 字符）

3. **检查 API 响应**:
   ```bash
   curl http://127.0.0.1:8000/api/agents/conversations?limit=30
   ```
   - 确认 `discussion_rounds_summaries` 包含四个 analyst 的 summaries
   - 确认每个 summary 都有内容

4. **检查前端显示**:
   - 打开前端页面
   - 查看 "📊 Analyst Summaries" 区域
   - 确认四个 analyst 的 summary 都显示
   - 确认每个 summary 都包含工具结果的分析

## 预期效果

✅ **四个 analyst 都有 summary**:
- MarketAnalyst: 基于市场数据的分析（至少 200 字符）
- TechnicalAnalyst: 基于技术指标的分析（至少 200 字符）
- FundamentalAnalyst: 基于基本面数据的分析（至少 200 字符）
- SentimentAnalyst: 基于情绪数据的分析（至少 200 字符）

✅ **前端显示 summary**:
- "📊 Analyst Summaries" 区域显示四个 analyst 的 summary
- 每个 analyst 显示：图标、名称、stance、工具、summary
- Conversation entry 优先使用 `summary` 字段

✅ **Summary 内容**:
- 基于工具结果的具体分析
- 包含具体数字和观察
- 清晰的结论和立场

## 总结

✅ **修复完成**:
- 四个 analyst 都会根据工具结果生成 summary（至少 200 字符）
- API 返回 `discussion_rounds_summaries` 包含四个 analyst 的 summary
- 前端显示 "📊 Analyst Summaries" 区域，展示四个 analyst 的 summary
- Conversation entry 优先使用 `summary` 字段

🎯 **预期效果**:
- 四个 analyst 都有基于工具结果的简短 summary
- 网页正确显示这些 summary
- 用户可以快速了解每个 analyst 的分析结果

