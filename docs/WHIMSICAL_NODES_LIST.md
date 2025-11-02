# 🎯 Whimsical 快速创建节点列表

## 📋 节点列表（可以直接在 Whimsical 中创建）

### 主要节点（按顺序创建）

#### 1. Goal
- **文本**: "Daily Trading Goal"
- **描述**: "Make trading decisions (BUY/SELL/HOLD with positions)"
- **图标**: 🎯 target 或 🏠 house
- **颜色**: 蓝色 (#e1f5ff)

#### 2. Market Agent
- **文本**: "Market Agent"
- **描述**: "Collect Market Data"
- **子节点**: 
  - "Fetch Stock Prices (OHLCV)"
  - "Fetch VIX Data"
  - "Fetch Market Indicators"
  - "Fetch Technical Signals"
- **图标**: 🤖 robot
- **颜色**: 粉色 (#ffe1f5)

#### 3. Market Data
- **文本**: "Market Data"
- **描述**: "Raw market data collected"
- **子节点**:
  - "Stock Prices"
  - "VIX"
  - "Indicators"
- **图标**: 📊 chart
- **颜色**: 浅蓝色

#### 4. Market Analyst
- **文本**: "Market Analyst"
- **描述**: "Analyze Market"
- **子节点**:
  - "Analyze Technical Patterns"
  - "Analyze Market Sentiment"
  - "Generate Recommendations"
  - "Key Observations"
- **图标**: 👤 person
- **颜色**: 粉色 (#ffe1f5)

#### 5. Market Analysis
- **文本**: "Market Analysis"
- **描述**: "Analysis results"
- **子节点**:
  - "Sentiment: bullish/neutral/bearish"
  - "Recommended Stocks"
  - "Key Signals"
- **图标**: 📈 chart-line
- **颜色**: 浅蓝色

#### 6. Analyst Discussion
- **文本**: "Analyst Discussion"
- **描述**: "Multi-Round Consensus Building"
- **子节点**:
  - "Round 1: Initial Consensus"
  - "Round 2: Tool Execution"
  - "Round 3: Final Consensus"
  - "Tools: news_scan, vix_term, fear_greed"
- **图标**: 👥 group
- **颜色**: 绿色 (#e1ffe1)

#### 7. Discussion Consensus
- **文本**: "Discussion Consensus"
- **描述**: "Final consensus from discussion"
- **子节点**:
  - "final_stance"
  - "rationale"
  - "signals_used"
  - "risk_signals"
- **图标**: 💬 speech-bubble
- **颜色**: 绿色

#### 8. Risk Analyst
- **文本**: "Risk Analyst"
- **描述**: "Position Risk Assessment"
- **子节点**:
  - "Evaluate Market Risk"
  - "Evaluate Current Position Risk"
  - "Position Concentration Analysis"
  - "Generate Position Control Report"
- **图标**: 🛡️ shield
- **颜色**: 黄色 (#fff4e1)

#### 9. Portfolio (Current)
- **文本**: "Current Portfolio"
- **描述**: "Current positions and value"
- **子节点**:
  - "Positions"
  - "Cash"
  - "Total Value"
- **图标**: 💰 money
- **颜色**: 紫色

#### 10. Risk Report
- **文本**: "Risk Report"
- **描述**: "Risk assessment results"
- **子节点**:
  - "risk_level"
  - "risk_score"
  - "current_position_risk"
  - "max_position_size"
  - "Position Control Report"
- **图标**: ⚠️ warning
- **颜色**: 黄色

#### 11. Trader Agent
- **文本**: "Trader Agent"
- **描述**: "Trading Decision"
- **子节点**:
  - "Evaluate All Inputs"
  - "Consider Risk Constraints"
  - "Determine BUY/SELL/HOLD"
  - "Calculate Position Sizes"
  - "Set Buy/Sell Prices"
- **图标**: 💼 briefcase
- **颜色**: 粉色 (#ffe1f5)

#### 12. Trading Decision
- **文本**: "Trading Decision"
- **描述**: "Final trading decision"
- **子节点**:
  - "action: BUY/SELL/HOLD"
  - "buy_orders"
  - "sell_orders"
  - "rationale"
- **图标**: ✅ check
- **颜色**: 绿色

#### 13. Execution
- **文本**: "Execute Orders"
- **描述**: "Execute and update portfolio"
- **子节点**:
  - "Execute Buy Orders"
  - "Execute Sell Orders"
  - "Update Portfolio"
  - "Log Trades"
- **图标**: ⚙️ gear
- **颜色**: 灰色

#### 14. Backend Display
- **文本**: "Backend Display System"
- **描述**: "Portfolio & Trade History Display"
- **子节点**:
  - "P&L Display"
  - "Trade History Display"
  - "Position Display"
  - "Risk Metrics Display"
  - "Performance Display"
- **图标**: 🖥️ computer
- **颜色**: 灰色 (#f0f0f0)

#### 15. Evaluation
- **文本**: "Evaluation & Feedback"
- **描述**: "Compare results and generate feedback"
- **子节点**:
  - "Compare Results vs Goal"
  - "Analyze Performance"
  - "Generate Feedback"
  - "Update for Next Cycle"
- **图标**: 🔄 refresh
- **颜色**: 绿色 (#e1ffe1)

---

## 🔗 连接关系（箭头指向）

1. **Goal** → **Market Agent**
2. **Market Agent** → **Market Data**
3. **Market Data** → **Market Analyst**
4. **Market Analyst** → **Market Analysis**
5. **Market Analysis** → **Analyst Discussion**
6. **Analyst Discussion** → **Discussion Consensus** (循环箭头)
7. **Discussion Consensus** → **Risk Analyst**
8. **Market Data** → **Risk Analyst**
9. **Market Analysis** → **Risk Analyst**
10. **Portfolio (Current)** → **Risk Analyst** (双向)
11. **Risk Analyst** → **Risk Report**
12. **Risk Report** → **Trader Agent**
13. **Discussion Consensus** → **Trader Agent**
14. **Market Data** → **Trader Agent**
15. **Market Analysis** → **Trader Agent**
16. **Trader Agent** → **Trading Decision**
17. **Trading Decision** → **Execution**
18. **Execution** → **Backend Display**
19. **Backend Display** → **Evaluation**
20. **Evaluation** → **Market Agent** (反馈循环)

---

## 🎨 分组建议

### Group 1: Data Collection Layer
- Market Agent
- Market Data

### Group 2: Analysis Layer
- Market Analyst
- Market Analysis
- Analyst Discussion
- Discussion Consensus

### Group 3: Risk Management Layer
- Risk Analyst
- Portfolio (Current)
- Risk Report

### Group 4: Decision Layer
- Trader Agent
- Trading Decision

### Group 5: Execution Layer
- Execution

### Group 6: Display Layer
- Backend Display

---

## 📝 快速创建步骤

### 在 Whimsical 中：

1. **创建 Flowchart**
   - 打开 Whimsical
   - 点击 "Create" → "Flowchart"

2. **添加节点**（按列表顺序）
   - 点击 "+" 添加节点
   - 输入文本（从上面的列表复制）
   - 添加图标（点击图标按钮，搜索建议的关键词）
   - 设置颜色

3. **连接节点**（按连接关系列表）
   - 选中节点，从连接点拖拽到目标节点

4. **分组**（可选）
   - 选中相关节点 → 右键 → "Group"

5. **美化**
   - 调整节点大小
   - 调整颜色
   - 调整箭头样式

6. **导出**
   - 点击右上角 "Share" → "Export" → 选择格式（PNG/SVG/PDF）

---

## 🎯 图标关键词搜索建议

在 Whimsical 图标搜索中：

| Agent | 搜索关键词 | 备选关键词 |
|-------|-----------|-----------|
| Goal | "target", "goal", "flag" | "trophy", "star" |
| Market Agent | "robot", "android" | "machine", "automation" |
| Market Data | "chart", "graph", "data" | "database", "server" |
| Market Analyst | "person", "user", "analyst" | "professional", "business" |
| Market Analysis | "chart-line", "analysis" | "graph", "trend" |
| Analyst Discussion | "group", "team", "people" | "meeting", "conversation" |
| Risk Analyst | "shield", "security" | "protection", "warning" |
| Portfolio | "money", "wallet", "cash" | "bank", "investment" |
| Trader Agent | "briefcase", "business" | "trader", "executive" |
| Execution | "gear", "settings", "action" | "process", "workflow" |
| Backend Display | "computer", "monitor", "screen" | "dashboard", "display" |
| Evaluation | "refresh", "loop", "cycle" | "arrow", "repeat" |

---

**使用提示**: 复制上面的节点文本，在 Whimsical 中快速创建！

