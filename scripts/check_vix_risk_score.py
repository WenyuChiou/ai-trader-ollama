#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 VIX 风险评分的实际值
"""

import sys
import os
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add backend to path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src.parent))

def main():
    print("="*60)
    print("VIX 风险评分检查")
    print("="*60)
    
    try:
        # Change to backend directory to import modules
        os.chdir(backend_src.parent)
        from src.tools.sentiment_tools import vix_term_structure, vix_risk_score
        
        print("\n正在获取 VIX 数据...")
        vix_data = vix_term_structure()
        
        print(f"\nVIX 数据:")
        print(f"  - VIX: {vix_data.get('vix')}")
        print(f"  - VIX3M: {vix_data.get('vix3m')}")
        print(f"  - Ratio: {vix_data.get('ratio')}")
        print(f"  - Source: {vix_data.get('source')}")
        print(f"  - As of: {vix_data.get('asof')}")
        
        print(f"\n计算风险评分...")
        risk_score = vix_risk_score(vix_data)
        
        print(f"\n结果:")
        print(f"  - VIX 指数: {vix_data.get('vix')}")
        print(f"  - 风险评分: {risk_score}")
        
        # 解释评分
        vix_val = vix_data.get('vix')
        if vix_val is None:
            print(f"\n说明: VIX 数据为空，返回默认值 4.0")
        else:
            try:
                vix_val = float(vix_val)
                if vix_val < 13:
                    level = "低风险"
                elif vix_val < 18:
                    level = "正常风险"
                elif vix_val < 24:
                    level = "中等风险"
                elif vix_val < 30:
                    level = "高风险"
                else:
                    level = "极高风险"
                
                print(f"\n评分规则:")
                print(f"  - VIX < 13: 2.0 (低风险)")
                print(f"  - 13 <= VIX < 18: 4.0 (正常风险)")
                print(f"  - 18 <= VIX < 24: 6.0 (中等风险)")
                print(f"  - 24 <= VIX < 30: 7.5 (高风险)")
                print(f"  - VIX >= 30: 9.0 (极高风险)")
                print(f"\n当前 VIX = {vix_val:.2f} → 风险等级: {level}")
                print(f"预期评分: {risk_score}")
                
                if vix_val >= 18 and vix_val < 24 and risk_score == 4.0:
                    print(f"\n⚠️  警告: VIX = {vix_val:.2f} 应该在 18-24 范围内，应该返回 6.0，但实际返回 {risk_score}")
                    print(f"可能原因:")
                    print(f"  1. VIX 数据获取失败，返回了默认值")
                    print(f"  2. 数据格式问题，无法解析 VIX 值")
                    print(f"  3. API 错误，返回了错误处理中的默认值")
            except (ValueError, TypeError):
                print(f"\n⚠️  警告: 无法解析 VIX 值 '{vix_val}'，返回默认值 4.0")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n[ERROR] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

