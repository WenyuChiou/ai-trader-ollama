#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的新闻工具测试脚本
- 只测试新闻工具，不运行交易循环
- 不会覆盖任何交易记录或持仓数据
- 可以安全地测试新闻工具功能
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.tools.news_tools import news_scan, plan_and_scan_news
from src.tools.jin10_tools import fetch_jin10_news


def test_news_scan():
    """测试 news_scan 工具"""
    print("\n" + "="*60)
    print("测试 news_scan 工具")
    print("="*60)
    
    keywords = ["NVDA", "AAPL", "market", "stocks"]
    print(f"\n关键词: {keywords}")
    
    try:
        result = news_scan(
            keywords=keywords,
            max_articles=10,
            recency_days=2
        )
        
        hits = result.get("hits", [])
        queries = result.get("queries", [])
        
        print(f"\n✅ 成功获取 {len(hits)} 条新闻")
        print(f"查询: {queries}")
        
        if hits:
            print(f"\n前5条新闻:")
            for i, hit in enumerate(hits[:5], 1):
                print(f"  {i}. {hit.get('title', 'No title')[:80]}")
                print(f"     来源: {hit.get('source', 'Unknown')}")
                print(f"     链接: {hit.get('link', 'No link')[:80]}")
                if hit.get('published'):
                    print(f"     时间: {hit.get('published')}")
        else:
            print("⚠️ 没有找到新闻")
            
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_plan_and_scan_news():
    """测试 plan_and_scan_news 工具"""
    print("\n" + "="*60)
    print("测试 plan_and_scan_news 工具")
    print("="*60)
    
    tickers = ["NVDA", "AAPL", "TSLA"]
    mview = {
        "sample_stocks": tickers,
        "market_summary": "Testing news tools"
    }
    
    print(f"\n股票代码: {tickers}")
    
    try:
        result = plan_and_scan_news(
            tickers=tickers,
            mview=mview,
            recency_days=2,
            max_articles=10,
            fetch_body_top=5  # 获取前5篇文章的内容
        )
        
        hits = result.get("hits", [])
        articles = result.get("articles", [])
        queries = result.get("queries", [])
        
        print(f"\n✅ 成功获取:")
        print(f"  - Hits: {len(hits)} 条")
        print(f"  - Articles (有内容): {len(articles)} 条")
        print(f"  - 查询: {queries}")
        
        if articles:
            print(f"\n前3篇文章详情:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. {article.get('title', 'No title')[:80]}")
                print(f"     来源: {article.get('source', 'Unknown')}")
                print(f"     链接: {article.get('url', 'No link')[:80]}")
                if article.get('summary'):
                    print(f"     摘要: {article.get('summary')[:100]}...")
                if article.get('keywords'):
                    print(f"     关键词: {', '.join(article.get('keywords', [])[:5])}")
        elif hits:
            print(f"\n前3条新闻标题:")
            for i, hit in enumerate(hits[:3], 1):
                print(f"  {i}. {hit.get('title', 'No title')[:80]}")
        else:
            print("⚠️ 没有找到新闻")
            
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fetch_jin10_news():
    """测试 fetch_jin10_news 工具"""
    print("\n" + "="*60)
    print("测试 fetch_jin10_news 工具")
    print("="*60)
    
    try:
        result = fetch_jin10_news(
            max_items=10,
            category="all"
        )
        
        if result.get("ok"):
            items = result.get("items", [])
            count = result.get("count", 0)
            
            print(f"\n✅ 成功获取 {count} 条新闻")
            
            if items:
                print(f"\n前5条新闻:")
                for i, item in enumerate(items[:5], 1):
                    print(f"  {i}. {item.get('title', 'No title')[:80]}")
                    print(f"     时间: {item.get('time', 'Unknown')}")
                    if item.get('content'):
                        print(f"     内容: {item.get('content')[:100]}...")
            else:
                print("⚠️ 没有找到新闻")
        else:
            print(f"❌ 错误: {result.get('error', 'Unknown error')}")
            
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_test_results(results: Dict[str, Any], output_file: Path):
    """保存测试结果到文件（不影响交易记录）"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_type": "news_tools_test",
        "results": results
    }
    
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试结果已保存到: {output_file}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("新闻工具测试脚本")
    print("="*60)
    print("\n⚠️  注意: 此脚本只测试新闻工具，不会影响交易记录或持仓数据")
    print("="*60)
    
    results = {}
    
    # 测试 news_scan
    results["news_scan"] = test_news_scan()
    
    # 测试 plan_and_scan_news
    results["plan_and_scan_news"] = test_plan_and_scan_news()
    
    # 测试 fetch_jin10_news
    results["fetch_jin10_news"] = test_fetch_jin10_news()
    
    # 保存测试结果
    output_file = ROOT / "data" / "logs" / "news_test_results.json"
    save_test_results(results, output_file)
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
    print("\n测试结果已保存，不会影响任何交易记录或持仓数据")


if __name__ == "__main__":
    main()
