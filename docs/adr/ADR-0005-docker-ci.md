# ADR-0005: Docker & CI

**Status:** Accepted
**Date:** 2026-02-23
**Author:** A0 Orchestrator + A3 DevOps Lead

## Context

The project had no containerization, no CI pipeline, and no automated quality gates. Deployment relied entirely on Windows `.bat` scripts. There was no way to automatically catch regressions, lint violations, or broken API contracts before merging to main.

## Decision

### 1. Dockerfile (Multi-Stage)

A multi-stage `Dockerfile` builds the backend:
- **Stage 1 (`deps`)**: Installs Python dependencies with build tools (gcc, libxml2-dev)
- **Stage 2 (`runtime`)**: Slim image with only runtime libraries

Key design choices:
- **Python 3.12** (not 3.14, which has Pydantic v1 compatibility warnings)
- **Ollama is external**: Not bundled. Connected via `OLLAMA_HOST` env var (default: `host.docker.internal:11434`)
- **Safe defaults**: `TRADING_MODE=READ_ONLY`, `LOG_FORMAT=json`
- **Built-in healthcheck**: `HEALTHCHECK` instruction pings `/api/health`

### 2. docker-compose.yml

Two services:
- **`backend`**: Main API server with volume for persistent data, config mounted read-only
- **`frontend`** (optional, `--profile with-frontend`): nginx serving static frontend files

Ollama is intentionally NOT a docker-compose service — it runs on the host (often with GPU access) and the backend connects via `OLLAMA_HOST`.

### 3. GitHub Actions CI (`ci.yml`)

Four jobs, running on every push/PR to `main`:

| Job | What it does | Fails build? |
|-----|-------------|-------------|
| `lint` | `ruff check` with baseline ignores | No (exit-zero for now) |
| `test` | `pytest tests/unit/` | Yes |
| `contract` | Verify OpenAPI schema generates | Yes |
| `docker` | Build image, run healthcheck | Yes |

Lint is non-blocking initially (`--exit-zero`) because the existing codebase has many pre-existing issues. This will be switched to blocking after a cleanup pass.

### 4. Ruff Configuration

`ruff.toml` selects `E`, `F`, `W` rules with baseline ignores:
- `E501`: Line too long (many existing)
- `E402`: Module-level import not at top (server.py has path setup)
- `F401`: Unused imports (some are intentional re-exports)
- `W605`: Invalid escape sequences (regex patterns)

### 5. .dockerignore

Excludes `.venv/`, `.git/`, `data/logs/`, `docs/`, `tests/` from the build context to keep images small.

## Alternatives Considered

1. **Include Ollama in docker-compose**: Rejected — Ollama needs GPU access and host-specific configuration. Better as an external service.
2. **GitHub Actions matrix (multiple Python versions)**: Deferred — project targets a single Python version for now.
3. **Strict lint from day one**: Rejected — would require fixing hundreds of existing issues before merging. Baseline ignores + incremental cleanup is more practical.
4. **Docker push to registry**: Deferred — no public deployment target yet.

## Consequences

### Positive
- Every PR gets automated testing, linting, contract verification, and Docker build check.
- Developers can run the full stack with `docker compose up` on any OS.
- Docker healthcheck enables orchestrator-level monitoring.
- `.bat` scripts remain the primary UX for Windows users — Docker is an alternative, not a replacement.

### Negative
- CI requires ~3-5 minutes per run (dependency installation dominates).
- Docker image is relatively large (~1.5GB) due to scientific Python dependencies (numpy, scipy, sentence-transformers).
- Lint is non-blocking initially, which means some issues slip through.

### Migration
- No breaking changes. All existing `.bat` scripts continue to work.
- Docker is purely additive — users who don't use Docker are unaffected.
