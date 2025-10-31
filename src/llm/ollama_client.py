from __future__ import annotations

import os
import time
import subprocess
from dataclasses import dataclass
from typing import Any, Optional

import requests
from langchain_ollama import ChatOllama


DEFAULT_HOST = "http://localhost:11434"
ENV_HOST = "OLLAMA_HOST"
ENV_MODEL = "OLLAMA_MODEL"


class OllamaInitError(RuntimeError):
    """Raised when Ollama server or model initialization fails with guidance text."""


@dataclass
class OllamaSettings:
    model: str = os.getenv(ENV_MODEL, "llama3.1")
    base_url: str = os.getenv(ENV_HOST, DEFAULT_HOST)
    temperature: float = 0.2
    num_ctx: Optional[int] = None         # Context window tokens (model-dependent)
    keep_alive: Optional[str] = None      # e.g., "5m", "30m", "0" (no keep alive)
    timeout_s: float = 8.0                # HTTP timeout for health/model checks
    auto_pull: bool = True                # Try to `ollama pull <model>` if missing
    max_retries: int = 2                  # Health/model-list retries


def _http_get(url: str, timeout: float) -> requests.Response:
    return requests.get(url, timeout=timeout)


def _server_version(base_url: str, timeout: float, retries: int) -> str:
    """Return server version string or raise OllamaInitError."""
    last_err: Optional[Exception] = None
    url = f"{base_url.rstrip('/')}/api/version"
    for _ in range(max(1, retries + 1)):
        try:
            r = _http_get(url, timeout)
            if r.ok:
                data = r.json()
                return data.get("version", "unknown")
            last_err = RuntimeError(f"HTTP {r.status_code}: {r.text[:240]}")
        except Exception as e:  # pragma: no cover - network env dependent
            last_err = e
        time.sleep(0.6)
    raise OllamaInitError(
        f"Cannot reach Ollama server at {base_url}.\n"
        f"Tip: ensure Ollama is running (e.g., start the app or run `ollama serve`).\n"
        f"Original error: {last_err}"
    )


def _list_models(base_url: str, timeout: float, retries: int) -> list[dict[str, Any]]:
    """List locally available models via /api/tags."""
    url = f"{base_url.rstrip('/')}/api/tags"
    last_err: Optional[Exception] = None
    for _ in range(max(1, retries + 1)):
        try:
            r = _http_get(url, timeout)
            if r.ok:
                data = r.json() or {}
                return data.get("models", [])
            last_err = RuntimeError(f"HTTP {r.status_code}: {r.text[:240]}")
        except Exception as e:
            last_err = e
        time.sleep(0.4)
    raise OllamaInitError(
        f"Failed to list models from {base_url}/api/tags.\n"
        f"Original error: {last_err}"
    )


def _has_model(models: list[dict[str, Any]], name: str) -> bool:
    name = (name or "").strip().lower()
    for m in models or []:
        if (m.get("name") or "").split(":")[0].lower() == name.split(":")[0].lower():
            return True
    return False


def _pull_model(name: str) -> None:
    """Attempt `ollama pull <name>` via subprocess for portability."""
    try:
        proc = subprocess.run(
            ["ollama", "pull", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=60 * 30,  # up to 30 min; large models can be big
        )
        if proc.returncode != 0:
            raise OllamaInitError(
                "Failed to pull model via `ollama pull`.\n"
                f"Command: ollama pull {name}\n"
                f"stderr: {proc.stderr[:400]}"
            )
    except FileNotFoundError as e:
        raise OllamaInitError(
            "The `ollama` CLI was not found in PATH.\n"
            "Install Ollama from https://ollama.com/ and ensure the CLI is available.\n"
            f"Original error: {e}"
        )


def ensure_ollama_ready(settings: OllamaSettings) -> None:
    """Health check server and ensure model exists (auto-pull if allowed)."""
    # 1) Server reachable
    _server_version(settings.base_url, settings.timeout_s, settings.max_retries)

    # 2) Model exists locally
    models = _list_models(settings.base_url, settings.timeout_s, settings.max_retries)
    if not _has_model(models, settings.model):
        if not settings.auto_pull:
            raise OllamaInitError(
                f"Model '{settings.model}' not found locally on Ollama ({settings.base_url}).\n"
                "Set auto_pull=True or run manually:  ollama pull <model>"
            )
        _pull_model(settings.model)  # may take a while
        # Re-validate model exists
        models = _list_models(settings.base_url, settings.timeout_s, settings.max_retries)
        if not _has_model(models, settings.model):
            raise OllamaInitError(
                f"Model '{settings.model}' is still not available after pull. "
                "Please verify the model name and try again."
            )


def get_llm(
    model: Optional[str] = None,
    *,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    num_ctx: Optional[int] = None,
    keep_alive: Optional[str] = None,
    auto_pull: bool = True,
) -> ChatOllama:
    """
    Create a robust ChatOllama instance with health checks and optional auto-pull.

    Parameters
    ----------
    model : str | None
        Model name (e.g., 'llama3.1', 'qwen2.5:7b'). Defaults to env OLLAMA_MODEL or 'llama3.1'.
    temperature : float | None
        Decoding temperature. Defaults to 0.2.
    base_url : str | None
        Ollama server URL. Defaults to env OLLAMA_HOST or 'http://127.0.0.1:11434'.
    num_ctx : int | None
        Context window size (tokens). Forwarded to ChatOllama if provided.
    keep_alive : str | None
        Keep-alive duration string, e.g., '5m'. Forwarded to ChatOllama if provided.
    auto_pull : bool
        If True, attempt to `ollama pull <model>` when missing.

    Raises
    ------
    OllamaInitError
        If the server is unreachable or the model is unavailable (and cannot be pulled).
    """
    settings = OllamaSettings(
        model=model or os.getenv(ENV_MODEL, "llama3.1"),
        base_url=base_url or os.getenv(ENV_HOST, DEFAULT_HOST),
        temperature=temperature if temperature is not None else 0.2,
        num_ctx=num_ctx,
        keep_alive=keep_alive,
        auto_pull=auto_pull,
    )

    ensure_ollama_ready(settings)

    # Build kwargs for ChatOllama carefully; only pass supported extras when set.
    kwargs: dict[str, Any] = {
        "model": settings.model,
        "temperature": settings.temperature,
        "base_url": settings.base_url,
    }
    if settings.num_ctx is not None:
        kwargs["num_ctx"] = settings.num_ctx
    if settings.keep_alive is not None:
        kwargs["keep_alive"] = settings.keep_alive

    return ChatOllama(**kwargs)