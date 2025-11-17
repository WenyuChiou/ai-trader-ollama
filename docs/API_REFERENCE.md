# API Reference

## Base URL
- Local: `http://localhost:8000`
- Production: Your Railway/Cloud URL

## Authentication
Currently no authentication required (local use only).

## Endpoints

### Health Check
**GET** `/api/health`

Check API server health.

**Response**:
```json
{
  "ok": true,
  "status": "healthy"
}
```

### System Info
**GET** `/api/system/info`

Get system information and configuration.

**Response**:
```json
{
  "ok": true,
  "version": "1.0.0",
  "position_limits": {
    "enabled": false,
    "mode": "auto"
  },
  "cash_reserve": {
    "enabled": false,
    "ratio": null
  }
}
```

### Market Status
**GET** `/api/market/is-open`

Check if market is currently open.

**Response**:
```json
{
  "ok": true,
  "is_open": true,
  "eastern_time": "2025-11-17T10:30:00-05:00",
  "market_hours": "9:30 AM - 4:00 PM ET"
}
```

### Portfolio Real-time
**GET** `/api/portfolio/real-time`

Get real-time portfolio data.

**Response**:
```json
{
  "ok": true,
  "cash": 5000.0,
  "total_value": 10000.0,
  "equity_value": 5000.0,
  "total_pnl": 100.0,
  "total_pnl_pct": 1.0,
  "positions": {
    "NVDA": 10
  },
  "positions_detail": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 500.0,
      "current_price": 510.0,
      "market_value": 5100.0,
      "unrealized_pnl": 100.0
    }
  },
  "positions_pnl": {
    "NVDA": {
      "unrealized_pnl": 100.0,
      "unrealized_pnl_pct": 2.0
    }
  }
}
```

### Equity History
**GET** `/api/portfolio/equity-history?limit=60`

Get historical equity records.

**Query Parameters**:
- `limit` (int): Number of records to return (default: 60)

**Response**:
```json
{
  "ok": true,
  "equity_history": [
    {
      "date": "2025-11-17",
      "total_value": 10000.0,
      "cash": 5000.0,
      "equity": 5000.0
    }
  ]
}
```

### Execute Trade
**POST** `/api/trading/execute-trade`

Execute a full trading cycle.

**Response**:
```json
{
  "ok": true,
  "decision": {
    "action": "BUY",
    "buy_orders": [...],
    "sell_orders": [...]
  },
  "portfolio": {...}
}
```

### Agent Conversations
**GET** `/api/agents/conversations?limit=30`

Get agent conversation logs.

**Query Parameters**:
- `limit` (int): Number of records (default: 30)
- `date` (string): Filter by date (YYYY-MM-DD)
- `include_demo` (bool): Include demo entries (default: false)

**Response**:
```json
{
  "ok": true,
  "conversations": [
    {
      "timestamp": "2025-11-17T10:00:00",
      "analyst": "Market Analyst",
      "stance": "bullish",
      "analysis": "..."
    }
  ]
}
```

### Recent Trades
**GET** `/api/trades/recent?limit=10`

Get recent trade history.

**Query Parameters**:
- `limit` (int): Number of records (default: 10)

**Response**:
```json
{
  "ok": true,
  "trades": [
    {
      "symbol": "NVDA",
      "action": "BUY",
      "quantity": 10,
      "price": 500.0,
      "timestamp": "2025-11-17T10:00:00"
    }
  ]
}
```

### System Initialization
**POST** `/api/system/init?force=true`

Reset system to initial state.

**Query Parameters**:
- `force` (bool): Force initialization (default: false)

**Response**:
```json
{
  "ok": true,
  "message": "System initialized"
}
```

## Error Responses

All endpoints return errors in this format:
```json
{
  "ok": false,
  "error": "Error message"
}
```

## Rate Limiting
Currently no rate limiting (local use only).

## CORS
CORS headers are set to allow all origins (`*`).

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Configuration Guide](CONFIGURATION.md)
- [Architecture Documentation](ARCHITECTURE.md)

