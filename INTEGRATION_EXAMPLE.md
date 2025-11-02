# 🔗 Event Bus Integration Examples

## Minimal Changes to Existing Code

### Example 1: Enhance BaseAgent

```python
# src/agents/base.py (modify existing)
from src.core.event_bus import EventBus, AgentEvent
from datetime import datetime

class BaseAgent:
    def __init__(self, spec: AgentSpec, llm: ChatOllama):
        self.spec = spec
        self.llm = llm
        self.event_bus = EventBus.get_instance()  # Add this line
        self.current_session_id = None  # Set by orchestrator
    
    def run(self, vars: Dict[str, Any], **kwargs) -> str | Dict[str, Any]:
        # Emit start event
        self._emit_event("start", {
            "input_keys": list(vars.keys()),
            "expect_json": kwargs.get("expect_json", False)
        }, "running")
        
        try:
            # ... existing run logic ...
            sys_prompt = self.render(self.spec.system, vars)
            usr_prompt = self.render(self.spec.user, vars)
            
            # Emit processing event
            self._emit_event("processing", {
                "system_length": len(sys_prompt),
                "user_length": len(usr_prompt)
            }, "running")
            
            messages = [
                SystemMessage(content=sys_prompt),
                HumanMessage(content=usr_prompt),
            ]
            
            output_text = self._call_llm(messages)
            
            # Emit success event
            self._emit_event("end", {
                "output_length": len(str(output_text)),
                "expect_json": kwargs.get("expect_json", False)
            }, "success")
            
            return output_text
        except Exception as e:
            self._emit_event("error", {"error": str(e)}, "error")
            raise
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any], status: str):
        """Helper to emit events"""
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

### Example 2: Enhance ToolBox

```python
# src/agents/toolbox.py (modify existing)
from src.core.event_bus import EventBus, AgentEvent
from datetime import datetime

class ToolBox:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self.event_bus = EventBus.get_instance()  # Add this line
        # ... rest of existing code ...
    
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
            if name not in self._tools:
                raise ValueError(f"Unknown tool: {name}")
            
            fn = self._tools[name].fn
            res = fn(**kwargs)
            
            # Emit success event
            self.event_bus.emit(AgentEvent(
                timestamp=datetime.now().isoformat(),
                agent_name="ToolBox",
                event_type="tool_result",
                status="success",
                payload={
                    "tool_name": name,
                    "result_summary": self._summarize_result(res)
                }
            ))
            
            return {"ok": True, "result": res}
        except Exception as e:
            # Emit error event
            self.event_bus.emit(AgentEvent(
                timestamp=datetime.now().isoformat(),
                agent_name="ToolBox",
                event_type="tool_error",
                status="error",
                payload={"tool_name": name, "error": str(e)}
            ))
            return {"ok": False, "error": str(e)}
    
    def _summarize_result(self, result: Any) -> str:
        """Summarize tool result for event payload"""
        if isinstance(result, dict):
            return f"keys: {list(result.keys())}"
        return str(type(result).__name__)
```

### Example 3: Enhance Analyst Discussion

```python
# src/agents/analyst_discussion.py (modify existing)
from src.core.event_bus import EventBus, AgentEvent
from datetime import datetime

def run_analyst_discussion(
    market_view: Dict[str, Any],
    _unused: Any = None,
    *,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 3,
    preferred_domains: List[str] | None = None,
    session_id: str | None = None,  # Add this parameter
) -> Dict[str, Any]:
    event_bus = EventBus.get_instance()
    
    # Generate session ID if not provided
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    # Emit discussion start
    event_bus.emit(AgentEvent(
        timestamp=datetime.now().isoformat(),
        agent_name="Discussion",
        event_type="discussion_start",
        status="running",
        payload={"rounds": rounds, "tool_budget": tool_budget},
        session_id=session_id
    ))
    
    # ... existing code ...
    
    for r in range(1, rounds + 1):
        # Emit round start
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Discussion",
            event_type="round_start",
            status="running",
            payload={"round": r},
            round_number=r,
            session_id=session_id
        ))
        
        # ... existing round logic ...
        
        # Emit round end with decision
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Discussion",
            event_type="round_end",
            status="success",
            payload={
                "round": r,
                "stance": final_stance,
                "tool_calls_count": len(tool_calls)
            },
            round_number=r,
            session_id=session_id
        ))
    
    return {
        "stance": final_stance,
        "rounds": rounds,
        "transcript": transcript,
        "actions": actions_taken,
        "session_id": session_id  # Include in return
    }
```

---

## Quick Start Guide

### 1. Install FastAPI and WebSocket Support

```bash
pip install fastapi uvicorn websockets python-multipart
```

### 2. Run the API Server

```bash
# Start the API server
uvicorn src.api.server:app --reload --port 8000
```

### 3. Test WebSocket Connection

```python
# test_websocket.py
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(test_websocket())
```

### 4. Frontend Integration Example (React)

```typescript
// frontend/src/hooks/useAgentEvents.ts
import { useEffect, useState } from 'react';

interface AgentEvent {
  timestamp: string;
  agent_name: string;
  event_type: string;
  status: string;
  payload: any;
  round_number?: number;
}

export function useAgentEvents() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'agent_event') {
        setEvents(prev => [...prev, data.data]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, []);

  return { events, isConnected };
}
```

```typescript
// frontend/src/components/AgentChat.tsx
import React from 'react';
import { useAgentEvents } from '../hooks/useAgentEvents';

export function AgentChat() {
  const { events, isConnected } = useAgentEvents();

  return (
    <div className="chat-container">
      <div className="status">
        Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      {events.map((event, idx) => (
        <div key={idx} className="message-bubble">
          <div className="agent-name">[{event.agent_name}]</div>
          <div className="message">
            {event.event_type}: {JSON.stringify(event.payload)}
          </div>
          <div className="timestamp">{event.timestamp}</div>
        </div>
      ))}
    </div>
  );
}
```

---

## Next Steps

1. **Integrate Event Bus**: Add event emission to your existing agents
2. **Start API Server**: Run `uvicorn src.api.server:app --reload`
3. **Build Frontend**: Create React/Vue components using WebSocket
4. **Add Visualizations**: Charts, agent status indicators, workflow graphs

The event system is backward compatible - existing code continues to work!

