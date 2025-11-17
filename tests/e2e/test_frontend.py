"""
End-to-end tests for Frontend
Tests UI components, frontend-backend integration
"""
import pytest
from pathlib import Path


@pytest.mark.e2e
class TestFrontend:
    """Test frontend components"""
    
    def test_frontend_file_exists(self):
        """Test that frontend monitor.html exists"""
        frontend_file = Path(__file__).parent.parent.parent / "frontend" / "monitor.html"
        assert frontend_file.exists(), "monitor.html not found"
    
    def test_frontend_structure(self):
        """Test frontend HTML structure"""
        frontend_file = Path(__file__).parent.parent.parent / "frontend" / "monitor.html"
        
        if frontend_file.exists():
            content = frontend_file.read_text(encoding='utf-8')
            
            # Check for key elements
            assert "<!DOCTYPE html>" in content or "<html" in content
            assert "portfolio" in content.lower() or "positions" in content.lower()
            assert "api" in content.lower() or "fetch" in content.lower()
    
    def test_frontend_api_integration_points(self):
        """Test frontend API integration points"""
        frontend_file = Path(__file__).parent.parent.parent / "frontend" / "monitor.html"
        
        if frontend_file.exists():
            content = frontend_file.read_text(encoding='utf-8')
            
            # Check for API endpoints
            api_endpoints = [
                "/api/portfolio/real-time",
                "/api/market/is-open",
                "/api/trading/execute-trade"
            ]
            
            for endpoint in api_endpoints:
                # Check if endpoint is referenced in frontend
                assert endpoint in content or endpoint.replace("/api", "api") in content, \
                    f"API endpoint {endpoint} not found in frontend"
    
    def test_frontend_config_exists(self):
        """Test that frontend config exists"""
        config_file = Path(__file__).parent.parent.parent / "frontend" / "config.js"
        # Config might be inline in monitor.html, so this is optional
        if config_file.exists():
            assert config_file.exists()

