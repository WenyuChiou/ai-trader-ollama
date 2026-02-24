# tests/unit/test_api_contract.py
"""
API contract tests (Phase 4).

Tests:
1. Response models validate correctly
2. Error envelope has the standardized shape
3. OpenAPI schema is generated and contains all endpoints
4. Response model field coverage
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class TestErrorEnvelope:
    """Standardized error envelope: {"ok": false, "error": {"code", "message", "details"}}"""

    def test_error_detail_required_fields(self):
        from src.api.response_models import ErrorDetail
        err = ErrorDetail(code="not_found", message="Resource not found")
        assert err.code == "not_found"
        assert err.message == "Resource not found"
        assert err.details is None

    def test_error_detail_with_details(self):
        from src.api.response_models import ErrorDetail
        err = ErrorDetail(code="validation_error", message="Bad input", details={"field": "cash", "issue": "negative"})
        assert err.details["field"] == "cash"

    def test_error_response_shape(self):
        from src.api.response_models import ErrorResponse, ErrorDetail
        resp = ErrorResponse(
            ok=False,
            error=ErrorDetail(code="mode_violation", message="Cannot trade in READ_ONLY"),
            request_id="abc12345",
        )
        d = resp.model_dump()
        assert d["ok"] is False
        assert d["error"]["code"] == "mode_violation"
        assert d["error"]["message"] == "Cannot trade in READ_ONLY"
        assert d["request_id"] == "abc12345"

    def test_make_error_envelope_helper(self):
        from src.api.error_handler import make_error_envelope
        env = make_error_envelope("test_code", "test message", details={"x": 1}, request_id="r1")
        assert env["ok"] is False
        assert env["error"]["code"] == "test_code"
        assert env["error"]["message"] == "test message"
        assert env["error"]["details"] == {"x": 1}
        assert env["request_id"] == "r1"

    def test_make_error_envelope_no_details(self):
        from src.api.error_handler import make_error_envelope
        env = make_error_envelope("err", "msg")
        assert "details" not in env["error"]
        assert env["request_id"]  # auto-generated


class TestResponseModels:
    """Verify Pydantic models serialize correctly."""

    def test_health_response(self):
        from src.api.response_models import HealthResponse
        resp = HealthResponse(status="ok", trading_mode="READ_ONLY", trading_disabled=False, version="1.0.0")
        d = resp.model_dump()
        assert d["status"] == "ok"
        assert d["trading_mode"] == "READ_ONLY"

    def test_trading_mode_response(self):
        from src.api.response_models import TradingModeResponse
        resp = TradingModeResponse(trading_mode="PAPER", trading_disabled=False, live_confirmed=False)
        d = resp.model_dump()
        assert d["trading_mode"] == "PAPER"

    def test_execute_trade_response(self):
        from src.api.response_models import ExecuteTradeResponse
        resp = ExecuteTradeResponse(ok=True, message="Trading cycle completed", trading_mode="PAPER")
        assert resp.ok is True
        assert resp.result is None

    def test_market_open_response(self):
        from src.api.response_models import MarketOpenResponse
        resp = MarketOpenResponse(
            is_open=True,
            timestamp="2026-02-23T10:00:00",
            eastern_time="2026-02-23 10:00:00 EST",
            current_et_time="10:00:00",
        )
        assert resp.minutes_until_open is None
        assert resp.minutes_until_close is None

    def test_vix_response_defaults(self):
        from src.api.response_models import VixTermResponse
        resp = VixTermResponse()
        assert resp.vix == 0
        assert resp.regime == "unknown"

    def test_conversations_response(self):
        from src.api.response_models import ConversationsResponse
        resp = ConversationsResponse()
        assert resp.conversations == []
        assert resp.tool_results_by_category == {}

    def test_system_info_response(self):
        from src.api.response_models import SystemInfoResponse, PositionLimits, AgentFreedom, OptimizationStatus
        resp = SystemInfoResponse(
            llm_model="deepseek-r1",
            llm_base_url="http://localhost:11434",
            version="1.0.0",
            position_limits=PositionLimits(enabled=False, mode="free"),
            agent_freedom=AgentFreedom(position_sizing="free", description="Full freedom"),
            optimizations=OptimizationStatus(enabled=True),
        )
        d = resp.model_dump()
        assert d["llm_model"] == "deepseek-r1"
        assert d["position_limits"]["enabled"] is False


# ---------------------------------------------------------------------------
# OpenAPI Schema Contract
# ---------------------------------------------------------------------------

class TestOpenAPIContract:
    """Verify that FastAPI generates a valid OpenAPI schema with all endpoints."""

    @pytest.fixture(scope="class")
    def openapi_schema(self):
        """Get the OpenAPI schema from the FastAPI app."""
        from src.api.server import app
        return app.openapi()

    def test_schema_has_info(self, openapi_schema):
        assert openapi_schema["info"]["title"] == "AI Trader API"
        assert openapi_schema["info"]["version"] == "1.1.0"

    def test_schema_has_openapi_version(self, openapi_schema):
        assert openapi_schema["openapi"].startswith("3.")

    def test_docs_url_configured(self):
        from src.api.server import app
        assert app.docs_url == "/api/docs"
        assert app.redoc_url == "/api/redoc"
        assert app.openapi_url == "/api/openapi.json"

    def test_critical_endpoints_present(self, openapi_schema):
        """All critical endpoints must appear in the OpenAPI paths."""
        paths = openapi_schema["paths"]
        required_paths = [
            "/api/health",
            "/api/trading/mode",
            "/api/trading/execute-trade",
            "/api/portfolio/real-time",
            "/api/portfolio/equity-history",
            "/api/trades/recent",
            "/api/market/is-open",
            "/api/vix/term",
            "/api/fear-greed",
            "/api/system/info",
            "/api/agents/conversations",
        ]
        for path in required_paths:
            assert path in paths, f"Missing endpoint in OpenAPI schema: {path}"

    def test_health_endpoint_has_response_model(self, openapi_schema):
        """Health endpoint should reference the HealthResponse schema."""
        health = openapi_schema["paths"]["/api/health"]["get"]
        resp_200 = health["responses"]["200"]
        # Should have a schema reference (response_model was set)
        schema = resp_200["content"]["application/json"]["schema"]
        assert "$ref" in schema or "properties" in schema

    def test_schema_serializable(self, openapi_schema):
        """OpenAPI schema must be JSON-serializable (contract snapshot test)."""
        serialized = json.dumps(openapi_schema, indent=2)
        assert len(serialized) > 100  # sanity check
        roundtrip = json.loads(serialized)
        assert roundtrip["info"]["title"] == "AI Trader API"
