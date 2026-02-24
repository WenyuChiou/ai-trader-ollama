# src/api/response_models.py
"""
Pydantic response models for all API endpoints.

These models serve as the API contract — FastAPI uses them for:
1. OpenAPI/Swagger documentation (/api/docs)
2. Response serialization and validation
3. Contract snapshot tests in CI

Phase 4 deliverable: D7 (API Contract & Shared Types)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Shared / Common Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Standardized error envelope — every error response uses this shape."""
    code: str = Field(..., description="Machine-readable error code (e.g. 'mode_violation', 'not_found')")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Any] = Field(None, description="Additional context (validation errors, debug info)")


class ErrorResponse(BaseModel):
    """Top-level error response wrapper."""
    ok: bool = Field(False, description="Always false for errors")
    error: ErrorDetail
    request_id: Optional[str] = Field(None, description="Correlation ID for log lookup")


# ============================================================================
# Health & Mode
# ============================================================================

class HealthResponse(BaseModel):
    status: str = Field("ok", description="Service health status")
    trading_mode: str = Field(..., description="Current trading mode: READ_ONLY, PAPER, or LIVE")
    trading_disabled: bool = Field(..., description="True if kill-switch is active")
    version: str = Field(..., description="API version string")


class TradingModeResponse(BaseModel):
    trading_mode: str
    trading_disabled: bool
    live_confirmed: bool


class DependencyStatus(BaseModel):
    status: str = Field(..., description="ok, degraded, or unreachable")
    url: Optional[str] = None
    path: Optional[str] = None
    models_available: Optional[int] = None
    error: Optional[str] = None


class HealthDepsResponse(BaseModel):
    status: str = Field(..., description="ok if all deps healthy, degraded otherwise")
    dependencies: Dict[str, DependencyStatus]


# ============================================================================
# Root / Info
# ============================================================================

class RootResponse(BaseModel):
    message: str
    version: str
    endpoints: Dict[str, str]


# ============================================================================
# Trading
# ============================================================================

class ExecuteTradeResponse(BaseModel):
    ok: bool = True
    message: str
    trading_mode: str
    result: Optional[Dict[str, Any]] = None


class PendingOrdersResponse(BaseModel):
    ok: bool = True
    message: str
    settled_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    pending_orders: List[Dict[str, Any]] = Field(default_factory=list)


class RecentTradesResponse(BaseModel):
    ok: bool = True
    trades: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Portfolio
# ============================================================================

class PositionDetail(BaseModel):
    quantity: int
    avg_cost: float
    total_cost: float
    cost_basis: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PortfolioRealtimeResponse(BaseModel):
    ok: bool = True
    portfolio: Dict[str, Any] = Field(default_factory=dict)
    positions: Dict[str, Any] = Field(default_factory=dict)
    last_prices: Dict[str, float] = Field(default_factory=dict)
    positions_detail: Dict[str, Any] = Field(default_factory=dict)
    positions_pnl: Dict[str, Any] = Field(default_factory=dict)


class EquityHistoryResponse(BaseModel):
    ok: bool = True
    records: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class RecordEquityResponse(BaseModel):
    ok: bool = True
    message: str = "Equity recorded successfully"
    date: Optional[str] = None


# ============================================================================
# Conversations
# ============================================================================

class ConversationsResponse(BaseModel):
    ok: bool = True
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    total: int = 0
    has_more: bool = False
    discussion_rounds: Dict[str, Any] = Field(default_factory=dict)
    discussion_rounds_summaries: Dict[str, Any] = Field(default_factory=dict)
    tool_results_by_category: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


# ============================================================================
# Market
# ============================================================================

class MarketOpenResponse(BaseModel):
    ok: bool = True
    is_open: bool
    timestamp: str
    eastern_time: str
    current_et_time: str
    market_hours: str = "9:30 AM - 4:00 PM ET"
    minutes_until_open: Optional[int] = None
    minutes_until_close: Optional[int] = None


class VixTermResponse(BaseModel):
    ok: bool = True
    vix: float = 0
    vix3m: float = 0
    ratio: float = 0
    vix_risk_score: float = 0
    regime: str = "unknown"
    error: Optional[str] = None


class FearGreedResponse(BaseModel):
    ok: bool = True
    value: float = 0
    label: str = "Unknown"
    fear_greed: Optional[Dict[str, Any]] = None


# ============================================================================
# System
# ============================================================================

class SystemInitResponse(BaseModel):
    ok: bool = True
    message: str
    deleted_files: List[str] = Field(default_factory=list)
    backup_created: bool = False
    backup_filename: Optional[str] = None
    note: Optional[str] = None


class PositionLimits(BaseModel):
    enabled: bool
    limits: Optional[Dict[str, Any]] = None
    mode: str


class AgentFreedom(BaseModel):
    position_sizing: str
    description: str


class OptimizationStatus(BaseModel):
    enabled: bool
    components: Dict[str, str] = Field(default_factory=dict)
    performance: Dict[str, str] = Field(default_factory=dict)
    note: Optional[str] = None


class SystemInfoResponse(BaseModel):
    ok: bool = True
    llm_model: str
    llm_base_url: str
    version: str
    position_limits: PositionLimits
    agent_freedom: AgentFreedom
    optimizations: OptimizationStatus


# ============================================================================
# Agents & Tools
# ============================================================================

class AgentStatus(BaseModel):
    name: str
    model: str
    status: str = "idle"


class AgentsStatusResponse(BaseModel):
    ok: bool = True
    agents: List[Dict[str, Any]] = Field(default_factory=list)


class ToolInfo(BaseModel):
    name: str
    description: str = ""
    category: str = "other"


class ToolsListResponse(BaseModel):
    ok: bool = True
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0


# ============================================================================
# Performance
# ============================================================================

class PerformanceStatisticsResponse(BaseModel):
    ok: bool = True
    statistics: Dict[str, Any] = Field(default_factory=dict)


class TradesByDateResponse(BaseModel):
    ok: bool = True
    trades: List[Dict[str, Any]] = Field(default_factory=list)


class SymbolAnalysisResponse(BaseModel):
    ok: bool = True
    analysis: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Data Upload
# ============================================================================

class DataUploadResponse(BaseModel):
    ok: bool = True
    uploaded: Dict[str, Any] = Field(default_factory=dict)
    message: str = "Data uploaded successfully"


# ============================================================================
# Verify
# ============================================================================

class VerifyUpdatesResponse(BaseModel):
    ok: bool = True
    file_exists: bool = False
    stats: Dict[str, int] = Field(default_factory=dict)
    recent_entries: List[Dict[str, Any]] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
