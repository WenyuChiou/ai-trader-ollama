# 🔧 Backend - AI Trader API

> **FastAPI backend service providing core functionality for multi-agent trading system**

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration Files](#-configuration-files)
- [API Endpoints](#-api-endpoints)
- [Agent System](#-agent-system)
- [Available Tools](#-available-tools)
- [Scripts](#-scripts)
- [Testing Guide](#-testing-guide)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Ollama

```bash
# Start Ollama service (keep running)
ollama serve

# Pull LLM model (in another terminal)
ollama pull llama3.1
```

### 3. Initialize Data

```bash
python scripts/init_data.py
```

This will create:
- Portfolio state (initial cash: $10,000)
- Memory directory structure
- Trading log files

### 4. Start API Server

#### Windows (PowerShell)

```powershell
cd backend\scripts
.\start_api_background.ps1
```

#### Manual Start

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

### 5. Verify API is Running

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

---

## 📁 Project Structure

```
backend/
├── src/                    # Source code
│   ├── agents/            # Agent implementations
│   │   ├── market_analyst.py      # Market Analyst
│   │   ├── analyst_discussion.py  # Discussion Agent
│   │   ├── risk_analyst.py        # Risk Analyst
│   │   ├── trader_agent.py       # Trader Agent
│   │   └── toolbox.py             # Tool interface
│   ├── api/               # FastAPI server
│   │   └── server.py      # Main API file
│   ├── data/              # Data management
│   │   ├── portfolio.py           # Portfolio
│   │   ├── trade_log.py           # Trade logs
│   │   ├── order_manager.py       # Order management
│   │   ├── real_time_tracker.py   # Real-time tracking
│   │   └── memory_manager.py      # Memory management
│   ├── tools/             # Tool library
│   │   ├── market_tools.py        # Market data tools
│   │   ├── news_tools.py          # News tools
│   │   ├── sentiment_tools.py     # Sentiment analysis tools
│   │   └── crypto_tools.py        # Cryptocurrency tools
│   ├── orchestrator/      # Trading flow orchestration
│   │   └── trading_cycle.py      # Trading cycle
│   └── llm/               # LLM client
│       └── ollama_client.py
├── config/                # Configuration files
│   ├── config.json        # Main configuration file
│   └── agents.yaml        # Agent configuration
├── prompts/               # Prompt templates
│   ├── discussion_agent.yml
│   ├── trader_agent.yml
│   └── market_analyst.yml
├── scripts/               # Utility scripts
│   ├── init_data.py              # Data initialization
│   ├── start_api_background.ps1  # Start API
│   ├── restart_api.ps1          # Restart API
│   ├── clear_test_data.py       # Clear test data
│   └── simulate_october_history.py  # October simulation
├── data/                  # Data directory (.gitignore)
│   └── logs/              # Log files
├── tests/                 # Test suite
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Configuration Files

### `config/config.json`

Main configuration file, includes:

- **Stock pool configuration** (`universe`): 72 stocks + inverse ETFs + leveraged ETFs
- **Market indices** (`market_indices`): S&P 500, NASDAQ, Dow Jones
- **Position limits**:
  - `position_limit_per_stock`: Max position per stock (15%)
  - `position_limit_total`: Total position limit (85%)
  - `position_limit_min_per_stock`: Min position per stock (3%)
- **LLM configuration**:
  - `default_model`: Default model (llama3.1)
  - `ollama_host`: Ollama server address
  - `timeout_seconds`: Request timeout
- **Discussion configuration**:
  - `discussion_rounds`: Number of discussion rounds (3)
  - `discussion_tool_budget`: Tool call budget (20)

For detailed configuration descriptions, see: [Configuration Settings](../README.md#-configuration-settings)

---

## 🔌 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API health check |
| `/api/portfolio/real-time` | GET | Real-time portfolio data |
| `/api/portfolio/equity-history` | GET | Equity history |
| `/api/trades/recent` | GET | Recent trade records |
| `/api/agents/conversations` | GET | Agent conversation records |
| `/api/trading/execute-trade` | POST | Execute trading cycle |
| `/api/trading/simulate-october` | POST | Start October simulation |
| `/api/trading/simulate-status` | GET | Simulation status |
| `/api/tools/list` | GET | Available tools list |
| `/api/system/info` | GET | System information |

**Complete API Documentation**: See [API Endpoints Documentation](../docs/archive/API_ENDPOINTS.md)

---

## 🤖 Agent System

### Agent Types

| Agent | Responsibility | Main Output |
|-------|---------------|-------------|
| **Market Analyst** | Analyze market trends, generate stock recommendations | Recommended stock list, market sentiment |
| **Discussion Agent** | Multi-round discussion analysis, comprehensive evaluation | Final stance, reasoning process |
| **Risk Analyst** | Evaluate portfolio risk, position control | Risk report, position recommendations |
| **Trader Agent** | Generate buy/sell orders | Buy/sell order list |

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

For detailed descriptions, see: [Agent System](../README.md#-agent-system)

---

## 🛠️ Available Tools

Tools available to Agents:

### Market Data Tools
- `fetch_market_batch`: Batch fetch stock OHLCV and technical indicators
- `vix_term`: Get VIX term structure
- `vix_close`: Get VIX closing price series
- `fear_greed`: Get Fear & Greed Index

### News & Economic Data Tools

#### News Tools (Updated 2025-11-10)

**`news_scan`**: Scan latest news articles with intelligent filtering
- **Features**:
  - Automatically filters outdated news sources (WSJ, Reuters, FT, Zero Hedge)
  - Only returns news from verified fresh sources (<6 hours old)
  - Supports keyword-based search
  - Date filtering (default: 10 days, configurable)
- **News Sources** (10 verified fresh sources):
  - **Core Financial News**: CNBC, MarketWatch, Seeking Alpha, Investing.com, Benzinga, Bloomberg
  - **Community Sources**: Reddit (WSB, Investing, Stocks), Hacker News
- **Usage**:
  ```python
  from src.tools.news_tools import news_scan
  result = news_scan(keywords=["market", "AI"], max_articles=12, recency_days=7)
  ```

**`business_rss`**: Fetch business news from RSS feeds
- **Features**:
  - Date filtering (default: 48 hours, configurable via `max_age_hours`)
  - Automatic sorting by date (newest first)
  - All news entries include timestamp information
- **Usage**:
  ```python
  from src.tools.news_tools import business_rss
  # Get news from last 48 hours (default)
  news = business_rss(max_items=40)
  # Get only news from last 24 hours
  fresh_news = business_rss(max_items=40, max_age_hours=24)
  ```

**Other News Tools**:
- `fetch_jin10_news`: Get Jin10 financial news
- `fetch_jin10_economic_data`: Get economic data
- `web_search`: DuckDuckGo search
- `fetch_url`: Get URL main content
- `plan_and_scan_news`: LLM-powered news query planning and scanning

**News Tool Verification**:
```bash
# Check news source freshness
python check_news_recency.py

# Quick test news tools
python quick_test_news.py
```

**Documentation**:
- `NEWS_TOOL_UPDATE.md` - News tool update summary
- `NEWS_UPDATE_VERIFICATION.md` - Verification report

### Cryptocurrency Tools
- `fetch_crypto_batch`: Batch fetch cryptocurrency data
- `get_crypto_price`: Get single cryptocurrency price

For complete tool list, see: [Available Tools](../README.md#-available-tools)

---

## 📜 Scripts

### Core Scripts

| Script | Description |
|--------|-------------|
| `init_data.py` | Initialize data (portfolio, memory, logs) |
| `start_api_background.ps1` | Start API server in background |
| `restart_api.ps1` | Restart API server |
| `clear_test_data.py` | Clear all test data and records |
| `simulate_october_history.py` | Run October historical simulation |
| `run_full_workflow.py` | Run complete trading workflow test |

### News Tools Scripts

| Script | Description |
|--------|-------------|
| `check_news_recency.py` | Check freshness of all news sources |
| `quick_test_news.py` | Quick test of news tools functionality |

### Utility Scripts

| Script | Description |
|--------|-------------|
| `check_cash_vs_orders.py` | Check if orders exceed available cash |
| `check_holdings_vs_orders.py` | Compare portfolio holdings with filled orders |
| `check_pending_orders_detail.py` | Detailed analysis of pending orders |
| `analyze_all_orders.py` | Comprehensive analysis of all orders |

### Scheduling Scripts

| Script | Description |
|--------|-------------|
| `schedule_daily_task.ps1` | Schedule daily trading task |
| `schedule_hourly_update.ps1` | Schedule hourly update task |

### Utility Scripts

| Script | Description |
|--------|-------------|
| `check_api_status.ps1` | Check API running status |
| `check_port.ps1` | Check port usage |
| `show_discussion_rounds.py` | Display discussion rounds |

---

## 🧪 Testing Guide

### Comprehensive Testing Framework

The backend includes a comprehensive 4-round testing framework:

#### Round 1: Backend API Testing ✅
```bash
python test_comprehensive.py
```
- Tests all API endpoints
- Validates data formats
- Checks file consistency
- **Result**: 9/9 tests passed (100%)

#### Round 2: Frontend Functionality Testing ✅
```bash
python test_frontend_comprehensive.py
```
- Tests all button functionality
- Validates data display
- Checks error handling
- **Result**: 22/22 tests passed (100%)

#### Round 3: Data Recording Scenarios (Next)
- Tests initialization data recording
- Tests trading cycle data recording
- Validates equity history updates

#### Round 4: Frontend-Backend Integration
- End-to-end workflow testing
- Real-time data synchronization

### Scenario-Based Testing

```bash
# Run all scenarios (1-12)
python test_scenarios.py --scenario 1 --auto
python test_scenarios.py --scenario 2 --auto
# ... see TEST_COMMANDS.md for full list
```

### Test File Descriptions

| Test File | Description |
|-----------|-------------|
| `test_comprehensive.py` | Round 1: Backend API comprehensive tests |
| `test_frontend_comprehensive.py` | Round 2: Frontend functionality tests |
| `test_scenarios.py` | Scenario-based testing (12 scenarios) |
| `test_full_workflow.py` | Complete workflow test |
| `test_frontend_integration.py` | Frontend integration test |

### Test Documentation

- **Test Commands**: `TEST_COMMANDS.md` - All test commands
- **Testing Guide**: `COMPREHENSIVE_TESTING_GUIDE.md` - Complete testing guide
- **Round 1 Report**: `TEST_ROUND_1_REPORT.md` - Backend API test results
- **Round 2 Report**: `TEST_ROUND_2_REPORT.md` - Frontend test results

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: src` | Run from `backend/` directory |
| Ollama connection error | Run `ollama serve` |
| Port 8000 is in use | Use `scripts/check_port.ps1` to find and terminate process |
| PowerShell execution policy error | Use `restart_api_bypass.ps1` |

### Restart API

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

For detailed troubleshooting, see: [Troubleshooting](../README.md#-troubleshooting)

---

## 📚 Related Documentation

### Core Documentation
- [API Endpoints Documentation](../docs/archive/API_ENDPOINTS.md)
- [Frontend-Backend Integration](../docs/archive/FRONTEND_BACKEND_INTEGRATION.md)
- [Portfolio Update Flow](../docs/archive/PORTFOLIO_UPDATE_FLOW.md)
- [Trading Hours Logic](docs/TRADING_HOURS_LOGIC.md)

### Feature Documentation
- [News Tool Update](NEWS_TOOL_UPDATE.md) - News tool enhancements and updates
- [News Update Verification](NEWS_UPDATE_VERIFICATION.md) - News tool verification report
- [Position Info Enhancement](POSITION_INFO_ENHANCEMENT.md) - Position information enhancements
- [Workflow Optimization](WORKFLOW_OPTIMIZATION_SUMMARY.md) - Trading workflow optimizations
- [Important Files](IMPORTANT_FILES.md) - Guide to important files and scripts

### Strategy Guides
- [Hedging Strategy Guide](../docs/archive/HEDGING_STRATEGY.md)
- [Leveraged ETF Guide](../docs/archive/LEVERAGED_ETF_GUIDE.md)
- [Market Indices Integration](../docs/archive/MARKET_INDICES_INTEGRATION.md)

### Operational Guides
- [Restart API Guide](../docs/archive/RESTART_API_GUIDE.md)

---

## 📝 License

MIT License © 2025 Wenyu Chiou
