# Roadmap: Professional Upgrade

**Version Target:** v1.0.0
**Start Date:** 2026-02-23

---

## Phase 1 — Recon & Baseline (Complete)

**Status:** DONE
**Deliverables:**
- `docs/PROJECT_AUDIT.md` — Architecture map, critical flows, risks
- `docs/READINESS_CRITERIA.md` — 55 measurable acceptance criteria
- `docs/ROADMAP.md` — This document

**Key Findings:**
- No runtime mode gating (READ_ONLY/PAPER/LIVE)
- No kill-switch or confirmation phrase for live trading
- No config schema validation
- No CI/CD pipeline
- No OpenAPI contract
- ~28 tests with no coverage enforcement

---

## Phase 2 — Safety Backbone

**Priority:** CRITICAL
**Depends on:** Phase 1
**Scope:**
1. Implement `TradingMode` enum: `READ_ONLY`, `PAPER`, `LIVE`
2. Mode resolution: config.json `trading_mode` + env `TRADING_MODE` (env wins)
3. Default = `READ_ONLY`
4. LIVE requires BOTH `mode=LIVE` in config AND `I_UNDERSTAND_LIVE_TRADING=YES` in env
5. Kill-switch: `TRADING_DISABLED=1` blocks all orders regardless of mode
6. Backend enforcement at order_manager.place_order() level
7. Audit log: every order attempt logged with mode, action, result, timestamp
8. Frontend: mode badge in header + LIVE warning banner
9. Tests: ≥8 cases covering all mode × action combinations

**ADR:** `docs/adr/ADR-0001-safety-modes.md`

**Acceptance:** RC-1.1 through RC-1.8

---

## Phase 3 — Configuration & Validation

**Priority:** HIGH
**Depends on:** Phase 2
**Scope:**
1. Pydantic model for config.json schema
2. Startup validation with actionable error messages
3. Sample configs: `config.readonly.json`, `config.paper.json`, `config.live.template.json`
4. `.env.example` with all documented variables
5. Backward compatibility: existing config.json works with deprecation warnings

**ADR:** `docs/adr/ADR-0002-config-schema-validation.md`

**Acceptance:** RC-2.1 through RC-2.6

---

## Phase 4 — API Contract & Shared Types

**Status:** DONE
**Depends on:** Phase 3
**Deliverables:**
- `backend/src/api/response_models.py` — 25+ Pydantic response models
- OpenAPI docs at `/api/docs`, `/api/redoc`, `/api/openapi.json`
- Standardized error envelope: `{"ok": false, "error": {"code", "message", "details"}, "request_id"}`
- 18 contract tests in `tests/unit/test_api_contract.py`
- `docs/adr/ADR-0003-api-contract-governance.md`

---

## Phase 5 — Observability & Health

**Status:** DONE
**Depends on:** Phase 4
**Deliverables:**
- `backend/src/utils/correlation.py` — contextvars-based correlation ID
- `CorrelationIDMiddleware` in server.py with `X-Correlation-ID` header
- JSON log format via `LOG_FORMAT=json` env var
- `/api/health/deps` endpoint (Ollama + data dir checks)
- 14 observability tests in `tests/unit/test_observability.py`
- `docs/adr/ADR-0004-observability.md`

---

## Phase 6 — Docker & CI

**Status:** DONE
**Depends on:** Phase 5
**Deliverables:**
- `Dockerfile` — multi-stage build, Python 3.12-slim, safe defaults
- `docker-compose.yml` — backend + optional nginx frontend
- `.github/workflows/ci.yml` — lint → test → contract → docker build
- `ruff.toml` — linter configuration
- `.dockerignore`
- `docs/adr/ADR-0005-docker-ci.md`

---

## Phase 7 — Docs & Release

**Status:** DONE
**Depends on:** Phase 6
**Deliverables:**
- `docs/SECURITY_MODES.md` — trading mode safety documentation
- `docs/DEPLOYMENT.md` — Docker, Windows scripts, manual deployment
- `SECURITY.md` — security policy and vulnerability reporting
- `docs/RELEASE_CHECKLIST.md` — pre-release checklist
- `scripts/verify.bat` — automated verification script
- Updated: `docs/CONFIGURATION.md`, `docs/CONTRIBUTING.md`, `docs/CHANGELOG.md`
- Version bumped to `1.1.0` in `server.py`

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Mode gating breaks existing automated workflows | Medium | High | Backward-compatible: add mode field, default READ_ONLY, document migration |
| Config validation rejects existing configs | Medium | High | Validate with warnings first, fail only on critical errors |
| CI catches many existing lint/type issues | High | Low | Fix incrementally, use baseline ignores |
| Docker doesn't cover all Windows-specific paths | Medium | Medium | Keep .bat scripts as primary UX, Docker as alternative |
| monitor.html changes break existing bookmarks/workflows | Low | Medium | Minimal frontend changes in safety phase, major refactor deferred |
