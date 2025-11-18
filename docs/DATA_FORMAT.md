# Data File Format Documentation

This document provides detailed specifications for all data files used by the AI-Trader Ollama system.

## Overview

All data files are stored in `data/logs/` directory (relative to project root). Files use JSON or JSONL (JSON Lines) format.

---

## Core Data Files

### 1. Portfolio State (`portfolio_state.json`)

**Location**: `data/logs/portfolio_state.json`  
**Format**: JSON (single object)  
**Purpose**: Current portfolio state snapshot

**Schema**:
```json
{
  "cash": float,              // Current cash balance
  "initial_value": float,     // Initial portfolio value (usually $10,000)
  "total_value": float,       // Current total portfolio value
  "positions": {              // Current holdings
    "SYMBOL": {
      "quantity": int,         // Number of shares
      "avg_cost": float,       // Average cost per share
      "total_cost": float      // Total cost basis
    }
  },
  "timestamp": "ISO8601"      // Optional: Last update timestamp
}
```

**Example**:
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
    },
    "MSFT": {
      "quantity": 5,
      "avg_cost": 420.00,
      "total_cost": 2100.00
    }
  },
  "timestamp": "2025-01-28T10:00:00Z"
}
```

**Field Descriptions**:
- `cash`: Available cash for trading
- `initial_value`: Starting capital (from `config.json` → `initial_cash`)
- `total_value`: `cash + sum(positions market values)`
- `positions`: Dictionary mapping stock symbols to position details
- `quantity`: Number of shares held
- `avg_cost`: Average purchase price per share
- `total_cost`: `quantity * avg_cost`

---

### 2. Equity History (`equity_history.jsonl`)

**Location**: `data/logs/equity_history.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Historical net asset value tracking  
**Recording Frequency**: Every 30 minutes during market hours

**Schema** (per line):
```json
{
  "date": "YYYY-MM-DD",                    // Date string
  "timestamp": "ISO8601",                  // Full timestamp with timezone
  "cash": float,                           // Cash balance at this time
  "equity_value": float,                    // Total market value of positions
  "total_value": float,                     // cash + equity_value
  "total_pnl": float,                       // Total profit/loss (total_value - initial_value)
  "total_pnl_pct": float,                   // Total P&L percentage
  "positions": {                            // Position details at this time
    "SYMBOL": {
      "quantity": int,
      "avg_cost": float,
      "current_price": float,
      "market_value": float,                // quantity * current_price
      "unrealized_pnl": float,              // (current_price - avg_cost) * quantity
      "unrealized_pnl_pct": float           // unrealized_pnl / (avg_cost * quantity) * 100
    }
  }
}
```

**Example**:
```json
{
  "date": "2025-01-28",
  "timestamp": "2025-01-28T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -1502.50,
  "total_pnl_pct": -15.03,
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

**Important Notes**:
- All timestamps are preserved (no deduplication by date)
- Multiple records per day are allowed (distinguished by timestamp)
- Used for performance analysis and equity curve visualization

---

### 3. Filled Orders (`filled_orders.jsonl`)

**Location**: `data/logs/filled_orders.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Completed trade records with realized P&L

**Schema** (per line):
```json
{
  "order_id": "string",                    // Unique order identifier
  "placed_at": "ISO8601",                  // When order was placed
  "symbol": "SYMBOL",                      // Stock symbol
  "action": "BUY" | "SELL",                // Order direction
  "quantity": int,                          // Number of shares
  "fill_price": float,                     // Execution price
  "status": "FILLED",                       // Order status
  "realized_pnl": float,                   // Realized P&L (SELL orders only)
  "realized_pnl_pct": float,               // Realized P&L percentage (SELL orders only)
  "cost_basis": float,                     // Original purchase cost (SELL orders only)
  "proceeds": float,                        // Sale proceeds (SELL orders only)
  "fill_result": {                         // Additional fill details
    "filled_at": "ISO8601",
    "fill_price": float,
    "fill_quantity": int
  }
}
```

**Example (BUY order)**:
```json
{
  "order_id": "order_001",
  "placed_at": "2025-01-28T10:30:00Z",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "fill_price": 150.25,
  "status": "FILLED",
  "fill_result": {
    "filled_at": "2025-01-28T10:30:00Z",
    "fill_price": 150.25,
    "fill_quantity": 10
  }
}
```

**Example (SELL order with P&L)**:
```json
{
  "order_id": "order_002",
  "placed_at": "2025-01-28T14:00:00Z",
  "symbol": "NVDA",
  "action": "SELL",
  "quantity": 10,
  "fill_price": 155.00,
  "status": "FILLED",
  "realized_pnl": 47.50,
  "realized_pnl_pct": 3.16,
  "cost_basis": 1502.50,
  "proceeds": 1550.00,
  "fill_result": {
    "filled_at": "2025-01-28T14:00:00Z",
    "fill_price": 155.00,
    "fill_quantity": 10,
    "realized_pnl": 47.50,
    "realized_pnl_pct": 3.16,
    "cost_basis": 1502.50,
    "proceeds": 1550.00
  }
}
```

**Field Descriptions**:
- `realized_pnl`: `proceeds - cost_basis` (only for SELL orders)
- `realized_pnl_pct`: `(realized_pnl / cost_basis) * 100`
- `cost_basis`: Original purchase cost (FIFO method)
- `proceeds`: `fill_price * quantity`

---

### 4. Discussion Actions (`discussion_actions.jsonl`)

**Location**: `data/logs/discussion_actions.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Agent conversations, analysis, and tool calls

**Schema** (per line):
```json
{
  "timestamp": "ISO8601",                  // When this action occurred
  "date": "YYYY-MM-DD",                    // Date string
  "agent": "AgentName",                     // Agent identifier
  "round": int,                             // Discussion round (1, 2, 3, or 0)
  "content": "string",                       // Full agent response/content
  "type": "discussion" | "tool_call" | "decision" | "other",
  "summary": "string",                      // Brief summary (optional)
  "stance": "BULLISH" | "BEARISH" | "NEUTRAL",  // Market stance (optional)
  "tools_used": ["tool1", "tool2"],        // List of tools called (optional)
  "recommended_stocks": ["SYMBOL1", "SYMBOL2"]  // Recommended stocks (optional)
}
```

**Agent Types**:
- `MarketAnalyst`: Market data and trend analysis
- `TechnicalAnalyst`: Technical indicators and chart patterns
- `FundamentalAnalyst`: Company fundamentals and financials
- `SentimentAnalyst`: Market sentiment and news analysis
- `DiscussionCoordinator`: Consensus building and synthesis
- `RiskAnalyst`: Risk assessment and position limits
- `TraderAgent`: Trading decision making

**Example**:
```json
{
  "timestamp": "2025-01-28T10:00:00Z",
  "date": "2025-01-28",
  "agent": "MarketAnalyst",
  "round": 1,
  "content": "Market analysis shows mixed signals...",
  "type": "discussion",
  "summary": "Market shows mixed sentiment with tech sector leading",
  "stance": "NEUTRAL",
  "tools_used": ["get_market_indices", "get_sector_rotation"],
  "recommended_stocks": ["NVDA", "MSFT", "AAPL"]
}
```

---

### 5. Pending Orders (`pending_orders.jsonl`)

**Location**: `data/logs/pending_orders.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Orders waiting to be executed

**Schema** (per line):
```json
{
  "order_id": "string",
  "placed_at": "ISO8601",
  "symbol": "SYMBOL",
  "action": "BUY" | "SELL",
  "quantity": int,
  "status": "PENDING"
}
```

**Note**: Orders are moved to `filled_orders.jsonl` when executed.

---

### 6. Trades (`trades.jsonl`)

**Location**: `data/logs/trades.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: All trade execution history

**Schema**: Similar to `filled_orders.jsonl` but may include additional execution details.

---

## Memory System Files

### Daily Memory (`memory/daily/YYYY-MM-DD.json`)

**Location**: `data/logs/memory/daily/YYYY-MM-DD.json`  
**Format**: JSON (single object)  
**Purpose**: Complete daily market snapshot and agent discussions

**Schema**:
```json
{
  "date": "YYYY-MM-DD",
  "market_analysis": {
    "market_view": {...},                   // Market data snapshot
    "discussion": {...},                    // Agent discussions
    "risk_report": {...},                   // Risk analysis
    "trading_decisions": {...},            // Trading decisions
    "portfolio_snapshot": {...},           // Portfolio state
    "executed_trades": [...]                // Trades executed
  }
}
```

**Compression**: After 30 days, daily memories are compressed to weekly summaries (only Monday and weekend records preserved).

---

### Weekly Memory (`memory/weekly/YYYY-WNN.jsonl`)

**Location**: `data/logs/memory/weekly/YYYY-WNN.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Weekly compressed memory summaries

**Schema** (per line):
```json
{
  "week": "YYYY-WNN",
  "monday": {...},                          // Monday memory (compressed)
  "weekend": {...},                         // Weekend memory (compressed)
  "days_in_week": int,
  "compressed_days": int
}
```

---

### Monthly Memory (`memory/monthly/YYYY-MM.jsonl`)

**Location**: `data/logs/memory/monthly/YYYY-MM.jsonl`  
**Format**: JSONL (one JSON object per line)  
**Purpose**: Monthly compressed memory summaries

---

## Data Access

### API Endpoints

All data can be accessed via REST API:

- **Portfolio**: `GET /api/portfolio/real-time`
- **Equity History**: `GET /api/portfolio/equity-history`
- **Trades**: `GET /api/trades/recent`
- **Conversations**: `GET /api/agents/conversations`
- **Performance**: `GET /api/performance/statistics`

### Direct File Access

Files can be read directly from `data/logs/` directory:

```python
import json
from pathlib import Path

# Read portfolio state
with open("data/logs/portfolio_state.json") as f:
    portfolio = json.load(f)

# Read equity history (JSONL)
equity_records = []
with open("data/logs/equity_history.jsonl") as f:
    for line in f:
        if line.strip():
            equity_records.append(json.loads(line))
```

---

## Data Integrity

### Recording Frequency

- **Equity History**: Every 30 minutes during market hours
- **Portfolio State**: Updated after each trading cycle
- **Filled Orders**: Recorded immediately upon order execution
- **Discussion Actions**: Recorded after each agent turn

### Data Preservation

- ✅ All timestamps preserved (no deduplication)
- ✅ Historical records never deleted (except via `/api/system/init?force=true`)
- ✅ Weekly compression preserves Monday and weekend records
- ✅ All realized P&L records retained

---

## Performance Analysis

Performance metrics are calculated from:

1. **Equity History**: Total return, max drawdown, Sharpe ratio
2. **Filled Orders**: Win rate, average trade return, realized P&L

See [Performance Analysis API](../README.md#-historical-performance-analysis) for details.

---

## File Size Considerations

- **JSONL files**: Can grow large over time. Consider periodic archiving.
- **Memory files**: Automatically compressed after 30 days.
- **Backup**: Use `scripts/backup_data.ps1` for regular backups.

---

## Troubleshooting

### Missing Data

If data files are missing:
1. Check `data/logs/` directory exists
2. Verify API server is running
3. Check file permissions
4. Review API logs for errors

### Corrupted Data

If files are corrupted:
1. Stop API server
2. Backup existing files
3. Restore from backup or reinitialize: `POST /api/system/init?force=true`

---

## Related Documentation

- [Data Storage Guide](DATA_STORAGE_GUIDE.md) - Storage location and file purposes
- [API Reference](API_REFERENCE.md) - API endpoints for data access
- [Performance Analysis](../README.md#-historical-performance-analysis) - Performance metrics

