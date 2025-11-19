#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试两个新闻工具的实际可用性
"""
import sys
import os
import io
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

def test_news_scan():
    """测试 news_scan 工具"""
    print("=" * 60)
    print("测试 news_scan 工具")
    print("=" * 60)
    
    try:
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        
        # 测试 news_scan
        print("\n1. 调用 news_scan...")
        result = toolbox.invoke(
            name="news_scan",
            keywords=["stock market", "AI"],
            max_articles=3,
            recency_days=2
        )
        
        if result and isinstance(result, dict):
            if result.get("ok"):
                actual_result = result.get("result", result)
                hits = actual_result.get("hits", [])
                hits_count = len(hits) if isinstance(hits, list) else 0
                
                print(f"   ✓ news_scan 执行成功")
                print(f"     - Hits: {hits_count}")
                
                if hits_count > 0:
                    print(f"   ✓ 成功获取 {hits_count} 个新闻条目")
                    # 显示第一个条目
                    if hits and len(hits) > 0:
                        first_hit = hits[0]
                        print(f"\n   第一个新闻条目:")
                        print(f"     - Title: {first_hit.get('title', 'N/A')[:60]}...")
                        print(f"     - Source: {first_hit.get('source', 'N/A')}")
                        print(f"     - Link: {first_hit.get('link', 'N/A')[:60]}...")
                    
                    # 检查是否有 articles 字段
                    articles = actual_result.get("articles", [])
                    if articles:
                        print(f"     - Articles: {len(articles)} (包含文章内容)")
                    else:
                        print(f"     - Articles: 0 (仅标题和链接，无文章内容)")
                    
                    return True
                else:
                    print(f"   ⚠ 未获取到新闻数据")
                    return False
            else:
                error = result.get("error", "Unknown error")
                print(f"   ✗ news_scan 执行失败: {error}")
                return False
        else:
            print(f"   ✗ news_scan 返回无效结果")
            return False
            
    except Exception as e:
        print(f"   ✗ news_scan 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plan_and_scan_news():
    """测试 plan_and_scan_news 工具"""
    print("\n" + "=" * 60)
    print("测试 plan_and_scan_news 工具")
    print("=" * 60)
    
    try:
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        
        # 测试 plan_and_scan_news
        print("\n1. 调用 plan_and_scan_news...")
        result = toolbox.invoke(
            name="plan_and_scan_news",
            tickers=[],
            max_articles=3,
            recency_days=2,
            fetch_body_top=3
        )
        
        if result and isinstance(result, dict):
            if result.get("ok"):
                actual_result = result.get("result", result)
                hits = actual_result.get("hits", [])
                articles = actual_result.get("articles", [])
                hits_count = len(hits) if isinstance(hits, list) else 0
                articles_count = len(articles) if isinstance(articles, list) else 0
                
                print(f"   ✓ plan_and_scan_news 执行成功")
                print(f"     - Hits: {hits_count}")
                print(f"     - Articles: {articles_count}")
                
                if articles_count > 0:
                    print(f"   ✓ 成功获取 {articles_count} 篇文章（包含内容）")
                    # 显示第一篇文章
                    if articles and len(articles) > 0:
                        first_article = articles[0]
                        print(f"\n   第一篇文章:")
                        print(f"     - Title: {first_article.get('title', 'N/A')[:60]}...")
                        print(f"     - Source: {first_article.get('source', 'N/A')}")
                        print(f"     - Link: {first_article.get('link', 'N/A')[:60]}...")
                        if first_article.get('summary'):
                            print(f"     - Summary: {first_article.get('summary', '')[:80]}...")
                        if first_article.get('keywords'):
                            print(f"     - Keywords: {first_article.get('keywords', [])}")
                    
                    return True
                elif hits_count > 0:
                    print(f"   ⚠ 获取到 {hits_count} 个新闻条目，但无文章内容")
                    return False
                else:
                    print(f"   ⚠ 未获取到新闻数据")
                    return False
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

if __name__ == "__main__":
    print("\n开始测试两个新闻工具的实际可用性...\n")
    
    test1_passed = test_news_scan()
    test2_passed = test_plan_and_scan_news()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"news_scan: {'✓ 可用' if test1_passed else '✗ 不可用'}")
    print(f"plan_and_scan_news: {'✓ 可用' if test2_passed else '✗ 不可用'}")
    
    print("\n" + "=" * 60)
    print("推荐使用")
    print("=" * 60)
    if test2_passed:
        print("✓ plan_and_scan_news - 推荐使用")
        print("  原因:")
        print("  - 包含文章内容和摘要（LLM 生成）")
        print("  - 包含关键字提取")
        print("  - 功能更完整")
    elif test1_passed:
        print("✓ news_scan - 可用但功能有限")
        print("  原因:")
        print("  - 仅返回标题和链接")
        print("  - 无文章内容和摘要")
    else:
        print("✗ 两个工具都不可用，需要检查配置")
    
    if test1_passed or test2_passed:
        print("\n✓ 至少有一个工具可用")
        sys.exit(0)
    else:
        print("\n✗ 两个工具都不可用")
        sys.exit(1)

