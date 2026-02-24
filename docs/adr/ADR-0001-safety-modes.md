# ADR-0001: Trading Safety Modes

**Status:** Accepted
**Date:** 2026-02-23
**Author:** A0 Orchestrator + A2 Backend Lead + A6 Security Reviewer

## Context

The AI Trader system places real stock orders via the Alpaca/yfinance integration. Prior to this change, **any authenticated request** to `/api/trading/execute-trade` could trigger real order placement with no safety net beyond admin authentication. This creates unacceptable risk:

- A misconfigured cron job could place live orders.
- A developer testing locally could accidentally trade with real money.
- A public demo deployment could be exploited to place orders.

Trading systems require defense-in-depth: multiple independent safety barriers must all be satisfied before real money is at risk.

## Decision

Introduce three explicit runtime modes enforced at the **order execution layer** (not just the UI):

| Mode | Orders | Audit Log | Default |
|------|--------|-----------|---------|
| `READ_ONLY` | Blocked (403) | Yes — records blocked attempts | **Yes** |
| `PAPER` | Logged & simulated | Yes — records allowed orders | No |
| `LIVE` | Real execution | Yes — records all orders | No |

### Mode Resolution (priority order)
1. Kill-switch `TRADING_DISABLED=1` → blocks everything regardless of mode
2. Environment variable `TRADING_MODE` (if set)
3. Config file `config.json` field `"trading_mode"` (if set)
4. Default: `READ_ONLY`

### LIVE Mode — Two-Factor Safety
LIVE mode requires **two independent opt-ins**:
1. Mode set to `LIVE` (via env or config)
2. Environment variable `I_UNDERSTAND_LIVE_TRADING=YES` (exact string match)

If either is missing, order placement is blocked with a clear error message.

### Kill-Switch
`TRADING_DISABLED=1` is an emergency override that blocks **all** order placement regardless of mode. This allows operators to instantly halt trading without changing config files or restarting the server.

### Enforcement Point
Mode gating is enforced in `OrderManager.place_order()` — the single code path through which all orders flow. This ensures safety cannot be bypassed by calling internal functions directly.

### Audit Log
Every order attempt (allowed or blocked) is written to `data/logs/audit_orders.jsonl` with:
- Timestamp (UTC ISO 8601)
- Trading mode
- Action (BUY/SELL)
- Symbol, quantity, price
- Result (ALLOWED / BLOCKED_MODE / BLOCKED_KILLSWITCH / BLOCKED_NO_CONFIRMATION)
- Reason string

## Alternatives Considered

1. **UI-only gating**: Hide trading buttons in frontend for demo users.
   - Rejected: frontend controls are easily bypassed via direct API calls.

2. **Admin auth as the only barrier**: Rely on ADMIN_SECRET for safety.
   - Rejected: admin auth controls *who* can trade, not *whether* trading should happen. A valid admin in a dev environment should still not accidentally place live orders.

3. **Separate server binaries for demo vs. live**: Build two different server configurations.
   - Rejected: adds build complexity and makes it easy to deploy the wrong binary.

## Consequences

### Positive
- Safe-by-default: new installations cannot accidentally trade.
- Defense-in-depth: kill-switch, mode gating, and confirmation phrase are independent barriers.
- Full audit trail for compliance and debugging.
- Frontend can display mode prominently to prevent user confusion.

### Negative
- Existing users who rely on default config for live trading must update their config and environment. This is a **breaking change** for anyone who was using the system in production without explicit mode configuration.

### Migration
- Existing `config.json` files will default to `READ_ONLY` if `trading_mode` is not set.
- To restore previous behavior: set `TRADING_MODE=PAPER` (or `LIVE` with confirmation) in environment.
- The `install.bat` and `setup_wizard.bat` scripts will be updated to explain mode selection.
