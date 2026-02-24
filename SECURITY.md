# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. Email the maintainer directly (see repository owner's profile)
3. Include steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Model

### Trading Safety

This system can execute real stock trades. Multiple safeguards prevent accidental order placement:

- **Default mode is READ_ONLY** — no orders can be placed without explicit opt-in
- **LIVE mode requires two-factor confirmation** — both `TRADING_MODE=LIVE` and `I_UNDERSTAND_LIVE_TRADING=YES` env vars
- **Kill-switch** — `TRADING_DISABLED=1` blocks all orders regardless of mode
- **Audit logging** — every order attempt (allowed or blocked) is logged to `audit_orders.jsonl`
- **Defense-in-depth** — orders are checked at both the API layer and the order manager layer

See [docs/SECURITY_MODES.md](docs/SECURITY_MODES.md) for full details.

### API Security

- **Admin authentication** via `ADMIN_TOKEN` environment variable
- **Rate limiting** on sensitive endpoints (3/min for trade execution)
- **CORS restrictions** in production mode
- **No traceback leakage** — errors return sanitized messages with correlation IDs
- **Request correlation** — every request gets an `X-Correlation-ID` for log tracing

### Data Security

- **No database** — all data stored in local JSONL files under `data/logs/`
- **No cloud storage by default** — data stays on your machine
- **No telemetry** — the system does not phone home
- **Credentials in env vars only** — never stored in config files (`.env` is gitignored)

### Dependencies

- Dependencies are declared in `backend/requirements.txt` with minimum version constraints
- CI runs on every PR to catch regressions
- Docker images use `python:3.12-slim` base (minimal attack surface)

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| 1.0.x   | Security fixes only |
| < 1.0   | No        |
