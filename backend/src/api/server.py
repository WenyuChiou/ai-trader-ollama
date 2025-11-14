# src/api/server.py
"""
FastAPI backend for real-time agent monitoring and frontend integration.
Provides WebSocket for real-time updates and REST API for historical data.
"""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from typing import List, Dict, Any, Optional
import random
from pathlib import Path
import json
import asyncio
from datetime import datetime, timezone, date, timedelta
from datetime import time as dt_time
import uuid
import sys
import os
import io
import logging

# Fix Windows console encoding for Unicode output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure backend directory is in Python path (for uvicorn imports)
# This allows the server to be started from any directory
_backend_dir = Path(__file__).resolve().parent.parent.parent  # Go up from src/api/server.py to backend/
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# CRITICAL: Helper function to get project root data/logs directory
# This ensures all API endpoints use the same path regardless of working directory
def get_project_logs_dir() -> Path:
    """Get the project root data/logs directory path."""
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

# Configure logging to ensure print statements are visible in uvicorn
# Uvicorn will show stderr output, so we'll use logging which goes to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # Use stderr so uvicorn shows it
)
logger = logging.getLogger(__name__)

# Helper function to print to stderr (visible in uvicorn)
def _get_order_date(order: dict) -> Optional[str]:
    """
    从订单中提取日期（优先从placed_at提取，兼容旧的order_date字段）
    
    返回:
    - 订单日期 (YYYY-MM-DD) 或 None
    """
    placed_at = order.get("placed_at", "")
    if placed_at:
        try:
            return datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
        except:
            pass
    # 兼容旧的order_date字段
    return order.get("order_date")

def log_print(message):
    """Print to stderr so it's visible in uvicorn output"""
    print(message, file=sys.stderr, flush=True)

from src.core.event_bus import EventBus, AgentEvent

# Create FastAPI app
app = FastAPI(
    title="AI Trader API",
    description="Real-time agent monitoring and trading cycle API",
    version="1.0.0"
)

# Define CORS headers as a constant to ensure consistency
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, Accept, Origin",
    "Access-Control-Expose-Headers": "*",
}

# CORS for frontend - MUST be added FIRST (outermost middleware)
# Handle null origin (file:// protocol) by allowing all origins
# Note: allow_credentials must be False when using allow_origins=["*"]
# If you need credentials, specify exact origins instead of "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including null (file:// protocol)
    allow_credentials=False,  # Must be False when using wildcard origins (True would cause error)
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods list
    allow_headers=["*"],  # Allow all headers (FastAPI CORSMiddleware supports "*")
    expose_headers=["*"],  # Expose all headers (FastAPI CORSMiddleware supports "*")
    max_age=3600,
)

# Response middleware to ensure CORS headers are ALWAYS present
# IMPORTANT: FastAPI middleware executes in REVERSE order (last registered = first executed)
# So this middleware (registered after CORS) runs FIRST and adds CORS headers to ALL responses
# This ensures CORS headers are present even if CORSMiddleware fails or is bypassed
@app.middleware("http")
async def add_cors_headers_middleware(request: Request, call_next):
    """Middleware to ensure CORS headers are always present in all responses"""
    try:
        response = await call_next(request)
        # Always add CORS headers to response (works for all response types)
        # Force set headers (don't use setdefault, always overwrite)
        if hasattr(response, 'headers'):
            for key, value in CORS_HEADERS.items():
                response.headers[key] = value
        return response
    except Exception as e:
        # If an exception occurs, return a response with CORS headers
        import traceback
        error_msg = str(e)
        # Remove emoji characters to avoid encoding issues
        import re
        error_msg = re.sub(r'[\U0001F300-\U0001F9FF]', '', error_msg)
        error_msg = re.sub(r'[\U0001FA00-\U0001FAFF]', '', error_msg)
        
        log_print(f"[MIDDLEWARE EXCEPTION] Error: {error_msg}")
        log_print(f"[MIDDLEWARE EXCEPTION] Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": error_msg,
                "message": "An internal server error occurred. Please check the server logs for details."
            },
            headers=CORS_HEADERS.copy()
        )

# Exception handlers to ensure CORS headers are always present
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with CORS headers"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "ok": False,
            "error": exc.detail,
            "message": f"HTTP {exc.status_code}: {exc.detail}"
        },
        headers=CORS_HEADERS.copy()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    """Global exception handler to ensure CORS headers are always present"""
    import traceback
    error_msg = str(exc)
    # Remove emoji characters to avoid encoding issues
    import re
    error_msg = re.sub(r'[\U0001F300-\U0001F9FF]', '', error_msg)
    error_msg = re.sub(r'[\U0001FA00-\U0001FAFF]', '', error_msg)
    
    log_print(f"[GLOBAL EXCEPTION HANDLER] Error: {error_msg}")
    log_print(f"[GLOBAL EXCEPTION HANDLER] Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": error_msg,
            "message": "An internal server error occurred. Please check the server logs for details."
        },
        headers=CORS_HEADERS.copy()
    )

# CORS for frontend - MUST be added AFTER the custom middleware
# Handle null origin (file:// protocol) by allowing all origins
# Note: allow_credentials must be False when using allow_origins=["*"]
# If you need credentials, specify exact origins instead of "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including null (file:// protocol)
    allow_credentials=False,  # Must be False when using wildcard origins (True would cause error)
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods list
    allow_headers=["*"],  # Allow all headers (FastAPI CORSMiddleware supports "*")
    expose_headers=["*"],  # Expose all headers (FastAPI CORSMiddleware supports "*")
    max_age=3600,
)

# Global event bus
event_bus = EventBus.get_instance()

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Trading cycle execution lock (prevent concurrent execution)
_trading_cycle_lock = asyncio.Lock()
_trading_cycle_executing = False


def load_trading_config():
    """从 config.json 读取交易配置"""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    universe = None
    tool_budget = 15  # 默认值：15个工具调用（足够4个analyst各用3-4个工具）
    rounds = 3
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                # 读取工具预算（优先使用 discussion_tool_budget，如果没有则使用默认值）
                tool_budget = config_data.get("discussion_tool_budget", config_data.get("tool_budget", 15))
                # 确保至少为8，否则工具调用太少
                if tool_budget < 8:
                    tool_budget = 15
                rounds = config_data.get("discussion_rounds", 3)
        except Exception as e:
            log_print(f"[Config] Failed to read config.json, using defaults: {e}")
    
    return {
        "universe": universe,
        "tool_budget": tool_budget,
        "rounds": rounds
    }


def broadcast_event(event: AgentEvent):
    """Broadcast event to all connected WebSocket clients"""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "agent_event",
        "data": {
            "timestamp": event.timestamp,
            "agent_name": event.agent_name,
            "event_type": event.event_type,
            "status": event.status,
            "payload": event.payload,
            "round_number": event.round_number,
            "session_id": event.session_id,
        }
    })
    
    # Broadcast to all connections (async-safe)
    disconnected = []
    for connection in active_connections:
        try:
            asyncio.create_task(connection.send_text(message))
        except Exception:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


# Subscribe event bus to WebSocket broadcaster
event_bus.subscribe(broadcast_event)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send current status on connection
        status = event_bus.get_all_agents_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": status
        })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        log_print(f"[WebSocket] Error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.options("/api/agents/status")
async def agents_status_options():
    """Handle CORS preflight for agents status endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/api/agents/status")
async def get_agents_status():
    """Get current status of all agents"""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    try:
        # Get status from event bus (may only contain agents that have run)
        status = event_bus.get_all_agents_status()
        
        # CRITICAL FIX: Always load agents.yaml to show all registered agents
        # Merge with event_bus status so we show both registered agents and their runtime status
        try:
            from pathlib import Path
            import yaml
            import sys
            
            # Ensure we're in the backend directory
            backend_dir = Path(__file__).parent.parent.parent
            agents_file = backend_dir / "config" / "agents.yaml"
            
            if agents_file.exists():
                with agents_file.open("r", encoding="utf-8") as f:
                    agents_config = yaml.safe_load(f)
                    log_print(f"[API] Loaded agents.yaml: {type(agents_config)}, keys: {list(agents_config.keys()) if isinstance(agents_config, dict) else 'N/A'}")
                    
                    # agents.yaml structure: direct dict of agent_name -> config
                    # OR nested under "agents" key
                    agent_dict = agents_config
                    if isinstance(agents_config, dict):
                        # Check if it's nested under "agents" key
                        if "agents" in agents_config:
                            agent_dict = agents_config["agents"]
                            log_print(f"[API] Found nested 'agents' key, using it")
                        # Also check if it's a direct dict of agent_name -> config
                        # (agents.yaml might have other top-level keys like "default_model", etc.)
                        # In that case, filter out non-agent keys
                        if agent_dict == agents_config:
                            # Filter out non-agent keys (like "default_model", "ollama_host", etc.)
                            # Agent keys should have "model" or "name" or "prompt_file" or similar agent config keys
                            # Based on agents.yaml structure: each agent has "model", "name", "temperature", "prompt_file"
                            original_count = len(agent_dict)
                            agent_dict = {
                                k: v for k, v in agents_config.items()
                                if isinstance(v, dict) and (
                                    "model" in v or "name" in v or "prompt_file" in v or
                                    "role" in v or "tools" in v or 
                                    "system_prompt" in v or "description" in v
                                )
                            }
                            log_print(f"[API] Filtered agents: {original_count} -> {len(agent_dict)} (keys: {list(agent_dict.keys())})")
                    
                    if agent_dict and isinstance(agent_dict, dict):
                        # Start with all registered agents from agents.yaml
                        agents = {}
                        for agent_name in agent_dict.keys():
                            # If agent has runtime status from event_bus, use it; otherwise use "idle"
                            if status and agent_name in status:
                                agents[agent_name] = status[agent_name]
                            else:
                                agents[agent_name] = {"status": "idle", "last_activity": None}
                        
                        log_print(f"[API] Loaded {len(agents)} agents from agents.yaml (merged with {len(status) if status else 0} runtime status)")
                        log_print(f"[API] Agent names: {list(agents.keys())}")
                        return JSONResponse(
                            status_code=200,
                            content=agents,
                            headers=cors_headers
                        )
                    else:
                        log_print(f"[API] WARNING: agent_dict is not a dict or is empty: {agent_dict}")
        except Exception as yaml_error:
            import traceback
            log_print(f"[API] Error loading agents.yaml: {yaml_error}")
            log_print(f"[API] Traceback: {traceback.format_exc()}")
            # Continue with event_bus status if available
        
        # Fallback: return event_bus status if agents.yaml loading failed
        log_print(f"[API] WARNING: Falling back to event_bus status (only {len(status) if status else 0} agents)")
        return JSONResponse(
            status_code=200,
            content=status if status else {},
            headers=cors_headers
        )
    except Exception as e:
        log_print(f"[API] Error getting agents status: {e}")
        import traceback
        log_print(f"[API] Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=200,
            content={},
            headers=cors_headers
        )


@app.get("/api/agents/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Get status of a specific agent"""
    return event_bus.get_agent_status(agent_name)


@app.get("/api/history")
async def get_history(
    agent_name: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    session_id: str | None = None
):
    """Get event history"""
    events = event_bus.get_history(
        agent_name=agent_name,
        event_type=event_type,
        limit=limit,
        session_id=session_id
    )
    return {"events": events, "count": len(events)}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full history of a trading session"""
    events = event_bus.get_history(session_id=session_id, limit=1000)
    return {
        "session_id": session_id,
        "events": events,
        "count": len(events)
    }


@app.post("/api/trading/execute")
async def execute_trading_cycle():
    """Trigger a new trading cycle"""
    from src.orchestrator.trading_cycle import execute_daily_trade
    
    # 从 config.json 读取配置
    config = load_trading_config()
    universe = config["universe"]
    tool_budget = config["tool_budget"]
    rounds = config["rounds"]
    
    if universe:
        log_print(f"[Trading Cycle] Using {len(universe)} stocks from config.json")
    log_print(f"[Trading Cycle] Tool budget: {tool_budget}, Rounds: {rounds}")
    
    session_id = str(uuid.uuid4())
    
    # Emit session start event
    event_bus.emit(AgentEvent(
        timestamp=datetime.now().isoformat(),
        agent_name="Orchestrator",
        event_type="session_start",
        status="running",
        payload={"session_id": session_id},
        session_id=session_id
    ))
    
    try:
        # Execute trading cycle
        result = execute_daily_trade(
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            universe=universe  # 使用从 config.json 读取的股票清单（如果存在）
        )
        
        # Emit session end event
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Orchestrator",
            event_type="session_end",
            status="success",
            payload={"result": result},
            session_id=session_id
        ))
        
        return {
            "session_id": session_id,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Orchestrator",
            event_type="session_error",
            status="error",
            payload={"error": str(e)},
            session_id=session_id
        ))
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "session_id": session_id}
        )


@app.options("/api/trading/execute-trade")
async def execute_trade_options():
    """Handle CORS preflight for execute-trade endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/trading/execute-trade")
async def execute_trade_direct():
    """直接执行交易循环，支持非交易时段规划明日交易"""
    global _trading_cycle_executing
    
    # 检查是否已有交易循环在执行（防重复执行）
    if _trading_cycle_executing:
        log_print("[TRADING CYCLE] Another trading cycle is already executing, rejecting request")
        return JSONResponse(
            status_code=429,  # Too Many Requests
            content={
                "ok": False,
                "error": "Trading cycle is already executing. Please wait for the current cycle to complete.",
                "message": "Another trading cycle is in progress. Please try again later."
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
    # 获取锁并设置执行标志
    async with _trading_cycle_lock:
        if _trading_cycle_executing:
            # 双重检查（另一个请求可能已经获取锁）
            log_print("[TRADING CYCLE] Another trading cycle started while waiting for lock, rejecting request")
            return JSONResponse(
                status_code=429,
                content={
                    "ok": False,
                    "error": "Trading cycle is already executing.",
                    "message": "Another trading cycle is in progress. Please try again later."
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        _trading_cycle_executing = True
        log_print("[TRADING CYCLE] Starting trading cycle execution (lock acquired)")
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.data.order_manager import OrderManager
        from datetime import time as dt_time, timedelta
        
        # 检查市场是否开盘（排除周末和节假日）
        from src.utils.trading_days import is_market_open as check_market_open
        now = datetime.now()
        is_market_open = check_market_open(now)
        
        # 从 config.json 读取配置
        config = load_trading_config()
        universe = config["universe"]
        tool_budget = config["tool_budget"]
        rounds = config["rounds"]
        
        log_print(f"[TRADING CYCLE] Tool budget: {tool_budget}, Rounds: {rounds}")
        
        # CRITICAL FIX: 市场收盘后，允许运行对话（AI分析），但不执行交易
        # 交易时段和收盘后都执行对话，但只有交易时段才执行交易
        # execute_daily_trade 内部会检查 is_market_open_for_simulation 来决定是否执行交易
        
        if not is_market_open:
            # 市场关闭：只运行对话和分析，不执行交易
            log_print(f"[TRADING CYCLE] Market is closed. Running analysis only (no trading)...")
        else:
            # 市场开放：运行对话并执行交易
            log_print(f"[TRADING CYCLE] Market is open. Executing trading cycle...")
        
        # 执行交易周期（包括对话和分析，交易执行由内部逻辑控制）
        try:
            result = execute_daily_trade(
                rounds=rounds,
                auto_tools=True,
                tool_budget=tool_budget,
                universe=universe
            )
            
            # 根据市场状态返回不同的消息
            if not is_market_open:
                message = "Analysis completed (market closed, no trades executed)"
            else:
                message = "Trading cycle completed"
            
            response = JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "message": message,
                    "result": result
                },
                headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                    }
                )
            return response
        except Exception as e:
            # 安全处理错误信息，移除emoji字符以避免Windows cp950编码问题
            import traceback
            error_msg = str(e)
            # 移除emoji字符（Unicode范围）
            import re
            error_msg = re.sub(r'[\U0001F300-\U0001F9FF]', '', error_msg)  # 移除emoji
            error_msg = re.sub(r'[\U0001FA00-\U0001FAFF]', '', error_msg)  # 移除扩展emoji
            
            # 打印详细错误信息到服务器日志
            log_print(f"[TRADING CYCLE] Error: {error_msg}")
            log_print(f"[TRADING CYCLE] Traceback: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": error_msg},
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
    finally:
        # 无论成功失败，都要释放执行标志
        _trading_cycle_executing = False
        log_print("[TRADING CYCLE] Trading cycle execution completed (lock released)")


@app.get("/api/portfolio/equity-history")
async def get_equity_history(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
):
    """
    Get portfolio equity history for chart visualization
    
    Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - limit: Maximum number of records to return
    """
    try:
        from src.data.equity_tracker import EquityTracker
        
        # CRITICAL: Use project root data/logs directory
        equity_tracker = EquityTracker(root=str(get_project_logs_dir()))
        records = equity_tracker.load_equity_history(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        return {
            "ok": True,
            "records": records,
            "count": len(records),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/current")
async def get_current_portfolio():
    """Get current portfolio status (from portfolio_state.json, fallback to equity_history if empty)"""
    try:
        import json
        from pathlib import Path
        from src.data.portfolio import Portfolio, Position
        from src.data.equity_tracker import EquityTracker
        
        # CRITICAL FIX: Load from portfolio_state.json, but if it's empty, try to recover from equity_history
        # Use absolute path to ensure correct file location
        _backend_dir = Path(__file__).resolve().parent.parent.parent  # Go up from src/api/server.py to backend/
        state_file = _backend_dir.parent / "data" / "logs" / "portfolio_state.json"
        
        # Try to load from portfolio_state.json first
        state = None
        if state_file.exists():
            log_print(f"[PORTFOLIO/CURRENT] Loading from: {state_file}")
            with state_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
            
            positions_count = len(state.get("positions", {}))
            log_print(f"[PORTFOLIO/CURRENT] Loaded state: cash={state.get('cash')}, positions={positions_count}")
            
            # If portfolio_state.json has positions, use it
            if positions_count > 0:
                # Create Portfolio object
                portfolio = Portfolio(
                    cash=float(state.get("cash", 10000.0)),
                    initial_value=float(state.get("initial_value", 10000.0)),
                )
                
                # Restore positions
                positions = state.get("positions", {})
                restored_count = 0
                for symbol, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        quantity = int(pos_info.get("quantity", 0))
                        avg_cost = float(pos_info.get("avg_cost", 0.0))
                        total_cost = float(pos_info.get("total_cost", 0.0))
                        if total_cost <= 0:
                            total_cost = avg_cost * quantity
                        
                        if quantity > 0:
                            portfolio._positions[symbol] = Position(
                                symbol=symbol,
                                quantity=quantity,
                                avg_cost=avg_cost,
                                total_cost=total_cost,
                            )
                            restored_count += 1
                
                log_print(f"[PORTFOLIO/CURRENT] Restored {restored_count} positions from portfolio_state.json")
                
                # Calculate current values
                portfolio_value = portfolio.value({})  # Use empty prices for now (just cost basis)
                equity_value = portfolio.equity_value({})
                total_value = portfolio.cash + equity_value
                
                # Build response
                positions_detail = {}
                for symbol, pos in portfolio._positions.items():
                    positions_detail[symbol] = {
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "total_cost": pos.total_cost,
                        "market_value": pos.quantity * pos.avg_cost,  # Use avg_cost as fallback
                    }
                
                portfolio_data = {
                    "date": date.today().isoformat(),
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "cash": round(portfolio.cash, 2),
                    "equity_value": round(equity_value, 2),
                    "total_value": round(total_value, 2),
                    "total_pnl": round(total_value - portfolio.initial_value, 2),
                    "total_pnl_pct": round(((total_value - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0, 2),
                    "positions": positions_detail,
                    "positions_count": len(portfolio._positions),
                }
                
                return {
                    "ok": True,
                    "portfolio": portfolio_data,
                }
        
        # FALLBACK: If portfolio_state.json is empty or missing, try to recover from equity_history
        log_print(f"[PORTFOLIO/CURRENT] portfolio_state.json is empty or missing, trying to recover from equity_history")
        # CRITICAL: Use project root data/logs directory
        equity_tracker = EquityTracker(root=str(get_project_logs_dir()))
        latest = equity_tracker.get_latest_equity()
        
        if latest and latest.get("positions_detail"):
            # Recover from equity_history
            positions_detail = latest.get("positions_detail", {})
            cash = latest.get("cash", 10000.0)
            total_value = latest.get("total_value", 10000.0)
            equity_value = latest.get("equity_value", 0.0)
            initial_value = latest.get("initial_value", 10000.0)
            
            log_print(f"[PORTFOLIO/CURRENT] Recovered from equity_history: cash={cash}, positions={len(positions_detail)}")
            
            portfolio_data = {
                "date": latest.get("date", date.today().isoformat()),
                "timestamp": latest.get("timestamp", datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')),
                "cash": round(cash, 2),
                "equity_value": round(equity_value, 2),
                "total_value": round(total_value, 2),
                "total_pnl": round(total_value - initial_value, 2),
                "total_pnl_pct": round(((total_value - initial_value) / initial_value * 100) if initial_value > 0 else 0, 2),
                "positions": positions_detail,
                "positions_count": len(positions_detail),
            }
            
            return {
                "ok": True,
                "portfolio": portfolio_data,
                "warning": "Recovered from equity_history (portfolio_state.json was empty or missing)",
            }
        
        # No data available
        return {
            "ok": True,
            "portfolio": None,
            "message": "No portfolio data available",
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.post("/api/trading/check-pending-orders")
async def check_pending_orders():
    """检查并结算今天的pending订单（交易时段使用）"""
    try:
        from src.data.order_manager import OrderManager
        from src.data.portfolio import Portfolio
        from datetime import date
        from pathlib import Path
        import json
        
        # CRITICAL: Use project root data/logs directory
        order_manager = OrderManager(root=str(get_project_logs_dir()))
        
        # 检查市场状态（允许在收盘后执行结算）
        now = datetime.now()
        is_market_open = order_manager._is_market_open(check_datetime=now)
        market_close_time = dt_time(16, 0)
        if not is_market_open and now.time() < market_close_time:
            return {
                "ok": True,
                "message": "Market not open yet, skipping pending order check",
                "settled_count": 0
            }
        if not is_market_open:
            log_print(f"[Check Pending Orders] Market closed, performing end-of-day settlement for {date.today().isoformat()}")
        
        # 获取今天的pending订单
        today = date.today().isoformat()
        pending_orders = order_manager.load_pending_orders(order_date=today)
        
        # 加载当前portfolio状态
        # CRITICAL: Use project root data/logs directory
        portfolio_file = get_project_logs_dir() / "portfolio_state.json"
        if not portfolio_file.exists():
            return {
                "ok": False,
                "error": "Portfolio state file not found"
            }
        
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        # 创建Portfolio对象
        current_portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # 恢复持仓
        from src.data.portfolio import Position
        for symbol, pos_info in state.get("positions", {}).items():
            if isinstance(pos_info, dict):
                qty = int(pos_info.get("quantity", 0))
                avg_cost = float(pos_info.get("avg_cost", 0))
                total_cost = float(pos_info.get("total_cost", 0))
                if total_cost <= 0:
                    total_cost = avg_cost * qty
                if qty > 0:
                    current_portfolio._positions[symbol] = Position(
                        symbol=symbol,
                        quantity=qty,
                        avg_cost=avg_cost,
                        total_cost=total_cost
                    )
        
        # CRITICAL FIX: 如果portfolio中没有持仓，但filled_orders中有今天的订单，需要恢复portfolio状态
        # 但是，不应该重新执行订单（因为现金已经被扣除过了），而是应该从filled_orders计算正确的现金和持仓
        if len(current_portfolio._positions) == 0:
            # CRITICAL: Use project root data/logs directory
            filled_file = get_project_logs_dir() / "filled_orders.jsonl"
            if filled_file.exists():
                try:
                    # 计算已成交订单的总成本和总收益
                    total_buy_cost = 0.0
                    total_sell_proceeds = 0.0
                    restored_positions = {}  # {symbol: {quantity, total_cost, avg_cost}}
                    
                    with filled_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                filled_order = json.loads(line)
                                if _get_order_date(filled_order) == today and filled_order.get("status") == "FILLED":
                                    symbol = filled_order.get("symbol")
                                    action = filled_order.get("action", "").upper()
                                    quantity = filled_order.get("quantity", 0)
                                    fill_price = filled_order.get("fill_price")
                                    if symbol and action and quantity > 0 and fill_price:
                                        if action == "BUY":
                                            cost = quantity * fill_price
                                            total_buy_cost += cost
                                            # 累加持仓（使用加权平均）
                                            if symbol in restored_positions:
                                                existing = restored_positions[symbol]
                                                total_qty = existing["quantity"] + quantity
                                                total_cost = existing["total_cost"] + cost
                                                avg_cost = total_cost / total_qty if total_qty > 0 else fill_price
                                                restored_positions[symbol] = {
                                                    "quantity": total_qty,
                                                    "total_cost": total_cost,
                                                    "avg_cost": avg_cost,
                                                }
                                            else:
                                                restored_positions[symbol] = {
                                                    "quantity": quantity,
                                                    "total_cost": cost,
                                                    "avg_cost": fill_price,
                                                }
                                        elif action == "SELL":
                                            proceeds = quantity * fill_price
                                            total_sell_proceeds += proceeds
                                            # 减少持仓
                                            if symbol in restored_positions:
                                                existing = restored_positions[symbol]
                                                if existing["quantity"] >= quantity:
                                                    remaining_qty = existing["quantity"] - quantity
                                                    if remaining_qty > 0:
                                                        # 按比例减少成本
                                                        cost_ratio = remaining_qty / existing["quantity"]
                                                        remaining_cost = existing["total_cost"] * cost_ratio
                                                        avg_cost = remaining_cost / remaining_qty if remaining_qty > 0 else existing["avg_cost"]
                                                        restored_positions[symbol] = {
                                                            "quantity": remaining_qty,
                                                            "total_cost": remaining_cost,
                                                            "avg_cost": avg_cost,
                                                        }
                                                    else:
                                                        # 全部卖出，移除持仓
                                                        del restored_positions[symbol]
                    
                    # 如果有恢复的持仓，更新portfolio状态
                    if restored_positions:
                        # 计算正确的现金：初始现金 - 买入成本 + 卖出收益
                        correct_cash = current_portfolio.initial_value - total_buy_cost + total_sell_proceeds
                        
                        # 确保现金不为负数（如果计算错误，至少保持为0）
                        if correct_cash < 0:
                            log_print(f"[Check Pending Orders] ⚠️ Warning: Calculated cash is negative (${correct_cash:.2f}), setting to 0")
                            correct_cash = 0.0
                        
                        # 更新portfolio现金
                        current_portfolio.cash = correct_cash
                        
                        # 恢复持仓（不调用buy/sell，直接设置）
                        from src.data.portfolio import Position
                        for symbol, pos_info in restored_positions.items():
                            current_portfolio._positions[symbol] = Position(
                                symbol=symbol,
                                quantity=pos_info["quantity"],
                                avg_cost=pos_info["avg_cost"],
                                total_cost=pos_info["total_cost"],
                            )
                        
                        # 保存portfolio状态
                        portfolio_state = {
                            "cash": current_portfolio.cash,
                            "initial_value": current_portfolio.initial_value,
                            "positions": {},
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        }
                        for symbol, pos in current_portfolio._positions.items():
                            portfolio_state["positions"][symbol] = {
                                "quantity": pos.quantity,
                                "avg_cost": pos.avg_cost,
                                "total_cost": pos.total_cost,
                            }
                        portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
                        log_print(f"[Check Pending Orders] ✅ Restored {len(current_portfolio._positions)} positions from filled orders (cash: ${correct_cash:.2f}, buy_cost: ${total_buy_cost:.2f}, sell_proceeds: ${total_sell_proceeds:.2f})")
                except Exception as e:
                    log_print(f"[Check Pending Orders] ⚠️ Warning: Failed to restore positions from filled orders: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 检查并结算订单
        settled_count = 0
        rejected_count = 0
        
        if not pending_orders:
            # 即使没有pending订单，也检查是否需要恢复持仓
            log_print(f"\n[Check Pending Orders] No pending orders for today ({today}), checking if portfolio needs restoration...")
        else:
            log_print(f"\n[Check Pending Orders] Checking {len(pending_orders)} pending orders for today ({today})...")
        
        for order in pending_orders:
            symbol = order.get("symbol")
            action = order.get("action", "").upper()
            quantity = order.get("quantity", 0)
            limit_price = order.get("limit_price", 0)
            order_id = order.get("order_id", "unknown")
            
            # CRITICAL: 检查订单是否已经在 filled_orders 中（防止重复执行）
            # CRITICAL: Use project root data/logs directory
            filled_file = get_project_logs_dir() / "filled_orders.jsonl"
            order_already_filled = False
            if filled_file.exists():
                try:
                    with filled_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                filled_order = json.loads(line)
                                if filled_order.get("order_id") == order_id and filled_order.get("status") == "FILLED":
                                    order_already_filled = True
                                    log_print(f"[Check Pending Orders] ⚠️ Order {order_id} already filled, skipping duplicate execution")
                                    break
                except Exception as e:
                    log_print(f"[Check Pending Orders] Warning: Failed to check filled orders: {e}")
            
            if order_already_filled:
                continue
            
            try:
                # CRITICAL FIX: 在市场收盘后，不应该再尝试结算订单
                # 如果市场已收盘，直接跳过订单结算，等待收盘后的清理逻辑处理
                if not is_market_open:
                    log_print(f"[Check Pending Orders] Market closed, skipping order {order_id} settlement (will be rejected at end-of-day cleanup)")
                    continue
                
                # 使用实时价格检查订单（只在市场开盘时）
                fill_result = order_manager.check_order_fill(order, today, use_realtime=True)
                
                # CRITICAL FIX: 再次检查市场状态，防止在市场收盘后执行订单
                # 如果市场已收盘，不应该执行订单，即使fill_result显示filled
                if not is_market_open:
                    log_print(f"[Check Pending Orders] Market closed during order check, skipping order {order_id} execution")
                    continue
                
                # 如果订单已成交，执行交易
                if fill_result.get("filled", False):
                    fill_price = fill_result.get("fill_price")
                    if fill_price:
                        # CRITICAL: 再次检查现金是否足够（防止重复执行导致现金为负）
                        if action == "BUY":
                            cost = quantity * fill_price
                            if cost > current_portfolio.cash:
                                log_print(f"[Check Pending Orders] ⚠️ Skipping {action} {quantity} {symbol}: insufficient cash (need ${cost:.2f}, have ${current_portfolio.cash:.2f})")
                                continue
                        
                        log_print(f"[Check Pending Orders] Executing {action} {quantity} {symbol} @ ${fill_price:.2f}...")
                        realized_pnl = None
                        if action == "BUY":
                            current_portfolio.buy(symbol, quantity, fill_price)
                        elif action == "SELL":
                            # 卖出时计算已实现损益
                            realized_pnl = current_portfolio.sell(symbol, quantity, fill_price)
                            log_print(f"[Check Pending Orders] Realized P&L: ${realized_pnl['realized_pnl']:.2f} ({realized_pnl['realized_pnl_pct']:+.2f}%)")
                        
                        # 标记订单为已成交（传递已实现损益）
                        order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl)
                        settled_count += 1
                        log_print(f"[Check Pending Orders] Order {order_id} executed successfully")
            except Exception as e:
                log_print(f"[Check Pending Orders] Error processing order {order_id}: {e}")
                import traceback
                traceback.print_exc()
                pass
        
        if not is_market_open:
            remaining_orders = order_manager.load_pending_orders(order_date=today)
            if remaining_orders:
                log_print(f"[Check Pending Orders] Cancelling {len(remaining_orders)} orders that remained pending after market close")
                for order in remaining_orders:
                    fill_result = {
                        "filled": False,
                        "fill_price": None,
                        "fill_reason": "Order expired at end of trading day without fill",
                        "daily_high": None,
                        "daily_low": None,
                        "current_price": None,
                    }
                    order_manager.mark_order_filled(order, fill_result)
                    rejected_count += 1
                log_print(f"[Check Pending Orders] ✅ Marked {rejected_count} orders as REJECTED after market close")
        
        pending_after_settlement = order_manager.load_pending_orders(order_date=today)
        
        if settled_count > 0:
            # 保存更新后的portfolio状态
            portfolio_state = {
                "cash": current_portfolio.cash,
                "initial_value": current_portfolio.initial_value,
                "positions": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            
            # 使用 _positions 来获取完整的 Position 对象
            for symbol, pos in current_portfolio._positions.items():
                portfolio_state["positions"][symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost,
                }
            
            portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
            log_print(f"[Check Pending Orders] Settled {settled_count} orders, portfolio updated")
            
            # 写入对话记录，说明订单已成交
            try:
                # CRITICAL: Use project root data/logs directory
                convo_file = get_project_logs_dir() / "discussion_actions.jsonl"
                convo_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 获取已成交的订单详情
                filled_orders_detail = []
                # CRITICAL: Use project root data/logs directory
                filled_file = get_project_logs_dir() / "filled_orders.jsonl"
                if filled_file.exists():
                    try:
                        with filled_file.open("r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    order = json.loads(line)
                                    if _get_order_date(order) == today and order.get("status") == "FILLED":
                                        filled_orders_detail.append(order)
                    except Exception:
                        pass
                
                # 只记录最近的成交订单（避免对话记录过长）
                recent_filled = filled_orders_detail[-settled_count:] if len(filled_orders_detail) >= settled_count else filled_orders_detail
                
                # 生成订单摘要
                order_summary = []
                for order in recent_filled:
                    symbol = order.get("symbol", "")
                    action = order.get("action", "").upper()
                    quantity = order.get("quantity", 0)
                    fill_price = order.get("fill_price", 0)
                    if symbol and quantity > 0 and fill_price > 0:
                        order_summary.append(f"{action} {quantity} {symbol} @ ${fill_price:.2f}")
                
                summary_text = f"Executed {settled_count} order(s): {', '.join(order_summary[:10])}"  # 最多显示10个
                if len(order_summary) > 10:
                    summary_text += f" and {len(order_summary) - 10} more"
                
                # 写入对话记录
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": today,
                    "agent": "OrderExecution",
                    "round": 0,
                    "content": summary_text,
                    "type": "execution",
                    "settled_count": settled_count,
                }
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
                log_print(f"[Check Pending Orders] Wrote execution conversation entry: {settled_count} orders filled")
            except Exception as e:
                log_print(f"[Check Pending Orders] Warning: Failed to write execution conversation: {e}")
                import traceback
                traceback.print_exc()
            
            # 更新当天的净值记录和每日记忆（如果有订单成交）
            try:
                from src.data.equity_tracker import EquityTracker
                from src.data.memory_manager import MemoryManager
                import yfinance as yf
                
                # 获取当前价格（优先使用实时价格，如果获取失败则使用平均成本价作为后备）
                last_prices = {}
                missing_prices = []
                for symbol in current_portfolio.positions.keys():
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.fast_info
                        price = info.get("lastPrice") or info.get("regularMarketPrice")
                        if price:
                            last_prices[symbol] = float(price)
                        else:
                            # 如果获取不到实时价格，使用平均成本价（但记录警告）
                            pos = current_portfolio._positions.get(symbol)
                            if pos:
                                last_prices[symbol] = pos.avg_cost
                                missing_prices.append(symbol)
                    except Exception as e:
                        # 如果获取失败，使用平均成本价
                        pos = current_portfolio._positions.get(symbol)
                        if pos:
                            last_prices[symbol] = pos.avg_cost
                            missing_prices.append(symbol)
                
                if missing_prices:
                    log_print(f"[Check Pending Orders] Warning: Could not fetch real-time prices for {len(missing_prices)} symbols, using avg_cost: {missing_prices}")
                
                # 计算净值
                equity_value = sum(
                    pos.quantity * last_prices.get(symbol, pos.avg_cost)
                    for symbol, pos in current_portfolio._positions.items()
                )
                total_value = current_portfolio.cash + equity_value
                total_pnl = total_value - current_portfolio.initial_value
                total_pnl_pct = (total_pnl / current_portfolio.initial_value * 100) if current_portfolio.initial_value > 0 else 0.0
                
                # 计算持仓P&L
                positions_pnl = {}
                positions_detail = {}
                for symbol, pos in current_portfolio._positions.items():
                    current_price = last_prices.get(symbol, pos.avg_cost)
                    market_value = pos.quantity * current_price
                    unrealized_pnl = market_value - pos.total_cost
                    unrealized_pnl_pct = (unrealized_pnl / pos.total_cost * 100) if pos.total_cost > 0 else 0.0
                    
                    positions_pnl[symbol] = {
                        "unrealized_pnl": round(unrealized_pnl, 2),
                        "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                    }
                    positions_detail[symbol] = {
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "current_price": current_price,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_pct": unrealized_pnl_pct,
                    }
                
                # 更新净值记录
                # CRITICAL: Use project root data/logs directory
                equity_tracker = EquityTracker(root=str(get_project_logs_dir()))
                portfolio_snapshot = {
                    "cash": current_portfolio.cash,
                    "equity_value": equity_value,
                    "total_value": total_value,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct,
                    "positions_detail": positions_detail,
                }
                equity_tracker.record_daily_equity(today, portfolio_snapshot)
                
                # 更新每日记忆（如果存在）
                # CRITICAL: Use project root data/logs directory
                memory_manager = MemoryManager(root=str(get_project_logs_dir()))
                daily_memory = memory_manager.load_daily_memory(today)
                if daily_memory:
                    # 获取已成交的订单（从filled_orders.jsonl读取）
                    filled_orders = []
                    # CRITICAL: Use project root data/logs directory
                    filled_file = get_project_logs_dir() / "filled_orders.jsonl"
                    if filled_file.exists():
                        try:
                            with filled_file.open("r", encoding="utf-8") as f:
                                for line in f:
                                    if line.strip():
                                        order = json.loads(line)
                                        if _get_order_date(order) == today and order.get("status") == "FILLED":
                                            filled_orders.append(order)
                        except Exception:
                            pass
                    
                    # 更新每日记忆中的成交明细和portfolio快照
                    daily_memory["executed_trades"] = filled_orders
                    daily_memory["portfolio_snapshot"] = portfolio_snapshot
                    daily_memory["executed_trades_count"] = len(filled_orders)
                    
                    # 重新保存
                    memory_file = memory_manager.daily_dir / f"{today}.json"
                    with memory_file.open("w", encoding="utf-8") as f:
                        json.dump(daily_memory, f, ensure_ascii=False, indent=2)
                    
                    log_print(f"[Check Pending Orders] Updated daily memory and equity record for {today}")
            except Exception as e:
                log_print(f"[Check Pending Orders] Warning: Failed to update daily records: {e}")
                import traceback
                traceback.print_exc()
        
        return {
            "ok": True,
            "message": f"Checked {len(pending_orders)} pending orders, {settled_count} filled, {rejected_count} rejected",
            "settled_count": settled_count,
            "rejected_count": rejected_count,
            "pending_count": len(pending_after_settlement)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/real-time")
async def get_real_time_portfolio():
    """Get real-time portfolio with current market prices"""
    try:
        import json
        from datetime import time as dt_time
        # Path 已经在文件顶部导入，不需要重新导入
        
        # 检查市场是否开盘 - 非交易时段不更新数据（排除周末和节假日）
        from src.utils.trading_days import is_market_open as check_market_open
        now = datetime.now()
        is_market_open = check_market_open(now)
        
        # Load portfolio state
        # CRITICAL: Use project root data/logs directory
        state_file = get_project_logs_dir() / "portfolio_state.json"
        if not state_file.exists():
            # Fallback to demo snapshot so the frontend can render
            from fastapi import Request
            demo = await demo_real_time_portfolio()  # type: ignore
            return demo
        
        with state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        from src.data.portfolio import Portfolio, Position
        portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # Restore positions
        positions = state.get("positions", {})
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                quantity = int(pos_info.get("quantity", 0))
                avg_cost = float(pos_info.get("avg_cost", 0.0))
                total_cost = float(pos_info.get("total_cost", 0.0))
                # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                if total_cost <= 0:
                    total_cost = avg_cost * quantity
                
                if quantity > 0:  # 只恢复有效持仓
                    portfolio._positions[symbol] = Position(
                        symbol=symbol,
                        quantity=quantity,
                        avg_cost=avg_cost,
                        total_cost=total_cost,
                    )
        
        # If there are no positions, avoid external data calls and return simple snapshot
        if len(portfolio._positions) == 0:
            total_value = portfolio.cash
            snapshot = {
                "ok": True,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "initial_value": portfolio.initial_value,
                "total_value": round(total_value, 2),
                "total_pnl": round(total_value - portfolio.initial_value, 2),
                "total_pnl_pct": 0.0,
                "cash": round(portfolio.cash, 2),
                "equity_value": 0.0,
                "positions": {},
                "positions_pnl": {},
                "source": "simple",
            }
        else:
            # 非交易时段：不更新数据，只返回已保存的快照
            if not is_market_open:
                # 获取最新快照（不更新）
                try:
                    from src.data.real_time_tracker import RealTimeTracker
                    # CRITICAL: Use project root data/logs directory
                    tracker = RealTimeTracker(root=str(get_project_logs_dir()))
                    snapshot = tracker.get_latest_snapshot()
                    if snapshot:
                        snapshot["ok"] = True
                        snapshot["source"] = "cached"
                        return {"ok": True, **snapshot}
                except Exception:
                    pass
                
                # 如果没有快照，返回静态数据（不更新价格）
                equity = sum((pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0)) for pos_info in positions.values() if isinstance(pos_info, dict))
                total_value = portfolio.cash + equity
                positions_detail = {}
                positions_pnl = {}
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0.0))
                        if total_cost <= 0:
                            total_cost = avg * qty
                        mv = avg * qty
                        cost_basis = total_cost
                        positions_detail[sym] = {
                            "quantity": qty,
                            "avg_cost": round(avg, 2),
                            "total_cost": round(total_cost, 2),
                            "cost_basis": round(cost_basis, 2),
                            "current_price": round(avg, 2),
                            "market_value": round(mv, 2),
                        }
                        unrealized_pnl = mv - cost_basis
                        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                        positions_pnl[sym] = {
                            "unrealized_pnl": round(unrealized_pnl, 2),
                            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                        }
                snapshot = {
                    "ok": True,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "initial_value": portfolio.initial_value,
                    "total_value": round(total_value, 2),
                    "total_pnl": round(total_value - portfolio.initial_value, 2),
                    "total_pnl_pct": round(((total_value - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0, 2),
                    "cash": round(portfolio.cash, 2),
                    "equity_value": round(equity, 2),
                    "positions": positions_detail,
                    "positions_pnl": positions_pnl,
                    "source": "static_after_hours",
                }
            else:
                # 交易时段：更新实时数据
                try:
                    from src.data.real_time_tracker import RealTimeTracker
                    # CRITICAL: Use project root data/logs directory
                    tracker = RealTimeTracker(root=str(get_project_logs_dir()))
                    # CRITICAL FIX: 强制记录净值，确保前端能看到最新变化
                    # 即使净值变化小于1%，也要记录（但限制频率：每30分钟最多记录一次）
                    snapshot = tracker.update_and_record(portfolio, force_record=False)
                    if snapshot:
                        snapshot["ok"] = True
                        # 额外检查：如果距离上次记录超过30分钟，强制记录一次
                        from src.data.equity_tracker import EquityTracker
                        # CRITICAL: Use project root data/logs directory
                        equity_tracker = EquityTracker(root=str(get_project_logs_dir()))
                        latest_equity = equity_tracker.get_latest_equity()
                        if latest_equity:
                            latest_timestamp_str = latest_equity.get("timestamp", "")
                            if latest_timestamp_str:
                                try:
                                    if "Z" in latest_timestamp_str:
                                        latest_timestamp = datetime.fromisoformat(latest_timestamp_str.replace("Z", "+00:00"))
                                    else:
                                        latest_timestamp = datetime.fromisoformat(latest_timestamp_str)
                                    now_utc = datetime.now(timezone.utc)
                                    if latest_timestamp.tzinfo:
                                        time_diff = now_utc - latest_timestamp
                                    else:
                                        latest_timestamp_utc = latest_timestamp.replace(tzinfo=timezone.utc)
                                        time_diff = now_utc - latest_timestamp_utc
                                    
                                    # 如果距离上次记录超过30分钟，强制记录一次
                                    if time_diff.total_seconds() >= 1800:  # 30分钟 = 1800秒
                                        equity_tracker.record_daily_equity(
                                            date_str=date.today().isoformat(),
                                            portfolio_snapshot=snapshot,
                                        )
                                        log_print(f"[REALTIME] Force recorded equity (30min interval): ${snapshot.get('total_value', 0):.2f}")
                                except Exception as e:
                                    log_print(f"[REALTIME] Error checking last record time: {e}")
                        return {"ok": True, **snapshot}
                except (ImportError, ModuleNotFoundError) as e:
                    # Fallback if yfinance or other deps missing
                    pass
                except Exception:
                    # Any other error, fallback to static data
                    pass
                
                # Fallback: 使用静态数据
                equity = sum((pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0)) for pos_info in positions.values() if isinstance(pos_info, dict))
                total_value = portfolio.cash + equity
                positions_detail = {}
                positions_pnl = {}
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0.0))
                        # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                        if total_cost <= 0:
                            total_cost = avg * qty
                        mv = avg * qty
                        cost_basis = total_cost
                        positions_detail[sym] = {
                            "quantity": qty,
                            "avg_cost": round(avg, 2),
                            "total_cost": round(total_cost, 2),
                            "cost_basis": round(cost_basis, 2),
                            "current_price": round(avg, 2),
                            "market_value": round(mv, 2),
                        }
                        # 计算P&L
                        unrealized_pnl = mv - cost_basis
                        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                        positions_pnl[sym] = {
                            "unrealized_pnl": round(unrealized_pnl, 2),
                            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                        }
                snapshot = {
                    "ok": True,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "initial_value": portfolio.initial_value,
                    "total_value": round(total_value, 2),
                    "total_pnl": round(total_value - portfolio.initial_value, 2),
                    "total_pnl_pct": round(((total_value - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0, 2),
                    "cash": round(portfolio.cash, 2),
                    "equity_value": round(equity, 2),
                    "positions": positions_detail,
                    "positions_pnl": positions_pnl,
                    "source": "simple",
                }
        
        # 确保返回的数据包含 CORS 头
        return JSONResponse(
            status_code=200,
            content={"ok": True, **snapshot},
            headers=CORS_HEADERS.copy()
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
            headers=CORS_HEADERS.copy()
        )


@app.get("/api/portfolio/recent-snapshots")
async def get_recent_snapshots(hours: int = 24):
    """Get recent real-time snapshots"""
    try:
        from src.data.real_time_tracker import RealTimeTracker
        # CRITICAL: Use project root data/logs directory
        tracker = RealTimeTracker(root=str(get_project_logs_dir()))
        snapshots = tracker.get_recent_snapshots(hours=hours)
        return {"ok": True, "snapshots": snapshots, "count": len(snapshots)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/vix/term")
async def get_vix_term():
    """Get VIX term structure data"""
    try:
        from src.tools.sentiment_tools import vix_term_structure, vix_risk_score
        vix_data = vix_term_structure()
        
        # Check if we got valid data
        if vix_data and vix_data.get("vix") is not None:
            # Add risk score
            vix_data["vix_risk_score"] = vix_risk_score(vix_data)
            
            # Add term structure interpretation
            ratio = vix_data.get("ratio")
            if ratio is not None:
                if ratio > 1.0:
                    vix_data["term_structure"] = "Contango"
                elif ratio < 1.0:
                    vix_data["term_structure"] = "Backwardation"
                else:
                    vix_data["term_structure"] = "Flat"
            
            return JSONResponse(
                status_code=200,
                content=vix_data,
                headers=CORS_HEADERS.copy()
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "VIX data not available"},
                headers=CORS_HEADERS.copy()
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers=CORS_HEADERS.copy()
        )


@app.get("/api/fear-greed")
async def get_fear_greed():
    """Get Fear & Greed Index data"""
    try:
        from src.tools.sentiment_tools import fetch_fear_greed
        fg_data = fetch_fear_greed()
        
        # fetch_fear_greed 返回的格式可能是：
        # 1. {"fear_greed": {...}} (如果已经包装)
        # 2. {"value": ..., "label": ..., ...} (如果直接返回)
        # 统一转换为 {"fear_greed": {...}} 格式
        
        result = {}
        if fg_data:
            # 如果已经有 fear_greed 字段，直接使用
            if "fear_greed" in fg_data:
                result = fg_data
            # 如果直接返回了 value/label 等字段，包装成 fear_greed
            elif "value" in fg_data or "label" in fg_data:
                result = {
                    "fear_greed": fg_data
                }
            else:
                # 空数据，返回默认值
                result = {
                    "fear_greed": {
                        "value": 0,
                        "label": "N/A",
                        "source": "unknown"
                    }
                }
        else:
            # 返回空数据而不是 404，让前端可以显示默认值
            result = {
                "fear_greed": {
                    "value": 0,
                    "label": "N/A",
                    "source": "unknown"
                }
            }
        
        return JSONResponse(
            status_code=200,
            content=result,
            headers=CORS_HEADERS.copy()
        )
    except Exception as e:
        # 即使出错也返回默认值，而不是 500 错误
        log_print(f"[API] Error fetching Fear & Greed: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "fear_greed": {
                    "value": 0,
                    "label": "N/A",
                    "source": "error",
                    "error": str(e)
                }
            },
            headers=CORS_HEADERS.copy()
        )


@app.options("/api/tools/list")
async def tools_list_options():
    """Handle CORS preflight for tools list endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/api/tools/list")
async def list_tools():
    """List all available tools from ToolBox"""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    try:
        import sys
        from pathlib import Path
        # Ensure we're in the backend directory
        backend_dir = Path(__file__).parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        from src.agents.toolbox import ToolBox
        toolbox = ToolBox()
        tools = toolbox.list()
        log_print(f"[API] Tools list: {len(tools)} tools found")
        return JSONResponse(
            status_code=200,
            content={"ok": True, "tools": tools},
            headers=cors_headers
        )
    except Exception as e:
        import traceback
        error_msg = str(e)
        # Remove emoji characters to avoid encoding issues
        import re
        error_msg = re.sub(r'[\U0001F300-\U0001F9FF]', '', error_msg)
        error_msg = re.sub(r'[\U0001FA00-\U0001FAFF]', '', error_msg)
        log_print(f"[API] Error listing tools: {error_msg}")
        log_print(f"[API] Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=200,
            content={"ok": True, "tools": [], "error": error_msg},
            headers=cors_headers
        )


@app.get("/api/demo/real-time")
async def demo_real_time_portfolio(volatility_bps: int = 15):
    """Generate a simulated real-time portfolio snapshot (demo mode).

    - Updates every call with a small random walk on prices
    - Persists last demo prices to data/logs/demo_prices.json
    - Appends snapshot to data/logs/real_time_snapshots.jsonl
    - Returns the same schema as /api/portfolio/real-time

    volatility_bps: per-tick volatility in basis points (default 15bps = 0.15%)
    """
    try:
        import json
        from datetime import datetime

        # CRITICAL: Use project root data/logs directory
        logs_dir = get_project_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Load portfolio state; create a demo one if not exists
        state_file = logs_dir / "portfolio_state.json"
        if state_file.exists():
            with state_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            # Seed a simple demo portfolio
            state = {
                "cash": 2500.0,
                "initial_value": 10000.0,
                "positions": {
                    "NVDA": {"quantity": 5, "avg_cost": 900.0, "total_cost": 4500.0},
                    "MSFT": {"quantity": 7, "avg_cost": 420.0, "total_cost": 2940.0},
                    "AAPL": {"quantity": 10, "avg_cost": 190.0, "total_cost": 1900.0},
                },
            }

        positions: Dict[str, Any] = state.get("positions", {})

        # Load or initialize last demo prices
        demo_prices_file = logs_dir / "demo_prices.json"
        if demo_prices_file.exists():
            with demo_prices_file.open("r", encoding="utf-8") as f:
                last_prices: Dict[str, float] = json.load(f)
        else:
            last_prices = {sym: float(info.get("avg_cost", 0.0)) for sym, info in positions.items()}

        # Simulate price changes with random walk
        sigma = max(1, int(volatility_bps)) / 10000.0  # convert bps to fraction
        new_prices: Dict[str, float] = {}
        for sym, info in positions.items():
            base = float(last_prices.get(sym, info.get("avg_cost", 0.0)) or info.get("avg_cost", 0.0))
            # random change in +/- ~3 sigma cap
            drift = random.uniform(-3*sigma, 3*sigma)
            price = max(0.01, base * (1.0 + drift))
            new_prices[sym] = round(price, 4)

        # Build portfolio snapshot
        cash = float(state.get("cash", 0.0))
        initial_value = float(state.get("initial_value", 10000.0))
        positions_detail: Dict[str, Any] = {}
        positions_pnl: Dict[str, Any] = {}
        equity_value = 0.0
        total_unrealized = 0.0

        for sym, info in positions.items():
            qty = int(info.get("quantity", 0))
            avg = float(info.get("avg_cost", 0.0))
            px = float(new_prices.get(sym, avg))
            mv = qty * px
            equity_value += mv
            unreal = (px - avg) * qty
            total_unrealized += unreal
            pnl_pct = ((px - avg) / avg * 100.0) if avg > 0 else 0.0

            positions_detail[sym] = {
                "quantity": qty,
                "avg_cost": round(avg, 4),
                "current_price": round(px, 4),
                "market_value": round(mv, 2),
            }
            positions_pnl[sym] = {
                "unrealized_pnl": round(unreal, 2),
                "unrealized_pnl_pct": round(pnl_pct, 3),
            }

        total_value = cash + equity_value
        total_pnl = total_value - initial_value
        total_pnl_pct = (total_pnl / initial_value * 100.0) if initial_value > 0 else 0.0

        snapshot = {
            "ok": True,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "initial_value": round(initial_value, 2),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 3),
            "cash": round(cash, 2),
            "equity_value": round(equity_value, 2),
            "positions": positions_detail,
            "positions_pnl": positions_pnl,
            "source": "demo",
        }

        # Persist latest prices
        with demo_prices_file.open("w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=2)

        # Append to real-time snapshots jsonl
        rts_file = logs_dir / "real_time_snapshots.jsonl"
        with rts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

        return snapshot
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post("/api/demo/conversation-tick")
async def demo_conversation_tick():
    """Append a synthetic agent conversation entry for demo display.

    This helps the frontend Conversations modal show activity in demo mode.
    """
    try:
        import json
        from datetime import datetime

        # CRITICAL: Use project root data/logs directory
        logs_dir = get_project_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        convo_file = logs_dir / "discussion_actions.jsonl"

        agents = [
            "MarketAgent",
            "MarketAnalyst",
            "DiscussionAgent",
            "RiskAnalyst",
            "TraderAgent",
        ]
        messages = [
            "Scanning market breadth & volatility regime...",
            "Top signals: momentum up, looking at NVDA/MSFT/AAPL weighting...",
            "Consensus forming: mild bullish with hedged exposure.",
            "Risk limits OK. Position size within constraints.",
            "Placing demo limit orders within price bands.",
        ]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "agent": random.choice(agents),
            "round": random.randint(1, 3),
            "content": random.choice(messages),
            "type": "demo",
        }

        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {"ok": True, "written": True, "entry": entry}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = 100):
    """Return recent trade records from logs (filled, pending, and general)."""
    try:
        import json
        from datetime import datetime

        # CRITICAL: Use project root data/logs directory explicitly
        logs_dir = get_project_logs_dir()
        
        trades_file = logs_dir / "trades.jsonl"
        filled_file = logs_dir / "filled_orders.jsonl"
        pending_file = logs_dir / "pending_orders.jsonl"

        def read_jsonl(path: Path, max_lines: int = None) -> list[dict]:
            """Read JSONL file, optionally only reading the last N lines for performance."""
            if not path.exists():
                return []
            items: list[dict] = []
            try:
                with path.open("r", encoding="utf-8") as f:
                    if max_lines:
                        # CRITICAL FIX: Optimize for large files - read from end
                        # Read last max_lines * 2 to ensure we have enough after filtering
                        f.seek(0, 2)  # Seek to end
                        file_size = f.tell()
                        if file_size == 0:
                            return []
                        
                        # Read backwards in chunks
                        chunk_size = min(8192, file_size)
                        position = max(0, file_size - chunk_size * 20)  # Read last ~160KB
                        f.seek(position)
                        lines = f.readlines()
                        # Only process the last max_lines
                        for line in lines[-max_lines:] if len(lines) > max_lines else lines:
                            if not line.strip():
                                continue
                            try:
                                items.append(json.loads(line.strip()))
                            except Exception:
                                continue
                    else:
                        # Read entire file (for small files or when limit not specified)
                        for line in f:
                            if not line.strip():
                                continue
                            try:
                                items.append(json.loads(line.strip()))
                            except Exception:
                                continue
            except Exception as e:
                # If file reading fails, return empty list
                print(f"[WARNING] Failed to read {path}: {e}")
                return []
            return items

        # CRITICAL FIX: Only read last N lines from each file for performance
        # Read 3x limit to ensure we have enough after merging and deduplication
        read_limit = limit * 3
        trades = read_jsonl(trades_file, max_lines=read_limit)
        filled = read_jsonl(filled_file, max_lines=read_limit)
        pending = read_jsonl(pending_file, max_lines=read_limit)

        # normalize and merge
        records: list[dict] = []
        def norm(x: dict, source: str) -> dict:
            # 对于pending订单，确保状态是PENDING而不是FILLED
            status = x.get("status", "")
            if source == "pending" or status.upper() == "PENDING":
                final_status = "PENDING"
            elif source == "filled" or status.upper() == "FILLED":
                final_status = "FILLED"
            else:
                final_status = status or ("FILLED" if source == "filled" else x.get("state", "PENDING"))
            
            # 提取已实现损益（仅SELL订单有值）
            realized_pnl = None
            realized_pnl_pct = None
            if source == "filled" and x.get("action") == "SELL":
                realized_pnl = x.get("realized_pnl")
                realized_pnl_pct = x.get("realized_pnl_pct")
            
            return {
                "timestamp": x.get("timestamp") or x.get("time") or x.get("date") or x.get("placed_at") or x.get("filled_at"),
                "symbol": x.get("symbol") or x.get("ticker"),
                "side": x.get("side") or x.get("action"),
                "quantity": x.get("quantity") or x.get("qty"),
                "price": x.get("price") or x.get("fill_price") or x.get("limit_price") or x.get("avg_price"),
                "fill_price": x.get("fill_price"),  # 添加fill_price字段
                "status": final_status,
                "order_id": x.get("order_id") or x.get("id"),
                "source": source,
                "placed_at": x.get("placed_at"),  # 添加placed_at字段
                "filled_at": x.get("filled_at"),  # 添加filled_at字段
                "order_date": x.get("order_date"),  # 添加order_date字段
                "realized_pnl": realized_pnl,  # 已实现损益（仅SELL订单）
                "realized_pnl_pct": realized_pnl_pct,  # 已实现损益百分比（仅SELL订单）
                "details": x,
            }

        for x in trades[-limit:]:
            records.append(norm(x, "trades"))
        for x in filled[-limit:]:
            records.append(norm(x, "filled"))
        for x in pending[-limit:]:
            records.append(norm(x, "pending"))

        # sort by timestamp desc
        def ts_key(r: dict):
            t = r.get("timestamp") or ""
            try:
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            except Exception:
                return datetime.min
        records.sort(key=ts_key, reverse=True)

        return {"ok": True, "trades": records[:limit], "count": len(records[:limit])}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.get("/api/system/info")
async def get_system_info():
    """Get system information including LLM model and configuration"""
    try:
        import json
        # Path 已经在文件顶部导入，不需要重复导入
        
        # Load config.json (use absolute path to ensure correct location)
        # Try multiple possible paths
        config_file = None
        possible_paths = [
            Path("config/config.json"),  # Relative from project root
            Path(__file__).parent.parent.parent / "config" / "config.json",  # Absolute from this file
            Path("backend/config/config.json"),  # Relative from backend directory
        ]
        
        for path in possible_paths:
            if path.exists():
                config_file = path
                break
        
        llm_config = {}
        config = {}
        if config_file and config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                config = json.load(f)
                llm_config = config.get("llm", {})
                print(f"[SYSTEM INFO] Loaded config from: {config_file}")
                print(f"[SYSTEM INFO] LLM default_model: {llm_config.get('default_model', 'NOT FOUND')}")
        else:
            print(f"[SYSTEM INFO WARNING] Config file not found. Tried paths: {possible_paths}")
        
        # Load agents.yaml to get agent-specific models
        agent_models = {}
        try:
            # Path 已经在文件顶部导入，不需要重复导入
            import yaml
            
            agents_file = Path("config/agents.yaml")
            if agents_file.exists():
                with agents_file.open("r", encoding="utf-8") as f:
                    agents_conf = yaml.safe_load(f)
                    if agents_conf:
                        for agent_key, agent_conf in agents_conf.items():
                            if isinstance(agent_conf, dict):
                                agent_models[agent_key] = agent_conf.get("model", llm_config.get("default_model", "llama3.1"))
        except Exception:
            pass
        
        return {
            "ok": True,
            "llm": {
                "default_model": llm_config.get("default_model", "llama3.1"),
                "ollama_host": llm_config.get("ollama_host", "http://localhost:11434"),
                "auto_pull": llm_config.get("auto_pull", True),
            },
            "agent_models": agent_models,
            "config": {
                "discussion_rounds": config.get("discussion_rounds", 3),
                "discussion_tool_budget": config.get("discussion_tool_budget", 2),
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/agents/conversations")
async def get_agent_conversations(
    limit: int = 50,
    date: str | None = None,
    include_demo: bool = False,
):
    """Get recent agent conversations/discussions"""
    try:
        import json
        from pathlib import Path
        
        # Load from discussion_actions.jsonl
        # CRITICAL: Use project root data/logs directory explicitly
        logs_dir = get_project_logs_dir()
        log_file = logs_dir / "discussion_actions.jsonl"
        
        conversations = []
        
        if log_file and log_file.exists():
            try:
                # CRITICAL FIX: Optimize file reading - read from end instead of loading entire file
                # This prevents memory issues and connection resets with large files
                with log_file.open("r", encoding="utf-8") as f:
                    # Read file in chunks from the end (more efficient for large files)
                    # Read last 500 lines max to avoid memory issues
                    try:
                        # Use seek to read from end
                        f.seek(0, 2)  # Seek to end
                        file_size = f.tell()
                        
                        # Read backwards in chunks
                        chunk_size = min(8192, file_size)  # 8KB chunks
                        position = max(0, file_size - chunk_size * 10)  # Read last ~80KB
                        f.seek(position)
                        lines = f.readlines()
                        
                        # Process lines in reverse (newest first)
                        for line in reversed(lines[-limit * 3:]):  # Get more lines, then filter
                            if len(conversations) >= limit * 2:  # Stop if we have enough
                                break
                            try:
                                entry = json.loads(line.strip())
                                if not entry:  # Skip empty entries
                                    continue
                                if date:
                                    entry_date = entry.get("date", entry.get("timestamp", ""))
                                    if entry_date and not entry_date.startswith(date):
                                        continue
                                # Exclude demo entries unless explicitly requested
                                if not include_demo and entry.get("type") == "demo":
                                    continue
                                conversations.append(entry)
                            except (json.JSONDecodeError, ValueError, TypeError):
                                continue
                    except (OSError, IOError) as e:
                        # Fallback: if seek fails, use simple readlines but limit
                        log_print(f"[WARN] Failed to read file efficiently: {e}, using fallback")
                        f.seek(0)
                        lines = f.readlines()
                        for line in reversed(lines[-limit * 3:]):
                            if len(conversations) >= limit * 2:
                                break
                            try:
                                entry = json.loads(line.strip())
                                if not entry:
                                    continue
                                if date:
                                    entry_date = entry.get("date", entry.get("timestamp", ""))
                                    if entry_date and not entry_date.startswith(date):
                                        continue
                                if not include_demo and entry.get("type") == "demo":
                                    continue
                                conversations.append(entry)
                            except (json.JSONDecodeError, ValueError, TypeError):
                                continue
            except Exception as e:
                log_print(f"[WARN] Failed to read conversation file: {e}")
                conversations = []
        
        # Also try to load from memory if available (but limit to avoid performance issues)
        # CRITICAL FIX: Only load from memory if we don't have enough conversations from file
        if len(conversations) < limit:
            try:
                from src.data.memory_manager import MemoryManager
                # Use the same logs directory we found above
                # CRITICAL: Use project root data/logs directory
                memory_root = str(get_project_logs_dir())
                memory_manager = MemoryManager(root=memory_root)
                
                # CRITICAL FIX: Reduce days to avoid loading too much data
                # Only load last 7 days instead of 30 to prevent memory issues
                recent_memories = memory_manager.load_recent_memories(days=7)  # Reduced from 30 to 7
                memory_count = 0
                max_memory_items = limit - len(conversations)  # Only fill up to limit
                
                for memory in recent_memories:
                    if memory_count >= max_memory_items:  # Stop if we've reached the limit
                        break
                    discussion = memory.get("discussion", {})
                    if discussion:
                        transcript = discussion.get("transcript", [])
                        if transcript:
                            # Extract individual messages from transcript
                            for msg in transcript:
                                if isinstance(msg, dict) and memory_count < max_memory_items:
                                    conversations.append({
                                        "date": memory.get("date", ""),
                                        "type": "memory",
                                        "agent": msg.get("agent", "Unknown"),
                                        "content": msg.get("content", msg.get("message", "")),
                                        "round": msg.get("round"),
                                    })
                                    memory_count += 1
            except Exception as e:
                log_print(f"[WARN] Failed to load from memory: {e}")

        # Sort by date (newest first)
        conversations.sort(
            key=lambda x: x.get("timestamp", x.get("date", "")), 
            reverse=True
        )
        
        # Limit results (避免前端性能問題)
        limited_conversations = conversations[:limit]
        total_count = len(conversations)
        
        return {
            "ok": True,
            "conversations": limited_conversations,
            "count": len(limited_conversations),
            "total": total_count,  # 總數（用於前端顯示"還有更多"）
            "has_more": total_count > limit
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/market/is-open")
async def is_market_open():
    """Market hour check: Trading days (Mon-Fri excluding holidays), 09:30-16:00 Eastern Time (EST/EDT)."""
    try:
        from src.utils.trading_days import is_market_open as check_market_open
        import pytz
        
        now = datetime.now()
        open_now = check_market_open(now)
        
        # Get Eastern Time for display
        et_tz = pytz.timezone('America/New_York')
        if now.tzinfo is None:
            # Assume local time, convert to ET
            try:
                import time
                offset_seconds = -time.timezone if time.daylight == 0 else -time.altzone
                from datetime import timedelta, timezone as dt_timezone
                local_tz = dt_timezone(timedelta(seconds=offset_seconds))
                now_with_tz = now.replace(tzinfo=local_tz)
            except:
                now_with_tz = pytz.UTC.localize(now)
        else:
            now_with_tz = now
        et_now = now_with_tz.astimezone(et_tz)
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True, 
                "open": open_now, 
                "now": now.isoformat(),
                "local_time": now.strftime('%Y-%m-%d %H:%M:%S'),
                "eastern_time": et_now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "eastern_time_iso": et_now.isoformat(),
                "market_hours": "9:30 AM - 4:00 PM ET"
            },
            headers=CORS_HEADERS.copy()
        )
    except Exception as e:
        log_print(f"[API] Error checking market status: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
            headers=CORS_HEADERS.copy()
        )


@app.options("/api/system/init")
async def system_init_options():
    """Handle CORS preflight for system init"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/system/init")
async def system_init(force: bool = False):
    """Reset logs and initialize portfolio to defaults, then seed minimal data.
    
    This will DELETE ALL:
    - Trading history
    - Conversation logs
    - Pending orders
    - Portfolio records
    - Memory files
    
    CRITICAL: This will overwrite portfolio_state.json!
    If portfolio has positions, a backup will be created automatically.
    
    Args:
        force: If True, proceed without checking. If False, will create backup if portfolio has positions.
    """
    # CRITICAL: Use project root data/logs directory explicitly
    # Determine project root: go up from backend/src/api/server.py to project root
    _backend_dir = Path(__file__).resolve().parent.parent.parent  # backend/
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_print(f"[SYSTEM INIT] Using logs directory: {logs_dir}")
    
    # CRITICAL FIX: Check if portfolio has positions before initializing
    # If it does, create a backup automatically
    backup_created = False
    backup_filename = None
    portfolio_file = logs_dir / "portfolio_state.json"
    if portfolio_file.exists():
        try:
            with portfolio_file.open("r", encoding="utf-8") as f:
                existing_state = json.load(f)
            existing_positions = existing_state.get("positions", {})
            existing_cash = existing_state.get("cash", 0.0)
            existing_total_value = existing_state.get("total_value", 0.0)
            
            if len(existing_positions) > 0 or existing_cash != 10000.0 or existing_total_value != 10000.0:
                # Portfolio has data - create backup
                from datetime import datetime
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = logs_dir / f"portfolio_state_backup_{backup_timestamp}.json"
                
                # Copy current state to backup
                import shutil
                shutil.copy2(portfolio_file, backup_file)
                backup_created = True
                backup_filename = backup_file.name
                
                log_print(f"[SYSTEM INIT] WARNING: Portfolio has {len(existing_positions)} positions, cash=${existing_cash:.2f}, total_value=${existing_total_value:.2f}")
                log_print(f"[SYSTEM INIT] Backup created: {backup_file.name}")
        except Exception as e:
            log_print(f"[SYSTEM INIT] Warning: Failed to check/create backup: {e}")
    
    # Clear ALL log files including memory files
    files_to_clear = [
        "equity_history.jsonl", "filled_orders.jsonl", "pending_orders.jsonl",
        "trades.jsonl", "real_time_snapshots.jsonl", "monitoring.jsonl",
        "discussion_actions.jsonl", "last_trade_date.txt",
        "events.jsonl",  # Events log
        "demo_prices.json",  # Demo prices cache
        "workflow_summary.json",  # Workflow summary
    ]
    
    # Also clear any .jsonl files that might exist (comprehensive cleanup)
    for jsonl_file in logs_dir.glob("*.jsonl"):
        if jsonl_file.name not in ["discussion_actions.jsonl"]:  # Will be recreated
            try:
                jsonl_file.unlink()
                log_print(f"[SYSTEM INIT] Cleared: {jsonl_file.name}")
            except Exception:
                pass
    
    # Clear any .json files except portfolio_state.json (will be recreated) and backups
    for json_file in logs_dir.glob("*.json"):
        if json_file.name not in ["portfolio_state.json"] and "backup" not in json_file.name.lower():
            try:
                json_file.unlink()
                log_print(f"[SYSTEM INIT] Cleared: {json_file.name}")
            except Exception:
                pass
    
    # Clear memory files (daily and weekly)
    try:
        from src.data.memory_manager import MemoryManager
        # CRITICAL: Use the same logs_dir path (project root data/logs)
        memory_manager = MemoryManager(root=str(logs_dir))
        # Clear all memory files
        memory_dir = logs_dir
        for memory_file in memory_dir.glob("memory_*.jsonl"):
            try:
                memory_file.unlink()
            except Exception:
                pass
        for memory_file in memory_dir.glob("memory_weekly_*.jsonl"):
            try:
                memory_file.unlink()
            except Exception:
                pass
        
        # Clear daily memory directory
        daily_memory_dir = memory_dir / "memory" / "daily"
        if daily_memory_dir.exists():
            for daily_file in daily_memory_dir.glob("*.json"):
                try:
                    daily_file.unlink()
                except Exception:
                    pass
        
        # Clear weekly memory directory
        weekly_memory_dir = memory_dir / "memory" / "weekly"
        if weekly_memory_dir.exists():
            for weekly_file in weekly_memory_dir.glob("*.json"):
                try:
                    weekly_file.unlink()
                except Exception:
                    pass
        
        # Clear monthly memory directory
        monthly_memory_dir = memory_dir / "memory" / "monthly"
        if monthly_memory_dir.exists():
            for monthly_file in monthly_memory_dir.glob("*.json"):
                try:
                    monthly_file.unlink()
                except Exception:
                    pass
        
        # Clear memory index directory
        memory_index_dir = memory_dir / "memory" / "index"
        if memory_index_dir.exists():
            for index_file in memory_index_dir.glob("*.json"):
                try:
                    index_file.unlink()
                except Exception:
                    pass
    except Exception:
        pass
    
    # Clear any backup files (optional - keep them for safety, but can clear old ones)
    # Uncomment below if you want to clear old backup files during init
    # for backup_file in logs_dir.glob("portfolio_state_backup_*.json"):
    #     try:
    #         backup_file.unlink()
    #     except Exception:
    #         pass
    
    # Clear equity history (EquityTracker uses equity_history.jsonl)
    # This is already in files_to_clear, but ensure it's cleared
    equity_file = logs_dir / "equity_history.jsonl"
    if equity_file.exists():
        try:
            equity_file.unlink()
        except Exception:
            pass
    
    # Clear key log files (already handled by glob above, but keep for explicit list)
    for name in files_to_clear:
        p = logs_dir / name
        if p.exists():
            try:
                p.unlink()
                log_print(f"[SYSTEM INIT] Cleared: {name}")
            except Exception:
                pass
    
    # Initialize empty discussion file
    (logs_dir / "discussion_actions.jsonl").touch(exist_ok=True)

    # Create a clean portfolio: all cash, no positions
    state = {
        "cash": 10000.0,
        "initial_value": 10000.0,
        "total_value": 10000.0,  # Add total_value for consistency
        "positions": {},
    }
    with (logs_dir / "portfolio_state.json").open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    # Record initial equity history entry (for chart display)
    snapshot = {
        "cash": 10000.0,
        "equity_value": 0.0,
        "total_value": 10000.0,
        "total_pnl": 0.0,
        "total_pnl_pct": 0.0,
        "positions_detail": {},
    }
    try:
        from src.data.equity_tracker import EquityTracker
        # CRITICAL: Use the same logs_dir path (project root data/logs)
        equity_tracker = EquityTracker(root=str(logs_dir))
        equity_tracker.record_daily_equity(date.today().isoformat(), snapshot)
    except Exception as e:
        log_print(f"[Init] Warning: Failed to record initial equity: {e}")
    
    # Return result with backup information
    response_data = {
        "ok": True,
        "message": "System initialized successfully",
        "note": "First trade after initialization must be triggered manually. Auto-trading will resume after the first manual trade."
    }
    
    if backup_created:
        response_data["backup_created"] = True
        response_data["backup_filename"] = backup_filename
        response_data["warning"] = f"Portfolio backup created: {backup_filename}"
    
    # CRITICAL: After initialization, do NOT automatically execute trading cycle
    # User must manually trigger the first trade. After that, auto-trading will resume normally.
    # This ensures user has control over the first trade after initialization.
    log_print("[SYSTEM INIT] Initialization complete. First trade must be triggered manually.")
    log_print("[SYSTEM INIT] Auto-trading will resume normally after the first manual trade.")
    
    # No automatic trading after initialization - user must trigger first trade manually
    response_data["auto_ran"] = False
    
    # Return with CORS headers
    return JSONResponse(
        status_code=200,
        content=response_data,
        headers=CORS_HEADERS.copy()
    )


@app.post("/api/trading/run-loop")
async def run_trading_loop():
    """Kick one trading cycle, but block if already executed today or market is closed."""
    # Check if market is open first (excluding weekends and holidays)
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_open = check_market_open(now)
    
    if not is_open:
        return {
            "ok": False, 
            "blocked": True, 
            "reason": "market_closed", 
            "message": "Market is closed. Trading only available Mon-Fri, 9:30 AM - 4:00 PM EST"
        }
    
    # CRITICAL: Use project root data/logs directory explicitly
    logs_dir = get_project_logs_dir()
    flag = logs_dir / "last_trade_date.txt"
    today = datetime.now().strftime("%Y-%m-%d")
    if flag.exists():
        last = flag.read_text(encoding="utf-8").strip()
        if last == today:
            return {"ok": False, "blocked": True, "reason": "already_executed_today", "date": today}
    
    # run once
    try:
        res = await execute_trading_cycle()
        
        # If execute_trading_cycle returned a JSONResponse (error), extract error
        if isinstance(res, JSONResponse):
            error_body = res.body.decode('utf-8') if hasattr(res.body, 'decode') else str(res.body)
            try:
                error_data = json.loads(error_body)
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": error_data.get("error", "Unknown error"), "date": today}
                )
            except:
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": "Trading cycle failed", "date": today}
                )
        
        # Success - write flag
        try:
            flag.write_text(today, encoding="utf-8")
        except Exception as e:
            log_print(f"[WARN] Failed to write last_trade_date.txt: {e}")
        
        return {"ok": True, "result": res, "date": today}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "traceback": traceback.format_exc(), "date": today}
        )


@app.post("/api/demo/seed-conversations")
async def seed_conversations(n: int = 10):
    """Generate N demo conversation entries quickly."""
    for _ in range(max(1, n)):
        await demo_conversation_tick()
    return {"ok": True, "written": n}


@app.options("/api/data/upload")
async def upload_data_options():
    """Handle CORS preflight for data upload endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/api/trades/realized-pnl")
async def get_realized_pnl(
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100
):
    """查询历史已实现损益记录
    
    参数:
    - date: 查询特定日期 (YYYY-MM-DD)
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - limit: 返回记录数量限制
    
    返回:
    - 已实现损益记录列表（仅SELL订单且有realized_pnl的）
    """
    try:
        from pathlib import Path
        import json
        from datetime import datetime
        
        filled_orders_file = Path("data/logs/filled_orders.jsonl")
        if not filled_orders_file.exists():
            return {
                "ok": True,
                "realized_pnl_records": [],
                "count": 0,
                "total_realized_pnl": 0.0
            }
        
        realized_pnl_records = []
        total_realized_pnl = 0.0
        
        with filled_orders_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    order = json.loads(line.strip())
                    # 只返回SELL订单且有已实现损益的
                    if order.get("action") == "SELL" and order.get("status") == "FILLED":
                        realized_pnl = order.get("realized_pnl")
                        if realized_pnl is not None:
                            # order_date已移除，使用placed_at或filled_at的日期部分
                            placed_at = order.get("placed_at") or order.get("filled_at", "")
                            order_date = placed_at[:10] if placed_at else ""
                            
                            # 日期过滤
                            if date:
                                if not order_date.startswith(date):
                                    continue
                            elif start_date or end_date:
                                if start_date and order_date < start_date:
                                    continue
                                if end_date and order_date > end_date:
                                    continue
                            
                            record = {
                                "order_id": order.get("order_id"),
                                "symbol": order.get("symbol"),
                                "quantity": order.get("quantity"),
                                "fill_price": order.get("fill_result", {}).get("fill_price") or order.get("fill_price"),
                                "cost_basis": order.get("cost_basis") or order.get("fill_result", {}).get("cost_basis"),
                                "proceeds": order.get("proceeds") or order.get("fill_result", {}).get("proceeds"),
                                "realized_pnl": float(realized_pnl),
                                "realized_pnl_pct": order.get("realized_pnl_pct", 0.0),
                                "order_date": order_date,
                                "filled_at": order.get("filled_at") or order.get("placed_at"),
                                "timestamp": order.get("filled_at") or order.get("placed_at")
                            }
                            realized_pnl_records.append(record)
                            total_realized_pnl += float(realized_pnl)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    continue
        
        # 按日期和时间排序（最新的在前）
        realized_pnl_records.sort(
            key=lambda x: x.get("timestamp", "") or x.get("filled_at", ""),
            reverse=True
        )
        
        # 限制返回数量
        realized_pnl_records = realized_pnl_records[:limit]
        
        return {
            "ok": True,
            "realized_pnl_records": realized_pnl_records,
            "count": len(realized_pnl_records),
            "total_realized_pnl": round(total_realized_pnl, 2),
            "date_filter": {
                "date": date,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.post("/api/data/upload")
async def upload_data(data: dict):
    """Upload data to Railway backend from local files"""
    try:
        import json
        from pathlib import Path
        
        # CRITICAL: Use project root data/logs directory explicitly
        logs_dir = get_project_logs_dir()
        
        uploaded_counts = {}
        
        # Upload conversations
        if "conversations" in data and data["conversations"]:
            convo_file = logs_dir / "discussion_actions.jsonl"
            count = 0
            with convo_file.open("a", encoding="utf-8") as f:
                for entry in data["conversations"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            uploaded_counts["conversations"] = count
            log_print(f"[Upload] Uploaded {count} conversations")
        
        # Upload trades
        if "trades" in data and data["trades"]:
            trades_file = logs_dir / "trades.jsonl"
            count = 0
            with trades_file.open("a", encoding="utf-8") as f:
                for entry in data["trades"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            uploaded_counts["trades"] = count
            log_print(f"[Upload] Uploaded {count} trades")
        
        # Upload filled orders
        if "filled_orders" in data and data["filled_orders"]:
            filled_file = logs_dir / "filled_orders.jsonl"
            count = 0
            with filled_file.open("a", encoding="utf-8") as f:
                for entry in data["filled_orders"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            uploaded_counts["filled_orders"] = count
            log_print(f"[Upload] Uploaded {count} filled orders")
        
        # Upload equity history
        if "equity_history" in data and data["equity_history"]:
            equity_file = logs_dir / "equity_history.jsonl"
            count = 0
            with equity_file.open("a", encoding="utf-8") as f:
                for entry in data["equity_history"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            uploaded_counts["equity_history"] = count
            log_print(f"[Upload] Uploaded {count} equity history records")
        
        # Upload pending orders
        if "pending_orders" in data and data["pending_orders"]:
            pending_file = logs_dir / "pending_orders.jsonl"
            count = 0
            with pending_file.open("a", encoding="utf-8") as f:
                for entry in data["pending_orders"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    count += 1
            uploaded_counts["pending_orders"] = count
            log_print(f"[Upload] Uploaded {count} pending orders")
        
        # CRITICAL: Upload portfolio_state.json (overwrite, not append)
        if "portfolio_state" in data and data["portfolio_state"]:
            portfolio_file = logs_dir / "portfolio_state.json"
            try:
                with portfolio_file.open("w", encoding="utf-8") as f:
                    json.dump(data["portfolio_state"], f, ensure_ascii=False, indent=2)
                uploaded_counts["portfolio_state"] = True
                log_print(f"[Upload] Uploaded portfolio_state.json")
            except Exception as e:
                log_print(f"[Upload] Warning: Failed to upload portfolio_state.json: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": "Data uploaded successfully",
                "uploaded": uploaded_counts
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        log_print(f"[Upload] Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )


# 模拟状态跟踪
_simulation_status = {
    "running": False,
    "current_day": 0,
    "total_days": 22,
    "started_at": None,
    "last_update": None,
    "error": None
}

def run_october_simulation_background():
    """后台运行10月模拟（在单独的线程中）"""
    import sys
    import io
    import time
    # Path 已经在文件顶部导入，不需要重新导入
    
    # Fix encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    try:
        # 确保在backend目录
        backend_dir = Path(__file__).parent.parent.parent
        os.chdir(str(backend_dir))
        sys.path.insert(0, str(backend_dir))
        
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.data.order_manager import OrderManager
        from src.data.portfolio import Portfolio
        from src.data.order_executor import get_current_or_open_price
        
        # 从 config.json 读取股票清单
        config_path = backend_dir / "config" / "config.json"
        universe = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]  # 默认值
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if "universe" in config_data and isinstance(config_data["universe"], list):
                        universe = config_data["universe"]
                        log_print(f"[Simulation] Using {len(universe)} stocks from config.json")
                    else:
                        log_print(f"[Simulation] No universe in config.json, using default: {len(universe)} stocks")
            except Exception as e:
                log_print(f"[Simulation] Failed to read config.json, using default: {e}")
        else:
            log_print(f"[Simulation] config.json not found, using default: {len(universe)} stocks")
        
        _simulation_status["running"] = True
        _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
        _simulation_status["error"] = None
        
        # 初始化
        # CRITICAL: Use project root data/logs directory
        logs_dir = get_project_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 清空对话日誌
        convo_file = logs_dir / "discussion_actions.jsonl"
        if convo_file.exists():
            convo_file.write_text("", encoding="utf-8")
        
        # 清空掛單記錄
        pending_file = logs_dir / "pending_orders.jsonl"
        if pending_file.exists():
            pending_file.write_text("", encoding="utf-8")
        
        # 重置組合狀態
        portfolio_file = logs_dir / "portfolio_state.json"
        initial_state = {
            "cash": 10000.0,
            "initial_value": 10000.0,
            "positions": {},
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        portfolio_file.write_text(json.dumps(initial_state, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # 清空單日鎖
        last_trade_file = logs_dir / "last_trade_date.txt"
        if last_trade_file.exists():
            last_trade_file.unlink()
        
        # 生成10月份的所有交易日
        start_date = date(2024, 10, 1)
        end_date = date(2024, 10, 31)
        trading_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 周一到周五
                trading_days.append(current)
            current += timedelta(days=1)
        
        _simulation_status["total_days"] = len(trading_days)
        
        # 結算函數
        def settle_orders(settle_date, logs_dir):
            # CRITICAL: Use project root data/logs directory
            order_manager = OrderManager(root=str(get_project_logs_dir()))
            pending_orders = order_manager.load_pending_orders(order_date=settle_date)
            
            if not pending_orders:
                return 0
            
            portfolio_file = logs_dir / "portfolio_state.json"
            if not portfolio_file.exists():
                return 0
            
            with portfolio_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
            
            portfolio = Portfolio(
                cash=float(state.get("cash", 10000.0)),
                initial_value=float(state.get("initial_value", 10000.0)),
            )
            
            for symbol, pos_info in state.get("positions", {}).items():
                if isinstance(pos_info, dict):
                    qty = int(pos_info.get("quantity", 0))
                    avg_cost = float(pos_info.get("avg_cost", 0))
                    if qty > 0:
                        portfolio.positions[symbol] = {"quantity": qty, "avg_cost": avg_cost}
            
            settled_count = 0
            log_print(f"\n[Settle Orders] Checking {len(pending_orders)} pending orders for {settle_date}...")
            for order in pending_orders:
                symbol = order.get("symbol")
                action = order.get("action", "").upper()
                quantity = order.get("quantity", 0)
                limit_price = order.get("limit_price", 0)
                order_id = order.get("order_id", "unknown")
                
                try:
                    # 检查订单是否成交
                    # 如果市场开盘且是今天，使用实时价格；否则使用历史数据
                    from datetime import date
                    is_today = settle_date == date.today().isoformat()
                    is_market_open = order_manager._is_market_open()
                    use_realtime = is_today and is_market_open
                    
                    log_print(f"[Settle Orders] Processing order {order_id}: {action} {quantity} {symbol} @ limit ${limit_price:.2f} (realtime={use_realtime})")
                    fill_result = order_manager.check_order_fill(order, settle_date, use_realtime=use_realtime)
                    
                    # 输出检查结果
                    current_price = fill_result.get("current_price")
                    if current_price:
                        log_print(f"[Settle Orders] Order {order_id}: current price=${current_price:.2f}, limit=${limit_price:.2f}, filled={fill_result.get('filled', False)}")
                    else:
                        daily_high = fill_result.get("daily_high")
                        daily_low = fill_result.get("daily_low")
                        if daily_high and daily_low:
                            log_print(f"[Settle Orders] Order {order_id}: daily High=${daily_high:.2f}, Low=${daily_low:.2f}, limit=${limit_price:.2f}, filled={fill_result.get('filled', False)}")
                    
                    # 如果市场未开盘或订单未成交，跳过
                    if not fill_result.get("filled", False):
                        log_print(f"[Settle Orders] Order {order_id} not filled: {fill_result.get('fill_reason', 'Unknown reason')}")
                        continue
                    
                    # 订单已成交，执行交易
                    fill_price = fill_result.get("fill_price")
                    if fill_price is None:
                        log_print(f"[Settle Orders] Order {order_id} filled but no fill_price, skipping")
                        continue
                    
                    log_print(f"[Settle Orders] Executing {action} {quantity} {symbol} @ ${fill_price:.2f}...")
                    realized_pnl = None
                    if action == "BUY":
                        portfolio.buy(symbol, quantity, fill_price)
                    elif action == "SELL":
                        # 卖出时计算已实现损益
                        realized_pnl = portfolio.sell(symbol, quantity, fill_price)
                        log_print(f"[Settle Orders] Realized P&L: ${realized_pnl['realized_pnl']:.2f} ({realized_pnl['realized_pnl_pct']:+.2f}%)")
                    
                    # 标记订单为已成交（传递已实现损益）
                    order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl)
                    settled_count += 1
                    log_print(f"[Settle Orders] Order {order_id} executed successfully")
                except Exception as e:
                    log_print(f"[Settle Orders] Error processing order {order_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    pass
            
            log_print(f"[Settle Orders] Completed: {settled_count} orders filled out of {len(pending_orders)} pending orders\n")
            
            portfolio_state = {
                "cash": portfolio.cash,
                "initial_value": portfolio.initial_value,
                "positions": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            
            for symbol, pos in portfolio.positions.items():
                if isinstance(pos, dict):
                    quantity = pos.get("quantity", 0)
                    avg_cost = pos.get("avg_cost", 0)
                    total_cost = pos.get("total_cost", 0)
                    # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                    if total_cost <= 0:
                        total_cost = avg_cost * quantity
                    portfolio_state["positions"][symbol] = {
                        "quantity": quantity,
                        "avg_cost": avg_cost,
                        "total_cost": total_cost,
                    }
            
            portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
            return settled_count
        
        # 模拟每一天
        for day_num, trade_date in enumerate(trading_days, 1):
            if not _simulation_status["running"]:
                break
                
            trade_date_str = trade_date.isoformat()
            _simulation_status["current_day"] = day_num
            _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
            
            # 結算前一天的訂單
            if day_num > 1:
                prev_date = trading_days[day_num - 2].isoformat()
                settle_orders(prev_date, logs_dir)
            
            # 執行當天交易循環
            try:
                window_start = (trade_date - timedelta(days=10)).isoformat()
                window_end = (trade_date + timedelta(days=1)).isoformat()
                
                result = execute_daily_trade(
                    start=window_start,
                    end=window_end,
                    universe=universe  # 使用从 config.json 读取的股票清单
                )
                
                _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                log_print(f"[Simulation] Error on {trade_date_str}: {e}")
                if "No data" not in str(e) and "YFPricesMissingError" not in str(e):
                    _simulation_status["error"] = str(e)
                    break
            
            # 等待5分钟（如果不是最后一天）
            if day_num < len(trading_days) and _simulation_status["running"]:
                # 等待5分钟 = 300秒
                for _ in range(300):
                    if not _simulation_status["running"]:
                        break
                    time.sleep(1)
        
        # 結算最後一天的訂單
        if trading_days and _simulation_status["running"]:
            last_date = trading_days[-1].isoformat()
            settle_orders(last_date, logs_dir)
        
        _simulation_status["running"] = False
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        
    except Exception as e:
        _simulation_status["running"] = False
        _simulation_status["error"] = str(e)
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        import traceback
        traceback.print_exc()


@app.post("/api/trading/simulate-october")
async def simulate_october(background_tasks: BackgroundTasks):
    """启动10月历史数据模拟（后台运行）"""
    if _simulation_status["running"]:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "模拟已在运行中"}
        )
    
    # 重置状态
    _simulation_status["running"] = False
    _simulation_status["current_day"] = 0
    _simulation_status["total_days"] = 22
    _simulation_status["started_at"] = None
    _simulation_status["last_update"] = None
    _simulation_status["error"] = None
    
    # 在后台线程中运行
    import threading
    thread = threading.Thread(target=run_october_simulation_background, daemon=True)
    thread.start()
    
    return {
        "ok": True,
        "message": "10月模拟已启动（后台运行）",
        "status": "started"
    }


@app.get("/api/trading/simulate-status")
async def get_simulation_status():
    """获取10月模拟的状态"""
    return {
        "ok": True,
        "status": _simulation_status.copy()
    }


@app.post("/api/trading/stop-simulation")
async def stop_simulation():
    """停止10月模拟"""
    _simulation_status["running"] = False
    return {
        "ok": True,
        "message": "模拟已停止"
    }


@app.get("/")
async def root():
    """API root endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "message": "AI Trader API",
            "version": "1.0.0",
            "endpoints": {
                "websocket": "/ws",
                "agent_status": "/api/agents/status",
                "history": "/api/history",
                "execute": "/api/trading/execute",
                "market_open": "/api/market/is-open",
                "system_init": "/api/system/init",
                "run_loop": "/api/trading/run-loop",
                "seed_conversations": "/api/demo/seed-conversations"
            }
        },
        headers=CORS_HEADERS.copy()
    )

