"""
测试新闻数据解析
检查新闻工具是否被正确调用和解析
"""
import sys
import os
import json
import io
from pathlib import Path

# Fix Unicode encoding for Windows PowerShell
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

def test_news_parsing():
    """测试新闻数据解析"""
    print("=" * 80)
    print("测试新闻数据解析")
    print("=" * 80)
    
    # 读取 discussion_actions.jsonl
    logs_dir = project_root / "data" / "logs"
    if not logs_dir.exists():
        print(f"[ERROR] 日志目录不存在: {logs_dir}")
        return
    
    # 查找最新的 discussion_actions.jsonl
    discussion_files = list(logs_dir.glob("**/discussion_actions.jsonl"))
    if not discussion_files:
        print(f"[ERROR] 找不到 discussion_actions.jsonl")
        return
    
    # 使用最新的文件
    discussion_file = max(discussion_files, key=lambda p: p.stat().st_mtime)
    print(f"[INFO] 使用文件: {discussion_file}")
    
    # 读取所有对话
    conversations = []
    news_tools = []
    
    with open(discussion_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                conversations.append(entry)
                
                # 检查是否是新闻工具
                if entry.get("type") == "tool":
                    tool_name = entry.get("tool_name", "")
                    if tool_name in ["news_scan", "plan_and_scan_news", "get_news_scan"]:
                        news_tools.append(entry)
            except json.JSONDecodeError as e:
                print(f"[WARN] 跳过无效的 JSON 行: {e}")
                continue
    
    print(f"\n[INFO] 总共找到 {len(conversations)} 条对话记录")
    print(f"[INFO] 找到 {len(news_tools)} 个新闻工具调用\n")
    
    if len(news_tools) == 0:
        print("[WARN] 没有找到新闻工具调用！")
        print("可能的原因：")
        print("  1. 新闻工具没有被调用")
        print("  2. 工具名称不匹配（检查 tool_name 字段）")
        print("  3. 数据文件路径不正确")
        return
    
    # 分析每个新闻工具
    for i, tool_entry in enumerate(news_tools, 1):
        print(f"\n{'=' * 80}")
        print(f"新闻工具 #{i}: {tool_entry.get('tool_name', 'Unknown')}")
        print(f"{'=' * 80}")
        print(f"Agent: {tool_entry.get('agent', 'Unknown')}")
        print(f"Timestamp: {tool_entry.get('timestamp', 'Unknown')}")
        print(f"Tool Category: {tool_entry.get('tool_category', 'Unknown')}")
        
        # 检查 tool_result
        tool_result = tool_entry.get("tool_result", {})
        print(f"\nTool Result Type: {type(tool_result)}")
        
        if isinstance(tool_result, dict):
            print(f"Tool Result Keys: {list(tool_result.keys())[:20]}")
            
            # 检查是否有 hits/articles/items
            if "hits" in tool_result:
                hits = tool_result["hits"]
                if isinstance(hits, list):
                    print(f"✓ Found 'hits' array with {len(hits)} items")
                    if len(hits) > 0:
                        print(f"  First item keys: {list(hits[0].keys())[:10] if isinstance(hits[0], dict) else 'not dict'}")
                else:
                    print(f"✗ 'hits' exists but is not an array: {type(hits)}")
            
            if "articles" in tool_result:
                articles = tool_result["articles"]
                if isinstance(articles, list):
                    print(f"✓ Found 'articles' array with {len(articles)} items")
                    if len(articles) > 0:
                        print(f"  First item keys: {list(articles[0].keys())[:10] if isinstance(articles[0], dict) else 'not dict'}")
                else:
                    print(f"✗ 'articles' exists but is not an array: {type(articles)}")
            
            if "items" in tool_result:
                items = tool_result["items"]
                if isinstance(items, list):
                    print(f"✓ Found 'items' array with {len(items)} items")
                else:
                    print(f"✗ 'items' exists but is not an array: {type(items)}")
            
            # 检查是否是数组对象
            keys = list(tool_result.keys())
            numeric_keys = [k for k in keys if isinstance(k, (int, str)) and str(k).isdigit()]
            if len(numeric_keys) > 0:
                print(f"⚠ Found {len(numeric_keys)} numeric keys (array-like object)")
                print(f"  First 10 keys: {numeric_keys[:10]}")
        
        elif isinstance(tool_result, list):
            print(f"✓ Tool result is an array with {len(tool_result)} items")
            if len(tool_result) > 0:
                print(f"  First item type: {type(tool_result[0])}")
                if isinstance(tool_result[0], dict):
                    print(f"  First item keys: {list(tool_result[0].keys())[:10]}")
        
        # 检查 content 字段
        content = tool_entry.get("content", "")
        if content:
            print(f"\nContent length: {len(content)} characters")
            if "Tool used:" in content:
                print("✓ Content contains 'Tool used:' prefix")
                # 尝试提取 JSON
                try:
                    result_text = content.split("Tool used:")[-1].split(":", 1)[-1].strip()
                    if result_text.startswith("{") or result_text.startswith("["):
                        parsed = json.loads(result_text)
                        print(f"✓ Successfully parsed JSON from content")
                        if isinstance(parsed, dict):
                            print(f"  Parsed keys: {list(parsed.keys())[:10]}")
                except Exception as e:
                    print(f"✗ Failed to parse JSON from content: {e}")
    
    print(f"\n{'=' * 80}")
    print("测试完成")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    test_news_parsing()

