# 💹 AI-Trader Ollama

> **A Multi-Agent Trading System with 29 Advanced Tools + 6 Specialized LLM Agents**  
> 📈 Analyzing **NASDAQ-100** (118+ symbols) with comprehensive fundamental, technical, and sentiment analysis  
> 🧠 Fully autonomous agent collaboration with real-time market data integration  
> 🎨 Dark tech-themed UI with live visualization and real-time updates  
> 🧠 **RAG Memory System**: Agents learn from historical trading decisions  
> 📰 **Enhanced News Integration**: News data with summaries, sources, and timestamps displayed in frontend

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-deepseek--r1-orange.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### 🌐 **Live Demo**

> **View the dashboard online**: [**https://WenyuChiou.github.io/ai-trader-ollama/monitor.html**](https://WenyuChiou.github.io/ai-trader-ollama/monitor.html)
> 
> 🔒 **Read-Only Mode**: The public website is in read-only mode for security. Trading controls are disabled. Use localhost for full control.

---

## 📚 Table of Contents

- [System Overview](#-system-overview)
- [Quick Start](#-quick-start)
- [Historical Performance Analysis](#-historical-performance-analysis)
- [Scheduled Tasks & Automation](#-scheduled-tasks--automation)
- [Configuration](#-configuration)
- [Data Storage & Records](#-data-storage--records)
- [Multi-Agent Architecture](#-multi-agent-architecture)
- [Tool Suite (28 Tools)](#-tool-suite-28-tools)
- [Trading Workflow](#-trading-workflow)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## 🌟 System Overview

### What is AI-Trader Ollama?

AI-Trader Ollama is a **fully autonomous multi-agent trading system** that combines:
- **6 specialized LLM agents** working in collaboration
- **28 advanced tools** for market analysis (21 market tools + 7 memory/RAG tools)
- **Real-time data integration** from multiple sources
- **Intelligent risk management** with position controls
- **RAG Memory System**: Agents automatically retrieve and learn from historical trading decisions
- **Time-range equity tracking**: View portfolio performance over day/week/month/custom periods
- **Weekly memory compression**: Automatic summarization of weekly memories (Monday + weekend only)

### Core Philosophy

1. **Multi-perspective Analysis**: Different agents analyze the market from their specialized viewpoints
2. **Tool Diversity**: 28 tools provide comprehensive market coverage (21 market tools + 7 memory/RAG tools)
3. **RAG System**: Advanced memory system with semantic search, quality scoring, and relation analysis
4. **Tool Filtering & Validation**: System automatically filters invalid tool calls and enforces restrictions per analyst type
5. **RAG Memory System**: Agents automatically retrieve historical memories before making decisions
6. **Autonomous Decision Making**: Agents discuss, debate, and reach consensus
7. **Risk-First Approach**: Every decision passes through risk analysis
8. **Transparency**: All reasoning is logged and visible
9. **Historical Learning**: Agents learn from past successes and failures

---

## 📊 Historical Performance Analysis

### Viewing Trading Performance

The system provides comprehensive performance analysis through API endpoints and the frontend dashboard.

#### Key Performance Metrics

- **Total Return**: Overall profit/loss in dollars and percentage
- **Annualized Return**: Return adjusted for time period (if data spans multiple days)
- **Win Rate**: Percentage of profitable trades
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure (annualized)
- **Trading Statistics**: Total trades, winning trades, losing trades, average trade return

#### Using Performance APIs

**Get Overall Statistics**:
```bash
curl "http://localhost:8000/api/performance/statistics?start_date=2025-01-01&end_date=2025-01-31"
```

**Get Trades by Date**:
```bash
curl "http://localhost:8000/api/performance/trades-by-date?start_date=2025-01-01&limit=30"
```

**Get Symbol Analysis**:
```bash
# All symbols
curl "http://localhost:8000/api/performance/symbol-analysis"

# Specific symbol
curl "http://localhost:8000/api/performance/symbol-analysis?symbol=NVDA"
```

#### Performance Metrics Explained

- **Total Return %**: `(Current Value - Initial Value) / Initial Value * 100`
- **Win Rate**: `(Winning Trades / Total Trades) * 100`
- **Max Drawdown**: Largest decline from a peak value
- **Sharpe Ratio**: `(Average Return / Standard Deviation) * sqrt(252)` (annualized, higher is better)
- **Average Holding Period**: Average days between buy and sell for each symbol

#### Data Sources

Performance analysis uses data from:
- `equity_history.jsonl`: Net asset value history (recorded every 30 minutes)
- `filled_orders.jsonl`: Completed trades with realized P&L

See [Data Format Documentation](docs/DATA_FORMAT.md) for detailed file formats.

---

## 🚀 Quick Start

### Prerequisites

**1. Python Environment**
- Python 3.10 or higher required
- Download from: https://www.python.org/downloads/

**2. Ollama Setup**
- Install Ollama from: https://ollama.ai/
- Pull LLM model: `ollama pull deepseek-r1`

**3. API Keys (Optional but Recommended)**
- FRED API for economic data (free): https://fred.stlouisfed.org/docs/api/api_key.html
- Set environment variable: `$env:FRED_API_KEY="your_api_key_here"`

---

### 🎯 Quick Setup (3 Steps)

**Step 1: Install Dependencies**
```powershell
# Run from project root directory
.\scripts\setup_step1_install_dependencies.ps1
```
This will:
- ✅ Check Python installation
- ✅ Check Ollama installation and pull deepseek-r1 model
- ✅ Create virtual environment
- ✅ Install all Python dependencies

**Step 2: Configure System**
```powershell
.\scripts\setup_step2_configure.ps1
```
This will:
- ✅ Validate configuration files (config.json, agents.yaml)
- ✅ Initialize data directory
- ✅ Initialize portfolio state
- ✅ Check environment variables

**Step 3: Start Services**
```powershell
.\scripts\setup_step3_start_services.ps1
```
This will:
- ✅ Check Ollama service
- ✅ Check port availability
- ✅ Start API server (choose from 3 options)

**After Setup:**
- 🌐 **API Server**: http://localhost:8000
- 📊 **API Docs**: http://localhost:8000/docs
- 🎨 **Frontend**: Open `frontend/monitor.html` in your browser

**Optional: Setup Scheduled Tasks**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
```
This will configure automated tasks for trading, equity recording, and data updates.

**Or run all steps at once:**
```powershell
.\scripts\setup_all_steps.ps1
```

---

### 🎬 First Run

After completing the setup:

1. **Start Ollama** (if not already running):
```powershell
   ollama serve
   ```

2. **Open Frontend**:
   - Open `frontend/monitor.html` in your browser
   - Or access via: http://localhost:3000/monitor.html

3. **Execute First Trade Cycle**:
   - Click "▶️ Start Trading" or "▶️ Run Analysis" button
   - Wait for agents to analyze (30-60 seconds)
   - View results in the dashboard

4. **View Results**:
   - **Portfolio**: Current positions and P&L
   - **Conversations**: Agent discussions and analysis
   - **Trades**: Trading history
   - **Charts**: Equity curve with time range selector (Day/Week/Month/Custom)
   - **Memory**: Historical trading decisions and learning

---

### 📋 Manual Installation (Alternative)

If you prefer manual setup:

**1. Clone Repository**
```bash
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama
```

**2. Install Dependencies**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
```

**3. Initialize System**
```powershell
python scripts/init_data.py
```

**4. Start Backend API**

**Option A: Task Scheduler (Recommended for long-term running)**
```powershell
# Right-click and run as administrator:
scripts\start_api_task_admin.bat
```

**Option B: Windows Service (Requires NSSM)**
```powershell
# Right-click and run as administrator:
scripts\start_api_service_admin.bat
```

**Option C: Development Mode (Requires window open)**

**With Virtual Environment** (Recommended):

**Method A: Using & operator** (PowerShell standard, same as monitor script):
```powershell
# Activate virtual environment first
& .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Method B: Using dot sourcing** (alternative):
```powershell
# Activate virtual environment first
. .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Direct Command** (if virtual environment is already activated):
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Command Parameters**:
- `--host 0.0.0.0`: Listen on all network interfaces (accessible from other devices)
- `--port 8000`: Use port 8000
- `--reload`: Enable auto-reload on code changes (development mode)

**Notes**: 
- Keep the terminal window open. Closing it will stop the API server.
- Both activation methods (Method A and B) work. Method A (`&`) is the PowerShell standard and matches what the monitor script uses for auto-restart.

**5. Access Dashboard**
- Open `frontend/monitor.html` in your browser
- Or access via: http://localhost:3000/monitor.html (if using a local server)

---

## ⚙️ Configuration

> **📝 Configuration Files**: All configuration is done through JSON/YAML files. No code changes required!

### 📄 Main Config File: `backend/config/config.json`

The main configuration file controls trading parameters, universe selection, and LLM settings.

#### 📋 Complete Configuration Reference

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  "universe": ["NVDA", "MSFT", "AAPL", ...],
  "crypto": ["BTC-USD", "ETH-USD", ...],
  "initial_cash": 10000,
  "position_limit_mode": "auto",
  "_position_limit_per_stock": null,
  "_position_limit_total": null,
  "_position_limit_min_per_stock": null,
  "min_cash_reserve_ratio": null,
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
  },
  "preferred_domains": [
    "www.cboe.com",
    "www.wsj.com",
    "www.reuters.com"
  ]
}
```

#### 🔧 Configuration Parameters

| Parameter | Description | Options | Default Value |
|-----------|-------------|---------|---------------|
| **Trading Universe** |
| `universe_source` | Universe source type | `"custom"`, `"nasdaq100"` | `"custom"` |
| `universe_limit` | Maximum symbols to analyze | Positive integer | `100` |
| `universe` | List of stock symbols | Array of strings | NASDAQ-100 + ETFs |
| `crypto` | Cryptocurrency symbols | Array of strings | `["BTC-USD", "ETH-USD", ...]` |
| **Capital & Position Limits** |
| `initial_cash` | Starting capital | Float | `10000` (USD) |
| `position_limit_mode` | Position limit mode | `"auto"`, `"configured"` | `"auto"` (LLM autonomous) |
| `_position_limit_per_stock` | Max % per stock | `0.0-1.0` or `null` | `null` (only used when mode=`"configured"`) |
| `_position_limit_total` | Max % total equity | `0.0-1.0` or `null` | `null` (only used when mode=`"configured"`) |
| `_position_limit_min_per_stock` | Min % per stock | `0.0-1.0` or `null` | `null` (only used when mode=`"configured"`) |
| `min_cash_reserve_ratio` | Min cash reserve % | `0.0-1.0` or `null` | `null` (only used when mode=`"configured"`) |
| **Trading Behavior** |
| `discussion_rounds` | Number of discussion rounds | `1-5` | `3` |
| `discussion_auto_tools` | Enable automatic tool calls | `true`, `false` | `true` |
| `discussion_tool_budget` | Max tool calls per cycle (Market/Technical/Sentiment only) | Positive integer | `15` |
| `budget_allocation` | Custom budget allocation per analyst (fundamental excluded) | Object | `{"market": 3, "technical": 4, "sentiment": 4}` |
| `max_orders_per_cycle` | Max orders per cycle | Positive integer | `20` |
| `trade_cooldown_hours` | Hours before trading same symbol | Float | `24.0` |
| **LLM Configuration** |
| `llm.default_model` | LLM model name | `"deepseek-r1"`, `"deepseek-r1:7b"`, `"deepseek-r1:32b"`, etc. | `"deepseek-r1"` |
| `llm.ollama_host` | Ollama server address | URL string | `"http://localhost:11434"` |
| `llm.auto_pull` | Auto-pull model if not found | `true`, `false` | `true` |
| `llm.timeout_seconds` | Request timeout | Float (seconds) | `8.0` |
| **Data Sources** |
| `preferred_domains` | Preferred news/data domains | Array of URLs | Financial news sites |

#### 📊 Parameter Details

**Trading Universe:**
- `universe`: List of stock symbols to trade (includes inverse/leveraged ETFs like SQQQ, TQQQ, TQQQ, SPXL, UPRO)
- `crypto`: List of cryptocurrency symbols (optional, for crypto trading)
- `universe_limit`: Maximum number of symbols to analyze (default: 100)

**Position Limits (Two Modes - Auto vs Configured):**

**Mode 1: `"auto"` (Default - LLM Autonomous):**
- Position limits are **disabled** - agent has **complete freedom** to decide position sizes
- Agent decides based on:
  - Number of recommended stocks (many stocks → smaller positions, few stocks → larger positions)
  - Signal strength and diversification needs
  - Market conditions and risk assessment
- Cash reserve is also LLM-decided (no hard limit)
- **This is the default mode** - agent operates autonomously

**Mode 2: `"configured"` (With Constraints):**
- Set `position_limit_mode` to `"configured"` to enable hard limits
- Uncomment and set position limit values:
  - `_position_limit_per_stock`: Max % per stock (e.g., 0.15 = 15%)
  - `_position_limit_total`: Max % total equity (e.g., 0.80 = 80%, leaves 20% cash)
  - `_position_limit_min_per_stock`: Min % per stock (e.g., 0.03 = 3%)
  - `min_cash_reserve_ratio`: Min cash reserve % (e.g., 0.20 = 20%)
- Agent will respect these hard limits when making trading decisions

**Example Configuration:**

```json
// Auto mode (default - LLM autonomous)
{
  "position_limit_mode": "auto",
  "_position_limit_per_stock": null,
  "_position_limit_total": null,
  "_position_limit_min_per_stock": null,
  "min_cash_reserve_ratio": null
}

// Configured mode (with constraints)
{
  "position_limit_mode": "configured",
  "_position_limit_per_stock": 0.15,
  "_position_limit_total": 0.80,
  "_position_limit_min_per_stock": 0.03,
  "min_cash_reserve_ratio": 0.20
}
```

**Trading Behavior:**
- `initial_cash`: Starting capital ($10,000 default)
- `discussion_rounds`: Number of discussion rounds (3 default, each round includes all 4 analysts)
- `discussion_tool_budget`: Max tool calls per cycle (15 default, shared across Market/Technical/Sentiment Analysts only)
- `budget_allocation`: Optional custom budget allocation per analyst (e.g., `{"market": 3, "technical": 4, "sentiment": 4}`). Fundamental Analyst is automatically excluded as its tools are not subject to budget limits.
- `max_orders_per_cycle`: Maximum orders per trading cycle (20 default, guideline for LLM)
- `trade_cooldown_hours`: Hours to wait before trading same symbol again (24.0 default)

**LLM Configuration:**
- `llm.default_model`: **Unified LLM model for all agents** (`deepseek-r1` default)
  - Available models: `deepseek-r1`, `deepseek-r1:7b`, `deepseek-r1:32b`, etc.
  - **All agents use this model by default** - no need to specify in `agents.yaml` unless you want a specific agent to use a different model
  - To use a different model, change this value and ensure it's pulled in Ollama: `ollama pull <model-name>`
- `llm.ollama_host`: Ollama server address (default: `http://localhost:11434`)
- `llm.auto_pull`: Automatically pull model if not found (true default)
- `llm.timeout_seconds`: Request timeout (8.0 seconds default)

#### Changing the LLM Model

**✅ Unified Model Configuration (Recommended):**

All agents automatically use `config.json` → `llm.default_model`. Simply update one place:

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

Individual agent configurations for temperature and prompt files. **Model is unified from `config.json`**.

```yaml
market_analyst:
  name: Market Analyst
  # model: deepseek-r1  # Uses config.json llm.default_model if not specified
  temperature: 0.3
  prompt_file: ../prompts/market_analyst.yml

technical_analyst:
  name: Technical Analyst
  # model: deepseek-r1  # Uses config.json llm.default_model if not specified
  temperature: 0.2
  prompt_file: ../prompts/technical_analyst.yml

# ... (8 agents total)
```

**Model Priority:**
1. `agents.yaml` → `model` field (if specified) - **highest priority**
2. `config.json` → `llm.default_model` - **default for all agents**
3. `"llama3.1"` - fallback

**To use different models per agent (optional):**
```yaml
market_analyst:
  model: deepseek-r1:32b  # Override: Use larger model for market analysis
  temperature: 0.3

technical_analyst:
  # No model specified - uses config.json llm.default_model
  temperature: 0.2
```

**Summary:**
- ✅ **Default behavior**: All agents use `config.json` → `llm.default_model`
- ✅ **No need to specify model in `agents.yaml`** unless you want a specific agent to use a different model
- ✅ **Change model in one place** (`config.json`) to update all agents

---

## 💾 Data Storage & Records

### 📁 Data Directory Structure

**All agent-generated data, conversations, positions, and trading records are stored in `data/logs/` directory** (relative to project root).

**Path Details:**
- **Project Root**: The directory containing `README.md` and `backend/` folder
- **Data Directory**: `{project_root}/data/logs/`
- **Example**: If project is at `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\`, then data is stored at `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs\`

**Quick Access:**
```powershell
# View portfolio state
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# View recent conversations (last 10)
Get-Content data\logs\discussion_actions.jsonl -Tail 10

# View equity history
Get-Content data\logs\equity_history.jsonl

# View filled orders
Get-Content data\logs\filled_orders.jsonl
```

**Complete Directory Structure:**
```
data/logs/
├── portfolio_state.json          # 持仓记录 (Current portfolio state: cash, positions, costs)
├── equity_history.jsonl          # 净值历史 (Net value history, recorded every 30 minutes, all timestamps preserved)
├── discussion_actions.jsonl      # 聊天记录 (All agent conversations, analyses, tool calls)
├── trades.jsonl                  # 交易记录 (All executed trades)
├── filled_orders.jsonl            # 已成交订单 (Completed orders with realized P&L)
├── pending_orders.jsonl          # 待处理订单 (Pending orders waiting for execution)
├── portfolio_state_backup_*.json  # 备份文件 (Auto-backup files from initialization)
├── discussion_actions_backup_*.jsonl  # 备份文件 (Backup files)
└── memory/
    ├── daily/                    # 每日快照 (Daily memory snapshots)
    │   └── YYYY-MM-DD.json
    ├── weekly/                   # 每周汇总 (Weekly summaries)
    │   └── YYYY-W##.jsonl
    ├── monthly/                  # 每月汇总 (Monthly summaries)
    │   └── YYYY-MM.jsonl
    └── index/                    # 内存索引 (Memory indices)
        └── daily_index.json
```

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

### System Initialization

**API Endpoint**: `POST /api/system/init?force=true`

**Function**: Reset the system to initial state by deleting all trading data files.

**What Gets Deleted**:
- `portfolio_state.json` (automatically backed up before deletion)
- `pending_orders.jsonl`
- `filled_orders.jsonl`
- `equity_history.jsonl`
- `discussion_actions.jsonl`

**What Gets Preserved**:
- `memory/` directory (agent learning data is preserved)
- Backup files (`portfolio_state_backup_*.json`, etc.)

**Usage**:
```bash
# Via API
curl -X POST "http://localhost:8000/api/system/init?force=true"

# Or from frontend
# Click "Initialize System" button (requires force=true confirmation)
```

**Safety Features**:
- Requires `force=true` parameter to prevent accidental deletion
- Automatically creates backup of `portfolio_state.json` before deletion
- Backup filename format: `portfolio_state_backup_YYYYMMDD_HHMMSS.json`

**Initialization Code Location**:
- **File**: `backend/src/api/server.py`
- **Function**: `system_init()` (lines 1055-1110)
- **Data Directory**: Automatically determined from project root → `data/logs/`

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

**Important Features**:
- ✅ **All Timestamps Preserved**: Every 30-minute record is kept (no deduplication by date)
- ✅ **Time-Range Queries**: Frontend supports day/week/month/custom date range selection
- ✅ **API Support**: Backend API supports `period` (day/week/month), `start_date`, `end_date`, `start_timestamp`, `end_timestamp` parameters
- ✅ **Default View**: Frontend displays recent week's data by default

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

**Timestamp Format**:
- **`date`**: Date in `YYYY-MM-DD` format (e.g., `"2025-01-28"`)
- **`timestamp`**: ISO 8601 format with UTC timezone (e.g., `"2025-01-28T10:00:00.000Z"`)
  - Format: `YYYY-MM-DDTHH:MM:SS.sssZ`
  - Always includes `Z` suffix indicating UTC timezone
  - Automatically generated when recording equity snapshot
  - Used for chronological sorting and time-based queries

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
  "summary": "Market shows mixed sentiment...",
  "stance": "NEUTRAL",
  "tools_used": ["get_market_indices", "get_sector_rotation"]
}
```

**Key Fields**:
- `agent`: Agent name (MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst, DiscussionCoordinator, RiskAnalyst, TraderAgent)
- `round`: Discussion round number (1, 2, 3, or 0 for non-discussion entries)
- `summary`: Agent's analysis summary (extracted from content if not present)
- `stance`: Market stance (BULLISH, BEARISH, NEUTRAL)
- `tools_used`: List of tools called by the agent
- `type`: Entry type (discussion, tool_call, decision, etc.)

---

### Quick Data Access Commands

**View Portfolio State** (Windows PowerShell):
```powershell
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**View Recent Conversations** (Last 10 entries):
```powershell
Get-Content data\logs\discussion_actions.jsonl -Tail 10
```

**View Equity History**:
```powershell
Get-Content data\logs\equity_history.jsonl
```

**View Filled Orders**:
```powershell
Get-Content data\logs\filled_orders.jsonl
```

**View Daily Memory Snapshot**:
```powershell
Get-Content data\logs\memory\daily\2025-11-16.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
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
- **Analysis Targets**: 
  - **With Holdings**: Current holdings + Recommended stocks + Major indices (SPY, QQQ, DIA, IWM, VTI)
  - **Without Holdings**: Recommended stocks + Major indices (SPY, QQQ, DIA, IWM, VTI)
  - **All targets must be analyzed simultaneously**
- **Tool Restrictions**: 
  - **Does NOT use news tools** (news analysis is handled by Sentiment Analyst)
  - System automatically filters out news tools if requested
  - Focuses on technical indicators and price action only

#### 3. **Fundamental Analyst** 💼
- **Specialty**: Financial statements, valuation, earnings
- **Priority Tools**: `get_company_fundamentals`, `get_earnings_history`, `get_financial_statements`
- **Analysis Targets**: 
  - **With Holdings**: Non-ETF holdings + Non-ETF recommended stocks (ETFs excluded)
  - **Without Holdings**: Non-ETF recommended stocks only
  - **ETFs and indices are excluded** (ETFs don't need fundamental analysis)
- **Budget Priority**: All fundamental analysis tools execute without tool budget restrictions (ensures all recommended stocks and holdings are analyzed)
- **Budget Allocation**: Tool budget is allocated among Market, Technical, and Sentiment Analysts only (Fundamental Analyst is excluded from budget allocation as its tools are not subject to budget limits)
- **Custom Budget Allocation**: You can configure budget allocation per analyst in `config.json` under `budget_allocation` (fundamental will be automatically excluded)

#### 4. **Sentiment Analyst** 😊
- **Specialty**: Market psychology, news sentiment, fear/greed
- **Priority Tools**: `fear_greed`, `vix_term`, `plan_and_scan_news` (mandatory)
- **News Analysis**: 
  - Automatically calls `plan_and_scan_news` at the start of each analysis cycle
  - System automatically filters out deprecated `news_scan` tool (converts to `plan_and_scan_news`)
  - If LLM requests `news_scan`, it's automatically converted to `plan_and_scan_news`
  - News analysis is mandatory for sentiment assessment

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

## 🛠️ Tool Suite (28 Tools)

The system includes **28 advanced tools** organized into two categories:
- **21 Market Analysis Tools**: Real-time data, technical indicators, fundamental data, news, and economic indicators
- **7 Memory/RAG Tools**: Historical memory retrieval with semantic search for learning from past trading decisions

**Tool Usage Rules**:
- **Tool Budget**: Shared across Market, Technical, and Sentiment Analysts (default: 15 calls per cycle)
- **Fundamental Analyst**: Tools are NOT subject to budget limits (can analyze all recommended stocks and holdings without budget constraints)
- **Budget Allocation**: Configurable in `config.json` via `budget_allocation` field (fundamental is automatically excluded)
- **Tool Filtering**: System automatically filters invalid tool calls and enforces restrictions
- **Tool Validation**: All tool calls are validated before execution (must have valid `name` field)
- **News Tools**: `news_scan` has been removed. Use `plan_and_scan_news` instead (includes LLM-generated summaries and keywords)
- **Automatic Conversion**: If LLM requests deprecated `news_scan`, it's automatically converted to `plan_and_scan_news`

### 🧠 Memory/RAG Tools (7 Tools)

These tools allow agents to retrieve and learn from historical trading memories:

1. **`get_recent_memories`**
   - **Purpose**: Get recent trading memories (last N days) for context
   - **Usage**: Automatically called at the start of each trading cycle
   - **Parameters**: `days` (default: 5), `summary_only` (default: true)
   - **Returns**: List of recent trading decisions, stances, and outcomes

2. **`search_memories_by_symbol`**
   - **Purpose**: Search historical memories for a specific stock
   - **Usage**: Called when analyzing specific stocks
   - **Parameters**: `symbol` (required), `days` (default: 30)
   - **Returns**: Historical analysis and decisions for the stock

3. **`search_memories_by_date_range`**
   - **Purpose**: Search memories within a date range
   - **Usage**: Review what happened during specific periods
   - **Parameters**: `start_date`, `end_date` (YYYY-MM-DD format)
   - **Returns**: Memories within the specified date range

4. **`get_weekly_memory_summary`**
   - **Purpose**: Get weekly compressed memory summary
   - **Usage**: Longer-term context (only Monday and weekend records preserved)
   - **Parameters**: `week_str` (optional, format: "2025-W01")
   - **Returns**: Weekly summary with Monday and weekend records

5. **`get_monthly_memory_summary`**
   - **Purpose**: Get monthly compressed memory summary
   - **Usage**: Very long-term trends and patterns
   - **Parameters**: `month_str` (optional, format: "2025-01")
   - **Returns**: Monthly aggregated summary

6. **`search_similar_decisions`**
   - **Purpose**: Search for similar trading decisions for a stock
   - **Usage**: Learn from past BUY/SELL actions
   - **Parameters**: `symbol` (required), `action_type` (optional: "BUY", "SELL", "HOLD")
   - **Returns**: Similar historical decisions with outcomes
   - **Features**: Supports semantic search to find similar situations

7. **`search_memories_by_semantic`** (NEW)
   - **Purpose**: Semantic search for memories using natural language query
   - **Usage**: Find memories related to specific concepts, market conditions, or trading patterns
   - **Parameters**: `query` (required, natural language), `top_k` (default: 10)
   - **Returns**: Memories ranked by semantic similarity
   - **Examples**: 
     - "bearish market with high volatility"
     - "successful NVDA trades"
     - "decisions during market crash"

**Memory System Features**:
- ✅ **Automatic Memory Loading**: Recent memories (last 5 days) are automatically loaded at the start of each trading cycle
- ✅ **Forced Memory Retrieval**: Market Analyst always calls `get_recent_memories` at the start (enforced by system)
- ✅ **Short/Long-Term Memory Separation**: 
  - Short-term (0-7 days): Full storage with complete transcripts
  - Medium-term (8-30 days): Summary storage with key conversation points
  - Long-term (30+ days): Compressed storage with core insights
- ✅ **Semantic Search**: Vector-based similarity search using embeddings (Ollama or sentence-transformers)
- ✅ **Hybrid Retrieval**: Combines keyword search (fast filtering) with semantic search (similarity matching)
- ✅ **Memory Quality Scoring**: Importance scoring based on P&L, volume, information density, and time decay
- ✅ **Memory Relations**: Automatic discovery of related memories (same stocks, similar conditions, similar decisions)
- ✅ **Caching**: Hot memory cache for recent 7 days, query result cache, and vector cache
- ✅ **Weekly Compression**: Old memories (>30 days) are compressed to weekly summaries (Monday + weekend only)
- ✅ **RAG Integration**: Agents use memories to avoid repeating mistakes and learn from successes

### 📊 Market Analysis Tools (21 Tools)

### Sentiment & Risk (3 tools)
- `vix_term`: VIX term structure
- `vix_close`: Historical VIX prices
- `fear_greed`: CNN Fear & Greed Index

### News & Information (3 tools)
- `plan_and_scan_news`: LLM-powered news query (recommended, includes article content with summaries and keywords)
  - **Usage**: Primary news tool for sentiment analysis
  - **Features**: Returns articles with LLM-generated summaries and keywords
  - **Parameters**: `tickers` (list of symbols), `max_articles` (default: 10), `recency_days` (default: 2), `fetch_body_top` (number of articles with full content)
  - **Mandatory for**: Sentiment Analyst (automatically added if not requested)
  - **Filtered from**: Technical Analyst (news analysis is handled by Sentiment Analyst)
- `web_search`: DuckDuckGo search
- `fetch_url`: Extract content from URL
- **News Display**: Frontend displays news with summaries, sources, timestamps, and keywords (sorted by recency)
- **Note**: `news_scan` has been removed. Use `plan_and_scan_news` instead. If LLM requests `news_scan`, it's automatically converted to `plan_and_scan_news`.

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
        │     │ • Economic indicators     │   │
        │     │ • Tools: get_market_      │   │
        │     │   indices, get_sector_   │   │
        │     │   rotation, get_economic_ │   │
        │     │   summary                │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Technical Analyst         │   │
        │     │ • Price patterns          │   │
        │     │ • Support/resistance      │   │
        │     │ • Technical indicators    │   │
        │     │ • Tools: get_advanced_    │   │
        │     │   indicators, get_support │   │
        │     │ • NO news tools (filtered)│   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Fundamental Analyst       │   │
        │     │ • Financial statements    │   │
        │     │ • Valuation metrics       │   │
        │     │ • Earnings history        │   │
        │     │ • Tools: get_company_     │   │
        │     │   fundamentals (unlimited)│   │
        │     │ • Analyzes all non-ETF    │   │
        │     │   stocks (no budget limit)│   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ Sentiment Analyst         │   │
        │     │ • News sentiment          │   │
        │     │ • Fear & Greed Index      │   │
        │     │ • VIX term structure      │   │
        │     │ • Tool: plan_and_scan_news│   │
        │     │   (mandatory, auto-added) │   │
        │     └──────────────────────────┘   │
        │     • Tool filtering & validation │
        │     • Invalid calls filtered out  │
        │     Time: 30-60 seconds             │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  3. Discussion Coordinator          │
        │     • Synthesizes all 4 analysts    │
        │     • Reviews tool results          │
        │     • Identifies consensus/disagreement│
        │     • Final consensus (stance)       │
        │     • Tool usage tracking           │
        │     • Tool filtering & validation   │
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
   - Risk Analyst recommendations → Directly influence position sizing
   - Market conditions and risk assessment → Considered in decision making

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

**4. Order Execution Rules**
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
│   ├── News APIs (plan_and_scan_news - recommended, includes LLM-generated summaries)
│   ├── Fear & Greed Index (CNN, standardized classification)
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
         │   ├── Market Analyst: Uses get_market_indices, get_sector_rotation, get_economic_summary
         │   ├── Technical Analyst: Uses get_advanced_indicators, get_support_resistance (NO news tools)
         │   ├── Fundamental Analyst: Uses get_company_fundamentals, get_earnings_history (NOT subject to budget - analyzes all recommended stocks and holdings)
         │   └── Sentiment Analyst: Uses fear_greed, vix_term, plan_and_scan_news (mandatory)
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
    └── Tool calls: fear_greed, vix_term, plan_and_scan_news (mandatory)

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

**Rule Classification**:
The system uses **two types of rules**:
1. **LLM-Decided Rules (Guidelines)**: Trader Agent (LLM) makes decisions based on these guidelines, with flexibility to adjust based on market conditions
2. **Configurable Hard Rules**: Can be set in `config.json` and are strictly enforced by the system

**Current System Default**: **Complete Agent Freedom** (Trader Agent has complete freedom to decide position sizes, only limited by available cash and market status)

---

#### 1. Market Status Rules (Hard Rules - System Enforced)

**Type**: System-enforced (cannot be overridden)

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

**Configuration**: Not configurable (system-enforced)

---

#### 2. Position Limits

**Current System**: **Complete Agent Freedom** - Position limits are **OPTIONAL** and only enforced if explicitly set in `config.json`

**Default Behavior (No Limits Set)**:

| Rule | Default Behavior | Type | How It Works |
|------|------------------|------|--------------|
| **Per Stock Maximum** | **No Limit** | Agent Decision | Agent decides based on signal strength, diversification needs, and market conditions |
| **Total Position Maximum** | **No Limit** | Agent Decision | Agent can use all available cash (limited only by cash balance) |
| **Minimum Position Size** | **No Limit** | Agent Decision | Agent can use any position size based on market conditions |
| **Maximum Positions** | **No Limit** | Agent Decision | Agent decides number of positions based on opportunities |

**Agent Decision Logic (No Limits)**:
- **Stock Count Adjustment**:
  - Many stocks (>10): Smaller positions per stock
  - Few stocks (<5): Larger positions per stock
- **Signal Strength**: Strong signals → larger positions, weak signals → smaller positions
- **Diversification**: Agent considers diversification needs when deciding position sizes

**Optional Limits (If Set in `config.json`)**:

| Rule | Configurable | Type | How It Works |
|------|--------------|------|--------------|
| **Per Stock Maximum** | Yes (`position_limit_per_stock`) | Hard Limit | Agent will respect this limit if set |
| **Total Position Maximum** | Yes (`position_limit_total`) | Hard Limit | Agent will respect this limit if set |
| **Minimum Position Size** | Yes (`position_limit_min_per_stock`) | Hard Limit | Agent will respect this limit if set |
| **Maximum Positions** | Yes (`max_positions`) | Hard Limit | Agent will respect this limit if set |

**LLM Decision Process**:
```
Trader Agent (LLM) receives:
├── Position limit guidelines (from config.json or defaults)
├── Risk Analyst recommendations
├── Market conditions (VIX, sentiment, etc.)
├── Current positions
└── Analyst consensus

Trader Agent decides:
├── Which stocks to buy/sell
├── Position sizes (within guideline ranges)
├── Number of positions (considering diversification)
└── Rationale for decisions
```

**Configuration in `config.json`**:

**Auto Mode (Default)**:
```json
{
  "position_limit_mode": "auto",
  "_position_limit_per_stock": null,
  "_position_limit_total": null,
  "_position_limit_min_per_stock": null,
  "min_cash_reserve_ratio": null
}
```

**Configured Mode (With Hard Limits)**:
```json
{
  "position_limit_mode": "configured",
  "_position_limit_per_stock": 0.15,
  "_position_limit_total": 0.80,
  "_position_limit_min_per_stock": 0.03,
  "min_cash_reserve_ratio": 0.20
}
```

**Note**: 
- In `"auto"` mode, the LLM has complete freedom to decide position sizes based on market conditions
- In `"configured"` mode, the LLM will respect the hard limits you set

**Example LLM Decisions**:
- **High VIX (7-10)**: LLM might use 5-8% per stock (below 15% guideline)
- **Low VIX (0-3)**: LLM might use 10-15% per stock (up to guideline)
- **Many recommended stocks**: LLM might use smaller positions per stock (e.g., 5-8%)
- **Few recommended stocks**: LLM might use larger positions per stock (e.g., 12-15%)

---

#### 3. Cash Management Rules

**Current System**: **Two Modes - Auto vs Configured**

**Mode 1: `"auto"` (Default - LLM Autonomous)**:

| Rule | Default Behavior | Type | How It Works |
|------|------------------|------|--------------|
| **Cash Reserve** | **No Limit** | Agent Decision | Agent decides cash reserve based on market conditions and risk |
| **Available Cash** | **Flexible** | Agent Decision | Agent can use all available cash if opportunities are strong |

**Mode 2: `"configured"` (With Hard Limit)**:

| Rule | Configurable | Type | How It Works |
|------|--------------|------|--------------|
| **Cash Reserve** | Yes (`min_cash_reserve_ratio`) | Hard Limit | Agent will maintain minimum cash reserve (e.g., 20%) |
| **Available Cash** | Limited by Reserve | Hard Limit | Agent can only use cash above the reserve threshold |

**LLM Decision Process**:
```
Trader Agent (LLM) receives:
├── Current cash balance
├── Cash reserve guideline (20%)
├── Recommended stocks and quantities
└── Risk assessment

Trader Agent decides:
├── How much cash to use (can use more or less than guideline)
├── Which orders to prioritize if cash is limited
└── Whether to reduce position sizes or skip some orders
```

**Configurable in `config.json`** (Optional):
```json
{
  "min_cash_reserve_ratio": 0.20  // Guideline: Keep 20% cash (LLM can adjust)
}
```

**System Safety Check** (Hard Rule - Cannot Override):
```
IF order_cost > portfolio.cash:
    Reduce quantity OR skip order
```
This is a **hard safety check** to prevent negative cash balance.

---

#### 4. Order Execution Rules (Hard Rules - System Enforced)

**Type**: System-enforced (cannot be overridden)

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

**Configuration**: Not configurable (system-enforced)

---

#### 6. Trading Frequency & Order Limits (Configurable)

**Type**: **Configurable in `config.json`**

| Rule | Default | Configurable | Description |
|------|---------|--------------|-------------|
| **Trading Frequency** | Every 30 minutes | No (system-enforced) | Fixed at 30-minute intervals |
| **Max Orders Per Cycle** | 20 | Yes | Maximum number of orders per trading cycle |
| **Discussion Rounds** | 3 | Yes | Number of discussion rounds |
| **Tool Budget** | 15 | Yes | Maximum tool calls per cycle (Market/Technical/Sentiment only) |
| **Budget Allocation** | `{"market": 3, "technical": 4, "sentiment": 4}` | Yes | Custom allocation per analyst (fundamental excluded) |

**Configurable in `config.json`**:
```json
{
  "max_orders_per_cycle": 20,        // Maximum orders per cycle (guideline for LLM)
  "discussion_rounds": 3,            // Number of discussion rounds
  "discussion_tool_budget": 15,      // Tool calls per cycle (Market/Technical/Sentiment only)
  "budget_allocation": {             // Optional: Custom allocation (fundamental excluded)
    "market": 3,
    "technical": 4,
    "sentiment": 4
  }
}
```

**Note**: `max_orders_per_cycle` is a **guideline** for the LLM. The LLM can generate fewer orders if it determines that's appropriate.

---

#### 7. Conversation & Analysis Rules

**Type**: **Configurable in `config.json`**

**Discussion Rounds**:
- **Number of Rounds**: 3 rounds per cycle (configurable)
- **Participants**: All 4 analysts participate in each round
- **Tool Budget**: 15 tool calls per cycle (configurable, shared across Market/Technical/Sentiment Analysts only)
- **Fundamental Analyst**: Tools are NOT subject to budget limits (analyzes all recommended stocks and holdings)
- **Budget Allocation**: Configurable via `budget_allocation` in `config.json` (fundamental automatically excluded)
- **Round Structure**:
  - Round 1: Initial analysis, tool calls
  - Round 2: Refinement based on Round 1, additional tool calls if needed
  - Round 3: Final synthesis, Discussion Coordinator summarizes

**Tool Call Rules**:
- Each analyst can call tools independently
- Tool results shared across rounds
- Tool budget tracked per cycle
- If budget exhausted, agents continue without tools
- **Tool Filtering**: System automatically filters invalid tool calls and enforces restrictions:
  - Technical Analyst: News tools are automatically filtered out
  - Sentiment Analyst: Deprecated `news_scan` is converted to `plan_and_scan_news`
  - Fundamental Analyst: Invalid tool calls (missing name) are filtered out
  - All analysts: Tool calls are validated before execution

**Tool Restrictions by Analyst**:
- **Technical Analyst**: Cannot use news tools (filtered automatically)
- **Sentiment Analyst**: Must use `plan_and_scan_news` (mandatory, auto-added if missing)
- **Fundamental Analyst**: `get_company_fundamentals` executes without budget restrictions
- **Market Analyst**: No specific restrictions (uses market and economic tools)

**Configurable in `config.json`**:
```json
{
  "discussion_rounds": 3,              // Number of discussion rounds
  "discussion_tool_budget": 15,        // Tool calls per cycle
  "discussion_auto_tools": true        // Enable automatic tool calls
}
```

---

### Rule Summary Table

| Rule Category | Type | Configurable | Current Default | LLM Decision |
|---------------|------|--------------|-----------------|--------------|
| **Market Status** | Hard (System) | No | 9:30 AM - 4:00 PM ET | N/A (System-enforced) |
| **Per Stock Max** | Optional Limit | Yes (`position_limit_per_stock`) | **No Limit** (if not set) | ✅ Agent decides freely (or respects limit if set) |
| **Total Position Max** | Optional Limit | Yes (`position_limit_total`) | **No Limit** (if not set) | ✅ Agent decides freely (or respects limit if set) |
| **Min Position Size** | Optional Limit | Yes (`position_limit_min_per_stock`) | **No Limit** (if not set) | ✅ Agent decides freely (or respects limit if set) |
| **Max Positions** | Optional Limit | Yes (`max_positions`) | **No Limit** (if not set) | ✅ Agent decides freely (or respects limit if set) |
| **Cash Reserve** | Optional Limit | Yes (`min_cash_reserve_ratio`) | **No Limit** (if not set) | ✅ Agent decides freely (or respects limit if set) |
| **Cash Safety** | Hard (System) | No | Must have cash | N/A (System-enforced) |
| **Order Type** | Hard (System) | No | Market orders only | N/A (System-enforced) |
| **Risk-Based Sizing** | LLM Guideline | No | VIX-based ranges | ✅ LLM decides based on risk |
| **Max Orders/Cycle** | LLM Guideline | Yes (`max_orders_per_cycle`) | 20 | ✅ LLM decides actual count |
| **Discussion Rounds** | Configurable | Yes (`discussion_rounds`) | 3 | N/A (System setting) |
| **Tool Budget** | Configurable | Yes (`discussion_tool_budget`) | 15 | N/A (System setting) |

**Key**:
- ✅ **LLM-Decided**: Trader Agent (LLM) makes the actual decision based on guidelines
- **Configurable**: Can be set in `config.json` (if not set, uses defaults)
- **Hard (System)**: System-enforced, cannot be overridden

---

### How to Configure Rules

**Option 1: Complete Agent Freedom (Current Default - Recommended)**

**Remove or comment out position limits in `config.json`** to give the agent complete freedom:

```json
{
  "_comment_position_limits": "Position limits are OPTIONAL. Remove these lines to give agent complete freedom.",
  "_position_limit_per_stock": 0.15,      // Commented out - agent has freedom
  "_position_limit_total": 0.85,          // Commented out - agent has freedom
  "_position_limit_min_per_stock": 0.03    // Commented out - agent has freedom
}
```

**Or simply don't include these fields at all.**

The agent will:
- **Decide position sizes autonomously** based on:
  - Market conditions and risk assessment
  - Signal strength and diversification needs
  - Number of recommended stocks
- **Adjust based on number of recommended stocks**:
  - Many stocks (>10): Use smaller positions (5-8%)
  - Few stocks (<5): Use larger positions (12-15%)
- **Consider signal strength, diversification needs, and market conditions**
- **Only limited by available cash** (hard safety check)

**Example Agent Decisions (No Limits)**:
- **High VIX (7.5) + 8 recommended stocks**: Uses 6% per stock (conservative)
- **Low VIX (2.0) + 3 recommended stocks**: Uses 14% per stock (aggressive)
- **Medium VIX (5.0) + 15 recommended stocks**: Uses 7% per stock (diversified)

**Option 2: Set Position Limits (Optional)**

If you want to set limits, explicitly add them to `config.json`:
```json
{
  "position_limit_per_stock": 0.15,      // Max 15% per stock (agent will respect)
  "position_limit_total": 0.85,          // Max 85% total (agent will respect)
  "position_limit_min_per_stock": 0.03,  // Min 3% per stock (agent will respect)
  "max_positions": 10                     // Max 10 different stocks (agent will respect)
}
```

**Current System**: Uses Option 1 (Complete agent freedom - no limits unless explicitly set)

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
- `GET /api/portfolio/equity-history`: Historical net value curve (with timestamps)
  - **Query Parameters**:
    - `limit` (default: 60): Maximum number of records to return
    - `period` (optional): `"day"`, `"week"`, or `"month"` - returns records from last N days
    - `start_date` (optional): Start date in `YYYY-MM-DD` format
    - `end_date` (optional): End date in `YYYY-MM-DD` format
    - `start_timestamp` (optional): Start timestamp in ISO 8601 format
    - `end_timestamp` (optional): End timestamp in ISO 8601 format
  - **Example**: `GET /api/portfolio/equity-history?period=week&limit=100`
- `POST /api/portfolio/record-equity`: Record equity snapshot (called by frontend every 30 minutes)
- `POST /api/trading/execute-trade`: Execute full trading cycle
- `POST /api/system/init?force=true`: Reset portfolio to initial state (deletes all trading data, preserves memory)

### System Information
- `GET /api/system/info`: System information including:
  - LLM model configuration
  - Position limits status (auto/configured mode)
  - **Optimization components status** (enabled by default)
  - Agent freedom settings

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

### Performance Analysis
- `GET /api/performance/statistics`: Get overall performance statistics
  - **Query Parameters**:
    - `start_date` (optional): Start date in `YYYY-MM-DD` format
    - `end_date` (optional): End date in `YYYY-MM-DD` format
  - **Returns**: Total return, annualized return, win rate, max drawdown, Sharpe ratio, etc.
  - **Example**: `GET /api/performance/statistics?start_date=2025-01-01&end_date=2025-01-31`
- `GET /api/performance/trades-by-date`: Get trades grouped by date
  - **Query Parameters**:
    - `start_date` (optional): Start date in `YYYY-MM-DD` format
    - `end_date` (optional): End date in `YYYY-MM-DD` format
    - `limit` (optional): Limit number of dates to return
  - **Returns**: Daily trade summaries with buy/sell orders and realized P&L
- `GET /api/performance/symbol-analysis`: Get performance analysis by symbol
  - **Query Parameters**:
    - `symbol` (optional): Stock symbol (returns all symbols if not specified)
    - `start_date` (optional): Start date in `YYYY-MM-DD` format
    - `end_date` (optional): End date in `YYYY-MM-DD` format
  - **Returns**: Per-symbol statistics including total P&L, win rate, average holding period

---

## 🚀 Deployment

### Railway Backend Deployment

Railway provides a simple and reliable way to deploy the AI-Trader backend API to the cloud.

#### Quick Deployment Steps

1. **Connect Repository to Railway**
   - Visit [Railway Dashboard](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `WenyuChiou/ai-trader-ollama` repository
   - Railway will automatically detect Python project and deploy

2. **Configuration Files**
   - ✅ `railway.json` - Railway deployment configuration
   - ✅ `Procfile` - Process start command
   - ✅ `backend/requirements.txt` - Python dependencies

3. **Environment Variables** (Optional but Recommended)
   - `FRED_API_KEY` - For economic data (free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html))
   - `OLLAMA_BASE_URL` - If using remote Ollama instance (default: `http://localhost:11434`)
   - `PORT` - Railway auto-assigns (no need to set manually)

4. **Deployment Process**
   - Railway automatically builds and deploys on push to `main` branch
   - Check deployment logs in Railway dashboard
   - Deployment typically takes 2-5 minutes

5. **Get Public URL**
   - After deployment, Railway provides a public URL (e.g., `https://your-app.up.railway.app`)
   - Go to Project → Settings → Networking → Generate Domain
   - Copy the generated URL

6. **Update Frontend Configuration**
   - Edit `frontend/config.js`
   - Update `production` URL to your Railway backend URL:
     ```javascript
     production: 'https://your-app.up.railway.app',
     ```
   - Commit and push to GitHub

#### Railway Configuration

**`railway.json`**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**`Procfile`**:
```
web: cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
```

**Note**: Both `railway.json` and `Procfile` use `cd backend` to ensure commands run from the correct directory.

#### Verification

After deployment, verify the backend is working:

1. **API Documentation**: `https://your-app.up.railway.app/docs`
   - Should display FastAPI Swagger UI

2. **Health Check**: `https://your-app.up.railway.app/api/health`
   - Should return: `{"status": "ok"}`

3. **Frontend Connection**: 
   - Open GitHub Pages: `https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
   - Check browser console (F12) for API connection status
   - Should see successful API requests

#### Railway Free Tier

- **Free Tier**: $5/month credit (usually sufficient for small applications)
- **Auto-scaling**: Railway automatically scales based on traffic
- **Auto-restart**: Railway restarts service on failure (configured in `railway.json`)
- **Logs**: View deployment and runtime logs in Railway dashboard

#### Troubleshooting Railway Deployment

**Deployment Fails**:
- Check Railway deployment logs
- Verify `requirements.txt` includes all dependencies
- Ensure `Procfile` format is correct (`web: ...`)
- Check that `railway.json` build command points to correct path

**API Not Responding**:
- Verify service is "Active" in Railway dashboard
- Check Railway logs for errors
- Verify `PORT` environment variable is set (Railway auto-assigns)
- Test health endpoint: `https://your-app.up.railway.app/api/health`

**Frontend Cannot Connect**:
- Verify `frontend/config.js` has correct Railway URL
- Check CORS settings (backend already configured for `*`)
- Check browser console for CORS errors
- Verify Railway service is running and accessible

#### Related Documentation

- 📖 [Railway Deployment Steps](RAILWAY_DEPLOYMENT_STEPS.md) - Detailed step-by-step guide (Chinese)
- 📖 [Deployment Guide](docs/DEPLOYMENT.md) - Complete deployment documentation
- 📖 [Daily Upload Setup](docs/DAILY_UPLOAD_SETUP.md) - Setup daily data upload to Railway

### GitHub Pages Frontend Deployment

The frontend is automatically deployed to GitHub Pages when you push to the `main` branch.

**Configuration**:
- **Source**: `Deploy from a branch`
- **Branch**: `main`
- **Folder**: `/frontend`
- **URL**: `https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`

**Update Process**:
1. Make changes to frontend files
2. Commit and push to `main` branch
3. GitHub Pages automatically deploys (1-2 minutes)
4. Access updated frontend at GitHub Pages URL

**Note**: The frontend is in read-only mode on GitHub Pages for security. Full trading controls are only available when running locally.

---

## ⏰ Scheduled Tasks & Automation

### PowerShell Scripts for Automation

All automation scripts are located in `scripts/` directory and can be run from the project root.

#### Setup Scripts

| Script | Purpose | Usage | Requirements |
|--------|---------|-------|-------------|
| `setup_scheduled_tasks.ps1` | Configure automated tasks | `.\scripts\setup_scheduled_tasks.ps1` | Admin rights (optional) |
| `setup_long_term_running.ps1` | Complete long-term setup | `.\scripts\setup_long_term_running.ps1` | Admin rights |
| `setup_daily_upload_simple.ps1` | Setup daily data upload | `.\scripts\setup_daily_upload_simple.ps1` | Admin rights (optional) |

#### Scheduled Task Scripts

| Script | Purpose | Schedule | Usage |
|--------|---------|----------|-------|
| `schedule_daily_task.ps1` | Schedule daily trading cycle | Daily at market open | `.\scripts\schedule_daily_task.ps1` |
| `schedule_hourly_update.ps1` | Schedule hourly data updates | Every hour | `.\scripts\schedule_hourly_update.ps1` |
| `schedule_monitoring_task.ps1` | Schedule system monitoring | Every 30 minutes | `.\scripts\schedule_monitoring_task.ps1` |
| `schedule_daily_upload_only.ps1` | Schedule daily data upload | Daily at specified time | `.\scripts\schedule_daily_upload_only.ps1` |

#### Service Management Scripts

| Script | Purpose | Usage | Requirements |
|--------|---------|-------|-------------|
| `start_api_task_scheduler.ps1` | Start API with Task Scheduler | `.\scripts\start_api_task_scheduler.ps1` | Admin rights |
| `stop_all_services.ps1` | Stop all running services | `.\scripts\stop_all_services.ps1` | None |
| `check_running_services.ps1` | Check service status | `.\scripts\check_running_services.ps1` | None |
| `check_api_status.ps1` | Check API health | `.\scripts\check_api_status.ps1` | None |

#### Data Management Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `backup_data.ps1` | Backup system data | `.\scripts\backup_data.ps1` | Creates timestamped backups |
| `restore_portfolio.ps1` | Restore portfolio from backup | `.\scripts\restore_portfolio.ps1` | Select backup to restore |
| `restore_from_equity_history.ps1` | Restore from equity history | `.\scripts\restore_from_equity_history.ps1` | Reconstructs portfolio state |
| `cleanup_backups.ps1` | Cleanup old backup files | `.\scripts\cleanup_backups.ps1` | Removes backups >7 days old |
| `cleanup_old_memory.ps1` | Cleanup old memory files | `.\scripts\cleanup_old_memory.ps1` | Removes old memory snapshots |

#### Monitoring Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `check_long_term_health.ps1` | Check system health | `.\scripts\check_long_term_health.ps1` | Weekly health check |
| `monitor_api_connection.ps1` | Monitor API connection | `.\scripts\monitor_api_connection.ps1` | Continuous monitoring |
| `check_port.ps1` | Check port availability | `.\scripts\check_port.ps1` | Check if port 8000 is available |

**Note**: All PowerShell scripts use UTF-8 encoding and support Windows PowerShell 5.1+ and PowerShell Core 7+. Some scripts require administrator privileges (indicated in Requirements column).

### Overview

The system supports automated scheduled tasks for:
- **Auto Trading**: Run trading cycles automatically at specified times
- **Equity Recording**: Record portfolio equity every 30 minutes
- **Data Updates**: Update market data and P&L calculations hourly
- **Daily Reports**: Generate performance reports automatically

### Quick Setup

**One-Command Setup (All Tasks)**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
```

Select option `5` to set up all tasks at once, or choose individual tasks (1-4).

### Available Tasks

#### 1. Auto Trading Cycle
- **Task Name**: `AITrader-AutoTrading`
- **Schedule**: Daily at 9:30 AM (weekdays only)
- **Script**: `backend/scripts/run_daily_trading.py`
- **Purpose**: Automatically execute trading cycles during market hours

**Custom Setup**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# Select option 1, then specify:
# - Trading time (default: 09:30)
# - Weekdays only (default: Yes)
```

#### 2. Equity Recording (Every 30 Minutes)
- **Task Name**: `AITrader-EquityRecording`
- **Schedule**: Every 30 minutes
- **Purpose**: Record portfolio equity for historical tracking and charts
- **API**: Calls `POST /api/portfolio/record-equity`

**Setup**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# Select option 2
```

**Note**: This task requires the API server to be running (`http://localhost:8000`).

#### 3. Data Update (Every Hour)
- **Task Name**: `AITrader-DataUpdate`
- **Schedule**: Every hour
- **Script**: `scripts/update_real_time_pnl.py`
- **Purpose**: Update real-time P&L calculations and market data

**Setup**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# Select option 3
```

#### 4. Daily Report Generation
- **Task Name**: `AITrader-DailyReport`
- **Schedule**: Daily at 6:00 PM (weekdays only)
- **Script**: `backend/scripts/generate_daily_report.py`
- **Purpose**: Generate daily performance reports

**Custom Setup**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# Select option 4, then specify:
# - Report time (default: 18:00)
```

### Managing Scheduled Tasks

**View All Tasks**:
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like 'AITrader-*' }
```

**Test a Task**:
```powershell
Start-ScheduledTask -TaskName 'AITrader-AutoTrading'
```

**Remove a Task**:
```powershell
Unregister-ScheduledTask -TaskName 'AITrader-AutoTrading' -Confirm:$false
```

**View Task Details**:
```powershell
Get-ScheduledTask -TaskName 'AITrader-AutoTrading' | Format-List
```

### Task Requirements

**Prerequisites**:
- ✅ API server must be running (for equity recording and data updates)
- ✅ Python environment activated (tasks use system Python)
- ✅ Administrator privileges (for creating scheduled tasks)

**Task Behavior**:
- Tasks run in background (no console window)
- Tasks survive system reboots
- Tasks can run even when user is logged off (if configured)
- Failed tasks are logged in Windows Event Viewer

### Troubleshooting

**Task Not Running**:
1. Check if task exists: `Get-ScheduledTask -TaskName 'AITrader-*'`
2. Check task status: `Get-ScheduledTaskInfo -TaskName 'AITrader-AutoTrading'`
3. Check Windows Event Viewer for errors
4. Verify API server is running (for API-dependent tasks)

**Task Running But No Data**:
1. Check API server logs
2. Verify Python scripts exist and are executable
3. Check file permissions for data/logs directory

**Modify Task Schedule**:
1. Open Task Scheduler (`taskschd.msc`)
2. Find task under "Task Scheduler Library"
3. Right-click → Properties → Triggers tab
4. Edit trigger settings

---

## 🔔 API Connection Monitor

### Overview

The system includes an automatic connection monitor that detects API server disconnections and notifies you with Windows Toast notifications.

### Features

- **Automatic Monitoring**: Checks API server status every 30 seconds
- **Disconnection Detection**: Alerts after 3 consecutive failures
- **Windows Toast Notifications**: Sends system notifications when API goes offline
- **Auto-Restart Option**: Prompts to restart API server automatically
- **Recovery Detection**: Notifies when API server comes back online

### Quick Setup (Recommended)

**One-Command Setup**:
```powershell
.\scripts\setup_api_monitor.ps1
```

This interactive script provides options to:
1. Start monitoring now (in current window)
2. Start monitoring in background window
3. Setup as scheduled task (auto-start on login)
4. Setup as scheduled task + start now
5. Test monitor first

### Manual Start

**Start Monitoring**:
```powershell
.\scripts\monitor_api_connection.ps1
```

**Run in Background**:
```powershell
Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File scripts\monitor_api_connection.ps1'
```

### Configuration

The monitor script accepts optional parameters:

```powershell
# Custom check interval (default: 30 seconds)
.\scripts\monitor_api_connection.ps1 -CheckInterval 60

# Custom retry count (default: 3 failures)
.\scripts\monitor_api_connection.ps1 -RetryCount 5

# Custom API URL
.\scripts\monitor_api_connection.ps1 -ApiUrl "http://localhost:8000/api/health"
```

### Notification Methods

**Option 1: BurntToast Module (Recommended)**
```powershell
# Install BurntToast module for better notifications
Install-Module -Name BurntToast -Scope CurrentUser
```

**Option 2: System Sound (Fallback)**
- Uses Windows system sounds if BurntToast is not available
- Shows console messages as alternative notification

### Testing

**Test the Monitor**:
```powershell
.\scripts\test_monitor_api.ps1
```

This will test:
- ✅ API connection check
- ✅ Notification system
- ✅ Restart function
- ✅ Port detection

### Behavior

1. **Normal Operation**: Shows status every 30 seconds (can be suppressed)
2. **Disconnection Detected**: After 3 consecutive failures:
   - Sends Windows Toast notification
   - Shows console alert
   - Prompts user to restart API server
3. **User Choice**:
   - **Yes**: Automatically restarts API server in new window
   - **No**: Continues monitoring, user can restart manually
4. **Recovery**: When API comes back online, sends recovery notification

### Manual Restart

If auto-restart fails, you can manually restart:

```powershell
# Option 1: Use setup script
.\scripts\setup_step3_start_services.ps1

# Option 2: Direct start (with virtual environment)
# Method A: Using & operator (PowerShell standard)
& .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Method B: Using dot sourcing (alternative)
. .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Direct start (if venv already activated)
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Note**: The monitor script uses `& "$activateScript"` (Method A) when auto-restarting. Both methods work, but `&` is the PowerShell standard for executing scripts.

### Scheduled Task Integration

You can set up the monitor as a scheduled task for continuous monitoring:

```powershell
# Create scheduled task (runs on system startup)
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ProjectRoot\scripts\monitor_api_connection.ps1`""
$Trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "AITrader-ConnectionMonitor" -Action $Action -Trigger $Trigger -Description "Monitor AI Trader API connection"
```

---

## 🚀 Running the System

### Starting the API Server

**Option A: Task Scheduler (Recommended for long-term running)**
```powershell
# Right-click and run as administrator:
scripts\start_api_task_admin.bat

# Or manually:
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
```
- ✅ Runs in background
- ✅ Auto-starts on Windows login
- ✅ Continues running even if CMD is closed
- ✅ Auto-restarts on failure

**Option B: Windows Service (Requires NSSM)**
```powershell
# Right-click and run as administrator:
scripts\start_api_service_admin.bat
```

**Option C: Development Mode (Requires window open)**

**With Virtual Environment** (Recommended):

**Method A: Using & operator** (PowerShell standard, same as monitor script):
```powershell
# Activate virtual environment first
& .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Method B: Using dot sourcing** (alternative):
```powershell
# Activate virtual environment first
. .\.venv\Scripts\Activate.ps1

# Navigate to backend directory
cd backend

# Start API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Direct Command** (if virtual environment is already activated):
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Command Parameters**:
- `--host 0.0.0.0`: Listen on all network interfaces (accessible from other devices)
- `--port 8000`: Use port 8000
- `--reload`: Enable auto-reload on code changes (development mode)

**Notes**: 
- Keep the terminal window open. Closing it will stop the API server.
- Both activation methods (Method A and B) work. Method A (`&`) is the PowerShell standard and matches what the monitor script uses for auto-restart.

### Stopping the API Server

**Stop Task Scheduler Service**:
```powershell
Stop-ScheduledTask -TaskName AITraderAPI
```

**Stop All Services**:
```powershell
# Run from project root:
.\scripts\stop_all_services.ps1
```

### Managing Services

**Check API Status**:
```powershell
.\scripts\check_api_status.ps1
```

**Check Running Services**:
```powershell
.\scripts\check_running_services.ps1
```

**Check Port Usage**:
```powershell
.\scripts\check_port.ps1
```

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

**Related Documentation**: See [`docs/FRONTEND_EQUITY_DISPLAY.md`](docs/FRONTEND_EQUITY_DISPLAY.md) for frontend display fixes

### News Display & Analysis Target Updates

**Recent Updates**:

1. **News Display Enhancement**:
   - ✅ Frontend now displays news with summaries, sources, and timestamps
   - ✅ News sorted by recency (latest first)
   - ✅ Supports multiple news data formats (hits, articles, items, array-like objects)
   - ✅ Displays LLM-generated summaries and keywords when available

2. **Technical Analysis Targets**:
   - ✅ **With Holdings**: Analyzes current holdings + recommended stocks + major indices (all required)
   - ✅ **Without Holdings**: Analyzes recommended stocks + major indices (both required)
   - ✅ All targets must be analyzed simultaneously

3. **Fundamental Analysis Targets**:
   - ✅ **With Holdings**: Analyzes non-ETF holdings + non-ETF recommended stocks
   - ✅ **Without Holdings**: Analyzes non-ETF recommended stocks only
   - ✅ ETFs and indices are excluded (ETFs don't need fundamental analysis)
   - ✅ ETF detection using `is_etf()` function (checks quoteType/instrumentType)

4. **Tool Usage & Filtering**:
   - ✅ **Tool Name Mapping**: 
     - `get_news` → `plan_and_scan_news` (automatic mapping)
     - `get_news_scan` → `plan_and_scan_news` (automatic mapping)
     - `news_scan` → `plan_and_scan_news` (deprecated, automatic conversion with warning)
   - ✅ **Tool Filtering by Analyst**:
     - Technical Analyst: News tools automatically filtered out (news handled by Sentiment Analyst)
     - Sentiment Analyst: Deprecated `news_scan` converted to `plan_and_scan_news`
     - Fundamental Analyst: Invalid tool calls (missing name) filtered out
   - ✅ **Tool Validation**: All tool calls validated before execution (must have valid `name` field)
   - ✅ **Removed**: `news_scan` tool registration (use `plan_and_scan_news` instead)
   - ✅ Enhanced debugging logs for news tool execution
5. **Fundamental Analysis Budget**:
   - ✅ Fundamental analysis tools (`get_company_fundamentals`) execute without tool budget restrictions
   - ✅ Ensures all recommended stocks and holdings are analyzed regardless of budget
   - ✅ Tools prioritized: Fundamental tools execute first, then other tools (subject to budget)
6. **FGI (Fear & Greed Index)**:
   - ✅ Standardized classification: 0-25 (EXTREME FEAR), 26-45 (FEAR), 46-55 (NEUTRAL), 56-75 (GREED), 76-100 (EXTREME GREED)
   - ✅ Data source priority: `feargreedmeter.com` (returns correct value 11)
7. **Signal Score**:
   - ✅ Removed automatic `signal_score` sorting and filtering
   - ✅ Agents now determine signal scores independently
8. **Agent Discussion Logic**:
   - ✅ Tool filtering and validation applied before execution
   - ✅ Invalid tool calls automatically filtered out
   - ✅ Tool restrictions enforced per analyst type
   - ✅ Mandatory tools automatically added (e.g., `plan_and_scan_news` for Sentiment Analyst)

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

**Related Documentation**: See [`docs/RECORD_CONSISTENCY.md`](docs/RECORD_CONSISTENCY.md) for portfolio P&L calculation consistency rules

### API Endpoint Errors

**Error**: `405 Method Not Allowed` or `500 Internal Server Error`

**Common Issues**:
- ✅ **Fixed**: Added `POST` method support to `/api/trading/check-pending-orders`
- ✅ **Fixed**: VIX and Fear & Greed endpoints now return default values instead of 500 errors when data fetch fails

**Related Documentation**: See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) for API endpoint troubleshooting

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

### Long-Term Running (Weeks/Months)

**For running the system continuously for weeks or months**, see the detailed guide:

📖 **Complete Guide**: [`docs/LONG_TERM_RUNNING_GUIDE.md`](docs/LONG_TERM_RUNNING_GUIDE.md)

**Quick Setup** (Recommended for long-term running):

1. **Use Task Scheduler** (easiest, no additional software):
   ```powershell
   # Right-click and run as administrator:
   scripts\start_api_task_admin.bat
   ```

2. **Features**:
   - ✅ Auto-start on system boot
   - ✅ Auto-restart on crash
   - ✅ Background running (close CMD and keep running)
   - ✅ Logging to `logs\api_task.log`

3. **Management**:
   ```powershell
   # Start
   Start-ScheduledTask -TaskName AITraderAPI
   
   # Stop
   Stop-ScheduledTask -TaskName AITraderAPI
   
   # Restart
   Stop-ScheduledTask -TaskName AITraderAPI
   Start-ScheduledTask -TaskName AITraderAPI
   
   # Check status
   Get-ScheduledTaskInfo -TaskName AITraderAPI
   
   # View logs
   Get-Content logs\api_task.log -Tail 50
   ```

**This setup will keep the API running continuously, even after system restarts, for weeks or months.**

### Complete Long-Term Running Setup

**For running the system for several weeks**, use the automated setup script:

```powershell
# Run as administrator:
powershell -ExecutionPolicy Bypass -File .\scripts\setup_long_term_running.ps1
```

**This script will:**
- ✅ Setup API Server (Task Scheduler)
- ✅ Setup Daily Upload (once per day, saves budget)
- ✅ Setup Weekly Maintenance (automatic cleanup every Sunday at 2 AM)
- ✅ Create maintenance scripts for automatic file cleanup

**Maintenance Features:**
- **Automatic Cleanup**: Old backup files (>7 days) and log files (>30 days) are automatically removed
- **Disk Space Monitoring**: Weekly check of data directory size
- **Memory Management**: Old memory files are cleaned up automatically
- **Log Rotation**: Prevents log files from growing too large

**Manual Maintenance**:
```powershell
# Clean up repository (remove old backups, logs, __pycache__)
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_repo.ps1

# Check system health
powershell -ExecutionPolicy Bypass -File .\scripts\check_system_features.py

# Check disk space
$dataSize = (Get-ChildItem -Path "data\logs" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Data directory size: $([math]::Round($dataSize, 2)) GB"
```

**Important Notes for Long-Term Running:**
- ✅ **Protection Mechanisms**: System prevents overselling (selling more than holdings) and overbuying (buying more than available cash)
- ✅ **Auto-Restart**: System automatically restarts on crash
- ✅ **Log Rotation**: Logs are automatically cleaned up to prevent disk space issues
- ✅ **Data Backup**: Daily upload to Railway ensures data is backed up remotely
- ✅ **Memory Management**: Automatic garbage collection and conversation history limiting
- ✅ **File Optimization**: API only reads last 80-100KB of large files for better performance
- ⚠️ **Monitor Weekly**: Check logs and disk space weekly (use `check_long_term_health.ps1`)
- ⚠️ **Monthly Restart**: Recommended to restart API server monthly for optimal performance

**Health Check**:
```powershell
# Check system health (recommended weekly):
powershell -ExecutionPolicy Bypass -File .\scripts\check_long_term_health.ps1
```

**Related Documentation**:
- 📖 [Long-Term Running Checklist](docs/LONG_TERM_RUNNING_CHECKLIST.md) - Complete checklist for long-term running
- 📖 [Long-Term Optimization Guide](docs/LONG_TERM_OPTIMIZATION.md) - Optimization recommendations

---

## 📖 Documentation

### Core Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Installation and first run
- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration reference
- **[API Reference](docs/API_REFERENCE.md)** - All API endpoints and usage
- **[Architecture Documentation](docs/ARCHITECTURE.md)** - System architecture overview
- **[Testing Guide](docs/TESTING.md)** - Running and writing tests
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Additional Documentation

| File | Description |
|------|-------------|
| `docs/AGENTS.md` | Complete agent architecture |
| `docs/TOOLS.md` | Detailed documentation for all 29 tools (23 market + 6 memory) |
| `docs/DATA_STORAGE_GUIDE.md` | Data storage locations and formats |
| `docs/LONG_TERM_RUNNING_GUIDE.md` | Long-term operation guide |

## 🧪 Testing

### Test Suite Overview

**All test files are located in the `tests/` directory** (not `test/`). The old `test/` directory has been removed and replaced with a properly structured test suite.

### Test Directory Structure (Main Branch)

```
tests/
├── integration/             # Integration tests for system components
│   ├── test_agent_architecture.py  # Agent system tests
│   ├── test_portfolio.py            # Portfolio management tests
│   ├── test_memory.py               # Memory system tests
│   └── test_api.py                  # API endpoint tests
├── e2e/                     # End-to-end tests
│   └── test_frontend.py             # Frontend integration tests
├── utils/                   # Test utilities and helpers
│   └── test_helpers.py
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest settings
└── README.md                # Test documentation
```

**Note**: `tests/unit/` directory (optimization component tests) only exists in `feature/system-optimization` branch.

### Running Tests

**Prerequisites**:
- Python 3.10+ installed
- Virtual environment activated
- Dependencies installed (`pip install -r backend/requirements.txt`)

**Run All Tests**:
```powershell
# From project root
pytest tests/ -v

# Or with more details
pytest tests/ -v --tb=short
```

**Run Specific Test Categories**:
```powershell
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# End-to-end tests only
pytest tests/e2e/ -v

# Specific test file
pytest tests/integration/test_portfolio.py -v
```

**Run with Coverage** (if pytest-cov installed):
```powershell
pytest tests/ --cov=backend/src --cov-report=html --cov-report=term-missing
```

### Test Status (Main Branch)

✅ **Current Status**: **~28 tests passing** (100% pass rate)

**Test Breakdown**:
- **Integration Tests**: ~24 tests passing
  - Agent Architecture: 6 tests ✅
  - Portfolio Management: 7 tests ✅
  - Memory System: 5 tests ✅
  - API Endpoints: 5 tests ✅
- **E2E Tests**: 4/4 passing
  - Frontend Integration: 4 tests ✅

**Note**: Unit tests for optimization components (~18 tests) are only in `feature/system-optimization` branch.

### Test Documentation

For detailed test documentation, see:
- **[Test README](tests/README.md)** - Test suite overview and guidelines (English)
- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation
- **[Test Scripts Guide](docs/TEST_SCRIPTS_GUIDE.md)** - Guide for independent test scripts (English)
- **[Test Results](docs/TEST_RESULTS.md)** - Latest test execution results

### Important Notes

1. **Test Location**: All tests are in `tests/` directory (not `test/`)
2. **Old Test Files**: The old `test/` directory has been removed
3. **Test Structure**: Tests are organized by type (unit/integration/e2e)
4. **Test Infrastructure**: Uses pytest with proper fixtures and configuration
5. **Test Coverage**: Structure complete, requires Ollama for full execution tests

---

## 🎯 Quick Reference

### Setup Scripts (PowerShell)

All setup scripts are located in `scripts/` directory and can be run from the project root.

| Script | Purpose | Usage | Requirements |
|--------|---------|-------|-------------|
| `setup_step1_install_dependencies.ps1` | Install Python dependencies and Ollama | `.\scripts\setup_step1_install_dependencies.ps1` | Python 3.10+, Ollama |
| `setup_step2_configure.ps1` | Configure system and initialize data | `.\scripts\setup_step2_configure.ps1` | Step 1 completed |
| `setup_step3_start_services.ps1` | Start API server | `.\scripts\setup_step3_start_services.ps1` | Steps 1-2 completed |
| `setup_all_steps.ps1` | Run all setup steps sequentially | `.\scripts\setup_all_steps.ps1` | Python 3.10+, Ollama |
| `setup_scheduled_tasks.ps1` | Setup automated tasks | `.\scripts\setup_scheduled_tasks.ps1` | Admin rights (optional) |

**Note**: All PowerShell scripts use UTF-8 encoding and support Windows PowerShell 5.1+ and PowerShell Core 7+.

### Management Scripts

| Script | Purpose | Usage | Requirements |
|--------|---------|-------|-------------|
| `start_api_task_admin.bat` | Setup Task Scheduler (long-term) | Right-click → Run as administrator | Admin rights |
| `start_api_service_admin.bat` | Setup Windows Service (requires NSSM) | Right-click → Run as administrator | Admin rights, NSSM |
| `stop_all_services.ps1` | Stop all running services | `.\scripts\stop_all_services.ps1` | None |
| `check_running_services.ps1` | Check service status | `.\scripts\check_running_services.ps1` | None |
| `check_api_status.ps1` | Check API health | `.\scripts\check_api_status.ps1` | None |

### Test Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `test_news_tools.py` | Test news tools independently | `python scripts/test_news_tools.py` | Does not overwrite trading records |
| `verify_portfolio.py` | Verify portfolio consistency | `python scripts/verify_portfolio.py` | Read-only, safe to run |
| `test_api_server.py` | Test API endpoints | `python scripts/test_api_server.py` | Requires API running |
| `test_frontend_features.py` | Test frontend features | `python scripts/test_frontend_features.py` | Requires API running |

**Important**: Use independent test scripts (`test_news_tools.py`, `verify_portfolio.py`) for testing. Do NOT use `run_daily_trading.py` for testing as it will overwrite trading records.

See [Test Scripts Guide](docs/TEST_SCRIPTS_GUIDE.md) for detailed information.

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `config.json` | Main trading configuration | `backend/config/config.json` |
| `agents.yaml` | Agent-specific settings | `backend/config/agents.yaml` |
| Prompt files | Agent prompts | `prompts/*.yml` |

### Data Files

| File | Purpose | Location |
|------|---------|----------|
| `portfolio_state.json` | Current portfolio state | `data/logs/portfolio_state.json` |
| `discussion_actions.jsonl` | Agent conversations | `data/logs/discussion_actions.jsonl` |
| `equity_history.jsonl` | Net value history | `data/logs/equity_history.jsonl` |
| `filled_orders.jsonl` | Completed orders | `data/logs/filled_orders.jsonl` |

---

## 📄 License

MIT License - see `LICENSE` file for details

---

**Built with ❤️ by the AI-Trader Team**

*Empowering traders with AI-driven insights and autonomous decision-making*
