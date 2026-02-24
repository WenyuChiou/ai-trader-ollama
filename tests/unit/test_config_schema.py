# tests/unit/test_config_schema.py
"""
Tests for config schema validation (Phase 3).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from pydantic import ValidationError
from src.utils.config_schema import TradingConfig, validate_config


class TestValidConfig:
    def test_minimal_config(self):
        """Empty dict should produce valid config with all defaults."""
        cfg = validate_config({})
        assert cfg.trading_mode == "READ_ONLY"
        assert cfg.initial_cash == 10000.0
        assert len(cfg.universe) > 0

    def test_full_config(self):
        """Real config.json structure should validate."""
        raw = {
            "universe_source": "custom",
            "universe": ["NVDA", "MSFT"],
            "initial_cash": 50000,
            "trading_mode": "PAPER",
            "position_limit_mode": "auto",
            "discussion_rounds": 3,
            "discussion_auto_tools": True,
            "discussion_tool_budget": 15,
            "max_orders_per_cycle": 20,
            "trade_cooldown_hours": 24.0,
            "llm": {
                "default_model": "deepseek-r1",
                "ollama_host": "http://localhost:11434",
            },
            "rag": {"short_term_days": 7},
        }
        cfg = validate_config(raw)
        assert cfg.trading_mode == "PAPER"
        assert cfg.initial_cash == 50000.0
        assert cfg.universe == ["NVDA", "MSFT"]

    def test_comment_keys_stripped(self):
        """Keys starting with '_' should be ignored."""
        raw = {
            "_comment": "This is a comment",
            "_position_limit_per_stock": 0.15,
            "initial_cash": 5000,
        }
        cfg = validate_config(raw)
        assert cfg.initial_cash == 5000.0

    def test_actual_config_file(self):
        """The real config.json in the repo should validate."""
        config_path = Path(__file__).resolve().parents[2] / "backend" / "config" / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            cfg = validate_config(raw)
            assert cfg.universe_source == "custom"
            assert len(cfg.universe) > 0

    def test_sample_readonly_config(self):
        config_path = Path(__file__).resolve().parents[2] / "backend" / "config" / "config.readonly.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            cfg = validate_config(raw)
            assert cfg.trading_mode == "READ_ONLY"

    def test_sample_paper_config(self):
        config_path = Path(__file__).resolve().parents[2] / "backend" / "config" / "config.paper.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            cfg = validate_config(raw)
            assert cfg.trading_mode == "PAPER"


class TestInvalidConfig:
    def test_invalid_trading_mode(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_config({"trading_mode": "YOLO"})
        errors = exc_info.value.errors()
        assert any("trading_mode" in str(e) for e in errors)

    def test_negative_initial_cash(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_config({"initial_cash": -100})
        errors = exc_info.value.errors()
        assert any("initial_cash" in str(e.get("loc", ())) for e in errors)

    def test_initial_cash_wrong_type(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_config({"initial_cash": "not_a_number"})
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_empty_universe(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_config({"universe": []})
        errors = exc_info.value.errors()
        assert any("universe" in str(e) for e in errors)

    def test_invalid_position_limit_mode(self):
        with pytest.raises(ValidationError):
            validate_config({"position_limit_mode": "freeform"})

    def test_discussion_rounds_too_high(self):
        with pytest.raises(ValidationError):
            validate_config({"discussion_rounds": 999})

    def test_llm_timeout_too_low(self):
        with pytest.raises(ValidationError):
            validate_config({"llm": {"timeout_seconds": 0.1}})


class TestConfigLoader:
    def test_load_without_validate(self):
        """load_config without validate=True should return raw dict."""
        from src.utils.config_loader import load_config
        config = load_config()
        assert isinstance(config, dict)

    def test_load_with_validate(self):
        """load_config with validate=True should run schema check."""
        from src.utils.config_loader import load_config
        config_path = Path(__file__).resolve().parents[2] / "backend" / "config" / "config.json"
        if config_path.exists():
            config = load_config(config_path, validate=True)
            assert isinstance(config, dict)
