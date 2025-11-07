# Tool Usage Analysis: 为什么有时有tool request，有时没有？

## 🔍 问题分析

### 1. 为什么LLM有时不调用工具？

**主要原因：**

1. **LLM模型限制**
   - llama3.1 等较小模型有时不严格遵循复杂指令
   - 即使prompt明确要求，也可能忽略或忘记

2. **上下文理解偏差**
   - LLM可能认为已有数据（market_view）足够，不需要额外工具
   - 看到 `tools_context` 中有数据，认为不需要再调用

3. **JSON解析问题**
   - LLM返回的JSON可能格式不正确
   - `tool_calls` 字段可能被解析错误或丢失

4. **Prompt冲突**
   - 有些prompt说"Use tools only when you genuinely need more information"
   - 有些prompt说"MUST call at least 2-3 tools"
   - LLM可能被这些冲突的指令搞混

### 2. 当前代码的处理方式

```python
# Fallback机制
if not tool_calls_list and use_tools and tool_calls_count < tool_budget:
    print(f"   ⚠️  No tools requested, using fallback tools")
    # 使用默认工具
```

**优点：**
- 确保即使LLM不调用工具，系统仍能工作
- 保证分析基于实际数据

**缺点：**
- 可能使用不相关的工具
- 浪费tool budget
- 掩盖了LLM不遵循指令的问题

## 💡 建议方案

### 方案1: 强制要求（当前部分实现）

**优点：**
- ✅ 确保所有分析基于实际数据
- ✅ 提高分析质量
- ✅ 避免"空分析"

**缺点：**
- ❌ 可能浪费tool budget（如果已有数据足够）
- ❌ 增加延迟（工具调用需要时间）
- ❌ LLM可能仍然不遵循（需要fallback）

**实现方式：**
- 保持当前的fallback机制
- 改进prompt，更明确地要求工具调用
- 在解析时检查，如果没有tool_calls，使用fallback

### 方案2: 智能选择（推荐）

**优点：**
- ✅ 更灵活，根据情况决定
- ✅ 节省tool budget
- ✅ 如果已有数据足够，不需要额外工具

**缺点：**
- ❌ 需要判断"何时需要工具"
- ❌ LLM可能错误判断

**实现方式：**
```python
# 检查是否有足够的上下文数据
has_sufficient_data = (
    market_view.get("stocks") and 
    len(market_view.get("stocks", {})) > 10 and
    market_view.get("vix") is not None
)

if not has_sufficient_data or not tool_calls_list:
    # 强制使用工具
    use_fallback_tools()
```

### 方案3: 混合方案（最佳）

**策略：**
1. **Market Analyst**: 总是需要工具（市场数据变化快）
2. **Technical Analyst**: 总是需要工具（技术指标需要计算）
3. **Fundamental Analyst**: 可选（如果已有fundamental数据）
4. **Sentiment Analyst**: 总是需要工具（新闻和情绪变化快）

**实现：**
```python
# 根据analyst类型决定是否强制工具
MANDATORY_TOOLS = {
    "market": True,
    "technical": True,
    "fundamental": False,  # 可选
    "sentiment": True,
}

if MANDATORY_TOOLS.get(analyst_type, True) and not tool_calls_list:
    use_fallback_tools()
```

## 🎯 推荐方案

**建议采用方案3（混合方案）+ 改进的fallback机制：**

1. **Market/Technical/Sentiment Analyst**: 强制要求工具
   - 这些数据变化快，需要实时获取
   - 即使有基础数据，也需要更深入的分析

2. **Fundamental Analyst**: 可选
   - 基本面数据变化慢
   - 如果已有数据，可以基于现有数据分析

3. **改进fallback机制**:
   - 根据analyst类型选择最相关的工具
   - 不要总是用同样的fallback工具

4. **改进prompt**:
   - 更明确地说明"为什么需要工具"
   - 给出具体示例
   - 减少冲突的指令

## 📊 当前统计

从测试结果看：
- Market Analyst: ✅ 通常调用工具（3-4个）
- Technical Analyst: ⚠️ 有时不调用（需要fallback）
- Fundamental Analyst: ⚠️ 有时不调用（需要fallback）
- Sentiment Analyst: ✅ 通常调用工具（2-3个）

## 🔧 具体改进建议

1. **改进Technical Analyst prompt**:
   ```
   你必须使用get_advanced_indicators来获取技术指标。
   没有技术指标数据，你无法进行技术分析。
   ```

2. **改进Fundamental Analyst prompt**:
   ```
   如果market_view中没有fundamental数据，你必须调用get_company_fundamentals。
   如果已有数据，可以基于现有数据分析，但仍建议调用工具获取最新数据。
   ```

3. **改进fallback逻辑**:
   ```python
   FALLBACK_TOOLS = {
       "market": ["get_market_indices", "get_sector_rotation"],
       "technical": ["get_advanced_indicators", "get_support_resistance"],
       "fundamental": ["get_company_fundamentals"],
       "sentiment": ["fear_greed", "news_scan"],
   }
   ```

