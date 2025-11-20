#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查净值显示和记录是否正常
- 检查 equity_history.jsonl 中的数据格式
- 检查 API 返回的数据格式
- 验证数据一致性
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from src.data.equity_tracker import EquityTracker


def check_equity_history_file(logs_dir: Path):
    """检查 equity_history.jsonl 文件"""
    print("\n" + "="*80)
    print("📊 检查 equity_history.jsonl 文件")
    print("="*80)
    
    equity_file = logs_dir / "equity_history.jsonl"
    
    if not equity_file.exists():
        print("❌ equity_history.jsonl 文件不存在")
        return False
    
    records = []
    issues = []
    
    try:
        with equity_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    records.append((line_num, record))
                    
                    # 检查必需字段
                    required_fields = ["date", "timestamp", "total_value", "cash", "equity_value"]
                    for field in required_fields:
                        if field not in record:
                            issues.append(f"第 {line_num} 行: 缺少字段 '{field}'")
                    
                    # 检查 timestamp 格式
                    if "timestamp" in record:
                        ts = record["timestamp"]
                        if not ts.endswith("Z"):
                            issues.append(f"第 {line_num} 行: timestamp 缺少 'Z' 后缀: {ts}")
                    
                    # 检查数值一致性
                    if "total_value" in record and "cash" in record and "equity_value" in record:
                        total_value = float(record["total_value"])
                        cash = float(record["cash"])
                        equity_value = float(record["equity_value"])
                        calculated_total = cash + equity_value
                        
                        if abs(total_value - calculated_total) > 0.01:
                            issues.append(
                                f"第 {line_num} 行: total_value ({total_value:.2f}) != cash ({cash:.2f}) + equity_value ({equity_value:.2f}) = {calculated_total:.2f}"
                            )
                    
                except json.JSONDecodeError as e:
                    issues.append(f"第 {line_num} 行: JSON 解析错误: {e}")
    
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False
    
    print(f"✅ 文件存在，共 {len(records)} 条记录")
    
    if records:
        print("\n最新 5 条记录:")
        for line_num, record in records[-5:]:
            print(f"  第 {line_num} 行:")
            print(f"    日期: {record.get('date', 'N/A')}")
            print(f"    时间戳: {record.get('timestamp', 'N/A')}")
            print(f"    总资产: ${record.get('total_value', 0):.2f}")
            print(f"    现金: ${record.get('cash', 0):.2f}")
            print(f"    持仓价值: ${record.get('equity_value', 0):.2f}")
            print(f"    总盈亏: ${record.get('total_pnl', 0):.2f}")
            print()
    
    if issues:
        print(f"⚠️  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 所有记录格式正确")
        return True


def check_equity_tracker_api(logs_dir: Path):
    """检查 EquityTracker API 返回的数据"""
    print("\n" + "="*80)
    print("🔍 检查 EquityTracker API")
    print("="*80)
    
    try:
        equity_tracker = EquityTracker(root=str(logs_dir))
        
        # 加载最近 10 条记录
        records = equity_tracker.load_equity_history(limit=10)
        
        if not records:
            print("⚠️  没有找到净值记录")
            return False
        
        print(f"✅ 成功加载 {len(records)} 条记录")
        
        print("\n最近 5 条记录:")
        for i, record in enumerate(records[-5:], 1):
            print(f"\n  记录 {i}:")
            print(f"    日期: {record.get('date', 'N/A')}")
            print(f"    时间戳: {record.get('timestamp', 'N/A')}")
            print(f"    总资产: ${record.get('total_value', 0):.2f}")
            print(f"    现金: ${record.get('cash', 0):.2f}")
            print(f"    持仓价值: ${record.get('equity_value', 0):.2f}")
            print(f"    总盈亏: ${record.get('total_pnl', 0):.2f}")
            print(f"    持仓数量: {len(record.get('positions', {}))}")
        
        # 检查数据格式
        issues = []
        for i, record in enumerate(records):
            # 检查必需字段
            if "total_value" not in record:
                issues.append(f"记录 {i+1}: 缺少 total_value 字段")
            if "timestamp" not in record:
                issues.append(f"记录 {i+1}: 缺少 timestamp 字段")
            elif not record["timestamp"].endswith("Z"):
                issues.append(f"记录 {i+1}: timestamp 缺少 'Z' 后缀")
        
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("\n✅ 所有记录格式正确")
            return True
    
    except Exception as e:
        print(f"❌ API 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_portfolio_state(logs_dir: Path):
    """检查 portfolio_state.json 文件"""
    print("\n" + "="*80)
    print("💼 检查 portfolio_state.json 文件")
    print("="*80)
    
    portfolio_file = logs_dir / "portfolio_state.json"
    
    if not portfolio_file.exists():
        print("⚠️  portfolio_state.json 文件不存在")
        return False
    
    try:
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        print("✅ 文件存在")
        print(f"\n当前状态:")
        print(f"  现金: ${state.get('cash', 0):.2f}")
        print(f"  初始值: ${state.get('initial_value', 0):.2f}")
        print(f"  总资产: ${state.get('total_value', 0):.2f}")
        print(f"  持仓数量: {len(state.get('positions', {}))}")
        
        # 检查数据一致性
        cash = float(state.get("cash", 0))
        total_value = float(state.get("total_value", 0))
        
        # 计算持仓价值
        equity_value = 0.0
        if "positions" in state:
            for symbol, pos_info in state["positions"].items():
                if isinstance(pos_info, dict):
                    quantity = float(pos_info.get("quantity", 0))
                    # 使用 avg_cost 作为当前价格（如果没有 current_price）
                    current_price = float(pos_info.get("current_price", pos_info.get("avg_cost", 0)))
                    equity_value += quantity * current_price
        
        calculated_total = cash + equity_value
        
        if abs(total_value - calculated_total) > 0.01:
            print(f"\n⚠️  数据不一致:")
            print(f"  total_value ({total_value:.2f}) != cash ({cash:.2f}) + calculated_equity ({equity_value:.2f}) = {calculated_total:.2f}")
            return False
        else:
            print(f"\n✅ 数据一致性检查通过")
            print(f"  total_value ({total_value:.2f}) = cash ({cash:.2f}) + equity_value ({equity_value:.2f})")
            return True
    
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*80)
    print("🔍 净值显示和记录检查工具")
    print("="*80)
    
    # 确定 logs 目录
    project_root = Path(__file__).resolve().parent.parent.parent
    logs_dir = project_root / "backend" / "data" / "logs"
    
    if not logs_dir.exists():
        print(f"❌ 日志目录不存在: {logs_dir}")
        return 1
    
    print(f"\n📁 日志目录: {logs_dir}")
    
    # 执行检查
    results = []
    
    results.append(("equity_history.jsonl 文件", check_equity_history_file(logs_dir)))
    results.append(("EquityTracker API", check_equity_tracker_api(logs_dir)))
    results.append(("portfolio_state.json 文件", check_portfolio_state(logs_dir)))
    
    # 总结
    print("\n" + "="*80)
    print("📋 检查总结")
    print("="*80)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ 所有检查通过！净值显示和记录功能正常。")
        return 0
    else:
        print("❌ 部分检查失败，请查看上面的详细信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

