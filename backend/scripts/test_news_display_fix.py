#!/usr/bin/env python3
"""
测试新闻显示修复 - 模拟数组对象格式的数据
"""
import json

def test_array_like_object_parsing():
    """测试数组对象格式的新闻数据解析"""
    
    # 模拟数组对象格式（键为数字字符串）
    array_like_object = {}
    for i in range(83):
        array_like_object[str(i)] = {
            "title": f"News Article {i+1}",
            "link": f"https://example.com/news/{i+1}",
            "source": "CNBC" if i % 2 == 0 else "MarketWatch",
            "published": "2025-01-28T10:00:00Z",
            "excerpt": f"This is a sample news article {i+1}"
        }
    
    print("=" * 80)
    print("[TEST] Testing Array-Like Object Parsing")
    print("=" * 80)
    
    print(f"\n[1] Created array-like object with {len(array_like_object)} keys")
    print(f"    Keys: {list(array_like_object.keys())[:10]}...")
    
    # 测试键检测逻辑（模拟前端代码）
    keys = list(array_like_object.keys())
    numeric_keys = [k for k in keys if str(k).isdigit()]
    
    print(f"\n[2] Key Analysis:")
    print(f"    Total keys: {len(keys)}")
    print(f"    Numeric keys: {len(numeric_keys)}")
    print(f"    All numeric: {len(numeric_keys) == len(keys)}")
    print(f"    >= 80% numeric: {len(numeric_keys) >= len(keys) * 0.8}")
    print(f"    >= 10 numeric: {len(numeric_keys) >= 10}")
    
    # 检查是否应该被识别为数组对象
    is_array_like = (
        len(numeric_keys) == len(keys) or 
        (len(numeric_keys) >= len(keys) * 0.8 and len(numeric_keys) >= 3) or
        (len(numeric_keys) >= 10)
    )
    
    print(f"\n[3] Array-Like Detection:")
    print(f"    Should be detected as array-like: {is_array_like}")
    
    if is_array_like:
        # 转换为数组
        array_values = list(array_like_object.values())
        print(f"\n[4] Conversion:")
        print(f"    Converted to array: {len(array_values)} items")
        print(f"    First item: {json.dumps(array_values[0], indent=2)[:200]}")
        
        # 检查是否能提取新闻数据
        news_items = []
        for item in array_values:
            if isinstance(item, dict):
                title = item.get("title") or item.get("headline") or item.get("name") or ""
                link = item.get("link") or item.get("href") or item.get("url") or ""
                if title or link:
                    news_items.append({
                        "title": title or "No title",
                        "link": link,
                        "source": item.get("source", "Unknown"),
                        "published": item.get("published", ""),
                        "excerpt": item.get("excerpt", "")
                    })
        
        print(f"\n[5] News Items Extraction:")
        print(f"    Extracted {len(news_items)} news items")
        if news_items:
            print(f"    Sample item: {json.dumps(news_items[0], indent=2)}")
    
    print("\n" + "=" * 80)
    print("[TEST] Complete")
    print("=" * 80)
    
    return is_array_like and len(news_items) > 0

if __name__ == "__main__":
    success = test_array_like_object_parsing()
    exit(0 if success else 1)

