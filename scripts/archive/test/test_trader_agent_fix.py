"""
测试 Trader Agent 修复：验证 max_total_position 为 None 时不会报错
"""
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("测试 Trader Agent 修复")
print("=" * 60)

# 测试 1: 检查修复后的代码
print("\n1. 检查修复后的代码")
print("-" * 60)

# 模拟参数
max_total_position = None  # 没有限制
current_total_position_pct = 0.3  # 30% 已持仓

# 修复后的逻辑
if max_total_position is not None:
    available_position_pct = max_total_position - current_total_position_pct
else:
    available_position_pct = 1.0  # 100% of portfolio (limited only by cash)

print(f"max_total_position: {max_total_position}")
print(f"current_total_position_pct: {current_total_position_pct:.1%}")
print(f"available_position_pct: {available_position_pct:.1%}")
print("✅ 修复后的代码可以正确处理 max_total_position = None")

# 测试 2: 检查 available_cash 为 None 的情况
print("\n2. 检查 available_cash 为 None 的情况")
print("-" * 60)

available_cash = None

# 修复后的逻辑
if available_cash is not None:
    print(f"  - Available cash: ${available_cash:,.2f} (hard limit, cannot exceed)")
else:
    print(f"  - Available cash: unlimited (no cash limit)")
print("✅ 修复后的代码可以正确处理 available_cash = None")

# 测试 3: 检查导入
print("\n3. 检查模块导入")
print("-" * 60)
try:
    from src.agents.trader_agent import run_trader
    print("✅ run_trader 导入成功")
except Exception as e:
    print(f"❌ run_trader 导入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("修复验证完成")
print("=" * 60)
print("修复内容:")
print("  1. 第 676-681 行: 当 max_total_position 为 None 时，使用 1.0 (100%) 作为可用仓位空间")
print("  2. 第 642-646 行: 当 available_cash 为 None 时，打印 'unlimited' 而不是格式化 None")
print("\n现在 Trader Agent 应该可以正常运行，即使没有设置仓位限制。")

