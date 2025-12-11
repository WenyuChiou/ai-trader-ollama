#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算预期的 Risk Score
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

print("=" * 80)
print("计算预期的 Risk Score")
print("=" * 80)
print()

try:
    from tools.sentiment_tools import vix_term_structure, vix_risk_score
    
    vix_data = vix_term_structure()
    vix_level = vix_data.get("vix") if vix_data else None
    vix_risk = vix_risk_score(vix_data) if vix_data else None
    
    print(f"当前 VIX Level: {vix_level}")
    print(f"当前 VIX Risk Score: {vix_risk}")
    print()
    
    print("根据 VIX Risk Score 计算规则:")
    print("  VIX < 13: risk_score = 2.0")
    print("  VIX < 18: risk_score = 4.0")
    print("  VIX < 24: risk_score = 6.0")
    print("  VIX < 30: risk_score = 7.5")
    print("  VIX >= 30: risk_score = 9.0")
    print()
    
    if vix_risk:
        print(f"当前 VIX Risk Score = {vix_risk}")
        
        if vix_risk >= 6.0:
            min_risk_score = max(5.0, vix_risk - 1.0)
            print(f"  -> Overall Risk Score 应该至少是 {min_risk_score:.1f} (max(5.0, {vix_risk:.1f} - 1.0))")
            print(f"  -> Stance 应该至少是 MEDIUM")
        elif vix_risk >= 4.0:
            min_risk_score = max(3.5, vix_risk - 0.5)
            print(f"  -> Overall Risk Score 应该至少是 {min_risk_score:.1f} (max(3.5, {vix_risk:.1f} - 0.5))")
            print(f"  -> Stance 可以是 MEDIUM")
        else:
            print(f"  -> Overall Risk Score 可以是 LOW")
        
        print()
        print("实际 Risk Score: 2.91")
        
        if vix_risk >= 6.0:
            expected_min = max(5.0, vix_risk - 1.0)
            diff = expected_min - 2.91
            print(f"预期最小值: {expected_min:.1f}")
            print(f"差异: {diff:.2f} (应该至少是 {expected_min:.1f})")
            print(f"结论: 实际值 2.91 低于预期最小值 {expected_min:.1f}，修复未生效")
        elif vix_risk >= 4.0:
            expected_min = max(3.5, vix_risk - 0.5)
            diff = expected_min - 2.91
            print(f"预期最小值: {expected_min:.1f}")
            print(f"差异: {diff:.2f} (应该至少是 {expected_min:.1f})")
            print(f"结论: 实际值 2.91 低于预期最小值 {expected_min:.1f}，修复未生效")
        else:
            print("结论: VIX Risk Score 较低，实际值可能正常")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)



