# Agent Loop 框架分析

## 📋 框架概览

### 核心组件

1. **主函数**: `run_analyst_discussion()` (`backend/src/agents/analyst_discussion.py`)
2. **Agent**: `discussion_agent` (通过 AgentFactory 创建)
3. **工具系统**: `ToolBox` (提供各种市场数据工具)
4. **调用位置**: `trading_cycle.py` 中的交易循环

### 关键参数

```python
run_analyst_discussion(
    market_view: Dict[str, Any],      # 市场视图数据
    rounds: int = 3,                  # 最大轮数
    auto_tools: bool = True,           # 是否自动执行工具
    tool_budget: int = 3,              # 工具调用预算
    min_tools: int = 3,                # 最小工具使用数量（强制要求）
    preferred_domains: List[str],      # 偏好域名
    historical_memories: List[Dict],   # 历史记忆
)
```

## 🔄 循环流程

### 每轮循环步骤

```
Round N:
1. 准备 prompt 上下文
   ├─ 已有工具结果摘要 (tool_context_lines)
   ├─ 如果未达到 min_tools，添加强制提示
   └─ 更新 tool_budget 状态

2. Agent 运行
   └─ agent.run(vars_ctx, expect_json=False, user_append=extra_user)

3. 解析输出
   ├─ 尝试解析 JSON (stance, tool_calls, actions)
   └─ 标准化共识数据 (_normalize_consensus)

4. 执行工具调用
   ├─ 遍历 tool_calls
   ├─ 调用 tb.invoke(name, **kwargs)
   ├─ 记录成功结果到 tool_context_lines
   └─ 更新 tool_budget 和 new_tools_executed

5. 检查早退条件
   ├─ finalize + min_tools 满足 → break
   └─ 连续2轮无新工具 + min_tools 满足 → break

6. 更新上下文
   └─ 准备下一轮
```

## ⚠️ 当前问题分析

### 问题 1: tool_budget 与 min_tools 冲突

**场景**:
- `tool_budget = 3`, `min_tools = 3`
- 如果前3轮各用1个工具，tool_budget 用完
- 但如果某个工具调用失败，实际只用了2个工具
- 此时 tool_budget = 0，无法再调用工具，但 min_tools 未满足

**代码位置**: `analyst_discussion.py:258-306`

```python
if auto_tools and tool_budget > 0 and tool_calls:
    for call in tool_calls:
        if tool_budget <= 0:  # ⚠️ 这里会阻止继续调用
            break
        # ... 执行工具调用
```

**影响**: Agent 无法满足 min_tools 要求，但循环可能继续或早退

---

### 问题 2: 早退条件可能过早触发

**场景**:
- Agent 在第1轮用了1个工具
- 第2、3轮都没有调用工具（consecutive_no_tools = 2）
- 但 `len(tool_context_lines) = 1 < min_tools = 3`
- 代码检查: `if consecutive_no_tools >= 2 and len(tool_context_lines) >= min_tools`
- 由于 min_tools 未满足，不会早退 ✅ (这部分逻辑正确)

**潜在问题**:
- 如果 Agent 一直不调用工具，循环会跑满 rounds
- 即使提示了 min_tools 要求，Agent 可能忽略

**代码位置**: `analyst_discussion.py:323-331`

---

### 问题 3: min_tools 提示可能不够强制

**场景**:
- Agent 收到 min_tools 提示（第228-241行）
- 但 Agent 可能：
  1. 返回的 JSON 中没有 tool_calls
  2. tool_calls 格式错误
  3. 调用的工具失败

**当前处理**:
- 只在 prompt 中添加文字提示
- 没有强制机制确保 Agent 必须调用工具

**代码位置**: `analyst_discussion.py:228-241`

```python
if len(tool_context_lines) < min_tools:
    # 添加提示文字
    extra_user += f"\n\n========== [MINIMUM TOOL REQUIREMENT] ==========\n..."
```

---

### 问题 4: 工具调用失败不计入 min_tools

**场景**:
- Agent 调用了工具，但工具执行失败
- `tool_context_lines` 不会增加
- 但 `tool_budget` 可能已经减少（取决于实现）

**代码位置**: `analyst_discussion.py:297-306`

```python
res = tb.invoke(name, **kwargs)
if res.get("ok"):
    new_tools_executed += 1
    tool_budget -= 1
    tool_context_lines.append(summary_line)  # ✅ 只有成功才添加
else:
    # ❌ 失败不计入，但 tool_budget 可能已减少
    print(f"[TOOL_ERR] {name} failed...")
```

---

### 问题 5: finalize 可能在 min_tools 未满足时被忽略

**场景**:
- Agent 在第1轮就 finalize
- 但只用了1个工具（< min_tools）
- 代码检查: `if decided_finalize and len(tool_context_lines) >= min_tools`
- 由于 min_tools 未满足，不会早退 ✅ (这部分逻辑正确)

**但问题**:
- Agent 已经决定 finalize，但被强制继续
- 可能导致 Agent 困惑或重复 finalize

**代码位置**: `analyst_discussion.py:319-321`

---

## 🔧 建议修复方案

### 方案 1: 改进 tool_budget 逻辑

```python
# 如果未达到 min_tools，允许超预算调用工具
if auto_tools and tool_calls:
    for call in tool_calls:
        # 如果未达到 min_tools，允许超预算
        if tool_budget <= 0 and len(tool_context_lines) >= min_tools:
            break
        # ... 执行工具调用
        if res.get("ok"):
            tool_budget -= 1  # 只在成功时减少预算
```

### 方案 2: 强制工具调用机制

```python
# 如果未达到 min_tools 且 Agent 没有调用工具，强制调用
if len(tool_context_lines) < min_tools and not tool_calls:
    # 强制调用默认工具（如 news_scan, vix_term）
    forced_tools = ["news_scan", "vix_term", "fear_greed"]
    for tool_name in forced_tools:
        if len(tool_context_lines) >= min_tools:
            break
        # 执行强制工具调用
```

### 方案 3: 改进早退条件

```python
# 确保在达到 min_tools 之前不会早退
if decided_finalize:
    if len(tool_context_lines) >= min_tools:
        break
    else:
        # 重置 finalize，强制继续
        decided_finalize = False
        print(f"[WARN] Agent tried to finalize but min_tools not met ({len(tool_context_lines)}/{min_tools})")
```

### 方案 4: 工具调用失败重试

```python
# 如果工具调用失败，尝试其他工具
if not res.get("ok") and len(tool_context_lines) < min_tools:
    # 尝试备用工具
    fallback_tools = ["news_scan", "vix_term"]
    for fallback in fallback_tools:
        if fallback != name:  # 避免重复
            res = tb.invoke(fallback, **fallback_kwargs)
            if res.get("ok"):
                # 成功，添加到 tool_context_lines
                break
```

---

## 📊 当前状态总结

### ✅ 正确的逻辑

1. **min_tools 检查**: 早退条件都检查了 `len(tool_context_lines) >= min_tools`
2. **提示机制**: 未达到 min_tools 时会添加提示
3. **工具结果累积**: 成功执行的工具会累积到 `tool_context_lines`

### ⚠️ 需要改进的地方

1. **tool_budget 限制**: 可能阻止达到 min_tools
2. **工具调用失败**: 不计入 min_tools，但可能消耗 budget
3. **强制机制不足**: 只有提示，没有强制调用
4. **Agent 不配合**: Agent 可能忽略 min_tools 提示

### 🎯 优先级

1. **高优先级**: 修复 tool_budget 与 min_tools 冲突
2. **中优先级**: 添加工具调用失败处理
3. **低优先级**: 添加强制工具调用机制（可能影响 Agent 自主性）

---

## 📝 测试场景

### 测试用例 1: 正常流程
- `rounds=3`, `tool_budget=8`, `min_tools=3`
- Agent 每轮调用1-2个工具
- 预期: 3轮内达到 min_tools，正常结束

### 测试用例 2: tool_budget 不足
- `rounds=5`, `tool_budget=2`, `min_tools=3`
- Agent 需要调用3个工具，但预算只有2
- 预期: 应该允许超预算调用以满足 min_tools

### 测试用例 3: 工具调用失败
- `rounds=3`, `tool_budget=5`, `min_tools=3`
- 前2个工具调用失败
- 预期: 应该继续尝试直到达到 min_tools

### 测试用例 4: Agent 不调用工具
- `rounds=3`, `tool_budget=8`, `min_tools=3`
- Agent 一直不返回 tool_calls
- 预期: 应该强制调用工具或至少运行满 rounds

---

## 🔗 相关文件

- `backend/src/agents/analyst_discussion.py` - 主循环实现
- `backend/scripts/test_agent_loop_final.py` - 测试脚本
- `backend/src/orchestrator/trading_cycle.py` - 调用位置
- `backend/src/agents/toolbox.py` - 工具系统

