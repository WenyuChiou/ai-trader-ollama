#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查当前市场状态
"""
import sys
import io
from datetime import datetime
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend到路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import pytz
    from src.utils.trading_days import is_market_open, is_trading_day
    
    # 直接获取美东时间（最可靠的方法，自动处理夏令时）
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz)
    
    # 获取本地时间用于显示
    now = datetime.now()
    
    # 检查市场状态（传入None让函数直接获取美东时间）
    market_open = is_market_open(None)
    is_trading = is_trading_day(et_time.date())
    
    print("=" * 60)
    print("当前市场状态检查")
    print("=" * 60)
    print(f"本地时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"当前ET时间: {et_time.time().strftime('%H:%M:%S')}")
    print(f"市场时间: 9:30 AM - 4:00 PM ET")
    print(f"")
    print(f"是否交易日: {'是' if is_trading else '否'}")
    print(f"市场状态: {'开放' if market_open else '关闭'}")
    print("=" * 60)
    
    # 详细分析
    if not is_trading:
        print("\n原因: 今天不是交易日（可能是周末或节假日）")
    elif et_time.time() < datetime.strptime("09:30", "%H:%M").time():
        print(f"\n原因: 市场尚未开盘（当前ET时间 {et_time.time().strftime('%H:%M:%S')} < 9:30 AM ET）")
    elif et_time.time() >= datetime.strptime("16:00", "%H:%M").time():
        print(f"\n原因: 市场已收盘（当前ET时间 {et_time.time().strftime('%H:%M:%S')} >= 4:00 PM ET）")
    else:
        print(f"\n✅ 市场应该开放（当前ET时间 {et_time.time().strftime('%H:%M:%S')} 在 9:30 AM - 4:00 PM ET 之间）")
        if not market_open:
            print("⚠️  但系统判断为关闭，可能存在时区转换问题！")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

