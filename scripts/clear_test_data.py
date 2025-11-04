#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""清空所有测试文件和记录，重置系统到初始状态"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
import json
from datetime import datetime, timezone

def clear_test_data():
    """清空所有测试数据"""
    print("=" * 60)
    print("清空测试文件和记录")
    print("=" * 60)
    
    # 确定日志目录
    logs_dir = Path("data/logs")
    if not logs_dir.exists():
        logs_dir = Path(__file__).parent.parent / "data" / "logs"
    
    if not logs_dir.exists():
        print(f"❌ 日志目录不存在: {logs_dir}")
        return
    
    print(f"📁 日志目录: {logs_dir}")
    print()
    
    # 1. 清空所有 JSONL 文件
    jsonl_files = [
        "discussion_actions.jsonl",
        "trades.jsonl",
        "filled_orders.jsonl",
        "pending_orders.jsonl",
        "real_time_snapshots.jsonl",
        "equity_history.jsonl",
        "events.jsonl",
    ]
    
    print("📝 清空 JSONL 文件:")
    for filename in jsonl_files:
        file_path = logs_dir / filename
        if file_path.exists():
            try:
                file_path.write_text("", encoding="utf-8")
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")
        else:
            print(f"  - {filename} (不存在)")
    
    print()
    
    # 2. 重置 portfolio_state.json
    portfolio_file = logs_dir / "portfolio_state.json"
    print("💼 重置投资组合状态:")
    try:
        initial_state = {
            "cash": 10000.0,
            "initial_value": 10000.0,
            "positions": {},
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        portfolio_file.write_text(
            json.dumps(initial_state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✓ portfolio_state.json (重置为初始状态: $10,000)")
    except Exception as e:
        print(f"  ✗ portfolio_state.json: {e}")
    
    print()
    
    # 3. 删除 last_trade_date.txt
    last_trade_file = logs_dir / "last_trade_date.txt"
    print("🔓 删除交易日锁定:")
    if last_trade_file.exists():
        try:
            last_trade_file.unlink()
            print(f"  ✓ last_trade_date.txt (已删除)")
        except Exception as e:
            print(f"  ✗ last_trade_date.txt: {e}")
    else:
        print(f"  - last_trade_date.txt (不存在)")
    
    print()
    
    # 4. 清空 memory 目录
    memory_dir = logs_dir / "memory"
    print("🧠 清空记忆文件:")
    if memory_dir.exists():
        try:
            # 清空 daily 目录
            daily_dir = memory_dir / "daily"
            if daily_dir.exists():
                for file in daily_dir.glob("*.json"):
                    try:
                        file.unlink()
                        print(f"  ✓ 删除: {file.name}")
                    except Exception as e:
                        print(f"  ✗ 删除 {file.name}: {e}")
            
            # 清空 weekly 目录
            weekly_dir = memory_dir / "weekly"
            if weekly_dir.exists():
                for file in weekly_dir.glob("*.jsonl"):
                    try:
                        file.unlink()
                        print(f"  ✓ 删除: {file.name}")
                    except Exception as e:
                        print(f"  ✗ 删除 {file.name}: {e}")
            
            # 重置 daily_index.json
            index_file = memory_dir / "index" / "daily_index.json"
            if index_file.exists():
                try:
                    index_file.write_text("{}", encoding="utf-8")
                    print(f"  ✓ 重置: daily_index.json")
                except Exception as e:
                    print(f"  ✗ 重置 daily_index.json: {e}")
        except Exception as e:
            print(f"  ✗ 清空 memory 目录: {e}")
    else:
        print(f"  - memory 目录不存在")
    
    print()
    
    # 5. 删除 demo_prices.json
    demo_prices_file = logs_dir / "demo_prices.json"
    print("🎲 删除演示数据:")
    if demo_prices_file.exists():
        try:
            demo_prices_file.unlink()
            print(f"  ✓ demo_prices.json (已删除)")
        except Exception as e:
            print(f"  ✗ demo_prices.json: {e}")
    else:
        print(f"  - demo_prices.json (不存在)")
    
    print()
    
    # 6. 清空 api_execution.log（可选，保留最近几行）
    log_file = logs_dir / "api_execution.log"
    print("📋 清空执行日志:")
    if log_file.exists():
        try:
            # 保留最后100行作为备份（可选）
            with log_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 100:
                # 只保留最后100行
                with log_file.open("w", encoding="utf-8") as f:
                    f.write("".join(lines[-100:]))
                print(f"  ✓ api_execution.log (保留最后100行)")
            else:
                # 完全清空
                log_file.write_text("", encoding="utf-8")
                print(f"  ✓ api_execution.log (已清空)")
        except Exception as e:
            print(f"  ✗ api_execution.log: {e}")
    else:
        print(f"  - api_execution.log (不存在)")
    
    print()
    print("=" * 60)
    print("✅ 测试数据清空完成！")
    print("=" * 60)
    print()
    print("系统已重置为初始状态：")
    print("  - 投资组合: $10,000 现金，无持仓")
    print("  - 所有交易记录已清空")
    print("  - 所有对话记录已清空")
    print("  - 所有记忆文件已清空")
    print("  - 交易日锁定已解除")
    print()
    print("现在可以开始新的实时交易测试。")

if __name__ == "__main__":
    clear_test_data()

