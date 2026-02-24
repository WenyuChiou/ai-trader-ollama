# ADR-0002: Configuration Schema Validation

**Status:** Accepted
**Date:** 2026-02-23
**Author:** A0 Orchestrator + A2 Backend Lead

## Context

The config loader (`config_loader.py`) previously used `dict.get()` with defaults for all configuration values. Invalid or mistyped config values were silently accepted, leading to subtle runtime bugs (e.g., `initial_cash: "ten thousand"` would quietly fail during arithmetic).

## Decision

Introduce a Pydantic v2 schema (`config_schema.py`) as the single source of truth for `config.json` structure:

- **`TradingConfig`**: Root model with all fields, types, constraints, and defaults.
- **Sub-models**: `LLMConfig`, `RAGConfig`, `BudgetAllocation`, `DateRange`.
- **`validate_config(raw_dict)`**: Strips `_`-prefixed comment keys, then validates.
- **`validate_config_file(path)`**: Loads JSON and validates in one call.
- **`load_config(..., validate=True)`**: Opt-in validation in the existing loader (backward-compatible).

### Sample Configs
Three sample configs are provided per trading mode:
- `config.readonly.json` — safe default for demos
- `config.paper.json` — simulated trading
- `config.live.template.json` — real trading template with recommended position limits

### Environment Variables
`.env.example` documents all supported environment variables including the new `TRADING_MODE`, `I_UNDERSTAND_LIVE_TRADING`, and `TRADING_DISABLED`.

## Alternatives Considered

1. **JSON Schema (jsonschema library)**: More universal but less ergonomic in Python. Pydantic already in requirements.txt and provides better error messages.
2. **No validation**: Status quo. Rejected due to silent failures.
3. **Strict validation at startup (fail-fast)**: Considered but deferred — `validate=True` is opt-in for now to avoid breaking existing deployments. Will become default in Phase 7.

## Consequences

### Positive
- Actionable error messages name the exact field and expected type.
- Sample configs serve as documentation and starting points.
- `.env.example` prevents users from guessing variable names.
- Comment keys (`_comment`, `_example_*`) are formally stripped, not passed to validation.

### Negative
- Adding a new config field requires updating both `config_schema.py` and the sample configs.

### Migration
- Existing `config.json` files validate successfully (tested against the real config in repo).
- `load_config()` without `validate=True` behaves identically to before (backward-compatible).
- Users who want validation can pass `validate=True` or call `validate_config_file()` directly.
