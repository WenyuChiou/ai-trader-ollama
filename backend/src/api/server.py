# src/api/server.py
"""
FastAPI backend for real-time agent monitoring and frontend integration.
Provides WebSocket for real-time updates and REST API for historical data.
"""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import random
from pathlib import Path
import json
import asyncio
from datetime import datetime
import uuid

from src.core.event_bus import EventBus, AgentEvent

app = FastAPI(
    title="AI Trader API",
    description="Real-time agent monitoring and trading cycle API",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global event bus
event_bus = EventBus.get_instance()

# Active WebSocket connections
active_connections: List[WebSocket] = []


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
        print(f"[WebSocket] Error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/agents/status")
async def get_agents_status():
    """Get current status of all agents"""
    return event_bus.get_all_agents_status()


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
            rounds=3,
            auto_tools=True,
            tool_budget=3
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
        
        equity_tracker = EquityTracker(root="data/logs")
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
    """Get current portfolio status (from equity history)"""
    try:
        from src.data.equity_tracker import EquityTracker
        
        equity_tracker = EquityTracker(root="data/logs")
        latest = equity_tracker.get_latest_equity()
        
        if latest:
            return {
                "ok": True,
                "portfolio": latest,
            }
        else:
            return {
                "ok": True,
                "portfolio": None,
                "message": "No portfolio data available",
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/real-time")
async def get_real_time_portfolio():
    """Get real-time portfolio with current market prices"""
    try:
        import json
        from pathlib import Path
        
        # Load portfolio state
        state_file = Path("data/logs/portfolio_state.json")
        if not state_file.exists():
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": "Portfolio state not found"}
            )
        
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
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=int(pos_info.get("quantity", 0)),
                    avg_cost=float(pos_info.get("avg_cost", 0.0)),
                    total_cost=float(pos_info.get("total_cost", 0.0)),
                )
        
        # Get real-time snapshot
        from src.data.real_time_tracker import RealTimeTracker
        tracker = RealTimeTracker(root="data/logs")
        snapshot = tracker.update_and_record(portfolio)
        
        return {"ok": True, **snapshot}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/recent-snapshots")
async def get_recent_snapshots(hours: int = 24):
    """Get recent real-time snapshots"""
    try:
        from src.data.real_time_tracker import RealTimeTracker
        tracker = RealTimeTracker(root="data/logs")
        snapshots = tracker.get_recent_snapshots(hours=hours)
        return {"ok": True, "snapshots": snapshots, "count": len(snapshots)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/tools/list")
async def list_tools():
    """List all available tools"""
    from src.agents.toolbox import ToolBox
    tb = ToolBox()
    return {"tools": tb.list()}


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

        logs_dir = Path("data/logs")
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
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

@app.get("/api/system/info")
async def get_system_info():
    """Get system information including LLM model and configuration"""
    try:
        import json
        from pathlib import Path
        
        # Load config.json
        config_file = Path("config/config.json")
        llm_config = {}
        config = {}
        if config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                config = json.load(f)
                llm_config = config.get("llm", {})
        
        # Load agents.yaml to get agent-specific models
        agent_models = {}
        try:
            from pathlib import Path
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
    date: str | None = None
):
    """Get recent agent conversations/discussions"""
    try:
        import json
        from pathlib import Path
        
        # Load from discussion_actions.jsonl
        log_file = Path("data/logs/discussion_actions.jsonl")
        conversations = []
        
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Read last N lines
                for line in lines[-limit * 2:]:  # Get more lines, then filter
                    try:
                        entry = json.loads(line.strip())
                        if date:
                            entry_date = entry.get("date", entry.get("timestamp", ""))
                            if entry_date and not entry_date.startswith(date):
                                continue
                        conversations.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # Also try to load from memory if available
        try:
            from src.data.memory_manager import MemoryManager
            memory_manager = MemoryManager(root="data/logs")
            
            # Get recent memories
            recent_memories = memory_manager.load_recent_memories(days=7, limit=limit)
            for memory in recent_memories:
                discussion = memory.get("discussion", {})
                if discussion:
                    transcript = discussion.get("transcript", [])
                    if transcript:
                        # Extract individual messages from transcript
                        for msg in transcript:
                            if isinstance(msg, dict):
                                conversations.append({
                                    "date": memory.get("date", ""),
                                    "type": "memory",
                                    "agent": msg.get("agent", "Unknown"),
                                    "content": msg.get("content", msg.get("message", "")),
                                    "round": msg.get("round"),
                                })
        except Exception as e:
            print(f"[WARN] Failed to load from memory: {e}")
        
        # Sort by date (newest first)
        conversations.sort(
            key=lambda x: x.get("date", x.get("timestamp", "")), 
            reverse=True
        )
        
        # Limit results
        return {
            "ok": True,
            "conversations": conversations[:limit],
            "count": len(conversations[:limit])
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "AI Trader API",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws",
            "agent_status": "/api/agents/status",
            "history": "/api/history",
            "execute": "/api/trading/execute"
        }
    }

