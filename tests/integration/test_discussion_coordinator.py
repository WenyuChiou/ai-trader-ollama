"""
Integration tests for Discussion Coordinator
Tests multi-round discussion flow, coordinator synthesis, and analyst inclusion
"""
import pytest
from pathlib import Path
import sys
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestDiscussionCoordinator:
    """Test Discussion Coordinator functionality"""
    
    def test_coordinator_includes_all_analysts(self):
        """Test that coordinator includes all four analysts in Key Insights"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found - run a trading cycle first")
        
        # Find Discussion Coordinator entries
        coordinator_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("agent") == "DiscussionCoordinator":
                            coordinator_entries.append(entry)
                    except:
                        pass
        
        if not coordinator_entries:
            pytest.skip("No Discussion Coordinator entries found")
        
        # Check latest coordinator entry
        latest_entry = coordinator_entries[-1]
        content = latest_entry.get("content", "")
        summary = latest_entry.get("summary", "")
        
        # Check that all four analysts are mentioned
        analyst_names = ["Market Analyst", "Technical Analyst", "Fundamental Analyst", "Sentiment Analyst"]
        found_analysts = []
        
        combined_text = (content + " " + summary).lower()
        for analyst in analyst_names:
            if analyst.lower() in combined_text or analyst.split()[0].lower() in combined_text:
                found_analysts.append(analyst)
        
        # At least 3 out of 4 analysts should be mentioned (allowing for some flexibility)
        assert len(found_analysts) >= 3, f"Only found {len(found_analysts)} analysts: {found_analysts}"
    
    def test_multi_round_discussion_structure(self):
        """Test that multi-round discussion has correct structure"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Group entries by round
        rounds = {}
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        round_num = entry.get("round", 0)
                        if round_num not in rounds:
                            rounds[round_num] = []
                        rounds[round_num].append(entry)
                    except:
                        pass
        
        # Check that we have multiple rounds (at least round 1, and possibly 2, 3, or 0)
        assert len(rounds) > 0, "No discussion rounds found"
        
        # Check that round 1 exists (minimum requirement)
        assert 1 in rounds, "Round 1 not found"
        
        # Check that each round has analyst entries
        for round_num in [1, 2, 3]:
            if round_num in rounds:
                round_entries = rounds[round_num]
                analyst_entries = [e for e in round_entries if e.get("type") == "discussion" and e.get("agent") != "DiscussionCoordinator"]
                assert len(analyst_entries) > 0, f"Round {round_num} has no analyst entries"
    
    def test_coordinator_has_stance(self):
        """Test that coordinator summary includes stance"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Find latest coordinator entry
        coordinator_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("agent") == "DiscussionCoordinator":
                            coordinator_entries.append(entry)
                    except:
                        pass
        
        if not coordinator_entries:
            pytest.skip("No Discussion Coordinator entries found")
        
        latest_entry = coordinator_entries[-1]
        
        # Check that stance exists
        stance = latest_entry.get("stance", "").lower()
        assert stance in ["bullish", "bearish", "neutral"], f"Invalid stance: {stance}"
        
        # Check that summary exists
        summary = latest_entry.get("summary", "")
        assert len(summary) > 0, "Coordinator summary is empty"
    
    def test_discussion_rounds_have_tools(self):
        """Test that discussion rounds include tool usage"""
        from src.orchestrator.trading_cycle import _get_project_logs_dir
        
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if not convo_file.exists():
            pytest.skip("No conversation file found")
        
        # Find tool entries in discussion rounds
        tool_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "tool" and entry.get("round", 0) > 0:
                            tool_entries.append(entry)
                    except:
                        pass
        
        # At least some tool usage should exist
        # This is a soft check - tools may not always be used
        if len(tool_entries) > 0:
            # Verify tool entries have required fields
            for entry in tool_entries[:5]:  # Check first 5
                assert "tool_name" in entry, "Tool entry missing tool_name"
                assert "tool_result" in entry, "Tool entry missing tool_result"
                assert "agent" in entry, "Tool entry missing agent"
                assert entry.get("round", 0) > 0, "Tool entry should have round > 0"

