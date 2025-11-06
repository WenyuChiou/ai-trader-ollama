# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe (118+ symbols) with comprehensive market analysis  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously  
> 🎨 **NEW**: Dark tech-themed UI with real-time data visualization

---

## 📚 Table of Contents

- [Latest Updates](#-latest-updates-november-2025)
- [Quick Start](#-quick-start)
- [Dark Tech UI Features](#-dark-tech-ui-features)
- [Agent System](#-agent-system)
- [Available Tools](#-available-tools)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration-settings)
- [Testing](#-backend-testing)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)

---

## 🆕 Latest Updates (November 2025)

### 🎨 Dark Tech UI Redesign
- **Deep dark theme** with cyan accent colors (#22d3ee)
- **Glassmorphism effects** with backdrop blur
- **Neon glow animations** on hover and active states
- **Gradient borders** for conversations and cards
- **Quick Navigation bar** with smooth scroll to sections
- **VIX Term Structure card** with risk indicator
- **Highlighted Cash display** with special emphasis
- **Real-time status indicators**:
  - Market Status (Open/Closed)
  - Agent Activity (Running/Idle)
  - Order Status (Pending/Filled counts)

### 🤖 Enhanced Agent System
- **ALL 118 stocks analyzed** (previously limited to 5)
- **Expanded tool suite**:
  - Economic indicators (FRED API)
  - Extended technical indicators (15+ indicators)
  - News scanning (20 articles)
  - Market sentiment analysis
- **Multi-round discussions** with tool auto-invocation
- **Historical memory integration** (past 5 trading days)

### 📊 Data & Visualization
- **Real-time portfolio tracking** with yfinance
- **Equity curve chart** (Chart.js) with linear/log scale
- **Portfolio distribution pie chart**
- **Live unrealized P&L** calculation
- **VIX term structure monitoring**

### ⚙️ Backend Improvements
- **Trade cooldown management** (24-hour per symbol)
- **Position limit enforcement** (max 15% per stock)
- **Pending order execution** with price range triggers
- **Comprehensive logging** for all operations

---

## 🚀 Quick Start

### Prerequisites

**Backend:**
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start Ollama service (keep it running)
ollama serve

# Pull LLM model (in another terminal)
ollama pull llama3.1
```

**Environment Variables:**
```bash
# Optional: Add FRED API key for economic data
export FRED_API_KEY=your_api_key_here
```

**Frontend:**
- No Node.js required! Frontend is pure HTML/CSS/JS
- Just need Python's HTTP server

### Initialize Data

```bash
cd backend
python scripts/init_data.py
```

This creates:
- Portfolio state (initial cash: $10,000)
- Memory directory structure  
- Trading log files

### Start the System

**Terminal 1: Backend API**
```bash
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2: Frontend Server**
```bash
cd frontend
python -m http.server 3000
```

**Terminal 3: (Optional) Ollama**
```bash
ollama serve
```

### Access the Dashboard

Open your browser and navigate to:
```
http://localhost:3000/monitor.html
```

---

## 🎨 Dark Tech UI Features

### 🧭 Quick Navigation
- **6 Section Buttons**: Summary | Chart | Holdings | Conversations | Execution | Trade History
- Smooth scroll behavior
- Active state highlighting with cyan gradient
- Glassmorphism background

### 📊 Summary Cards
1. **Total Portfolio Value** - with percentage change
2. **Available Cash** - highlighted with neon glow
3. **Total P&L** - color-coded (green/red)
4. **Equity Value** - with position count
5. **VIX Term Structure** - displays VIX, VIX 3M, Ratio, Risk Score

### 📈 Interactive Charts
- **Equity Curve**: Total asset value over time (linear/log scale toggle)
- **Portfolio Distribution**: Pie chart by market value
- Powered by Chart.js

### 💬 Conversation Display
- Gradient borders with cyan glow
- Agent tags with neon effect
- Formatted content with proper spacing
- Round indicators and tool results
- Real-time conversation streaming

### 📋 Tables & Data
- **Holdings**: Current positions with live prices
- **Execution Details**: Pending and filled orders
- **Trade History**: Complete transaction log
- Dark theme with cyan accents
- Status badges (PENDING, FILLED, REJECTED, CANCELLED)

---

## 🤖 Agent System

### Core Agents

#### 1. **DiscussionAgent** 📢
- **Role**: Multi-round discussion coordinator
- **Tools**: news_scan, vix_term, fear_greed, economic indicators, technical analysis
- **Process**:
  1. Analyzes market view (all 118 stocks)
  2. Invokes tools based on information needs
  3. Discusses findings across 3 rounds
  4. Determines final stance (bullish/neutral/bearish)
  5. Recommends specific stocks

#### 2. **RiskAnalyst** 🛡️
- **Role**: Portfolio risk assessment
- **Analysis**:
  - Position concentration
  - VIX regime evaluation
  - Drawdown risk
  - Diversification metrics
- **Output**: Risk report with action suggestions

#### 3. **TraderAgent** 💼
- **Role**: Trade execution decisions
- **Inputs**: Discussion consensus + Risk report + VIX data
- **Decisions**:
  - BUY: With limit price and quantity
  - HOLD: Maintain current positions
  - SELL: Exit positions

### Virtual Agents (Data Aggregators)

These are constructed in `trading_cycle.py` for frontend display:

- **MarketAnalyst**: Technical indicator aggregation
- **FundamentalAnalyst**: News and economic data
- **TechnicalAnalyst**: Signal score calculation
- **SentimentAnalyst**: Market sentiment synthesis

### Conversation Flow

```
1. Market Data Fetch (yfinance)
   ↓
2. MarketAnalyst: Evaluate ALL stocks → recommend top candidates
   ↓
3. DiscussionAgent: Multi-round discussion with tool usage
   - Round 1: Initial assessment + tool calls
   - Round 2: Process tool results + additional tools if needed
   - Round 3: Final consensus
   ↓
4. RiskAnalyst: Assess current portfolio risk
   ↓
5. TraderAgent: Make BUY/HOLD/SELL decisions
   ↓
6. Order Execution: Create/fill orders based on market status
```

### 🔄 Multi-Round Discussion Flow (Detailed)

```
START
 │
 ├─→ [INPUT] Market View (118 stocks with technical indicators)
 │    • NVDA: RSI=65, MACD=+2.3, signal_score=4.5
 │    • AAPL: RSI=58, MACD=+1.1, signal_score=3.8
 │    • ... (all 118 stocks)
 │
 ├─→ [ROUND 1] Initial Assessment (Exploration Phase)
 │    │
 │    ├─ Agent Reasoning:
 │    │   "I see strong signals for NVDA, but need to verify:
 │    │    1. What is the VIX risk level?
 │    │    2. Any recent news on NVDA?
 │    │    3. What's the Fear & Greed Index?"
 │    │
 │    ├─ Output JSON:
 │    │   {
 │    │     "stance": "need_more_info",
 │    │     "tool_calls": [
 │    │       {"name": "vix_term", "args": {}},
 │    │       {"name": "news_scan", "args": {"keywords": ["NVDA", "nvidia"]}},
 │    │       {"name": "fear_greed", "args": {}}
 │    │     ]
 │    │   }
 │    │
 │    └─→ System Executes Tools:
 │         ✅ vix_term → VIX=18.0, VIX3M=20.6, ratio=1.1 (Contango)
 │         ✅ news_scan → Found 15 news articles
 │         ✅ fear_greed → Index=55 (Greed)
 │         
 │         Virtual Agents Log:
 │         → MarketAnalyst: "Technical signals strong"
 │         → FundamentalAnalyst: "News mostly positive"
 │         → SentimentAnalyst: "Market greed level moderate"
 │
 ├─→ [ROUND 2] Deep Analysis (Validation Phase)
 │    │
 │    ├─ Agent Reasoning (with new information):
 │    │   "Good, now I know:
 │    │    - VIX=18 is moderate, not high risk
 │    │    - NVDA news is positive (AI demand strong)
 │    │    - Market sentiment at 55, optimistic but not overheated
 │    │    Still want to check economic fundamentals..."
 │    │
 │    ├─ Output JSON:
 │    │   {
 │    │     "stance": "leaning_bullish",
 │    │     "tool_calls": [
 │    │       {"name": "get_unemployment", "args": {}},
 │    │       {"name": "get_treasury_yields", "args": {}}
 │    │     ]
 │    │   }
 │    │
 │    └─→ System Executes Tools:
 │         ✅ get_unemployment → 3.8% (Low, strong economy)
 │         ✅ get_treasury_yields → 4.25% (Moderate)
 │         
 │         Virtual Agents Log:
 │         → FundamentalAnalyst: "Economic data supports growth"
 │         → RiskAnalyst: "Risk metrics within acceptable range"
 │
 └─→ [ROUND 3] Final Decision (Consensus Phase)
      │
      ├─ Agent Reasoning (comprehensive analysis):
      │   "Comprehensive Analysis:
      │    ✅ Technical: NVDA, AAPL, MSFT showing strong signals
      │    ✅ Fundamental: Economic data is solid
      │    ✅ Sentiment: Market optimistic but not euphoric
      │    ✅ Risk: VIX moderate, manageable
      │    → DECISION: BULLISH"
      │
      ├─ Output JSON (Final Consensus):
      │   {
      │     "stance": "bullish",
      │     "recommended_stocks": ["NVDA", "AAPL", "MSFT", "GOOGL"],
      │     "rationale": [
      │       "Strong technical indicators, signal scores > 4.0",
      │       "Positive market sentiment, Fear & Greed at 55",
      │       "Solid economic data, unemployment at 3.8%",
      │       "VIX=18 moderate, acceptable risk level"
      │     ],
      │     "confidence": 0.85,
      │     "tool_budget_used": 5,
      │     "actions": [{"type": "finalize"}]
      │   }
      │
      └─→ Discussion Complete → Proceed to RiskAnalyst
```

### Key Mechanisms

**Tool Budget System:**
- Total budget: 8 tool calls per discussion
- Round 1 typically uses: 3 calls
- Round 2 typically uses: 2 calls  
- Round 3 typically uses: 1 call
- Prevents infinite loops, ensures efficiency

**Early Termination:**
- If `finalize` action detected + minimum tools used (3)
- Agent can end discussion before Round 3 if confident
- Saves time while ensuring information adequacy

**Virtual Agents:**
Virtual agents are data aggregators (not LLM-based) constructed for frontend display:
- **MarketAnalyst**: Aggregates technical indicator data
- **FundamentalAnalyst**: Compiles news and economic data
- **TechnicalAnalyst**: Calculates signal scores
- **SentimentAnalyst**: Synthesizes market sentiment
- **ToolSystem**: Logs all tool executions

---

## 🛠️ Available Tools

### Market Data Tools
- `fetch_market_batch`: OHLCV + indicators for multiple symbols
- `vix_term`: VIX term structure (VIX, VIX3M, ratio)
- `fear_greed`: CNN Fear & Greed Index
- `check_market_open`: Market hours validation

### News & Sentiment
- `news_scan`: Multi-query news search (DuckDuckGo) - up to 20 articles
- `plan_and_scan_news`: Automatic news query generation

### Technical Analysis
- `rsi`: Relative Strength Index
- `macd`: MACD with signal line
- `bollinger_bands`: Bollinger Bands (upper, middle, lower)
- `adx`: Average Directional Index
- `stochastic`: Stochastic Oscillator
- `roc`: Rate of Change
- `williams_r`: Williams %R
- `atr`: Average True Range
- `obv`: On-Balance Volume
- `mfi`: Money Flow Index
- `vwap`: Volume Weighted Average Price
- `pivot_points`: Support/Resistance levels
- `ichimoku`: Ichimoku Cloud components

### Economic Indicators (FRED API)
- `get_unemployment`: Unemployment rate
- `get_inflation`: CPI data
- `get_gdp`: GDP growth
- `get_treasury_yields`: 10Y Treasury yield
- `get_fed_funds`: Federal Funds Rate

### Trading Tools
- `assess_trend`: Trend classification (uptrend/downtrend/neutral)
- `vix_regime`: VIX level classification (low/normal/elevated/spike)
- `vix_risk_score`: VIX risk score (0-10)

---

## 🌐 API Endpoints

### Portfolio
- `GET /api/portfolio/current` - Current portfolio snapshot
- `GET /api/portfolio/real-time` - Real-time with market prices
- `GET /api/portfolio/equity-history` - Historical equity curve
- `GET /api/portfolio/recent-snapshots` - Recent snapshots (last 24h)

### Trading
- `POST /api/trading/execute-trade` - Execute trading cycle
- `GET /api/trading/trades` - Get all trades
- `GET /api/trading/filled-orders` - Get filled orders only

### Market Data
- `GET /api/vix/term` - VIX term structure
- `POST /api/tools/{tool_name}` - Execute specific tool

### Conversations
- `GET /api/conversations/` - Get all conversations
- `GET /api/conversations/latest` - Get latest conversation

---

## ⚙️ Configuration Settings

### Stock Universe (`config/config.json`)

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", ...
    // Total: 118 symbols (stocks + ETFs)
  ],
  "inverse_etfs": ["SQQQ", "SPXU", "SH", "PSQ", "SDS", "DOG", "SOXS"],
  "leveraged_etfs": ["TQQQ", "SOXL", "UPRO", "TNA", "FAS", ...],
  "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", ...],
  
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,  // Max 15% per stock
  "position_limit_total": 0.85,      // Max 85% total invested
  
  "discussion_rounds": 3,
  "discussion_tool_budget": 8,       // Max tool calls per discussion
  
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434",
    "timeout_seconds": 8.0
  }
}
```

### Agent Configuration (`config/agents.yaml`)

```yaml
discussion_agent:
  model: llama3.1
  temperature: 0.7
  max_rounds: 3

risk_analyst:
  model: llama3.1
  temperature: 0.5

trader_agent:
  model: llama3.1
  temperature: 0.3
  max_positions: 10
```

---

## 🧪 Backend Testing

### Run All Scenarios
```bash
cd backend
python scripts/test_all_scenarios.py
```

Tests:
1. **Trading Hours**: Execute during market open
2. **Non-Trading Hours**: Test pending order creation
3. **Multi-Day Flow**: Verify record persistence

### Run API Tests
```bash
cd backend
python scripts/test_backend_api.py
```

Validates:
- Portfolio endpoints
- Trading execution
- Conversation retrieval
- Tool invocation

### Manual Testing
```bash
cd backend
python test_api_updates.py
```

Checks:
- yfinance data freshness
- Real-time portfolio updates
- Equity history persistence
- VIX data retrieval

---

## 📁 Project Structure

```
ai-trader-ollama/
├── backend/
│   ├── src/
│   │   ├── agents/           # Core agent implementations
│   │   │   ├── analyst_discussion.py  # DiscussionAgent
│   │   │   ├── risk_analyst.py        # RiskAnalyst
│   │   │   └── trader_agent.py        # TraderAgent
│   │   ├── api/              # FastAPI server
│   │   │   └── server.py
│   │   ├── data/             # Data management
│   │   │   ├── market_data.py         # yfinance wrapper
│   │   │   ├── portfolio.py           # Portfolio tracking
│   │   │   ├── trade_history_tracker.py  # Cooldown management
│   │   │   └── order_executor.py      # Order execution
│   │   ├── orchestrator/     # Trading logic
│   │   │   └── trading_cycle.py       # Main trading flow
│   │   ├── tools/            # All trading tools
│   │   │   ├── market_tools.py        # Market data tools
│   │   │   ├── news_tools.py          # News scanning
│   │   │   ├── economic_indicators.py # FRED API
│   │   │   ├── ta_indicators.py       # Technical indicators
│   │   │   └── analysis_tools.py      # Analysis helpers
│   │   └── llm/              # LLM client
│   │       └── ollama_client.py
│   ├── scripts/              # Utility scripts
│   ├── data/logs/            # Trading logs
│   └── requirements.txt
├── frontend/
│   └── monitor.html          # Main dashboard (3700+ lines)
├── config/
│   ├── config.json           # System configuration
│   └── agents.yaml           # Agent settings
├── prompts/                  # Agent prompts
└── docs/                     # Documentation
```

---

## 📖 Documentation

### Key Documents
- [AGENTS.md](docs/AGENTS.md) - Detailed agent architecture
- [TOOLS.md](docs/TOOLS.md) - Complete tool reference
- [INFORMATION_FLOW_COMPLETE.md](docs/INFORMATION_FLOW_COMPLETE.md) - Data flow diagrams
- [TRADING_HOURS_LOGIC.md](backend/docs/TRADING_HOURS_LOGIC.md) - Market hours handling

### Testing Guides
- [TESTING_AND_DATA_PERSISTENCE.md](backend/docs/TESTING_AND_DATA_PERSISTENCE.md)
- [TESTING_GUIDE.md](backend/docs/TESTING_GUIDE.md)

---

## 🐛 Troubleshooting

### Issue: Portfolio shows $0
**Solution**: Run initialization
```bash
cd backend
python scripts/init_data.py
```

### Issue: No conversations appearing
**Solution**: Execute a trading cycle
```bash
# Via API
curl -X POST http://localhost:8000/api/trading/execute-trade

# Or via UI
Click "Start Trading" button
```

### Issue: yfinance errors
**Solution**: Check market hours and date range
```python
# Market must be open or use historical dates
start = "2025-11-01"
end = "2025-11-05"
```

### Issue: Ollama connection refused
**Solution**: Ensure Ollama is running
```bash
ollama serve
```

### Issue: Unicode errors in logs
**Solution**: Set environment encoding
```bash
# Windows PowerShell
$env:PYTHONIOENCODING="utf-8"

# Linux/Mac
export PYTHONIOENCODING=utf-8
```

---

## 🤝 Contributing

This is a research project. Feel free to fork and experiment!

Key areas for contribution:
- Additional technical indicators
- Alternative LLM backends
- Enhanced risk models
- Backtesting framework
- Performance optimization

---

## 📜 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **LangChain**: Agent framework and tool abstractions
- **Ollama**: Local LLM serving
- **yfinance**: Market data
- **FastAPI**: High-performance API
- **Chart.js**: Interactive charts
- **FRED API**: Economic indicators

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review [Documentation](#-documentation)
3. Open an issue on GitHub

---

**Built with ❤️ for autonomous trading research**

*Disclaimer: This is an educational project. Not financial advice. Trade at your own risk.*
