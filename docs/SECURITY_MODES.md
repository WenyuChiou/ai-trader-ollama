# Security Modes

This document explains the trading mode safety system that prevents accidental live trading.

## Trading Modes

| Mode | Default? | Orders Executed? | Use Case |
|------|----------|-----------------|----------|
| `READ_ONLY` | Yes | No | Demo, monitoring, development |
| `PAPER` | No | Simulated only | Backtesting, strategy validation |
| `LIVE` | No | Real orders | Production trading (requires 2-factor confirmation) |

## Mode Resolution (Priority Order)

1. **Kill-switch**: `TRADING_DISABLED=1` blocks ALL orders regardless of mode
2. **Environment variable**: `TRADING_MODE=PAPER` (overrides config)
3. **Config file**: `config.json` → `"trading_mode": "READ_ONLY"`
4. **Default**: `READ_ONLY`

## Setting the Mode

### Option 1: Environment Variable (Recommended)

```bash
# Windows
set TRADING_MODE=PAPER

# Linux/Mac
export TRADING_MODE=PAPER
```

### Option 2: Config File

Edit `backend/config/config.json`:
```json
{
  "trading_mode": "PAPER"
}
```

### Option 3: Sample Configs

Pre-built configs for each mode:
- `backend/config/config.readonly.json` — Safe default for demos
- `backend/config/config.paper.json` — Simulated trading
- `backend/config/config.live.template.json` — Real trading template

## LIVE Mode Safeguards

LIVE mode requires **two independent confirmations**:

1. Set `TRADING_MODE=LIVE` (in env or config)
2. Set `I_UNDERSTAND_LIVE_TRADING=YES` (env var only, cannot be set in config)

If either is missing, the system falls back to `READ_ONLY`.

```bash
# Both required for LIVE trading
set TRADING_MODE=LIVE
set I_UNDERSTAND_LIVE_TRADING=YES
```

## Kill-Switch

Emergency stop for all trading:

```bash
set TRADING_DISABLED=1
```

This blocks all orders in ANY mode (including LIVE). The kill-switch:
- Takes effect immediately (no restart needed)
- Returns HTTP 403 from all trading endpoints
- Logs the block to the audit log
- Shows a warning banner in the frontend

To re-enable: `set TRADING_DISABLED=0` or unset the variable.

## Audit Logging

Every order attempt (allowed or blocked) is logged to `data/logs/audit_orders.jsonl`:

```json
{
  "timestamp": "2026-02-23T15:30:00Z",
  "mode": "READ_ONLY",
  "action": "BUY",
  "symbol": "NVDA",
  "quantity": 10,
  "price": 150.0,
  "allowed": false,
  "reason": "READ_ONLY mode blocks BUY"
}
```

## Frontend Indicators

The web dashboard (`monitor.html`) displays:
- **Mode badge** in the header: blue (READ_ONLY), yellow (PAPER), red pulsing (LIVE)
- **LIVE warning banner**: Red sticky banner at the top when in LIVE mode
- **403 error handling**: Clear messages when orders are blocked

## API Endpoints

- `GET /api/health` — Returns current `trading_mode` and `trading_disabled` status
- `GET /api/trading/mode` — Detailed mode info including `live_confirmed`
- `POST /api/trading/execute-trade` — Returns 403 if mode blocks trading

## Enforcement Points

Orders are blocked at multiple layers:
1. **API layer** (`server.py`): Pre-flight check before entering trading cycle
2. **Order manager** (`order_manager.py`): `assert_can_trade()` at `place_order()`
3. **Audit logger**: Records every attempt regardless of outcome

## Architecture Decision

See [ADR-0001: Safety Modes](adr/ADR-0001-safety-modes.md) for the full rationale.

## See Also

- [Configuration Guide](CONFIGURATION.md)
- [Quick Start Guide](QUICK_START.md)
