# src/utils/config_schema.py
"""
Pydantic schema for config.json — single source of truth for configuration.

Validates all config fields at startup with actionable error messages.
Unknown keys are silently ignored (forward-compatible).
Keys starting with '_' are treated as comments and ignored.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class LLMConfig(BaseModel):
    """LLM / Ollama configuration."""
    default_model: str = Field("deepseek-r1", description="Ollama model name")
    ollama_host: str = Field("http://localhost:11434", description="Ollama server URL")
    auto_pull: bool = Field(True, description="Auto-download model if missing")
    timeout_seconds: float = Field(8.0, ge=1.0, le=600.0, description="LLM request timeout in seconds")

    model_config = {"extra": "ignore"}


class RAGConfig(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration."""
    short_term_days: int = Field(7, ge=1, le=365)
    medium_term_days: int = Field(30, ge=1, le=365)
    long_term_days: int = Field(90, ge=1, le=3650)
    embedding_model: str = Field("nomic-embed-text")
    embedding_dimension: int = Field(384, ge=32, le=4096)
    use_ollama_embedding: bool = Field(True)
    fallback_embedding_model: str = Field("all-MiniLM-L6-v2")
    vector_search_top_k: int = Field(10, ge=1, le=100)
    enable_semantic_search: bool = Field(True)
    enable_cache: bool = Field(True)
    cache_size: int = Field(100, ge=0, le=10000)

    model_config = {"extra": "ignore"}


class BudgetAllocation(BaseModel):
    """Tool budget allocation per analyst type."""
    market: int = Field(3, ge=0, le=50)
    technical: int = Field(4, ge=0, le=50)
    sentiment: int = Field(4, ge=0, le=50)

    model_config = {"extra": "ignore"}


class DateRange(BaseModel):
    """Date range for historical simulation."""
    start: str = Field("2024-01-02", description="Start date YYYY-MM-DD")
    end: str = Field("2024-01-31", description="End date YYYY-MM-DD")

    model_config = {"extra": "ignore"}


class TradingConfig(BaseModel):
    """
    Root configuration schema for config.json.

    All fields have sensible defaults so that a minimal config (even {}) is valid.
    """
    # --- Trading mode (Phase 2 safety) ---
    trading_mode: str = Field(
        "READ_ONLY",
        description="Runtime mode: READ_ONLY (default, safe), PAPER, or LIVE",
    )

    # --- Universe ---
    universe_source: str = Field("custom", description="'custom' or 'sp500'")
    universe_limit: int = Field(100, ge=1, le=1000)
    universe: List[str] = Field(
        default_factory=lambda: ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"],
        description="List of stock ticker symbols",
    )

    # --- Portfolio ---
    initial_cash: float = Field(10000.0, gt=0, description="Starting cash in USD")

    # --- Position limits ---
    position_limit_mode: str = Field(
        "auto",
        description="'auto' (LLM decides) or 'configured' (hard limits)",
    )
    min_cash_reserve_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Min cash reserve ratio (only for 'configured' mode)",
    )

    # --- Discussion ---
    discussion_rounds: int = Field(3, ge=1, le=10)
    discussion_auto_tools: bool = Field(True)
    discussion_tool_budget: int = Field(15, ge=0, le=100)
    budget_allocation: Optional[BudgetAllocation] = None

    # --- Order limits ---
    max_orders_per_cycle: int = Field(20, ge=1, le=200)
    trade_cooldown_hours: float = Field(24.0, ge=0.0)

    # --- Date range (for simulation) ---
    date_range: Optional[DateRange] = None

    # --- LLM ---
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # --- News ---
    news_html_sources: List[str] = Field(default_factory=list)

    # --- RAG ---
    rag: RAGConfig = Field(default_factory=RAGConfig)

    model_config = {"extra": "ignore"}  # Ignore unknown keys (comments, future fields)

    @field_validator("trading_mode")
    @classmethod
    def validate_trading_mode(cls, v: str) -> str:
        allowed = {"READ_ONLY", "PAPER", "LIVE"}
        upper = v.strip().upper()
        if upper not in allowed:
            raise ValueError(
                f"trading_mode must be one of {allowed}, got '{v}'. "
                f"Default is 'READ_ONLY' (safe, no orders placed)."
            )
        return upper

    @field_validator("position_limit_mode")
    @classmethod
    def validate_position_limit_mode(cls, v: str) -> str:
        allowed = {"auto", "configured"}
        if v not in allowed:
            raise ValueError(f"position_limit_mode must be one of {allowed}, got '{v}'")
        return v

    @field_validator("universe_source")
    @classmethod
    def validate_universe_source(cls, v: str) -> str:
        allowed = {"custom", "sp500"}
        if v not in allowed:
            raise ValueError(f"universe_source must be one of {allowed}, got '{v}'")
        return v

    @field_validator("universe")
    @classmethod
    def validate_universe_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("universe must contain at least one stock ticker symbol")
        return v


def validate_config(raw: Dict[str, Any]) -> TradingConfig:
    """
    Validate a raw config dict (loaded from JSON) against the schema.

    Strips keys starting with '_' (comment keys) before validation.
    Returns a validated TradingConfig instance.
    Raises pydantic.ValidationError with actionable messages on failure.
    """
    # Strip comment keys at top level
    cleaned = {k: v for k, v in raw.items() if not k.startswith("_")}
    return TradingConfig(**cleaned)


def validate_config_file(config_path: str | None = None) -> TradingConfig:
    """
    Load and validate config.json.

    Returns validated TradingConfig.
    Raises FileNotFoundError or pydantic.ValidationError with clear messages.
    """
    import json
    from pathlib import Path

    if config_path is None:
        config_path = str(Path(__file__).resolve().parents[2] / "config" / "config.json")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            f"Copy config.example.json to config.json and customize it."
        )

    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    return validate_config(raw)
