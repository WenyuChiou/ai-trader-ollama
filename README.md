# 💹 AI-Trader Ollama

> **A Multi-Agent Trading System with 23 Advanced Tools + 6 Specialized LLM Agents**  
> 📈 Analyzing **NASDAQ-100** (118+ symbols) with comprehensive fundamental, technical, and sentiment analysis  
> 🧠 Fully autonomous agent collaboration with real-time market data integration  
> 🎨 Dark tech-themed UI with live visualization and real-time updates

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-deepseek-r1-orange.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### 🌐 **Live Demo**

> **View the dashboard online**: [**https://WenyuChiou.github.io/ai-trader-ollama/monitor.html**](https://WenyuChiou.github.io/ai-trader-ollama/monitor.html)
> 
> 🔒 **Read-Only Mode**: The public website is in read-only mode for security. Trading controls are disabled. Use localhost for full control.

---

## 📚 Table of Contents

- [Latest Updates](#-latest-updates-january-2025)
- [System Overview](#-system-overview)
- [Quick Start](#-quick-start)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [Tool Suite (23 Tools)](#-tool-suite-23-tools)
- [Agent Discussion Flow](#-agent-discussion-flow)
- [Trading Workflow](#-trading-workflow)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Advanced Features](#-advanced-features)
- [Long-Term Operation & Best Practices](#-long-term-operation--best-practices)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

---

## 🆕 Latest Updates (January 2025)

### 🔄 **Automatic Trading Management** (Enhanced)

**Intelligent Market Status Detection:**
- ✅ **Automatic Market Detection**: System automatically detects trading hours and manages Auto Trade
- ✅ **Trading Hours**: Auto Trade runs **every 1 hour** during market hours (conversation/planning)
- ✅ **Data Refresh**: Continuous data updates every **30 seconds** (independent of trading cycle)
- ✅ **Non-Trading Hours**: Automatically checks if tomorrow is already planned
  - If already planned: Shows "Tomorrow Already Planned, Waiting" status
  - If not planned: Executes one planning cycle, then stops
- ✅ **Market Transition**: Automatically restarts Auto Trade when market transitions from closed to open
- ✅ **Status Display**: Real-time status indicator showing current Auto Trade state
  - 🟢 Green: Running / Completed
  - ⚪ Gray: Waiting / Already Planned
  - 🔴 Red: Error / Failed
  - 🟡 Yellow: Detecting / Checking
- ✅ **Initialization Conflict Detection**: Prevents system initialization during active trading/planning operations

**Previous**: Manual checkbox to enable/disable Auto Trade  
**Now**: Fully automatic - system manages itself based on market status

**Update (Latest)**: 
- Trading cycle interval optimized to **1 hour** (reduces frequent trading, saves resources)
- Data refresh continues **every 30 seconds** for real-time monitoring
- Prevents memory buildup from excessive LLM calls

### 🤖 **Multi-Analyst System** (Major Enhancement)

**All Analysts Now Real LLM Agents:**
- ✅ **Market Analyst**: Macro trends, sector rotation, economic environment
- ✅ **Technical Analyst**: Technical indicators, support/resistance, momentum
- ✅ **Fundamental Analyst**: Valuation, earnings, financial statements
- ✅ **Sentiment Analyst**: Market psychology, news sentiment, fear/greed
- ✅ **Risk Analyst**: Portfolio risk, position management (LLM-powered)
- ✅ **Trader Agent**: Final trading decisions based on all analyses

**Previous**: Discussion Agent → Risk Analyst → Trader  
**Now**: Market → Technical → Fundamental → Sentiment → Risk → Trader

Each analyst:
- Uses specialized LLM prompts for their domain
- Has access to all 23 tools but prioritizes domain-specific ones
- Passes findings to the next analyst
- Contributes to final consensus through voting

### 📊 **Tool Expansion: 14 → 23 Tools** (+64%)

**New Technical Indicators (2):**
- `get_advanced_indicators`: RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR, OBV, Volume
- `get_support_resistance`: Support/resistance levels, price pivots

**New Fundamental Data (3):**
- `get_company_fundamentals`: P/E, P/B, PEG, ROE, profit margins, analyst ratings
- `get_earnings_history`: Quarterly/annual earnings, surprises, growth
- `get_financial_statements`: Balance sheet, cashflow statements

**New Market Indicators (4):**
- `get_market_breadth`: Advancing/declining stocks, market sentiment
- `get_sector_rotation`: 11-sector performance ranking
- `get_correlation_matrix`: Stock correlations for diversification
- `get_market_indices`: S&P 500, Dow, NASDAQ, Russell 2000, VIX

### 🎯 **Key Improvements**

| Feature | Before | Now |
|---------|--------|-----|
| **Tool Count** | 14 | 23 (+64%) |
| **Agents** | Virtual roles | Real LLM agents |
| **Technical Analysis** | Basic | Advanced (8+ indicators) |
| **Fundamental Analysis** | ❌ None | ✅ Complete |
| **Market Analysis** | Basic | Comprehensive |
| **Tool Freedom** | Fixed few | 23 tools, any combination |
| **Agent Collaboration** | Single discussion | 4 specialists → consensus |
| **Trading Interval** | 5 minutes | 1 hour (optimized) |
| **Data Refresh** | 60 seconds | 30 seconds (continuous) |
| **Memory Management** | Unbounded | Limited history (20 entries) |
| **Time Display** | UTC only | Eastern Time (EST/EDT) with auto DST |
| **Deployment** | Local only | GitHub Pages ready |
| **Security** | ❌ None | ✅ Read-only mode for shared access |
| **API Config** | Manual | ✅ Auto-detection |
| **Order Safety** | Basic | ✅ Duplicate prevention, cash validation |
| **Net Value** | Basic | ✅ Anomaly detection, accurate calculation |

---

## 🌟 System Overview

### What is AI-Trader Ollama?

AI-Trader Ollama is a **fully autonomous multi-agent trading system** that combines:
- **6 specialized LLM agents** working in collaboration
- **23 advanced tools** for market analysis
- **Real-time data integration** from multiple sources
- **Intelligent risk management** with position controls
- **Historical memory system** for learning from past trades

### Core Philosophy

1. **Multi-perspective Analysis**: Different agents analyze the market from their specialized viewpoints
2. **Tool Diversity**: 23 tools provide comprehensive market coverage
3. **Autonomous Decision Making**: Agents discuss, debate, and reach consensus
4. **Risk-First Approach**: Every decision passes through risk analysis
5. **Transparency**: All reasoning is logged and visible

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Daily Trading Cycle                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Market Data Fetch (118 stocks + VIX + indicators)       │
│     • yfinance: OHLCV, volume                                │
│     • Technical indicators: RSI, MACD, BB, signal_score      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Multi-Analyst Discussion System                          │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   Market    │→ │  Technical   │→ │  Fundamental    │    │
│  │   Analyst   │  │   Analyst    │  │   Analyst       │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│        │                  │                   │              │
│        └──────────────────┼───────────────────┘              │
│                           ▼                                  │
│                  ┌─────────────────┐                         │
│                  │   Sentiment     │                         │
│                  │   Analyst       │                         │
│                  └─────────────────┘                         │
│                           │                                  │
│                           ▼                                  │
│                  [Final Consensus]                           │
│                                                               │
│  Each analyst uses 3-5 tools from the 23 available          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Risk Analyst (LLM-powered)                               │
│     • Market risk assessment                                 │
│     • Position concentration check                           │
│     • VIX & correlation analysis                             │
│     • Position control recommendations                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Trader Agent                                             │
│     • BUY/SELL decisions                                     │
│     • Position sizing (max 15% per stock)                    │
│     • Price range calculation                                │
│     • Order placement                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Order Execution & Management                             │
│     • Pending orders (market closed)                         │
│     • Limit orders with trigger prices                       │
│     • Position limits & cooldowns                            │
│     • Trade logging                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Portfolio & Memory Update                                │
│     • Portfolio state saved                                  │
│     • Equity history recorded                                │
│     • Memory snapshot for next cycle                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

**1. Python Environment**
```bash
# Python 3.10 or higher required
python --version

# Install dependencies
cd backend
pip install -r requirements.txt
```

**2. Ollama Setup**
```bash
# Install Ollama from https://ollama.ai/

# Start Ollama service (keep running in terminal 1)
ollama serve

# Pull LLM model (in terminal 2)
ollama pull deepseek-r1
```

**3. API Keys (Optional but Recommended)**
```bash
# FRED API for economic data (free: https://fred.stlouisfed.org/docs/api/api_key.html)
export FRED_API_KEY=your_api_key_here

# For Windows PowerShell:
$env:FRED_API_KEY="your_api_key_here"
```

### Installation

**1. Clone Repository**
```bash
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama
```

**2. Initialize System**
```bash
# From project root directory
cd "path\to\ai-trader-ollama"

# Initialize portfolio and data structures
python scripts/init_data.py

# This creates:
# - data/logs/portfolio_state.json (initial $10,000)
# - data/logs/equity_history.jsonl
# - data/logs/discussion_actions.jsonl
# - data/logs/trade_log.jsonl
```

**3. Start Backend API**

**Important**: Scripts are in the **project root** `scripts/` folder.

```powershell
# Make sure you're in the project ROOT directory (not backend/)
cd "path\to\ai-trader-ollama"

# Method 1: Stable version (Recommended, with auto-restart)
.\scripts\start_api_stable_bypass.ps1

# Method 2: Fast restart (Daily use, quick restart)
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1

# Method 3: Manual start (Development/Testing)
# From project ROOT directory:
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Command Explanation** (`python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload`):

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| `python -m uvicorn` | - | Run uvicorn ASGI server via Python module |
| `backend.src.api.server:app` | - | Path to FastAPI app: `backend/src/api/server.py` → `app` object |
| `--host 0.0.0.0` | `0.0.0.0` | **Bind to all network interfaces** (allows LAN access, not just localhost) |
| `--port 8000` | `8000` | **Listen on port 8000** |
| `--reload` | - | **Auto-reload on code changes** (development mode) |

**Important Notes**:
- ✅ `--host 0.0.0.0` allows access from other devices on your network
- ✅ `--host 127.0.0.1` (or `localhost`) only allows local access
- ✅ `--reload` automatically restarts server when you modify code (development only)
- ⚠️ Remove `--reload` for production (better performance)

**4. Monitor API Status** (After Starting)

**Quick Check** (in browser):
```
http://localhost:8000/api/status
http://localhost:8000/docs
```

**Quick Check** (in PowerShell):
```powershell
# Check if port 8000 is in use
netstat -ano | findstr 8000

# Test API response
curl http://localhost:8000/api/status

# Or use Invoke-WebRequest
Invoke-WebRequest -Uri http://localhost:8000/api/status | Select-Object -ExpandProperty Content
```

**Expected Response**:
```json
{
  "ok": true,
  "status": "running",
  "message": "API is operational"
}
```

**If API is NOT running**, you'll see:
- Connection refused error
- Port 8000 not in use
- Browser shows "This site can't be reached"

**5. Access Dashboard**

**Local Access**:
```
http://localhost:3000/monitor.html
```

**Public Access** (after deployment):
```
https://your-username.github.io/ai-trader-ollama/monitor.html
```

<details>
<summary><b>Frontend Setup (Developer Only - Click to expand)</b></summary>

```bash
# In a new terminal
cd frontend
python -m http.server 3000
```

> 💡 **Tip**: After deploying to GitHub Pages, anyone can access your frontend via the public URL. See [Deployment Guide](#-deployment--sharing) for details.

</details>

### First Trading Cycle

1. **Check System Status**
   - Open dashboard: `http://localhost:3000/monitor.html`
   - Market Status indicator (top right)
   - Portfolio display (should show $10,000 cash)

2. **Initialize Market Data**
   - Click "🔄 Refresh Data" to fetch current prices

3. **Start Trading**
   - Click "▶️ Start Trading"
   - Wait for agents to analyze (~30-60 seconds)
   - Watch conversation panel for agent discussions

4. **Review Results**
   - Check "Execution Details" for orders
   - View "Holdings" for new positions
   - Monitor "Net Value Curve" for equity changes

---

## 🤖 Multi-Agent Architecture

### Agent Specifications

#### 1. **Market Analyst** 🌐

**Specialty**: Macro trends, sector rotation, market structure  
**Years of Experience**: 14  
**Model**: deepseek-r1 (temperature: 0.3)

**Priority Tools**:
- `get_market_indices`: S&P 500, Dow, NASDAQ, Russell 2000
- `get_sector_rotation`: 11-sector performance ranking
- `get_market_breadth`: Advancing/declining stocks ratio
- `get_economic_summary`: GDP, unemployment, CPI, Fed funds
- `vix_term`: Market volatility structure

**Output Format**:
```json
{
  "stance": "risk_on | risk_off | neutral",
  "market_score": 0-10,
  "analysis": "...",
  "market_regime": {
    "trend": "bull/bear/sideways",
    "volatility": "low/medium/high",
    "phase": "early/mid/late_cycle/recession"
  },
  "sector_leadership": {...},
  "tool_calls": [...]
}
```

---

#### 2. **Technical Analyst** 📈

**Specialty**: Chart patterns, indicators, support/resistance  
**Years of Experience**: 12  
**Model**: deepseek-r1 (temperature: 0.2)

**Priority Tools**:
- `get_advanced_indicators`: RSI, MACD, BB, ADX, Stochastic, ATR, OBV
- `get_support_resistance`: Key price levels
- `vix_term`: Volatility analysis
- `get_market_indices`: Broad market context

**Output Format**:
```json
{
  "stance": "bullish | bearish | neutral",
  "technical_score": 0-10,
  "analysis": "...",
  "key_levels": {
    "NVDA": {"support": [120.5, 118.2], "resistance": [125.0, 128.5]}
  },
  "indicators_summary": {
    "NVDA": {"rsi": 65, "macd": "bullish", "trend": "up"}
  },
  "tool_calls": [...]
}
```

---

#### 3. **Fundamental Analyst** 💼

**Specialty**: Financial statements, valuation, earnings  
**Years of Experience**: 15  
**Model**: deepseek-r1 (temperature: 0.2)

**Priority Tools**:
- `get_company_fundamentals`: P/E, ROE, profit margins, growth
- `get_earnings_history`: Quarterly/annual earnings, surprises
- `get_financial_statements`: Balance sheet, cashflow
- `news_scan`: Company-specific news
- `get_sector_rotation`: Industry context

**Output Format**:
```json
{
  "stance": "bullish | bearish | neutral",
  "fundamental_score": 0-10,
  "analysis": "...",
  "valuations": {
    "NVDA": {"pe": 45.2, "forward_pe": 38.5, "assessment": "fair"}
  },
  "earnings_quality": {
    "NVDA": {"growth": "25%", "surprise": "+5%", "quality": "high"}
  },
  "tool_calls": [...]
}
```

---

#### 4. **Sentiment Analyst** 😊

**Specialty**: Market psychology, news sentiment, fear/greed  
**Years of Experience**: 10  
**Model**: deepseek-r1 (temperature: 0.3)

**Priority Tools**:
- `fear_greed`: CNN Fear & Greed Index (0-100)
- `vix_term`: Volatility and fear measurement
- `news_scan`: Sentiment from news headlines
- `get_market_breadth`: Market participation
- `plan_and_scan_news`: AI-powered news analysis

**Output Format**:
```json
{
  "stance": "bullish | bearish | neutral",
  "sentiment_score": 0-10,
  "analysis": "...",
  "fear_greed": {
    "value": 65,
    "label": "greed",
    "interpretation": "..."
  },
  "vix_analysis": {...},
  "news_sentiment": {...},
  "contrarian_signals": [...],
  "tool_calls": [...]
}
```

---

#### 5. **Risk Analyst** 🛡️

**Specialty**: Risk assessment, position management  
**Years of Experience**: 15  
**Model**: deepseek-r1 (temperature: 0.2)

**Priority Tools**:
- `vix_term`: Tail risk assessment
- `fear_greed`: Sentiment extremes
- `get_correlation_matrix`: Diversification analysis
- `get_market_breadth`: Market health
- `get_economic_summary`: Macro risk factors

**Output Format**:
```json
{
  "overall_risk_level": "low | medium | high | extreme",
  "risk_score": 0-10,
  "analysis": "...",
  "market_risks": [...],
  "position_risks": [...],
  "position_control_report": {
    "max_position_per_stock": 0.15,
    "recommended_position_sizes": {...}
  },
  "tool_calls": [...]
}
```

---

#### 6. **Trader Agent** 💰

**Specialty**: Trading decisions, position sizing  
**Years of Experience**: N/A (Pure logic-based)  
**Model**: deepseek-r1 (temperature: 0.25)

**Inputs**:
- Market data with prices
- All analyst recommendations
- Risk report with position limits
- Current portfolio state

**Output Format**:
```json
{
  "buy_orders": [
    {
      "symbol": "NVDA",
      "quantity": 10,
      "buy_price": 122.50,
      "buy_price_min": 121.89,
      "buy_price_max": 123.11,
      "total_cost": 1225.00,
      "rationale": "..."
    }
  ],
  "sell_orders": [...],
  "stance": "bullish | bearish | neutral"
}
```

---

## 🛠️ Tool Suite (23 Tools)

### Sentiment & Risk (3 tools)

| Tool | Description | Return |
|------|-------------|--------|
| `vix_term` | Fetch ^VIX & ^VIX3M term structure | VIX levels, ratio, term structure |
| `vix_close` | Historical VIX close prices | Time series data |
| `fear_greed` | CNN Fear & Greed Index | 0-100 score with label |

**Example**:
```python
vix_data = vix_term()
# Returns: {"vix": 18.5, "vix3m": 20.2, "ratio": 1.09, "term_structure": "contango"}

fear_greed_data = fear_greed()
# Returns: {"value": 65, "label": "Greed", "description": "..."}
```

---

### News & Information (5 tools)

| Tool | Description | Use Case |
|------|-------------|----------|
| `news_scan` | Scan news by keywords | Get recent headlines |
| `plan_and_scan_news` | LLM-powered news query | Intelligent news gathering |
| `web_search` | DuckDuckGo search | Research specific topics |
| `fetch_url` | Extract content from URL | Read full articles |
| `fetch_jin10_news` | Jin10 financial news (Chinese) | Asian market coverage |

**Example**:
```python
news = news_scan(keywords=["NVDA", "earnings"], days=3, max_n=20)
# Returns: {"ok": True, "hits": [...], "count": 20}
```

---

### Economic Data - FRED API (3 tools)

| Tool | Description | Indicators |
|------|-------------|------------|
| `get_economic_summary` | Key US economic indicators | GDP, unemployment, CPI, Fed funds |
| `get_labor_market_data` | Labor market data | Unemployment rate, payrolls, claims |
| `fetch_fred_indicator` | Specific FRED indicator | Any FRED series by ID |

**Example**:
```python
econ = get_economic_summary()
# Returns:
# {
#   "GDP": {"value": 2.8, "date": "2024-Q3", "change": "+0.3%"},
#   "unemployment_rate": {"value": 4.1, "date": "2024-12"},
#   "CPI": {"value": 3.2, "date": "2024-12", "yoy_change": "+3.2%"},
#   "fed_funds_rate": {"value": 5.25, "date": "2024-12"}
# }
```

---

### Technical Indicators (2 tools)

| Tool | Description | Indicators |
|------|-------------|------------|
| `get_advanced_indicators` | Comprehensive technical analysis | RSI, MACD, BB, ADX, Stochastic, ATR, OBV, Volume |
| `get_support_resistance` | Key price levels | Support/resistance arrays, nearest levels |

**Example**:
```python
indicators = get_advanced_indicators(symbol="NVDA", period="3mo")
# Returns:
# {
#   "symbol": "NVDA",
#   "last_price": 122.50,
#   "indicators": {
#     "rsi_14": 65.2,
#     "macd": {"macd": 2.3, "signal": 1.8, "histogram": 0.5},
#     "bollinger_bands": {"upper": 125.0, "middle": 120.0, "lower": 115.0},
#     "adx": {"adx": 28.5, "plus_di": 32.1, "minus_di": 18.4},
#     "stochastic": {"k": 78.5, "d": 72.3},
#     "atr_14": 3.45,
#     "obv": 1234567890,
#     "volume": {"current": 45000000, "avg_20": 42000000, "ratio": 1.07}
#   }
# }

sr = get_support_resistance(symbol="NVDA", period="6mo")
# Returns:
# {
#   "symbol": "NVDA",
#   "current_price": 122.50,
#   "resistances": [125.0, 128.5, 132.0],
#   "supports": [120.0, 118.2, 115.5],
#   "nearest_resistance": 125.0,
#   "nearest_support": 120.0
# }
```

---

### Fundamental Data (3 tools)

| Tool | Description | Data |
|------|-------------|------|
| `get_company_fundamentals` | Comprehensive fundamentals | Valuation, profitability, growth, financial health |
| `get_earnings_history` | Earnings data | Quarterly/annual earnings, surprises |
| `get_financial_statements` | Financial statements | Balance sheet, cashflow |

**Example**:
```python
fundamentals = get_company_fundamentals(symbol="NVDA")
# Returns:
# {
#   "symbol": "NVDA",
#   "company_name": "NVIDIA Corporation",
#   "sector": "Technology",
#   "fundamentals": {
#     "valuation": {
#       "market_cap": 3000000000000,
#       "pe_ratio": 45.2,
#       "forward_pe": 38.5,
#       "peg_ratio": 1.8,
#       "price_to_book": 22.5,
#       "ev_to_ebitda": 35.2
#     },
#     "profitability": {
#       "profit_margins": 0.48,
#       "operating_margins": 0.52,
#       "return_on_equity": 0.65,
#       "eps_trailing": 2.71,
#       "eps_forward": 3.18
#     },
#     "growth": {
#       "revenue_growth": 0.34,
#       "earnings_growth": 0.55
#     },
#     "financial_health": {
#       "debt_to_equity": 0.15,
#       "current_ratio": 3.5,
#       "free_cashflow": 28000000000
#     },
#     "dividend": {
#       "dividend_yield": 0.003
#     },
#     "analyst_ratings": {
#       "target_price": 140.0,
#       "recommendation": "buy",
#       "number_of_analysts": 45
#     }
#   }
# }
```

---

### Market Indicators (4 tools)

| Tool | Description | Use Case |
|------|-------------|----------|
| `get_market_breadth` | Market participation | Advancing/declining, sentiment |
| `get_sector_rotation` | Sector performance | Leadership identification |
| `get_correlation_matrix` | Stock correlations | Diversification analysis |
| `get_market_indices` | Major indices | S&P 500, Dow, NASDAQ, Russell 2000 |

**Example**:
```python
breadth = get_market_breadth()
# Returns:
# {
#   "total_stocks": 10,
#   "advancing": 7,
#   "declining": 3,
#   "advance_decline_ratio": 2.33,
#   "market_sentiment": "bullish"
# }

sectors = get_sector_rotation(period="1mo")
# Returns:
# {
#   "period": "1mo",
#   "sectors": [
#     {"sector": "Technology", "etf": "XLK", "return_pct": 5.2},
#     {"sector": "Healthcare", "etf": "XLV", "return_pct": 2.8},
#     ...
#   ],
#   "top_sector": {"sector": "Technology", "return_pct": 5.2},
#   "bottom_sector": {"sector": "Energy", "return_pct": -2.1}
# }

indices = get_market_indices()
# Returns:
# {
#   "indices": [
#     {"name": "S&P 500", "symbol": "^GSPC", "price": 4800.5, "change": 25.3, "change_pct": 0.53},
#     {"name": "NASDAQ", "symbol": "^IXIC", "price": 15000.2, "change": 85.6, "change_pct": 0.57},
#     ...
#   ]
# }
```

---

### Crypto (2 tools)

| Tool | Description |
|------|-------------|
| `fetch_crypto_batch` | Batch crypto data with indicators |
| `get_crypto_price` | Single crypto current price |

---

### Jin10 (1 tool)

| Tool | Description |
|------|-------------|
| `fetch_jin10_economic_data` | Economic data from Jin10 (Chinese) |

---

## 🔄 Agent Discussion Flow

### Multi-Agent Collaboration Process

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Market Analyst                                      │
├─────────────────────────────────────────────────────────────┤
│ • Tools: get_market_indices(), get_sector_rotation(),       │
│          get_economic_summary()                              │
│ • Analysis: Overall market trends, sector rotation,          │
│            economic environment                              │
│ • Output: "Market in mid-cycle bull phase. Tech and         │
│          healthcare sectors leading. GDP growth stable,      │
│          VIX at low levels."                                 │
│ • Stance: risk_on (Score: 7.5/10)                           │
│ • Stock Selection: Based on signal_score > 5.0              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Pass analysis results)
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Technical Analyst                                   │
├─────────────────────────────────────────────────────────────┤
│ • Receives: Market Analyst's "risk_on" stance               │
│ • Tools: get_advanced_indicators(), get_support_resistance() │
│ • Strategy: Sort by signal_score, prioritize high scores    │
│ • Analysis: RSI, MACD, Bollinger Bands, support/resistance,  │
│            price momentum                                    │
│ • Output: "NVDA: RSI=65, MACD bullish, support at 120.     │
│          MSFT: Breakout above resistance 380, volume up.    │
│          Strong technical setup, multiple stocks with       │
│          signal_score > 6.0"                                 │
│ • Stance: bullish (Score: 8.2/10)                           │
│ • Stocks Analyzed: Up to 8 (limited by tool_budget=15,     │
│                    max 8 tools per analyst)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Pass analysis results)
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Fundamental Analyst                                 │
├─────────────────────────────────────────────────────────────┤
│ • Receives: Market "risk_on" + Technical "bullish"          │
│ • Tools: get_company_fundamentals(),                        │
│          get_earnings_history(),                            │
│          get_financial_statements()                          │
│ • Analysis: P/E ratio, earnings growth, ROE, financial health│
│ • Output: "NVDA: P/E=45, earnings growth 55%, ROE=65%.       │
│          Fair valuation, strong earnings quality,            │
│          +5% surprise."                                      │
│ • Stance: bullish (Score: 7.8/10)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Pass analysis results)
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Sentiment Analyst                                   │
├─────────────────────────────────────────────────────────────┤
│ • Receives: All previous stances (3 bullish)                │
│ • Tools: fear_greed(), vix_term(), news_scan()               │
│ • Analysis: Fear & Greed Index, VIX structure, news sentiment│
│ • Output: "Market sentiment bullish but approaching greed.  │
│          F&G=65 (Greed), VIX=18 (Low), news positive.       │
│          Watch for potential reversal signals."              │
│ • Stance: bullish (Score: 6.5/10)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Aggregate all stances)
┌─────────────────────────────────────────────────────────────┐
│ Final Consensus                                             │
├─────────────────────────────────────────────────────────────┤
│ • Vote: 4 bullish / 0 bearish / 0 neutral                    │
│ • Final Stance: BULLISH                                     │
│ • Tool Calls: 12-15 per cycle (shared 15 budget)            │
│ • Tool Diversity: 8+ different tools                       │
│ • Stock Coverage: Technical Analyst analyzes up to 8 stocks │
│                    (limited by tool_budget=15)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Pass to Risk Analyst)
┌─────────────────────────────────────────────────────────────┐
│ Risk Analyst                                                │
├─────────────────────────────────────────────────────────────┤
│ • Receives: Final consensus + market data + current positions│
│ • Tools: get_correlation_matrix(), vix_term()                │
│ • Analysis: Position concentration, market risk, correlation │
│ • Output: Position control report, risk-adjusted sizes       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (Pass to Trader)
┌─────────────────────────────────────────────────────────────┐
│ Trader Agent                                                │
├─────────────────────────────────────────────────────────────┤
│ • Input: Final consensus (bullish) + risk report +           │
│          signal_score data                                   │
│ • Decision Logic: Prioritize stocks with signal_score > 3.0 │
│ • Trading Decision: Buy NVDA x10 @ $122.50                  │
│                     (max 15% portfolio)                      │
│ • Order Type: Limit order with price range                   │
│ • Filter: signal_score > 3.0 (medium signal and above)      │
└─────────────────────────────────────────────────────────────┘
```

<details>
<summary><b>Signal Score System (0-10) - Technical Details (Click to expand)</b></summary>

**Signal Score** is a comprehensive technical indicator scoring system (0-10) that evaluates stock buy signal strength:

#### Scoring Dimensions (6 dimensions, total 0-10)

1. **Moving Average Trend (0-2 points)**
   - Base: MA20 > MA50 (+1.0)
   - Enhanced: MA20 significantly above MA50 (>2%) (+1.0)

2. **MACD Signal (0-2.5 points)**
   - MACD line > Signal line (+1.0)
   - MACD histogram positive (+0.5)
   - Strong momentum (+1.0)

3. **RSI Signal (0-2 points)**
   - RSI in 50-70 (+1.0)
   - RSI in 55-65 optimal (+1.0)
   - RSI in 30-50 oversold bounce (+0.5)
   - Extreme RSI (>80 or <20) (-0.5)

4. **Bollinger Bands Position (0-1.5 points)**
   - Position in 0.2-0.8 (+1.0)
   - Position in 0.5-0.7 stronger (+0.5)
   - Extreme position (>0.95 or <0.05) (-0.5)

5. **Price Momentum (0-1.5 points)**
   - Positive momentum (+0.5)
   - Strong positive momentum (>2%) (+1.0)
   - Strong negative momentum (<-2%) (-0.5)

6. **Volume Confirmation (0-1 point)**
   - Volume > 1.2x average (+0.5)
   - Volume > 1.5x average (+0.5)

#### Score Interpretation

- **0-2**: Weak signal (bearish or neutral)
- **3-5**: Medium signal (slightly bullish)
- **6-8**: Strong signal (clearly bullish)
- **9-10**: Very strong signal (strongly bullish)

#### Usage

- **Market Analyst**: Uses `signal_score > 5.0` to filter high-signal stocks
- **Technical Analyst**: Sorts by `signal_score`, prioritizes high scores (up to 8 stocks, limited by tool_budget)
- **Trader Agent**: Uses `signal_score > 3.0` as buy threshold

### Agent Tool Usage Summary

| Agent | Priority Tools | Typical Calls | Focus |
|-------|---------------|---------------|-------|
| **Market** | market_indices, sector_rotation, economic_summary | 2-3 | Macro environment |
| **Technical** | advanced_indicators, support_resistance | Up to 8 | Price action (multi-stock analysis, budget limited) |
| **Fundamental** | company_fundamentals, earnings_history | 2-3 | Valuation analysis |
| **Sentiment** | fear_greed, vix_term, news_scan | 2-3 | Market psychology |
| **Risk** | vix_term, correlation_matrix, market_breadth | 2-3 | Risk management |

**Total**: ~12-15 tool calls per cycle (shared 15 budget)  
**Diversity**: 8+ different tools  
**Stock Coverage**: Technical Analyst analyzes up to 8 stocks (limited by tool_budget=15, max 8 tools per analyst)

</details>

---

## 📈 Trading Workflow

### High-Level Process

1. **Data Collection** (5-10 seconds)
   - Fetch market data for 118+ NASDAQ-100 stocks
   - Calculate technical indicators (RSI, MACD, signal_score)
   - Get economic indicators and market sentiment

2. **Multi-Agent Analysis** (30-60 seconds)
   - Market Analyst: Macro trends and sector rotation
   - Technical Analyst: Price patterns and indicators (up to 8 stocks)
   - Fundamental Analyst: Valuation and earnings
   - Sentiment Analyst: Market psychology and news

3. **Risk Assessment** (10-20 seconds)
   - Position concentration analysis
   - Market risk evaluation
   - Position size recommendations

4. **Trading Decisions** (5-10 seconds)
   - Generate buy/sell orders based on consensus
   - Apply position limits (max 15% per stock)
   - Calculate price ranges for limit orders

5. **Order Execution**
   - Market open: Execute immediately if price is within range
   - Market closed: Place pending orders for next trading day

6. **Portfolio Update**
   - Update portfolio state
   - Record equity history
   - Save memory snapshot

<details>
<summary><b>Trading Workflow Technical Details (Developer Only - Click to expand)</b></summary>

### Complete Cycle Breakdown

#### Phase 1: Data Collection (5-10 seconds)

```python
# Fetch 118 stocks from NASDAQ-100
market_data = fetch_market_batch(symbols=universe, start=start_date, end=end_date)

# Returns for each stock:
{
  "NVDA": {
    "price": 122.50,
    "change_pct": 2.3,
    "rsi14": 65.2,
    "macd": 2.3,
    "bb_pos": 0.75,
    "signal_score": 7.8,
    ...
  },
  ...
}
```

#### Phase 2: Multi-Analyst Discussion (30-60 seconds)

```python
# Run 4 analysts in sequence
discussion_result = run_multi_analyst_discussion(
    market_view=market_data,
    use_tools=True,
    tool_budget=15
)

# Returns:
{
  "final_stance": "bullish",
  "analyst_reports": {
    "market": {...},
    "technical": {...},
    "fundamental": {...},
    "sentiment": {...}
  },
  "tool_calls": [...],  # All tool invocations
  "transcript": [...]    # Full discussion text
}
```

#### Phase 3: Risk Analysis (10-20 seconds)

```python
# LLM-powered risk assessment
risk_report = run_risk_analyst_llm(
    market_json=market_data,
    current_positions=portfolio.positions,
    portfolio_value=portfolio.total_value,
    discussion_risk_signals=discussion_result,
    use_tools=True
)

# Returns:
{
  "overall_risk_level": "medium",
  "risk_score": 5.2,
  "position_control_report": {
    "max_position_per_stock": 0.15,
    "recommended_position_sizes": {
      "NVDA": {"current_pct": 0.10, "max_pct": 0.15, "adjustment": "HOLD"}
    }
  },
  "market_risks": [...],
  "position_risks": [...]
}
```

#### Phase 4: Trading Decisions (5-10 seconds)

```python
# Trader makes final decisions
decision = run_trader(
    market=market_data,
    mview=enriched_market,
    rview=risk_report,
    convo=discussion_result,
    current_positions=portfolio.positions,
    portfolio_value=portfolio.total_value
)

# Returns:
{
  "buy_orders": [
    {
      "symbol": "NVDA",
      "quantity": 10,
      "buy_price": 122.50,
      "buy_price_min": 121.89,  # 99.5% of current price
      "buy_price_max": 123.11,  # 100.5% of current price
      "total_cost": 1225.00,
      "rationale": "Strong fundamentals + bullish technical setup"
    }
  ],
  "sell_orders": [...]
}
```

#### Phase 5: Order Execution

**Scenario A: Market Closed**
```python
# Orders are placed as pending
order_manager.place_order(
    symbol="NVDA",
    action="BUY",
    quantity=10,
    limit_price=121.89,  # Aggressive limit for higher fill rate
    price_range={"min": 121.89, "max": 123.11},
    order_date=tomorrow  # Next trading day
)

# Order status: PENDING
# Will execute when market opens if price is within range
```

**Scenario B: Market Open**
```python
# Check if price is within limit range
current_price = get_current_price("NVDA")
if limit_price_min <= current_price <= limit_price_max:
    # Execute immediately
    portfolio.buy(symbol="NVDA", quantity=10, price=current_price)
    trade_logger.log(symbol="NVDA", action="BUY", status="FILLED")
else:
    # Place pending order
    order_manager.place_order(...)
```

#### Phase 6: Post-Trade Operations

```python
# 1. Update portfolio state
portfolio.save()  # Save to portfolio_state.json

# 2. Record equity history
equity_tracker.record_daily_equity(
    date_str=today,
    portfolio_snapshot={
        "total_value": portfolio.total_value,
        "cash": portfolio.cash,
        "equity_value": portfolio.equity_value,
        "positions": portfolio.positions
    }
)

# 3. Save memory snapshot
memory_manager.save_daily_memory(
    date=today,
    market_view=market_data,
    discussion=discussion_result,
    risk_report=risk_report,
    decision=decision,
    executed_trades=executed_trades
)

# 4. Write conversation log
# Saved to discussion_actions.jsonl for frontend display
```

### Order Management Details

#### Limit Order Strategy

**For BUY orders:**
```python
# Use 99.5% of current price as limit (aggressive for higher fill rate)
limit_price = current_price * 0.995

# Price range for trigger check
price_range = {
    "min": current_price * 0.995,  # 99.5%
    "max": current_price * 1.005   # 100.5%
}

# Order fills if market price is within range
```

**For SELL orders:**
```python
# Use 100.5% of current price as limit (aim to sell higher)
limit_price = current_price * 1.005

# Price range
price_range = {
    "min": current_price * 0.995,
    "max": current_price * 1.005
}
```

#### Position Controls

**Hard Limits:**
- Max position per stock: **15%** of portfolio value
- Max total equity: **85%** of portfolio value
- Min cash reserve: **15%** of portfolio value
- Max number of positions: **10** different stocks
- Trade cooldown: **24 hours** per symbol

**Example Calculation:**
```python
# Portfolio: $10,000
max_per_stock = 10000 * 0.15 = $1,500
min_cash_reserve = 10000 * 0.15 = $1,500
available_for_trading = 10000 - 1500 = $8,500

# If NVDA costs $122.50
max_quantity = floor(1500 / 122.50) = 12 shares
max_cost = 12 * 122.50 = $1,470

# Check: $1,470 < $1,500 ✅
```

</details>

---

## 📡 API Endpoints

<details>
<summary><b>Complete API Reference (Developer Only - Click to expand)</b></summary>

### Portfolio & Trading

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/portfolio/state` | Current portfolio state |
| `GET` | `/api/portfolio/real-time` | Real-time portfolio with live prices |
| `GET` | `/api/portfolio/equity-history` | Historical net value curve |
| `POST` | `/api/trading/execute-trade` | Execute full trading cycle |
| `POST` | `/api/portfolio/initialize` | Reset portfolio to initial state |

**Example**:
```bash
# Get real-time portfolio
curl http://localhost:8000/api/portfolio/real-time

# Returns:
{
  "total_value": 11250.00,
  "cash": 2500.00,
  "equity_value": 8750.00,
  "positions_count": 3,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 120.00,
      "current_price": 122.50,
      "market_value": 1225.00,
      "unrealized_pnl": 25.00,
      "unrealized_pnl_pct": 2.08
    },
    ...
  },
  "total_unrealized_pnl": 250.00,
  "total_unrealized_pnl_pct": 2.86
}
```

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/status` | Check if market is open |
| `GET` | `/api/market/universe` | Get NASDAQ-100 universe |
| `GET` | `/api/market/price/{symbol}` | Current price for symbol |
| `GET` | `/api/vix/term` | VIX term structure |

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/orders/pending` | Get pending orders |
| `POST` | `/api/orders/check-fills` | Check and execute pending orders |
| `GET` | `/api/orders/history` | Order history |

### Conversations & Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/conversations` | Get agent discussions |
| `GET` | `/api/trades/history` | Trade log |
| `GET` | `/api/logs/list` | List all log files |

### Full API Documentation

For complete API documentation with request/response schemas:
```bash
# Start API server
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000

# Access Swagger UI
http://localhost:8000/docs

# Access ReDoc
http://localhost:8000/redoc
```

</details>

**Quick Access**: All API endpoints are available via Swagger UI at `http://localhost:8000/docs` when the backend is running.

For complete API documentation, see: [📖 API Reference](docs/API_REFERENCE.md)

---

## 🎨 Frontend Features

<details>
<summary><b>Frontend Dashboard Details (Developer Only - Click to expand)</b></summary>

### Dashboard Components

#### 1. **Quick Navigation Bar**
- Smooth scroll to any section
- Always visible at top
- Sections: Summary, Holdings, Execution, Trades, Net Value, Conversations

#### 2. **Summary Cards**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Total Value │    Cash     │   Equity    │    P&L      │
│  $11,250    │   $2,500    │   $8,750    │  +$1,250    │
│             │ (Highlight) │             │   +12.5%    │
└─────────────┴─────────────┴─────────────┴─────────────┘

┌─────────────┬─────────────┐
│  VIX Index  │  Positions  │
│    18.5     │      3      │
│  Contango   │  Max: 10    │
└─────────────┴─────────────┘
```

#### 3. **Holdings Table**
- Real-time prices via yfinance
- Unrealized P&L calculation
- Pie chart distribution
- Sortable columns

#### 4. **Execution Details**
- Order status (Pending/Filled)
- Status lights (🟡 Pending, 🟢 Filled, 🔴 Failed)
- Price ranges for limit orders
- Rationale for each order

#### 5. **Net Value Curve**
- Chart.js line chart
- Linear/Log scale toggle
- Hover for exact values
- Performance metrics

#### 6. **Conversation Panel**
- Real-time agent discussions
- Color-coded by agent type
- Tool usage indicators
- Collapsible sections

#### 7. **Equity Chart Enhancements** ⭐ New
- **Eastern Time Display**: All timestamps displayed in EST/EDT with automatic DST handling
- **Robust Time Parsing**: Handles timestamps with or without timezone information
- **Time Format**: X-axis shows `Month Day HH:MM` (e.g., "Nov 10 14:30")
- **Tooltip Details**: Full timestamp with seconds on hover
- **Data Recording Optimization**: Limits recording frequency to prevent excessive data points

### UI Theme

**Dark Tech Style**:
- Background: `#0a0a0a` (deep black)
- Cards: `rgba(20, 20, 25, 0.8)` (dark with transparency)
- Accent: `#22d3ee` (cyan)
- Text: `#e5e7eb` (light gray)
- Borders: Gradient cyan
- Effects: Glassmorphism, neon glow, smooth animations

</details>

**User-facing**: Access the dashboard at `http://localhost:3000/monitor.html` or via GitHub Pages after deployment.

---

## ⚙️ Configuration

### Main Config File: `backend/config/config.json`

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  "universe": ["NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", ...],
  "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", ...],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03,
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 15,
  "llm": {
    "default_model": "deepseek-r1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

**Key Parameters:**
- `universe`: List of stock symbols to trade (includes inverse/leveraged ETFs like SQQQ, TQQQ)
- `crypto`: List of cryptocurrency symbols (optional)
- `initial_cash`: Starting capital ($10,000 default)
- `position_limit_per_stock`: Max 15% per stock (guideline for agent decision-making)
- `position_limit_total`: Max 85% total equity (guideline, leaves 15% cash reserve)
- `position_limit_min_per_stock`: Min 3% per stock (for diversification)
- `discussion_rounds`: Number of discussion rounds (3 default)
- `discussion_tool_budget`: Max tool calls per cycle (15 default)
- `llm.default_model`: LLM model to use (`deepseek-r1` default)
- `llm.timeout_seconds`: Request timeout (8.0 seconds default)

---

### Agent Config: `backend/config/agents.yaml`

```yaml
market_analyst:
  name: Market Analyst
  model: deepseek-r1
  temperature: 0.3
  prompt_file: ../prompts/market_analyst.yml

technical_analyst:
  name: Technical Analyst
  model: deepseek-r1
  temperature: 0.2
  prompt_file: ../prompts/technical_analyst.yml

# ... (6 agents total)
```

---

### Environment Variables

```bash
# Required for Ollama
OLLAMA_HOST=http://localhost:11434  # Default

# Optional: FRED API
FRED_API_KEY=your_api_key_here

# Optional: Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## 🧪 Testing

### Comprehensive Testing Framework

The system includes a comprehensive 4-round testing framework:

#### Round 1: Backend API Testing ✅
```bash
cd backend
python test_comprehensive.py
```
- Tests all API endpoints
- Validates data formats
- Checks file consistency
- **Result**: 9/9 tests passed (100%)

#### Round 2: Frontend Functionality Testing ✅
```bash
cd backend
python test_frontend_comprehensive.py
```
- Tests all button functionality
- Validates data display
- Checks error handling
- Tests UI/UX features
- **Result**: 22/22 tests passed (100%)

#### Round 3: Data Recording Scenarios (Next)
- Tests initialization data recording
- Tests trading cycle data recording
- Validates equity history updates
- Checks conversation logging

#### Round 4: Frontend-Backend Integration
- End-to-end workflow testing
- Real-time data synchronization
- Order execution flow
- Portfolio updates

### Quick Tests

**1. Tool Test (No LLM Required)**
```bash
cd backend
python test_agent_tools.py
```

**2. Scenario-Based Testing**
```bash
cd backend
# Run all scenarios (1-12)
python test_scenarios.py --scenario 1 --auto
python test_scenarios.py --scenario 2 --auto
# ... see TEST_COMMANDS.md for full list
```

**3. Manual Testing via API**
```bash
# Initialize system
curl -X POST http://localhost:8000/api/system/init

# Execute trading cycle
curl -X POST http://localhost:8000/api/trading/execute-trade

# Check portfolio
curl http://localhost:8000/api/portfolio/real-time
```

### Test Documentation

- **Test Commands**: `backend/TEST_COMMANDS.md` - All test commands
- **Testing Guide**: `backend/COMPREHENSIVE_TESTING_GUIDE.md` - Complete testing guide
- **Round 1 Report**: `backend/TEST_ROUND_1_REPORT.md` - Backend API test results
- **Round 2 Report**: `backend/TEST_ROUND_2_REPORT.md` - Frontend test results

---

## 🚀 Deployment & Sharing

### GitHub Pages Deployment (Frontend) ⭐ New

Deploy the frontend to GitHub Pages so others can access it via browser (like https://hkuds.github.io/AI-Trader/portfolio.html):

#### Quick Deployment Steps (5 minutes)

1. **Push to GitHub** (if not already done)
   ```powershell
   git add .
   git commit -m "Prepare for GitHub Pages"
   git push origin main
   ```

2. **Enable GitHub Pages**
   - Go to repository: `https://github.com/your-username/ai-trader-ollama`
   - Click **Settings** → **Pages**
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/frontend`
   - Click **Save**

3. **Wait for Deployment** (1-2 minutes)
   - GitHub Actions will automatically deploy
   - You'll see a green success message
   - Get your public URL: `https://your-username.github.io/ai-trader-ollama/monitor.html`

4. **Configure Backend API Address**
   - Edit `frontend/config.js`
   - Update `production` to your backend API address:
   ```javascript
   production: 'https://your-railway-app.railway.app',  // Or ngrok URL
   ```
   - Commit and push:
   ```powershell
   git add frontend/config.js
   git commit -m "Configure API for GitHub Pages"
   git push origin main
   ```

5. **Deploy Backend** (Choose one):
   - **Option A**: Use ngrok (quick test, 5 minutes) - See [Backend Deployment Guide](docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md)
   - **Option B**: Deploy to Railway (stable, recommended) - See [Backend Deployment Guide](docs/BACKEND_DEPLOYMENT_STEP_BY_STEP.md)

6. **Access Your Website**:
   ```
   https://your-username.github.io/ai-trader-ollama/monitor.html
   ```

**Example** (if your username is `WenyuChiou`):
```
https://WenyuChiou.github.io/ai-trader-ollama/monitor.html
```

**Now anyone can access your website via the internet!** ✅

**Features**:
- ✅ Automatic deployment via GitHub Actions
- ✅ Auto HTTPS (no SSL configuration needed)
- ✅ Auto-update on every push
- ✅ Read-only mode for security
- ✅ Professional public URL

**For detailed guide, see**: [📖 GitHub Pages Setup Guide](docs/GITHUB_PAGES_SETUP.md)

#### Backend Deployment Options

**Option 1: Railway (Recommended) ⭐⭐⭐⭐⭐**
- $5/month free credit (usually enough)
- 24/7 running (no sleep)
- Auto-deployment
- Fixed URL

**Option 2: Render (Completely Free) ⭐⭐⭐⭐**
- Free tier available
- Auto-deployment
- ⚠️ Sleeps after 15 min inactivity (slow wake-up)

**Option 3: Fly.io (Free Tier) ⭐⭐⭐**
- Free tier available
- Global deployment
- Requires Dockerfile

**For complete free deployment options, see**: [📖 Free Deployment Options Guide](docs/FREE_DEPLOYMENT_OPTIONS.md)

For detailed deployment guide, see: [📖 GitHub Deployment Guide](docs/GITHUB_DEPLOYMENT.md)

### 🌐 Access Methods Comparison

| Access Method | Frontend URL | Use Case | Configuration Difficulty | Security | Internet Access |
|--------------|--------------|----------|-------------------------|----------|----------------|
| **Public Access** | `https://username.github.io/ai-trader-ollama/monitor.html` | Share with anyone, internet access | ⭐⭐ | Read-only mode | ✅ Yes |
| **LAN Access** | `http://192.168.x.x:3000/monitor.html` | Same WiFi/network, local sharing | ⭐ | 🔒 Read-only mode (automatic) | ❌ No (same network only) |
| **Local Access** | `http://localhost:3000/monitor.html` | Personal use only | ⭐ | ✅ Full control | ❌ No (local only) |

**🔒 Read-Only Mode**: When accessing via IP address (shared website), the system automatically enables read-only mode:
- ✅ View all data (portfolio, trades, conversations)
- ✅ Refresh data
- ❌ Cannot execute trades
- ❌ Cannot initialize system
- ❌ Cannot start auto-trade

**✅ Full Control Mode**: When accessing via `localhost` or `127.0.0.1`:
- ✅ All features available
- ✅ Can execute trades
- ✅ Can initialize system
- ✅ Can start auto-trade

**API Address Auto-Detection**: The frontend automatically detects the access method and uses the correct backend API address:
- `localhost` → `http://127.0.0.1:8000`
- IP address → `http://IP:8000` (same IP, port 8000)
- Hostname → `http://hostname:8000`

### 🌍 Public Internet Access (Different Network)

**Problem**: LAN access (`http://192.168.x.x:3000`) only works on the same network. People on different networks cannot access.

**Solutions**:

#### Option 1: Use ngrok (Easiest, 5 minutes) ⭐ Recommended

1. **Download ngrok**: https://ngrok.com/
2. **Start backend**:
   ```powershell
   python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
   ```
3. **Start ngrok** (new terminal):
   ```powershell
   ngrok http 8000
   ```
4. **Copy the public URL** (e.g., `https://abc123.ngrok.io`)
5. **Update `frontend/config.js`**:
   ```javascript
   production: 'https://abc123.ngrok.io'
   ```
6. **Share the link** - Anyone can access via internet! ✅

**Pros**: Free, easy, quick setup  
**Cons**: URL changes each restart (free version)

#### Option 2: Deploy to Cloud (Railway + GitHub Pages) ⭐⭐⭐ Best for Long-term

1. **Deploy backend to Railway**: https://railway.app/
   - Connect GitHub repo
   - Auto-deploy
   - Get public URL (e.g., `https://ai-trader.railway.app`)

2. **Deploy frontend to GitHub Pages**:
   - Settings → Pages → Enable
   - Get public URL (e.g., `https://username.github.io/ai-trader-ollama/monitor.html`)

3. **Update `frontend/config.js`** with Railway URL

**Pros**: Stable, fixed URL, 24/7 running  
**Cons**: Requires GitHub account, some setup time

**For detailed guide, see**: [📖 Public Access Guide](docs/PUBLIC_ACCESS_GUIDE.md)

### 🤔 FAQ: Do I still need LAN sharing after deploying to Railway?

**Answer**: **Not required, but you can keep it for quick local testing.**

If you've deployed to **GitHub Pages + Railway**:
- ✅ **Public access**: Anyone can access via `https://username.github.io/...`
- ❌ **LAN sharing**: Not required (public access covers all scenarios)

**But you can keep LAN sharing for**:
- 🏠 Quick local testing (without waiting for GitHub Pages deployment)
- 🏢 Office-only sharing (without exposing to public internet)
- 💻 Development debugging (quickly share with colleagues)

**Recommendation**: Use **GitHub Pages + Railway** as the main method. Keep LAN sharing as an optional backup for quick local testing.

**For detailed scenarios, see**: [📖 Deployment Scenarios Guide](docs/DEPLOYMENT_SCENARIOS.md)

### ⚠️ Local Sharing (Deprecated - Use GitHub Pages + Railway Instead)

**Note**: LAN sharing is deprecated. **Recommended**: Use **GitHub Pages + Railway** for public access.

**Why deprecated?**
- ❌ Only works on same network
- ❌ Requires your computer to run continuously
- ❌ IP address may change
- ❌ Complex configuration

**Recommended alternative**: See [GitHub Pages Deployment](#github-pages-deployment-frontend--new) above.

---

<details>
<summary><b>Old LAN Sharing Instructions (Deprecated - Click to expand)</b></summary>

If you still need LAN sharing for quick local testing:

1. **Start Backend (Allow LAN Access)**
   ```powershell
   .\scripts\restart_api_fast.ps1
   ```

2. **Start Frontend (Allow LAN Access)**
   ```powershell
   # Use script (recommended - runs in new window)
   powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_share.ps1
   
   # Or manually (keep window open)
   cd frontend
   python -m http.server 3000
   ```

3. **Get Share Link**
   ```powershell
   .\scripts\get_share_link.ps1
   ```

**LAN Access Address Examples**:
```
http://192.168.4.24:3000/monitor.html  # Frontend (replace with your actual IP)
http://192.168.4.24:8000/docs           # API Documentation (replace with your actual IP)
```

**⚠️ Note**: These scripts are deprecated. Use GitHub Pages + Railway instead.

</details>

**To get your actual IP address**:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
```

For detailed instructions, see: [📖 Sharing Access Guide](docs/SHARING_ACCESS.md)

---

## 📂 Project Structure

```
ai-trader-ollama/
├── backend/
│   ├── config/
│   │   ├── agents.yaml          # Agent configurations
│   │   ├── config.json          # Trading parameters
│   │   └── universe.json        # NASDAQ-100 symbols (118)
│   ├── prompts/
│   │   ├── market_analyst.yml   # Market Analyst prompt
│   │   ├── technical_analyst.yml
│   │   ├── fundamental_analyst.yml
│   │   ├── sentiment_analyst.yml
│   │   ├── risk_analyst.yml
│   │   ├── discussion_agent.yml
│   │   └── trader_agent.yml
│   ├── src/
│   │   ├── agents/
│   │   │   ├── base.py              # BaseAgent class
│   │   │   ├── factory.py           # AgentFactory
│   │   │   ├── toolbox.py           # ToolBox (23 tools)
│   │   │   ├── multi_analyst_system.py  # 🆕 Multi-analyst coordinator
│   │   │   ├── risk_analyst_llm.py  # 🆕 LLM-powered Risk Analyst
│   │   │   ├── trader_agent.py      # Trader logic
│   │   │   └── analyst_discussion.py # Legacy (replaced)
│   │   ├── tools/
│   │   │   ├── market_tools.py      # Market data fetching
│   │   │   ├── sentiment_tools.py   # VIX, Fear & Greed
│   │   │   ├── analysis_tools.py    # Risk scores
│   │   │   ├── news_tools.py        # News scanning
│   │   │   ├── crypto_tools.py      # Crypto data
│   │   │   ├── jin10_tools.py       # Jin10 news
│   │   │   ├── economic_indicators.py  # FRED API
│   │   │   ├── technical_indicators.py  # 🆕 Advanced indicators
│   │   │   ├── fundamental_data.py      # 🆕 Fundamentals & earnings
│   │   │   └── market_indicators.py     # 🆕 Breadth, sectors, correlations
│   │   ├── data/
│   │   │   ├── portfolio.py         # Portfolio management
│   │   │   ├── trade_log.py         # Trade logging
│   │   │   ├── order_manager.py     # Order management
│   │   │   ├── equity_tracker.py    # Net value history
│   │   │   ├── memory_manager.py    # Historical memory
│   │   │   └── trade_history_tracker.py  # Cooldown tracking
│   │   ├── orchestrator/
│   │   │   └── trading_cycle.py     # Main trading cycle
│   │   ├── api/
│   │   │   └── server.py            # FastAPI server
│   │   └── utils/
│   │       ├── validators.py        # JSON validation
│   │       └── config_loader.py     # Config loading
│   ├── data/
│   │   └── logs/
│   │       ├── portfolio_state.json      # Current portfolio
│   │       ├── equity_history.jsonl      # Net value history
│   │       ├── discussion_actions.jsonl  # Agent conversations
│   │       ├── trade_log.jsonl           # Trade history
│   │       ├── pending_orders/           # Pending orders by date
│   │       └── memory/                   # Daily memory snapshots
│   ├── scripts/
│   │   ├── init_data.py             # Initialize system
│   │   ├── start_api.py             # Start API server
│   │   └── check_pending_orders.py  # Check order fills
│   ├── test_agent_tools.py          # Tool tests
│   ├── test_multi_analyst_system.py # 🆕 Multi-analyst tests
│   ├── test_complete_agent_loop.py  # 🆕 Full cycle tests
│   ├── test_scenarios.py            # 🆕 Scenario tests (to be created)
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── monitor.html                 # Main dashboard
│   ├── favicon.svg                  # Favicon
│   └── (no build step required)
├── docs/
│   ├── AGENT_SYSTEM.md              # Agent documentation
│   ├── API_REFERENCE.md             # API documentation
│   ├── TOOLS.md                     # Tool documentation
│   └── ARCHITECTURE.md              # System architecture
└── README.md                        # This file
```

---

## 🚀 Advanced Features

### 1. Historical Memory System

**Purpose**: Learn from past trading days

**Implementation**:
```python
# Load recent memories (past 5 days)
memories = memory_manager.load_recent_memories(days=5, summary_only=True)

# Each memory contains:
{
  "date": "2025-01-06",
  "summary": {
    "final_stance": "bullish",
    "portfolio_value": 11250.00,
    "executed_trades": [...],
    "key_insights": "..."
  }
}

# Inject into discussion prompt
discussion_result = run_multi_analyst_discussion(
    market_view=market_data,
    historical_memories=memories  # Context for agents
)
```

---

### 2. Trade Cooldown Management

**Purpose**: Prevent over-trading

**Implementation**:
```python
# Check cooldown (24 hours default)
can_trade, hours_remaining = trade_history.can_trade(symbol="NVDA", cooldown_hours=24.0)

if not can_trade:
    print(f"NVDA on cooldown: {hours_remaining:.1f} hours remaining")
    # Skip this trade
```

---

### 3. Dynamic Position Sizing

**Formula**:
```python
# Calculate position size based on risk and portfolio value
base_size = portfolio_value * 0.10  # 10% base allocation

# Adjust based on:
# 1. Signal strength (0-10)
signal_adjustment = signal_score / 10.0

# 2. Risk level (higher risk = smaller position)
risk_adjustment = 1.0 - (risk_score / 20.0)

# 3. Current exposure
exposure_adjustment = 1.0 - (current_exposure / max_total_position)

# Final size
final_size = base_size * signal_adjustment * risk_adjustment * exposure_adjustment

# Cap at 15% per stock
final_size = min(final_size, portfolio_value * 0.15)
```

---

### 4. Price Range Triggers

**For Pending Orders**:
```python
# When market opens, check if price is within range
if price_min <= current_price <= price_max:
    # Execute order
    portfolio.buy(symbol, quantity, price=current_price)
    order.status = "FILLED"
else:
    # Keep pending or cancel if too far from target
    if abs(current_price - target_price) / target_price > 0.05:
        order.status = "CANCELLED"
        order.reason = "Price moved too far from target"
```

---

### 5. Real-time Portfolio Valuation

**Using yfinance**:
```python
# Update portfolio with live prices
for symbol, position in portfolio.positions.items():
    ticker = yf.Ticker(symbol)
    current_price = ticker.history(period="1d")['Close'].iloc[-1]
    
    position.current_price = current_price
    position.market_value = position.quantity * current_price
    position.unrealized_pnl = position.market_value - position.cost_basis

# Calculate total portfolio value
portfolio.total_value = portfolio.cash + sum(pos.market_value for pos in positions)
```

---

## 🔄 Long-Term Operation & Best Practices

### 🚀 Quick Start: How to Run Long-Term

#### Step 1: Start Backend API (Required)

**Important**: Scripts are in the **project root** `scripts/` folder, not `backend/scripts/`.

**Open PowerShell and run**:
```powershell
# Navigate to project ROOT directory (not backend/)
cd "path\to\ai-trader-ollama"

# Start API with auto-restart (recommended for long-term)
.\scripts\start_api_stable_bypass.ps1
```

**If you're in the backend directory**:
```powershell
# Go back to project root first
cd ..

# Then run the script
.\scripts\start_api_stable_bypass.ps1
```

**Or use full path from anywhere**:
```powershell
# Replace with your actual project path
& "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\scripts\start_api_stable_bypass.ps1"
```

**What this does**:
- ✅ Starts backend API server on port 8000
- ✅ Auto-restarts if it crashes (up to 10 times)
- ✅ Logs all operations for troubleshooting
- ✅ Keeps running even if you close the terminal

**Verify it's running** (Monitoring Steps):

**Step 1: Check API Status** (Browser):
```
Open: http://localhost:8000/api/status
Expected: {"ok": true, "status": "running"}
```

**Step 2: Check API Documentation** (Browser):
```
Open: http://localhost:8000/docs
Expected: Swagger UI interface showing all API endpoints
```

**Step 3: Check Port** (PowerShell):
```powershell
# Check if port 8000 is listening
netstat -ano | findstr 8000

# Should show: TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING
```

**Step 4: Test API Endpoint** (PowerShell):
```powershell
# Test status endpoint
curl http://localhost:8000/api/status

# Or test with Invoke-WebRequest
$response = Invoke-WebRequest -Uri http://localhost:8000/api/status
$response.Content
```

**If API is NOT running**, you'll see:
- ❌ Connection refused / Connection timeout
- ❌ Port 8000 not in `netstat` output
- ❌ Browser shows "This site can't be reached" or "ERR_CONNECTION_REFUSED"

**Troubleshooting**:
- If port 8000 is already in use, stop the old process first
- Check the PowerShell window where API is running for error messages
- Verify Python environment is activated
- Check if Ollama is running (required for LLM agents)

#### Step 2: Enable Auto Trading (Optional but Recommended)

1. Open dashboard: `http://localhost:3000/monitor.html`
2. Click **"▶️ Start Auto Trade"** button
3. System will automatically:
   - Execute trading cycles every 1 hour (during market hours)
   - Check tomorrow planning every 1 hour (during non-trading hours)
   - Refresh data every 30 seconds

**You can now close the browser** - backend continues running!

<details>
<summary><b>Frontend Setup (Developer Only - Click to expand)</b></summary>

```powershell
# In a new terminal
cd frontend
python -m http.server 3000
```

</details>

#### Step 3: Monitor System (Daily Check)

**Quick Status Check**:
```powershell
# Check if API is running
curl http://localhost:8000/api/status

# Or open in browser
start http://localhost:8000/api/status
```

**View Portfolio**:
- Open dashboard: `http://localhost:3000/monitor.html`
- All data will be up-to-date (even if you closed it before)

#### Step 4: Maintenance (Weekly/Monthly)

**Clean old memory files** (optional):
```powershell
python scripts/cleanup_old_memory.py
```

**Check system health**:
- Review error logs (if any)
- Check disk space
- Verify orders are executing

---

### Running the System Continuously

The system is designed to run continuously for extended periods. Here are the key considerations and best practices:

#### ✅ **What Runs Automatically**

1. **Memory Management**
   - ✅ Discussion history automatically limited to 20 entries
   - ✅ Automatic garbage collection after each trading cycle
   - ✅ Temporary data cleaned up automatically
   - ✅ No memory leaks from conversation history

2. **Trading Operations**
   - ✅ Automatic order fill checking (every 30 seconds during market hours)
   - ✅ Automatic trading cycle execution (every 1 hour during market hours)
   - ✅ Automatic tomorrow planning check (every 1 hour during non-trading hours)
   - ✅ Portfolio state automatically saved after each operation

3. **Data Refresh**
   - ✅ Frontend auto-refreshes data every 30 seconds
   - ✅ Backend continuously monitors market status
   - ✅ Automatic transition between trading and non-trading modes

#### ⚠️ **Important Considerations**

##### 1. **Backend API Server** (Must Keep Running)

**Critical**: The backend API server must remain running at all times.

**Recommended Setup**:
```powershell
# Use stable startup script with auto-restart
.\scripts\start_api_stable_bypass.ps1
```

**Features**:
- ✅ Auto-restart on crash (up to 10 times)
- ✅ Complete error handling
- ✅ Logging for troubleshooting
- ✅ Suitable for long-term operation

**Monitoring**:
- Check API status: `http://localhost:8000/api/status`
- Check logs for errors
- Verify orders are being executed correctly

##### 2. **Frontend Dashboard** (Can Be Closed)

**✅ You can close the dashboard** - it won't affect backend operations.

**Why**:
- Dashboard is **display-only** - it doesn't execute trading logic
- All trading logic runs in the backend
- Backend continues to:
  - Execute trading cycles
  - Check order fills
  - Plan for tomorrow
  - Save all data

**Behavior When Closed**:
- ✅ Backend continues hourly trading cycles (market hours)
- ✅ Backend continues hourly planning checks (non-trading hours)
- ✅ All data saved to files
- ❌ Dashboard stops refreshing (no impact on backend)

**When You Reopen**:
- ✅ Automatically loads latest data
- ✅ All functions restored
- ✅ Shows complete history

##### 3. **System Resources**

**Memory Usage**:
- ✅ Auto-limited discussion history (20 entries max)
- ✅ Automatic garbage collection
- ✅ No memory leaks
- ⚠️ Memory files accumulate on disk (doesn't affect performance)

**Disk Space**:
- ⚠️ `discussion_actions.jsonl` grows continuously
- ⚠️ `memory/daily/` creates one file per day
- ⚠️ `equity_history.jsonl` grows with each record
- **Recommendation**: Periodically clean old files (see below)

**Cleanup Script**:
```powershell
# Clean up old memory files (before today)
python scripts/cleanup_old_memory.py
```

##### 4. **Network Connection**

**Required**:
- ✅ Backend needs internet connection for market data
- ✅ yfinance requires network access
- ⚠️ If network fails, tool calls will fail (but system won't crash)

**Handling Network Issues**:
- System will retry on next cycle
- Errors logged for review
- No data loss (all state saved to files)

##### 5. **System Time**

**Critical**: System time must be accurate.

**Why**:
- Used to determine trading hours
- Used for order timestamps
- Used for equity history recording

**Check**:
```powershell
# Verify system time is correct
Get-Date
```

#### 📋 **Long-Term Operation Checklist**

##### **Daily Checks** (Recommended)

- [ ] Verify backend API is running (`http://localhost:8000/api/status`)
- [ ] Check for error logs
- [ ] Verify orders are executing correctly
- [ ] Check portfolio state is normal

##### **Weekly Checks** (Recommended)

- [ ] Check `discussion_actions.jsonl` file size
- [ ] Check memory file count in `backend/data/logs/memory/daily/`
- [ ] Check disk space
- [ ] Review error logs for patterns
- [ ] Consider cleaning old memory files if needed

##### **Monthly Checks** (Recommended)

- [ ] Review system performance
- [ ] Check log file sizes
- [ ] Backup important data
- [ ] Clean old memory files (keep last 30 days)
- [ ] Review trading performance

#### 🧹 **Memory File Cleanup**

**Automatic Cleanup** (Already Implemented):
- ✅ In-memory `discussion_history` limited to 20 entries
- ✅ Automatic garbage collection after each cycle
- ✅ Discussion history reinitialized each cycle

**Manual Cleanup** (Optional):

**Option 1: Clean Old Daily Memory Files**
```powershell
# Delete memory files before today
python scripts/cleanup_old_memory.py
```

**Option 2: Full System Reset**
```bash
# WARNING: This clears ALL data
# Use frontend "Initialize System" button
# Or via API:
curl -X POST http://localhost:8000/api/system/init
```

**Option 3: Selective Cleanup**
```powershell
# Keep last 30 days, delete older files
# (Manual file deletion - be careful!)
```

#### 💡 **Best Practices**

1. **Startup**:
   - Always use `start_api_stable_bypass.ps1` for long-term operation
   - Verify API is running before leaving system unattended
   - Keep the PowerShell window open (or minimize it)

2. **Monitoring**:
   - Check API status daily: `http://localhost:8000/api/status`
   - Review error logs weekly
   - Monitor disk space monthly
   - Use dashboard for visual monitoring: `http://localhost:3000/monitor.html`

3. **Dashboard**:
   - Can be closed when not needed
   - Reopen anytime to check status
   - No impact on backend operations
   - Auto-refreshes when open

4. **Backup**:
   - Periodically backup `backend/data/logs/` directory
   - Especially before major operations (e.g., system init)
   - Backup portfolio state before major changes

5. **Maintenance**:
   - Clean old memory files monthly: `python scripts/cleanup_old_memory.py`
   - Review and archive old logs quarterly
   - Keep system time synchronized
   - Restart API weekly (optional, for fresh start)

#### 📝 **Daily Usage Example**

**Morning (Before Market Opens)**:
```powershell
# 1. Check if API is still running
curl http://localhost:8000/api/status

# 2. If not running, restart
.\scripts\restart_api_fast.ps1

# 3. Open dashboard to check status
start http://localhost:3000/monitor.html
```

**During Market Hours**:
- System automatically executes trading cycles every hour
- No action needed - just let it run
- Check frontend occasionally to monitor progress

**Evening (After Market Closes)**:
- System automatically checks for tomorrow planning
- No action needed
- Can close frontend - backend continues

**Weekly Maintenance**:
```powershell
# Clean old memory files
python scripts/cleanup_old_memory.py

# Check system health
curl http://localhost:8000/api/system/info
```

#### ⚡ **Common Operations**

**Restart Backend** (if needed):
```powershell
# From project root directory
.\scripts\restart_api_fast.ps1

# Or with full path
powershell -ExecutionPolicy Bypass -File "path\to\ai-trader-ollama\scripts\restart_api_fast.ps1"
```

**Stop Backend** (temporarily):
```powershell
# Find and stop the process
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

**View Share Links** (for local network):
```powershell
.\scripts\get_share_link.ps1
```

**Check System Info**:
```powershell
# Via browser
start http://localhost:8000/api/system/info

# Or via curl
curl http://localhost:8000/api/system/info
```

#### 🔍 **Troubleshooting Long-Term Issues**

**Issue**: Backend stops responding
- **Solution**: Use `restart_api_fast.ps1` to restart
- **Prevention**: Use `start_api_stable_bypass.ps1` (auto-restart)

**Issue**: Disk space running low
- **Solution**: Run `cleanup_old_memory.py` to remove old files
- **Prevention**: Set up monthly cleanup schedule

**Issue**: Memory usage high
- **Solution**: System auto-manages memory, but check for memory leaks
- **Prevention**: Ensure using latest code with memory optimizations

**Issue**: Network connection lost
- **Solution**: System will retry on next cycle
- **Prevention**: Ensure stable internet connection

---

## ❓ Troubleshooting

### Common Issues

#### 1. **Ollama Connection Error**

**Error**: `Failed to connect to Ollama`

**Solutions**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# If not running, start it
ollama serve

# Check if model is pulled
ollama list

# If deepseek-r1 not listed, pull it
ollama pull deepseek-r1
```

---

#### 2. **FRED API Errors**

**Error**: `FRED API key not found` or `401 Unauthorized`

**Solutions**:
```bash
# Set API key
export FRED_API_KEY=your_key_here

# Verify it's set
echo $FRED_API_KEY

# For Windows PowerShell:
$env:FRED_API_KEY="your_key_here"
```

---

#### 3. **Dashboard CORS Errors**

**Error**: `Access to fetch at 'file://...' has been blocked by CORS`

**Solution**: Access via HTTP server, not directly:
```
http://localhost:3000/monitor.html
```

<details>
<summary><b>Frontend Setup (Developer Only - Click to expand)</b></summary>

```bash
cd frontend
python -m http.server 3000
```

</details>

---

#### 4. **Portfolio State Not Found**

**Error**: `FileNotFoundError: portfolio_state.json`

**Solution**:
```bash
cd backend
python scripts/init_data.py
```

---

#### 5. **Agent Timeout**

**Error**: Agent takes too long to respond

**Solutions**:
- Reduce `tool_budget` in trading_cycle.py (default: 15)
- Increase Ollama timeout
- Use faster model (e.g., `deepseek-r1:7b` instead of `deepseek-r1:32b`)

---

#### 6. **Memory Errors**

**Error**: `Out of memory` when running LLM

**Solutions**:
```bash
# Use smaller model (if needed)
ollama pull deepseek-r1:7b

# Update agents.yaml (if switching models)
model: deepseek-r1:7b
```

---

#### 7. **Initialization Conflict Detection** ⭐ New

**Function**: Prevents system initialization during active trading/planning operations

**Behavior**:
- When active operations are detected, prompts the user
- Provides options: Cancel or Force initialization
- Force initialization stops all active operations

**Use Case**: Avoid accidentally clearing data during trade execution or auto-planning

---

#### 8. **Restart Backend API (Windows PowerShell)**

**Scenario**: Dashboard shows `Disconnected / Refreshing...` or cannot connect to `http://127.0.0.1:8000`

##### **Quick Restart (Daily Use) ⭐ Recommended**

```powershell
# One-click quick restart (3-5 seconds)
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**Features**:
- ✅ Automatically stops old process
- ✅ Smart port check (max 2 seconds wait)
- ✅ Automatically starts new API
- ✅ Shows share link
- ✅ Total time: ~3-5 seconds

**Output Example**:
```
Restarting API (fast mode)...
[OK] API restarted

Access:
  Local: http://127.0.0.1:8000/docs
  Share: http://192.168.4.24:8000/docs
```

##### **Stable Start (First Start or Need Auto-Restart Feature)**

```powershell
# Stable version start (with auto-restart, error handling)
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1
```

**Features**:
- ✅ Auto-restart on crash (max 10 times)
- ✅ Complete error handling
- ✅ Logging
- ✅ Suitable for long-term operation

##### **View Share Link**

```powershell
# View your share link anytime
powershell -ExecutionPolicy Bypass -File .\scripts\get_share_link.ps1
```

---

## 📖 Documentation

### Detailed Documentation Files

| File | Description |
|------|-------------|
| `docs/AGENT_SYSTEM.md` | Complete agent architecture, prompts, and interaction patterns |
| `docs/API_REFERENCE.md` | Full API endpoint documentation with examples |
| `docs/TOOLS.md` | Detailed documentation for all 23 tools |
| `docs/ARCHITECTURE.md` | System design, data flow, and component interactions |
| `docs/DEPLOYMENT.md` | Production deployment guide |
| `docs/CONTRIBUTING.md` | Contribution guidelines |

### Quick Links

- **Agent Prompts**: `backend/prompts/`
- **Tool Implementations**: `backend/src/tools/`
- **API Server**: `backend/src/api/server.py`
- **Trading Logic**: `backend/src/orchestrator/trading_cycle.py`
- **Dashboard**: `frontend/monitor.html`

---

## 🤝 Contributing

We welcome contributions! Please see `docs/CONTRIBUTING.md` for guidelines.

**Areas for Contribution**:
- New tools (e.g., options data, macro indicators)
- Additional agents (e.g., options trader, macro analyst)
- UI improvements
- Performance optimizations
- Documentation enhancements

---

## 📄 License

MIT License - see `LICENSE` file for details

---

## 🙏 Acknowledgments

- **LangChain**: Agent framework
- **Ollama**: Local LLM inference
- **yfinance**: Market data
- **FRED API**: Economic data
- **Chart.js**: Dashboard charts
- **FastAPI**: Backend API framework

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/WenyuChiou/ai-trader-ollama/issues)
- **Discussions**: [GitHub Discussions](https://github.com/WenyuChiou/ai-trader-ollama/discussions)
- **Email**: wenyuchiou@example.com

---

## 🗺️ Roadmap

### Q1 2025
- ✅ Multi-Analyst System
- ✅ 23 Advanced Tools
- ✅ LLM-powered Risk Analyst
- ✅ Trading Interval Optimization (1 hour)
- ✅ GitHub Pages Deployment
- ✅ Time Display Enhancement (EST/EDT)
- ✅ Memory Management Optimization
- ✅ Initialization Conflict Detection
- 🔄 Scenario-based Testing
- 📋 Dashboard Integration

### Q2 2025
- Options trading capability
- Backtesting framework
- Performance analytics dashboard
- Multi-timeframe analysis
- Portfolio optimization algorithms

### Q3 2025
- Sentiment analysis from social media
- Real-time news alerts
- Advanced order types (stop-loss, trailing stop)
- Portfolio rebalancing automation
- Risk-adjusted performance metrics

---

## 📊 Testing Status

### Current Status: Round 2 Complete ✅

- **Round 1**: Backend API Testing - ✅ 9/9 passed (100%)
- **Round 2**: Dashboard Functionality Testing - ✅ 22/22 passed (100%)
- **Round 3**: Data Recording Scenarios - ⏭️ Next
- **Round 4**: Dashboard-Backend Integration - ⏭️ Pending

See `backend/TESTING_STATUS.md` for detailed testing information.

---

**Built with ❤️ by the AI-Trader Team**

*Empowering traders with AI-driven insights and autonomous decision-making*
