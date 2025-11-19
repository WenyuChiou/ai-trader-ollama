# API Data Parsing Documentation

This document describes how all API endpoints parse and handle the unified data format.

## Overview

All API endpoints must correctly parse data with:
- **Timestamp Format**: ISO 8601 UTC format with 'Z' suffix (`YYYY-MM-DDTHH:MM:SS.fffZ`)
- **Field Consistency**: Required fields must be present and correctly typed
- **Backward Compatibility**: Support for legacy data formats (without 'Z' suffix, with `+00:00`, etc.)

---

## API Endpoints

### 1. `/api/portfolio/equity-history`

**Purpose**: Get equity history records

**Data Source**: `equity_history.jsonl`

**Parsing Logic**:
- Uses `EquityTracker.load_equity_history()` which:
  - Automatically adds missing `timestamp` fields (defaults to `date + T12:00:00.000Z`)
  - Ensures all timestamps end with 'Z' suffix
  - Supports filtering by `start_date`/`end_date` or `start_timestamp`/`end_timestamp`
  - Sorts records chronologically by timestamp

**Timestamp Handling**:
```python
# In EquityTracker.load_equity_history():
if "timestamp" not in record:
    record["timestamp"] = record["date"] + "T12:00:00.000Z"

if not record["timestamp"].endswith('Z'):
    record["timestamp"] = record["timestamp"] + 'Z'
```

**Response Format**:
```json
{
  "ok": true,
  "records": [
    {
      "date": "YYYY-MM-DD",
      "timestamp": "YYYY-MM-DDTHH:MM:SS.fffZ",
      "cash": float,
      "equity_value": float,
      "total_value": float,
      "total_pnl": float,
      "total_pnl_pct": float,
      "positions": {...}
    }
  ],
  "count": int
}
```

---

### 2. `/api/portfolio/record-equity`

**Purpose**: Record equity snapshot

**Data Source**: Frontend POST request

**Parsing Logic**:
- Extracts `date` from request (or from `timestamp` if `date` missing)
- Uses `EquityTracker.record_daily_equity()` which:
  - Generates UTC timestamp with 'Z' suffix
  - Validates timestamp format
  - Appends to `equity_history.jsonl`

**Timestamp Generation**:
```python
timestamp_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
```

---

### 3. `/api/trades/recent`

**Purpose**: Get recent filled orders

**Data Source**: `filled_orders.jsonl`

**Parsing Logic**:
- Reads from end of file (optimized for large files)
- Parses JSON lines directly
- Returns raw order objects (no timestamp normalization needed, as they're already in correct format)

**Timestamp Format**: Orders should have `placed_at` and `filled_at` in UTC format (`YYYY-MM-DDTHH:MM:SS.fffZ`)

**Response Format**:
```json
{
  "ok": true,
  "trades": [
    {
      "order_id": "string",
      "placed_at": "YYYY-MM-DDTHH:MM:SS.fffZ",
      "filled_at": "YYYY-MM-DDTHH:MM:SS.fffZ",
      "symbol": "SYMBOL",
      "action": "BUY" | "SELL",
      "quantity": int,
      "fill_price": float,
      "status": "FILLED",
      "realized_pnl": float,  // SELL orders only
      "realized_pnl_pct": float,  // SELL orders only
      "cost_basis": float,  // SELL orders only
      "proceeds": float  // SELL orders only
    }
  ]
}
```

---

### 4. `/api/performance/statistics`

**Purpose**: Calculate performance statistics

**Data Sources**: 
- `equity_history.jsonl` (via `_load_equity_history()`)
- `filled_orders.jsonl` (via `_load_filled_orders()`)

**Parsing Logic**:

**Equity History** (`_load_equity_history()`):
```python
timestamp = record.get("timestamp", "")
if timestamp:
    if timestamp.endswith('Z'):
        record_date = timestamp.split("T")[0]
    elif '+' in timestamp or '-' in timestamp[10:]:
        record_date = timestamp.split("T")[0] if "T" in timestamp else timestamp.split(" ")[0]
    else:
        record_date = timestamp.split("T")[0] if "T" in timestamp else timestamp.split(" ")[0]
else:
    record_date = record.get("date", "")
```

**Filled Orders** (`_load_filled_orders()`):
```python
placed_at = order.get("placed_at", "")
if placed_at:
    if placed_at.endswith('Z'):
        order_date = placed_at.split("T")[0]
    elif '+' in placed_at or '-' in placed_at[10:]:
        order_date = placed_at.split("T")[0] if "T" in placed_at else placed_at.split(" ")[0]
    else:
        order_date = placed_at.split("T")[0] if "T" in placed_at else placed_at.split(" ")[0]
else:
    order_date = order.get("date", "")
```

**Key Features**:
- Supports UTC format (`Z` suffix)
- Supports ISO 8601 format (`+00:00` or `-05:00`)
- Falls back to `date` field if timestamp missing
- Handles malformed records gracefully (skips with warning)

---

### 5. `/api/performance/trades-by-date`

**Purpose**: Get trades grouped by date

**Data Source**: `filled_orders.jsonl` (via `_load_filled_orders()`)

**Parsing Logic**: Same as `/api/performance/statistics` for filled orders

---

### 6. `/api/performance/symbol-analysis`

**Purpose**: Get symbol-specific performance analysis

**Data Sources**: 
- `filled_orders.jsonl` (via `_load_filled_orders()`)
- Filters by `symbol` parameter

**Parsing Logic**: Same as `/api/performance/statistics` for filled orders

---

## Timestamp Parsing Strategy

All API endpoints use a unified timestamp parsing strategy:

### 1. **Primary Format (UTC with Z suffix)**
```
YYYY-MM-DDTHH:MM:SS.fffZ
Example: 2025-01-28T10:00:00.000Z
```

### 2. **Fallback Formats**
- ISO 8601 with timezone: `YYYY-MM-DDTHH:MM:SS+00:00`
- ISO 8601 without timezone: `YYYY-MM-DDTHH:MM:SS`
- Date string: `YYYY-MM-DD`

### 3. **Parsing Logic**
```python
def parse_timestamp(ts: str) -> str:
    """Parse timestamp and return date string"""
    if not ts:
        return ""
    
    # UTC format (Z suffix)
    if ts.endswith('Z'):
        return ts.split("T")[0]
    
    # ISO 8601 with timezone
    if '+' in ts or (len(ts) > 10 and '-' in ts[10:]):
        return ts.split("T")[0] if "T" in ts else ts.split(" ")[0]
    
    # ISO 8601 without timezone
    if "T" in ts:
        return ts.split("T")[0]
    
    # Date string
    return ts.split(" ")[0] if " " in ts else ts
```

---

## Data Consistency Checks

### Equity History Records

**Required Fields**:
- `date`: `YYYY-MM-DD`
- `timestamp`: `YYYY-MM-DDTHH:MM:SS.fffZ`
- `cash`: `float`
- `equity_value`: `float`
- `total_value`: `float`
- `total_pnl`: `float`
- `total_pnl_pct`: `float`
- `positions`: `dict`

**Validation**:
- `total_value = cash + equity_value` (within ±0.01 tolerance)
- `timestamp` must end with 'Z' (auto-fixed if missing)

### Filled Orders Records

**Required Fields (All Orders)**:
- `order_id`: `string`
- `placed_at`: `YYYY-MM-DDTHH:MM:SS.fffZ`
- `symbol`: `string`
- `action`: `"BUY" | "SELL"`
- `quantity`: `int`
- `fill_price`: `float`
- `status`: `"FILLED"`

**Additional Fields (SELL Orders Only)**:
- `realized_pnl`: `float`
- `realized_pnl_pct`: `float`
- `cost_basis`: `float`
- `proceeds`: `float`
- `filled_at`: `YYYY-MM-DDTHH:MM:SS.fffZ` (optional)

**Validation**:
- SELL orders must have `realized_pnl`, `realized_pnl_pct`, `cost_basis`, `proceeds`
- BUY orders should NOT have realized P&L fields
- `placed_at` and `filled_at` must end with 'Z' (auto-fixed if missing)

---

## Error Handling

### Malformed Records

All API endpoints handle malformed records gracefully:

1. **JSON Parse Errors**: Skip record, log warning, continue processing
2. **Missing Required Fields**: Skip record, log warning, continue processing
3. **Invalid Timestamp Format**: Attempt to parse, fallback to `date` field
4. **Type Errors**: Skip record, log warning, continue processing

### Example Error Handling

```python
try:
    record = json.loads(line.strip())
    # Process record
except (json.JSONDecodeError, AttributeError, TypeError) as e:
    print(f"[API] Skipping malformed record: {e}")
    continue
```

---

## Testing

Use the test script to verify API parsing:

```bash
python backend/scripts/test_api_parsing.py
```

This script tests:
1. Equity history parsing
2. Filled orders parsing
3. API endpoint compatibility
4. Timestamp format validation

---

## Migration Notes

### Legacy Data Support

All API endpoints support legacy data formats:
- Timestamps without 'Z' suffix (auto-fixed)
- Timestamps with `+00:00` timezone (parsed correctly)
- Records without `timestamp` field (uses `date` field)

### Data Normalization

When reading data:
- Missing timestamps are auto-generated
- Timestamps without 'Z' are auto-fixed
- Invalid formats are handled gracefully

When writing data:
- All timestamps are generated in UTC format with 'Z' suffix
- All required fields are validated before writing

---

## Related Documentation

- [Record Consistency Documentation](RECORD_CONSISTENCY.md) - Data format specifications
- [Data Format Documentation](DATA_FORMAT.md) - Complete data file schemas

