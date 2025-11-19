"""
ETF检测工具：检查symbol是否是ETF
"""
from typing import Optional
import yfinance as yf


# 已知的主要指数ETF列表（用于快速检查）
KNOWN_INDEX_ETFS = {
    "SPY", "QQQ", "DIA", "IWM", "VTI",  # 主要指数ETF
    "TQQQ", "SQQQ", "SPXL", "SPXU", "UPRO",  # 杠杆/反向ETF
    "SH", "PSQ", "SDS", "SOXS",  # 其他反向ETF
    "XLK", "XLV", "XLF", "XLY", "XLI", "XLE", "XLU", "XLRE", "XLB", "XLP", "XLC",  # 板块ETF
}


def is_etf(symbol: str, use_cache: bool = True) -> bool:
    """
    检查symbol是否是ETF
    
    Args:
        symbol: 股票代码
        use_cache: 是否使用已知ETF列表进行快速检查（默认True）
    
    Returns:
        True if ETF, False otherwise
    """
    if not symbol:
        return False
    
    symbol_upper = symbol.upper().strip()
    
    # 快速检查：已知的ETF列表
    if use_cache and symbol_upper in KNOWN_INDEX_ETFS:
        return True
    
    # 使用yfinance检查quoteType
    try:
        ticker = yf.Ticker(symbol_upper)
        info = ticker.info
        
        # 检查quoteType字段
        quote_type = info.get("quoteType", "").upper()
        if quote_type == "ETF":
            return True
        
        # 检查instrumentType字段（备用）
        instrument_type = info.get("instrumentType", "").upper()
        if instrument_type == "ETF":
            return True
        
        # 检查sector字段（ETF通常没有sector或sector为None）
        # 但这不是可靠指标，因为有些ETF也有sector
        
        return False
        
    except Exception as e:
        # 如果yfinance查询失败，返回False（假设不是ETF）
        # 可以记录日志，但这里不导入logging避免循环依赖
        return False


def filter_non_etf_symbols(symbols: list[str]) -> list[str]:
    """
    过滤掉ETF，只返回非ETF的symbols
    
    Args:
        symbols: symbol列表
    
    Returns:
        过滤后的非ETF symbol列表
    """
    return [sym for sym in symbols if not is_etf(sym)]


def filter_etf_symbols(symbols: list[str]) -> list[str]:
    """
    只返回ETF symbols
    
    Args:
        symbols: symbol列表
    
    Returns:
        过滤后的ETF symbol列表
    """
    return [sym for sym in symbols if is_etf(sym)]


# Known cryptocurrency symbols (for filtering)
KNOWN_CRYPTO_SYMBOLS = {
    "BTC", "ETH", "DOGE", "SOL", "BNB", "USDT", "XRP", "ADA", "MATIC", "DOT",
    "BTC-USD", "ETH-USD", "DOGE-USD", "SOL-USD", "BNB-USD", "USDT-USD", 
    "XRP-USD", "ADA-USD", "MATIC-USD", "DOT-USD",
}


def is_crypto(symbol: str) -> bool:
    """
    Check if symbol is a cryptocurrency
    
    Args:
        symbol: Stock/crypto symbol
    
    Returns:
        True if cryptocurrency, False otherwise
    """
    if not symbol:
        return False
    
    symbol_upper = symbol.upper().strip()
    
    # Quick check: known crypto symbols
    if symbol_upper in KNOWN_CRYPTO_SYMBOLS:
        return True
    
    # Check if ends with -USD (crypto format)
    if symbol_upper.endswith("-USD"):
        return True
    
    return False


def filter_crypto_symbols(symbols: list[str]) -> list[str]:
    """
    Filter out cryptocurrency symbols, return only stock symbols
    
    Args:
        symbols: symbol list
    
    Returns:
        Filtered list without crypto symbols
    """
    return [sym for sym in symbols if not is_crypto(sym)]
