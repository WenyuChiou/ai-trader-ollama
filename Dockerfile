# Dockerfile — AI Trader Backend
# Multi-stage build: deps → runtime
# Ollama is an EXTERNAL dependency — not bundled in this image.
#
# Build:  docker build -t ai-trader-backend .
# Run:    docker run -p 8000:8000 -e OLLAMA_HOST=http://host.docker.internal:11434 ai-trader-backend

# ---------------------------------------------------------------------------
# Stage 1: Install Python dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS deps

WORKDIR /app

# System deps for numpy/scipy/lxml wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir httpx pytest

# ---------------------------------------------------------------------------
# Stage 2: Runtime image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# System runtime deps (libxml2 for lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY backend/ ./backend/

# Copy config files
COPY backend/config/ ./backend/config/

# Create data directory
RUN mkdir -p /app/data/logs

# Environment defaults — safe by design
ENV TRADING_MODE=READ_ONLY \
    TRADING_DISABLED=0 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

EXPOSE 8000

# Health check — uses the /api/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run uvicorn
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
