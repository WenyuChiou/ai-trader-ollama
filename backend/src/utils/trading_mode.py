# src/utils/trading_mode.py
"""
Trading Mode Gating — Safety backbone for the AI Trader system.

Runtime modes:
  READ_ONLY  — Default. View portfolio, run analysis, no orders placed.
  PAPER      — Orders are logged and simulated but never sent to a real broker.
  LIVE       — Real orders. Requires TWO independent opt-ins plus no kill-switch.

Resolution order (highest priority first):
  1. TRADING_DISABLED=1 env var → always blocks orders (kill-switch)
  2. Environment variable TRADING_MODE (if set)
  3. config.json field "trading_mode" (if set)
  4. Default: READ_ONLY
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class TradingMode(str, Enum):
    """Runtime trading modes."""
    READ_ONLY = "READ_ONLY"
    PAPER = "PAPER"
    LIVE = "LIVE"


class TradingModeError(Exception):
    """Raised when an operation is blocked by the current trading mode."""

    def __init__(self, message: str, mode: TradingMode, action: str):
        self.mode = mode
        self.action = action
        super().__init__(message)


class OrderAuditLogger:
    """Append-only audit log for every order attempt (allowed or blocked)."""

    def __init__(self, logs_dir: Optional[Path] = None):
        if logs_dir is None:
            # Default: project_root/data/logs
            logs_dir = Path(__file__).resolve().parents[3] / "data" / "logs"
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.logs_dir / "audit_orders.jsonl"

    def log(
        self,
        *,
        mode: TradingMode,
        action: str,
        symbol: str,
        quantity: int,
        price: float,
        result: str,
        reason: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Write one audit record. Returns the record dict."""
        record = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "mode": mode.value,
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "result": result,  # "ALLOWED", "BLOCKED_MODE", "BLOCKED_KILLSWITCH", "BLOCKED_NO_CONFIRMATION"
            "reason": reason,
        }
        if extra:
            record["extra"] = extra

        try:
            with self.audit_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            # Audit logging must not crash the server
            print(f"[AUDIT] WARNING: Failed to write audit log: {e}")

        return record


# ---------------------------------------------------------------------------
# Singleton-ish helpers so the rest of the codebase can just call
# `get_trading_mode()` and `assert_can_trade()` without plumbing.
# ---------------------------------------------------------------------------

_audit_logger: Optional[OrderAuditLogger] = None


def get_audit_logger(logs_dir: Optional[Path] = None) -> OrderAuditLogger:
    """Return (and lazily create) the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = OrderAuditLogger(logs_dir)
    return _audit_logger


def resolve_trading_mode(config: Optional[Dict[str, Any]] = None) -> TradingMode:
    """
    Resolve the effective trading mode.

    Priority:
      1. Env var TRADING_MODE (if set and valid)
      2. config dict key "trading_mode" (if set and valid)
      3. Default: READ_ONLY
    """
    # 1. Environment variable
    env_mode = os.getenv("TRADING_MODE", "").strip().upper()
    if env_mode:
        try:
            return TradingMode(env_mode)
        except ValueError:
            print(f"[WARN] Invalid TRADING_MODE env var: '{env_mode}', falling back to config/default")

    # 2. Config
    if config:
        cfg_mode = str(config.get("trading_mode", "")).strip().upper()
        if cfg_mode:
            try:
                return TradingMode(cfg_mode)
            except ValueError:
                print(f"[WARN] Invalid trading_mode in config: '{cfg_mode}', falling back to default")

    # 3. Default
    return TradingMode.READ_ONLY


def is_kill_switch_active() -> bool:
    """Return True if the kill-switch env var TRADING_DISABLED is set to '1'."""
    return os.getenv("TRADING_DISABLED", "0").strip() == "1"


def is_live_confirmed() -> bool:
    """Return True if the LIVE confirmation phrase is present in the environment."""
    return os.getenv("I_UNDERSTAND_LIVE_TRADING", "").strip() == "YES"


def assert_can_trade(
    *,
    mode: Optional[TradingMode] = None,
    config: Optional[Dict[str, Any]] = None,
    action: str = "UNKNOWN",
    symbol: str = "UNKNOWN",
    quantity: int = 0,
    price: float = 0.0,
) -> TradingMode:
    """
    Gate-check: raise TradingModeError if the current mode does not permit
    placing orders.  Also writes an audit log entry.

    Returns the resolved TradingMode on success so callers can use it.
    """
    if mode is None:
        mode = resolve_trading_mode(config)

    audit = get_audit_logger()

    # Kill-switch overrides everything
    if is_kill_switch_active():
        audit.log(
            mode=mode,
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=price,
            result="BLOCKED_KILLSWITCH",
            reason="TRADING_DISABLED=1 is set — kill-switch active",
        )
        raise TradingModeError(
            "Trading is disabled via kill-switch (TRADING_DISABLED=1). "
            "Remove this environment variable to re-enable trading.",
            mode=mode,
            action=action,
        )

    # READ_ONLY blocks all orders
    if mode == TradingMode.READ_ONLY:
        audit.log(
            mode=mode,
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=price,
            result="BLOCKED_MODE",
            reason="READ_ONLY mode — orders are not permitted",
        )
        raise TradingModeError(
            "Cannot place orders in READ_ONLY mode. "
            "Set trading_mode to PAPER or LIVE to enable order placement.",
            mode=mode,
            action=action,
        )

    # LIVE requires confirmation phrase
    if mode == TradingMode.LIVE and not is_live_confirmed():
        audit.log(
            mode=mode,
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=price,
            result="BLOCKED_NO_CONFIRMATION",
            reason="LIVE mode requires I_UNDERSTAND_LIVE_TRADING=YES",
        )
        raise TradingModeError(
            "LIVE mode requires the environment variable "
            "I_UNDERSTAND_LIVE_TRADING=YES as a safety confirmation. "
            "This is a deliberate two-factor safety check.",
            mode=mode,
            action=action,
        )

    # PAPER or confirmed LIVE — allowed
    audit.log(
        mode=mode,
        action=action,
        symbol=symbol,
        quantity=quantity,
        price=price,
        result="ALLOWED",
        reason=f"Order permitted in {mode.value} mode",
    )

    return mode
