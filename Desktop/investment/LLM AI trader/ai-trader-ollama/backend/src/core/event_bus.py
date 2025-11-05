# src/core/event_bus.py
"""
Event Bus for real-time agent activity tracking.
Enables frontend visualization and monitoring.
"""
from __future__ import annotations

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import threading
from pathlib import Path


@dataclass
class AgentEvent:
    """Standardized agent activity event for frontend consumption"""
    timestamp: str
    agent_name: str
    event_type: str  # "start", "tool_call", "decision", "end", "error", "message"
    status: str      # "running", "success", "error", "idle"
    payload: Dict[str, Any]
    round_number: Optional[int] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class EventBus:
    """
    Central event bus for agent activities.
    Supports real-time subscribers (for WebSocket) and persistent logging.
    """
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __init__(self, log_path: Optional[Path] = None):
        self._subscribers: List[Callable[[AgentEvent], None]] = []
        self._event_log: List[AgentEvent] = []
        self._max_log_size = 1000  # Keep last 1000 events in memory
        self.log_path = log_path or Path("data/logs/events.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'EventBus':
        """Singleton pattern for global event bus"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def subscribe(self, callback: Callable[[AgentEvent], None]):
        """Subscribe to events (for WebSocket broadcasting)"""
        with self._lock:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[AgentEvent], None]):
        """Unsubscribe from events"""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def emit(self, event: AgentEvent):
        """Emit event to all subscribers and persist to log"""
        with self._lock:
            # Persist to file
            self._persist_event(event)
            
            # Keep in memory (limit size)
            self._event_log.append(event)
            if len(self._event_log) > self._max_log_size:
                self._event_log.pop(0)
            
            # Notify subscribers
            for callback in self._subscribers:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[EventBus] Error in subscriber: {e}")
    
    def _persist_event(self, event: AgentEvent):
        """Write event to JSONL file"""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[EventBus] Failed to persist event: {e}")
    
    def get_history(
        self,
        agent_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get event history for frontend"""
        events = list(self._event_log)
        
        # Filter by agent
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Filter by session
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        
        # Return most recent
        return [e.to_dict() for e in events[-limit:]]
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get current status of an agent"""
        agent_events = [e for e in self._event_log if e.agent_name == agent_name]
        if not agent_events:
            return {"status": "idle", "last_activity": None}
        
        last_event = agent_events[-1]
        return {
            "status": last_event.status,
            "last_activity": last_event.timestamp,
            "last_event_type": last_event.event_type,
            "round_number": last_event.round_number,
        }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        agent_names = set(e.agent_name for e in self._event_log)
        return {name: self.get_agent_status(name) for name in agent_names}

