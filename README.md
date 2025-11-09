# 💹 AI-Trader Ollama

> **A Multi-Agent Trading System with 23 Advanced Tools + 6 Specialized LLM Agents**  
> 📈 Analyzing **NASDAQ-100** (118+ symbols) with comprehensive fundamental, technical, and sentiment analysis  
> 🧠 Fully autonomous agent collaboration with real-time market data integration  
> 🎨 Dark tech-themed UI with live visualization and real-time updates

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.1-orange.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
- [Frontend Features](#-frontend-features)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Advanced Features](#-advanced-features)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

---

## 🆕 Latest Updates (January 2025)

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
ollama pull llama3.1
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
cd backend

# Initialize portfolio and data structures
python scripts/init_data.py

# This creates:
# - data/logs/portfolio_state.json (initial $10,000)
# - data/logs/equity_history.jsonl
# - data/logs/discussion_actions.jsonl
# - data/logs/trade_log.jsonl
```

**3. Start Backend API**
```bash
cd backend

# Method 1: Direct Python
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using script
python scripts/start_api.py
```

**4. Start Frontend**
```bash
# In a new terminal
cd frontend
python -m http.server 3000
```

**5. Access Dashboard**
```
Open browser: http://localhost:3000/monitor.html
```

### First Trading Cycle

1. **Check System Status**
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
**Model**: llama3.1 (temperature: 0.3)

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
**Model**: llama3.1 (temperature: 0.2)

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
**Model**: llama3.1 (temperature: 0.2)

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
**Model**: llama3.1 (temperature: 0.3)

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
**Model**: llama3.1 (temperature: 0.2)

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
**Model**: llama3.1 (temperature: 0.25)

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

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Market Analyst                                       │
├─────────────────────────────────────────────────────────────┤
│ • Calls: get_market_indices(), get_sector_rotation(),        │
│          get_economic_summary()                              │
│ • Analyzes: Market regime, sector leadership                 │
│ • Output: "Market is in mid-cycle bull phase, Technology    │
│           and Healthcare leading. GDP growth steady."        │
│ • Stance: risk_on (Score: 7.5/10)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (passes findings to)
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Technical Analyst                                    │
├─────────────────────────────────────────────────────────────┤
│ • Receives: Market Analyst's "risk_on" stance               │
│ • Calls: get_advanced_indicators("NVDA"),                   │
│          get_support_resistance("NVDA")                      │
│ • Analyzes: RSI=65, MACD bullish, above support at 120      │
│ • Output: "Strong momentum, RSI approaching overbought      │
│           but trend intact. Support at 120."                │
│ • Stance: bullish (Score: 8.2/10)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (passes findings to)
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Fundamental Analyst                                  │
├─────────────────────────────────────────────────────────────┤
│ • Receives: Market "risk_on" + Technical "bullish"          │
│ • Calls: get_company_fundamentals("NVDA"),                  │
│          get_earnings_history("NVDA")                        │
│ • Analyzes: P/E=45, earnings growth 55%, ROE=65%            │
│ • Output: "Valuation reasonable given growth. Strong        │
│           earnings quality, beat estimates by 5%."          │
│ • Stance: bullish (Score: 7.8/10)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (passes findings to)
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Sentiment Analyst                                    │
├─────────────────────────────────────────────────────────────┤
│ • Receives: All previous stances (3 bullish)                │
│ • Calls: fear_greed(), vix_term(), news_scan("NVDA")        │
│ • Analyzes: F&G=65 (greed), VIX=18 (low), positive news     │
│ • Output: "Market sentiment bullish but approaching greed.  │
│           Watch for potential reversal signals."            │
│ • Stance: bullish (Score: 6.5/10)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (all stances aggregated)
┌─────────────────────────────────────────────────────────────┐
│ Final Consensus                                              │
├─────────────────────────────────────────────────────────────┤
│ • Votes: 4 bullish / 0 bearish / 0 neutral                  │
│ • Final Stance: BULLISH                                     │
│ • Tool Calls: 12 total (within 15 budget)                   │
│ • Tool Diversity: 8 different tools used                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (passes to Risk Analyst)
┌─────────────────────────────────────────────────────────────┐
│ Risk Analyst (receives consensus + market data)             │
├─────────────────────────────────────────────────────────────┤
│ • Analyzes: Position concentration, market risks            │
│ • Calls: get_correlation_matrix(), vix_term()               │
│ • Output: Position control report, risk-adjusted sizes      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (passes to Trader)
┌─────────────────────────────────────────────────────────────┐
│ Trader Agent (makes final decisions)                        │
├─────────────────────────────────────────────────────────────┤
│ • Inputs: Consensus (bullish) + Risk Report                 │
│ • Decisions: BUY NVDA x10 @ $122.50 (max 15% portfolio)     │
│ • Order Placement: Limit order with price range             │
└─────────────────────────────────────────────────────────────┘
```

### Tool Usage by Agent

| Agent | Priority Tools | Typical # Calls | Focus |
|-------|----------------|-----------------|-------|
| **Market** | market_indices, sector_rotation, economic_summary | 2-3 | Macro environment |
| **Technical** | advanced_indicators, support_resistance | 2-3 | Price action |
| **Fundamental** | company_fundamentals, earnings_history | 2-3 | Valuation |
| **Sentiment** | fear_greed, vix_term, news_scan | 2-3 | Psychology |
| **Risk** | vix_term, correlation_matrix, market_breadth | 2-3 | Risk management |

**Total**: ~12 tool calls per cycle (within 15 budget)  
**Diversity**: 8+ different tools typically used

---

## 📈 Trading Workflow

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

## 📡 API Endpoints

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

---

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/status` | Check if market is open |
| `GET` | `/api/market/universe` | Get NASDAQ-100 universe |
| `GET` | `/api/market/price/{symbol}` | Current price for symbol |
| `GET` | `/api/vix/term` | VIX term structure |

---

### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/orders/pending` | Get pending orders |
| `POST` | `/api/orders/check-fills` | Check and execute pending orders |
| `GET` | `/api/orders/history` | Order history |

---

### Conversations & Logs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/conversations` | Get agent discussions |
| `GET` | `/api/trades/history` | Trade log |
| `GET` | `/api/logs/list` | List all log files |

---

### Full API Documentation

For complete API documentation with request/response schemas:
```bash
# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Access Swagger UI
http://localhost:8000/docs

# Access ReDoc
http://localhost:8000/redoc
```

---

## 🎨 Frontend Features

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

---

### UI Theme

**Dark Tech Style**:
- Background: `#0a0a0a` (deep black)
- Cards: `rgba(20, 20, 25, 0.8)` (dark with transparency)
- Accent: `#22d3ee` (cyan)
- Text: `#e5e7eb` (light gray)
- Borders: Gradient cyan
- Effects: Glassmorphism, neon glow, smooth animations

---

## ⚙️ Configuration

### Main Config File: `backend/config/config.json`

```json
{
  "universe": "nasdaq100",
  "max_positions": 10,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03,
  "min_cash_reserve_ratio": 0.15,
  "trade_cooldown_hours": 24.0,
  "initial_cash": 10000.0,
  "initial_equity": 10000.0
}
```

**Parameters:**
- `max_positions`: Maximum number of different stocks
- `position_limit_per_stock`: Max 15% per stock
- `position_limit_total`: Max 85% total equity
- `min_cash_reserve_ratio`: Keep 15% cash
- `trade_cooldown_hours`: 24h cooldown per symbol
- `initial_cash` / `initial_equity`: Starting capital

---

### Agent Config: `backend/config/agents.yaml`

```yaml
market_analyst:
  name: Market Analyst
  model: llama3.1
  temperature: 0.3
  prompt_file: ../prompts/market_analyst.yml

technical_analyst:
  name: Technical Analyst
  model: llama3.1
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

# If llama3.1 not listed, pull it
ollama pull llama3.1
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

#### 3. **Frontend CORS Errors**

**Error**: `Access to fetch at 'file://...' has been blocked by CORS`

**Solution**: Don't open `monitor.html` directly. Use HTTP server:
```bash
cd frontend
python -m http.server 3000

# Then access: http://localhost:3000/monitor.html
```

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
- Use faster model (e.g., `llama3.1:8b` instead of `llama3.1:70b`)

---

#### 6. **Memory Errors**

**Error**: `Out of memory` when running LLM

**Solutions**:
```bash
# Use smaller model
ollama pull llama3.1:8b

# Update agents.yaml
model: llama3.1:8b
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
- **Frontend**: `frontend/monitor.html`

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
- **Chart.js**: Frontend charts
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
- 🔄 Scenario-based Testing
- 📋 Frontend Integration

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

**Built with ❤️ by the AI-Trader Team**

*Empowering traders with AI-driven insights and autonomous decision-making*
