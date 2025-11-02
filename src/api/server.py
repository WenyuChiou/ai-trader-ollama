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


@app.get("/api/tools/list")
async def list_tools():
    """List all available tools"""
    from src.agents.toolbox import ToolBox
    tb = ToolBox()
    return {"tools": tb.list()}


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

