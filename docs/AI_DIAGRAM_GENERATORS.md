# 🤖 AI 图表生成工具推荐

## 🎯 可以使用 AI 生成图表的工具

### 1. **Mermaid + AI 辅助** ⭐⭐⭐⭐⭐ (推荐)

**方法**: 使用 AI（如 ChatGPT、Claude、Cursor）生成 Mermaid 代码

**优点**:
- ✅ 完全免费
- ✅ AI 可以直接生成代码
- ✅ 可以使用 Mermaid Live Editor 渲染
- ✅ 可以迭代优化

**使用步骤**:
1. 向 AI 提供你的系统描述（Agent 角色、工作流程等）
2. AI 生成 Mermaid 代码
3. 复制代码到 https://mermaid.live/
4. 预览和导出

**提示词示例**:
```
请帮我生成一个 Mermaid 流程图，描述以下 AI 交易系统：

系统包含以下 Agent：
1. Market Agent - 抓取市场数据
2. Market Analyst - 分析市场
3. Analyst Discussion - 多轮讨论
4. Risk Analyst - 风险评估
5. Trader Agent - 交易决策

工作流程：
Goal → Market Agent → Market Data → Market Analyst → 
Analysis → Analyst Discussion → Consensus → 
Risk Analyst → Risk Report → Trader Agent → Trading Decision → 
Execution → Backend Display → Evaluation → Next Cycle

请生成完整的 Mermaid 代码，包含样式和颜色。
```

---

### 2. **Excalidraw + AI** ⭐⭐⭐⭐

**方法**: 使用 Excalidraw 的 AI 功能（如果有）或让 AI 生成绘制指南

**步骤**:
1. 向 AI 描述你想要的图表
2. AI 生成绘制步骤和元素列表
3. 在 Excalidraw 中按照步骤绘制
4. 或使用 Excalidraw 的模板

---

### 3. **Draw.io + AI 提示词** ⭐⭐⭐⭐

**方法**: 使用 AI 生成 Draw.io 的 XML 结构或绘制指南

**步骤**:
1. 向 AI 描述图表需求
2. AI 生成节点列表、连接关系、布局建议
3. 在 Draw.io 中按照指南创建

---

### 4. **Figma + AI 插件** ⭐⭐⭐⭐⭐ (专业)

**Figma AI 插件**:
- **Diagram AI** - 可以根据文本生成图表
- **Able** - AI 辅助设计工具

**步骤**:
1. 安装 Figma AI 插件
2. 输入系统描述
3. AI 自动生成图表
4. 手动调整和美化

---

### 5. **Microsoft Copilot + Visio** ⭐⭐⭐⭐

**方法**: 使用 Microsoft Copilot 辅助生成 Visio 图表

**步骤**:
1. 在 Microsoft 365 中使用 Copilot
2. 描述图表需求
3. Copilot 辅助生成 Visio 图表

---

## 🎯 最佳方案：使用 AI 生成 Mermaid 代码

### 方案 A: ChatGPT/Claude 生成 Mermaid 代码

**提示词模板**:

```
我是一个 AI 交易系统开发者。请帮我生成一个 Mermaid 流程图代码，描述以下系统：

**Agent 角色**:
1. Market Agent - 负责抓取当日股票数据
2. Market Analyst - 负责分析市场数据
3. Analyst Discussion - 负责多轮讨论，形成共识
4. Risk Analyst - 负责评估当前仓位风险，提出仓位控管报告
5. Trader Agent - 决定买卖（包含买卖那些公司、部位、买进价格、卖出价格等）

**工作流程**:
1. Goal: Daily Trading Decision
2. Market Agent 收集市场数据（股票价格、VIX、指标）
3. Market Analyst 分析市场（技术面、情绪面、推荐股票）
4. Analyst Discussion 多轮讨论（使用工具：news_scan, vix_term, fear_greed）
5. 形成 Discussion Consensus（final_stance, rationale, risk_signals）
6. Risk Analyst 评估风险（输入：市场数据、分析结果、讨论共识、当前持仓）
7. 生成 Risk Report（risk_level, position_risk, Position Control Report）
8. Trader Agent 做交易决策（输入：所有上述信息）
9. 生成 Trading Decision（action: BUY/SELL/HOLD, buy_orders, sell_orders）
10. Execute Orders 执行交易
11. Backend Display 显示损益、交易历史等
12. Evaluation & Feedback 评估和反馈
13. 反馈循环到下一个交易周期

**要求**:
- 使用 Mermaid graph TD 语法
- 包含节点间的连接关系
- 添加合适的样式和颜色
- 节点文本清晰，包含关键信息
- 使用 subgraph 分组相关节点（可选）

请生成完整的 Mermaid 代码，可以直接在 Mermaid Live Editor 中使用。
```

### 方案 B: 直接在 Cursor/AI 中生成

**你已经在使用 Cursor**，可以直接：

1. **在当前对话中**：
   - 我可以直接为你生成或优化 Mermaid 代码
   - 你可以告诉我需要的调整

2. **使用 Cursor 的 AI 功能**：
   - 选中已有的 Mermaid 代码
   - 使用 Cursor 的 AI 优化或修改

---

## 📝 提供给 AI 的系统描述（完整版）

如果你想用其他 AI 工具生成，可以使用以下描述：

```
请生成一个 Mermaid 流程图，描述一个 AI 交易系统的完整工作流程。

**系统概述**:
这是一个多 Agent 协作的 AI 交易系统，包含多个专业 Agent 角色，通过协作完成每日交易决策。

**Agent 角色和职责**:

1. **Market Agent** (市场数据收集)
   - 输入: symbols, start, end
   - 输出: 当日股票数据（OHLCV、指标、VIX等）

2. **Market Analyst** (市场分析)
   - 输入: market_view
   - 输出: 市场分析结果（情绪、信号、推荐股票）

3. **Analyst Discussion** (分析师讨论)
   - 输入: market_view, risk_view
   - 功能: 多轮讨论，使用工具（news_scan, vix_term, fear_greed等）
   - 输出: final_stance, rationale, signals_used, risk_signals

4. **Risk Analyst** (风险评估)
   - 输入: market_json, current_positions, analyst_discussion 风险结果
   - 功能: 评估当前仓位风险
   - 输出: risk_level, position_risk, Position Control Report

5. **Trader Agent** (交易决策)
   - 输入: market_view, risk_view, consensus, current_positions
   - 功能: 综合所有信息做最终交易决策
   - 输出: action (BUY/SELL/HOLD), buy_orders, sell_orders (包含价格和数量)

**工作流程**:
1. Goal: Daily Trading Decision
2. Market Agent → Market Data
3. Market Data → Market Analyst
4. Market Analyst → Market Analysis
5. Market Analysis → Analyst Discussion (多轮，使用工具)
6. Analyst Discussion → Discussion Consensus
7. Discussion Consensus + Market Data + Market Analysis → Risk Analyst
8. Current Portfolio → Risk Analyst (双向)
9. Risk Analyst → Risk Report
10. Risk Report + Consensus + Market Data + Market Analysis → Trader Agent
11. Trader Agent → Trading Decision
12. Trading Decision → Execute Orders
13. Execute Orders → Trade Logger
14. Trade Logger → Backend Display System
15. Backend Display → Evaluation & Feedback
16. Evaluation → Next Trading Cycle (反馈循环到 Market Agent)

**后端系统**:
- P&L Display (损益展示)
- Trade History (交易历史)
- Position Display (仓位展示)
- Risk Metrics (风险指标)
- Performance (绩效统计)

**要求**:
- 使用 Mermaid graph TD 语法
- 包含所有连接关系
- 添加样式和颜色区分不同类型的 Agent
- 节点文本清晰
- 可以使用 subgraph 分组

请生成完整、可直接使用的 Mermaid 代码。
```

---

## 🤖 推荐的 AI 工具组合

### 组合 1: ChatGPT/Claude + Mermaid Live Editor
1. 向 ChatGPT/Claude 提供上面的提示词
2. 获取生成的 Mermaid 代码
3. 复制到 https://mermaid.live/
4. 预览和导出

### 组合 2: Cursor (当前工具) + Mermaid Live Editor
1. 我可以直接为你生成/优化 Mermaid 代码
2. 你可以要求我调整样式、布局、节点等
3. 复制到 Mermaid Live Editor 使用

### 组合 3: Figma AI 插件
1. 安装 Figma AI 插件（如 Diagram AI）
2. 输入系统描述
3. AI 自动生成图表
4. 在 Figma 中进一步美化

---

## 💡 提示词优化建议

### 对于生成 Mermaid 代码的 AI 提示词：

1. **明确说明格式**：
   - "请使用 Mermaid graph TD 语法"
   - "请包含样式定义"

2. **提供具体信息**：
   - Agent 名称和职责
   - 数据流向
   - 关键节点

3. **要求样式**：
   - "请为不同类型的 Agent 使用不同颜色"
   - "请添加合适的样式"

4. **迭代优化**：
   - "请添加更多细节"
   - "请优化布局"
   - "请调整颜色"

---

## 🎯 快速开始

### 如果你想让我（Cursor AI）直接生成：

**只需告诉我**：
- "请帮我优化 Mermaid 流程图"
- "请添加更多细节"
- "请调整颜色方案"
- "请添加特定节点"

我可以直接为你生成或修改代码！

### 如果你想用其他 AI 工具：

1. **复制上面的提示词模板**
2. **粘贴到 ChatGPT/Claude 等 AI 工具**
3. **获取生成的 Mermaid 代码**
4. **使用 Mermaid Live Editor 渲染**

---

**推荐**: 由于你已经在使用 Cursor，我可以直接为你生成、优化或调整 Mermaid 代码！告诉我你想要什么样的图表即可。

