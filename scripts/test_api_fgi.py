#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 FGI API 是否正确使用标准分级
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

def test_fgi_label_function():
    """测试 FGI 分级函数"""
    from src.tools.sentiment_tools import _get_fgi_label
    
    print("=" * 60)
    print("测试 FGI 分级函数 (_get_fgi_label)")
    print("=" * 60)
    
    test_cases = [
        (11, "EXTREME FEAR"),
        (25, "EXTREME FEAR"),
        (26, "FEAR"),
        (45, "FEAR"),
        (46, "NEUTRAL"),
        (55, "NEUTRAL"),
        (56, "GREED"),
        (75, "GREED"),
        (76, "EXTREME GREED"),
        (100, "EXTREME GREED"),
    ]
    
    all_passed = True
    for value, expected in test_cases:
        result = _get_fgi_label(value)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"{status} Value {value:3d} -> {result:20s} (期望: {expected})")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败！")
    print("=" * 60)
    return all_passed

def test_fetch_fear_greed():
    """测试 fetch_fear_greed 函数"""
    from src.tools.sentiment_tools import fetch_fear_greed
    
    print("\n" + "=" * 60)
    print("测试 fetch_fear_greed 函数")
    print("=" * 60)
    
    try:
        result = fetch_fear_greed(timeout=5.0)
        
        if result:
            value = result.get("value")
            label = result.get("label")
            source = result.get("source", "unknown")
            
            print(f"✓ 成功获取 FGI 数据")
            print(f"  Value: {value}")
            print(f"  Label: {label}")
            print(f"  Source: {source}")
            
            # 验证 label 是否符合标准分级
            if value is not None:
                from src.tools.sentiment_tools import _get_fgi_label
                expected_label = _get_fgi_label(value)
                if label == expected_label:
                    print(f"  ✓ Label 符合标准分级: {expected_label}")
                else:
                    print(f"  ✗ Label 不符合标准分级!")
                    print(f"    实际: {label}")
                    print(f"    期望: {expected_label}")
                    return False
        else:
            print("✗ 返回 None")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\n开始测试 FGI API 更新...\n")
    
    test1_passed = test_fgi_label_function()
    test2_passed = test_fetch_fear_greed()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ 所有 API 测试通过！")
        sys.exit(0)
    else:
        print("✗ 部分 API 测试失败！")
        sys.exit(1)

