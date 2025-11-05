#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复现有portfolio_state.json，添加缺失的total_cost字段"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path

def fix_portfolio_total_cost():
    """修复portfolio_state.json，添加total_cost字段"""
    portfolio_file = Path("data/logs/portfolio_state.json")
    
    if not portfolio_file.exists():
        print("❌ portfolio_state.json 不存在")
        return
    
    print("=" * 60)
    print("修复 portfolio_state.json - 添加 total_cost 字段")
    print("=" * 60)
    
    # 读取现有数据
    with portfolio_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    
    positions = state.get("positions", {})
    fixed_count = 0
    
    print(f"\n检查 {len(positions)} 个持仓...")
    
    for symbol, pos_info in positions.items():
        if isinstance(pos_info, dict):
            quantity = pos_info.get("quantity", 0)
            avg_cost = pos_info.get("avg_cost", 0.0)
            total_cost = pos_info.get("total_cost", 0.0)
            
            # 如果total_cost缺失或为0，计算它
            if total_cost <= 0 and quantity > 0 and avg_cost > 0:
                calculated_total_cost = avg_cost * quantity
                pos_info["total_cost"] = calculated_total_cost
                fixed_count += 1
                print(f"  ✓ {symbol}: 添加 total_cost = ${calculated_total_cost:.2f} (avg_cost=${avg_cost:.2f} × quantity={quantity})")
            elif total_cost > 0:
                print(f"  - {symbol}: total_cost 已存在 = ${total_cost:.2f}")
            else:
                print(f"  ⚠ {symbol}: 无法计算 total_cost (quantity={quantity}, avg_cost={avg_cost})")
    
    if fixed_count > 0:
        # 保存修复后的数据
        backup_file = portfolio_file.with_suffix('.json.bak')
        try:
            # 创建备份
            import shutil
            shutil.copy2(portfolio_file, backup_file)
            print(f"\n✓ 已创建备份: {backup_file}")
        except Exception as e:
            print(f"\n⚠ 创建备份失败: {e}")
        
        # 保存修复后的数据
        try:
            with portfolio_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
                f.flush()
                import os
                os.fsync(f.fileno())
            print(f"✓ 已修复并保存: {portfolio_file}")
        except Exception as e:
            print(f"✗ 保存失败: {e}")
            return
    
    print("\n" + "=" * 60)
    if fixed_count > 0:
        print(f"✅ 修复完成！共修复 {fixed_count} 个持仓")
    else:
        print("ℹ️  所有持仓的 total_cost 字段都已存在")
    print("=" * 60)

if __name__ == "__main__":
    fix_portfolio_total_cost()

