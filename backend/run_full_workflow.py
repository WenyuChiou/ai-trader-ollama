#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流程测试脚本
运行一次完整的交易周期，包括：
1. 市场数据获取
2. 分析师讨论（生成聊天记录）
3. 订单创建
4. 订单执行检查
5. 整理所有输出
"""
from __future__ import annotations
import sys
import json
import io
from pathlib import Path
from datetime import date, datetime, timezone
from typing import Dict, Any, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加backend目录到路径
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio
from src.utils.config_loader import load_config

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    if not file_path.exists():
        return []
    entries = []
    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def format_workflow_summary() -> Dict[str, Any]:
    """运行完整工作流程并整理结果"""
    print("=" * 80)
    print("🚀 开始运行完整交易工作流程")
    print("=" * 80)
    
    # 1. 加载配置
    config = load_config()
    universe = config.get("universe", ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"])
    tool_budget = config.get("tool_budget", 8)
    rounds = config.get("rounds", 3)
    
    print(f"\n📋 配置信息:")
    print(f"  - Universe: {len(universe)} 只股票")
    print(f"  - Tool Budget: {tool_budget}")
    print(f"  - Rounds: {rounds}")
    
    # 2. 运行交易周期
    print(f"\n🔄 执行交易周期...")
    try:
        result = execute_daily_trade(
            universe=universe,
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            min_tools=3,
        )
        print("✅ 交易周期执行完成")
    except Exception as e:
        print(f"❌ 交易周期执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    
    # 3. 收集所有数据
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 3.1 聊天记录（discussion_actions.jsonl）
    convo_file = logs_dir / "discussion_actions.jsonl"
    conversations = load_jsonl(convo_file)
    print(f"\n💬 聊天记录: {len(conversations)} 条")
    
    # 3.2 订单记录
    pending_file = logs_dir / "pending_orders.jsonl"
    filled_file = logs_dir / "filled_orders.jsonl"
    pending_orders = load_jsonl(pending_file)
    filled_orders = load_jsonl(filled_file)
    print(f"📦 订单记录: {len(pending_orders)} pending, {len(filled_orders)} filled")
    
    # 3.3 Portfolio状态
    portfolio_file = logs_dir / "portfolio_state.json"
    portfolio_state = {}
    if portfolio_file.exists():
        with portfolio_file.open('r', encoding='utf-8') as f:
            portfolio_state = json.load(f)
    print(f"💰 Portfolio状态: Cash=${portfolio_state.get('cash', 0):.2f}")
    
    # 4. 整理结果
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "universe_size": len(universe),
            "tool_budget": tool_budget,
            "rounds": rounds,
        },
        "trading_cycle_result": {
            "final_stance": result.get("final_stance", "unknown"),
            "market_summary": result.get("market_summary", {}),
        },
        "conversations": {
            "total": len(conversations),
            "recent": conversations[-10:] if len(conversations) > 10 else conversations,  # 最近10条
            "by_type": {},
        },
        "orders": {
            "pending": {
                "total": len(pending_orders),
                "recent": pending_orders[-10:] if len(pending_orders) > 10 else pending_orders,
            },
            "filled": {
                "total": len(filled_orders),
                "recent": filled_orders[-10:] if len(filled_orders) > 10 else filled_orders,
            },
        },
        "portfolio": portfolio_state,
    }
    
    # 统计对话类型
    for conv in conversations:
        conv_type = conv.get("type", "unknown")
        summary["conversations"]["by_type"][conv_type] = summary["conversations"]["by_type"].get(conv_type, 0) + 1
    
    return summary

def print_workflow_summary(summary: Dict[str, Any]):
    """打印格式化的摘要"""
    print("\n" + "=" * 80)
    print("📊 工作流程完整摘要")
    print("=" * 80)
    
    # 配置信息
    print(f"\n📋 配置:")
    print(f"  - Universe大小: {summary['config']['universe_size']} 只股票")
    print(f"  - Tool Budget: {summary['config']['tool_budget']}")
    print(f"  - Rounds: {summary['config']['rounds']}")
    
    # 交易周期结果
    print(f"\n🔄 交易周期结果:")
    print(f"  - Final Stance: {summary['trading_cycle_result']['final_stance']}")
    
    # 对话记录
    print(f"\n💬 对话记录:")
    print(f"  - 总计: {summary['conversations']['total']} 条")
    print(f"  - 按类型分布:")
    for conv_type, count in summary['conversations']['by_type'].items():
        print(f"    * {conv_type}: {count} 条")
    
    if summary['conversations']['recent']:
        print(f"\n  - 最近对话 (最后{len(summary['conversations']['recent'])}条):")
        for i, conv in enumerate(summary['conversations']['recent'], 1):
            agent = conv.get("agent", "Unknown")
            conv_type = conv.get("type", "unknown")
            content = conv.get("content", conv.get("analysis", ""))[:100]
            timestamp = conv.get("timestamp", conv.get("date", ""))
            print(f"    {i}. [{conv_type}] {agent}: {content}...")
            print(f"       时间: {timestamp}")
    
    # 订单记录
    print(f"\n📦 订单记录:")
    print(f"  - Pending: {summary['orders']['pending']['total']} 笔")
    if summary['orders']['pending']['recent']:
        print(f"    - 最近订单:")
        for order in summary['orders']['pending']['recent'][-5:]:
            symbol = order.get("symbol", "?")
            action = order.get("action", "?")
            quantity = order.get("quantity", 0)
            limit_price = order.get("limit_price", 0)
            order_date = order.get("order_date", "?")
            print(f"      * {order_date} {action} {quantity} {symbol} @ ${limit_price:.2f}")
    
    print(f"  - Filled: {summary['orders']['filled']['total']} 笔")
    if summary['orders']['filled']['recent']:
        print(f"    - 最近成交:")
        for order in summary['orders']['filled']['recent'][-5:]:
            symbol = order.get("symbol", "?")
            action = order.get("action", "?")
            quantity = order.get("quantity", 0)
            fill_price = order.get("fill_price", order.get("price", 0))
            fill_date = order.get("fill_date", order.get("order_date", "?"))
            print(f"      * {fill_date} {action} {quantity} {symbol} @ ${fill_price:.2f}")
    
    # Portfolio状态
    print(f"\n💰 Portfolio状态:")
    cash = summary['portfolio'].get('cash', 0)
    initial_value = summary['portfolio'].get('initial_value', 10000)
    positions = summary['portfolio'].get('positions', {})
    print(f"  - 现金: ${cash:.2f}")
    print(f"  - 初始价值: ${initial_value:.2f}")
    print(f"  - 持仓数量: {len(positions)}")
    if positions:
        print(f"  - 持仓详情:")
        for symbol, pos_data in list(positions.items())[:5]:
            if isinstance(pos_data, dict):
                quantity = pos_data.get('quantity', 0)
                avg_cost = pos_data.get('avg_cost', 0)
                print(f"    * {symbol}: {quantity} 股 @ ${avg_cost:.2f}")
            else:
                print(f"    * {symbol}: {pos_data}")
    
    print("\n" + "=" * 80)
    print("✅ 工作流程摘要完成")
    print("=" * 80)

if __name__ == "__main__":
    try:
        summary = format_workflow_summary()
        if "error" not in summary:
            print_workflow_summary(summary)
            
            # 保存到文件
            output_file = Path("data/logs/workflow_summary.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open('w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n💾 摘要已保存到: {output_file}")
        else:
            print(f"\n❌ 工作流程执行失败: {summary['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

