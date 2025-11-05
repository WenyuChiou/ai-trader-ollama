# src/llm/ollama_client.py
from __future__ import annotations

import os
import time
import subprocess
from dataclasses import dataclass
from typing import Any, Optional, List
from pathlib import Path  # 统一在文件顶部导入，避免函数内部重复导入导致的作用域问题

import requests
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

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


# ---------------------------
# Health & model helpers
# ---------------------------
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
        except Exception as e:  # pragma: no cover
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


# --- 原函式上方不動，覆蓋 get_llm 內容 ---
def get_llm(
    model: Optional[str] = None,
    *,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    num_ctx: Optional[int] = None,
    keep_alive: Optional[str] = "10m",   # 預設保溫，降低 unload
    auto_pull: Optional[bool] = None,
    streaming: bool = False,             # ← 新增：預設關閉串流
) -> ChatOllama:
    """
    Return a ChatOllama instance with health checks and optional auto-pull.
    
    Configuration priority:
    1. Function parameters (highest)
    2. Environment variables (OLLAMA_HOST, OLLAMA_MODEL)
    3. config.json "llm" section
    4. Default values (lowest)
    """
    # Load config.json if available
    llm_config_from_file = {}
    try:
        # Path 已经在文件顶部导入，不需要重复导入
        import json
        config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
                llm_config_from_file = config.get("llm", {})
    except Exception:
        pass  # If config loading fails, use defaults
    
    # Priority: parameter > env var > config.json > default
    final_model = (
        model or 
        os.getenv(ENV_MODEL) or 
        llm_config_from_file.get("default_model") or 
        "llama3.1"
    )
    
    final_base_url = (
        base_url or 
        os.getenv(ENV_HOST) or 
        llm_config_from_file.get("ollama_host") or 
        DEFAULT_HOST
    )
    
    final_auto_pull = (
        auto_pull if auto_pull is not None else
        llm_config_from_file.get("auto_pull", True)
    )
    
    settings = OllamaSettings(
        model=final_model,
        base_url=final_base_url,
        temperature=temperature if temperature is not None else 0.2,
        num_ctx=num_ctx,
        keep_alive=keep_alive,
        auto_pull=final_auto_pull,
        timeout_s=float(llm_config_from_file.get("timeout_seconds", 8.0)),
    )

    ensure_ollama_ready(settings)

    kwargs: dict[str, Any] = {
        "model": settings.model,
        "temperature": settings.temperature,
        "base_url": settings.base_url,
        "streaming": streaming,          # ← 傳入 ChatOllama
    }
    if settings.num_ctx is not None:
        kwargs["num_ctx"] = settings.num_ctx
    if settings.keep_alive is not None:
        kwargs["keep_alive"] = settings.keep_alive

    return ChatOllama(**kwargs)



# ---------------------------
# Unified client for BaseAgent (stable: via ChatOllama)
# ---------------------------
class OllamaClient:
    """
    Thin wrapper around LangChain ChatOllama exposing invoke() expected by BaseAgent.
    """

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        base_url: Optional[str] = None,
        num_ctx: Optional[int] = None,
        keep_alive: Optional[str] = "10m",
        auto_pull: bool = True,
    ):
        # 一律用非串流，最穩
        self.chat = get_llm(
            model=model,
            temperature=temperature,
            base_url=base_url,
            num_ctx=num_ctx,
            keep_alive=keep_alive,
            auto_pull=auto_pull,
            streaming=False,   # ← 關鍵
        )

# --- 在 OllamaClient.invoke 中加入重試邏輯 ---
    def invoke(
        self,
        *,
        system: str,
        user: Optional[str],
        model: str,
        temperature: float = 0.2,
        tools: Optional[list] = None,
        stream: bool = False,   # 參數留著，但實際仍非串流
    ) -> str:
        # 允許動態覆寫溫度
        try:
            if hasattr(self.chat, "temperature"):
                self.chat.temperature = temperature
        except Exception:
            pass

        msgs: List = []
        if system:
            msgs.append(SystemMessage(content=system))
        if user:
            msgs.append(HumanMessage(content=user))

        # 一次性呼叫 + 空回覆/載入狀態的穩健重試
        for attempt in (1, 2):
            try:
                print(f"[DEBUG] Sending to model: {model} ({len(system)} chars)")
                ai = self.chat.invoke(msgs)
                content = (ai.content if isinstance(ai, AIMessage) else str(ai or "")).strip()
                if content:
                    return content
                # 空字串也觸發重試
                if attempt == 1:
                    time.sleep(0.5)
                    continue
                return ""  # 第二次還是空，就回空字串讓上層韌性解析處理
            except ValueError as e:
                # LangChain 在遇到空串流時會丟這個錯：No data received from Ollama stream
                if "No data received from Ollama stream" in str(e) and attempt == 1:
                    time.sleep(0.5)
                    continue
                raise  # 其它錯誤直接拋出


    @staticmethod
    def extract_json(text: str) -> str:
        s = text.strip()
        if s.startswith("```"):
            s = s.strip("`")
            idx = s.find("\n")
            if idx != -1:
                s = s[idx+1:]
        first = s.find("{")
        last = s.rfind("}")
        if first != -1 and last != -1 and last > first:
            return s[first:last+1]
        return s
