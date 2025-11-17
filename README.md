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

- [System Overview](#-system-overview)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Data Storage & Records](#-data-storage--records)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [Tool Suite (23 Tools)](#-tool-suite-23-tools)
- [Trading Workflow](#-trading-workflow)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)

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
```

**3. Start Backend API**

```powershell
# Make sure you're in the project ROOT directory (not backend/)
cd "path\to\ai-trader-ollama"

# Method 1: Background Service (Recommended - runs even after closing CMD)
# Option A: Windows Service (requires NSSM)
#   Right-click: scripts\start_api_service_admin.bat → "Run as administrator"

# Option B: Task Scheduler (no additional software needed) ⭐ EASIEST
#   Right-click: scripts\start_api_task_admin.bat → "Run as administrator"

# Method 2: Stable version (with auto-restart, but requires window open)
.\scripts\start_api_stable_bypass.ps1

# Method 3: Fast restart (Daily use, quick restart)
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1

# Method 4: Manual start (Development/Testing)
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**⚠️ Important**: Methods 2-4 require keeping the terminal window open. Use Method 1 for background operation.

**4. Access Dashboard**

**Local Access**:
```
http://localhost:3000/monitor.html
```

**Public Access** (after deployment):
```
https://your-username.github.io/ai-trader-ollama/monitor.html
```

---

## ⚙️ Configuration

### Main Config File: `backend/config/config.json`

The main configuration file controls trading parameters, universe selection, and LLM settings.

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  "universe": ["NVDA", "MSFT", "AAPL", ...],
  "crypto": ["BTC-USD", "ETH-USD", ...],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03,
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 15,
  "max_orders_per_cycle": 20,
  "trade_cooldown_hours": 24.0,
  "llm": {
    "default_model": "deepseek-r1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

#### Key Parameters

**Trading Universe:**
- `universe`: List of stock symbols to trade (includes inverse/leveraged ETFs like SQQQ, TQQQ)
- `crypto`: List of cryptocurrency symbols (optional)
- `universe_limit`: Maximum number of symbols to analyze (default: 100)

**Position Limits:**
- `position_limit_per_stock`: Max 15% per stock (guideline for agent decision-making)
- `position_limit_total`: Max 85% total equity (guideline, leaves 15% cash reserve)
- `position_limit_min_per_stock`: Min 3% per stock (for diversification)

**Trading Behavior:**
- `initial_cash`: Starting capital ($10,000 default)
- `discussion_rounds`: Number of discussion rounds (3 default)
- `discussion_tool_budget`: Max tool calls per cycle (15 default)
- `max_orders_per_cycle`: Maximum orders per trading cycle (20 default)
- `trade_cooldown_hours`: Hours to wait before trading same symbol again (24.0 default)

**LLM Configuration:**
- `llm.default_model`: LLM model to use (`deepseek-r1` default)
  - Available models: `deepseek-r1`, `deepseek-r1:7b`, `deepseek-r1:32b`, etc.
  - To use a different model, change this value and ensure it's pulled in Ollama
- `llm.ollama_host`: Ollama server address (default: `http://localhost:11434`)
- `llm.auto_pull`: Automatically pull model if not found (true default)
- `llm.timeout_seconds`: Request timeout (8.0 seconds default)

#### Changing the LLM Model

**Step 1: Pull the model in Ollama**
```bash
# Pull a different model (example: smaller 7B model)
ollama pull deepseek-r1:7b

# Or use a different model entirely
ollama pull llama3.2
```

**Step 2: Update config.json**
```json
{
  "llm": {
    "default_model": "deepseek-r1:7b",  // Changed from "deepseek-r1"
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

**Step 3: Restart the API**
```powershell
.\scripts\restart_api_fast.ps1
```

**Note**: Different models have different capabilities:
- **Larger models** (32B): Better reasoning, slower, more memory
- **Smaller models** (7B): Faster, less memory, may have lower quality
- **Recommended**: `deepseek-r1` (balanced performance)

### Agent Config: `backend/config/agents.yaml`

Individual agent configurations including model, temperature, and prompt files.

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

**To use different models per agent:**
```yaml
market_analyst:
  model: deepseek-r1:32b  # Use larger model for market analysis
  temperature: 0.3

technical_analyst:
  model: deepseek-r1:7b   # Use smaller model for technical analysis
  temperature: 0.2
```

---

## 💾 Data Storage & Records

### Data Directory Structure

**All agent-generated data, conversations, positions, and trading records are stored in `data/logs/` directory** (relative to project root).

**Path Details:**
- **Project Root**: The directory containing `README.md` and `backend/` folder
- **Data Directory**: `{project_root}/data/logs/`
- **Example**: If project is at `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\`, then data is stored at `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs\`

After each agent execution cycle, the following data is automatically saved:

```
data/logs/
├── portfolio_state.json          # Current portfolio state (cash, positions)
├── equity_history.jsonl          # Net value history (P&L records)
├── discussion_actions.jsonl      # Agent conversations and discussions
├── trades.jsonl                  # Trade execution history
├── filled_orders.jsonl            # Completed orders (with realized P&L)
├── pending_orders.jsonl          # Pending orders
├── memory/
│   ├── daily/                    # Daily memory snapshots
│   │   └── YYYY-MM-DD.json
│   ├── weekly/                   # Weekly summaries
│   ├── monthly/                  # Monthly summaries
│   └── index/                    # Memory indices
└── real_time_snapshots.jsonl     # Real-time portfolio snapshots
```

**Key Points:**
- **Position Information**: Stored in `portfolio_state.json` (current holdings, cash balance)
- **Agent Conversations**: Stored in `discussion_actions.jsonl` (all agent discussions, analyses, and summaries)
- **Trading Records**: Stored in `trades.jsonl` and `filled_orders.jsonl` (execution history and P&L)
- **Memory System**: Stored in `memory/` subdirectories (daily/weekly/monthly snapshots for agent learning)
- **Equity History**: Stored in `equity_history.jsonl` (portfolio value over time)

All files are automatically created and updated by the system. No manual file management is required.

### Portfolio State (`portfolio_state.json`)

**Location**: `data/logs/portfolio_state.json`

**Contains**:
- Current cash balance
- Current positions (symbol, quantity, avg_cost, total_cost)
- Initial value
- Total value

**Format**:
```json
{
  "cash": 2197.50,
  "initial_value": 10000.0,
  "total_value": 8497.50,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "total_cost": 1502.50
    }
  }
}
```

### Equity History (`equity_history.jsonl`)

**Location**: `data/logs/equity_history.jsonl`

**Contains**: Net value (equity) history with P&L records

**Recording Frequency**: Records are automatically saved every **30 minutes** during market hours.

**Format** (JSONL - one record per line):
```json
{
  "date": "2025-01-28",
  "timestamp": "2025-01-28T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -2.50,
  "total_pnl_pct": -0.03,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 150.25,
      "market_value": 1502.50,
      "unrealized_pnl": 0.00,
      "unrealized_pnl_pct": 0.00
    }
  }
}
```

**Fields**:
- `total_pnl`: Total profit/loss in dollars (total_value - initial_value)
- `total_pnl_pct`: Total profit/loss percentage
- `equity_value`: Current market value of all positions
- `total_value`: Cash + equity_value

### Trade History (`trades.jsonl`)

**Location**: `data/logs/trades.jsonl`

**Contains**: All executed trades

**Format**:
```json
{
  "timestamp": "2025-01-28T10:30:00Z",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "price": 150.25,
  "total_cost": 1502.50,
  "status": "FILLED"
}
```

### Filled Orders (`filled_orders.jsonl`)

**Location**: `data/logs/filled_orders.jsonl`

**Contains**: Completed orders with realized P&L (for SELL orders)

**Format**:
```json
{
  "order_id": "order_123",
  "placed_at": "2025-01-28T10:30:00",  # Note: order_date field has been removed, use placed_at instead
  "symbol": "NVDA",
  "action": "SELL",
  "quantity": 10,
  "fill_price": 155.00,
  "status": "FILLED",
  "realized_pnl": 47.50,
  "realized_pnl_pct": 3.16,
  "cost_basis": 1502.50,
  "proceeds": 1550.00
}
```

**P&L Fields** (for SELL orders):
- `realized_pnl`: Realized profit/loss in dollars
- `realized_pnl_pct`: Realized profit/loss percentage
- `cost_basis`: Original purchase cost
- `proceeds`: Sale proceeds

### Memory System (`memory/`)

**Location**: `data/logs/memory/`

**Purpose**: Historical memory for learning from past trades

**Daily Memory** (`memory/daily/YYYY-MM-DD.json`):
- Market view snapshot
- Agent discussions
- Risk reports
- Trading decisions
- Portfolio snapshot
- Executed trades

**Weekly/Monthly Summaries**:
- Aggregated insights
- Performance summaries
- Key learnings

**Usage**: Agents can access recent memories (last 5-7 days) to inform current decisions.

### Agent Conversations (`discussion_actions.jsonl`)

**Location**: `data/logs/discussion_actions.jsonl`

**Contains**: All agent conversations, tool calls, and analysis

**Format**:
```json
{
  "timestamp": "2025-01-28T10:00:00Z",
  "date": "2025-01-28",
  "agent": "MarketAnalyst",
  "round": 0,
  "content": "Market analysis...",
  "type": "discussion",
  "tools_used": ["get_market_indices", "get_sector_rotation"]
}
```

---

## 🤖 Multi-Agent Architecture

### Agent Specifications

#### 1. **Market Analyst** 🌐
- **Specialty**: Macro trends, sector rotation, market structure
- **Priority Tools**: `get_market_indices`, `get_sector_rotation`, `get_market_breadth`, `get_economic_summary`

#### 2. **Technical Analyst** 📈
- **Specialty**: Chart patterns, indicators, support/resistance
- **Priority Tools**: `get_advanced_indicators`, `get_support_resistance`, `vix_term`

#### 3. **Fundamental Analyst** 💼
- **Specialty**: Financial statements, valuation, earnings
- **Priority Tools**: `get_company_fundamentals`, `get_earnings_history`, `get_financial_statements`

#### 4. **Sentiment Analyst** 😊
- **Specialty**: Market psychology, news sentiment, fear/greed
- **Priority Tools**: `fear_greed`, `vix_term`, `news_scan`

#### 5. **Risk Analyst** 🛡️
- **Specialty**: Risk assessment, position management
- **Priority Tools**: `vix_term`, `get_correlation_matrix`, `get_market_breadth`

#### 6. **Trader Agent** 💰
- **Specialty**: Trading decisions, position sizing
- **Type**: LLM-based agent (uses deepseek-r1)
- **Inputs**: 
  - All analyst recommendations (consensus stance, recommended stocks)
  - Risk report (risk level, VIX score, position recommendations)
  - Portfolio state (current positions, available cash, P&L)
  - Market data (current prices, market status)
- **Outputs**: 
  - Buy/sell orders with quantities and prices
  - Rationale (LLM-generated explanation)
  - Risk compliance check
- **Decision Process**: 
  - LLM analyzes all inputs simultaneously
  - Considers hard rules (position limits, cash constraints)
  - Integrates Risk Analyst recommendations
  - Generates natural language rationale

---

## 🛠️ Tool Suite (23 Tools)

### Sentiment & Risk (3 tools)
- `vix_term`: VIX term structure
- `vix_close`: Historical VIX prices
- `fear_greed`: CNN Fear & Greed Index

### News & Information (5 tools)
- `news_scan`: Scan news by keywords
- `plan_and_scan_news`: LLM-powered news query
- `web_search`: DuckDuckGo search
- `fetch_url`: Extract content from URL
- `fetch_jin10_news`: Jin10 financial news

### Economic Data (3 tools)
- `get_economic_summary`: Key US economic indicators
- `get_labor_market_data`: Labor market data
- `fetch_fred_indicator`: Specific FRED indicator

### Technical Indicators (2 tools)
- `get_advanced_indicators`: RSI, MACD, BB, ADX, Stochastic, ATR, OBV
- `get_support_resistance`: Support/resistance levels

### Fundamental Data (3 tools)
- `get_company_fundamentals`: P/E, ROE, profit margins, growth
- `get_earnings_history`: Quarterly/annual earnings
- `get_financial_statements`: Balance sheet, cashflow

### Market Indicators (4 tools)
- `get_market_breadth`: Advancing/declining stocks
- `get_sector_rotation`: 11-sector performance
- `get_correlation_matrix`: Stock correlations
- `get_market_indices`: S&P 500, Dow, NASDAQ, Russell 2000

### Crypto (2 tools)
- `fetch_crypto_batch`: Batch crypto data
- `get_crypto_price`: Single crypto price

### Jin10 (1 tool)
- `fetch_jin10_economic_data`: Economic data from Jin10

---

## 📈 Trading Workflow

### Trading Frequency & Schedule

**Trading Cycle Frequency**: 
- **Market Hours (9:30 AM - 4:00 PM ET)**: Automatic trading runs every **30 minutes**
- **Market Closed**: Analysis runs continuously (every 30 minutes) but **no orders generated**
- **Trading Days Only**: System respects market holidays and weekends

**Schedule Example**:
```
Market Open Day (e.g., Monday):
├── 9:30 AM ET  → First trading cycle (if market opens on time)
├── 10:00 AM ET → Trading cycle
├── 10:30 AM ET → Trading cycle
├── 11:00 AM ET → Trading cycle
├── ... (every 30 minutes)
├── 3:30 PM ET  → Trading cycle
└── 4:00 PM ET  → Last trading cycle (market closes)

Market Closed (e.g., After 4:00 PM or Weekend):
├── Analysis runs every 30 minutes
├── No trading orders generated
└── Results saved for next trading session
```

**Agent Conversation Frequency**:
- **During Market Hours**: Full agent discussions every 30 minutes (4 analysts + coordinator + risk + trader)
- **Market Closed**: Agents still analyze but trader generates no orders
- **Discussion Rounds**: 3 rounds of discussion per cycle (all analysts participate in each round)

### Complete Trading Cycle Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING CYCLE (30 min intervals)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  1. Market Data Collection          │
        │     • Fetch 118+ NASDAQ-100 stocks  │
        │     • Calculate technical indicators│
        │     • Get economic data & sentiment  │
        │     Time: 5-10 seconds               │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  2. Multi-Agent Analysis            │
        │     ┌──────────────────────────┐   │
        │     │ Market Analyst            │   │
        │     │ • Macro trends            │   │
        │     │ • Sector rotation         │   │
        │     │ • Market breadth          │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Technical Analyst         │   │
        │     │ • Price patterns          │   │
        │     │ • Support/resistance      │   │
        │     │ • Technical indicators    │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Fundamental Analyst       │   │
        │     │ • Financial statements    │   │
        │     │ • Valuation metrics       │   │
        │     │ • Earnings history        │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Sentiment Analyst         │   │
        │     │ • News sentiment          │   │
        │     │ • Fear & Greed Index      │   │
        │     │ • VIX term structure      │   │
        │     └──────────────────────────┘   │
        │     Time: 30-60 seconds             │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  3. Discussion Coordinator          │
        │     • Synthesizes all 4 analysts    │
        │     • 3 rounds of discussion        │
        │     • Final consensus (stance)       │
        │     • Tool usage tracking           │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  4. Risk Assessment                 │
        │     • Position concentration        │
        │     • Market risk evaluation        │
        │     • Position size recommendations│
        │     • VIX risk scoring              │
        │     Time: 10-20 seconds              │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  5. Trader Agent Decision           │
        │     ┌──────────────────────────┐    │
        │     │ Inputs:                   │    │
        │     │ • Analyst consensus       │    │
        │     │ • Risk report             │    │
        │     │ • Current positions       │    │
        │     │ • Market data             │    │
        │     └──────────────────────────┘    │
        │     ┌──────────────────────────┐    │
        │     │ LLM Processing:           │    │
        │     │ • Analyzes all inputs     │    │
        │     │ • Considers risk limits   │    │
        │     │ • Generates buy/sell      │    │
        │     └──────────────────────────┘    │
        │     ┌──────────────────────────┐    │
        │     │ Outputs:                  │    │
        │     │ • buy_orders[]            │    │
        │     │ • sell_orders[]          │    │
        │     │ • rationale               │    │
        │     └──────────────────────────┘    │
        │     Time: 5-10 seconds                │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  6. Hard Rules Validation           │
        │     ✓ Market status check           │
        │     ✓ Cash availability             │
        │     ✓ Position limits               │
        │     ✓ Position count limit          │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  7. Order Execution                 │
        │     • Market open: Execute orders    │
        │     • Market closed: Analysis only   │
        │     • All orders are market orders  │
        │     • Immediate fill guaranteed     │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  8. Portfolio Update                 │
        │     • Update portfolio state         │
        │     • Record equity history          │
        │     • Save memory snapshot           │
        │     • Log conversations & trades     │
        └─────────────────────────────────────┘
```

### Detailed Trading Scenarios

#### Scenario 1: Market Open - Bullish Consensus

**Market Conditions**:
- Market is open (9:30 AM - 4:00 PM ET)
- VIX < 20 (low volatility)
- Analyst consensus: **BULLISH**
- Risk Analyst: Low risk, recommends 10-15% per stock

**Agent Dialogue Example**:
```
Market Analyst: "S&P 500 up 0.5%, NASDAQ leading with tech sector rotation. 
                 Market breadth strong with 65% advancing stocks."

Technical Analyst: "NVDA showing bullish momentum, RSI 55, MACD positive. 
                    Support at $150, resistance at $160."

Fundamental Analyst: "NVDA P/E ratio 35, below sector average. Strong revenue 
                      growth, healthy cash flow. Valuation attractive."

Sentiment Analyst: "Fear & Greed Index at 65 (Greed). News sentiment positive 
                    on AI sector. VIX term structure normal."

Discussion Coordinator: "Consensus: BULLISH. All analysts agree NVDA is 
                         attractive. Recommended allocation: 12% portfolio."

Risk Analyst: "Portfolio risk: LOW. Current positions: 3 stocks (45% total). 
               Can add NVDA with 12% allocation. Position limit: 15% per stock."

Trader Agent: "Based on bullish consensus and low risk, generating BUY order 
               for NVDA: 12% allocation, market price $155.00, quantity 7 shares."
```

**Trader Agent Decision Process**:
1. **LLM Analysis**: Processes all analyst inputs, risk report, current positions
2. **Risk Compliance**: Checks position limits (12% < 15% max, total 57% < 80% max)
3. **Cash Check**: Verifies sufficient cash available
4. **Order Generation**: Creates market order for immediate execution

**Hard Rules Applied**:
- ✓ Market open: Orders can be executed
- ✓ Position limit: 12% < 15% max per stock
- ✓ Total position: 57% < 80% max
- ✓ Cash available: Sufficient for purchase
- ✓ Position count: 4 stocks < 10 max

**Result**: Order executed immediately at market price.

---

#### Scenario 2: Market Open - Bearish Consensus with Existing Positions

**Market Conditions**:
- Market is open
- VIX > 25 (high volatility)
- Analyst consensus: **BEARISH**
- Current position: NVDA (15% of portfolio, -5% P&L)

**Agent Dialogue Example**:
```
Market Analyst: "S&P 500 down 1.2%, NASDAQ down 1.5%. Market breadth weak, 
                 only 35% advancing. Sector rotation to defensive."

Technical Analyst: "NVDA breaking support at $150. RSI oversold at 30, 
                    but trend is down. Next support at $140."

Fundamental Analyst: "NVDA earnings miss expectations. Revenue growth slowing. 
                      P/E ratio elevated at 40. Valuation concerns."

Sentiment Analyst: "Fear & Greed Index at 25 (Fear). Negative news on chip 
                    sector. VIX term structure inverted (bearish signal)."

Discussion Coordinator: "Consensus: BEARISH. Risk-off environment. Recommend 
                         reducing tech exposure, especially NVDA."

Risk Analyst: "Portfolio risk: HIGH. VIX risk score: 7.5/10. NVDA position 
               at 15% limit. Recommend reducing to 8% or exiting entirely."

Trader Agent: "Based on bearish consensus and high risk, generating SELL order 
               for NVDA: Reduce position from 15% to 8% (sell 4 shares). 
               Preserve capital in volatile market."
```

**Trader Agent Decision Process**:
1. **LLM Analysis**: Identifies risk-off environment, high VIX, negative sentiment
2. **Position Management**: Decides to reduce exposure (not exit completely)
3. **Risk Compliance**: Follows Risk Analyst recommendation (reduce to 8%)
4. **Order Generation**: Creates SELL order for partial position

**Hard Rules Applied**:
- ✓ Market open: Orders can be executed
- ✓ Position reduction: 15% → 8% (within limits)
- ✓ Risk management: Reduces exposure in high-risk environment

**Result**: Partial sell order executed, position reduced to 8%.

---

#### Scenario 3: Market Closed - Analysis Only

**Market Conditions**:
- Market is closed (after 4:00 PM ET or before 9:30 AM ET)
- All agents still run analysis
- No orders generated

**Agent Dialogue Example**:
```
[All agents run analysis as normal...]

Trader Agent: "Market is currently closed. Analysis completed:
              - Market stance: NEUTRAL
              - VIX risk: 4.0/10
              - Recommended actions: Monitor for next session
              - No trading orders generated (market orders only execute 
                during trading hours: 9:30 AM - 4:00 PM ET)"
```

**Hard Rules Applied**:
- ✓ Market closed: **NO ORDERS GENERATED** (hard rule)
- ✓ Analysis still runs: Agents provide insights for next session
- ✓ Portfolio state: Unchanged, but analysis saved to memory

**Result**: Analysis saved, no trading activity.

---

### Trader Agent: LLM-Based Decision Making

**Is Trader Agent an LLM?**
- **Yes**: Trader Agent uses LLM (deepseek-r1) to make trading decisions
- **Input**: Structured data (analyst reports, risk assessment, positions, market data)
- **Output**: Trading orders (buy/sell) with rationale

**Decision-Making Process**:

```
┌─────────────────────────────────────────────────────────────┐
│              Trader Agent Decision Flow                      │
└─────────────────────────────────────────────────────────────┘

Input Layer:
├── Analyst Consensus
│   ├── Final stance (BULLISH/BEARISH/NEUTRAL)
│   ├── Recommended stocks
│   └── Key insights from 4 analysts
│
├── Risk Report
│   ├── Overall risk level (LOW/MEDIUM/HIGH)
│   ├── VIX risk score (0-10)
│   ├── Position control recommendations
│   └── Position limit checks
│
├── Current Portfolio
│   ├── Current positions (symbol, quantity, P&L)
│   ├── Available cash
│   └── Portfolio value
│
└── Market Data
    ├── Current prices
    ├── Market status (open/closed)
    └── Market indicators

                    ▼
        ┌───────────────────────┐
        │   LLM Processing       │
        │   (deepseek-r1)        │
        │                        │
        │  • Analyzes all inputs │
        │  • Weighs risk factors │
        │  • Considers position  │
        │    limits              │
        │  • Generates rationale │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │   Hard Rules Check    │
        │                        │
        │  ✓ Market open?        │
        │  ✓ Cash available?     │
        │  ✓ Position limits?    │
        │  ✓ Position count?    │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │   Output Generation   │
        │                        │
        │  • buy_orders[]        │
        │  • sell_orders[]       │
        │  • rationale           │
        │  • risk_compliance    │
        └───────────────────────┘
```

**How Trader Agent Decides Buy/Sell**:

1. **Stance Analysis**: 
   - BULLISH → Generate BUY orders for recommended stocks
   - BEARISH → Generate SELL orders for existing positions or avoid new buys
   - NEUTRAL → Conservative approach, may hold or make small adjustments

2. **Risk Integration**:
   - High VIX risk (7-10) → Reduce position sizes, be more conservative
   - Low VIX risk (0-4) → Can be more aggressive, larger positions
   - Risk Analyst recommendations → Directly influence position sizing

3. **Position Management**:
   - Existing positions with negative P&L + bearish consensus → Consider selling
   - Existing positions at limit (15%) + new opportunities → May reduce to make room
   - No positions + bullish consensus → Generate new BUY orders

4. **LLM Reasoning**:
   - Trader Agent uses LLM to synthesize all information
   - LLM considers multiple factors simultaneously
   - LLM generates natural language rationale explaining decisions
   - LLM can make nuanced decisions (e.g., partial sells, gradual entries)

---

### Hard Rules & Constraints

**1. Market Status (Hard Rule)**
```
IF market_closed:
    NO_ORDERS_GENERATED
    Analysis only
ELSE:
    Orders can be executed
```

**2. Position Limits (Hard Rules)**
- **Per Stock Limit**: Maximum 15% of portfolio per stock
- **Total Position Limit**: Maximum 80% of portfolio in positions (20% cash reserve)
- **Minimum Position**: Minimum 3% per stock (for diversification)
- **Position Count**: Maximum 10 different stocks

**3. Cash Constraints (Hard Rule)**
```
IF order_cost > available_cash:
    Reduce quantity OR skip order
ELSE:
    Execute order
```

**4. Risk-Based Position Sizing (Guidelines, not hard rules)**
- High VIX risk (7-10) → Smaller positions (5-8% per stock)
- Medium VIX risk (4-6) → Normal positions (8-12% per stock)
- Low VIX risk (0-3) → Larger positions (10-15% per stock)

**5. Order Execution Rules**
- All orders are **market orders** (immediate execution)
- No limit orders (guaranteed fill at current price)
- Orders execute immediately when market is open
- No pending orders (all filled or rejected)

---

### Trading Decision Examples

#### Example 1: New Position Entry
```
Input:
- Stance: BULLISH
- Recommended: NVDA, MSFT, AAPL
- Risk: LOW (VIX 15)
- Current positions: None
- Available cash: $10,000

Trader Agent Decision:
- Generate 3 BUY orders
- NVDA: 12% ($1,200, ~7 shares @ $170)
- MSFT: 10% ($1,000, ~2 shares @ $500)
- AAPL: 8% ($800, ~3 shares @ $270)
- Total: 30% of portfolio
- Rationale: "Diversified entry into tech sector with strong fundamentals"
```

#### Example 2: Position Adjustment
```
Input:
- Stance: NEUTRAL
- Current position: NVDA (15% of portfolio, +8% P&L)
- Risk: MEDIUM (VIX 20)
- New opportunity: MSFT (recommended)

Trader Agent Decision:
- Reduce NVDA: 15% → 10% (sell 3 shares)
- Add MSFT: 10% (buy 2 shares)
- Rationale: "Taking profits on NVDA, rebalancing to include MSFT for diversification"
```

#### Example 3: Risk-Off Exit
```
Input:
- Stance: BEARISH
- Current position: NVDA (12% of portfolio, -3% P&L)
- Risk: HIGH (VIX 28)
- Risk Analyst: Recommend reducing tech exposure

Trader Agent Decision:
- SELL NVDA: Exit entire position (12% → 0%)
- No new BUY orders
- Rationale: "Risk-off environment, exiting tech position to preserve capital"
```

---

### Information Flow & Data Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    INFORMATION FLOW DIAGRAM                     │
└─────────────────────────────────────────────────────────────────┘

External Data Sources:
├── Market Data (yfinance)
│   ├── Real-time prices (118+ NASDAQ-100 stocks)
│   ├── OHLCV data
│   ├── Technical indicators (RSI, MACD, etc.)
│   └── Market indices (S&P 500, NASDAQ, Dow)
│
├── Economic Data (FRED API)
│   ├── Economic indicators
│   ├── Labor market data
│   └── Federal Reserve data
│
├── News & Sentiment
│   ├── News APIs (news_scan, plan_and_scan_news)
│   ├── Jin10 financial news
│   ├── Fear & Greed Index (CNN)
│   └── VIX term structure (CBOE)
│
└── Fundamental Data
    ├── Company fundamentals (yfinance)
    ├── Earnings history
    └── Financial statements

                    ▼
        ┌───────────────────────┐
        │  Market Data Layer    │
        │  (fetch_market_batch) │
        │                       │
        │  • Aggregates all     │
        │    external data      │
        │  • Calculates         │
        │    indicators         │
        │  • Formats for agents │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Agent Analysis Layer │
        │                       │
        │  Round 1:             │
        │  ├── Market Analyst   │
        │  ├── Technical Analyst│
        │  ├── Fundamental     │
        │  └── Sentiment        │
        │                       │
        │  Round 2:             │
        │  ├── (Same agents)    │
        │  └── Tool calls       │
        │                       │
        │  Round 3:             │
        │  ├── (Same agents)    │
        │  └── Final synthesis  │
        │                       │
        │  Discussion Coordinator│
        │  └── Consensus stance │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Risk Assessment Layer │
        │                       │
        │  • Position analysis   │
        │  • VIX risk scoring    │
        │  • Position limits     │
        │  • Recommendations     │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Trading Decision     │
        │  (Trader Agent)       │
        │                       │
        │  • Synthesizes all    │
        │    inputs             │
        │  • Generates orders   │
        │  • Applies hard rules │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Execution Layer      │
        │                       │
        │  • Market orders      │
        │  • Immediate fill     │
        │  • Portfolio update   │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │  Data Storage         │
        │                       │
        │  • portfolio_state.json│
        │  • discussion_actions.jsonl│
        │  • trades.jsonl       │
        │  • equity_history.jsonl│
        │  • memory/daily/      │
        └───────────────────────┘
```

---

### Market Open vs. Market Closed: Complete Analysis Flow

#### Market Open Flow (9:30 AM - 4:00 PM ET)

**Timing**: Every 30 minutes during trading hours

**Complete Flow**:

```
┌─────────────────────────────────────────────────────────────┐
│         MARKET OPEN: FULL TRADING CYCLE (30 min)           │
└─────────────────────────────────────────────────────────────┘

T+0:00  → Data Collection (5-10 sec)
         ├── Fetch market data (118+ stocks)
         ├── Calculate indicators
         └── Get economic/sentiment data
              │
              ▼
T+0:10  → Multi-Agent Analysis (30-60 sec)
         ├── Round 1: All 4 analysts analyze independently
         │   ├── Market Analyst: Uses get_market_indices, get_sector_rotation
         │   ├── Technical Analyst: Uses get_advanced_indicators, get_support_resistance
         │   ├── Fundamental Analyst: Uses get_company_fundamentals, get_earnings_history
         │   └── Sentiment Analyst: Uses fear_greed, vix_term, news_scan
         │
         ├── Round 2: Analysts refine analysis based on Round 1
         │   └── Additional tool calls if needed
         │
         ├── Round 3: Final analysis and synthesis
         │   └── Discussion Coordinator synthesizes all views
         │
         └── Output: Consensus stance (BULLISH/BEARISH/NEUTRAL)
              │
              ▼
T+1:00  → Risk Assessment (10-20 sec)
         ├── Analyze current positions
         ├── Calculate VIX risk score (0-10)
         ├── Check position limits
         ├── Generate position recommendations
         └── Output: Risk report with position control recommendations
              │
              ▼
T+1:20  → Trader Agent Decision (5-10 sec)
         ├── LLM processes all inputs:
         │   ├── Analyst consensus (stance, recommended stocks)
         │   ├── Risk report (risk level, VIX score, recommendations)
         │   ├── Current positions (symbols, quantities, P&L)
         │   └── Market data (prices, status)
         │
         ├── Hard rules check:
         │   ├── ✓ Market open? (YES - can trade)
         │   ├── ✓ Cash available?
         │   ├── ✓ Position limits?
         │   └── ✓ Position count?
         │
         └── Output: buy_orders[], sell_orders[], rationale
              │
              ▼
T+1:30  → Order Execution (5-10 sec)
         ├── For each BUY order:
         │   ├── Check cash availability
         │   ├── Get real-time price
         │   ├── Execute market order (immediate fill)
         │   └── Update portfolio
         │
         ├── For each SELL order:
         │   ├── Check position exists
         │   ├── Get real-time price
         │   ├── Execute market order (immediate fill)
         │   └── Update portfolio
         │
         └── All orders: FILLED immediately (no pending)
              │
              ▼
T+1:40  → Portfolio Update (2-5 sec)
         ├── Update portfolio_state.json
         ├── Record to equity_history.jsonl (every 30 min)
         ├── Save to discussion_actions.jsonl
         ├── Save to trades.jsonl
         └── Save memory snapshot to memory/daily/YYYY-MM-DD.json

Total Time: ~2 minutes per cycle
Frequency: Every 30 minutes
Daily Cycles: ~13 cycles (9:30 AM - 4:00 PM)
```

**Agent Conversation Pattern (Market Open)**:
```
Cycle Start (T+0:00)
│
├── Market Analyst: "Market analysis based on current data..."
│   └── Tool calls: get_market_indices, get_sector_rotation
│
├── Technical Analyst: "Technical indicators show..."
│   └── Tool calls: get_advanced_indicators, get_support_resistance
│
├── Fundamental Analyst: "Fundamental analysis reveals..."
│   └── Tool calls: get_company_fundamentals, get_earnings_history
│
└── Sentiment Analyst: "Market sentiment indicates..."
    └── Tool calls: fear_greed, vix_term, news_scan

Round 2 (T+0:30)
│
├── All analysts refine based on Round 1 results
└── Additional tool calls if needed

Round 3 (T+1:00)
│
├── Discussion Coordinator: "Synthesizing all analyst views..."
│   └── Output: Final consensus stance
│
├── Risk Analyst: "Risk assessment complete..."
│   └── Output: Risk report with recommendations
│
└── Trader Agent: "Based on analysis, generating orders..."
    └── Output: Trading orders with rationale
```

---

#### Market Closed Flow (Before 9:30 AM or After 4:00 PM ET)

**Timing**: Every 30 minutes (same frequency, but no trading)

**Complete Flow**:

```
┌─────────────────────────────────────────────────────────────┐
│      MARKET CLOSED: ANALYSIS ONLY (30 min intervals)        │
└─────────────────────────────────────────────────────────────┘

T+0:00  → Data Collection (5-10 sec)
         ├── Fetch last available market data
         ├── Calculate indicators (using last close prices)
         └── Get economic/sentiment data (still available)
              │
              ▼
T+0:10  → Multi-Agent Analysis (30-60 sec)
         ├── Round 1-3: Same as market open
         ├── All 4 analysts analyze independently
         ├── Discussion Coordinator synthesizes
         └── Output: Consensus stance (for next session)
              │
              ▼
T+1:00  → Risk Assessment (10-20 sec)
         ├── Analyze current positions (using last close prices)
         ├── Calculate VIX risk score
         ├── Check position limits
         └── Output: Risk report (for next session)
              │
              ▼
T+1:20  → Trader Agent Analysis (5-10 sec)
         ├── LLM processes all inputs (same as market open)
         ├── Hard rules check:
         │   └── ✗ Market open? (NO - cannot trade)
         │
         └── Output: Analysis summary only, NO ORDERS
              │
              ▼
T+1:30  → Data Storage Only (2-5 sec)
         ├── Save analysis to discussion_actions.jsonl
         ├── Save memory snapshot
         └── NO portfolio updates (no trades executed)

Total Time: ~2 minutes per cycle
Frequency: Every 30 minutes
Purpose: Prepare analysis for next trading session
```

**Agent Conversation Pattern (Market Closed)**:
```
Cycle Start (T+0:00)
│
├── All analysts run analysis (same as market open)
│   └── Tool calls still work (using last available data)
│
└── Discussion Coordinator: "Synthesizing views for next session..."

Risk Analyst: "Current portfolio risk assessment..."

Trader Agent: "Market is currently closed. Analysis completed:
              - Market stance: [BULLISH/BEARISH/NEUTRAL]
              - VIX risk: [score]/10
              - Recommended actions: [for next session]
              - No trading orders generated (market orders only 
                execute during trading hours: 9:30 AM - 4:00 PM ET)"
```

**Key Differences (Market Closed)**:
- ✓ All agents still run analysis
- ✓ Tool calls still work (using last available data)
- ✓ Analysis saved to memory
- ✗ **NO trading orders generated** (hard rule)
- ✗ Portfolio state unchanged
- ✗ No equity history updates

---

### Trading Rules & Constraints (Complete List)

#### 1. Market Status Rules (Hard Rules - Enforced)

```
IF market_status == CLOSED:
    ├── NO buy_orders generated
    ├── NO sell_orders generated
    ├── Analysis still runs
    └── Results saved for next session

IF market_status == OPEN:
    ├── Orders can be generated
    ├── Orders execute immediately (market orders)
    └── Portfolio updates in real-time
```

**Market Hours**:
- **Open**: 9:30 AM ET
- **Close**: 4:00 PM ET
- **Trading Days**: Monday-Friday (excluding holidays)
- **Holidays**: System respects NYSE/NASDAQ holidays

#### 2. Position Limits (Hard Rules - Enforced)

| Rule | Limit | Type | Enforcement |
|------|-------|------|-------------|
| **Per Stock Maximum** | 15% of portfolio | Hard | Trader Agent + Execution Layer |
| **Total Position Maximum** | 80% of portfolio | Hard | Trader Agent + Execution Layer |
| **Cash Reserve Minimum** | 20% of portfolio | Hard | Execution Layer |
| **Minimum Position Size** | 3% of portfolio | Guideline | Trader Agent decision |
| **Maximum Positions** | 10 different stocks | Hard | Execution Layer |

**Position Limit Logic**:
```
For each BUY order:
    IF current_position[symbol] + new_order_value > 15% of portfolio:
        Reduce quantity to stay within 15% limit
    
    IF total_positions_value + new_order_value > 80% of portfolio:
        Reduce quantity to stay within 80% limit
    
    IF available_cash < order_cost:
        Reduce quantity OR skip order
    
    IF position_count >= 10 AND symbol not in current_positions:
        Skip order (max positions reached)
```

#### 3. Cash Management Rules (Hard Rules - Enforced)

```
Available Cash Calculation:
    available_cash = portfolio.cash - (portfolio_value * 0.20)
    
For each BUY order:
    IF order_cost > available_cash:
        ├── Calculate max_affordable_qty = floor(available_cash / price)
        ├── IF max_affordable_qty > 0:
        │   └── Reduce quantity to max_affordable_qty
        └── ELSE:
            └── Skip order (insufficient cash)
```

#### 4. Order Execution Rules (Hard Rules - Enforced)

```
Order Type: MARKET ORDERS ONLY
    ├── No limit orders
    ├── No stop orders
    └── Immediate execution at current price

Execution Guarantee:
    ├── Market open: Orders execute immediately
    ├── Market closed: NO orders generated
    └── All orders: FILLED or REJECTED (no PENDING)

Order Status:
    ├── FILLED: Order executed successfully
    ├── REJECTED: Order failed (cash insufficient, limits exceeded)
    └── PENDING: NOT USED (all orders fill immediately)
```

#### 5. Risk-Based Position Sizing (Guidelines - LLM Decision)

**VIX Risk Score → Position Size Guidelines**:

| VIX Risk Score | Risk Level | Position Size Range | Trader Agent Behavior |
|----------------|------------|---------------------|----------------------|
| 0-3 | LOW | 10-15% per stock | More aggressive, larger positions |
| 4-6 | MEDIUM | 8-12% per stock | Normal position sizing |
| 7-10 | HIGH | 5-8% per stock | Conservative, smaller positions |

**Note**: These are **guidelines** that Trader Agent (LLM) considers, not hard rules. The LLM can make nuanced decisions based on multiple factors.

#### 6. Conversation & Analysis Rules

**Discussion Rounds**:
- **Number of Rounds**: 3 rounds per cycle
- **Participants**: All 4 analysts participate in each round
- **Tool Budget**: 15 tool calls per cycle (shared across all analysts)
- **Round Structure**:
  - Round 1: Initial analysis, tool calls
  - Round 2: Refinement based on Round 1, additional tool calls if needed
  - Round 3: Final synthesis, Discussion Coordinator summarizes

**Tool Call Rules**:
- Each analyst can call tools independently
- Tool results shared across rounds
- Tool budget tracked per cycle
- If budget exhausted, agents continue without tools

---

### Data Flow & Storage Timeline

```
Every 30 Minutes:
├── Real-time Data Collection
│   └── Market data, indicators, sentiment
│
├── Agent Analysis
│   ├── 4 analysts × 3 rounds = 12 analysis entries
│   ├── Discussion Coordinator synthesis
│   └── Risk Analyst assessment
│
├── Trading Decision
│   └── Trader Agent orders (if market open)
│
└── Data Storage
    ├── discussion_actions.jsonl (all agent conversations)
    ├── portfolio_state.json (updated if trades executed)
    ├── equity_history.jsonl (updated every 30 min during market hours)
    ├── trades.jsonl (new trades if any)
    └── memory/daily/YYYY-MM-DD.json (snapshot every cycle)

Daily Summary:
└── memory/daily/YYYY-MM-DD.json
    ├── Complete market view snapshot
    ├── All agent discussions
    ├── Risk reports
    ├── Trading decisions
    ├── Portfolio snapshot
    └── Executed trades
```

---

### Key Points

1. **Trading Frequency**: Every 30 minutes during market hours (9:30 AM - 4:00 PM ET)
2. **Analysis Frequency**: Every 30 minutes (even when market closed)
3. **Agent Conversations**: 3 rounds per cycle, all 4 analysts participate
4. **Trader Agent is LLM-based**: Uses deepseek-r1 to make nuanced trading decisions
5. **Hard Rules Enforced**: Market status, position limits, cash constraints are strictly enforced
6. **Risk Integration**: Risk Analyst recommendations directly influence Trader Agent decisions
7. **Multi-Factor Analysis**: Trader Agent considers all inputs simultaneously (not sequential)
8. **Natural Language Rationale**: Every decision includes LLM-generated explanation
9. **Market Orders Only**: All orders execute immediately at current price (no limit orders)
10. **Information Flow**: External data → Market layer → Agent analysis → Risk → Trading → Execution → Storage

---

## 📡 API Endpoints

**Quick Access**: All API endpoints are available via Swagger UI at `http://localhost:8000/docs`

### Portfolio & Trading
- `GET /api/portfolio/state`: Current portfolio state
- `GET /api/portfolio/real-time`: Real-time portfolio with live prices
- `GET /api/portfolio/equity-history`: Historical net value curve
- `POST /api/trading/execute-trade`: Execute full trading cycle
- `POST /api/system/init`: Reset portfolio to initial state

### Market Data
- `GET /api/market/status`: Check if market is open
- `GET /api/market/universe`: Get NASDAQ-100 universe
- `GET /api/market/price/{symbol}`: Current price for symbol

### Orders
- `GET /api/orders/pending`: Get pending orders
- `POST /api/orders/check-fills`: Check and execute pending orders
- `GET /api/orders/history`: Order history

### Conversations & Logs
- `GET /api/agents/conversations`: Get agent discussions
- `GET /api/trades/history`: Trade log
- `GET /api/trades/realized-pnl`: Historical realized P&L records (query by date, start_date, end_date, limit)

---

## 🚀 Deployment

### GitHub Pages Deployment (Frontend)

1. **Push to GitHub**
   ```powershell
   git add .
   git commit -m "Prepare for GitHub Pages"
   git push origin main
   ```

2. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/frontend`
   - Click Save

3. **Configure Backend API**
   - Edit `frontend/config.js`
   - Update `production` to your Railway backend URL

4. **Deploy Backend to Railway**
   - Connect GitHub repo to Railway
   - Auto-deploy backend
   - Get public URL

### Daily Auto-Upload to Railway

**Setup Daily Upload Task**:
   ```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\schedule_daily_upload_only.ps1
```

**Manual Upload**:
   ```powershell
python scripts\upload_data_to_railway.py
```

> 📖 **Detailed Guide**: See [`docs/USER_MANUAL_RAILWAY_UPDATE.md`](docs/USER_MANUAL_RAILWAY_UPDATE.md)

---

## ❓ Troubleshooting

### Ollama Connection Error

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

### FRED API Errors

**Error**: `FRED API key not found`

**Solutions**:
```bash
# Set API key
export FRED_API_KEY=your_key_here

# For Windows PowerShell:
$env:FRED_API_KEY="your_key_here"
```

### Portfolio State Not Found

**Error**: `FileNotFoundError: portfolio_state.json`

**Solution**:
```bash
python scripts/init_data.py
```

### Frontend Positions Display Issues

**Error**: Positions table shows `undefined` or `NaN` for shares, cost, price, etc.

**Root Cause**: Frontend was reading from `positions` (quantity only) instead of `positions_detail` (full information).

**Solution**: 
- ✅ **Fixed**: Frontend now reads from `positions_detail` with fallback logic
- Refresh the browser page (F5 or Ctrl+R) to see the fix
- All position fields should now display correctly

**Related Documentation**: See [`docs/FRONTEND_POSITIONS_FIX.md`](docs/FRONTEND_POSITIONS_FIX.md)

### Portfolio P&L Calculation Issues

**Error**: 
- `cost_basis=0 (total_cost=undefined, cost_basis=undefined)` in console
- Net value not returning to 10000 when positions are cleared

**Root Cause**: 
- API was not populating `positions_detail` when market data fetch failed
- Missing `total_cost` and `cost_basis` fields
- Incorrect `total_value` calculation

**Solution**:
- ✅ **Fixed**: API now always populates `positions_detail` with basic info (even when market is closed)
- ✅ **Fixed**: Added `total_cost` and `cost_basis` fields
- ✅ **Fixed**: Corrected `total_value = cash + equity_value` calculation

**Related Documentation**: See [`docs/PORTFOLIO_PNL_FIX.md`](docs/PORTFOLIO_PNL_FIX.md)

### API Endpoint Errors

**Error**: `405 Method Not Allowed` or `500 Internal Server Error`

**Common Issues**:
- ✅ **Fixed**: Added `POST` method support to `/api/trading/check-pending-orders`
- ✅ **Fixed**: VIX and Fear & Greed endpoints now return default values instead of 500 errors when data fetch fails

**Related Documentation**: See [`docs/FRONTEND_CONSOLE_ERRORS_FIXED.md`](docs/FRONTEND_CONSOLE_ERRORS_FIXED.md)

### Restart Backend API

**Quick Restart** (if API is running in a window):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**If API is running as Windows Service**:
```powershell
# Restart service
Restart-Service -Name AITraderAPI

# Or use the service script
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
# Then choose (R)estart
```

**If API is running as Scheduled Task**:
```powershell
# Restart task
Stop-ScheduledTask -TaskName AITraderAPI
Start-ScheduledTask -TaskName AITraderAPI

# Or use the task script
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# Then choose (R)estart
```

**Stable Start** (with auto-restart, but requires window open):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1
```

### Run API in Background (Close CMD and Keep Running)

**Option 1: Windows Service (Recommended, requires NSSM)**

1. **Install NSSM** (automatic):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\install_nssm.ps1
   ```
   Or manually:
   - Download from: https://nssm.cc/download
   - Extract to `C:\nssm\`

2. **Install Service** (requires administrator privileges):
   
   **Method A (Recommended)**: Right-click and run as administrator
   ```
   Right-click: scripts\start_api_service_admin.bat
   Select: "Run as administrator"
   ```
   
   **Method B**: Run in administrator PowerShell
   ```powershell
   # Open PowerShell as administrator, then run:
   powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
   ```
   
   **Note**: The script will automatically install NSSM if not found.

3. **Manage Service**:
   ```powershell
   # Start
   Start-Service -Name AITraderAPI
   
   # Stop
   Stop-Service -Name AITraderAPI
   
   # Restart
   Restart-Service -Name AITraderAPI
   
   # Check status
   Get-Service -Name AITraderAPI
   
   # View logs
   Get-Content logs\api_service.log -Tail 50
   ```

**Option 2: Task Scheduler (No additional software needed)**

1. **Install Task** (requires administrator privileges):
   
   **Method A (Recommended)**: Right-click and run as administrator
   ```
   Right-click: scripts\start_api_task_admin.bat
   Select: "Run as administrator"
   ```
   
   **Method B**: Run in administrator PowerShell
   ```powershell
   # Open PowerShell as administrator, then run:
   powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
   ```

2. **Manage Task**:
   ```powershell
   # Start
   Start-ScheduledTask -TaskName AITraderAPI
   
   # Stop
   Stop-ScheduledTask -TaskName AITraderAPI
   
   # Check status
   Get-ScheduledTaskInfo -TaskName AITraderAPI
   
   # View logs
   Get-Content logs\api_task.log -Tail 50
   ```

**Comparison**:

| Method | Close CMD? | Auto-start on Boot? | Requires Software? |
|--------|------------|---------------------|-------------------|
| Windows Service | ✅ Yes | ✅ Yes | NSSM |
| Task Scheduler | ✅ Yes | ✅ Yes (on logon) | No |
| Stable Script | ❌ No | ❌ No | No |
| Fast Restart | ❌ No | ❌ No | No |

**Recommendation**: Use **Task Scheduler** (Option 2) if you don't want to install NSSM. Use **Windows Service** (Option 1) if you need more control and automatic startup on system boot.

---

## 📖 Documentation

### Detailed Documentation Files

| File | Description |
|------|-------------|
| `docs/AGENT_SYSTEM.md` | Complete agent architecture |
| `docs/API_REFERENCE.md` | Full API endpoint documentation |
| `docs/TOOLS.md` | Detailed documentation for all 23 tools |
| `docs/ARCHITECTURE.md` | System design and data flow |
| `docs/USER_MANUAL_RAILWAY_UPDATE.md` | Daily upload guide |

### Recent Fixes & Improvements

| File | Description |
|------|-------------|
| `docs/FRONTEND_POSITIONS_FIX.md` | Frontend positions display fix (undefined/NaN issue) |
| `docs/PORTFOLIO_PNL_FIX.md` | Portfolio P&L calculation and net value fixes |
| `docs/FRONTEND_CONSOLE_ERRORS_FIXED.md` | API endpoint error fixes (405, 500 errors) |
| `docs/COMPLETE_FIX_SUMMARY.md` | Comprehensive summary of all recent fixes |
| `docs/API_IMPLEMENTATION_COMPLETE.md` | API endpoint implementation status |
| `docs/TOOL_RESULTS_DISPLAY_FIX.md` | Tool results display fix and Discussion Rounds Panel implementation |

---

## 📄 License

MIT License - see `LICENSE` file for details

---

**Built with ❤️ by the AI-Trader Team**

*Empowering traders with AI-driven insights and autonomous decision-making*
