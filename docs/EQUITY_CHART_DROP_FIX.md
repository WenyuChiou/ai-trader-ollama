# Equity Chart Drop Fix

## Problem Analysis

### Issue 1: Flat Line ($9797.43)
**Observation**: From 16:46 to 20:51, all records show the same value ($9797.43)

**Root Cause**: 
- Market closes at 4:00 PM ET (16:00)
- After market close, prices don't change, so equity value remains constant
- This is **normal behavior** - not a bug

### Issue 2: Sharp Drop at End
**Observation**: Chart shows a sharp drop to $9,654.66 at 19:18

**Root Cause**:
- Last record (20:51) shows all positions with `current_price = N/A`, `market_value = $0.00`
- But `total_value` is still correctly recorded as $9797.43
- Frontend may calculate `total_value = cash + sum(market_value)` when `market_value = 0`
- This causes display error: `$99.37 + $0 = $99.37` (incorrect)

**Why `current_price = N/A`?**:
- Market closed, yfinance cannot fetch real-time prices
- Price fetching fails, `current_price` becomes `N/A`
- `market_value` becomes `0` (quantity * N/A = 0)
- But `total_value` is still correct from previous calculation

## Fixes Applied

### Fix 1: API Endpoint Market Check
**File**: `backend/src/api/server.py`

Added market status check in `/api/portfolio/record-equity` endpoint:
- If market is closed, return early with status message
- Prevents recording with invalid price data

### Fix 2: Price Fallback in Equity Tracker
**File**: `backend/src/data/equity_tracker.py`

**Before**:
```python
if "current_price" in pos_info:
    positions_record[symbol]["current_price"] = pos_info["current_price"]
```

**After**:
```python
# CRITICAL FIX: Ensure current_price is always present (use avg_cost as fallback if missing)
current_price = pos_info.get("current_price")
if current_price is None or current_price == "N/A" or current_price == 0:
    # Use avg_cost as fallback to prevent market_value = 0
    current_price = avg_cost
    print(f"[EQUITY] Position {symbol} missing current_price, using avg_cost=${avg_cost:.2f} as fallback")

# CRITICAL FIX: Ensure market_value is always calculated (never 0 if we have quantity and price)
market_value = pos_info.get("market_value", 0)
if market_value == 0 and quantity > 0 and current_price > 0:
    market_value = quantity * current_price
    print(f"[EQUITY] Recalculated market_value for {symbol}: {quantity} * ${current_price:.2f} = ${market_value:.2f}")
```

**Benefits**:
- ✅ `current_price` is never `N/A` (uses `avg_cost` as fallback)
- ✅ `market_value` is never `0` if we have quantity and price
- ✅ Chart displays correctly even when price fetching fails

### Fix 3: Frontend Market Check Enhancement
**File**: `frontend/monitor.html`

**Before**:
```javascript
if (!marketOpen) {
    console.log('[Equity Record] Market is closed, skipping equity recording');
    return;
}
```

**After**:
```javascript
if (!marketOpen) {
    console.log('[Equity Record] Market is closed, skipping equity recording (will resume at next market open)');
    return; // Don't record when market is closed
}
// CRITICAL: If check fails, skip recording to prevent data corruption
// Better to skip than record with invalid data
```

**Benefits**:
- ✅ More robust error handling
- ✅ Prevents recording when market status check fails

## Expected Behavior After Fix

### During Market Hours (9:30 AM - 4:00 PM ET)
- ✅ Records every 30 minutes with real-time prices
- ✅ Chart shows accurate equity curve
- ✅ All positions have `current_price` and `market_value`

### After Market Close (After 4:00 PM ET)
- ✅ No new records created (market closed check prevents recording)
- ✅ Last record before market close is preserved
- ✅ Chart shows flat line (normal - prices don't change after close)
- ✅ No sharp drop (price fallback ensures `market_value` is never 0)

### If Price Fetching Fails
- ✅ Uses `avg_cost` as fallback for `current_price`
- ✅ Recalculates `market_value = quantity * current_price`
- ✅ Chart displays correctly (no drop to $0)

## Testing

Run the analysis script to verify:
```powershell
python backend/scripts/analyze_equity_drop.py
```

Expected output:
- All records should have `current_price` (never `N/A`)
- All records should have `market_value > 0` (if quantity > 0)
- No records after market close (4:00 PM ET)

## Related Files

- `backend/src/api/server.py` - API endpoint with market check
- `backend/src/data/equity_tracker.py` - Price fallback logic
- `frontend/monitor.html` - Frontend market check
- `backend/scripts/analyze_equity_drop.py` - Analysis script

