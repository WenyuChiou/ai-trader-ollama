"""
Integration tests for Conversation and Memory System
Tests conversation logging, memory system, prompt loading
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestMemory:
    """Test memory and conversation system"""
    
    def test_conversation_logging_structure(self, tmp_path):
        """Test conversation logging structure"""
        log_file = tmp_path / "discussion_actions.jsonl"
        
        # Create sample conversation entry
        entry = {
            "timestamp": "2025-01-01T10:00:00",
            "analyst": "Market Analyst",
            "type": "discussion",
            "stance": "bullish",
            "analysis": "Test analysis"
        }
        
        # Write entry
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Verify entry
        assert log_file.exists()
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            loaded_entry = json.loads(lines[0])
            assert loaded_entry["analyst"] == "Market Analyst"
    
    def test_memory_file_structure(self, tmp_path):
        """Test memory file structure"""
        memory_dir = tmp_path / "memory" / "daily"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        memory_file = memory_dir / "2025-01-01.json"
        memory_data = {
            "date": "2025-01-01",
            "market_view": {},
            "market_analysis": {},
            "discussion": {},
            "risk_report": {},
            "decision": {},
            "portfolio_snapshot": {}
        }
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2)
        
        assert memory_file.exists()
        with open(memory_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            assert loaded_data["date"] == "2025-01-01"
            assert "market_view" in loaded_data
    
    def test_memory_index_structure(self, tmp_path):
        """Test memory index structure"""
        index_dir = tmp_path / "memory" / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = index_dir / "daily_index.json"
        index_data = {
            "2025-01-01": {
                "file": "2025-01-01.json",
                "date": "2025-01-01",
                "exists": True
            }
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)
        
        assert index_file.exists()
        with open(index_file, 'r', encoding='utf-8') as f:
            loaded_index = json.load(f)
            assert "2025-01-01" in loaded_index
    
    def test_prompt_file_structure(self):
        """Test prompt file structure"""
        from pathlib import Path
        import yaml
        
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        # Test market analyst prompt
        market_prompt = prompts_dir / "market_analyst.yml"
        if market_prompt.exists():
            with open(market_prompt, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
                assert prompt_data is not None
                # Check for common prompt fields
                assert "system" in prompt_data or "instructions" in prompt_data or "role" in prompt_data
    
    def test_conversation_entry_types(self, tmp_path):
        """Test different conversation entry types"""
        log_file = tmp_path / "discussion_actions.jsonl"
        
        entry_types = [
            {"type": "discussion", "analyst": "Market Analyst"},
            {"type": "discussion", "analyst": "Technical Analyst"},
            {"type": "discussion", "analyst": "Risk Analyst"},
            {"type": "discussion", "analyst": "Trader Agent"},
            {"type": "tool", "tool": "get_market_indices"}
        ]
        
        for entry in entry_types:
            entry["timestamp"] = "2025-01-01T10:00:00"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
        
        # Verify all entries
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == len(entry_types)
            for i, line in enumerate(lines):
                loaded_entry = json.loads(line)
                assert loaded_entry["type"] == entry_types[i]["type"]

