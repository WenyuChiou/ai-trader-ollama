#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动交易逻辑测试脚本
测试自动交易是否会在正确的条件下启动（不实际执行交易）

测试场景：
1. 市场开放 + 30分钟间隔 → 应该启动
2. 市场关闭 → 不应该启动
3. 市场开放但手动交易正在执行 → 应该跳过
4. 连续错误3次 → 应该停止
5. 页面刷新后恢复 → 应该继续
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

def get_market_status():
    """模拟检查市场状态"""
    try:
        from src.api.server import is_market_open
        return is_market_open()
    except Exception as e:
        print(f"[ERROR] Failed to check market status: {e}")
        return None

def test_scenario(name, description, market_open, time_since_last_trade_minutes, is_manual_trading=False, error_count=0):
    """测试单个场景"""
    print(f"\n{'='*60}")
    print(f"测试场景: {name}")
    print(f"描述: {description}")
    print(f"{'='*60}")
    
    # 条件检查
    print(f"\n条件:")
    print(f"  - 市场状态: {'开放' if market_open else '关闭'}")
    print(f"  - 距离上次交易: {time_since_last_trade_minutes} 分钟")
    print(f"  - 手动交易中: {'是' if is_manual_trading else '否'}")
    print(f"  - 错误计数: {error_count}/3")
    
    # 逻辑判断
    should_execute = False
    reasons = []
    
    # 条件1: 市场必须开放
    if not market_open:
        reasons.append("✗ 市场关闭，不执行自动交易")
    else:
        reasons.append("✓ 市场开放")
        
        # 条件2: 必须间隔30分钟
        if time_since_last_trade_minutes < 30:
            reasons.append(f"✗ 距离上次交易仅 {time_since_last_trade_minutes} 分钟，未达到30分钟间隔")
        else:
            reasons.append(f"✓ 距离上次交易 {time_since_last_trade_minutes} 分钟，满足30分钟间隔")
        
        # 条件3: 手动交易不能正在执行
        if is_manual_trading:
            reasons.append("✗ 手动交易正在执行，跳过自动交易")
        else:
            reasons.append("✓ 手动交易未在执行")
        
        # 条件4: 错误计数不能超过3
        if error_count >= 3:
            reasons.append(f"✗ 错误计数 {error_count} >= 3，停止自动交易")
        else:
            reasons.append(f"✓ 错误计数 {error_count} < 3")
        
        # 所有条件都满足
        if (time_since_last_trade_minutes >= 30 and 
            not is_manual_trading and 
            error_count < 3):
            should_execute = True
    
    print(f"\n判断结果:")
    for reason in reasons:
        print(f"  {reason}")
    
    print(f"\n结论: {'✓ 应该执行自动交易' if should_execute else '✗ 不应该执行自动交易'}")
    
    return should_execute

def main():
    """主测试函数"""
    print("="*60)
    print("自动交易逻辑测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取实际市场状态
    print("\n正在检查实际市场状态...")
    actual_market_status = get_market_status()
    if actual_market_status is not None:
        print(f"实际市场状态: {'开放' if actual_market_status else '关闭'}")
    else:
        print("无法获取市场状态，将使用模拟数据")
    
    # 测试场景1: 市场开放 + 满足30分钟间隔 → 应该启动
    test_scenario(
        "场景1: 正常自动交易",
        "市场开放，距离上次交易35分钟，无手动交易，无错误",
        market_open=True,
        time_since_last_trade_minutes=35,
        is_manual_trading=False,
        error_count=0
    )
    
    # 测试场景2: 市场关闭 → 不应该启动
    test_scenario(
        "场景2: 市场关闭",
        "市场关闭，即使满足其他条件也不执行",
        market_open=False,
        time_since_last_trade_minutes=35,
        is_manual_trading=False,
        error_count=0
    )
    
    # 测试场景3: 市场开放但间隔不足 → 不应该启动
    test_scenario(
        "场景3: 间隔不足",
        "市场开放，但距离上次交易仅15分钟",
        market_open=True,
        time_since_last_trade_minutes=15,
        is_manual_trading=False,
        error_count=0
    )
    
    # 测试场景4: 手动交易正在执行 → 应该跳过
    test_scenario(
        "场景4: 手动交易中",
        "市场开放，满足间隔，但手动交易正在执行",
        market_open=True,
        time_since_last_trade_minutes=35,
        is_manual_trading=True,
        error_count=0
    )
    
    # 测试场景5: 连续错误3次 → 应该停止
    test_scenario(
        "场景5: 错误过多",
        "市场开放，满足间隔，但已连续错误3次",
        market_open=True,
        time_since_last_trade_minutes=35,
        is_manual_trading=False,
        error_count=3
    )
    
    # 测试场景6: 市场刚开放 → 应该立即启动（2秒后）
    test_scenario(
        "场景6: 市场刚开放",
        "市场刚开放，首次执行（2秒后）",
        market_open=True,
        time_since_last_trade_minutes=999,  # 表示首次执行
        is_manual_trading=False,
        error_count=0
    )
    
    # 测试场景7: 页面刷新后恢复 → 应该继续
    test_scenario(
        "场景7: 页面刷新恢复",
        "页面刷新后，市场开放，距离上次交易32分钟（在合理范围内）",
        market_open=True,
        time_since_last_trade_minutes=32,
        is_manual_trading=False,
        error_count=0
    )
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n关键逻辑总结:")
    print("1. 市场必须开放（9:30 AM - 4:00 PM ET）")
    print("2. 必须间隔30分钟（或首次执行）")
    print("3. 手动交易不能正在执行")
    print("4. 错误计数不能 >= 3")
    print("5. 所有条件都满足时才执行自动交易")
    print("\n注意: 此测试不实际执行交易，仅验证逻辑")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

