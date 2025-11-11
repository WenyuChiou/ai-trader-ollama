#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查新闻源的新鲜度 - 确认所有新闻都是最新的
"""
from __future__ import annotations
import sys
import io
import feedparser
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from src.tools.news_tools import BUSINESS_FEEDS

def parse_date(entry):
    """解析新闻日期"""
    # 尝试多种日期格式
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except:
            pass
    
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except:
            pass
    
    # 尝试解析 published 字符串
    if hasattr(entry, 'published'):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(entry.published)
        except:
            pass
    
    return None

def check_feed_recency(url: str, name: str) -> dict:
    """检查单个 RSS Feed 的新鲜度"""
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo or len(feed.entries) == 0:
            return {
                "name": name,
                "status": "❌ Error",
                "latest_date": None,
                "age_hours": None,
                "items": 0
            }
        
        # 检查前 5 条新闻的日期
        dates = []
        for entry in feed.entries[:5]:
            date = parse_date(entry)
            if date:
                dates.append(date)
        
        if not dates:
            return {
                "name": name,
                "status": "⚠️ No dates",
                "latest_date": None,
                "age_hours": None,
                "items": len(feed.entries)
            }
        
        latest_date = max(dates)
        now = datetime.now(timezone.utc)
        age = now - latest_date
        age_hours = age.total_seconds() / 3600
        
        # 判断新鲜度
        if age_hours < 1:
            status = "✅ 最新 (<1小时)"
        elif age_hours < 6:
            status = "✅ 很新 (<6小时)"
        elif age_hours < 24:
            status = "⚠️ 较旧 (<24小时)"
        elif age_hours < 48:
            status = "⚠️ 旧 (<48小时)"
        else:
            status = "❌ 很旧 (>48小时)"
        
        return {
            "name": name,
            "status": status,
            "latest_date": latest_date,
            "age_hours": age_hours,
            "items": len(feed.entries),
            "sample_title": feed.entries[0].title[:60] if feed.entries else None
        }
    except Exception as e:
        return {
            "name": name,
            "status": f"❌ Exception: {e}",
            "latest_date": None,
            "age_hours": None,
            "items": 0
        }

def main():
    print("=" * 80)
    print("检查新闻源新鲜度")
    print("=" * 80)
    print()
    
    results = []
    for url in BUSINESS_FEEDS:
        name = url.split("//")[-1].split("/")[0] if "//" in url else url
        result = check_feed_recency(url, name)
        results.append(result)
        
        # 显示结果
        status = result["status"]
        items = result.get("items", 0)
        age_info = ""
        if result.get("age_hours") is not None:
            age_hours = result["age_hours"]
            if age_hours < 24:
                age_info = f" ({age_hours:.1f} 小时前)"
            else:
                age_info = f" ({age_hours/24:.1f} 天前)"
        
        print(f"{status:<25} {result['name']:<40} {items} 条{age_info}")
        if result.get("sample_title"):
            print(f"  示例: {result['sample_title']}...")
        if result.get("latest_date"):
            print(f"  最新时间: {result['latest_date']}")
        print()
    
    # 统计
    print("=" * 80)
    print("统计结果")
    print("=" * 80)
    
    fresh = [r for r in results if "✅" in r["status"]]
    old = [r for r in results if "⚠️" in r["status"]]
    error = [r for r in results if "❌" in r["status"]]
    
    print(f"总计: {len(results)} 个新闻源")
    print(f"✅ 最新/很新: {len(fresh)}")
    print(f"⚠️  较旧/旧: {len(old)}")
    print(f"❌ 错误/很旧: {len(error)}")
    print()
    
    # 推荐使用的源（最新）
    print("=" * 80)
    print("推荐使用的新闻源（最新）")
    print("=" * 80)
    for r in fresh:
        print(f"✅ {r['name']:<40} {r.get('age_hours', 0):.1f} 小时前")
    
    # 需要检查的源（较旧）
    if old:
        print("\n" + "=" * 80)
        print("需要检查的新闻源（较旧）")
        print("=" * 80)
        for r in old:
            print(f"⚠️  {r['name']:<40} {r.get('age_hours', 0):.1f} 小时前 ({r.get('age_hours', 0)/24:.1f} 天前)")
    
    # 有问题的源
    if error:
        print("\n" + "=" * 80)
        print("有问题的新闻源")
        print("=" * 80)
        for r in error:
            print(f"❌ {r['name']:<40} {r['status']}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

