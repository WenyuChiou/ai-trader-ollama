# Release Checklist

Use this checklist before tagging a new release.

## Pre-Release Verification

### Safety
- [ ] Default trading mode is `READ_ONLY` (verify in `trading_mode.py`)
- [ ] Kill-switch (`TRADING_DISABLED=1`) blocks all orders (run `test_trading_mode.py`)
- [ ] LIVE mode requires both env vars (run `test_trading_mode.py::TestLiveMode`)
- [ ] Audit logger records all order attempts

### Tests
- [ ] All unit tests pass: `python -m pytest tests/unit/ -v`
- [ ] No regressions in existing functionality
- [ ] Test count matches or exceeds previous release

### Linting
- [ ] New code passes ruff: `ruff check backend/src/ --select=E,F,W --ignore=E501,E402,F401,W605`
- [ ] No new lint warnings introduced

### API Contract
- [ ] OpenAPI schema generates: visit `http://localhost:8000/api/docs`
- [ ] All critical endpoints present in schema
- [ ] Error responses use standardized envelope

### Configuration
- [ ] `config.json` validates against schema (run `test_config_schema.py`)
- [ ] Sample configs validate (`config.readonly.json`, `config.paper.json`)
- [ ] `.env.example` documents all environment variables

### Docker
- [ ] `docker build -t ai-trader-backend .` succeeds
- [ ] `docker compose up` starts and passes healthcheck
- [ ] Container uses `READ_ONLY` mode by default

### Documentation
- [ ] `CHANGELOG.md` updated with all changes
- [ ] New features documented
- [ ] ADRs written for architectural decisions
- [ ] `SECURITY.md` is current

### Windows Scripts
- [ ] `scripts\install.bat` works on clean Windows machine
- [ ] `scripts\quick_start.bat` starts backend and frontend
- [ ] `scripts\verify_environment.bat` reports correct status

## Release Steps

1. Run verification script: `scripts\verify.bat`
2. Update version in `server.py` (`FastAPI(version="x.y.z")`)
3. Update `CHANGELOG.md` with release date
4. Create git tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. Push tag: `git push origin v1.1.0`
6. Create GitHub release with changelog excerpt

## Post-Release

- [ ] Verify CI passes on the tagged commit
- [ ] Verify Docker image builds from the tag
- [ ] Update `docs/ROADMAP.md` with completed phases
