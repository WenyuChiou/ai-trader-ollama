#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查订单记录是否有超出可用现金的问题
- 按时间顺序模拟订单执行
- 检查每个BUY订单执行时的现金是否足够
- 验证现金余额是否正确更新
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from src.data.portfolio import Portfolio


def parse_timestamp(ts_str):
    """解析时间戳字符串"""
    try:
        # 处理各种时间戳格式
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        return datetime.min


def load_orders(logs_dir: Path):
    """加载所有订单记录"""
    filled_orders_file = logs_dir / "filled_orders.jsonl"
    
    if not filled_orders_file.exists():
        print(f"❌ 订单文件不存在: {filled_orders_file}")
        return []
    
    orders = []
    try:
        with filled_orders_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    order = json.loads(line)
                    order['_line_num'] = line_num
                    orders.append(order)
                except json.JSONDecodeError as e:
                    print(f"⚠️  第 {line_num} 行 JSON 解析错误: {e}")
    except Exception as e:
        print(f"❌ 读取订单文件失败: {e}")
        return []
    
    # 按时间排序
    orders.sort(key=lambda x: parse_timestamp(x.get("placed_at", x.get("filled_at", ""))))
    
    return orders


def check_orders_cash_validation(orders, initial_cash=10000.0):
    """检查订单现金验证"""
    print("\n" + "="*80)
    print("💰 订单现金验证检查")
    print("="*80)
    
    if not orders:
        print("⚠️  没有找到订单记录")
        return True
    
    print(f"📊 共找到 {len(orders)} 条订单记录")
    print(f"💰 初始现金: ${initial_cash:.2f}\n")
    
    # 模拟投资组合
    portfolio = Portfolio(cash=initial_cash, initial_value=initial_cash)
    
    issues = []
    buy_orders = []
    sell_orders = []
    
    # 按时间顺序处理订单
    for i, order in enumerate(orders, 1):
        symbol = order.get("symbol", "UNKNOWN")
        action = order.get("action", "").upper()
        quantity = order.get("quantity", 0)
        fill_price = order.get("fill_price", 0.0)
        order_id = order.get("order_id", f"order_{i}")
        placed_at = order.get("placed_at", order.get("filled_at", ""))
        
        if action == "BUY":
            buy_orders.append(order)
            total_cost = fill_price * quantity
            cash_before = portfolio.cash
            
            # 检查现金是否足够
            if total_cost > cash_before:
                issue = {
                    "order_id": order_id,
                    "line_num": order.get("_line_num", i),
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "fill_price": fill_price,
                    "total_cost": total_cost,
                    "cash_before": cash_before,
                    "cash_after": cash_before - total_cost,
                    "shortfall": total_cost - cash_before,
                    "placed_at": placed_at,
                    "issue_type": "INSUFFICIENT_CASH",
                }
                issues.append(issue)
                print(f"❌ 订单 {i} ({order_id}):")
                print(f"   符号: {symbol}")
                print(f"   操作: {action}")
                print(f"   数量: {quantity}")
                print(f"   价格: ${fill_price:.2f}")
                print(f"   总成本: ${total_cost:.2f}")
                print(f"   执行前现金: ${cash_before:.2f}")
                print(f"   现金缺口: ${total_cost - cash_before:.2f}")
                print(f"   时间: {placed_at}")
                print()
            else:
                # 执行买入
                try:
                    portfolio.buy(symbol, quantity, fill_price)
                    cash_after = portfolio.cash
                    print(f"✅ 订单 {i} ({order_id}): BUY {quantity} {symbol} @ ${fill_price:.2f} = ${total_cost:.2f}")
                    print(f"   现金: ${cash_before:.2f} → ${cash_after:.2f}")
                except ValueError as e:
                    issue = {
                        "order_id": order_id,
                        "line_num": order.get("_line_num", i),
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "fill_price": fill_price,
                        "total_cost": total_cost,
                        "cash_before": cash_before,
                        "error": str(e),
                        "placed_at": placed_at,
                        "issue_type": "EXECUTION_ERROR",
                    }
                    issues.append(issue)
                    print(f"❌ 订单 {i} ({order_id}): 执行失败 - {e}")
        
        elif action == "SELL":
            sell_orders.append(order)
            # 检查持仓是否足够
            pos = portfolio.get_position(symbol)
            if pos is None or pos.quantity < quantity:
                issue = {
                    "order_id": order_id,
                    "line_num": order.get("_line_num", i),
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "fill_price": fill_price,
                    "position_quantity": pos.quantity if pos else 0,
                    "placed_at": placed_at,
                    "issue_type": "INSUFFICIENT_POSITION",
                }
                issues.append(issue)
                print(f"❌ 订单 {i} ({order_id}):")
                print(f"   符号: {symbol}")
                print(f"   操作: {action}")
                print(f"   数量: {quantity}")
                print(f"   持仓数量: {pos.quantity if pos else 0}")
                print(f"   时间: {placed_at}")
                print()
            else:
                # 执行卖出
                try:
                    cash_before = portfolio.cash
                    realized_pnl = portfolio.sell(symbol, quantity, fill_price)
                    cash_after = portfolio.cash
                    proceeds = quantity * fill_price
                    print(f"✅ 订单 {i} ({order_id}): SELL {quantity} {symbol} @ ${fill_price:.2f} = ${proceeds:.2f}")
                    print(f"   现金: ${cash_before:.2f} → ${cash_after:.2f}")
                    print(f"   已实现盈亏: ${realized_pnl['realized_pnl']:.2f} ({realized_pnl['realized_pnl_pct']:.2f}%)")
                except ValueError as e:
                    issue = {
                        "order_id": order_id,
                        "line_num": order.get("_line_num", i),
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "fill_price": fill_price,
                        "error": str(e),
                        "placed_at": placed_at,
                        "issue_type": "EXECUTION_ERROR",
                    }
                    issues.append(issue)
                    print(f"❌ 订单 {i} ({order_id}): 执行失败 - {e}")
    
    # 总结
    print("\n" + "="*80)
    print("📋 检查总结")
    print("="*80)
    print(f"总订单数: {len(orders)}")
    print(f"  - 买入订单: {len(buy_orders)}")
    print(f"  - 卖出订单: {len(sell_orders)}")
    print(f"发现问题: {len(issues)}")
    print(f"最终现金: ${portfolio.cash:.2f}")
    print(f"最终持仓数量: {len(portfolio._positions)}")
    
    if issues:
        print("\n⚠️  发现的问题:")
        for issue in issues:
            print(f"  - {issue['issue_type']}: {issue.get('symbol', 'UNKNOWN')} - {issue.get('order_id', 'UNKNOWN')}")
        return False
    else:
        print("\n✅ 所有订单现金验证通过！")
        return True


def check_order_amounts(orders):
    """检查订单金额计算是否正确"""
    print("\n" + "="*80)
    print("🔍 订单金额计算检查")
    print("="*80)
    
    issues = []
    
    for i, order in enumerate(orders, 1):
        symbol = order.get("symbol", "UNKNOWN")
        action = order.get("action", "").upper()
        quantity = order.get("quantity", 0)
        fill_price = order.get("fill_price", 0.0)
        order_id = order.get("order_id", f"order_{i}")
        
        # 计算订单金额
        calculated_amount = fill_price * quantity
        
        # 检查是否有 amount 字段
        if "amount" in order:
            recorded_amount = order["amount"]
            if abs(calculated_amount - recorded_amount) > 0.01:
                issue = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "action": action,
                    "calculated": calculated_amount,
                    "recorded": recorded_amount,
                    "difference": abs(calculated_amount - recorded_amount),
                }
                issues.append(issue)
                print(f"⚠️  订单 {order_id}: 金额不一致")
                print(f"   计算值: ${calculated_amount:.2f}")
                print(f"   记录值: ${recorded_amount:.2f}")
                print(f"   差异: ${abs(calculated_amount - recorded_amount):.2f}")
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个金额不一致的问题")
        return False
    else:
        print("✅ 所有订单金额计算正确")
        return True


def main():
    """主函数"""
    print("="*80)
    print("🔍 订单现金验证检查工具")
    print("="*80)
    
    # 确定 logs 目录（检查多个可能的位置）
    project_root = Path(__file__).resolve().parent.parent.parent
    possible_dirs = [
        project_root / "data" / "logs",
        project_root / "backend" / "data" / "logs",
    ]
    
    logs_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            logs_dir = dir_path
            break
    
    if logs_dir is None:
        print(f"❌ 日志目录不存在，检查了以下位置:")
        for dir_path in possible_dirs:
            print(f"   - {dir_path}")
        return 1
    
    print(f"\n📁 日志目录: {logs_dir}")
    
    # 加载订单
    orders = load_orders(logs_dir)
    
    if not orders:
        print("⚠️  没有找到订单记录")
        return 0
    
    # 获取初始现金（从 portfolio_state.json 或使用默认值）
    initial_cash = 10000.0
    portfolio_state_file = logs_dir / "portfolio_state.json"
    if portfolio_state_file.exists():
        try:
            with portfolio_state_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
                initial_cash = float(state.get("initial_value", 10000.0))
                print(f"📊 从 portfolio_state.json 读取初始现金: ${initial_cash:.2f}")
        except Exception as e:
            print(f"⚠️  读取 portfolio_state.json 失败: {e}，使用默认值 ${initial_cash:.2f}")
    
    # 执行检查
    results = []
    
    results.append(("订单现金验证", check_orders_cash_validation(orders, initial_cash)))
    results.append(("订单金额计算", check_order_amounts(orders)))
    
    # 总结
    print("\n" + "="*80)
    print("📋 最终总结")
    print("="*80)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ 所有检查通过！订单记录正常。")
        return 0
    else:
        print("❌ 部分检查失败，请查看上面的详细信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

