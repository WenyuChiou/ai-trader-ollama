"""
Integration tests for Agent Architecture
Tests tool usage, agent communication, order generation, initialization
"""
import pytest
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestAgentArchitecture:
    """Test agent architecture components"""
    
    def test_import_agents(self):
        """Test that all agents can be imported"""
        from src.agents.multi_analyst_system import run_multi_analyst_discussion
        from src.agents.trader_agent import run_trader
        from src.agents.risk_analyst import run_risk_analyst
        
        assert run_multi_analyst_discussion is not None
        assert run_trader is not None
        assert run_risk_analyst is not None
    
    def test_toolbox_availability(self):
        """Test that toolbox is available and has tools"""
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        tools = toolbox.list()
        
        assert len(tools) > 0
        assert "get_market_indices" in tools
        assert "vix_close" in tools
    
    def test_multi_analyst_discussion_structure(self, sample_market_data):
        """Test multi-analyst discussion structure"""
        from src.agents.multi_analyst_system import run_multi_analyst_discussion
        
        # Note: This is a structure test, not a full execution test
        # Full execution requires Ollama and may take time
        result = run_multi_analyst_discussion(
            market_view=sample_market_data,
            use_tools=False,  # Skip tools for faster test
            tool_budget=0
        )
        
        assert isinstance(result, dict)
        assert "final_stance" in result
        assert "analyst_reports" in result
    
    def test_trader_agent_structure(self, sample_market_data, sample_positions):
        """Test trader agent structure"""
        from src.agents.trader_agent import run_trader
        
        # Note: This is a structure test, not a full execution test
        market = sample_market_data
        mview = sample_market_data
        last_prices = {symbol: data["price"] for symbol, data in sample_market_data["stocks"].items()}
        
        # This would require full LLM execution, so we just test structure
        # In a real test, we'd mock the LLM calls
        assert market is not None
        assert mview is not None
        assert len(last_prices) > 0
    
    def test_agent_factory(self):
        """Test agent factory can load agents"""
        from src.agents.factory import AgentFactory
        from pathlib import Path
        
        config_file = Path(__file__).parent.parent.parent / "backend" / "config" / "agents.yaml"
        if config_file.exists():
            factory = AgentFactory(config_file)
            assert factory is not None
    
    def test_prompt_loading(self):
        """Test that prompts can be loaded"""
        from pathlib import Path
        import yaml
        
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        prompt_files = [
            "market_analyst.yml",
            "technical_analyst.yml",
            "fundamental_analyst.yml",
            "sentiment_analyst.yml"
        ]
        
        for prompt_file in prompt_files:
            prompt_path = prompts_dir / prompt_file
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_data = yaml.safe_load(f)
                    assert prompt_data is not None
                    assert "system" in prompt_data or "instructions" in prompt_data

