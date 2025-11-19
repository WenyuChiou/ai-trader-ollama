#!/usr/bin/env python3
"""
测试新闻API返回的数据格式
"""
import requests
import json

def test_news_api():
    """测试新闻API返回的数据结构"""
    base_url = "http://localhost:8000"
    
    print("=" * 80)
    print("[TEST] Testing News API Data Format")
    print("=" * 80)
    
    # 1. 获取conversations数据
    try:
        print("\n[1] Fetching conversations...")
        response = requests.get(f"{base_url}/api/agents/conversations?limit=100")
        if response.status_code != 200:
            print(f"[ERROR] API returned status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        if not data.get("ok"):
            print(f"[ERROR] API returned error: {data.get('error')}")
            return
        
        tool_results_by_category = data.get("tool_results_by_category", {})
        news_tools = tool_results_by_category.get("news", [])
        
        print(f"[OK] Found {len(news_tools)} news tool results")
        
        if len(news_tools) == 0:
            print("[WARN] No news tools found in tool_results_by_category")
            print("[INFO] Checking conversations for news tools...")
            
            conversations = data.get("conversations", [])
            news_convs = [c for c in conversations if c.get("type") == "tool" and 
                         ("news" in (c.get("tool_name") or "").lower() or 
                          "plan_and_scan" in (c.get("tool_name") or "").lower())]
            print(f"[INFO] Found {len(news_convs)} news tool conversations")
            
            if len(news_convs) > 0:
                print("\n[INFO] Sample news tool conversation:")
                sample = news_convs[0]
                print(f"  Tool name: {sample.get('tool_name')}")
                print(f"  Content: {sample.get('content', '')[:200]}")
                tool_result = sample.get('tool_result', {})
                print(f"  Tool result type: {type(tool_result)}")
                if isinstance(tool_result, dict):
                    print(f"  Tool result keys: {list(tool_result.keys())[:20]}")
                    print(f"  Tool result: {json.dumps(tool_result, indent=2)[:500]}")
                elif isinstance(tool_result, list):
                    print(f"  Tool result length: {len(tool_result)}")
                    if len(tool_result) > 0:
                        print(f"  First item: {json.dumps(tool_result[0], indent=2)[:300]}")
        else:
            # 分析每个新闻工具的结果
            for i, news_tool in enumerate(news_tools[:3]):  # 只检查前3个
                print(f"\n[2.{i+1}] Analyzing news tool {i+1}:")
                tool_name = news_tool.get("tool_name", "Unknown")
                tool_result = news_tool.get("tool_result", {})
                
                print(f"  Tool name: {tool_name}")
                print(f"  Tool result type: {type(tool_result)}")
                
                if isinstance(tool_result, dict):
                    keys = list(tool_result.keys())
                    print(f"  Keys ({len(keys)}): {keys[:20]}{'...' if len(keys) > 20 else ''}")
                    
                    # 检查是否是数组对象
                    numeric_keys = [k for k in keys if str(k).isdigit()]
                    print(f"  Numeric keys: {len(numeric_keys)}/{len(keys)}")
                    
                    if numeric_keys:
                        print(f"  [INFO] This appears to be an array-like object!")
                        print(f"  Sample numeric keys: {numeric_keys[:10]}")
                        # 检查第一个元素的结构
                        if numeric_keys:
                            first_key = numeric_keys[0]
                            first_item = tool_result.get(first_key)
                            if first_item:
                                print(f"  First item type: {type(first_item)}")
                                if isinstance(first_item, dict):
                                    print(f"  First item keys: {list(first_item.keys())[:10]}")
                                    print(f"  First item sample: {json.dumps(first_item, indent=2)[:300]}")
                    
                    # 检查标准格式
                    if "hits" in tool_result:
                        hits = tool_result["hits"]
                        print(f"  [OK] Found 'hits' array: {len(hits) if isinstance(hits, list) else 'not a list'} items")
                    if "items" in tool_result:
                        items = tool_result["items"]
                        print(f"  [OK] Found 'items' array: {len(items) if isinstance(items, list) else 'not a list'} items")
                    if "articles" in tool_result:
                        articles = tool_result["articles"]
                        print(f"  [OK] Found 'articles' array: {len(articles) if isinstance(articles, list) else 'not a list'} items")
                
                elif isinstance(tool_result, list):
                    print(f"  [OK] Tool result is a list: {len(tool_result)} items")
                    if len(tool_result) > 0:
                        print(f"  First item type: {type(tool_result[0])}")
                        if isinstance(tool_result[0], dict):
                            print(f"  First item keys: {list(tool_result[0].keys())[:10]}")
                
                else:
                    print(f"  [WARN] Unexpected tool_result type: {type(tool_result)}")
                    print(f"  Tool result: {str(tool_result)[:200]}")
        
        print("\n" + "=" * 80)
        print("[TEST] Complete")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API. Is the server running?")
        print(f"[INFO] Expected URL: {base_url}")
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news_api()

