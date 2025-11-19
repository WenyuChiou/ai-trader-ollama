#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证持仓记录一致性脚本
- 检查 portfolio_state.json 和 equity_history.jsonl 的一致性
- 验证持仓数据的正确性
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> backend/
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BACKEND_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.data.portfolio import Portfolio


def load_portfolio_state(portfolio_file: Path) -> Optional[Dict[str, Any]]:
    """加载 portfolio_state.json"""
    if not portfolio_file.exists():
        return None
    
    try:
        with portfolio_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载 portfolio_state.json 失败: {e}")
        return None


def load_latest_equity(equity_file: Path) -> Optional[Dict[str, Any]]:
    """加载 equity_history.jsonl 的最新记录"""
    if not equity_file.exists():
        return None
    
    try:
        with equity_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return None
            # 获取最后一行
            last_line = lines[-1].strip()
            if last_line:
                return json.loads(last_line)
    except Exception as e:
        print(f"❌ 加载 equity_history.jsonl 失败: {e}")
        return None


def compare_positions(portfolio_positions: Dict[str, Any], equity_positions: Dict[str, Any]) -> Dict[str, Any]:
    """比较两个持仓字典"""
    portfolio_symbols = set(portfolio_positions.keys())
    equity_symbols = set(equity_positions.keys())
    
    common = portfolio_symbols & equity_symbols
    only_in_portfolio = portfolio_symbols - equity_symbols
    only_in_equity = equity_symbols - portfolio_symbols
    
    differences = {}
    for symbol in common:
        p_pos = portfolio_positions[symbol]
        e_pos = equity_positions[symbol]
        
        diff = {}
        if p_pos.get("quantity") != e_pos.get("quantity"):
            diff["quantity"] = {
                "portfolio": p_pos.get("quantity"),
                "equity": e_pos.get("quantity")
            }
        if abs(p_pos.get("avg_cost", 0) - e_pos.get("avg_cost", 0)) > 0.01:
            diff["avg_cost"] = {
                "portfolio": p_pos.get("avg_cost"),
                "equity": e_pos.get("avg_cost")
            }
        
        if diff:
            differences[symbol] = diff
    
    return {
        "common": list(common),
        "only_in_portfolio": list(only_in_portfolio),
        "only_in_equity": list(only_in_equity),
        "differences": differences
    }


def verify_portfolio():
    """验证持仓记录"""
    print("\n" + "="*60)
    print("持仓记录验证")
    print("="*60)
    
    # 使用项目根目录的 data/logs
    project_root = ROOT.parent  # backend/ -> project root
    logs_dir = project_root / "data" / "logs"
    portfolio_file = logs_dir / "portfolio_state.json"
    equity_file = logs_dir / "equity_history.jsonl"
    
    # 加载数据
    print("\n1. 加载数据...")
    portfolio_state = load_portfolio_state(portfolio_file)
    if not portfolio_state:
        print("❌ portfolio_state.json 不存在或无法加载")
        return False
    
    equity_record = load_latest_equity(equity_file)
    if not equity_record:
        print("❌ equity_history.jsonl 不存在或无法加载")
        return False
    
    print("✅ 数据加载成功")
    
    # 显示基本信息
    print("\n2. 基本信息:")
    print(f"   portfolio_state.json:")
    print(f"     - 时间戳: {portfolio_state.get('timestamp', 'N/A')}")
    print(f"     - 现金: ${portfolio_state.get('cash', 0):.2f}")
    print(f"     - 总价值: ${portfolio_state.get('total_value', 0):.2f}")
    print(f"     - 持仓数量: {len(portfolio_state.get('positions', {}))}")
    
    print(f"\n   equity_history.jsonl (最新记录):")
    print(f"     - 日期: {equity_record.get('date', 'N/A')}")
    print(f"     - 时间戳: {equity_record.get('timestamp', 'N/A')}")
    print(f"     - 现金: ${equity_record.get('cash', 0):.2f}")
    print(f"     - 总价值: ${equity_record.get('total_value', 0):.2f}")
    print(f"     - 持仓数量: {len(equity_record.get('positions', {}))}")
    
    # 比较持仓
    print("\n3. 持仓比较:")
    portfolio_positions = portfolio_state.get("positions", {})
    equity_positions = equity_record.get("positions", {})
    
    comparison = compare_positions(portfolio_positions, equity_positions)
    
    print(f"   共同持仓: {len(comparison['common'])} 个")
    if comparison['common']:
        print(f"     符号: {', '.join(sorted(comparison['common']))}")
    
    if comparison['only_in_portfolio']:
        print(f"   ⚠️  仅在 portfolio_state.json: {', '.join(comparison['only_in_portfolio'])}")
    
    if comparison['only_in_equity']:
        print(f"   ⚠️  仅在 equity_history.jsonl: {', '.join(comparison['only_in_equity'])}")
    
    if comparison['differences']:
        print(f"   ⚠️  持仓差异:")
        for symbol, diff in comparison['differences'].items():
            print(f"     - {symbol}: {diff}")
    
    # 验证现金一致性
    print("\n4. 现金一致性:")
    cash_diff = abs(portfolio_state.get('cash', 0) - equity_record.get('cash', 0))
    if cash_diff < 0.01:
        print(f"   ✅ 现金一致 (差异: ${cash_diff:.2f})")
    else:
        print(f"   ⚠️  现金不一致 (差异: ${cash_diff:.2f})")
        print(f"     portfolio_state: ${portfolio_state.get('cash', 0):.2f}")
        print(f"     equity_history: ${equity_record.get('cash', 0):.2f}")
    
    # 验证总价值一致性
    print("\n5. 总价值一致性:")
    value_diff = abs(portfolio_state.get('total_value', 0) - equity_record.get('total_value', 0))
    if value_diff < 1.0:
        print(f"   ✅ 总价值一致 (差异: ${value_diff:.2f})")
    else:
        print(f"   ⚠️  总价值不一致 (差异: ${value_diff:.2f})")
        print(f"     portfolio_state: ${portfolio_state.get('total_value', 0):.2f}")
        print(f"     equity_history: ${equity_record.get('total_value', 0):.2f}")
    
    # 总结
    print("\n6. 验证总结:")
    is_consistent = (
        len(comparison['only_in_portfolio']) == 0 and
        len(comparison['only_in_equity']) == 0 and
        len(comparison['differences']) == 0 and
        cash_diff < 0.01 and
        value_diff < 1.0
    )
    
    if is_consistent:
        print("   ✅ 持仓记录一致")
        return True
    else:
        print("   ⚠️  持仓记录存在不一致")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("持仓记录验证脚本")
    print("="*60)
    
    is_consistent = verify_portfolio()
    
    print("\n" + "="*60)
    if is_consistent:
        print("✅ 验证通过")
    else:
        print("⚠️  验证发现问题，请检查上述差异")
    print("="*60)


if __name__ == "__main__":
    main()

