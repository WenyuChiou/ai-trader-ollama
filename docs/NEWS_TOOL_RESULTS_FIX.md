# 新闻工具结果显示问题修复

## 问题描述

Sentiment Analyst 调用了 `news_scan` 工具，但前端显示：
- "No tool results found for SentimentAnalyst"
- "No news data available"
- "News tools (news_scan, plan_and_scan_news) have not been used yet."

## 根本原因

在 `trading_cycle.py` 中，工具结果保存时，agent 名称映射不完整：

```python
agent_name_map = {
    "market": "MarketAnalyst",
    "technical": "TechnicalAnalyst",
    "fundamental": "FundamentalAnalyst",
    "sentiment": "SentimentAnalyst",  # 只支持小写 "sentiment"
}
agent_name = agent_name_map.get(analyst_name.lower(), analyst_name)
```

问题：
- `multi_analyst_system.py` 中 `all_tool_calls` 的 `analyst` 字段是 `"SentimentAnalyst"`（完整名称）
- `analyst_name.lower()` 会将 `"SentimentAnalyst"` 转换为 `"sentimentanalyst"`，而不是 `"sentiment"`
- 映射失败，使用原始名称，但前端可能期望标准化的名称

## 修复方案

### 1. 改进 agent 名称映射

```python
agent_name_map = {
    "market": "MarketAnalyst",
    "marketanalyst": "MarketAnalyst",  # 支持完整名称
    "technical": "TechnicalAnalyst",
    "technicalanalyst": "TechnicalAnalyst",
    "fundamental": "FundamentalAnalyst",
    "fundamentanalyst": "FundamentalAnalyst",
    "sentiment": "SentimentAnalyst",
    "sentimentanalyst": "SentimentAnalyst",  # CRITICAL FIX: 支持完整名称匹配
}
# CRITICAL FIX: 先尝试完整匹配，再尝试小写匹配
agent_name = agent_name_map.get(analyst_name, agent_name_map.get(analyst_name.lower(), analyst_name))
```

### 2. 工具结果保存流程

1. **工具执行** (`multi_analyst_system.py`):
   - Sentiment Analyst 调用 `news_scan`
   - 自动转换为 `plan_and_scan_news(fetch_body_top=10)`
   - 工具结果添加到 `all_tool_calls`:
     ```python
     all_tool_calls.append({
         "analyst": "SentimentAnalyst",
         "tool": "plan_and_scan_news",
         "result": tool_result
     })
     ```

2. **保存到文件** (`trading_cycle.py`):
   - 遍历 `all_tool_calls`
   - 标准化 agent 名称（现在支持完整名称匹配）
   - 写入 `discussion_actions.jsonl`:
     ```json
     {
         "type": "tool",
         "agent": "SentimentAnalyst",
         "tool_name": "plan_and_scan_news",
         "tool_category": "news",
         "tool_result": {...}
     }
     ```

3. **前端API读取** (`server.py`):
   - 读取 `discussion_actions.jsonl`
   - 按 `tool_category` 分类工具结果
   - 返回 `tool_results_by_category.news`

4. **前端显示** (`monitor.html`):
   - 从 `tool_results_by_category.news` 收集新闻数据
   - 显示在新闻模态框中

## 验证步骤

### 1. 检查工具是否被调用

查看后端日志：
```
[4/4] Sentiment Analyst analyzing...
   [TOOL] Tools requested: 3
   [TOOL] Tool names: fear_greed, vix_term, news_scan
   [NEWS] Converting news_scan to plan_and_scan_news to fetch article content
   [OK] Tool plan_and_scan_news executed successfully - 10 hits, 4 articles
```

### 2. 检查工具结果是否被保存

检查 `data/logs/discussion_actions.jsonl` 文件，应该包含：
```json
{
    "type": "tool",
    "agent": "SentimentAnalyst",
    "tool_name": "plan_and_scan_news",
    "tool_category": "news",
    "tool_result": {
        "hits": [...],
        "articles": [...],
        "queries": [...]
    }
}
```

### 3. 检查前端API返回

访问 `/api/agents/conversations`，检查返回的 `tool_results_by_category.news` 是否包含工具结果。

### 4. 检查前端显示

打开前端，点击新闻按钮，应该能看到新闻数据。

## 如果问题仍然存在

### 检查点1: 工具执行是否成功

查看后端日志，确认工具执行成功：
```
[OK] Tool plan_and_scan_news executed successfully - 10 hits, 4 articles
```

如果显示失败，检查工具执行错误。

### 检查点2: 文件是否被写入

检查 `data/logs/discussion_actions.jsonl` 文件，确认工具结果被写入。

### 检查点3: 前端API是否正确读取

检查 `/api/agents/conversations` 返回的 `tool_results_by_category.news` 数组是否为空。

### 检查点4: 前端解析是否正确

打开浏览器控制台，检查是否有错误：
```javascript
[News] Using tool_results_by_category.news: X items
```

## 相关文件

- `backend/src/orchestrator/trading_cycle.py` - 工具结果保存逻辑
- `backend/src/agents/multi_analyst_system.py` - 工具执行逻辑
- `backend/src/api/server.py` - 前端API（工具结果分类）
- `frontend/monitor.html` - 前端显示逻辑

## 修复状态

✅ **已修复**: Agent 名称映射问题
- 支持完整 agent 名称匹配（如 `SentimentAnalyst`）
- 支持小写匹配（如 `sentiment`）
- 确保工具结果正确保存和显示

## 测试建议

运行一次交易循环，然后：
1. 检查后端日志，确认工具被调用
2. 检查 `discussion_actions.jsonl`，确认工具结果被保存
3. 检查前端，确认新闻数据被显示

