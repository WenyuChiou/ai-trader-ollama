# Contributing Guide

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for new features
5. Run verification: `scripts\verify.bat`
6. Commit changes: `git commit -m "Add feature"`
7. Push to branch: `git push origin feature/your-feature`
8. Create Pull Request

## Development Setup

```bash
# Clone and setup
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
pip install pytest ruff httpx slowapi
```

## Quality Gates

All PRs must pass these checks (enforced by CI):

### 1. Unit Tests
```bash
cd tests
python -m pytest unit/ -v --tb=short
```

### 2. Lint (ruff)
```bash
ruff check backend/src/ --select=E,F,W --ignore=E501,E402,F401,W605
```

### 3. API Contract
```bash
python -c "import sys; sys.path.insert(0,'backend'); from src.api.server import app; print(f'OK: {len(app.openapi()[\"paths\"])} endpoints')"
```

### 4. Verification Script
```bash
scripts\verify.bat
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to functions/classes
- Use `ruff` for linting (config in `ruff.toml`)

## Adding a New API Endpoint

1. Add the route in `backend/src/api/server.py`
2. Create a Pydantic response model in `backend/src/api/response_models.py`
3. Add `response_model=` to the endpoint decorator
4. Add a test in `tests/unit/test_api_contract.py`
5. Verify the endpoint appears in OpenAPI: `/api/docs`

## Adding a Config Field

1. Add the field to `backend/src/utils/config_schema.py` (in `TradingConfig`)
2. Update sample configs (`config.readonly.json`, etc.)
3. Add a test in `tests/unit/test_config_schema.py`
4. Document in `docs/CONFIGURATION.md`

## Architecture Decisions

Major changes should be documented as ADRs in `docs/adr/`:
- Use the format: `ADR-NNNN-short-title.md`
- Follow the template: Context → Decision → Alternatives → Consequences

## Testing

- Add tests for new features in `tests/unit/`
- Ensure all tests pass before submitting PR
- Test edge cases and error conditions
- Target: tests should run in < 1 second

## Documentation

- Update `docs/CHANGELOG.md` for user-visible changes
- Update relevant docs files
- Add examples for new features
- Reference ADRs for architectural decisions

## Pull Request Process

1. Ensure all CI checks pass
2. Update documentation
3. Describe changes clearly in PR description
4. Reference related issues
5. Wait for review

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Security Modes](SECURITY_MODES.md)
- [Release Checklist](RELEASE_CHECKLIST.md)
