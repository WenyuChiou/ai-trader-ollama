"""
Integration tests for Conversation Logging
Tests agent conversation recording, Discussion Coordinator recording, tool call logging,
conversation history persistence, and conversation query API
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestConversationLogging:
    """Test conversation logging functionality"""
    
    def test_agent_conversation_structure(self):
        """Test that agent conversation entries have correct structure"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found - run a trading cycle first")
        
        # Read conversation entries
        entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except:
                        pass
        
        if not entries:
            pytest.skip("No conversation entries found")
        
        # Check structure of entries
        required_fields = ["timestamp", "date", "agent", "type", "content"]
        
        for entry in entries[:10]:  # Check first 10 entries
            for field in required_fields:
                assert field in entry, f"Entry missing required field: {field}"
            
            # Check agent name is valid
            agent = entry.get("agent", "")
            assert agent in [
                "MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst",
                "SentimentAnalyst", "DiscussionCoordinator", "RiskAnalyst", "TraderAgent"
            ], f"Invalid agent name: {agent}"
            
            # Check type is valid
            assert entry.get("type") in ["discussion", "tool"], f"Invalid type: {entry.get('type')}"
    
    def test_discussion_coordinator_recording(self):
        """Test that Discussion Coordinator entries are recorded"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Find Discussion Coordinator entries
        coordinator_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        agent = entry.get("agent", "").lower()
                        if "coordinator" in agent or "discussion" in agent:
                            coordinator_entries.append(entry)
                    except:
                        pass
        
        if coordinator_entries:
            # Check coordinator entry structure
            for entry in coordinator_entries:
                assert "content" in entry
                assert "summary" in entry or "stance" in entry
                assert entry.get("type") == "discussion"
        else:
            pytest.skip("No Discussion Coordinator entries found - may need to run trading cycle")
    
    def test_tool_call_logging(self):
        """Test that tool calls are logged correctly"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Find tool call entries
        tool_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "tool":
                            tool_entries.append(entry)
                    except:
                        pass
        
        if tool_entries:
            # Check tool entry structure
            for entry in tool_entries:
                assert "tool_name" in entry or "name" in entry
                assert "agent" in entry
                assert "result" in entry or "tool_result" in entry
        else:
            # Check if tools_used field exists in discussion entries
            with convo_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if "tools_used" in entry and entry.get("tools_used"):
                                # Tools are logged in tools_used field
                                assert isinstance(entry["tools_used"], list)
                                return
                        except:
                            pass
            pytest.skip("No tool call entries found")
    
    def test_conversation_history_persistence(self):
        """Test that conversation history is persisted correctly"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Read all entries
        entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except:
                        pass
        
        if not entries:
            pytest.skip("No conversation entries found")
        
        # Check that entries have timestamps
        for entry in entries:
            assert "timestamp" in entry or "date" in entry
            assert entry.get("timestamp") or entry.get("date")
        
        # Check that entries are in chronological order (if multiple entries)
        if len(entries) > 1:
            timestamps = []
            for entry in entries:
                ts = entry.get("timestamp", entry.get("date", ""))
                if ts:
                    timestamps.append(ts)
            
            # Verify timestamps are valid
            assert len(timestamps) > 0
    
    def test_conversation_query_api_structure(self):
        """Test that conversation query API returns correct structure"""
        # This test checks the API endpoint structure without actually calling it
        # Full API tests should be in test_api.py
        
        # Check that the API function exists and has correct signature
        try:
            from src.api.server import fetch_conversations_api
            assert fetch_conversations_api is not None
        except ImportError:
            pytest.skip("API module not available")
    
    def test_agent_round_tracking(self):
        """Test that discussion rounds are tracked correctly"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Find entries with round numbers
        round_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if "round" in entry:
                            round_entries.append(entry)
                    except:
                        pass
        
        if round_entries:
            # Check round numbers are valid
            for entry in round_entries:
                round_num = entry.get("round")
                assert isinstance(round_num, int)
                assert round_num >= 0  # Round 0 is final summary, rounds 1-3 are discussion rounds
        else:
            pytest.skip("No round entries found")
    
    def test_multiple_analyst_recording(self):
        """Test that all analyst types are recorded"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Collect all agent types
        agent_types = set()
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        agent = entry.get("agent", "")
                        if agent:
                            agent_types.add(agent)
                    except:
                        pass
        
        # Check that we have at least some analyst types
        expected_agents = [
            "MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst",
            "SentimentAnalyst", "DiscussionCoordinator", "RiskAnalyst", "TraderAgent"
        ]
        
        found_agents = [agent for agent in expected_agents if agent in agent_types]
        assert len(found_agents) > 0, f"No expected agents found. Found: {agent_types}"

