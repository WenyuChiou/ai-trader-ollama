# Phase 1 Recon Summary

## Architecture
- Backend: FastAPI (Python) on port 8000, uvicorn
- Frontend: Vanilla HTML/CSS/JS (no build), served via python -m http.server 8080
- LLM: Ollama local (deepseek-r1 default, langchain-ollama)
- Data: JSONL files in data/logs/
- Config: config.json + agents.yaml + .env

## Critical Findings
1. NO mode gating (READ_ONLY/PAPER/LIVE) exists
2. NO kill-switch for trading
3. Orders placed directly with no env confirmation
4. Admin auth exists but dev mode bypasses it
5. No CI/CD at all
6. No OpenAPI spec
7. No config schema validation (just dict.get with defaults)
8. No structured logging (basic rotating file handler)
9. Frontend has basic read-only mode by IP detection only
10. 15,598-line monolithic monitor.html
11. Shared types exist (shared/types/) but not used
12. ~28 tests, no coverage enforcement
