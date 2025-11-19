#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的新闻工具测试脚本
- 只测试新闻工具，不运行完整的交易循环
- 不会覆盖任何交易记录或持仓数据
- 可以安全地测试新闻工具的功能
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any

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
    print("Testing news_scan tool")
    print("="*60)
    
    keywords = ["NVDA", "AAPL", "market", "stocks"]
    print(f"\nKeywords: {keywords}")
    
    try:
        result = news_scan(
            keywords=keywords,
            max_articles=10,
            recency_days=2
        )
        
        print(f"\nResult structure: {list(result.keys())}")
        hits = result.get("hits", [])
        queries = result.get("queries", [])
        
        print(f"\nQueries used: {queries}")
        print(f"\nFound {len(hits)} news hits")
        
        if hits:
            print("\nFirst 3 hits:")
            for i, hit in enumerate(hits[:3], 1):
                print(f"\n{i}. {hit.get('title', 'No title')}")
                print(f"   Source: {hit.get('source', 'Unknown')}")
                print(f"   Link: {hit.get('link', 'No link')}")
                print(f"   Published: {hit.get('published', 'Unknown')}")
        else:
            print("\n⚠️  No hits found!")
        
        return result
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_plan_and_scan_news():
    """测试 plan_and_scan_news 工具"""
    print("\n" + "="*60)
    print("Testing plan_and_scan_news tool")
    print("="*60)
    
    tickers = ["NVDA", "AAPL", "TSLA"]
    mview = {
        "sample_stocks": tickers,
        "market_summary": "Testing news tools"
    }
    
    print(f"\nTickers: {tickers}")
    
    try:
        result = plan_and_scan_news(
            tickers=tickers,
            mview=mview,
            recency_days=2,
            max_articles=10,
            fetch_body_top=3  # 获取前3篇文章的内容
        )
        
        print(f"\nResult structure: {list(result.keys())}")
        queries = result.get("queries", [])
        hits = result.get("hits", [])
        articles = result.get("articles", [])
        
        print(f"\nQueries generated: {queries}")
        print(f"\nFound {len(hits)} hits")
        print(f"Found {len(articles)} articles with content")
        
        if articles:
            print("\nFirst 3 articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article.get('title', 'No title')}")
                print(f"   Source: {article.get('source', 'Unknown')}")
                print(f"   URL: {article.get('url', 'No URL')}")
                summary = article.get('summary', '')
                keywords = article.get('keywords', [])
                if summary:
                    print(f"   Summary: {summary[:100]}...")
                if keywords:
                    print(f"   Keywords: {', '.join(keywords)}")
        elif hits:
            print("\nArticles not available, showing hits:")
            for i, hit in enumerate(hits[:3], 1):
                print(f"\n{i}. {hit.get('title', 'No title')}")
                print(f"   Source: {hit.get('source', 'Unknown')}")
                print(f"   Link: {hit.get('link', 'No link')}")
        else:
            print("\n⚠️  No news found!")
        
        return result
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fetch_jin10_news():
    """测试 fetch_jin10_news 工具"""
    print("\n" + "="*60)
    print("Testing fetch_jin10_news tool")
    print("="*60)
    
    try:
        result = fetch_jin10_news(
            max_items=10,
            category="all"
        )
        
        if result.get("ok"):
            items = result.get("items", [])
            count = result.get("count", 0)
            
            print(f"\nFound {count} news items")
            
            if items:
                print("\nFirst 3 items:")
                for i, item in enumerate(items[:3], 1):
                    print(f"\n{i}. {item.get('title', 'No title')}")
                    print(f"   Time: {item.get('time', 'Unknown')}")
                    print(f"   Category: {item.get('category', 'Unknown')}")
                    content = item.get('content', '')
                    if content:
                        print(f"   Content: {content[:100]}...")
                    url = item.get('url', '')
                    if url:
                        print(f"   URL: {url}")
            else:
                print("\n⚠️  No items found!")
        else:
            print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        return result
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_test_results(results: Dict[str, Any], output_file: Path):
    """保存测试结果到文件（不影响交易记录）"""
    try:
        # 只保存摘要信息，不保存完整内容
        summary = {
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_date": date.today().isoformat(),
            "results": {}
        }
        
        for tool_name, result in results.items():
            if result:
                if tool_name == "news_scan":
                    summary["results"][tool_name] = {
                        "hits_count": len(result.get("hits", [])),
                        "queries": result.get("queries", [])
                    }
                elif tool_name == "plan_and_scan_news":
                    summary["results"][tool_name] = {
                        "hits_count": len(result.get("hits", [])),
                        "articles_count": len(result.get("articles", [])),
                        "queries": result.get("queries", [])
                    }
                elif tool_name == "fetch_jin10_news":
                    summary["results"][tool_name] = {
                        "ok": result.get("ok", False),
                        "items_count": result.get("count", 0)
                    }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Test results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Failed to save test results: {e}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("News Tools Test Script")
    print("="*60)
    print("\nThis script tests news tools WITHOUT running trading cycle.")
    print("It will NOT modify any trading records or portfolio data.")
    print("="*60)
    
    results = {}
    
    # 测试各个新闻工具
    print("\n1. Testing news_scan...")
    results["news_scan"] = test_news_scan()
    
    print("\n2. Testing plan_and_scan_news...")
    results["plan_and_scan_news"] = test_plan_and_scan_news()
    
    print("\n3. Testing fetch_jin10_news...")
    results["fetch_jin10_news"] = test_fetch_jin10_news()
    
    # 保存测试结果
    output_file = Path(__file__).parent.parent / "data" / "logs" / "news_tools_test_results.json"
    save_test_results(results, output_file)
    
    # 总结
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for tool_name, result in results.items():
        if result:
            if tool_name == "news_scan":
                hits = len(result.get("hits", []))
                print(f"✅ {tool_name}: {hits} hits found")
            elif tool_name == "plan_and_scan_news":
                hits = len(result.get("hits", []))
                articles = len(result.get("articles", []))
                print(f"✅ {tool_name}: {hits} hits, {articles} articles")
            elif tool_name == "fetch_jin10_news":
                if result.get("ok"):
                    count = result.get("count", 0)
                    print(f"✅ {tool_name}: {count} items found")
                else:
                    print(f"❌ {tool_name}: Failed")
        else:
            print(f"❌ {tool_name}: Failed")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)


if __name__ == "__main__":
    main()
