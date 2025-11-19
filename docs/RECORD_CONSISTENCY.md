# Record Consistency Documentation

This document describes the consistency requirements and validation rules for all data records in the AI-Trader system.

## Overview

All records must follow strict consistency rules for:
- **Timestamp Format**: ISO 8601 UTC format with 'Z' suffix
- **Numerical Calculations**: All P&L calculations must be mathematically consistent
- **Field Completeness**: Required fields must be present
- **Data Integrity**: Cross-field validation (e.g., total_value = cash + equity_value)

---

## 1. Equity History Records (`equity_history.jsonl`)

### Timestamp Format
- **Required Format**: `YYYY-MM-DDTHH:MM:SS.fffZ` (UTC timezone)
- **Example**: `2025-01-28T10:00:00.000Z`
- **Validation**: Must end with 'Z' to indicate UTC timezone

### Required Fields
```json
{
  "date": "YYYY-MM-DD",           // Date string (YYYY-MM-DD)
  "timestamp": "ISO8601",          // Full timestamp with Z suffix
  "cash": float,                   // Cash balance
  "equity_value": float,           // Total market value of positions
  "total_value": float,            // cash + equity_value
  "total_pnl": float,              // total_value - initial_value
  "total_pnl_pct": float,          // (total_pnl / initial_value) * 100
  "positions": {                   // Position details
    "SYMBOL": {
      "quantity": int,
      "avg_cost": float,
      "current_price": float,
      "market_value": float,       // quantity * current_price
      "unrealized_pnl": float,     // (current_price - avg_cost) * quantity
      "unrealized_pnl_pct": float  // (unrealized_pnl / (avg_cost * quantity)) * 100
    }
  }
}
```

### Consistency Rules

1. **Total Value Calculation**:
   ```
   total_value = cash + equity_value
   ```
   Tolerance: ±0.01 (floating point precision)

2. **Equity Value Calculation**:
   ```
   equity_value = sum(positions[SYMBOL].market_value for all SYMBOL)
   ```

3. **Market Value Calculation** (per position):
   ```
   market_value = quantity * current_price
   ```
   Tolerance: ±0.01

4. **Unrealized P&L Calculation** (per position):
   ```
   unrealized_pnl = (current_price - avg_cost) * quantity
   unrealized_pnl_pct = (unrealized_pnl / (avg_cost * quantity)) * 100
   ```
   Tolerance: ±0.01

5. **Total P&L Calculation**:
   ```
   total_pnl = total_value - initial_value
   total_pnl_pct = (total_pnl / initial_value) * 100
   ```

6. **Timestamp Ordering**:
   - Records must be in chronological order (earliest to latest)
   - Multiple records per day are allowed (distinguished by timestamp)

### Recording Frequency
- **During Market Hours**: Every 30 minutes (at :00 and :30 marks)
- **After Market Close**: No recording (resumes at next market open)

---

## 2. Filled Orders Records (`filled_orders.jsonl`)

### Timestamp Format
- **Required Format**: `YYYY-MM-DDTHH:MM:SS.fffZ` (UTC timezone)
- **Fields**: `placed_at`, `filled_at` (if present)
- **Example**: `2025-01-28T10:30:00.000Z`

### Required Fields (All Orders)
```json
{
  "order_id": "string",            // Unique identifier
  "placed_at": "ISO8601",          // When order was placed (UTC, Z suffix)
  "symbol": "SYMBOL",              // Stock symbol
  "action": "BUY" | "SELL",        // Order direction
  "quantity": int,                 // Number of shares
  "fill_price": float,             // Execution price
  "status": "FILLED"               // Order status
}
```

### Additional Fields (SELL Orders Only)
```json
{
  "realized_pnl": float,           // proceeds - cost_basis
  "realized_pnl_pct": float,       // (realized_pnl / cost_basis) * 100
  "cost_basis": float,             // Original purchase cost (FIFO)
  "proceeds": float,               // fill_price * quantity
  "filled_at": "ISO8601"           // When order was filled (UTC, Z suffix)
}
```

### Consistency Rules

1. **BUY Orders**:
   - Must NOT have `realized_pnl`, `realized_pnl_pct`, `cost_basis`, or `proceeds` fields
   - Or these fields must be `0` or `null`

2. **SELL Orders**:
   - **Required Fields**: `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`
   - **Proceeds Calculation**:
     ```
     proceeds = fill_price * quantity
     ```
     Tolerance: ±0.01
   
   - **Realized P&L Calculation**:
     ```
     realized_pnl = proceeds - cost_basis
     ```
     Tolerance: ±0.01
   
   - **Realized P&L Percentage**:
     ```
     realized_pnl_pct = (realized_pnl / cost_basis) * 100
     ```
     Tolerance: ±0.01
     Note: If `cost_basis` is 0, `realized_pnl_pct` should be 0 or undefined

3. **Timestamp Consistency**:
   - `filled_at` must be >= `placed_at` (if both present)
   - Both timestamps must be in UTC (Z suffix)

---

## 3. Portfolio State (`portfolio_state.json`)

### Consistency Rules

1. **Total Value Calculation**:
   ```
   total_value = cash + sum(positions[SYMBOL].quantity * positions[SYMBOL].current_price)
   ```
   Tolerance: ±0.01

2. **Total P&L Calculation**:
   ```
   total_pnl = total_value - initial_value
   ```
   Tolerance: ±0.01

3. **Position Cost Basis**:
   ```
   total_cost = quantity * avg_cost
   ```
   Tolerance: ±0.01

---

## 4. Timestamp Format Standard

### Standard Format
- **Format**: `YYYY-MM-DDTHH:MM:SS.fffZ`
- **Timezone**: UTC (indicated by 'Z' suffix)
- **Precision**: Milliseconds (3 decimal places)

### Examples
```
2025-01-28T10:00:00.000Z  ✅ Correct
2025-01-28T10:00:00Z      ✅ Correct (no milliseconds)
2025-01-28T10:00:00       ❌ Missing timezone indicator
2025-01-28 10:00:00       ❌ Wrong format
2025-01-28T10:00:00+00:00 ❌ Should use 'Z' instead of '+00:00'
```

### Implementation
All timestamp generation must use:
```python
from datetime import datetime, timezone

timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
```

---

## 5. Validation Checklist

### Equity History
- [ ] All records have `date` and `timestamp` fields
- [ ] Timestamps end with 'Z' (UTC)
- [ ] `total_value = cash + equity_value` (within tolerance)
- [ ] For each position: `market_value = quantity * current_price`
- [ ] For each position: `unrealized_pnl = (current_price - avg_cost) * quantity`
- [ ] For each position: `unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100`
- [ ] Records are in chronological order

### Filled Orders
- [ ] All orders have `placed_at` timestamp (UTC, Z suffix)
- [ ] SELL orders have `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`
- [ ] BUY orders do NOT have realized P&L fields (or they are 0/null)
- [ ] For SELL orders: `proceeds = fill_price * quantity`
- [ ] For SELL orders: `realized_pnl = proceeds - cost_basis`
- [ ] For SELL orders: `realized_pnl_pct = (realized_pnl / cost_basis) * 100`
- [ ] `filled_at >= placed_at` (if both present)

### Portfolio State
- [ ] `total_value = cash + equity_value` (within tolerance)
- [ ] `total_pnl = total_value - initial_value` (within tolerance)
- [ ] All positions have `quantity`, `avg_cost`, `total_cost`

---

## 6. Running Consistency Checks

Use the consistency check script:
```bash
python backend/scripts/check_record_consistency.py
```

This script will:
1. Validate all equity history records
2. Validate all filled orders records
3. Validate portfolio state
4. Report any inconsistencies found

---

## 7. Common Issues and Fixes

### Issue: Timestamp Missing 'Z' Suffix
**Symptom**: Timestamps like `2025-01-28T10:00:00.000` instead of `2025-01-28T10:00:00.000Z`
**Fix**: Ensure all timestamp generation uses UTC timezone and 'Z' suffix

### Issue: Total Value Mismatch
**Symptom**: `total_value != cash + equity_value`
**Fix**: Recalculate `total_value` from `cash` and `equity_value` before saving

### Issue: SELL Order Missing Realized P&L
**Symptom**: SELL orders without `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`
**Fix**: Ensure `mark_order_filled()` is called with `realized_pnl` parameter for SELL orders

### Issue: Unrealized P&L Calculation Error
**Symptom**: `unrealized_pnl != (current_price - avg_cost) * quantity`
**Fix**: Recalculate using correct formula before saving

---

## 8. Code References

### Timestamp Generation
- **Equity History**: `backend/src/data/equity_tracker.py` → `record_daily_equity()`
- **Filled Orders**: `backend/src/data/order_manager.py` → `place_order()`, `mark_order_filled()`
- **Trading Cycle**: `backend/src/orchestrator/trading_cycle.py` → Market order execution

### P&L Calculations
- **Unrealized P&L**: `backend/src/api/server.py` → `get_portfolio_real_time()`
- **Realized P&L**: `backend/src/orchestrator/trading_cycle.py` → `portfolio.sell()`
- **Total P&L**: `backend/src/api/server.py` → `get_portfolio_real_time()`

---

## 9. Related Documentation

- [Data Format Documentation](DATA_FORMAT.md) - Complete data file schemas
- [Performance Analysis](../README.md#-historical-performance-analysis) - How records are used for analysis

