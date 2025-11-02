# 🎨 Frontend-Ready Architecture Optimization

## 📊 Current Limitations

1. **No Event System**: Agent activities are not tracked in real-time
2. **Limited Observability**: Only console prints, no structured logs
3. **No State Management**: Agent states are ephemeral
4. **No API Layer**: No REST/WebSocket for frontend consumption
5. **No Historical Tracking**: Daily updates are not preserved

## 🏗️ Recommended Architecture

### Option 1: **LangGraph + FastAPI + WebSocket** (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React/Vue)                 │
│  - Agent Activity Dashboard                            │
│  - Real-time Chat Interface (like image)                │
│  - Daily Updates & History                             │
└──────────────────┬──────────────────────────────────────┘
                    │ WebSocket / REST API
┌───────────────────▼──────────────────────────────────────┐
│              FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │  WebSocket Manager (Broadcast Events)            │   │
│  │  REST API (Historical Data)                      │   │
│  └──────────────────────────────────────────────────┘   │
│                  │                                       │
│  ┌───────────────▼───────────────────────────────┐     │
│  │      Event Bus / Observer Pattern             │     │
│  │  - Agent State Changes                        │     │
│  │  - Tool Invocations                           │     │
│  │  - Decision Events                            │     │
│  └───────────────┬───────────────────────────────┘     │
│                  │                                       │
│  ┌───────────────▼───────────────────────────────┐     │
│  │         LangGraph Workflow                     │     │
│  │  - Visual Agent Graph                         │     │
│  │  - State Management                           │     │
│  │  - Step-by-step Execution                     │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────┐
│            State Storage (PostgreSQL/Redis)              │
│  - Agent States                                          │
│  - Event Logs                                            │
│  - Historical Sessions                                   │
└──────────────────────────────────────────────────────────┘
```

### Option 2: **Current Architecture + Event System** (Minimal Changes)

Add event system to current architecture without major refactor.

---

## 🚀 Implementation Plan

### Phase 1: Event System Foundation

#### 1.1 Create Event Bus

```python
# src/core/event_bus.py
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class AgentEvent:
    """Standardized agent activity event"""
    timestamp: str
    agent_name: str
    event_type: str  # "start", "tool_call", "decision", "end", "error"
    status: str      # "running", "success", "error"
    payload: Dict[str, Any]
    round_number: int | None = None
    session_id: str | None = None

class EventBus:
    """Central event bus for agent activities"""
    def __init__(self):
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._event_log: List[AgentEvent] = []
    
    def subscribe(self, callback: Callable[[AgentEvent], None]):
        """Subscribe to events (for WebSocket broadcasting)"""
        self._subscribers.append(callback)
    
    def emit(self, event: AgentEvent):
        """Emit event to all subscribers"""
        self._event_log.append(event)
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"[EventBus] Error in subscriber: {e}")
    
    def get_history(self, agent_name: str | None = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history for frontend"""
        events = self._event_log
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        return [asdict(e) for e in events[-limit:]]
```

#### 1.2 Agent Base with Event Emission

```python
# src/agents/base.py (enhanced)
from src.core.event_bus import EventBus, AgentEvent

class BaseAgent:
    def __init__(self, spec: AgentSpec, llm: ChatOllama, event_bus: EventBus | None = None):
        self.spec = spec
        self.llm = llm
        self.event_bus = event_bus or EventBus.get_instance()
        self.current_session_id = None
    
    def run(self, vars: Dict[str, Any], **kwargs) -> str | Dict[str, Any]:
        # Emit start event
        self._emit_event("start", {"vars_keys": list(vars.keys())}, "running")
        
        try:
            # ... existing run logic ...
            
            # Emit success event
            self._emit_event("end", {"output_length": len(str(result))}, "success")
            return result
        except Exception as e:
            self._emit_event("error", {"error": str(e)}, "error")
            raise
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any], status: str):
        event = AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name=self.spec.name,
            event_type=event_type,
            status=status,
            payload=payload,
            session_id=self.current_session_id
        )
        self.event_bus.emit(event)
```

#### 1.3 ToolBox with Event Tracking

```python
# src/agents/toolbox.py (enhanced)
class ToolBox:
    def __init__(self, event_bus: EventBus | None = None):
        self._tools = {}
        self.event_bus = event_bus or EventBus.get_instance()
    
    def invoke(self, name: str, **kwargs) -> Dict[str, Any]:
        # Emit tool call event
        self.event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="ToolBox",
            event_type="tool_call",
            status="running",
            payload={"tool_name": name, "args": kwargs}
        ))
        
        try:
            result = self._execute_tool(name, kwargs)
            # Emit success
            self.event_bus.emit(AgentEvent(
                timestamp=datetime.now().isoformat(),
                agent_name="ToolBox",
                event_type="tool_result",
                status="success",
                payload={"tool_name": name, "result_summary": self._summarize_result(result)}
            ))
            return result
        except Exception as e:
            # Emit error
            self.event_bus.emit(AgentEvent(
                timestamp=datetime.now().isoformat(),
                agent_name="ToolBox",
                event_type="tool_error",
                status="error",
                payload={"tool_name": name, "error": str(e)}
            ))
            raise
```

---

### Phase 2: FastAPI Backend

```python
# src/api/server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
from src.core.event_bus import EventBus

app = FastAPI(title="AI Trader API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

event_bus = EventBus()
active_connections: List[WebSocket] = []

# WebSocket subscriber for real-time updates
def broadcast_event(event: AgentEvent):
    """Broadcast event to all connected WebSocket clients"""
    message = json.dumps({
        "type": "agent_event",
        "data": {
            "timestamp": event.timestamp,
            "agent_name": event.agent_name,
            "event_type": event.event_type,
            "status": event.status,
            "payload": event.payload,
            "round_number": event.round_number,
        }
    })
    for connection in active_connections:
        try:
            asyncio.create_task(connection.send_text(message))
        except Exception:
            active_connections.remove(connection)

event_bus.subscribe(broadcast_event)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/api/agents/status")
async def get_agents_status():
    """Get current status of all agents"""
    return {
        "agents": [
            {
                "name": "market_agent",
                "status": "idle",
                "last_activity": "..."
            },
            # ...
        ]
    }

@app.get("/api/history/{session_id}")
async def get_session_history(session_id: str):
    """Get full history of a trading session"""
    events = event_bus.get_history(limit=1000)
    return {"events": events}

@app.post("/api/trading/execute")
async def execute_trading_cycle():
    """Trigger a new trading cycle"""
    from src.orchestrator.trading_cycle import execute_daily_trade
    
    # Execute with event tracking
    result = execute_daily_trade(...)
    return result
```

---

### Phase 3: Frontend Components (Example Structure)

```
frontend/
├── src/
│   ├── components/
│   │   ├── AgentChat.tsx          # Chat interface (like image)
│   │   ├── AgentStatus.tsx        # Agent status indicators
│   │   ├── ToolCallMonitor.tsx   # Tool invocations
│   │   └── Dashboard.tsx          # Main dashboard
│   ├── hooks/
│   │   ├── useWebSocket.ts        # WebSocket connection
│   │   └── useAgentEvents.ts      # Event processing
│   ├── services/
│   │   └── api.ts                 # REST API client
│   └── App.tsx
```

**Example: AgentChat Component** (Similar to image)
```typescript
// frontend/src/components/AgentChat.tsx
import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface AgentMessage {
  agent: string;
  message: string;
  timestamp: string;
  event_type: string;
}

export function AgentChat() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const { events } = useWebSocket('ws://localhost:8000/ws');
  
  useEffect(() => {
    if (events) {
      const newMessage: AgentMessage = {
        agent: events.data.agent_name,
        message: formatAgentMessage(events),
        timestamp: events.data.timestamp,
        event_type: events.data.event_type
      };
      setMessages(prev => [...prev, newMessage]);
    }
  }, [events]);
  
  return (
    <div className="chat-container">
      {messages.map((msg, idx) => (
        <MessageBubble
          key={idx}
          agent={msg.agent}
          message={msg.message}
          timestamp={msg.timestamp}
        />
      ))}
    </div>
  );
}
```

---

### Phase 4: LangGraph Integration (Optional but Recommended)

LangGraph provides visual workflow graphs:

```python
# src/orchestrator/langgraph_workflow.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

class TradingState(TypedDict):
    market_data: Dict[str, Any]
    analysis: Dict[str, Any]
    discussion: Dict[str, Any]
    decision: Dict[str, Any]

def create_trading_graph(event_bus: EventBus):
    workflow = StateGraph(TradingState)
    
    # Add nodes
    workflow.add_node("market_agent", market_agent_node)
    workflow.add_node("market_analyst", market_analyst_node)
    workflow.add_node("discussion", discussion_node)
    workflow.add_node("trader", trader_node)
    
    # Define edges
    workflow.set_entry_point("market_agent")
    workflow.add_edge("market_agent", "market_analyst")
    workflow.add_edge("market_analyst", "discussion")
    workflow.add_edge("discussion", "trader")
    workflow.add_edge("trader", END)
    
    return workflow.compile()
```

**Benefits:**
- Visual workflow representation
- Built-in state management
- Easy to debug and visualize
- Compatible with LangSmith for monitoring

---

## 📦 Alternative: Lightweight Solution (Current + Events)

If you want to keep current architecture but add observability:

### Minimal Changes Required:

1. **Add Event Bus** (as shown above)
2. **Add WebSocket Server** (simple FastAPI)
3. **Enhance Logging** (structured JSON logs)

```python
# src/utils/structured_logger.py
import json
from datetime import datetime

class StructuredLogger:
    def log_agent_activity(self, agent: str, action: str, data: Dict):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "data": data
        }
        # Write to JSONL file (easy for frontend to parse)
        with open("data/logs/activities.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

---

## 🔄 Recommended Tech Stack

### Backend:
- **FastAPI**: REST + WebSocket support
- **LangGraph**: Workflow visualization (optional)
- **PostgreSQL**: Session history, agent states
- **Redis**: Real-time state cache (optional)

### Frontend:
- **React** or **Vue**: Component framework
- **WebSocket Client**: Real-time updates
- **Chart.js / Recharts**: Data visualization
- **TailwindCSS**: Styling (for chat UI like image)

### Optional:
- **LangSmith**: LLM observability
- **Grafana**: System monitoring (like in image)
- **Docker**: Containerization for deployment

---

## 🎯 Implementation Priority

1. **Phase 1 (Week 1)**: Event Bus + Structured Logging
2. **Phase 2 (Week 2)**: FastAPI + WebSocket Backend
3. **Phase 3 (Week 3)**: Basic Frontend (Chat UI)
4. **Phase 4 (Week 4)**: Dashboard + Historical View

---

## 📝 Next Steps

Would you like me to:
1. ✅ Implement the Event Bus system?
2. ✅ Create the FastAPI backend skeleton?
3. ✅ Build a simple React frontend example?
4. ✅ Integrate LangGraph for workflow visualization?

Let me know which phase you'd like to start with!

