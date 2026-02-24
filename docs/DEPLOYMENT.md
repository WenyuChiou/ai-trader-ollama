# Deployment Guide

## Deployment Options

| Method | Best For | Complexity |
|--------|----------|------------|
| Windows `.bat` scripts | Primary UX, local trading | Low |
| Docker Compose | Consistent environments | Medium |
| Manual Python | Custom setups, debugging | Medium |

---

## Option 1: Windows Scripts (Recommended)

The primary deployment method — optimized for the target user base.

### Prerequisites
- Windows 10/11
- Python 3.10+
- Ollama installed and running

### Steps

```cmd
:: 1. Install dependencies
scripts\install.bat

:: 2. Run setup wizard (interactive config)
scripts\setup_wizard.bat

:: 3. Verify everything works
scripts\verify_environment.bat

:: 4. Start the system
scripts\quick_start.bat
```

### Running as Background Service

For long-term automated trading:
```cmd
:: Start backend as a background service
scripts\start_backend_auto.bat

:: Or start full stack (backend + frontend)
scripts\start_full_local.bat
```

See [Long-Term Running Guide](LONG_TERM_RUNNING_GUIDE.md) for scheduled tasks setup.

---

## Option 2: Docker Compose

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)
- Ollama running on the host

### Steps

```bash
# 1. Build and start (backend only)
docker compose up --build

# 2. With frontend (nginx)
docker compose --profile with-frontend up --build

# 3. Stop
docker compose down
```

### Configuration

Set environment variables in a `.env` file or pass them directly:

```bash
# .env
TRADING_MODE=READ_ONLY
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=deepseek-r1
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Persistent Data

Trading data is stored in a Docker volume (`trader-data`). Data persists across container restarts.

```bash
# View volume data
docker volume inspect ai-trader-ollama_trader-data

# Reset data (WARNING: destroys all trading history)
docker compose down -v
```

### Ollama Connection

Ollama runs on your host machine, not inside Docker. The backend connects via:
- **Windows/Mac Docker Desktop**: `http://host.docker.internal:11434` (default)
- **Linux**: `http://172.17.0.1:11434` or use `--network=host`

---

## Option 3: Manual Python

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start backend
cd backend
uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# 4. Open frontend
# Serve frontend/ directory with any static file server on port 8080
python -m http.server 8080 -d ../frontend
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADING_MODE` | `READ_ONLY` | `READ_ONLY`, `PAPER`, or `LIVE` |
| `TRADING_DISABLED` | `0` | Set to `1` to block all orders (kill-switch) |
| `I_UNDERSTAND_LIVE_TRADING` | (not set) | Must be `YES` for LIVE mode |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Default LLM model |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `text` | `text` or `json` |
| `ADMIN_TOKEN` | (not set) | Admin API authentication token |
| `ENVIRONMENT` | `development` | `development` or `production` |

---

## Health Checks

### API Health
```bash
curl http://localhost:8000/api/health
# {"status":"ok","trading_mode":"READ_ONLY","trading_disabled":false,"version":"1.0.0"}
```

### Dependency Health
```bash
curl http://localhost:8000/api/health/deps
# {"status":"ok","dependencies":{"ollama":{"status":"ok","models_available":5},"data_dir":{"status":"ok"}}}
```

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

---

## See Also

- [Security Modes](SECURITY_MODES.md) — Trading mode safety system
- [Configuration Guide](CONFIGURATION.md) — All config options
- [Quick Start Guide](QUICK_START.md) — Fastest path to running
- [Troubleshooting](TROUBLESHOOTING.md) — Common issues
