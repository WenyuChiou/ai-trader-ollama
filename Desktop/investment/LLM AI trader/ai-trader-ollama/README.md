# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe with hedging and leveraged ETF support  
> 🧠 **8+ Specialized Agents** that analyze, discuss, and decide — entirely autonomously  
> ✨ **Modern Neon Cyberpunk UI** with real-time data visualization and glassmorphism effects

---

## 📚 Table of Contents

- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [API Startup & Shutdown](#-api-startup--shutdown)
- [Backend Testing](#-backend-testing)
- [Configuration Settings](#-configuration-settings)
- [Frontend Testing](#-frontend-testing)
- [Agent System](#-agent-system)
- [Available Tools](#-available-tools)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

---

## ✨ Key Features

### 🎨 Modern Neon Cyberpunk UI Design

**Visual Design:**
- 🌌 **Dynamic Background**: Deep space gradient with animated neon grid
- 💎 **Glassmorphism Effects**: Translucent cards with backdrop blur and color saturation
- 🌈 **Neon Gradients**: Cyan (`#00f5ff`) and Purple (`#a855f7`) color scheme throughout
- ✨ **Glow Effects**: Multi-layer text shadows and neon borders on interactive elements
- 🎭 **3D Hover Effects**: Cards lift up and scale with animated gradient borders

**Data Visualization:**
- 📊 **Real-time Charts**: Equity curves with neon glow effects and smooth animations
- 💰 **Glowing Numbers**: Large currency values with cyan/purple text shadows
- 📈 **Live Indicators**: Status dots with pulsing animations for market and agent status
- 🎯 **Smart Tables**: Gradient headers, hover effects with left neon accent bars

**Interaction Design:**
- 🔘 **Neon Buttons**: Gradient backgrounds with light sweep animations on hover
- 🏷️ **Status Badges**: Glowing pills with semantic colors (green/orange/gray)
- 💬 **Conversation Cards**: Glassmorphic containers with left gradient accent bars
- ⚡ **Smooth Transitions**: 0.3-0.4s cubic-bezier easing for all animations

**Typography & Formatting:**
- 🔢 **Precision Display**: All numbers rounded to 1 decimal place for clarity
- 📏 **Enhanced Spacing**: Larger padding and margins for better readability
- 🎨 **Gradient Text**: Major headings use cyan-to-purple gradient text
- ✍️ **Modern Fonts**: System font stack with tabular numbers for data consistency

### 🤖 Advanced Multi-Agent System

**8 Specialized Trading Agents:**
1. **MarketAnalyst** 📊
   - Analyzes entire universe (72+ stocks) technical indicators
   - Generates market sentiment and key observations
   - Identifies trending stocks and market patterns

2. **FundamentalAnalyst** 📈
   - Evaluates fundamental data and earnings
   - Synthesizes company sentiment analysis
   - Provides long-term value assessments

3. **TechnicalAnalyst** 📉
   - Calculates RSI, MACD, Bollinger Bands
   - Generates technical signal scores
   - Identifies top trading opportunities

4. **SentimentAnalyst** 😊
   - Monitors Fear & Greed Index (CNN)
   - Tracks VIX term structure (VIX vs VIX3M)
   - Calculates VIX risk scores
   - Assesses market emotional state

5. **DiscussionAgent** 💬
   - Conducts multi-round analysis (3 rounds default)
   - Automatically calls 20+ tools for data gathering
   - Synthesizes all information into actionable insights
   - Provides detailed reasoning and stance

6. **RiskAnalyst** ⚠️
   - Evaluates portfolio concentration
   - Checks position limit compliance
   - Generates risk warnings and diversification advice
   - Calculates overall risk scores

7. **TraderAgent** 💼
   - Makes final BUY/SELL decisions
   - Calculates optimal position sizes
   - Sets price bands for limit orders
   - Generates detailed trade rationale

8. **ToolSystem** 🔧
   - Logs all tool usage (news, VIX, Fear & Greed, etc.)
   - Tracks data source reliability
   - Records API call timestamps

**Agent Intelligence:**
- 🧠 **Autonomous Operation**: Agents make decisions without human intervention
- 🔄 **Continuous Learning**: Each cycle builds on historical context
- 🤝 **Collaborative Analysis**: Agents share insights through discussion rounds
- 📊 **Tool Integration**: Automatic access to 20+ market data and news tools
- 💾 **Memory System**: All conversations saved to `discussion_actions.jsonl`

### 🛠️ 20+ Integrated Tools

**Market Data:**
- `fetch_market_batch`: Batch OHLCV + technical indicators for full universe
- `vix_term`: VIX term structure analysis (contango/backwardation)
- `vix_close`: Historical VIX data for volatility analysis
- `fear_greed`: CNN Fear & Greed Index (0-100 scale)

**News & Intelligence:**
- `news_scan`: Multi-source news aggregation (Reuters, WSJ, FT, etc.)
- `plan_and_scan_news`: LLM-powered intelligent news planning
- `web_search`: DuckDuckGo search with domain whitelist
- `fetch_url`: Full article content extraction

**Crypto Analysis:**
- `fetch_crypto_batch`: Batch cryptocurrency data and indicators
- `get_crypto_price`: Real-time crypto prices

**Agent Features:**
- 🎯 **Auto Tool Selection**: LLM chooses relevant tools based on context
- 📊 **Tool Budget**: 20 calls per cycle (configurable)
- 🔄 **Smart Caching**: Reduces redundant API calls
- 📝 **Full Logging**: All tool calls recorded in conversation history

### 📈 Trading Features

**Position Management:**
- 💰 Initial Cash: $10,000 (configurable)
- 📊 Position Limits: Per-stock (15%), Total (85%)
- 🎯 Minimum Position: 3% per stock
- 🔄 Auto Rebalancing: Based on risk analysis

**Order Types:**
- 📍 **Limit Orders**: Price bands (min/max) for better execution
- ⏱️ **Pending Orders**: Hold overnight, execute during market hours
- ✅ **Filled Orders**: Complete history with timestamps
- 📊 **Order Status**: Real-time tracking (PENDING → FILLED)

**Risk Management:**
- ⚠️ **Real-time Risk Scores**: Continuous risk evaluation
- 🎯 **Position Concentration Alerts**: Warns of over-exposure
- 📊 **VIX Risk Integration**: Volatility-based position sizing
- 🛡️ **Hedging Support**: Inverse ETFs (SQQQ, SPXU, SH, etc.)
- ⚡ **Leveraged ETF Control**: Moderate use with strict limits

**Trading Schedule:**
- 🌅 **Market Hours**: Auto-detect US market open/close
- ⏰ **Auto Trading**: Configurable intervals (default 30 min)
- 📅 **Pre-planning**: Off-hours planning for next trading day
- 📊 **Historical View**: Charts and conversations visible 24/7

### 📊 Data Persistence

**Complete Record Keeping:**
- 💾 `portfolio_state.json`: Current holdings and cash
- 📈 `equity_history.jsonl`: Daily equity snapshots with timestamps
- 💬 `discussion_actions.jsonl`: All agent conversations and tool calls
- 📋 `pending_orders.jsonl`: Unfilled orders awaiting market hours
- ✅ `filled_orders.jsonl`: Complete trade execution history
- 📊 `real_time_snapshots.jsonl`: Intraday portfolio snapshots

**Data Features:**
- ⏱️ **Multi-record per Day**: Track intraday changes (every 30s or 0.5% change)
- 🔄 **Auto Persistence**: Never lose data except on initialization
- 📊 **Historical Charts**: Full equity curve with zoom and pan
- 💾 **Memory System**: Agents reference past decisions

---

## 🚀 Quick Start

### 5-Day Live Trading Test

For running a 5-day live trading test with automatic market hours management:

```powershell
cd backend\scripts
.\start_api_market_hours.ps1
```

This will:
- ✅ Automatically start API at market open (9:30 AM EST)
- ✅ Automatically stop API at market close (4:00 PM EST)
- ✅ Skip weekends automatically
- ✅ Run for 5 consecutive trading days

For scheduling details and scripts, see [Backend Scripts](backend/README.md#-scripts).

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

**Frontend:**
- No Node.js required! Frontend is pure HTML
- Just need Python's HTTP server

### Initialize Data

```bash
cd backend
python scripts/init_data.py
```

This will create:
- Portfolio state (initial cash: $10,000)
- Memory directory structure
- Trading log files

---

## 🔧 API Startup & Shutdown

### Starting the API

#### Method 1: PowerShell Script (Windows - Recommended)

```powershell
cd backend\scripts
.\start_api_background.ps1
```

This opens a new PowerShell window running the API. **Keep this window open** - closing it will stop the API.

#### Method 2: Manual Start

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

**Keep this terminal window open** - closing it (or pressing `Ctrl+C`) will stop the API.

#### Method 3: Background Run (PowerShell, Optional)

```powershell
cd backend
Start-Job -ScriptBlock { 
    Set-Location "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
    python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 
}

# Check status
Get-Job

# View output
Receive-Job <JobId>

# Stop
Stop-Job <JobId>
Remove-Job <JobId>
```

### Verifying API is Running

**Test health check endpoint:**
```powershell
curl http://localhost:8000/
```

**Expected response:**
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

**Check port usage:**
```powershell
netstat -ano | findstr ":8000"
```

You can also manually test key endpoints using curl as shown below.

### Stopping the API

#### If using script start (Method 1)

**Simple method:**
- Close the PowerShell window showing API logs
- API will automatically stop

**If window is closed/minimized:**
```powershell
# Find and terminate process
cd backend\scripts
.\check_port.ps1
# Follow prompts, or manually:
taskkill /PID <PID> /F
```

#### If manually started (Method 2)

**In the terminal running API:**
- Press `Ctrl + C` to gracefully stop
- Or directly close the terminal window

#### Verify API has stopped

```powershell
# Should show empty (port not in use)
netstat -ano | findstr ":8000"

# Or test connection (should fail)
curl http://localhost:8000/
```

### Restarting the API

If you encounter issues, you can use the restart script:

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

Or manually:
```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
```

**Note**: If you encounter PowerShell execution policy errors, use `restart_api_bypass.ps1`.

---

## 🧪 Backend Testing

### Quick Test

```bash
cd backend
python test_api.py
```

**Expected output:**
```
✅ PASS - Portfolio Initialization
✅ PASS - Portfolio State File
✅ PASS - API Server Imports
✅ All tests passed! Backend is ready.
```

### Full Test Suite

```bash
cd backend

# Run all tests
python tests/run_all.py

# Run specific tests
python test_full_workflow.py
python test_october_simulation_full.py
```

### API Endpoint Testing

**Test all endpoints:**
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

**Manual test key endpoints:**
```powershell
# Health check
curl http://localhost:8000/

# Real-time portfolio
curl http://localhost:8000/api/portfolio/real-time

# Tools list
curl http://localhost:8000/api/tools/list

# Agent conversations
curl http://localhost:8000/api/agents/conversations?limit=10

# Trade records
curl http://localhost:8000/api/trades/recent?limit=10
```

### Test Trading Cycle

```bash
cd backend
python test_full_workflow.py
```

This will test:
- Market data fetching
- Agent analysis
- Tool calls
- Trading decisions
- Conversation logging

### Test October Simulation

```bash
cd backend
python test_october_simulation_full.py
```

This will test the complete October historical simulation flow.

---

## ⚙️ Configuration Settings

### Main Configuration File: `backend/config/config.json`

#### Basic Configuration

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", "AVGO", "TSLA",
    ...
  ],
  
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03
}
```

**Key Parameters:**

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `universe` | Stock pool list | - | 72 stocks (configured) |
| `initial_cash` | Initial cash | 10000 | Adjust as needed |
| `position_limit_per_stock` | Max position per stock | 0.15 (15%) | 0.10-0.20 |
| `position_limit_total` | Total position limit | 0.85 (85%) | 0.80-0.90 |
| `position_limit_min_per_stock` | Min position per stock | 0.03 (3%) | 0.02-0.05 |

#### Inverse ETF Configuration (Hedging)

```json
{
  "inverse_etfs": [
    "SQQQ",  // 3x Inverse NASDAQ
    "SPXU",  // 3x Inverse S&P 500
    "SH",    // 1x Inverse S&P 500
    "PSQ",   // 1x Inverse QQQ
    "SDS",   // 2x Inverse S&P 500
    "DOG",   // 1x Inverse Dow Jones
    "SOXS"   // 3x Inverse Semiconductor ETF
  ]
}
```

**Use Cases:**
- VIX > 20 (high volatility)
- Bearish market sentiment but want to protect long positions
- Technical indicators suggest market reversal

#### Leveraged ETF Configuration (Use Moderately)

```json
{
  "leveraged_etfs": [
    "TQQQ",  // 3x Leveraged NASDAQ
    "SOXL",  // 3x Leveraged Semiconductor
    "UPRO",  // 3x Leveraged S&P 500
    "TNA",   // 3x Leveraged Small Cap
    "FAS",   // 3x Leveraged Financials
    "CURE",  // 3x Leveraged Healthcare
    "LABU",  // 3x Leveraged Biotech
    "TECL",  // 3x Leveraged Technology
    "TMF",   // 3x Leveraged 20+ Year Treasury
    "EDC"    // 3x Leveraged Emerging Markets
  ]
}
```

**Use Cases:**
- Strong bullish trend (clear uptrend)
- VIX < 15 (low volatility)
- Strong technical indicators (RSI < 70, bullish MACD)

**Position Limits:**
- Single leveraged ETF: Max 5-10% of portfolio value
- Total leveraged ETF positions: Max 20-30% of portfolio value

#### Market Index Configuration (Technical Analysis Reference)

```json
{
  "market_indices": [
    "^GSPC",  // S&P 500
    "^IXIC",  // NASDAQ Composite
    "^DJI"    // Dow Jones Industrial Average
  ]
}
```

These indices are used for Agent technical analysis but do not participate in trading.

#### LLM Configuration

```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `default_model` | Default LLM model | "llama3.1" |
| `ollama_host` | Ollama server address | "http://localhost:11434" |
| `auto_pull` | Auto-download missing models | true |
| `timeout_seconds` | Request timeout | 8.0 |

#### Discussion Configuration

```json
{
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 20
}
```

**Parameters:**

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `discussion_rounds` | Number of discussion rounds | 3 | 3-5 |
| `discussion_auto_tools` | Auto tool calls | true | true |
| `discussion_tool_budget` | Tool call budget | 20 | 15-25 |

#### Preferred Domains Configuration

```json
{
  "preferred_domains": [
    "www.cboe.com",
    "www.wsj.com",
    "www.reuters.com",
    "www.ft.com",
    "www.cmegroup.com",
    "fred.stlouisfed.org",
    "home.treasury.gov"
  ]
}
```

These domains are used for news searches to ensure reliable information sources.

#### Cryptocurrency Configuration (Optional)

```json
{
  "crypto": [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    ...
  ]
}
```

**Note**: Cryptocurrencies are currently only used for analysis and do not participate in trading.

---

## 🌐 Frontend Testing

### Starting Frontend Server

**Method 1: Python HTTP Server (Recommended)**

```bash
cd frontend
python -m http.server 8080
```

**Then open browser:** `http://127.0.0.1:8080/monitor.html`

**Method 2: PowerShell Script (Windows)**

```powershell
cd frontend
.\start_frontend_server.ps1
```

### Verifying Frontend Connection

**Check connection status:**
- ✅ Green dot + "Connected": API is running
- ❌ Red dot + "Disconnected": API is not running or connection error

**Check functionality:**

1. **Portfolio Data**
   - ✅ Total Value: $10,000.00 (or your initial amount)
   - ✅ Cash: $10,000.00
   - ✅ Equity Value: $0.00 (if no positions)
   - ✅ Total P&L: $0.00

2. **Auto Refresh**
   - ✅ Auto Refresh toggle works
   - ✅ Manual Refresh button works
   - ✅ Auto refreshes every 60 seconds (if enabled)

3. **Agent Conversations**
   - ✅ Conversation list displays
   - ✅ Each Agent has dedicated icon
   - ✅ Conversation content displays completely (not truncated)

4. **Trade Records**
   - ✅ Execution Details shows trades
   - ✅ No duplicate records
   - ✅ Shows correct buy/sell direction and prices

5. **Control Buttons**
   - ✅ "▶️ Start Trading" button works
   - ✅ "Auto Trade (5 min)" checkbox works
   - ✅ "Refresh" button works

### Frontend Feature Testing

**Test trade execution:**
1. Click "▶️ Start Trading" button
2. Wait for Agent analysis to complete
3. Check if conversations appear
4. Check if trade orders are generated
5. Check if portfolio is updated

**Test auto trading:**
1. Check "Auto Trade (5 min)" checkbox
2. Wait 5 minutes
3. Check if trading cycle executes automatically
4. Check if conversations and trades are updated

---

## 🤖 Agent System

### Agent Types and Responsibilities

The system uses **two types of agents**: **Core Agents** (LLM-powered decision makers) and **Virtual Agents** (data aggregators for frontend display). All outputs are logged to `backend/data/logs/discussion_actions.jsonl` for the frontend Conversations panel:

### 🎯 Core Agents (LLM-Powered)
These agents use LLMs for autonomous decision-making. Defined in `backend/src/agents/`:

#### 1. **DiscussionAgent** 💬
- **File**: `analyst_discussion.py`
- **Role**: Multi-round discussion and tool orchestration
- **Type**: Full LLM agent with autonomous tool calling
- **Features**:
  - 3-5 discussion rounds
  - **Minimum 3 tools required** per cycle
  - Tool budget: 8 calls per round
  - Auto tool selection based on market context
  - Agent-generated keywords
  - Historical memory integration (last 5 days)
- **Outputs**: Final stance (BULLISH/BEARISH/NEUTRAL), detailed reasoning, complete tool results

#### 2. **RiskAnalyst** ⚠️
- **File**: `risk_analyst.py`
- **Role**: Portfolio risk evaluation
- **Type**: Full LLM agent analyzing risk factors
- **Inputs**: Current positions, portfolio value, market volatility, discussion insights
- **Outputs**:
  - `overall_risk`: LOW/MEDIUM/HIGH
  - Position concentration warnings
  - Diversification recommendations
  - P&L analysis for each position
- **Features**: Real-time P&L tracking, position limit enforcement

#### 3. **TraderAgent** 💼
- **File**: `trader_agent.py`
- **Role**: Final trading decisions and order generation
- **Type**: Full LLM agent making trade decisions
- **Inputs**: Discussion stance, risk report, position limits, market conditions
- **Outputs**:
  - `action`: BUY/SELL/HOLD
  - `buy_orders` / `sell_orders` with quantities and price bands
  - Trade rationale
- **Features**: Optimal position sizing (3-15% per stock), risk-adjusted quantities

---

### 📊 Virtual Agents (Data Aggregators)
These are **not separate agent classes** but data formatting layers in `trading_cycle.py` that package tool outputs for frontend display:

#### 4. **MarketAnalyst** 📊
- **Source**: `src/tools/market_analyst.py`
- **Purpose**: Aggregates market data analysis
- **Data**: Market sentiment, recommended stocks (top 10), key observations (trend analysis)

#### 5. **TechnicalAnalyst** 📉
- **Source**: `src/tools/market_tools.py` (technical indicators)
- **Purpose**: Formats technical analysis
- **Data**: Top signals (stocks with signal_score ≥3), RSI, MACD, Bollinger Bands

#### 6. **FundamentalAnalyst** 📈
- **Source**: Market analysis aggregation
- **Purpose**: Presents fundamental view
- **Data**: Market sentiment, recommended stocks, key observations

#### 7. **SentimentAnalyst** 😊
- **Source**: `src/tools/sentiment_tools.py`
- **Purpose**: Packages sentiment data
- **Data**: 
  - Fear & Greed Index (0-100, with label)
  - VIX Term Structure (VIX vs VIX3M ratio)
  - VIX Risk Score (0-10)

#### 8. **ToolSystem** 🔧
- **Source**: Direct tool call logging in `trading_cycle.py`
- **Purpose**: Logs all tool invocations
- **Tracked Tools**:
  - `news_scan`: 20 news articles, all headlines displayed
  - `vix_term`: VIX term structure analysis
  - `fear_greed`: Market sentiment index
  - `get_economic_summary`: GDP, CPI, Unemployment, Fed Rate
  - `get_labor_market_data`: Nonfarm Payrolls, Labor Force, Initial Claims
  - `fetch_fred_indicator`: Custom economic indicator queries
  - `fetch_jin10_news`: International financial news

### 🔄 Multi-Agent Discussion Flow

```
Trading Cycle Start
        ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 1: Market Data Collection                          │
├───────────────────────────────────────────────────────────┤
│ • fetch_market_batch (72+ stocks)                         │
│ • OHLCV + Technical Indicators                            │
│ • Real-time prices                                        │
└─────────────────────┬─────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 2: Data Aggregation (Virtual Agents)               │
├───────────────────────────────────────────────────────────┤
│ MarketAnalyst → Market sentiment, recommended stocks      │
│   (from market_tools)                                     │
│ TechnicalAnalyst → Technical signals, top stocks          │
│   (from market_tools indicators)                          │
│ FundamentalAnalyst → Fundamental ratings                  │
│   (aggregated from market analysis)                       │
│ SentimentAnalyst → Fear/Greed, VIX risk                   │
│   (from sentiment_tools)                                  │
└─────────────────────┬─────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 3: Multi-Round Discussion (DiscussionAgent)        │
├───────────────────────────────────────────────────────────┤
│ Round 1: Initial analysis                                 │
│   - Synthesize all analyst inputs                         │
│   - Form preliminary stance                               │
│                                                            │
│ Round 2: Deep dive with tools (Min 3 tools required)      │
│   - Call news_scan (20 articles, agent-selected keywords) │
│   - Call economic tools (GDP, unemployment, etc.)         │
│   - Call vix_term, fear_greed for sentiment               │
│   - Agent autonomously selects tools based on context     │
│                                                            │
│ Round 3: Final synthesis                                  │
│   - Integrate all information                             │
│   - Generate final stance with confidence                 │
│   - Provide detailed reasoning                            │
└─────────────────────┬─────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 4: Risk Evaluation (RiskAnalyst)                   │
├───────────────────────────────────────────────────────────┤
│ • Evaluate current positions                              │
│ • Check concentration limits                              │
│ • Calculate P&L for each position                         │
│ • Generate warnings and recommendations                   │
└─────────────────────┬─────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 5: Trading Decision (TraderAgent)                  │
├───────────────────────────────────────────────────────────┤
│ • Consider discussion stance + risk report                │
│ • Calculate optimal position sizes                        │
│ • Generate BUY/SELL orders                                │
│ • Set limit price bands                                   │
└─────────────────────┬─────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────┐
│ Phase 6: Order Execution & Persistence                   │
├───────────────────────────────────────────────────────────┤
│ • Save orders to pending_orders.jsonl                     │
│ • Update portfolio_state.json                             │
│ • Record conversations to discussion_actions.jsonl        │
│ • Save equity snapshot to equity_history.jsonl            │
│ • Log all tool usage (ToolSystem)                         │
└───────────────────────────────────────────────────────────┘
```

### 🧠 Agent Intelligence Features

- **Autonomous Operation**: Agents make decisions without human intervention
- **Historical Memory**: Each cycle loads last 5 days of portfolio snapshots and decisions
- **Collaborative Analysis**: Agents share insights through structured discussion rounds
- **Tool Integration**: 
  - Auto tool selection based on context
  - 8 tool calls per round budget (increased for comprehensive analysis)
  - **Minimum 3 tools required** per trading cycle for thorough research
  - No domain restrictions for news sources
  - Agent-generated keywords (not hardcoded)
- **Economic Data Integration** (FRED API):
  - Real-time US economic indicators (GDP, CPI, Unemployment, Fed Funds Rate)
  - Labor market data (Nonfarm Payrolls, Labor Force, Initial Claims)
  - Custom indicator queries by series ID
- **Complete Logging**: All conversations saved in full (no truncation)
  - Discussion rounds: Complete content preserved
  - Tool results: All 20 news headlines displayed
  - Market indicators: VIX, Fear & Greed tracked every cycle
  - Economic data: Tracked when relevant to market conditions

### 📝 Notes

- **Off-hours**: If a plan for the next trading day already exists, the system reuses it (no duplicate plans). Conversations and pending orders still display.
- **Frontend**: Renders conversations without raw JSON blocks; JSON-like payloads are formatted as bullet lists with proper spacing and typography.
- **Tool Budget**: Increased from 2 to 8 calls per round, with minimum 3 tools required per cycle to ensure comprehensive market analysis.

### Sentiment Data Sources
- **Fear & Greed Index (FGI)**: Pulled each cycle; logged as a ToolSystem entry like `fear_greed: value=XX, label=Greed/Fear, asof=YYYY-MM-DD` and summarized by `SentimentAnalyst`.
- **VIX Term Structure**: `VIX` vs `VIX3M` and `ratio`; logged as ToolSystem and summarized by `SentimentAnalyst` with a computed `vix_risk_score`.

---

## 🔄 Updated End‑to‑End Workflow (All Agents + Tools)

1) Market Data (MarketAgent/Tools)
- fetch_market_batch loads OHLCV and technical indicators for the entire configured universe (not a small subset).
- Output: per‑symbol signals (RSI/MACD/BB/signal_score), VIX snapshot.

2) MarketAnalyst (Analysis)
- Uses market_view to derive market_sentiment, recommended_stocks, and key_observations.
- Conversation: summary line recorded (agent=MarketAnalyst, type=summary).

3) SentimentAnalyst (FGI/VIX)
- Tools: fear_greed (FGI), vix_term (VIX vs VIX3M), plus derived vix_risk_score.
- Conversation: summary line + ToolSystem entries for fear_greed and vix_term every cycle.

4) FundamentalAnalyst (Fundamentals/Sentiment synthesis)
- Uses recommended_stocks + sentiment summary to form a fundamentals/sentiment view.
- Conversation: summary line recorded.

5) TechnicalAnalyst (Technical focus)
- Highlights top signals and key indicators for most relevant names.
- Conversation: summary line recorded with top_signals and indicator snapshot.

6) DiscussionAgent (Multi‑round discussion)
- Runs 1–3 rounds (configurable), optionally calls tools (e.g., news_scan).
- Conversation: full transcript per round, tool_context captured.

7) RiskAnalyst (Risk evaluation)
- Inputs: market_view, positions (if any), portfolio_value, discussion risk signals.
- Output: overall_risk_level, warnings, limits, diversification notes.
- Conversation: summary line recorded (agent=RiskAnalyst, type=summary).

8) TraderAgent (Decision & Orders)
- Inputs: market_view + market_analysis + risk_report + position_config.
- Output: action, buy_orders/sell_orders with price bands; pending orders placed with order_date per trading calendar.
- Conversation: summary line recorded (agent=TraderAgent, type=summary).

9) Persistence & Frontend Integration
- discussion_actions.jsonl: all agent summaries, tools, and discussion transcript.
- pending_orders.jsonl: pending limit orders (PENDING). Filled orders are never shown during closed hours on the dashboard.
- portfolio_state.json + equity_history.jsonl + real_time_snapshots.jsonl: portfolio summary and history for charts and summary cards.

---

## 🧰 Tool Catalog

### Market Data Tools
- **fetch_market_batch**: OHLCV + technical indicators for 72+ stocks
- **Technical Indicators** (via `ta_indicators.py`):
  - **Trend**: SMA, ADX
  - **Momentum**: RSI, MACD, Stochastic, ROC, Williams %R
  - **Volatility**: Bollinger Bands, ATR, Keltner Channels
  - **Volume**: OBV, VWAP, MFI
  - **Other**: Pivot Points, Ichimoku Cloud
  - **Signal Scoring**: 0-6 scale based on multi-indicator confirmation

### Sentiment Tools
- **fear_greed**: CNN Fear & Greed Index (0-100 scale, multi-source fallback)
- **vix_term**: VIX vs VIX3M ratio, contango/backwardation analysis
- **vix_close**: Current VIX level
- Computed: **vix_risk_score** (0-10 volatility risk rating)

### News & Web Tools
- **news_scan**: Multi-query news aggregation (20 articles per call)
  - Agent-generated keywords
  - All headlines displayed in frontend
  - No domain restrictions
- **fetch_jin10_news**: International financial news
- **web_search**: General web search (optional)
- **fetch_url**: Direct URL content fetching (optional)

### Economic Data Tools (FRED API)
- **get_economic_summary**: Comprehensive US economic indicators
  - GDP, CPI, Unemployment Rate, Fed Funds Rate
  - 10-Year Treasury Yield, Nonfarm Payrolls
  - Consumer Sentiment, Housing Starts
- **get_labor_market_data**: Labor market statistics
  - Unemployment Rate, Nonfarm Payrolls
  - Labor Force Participation, Continuing Claims
  - Initial Claims (weekly)
- **fetch_fred_indicator**: Custom indicator query by series ID
  - Any FRED series (e.g., UNRATE, GDP, CPIAUCSL)
  - Configurable data points and date range

### Tool Usage Strategy
- **Priority 1**: Market data (always fetched)
- **Priority 2**: Sentiment tools (VIX, Fear & Greed - every cycle)
- **Priority 3**: News and economic data (agent-selected based on context)
- **Minimum**: 3 tools per trading cycle for comprehensive analysis

---

## ⏱️ Scheduling & Frontend Behavior

- Trading Hours (open)
  - Auto trading loop every 30 minutes (configurable on the client) via the dashboard toggle.
  - Real‑time portfolio snapshot updates continuously; charts and summary cards refresh every 60s.

- Non‑Trading Hours (closed)
  - No live price updates; dashboard shows historical equity, conversations, and tomorrow’s pending orders.
  - Planning runs once on demand (Start Trading). Client auto‑check hourly: if tomorrow plan is missing, it plans once; otherwise, no new plans are created.
  - Dashboard hides FILLED rows when the market is closed to avoid confusion.

All behavior is implemented in the single‑file frontend (`frontend/monitor.html`) and the FastAPI backend (`backend/src/api/server.py`).

### Detailed Description

#### 1. Market Analyst

**Responsibilities:**
- Analyze technical indicators for all stocks
- Evaluate market trends (uptrend/downtrend/sideways)
- Generate recommended stock list
- Assess market sentiment (bullish/bearish/neutral)

**Output:**
```json
{
  "market_sentiment": "bullish",
  "recommended_stocks": ["NVDA", "MSFT", "AAPL"],
  "key_observations": ["Tech sector showing strength", ...],
  "concerns": ["VIX elevated", ...]
}
```

**Location:** `backend/src/tools/market_analyst.py`

#### 2. Discussion Agent

**Responsibilities:**
- Conduct multi-round discussions (default 3 rounds)
- Automatically call tools to get additional information (news, VIX, fear-greed index, etc.)
- Synthesize all information to form final stance
- Provide detailed reasoning process

**Output:**
```json
{
  "stance": "bullish",
  "rationale": [
    {"source": "technical_indicators", "reason": "..."},
    {"source": "news_scan", "reason": "..."},
    ...
  ],
  "signals_used": ["rsi14", "macd", "vix", ...],
  "tool_calls": [...],
  "to_agent_notes": "..."
}
```

**Location:** `backend/src/agents/analyst_discussion.py`

#### 3. Risk Analyst

**Responsibilities:**
- Evaluate current position risk
- Check position limit compliance
- Generate position control recommendations
- Identify over-concentration risks

**Output:**
```json
{
  "overall_risk": "medium",
  "position_control_report": {
    "recommended_position_sizes": {...},
    "position_limit_checks": [...]
  },
  "warnings": [...]
}
```

**Location:** `backend/src/agents/risk_analyst.py`

#### 4. Trader Agent

**Responsibilities:**
- Generate buy/sell orders based on all analysis
- Calculate position sizes
- Set buy/sell price ranges
- Consider risk reports and position limits

**Output:**
```json
{
  "action": "BUY",
  "buy_orders": [
    {
      "symbol": "NVDA",
      "buy_price": 199.77,
      "buy_price_min": 198.77,
      "buy_price_max": 199.77,
      "quantity": 7,
      "total_cost": 1398.39
    }
  ],
  "sell_orders": [...],
  "rationale": "..."
}
```

**Location:** `backend/src/agents/trader_agent.py`

### Agent Workflow

```
1. Market Data Collection
   ↓
2. Market Analyst → Recommended stocks + Market sentiment
   ↓
3. Discussion Agent (3 rounds) → Final stance + Reasoning
   ↓
4. Risk Analyst → Risk report + Position recommendations
   ↓
5. Trader Agent → Buy/sell orders
   ↓
6. Order Execution → Update portfolio
```

---

## 🛠️ Available Tools

Tools available to Agents, categorized by type:

### 📊 Market Data Tools

#### `fetch_market_batch`
**Purpose**: Batch fetch stock OHLCV data and technical indicators  
**Input**: Stock symbol list, start date, end date  
**Output**: Price, RSI, MACD, Bollinger Bands, signal score, VIX data for each stock, etc.  
**Use Cases**: 
- Market Analyst analyzes technical indicators for all stocks (default analyzes entire universe, 72 stocks)
- Discussion Agent evaluates market trends
- Trader Agent selects trading targets

**Example:**
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL", ...],  # Usually includes entire universe (72 stocks)
  "start": "2024-01-01",
  "end": "2025-01-27"
}
```

#### `vix_term`
**Purpose**: Get VIX term structure (VIX vs VIX3M ratio)  
**Output**: VIX value, VIX3M value, ratio (>1 = contango, <1 = backwardation)  
**Use Cases**: 
- Assess market panic level
- Determine if market is in contango or backwardation
- Risk Analyst evaluates market risk

#### `vix_close` / `fetch_vix_close`
**Purpose**: Get VIX historical closing price series  
**Input**: Start date, end date  
**Output**: VIX historical price array and date array  
**Use Cases**: 
- Analyze VIX trend changes
- Calculate VIX z-score
- Assess historical market volatility levels

#### `fear_greed`
**Purpose**: Get Fear & Greed Index  
**Output**: Index value (0-100), label (Extreme Fear/Fear/Neutral/Greed/Extreme Greed)  
**Use Cases**: 
- Assess market sentiment
- Determine if market is overly fearful or greedy
- Discussion Agent synthesizes market sentiment analysis

### 📰 News Tools

#### `news_scan`
**Purpose**: Scan news articles, search for news related to stocks/keywords  
**Input**: Keyword list (stock symbols, query terms), recent days, max articles, preferred domains  
**Output**: News titles, URLs, sources, dates, summaries  
**Use Cases**: 
- Discussion Agent gets latest market news (one of the most important tools)
- Assess market sentiment related to stocks
- Analyze company earnings, announcements, and other major events

**Example:**
```python
{
  "keywords": ["NVDA", "earnings"],
  "recency_days": 7,
  "max_articles": 12,
  "domains": ["www.reuters.com", "www.wsj.com"]
}
```

#### `web_search`
**Purpose**: DuckDuckGo web search (whitelisted domains)  
**Input**: Search query, max results, preferred domains  
**Output**: Search result titles, URLs, summaries  
**Use Cases**: 
- Search for specific stock or market information
- Get real-time market dynamics
- Supplement information not covered by news scanning

#### `fetch_url`
**Purpose**: Get main content of specified URL  
**Input**: URL address  
**Output**: Web page title, body content, extraction date  
**Use Cases**: 
- Get full content of news articles
- Analyze specific web page information
- Extract detailed market analysis

#### `plan_and_scan_news`
**Purpose**: Intelligent news planning and scanning (LLM generates queries then searches)  
**Input**: Market view (optional), topic list (optional), max articles  
**Output**: News article list (may include fetched URL content)  
**Use Cases**: 
- Discussion Agent automatically plans news search strategy
- Generate relevant queries based on market conditions

### 💰 Cryptocurrency Tools

#### `fetch_crypto_batch`
**Purpose**: Batch fetch cryptocurrency OHLCV data and technical indicators  
**Input**: Cryptocurrency code list (e.g., BTC-USD, ETH-USD), start date, end date  
**Output**: Same structure as `fetch_market_batch`, but includes cryptocurrency data  
**Use Cases**: 
- Analyze cryptocurrency market trends
- Assess correlation between cryptocurrencies and stock markets
- Get cryptocurrencies as market sentiment indicators

**Note**: Cryptocurrencies are currently only used for analysis and do not participate in actual trading.

#### `get_crypto_price`
**Purpose**: Get current price of single cryptocurrency  
**Input**: Cryptocurrency code (e.g., BTC-USD), start date, end date (optional)  
**Output**: Cryptocurrency price and technical indicators  
**Use Cases**: 
- Quickly get single cryptocurrency price
- Assess cryptocurrency market sentiment

### 🔍 Tool Usage Strategy

**Tool call priority:**
1. **Market data first**: `fetch_market_batch` is usually called first to get technical indicators for all stocks (entire universe, 72 stocks)
2. **Sentiment indicators**: `vix_term`, `fear_greed` for market sentiment assessment
3. **News supplement**: `news_scan` gets latest news to supplement market analysis (one of the most important tools, 20 articles per call)

**Tool budget**: Default each trading cycle has **15 tool call budget** (5 calls per round × 3 rounds), allowing Agents to fully use tools for analysis.

**Important Notes**: 
- `news_scan` is one of the most important tools for Discussion Agent to get real-time market news
- `fetch_market_batch` analyzes the entire universe (read from `config.json`, default 72 stocks), not just the first few
- All tools are used autonomously by LLM, with no hardcoded priority restrictions

### Tool Usage Example

**Agent automatically calls tools:**
```python
# Discussion Agent automatically calls tools
tool_calls = [
    {
        "name": "news_scan",
        "args": {"keywords": ["NVDA", "earnings"], "max_articles": 10},
        "why": "Need to check latest news about NVDA earnings"
    },
    {
        "name": "vix_term",
        "args": {"start": "2024-01-01", "end": "2024-01-31"},
        "why": "Check VIX term structure for volatility assessment"
    },
    {
        "name": "fear_greed",
        "args": {},
        "why": "Get market sentiment indicator"
    }
]
```

**Tool call budget:**
- Default budget: 20 tool calls
- Each discussion round can use multiple tools
- Agents automatically select most relevant tools

---

## 📁 Project Structure

```
ai-trader-ollama/
├── backend/                 # Python backend (main code)
│   ├── src/
│   │   ├── agents/         # All trading Agents
│   │   │   ├── market_analyst.py      # Market Analyst
│   │   │   ├── analyst_discussion.py  # Discussion Agent
│   │   │   ├── risk_analyst.py        # Risk Analyst
│   │   │   ├── trader_agent.py       # Trader Agent
│   │   │   └── toolbox.py            # Tool interface
│   │   ├── data/           # Portfolio, trade logs, memory management
│   │   ├── tools/           # All available tools
│   │   ├── orchestrator/    # Main trading cycle
│   │   └── api/             # FastAPI server
│   ├── config/             # Configuration files
│   │   └── config.json      # Main configuration file
│   ├── prompts/            # Agent prompt templates
│   │   ├── discussion_agent.yml
│   │   ├── trader_agent.yml
│   │   └── ...
│   ├── scripts/            # Utility scripts
│   │   ├── init_data.py
│   │   ├── start_api_background.ps1
│   │   └── ...
│   └── tests/              # Test suite
├── frontend/               # Frontend monitoring panel
│   └── monitor.html        # Main monitoring page (pure HTML)
├── docs/                   # Documentation
│   ├── archive/            # Archived documentation
│   └── ...
└── README.md               # This file
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: src` | Run from `backend/` directory |
| Ollama connection error | Run `ollama serve` |
| Port 8000 is in use | Use `backend\scripts\check_port.ps1` to find and terminate process |
| Frontend "Connection Error" | Check if backend API is running on port 8000 |
| No portfolio data | Run `python scripts/init_data.py` |
| PowerShell execution policy error | Use `restart_api_bypass.ps1` or `powershell -ExecutionPolicy Bypass` |

### Verifying System Status

**Check backend API:**
```powershell
curl http://localhost:8000/api/portfolio/real-time
```

**Check port usage:**
```powershell
netstat -ano | findstr ":8000"
```

**Check data initialization:**
```bash
ls backend/data/logs/portfolio_state.json
```

---

## 📚 Documentation

For complete documentation, see **[Documentation Index](docs/README.md)** which includes:
- Core documentation (Backend, Frontend, System Flow)
- Trading-related guides (Hedging, Leveraged ETFs, Market Indices)
- API documentation (Endpoints, Integration, Portfolio Flow)
- Trading hours logic
- Archived documentation

### Quick Links
- **[Complete System Flow](docs/COMPLETE_SYSTEM_FLOW.md)** - Detailed frontend & backend integration flow
- **[Backend README](backend/README.md)** - Backend setup and API documentation
- **[Frontend README](frontend/README.md)** - Frontend setup and usage
- **[Trading Hours Logic](backend/docs/TRADING_HOURS_LOGIC.md)** - Trading hours behavior

---

## ✅ System Status

**Current Status**: Production Ready ✅

All core features implemented and tested:
- ✅ Complete trading cycle (all Agents participate)
- ✅ Memory management system (save/load historical decisions)
- ✅ Automated execution
- ✅ Real-time monitoring panel (auto-refresh every 60 seconds)
- ✅ Hedging strategy support (inverse ETFs)
- ✅ Leveraged ETF support (moderate use)
- ✅ Market index technical analysis
- ✅ Complete API documentation
- ✅ Market Analyst complete analysis of universe all stocks (72 stocks)
- ✅ Detailed technical indicators display (RSI, MACD, signal scores, etc.)
- ✅ Trading hours logic (pre-market, market hours, after-hours)
- ✅ Non-trading hours display improvements (historical charts, tomorrow's orders)

---

## 📄 License

MIT License © 2025 Wenyu Chiou

---

## 👤 Author

**Wenyu Chiou**  
Lehigh University
📧 wec324@lehigh.edu
