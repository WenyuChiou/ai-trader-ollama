# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.1.0] - 2026-02-23

### Added — Safety & Security
- **Trading mode gating**: `READ_ONLY` (default), `PAPER`, `LIVE` modes with defense-in-depth enforcement
- **Kill-switch**: `TRADING_DISABLED=1` blocks all orders regardless of mode
- **LIVE two-factor confirmation**: Requires both `TRADING_MODE=LIVE` and `I_UNDERSTAND_LIVE_TRADING=YES`
- **Audit logging**: Every order attempt (allowed/blocked) logged to `audit_orders.jsonl`
- **Frontend mode badge**: Color-coded (blue/yellow/red) with LIVE warning banner

### Added — Configuration
- **Pydantic v2 config schema** (`config_schema.py`): Type-safe validation with actionable error messages
- **Sample configs**: `config.readonly.json`, `config.paper.json`, `config.live.template.json`
- **`.env.example`**: Documents all supported environment variables
- **Backward-compatible**: Existing `config.json` files validate without changes

### Added — API Contract
- **OpenAPI documentation**: Swagger UI at `/api/docs`, ReDoc at `/api/redoc`
- **Pydantic response models** for all endpoints (`response_models.py`)
- **Standardized error envelope**: `{"ok": false, "error": {"code", "message", "details"}, "request_id"}`
- **`make_error_envelope()`** helper for consistent error formatting

### Added — Observability
- **Correlation ID middleware**: Per-request `X-Correlation-ID` header, propagated via `contextvars`
- **JSON log format**: `LOG_FORMAT=json` for production log aggregation
- **`/api/health/deps`** endpoint: Checks Ollama connectivity and data directory health
- **`CorrelationFilter`**: Injects correlation ID into all log messages

### Added — Docker & CI
- **`Dockerfile`**: Multi-stage build, Python 3.12-slim, safe defaults, built-in healthcheck
- **`docker-compose.yml`**: Backend + optional nginx frontend, persistent data volume
- **GitHub Actions CI**: Lint (ruff) → Test (pytest) → Contract (OpenAPI) → Docker build
- **`ruff.toml`**: Linter configuration with baseline ignores

### Added — Documentation
- `docs/SECURITY_MODES.md` — Trading mode safety system
- `docs/DEPLOYMENT.md` — Docker, Windows scripts, and manual deployment
- `SECURITY.md` — Security policy and vulnerability reporting
- `docs/RELEASE_CHECKLIST.md` — Release readiness checklist
- `docs/adr/ADR-0001` through `ADR-0005` — Architecture decision records
- `docs/PROJECT_AUDIT.md` — Architecture map and risk inventory
- `docs/READINESS_CRITERIA.md` — 55 measurable acceptance criteria
- `docs/ROADMAP.md` — 7-phase milestone plan

### Added — Testing
- 69 unit tests across 4 test files (0.34s total):
  - `test_trading_mode.py` (22 tests): Mode resolution, kill-switch, order blocking, audit logging
  - `test_config_schema.py` (15 tests): Schema validation, sample configs, loader integration
  - `test_api_contract.py` (18 tests): Response models, error envelope, OpenAPI contract
  - `test_observability.py` (14 tests): Correlation IDs, JSON formatter, health/deps model

### Changed
- `server.py`: OpenAPI docs enabled, correlation ID middleware, `/health/deps`, response models
- `error_handler.py`: Standardized error envelope with `error.code` and `error.message`
- `logger.py`: Refactored to use `contextvars` correlation IDs and optional JSON output
- `order_manager.py`: Integrated trading mode gating at `place_order()`

### Security
- Default trading mode is `READ_ONLY` — no accidental live trading
- Error responses no longer leak tracebacks (sanitized with correlation ID)
- CORS is restricted in production mode

---

## [Unreleased] - feature/system-optimization branch

### Added
- ToolCoordinator for intelligent tool selection
- SharedContext for agent communication
- BudgetAllocator for adaptive budget allocation
- Parallel execution structure
- Comprehensive test suite
- Documentation files (Quick Start, Configuration, API Reference, etc.)
- Scripts cleanup and organization

### Changed
- Agent system structure (ready for parallel execution)
- Tool usage optimization
- Budget allocation strategy

### Performance
- 25-33% reduction in tool calls (with caching)
- 25% reduction in execution time (current)
- 50-70% reduction potential (with full parallel execution)

## [1.0.0] - 2025-11-17

### Added
- Initial release
- Multi-agent trading system
- 23 advanced tools
- Real-time market data integration
- Portfolio management
- Order execution
- Frontend dashboard
