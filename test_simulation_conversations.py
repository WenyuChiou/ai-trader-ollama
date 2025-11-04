#!/usr/bin/env python3
"""
测试模拟是否能正确生成对话
"""
import sys
import os
import io
import json
from pathlib import Path
from datetime import date, datetime, timezone, timedelta

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_conversation_file():
    """检查对话文件状态"""
    logs_dir = Path("data/logs")
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    print("=" * 80)
    print("检查对话文件状态")
    print("=" * 80)
    
    if not convo_file.exists():
        print(f"❌ 文件不存在: {convo_file.absolute()}")
        return False
    
    print(f"✅ 文件存在: {convo_file.absolute()}")
    
    # 读取文件内容
    try:
        with convo_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines:
            print(f"⚠️  文件为空（0 行）")
            print(f"   说明：模拟可能刚启动，或者 execute_daily_trade 没有执行")
            return False
        
        print(f"✅ 文件包含 {len(lines)} 行对话")
        print("\n最近 3 条对话:")
        for i, line in enumerate(lines[-3:], 1):
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", "Unknown")
                date_str = entry.get("date", entry.get("timestamp", "N/A"))
                content_preview = entry.get("content", "")[:50]
                print(f"  {i}. [{agent}] {date_str}: {content_preview}...")
            except:
                print(f"  {i}. [Invalid JSON]: {line[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

def test_single_day_execution():
    """测试单日执行"""
    print("\n" + "=" * 80)
    print("测试单日执行（2024-10-01）")
    print("=" * 80)
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        # 执行单日交易
        print("\n[INFO] 执行 execute_daily_trade...")
        result = execute_daily_trade(
            start="2024-09-20",  # 提前10天获取数据
            end="2024-10-01",
            universe=["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]  # 使用少量股票测试
        )
        
        print(f"\n[INFO] 执行结果:")
        print(f"  - Final stance: {result.get('final_stance', 'N/A')}")
        print(f"  - Buy orders: {len(result.get('buy_orders', []))}")
        print(f"  - Sell orders: {len(result.get('sell_orders', []))}")
        print(f"  - Placed orders: {len(result.get('placed_orders', []))}")
        
        # 检查对话文件
        logs_dir = Path("data/logs")
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if convo_file.exists():
            with convo_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"\n[INFO] 对话文件状态:")
            print(f"  - 总行数: {len(lines)}")
            if lines:
                print(f"  - 最后一行: {lines[-1][:100]}...")
                return True
            else:
                print(f"  - ⚠️  文件为空")
                return False
        else:
            print(f"\n[ERROR] 对话文件不存在")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("模拟对话生成测试")
    print("=" * 80)
    
    # 步骤1: 检查当前文件状态
    has_conversations = check_conversation_file()
    
    # 步骤2: 如果文件为空，测试单日执行
    if not has_conversations:
        print("\n文件为空，执行单日测试...")
        success = test_single_day_execution()
        if success:
            print("\n✅ 测试成功：对话已生成")
            check_conversation_file()  # 再次检查
        else:
            print("\n❌ 测试失败：对话未生成")
    else:
        print("\n✅ 对话文件已有内容，无需测试")

