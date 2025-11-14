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

# Method 1: Stable version (Recommended, with auto-restart)
.\scripts\start_api_stable_bypass.ps1

# Method 2: Fast restart (Daily use, quick restart)
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1

# Method 3: Manual start (Development/Testing)
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

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

All trading data, records, and memory are stored in `data/logs/`:

```
data/logs/
├── portfolio_state.json          # Current portfolio state (cash, positions)
├── equity_history.jsonl          # Net value history (P&L records)
├── discussion_actions.jsonl      # Agent conversations
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
  "order_date": "2025-01-28",
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
- **Inputs**: All analyst recommendations + risk report + portfolio state

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

1. **Data Collection** (5-10 seconds)
   - Fetch market data for 118+ NASDAQ-100 stocks
   - Calculate technical indicators
   - Get economic indicators and market sentiment

2. **Multi-Agent Analysis** (30-60 seconds)
   - Market Analyst: Macro trends
   - Technical Analyst: Price patterns
   - Fundamental Analyst: Valuation
   - Sentiment Analyst: Market psychology

3. **Risk Assessment** (10-20 seconds)
   - Position concentration analysis
   - Market risk evaluation
   - Position size recommendations

4. **Trading Decisions** (5-10 seconds)
   - Generate buy/sell orders
   - Apply position limits (max 15% per stock)
   - Calculate price ranges for limit orders

5. **Order Execution**
   - Market open: Execute immediately
   - Market closed: Place pending orders

6. **Portfolio Update**
   - Update portfolio state
   - Record equity history
   - Save memory snapshot

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

### Restart Backend API

**Quick Restart**:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**Stable Start** (with auto-restart):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_stable_bypass.ps1
```

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

---

## 📄 License

MIT License - see `LICENSE` file for details

---

**Built with ❤️ by the AI-Trader Team**

*Empowering traders with AI-driven insights and autonomous decision-making*
