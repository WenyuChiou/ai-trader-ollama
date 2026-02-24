# ADR-0003: API Contract Governance

**Status:** Accepted
**Date:** 2026-02-23
**Author:** A0 Orchestrator + A2 Backend Lead

## Context

The API lacked formal contract documentation. Endpoints returned ad-hoc JSON shapes — some with `"ok": true`, some with raw dicts, and errors used inconsistent formats (some exposed tracebacks, some returned flat strings). This made frontend integration fragile and made it impossible to detect breaking changes automatically.

## Decision

### 1. Enable OpenAPI Documentation

FastAPI's built-in OpenAPI generation is enabled at:
- `/api/docs` — Swagger UI (interactive)
- `/api/redoc` — ReDoc (reference)
- `/api/openapi.json` — Raw OpenAPI 3.x JSON schema

### 2. Standardized Error Envelope

All error responses use this shape:

```json
{
  "ok": false,
  "error": {
    "code": "mode_violation",
    "message": "Cannot execute trades in READ_ONLY mode.",
    "details": null
  },
  "request_id": "a1b2c3d4"
}
```

- `error.code`: Machine-readable string (snake_case). Frontend can switch on this.
- `error.message`: Human-readable explanation.
- `error.details`: Optional object with extra context (validation errors, etc.).
- `request_id`: Short UUID for log correlation.

The `make_error_envelope()` helper in `error_handler.py` enforces this format.

### 3. Pydantic Response Models

`response_models.py` defines Pydantic v2 models for all API responses. Key models:
- `HealthResponse`, `TradingModeResponse`
- `ExecuteTradeResponse`, `RecentTradesResponse`, `PendingOrdersResponse`
- `PortfolioRealtimeResponse`, `EquityHistoryResponse`
- `ConversationsResponse`
- `MarketOpenResponse`, `VixTermResponse`, `FearGreedResponse`
- `SystemInfoResponse`, `SystemInitResponse`
- `ErrorResponse` (wraps `ErrorDetail`)

Response models are attached via `response_model=` on endpoint decorators where feasible. Endpoints that return complex dynamic payloads (e.g., conversations with deeply nested tool results) use `Dict[str, Any]` fields to preserve flexibility while still documenting the top-level shape.

### 4. Shared Types Strategy

The frontend (`monitor.html`) is vanilla JS — no TypeScript types to maintain. The OpenAPI JSON schema at `/api/openapi.json` serves as the single source of truth. If TypeScript types are needed in the future, they can be auto-generated from the OpenAPI spec using `openapi-typescript` or similar tools.

### 5. Contract Snapshot Tests

`tests/unit/test_api_contract.py` includes:
- Response model serialization tests
- Error envelope shape validation
- OpenAPI schema generation test (verifies all critical endpoints are present)
- Schema JSON serializability check (foundation for CI snapshot diffing)

## Alternatives Considered

1. **Generate TypeScript types from Pydantic**: Considered `pydantic-to-typescript`. Rejected because the frontend is vanilla JS, and this adds a build step with no consumer.
2. **JSON Schema validation library**: Unnecessary — Pydantic models already produce JSON Schema via OpenAPI.
3. **GraphQL**: Over-engineered for this use case. REST + OpenAPI is sufficient.
4. **Strict response_model on every endpoint**: Some endpoints return deeply dynamic data (tool results, conversation entries) that would require overly complex models. We use `Dict[str, Any]` for these fields.

## Consequences

### Positive
- Developers can explore the API at `/api/docs` without reading code.
- Error handling is consistent — frontend can reliably parse `error.code`.
- OpenAPI schema enables future auto-generation of client SDKs or TypeScript types.
- Contract tests catch accidental endpoint removal or rename.

### Negative
- Adding a new endpoint requires creating a response model in `response_models.py`.
- Deeply nested dynamic payloads (tool_results_by_category) are typed as `Dict[str, Any]`, which provides less type safety.

### Migration
- Existing frontend code is backward-compatible: `ok`, error codes like `mode_violation` and `trading_disabled` are preserved.
- The error envelope change adds `error.code` and `error.message` as nested fields. Old code checking `response.error` as a string should be updated to check `response.error.message` or `response.error.code`.
