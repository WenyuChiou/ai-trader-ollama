# 工具调用机制说明

**更新时间**: 2025-11-14

---

## 🔧 工具调用机制

### 1. Agent自主决策

**机制**: Agents（分析师）可以自主决定调用哪些工具

**流程**:
1. Agent 分析市场数据和上下文
2. Agent 决定需要哪些工具来获取额外信息
3. Agent 在响应中返回 `tool_calls` 列表
4. 系统执行工具并返回结果
5. Agent 基于工具结果生成最终分析

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 168-199 行

```python
# Agent 返回 tool_calls
tool_calls_list = market_result.get("tool_calls", [])

# 执行工具
for tool_call in tool_calls_list[:max_tools_per_analyst]:
    tool_result = _execute_tool(toolbox, tool_call, market_summary)
    # ... 处理结果
```

---

### 2. Fallback机制

**机制**: 如果Agent没有请求工具，系统会自动添加必要的工具

**触发条件**:
- Agent 没有返回 `tool_calls`
- 工具预算 (`tool_budget`) 还有剩余
- `use_tools = True`

**Fallback工具**:

**Market Analyst**:
- `get_market_indices`: 获取市场指数
- `get_sector_rotation`: 分析板块轮动
- `get_market_breadth`: 获取市场广度

**Sentiment Analyst**:
- `fear_greed`: 恐惧贪婪指数
- `vix_term`: VIX期限结构
- `news_scan`: **新闻扫描（自动添加）**

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 172-178 行, 第 530-534 行

---

### 3. 新闻工具使用

**工具名称**: `news_scan`

**自动添加机制**:
1. **Fallback添加**: 如果Sentiment Analyst没有请求工具，自动添加 `news_scan`
2. **强制添加**: 即使Agent请求了其他工具，如果缺少新闻工具，也会自动添加
3. **自动参数**: 如果没有提供keywords，系统会自动从market_summary中提取symbols作为keywords

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 1200-1222 行

```python
# 处理 news_scan 工具：确保有 keywords
if tool_name == "news_scan":
    if not has_keywords:
        # 从 market_summary 中提取 symbols
        symbols = market_summary.get("symbols") or market_summary.get("sample_stocks") or []
        if symbols:
            keywords = [str(s) for s in symbols[:10]]
        else:
            keywords = ["market", "AI", "tariff", "stocks", "economy"]
        tool_args["keywords"] = keywords
```

**默认Keywords**:
- 如果market_summary中有symbols，使用前10个symbols
- 如果没有，使用默认关键词：`["market", "AI", "tariff", "stocks", "economy"]`

---

### 4. 工具调用限制

**每个Analyst限制**: 最多5个工具（`max_tools_per_analyst = 5`）

**总预算限制**: `tool_budget`（默认15个工具）

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 185 行

```python
max_tools_per_analyst = min(5, tool_budget - tool_calls_count)
```

---

### 5. 工具执行流程

**步骤**:
1. 检查工具是否存在
2. 验证和补充参数（如symbols, keywords）
3. 执行工具
4. 格式化结果
5. 传递给Agent进行进一步分析

**代码位置**: `backend/src/agents/multi_analyst_system.py` 第 1163-1243 行

---

## 📰 新闻工具使用情况

### 为什么可能看不到新闻？

**可能原因**:
1. **Agent主动请求了其他工具**: 如果Agent主动请求了工具，fallback不会触发
2. **工具预算用完**: 如果工具预算用完了，不会添加新工具
3. **工具执行失败**: 如果news_scan执行失败，结果可能为空

### 如何确保新闻被使用？

**已实现的机制**:
1. ✅ **Fallback强制添加**: Sentiment Analyst的fallback中包含news_scan
2. ✅ **主动检查**: 即使Agent请求了工具，如果缺少新闻工具，也会自动添加
3. ✅ **自动参数**: 自动从market_summary提取keywords

**最新改进** (2025-11-14):
- 即使Agent请求了其他工具，如果缺少新闻工具，系统会自动添加 `news_scan`
- 使用更多keywords（最多10个symbols）以提高新闻覆盖率

---

## 🔍 检查工具使用情况

### 查看后端日志

**日志位置**: 控制台输出

**关键日志**:
```
[TOOL] Tools requested: 3
[TOOL] Executing: news_scan
[INFO] Auto-added keywords=['NVDA', 'MSFT', 'AAPL', ...] to news_scan
[OK] Tool news_scan executed successfully
```

### 查看前端显示

**位置**: 对话面板中的工具调用记录

**显示内容**:
- 工具名称
- 工具参数
- 工具结果（如果有）

---

## ✅ 总结

**工具调用机制**:
1. ✅ Agents自主决定调用工具
2. ✅ Fallback机制确保必要工具被使用
3. ✅ 新闻工具（news_scan）在Sentiment Analyst中强制使用
4. ✅ 自动参数补充（keywords, symbols等）

**新闻工具**:
- ✅ 在Sentiment Analyst的fallback中自动添加
- ✅ 即使Agent请求了其他工具，也会检查并添加新闻工具
- ✅ 自动从market_summary提取keywords
- ✅ 默认使用市场相关关键词

**如果看不到新闻**:
- 检查后端日志，确认工具是否被执行
- 检查工具结果是否为空
- 检查前端是否正确显示工具调用记录

