# API 端点增强完成报告

## 修复内容

### 1. ✅ Market Sentiment Dashboard 数据获取修复

**问题**: Market Sentiment Dashboard 没有正确抓取数据

**修复**:
- **`/api/vix/term`**: 
  - 修复函数调用：从 `get_vix_term_structure` 改为 `vix_term_structure`（从 `sentiment_tools`）
  - 修复返回格式：直接返回 `vix`, `vix3m`, `ratio`, `vix_risk_score`（前端期望的格式）
  - 添加风险分数计算：使用 `vix_risk_score` 函数
  
- **`/api/fear-greed`**:
  - 修复函数调用：从 `get_fear_greed_index` 改为 `fetch_fear_greed`（从 `sentiment_tools`）
  - 修复返回格式：直接返回 `value` 和 `label`（前端期望的格式）
  - 同时保留完整 `fear_greed` 对象供前端使用

**API 响应格式**:
```json
// /api/vix/term
{
  "ok": true,
  "vix": 19.83,           // ✅ 直接返回数值
  "vix3m": 21.58,         // ✅ 直接返回数值
  "ratio": 1.088,         // ✅ 直接返回数值
  "vix_risk_score": 4.0,  // ✅ 添加风险分数
  "regime": "contango"
}

// /api/fear-greed
{
  "ok": true,
  "value": 22,            // ✅ 直接返回数值
  "label": "Extreme Fear", // ✅ 直接返回标签
  "fear_greed": {...}     // ✅ 保留完整对象
}
```

### 2. ✅ 三轮讨论记录提取和展示

**问题**: 聊天记录的三轮记录应该要萃取之后，把每个 agent 的 summary 分别展示出来

**修复**:
- 添加 `discussion_rounds_summaries` 字段到 API 响应
- 按 round（1, 2, 3）和 agent 分组
- 提取每个 agent 的 summary、stance、tools_used

**API 响应格式**:
```json
{
  "ok": true,
  "conversations": [...],
  "discussion_rounds": {
    "1": [...],  // 原始数据
    "2": [...],
    "3": [...]
  },
  "discussion_rounds_summaries": {  // ✅ 新增：按 agent 分组的 summaries
    "1": [
      {
        "agent": "MarketAnalyst",
        "summary": "...",
        "stance": "bullish",
        "tools_used": ["get_market_indices", "get_sector_rotation"]
      },
      {
        "agent": "TechnicalAnalyst",
        "summary": "...",
        "stance": "neutral",
        "tools_used": ["get_advanced_indicators"]
      }
    ],
    "2": [...],
    "3": [...]
  }
}
```

### 3. ✅ 工具结果分类显示

**问题**: agent 如果有调用工具，要把结果放在前端的特定栏位，如 shownews, risk, market 等

**修复**:
- 在 `trading_cycle.py` 中为每个工具 entry 添加 `tool_category` 字段
- 在 API 响应中添加 `tool_results_by_category` 字段
- 按工具类型分类：news, risk, market, fundamental, economic, crypto, other

**工具分类映射**:
- **news**: `news_scan`, `plan_and_scan_news`, `fetch_jin10_news`, `web_search`, `fetch_url`
- **risk**: `vix_term`, `vix_close`, `fear_greed`, `get_market_breadth`
- **market**: `get_market_indices`, `get_sector_rotation`, `get_correlation_matrix`, `get_advanced_indicators`, `get_support_resistance`
- **fundamental**: `get_company_fundamentals`, `get_earnings_history`, `get_financial_statements`
- **economic**: `get_economic_summary`, `get_labor_market_data`, `fetch_fred_indicator`, `fetch_jin10_economic_data`
- **crypto**: `fetch_crypto_batch`, `get_crypto_price`

**API 响应格式**:
```json
{
  "ok": true,
  "conversations": [...],
  "tool_results_by_category": {  // ✅ 新增：按工具类型分类
    "news": [
      {
        "tool_name": "news_scan",
        "tool_result": {
          "hits": [...],
          "queries": [...]
        },
        "timestamp": "...",
        "agent": "ToolSystem"
      }
    ],
    "risk": [
      {
        "tool_name": "vix_term",
        "tool_result": {
          "vix": 19.83,
          "vix3m": 21.58,
          "ratio": 1.088
        },
        "timestamp": "...",
        "agent": "ToolSystem"
      }
    ],
    "market": [...],
    "fundamental": [...],
    "economic": [...],
    "crypto": [...],
    "other": [...]
  }
}
```

**工具 Entry 格式**:
```json
{
  "agent": "ToolSystem",
  "type": "tool",
  "tool_name": "news_scan",
  "tool_category": "news",  // ✅ 新增：工具分类
  "tool_result": {          // ✅ 新增：结构化工具结果
    "hits": [...],
    "queries": [...]
  },
  "content": "Tool used: news_scan: {...}",
  "timestamp": "..."
}
```

## 修改的文件

1. **`backend/src/api/server.py`**:
   - 修复 `/api/vix/term` 端点（第 739-792 行）
   - 修复 `/api/fear-greed` 端点（第 794-838 行）
   - 增强 `/api/agents/conversations` 端点（第 318-481 行）：
     - 添加 `discussion_rounds_summaries` 字段
     - 添加 `tool_results_by_category` 字段

2. **`backend/src/orchestrator/trading_cycle.py`**:
   - 添加工具分类逻辑（第 618-631 行）
   - 在工具 entry 中添加 `tool_category` 和 `tool_result` 字段（第 633-643 行）

## 验证步骤

1. **测试 Market Sentiment Dashboard**:
   ```bash
   curl http://127.0.0.1:8000/api/vix/term
   curl http://127.0.0.1:8000/api/fear-greed
   ```
   - 应该返回正确的 `vix`, `vix3m`, `ratio`, `vix_risk_score` 和 `value`, `label`

2. **测试三轮讨论记录**:
   ```bash
   curl http://127.0.0.1:8000/api/agents/conversations?limit=30
   ```
   - 响应应该包含 `discussion_rounds_summaries` 字段
   - 每个 round 应该包含按 agent 分组的 summaries

3. **测试工具结果分类**:
   ```bash
   curl http://127.0.0.1:8000/api/agents/conversations?limit=30
   ```
   - 响应应该包含 `tool_results_by_category` 字段
   - 工具应该按类型分类（news, risk, market等）

## 总结

✅ **所有修复已完成**:
- Market Sentiment Dashboard 数据获取正确
- 三轮讨论记录按 agent 分组显示 summary
- 工具结果按类型分类（news, risk, market等）

🎯 **预期效果**:
- 前端可以正确显示 Market Sentiment Dashboard
- 前端可以正确显示每个 agent 的 summary（按 round 分组）
- 前端可以根据工具类型（news, risk, market等）分类显示工具结果

