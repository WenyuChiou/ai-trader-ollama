# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 🏗️ Project Structure

```
ai-trader-ollama/
├── backend/                 # Python backend (main code)
│   ├── src/
│   │   ├── agents/         # All trading agents
│   │   ├── data/           # Portfolio, Trade Logger, Market Data, Memory Manager
│   │   ├── tools/          # All available tools
│   │   ├── orchestrator/   # Main trading loop
│   │   └── llm/            # Ollama LLM client
│   ├── config/            # Configuration files
│   ├── tests/             # Test suite
│   ├── scripts/           # Utility scripts (including daily trading)
│   └── prompts/           # Agent prompt templates
└── docs/                  # Documentation
```

---

## 🚀 Quick Start

```bash
cd backend
pip install -r requirements.txt
ollama serve
ollama pull llama3.1

# Edit config/config.json for your universe and dates
python run.py
```

---

## 🔄 Daily Automatic Trading

### ⏰ Time Flow Explanation

**System Work Mode**: **Analyze yesterday's data today, execute immediately after today's market open**

```
Timeline Example:
  Day N-1 (2025-01-27)          Day N (2025-01-28)
  Close 16:00 EST        →      Before Open 09:00 EST  →  After Open 09:30 EST
                                  │                      │
                                  ├─ Run Script          └─ Execute Orders Immediately
                                  ├─ Analyze: 1/27 Closing Price
                                  └─ Generate Trade Orders (using yesterday's closing price)

Detailed Process:
1. Run Time: Today morning 09:00 (before US market open)
2. Analyze Data: Yesterday's closing price (e.g., 1/27 closing price)
3. Decision Generation: Based on yesterday's closing price analysis, generate buy/sell orders
4. Order Execution: Execute immediately after today's market open (using yesterday's closing price as execution price)
5. Portfolio Update: Update holdings and cash after trades complete
6. Memory Save: Save complete decision process to memory files
```

**Why Use Yesterday's Closing Price?**
- ✅ **Data Completeness**: Closing price is definitive and complete data
- ✅ **Suitable for Technical Analysis**: Daily closing price is suitable for calculating MA, RSI, MACD and other technical indicators
- ✅ **Avoid Delays**: No dependency on real-time API, uses free yfinance
- ✅ **Immediate Execution**: Execute immediately after market open, no need to wait until close

**Order Execution Price**:
- **Base Price**: Uses **yesterday's closing price** as base
- **Price Range Strategy** (low buy, high sell):
  - **Buy**: Price range `[98% of current price, current price]`, execution uses **lowest price** (low buy)
  - **Sell**: Price range `[100.5% of current price, 102% of current price]`, execution uses **highest price** (high sell)
- This is simulated trading, price range provides buffer, actual market opening price within range can execute

---

### Current Run Method

Currently requires **manual execution**:
```bash
cd backend
python run.py
```

### Automatic Run Setup

The system provides **daily automatic run script** that can be scheduled to run daily:

#### Windows Setup

1. **Use PowerShell Script (Recommended)**:
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File scripts\schedule_daily_task.ps1
```

2. **Or Use Task Scheduler**:
   - Open Task Scheduler
   - Create basic task
   - Set to run daily at **09:00** (before market open)
   - Program: `python`
   - Arguments: `backend\scripts\run_daily_trading.py`
   - Start in: `backend` directory

#### Linux/Mac Setup

```bash
cd backend
bash scripts/schedule_daily_task.sh
```

Or manually add crontab:
```bash
crontab -e
# Add: 0 9 * * 1-5 cd /path/to/backend && python scripts/run_daily_trading.py
# Description: Run every weekday morning at 9:00 (before US market open)
```

### Daily Run Script Features

✅ **Automatic Trading Day Detection**: Skips weekends  
✅ **Portfolio State Management**: Automatically loads and saves position state  
✅ **Memory Save**: Automatically saves daily decision memories (includes historical memory injection)  
✅ **Logging**: All trades logged to `trades.jsonl`  
✅ **Error Handling**: Saves current state even if run fails  
✅ **Historical Memory Integration**: Automatically loads last 5 days of historical decisions as reference

Detailed setup instructions: See `backend/scripts/setup_daily_scheduler.md`

### Manual Run Examples

```bash
cd backend

# Run today's trading (using yesterday's data)
python scripts/run_daily_trading.py

# Run trading for specific date
python scripts/run_daily_trading.py --date 2025-01-28

# Force run (run even on weekends, for testing)
python scripts/run_daily_trading.py --force
```

---

## 🧠 Agent Types & Framework Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Complete Daily Trading Framework               │
│                                                             │
│  Market Data → Analysis → Discussion → Risk → Trade         │
│                                                             │
│  Input: Stock Universe, Date Range                         │
│  Output: Trading Decisions, Portfolio Status, Trade Logs    │
└─────────────────────────────────────────────────────────────┘
```

### Agent Types (6 Core Agents)

| Agent Type | When Called | Purpose | Input | Output | LLM Model |
|-----------|------------|---------|-------|--------|-----------|
| **Market Agent** | **Step 1** - Immediately at cycle start | Fetch OHLCV + Technical Indicators | `symbols[]`, `start`, `end` | `market_view` (stocks data with TA) | llama3.1 |
| **Market Analyst** | **Step 1c** - Right after market data collection | Analyze trends, generate recommendations | `market_view` | `market_analysis` (sentiment, recommended stocks) | llama3.1 |
| **Discussion Agent** | **Step 2** - After Market Analyst, with historical memories | Multi-round analysis with tool calls | `enriched_market`, `historical_memories` | `consensus` (stance, reasoning, tool results) | llama3.1 |
| **Risk Analyst** | **Step 3** - After Discussion Agent, when positions exist | Assess portfolio risk and position limits | `market_view`, `positions`, `portfolio_value` | `risk_report` (risk level, position control) | llama3.1 |
| **Trader Agent** | **Step 4** - After Risk Analyst, to make final decisions | Generate buy/sell orders | `market_view`, `consensus`, `risk_report` | `decision` (buy_orders, sell_orders) | llama3.1 |
| **Execution** | **Step 5** - Immediately after Trader Agent decisions | Execute trades, update portfolio | `decision` | `executed_trades`, `portfolio` status | No LLM |

### Agent Call Timing & Sequence

**Execution Flow**:
```
Daily Trading Cycle Starts (09:00)
  ↓
[Step 1] Market Agent (fetch_market_batch)
  ├─ Trigger: Cycle start
  ├─ Purpose: Collect OHLCV + technical indicators
  └─ Output: market_view
  ↓
[Step 1c] Market Analyst (run_market_analyst)
  ├─ Trigger: Immediately after market data collection
  ├─ Purpose: Analyze trends, generate stock recommendations
  ├─ Input: market_view
  └─ Output: market_analysis (recommended_stocks, sentiment)
  ↓
[Step 1.5] Load Historical Memories ⚡ MEMORY USAGE #1
  ├─ When: After Market Analyst, before Discussion Agent
  ├─ Action: Load last 5 days of memory summaries
  ├─ Format: summary_only=True (only key info)
  └─ Inject: Pass as historical_memories to Discussion Agent
  ↓
[Step 2] Discussion Agent (run_analyst_discussion)
  ├─ Trigger: After Market Analyst completes
  ├─ Purpose: Multi-round analysis with automatic tool calling
  ├─ Input: enriched_market, historical_memories
  ├─ Auto-tools: news_scan, vix_term, fear_greed (if info insufficient)
  └─ Output: consensus (final_stance, reasoning)
  ↓
[Step 3] Risk Analyst (run_risk_analyst)
  ├─ Trigger: After Discussion Agent, if positions exist
  ├─ Purpose: Assess portfolio risk, position limits
  ├─ Input: market_view, current_positions, portfolio_value
  └─ Output: risk_report (risk_level, position_control_report)
  ↓
[Step 4] Trader Agent (run_trader)
  ├─ Trigger: After Risk Analyst completes
  ├─ Purpose: Generate final buy/sell orders with position sizing
  ├─ Input: market_view, consensus, risk_report, position_config
  └─ Output: decision (buy_orders, sell_orders with price ranges)
  ↓
[Step 5] Execution
  ├─ Trigger: Immediately after Trader Agent decisions
  ├─ Purpose: Execute trades, update portfolio
  ├─ Fill Check: Verify prices are within order ranges
  └─ Output: executed_trades, updated portfolio
  ↓
[Step 7] Memory Save ⚡ MEMORY USAGE #2
  ├─ When: After execution completes
  ├─ Action: Save complete daily memory to memory/daily/YYYY-MM-DD.json
  ├─ Includes: Full cycle data (market, analysis, discussion, decisions, portfolio)
  └─ Compress: Old memories (>30 days) to memory/weekly/ (auto)
```

**Key Timing Points**:
- **Market Agent**: Called **first** - no dependencies
- **Market Analyst**: Called **immediately after** market data is ready
- **Discussion Agent**: Called **after** Market Analyst, with **historical memories** loaded
- **Risk Analyst**: Called **only if** portfolio has positions (can be skipped on first day)
- **Trader Agent**: Called **after** all analysis complete, makes final decisions
- **Execution**: Called **immediately** after Trader Agent, executes orders with fill checks

---

## 🔄 Complete Daily Workflow

### Step 1: Market Data Collection 📊

**Agent**: Market Agent (via `fetch_market_batch` tool)

**Time Point**: Today morning 09:00 (before market open)

**Input**:
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"],  # From config.json "universe"
  "start": "2024-01-01",  # YYYY-MM-DD (historical data start)
  "end": "2025-01-27"     # YYYY-MM-DD (yesterday, to get yesterday's closing price)
}
```

**Process**:
1. Fetches OHLCV data via yfinance (uses **yesterday's closing price**)
2. Computes technical indicators (RSI14, MACD, Bollinger Bands, MA20/50)
3. Calculates `signal_score` (0-10 composite score)
4. Fetches VIX data (volatility index)
5. Supports stocks, bonds (^TNX, ^IRX, ^FVX), crypto (BTC-USD, ETH-USD)

**Note**: Using yesterday's closing price because:
- Closing price is complete and definitive data
- Suitable for technical analysis calculations
- No dependency on real-time API (free)

**Output**: `market_view`
```python
{
  "stocks": {
    "NVDA": {
      "price": 150.25,           # Latest close price
      "change_pct": 2.5,         # Daily change %
      "rsi14": 65.0,            # RSI (0-100)
      "macd": 2.5,               # MACD value
      "macd_signal": 2.0,        # MACD signal line
      "macd_hist": 0.5,          # MACD histogram
      "bb_upper": 155.0,         # Bollinger upper band
      "bb_middle": 150.0,        # Bollinger middle
      "bb_lower": 145.0,         # Bollinger lower band
      "bb_pos": 0.5,             # Position in BB (0=lower, 1=upper)
      "ma20": 148.0,             # 20-day moving average
      "ma50": 145.0,             # 50-day moving average
      "signal_score": 4.5        # Composite score (0-10)
    },
    # ... more stocks from universe
  },
  "vix": {
    "level": 18.5,               # VIX current level
    "chg_1d": -1.2,              # VIX 1-day change
    "zscore": 0.8                # VIX z-score
  },
  "crypto": {                    # If crypto in symbols
    "BTC-USD": { ... }
  }
}
```

---

### Step 2: Market Analysis 📈

**Agent**: Market Analyst (LLM-based analysis)

**When Called**: Immediately after Step 1 (market data collection)

**Input**: `market_view` (from Step 1)

**Process**:
1. LLM analyzes all stocks in universe
2. Assesses trends (uptrend/downtrend/sideways)
3. Evaluates VIX regime (low/normal/elevated/spike)
4. Generates buy recommendations based on:
   - Technical trend analysis
   - VIX risk level (threshold: 7.0)
   - Signal score (threshold: 3.0)

**Output**: `market_analysis`
```python
{
  "market_sentiment": "bullish" | "neutral" | "cautious" | "bearish",
  "recommended_stocks": ["NVDA", "MSFT", "AAPL"],  # Top buy candidates
  "key_observations": [
    "NVDA: uptrend",
    "MSFT: uptrend",
    "AAPL: sideways"
  ],
  "concerns": [
    "VIX elevated (level=18.5, z=0.8)"
  ],
  "vix": {
    "regime": "normal" | "elevated" | "spike",
    "risk_score": 7.5
  }
}
```

---

### Step 3: Discussion Agent 🤖

**Agent**: Discussion Agent (Multi-round with feedback loop)

**When Called**: After Market Analyst completes, with historical memories loaded (last 5 days)

**Input**: `enriched_market`
```python
{
  "symbols": ["NVDA", "MSFT", ...],
  "stocks": { ... },              # From market_view
  "vix": { ... },                 # From market_view
  "recommended_stocks": ["NVDA", "MSFT"],  # From market_analysis
  "market_sentiment": "bullish",   # From market_analysis
  "signal_score_top": [("NVDA", 4.5), ("MSFT", 4.2)]
}
```

**Process**: Multi-round discussion
- **Round 1**: Analyzes market → Calls tools if needed → Gets results
- **Round 2**: Sees `[TOOLS CONTEXT]` → Reflects → Calls new tools if needed
- **Round N**: Has full context → Forms final stance

**Tool Calling**: Automatically calls tools when information is insufficient
- Available tools: `news_scan`, `vix_term`, `fear_greed`, `fetch_jin10_news`, etc.
- Tool results injected into next round as `[TOOLS CONTEXT]`
- Tool budget: 2 (configurable)

**Output**: `consensus`
```python
{
  "final_stance": "bullish" | "neutral" | "cautious" | "bearish",
  "rounds": 3,                    # Number of discussion rounds
  "transcript": [                 # Round-by-round discussion
    "Round 1: Analyzed market data... Called news_scan for NVDA...",
    "Round 2: Received news results... Called fear_greed...",
    "Round 3: Final stance: bullish..."
  ],
  "actions": [
    {"type": "consider_probe", "why": "Need more sentiment data"},
    {"type": "finalize", "why": "Have sufficient information"}
  ],
  "tool_context": [               # Summarized tool results
    "news_scan: 15 hits for NVDA, positive sentiment",
    "fear_greed: 65 (Greed), market sentiment positive",
    "vix_term: VIX=18.5, VIX3M=20.0, ratio=1.08 (contango)"
  ],
  "risk_signals": ["high_volatility"]
}
```

---

### Step 4: Risk Analysis ⚠️

**Agent**: Risk Analyst

**When Called**: After Discussion Agent completes, only if portfolio has existing positions (can be skipped on first trading day)

**Input**:
```python
{
  "market_json": market_view,           # Market data
  "current_positions": {                 # Current holdings
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.00,
      "current_price": 150.25,
      "market_value": 1502.50
    }
  },
  "portfolio_value": 10000.0,           # Total portfolio value
  "discussion_risk_signals": {          # From Discussion Agent
    "risk_level": "medium",
    "risk_signals": ["high_volatility"]
  }
}
```

**Process**:
1. Assesses market risk (VIX level, volatility)
2. Calculates position concentration (HHI index)
3. Evaluates single stock exposure vs limits
4. Generates position control recommendations

**Output**: `risk_report`
```python
{
  "overall_risk_level": "high" | "medium" | "low",
  "risk_score": 6.5,                    # 0-10 scale
  "current_position_risk": {
    "position_concentration": 0.45,     # HHI concentration (0-1)
    "single_stock_exposure": {
      "NVDA": 0.15                       # 15% exposure
    },
    "overall_exposure": 0.75,            # 75% of capital deployed
    "max_single_position": 0.20          # 20% recommended limit
  },
  "position_control_report": {
    "recommended_max_position_size": 0.15,    # 15% per stock
    "recommended_total_exposure": 0.85,       # 85% total
    "cash_reserve_min": 0.15,                 # Keep 15% cash
    "recommended_position_sizes": {
      "NVDA": {
        "max_pct": 0.15,
        "min_pct": 0.03
      }
    }
  },
  "risk_warnings": [
    "High concentration in technology stocks"
  ]
}
```

---

### Step 5: Trading Decision 💰

**Agent**: Trader Agent

**When Called**: After Risk Analyst completes (or after Discussion Agent if no positions exist)

**Input**:
```python
{
  "market": market_view,                # Market data
  "mview": enriched_market,             # Enriched market + analysis
  "rview": risk_report,                 # Risk assessment
  "convo": consensus,                   # Discussion consensus
  "last_prices": {"NVDA": 150.25, ...}, # Latest prices
  "current_positions": { ... },         # Current holdings
  "portfolio_value": 10000.0,           # Portfolio value
  "position_config": {                   # Position limits (from config.json)
    "max_position_per_stock": 0.15,     # 15% max per stock
    "max_total_position": 0.85,         # 85% total
    "min_position_per_stock": 0.03      # 3% min per stock
  }
}
```

**Process**:
1. Evaluates all recommended stocks from Market Analyst
2. Considers VIX risk level (threshold: 7.5 for cautious)
3. Applies risk report position limits
4. Calculates position sizes dynamically:
   - If many recommended stocks → smaller positions per stock (more diversified)
   - If few recommended stocks → larger positions per stock
   - Respects max/min limits from config
5. Generates buy/sell orders with prices and quantities

**Output**: `decision`
```python
{
  "action": "BUY" | "SELL" | "HOLD",
  "stance": "bullish",                   # Market stance
  "vix_risk": 7.5,                      # VIX-based risk score
  "rationale": "Strong technical signals on NVDA and MSFT. Market sentiment bullish.",
  "buy_orders": [
    {
      "symbol": "NVDA",
      "quantity": 10,                    # Calculated based on position limits
      "buy_price": 150.25,              # Base price (for calculation)
      "buy_price_min": 147.25,          # Min buy price (range lower bound, 2% below current)
      "buy_price_max": 150.25,          # Max buy price (range upper bound, not exceeding current price)
      "total_cost": 1502.50,            # quantity * buy_price (base calculation)
      "position_pct": 0.12,              # 12% of portfolio
      "reason": "Strong RSI=65, positive MACD, signal_score=4.5"
    },
    {
      "symbol": "MSFT",
      "quantity": 15,
      "buy_price": 420.00,
      "buy_price_min": 411.60,          # Low buy: 2% below current price
      "buy_price_max": 420.00,
      "total_cost": 6300.00,
      "position_pct": 0.50,
      "reason": "Uptrend confirmed, moderate volatility"
    }
  ],
  "sell_orders": [
    {
      "symbol": "AAPL",
      "quantity": 5,
      "sell_price": 175.00,             # Base price (for calculation)
      "sell_price_min": 175.88,         # Min sell price (range lower bound, 0.5% above current)
      "sell_price_max": 178.50,         # Max sell price (range upper bound, 2% above current)
      "total_proceeds": 875.00,         # Estimated based on base price
      "reason": "Profit taking, signal_score declining"
    }
  ],
  "potential_buys": [                    # Filtered and prioritized
    {"symbol": "NVDA", "score": 4.5, "trend": "uptrend"},
    {"symbol": "MSFT", "score": 4.2, "trend": "uptrend"}
  ]
}
```

**Price Range Strategy**:
- **Buy Orders**: Price range `[buy_price_min, buy_price_max]`
  - `buy_price_min` = 98% of current price (2% below current, **low buy**)
  - `buy_price_max` = current price (not exceeding current price)
  - **Execution Strategy**: Prefer `buy_price_min` (buy at lowest price)

- **Sell Orders**: Price range `[sell_price_min, sell_price_max]`
  - `sell_price_min` = 100.5% of current price (0.5% above current)
  - `sell_price_max` = 102% of current price (2% above current, **high sell**)
  - **Execution Strategy**: Prefer `sell_price_max` (sell at highest price)

---

### Step 6: Trade Execution ⚙️

**When Called**: Immediately after Trader Agent generates decisions (after market open at 09:30 EST)

**Time Point**: Execute immediately after today's market open (09:30 EST)

**Process**:
1. **Execute Buy Orders**:
   - Sorted by `total_cost` (largest first)
   - **Fill Check**: Attempts to fetch actual opening price, with fallback strategy
   - Price fetching strategy:
     1. Try to get today's opening price (Open) via yfinance
     2. If not available, try real-time price (`regularMarketPrice`) from yfinance
     3. If still unavailable, fallback to yesterday's closing price (used as baseline)
     4. **Note**: Since system runs before/at market open, actual opening price may not be available yet
   - If actual price obtained and within range → Execute fill (use optimal price in range)
   - If actual price out of range → Mark as not filled (REJECTED or PENDING)
   - If actual price unavailable → Use price range minimum (`buy_price_min`) as fallback
   - Checks cash availability
   - Reduces quantity if cash insufficient
   - **Execution Price**: 
     - Prefer actual price if available and within range
     - Otherwise use price range minimum (`buy_price_min`) for **low buy** (fallback)
   - Updates Portfolio (cash, positions, avg_cost)
   - Logs to Trade Logger (includes price range and fill status)

2. **Execute Sell Orders**:
   - Validates position exists
   - **Fill Check**: Attempts to fetch actual opening price, with fallback strategy
   - Price fetching strategy (same as buy orders):
     1. Try today's opening price (Open)
     2. Try real-time price (`regularMarketPrice`)
     3. Fallback to yesterday's closing price
   - If actual price within range → Execute fill (use optimal price in range)
   - If actual price below min sell price → Mark as PENDING (wait for higher price)
   - If actual price above max sell price → Execute at higher price (better price)
   - If actual price unavailable → Use price range maximum (`sell_price_max`) as fallback
   - **Execution Price**: 
     - Prefer actual price if available and within range
     - Otherwise use price range maximum (`sell_price_max`) for **high sell** (fallback)
   - Updates Portfolio
   - Logs to Trade Logger (includes price range and fill status)

**Execution Price Notes**:
- Order prices are based on **yesterday's closing price** (base price)
- **Price Range Strategy** (low buy, high sell):
  - **Buy**: Price range `[98% of current price, current price]`, execution uses **lowest price** or **actual price** (low buy)
  - **Sell**: Price range `[100.5% of current price, 102% of current price]`, execution uses **highest price** or **actual price** (high sell)

**Fill Check Mechanism**:
- 🔍 **Price Fetching Strategy** (with limitations):
  1. **Primary**: Try to get today's opening price (Open) via yfinance history
     - ⚠️ **Limitation**: May not be available if system runs at 09:00 (before market open at 09:30)
  2. **Secondary**: Try real-time price (`regularMarketPrice`) from yfinance ticker.info
     - ⚠️ **Limitation**: May not be available if market hasn't opened yet
  3. **Tertiary**: Fallback to yesterday's closing price (`previousClose`)
  4. **Final Fallback**: If all fail, return `None` and use price range bounds
  
- ⚠️ **Critical Limitation**: 
  - System runs at **09:00 EST** (before market open at 09:30)
  - At this time, **today's opening price doesn't exist yet**
  - yfinance typically requires market to be open or closed to have that day's data
  - **Result**: Most likely will use **yesterday's closing price** or **price range bounds** as execution price
  
- 🔄 **Fallback Execution Logic**:
  - If `actual_price` is `None` → Use price range bounds:
    - **Buy**: Use `buy_price_min` (lowest in range) → Executes as FILLED
    - **Sell**: Use `sell_price_max` (highest in range) → Executes as FILLED
  - This ensures orders are executed even without real-time price data
- ✅ **Can Fill**: If actual price available and within range → Execute fill (use optimal price)
- ⏳ **Pending Fill**: If sell price below min sell price → Mark as PENDING (wait for higher price)
- ❌ **Rejected Fill**: If buy price above max buy price → Mark as REJECTED (do not execute)
- 📊 **Actual Price Recording**: All fill records include `actual_price` and `execution_reason` for tracking
- 🔄 **Fallback Behavior**: If `actual_price` is `None`, system uses price range bounds (`buy_price_min` or `sell_price_max`) and marks execution as successful

**Fill Status**:
- `FILLED`: Order successfully filled
- `PENDING`: Price requirement not met, waiting (sell orders only)
- `REJECTED`: Price out of range, execution rejected

**Output**: Execution Results
```python
{
  "executed_trades": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "price": 147.25,  # Actual execution price
      "actual_price": 148.50,  # Actual market opening price (for fill check)
      "price_range": {
        "min": 147.25,   # buy_price_min (2% below current price)
        "max": 150.25    # buy_price_max (current price)
      },
      "quantity": 10,
      "amount": 1472.50,  # Actual payment amount (price * quantity)
      "status": "FILLED",  # Fill status: FILLED / PENDING / REJECTED
      "execution_reason": "Price $148.50 within buy range [$147.25, $150.25]"
    }
  ],
  "execution_errors": [
    "BUY MSFT: Price $425.00 above buy_max $420.00",  # Price out of range, not filled
    "SELL AAPL: Price $174.00 below sell_min $175.88 (waiting for higher price)"  # Pending order
  ],
  "portfolio": {
    "cash": 2197.50,                     # Remaining cash
    "positions": {
      "NVDA": 10,                         # Quantity
      "MSFT": 15
    },
    "positions_detail": {
      "NVDA": {
        "quantity": 10,
        "avg_cost": 150.25,               # Average cost basis
        "current_price": 150.25,
        "market_value": 1502.50
      }
    },
    "total_value": 8497.50,              # Cash + equity
    "equity_value": 6300.00,             # Stock value only
    "total_pnl": -2.50,                  # Total profit/loss
    "total_pnl_pct": -0.03,              # -0.03%
    "positions_pnl": {
      "NVDA": 0.00,                       # Unrealized P&L
      "MSFT": 0.00
    }
  }
}
```

---

### Step 7: Trade Logging & Memory 📝

**Time Point**: After trade execution completes

**Process**: 
1. All trades logged to `backend/data/logs/trades.jsonl`
2. **Daily Memory** automatically saved to `backend/data/logs/memory/daily/YYYY-MM-DD.json`
3. **Weekly Compression**: Automatically compresses memories older than 30 days to `memory/weekly/YYYY-WXX.jsonl`

**Trade Log Format**: JSON Lines (one trade per line)
```json
{
  "symbol": "NVDA",
  "action": "BUY",
  "price": 150.25,
  "quantity": 10,
  "amount": 1502.50,
  "status": "SUCCESS",
  "ts": "2025-01-28 14:30:00",
  "reason": "Strong technical signals",
  "rationale": "Strong RSI=65, positive MACD, signal_score=4.5",
  "stance": "bullish",
  "vix_risk": 7.5
}
```

**Memory includes**:
- Complete market view
- Market analysis results
- Full discussion transcript
- Risk report
- Trading decisions
- Portfolio snapshot

---

## 🧠 Memory Management

### When Memory is Used

Memory is used at **two key points** in the trading cycle:

#### 1. **Loading Historical Memories (Step 1.5) - BEFORE Discussion Agent**

**When**: After Market Analyst completes, **before** Discussion Agent starts

**Location**: `backend/src/orchestrator/trading_cycle.py` (Step 1.5)

**Process**:
```python
# Load last 5 days of memory summaries
historical_memories = memory_manager.load_recent_memories(
    days=5,
    end_date=end if end else None,
    summary_only=True,  # Only summaries to reduce prompt length
)
```

**Purpose**: Provide context to Discussion Agent about past trading decisions

**What is Loaded**:
- Last 5 days of memory summaries
- Includes: date, stance, recommended_stocks, decisions, portfolio_snapshot, risk_level
- **summary_only=True**: Only key information, not full transcripts (to save token space)

**Usage**: Injected into Discussion Agent as `historical_context` in the prompt

---

#### 2. **Saving Daily Memory (Step 7) - AFTER Trading Execution**

**When**: After all trading execution completes

**Location**: `backend/src/orchestrator/trading_cycle.py` (Step 7)

**Process**:
```python
memory_manager.save_daily_memory(
    date=today,
    market_view=market_view,
    market_analysis=market_analysis,
    discussion=convo,
    risk_report=risk_report,
    decision=decision,
    portfolio_snapshot=portfolio_snapshot,
)
```

**Purpose**: Save complete daily trading cycle for future reference

**What is Saved**:
- Complete market view (compressed)
- Market analysis results
- Full discussion transcript
- Risk report
- Trading decisions (buy/sell orders)
- Portfolio snapshot (cash, positions, P&L)

**Storage**: `backend/data/logs/memory/daily/YYYY-MM-DD.json`

---

### Memory Usage Flow

```
Trading Cycle Starts
  ↓
[Step 1] Market Agent collects data
  ↓
[Step 1c] Market Analyst analyzes
  ↓
[Step 1.5] ⚡ LOAD HISTORICAL MEMORIES
  ├─ Load last 5 days of summaries
  ├─ Format as historical_context
  └─ Prepare for Discussion Agent
  ↓
[Step 2] Discussion Agent
  ├─ Receives: enriched_market + historical_memories
  ├─ Uses historical_context in prompt
  └─ Makes decisions considering past trends
  ↓
[Step 3-6] Risk Analyst → Trader Agent → Execution
  ↓
[Step 7] ⚡ SAVE DAILY MEMORY
  ├─ Save complete cycle to daily/YYYY-MM-DD.json
  ├─ Update index for fast retrieval
  └─ Compress old memories (>30 days) to weekly/
```

---

### Memory Features

- ✅ **Hierarchical Storage**: Daily (last 30 days) / Weekly (compressed archive)
- ✅ **Smart Indexing**: Fast retrieval (by date, stock, stance)
- ✅ **Auto Compression**: Memories older than 30 days are automatically compressed
- ✅ **Historical Search**: `search_memories()` supports multi-criteria search

### When Memory Files are Created/Updated

#### Daily Memory Files
- **Created**: After each trading cycle completes (Step 7)
- **Location**: `memory/daily/YYYY-MM-DD.json`
- **Action**: Saves complete daily memory to `memory/daily/YYYY-MM-DD.json`
- **Includes**: Full market view, analysis, discussion, risk report, decisions, portfolio snapshot

#### Weekly Compression
- **Called**: Automatically during `save_daily_memory()` (if `compress_old=True`, which is default)
- **Trigger**: When saving a new daily memory, checks for memories older than 30 days
- **Action**: Compresses old memories to `memory/weekly/YYYY-WXX.jsonl` (JSON Lines format)
- **Purpose**: Saves storage space by keeping only key summaries instead of full data

### Memory Usage

```python
from src.data.memory_manager import MemoryManager

memory_manager = MemoryManager()

# Search NVDA trading history
nvda_history = memory_manager.search_memories(symbol="NVDA", limit=10)

# Load last 5 days of memory summaries
recent = memory_manager.load_recent_memories(days=5, summary_only=True)
```

Detailed documentation: `docs/MEMORY_OPTIMIZATION.md`

---

## 🛠️ Available Tools (Input/Output)

Tools are registered in `ToolBox` and can be called by agents during discussion rounds.

### Market & Sentiment Tools

#### `vix_term`
**Purpose**: Fetch VIX term structure (VIX vs VIX3M ratio)

**Input**: None (uses current date)

**Output**:
```python
{
  "vix": 18.5,                          # Current VIX level
  "vix3m": 20.0,                        # VIX3M level
  "ratio": 1.08                         # VIX3M/VIX ratio (>1 = contango)
}
```

---

#### `vix_close`
**Purpose**: Fetch VIX historical close series

**Input**:
```python
{
  "start": "2024-01-01",               # YYYY-MM-DD
  "end": "2024-01-31"                  # YYYY-MM-DD
}
```

**Output**:
```python
{
  "series": [18.5, 19.0, 18.2, ...],   # VIX close values
  "dates": ["2024-01-01", ...]         # Corresponding dates
}
```

---

#### `fear_greed`
**Purpose**: Fetch Fear & Greed Index

**Input**: None

**Output**:
```python
{
  "value": 65,                         # 0-100 (0=Extreme Fear, 100=Extreme Greed)
  "label": "Greed",                    # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
  "source": "feargreedmeter.com",      # Data source
  "extracted_date": "2025-01-28",      # Date of data
  "asof": "2025-01-28 14:30:00"        # Timestamp
}
```

---

#### `fetch_crypto_batch`
**Purpose**: Fetch cryptocurrency OHLCV and technical indicators

**Input**:
```python
{
  "symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],  # Crypto symbols
  "start": "2024-01-01",                         # Optional: YYYY-MM-DD
  "end": "2024-01-31"                            # Optional: YYYY-MM-DD
}
```

**Output**:
```python
{
  "crypto": {
    "BTC-USD": {
      "price": 42952.61,
      "change_pct": 2.5,
      "rsi14": 48.88,
      "macd": 250.0,
      "signal_score": 5.0,
      # ... same structure as stock data
    },
    "ETH-USD": { ... }
  }
}
```

---

#### `get_crypto_price`
**Purpose**: Get current price for a single cryptocurrency

**Input**:
```python
{
  "symbol": "BTC-USD",                  # Single crypto symbol
  "start": "2024-01-01",                # Optional
  "end": "2024-01-31"                   # Optional
}
```

**Output**:
```python
{
  "price": 42952.61,
  "change_pct": 2.5,
  "rsi14": 48.88,
  # ... technical indicators
}
```

---

### News & Economic Data Tools

#### `news_scan`
**Purpose**: Scan news articles for sentiment indicators

**Input**:
```python
{
  "keywords": ["NVDA", "earnings"],     # Search keywords (also accepts: tickers, queries, symbols)
  "recency_days": 7,                   # Days back to search (also accepts: days)
  "max_articles": 12,                   # Max articles to return (also accepts: max_n)
  "domains": ["www.reuters.com", ...]  # Optional: preferred domains (also accepts: preferred_domains)
}
```

**Output**:
```python
{
  "hits": [
    {
      "title": "NVDA Earnings Beat Expectations",
      "url": "https://...",
      "source": "reuters.com",
      "date": "2025-01-27",
      "snippet": "..."
    },
    # ... more articles
  ],
  "queries": ["NVDA", "earnings"],      # Actual queries used
  "count": 15                           # Total hits found
}
```

---

#### `fetch_jin10_news`
**Purpose**: Fetch financial news from Jin10 (Chinese financial platform)

**Input**:
```python
{
  "max_items": 20,                      # Maximum items to fetch
  "category": "all"                     # Category filter ("all" currently supported)
}
```

**Output**:
```python
{
  "ok": true,
  "items": [
    {
      "title": "新闻标题",
      "time": "14:30:00",
      "content": "新闻内容",
      "category": "market",
      "url": "https://www.jin10.com/..."
    }
  ],
  "count": 15                           # Actual items fetched
}
```

---

#### `fetch_jin10_economic_data`
**Purpose**: Fetch economic indicators (CPI, PMI, GDP, employment, etc.)

**Input**:
```python
{
  "max_items": 20,                      # Maximum items to fetch
  "data_type": "all"                    # Data type filter
}
```

**Output**:
```python
{
  "ok": true,
  "data": [
    {
      "title": "美国CPI数据",
      "time": "14:30:00",
      "content": "CPI同比上涨2.5%",
      "data_type": "inflation",
      "indicators": ["CPI"],
      "values": {"CPI": "2.5%"},
      "country": "美国",
      "url": "https://..."
    }
  ],
  "count": 5
}
```

---

#### `web_search`
**Purpose**: DuckDuckGo search with domain whitelist

**Input**:
```python
{
  "query": "NVDA earnings",            # Search query
  "max_results": 10,                   # Max results
  "domains": ["www.reuters.com"]       # Optional: whitelist domains
}
```

**Output**:
```python
{
  "results": [
    {
      "title": "...",
      "url": "https://...",
      "snippet": "..."
    }
  ],
  "count": 10
}
```

---

#### `fetch_url`
**Purpose**: Fetch and extract main content from a URL

**Input**:
```python
{
  "url": "https://www.reuters.com/..."  # URL to fetch
}
```

**Output**:
```python
{
  "title": "Article Title",
  "content": "Main article content...",
  "url": "https://..."
}
```

---

#### `plan_and_scan_news`
**Purpose**: Intelligent news planning and scanning (LLM generates queries → news_scan → optional fetch_url)

**Input**:
```python
{
  "mview": {                            # Market view (optional)
    "market_sentiment": "bullish",
    "recommended_stocks": ["NVDA"],
    "key_observations": [...]
  },
  "topics": ["earnings", "AI"],        # Optional topics
  "max_articles": 10                   # Max articles
}
```

**Output**: Same as `news_scan` + optional fetched URLs

---

### Trading Tools

#### `portfolio_status`
**Purpose**: Get current portfolio status

**Input**: None (uses current portfolio state)

**Output**:
```python
{
  "cash": 2197.50,
  "positions": {
    "NVDA": 10,
    "MSFT": 15
  },
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -2.50,
  "total_pnl_pct": -0.03
}
```

---

#### `buy`
**Purpose**: Execute buy order (called by Trader Agent, not Discussion Agent)

**Input**:
```python
{
  "symbol": "NVDA",
  "quantity": 10,
  "price": 150.25
}
```

**Output**:
```python
{
  "ok": true,
  "result": {
    "symbol": "NVDA",
    "quantity": 10,
    "price": 150.25,
    "amount": 1502.50,
    "status": "SUCCESS"
  }
}
```

---

#### `sell`
**Purpose**: Execute sell order

**Input**:
```python
{
  "symbol": "AAPL",
  "quantity": 5,
  "price": 175.00
}
```

**Output**:
```python
{
  "ok": true,
  "result": {
    "symbol": "AAPL",
    "quantity": 5,
    "price": 175.00,
    "amount": 875.00,
    "status": "SUCCESS"
  }
}
```

---

## 📊 Stock Universe Configuration

### Universe Definition

The system trades stocks from a configurable universe defined in `backend/config/config.json`:

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META",
    // ... up to 100 stocks (NASDAQ-100 focus)
  ],
  "crypto": [                    // Optional: cryptocurrencies
    "BTC-USD", "ETH-USD", "SOL-USD"
  ]
}
```

### Supported Symbol Types

| Type | Examples | Usage |
|------|----------|-------|
| **Stocks** | `NVDA`, `MSFT`, `AAPL` | Primary trading universe |
| **Crypto** | `BTC-USD`, `ETH-USD`, `SOL-USD` | Cryptocurrency trading |
| **Bonds** | `^TNX`, `^IRX`, `^FVX` | Treasury yields (risk analysis) |
| **Indices** | `^GSPC`, `^DJI`, `^VIX` | Market indices |
| **Inverse ETFs** | `SQQQ`, `SPXU`, `SH`, `PSQ`, `SDS`, `DOG` | Hedging instruments |

### Position Sizing Configuration

```json
{
  "initial_cash": 10000,              // Starting capital
  "position_limit_per_stock": 0.15,   // Max 15% per stock
  "position_limit_total": 0.85,       // Max 85% total exposure
  "position_limit_min_per_stock": 0.03  // Min 3% per stock (for diversification)
}
```

**Dynamic Position Sizing**:
- If many recommended stocks → Smaller positions per stock (more diversified)
- If few recommended stocks → Larger positions per stock
- Respects min/max limits from config

---

## 🔄 Feedback Loop Mechanism

### How It Works

1. **Discussion Agent** analyzes market data
2. If information insufficient → **Calls tools** (news_scan, vix_term, fear_greed, etc.)
3. Tool results **summarized** → Added to `[TOOLS CONTEXT]`
4. Next round: Agent sees `[TOOLS CONTEXT]` → **Reflects** → Avoids redundant calls
5. Process repeats until agent **finalizes** or tool budget exhausted

### Tool Budget

- **Default**: 2 tools per discussion cycle (configurable)
- **Early Exit**: If 2 consecutive rounds without new tools → discussion finalizes

### Example Feedback Loop

```
Round 1:
  Agent: "Need sentiment data for NVDA"
  → Calls: news_scan(keywords=["NVDA"])
  → Result: "15 hits, positive sentiment"
  → Added to [TOOLS CONTEXT]

Round 2:
  Agent sees [TOOLS CONTEXT]: "news_scan: 15 hits, positive sentiment"
  → Agent: "Good news sentiment. Need market fear/greed level"
  → Calls: fear_greed()
  → Result: "65 (Greed)"
  → Added to [TOOLS CONTEXT]

Round 3:
  Agent sees full context:
    - news_scan: 15 hits, positive sentiment
    - fear_greed: 65 (Greed)
  → Agent: "All information gathered. Final stance: bullish"
  → No new tools called → Finalizes
```

---

## 🧪 Testing

All tests are in `backend/tests/`:

```bash
cd backend

# Run all tests
python tests/run_all.py

# Run specific test
python tests/test_00_config.py           # Config validation
python tests/test_05_full_trading_loop.py  # Complete trading cycle
python tests/test_10_tools_integration.py  # All tools test
```

See `backend/tests/README.md` for complete test documentation.

---

## 📚 Configuration

### Main Config: `backend/config/config.json`

```json
{
  "universe": ["NVDA", "MSFT", ...],      // Stock symbols to trade
  "initial_cash": 10000,                  // Starting capital
  "position_limit_per_stock": 0.15,      // Max 15% per stock
  "position_limit_total": 0.85,          // Max 85% total
  "position_limit_min_per_stock": 0.03,  // Min 3% per stock
  "date_range": {
    "start": "2024-01-02",
    "end": "2024-01-31"
  },
  "discussion_rounds": 3,                 // Discussion rounds
  "discussion_auto_tools": true,          // Auto tool calling
  "discussion_tool_budget": 2            // Max tools per cycle
}
```

### Agent Config: `backend/config/agents.yaml`

Defines LLM model and temperature for each agent:
- `market_agent`: llama3.1, temp=0.2
- `market_analyst`: llama3.1, temp=0.3
- `discussion_agent`: llama3.1, temp=0.3
- `risk_analyst`: llama3.1, temp=0.2
- `trader_agent`: llama3.1, temp=0.25

---

## 🔧 Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: src` | Not run from backend directory | `cd backend` before running |
| VIX level = nan | yfinance outage | System auto-falls back to VIXY |
| Ollama connection error | Ollama not running | `ollama serve` |
| `KeyError: Agent key not found` | Config path issue | Ensure `backend/config/agents.yaml` exists |

---

## 📚 Documentation

- `docs/MULTI_AGENT_DISCUSSION.md` - Discussion system details
- `docs/INFORMATION_FLOW_COMPLETE.md` - Complete information flow
- `docs/HKUDS_COMPARISON_AND_FEEDBACK.md` - Comparison with HKUDS/AI-Trader
- `docs/MEMORY_OPTIMIZATION.md` - Memory management system
- `backend/tests/README.md` - Testing guide
- `backend/scripts/setup_daily_scheduler.md` - Daily automation setup
- `docs/TRADING_TIMELINE.md` - Detailed trading timeline and execution flow
- `docs/PRICE_DATA_STRATEGY.md` - Price data strategy (closing prices vs real-time)
- `docs/ORDER_EXECUTION_AND_FILL_CHECK.md` - Order execution and fill check mechanism

---

## 🧰 License

MIT License © 2025 Wenyu Chiou

---

## 🙌 Author

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu
