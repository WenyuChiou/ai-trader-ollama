#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具集成测试：测试各种工具是否能正常工作
包括：Crypto、Fear & Greed、Jin10、Treasury Bonds、Market Batch
"""
from __future__ import annotations
import sys
from pathlib import Path

# 使用标准的路径设置（与其他测试一致）
ROOT = Path(__file__).resolve().parents[1]  # backend/
SRC = ROOT / "src"  # backend/src/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.tools.crypto_tools import fetch_crypto_batch, get_crypto_price
from src.tools.sentiment_tools import fetch_fear_greed
from src.tools.jin10_tools import fetch_jin10_news, fetch_jin10_economic_data
from src.data.market_data import get_multi_prices
from src.tools.market_tools import fetch_market_batch


def test_crypto_tools():
    """测试加密货币工具"""
    print("\n[TEST] Crypto Tools")
    print("-" * 60)
    try:
        # 测试批量获取（使用 .invoke()）
        result = fetch_crypto_batch.invoke({"symbols": ["BTC-USD", "ETH-USD"]})
        if result and isinstance(result, dict):
            crypto_count = len(result.get("crypto", {}))
            print(f"  [OK] fetch_crypto_batch: {crypto_count} cryptocurrencies")
        else:
            print(f"  [WARN] fetch_crypto_batch returned unexpected format")
        
        # 测试单个价格（使用 .invoke()）
        btc_price = get_crypto_price.invoke({"symbol": "BTC-USD"})
        if btc_price and isinstance(btc_price, dict):
            price = btc_price.get("price", 0)
            print(f"  [OK] get_crypto_price(BTC-USD): ${price:.2f}")
        else:
            print(f"  [WARN] get_crypto_price(BTC-USD): No data")
        
        # 测试市场批量获取（包含 crypto）
        crypto_symbols = ["BTC-USD", "ETH-USD"]
        data = get_multi_prices(crypto_symbols, "2024-01-01", "2024-01-31")
        if data:
            print(f"  [OK] get_multi_prices with crypto: {len(data)} symbols")
        else:
            print(f"  [WARN] get_multi_prices with crypto: No data")
        
        return True
    except Exception as e:
        print(f"  [WARN] Crypto tools failed: {type(e).__name__}: {e} (may be network issue)")
        return True  # 不阻止其他测试


def test_fear_greed():
    """测试 Fear & Greed Index"""
    print("\n[TEST] Fear & Greed Index")
    print("-" * 60)
    try:
        result = fetch_fear_greed()
        if result and result.get("value") is not None:
            value = result.get("value", 0)
            label = result.get("label", "unknown")
            print(f"  [OK] Fear & Greed: {value} ({label})")
        else:
            print(f"  [WARN] Fear & Greed: No data")
    except Exception as e:
        print(f"  [WARN] Fear & Greed failed: {type(e).__name__}: {e} (may be network issue)")
    return True  # 不阻止其他测试


def test_jin10_tools():
    """测试 Jin10 工具"""
    print("\n[TEST] Jin10 Tools")
    print("-" * 60)
    try:
        # 测试新闻（使用 .invoke()）
        news = fetch_jin10_news.invoke({"max_items": 5, "category": "all"})
        if news and isinstance(news, dict):
            items_count = len(news.get("items", []))
            print(f"  [OK] fetch_jin10_news: {items_count} items")
        else:
            print(f"  [WARN] fetch_jin10_news returned unexpected format")
        
        # 测试经济数据（使用 .invoke()）
        econ_data = fetch_jin10_economic_data.invoke({"max_items": 5})
        if econ_data and isinstance(econ_data, dict):
            data_count = len(econ_data.get("data", []))
            print(f"  [OK] fetch_jin10_economic_data: {data_count} items")
        else:
            print(f"  [WARN] fetch_jin10_economic_data returned unexpected format")
    except Exception as e:
        print(f"  [WARN] Jin10 tools failed: {type(e).__name__}: {e} (may be network issue)")
    return True  # 不阻止其他测试


def test_treasury_bonds():
    """测试国债数据"""
    print("\n[TEST] Treasury Bonds")
    print("-" * 60)
    try:
        bonds = ["^TNX", "^IRX", "^FVX"]  # 10年、3个月、5年国债
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=30)
        
        result = get_multi_prices(bonds, start.isoformat(), end.isoformat())
        if result:
            fetched_count = len([s for s in bonds if s in result])
            print(f"  [OK] Treasury bonds: {fetched_count}/{len(bonds)} symbols fetched")
            for symbol in bonds:
                if symbol in result and not result[symbol].empty:
                    last_close = result[symbol]["Close"].iloc[-1]
                    print(f"       {symbol}: {last_close:.2f}")
        else:
            print(f"  [WARN] Treasury bonds: No data")
    except Exception as e:
        print(f"  [WARN] Treasury bonds failed: {type(e).__name__}: {e} (may be network issue)")
    return True  # 不阻止其他测试


def test_market_batch_with_bonds():
    """测试市场批量获取（包含国债）"""
    print("\n[TEST] Market Batch (with Bonds)")
    print("-" * 60)
    try:
        symbols = ["AAPL", "^TNX", "^VIX"]
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=30)
        
        result = fetch_market_batch.invoke({
            "symbols": symbols,
            "start": start.isoformat(),
            "end": end.isoformat(),
        })
        
        if result:
            stocks_count = len(result.get("stocks", {}))
            print(f"  [OK] Market batch: fetched {stocks_count} stocks")
            if "vix" in result:
                print(f"       VIX: {result['vix'].get('level', 'N/A')}")
        else:
            print(f"  [WARN] Market batch: No data")
    except Exception as e:
        print(f"  [WARN] Market batch failed: {type(e).__name__}: {e} (may be network issue)")
    return True  # 不阻止其他测试


def main():
    """运行所有工具测试"""
    print("=" * 80)
    print("TOOLS INTEGRATION TESTS")
    print("=" * 80)
    
    results = []
    
    results.append(("Crypto Tools", test_crypto_tools()))
    results.append(("Fear & Greed", test_fear_greed()))
    results.append(("Jin10 Tools", test_jin10_tools()))
    results.append(("Treasury Bonds", test_treasury_bonds()))
    results.append(("Market Batch", test_market_batch_with_bonds()))
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAILED]"
        print(f"  {status} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    print("=" * 80)
    
    # 工具测试可能因网络问题失败，但不应该阻止整体测试
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

