# 如何运行详细测试查看完整循环

## 🚀 快速开始

### 运行完整交易循环测试（包含详细轮次）

```bash
cd backend
python run_detailed_test.py
```

这将展示：
- ✅ 每轮讨论的完整输出
- ✅ 工具调用过程（news_scan, vix_term 等）
- ✅ Agent 提出的问题
- ✅ Agent 的反思和推理过程
- ✅ 对话内容（transcript）
- ✅ 最终决策和执行结果

## 📊 输出结构

测试会展示以下信息：

### 1. STEP 1: Market Data Collection
- 分析的股票数量
- Top 信号

### 2. STEP 2: Analyst Discussion - DETAILED ROUNDS
- **每轮的完整输出**，包括：
  - Stance（市场立场）
  - Rationale（推理过程）
  - Tool Calls（工具调用）
  - Actions（决策动作）
  - Raw Output（原始文本）

### 3. STEP 3: Risk Analysis
- 风险等级和评分

### 4. STEP 4: Trader Agent Decision
- 买卖决策和理由

### 5. STEP 5: Trade Execution
- 实际执行的交易

### 6. STEP 6: Portfolio Status
- 现金、持仓、盈亏

## 📝 每轮循环展示示例

### Round 1: 信息收集

```
[STANCE] neutral

[RATIONALE - Reasoning Process]
  - initial_analysis: NVDA shows positive technical signals, but need more information

[TOOL CALLS - Information Gathering]
  Tool: news_scan
    Why: Need to assess recent news sentiment for NVDA
    Args: {
      "keywords": ["NVDA"],
      "recency_days": 7,
      "max_articles": 10
    }
  Tool: vix_term
    Why: Need to understand volatility structure

[ACTIONS - Decision Process]
  Action: consider_probe
    Why: Need to gather more information before finalizing stance
    Next Checks: ["news_sentiment", "volatility_structure"]

[RAW OUTPUT - Full Text]
  ...完整的 Agent 输出...
```

**系统输出：**
```
[TOOLS_OK] news_scan: 15 hits, queries=['NVDA'], samples=['NVDA earnings...']
[TOOLS_OK] vix_term: VIX=16.5, VIX3M=19.0, ratio=1.15 (contango if >1)
```

### Round 2: 基于工具结果推理

```
[STANCE] bullish

[RATIONALE - Reasoning Process]
  - technical_indicators: NVDA shows strong momentum: RSI=65, MACD positive
  - news_scan: Recent news highly positive: earnings beat, strong AI chip demand
  - vix_term: VIX structure shows contango, indicating stable market sentiment

[TOOL CALLS - Information Gathering]
  (无新工具调用 - 基于 Round 1 的工具结果推理)

[ACTIONS - Decision Process]
  Action: finalize
    Why: Have sufficient information from tools and analysis

[RAW OUTPUT - Full Text]
  ...完整的 Agent 输出...
```

**工具结果已注入（来自 Round 1）：**
```
[TOOLS CONTEXT]
- news_scan: 15 hits, queries=['NVDA'], samples=['NVDA earnings...']
- vix_term: VIX=16.5, VIX3M=19.0, ratio=1.15

⚠️ IMPORTANT: DO NOT call these tools again!
```

## 💾 结果保存

详细结果会保存到：
```
backend/data/logs/full_cycle_detailed.json
```

包含：
- 完整的 discussion transcript
- 所有工具调用历史
- 每轮的 JSON 解析结果
- 最终决策和执行结果

## 📖 更多信息

详细机制说明请参考：
- `docs/DISCUSSION_ROUNDS_EXAMPLE.md` - 完整的轮次机制说明
- `docs/DAILY_ACTION_OUTPUT.md` - 每日最终 Action 输出说明

