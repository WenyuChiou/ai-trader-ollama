#!/usr/bin/env python3
"""
端到端测试：验证新闻工具从调用到前端显示的完整流程
"""
import sys
import os
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_news_tool_execution():
    """测试1: 验证新闻工具能被正确调用并返回数据"""
    print("=" * 80)
    print("[TEST 1] Testing News Tool Execution")
    print("=" * 80)
    
    try:
        from src.agents.toolbox import ToolBox
        from src.tools.news_tools import plan_and_scan_news
        
        toolbox = ToolBox()
        
        # 测试1.1: 直接调用plan_and_scan_news
        print("\n[1.1] Direct call to plan_and_scan_news...")
        result = plan_and_scan_news(
            tickers=["NVDA", "AAPL"],
            mview={},
            max_articles=5,
            recency_days=2,
            fetch_body_top=3
        )
        
        if result:
            hits = result.get("hits", [])
            articles = result.get("articles", [])
            queries = result.get("queries", [])
            
            print(f"  [OK] Tool executed successfully")
            print(f"  - Hits: {len(hits)}")
            print(f"  - Articles: {len(articles)}")
            print(f"  - Queries: {queries}")
            
            if len(hits) > 0 or len(articles) > 0:
                print(f"  [OK] News data retrieved: {len(hits) + len(articles)} items")
                if articles:
                    print(f"  - Sample article: {articles[0].get('title', 'No title')[:50]}...")
                return True
            else:
                print(f"  [WARN] No news data returned (may be normal if no recent news)")
                return False
        else:
            print(f"  [ERROR] Tool returned None")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_tool_via_toolbox():
    """测试2: 通过ToolBox调用新闻工具（模拟agent调用）"""
    print("\n" + "=" * 80)
    print("[TEST 2] Testing News Tool via ToolBox (Agent Simulation)")
    print("=" * 80)
    
    try:
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        
        # 测试2.1: 通过ToolBox调用plan_and_scan_news
        print("\n[2.1] Calling plan_and_scan_news via ToolBox...")
        result = toolbox.invoke(
            "plan_and_scan_news",
            tickers=["NVDA"],
            mview={},
            max_articles=5,
            recency_days=2,
            fetch_body_top=3
        )
        
        if result and result.get("ok"):
            actual_result = result.get("result", result)
            hits = actual_result.get("hits", [])
            articles = actual_result.get("articles", [])
            
            print(f"  [OK] ToolBox invocation successful")
            print(f"  - Hits: {len(hits)}")
            print(f"  - Articles: {len(articles)}")
            
            if len(hits) > 0 or len(articles) > 0:
                print(f"  [OK] News data retrieved via ToolBox")
                return True, actual_result
            else:
                print(f"  [WARN] No news data (may be normal)")
                return False, actual_result
        else:
            print(f"  [ERROR] ToolBox invocation failed: {result}")
            return False, None
            
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_news_formatting_for_agent():
    """测试3: 验证新闻数据格式化（供agent使用）"""
    print("\n" + "=" * 80)
    print("[TEST 3] Testing News Data Formatting for Agent")
    print("=" * 80)
    
    try:
        from src.agents.multi_analyst_system import _format_tool_result
        
        # 模拟新闻工具返回结果
        mock_news_result = {
            "hits": [
                {
                    "title": "NVDA Stock Surges on AI Demand",
                    "link": "https://example.com/news1",
                    "source": "CNBC",
                    "published": "2025-01-28T10:00:00Z"
                }
            ],
            "articles": [
                {
                    "title": "NVDA Stock Surges on AI Demand",
                    "url": "https://example.com/news1",
                    "source": "CNBC",
                    "excerpt": "NVIDIA Corporation shares surged today as demand for AI chips continues to grow.",
                    "summary": "NVIDIA stock rises due to increasing AI chip demand.",
                    "keywords": ["NVDA", "AI", "chips"]
                }
            ],
            "queries": ["NVDA stock"]
        }
        
        print("\n[3.1] Formatting news result for agent...")
        formatted = _format_tool_result("plan_and_scan_news", mock_news_result)
        
        print(f"  [OK] Formatting successful")
        print(f"  - Formatted length: {len(formatted)} characters")
        print(f"  - Contains title: {'Title:' in formatted}")
        print(f"  - Contains content: {'Content:' in formatted or 'Summary:' in formatted}")
        print(f"\n  Sample formatted output (first 300 chars):")
        print(f"  {formatted[:300]}...")
        
        # 检查格式化结果是否包含必要信息
        has_title = "Title:" in formatted or "NVDA Stock" in formatted
        has_content = "Content:" in formatted or "Summary:" in formatted or "excerpt" in formatted.lower()
        
        if has_title and has_content:
            print(f"  [OK] Formatted result contains necessary information for agent")
            return True
        else:
            print(f"  [WARN] Formatted result may be missing some information")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_api_response():
    """测试4: 验证API返回的新闻数据格式"""
    print("\n" + "=" * 80)
    print("[TEST 4] Testing News API Response Format")
    print("=" * 80)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        print("\n[4.1] Fetching conversations from API...")
        response = requests.get(f"{base_url}/api/agents/conversations?limit=100", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tool_results_by_category = data.get("tool_results_by_category", {})
            news_tools = tool_results_by_category.get("news", [])
            
            print(f"  [OK] API response received")
            print(f"  - News tools in response: {len(news_tools)}")
            
            if len(news_tools) > 0:
                print(f"  [OK] News tools found in API response")
                
                # 检查第一个新闻工具的结果格式
                first_tool = news_tools[0]
                tool_result = first_tool.get("tool_result", {})
                
                print(f"\n[4.2] Analyzing first news tool result...")
                print(f"  - Tool name: {first_tool.get('tool_name')}")
                print(f"  - Result type: {type(tool_result)}")
                
                if isinstance(tool_result, dict):
                    keys = list(tool_result.keys())
                    print(f"  - Result keys: {keys[:10]}...")
                    
                    # 检查是否是数组对象
                    numeric_keys = [k for k in keys if str(k).isdigit()]
                    is_array_like = len(numeric_keys) >= len(keys) * 0.8 or len(numeric_keys) >= 10
                    
                    print(f"  - Numeric keys: {len(numeric_keys)}/{len(keys)}")
                    print(f"  - Is array-like: {is_array_like}")
                    
                    if is_array_like:
                        print(f"  [OK] Result is array-like object (can be converted to array)")
                        # 尝试转换为数组
                        array_values = list(tool_result.values())
                        print(f"  - Converted to array: {len(array_values)} items")
                        
                        # 检查是否能提取新闻数据
                        news_items = []
                        for item in array_values[:5]:  # 只检查前5个
                            if isinstance(item, dict):
                                title = item.get("title") or item.get("headline") or ""
                                link = item.get("link") or item.get("href") or item.get("url") or ""
                                if title or link:
                                    news_items.append({"title": title, "link": link})
                        
                        print(f"  - Extractable news items: {len(news_items)}")
                        if news_items:
                            print(f"  [OK] Can extract news data from array-like object")
                            return True
                        else:
                            print(f"  [WARN] Cannot extract news data (may need field name adjustments)")
                            return False
                    else:
                        # 检查标准格式
                        hits = tool_result.get("hits", [])
                        articles = tool_result.get("articles", [])
                        items = tool_result.get("items", [])
                        
                        print(f"  - Hits: {len(hits)}")
                        print(f"  - Articles: {len(articles)}")
                        print(f"  - Items: {len(items)}")
                        
                        if len(hits) > 0 or len(articles) > 0 or len(items) > 0:
                            print(f"  [OK] Standard format detected with news data")
                            return True
                        else:
                            print(f"  [WARN] Standard format but no news data")
                            return False
                else:
                    print(f"  [WARN] Unexpected result type")
                    return False
            else:
                print(f"  [WARN] No news tools in API response (may need to run trading cycle first)")
                return False
        else:
            print(f"  [ERROR] API request failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  [WARN] Cannot connect to API (server may not be running)")
        print(f"  Skipping API test...")
        return None
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("END-TO-END NEWS TESTING")
    print("=" * 80)
    
    results = {}
    
    # 测试1: 新闻工具执行
    results["tool_execution"] = test_news_tool_execution()
    
    # 测试2: 通过ToolBox调用
    success, news_data = test_news_tool_via_toolbox()
    results["toolbox_invocation"] = success
    
    # 测试3: 数据格式化
    results["formatting"] = test_news_formatting_for_agent()
    
    # 测试4: API响应格式
    api_result = test_news_api_response()
    results["api_response"] = api_result
    
    # 总结
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results.items():
        if result is None:
            status = "[SKIP]"
        elif result:
            status = "[PASS]"
        else:
            status = "[FAIL]"
        print(f"  {test_name}: {status}")
    
    all_passed = all(r for r in results.values() if r is not None)
    some_passed = any(r for r in results.values() if r)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[OK] ALL TESTS PASSED")
    elif some_passed:
        print("[WARN] SOME TESTS PASSED (check warnings)")
    else:
        print("[ERROR] TESTS FAILED")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

