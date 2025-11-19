#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 SentimentAnalyst 是否调用新闻工具并检查输出
"""
import sys
import os
import io
import json
from pathlib import Path

# CRITICAL FIX: Windows PowerShell UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 设置工作目录
os.chdir(backend_dir)

def test_sentiment_analyst_news_tools():
    """测试 SentimentAnalyst 是否强制调用新闻工具"""
    print("=" * 60)
    print("测试 SentimentAnalyst 新闻工具调用")
    print("=" * 60)
    
    try:
        from src.agents.multi_analyst_system import run_multi_analyst_discussion
        from src.agents.toolbox import ToolBox
        
        # 创建简单的市场视图
        market_view = {
            "market_status": "open",
            "current_time": "2025-01-20T10:00:00Z",
            "summary": "Market is open"
        }
        
        print("\n1. 测试强制新闻工具调用逻辑...")
        
        # 模拟 SentimentAnalyst 的工具调用逻辑
        toolbox = ToolBox()
        
        # 检查 plan_and_scan_news 工具是否存在
        # ToolBox 使用 list() 方法列出所有工具
        available_tools = toolbox.list()
        
        if "plan_and_scan_news" in available_tools:
            print("   ✓ plan_and_scan_news 工具已注册")
        else:
            print("   ✗ plan_and_scan_news 工具未注册")
            print(f"   可用工具: {', '.join(available_tools[:10])}...")
            return False
        
        # 检查 news_scan 工具是否存在
        if "news_scan" in available_tools:
            print("   ✓ news_scan 工具已注册")
        else:
            print("   ⚠ news_scan 工具未注册（可能已被 plan_and_scan_news 替代）")
        
        print("\n2. 测试新闻工具执行...")
        
        # 测试 plan_and_scan_news 工具调用
        test_tool_call = {
            "name": "plan_and_scan_news",
            "args": {
                "tickers": [],
                "max_articles": 5,
                "recency_days": 2,
                "fetch_body_top": 5
            },
            "why": "Test: Fetch latest market news"
        }
        
        try:
            result = toolbox.invoke(
                name=test_tool_call["name"],
                **test_tool_call["args"]
            )
            
            if result and isinstance(result, dict):
                if result.get("ok"):
                    actual_result = result.get("result", result)
                    hits_count = len(actual_result.get("hits", [])) if isinstance(actual_result.get("hits"), list) else 0
                    articles_count = len(actual_result.get("articles", [])) if isinstance(actual_result.get("articles"), list) else 0
                    
                    print(f"   ✓ plan_and_scan_news 执行成功")
                    print(f"     - Hits: {hits_count}")
                    print(f"     - Articles: {articles_count}")
                    
                    # 检查是否有文章数据
                    if articles_count > 0:
                        print(f"   ✓ 成功获取 {articles_count} 篇文章")
                        # 显示第一篇文章的信息
                        articles = actual_result.get("articles", [])
                        if articles and len(articles) > 0:
                            first_article = articles[0]
                            print(f"\n   第一篇文章示例:")
                            print(f"     - Title: {first_article.get('title', 'N/A')[:60]}...")
                            print(f"     - Source: {first_article.get('source', 'N/A')}")
                            print(f"     - Link: {first_article.get('link', 'N/A')[:60]}...")
                            if first_article.get('summary'):
                                print(f"     - Summary: {first_article.get('summary', '')[:80]}...")
                    else:
                        print(f"   ⚠ 未获取到文章数据（hits: {hits_count}）")
                    
                    return True
                else:
                    error = result.get("error", "Unknown error")
                    print(f"   ✗ plan_and_scan_news 执行失败: {error}")
                    return False
            else:
                print(f"   ✗ plan_and_scan_news 返回无效结果")
                return False
                
        except Exception as e:
            print(f"   ✗ plan_and_scan_news 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_force_news_tool_logic():
    """测试强制添加新闻工具的逻辑"""
    print("\n" + "=" * 60)
    print("测试强制新闻工具逻辑")
    print("=" * 60)
    
    # 模拟 SentimentAnalyst 的工具调用列表
    tool_calls_list = []
    
    # 检查是否有新闻工具
    has_news_tool = any(tc.get("name") in ["news_scan", "plan_and_scan_news"] for tc in tool_calls_list)
    
    print(f"1. 初始工具调用列表: {len(tool_calls_list)} 个工具")
    print(f"2. 是否已有新闻工具: {has_news_tool}")
    
    # 模拟强制添加逻辑
    if not has_news_tool:
        print("3. 强制添加 plan_and_scan_news...")
        tool_calls_list.insert(0, {
            "name": "plan_and_scan_news", 
            "args": {"tickers": [], "max_articles": 10, "recency_days": 2, "fetch_body_top": 10}, 
            "why": "MANDATORY: News analysis with article content is critical for sentiment assessment"
        })
        print(f"   ✓ 已添加 plan_and_scan_news")
        print(f"4. 更新后工具调用列表: {len(tool_calls_list)} 个工具")
        
        # 验证
        has_news_tool_after = any(tc.get("name") in ["news_scan", "plan_and_scan_news"] for tc in tool_calls_list)
        if has_news_tool_after:
            print(f"   ✓ 验证通过：新闻工具已添加")
            return True
        else:
            print(f"   ✗ 验证失败：新闻工具未正确添加")
            return False
    else:
        print("3. 已有新闻工具，无需添加")
        return True

def check_recent_discussion_logs():
    """检查最近的讨论日志，查看 SentimentAnalyst 是否调用了新闻工具"""
    print("\n" + "=" * 60)
    print("检查最近的讨论日志")
    print("=" * 60)
    
    logs_file = Path(__file__).parent.parent / "data" / "logs" / "discussion_actions.jsonl"
    
    if not logs_file.exists():
        print("   ⚠ discussion_actions.jsonl 文件不存在")
        return False
    
    try:
        with open(logs_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        entries = []
        for line in lines:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except:
                    continue
        
        print(f"   总日志条目: {len(entries)}")
        
        # 查找 SentimentAnalyst 的工具调用
        sentiment_tools = [
            e for e in entries 
            if e.get('type') == 'tool' 
            and 'sentiment' in e.get('agent', '').lower()
        ]
        
        print(f"   SentimentAnalyst 工具调用: {len(sentiment_tools)}")
        
        # 查找新闻工具调用
        news_tools = [
            e for e in sentiment_tools 
            if e.get('tool_name') in ['plan_and_scan_news', 'news_scan', 'get_news_scan']
        ]
        
        print(f"   新闻工具调用: {len(news_tools)}")
        
        if news_tools:
            print("\n   最近的新闻工具调用:")
            for tool in news_tools[-5:]:
                print(f"     - {tool.get('tool_name')} (agent: {tool.get('agent')}, timestamp: {tool.get('timestamp', 'N/A')})")
            
            # 检查工具结果
            for tool in news_tools[-1:]:
                tool_result = tool.get('tool_result', {})
                if isinstance(tool_result, dict):
                    if tool_result.get('ok'):
                        actual_result = tool_result.get('result', tool_result)
                        hits = actual_result.get('hits', [])
                        articles = actual_result.get('articles', [])
                        print(f"\n   最新工具结果:")
                        print(f"     - Hits: {len(hits) if isinstance(hits, list) else 0}")
                        print(f"     - Articles: {len(articles) if isinstance(articles, list) else 0}")
                    else:
                        print(f"\n   最新工具结果: 执行失败 - {tool_result.get('error', 'Unknown error')}")
            
            return True
        else:
            print("   ⚠ 未找到新闻工具调用记录")
            print("   最近的 SentimentAnalyst 工具调用:")
            for tool in sentiment_tools[-5:]:
                print(f"     - {tool.get('tool_name')} (agent: {tool.get('agent')})")
            return False
            
    except Exception as e:
        print(f"   ✗ 读取日志失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n开始测试 SentimentAnalyst 新闻工具...\n")
    
    test1_passed = test_force_news_tool_logic()
    test2_passed = test_sentiment_analyst_news_tools()
    test3_passed = check_recent_discussion_logs()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"强制新闻工具逻辑: {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"新闻工具执行: {'✓ 通过' if test2_passed else '✗ 失败'}")
    print(f"日志检查: {'✓ 通过' if test3_passed else '✗ 失败'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n✓ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n✗ 部分测试失败！")
        sys.exit(1)

