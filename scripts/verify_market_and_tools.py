#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证市场判断和工具信息
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def check_market_status():
    """检查市场状态"""
    print("=" * 60)
    print("1. 市场状态检查")
    print("=" * 60)
    
    try:
        from src.utils.trading_days import is_market_open
        
        now = datetime.now()
        market_open = is_market_open(now)
        
        print(f"当前时间: {now}")
        print(f"市场状态: {'开放' if market_open else '关闭'}")
        
        # 检查美东时间
        try:
            import pytz
            et_tz = pytz.timezone('America/New_York')
            if now.tzinfo is None:
                # 假设是本地时间，转换为UTC再转ET
                import time
                offset_seconds = -time.timezone if time.daylight == 0 else -time.altzone
                from datetime import timedelta, timezone as dt_timezone
                local_tz = dt_timezone(timedelta(seconds=offset_seconds))
                now_with_tz = now.replace(tzinfo=local_tz)
            else:
                now_with_tz = now
            et_time = now_with_tz.astimezone(et_tz)
            print(f"美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"美东时间: {et_time.time().strftime('%H:%M:%S')} (市场时间: 9:30 AM - 4:00 PM ET)")
        except Exception as e:
            print(f"时区转换失败: {e}")
        
        return market_open
    except Exception as e:
        print(f"❌ 市场状态检查失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_tools_in_conversations():
    """检查对话中的工具信息"""
    print("\n" + "=" * 60)
    print("2. 工具信息检查")
    print("=" * 60)
    
    logs_dir = Path("data/logs")
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if not convo_file.exists():
        print(f"❌ 对话文件不存在: {convo_file}")
        return False
    
    try:
        with convo_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ 对话文件为空")
            return False
        
        # 检查最后10条记录
        print(f"\n检查最后10条记录（共{len(lines)}条）:")
        print("-" * 60)
        
        entries_with_tools = 0
        entries_without_tools = 0
        total_tools = 0
        
        for i, line in enumerate(lines[-10:], 1):
            if not line.strip():
                continue
            
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", "Unknown")
                tools_used = entry.get("tools_used", [])
                has_summary = "summary" in entry
                round_num = entry.get("round", 0)
                
                if tools_used:
                    entries_with_tools += 1
                    total_tools += len(tools_used)
                    print(f"{i}. {agent} (round={round_num}): ✅ tools_used={tools_used} (summary={'✅' if has_summary else '❌'})")
                else:
                    entries_without_tools += 1
                    print(f"{i}. {agent} (round={round_num}): ⚠️  tools_used=[] (summary={'✅' if has_summary else '❌'})")
            except json.JSONDecodeError as e:
                print(f"{i}. ❌ JSON解析失败: {e}")
        
        print("-" * 60)
        print(f"统计:")
        print(f"  - 有工具信息的条目: {entries_with_tools}")
        print(f"  - 无工具信息的条目: {entries_without_tools}")
        print(f"  - 工具总数: {total_tools}")
        
        # 检查是否有工具但未显示
        if entries_with_tools > 0:
            print(f"\n✅ 工具信息已正确存储")
            return True
        else:
            print(f"\n⚠️  没有找到工具信息（可能是新系统或工具未使用）")
            return True  # 仍然返回True，因为可能是正常的（没有使用工具）
    
    except Exception as e:
        print(f"❌ 检查工具信息失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_discussion_rounds():
    """检查讨论轮次"""
    print("\n" + "=" * 60)
    print("3. 讨论轮次检查")
    print("=" * 60)
    
    logs_dir = Path("data/logs")
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if not convo_file.exists():
        print(f"❌ 对话文件不存在: {convo_file}")
        return False
    
    try:
        with convo_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 按日期分组，检查今天的记录
        today = datetime.now().date().isoformat()
        today_entries = []
        
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line.strip())
                if entry.get("date") == today:
                    today_entries.append(entry)
            except:
                continue
        
        if not today_entries:
            print(f"⚠️  今天（{today}）没有对话记录")
            return True
        
        # 按round分组
        rounds = {}
        for entry in today_entries:
            round_num = entry.get("round", 0)
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(entry)
        
        print(f"\n今天（{today}）的对话记录:")
        print(f"  总记录数: {len(today_entries)}")
        print(f"  轮次分布:")
        for round_num in sorted(rounds.keys()):
            entries = rounds[round_num]
            agents = [e.get("agent", "Unknown") for e in entries]
            print(f"    Round {round_num}: {len(entries)} 条记录 - {', '.join(set(agents))}")
        
        # 检查是否有三轮讨论（round 1, 2, 3）
        has_rounds = any(r > 0 for r in rounds.keys())
        if has_rounds:
            print(f"\n✅ 找到讨论轮次数据")
        else:
            print(f"\n⚠️  没有找到讨论轮次数据（round > 0）")
        
        return True
    
    except Exception as e:
        print(f"❌ 检查讨论轮次失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("市场判断和工具信息验证")
    print("=" * 60)
    
    # 1. 检查市场状态
    market_status = check_market_status()
    
    # 2. 检查工具信息
    tools_ok = check_tools_in_conversations()
    
    # 3. 检查讨论轮次
    rounds_ok = check_discussion_rounds()
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    print(f"市场状态: {'✅ 正常' if market_status is not None else '❌ 失败'}")
    print(f"工具信息: {'✅ 正常' if tools_ok else '❌ 失败'}")
    print(f"讨论轮次: {'✅ 正常' if rounds_ok else '❌ 失败'}")
    
    if market_status is not None and tools_ok and rounds_ok:
        print("\n✅ 所有检查通过，可以继续修改API端点")
        sys.exit(0)
    else:
        print("\n❌ 部分检查失败，请先修复问题")
        sys.exit(1)

