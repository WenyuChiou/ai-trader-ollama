#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试新闻工具 - 一键测试所有功能
"""
from __future__ import annotations
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.tools.news_tools import news_scan, business_rss
from collections import Counter

def main():
    print("\n" + "=" * 80)
    print("🚀 快速新闻工具测试")
    print("=" * 80)
    print()
    
    # 测试 1: Business RSS
    print("📰 测试 1: Business RSS Feeds")
    print("-" * 80)
    try:
        hits = business_rss(max_items=30)
        sources = Counter([h.get("source", "unknown") for h in hits])
        
        print(f"✅ 成功获取 {len(hits)} 条新闻")
        print(f"📊 来源分布: {len(sources)} 个不同来源")
        print("\n前 5 条新闻:")
        for i, hit in enumerate(hits[:5], 1):
            print(f"  {i}. [{hit.get('source', 'N/A')}] {hit.get('title', 'N/A')[:70]}...")
        print()
    except Exception as e:
        print(f"❌ 错误: {e}\n")
    
    # 测试 2: News Scan
    print("🔍 测试 2: News Scan (关键词: NVDA, stock market)")
    print("-" * 80)
    try:
        result = news_scan(
            keywords=["NVDA", "stock market"],
            max_articles=20,
            recency_days=7
        )
        
        hits = result.get("hits", [])
        sources = Counter([h.get("source", "unknown") for h in hits])
        
        print(f"✅ 成功获取 {len(hits)} 条新闻")
        print(f"📊 来源分布: {len(sources)} 个不同来源")
        print("\n来源统计:")
        for source, count in sources.most_common(5):
            print(f"  - {source}: {count} 条")
        print("\n前 5 条新闻:")
        for i, hit in enumerate(hits[:5], 1):
            print(f"  {i}. [{hit.get('source', 'N/A')}] {hit.get('title', 'N/A')[:70]}...")
        print()
    except Exception as e:
        print(f"❌ 错误: {e}\n")
    
    # 测试 3: 测试特定股票
    print("📈 测试 3: 测试特定股票新闻 (AAPL, MSFT)")
    print("-" * 80)
    try:
        result = news_scan(
            keywords=["AAPL", "MSFT", "earnings"],
            max_articles=15,
            recency_days=7
        )
        
        hits = result.get("hits", [])
        print(f"✅ 成功获取 {len(hits)} 条相关新闻")
        print("\n前 5 条新闻:")
        for i, hit in enumerate(hits[:5], 1):
            print(f"  {i}. [{hit.get('source', 'N/A')}] {hit.get('title', 'N/A')[:70]}...")
        print()
    except Exception as e:
        print(f"❌ 错误: {e}\n")
    
    print("=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print("\n💡 提示:")
    print("  - 如果看到多个不同的新闻来源，说明多元化工作正常")
    print("  - 如果新闻标题与关键词相关，说明搜索功能正常")
    print("  - 如果新闻时间较新，说明实时更新正常")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

