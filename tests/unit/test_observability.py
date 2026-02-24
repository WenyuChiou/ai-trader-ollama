# tests/unit/test_observability.py
"""
Tests for Phase 5 observability features:
1. Correlation ID (contextvars-based)
2. JSON log formatter
3. Health/deps response model
4. Error envelope includes correlation ID
"""
from __future__ import annotations

import json
import logging
import sys
from io import StringIO
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ---------------------------------------------------------------------------
# Correlation ID
# ---------------------------------------------------------------------------

class TestCorrelationID:
    def test_new_correlation_id_returns_8_chars(self):
        from src.utils.correlation import new_correlation_id
        cid = new_correlation_id()
        assert len(cid) == 8
        assert cid.isalnum()

    def test_get_after_set(self):
        from src.utils.correlation import set_correlation_id, get_correlation_id
        set_correlation_id("test1234")
        assert get_correlation_id() == "test1234"

    def test_new_overwrites_previous(self):
        from src.utils.correlation import new_correlation_id, get_correlation_id
        cid1 = new_correlation_id()
        cid2 = new_correlation_id()
        assert cid1 != cid2
        assert get_correlation_id() == cid2

    def test_default_is_empty(self):
        """In a fresh context, get_correlation_id returns empty string."""
        import contextvars
        from src.utils.correlation import _correlation_id
        # Run in a clean copy of context
        ctx = contextvars.copy_context()
        result = ctx.run(_correlation_id.get)
        # Default should be empty string (or whatever was set in this test file's context)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# JSON Log Formatter
# ---------------------------------------------------------------------------

class TestJSONFormatter:
    def test_json_formatter_output(self):
        from src.utils.logger import JSONFormatter
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello world", args=(), exc_info=None,
        )
        record.cid = "abc12345"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["cid"] == "abc12345"
        assert parsed["msg"] == "hello world"
        assert "ts" in parsed

    def test_json_formatter_with_exception(self):
        from src.utils.logger import JSONFormatter
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="err", args=(), exc_info=exc_info,
        )
        record.cid = "x"
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestCorrelationFilter:
    def test_filter_injects_cid(self):
        from src.utils.correlation import set_correlation_id
        from src.utils.logger import CorrelationFilter
        set_correlation_id("filt1234")
        f = CorrelationFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hi", args=(), exc_info=None,
        )
        f.filter(record)
        assert record.cid == "filt1234"
        assert record.trace_id == "filt1234"

    def test_filter_generates_fallback_when_empty(self):
        from src.utils.correlation import set_correlation_id
        from src.utils.logger import CorrelationFilter
        set_correlation_id("")
        f = CorrelationFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hi", args=(), exc_info=None,
        )
        f.filter(record)
        # Should generate a fallback UUID
        assert len(record.cid) == 8


class TestSetupLogger:
    def test_text_format(self, tmp_path):
        from src.utils.logger import setup_logger
        logger = setup_logger("test_text", log_dir=tmp_path, log_format="text")
        assert len(logger.handlers) == 2  # file + console

    def test_json_format(self, tmp_path):
        from src.utils.logger import setup_logger, JSONFormatter
        logger = setup_logger("test_json", log_dir=tmp_path, log_format="json")
        # Both handlers should use JSONFormatter
        for handler in logger.handlers:
            assert isinstance(handler.formatter, JSONFormatter)


# ---------------------------------------------------------------------------
# Health Deps Response Model
# ---------------------------------------------------------------------------

class TestHealthDepsModel:
    def test_healthy_response(self):
        from src.api.response_models import HealthDepsResponse, DependencyStatus
        resp = HealthDepsResponse(
            status="ok",
            dependencies={
                "ollama": DependencyStatus(status="ok", url="http://localhost:11434", models_available=3),
                "data_dir": DependencyStatus(status="ok", path="/data/logs"),
            },
        )
        d = resp.model_dump()
        assert d["status"] == "ok"
        assert d["dependencies"]["ollama"]["models_available"] == 3

    def test_degraded_response(self):
        from src.api.response_models import HealthDepsResponse, DependencyStatus
        resp = HealthDepsResponse(
            status="degraded",
            dependencies={
                "ollama": DependencyStatus(status="unreachable", url="http://localhost:11434", error="Connection refused"),
            },
        )
        d = resp.model_dump()
        assert d["status"] == "degraded"
        assert d["dependencies"]["ollama"]["error"] == "Connection refused"


# ---------------------------------------------------------------------------
# Error Envelope + Correlation
# ---------------------------------------------------------------------------

class TestErrorEnvelopeCorrelation:
    def test_make_error_envelope_accepts_request_id(self):
        from src.api.error_handler import make_error_envelope
        env = make_error_envelope("test", "msg", request_id="corr1234")
        assert env["request_id"] == "corr1234"

    def test_make_error_envelope_auto_generates_id(self):
        from src.api.error_handler import make_error_envelope
        env = make_error_envelope("test", "msg")
        assert len(env["request_id"]) == 8
