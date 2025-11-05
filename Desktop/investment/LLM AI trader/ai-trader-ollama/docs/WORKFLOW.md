# 🔄 Complete Daily Workflow

This document explains the complete daily trading workflow in detail.

---

## ⏰ Time Flow

**System Work Mode**: **Analyze yesterday's data today, execute immediately after today's market open**

```
Timeline Example:
  Day N-1 (2025-01-27)          Day N (2025-01-28)
  Close 16:00 EST        →      Before Open 09:00 EST  →  After Open 09:30 EST
                                  │                      │
                                  ├─ Run Script          └─ Execute Orders Immediately
                                  ├─ Analyze: 1/27 Closing Price
                                  └─ Generate Trade Orders (using yesterday's closing price)
```

**Why Use Yesterday's Closing Price?**
- ✅ **Data Completeness**: Closing price is definitive and complete data
- ✅ **Suitable for Technical Analysis**: Daily closing price is suitable for calculating MA, RSI, MACD
- ✅ **Avoid Delays**: No dependency on real-time API, uses free yfinance
- ✅ **Immediate Execution**: Execute immediately after market open, no need to wait until close

---

## 📊 Step-by-Step Workflow

### Step 1: Market Data Collection

**Agent**: Market Agent (via `fetch_market_batch` tool)  
**Time**: Today morning 09:00 (before market open)

**Input**:
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL", ...],  # From config.json
  "start": "2024-01-01",                     # Historical data start
  "end": "2025-01-27"                        # Yesterday (closing price)
}
```

**Process**:
1. Fetches OHLCV data via yfinance (uses **yesterday's closing price**)
2. Computes technical indicators (RSI14, MACD, Bollinger Bands, MA20/50)
3. Calculates `signal_score` (0-10 composite score)
4. Fetches VIX data (volatility index)

**Output**: `market_view` - Complete market data with technical indicators

---

### Step 1c: Market Analysis

**Agent**: Market Analyst  
**When**: Immediately after market data collection

**Input**: `market_view`

**Process**:
1. LLM analyzes all stocks in universe
2. Assesses trends (uptrend/downtrend/sideways)
3. Evaluates VIX regime (low/normal/elevated/spike)
4. Generates buy recommendations

**Output**: `market_analysis` - Recommended stocks, market sentiment

---

### Step 1.5: Load Historical Memories

**When**: After Market Analyst, before Discussion Agent

**Process**:
- Loads last 5 days of memory summaries
- Formats as `historical_context`
- Injects into Discussion Agent prompt

**Purpose**: Provide context about past trading decisions

---

### Step 2: Discussion Agent

**Agent**: Discussion Agent (Multi-round with feedback loop)  
**When**: After Market Analyst completes, with historical memories

**Input**: `enriched_market` + `historical_memories`

**Process**: Multi-round discussion
- **Round 1**: Analyzes market → Calls tools if needed → Gets results
- **Round 2**: Sees `[TOOLS CONTEXT]` → Reflects → Calls new tools if needed
- **Round N**: Has full context → Forms final stance

**Tool Calling**: Automatically calls tools when information is insufficient
- Available: `news_scan`, `vix_term`, `fear_greed`, `fetch_jin10_news`, etc.
- Tool results injected into next round as `[TOOLS CONTEXT]`
- Tool budget: 2 (configurable)

**Output**: `consensus` - Final stance, reasoning, tool results

---

### Step 3: Risk Analysis

**Agent**: Risk Analyst  
**When**: After Discussion Agent, only if portfolio has positions

**Input**: `market_view`, `current_positions`, `portfolio_value`

**Process**:
1. Assesses market risk (VIX level, volatility)
2. Calculates position concentration (HHI index)
3. Evaluates single stock exposure vs limits
4. Generates position control recommendations

**Output**: `risk_report` - Risk level, position limits

---

### Step 4: Trading Decision

**Agent**: Trader Agent  
**When**: After Risk Analyst completes

**Input**: `market_view`, `consensus`, `risk_report`, `position_config`

**Process**:
1. Evaluates all recommended stocks
2. Considers VIX risk level
3. Applies risk report position limits
4. Calculates position sizes dynamically
5. Generates buy/sell orders with prices

**Output**: `decision` - Buy/sell orders with price ranges

**Price Range Strategy**:
- **Buy Orders**: `[98% of current price, current price]` (low buy)
- **Sell Orders**: `[100.5% of current price, 102% of current price]` (high sell)

---

### Step 5: Order Execution

**When**: After Trader Agent decisions (after market open at 09:30 EST)

**Process**:
1. **Place Orders**: Creates limit orders (pre-market)
2. **Fill Check** (after market close):
   - Checks if orders were filled based on daily High/Low
   - Updates portfolio with executed trades
   - Records fill status (FILLED/PENDING/REJECTED)

**Execution Strategy**:
- Attempts to fetch actual opening price
- Falls back to price range bounds if unavailable
- Buy: Uses lowest price in range
- Sell: Uses highest price in range

---

### Step 6: Memory & Tracking

**When**: After execution completes

**Process**:
1. Saves complete daily memory to `memory/daily/YYYY-MM-DD.json`
2. Records portfolio equity to `equity_history.jsonl`
3. Updates monitoring logs

**Memory Includes**:
- Complete market view
- Market analysis results
- Full discussion transcript
- Risk report
- Trading decisions
- Portfolio snapshot

---

## 🔄 Complete Flow Diagram

```
Daily Trading Cycle Starts (09:00)
  ↓
[Step 1] Market Agent
  └─ Fetch OHLCV + Technical Indicators
  ↓
[Step 1c] Market Analyst
  └─ Analyze trends, generate recommendations
  ↓
[Step 1.5] Load Historical Memories
  └─ Load last 5 days of summaries
  ↓
[Step 2] Discussion Agent
  └─ Multi-round analysis with tool calls
  ↓
[Step 3] Risk Analyst
  └─ Assess portfolio risk
  ↓
[Step 4] Trader Agent
  └─ Generate buy/sell orders
  ↓
[Step 5] Execution
  └─ Place orders (pre-market)
  └─ Check fills (after close)
  ↓
[Step 6] Memory & Tracking
  └─ Save daily memory
  └─ Record equity
```

---

## 📝 Detailed Output Examples

See [`docs/AGENTS.md`](AGENTS.md) for detailed input/output examples for each agent.

---

## 🔍 Related Documentation

- [`docs/TRADING_TIMELINE.md`](TRADING_TIMELINE.md) - Trading timeline details
- [`docs/ORDER_EXECUTION_AND_FILL_CHECK.md`](ORDER_EXECUTION_AND_FILL_CHECK.md) - Execution mechanism
- [`docs/PRICE_DATA_STRATEGY.md`](PRICE_DATA_STRATEGY.md) - Price data strategy

