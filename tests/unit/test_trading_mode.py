# tests/unit/test_trading_mode.py
"""
Tests for the trading mode gating system (Phase 2 — Safety Backbone).

Covers:
  - Mode resolution from env, config, and defaults
  - Kill-switch blocks all modes
  - READ_ONLY blocks orders
  - PAPER allows orders
  - LIVE requires confirmation phrase
  - LIVE + confirmation allows orders
  - Audit log entries for every attempt
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure backend is on path
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.utils.trading_mode import (
    TradingMode,
    TradingModeError,
    OrderAuditLogger,
    assert_can_trade,
    resolve_trading_mode,
    is_kill_switch_active,
    is_live_confirmed,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure a clean environment for every test."""
    monkeypatch.delenv("TRADING_MODE", raising=False)
    monkeypatch.delenv("TRADING_DISABLED", raising=False)
    monkeypatch.delenv("I_UNDERSTAND_LIVE_TRADING", raising=False)
    # Reset the global audit logger so each test gets a fresh one
    import src.utils.trading_mode as tm
    tm._audit_logger = None


@pytest.fixture
def audit_dir(tmp_path):
    """Provide a temp directory for audit logs."""
    d = tmp_path / "logs"
    d.mkdir()
    return d


def _read_audit(audit_dir: Path):
    """Read all audit records from the temp audit file."""
    audit_file = audit_dir / "audit_orders.jsonl"
    if not audit_file.exists():
        return []
    records = []
    for line in audit_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# 1. Mode Resolution
# ---------------------------------------------------------------------------

class TestResolveMode:
    def test_default_is_read_only(self):
        assert resolve_trading_mode() == TradingMode.READ_ONLY

    def test_env_overrides_config(self, monkeypatch):
        monkeypatch.setenv("TRADING_MODE", "PAPER")
        config = {"trading_mode": "LIVE"}
        assert resolve_trading_mode(config) == TradingMode.PAPER

    def test_config_used_when_no_env(self):
        config = {"trading_mode": "PAPER"}
        assert resolve_trading_mode(config) == TradingMode.PAPER

    def test_invalid_env_falls_back_to_config(self, monkeypatch):
        monkeypatch.setenv("TRADING_MODE", "INVALID_MODE")
        config = {"trading_mode": "PAPER"}
        assert resolve_trading_mode(config) == TradingMode.PAPER

    def test_invalid_config_falls_back_to_default(self):
        config = {"trading_mode": "BOGUS"}
        assert resolve_trading_mode(config) == TradingMode.READ_ONLY

    def test_case_insensitive_env(self, monkeypatch):
        monkeypatch.setenv("TRADING_MODE", "paper")
        assert resolve_trading_mode() == TradingMode.PAPER

    def test_live_from_env(self, monkeypatch):
        monkeypatch.setenv("TRADING_MODE", "LIVE")
        assert resolve_trading_mode() == TradingMode.LIVE


# ---------------------------------------------------------------------------
# 2. Kill-Switch
# ---------------------------------------------------------------------------

class TestKillSwitch:
    def test_kill_switch_inactive_by_default(self):
        assert not is_kill_switch_active()

    def test_kill_switch_active(self, monkeypatch):
        monkeypatch.setenv("TRADING_DISABLED", "1")
        assert is_kill_switch_active()

    def test_kill_switch_zero_is_inactive(self, monkeypatch):
        monkeypatch.setenv("TRADING_DISABLED", "0")
        assert not is_kill_switch_active()

    def test_kill_switch_blocks_paper(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "PAPER")
        monkeypatch.setenv("TRADING_DISABLED", "1")
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError) as exc_info:
            assert_can_trade(action="BUY", symbol="AAPL", quantity=10, price=150.0)
        assert "kill-switch" in str(exc_info.value).lower()

        records = _read_audit(audit_dir)
        assert len(records) == 1
        assert records[0]["result"] == "BLOCKED_KILLSWITCH"

    def test_kill_switch_blocks_live(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "LIVE")
        monkeypatch.setenv("I_UNDERSTAND_LIVE_TRADING", "YES")
        monkeypatch.setenv("TRADING_DISABLED", "1")
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError):
            assert_can_trade(action="BUY", symbol="AAPL", quantity=10, price=150.0)

        records = _read_audit(audit_dir)
        assert records[0]["result"] == "BLOCKED_KILLSWITCH"


# ---------------------------------------------------------------------------
# 3. READ_ONLY Mode
# ---------------------------------------------------------------------------

class TestReadOnlyMode:
    def test_read_only_blocks_buy(self, audit_dir):
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError) as exc_info:
            assert_can_trade(action="BUY", symbol="NVDA", quantity=5, price=120.0)
        assert exc_info.value.mode == TradingMode.READ_ONLY

        records = _read_audit(audit_dir)
        assert len(records) == 1
        assert records[0]["result"] == "BLOCKED_MODE"
        assert records[0]["mode"] == "READ_ONLY"

    def test_read_only_blocks_sell(self, audit_dir):
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError):
            assert_can_trade(action="SELL", symbol="MSFT", quantity=3, price=400.0)


# ---------------------------------------------------------------------------
# 4. PAPER Mode
# ---------------------------------------------------------------------------

class TestPaperMode:
    def test_paper_allows_buy(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "PAPER")
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        mode = assert_can_trade(action="BUY", symbol="GOOG", quantity=2, price=170.0)
        assert mode == TradingMode.PAPER

        records = _read_audit(audit_dir)
        assert len(records) == 1
        assert records[0]["result"] == "ALLOWED"
        assert records[0]["mode"] == "PAPER"

    def test_paper_allows_sell(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "PAPER")
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        mode = assert_can_trade(action="SELL", symbol="AAPL", quantity=10, price=190.0)
        assert mode == TradingMode.PAPER


# ---------------------------------------------------------------------------
# 5. LIVE Mode
# ---------------------------------------------------------------------------

class TestLiveMode:
    def test_live_without_confirmation_blocked(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "LIVE")
        # Deliberately NOT setting I_UNDERSTAND_LIVE_TRADING
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError) as exc_info:
            assert_can_trade(action="BUY", symbol="TSLA", quantity=1, price=250.0)
        assert "I_UNDERSTAND_LIVE_TRADING" in str(exc_info.value)

        records = _read_audit(audit_dir)
        assert records[0]["result"] == "BLOCKED_NO_CONFIRMATION"

    def test_live_with_confirmation_allowed(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "LIVE")
        monkeypatch.setenv("I_UNDERSTAND_LIVE_TRADING", "YES")
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        mode = assert_can_trade(action="BUY", symbol="AMZN", quantity=5, price=185.0)
        assert mode == TradingMode.LIVE

        records = _read_audit(audit_dir)
        assert records[0]["result"] == "ALLOWED"
        assert records[0]["mode"] == "LIVE"

    def test_live_wrong_confirmation_blocked(self, monkeypatch, audit_dir):
        monkeypatch.setenv("TRADING_MODE", "LIVE")
        monkeypatch.setenv("I_UNDERSTAND_LIVE_TRADING", "yes")  # lowercase — must be exactly "YES"
        import src.utils.trading_mode as tm
        tm._audit_logger = OrderAuditLogger(audit_dir)

        with pytest.raises(TradingModeError):
            assert_can_trade(action="BUY", symbol="META", quantity=3, price=500.0)


# ---------------------------------------------------------------------------
# 6. Audit Logger
# ---------------------------------------------------------------------------

class TestAuditLogger:
    def test_audit_records_all_fields(self, audit_dir):
        logger = OrderAuditLogger(audit_dir)
        record = logger.log(
            mode=TradingMode.PAPER,
            action="BUY",
            symbol="NVDA",
            quantity=10,
            price=120.50,
            result="ALLOWED",
            reason="Test",
        )
        assert record["mode"] == "PAPER"
        assert record["symbol"] == "NVDA"
        assert record["quantity"] == 10
        assert record["price"] == 120.50
        assert "ts" in record

    def test_audit_persists_to_file(self, audit_dir):
        logger = OrderAuditLogger(audit_dir)
        logger.log(mode=TradingMode.READ_ONLY, action="BUY", symbol="X",
                    quantity=1, price=1.0, result="BLOCKED_MODE", reason="test")
        logger.log(mode=TradingMode.PAPER, action="SELL", symbol="Y",
                    quantity=2, price=2.0, result="ALLOWED", reason="test")

        records = _read_audit(audit_dir)
        assert len(records) == 2
        assert records[0]["symbol"] == "X"
        assert records[1]["symbol"] == "Y"

    def test_audit_extra_field(self, audit_dir):
        logger = OrderAuditLogger(audit_dir)
        record = logger.log(
            mode=TradingMode.LIVE,
            action="BUY",
            symbol="TEST",
            quantity=1,
            price=1.0,
            result="ALLOWED",
            reason="test",
            extra={"correlation_id": "abc123"},
        )
        assert record["extra"]["correlation_id"] == "abc123"
