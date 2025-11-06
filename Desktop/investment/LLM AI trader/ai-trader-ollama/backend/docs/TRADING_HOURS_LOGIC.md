# Trading Hours Logic

This document explains how the AI Trader system handles trading hours and off-hours behavior.

## Market Hours Detection

**Location**: `backend/src/api/server.py` - `is_market_open()` function

**Logic**:
```python
def is_market_open() -> bool:
    """
    Check if US stock market is currently open
    Trading hours: Monday-Friday, 9:30 AM - 4:00 PM ET
    """
    now = datetime.now(timezone(timedelta(hours=-5)))  # ET timezone
    
    # Check if weekday (Monday=0, Sunday=6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check time range
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    return market_open <= now <= market_close
```

---

## Trading Hours Behavior

### During Market Hours (9:30 AM - 4:00 PM ET, Mon-Fri)

#### Backend (`/api/portfolio/real-time`)
- Fetches **live prices** from yfinance
- Updates portfolio with **current market values**
- Records equity snapshots:
  - Every 30 seconds OR
  - When portfolio value changes by ≥0.5%
- Returns real-time P&L for all positions

#### Frontend (`monitor.html`)
- Auto-refresh every 60 seconds
- Displays live portfolio values
- Charts update with new equity points
- "Start Trading" button executes immediately
- Order execution:
  - BUY orders executed at current market price
  - Orders saved to `filled_orders.jsonl`
  - Portfolio state updated immediately

---

## Off-Hours Behavior

### Non-Trading Hours (4:00 PM - 9:30 AM ET, Weekends)

#### Backend (`/api/portfolio/real-time`)
- **No live price fetching**
- Reads last known state from `portfolio_state.json`
- Returns:
  - Last recorded positions
  - Last recorded equity value
  - Historical P&L (no updates)
- Equity recording:
  - Records **once per day** if no record exists
  - Uses closing prices from last trading day
  - Prevents duplicate records

#### Frontend (`monitor.html`)
- Auto-refresh continues (every 60 seconds)
- Displays historical values (not live)
- Charts show yesterday's data
- "Start Trading" button:
  - **Plans for next trading day**
  - Creates pending orders with **tomorrow's date**
- Order behavior:
  - Orders saved to `pending_orders.jsonl` with `order_date = tomorrow`
  - Status: `PENDING`
  - Will be checked for execution when market opens

---

## Order Date Logic

**Location**: `backend/src/orchestrator/trading_cycle.py`

### Market Open
```python
if is_market_open:
    today = date.today().isoformat()  # Current date
    # Orders execute immediately
```

### Market Closed
```python
else:
    tomorrow = date.today() + timedelta(days=1)
    # Skip weekends
    while tomorrow.weekday() >= 5:
        tomorrow += timedelta(days=1)
    today = tomorrow.isoformat()  # Next trading day
    
    # Check if orders already exist for tomorrow
    existing_orders = order_manager.load_pending_orders(order_date=today)
    if existing_orders:
        # Skip - plan already exists
    else:
        # Create new orders for tomorrow
```

---

## Pending Order Execution

**When**: Next market open (Monday 9:30 AM or next trading day)

**Process**:
1. System loads pending orders with `order_date = today`
2. For each pending order:
   - Fetch current market price
   - Check if limit price can be filled:
     - **BUY**: `current_price <= limit_price`
     - **SELL**: `current_price >= limit_price`
   - If fillable:
     - Execute order
     - Move to `filled_orders.jsonl`
     - Update portfolio state
     - Remove from pending

---

## Data Persistence

### Always Persisted
- `portfolio_state.json`: Current cash + positions
- `filled_orders.jsonl`: All executed trades
- `equity_history.jsonl`: Daily equity snapshots
- `discussion_actions.jsonl`: All agent conversations
- `pending_orders.jsonl`: Orders waiting for execution

### Never Reset (Except Manual Initialization)
All historical data is preserved across:
- Market open/close transitions
- Server restarts
- Multiple trading cycles
- Page refreshes

---

## Frontend Refresh Behavior

**Location**: `frontend/monitor.html`

### Auto-Refresh (Every 60s)
```javascript
function refreshData(showLoading = true) {
    // Always fetch portfolio, conversations, trades
    // During market hours: Live data
    // During off-hours: Historical data
}
```

### Manual "Start Trading" Click
- Checks `is_market_open` via API
- If open: Executes trading cycle immediately
- If closed: Creates pending orders for tomorrow

### Holdings Display
- **Market Open**: Shows current positions with live P&L
- **Market Closed**: Shows last positions with closing P&L
- **Never Hidden**: Holdings remain visible after market close

---

## API Endpoints Behavior Summary

| Endpoint | Market Open | Market Closed |
|----------|-------------|---------------|
| `/api/portfolio/real-time` | Live prices, real-time P&L | Historical prices, last P&L |
| `/api/trading/execute-trade` | Immediate execution | Creates pending orders |
| `/api/trades/history` | All trades including today | All trades up to yesterday |
| `/api/agents/conversations` | Latest conversations | Latest conversations |
| `/api/equity/history` | All equity points | All equity points |

---

## Key Design Principles

1. **No Data Loss**: All records preserved regardless of market hours
2. **Graceful Degradation**: System works in off-hours with historical data
3. **Smart Planning**: Off-hours planning prevents duplicate orders
4. **Transparent State**: Frontend clearly shows whether data is live or historical
5. **Automatic Recovery**: System automatically resumes live updates when market opens

---

## Testing Market Hours Logic

**Test Script**: `backend/scripts/test_trading_scenarios_en.py`

Tests covered:
- Market open/close detection
- Order date assignment
- Equity recording frequency
- Data file integrity
- Portfolio state persistence

**Manual Testing**:
1. **During Market Hours**: Run trading cycle, verify immediate execution
2. **After Market Close**: Run trading cycle, verify pending orders created for tomorrow
3. **Next Day**: Verify pending orders execute when market opens

---

## Configuration

**No configuration needed** - Market hours are hardcoded to US stock market hours (9:30 AM - 4:00 PM ET, Mon-Fri).

For testing with different hours, modify `is_market_open()` function in `backend/src/api/server.py`.

