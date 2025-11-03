# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 🎯 Quick Overview

AI-Trader Ollama is an autonomous trading system that uses multiple specialized AI agents to analyze market data, discuss trading strategies, assess risks, and execute trades automatically. The system runs daily at 9:00 AM, analyzes yesterday's market data, and makes trading decisions based on technical analysis, market sentiment, and risk management.

### Key Features

- 🤖 **Multi-Agent Architecture**: Market Analyst, Discussion Agent, Risk Analyst, Trader Agent
- 🔄 **Feedback Loop**: Agents automatically call tools (news, sentiment, economic data) when needed
- 💾 **Memory System**: Learns from historical trading decisions
- 📊 **Automated Trading**: Daily execution with portfolio management
- 📈 **Monitoring & Optimization**: Built-in performance tracking and optimization suggestions

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start Ollama service
ollama serve

# Pull LLM model
ollama pull llama3.1
```

### First Run

```bash
cd backend

# Edit config/config.json to set your universe and dates
# Then run:
python scripts/run_daily_trading.py
```

**Detailed Setup**: See [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md)

---

## 📁 Project Structure

```
ai-trader-ollama/
├── backend/                 # Python backend (main code)
│   ├── src/
│   │   ├── agents/         # All trading agents
│   │   ├── data/           # Portfolio, Trade Logger, Memory Manager
│   │   ├── tools/          # All available tools
│   │   ├── orchestrator/   # Main trading loop
│   │   └── llm/            # Ollama LLM client
│   ├── config/            # Configuration files
│   ├── tests/             # Test suite
│   ├── scripts/           # Utility scripts
│   └── prompts/           # Agent prompt templates
├── frontend/              # React dashboard (optional)
└── docs/                  # Documentation
```

---

## 🔄 How It Works

### Daily Trading Cycle

1. **Market Data Collection** (9:00 AM)
   - Fetches OHLCV + technical indicators for universe stocks
   - Analyzes yesterday's closing prices

2. **Multi-Agent Analysis**
   - **Market Analyst**: Evaluates trends, generates stock recommendations
   - **Discussion Agent**: Multi-round analysis with automatic tool calling (news, sentiment)
   - **Risk Analyst**: Assesses portfolio risk and position limits
   - **Trader Agent**: Generates buy/sell orders with position sizing

3. **Order Execution**
   - Places limit orders (pre-market)
   - Checks fills after market close
   - Updates portfolio automatically

4. **Memory & Tracking**
   - Saves complete daily cycle to memory
   - Records portfolio equity for performance tracking

**Detailed Workflow**: See [`docs/WORKFLOW.md`](docs/WORKFLOW.md)

---

## 🤖 Agent Architecture

| Agent | Purpose | Key Output |
|-------|---------|------------|
| **Market Agent** | Fetch OHLCV + technical indicators | Market data with TA |
| **Market Analyst** | Analyze trends, recommend stocks | Recommended buy candidates |
| **Discussion Agent** | Multi-round analysis with tools | Final stance & reasoning |
| **Risk Analyst** | Assess portfolio risk | Risk report & position limits |
| **Trader Agent** | Generate trading decisions | Buy/sell orders with prices |
| **Execution** | Execute trades, update portfolio | Executed trades & portfolio status |

**Agent Details**: See [`docs/AGENTS.md`](docs/AGENTS.md)

---

## 🛠️ Available Tools

Agents have access to various tools for market analysis:

- **Market Data**: `fetch_market_batch`, `vix_term`, `vix_close`
- **Sentiment**: `fear_greed`, `news_scan`, `plan_and_scan_news`
- **News & Economic Data**: `fetch_jin10_news`, `fetch_jin10_economic_data`, `web_search`
- **Crypto**: `fetch_crypto_batch`, `get_crypto_price`
- **Portfolio**: `portfolio_status`

**Tool Reference**: See [`docs/TOOLS.md`](docs/TOOLS.md)

---

## ⚙️ Configuration

### Main Config: `backend/config/config.json`

```json
{
  "universe": ["NVDA", "MSFT", "AAPL", ...],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "discussion_rounds": 3,
  "discussion_tool_budget": 2
}
```

**Configuration Guide**: See [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)

---

## 📅 Daily Automation

The system can run automatically every weekday at 9:00 AM:

### Windows

```powershell
cd backend\scripts
.\schedule_daily_task.ps1
```

### Linux/Mac

```bash
cd backend/scripts
bash schedule_daily_task.sh
```

**Setup Guide**: See [`backend/scripts/setup_daily_scheduler.md`](backend/scripts/setup_daily_scheduler.md)

---

## 📊 Monitoring & Optimization

### View Monitoring Report

```bash
cd backend
python scripts/monitoring_system.py --days 7
```

### View Optimization Suggestions

```bash
python scripts/optimization_system.py --days 30
```

### Combined Report

```bash
python scripts/run_monitoring_and_optimization.py
```

---

## 🧪 Testing

All tests are in `backend/tests/`:

```bash
cd backend

# Run all tests
python tests/run_all.py

# Run specific test
python tests/test_05_full_trading_loop.py
```

**Testing Guide**: See [`backend/tests/README.md`](backend/tests/README.md)

---

## 📚 Documentation

### Getting Started
- [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) - Detailed setup and first run guide
- [`backend/运行说明.md`](backend/运行说明.md) - 中文快速指南

### Core Concepts
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Complete daily workflow explanation
- [`docs/AGENTS.md`](docs/AGENTS.md) - Agent types, timing, and responsibilities
- [`docs/TOOLS.md`](docs/TOOLS.md) - Complete tool reference with examples
- [`docs/MEMORY_OPTIMIZATION.md`](docs/MEMORY_OPTIMIZATION.md) - Memory management system

### Trading Logic
- [`docs/TRADING_TIMELINE.md`](docs/TRADING_TIMELINE.md) - Trading timeline and execution flow
- [`docs/PRICE_DATA_STRATEGY.md`](docs/PRICE_DATA_STRATEGY.md) - Price data strategy explanation
- [`docs/ORDER_EXECUTION_AND_FILL_CHECK.md`](docs/ORDER_EXECUTION_AND_FILL_CHECK.md) - Order execution mechanism

### Advanced
- [`docs/MULTI_AGENT_DISCUSSION.md`](docs/MULTI_AGENT_DISCUSSION.md) - Discussion system details
- [`docs/HKUDS_COMPARISON_AND_FEEDBACK.md`](docs/HKUDS_COMPARISON_AND_FEEDBACK.md) - Comparison with HKUDS/AI-Trader

### Configuration & Automation
- [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) - Configuration guide
- [`backend/scripts/setup_daily_scheduler.md`](backend/scripts/setup_daily_scheduler.md) - Automation setup

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: src` | Run from `backend/` directory |
| Ollama connection error | Run `ollama serve` |
| VIX level = nan | System auto-falls back to VIXY |
| Config path error | Ensure `backend/config/agents.yaml` exists |

**More Help**: See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)

---

## 📄 License

MIT License © 2025 Wenyu Chiou

---

## 👤 Author

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu
