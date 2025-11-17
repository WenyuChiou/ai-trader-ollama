#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试市场状态判断
"""
import sys
import io
from datetime import datetime

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend到路径
from pathlib import Path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    import pytz
    from src.utils.trading_days import is_market_open
    
    # 获取美东时间
    et_tz = pytz.timezone('America/New_York')
    now_et = datetime.now(et_tz)
    
    # 检查市场状态
    now = datetime.now()
    market_open = is_market_open(now)
    
    print("=" * 60)
    print("市场状态检查")
    print("=" * 60)
    print(f"本地时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"美东时间: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"当前ET时间: {now_et.time().strftime('%H:%M:%S')}")
    print(f"市场时间: 9:30 AM - 4:00 PM ET")
    print(f"市场状态: {'开放' if market_open else '关闭'}")
    print("=" * 60)
    
    # 验证：如果美东时间是19:22，市场应该是关闭的
    if now_et.hour >= 16 or now_et.hour < 9 or (now_et.hour == 9 and now_et.minute < 30):
        expected = False
        if market_open == expected:
            print("✅ 市场状态判断正确（市场已关闭）")
        else:
            print(f"❌ 市场状态判断错误（应该是关闭，但返回了开放）")
    else:
        expected = True
        if market_open == expected:
            print("✅ 市场状态判断正确（市场开放）")
        else:
            print(f"❌ 市场状态判断错误（应该是开放，但返回了关闭）")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

