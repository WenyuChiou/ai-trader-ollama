# src/agents/market_agent.py
from __future__ import annotations
from typing import Dict, Any, Iterable, List, Optional
from src.tools.market_tools import fetch_market_batch


def run_market_agent(
    symbols: Optional[Iterable[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    asset_classes: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """
    Market Agent: 抓取市场数据（支持多资产类别）
    
    支持资产类别：
    - stocks: 股票（NVDA, MSFT, AAPL, etc.）
    - bonds: 债券（^TNX, ^IRX, LQD, HYG, etc.）
    - commodities: 商品（GC=F 黄金, CL=F 原油, etc.）
    - indices: 指数（^GSPC, ^DJI, ^N225 日经, ^FTSE 富时, ^GDAXI 德指, ^HSI 恒指, etc.）
    - volatility: 波动率（^VIX, ^VIX3M）
    
    Args:
        symbols: 股票代码列表（legacy 参数）
        start: 开始日期（YYYY-MM-DD），默认 180 天前
        end: 结束日期（YYYY-MM-DD），默认今天
        asset_classes: 资产类别字典
            {
                "stocks": ["NVDA", "MSFT", ...],
                "bonds": ["^TNX", "LQD", ...],
                "commodities": ["GC=F", "CL=F", ...],
                "indices": ["^GSPC", "^N225", ...],
                "volatility": ["^VIX", "^VIX3M"]
            }
    
    Returns:
        {
            "raw": LLM 生成的文本描述（如果有使用 LLM Agent）
            "market_data": {
                "stocks": {...},
                "bonds": {...},
                "commodities": {...},
                "indices": {...},
                "volatility": {...},
                "VIX": {...}
            },
            "inputs": {...}
        }
    """
    # 使用 fetch_market_batch 工具抓取数据
    market_data = fetch_market_batch.invoke({
        "symbols": list(symbols) if symbols else None,
        "asset_classes": asset_classes,
        "start": start,
        "end": end,
        "interval": "1d",
        "auto_adjust": False,
    })
    
    return {
        "raw": f"Market data fetched for {len(market_data.get('stocks', {}))} stocks, "
               f"{len(market_data.get('bonds', {}))} bonds, "
               f"{len(market_data.get('commodities', {}))} commodities, "
               f"{len(market_data.get('indices', {}))} indices.",
        "market_data": market_data,
        "inputs": {
            "symbols": list(symbols) if symbols else None,
            "asset_classes": asset_classes,
            "start": start,
            "end": end,
        },
    }
