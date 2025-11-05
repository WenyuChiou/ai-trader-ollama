# Complete System Flow: Frontend & Backend Integration

## Overview

This document provides a comprehensive overview of the entire AI-Trader system flow, covering both frontend dashboard interactions and backend trading logic.

## System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Frontend      │◄───────►│   FastAPI        │◄───────►│   Trading       │
│   Dashboard     │  HTTP   │   Backend        │  Logic  │   Agents        │
│   (monitor.html)│         │   (server.py)    │         │   & Tools       │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      ▼
                              ┌──────────────────┐
                              │   Data Storage   │
                              │   (JSONL files)  │
                              └──────────────────┘
```

## Frontend Flow

### 1. Initialization & Connection

**On Page Load:**
- Dashboard connects to `http://127.0.0.1:8000`
- Checks API health via `/api/market/is-open`
- Displays connection status (green dot = connected, red = disconnected)
- Shows market status (green = open, red = closed)
- Shows conversation status (orange = generating, gray = idle)

**Status Indicators:**
- **Connection Status**: Real-time API connectivity
- **Market Status**: Trading hours (9:30 AM - 4:00 PM EST, Mon-Fri)
- **Conversation Status**: Agent discussion generation state

### 2. Data Refresh Cycle

**Auto Refresh (30 seconds):**
- Runs every 30 seconds when market is open
- Automatically stops when market closes
- Fetches:
  - Portfolio data (cash, positions, P&L)
  - Equity history (for charts)
  - Conversations (agent discussions)
  - Trade execution details
  - Backend status

**Manual Refresh:**
- User can click "Refresh" button anytime
- Same data fetch as auto refresh

**Market Hours Behavior:**
- **During Market Hours**: Fetches real-time portfolio with live prices
- **After Market Hours**: Fetches cached snapshots and historical data

### 3. Trading Cycle Execution

**Auto Trade (30 minutes during market hours):**
- Automatically runs every 30 minutes when market is open
- Stops automatically when market closes
- Executes full trading cycle:
  1. Checks pending orders from previous day
  2. Fills limit orders if price conditions met
  3. Runs agent analysis (Market, Fundamental, Technical, Sentiment, Risk)
  4. Generates trading decisions
  5. Executes market orders immediately (if market open)
  6. Creates limit orders (if market closed)

**Manual Trading:**
- User can click "Start Trading" button
- Same execution flow as auto trade
- Works during market hours and non-market hours

**Minute-Level Fill Check:**
- Runs every 60 seconds during market hours
- Checks for pending orders with today's date
- Triggers order fill check if pending orders exist

### 4. Data Display

**Summary Cards:**
- Total Portfolio Value (cash + equity)
- Total P&L (realized + unrealized)
- Available Cash
- Equity Value (current positions)

**Positions Table:**
- Lists all current holdings
- Shows quantity, average cost, current price
- Displays per-position P&L

**Equity Chart:**
- Historical net value over time
- Updates every 30 seconds during market hours
- Shows trend even during non-market hours

**Execution Details:**
- Shows all orders (pending and filled)
- Highlights tomorrow's orders with badge
- Hides filled orders during non-market hours

**Conversations:**
- Displays agent discussions in readable format
- Shows tool usage (FGI, VIX, news, economic data)
- Formats JSON summaries as key-value lists
- Shows agent icons and timestamps

## Backend Flow

### 1. Trading Cycle Entry Point

**API Endpoint: `/api/trading/execute-trade`**

**Market Hours (9:30 AM - 4:00 PM EST, Mon-Fri):**
1. Check for pending orders from today
2. Fill pending orders if price conditions met
3. Run full agent analysis cycle
4. Execute new market orders immediately
5. Update portfolio and log trades

**Non-Market Hours:**
1. Check if tomorrow's orders already exist
2. If not, plan tomorrow's trades (create limit orders)
3. If yes, skip planning (avoid duplicates)

### 2. Agent Analysis Cycle

**Step 1: Market Data Fetching**
- Fetches OHLCV data for universe stocks
- Calculates technical indicators (RSI, MACD, Bollinger Bands)
- Computes signal scores

**Step 2: Market Analyst**
- Analyzes overall market sentiment
- Recommends stocks based on market conditions
- Output: `market_sentiment`, `recommended_stocks`

**Step 3: Fundamental Analyst**
- Evaluates fundamental factors
- Provides key observations per stock
- Output: `market_sentiment`, `recommended_stocks`, `key_observations`

**Step 4: Technical Analyst**
- Analyzes technical indicators
- Identifies top signals
- Output: `top_signals`, `indicators` (RSI, MACD, BB positions)

**Step 5: Sentiment Analyst**
- Fetches Fear & Greed Index (FGI)
- Fetches VIX term structure
- Calculates VIX risk score
- Output: `fgi`, `vix_term`, `vix_risk_score`

**Step 6: Tool System**
- Explicitly calls tools:
  - `fear_greed`: FGI data
  - `vix_term`: VIX term structure
  - `news_scan`: News scanning
  - `fetch_jin10_economic_data`: Economic calendar
- Logs tool usage separately

**Step 7: Risk Analyst**
- Evaluates portfolio risk
- Calculates position limits
- Identifies safe and high-risk stocks
- Output: `overall_risk_level`, `risk_score`, `max_position_size`, `safe_stocks`, `high_risk_stocks`

**Step 8: Discussion Agent**
- Facilitates multi-round discussion
- Synthesizes all agent inputs
- Reaches consensus on market stance
- Output: Discussion transcript and final stance

**Step 9: Trader Agent**
- Makes final trading decisions
- Generates buy/sell orders with prices and quantities
- Considers risk limits and cooldown periods
- Output: `buy_orders`, `sell_orders`, `rationale`

### 3. Order Execution Logic

**Pending Order Check (Market Hours Only):**
1. Load pending orders for today
2. For each pending order:
   - Get current market price
   - Check if price condition met:
     - BUY: current_price <= limit_price
     - SELL: current_price >= limit_price
   - If condition met, execute immediately
   - Update portfolio
   - Mark order as FILLED
   - Log trade

**New Order Execution:**

**During Market Hours:**
1. For each buy order:
   - Check cash availability
   - Check position limits
   - Check cooldown periods
   - Execute market order immediately at current price
   - Update portfolio
   - Log as FILLED

2. For each sell order:
   - Check position availability
   - Execute market order immediately at current price
   - Update portfolio
   - Log as FILLED

**During Non-Market Hours:**
1. For each buy order:
   - Create limit order (limit_price = buy_price * 0.998)
   - Save to `pending_orders.jsonl`
   - Status: PENDING

2. For each sell order:
   - Create limit order (limit_price = sell_price * 1.002)
   - Save to `pending_orders.jsonl`
   - Status: PENDING

### 4. Portfolio Management

**Portfolio State:**
- Stored in `data/logs/portfolio_state.json`
- Contains: cash, positions, initial_value
- Updated after each trade

**Position Tracking:**
- Each position: symbol, quantity, avg_cost, total_cost
- P&L calculated using current market prices
- Real-time updates during market hours

**Equity History:**
- Recorded in `data/logs/equity_history.jsonl`
- Snapshot every trading cycle
- Used for frontend chart display

### 5. Data Logging

**Conversations:**
- File: `data/logs/discussion_actions.jsonl`
- Format: JSON lines with agent, type, content, timestamp
- Includes: summaries, tool usage, discussion rounds

**Trades:**
- File: `data/logs/trades.jsonl`
- Format: Trade records with symbol, action, price, quantity, status

**Pending Orders:**
- File: `data/logs/pending_orders.jsonl`
- Format: Order details with limit_price, order_date, status

**Filled Orders:**
- File: `data/logs/filled_orders.jsonl`
- Format: Filled order details with fill_price, fill_reason

**Real-Time Snapshots:**
- File: `data/logs/real_time_snapshots.jsonl`
- Format: Portfolio snapshots with timestamp

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND DASHBOARD                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Auto Refresh │  │  Auto Trade │  │  Fill Check  │       │
│  │  (30s)       │  │  (30 min)   │  │  (60s)       │       │
│  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼──────────────────┼─────────────────┼─────────────┘
          │                  │                 │
          ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    API ENDPOINTS                             │
│  /api/portfolio/real-time  /api/trading/execute-trade      │
│  /api/agents/conversations  /api/trades/recent              │
│  /api/market/is-open       /api/portfolio/equity-history    │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRADING CYCLE                             │
│                                                              │
│  1. Check Pending Orders (if market open)                   │
│     └─> Fill if price conditions met                       │
│                                                              │
│  2. Fetch Market Data (OHLCV, indicators)                   │
│                                                              │
│  3. Run Agent Analysis:                                     │
│     ├─> Market Analyst                                      │
│     ├─> Fundamental Analyst                                 │
│     ├─> Technical Analyst                                   │
│     ├─> Sentiment Analyst (FGI, VIX)                       │
│     ├─> Tool System (explicit tool calls)                   │
│     ├─> Risk Analyst                                        │
│     ├─> Discussion Agent                                    │
│     └─> Trader Agent                                        │
│                                                              │
│  4. Execute Orders:                                         │
│     ├─> Market Hours: Immediate market orders               │
│     └─> Non-Market Hours: Create limit orders              │
│                                                              │
│  5. Update Portfolio & Log Data                             │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Portfolio    │  │ Conversations│  │ Orders       │      │
│  │ State        │  │ Actions      │  │ (Pending/    │      │
│  │              │  │              │  │  Filled)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Market Hours Awareness

**Frontend:**
- Auto refresh only during market hours
- Auto trade only during market hours
- Shows market status indicator
- Displays different data based on market state

**Backend:**
- Checks market hours before executing trades
- Market orders only during market hours
- Limit orders during non-market hours
- Pending order checks only during market hours

### 2. Order Execution Strategy

**Market Orders (During Market Hours):**
- Execute immediately at current market price
- No waiting for price conditions
- Instant portfolio updates
- Immediate position creation

**Limit Orders (Non-Market Hours):**
- Created with price offsets:
  - BUY: -0.2% from base price
  - SELL: +0.2% from base price
- Checked at market open
- Filled if price conditions met
- Remains pending if conditions not met

### 3. Agent Conversation Format

**Frontend Display:**
- Parses JSON summaries into readable key-value lists
- Shows tool results with labels
- Displays comments separately
- Uses icons for different agents
- Formats arrays as badges

**Backend Output:**
- Structured JSON summaries
- Tool usage explicitly logged
- Discussion transcripts included
- All agent outputs preserved

### 4. Error Handling

**Frontend:**
- Graceful degradation if API unavailable
- Shows cached data if available
- Continues displaying conversations and orders even if portfolio fails
- Distinguishes between connection errors and data errors

**Backend:**
- Validates all inputs
- Handles missing data gracefully
- Logs errors for debugging
- Continues execution even if some agents fail

## Testing the Flow

### Manual Testing Steps

1. **Start API:**
   ```bash
   cd backend
   $env:PYTHONPATH = "$PWD;$PWD\src"
   python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
   ```

2. **Open Dashboard:**
   - Navigate to `frontend/monitor.html` in browser
   - Should show "Connected" status

3. **During Market Hours:**
   - Click "Start Trading"
   - Should see market orders execute immediately
   - Check positions table for new holdings
   - Verify conversations appear

4. **Non-Market Hours:**
   - Click "Start Trading"
   - Should create limit orders for tomorrow
   - Check Execution Details for PENDING orders
   - Verify "TOMORROW" badge appears

5. **Verify Data Updates:**
   - Wait for auto refresh (30s)
   - Check if portfolio values update
   - Verify equity chart updates
   - Confirm conversations appear

## Troubleshooting

### Common Issues

1. **All orders showing PENDING:**
   - Check if market is open
   - Verify limit_price is set correctly
   - Check if prices meet fill conditions

2. **No positions created:**
   - Verify market orders executed
   - Check cash availability
   - Review execution errors in logs

3. **Conversations not showing:**
   - Check `discussion_actions.jsonl` file
   - Verify API endpoint returns data
   - Check frontend console for errors

4. **Portfolio not updating:**
   - Verify API is running
   - Check market hours status
   - Review portfolio_state.json file

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Advanced order types (stop-loss, trailing stop)
- [ ] Multi-strategy support
- [ ] Performance analytics
- [ ] Risk management dashboard
- [ ] Backtesting capabilities

