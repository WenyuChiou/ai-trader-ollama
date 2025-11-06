"""
Economic & Labor Data Tools - Using Reliable Free APIs
使用可靠的免费API获取经济与劳动数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
import os

# =============================================================================
# API配置 - 用户需要在环境变量或config中设置
# =============================================================================

# FRED API (Federal Reserve Economic Data) - 免费，需注册获取key
# 注册地址: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Alpha Vantage API - 免费tier: 5 calls/min, 500 calls/day
# 注册地址: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")


# =============================================================================
# FRED API - 美联储经济数据 (最推荐，数据最全)
# =============================================================================

def fetch_fred_indicator(
    *,
    series_id: str,
    limit: int = 1,
) -> Dict[str, Any]:
    """
    从FRED获取单个经济指标
    
    常用series_id:
    - GDP: 实际GDP
    - UNRATE: 失业率
    - CPIAUCSL: 消费者价格指数
    - FEDFUNDS: 联邦基金利率
    - DGS10: 10年期国债收益率
    - PAYEMS: 非农就业人数
    - UMCSENT: 密歇根消费者信心指数
    - HOUST: 新屋开工
    - DEXCHUS: 中国/美国汇率
    
    返回:
    {
        "series_id": str,
        "title": str,
        "latest_value": float,
        "latest_date": str,
        "unit": str,
        "success": bool
    }
    """
    if not FRED_API_KEY:
        return {
            "success": False,
            "error": "FRED_API_KEY not configured",
            "message": "Please set FRED_API_KEY in environment variables",
            "setup_url": "https://fred.stlouisfed.org/docs/api/api_key.html"
        }
    
    try:
        # 获取系列信息
        info_url = f"https://api.stlouisfed.org/fred/series"
        info_params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json"
        }
        info_response = requests.get(info_url, params=info_params, timeout=10)
        info_data = info_response.json()
        
        if "seriess" not in info_data or len(info_data["seriess"]) == 0:
            return {
                "success": False,
                "error": f"Series {series_id} not found"
            }
        
        series_info = info_data["seriess"][0]
        title = series_info.get("title", series_id)
        unit = series_info.get("units", "")
        
        # 获取最新数据
        obs_url = f"https://api.stlouisfed.org/fred/series/observations"
        obs_params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        obs_response = requests.get(obs_url, params=obs_params, timeout=10)
        obs_data = obs_response.json()
        
        if "observations" not in obs_data or len(obs_data["observations"]) == 0:
            return {
                "success": False,
                "error": f"No observations found for {series_id}"
            }
        
        latest_obs = obs_data["observations"][0]
        latest_value = float(latest_obs["value"]) if latest_obs["value"] != "." else None
        latest_date = latest_obs["date"]
        
        return {
            "success": True,
            "series_id": series_id,
            "title": title,
            "latest_value": latest_value,
            "latest_date": latest_date,
            "unit": unit,
            "source": "FRED (Federal Reserve Economic Data)"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "series_id": series_id
        }


def fetch_key_economic_data() -> Dict[str, Any]:
    """
    获取关键经济指标（一次性获取多个常用指标）
    
    返回:
    {
        "indicators": {
            "GDP": {...},
            "Unemployment": {...},
            "CPI": {...},
            ...
        },
        "success": bool,
        "count": int
    }
    """
    # 定义关键指标
    key_indicators = {
        "GDP": "GDP",
        "Unemployment_Rate": "UNRATE",
        "CPI": "CPIAUCSL",
        "Fed_Funds_Rate": "FEDFUNDS",
        "10Y_Treasury": "DGS10",
        "Nonfarm_Payrolls": "PAYEMS",
        "Consumer_Confidence": "UMCSENT",
        "Housing_Starts": "HOUST"
    }
    
    results = {}
    success_count = 0
    
    for name, series_id in key_indicators.items():
        result = fetch_fred_indicator(series_id=series_id)
        if result.get("success"):
            results[name] = {
                "value": result["latest_value"],
                "date": result["latest_date"],
                "unit": result.get("unit", ""),
                "title": result.get("title", name)
            }
            success_count += 1
    
    return {
        "success": success_count > 0,
        "indicators": results,
        "count": success_count,
        "total": len(key_indicators),
        "message": f"Successfully fetched {success_count}/{len(key_indicators)} indicators" if success_count > 0 else "No indicators fetched. Check API key."
    }


# =============================================================================
# Alpha Vantage API - 经济指标
# =============================================================================

def fetch_alphavantage_economic(
    *,
    function: str = "REAL_GDP",
    interval: str = "annual"
) -> Dict[str, Any]:
    """
    从Alpha Vantage获取经济指标
    
    支持的function:
    - REAL_GDP: 实际GDP
    - REAL_GDP_PER_CAPITA: 人均实际GDP
    - TREASURY_YIELD: 国债收益率
    - FEDERAL_FUNDS_RATE: 联邦基金利率
    - CPI: 消费者价格指数
    - INFLATION: 通胀率
    - RETAIL_SALES: 零售销售
    - DURABLES: 耐用品订单
    - UNEMPLOYMENT: 失业率
    - NONFARM_PAYROLL: 非农就业
    
    interval: quarterly, monthly, annual
    """
    if not ALPHA_VANTAGE_API_KEY:
        return {
            "success": False,
            "error": "ALPHA_VANTAGE_API_KEY not configured",
            "message": "Please set ALPHA_VANTAGE_API_KEY in environment variables",
            "setup_url": "https://www.alphavantage.co/support/#api-key"
        }
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": function,
            "interval": interval,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Alpha Vantage返回格式通常是 {"name": "...", "interval": "...", "data": [...]}
        if "data" in data and len(data["data"]) > 0:
            latest = data["data"][0]
            return {
                "success": True,
                "function": function,
                "name": data.get("name", function),
                "interval": interval,
                "latest_value": latest.get("value"),
                "latest_date": latest.get("date"),
                "source": "Alpha Vantage"
            }
        elif "Error Message" in data or "Note" in data:
            return {
                "success": False,
                "error": data.get("Error Message") or data.get("Note"),
                "function": function
            }
        else:
            return {
                "success": False,
                "error": "Unexpected response format",
                "function": function,
                "response": str(data)[:200]
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "function": function
        }


# =============================================================================
# 综合经济数据摘要（优先使用FRED，fallback到Alpha Vantage）
# =============================================================================

def get_economic_summary() -> Dict[str, Any]:
    """
    获取经济数据摘要，自动选择最佳数据源
    
    返回:
    {
        "summary": str,  # 文字摘要
        "indicators": {...},
        "source": str,
        "success": bool
    }
    """
    # 优先使用FRED（数据最全）
    if FRED_API_KEY:
        result = fetch_key_economic_data()
        if result.get("success"):
            # 生成摘要
            indicators = result["indicators"]
            summary_parts = []
            
            if "Unemployment_Rate" in indicators:
                unemp = indicators["Unemployment_Rate"]
                summary_parts.append(f"Unemployment: {unemp['value']}% (as of {unemp['date']})")
            
            if "CPI" in indicators:
                cpi = indicators["CPI"]
                summary_parts.append(f"CPI: {cpi['value']} (as of {cpi['date']})")
            
            if "Fed_Funds_Rate" in indicators:
                fed = indicators["Fed_Funds_Rate"]
                summary_parts.append(f"Fed Funds Rate: {fed['value']}% (as of {fed['date']})")
            
            if "GDP" in indicators:
                gdp = indicators["GDP"]
                summary_parts.append(f"GDP: ${gdp['value']}B (as of {gdp['date']})")
            
            summary = "; ".join(summary_parts) if summary_parts else "Economic data available"
            
            return {
                "success": True,
                "summary": summary,
                "indicators": indicators,
                "source": "FRED",
                "count": result["count"]
            }
    
    # Fallback到Alpha Vantage
    if ALPHA_VANTAGE_API_KEY:
        # 尝试获取几个关键指标
        unemployment = fetch_alphavantage_economic(function="UNEMPLOYMENT", interval="monthly")
        cpi = fetch_alphavantage_economic(function="CPI", interval="monthly")
        
        indicators = {}
        if unemployment.get("success"):
            indicators["Unemployment"] = unemployment
        if cpi.get("success"):
            indicators["CPI"] = cpi
        
        if indicators:
            summary = f"Economic data from Alpha Vantage: {len(indicators)} indicators"
            return {
                "success": True,
                "summary": summary,
                "indicators": indicators,
                "source": "Alpha Vantage",
                "count": len(indicators)
            }
    
    # 如果都没有配置API key
    return {
        "success": False,
        "error": "No economic data API configured",
        "message": "Please configure FRED_API_KEY or ALPHA_VANTAGE_API_KEY",
        "setup": {
            "FRED": "https://fred.stlouisfed.org/docs/api/api_key.html (Recommended)",
            "Alpha Vantage": "https://www.alphavantage.co/support/#api-key"
        }
    }


# =============================================================================
# 劳动市场数据（失业率、就业人数等）
# =============================================================================

def get_labor_market_data() -> Dict[str, Any]:
    """
    获取劳动市场关键数据
    
    返回:
    {
        "unemployment_rate": {...},
        "nonfarm_payrolls": {...},
        "labor_force": {...},
        "success": bool
    }
    """
    if not FRED_API_KEY:
        return {
            "success": False,
            "error": "FRED_API_KEY not configured for labor market data"
        }
    
    # 劳动市场关键指标
    labor_indicators = {
        "Unemployment_Rate": "UNRATE",  # 失业率
        "Nonfarm_Payrolls": "PAYEMS",   # 非农就业人数
        "Labor_Force": "CLF16OV",       # 劳动力总数
        "Employment_Level": "CE16OV",   # 就业人数
        "Initial_Claims": "ICSA"        # 初次申请失业救济人数
    }
    
    results = {}
    for name, series_id in labor_indicators.items():
        result = fetch_fred_indicator(series_id=series_id)
        if result.get("success"):
            results[name] = {
                "value": result["latest_value"],
                "date": result["latest_date"],
                "unit": result.get("unit", ""),
                "title": result.get("title", name)
            }
    
    success = len(results) > 0
    
    # 生成摘要
    summary = ""
    if "Unemployment_Rate" in results:
        summary += f"Unemployment: {results['Unemployment_Rate']['value']}%"
    if "Nonfarm_Payrolls" in results:
        payrolls = results['Nonfarm_Payrolls']['value']
        summary += f" | Nonfarm Payrolls: {payrolls:,.0f}K"
    
    return {
        "success": success,
        "indicators": results,
        "summary": summary or "No labor market data available",
        "count": len(results),
        "source": "FRED"
    }

