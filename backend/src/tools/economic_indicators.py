"""
Economic indicators and labor market data from FRED (Federal Reserve Economic Data) API.
"""
import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def _get_fred_api_key() -> Optional[str]:
    """Get FRED API key from config.json or environment variable."""
    # First try config.json
    try:
        from src.utils.config_loader import load_config
        config = load_config()
        api_key = config.get("fred_api_key")
        if api_key and isinstance(api_key, str) and api_key.strip():
            return api_key.strip()
    except Exception:
        pass
    
    # Fallback to environment variable
    return os.getenv("FRED_API_KEY")


def _fetch_fred_series(series_id: str, api_key: str, limit: int = 1) -> Optional[Dict[str, Any]]:
    """
    Fetch data for a specific FRED series.
    
    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')
        api_key: FRED API key
        limit: Number of most recent observations to fetch
        
    Returns:
        Dictionary with series data or None if error
    """
    try:
        # Get observations
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "observations" in data and len(data["observations"]) > 0:
            obs = data["observations"][0]
            return {
                "series_id": series_id,
                "date": obs.get("date"),
                "value": obs.get("value"),
                "realtime_start": obs.get("realtime_start"),
                "realtime_end": obs.get("realtime_end")
            }
        return None
        
    except Exception as e:
        return {"error": str(e), "series_id": series_id}


def get_economic_summary() -> str:
    """
    Get a summary of key US economic indicators from FRED.
    
    Fetches:
    - GDP (Gross Domestic Product)
    - UNRATE (Unemployment Rate)
    - CPIAUCSL (Consumer Price Index)
    - FEDFUNDS (Federal Funds Rate)
    - DGS10 (10-Year Treasury Constant Maturity Rate)
    - PAYEMS (All Employees, Total Nonfarm)
    - UMCSENT (University of Michigan: Consumer Sentiment)
    - HOUST (Housing Starts)
    
    Returns:
        Formatted string with economic summary or error message
    """
    api_key = _get_fred_api_key()
    if not api_key:
        return "[ERROR] FRED_API_KEY not configured. Set environment variable to enable economic data."
    
    indicators = {
        "GDP": "GDP (Billions $)",
        "UNRATE": "Unemployment Rate (%)",
        "CPIAUCSL": "CPI (Consumer Price Index)",
        "FEDFUNDS": "Federal Funds Rate (%)",
        "DGS10": "10-Year Treasury Rate (%)",
        "PAYEMS": "Nonfarm Payrolls (Thousands)",
        "UMCSENT": "Consumer Sentiment Index",
        "HOUST": "Housing Starts (Thousands)"
    }
    
    results = []
    results.append("=== US Economic Indicators (FRED) ===\n")
    
    for series_id, label in indicators.items():
        data = _fetch_fred_series(series_id, api_key, limit=1)
        if data and "value" in data and data["value"] != ".":
            try:
                value = float(data["value"])
                date = data.get("date", "N/A")
                results.append(f"{label}: {value:,.2f} (as of {date})")
            except (ValueError, TypeError):
                results.append(f"{label}: {data.get('value', 'N/A')} (as of {data.get('date', 'N/A')})")
        elif data and "error" in data:
            results.append(f"{label}: [Error: {data['error']}]")
        else:
            results.append(f"{label}: No data available")
    
    results.append(f"\nData source: Federal Reserve Economic Data (FRED)")
    results.append(f"Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(results)


def get_labor_market_data() -> str:
    """
    Get detailed US labor market data from FRED.
    
    Fetches:
    - UNRATE (Unemployment Rate)
    - PAYEMS (Total Nonfarm Payrolls)
    - CIVPART (Labor Force Participation Rate)
    - LNS14000000 (Unemployment Rate - alternative measure)
    - IC4WSA (Initial Claims, 4-week moving average)
    
    Returns:
        Formatted string with labor market summary or error message
    """
    api_key = _get_fred_api_key()
    if not api_key:
        return "[ERROR] FRED_API_KEY not configured. Set environment variable to enable labor market data."
    
    indicators = {
        "UNRATE": "Unemployment Rate (%)",
        "PAYEMS": "Total Nonfarm Payrolls (Thousands)",
        "CIVPART": "Labor Force Participation Rate (%)",
        "LNS14000000": "Unemployment Rate - Seasonally Adjusted (%)",
        "IC4WSA": "Initial Claims - 4 Week MA (Thousands)"
    }
    
    results = []
    results.append("=== US Labor Market Data (FRED) ===\n")
    
    for series_id, label in indicators.items():
        data = _fetch_fred_series(series_id, api_key, limit=1)
        if data and "value" in data and data["value"] != ".":
            try:
                value = float(data["value"])
                date = data.get("date", "N/A")
                results.append(f"{label}: {value:,.2f} (as of {date})")
            except (ValueError, TypeError):
                results.append(f"{label}: {data.get('value', 'N/A')} (as of {data.get('date', 'N/A')})")
        elif data and "error" in data:
            results.append(f"{label}: [Error: {data['error']}]")
        else:
            results.append(f"{label}: No data available")
    
    results.append(f"\nData source: Federal Reserve Economic Data (FRED)")
    results.append(f"Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(results)


def get_treasury_yield_curve() -> str:
    """
    Get US Treasury yield curve (short-term and long-term bond rates) from FRED.
    
    Fetches:
    - DGS1MO: 1-Month Treasury Constant Maturity Rate
    - DGS3MO: 3-Month Treasury Constant Maturity Rate
    - DGS6MO: 6-Month Treasury Constant Maturity Rate
    - DGS1: 1-Year Treasury Constant Maturity Rate
    - DGS2: 2-Year Treasury Constant Maturity Rate
    - DGS5: 5-Year Treasury Constant Maturity Rate
    - DGS10: 10-Year Treasury Constant Maturity Rate
    - DGS30: 30-Year Treasury Constant Maturity Rate
    
    Returns:
        Formatted string with treasury yield curve or error message
    """
    api_key = _get_fred_api_key()
    if not api_key:
        return "[ERROR] FRED_API_KEY not configured. Set environment variable to enable treasury yield data."
    
    treasury_rates = {
        "DGS1MO": "1-Month Treasury Rate (%)",
        "DGS3MO": "3-Month Treasury Rate (%)",
        "DGS6MO": "6-Month Treasury Rate (%)",
        "DGS1": "1-Year Treasury Rate (%)",
        "DGS2": "2-Year Treasury Rate (%)",
        "DGS5": "5-Year Treasury Rate (%)",
        "DGS10": "10-Year Treasury Rate (%)",
        "DGS30": "30-Year Treasury Rate (%)"
    }
    
    results = []
    results.append("=== US Treasury Yield Curve (FRED) ===\n")
    results.append("Short-Term Rates:\n")
    
    short_term = ["DGS1MO", "DGS3MO", "DGS6MO", "DGS1", "DGS2"]
    long_term = ["DGS5", "DGS10", "DGS30"]
    
    for series_id in short_term:
        if series_id not in treasury_rates:
            continue
        label = treasury_rates[series_id]
        data = _fetch_fred_series(series_id, api_key, limit=1)
        if data and "value" in data and data["value"] != ".":
            try:
                value = float(data["value"])
                date = data.get("date", "N/A")
                results.append(f"  {label}: {value:,.2f}% (as of {date})")
            except (ValueError, TypeError):
                results.append(f"  {label}: {data.get('value', 'N/A')} (as of {data.get('date', 'N/A')})")
        elif data and "error" in data:
            results.append(f"  {label}: [Error: {data['error']}]")
        else:
            results.append(f"  {label}: No data available")
    
    results.append("\nLong-Term Rates:\n")
    
    for series_id in long_term:
        if series_id not in treasury_rates:
            continue
        label = treasury_rates[series_id]
        data = _fetch_fred_series(series_id, api_key, limit=1)
        if data and "value" in data and data["value"] != ".":
            try:
                value = float(data["value"])
                date = data.get("date", "N/A")
                results.append(f"  {label}: {value:,.2f}% (as of {date})")
            except (ValueError, TypeError):
                results.append(f"  {label}: {data.get('value', 'N/A')} (as of {data.get('date', 'N/A')})")
        elif data and "error" in data:
            results.append(f"  {label}: [Error: {data['error']}]")
        else:
            results.append(f"  {label}: No data available")
    
    # Calculate yield curve spread (10Y - 2Y)
    data_2y = _fetch_fred_series("DGS2", api_key, limit=1)
    data_10y = _fetch_fred_series("DGS10", api_key, limit=1)
    
    if (data_2y and "value" in data_2y and data_2y["value"] != "." and
        data_10y and "value" in data_10y and data_10y["value"] != "."):
        try:
            rate_2y = float(data_2y["value"])
            rate_10y = float(data_10y["value"])
            spread = rate_10y - rate_2y
            results.append(f"\nYield Curve Spread (10Y - 2Y): {spread:,.2f}%")
            if spread < 0:
                results.append("  ⚠️ Inverted Yield Curve (recession signal)")
            elif spread < 0.5:
                results.append("  ⚠️ Flat Yield Curve (caution)")
            else:
                results.append("  ✅ Normal Yield Curve")
        except (ValueError, TypeError):
            pass
    
    results.append(f"\nData source: Federal Reserve Economic Data (FRED)")
    results.append(f"Retrieved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(results)


def fetch_fred_indicator(series_id: str, limit: int = 1) -> str:
    """
    Fetch a specific economic indicator from FRED API by series ID.
    
    Common series IDs:
    - GDP: Gross Domestic Product
    - UNRATE: Unemployment Rate
    - CPIAUCSL: Consumer Price Index for All Urban Consumers
    - FEDFUNDS: Federal Funds Effective Rate
    - DGS1MO, DGS3MO, DGS6MO, DGS1, DGS2, DGS5, DGS10, DGS30: Treasury rates (1-month to 30-year)
    - PAYEMS: All Employees, Total Nonfarm
    - UMCSENT: University of Michigan Consumer Sentiment Index
    - HOUST: Housing Starts
    - INDPRO: Industrial Production Index
    - RSXFS: Advance Retail Sales: Retail Trade
    
    Args:
        series_id: FRED series identifier
        limit: Number of recent observations (default: 1)
        
    Returns:
        Formatted string with indicator data or error message
    """
    api_key = _get_fred_api_key()
    if not api_key:
        return f"[ERROR] FRED_API_KEY not configured. Cannot fetch {series_id}."
    
    data = _fetch_fred_series(series_id, api_key, limit=limit)
    
    if not data:
        return f"[ERROR] No data available for series {series_id}"
    
    if "error" in data:
        return f"[ERROR] Failed to fetch {series_id}: {data['error']}"
    
    if "value" not in data or data["value"] == ".":
        return f"[INFO] {series_id}: No recent data available"
    
    try:
        value = float(data["value"])
        date = data.get("date", "N/A")
        return f"{series_id}: {value:,.4f} (as of {date})"
    except (ValueError, TypeError):
        return f"{series_id}: {data.get('value', 'N/A')} (as of {data.get('date', 'N/A')})"

