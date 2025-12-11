#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logs_dir = Path("data/logs")
portfolio_file = logs_dir / "portfolio_state.json"

print("=" * 80)
print("检查持仓限制")
print("=" * 80)
print()

if portfolio_file.exists():
    portfolio = json.load(open(portfolio_file, encoding="utf-8"))
    positions = portfolio.get("positions", {})
    cash = portfolio.get("cash", 0)
    
    print(f"当前持仓数: {len(positions)}")
    print(f"现金: ${cash:.2f}")
    print()
    print("持仓列表:")
    for sym, info in positions.items():
        qty = info.get("quantity", 0) if isinstance(info, dict) else info
        print(f"  {sym}: {qty} shares")
    
    print()
    print("检查 XEL:")
    if "XEL" in positions:
        print(f"  ✓ XEL 已在持仓中")
    else:
        print(f"  ✗ XEL 不在持仓中")
    
    print()
    print("检查持仓限制:")
    MAX_POSITIONS = 10  # 默认值
    current_count = len(positions)
    print(f"  当前持仓数: {current_count}")
    print(f"  最大持仓数: {MAX_POSITIONS}")
    
    if current_count >= MAX_POSITIONS:
        print(f"  ⚠️  已达到最大持仓数！")
        if "XEL" not in positions:
            print(f"  ❌ 根本原因: XEL 不在持仓中，且已达到最大持仓数 ({current_count}/{MAX_POSITIONS})")
            print(f"  ❌ 订单被跳过: BUY XEL skipped: max positions reached")
        else:
            print(f"  ✓ XEL 已在持仓中，应该可以加仓")
    else:
        print(f"  ✓ 未达到最大持仓数，可以买入 XEL")
else:
    print("portfolio_state.json 不存在")

print()
print("=" * 80)





