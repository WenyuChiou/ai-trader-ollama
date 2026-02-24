# ADR-0004: Observability

**Status:** Accepted
**Date:** 2026-02-23
**Author:** A0 Orchestrator + A2 Backend Lead

## Context

The system relied on `print()` statements (70+ in `trading_cycle.py` alone) for operational visibility. Log output was unstructured plain text, making it impossible to filter, aggregate, or correlate across a single request or trading cycle. The health endpoint (`/api/health`) only reported service status — it did not check whether external dependencies (Ollama) were actually reachable.

## Decision

### 1. Correlation ID via `contextvars`

`src/utils/correlation.py` provides:
- `new_correlation_id()` — generates an 8-char hex ID and stores it in a `ContextVar`
- `get_correlation_id()` / `set_correlation_id()` — read/write from any async or sync code

A `CorrelationIDMiddleware` in `server.py`:
1. Reads `X-Correlation-ID` header (if present) or generates a new ID
2. Stores it in the context variable
3. Returns it in the response `X-Correlation-ID` header

All log messages automatically include the correlation ID via `CorrelationFilter`.

### 2. JSON Log Format

`LOG_FORMAT=json` environment variable switches all log output to single-line JSON:

```json
{"ts": "2026-02-23T15:30:00+00:00", "level": "INFO", "logger": "ai_trader", "cid": "a1b2c3d4", "msg": "Trading cycle started"}
```

Default remains `text` for human readability during development. JSON format is intended for production log aggregation (CloudWatch, Datadog, ELK, etc.).

### 3. `/api/health/deps` Endpoint

New endpoint that checks external dependency health:

- **Ollama**: Async HTTP call to `{ollama_host}/api/tags` with 5s timeout. Returns status, URL, and model count.
- **Data directory**: Verifies the logs directory exists and is writable.

Response shape:
```json
{
  "status": "ok",
  "dependencies": {
    "ollama": {"status": "ok", "url": "http://localhost:11434", "models_available": 5},
    "data_dir": {"status": "ok", "path": "/data/logs"}
  }
}
```

`status` is `"ok"` only when all dependencies are healthy; otherwise `"degraded"`.

### 4. Unified Logger Update

`logger.py` was refactored:
- Replaced `TraceIDFilter` with `CorrelationFilter` (reads from `contextvars`)
- Added `JSONFormatter` class for structured output
- `setup_logger()` accepts `log_format` parameter (or reads `LOG_FORMAT` env)
- Backward-compatible: `trace_id` attribute is aliased to `cid`

## Alternatives Considered

1. **OpenTelemetry**: Full distributed tracing. Deferred — too heavy for a single-process application. Can be added later using the correlation ID as a trace parent.
2. **structlog**: Popular structured logging library. Rejected because the existing `logging` module is sufficient and avoids a new dependency.
3. **Migrate all print() to logger**: Desirable but out of scope — touching 70+ print statements across `trading_cycle.py` would be a large, risky change. Deferred to a future cleanup phase.

## Consequences

### Positive
- Any log line can be traced back to a specific API request or trading cycle via the correlation ID.
- JSON logs are machine-parseable for log aggregation services.
- `/api/health/deps` enables monitoring dashboards to detect Ollama connectivity issues before users encounter them.
- The `X-Correlation-ID` response header lets frontend or scripts correlate errors with backend logs.

### Negative
- `print()` statements in existing code do not include correlation IDs — they need incremental migration.
- JSON log lines are harder to read in a terminal without `jq` or similar tooling.

### Migration
- Existing logger usage is backward-compatible (`trace_id` attribute still works).
- Default format is `text` — no change for existing deployments.
- `/api/health/deps` is a new endpoint with no breaking changes.
