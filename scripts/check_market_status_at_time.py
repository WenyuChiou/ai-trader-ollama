#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定时间点的市场状态
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import datetime
import pytz

def check_market_status(utc_timestamp_str):
    """检查UTC时间戳对应的市场状态"""
    # 解析UTC时间戳
    utc_time = datetime.fromisoformat(utc_timestamp_str.replace('Z', '+00:00'))
    
    # 转换为美东时间
    et_tz = pytz.timezone('America/New_York')
    et_time = utc_time.astimezone(et_tz)
    
    print("=" * 60)
    print("市场状态检查")
    print("=" * 60)
    print(f"UTC时间: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"星期几: {et_time.strftime('%A')}")
    print(f"是否工作日: {et_time.weekday() < 5}")
    print()
    
    # 检查是否是交易日
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.src.utils.trading_days import is_trading_day, is_market_open
    
    check_date = et_time.date()
    is_trading = is_trading_day(check_date)
    print(f"是否是交易日: {is_trading}")
    
    if not is_trading:
        print(f"原因: ", end="")
        if check_date.weekday() >= 5:
            print("周末")
        else:
            print("节假日")
        print()
    
    # 检查市场是否开放
    market_open = is_market_open(utc_time)
    print(f"市场是否开放: {market_open}")
    print()
    
    # 显示时间范围
    current_time = et_time.time()
    market_open_time = datetime.strptime("09:30", "%H:%M").time()
    market_close_time = datetime.strptime("16:00", "%H:%M").time()
    
    print(f"当前时间: {current_time.strftime('%H:%M:%S')}")
    print(f"市场开放时间: {market_open_time.strftime('%H:%M')}")
    print(f"市场关闭时间: {market_close_time.strftime('%H:%M')}")
    print()
    
    if market_open_time <= current_time < market_close_time:
        print("✅ 时间范围内，市场应该开放")
    else:
        print("❌ 时间范围外，市场应该关闭")
        if current_time < market_open_time:
            print(f"   原因: 尚未开盘（当前 {current_time.strftime('%H:%M')} < 开盘时间 {market_open_time.strftime('%H:%M')}）")
        else:
            print(f"   原因: 已收盘（当前 {current_time.strftime('%H:%M')} >= 收盘时间 {market_close_time.strftime('%H:%M')}）")
    
    print("=" * 60)

if __name__ == "__main__":
    # 默认检查对话记录中的时间
    timestamp = "2025-11-21T14:15:32.749Z"
    
    if len(sys.argv) > 1:
        timestamp = sys.argv[1]
    
    check_market_status(timestamp)

