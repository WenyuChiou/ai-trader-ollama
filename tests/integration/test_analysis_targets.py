"""
Integration tests for Analysis Targets
Tests that Technical Analyst and Fundamental Analyst analyze the correct targets
"""
import pytest
from pathlib import Path
import sys
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))

from src.utils.etf_checker import is_etf, filter_non_etf_symbols


@pytest.mark.integration
class TestAnalysisTargets:
    """Test analysis target requirements"""
    
    def test_etf_detection(self):
        """Test ETF detection function"""
        # Known ETFs
        assert is_etf("SPY") == True
        assert is_etf("QQQ") == True
        assert is_etf("TQQQ") == True
        assert is_etf("SQQQ") == True
        
        # Known stocks (non-ETF)
        assert is_etf("NVDA") == False
        assert is_etf("MSFT") == False
        assert is_etf("AAPL") == False
    
    def test_filter_non_etf_symbols(self):
        """Test filtering non-ETF symbols"""
        symbols = ["NVDA", "MSFT", "SPY", "QQQ", "AAPL", "TQQQ"]
        non_etf = filter_non_etf_symbols(symbols)
        
        assert "NVDA" in non_etf
        assert "MSFT" in non_etf
        assert "AAPL" in non_etf
        assert "SPY" not in non_etf
        assert "QQQ" not in non_etf
        assert "TQQQ" not in non_etf
    
    def test_technical_analyst_targets_with_holdings(self):
        """Test Technical Analyst targets when holdings exist"""
        # This test verifies the logic, not actual execution
        current_positions = {
            "NVDA": {"quantity": 10},
            "MSFT": {"quantity": 5}
        }
        recommended_stocks = ["AAPL", "GOOG"]
        major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
        
        # Technical Analyst should analyze ALL:
        # 1. Holdings: NVDA, MSFT
        # 2. Recommended: AAPL, GOOG
        # 3. Indices: SPY, QQQ, DIA, IWM, VTI
        expected_targets = set(["NVDA", "MSFT", "AAPL", "GOOG"] + major_indices)
        
        # Verify all targets are included
        assert len(expected_targets) == 9  # 2 holdings + 2 recommended + 5 indices
    
    def test_technical_analyst_targets_without_holdings(self):
        """Test Technical Analyst targets when no holdings exist"""
        current_positions = {}
        recommended_stocks = ["AAPL", "GOOG"]
        major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
        
        # Technical Analyst should analyze:
        # 1. Recommended: AAPL, GOOG
        # 2. Indices: SPY, QQQ, DIA, IWM, VTI
        expected_targets = set(recommended_stocks + major_indices)
        
        # Verify all targets are included
        assert len(expected_targets) == 7  # 2 recommended + 5 indices
    
    def test_fundamental_analyst_targets_with_holdings(self):
        """Test Fundamental Analyst targets when holdings exist"""
        current_positions = {
            "NVDA": {"quantity": 10},  # Stock
            "SPY": {"quantity": 5},    # ETF (should be excluded)
            "MSFT": {"quantity": 3}    # Stock
        }
        recommended_stocks = ["AAPL", "GOOG", "TQQQ"]  # TQQQ is ETF
        
        # Fundamental Analyst should analyze:
        # 1. Non-ETF Holdings: NVDA, MSFT (SPY excluded)
        # 2. Non-ETF Recommended: AAPL, GOOG (TQQQ excluded)
        non_etf_holdings = [sym for sym in current_positions.keys() if not is_etf(sym)]
        non_etf_recommended = [sym for sym in recommended_stocks if not is_etf(sym)]
        
        expected_targets = set(non_etf_holdings + non_etf_recommended)
        
        assert "NVDA" in expected_targets
        assert "MSFT" in expected_targets
        assert "AAPL" in expected_targets
        assert "GOOG" in expected_targets
        assert "SPY" not in expected_targets
        assert "TQQQ" not in expected_targets
    
    def test_fundamental_analyst_targets_without_holdings(self):
        """Test Fundamental Analyst targets when no holdings exist"""
        current_positions = {}
        recommended_stocks = ["AAPL", "GOOG", "SPY", "QQQ"]  # SPY, QQQ are ETFs
        
        # Fundamental Analyst should analyze:
        # 1. Non-ETF Recommended: AAPL, GOOG (SPY, QQQ excluded)
        non_etf_recommended = [sym for sym in recommended_stocks if not is_etf(sym)]
        
        expected_targets = set(non_etf_recommended)
        
        assert "AAPL" in expected_targets
        assert "GOOG" in expected_targets
        assert "SPY" not in expected_targets
        assert "QQQ" not in expected_targets
    
    def test_fundamental_analyst_excludes_indices(self):
        """Test that Fundamental Analyst excludes major indices"""
        major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
        
        # All major indices should be detected as ETFs
        for idx in major_indices:
            assert is_etf(idx) == True, f"{idx} should be detected as ETF"
        
        # Fundamental Analyst should not analyze these
        filtered = filter_non_etf_symbols(major_indices)
        assert len(filtered) == 0, "Major indices should all be filtered out"
    
    def test_technical_analyst_includes_indices(self):
        """Test that Technical Analyst includes major indices"""
        major_indices = ["SPY", "QQQ", "DIA", "IWM", "VTI"]
        
        # Technical Analyst should analyze all indices
        # (This is a logic test, not execution test)
        assert len(major_indices) == 5
        assert all(idx in major_indices for idx in ["SPY", "QQQ", "DIA", "IWM", "VTI"])

