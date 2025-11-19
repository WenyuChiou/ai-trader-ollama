#!/usr/bin/env python3
"""
测试所有新闻工具的实际功能，确定哪些可用哪些不可用
"""
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

def test_news_scan():
    """测试 news_scan 工具"""
    print("\n" + "="*80)
    print("📰 Testing news_scan tool")
    print("="*80)
    
    try:
        from src.tools.news_tools import news_scan
        
        print("Testing with keywords: ['NVDA', 'market', 'AI']")
        result = news_scan(
            keywords=["NVDA", "market", "AI"],
            max_articles=5,
            recency_days=2
        )
        
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            hits = result.get("hits", [])
            queries = result.get("queries", [])
            print(f"✅ news_scan executed successfully")
            print(f"   Hits: {len(hits)}")
            print(f"   Queries: {queries}")
            if hits:
                print(f"   First hit: {hits[0].get('title', 'N/A')[:80]}...")
                return {"ok": True, "hits": len(hits), "tool": "news_scan"}
            else:
                print(f"   ⚠️  No hits returned")
                return {"ok": True, "hits": 0, "tool": "news_scan", "warning": "No data"}
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return {"ok": False, "error": f"Unexpected result type: {type(result)}", "tool": "news_scan"}
    except Exception as e:
        import traceback
        print(f"❌ news_scan failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"ok": False, "error": str(e), "tool": "news_scan"}

def test_plan_and_scan_news():
    """测试 plan_and_scan_news 工具"""
    print("\n" + "="*80)
    print("📰 Testing plan_and_scan_news tool")
    print("="*80)
    
    try:
        from src.tools.news_tools import plan_and_scan_news
        
        print("Testing with tickers: ['NVDA', 'AAPL']")
        result = plan_and_scan_news(
            tickers=["NVDA", "AAPL"],
            mview={},
            max_articles=5,
            recency_days=2,
            fetch_body_top=2  # 获取前2篇文章的内容
        )
        
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            hits = result.get("hits", [])
            articles = result.get("articles", [])
            queries = result.get("queries", [])
            print(f"✅ plan_and_scan_news executed successfully")
            print(f"   Hits: {len(hits)}")
            print(f"   Articles (with content): {len(articles)}")
            print(f"   Queries: {queries}")
            if articles:
                print(f"   First article: {articles[0].get('title', 'N/A')[:80]}...")
                print(f"   Has excerpt: {bool(articles[0].get('excerpt'))}")
            elif hits:
                print(f"   First hit: {hits[0].get('title', 'N/A')[:80]}...")
            if articles or hits:
                return {"ok": True, "hits": len(hits), "articles": len(articles), "tool": "plan_and_scan_news"}
            else:
                print(f"   ⚠️  No hits or articles returned")
                return {"ok": True, "hits": 0, "articles": 0, "tool": "plan_and_scan_news", "warning": "No data"}
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return {"ok": False, "error": f"Unexpected result type: {type(result)}", "tool": "plan_and_scan_news"}
    except Exception as e:
        import traceback
        print(f"❌ plan_and_scan_news failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"ok": False, "error": str(e), "tool": "plan_and_scan_news"}

def test_fetch_jin10_news():
    """测试 fetch_jin10_news 工具"""
    print("\n" + "="*80)
    print("📰 Testing fetch_jin10_news tool")
    print("="*80)
    
    try:
        from src.tools.jin10_tools import fetch_jin10_news
        
        print("Testing with max_items=10")
        result = fetch_jin10_news(max_items=10, category="all")
        
        print(f"Result type: {type(result)}")
        if isinstance(result, dict):
            ok = result.get("ok", False)
            items = result.get("items", [])
            count = result.get("count", 0)
            print(f"✅ fetch_jin10_news executed successfully")
            print(f"   OK: {ok}")
            print(f"   Items: {len(items)}")
            print(f"   Count: {count}")
            if items:
                print(f"   First item: {items[0].get('title', 'N/A')[:80]}...")
                return {"ok": True, "items": len(items), "tool": "fetch_jin10_news"}
            else:
                print(f"   ⚠️  No items returned")
                return {"ok": True, "items": 0, "tool": "fetch_jin10_news", "warning": "No data"}
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return {"ok": False, "error": f"Unexpected result type: {type(result)}", "tool": "fetch_jin10_news"}
    except Exception as e:
        import traceback
        print(f"❌ fetch_jin10_news failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"ok": False, "error": str(e), "tool": "fetch_jin10_news"}

def test_toolbox_integration():
    """测试工具箱集成"""
    print("\n" + "="*80)
    print("🔧 Testing ToolBox Integration")
    print("="*80)
    
    try:
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        available_tools = toolbox.list()
        
        print(f"Available tools: {len(available_tools)}")
        
        # 检查新闻相关工具
        news_tools = [t for t in available_tools if "news" in t.lower() or "scan" in t.lower()]
        print(f"\nNews-related tools: {news_tools}")
        
        # 测试每个新闻工具
        results = {}
        for tool_name in news_tools:
            print(f"\n--- Testing {tool_name} via ToolBox ---")
            try:
                if tool_name == "news_scan":
                    result = toolbox.invoke("news_scan", keywords=["NVDA"], max_articles=3, recency_days=2)
                elif tool_name == "plan_and_scan_news":
                    result = toolbox.invoke("plan_and_scan_news", tickers=["NVDA"], mview={}, max_articles=3, recency_days=2, fetch_body_top=2)
                elif tool_name == "fetch_jin10_news":
                    result = toolbox.invoke("fetch_jin10_news", max_items=5, category="all")
                else:
                    print(f"   ⚠️  Unknown tool, skipping")
                    continue
                
                print(f"   Result type: {type(result)}")
                if isinstance(result, dict):
                    ok = result.get("ok", False)
                    if ok:
                        actual_result = result.get("result", result)
                        print(f"   ✅ ToolBox invoke successful")
                        if isinstance(actual_result, dict):
                            hits = actual_result.get("hits", [])
                            articles = actual_result.get("articles", [])
                            items = actual_result.get("items", [])
                            print(f"      Hits: {len(hits)}, Articles: {len(articles)}, Items: {len(items)}")
                            results[tool_name] = {"ok": True, "hits": len(hits), "articles": len(articles), "items": len(items)}
                        else:
                            print(f"      Result: {str(actual_result)[:100]}...")
                            results[tool_name] = {"ok": True, "result": str(actual_result)[:100]}
                    else:
                        error = result.get("error", "Unknown error")
                        print(f"   ❌ ToolBox invoke failed: {error}")
                        results[tool_name] = {"ok": False, "error": error}
                else:
                    print(f"   ❌ Unexpected result type: {type(result)}")
                    results[tool_name] = {"ok": False, "error": f"Unexpected type: {type(result)}"}
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                import traceback
                traceback.print_exc()
                results[tool_name] = {"ok": False, "error": str(e)}
        
        return {"ok": True, "results": results, "available_tools": news_tools}
    except Exception as e:
        import traceback
        print(f"❌ ToolBox integration test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"ok": False, "error": str(e)}

def main():
    """Main function"""
    print("="*80)
    print("🧪 News Tools Test")
    print("="*80)
    
    results = {}
    
    # 测试直接调用
    print("\n" + "="*80)
    print("📋 Direct Function Tests")
    print("="*80)
    
    results["news_scan"] = test_news_scan()
    results["plan_and_scan_news"] = test_plan_and_scan_news()
    results["fetch_jin10_news"] = test_fetch_jin10_news()
    
    # 测试工具箱集成
    toolbox_result = test_toolbox_integration()
    results["toolbox"] = toolbox_result
    
    # 总结
    print("\n" + "="*80)
    print("📊 Summary")
    print("="*80)
    
    print("\nDirect Function Tests:")
    for tool_name, result in results.items():
        if tool_name == "toolbox":
            continue
        if result.get("ok"):
            status = "✅"
            if "warning" in result:
                status = "⚠️"
            print(f"{status} {tool_name}: OK")
            if "hits" in result:
                print(f"   Hits: {result['hits']}")
            if "articles" in result:
                print(f"   Articles: {result['articles']}")
            if "items" in result:
                print(f"   Items: {result['items']}")
        else:
            print(f"❌ {tool_name}: FAILED - {result.get('error', 'Unknown error')}")
    
    print("\nToolBox Integration:")
    if toolbox_result.get("ok"):
        print("✅ ToolBox integration: OK")
        if "results" in toolbox_result:
            for tool_name, result in toolbox_result["results"].items():
                if result.get("ok"):
                    print(f"   ✅ {tool_name}: OK")
                    if "hits" in result:
                        print(f"      Hits: {result['hits']}, Articles: {result['articles']}, Items: {result['items']}")
                else:
                    print(f"   ❌ {tool_name}: FAILED - {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ ToolBox integration: FAILED - {toolbox_result.get('error', 'Unknown error')}")
    
    # 推荐使用的工具
    print("\n" + "="*80)
    print("💡 Recommendations")
    print("="*80)
    
    working_tools = []
    for tool_name, result in results.items():
        if tool_name == "toolbox":
            continue
        if result.get("ok") and (result.get("hits", 0) > 0 or result.get("articles", 0) > 0 or result.get("items", 0) > 0):
            working_tools.append(tool_name)
    
    if working_tools:
        print(f"✅ Working tools (with data): {', '.join(working_tools)}")
        print(f"   Recommended: Use these tools in agent prompts")
    else:
        print("⚠️  No tools returned data (may be network/API issues)")
        print("   Check network connection and API availability")
    
    # 检查工具箱中的工具
    if toolbox_result.get("ok") and "results" in toolbox_result:
        toolbox_working = [t for t, r in toolbox_result["results"].items() if r.get("ok")]
        if toolbox_working:
            print(f"✅ ToolBox working tools: {', '.join(toolbox_working)}")
    
    return 0 if working_tools else 1

if __name__ == "__main__":
    sys.exit(main())

