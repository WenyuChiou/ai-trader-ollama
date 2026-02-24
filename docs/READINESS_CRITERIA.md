# Readiness Criteria

**Date:** 2026-02-23
**Purpose:** Measurable acceptance criteria for the professional upgrade of ai-trader-ollama.
**Verdict:** All criteria must pass before the project is considered release-ready.

---

## RC-1: Safety Modes

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 1.1 | Default runtime mode is `READ_ONLY` | Start server with no env/config overrides → `/api/health` reports `mode: "READ_ONLY"` | [ ] |
| 1.2 | `READ_ONLY` mode blocks all order placement | POST `/api/trading/execute-trade` in READ_ONLY → returns 403 with `"mode_violation"` error | [ ] |
| 1.3 | `PAPER` mode logs orders but never calls real broker | Execute trade in PAPER → orders appear in audit log with `mode: "PAPER"`, no external calls | [ ] |
| 1.4 | `LIVE` requires config `mode="LIVE"` AND env `I_UNDERSTAND_LIVE_TRADING=YES` | Set config to LIVE but omit env → returns 403. Set env but config is PAPER → returns 403 | [ ] |
| 1.5 | Kill-switch `TRADING_DISABLED=1` blocks all orders regardless of mode | Set LIVE + confirmation + TRADING_DISABLED=1 → returns 403 with `"trading_disabled"` | [ ] |
| 1.6 | Every order attempt (allowed or blocked) produces audit log entry | Check `data/logs/audit_orders.jsonl` after any trade attempt → entry exists with timestamp, mode, action, result | [ ] |
| 1.7 | UI displays current mode prominently | Frontend shows mode badge (green=READ_ONLY, yellow=PAPER, red=LIVE with warning banner) | [ ] |
| 1.8 | Tests cover all mode transitions | `pytest tests/ -k mode` passes: ≥8 test cases covering all mode × action combinations | [ ] |

---

## RC-2: Configuration & Validation

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 2.1 | Config schema is formally defined | Pydantic model or JSON Schema file exists and is imported at startup | [ ] |
| 2.2 | Invalid config fails fast with actionable error | Set `"initial_cash": "not_a_number"` → startup fails with message naming the field and expected type | [ ] |
| 2.3 | Missing required fields fail fast | Remove `"universe"` from config → startup fails with message naming the missing field | [ ] |
| 2.4 | Sample configs exist per mode | Files exist: `config.readonly.json`, `config.paper.json`, `config.live.template.json` | [ ] |
| 2.5 | `.env.example` exists and documents all vars | `.env.example` lists: ADMIN_SECRET, ENVIRONMENT, TRADING_MODE, I_UNDERSTAND_LIVE_TRADING, TRADING_DISABLED, OLLAMA_HOST, LOG_LEVEL, etc. | [ ] |
| 2.6 | No secrets committed to git | `git log --all -p -- '*.env' '*.secret'` returns nothing. `.gitignore` covers `.env*` | [ ] |

---

## RC-3: API Contract

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 3.1 | OpenAPI spec exists | `docs/openapi.yaml` or auto-generated at `/api/docs` (FastAPI Swagger) | [ ] |
| 3.2 | All endpoints return consistent error envelope | Every 4xx/5xx response has shape: `{"error": {"code": str, "message": str, "details": any}}` | [ ] |
| 3.3 | Response schemas match spec | CI contract check compares actual responses against OpenAPI spec → passes | [ ] |
| 3.4 | Frontend uses typed API responses | Frontend code references documented field names, not magic strings | [ ] |

---

## RC-4: Observability

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 4.1 | Structured JSON logs | `LOG_FORMAT=json` → log output is valid JSON with keys: `timestamp`, `level`, `message`, `correlation_id` | [ ] |
| 4.2 | Correlation IDs thread through trading cycle | A single trade execution produces logs sharing one `correlation_id` across all 5 stages | [ ] |
| 4.3 | `/health` returns basic status | GET `/api/health` → `{"status": "ok", "mode": "READ_ONLY", "version": "x.y.z"}` | [ ] |
| 4.4 | `/health/deps` checks Ollama | GET `/api/health/deps` → `{"ollama": {"status": "ok"/"unavailable", "model": "deepseek-r1"}}` | [ ] |
| 4.5 | Errors surfaced to frontend with stable schema | Frontend receives errors as `{"error": {"code": str, "message": str}}` | [ ] |

---

## RC-5: Testing

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 5.1 | Unit tests for config validation | `pytest tests/ -k config` → ≥5 tests pass | [ ] |
| 5.2 | Unit tests for mode gating | `pytest tests/ -k mode` → ≥8 tests pass | [ ] |
| 5.3 | Integration tests with mocked Ollama | `pytest tests/integration/ -k ollama` → ≥3 tests pass without Ollama running | [ ] |
| 5.4 | Mock broker exists and is used in tests | `tests/mocks/mock_broker.py` exists. Tests never call real order execution. | [ ] |
| 5.5 | Test coverage ≥60% for backend/src/ | `pytest --cov=backend/src --cov-report=term` → ≥60% | [ ] |
| 5.6 | All tests pass | `pytest tests/ -v` → 0 failures | [ ] |
| 5.7 | E2E smoke test passes | Frontend loads, connects to backend in mock mode, displays portfolio → pass | [ ] |

---

## RC-6: Code Quality

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 6.1 | Linter passes (ruff) | `ruff check backend/src/` → 0 errors | [ ] |
| 6.2 | Type checker passes | `mypy backend/src/ --ignore-missing-imports` or `pyright` → 0 errors (or ≤10 known exclusions) | [ ] |
| 6.3 | CI runs on every push | `.github/workflows/ci.yml` exists and runs: lint, typecheck, test | [ ] |
| 6.4 | CI is green on main branch | Latest CI run on main → all jobs pass | [ ] |

---

## RC-7: Dependency & Security

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 7.1 | Dependencies pinned or constrained | `requirements.txt` uses `>=x.y,<z` or `==x.y.z` for critical deps | [ ] |
| 7.2 | No known critical CVEs | `pip audit` or `safety check` → 0 critical vulnerabilities | [ ] |
| 7.3 | Supported Python versions documented | README states supported Python version(s) (e.g., 3.10+) | [ ] |
| 7.4 | SECURITY.md exists | `SECURITY.md` documents: safe defaults, threat model summary, reporting process | [ ] |

---

## RC-8: Documentation

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 8.1 | Quick Start works end-to-end | New user follows docs/QUICK_START.md on Windows → system running in ≤10 min | [ ] |
| 8.2 | Config docs match actual config | Every key in config.json is documented in docs/CONFIGURATION.md | [ ] |
| 8.3 | Security modes documented | docs/SECURITY_MODES.md explains READ_ONLY, PAPER, LIVE with examples | [ ] |
| 8.4 | Troubleshooting covers common issues | docs/TROUBLESHOOTING.md has ≥10 entries for known issues | [ ] |
| 8.5 | CONTRIBUTING.md exists | Describes: dev setup, code style, testing, PR process | [ ] |
| 8.6 | Scripts documentation accurate | install.bat, setup_wizard.bat, quick_start.bat behavior matches docs | [ ] |

---

## RC-9: Docker & Reproducibility

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 9.1 | Docker compose works | `docker compose up` starts backend (+ optional frontend) | [ ] |
| 9.2 | Backend starts in READ_ONLY by default in Docker | Container starts → `/api/health` reports `mode: "READ_ONLY"` | [ ] |
| 9.3 | Ollama is external dependency | Docker compose expects Ollama at configurable `OLLAMA_HOST`, not bundled | [ ] |

---

## RC-10: Release Engineering

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 10.1 | CHANGELOG.md exists | Documents all notable changes per version | [ ] |
| 10.2 | Version is defined somewhere | `__version__` in Python code or `version` in config | [ ] |
| 10.3 | Release checklist exists | docs/RELEASE_CHECKLIST.md with steps: test → tag → changelog → publish | [ ] |
| 10.4 | Verification script passes | `scripts/verify.bat` runs: config validation + tests + contract check → all pass | [ ] |

---

## RC-11: Windows UX Preserved

| # | Criterion | Measurement | Pass/Fail |
|---|-----------|-------------|-----------|
| 11.1 | `scripts/install.bat` works | Run on fresh Windows with Python + Ollama → venv created, deps installed, data dirs exist | [ ] |
| 11.2 | `scripts/setup_wizard.bat` works | Interactive wizard completes → .env and config.json are valid | [ ] |
| 11.3 | `scripts/quick_start.bat` works | Backend starts, frontend opens in browser, portfolio displays | [ ] |
| 11.4 | No breaking changes to existing users | Existing config.json from current version still works (with deprecation warnings if needed) | [ ] |

---

## Summary

| Category | Criteria Count | Must Pass |
|----------|---------------|-----------|
| Safety Modes | 8 | All |
| Configuration | 6 | All |
| API Contract | 4 | All |
| Observability | 5 | All |
| Testing | 7 | All |
| Code Quality | 4 | All |
| Dependencies | 4 | All |
| Documentation | 6 | All |
| Docker | 3 | All |
| Release | 4 | All |
| Windows UX | 4 | All |
| **Total** | **55** | **55** |
