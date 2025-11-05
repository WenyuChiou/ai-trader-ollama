# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe with hedging and leveraged ETF support  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 📚 Table of Contents

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

The system runs all agents each cycle (trading and off-hours planning) and logs their outputs to `backend/data/logs/discussion_actions.jsonl` so the frontend shows them in the Conversations panel:

- MarketAnalyst: Market sentiment + recommended stocks; key observations
- FundamentalAnalyst: Fundamental/sentiment summary for recommended stocks
- TechnicalAnalyst: Technical snapshot (RSI/MACD/BB) and top-signal tickers
- SentimentAnalyst: VIX term structure, Fear & Greed Index (FGI), vix_risk_score
- RiskAnalyst: Overall risk, limits, warnings, diversification guidance
- TraderAgent: Action, buy/sell counts and rationale
- ToolSystem: Tool usage entries (news_scan, vix_term, fear_greed, etc.)
- DiscussionAgent: Multi-round discussion with final stance and reasoning

Notes:
- Off-hours: if a plan for the next trading day already exists, the system reuses it (no duplicate plans). Conversations and pending orders still display.
- Frontend renders conversations without raw JSON blocks; JSON-like payloads are formatted as bullet lists.

### Sentiment Data Sources
- Fear & Greed Index (FGI): pulled each cycle; logged as a ToolSystem entry like `fear_greed: value=XX, label=Greed/Fear, asof=YYYY-MM-DD` and summarized by `SentimentAnalyst`.
- VIX Term Structure: `VIX` vs `VIX3M` and `ratio`; logged as ToolSystem and summarized by `SentimentAnalyst` with a computed `vix_risk_score`.
- Economic Data (Jin10): key recent items appended as a ToolSystem entry and injected into the discussion context.

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

## 🧰 Tool Catalog (Always Available)

- Market Data
  - fetch_market_batch: OHLCV + indicators for full universe
  - ta_indicators helpers (internal)

- Sentiment
  - fear_greed: CNN Fear & Greed (multi‑source fallback); ToolSystem entry every cycle
  - vix_term: VIX vs VIX3M ratio (+ vix_risk_score); ToolSystem entry every cycle

- News & Web
  - news_scan: multi‑query recent news; recorded when called by discussion
  - web_search/fetch_url (optional in some flows)

- Economic
  - jin10_economic_data: key recent economic datapoints; ToolSystem entry each cycle

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

### 📰 News & Economic Data Tools

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

#### `fetch_jin10_news`
**Purpose**: Get Jin10 financial news (Chinese financial news platform)  
**Input**: Max entries, category  
**Output**: News titles, times, content, categories, URLs  
**Use Cases**: 
- Get Chinese financial news
- Analyze Chinese market sentiment
- Get real-time financial news flashes

#### `fetch_jin10_economic_data`
**Purpose**: Get economic data (GDP, CPI, PMI, etc.)  
**Input**: Max entries  
**Output**: Economic data indicators, values, times, impacts  
**Use Cases**: 
- Assess macroeconomic environment
- Analyze impact of economic indicators on markets
- Risk Analyst evaluates systemic risk

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
3. **News supplement**: `news_scan` gets latest news to supplement market analysis (one of the most important tools)
4. **Economic data**: `fetch_jin10_economic_data` assesses macroeconomic environment

**Tool budget**: Default each trading cycle has **20 tool call budget**, allowing Agents to fully use tools for analysis.

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
