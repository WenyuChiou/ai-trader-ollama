# 完整讨论轮次展示

## 📊 讨论轮次机制说明

### 完整的每轮循环流程

每轮讨论遵循以下流程：

```
ROUND 1:
1. Agent 分析市场数据
   ↓
2. Agent 判断是否需要更多信息
   ↓
3. 如果需要 → 调用工具（news_scan, vix_term, fear_greed 等）
   ↓
4. 工具结果注入到下一轮的 [TOOLS CONTEXT]
   ↓
5. Agent 基于工具结果进行反思和推理
   ↓
6. 输出结构化 JSON（stance, rationale, tool_calls, actions）
   ↓
7. 决定是否继续下一轮（consider_probe）或结束（finalize）

ROUND 2:
1. Agent 接收上一轮的工具结果（在 [TOOLS CONTEXT] 中）
   ↓
2. Agent 被明确告知：不要重复调用已执行过的工具
   ↓
3. Agent 基于现有信息进行推理
   ↓
4. 如果信息不足 → 可以调用新工具（但工具预算有限）
   ↓
5. 输出更新的 stance 和 rationale

...（继续直到 rounds 上限或 finalize）
```

## 🎯 每轮输出结构

### Agent 的输出（JSON 格式）

每轮 Agent 会输出以下结构：

```json
{
  "stance": "bullish" | "bearish" | "neutral",
  "rationale": [
    {
      "source": "technical_indicators",
      "reason": "NVDA shows strong momentum with RSI=65..."
    },
    {
      "source": "news_scan",
      "reason": "Recent news about AI chips positive..."
    }
  ],
  "signals_used": ["rsi14", "macd", "news"],
  "tool_calls": [
    {
      "name": "news_scan",
      "args": {
        "keywords": ["NVDA", "AI"],
        "recency_days": 7,
        "max_articles": 10
      },
      "why": "Need to check recent news about NVDA and AI sector"
    },
    {
      "name": "vix_term",
      "args": {},
      "why": "Need to assess market volatility structure"
    }
  ],
  "actions": [
    {
      "type": "consider_probe",
      "why": "Have initial stance but want to verify with tools",
      "next_checks": ["news_sentiment", "vix_structure"]
    }
  ],
  "to_agent_notes": "Next round: focus on risk assessment"
}
```

## 🔄 工具调用机制

### 工具调用流程

1. **Agent 判断需要信息**
   - Agent 分析当前市场数据
   - 发现缺少某些关键信息（如新闻情绪、VIX 结构等）
   - 决定调用工具

2. **工具调用**
   ```python
   tool_calls = [
       {
           "name": "news_scan",
           "args": {"keywords": ["NVDA"], "recency_days": 7},
           "why": "Need to check recent NVDA news"
       }
   ]
   ```

3. **工具执行**
   ```python
   # ToolBox 执行工具
   result = toolbox.invoke("news_scan", keywords=["NVDA"], recency_days=7)
   # 返回: {"ok": True, "result": {"hits": [...], "queries": [...]}}
   ```

4. **工具结果摘要**
   ```python
   # 生成摘要供下一轮使用
   summary = "news_scan: 15 hits, queries=['NVDA'], samples=['NVDA earnings...', 'AI chip demand...']"
   ```

5. **注入到下一轮**
   ```
   [TOOLS CONTEXT] - USE THESE RESULTS, DO NOT CALL THESE TOOLS AGAIN
   - news_scan: 15 hits, queries=['NVDA'], samples=['NVDA earnings...']
   
   ⚠️ IMPORTANT: The tools listed above have already been executed.
   DO NOT call these tools again in tool_calls.
   ```

## 💭 反思和推理过程

### Agent 的反思机制

1. **第一轮：信息收集**
   ```
   Agent: "我需要更多信息来判断市场立场。让我调用 news_scan 和 vix_term。"
   → 调用工具
   → 工具结果注入 [TOOLS CONTEXT]
   ```

2. **第二轮：基于工具结果推理**
   ```
   Agent: "好的，我看到 news_scan 显示了 15 条相关新闻。
           让我分析这些新闻的情绪和 VIX 结构。
           
           基于工具结果：
           - 新闻情绪：整体正面（AI 芯片需求强劲）
           - VIX 结构：contango（ratio=1.15），市场情绪稳定
           
           我的立场：bullish（看涨）
           理由：
           - 技术指标显示强势（RSI=65, MACD positive）
           - 新闻情绪正面
           - 波动率结构稳定"
   ```

3. **第三轮：最终确认**
   ```
   Agent: "我已经收集了足够的信息，形成了明确的立场。
           让我 finalize 我的分析。
           
           Final stance: bullish
           Rationale: [综合所有信息]"
   ```

## 📋 完整轮次示例

### Round 1: 信息收集阶段

**Agent 输出：**
```json
{
  "stance": "neutral",
  "rationale": [
    {
      "source": "initial_analysis",
      "reason": "NVDA shows positive technical signals, but need more information about market sentiment"
    }
  ],
  "tool_calls": [
    {
      "name": "news_scan",
      "args": {"keywords": ["NVDA", "AI"], "recency_days": 7},
      "why": "Need to assess recent news sentiment for NVDA and AI sector"
    },
    {
      "name": "vix_term",
      "args": {},
      "why": "Need to understand volatility term structure for risk assessment"
    }
  ],
  "actions": [
    {
      "type": "consider_probe",
      "why": "Need to gather more information before finalizing stance",
      "next_checks": ["news_sentiment", "volatility_structure"]
    }
  ]
}
```

**系统操作：**
```
[TOOLS_OK] news_scan: 15 hits, queries=['NVDA', 'AI'], samples=['NVDA earnings beat expectations...']
[TOOLS_OK] vix_term: VIX=16.5, VIX3M=19.0, ratio=1.15 (contango if >1)
```

**工具结果注入到 Round 2：**
```
[TOOLS CONTEXT]
- news_scan: 15 hits, queries=['NVDA', 'AI'], samples=['NVDA earnings beat...']
- vix_term: VIX=16.5, VIX3M=19.0, ratio=1.15 (contango if >1)

⚠️ IMPORTANT: DO NOT call these tools again!
```

### Round 2: 推理和反思阶段

**Agent 输出（基于工具结果）：**
```json
{
  "stance": "bullish",
  "rationale": [
    {
      "source": "technical_indicators",
      "reason": "NVDA shows strong momentum: RSI=65 (neutral-strong), MACD positive, price above MA20"
    },
    {
      "source": "news_scan",
      "reason": "Recent news highly positive: earnings beat, strong AI chip demand, positive analyst outlook"
    },
    {
      "source": "vix_term",
      "reason": "VIX structure shows contango (ratio=1.15), indicating stable market sentiment"
    }
  ],
  "signals_used": ["rsi14", "macd", "news_scan", "vix_term"],
  "tool_calls": [],  // 不再调用工具（因为已有足够信息）
  "actions": [
    {
      "type": "finalize",
      "why": "Have sufficient information from tools and analysis",
      "next_checks": []
    }
  ]
}
```

**系统操作：**
```
[INFO] Agent finalized stance: bullish
[INFO] No new tools called (agent used existing tool results)
```

### Round 3: （可选）最终确认

如果设置了更多轮次，Agent 可能会进一步细化分析。

## 🎯 关键机制总结

### 1. **工具预算管理**
- 每轮有 `tool_budget` 限制
- 每次工具调用消耗 1 个预算
- 预算耗尽后无法调用新工具

### 2. **工具结果注入**
- 工具结果被总结成一行摘要
- 注入到下一轮的 `[TOOLS CONTEXT]`
- Agent 被明确告知不要重复调用

### 3. **早退机制**
- 如果 Agent 明确 `finalize`，提前结束
- 如果连续 2 轮没有新工具，提前结束（内容稳定）

### 4. **反思和推理**
- Agent 基于工具结果进行推理
- 每轮更新 stance 和 rationale
- 最终形成综合判断

## 📝 运行测试查看结果

### 运行讨论轮次测试

```bash
cd backend
python show_discussion_rounds.py
```

### 运行完整交易循环测试

```bash
cd backend
python test_full_cycle_detailed.py
```

这将展示：
- ✅ 每轮的完整输出
- ✅ 工具调用过程
- ✅ 问题提出和反思
- ✅ 对话内容
- ✅ 最终 stance 和 rationale

**详细结果会保存到 `backend/data/logs/discussion_rounds_result.json`**

