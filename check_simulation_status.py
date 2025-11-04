#!/usr/bin/env python3
"""
检查模拟状态和对话生成情况
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_simulation_status():
    """检查模拟状态"""
    print("=" * 80)
    print("检查模拟状态和对话生成")
    print("=" * 80)
    print()
    
    # 1. 检查 discussion_actions.jsonl
    logs_dir = Path("data/logs")
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    print(f"[1] 检查对话文件: {convo_file.absolute()}")
    if not convo_file.exists():
        print("   ✗ 文件不存在！")
        print("   可能原因：模拟未启动，或文件被清空")
        return False
    else:
        print("   ✓ 文件存在")
        
        # 读取文件内容
        try:
            with convo_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"   文件大小: {len(lines)} 行")
            
            if len(lines) == 0:
                print("   ⚠ 文件为空！")
                print("   可能原因：")
                print("     - 模拟刚启动，还没生成对话")
                print("     - 模拟执行失败，没有调用 execute_daily_trade")
                print("     - 对话写入失败")
            else:
                print("   ✓ 文件有内容")
                print(f"\n   前 5 条对话:")
                for i, line in enumerate(lines[:5], 1):
                    try:
                        entry = json.loads(line.strip())
                        agent = entry.get("agent", "Unknown")
                        date = entry.get("date", entry.get("timestamp", "N/A"))
                        content_preview = entry.get("content", "")[:50]
                        print(f"     {i}. [{date}] {agent}: {content_preview}...")
                    except:
                        print(f"     {i}. (解析失败): {line[:50]}...")
        except Exception as e:
            print(f"   ✗ 读取文件失败: {e}")
            return False
    
    print()
    
    # 2. 检查 API 模拟状态
    print("[2] 检查 API 模拟状态")
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/api/trading/simulate-status", timeout=5)
        if response.ok:
            data = response.json()
            status = data.get("status", {})
            print(f"   运行状态: {'运行中' if status.get('running') else '未运行'}")
            print(f"   当前天数: {status.get('current_day', 0)} / {status.get('total_days', 22)}")
            print(f"   开始时间: {status.get('started_at', 'N/A')}")
            print(f"   最后更新: {status.get('last_update', 'N/A')}")
            if status.get('error'):
                print(f"   ⚠ 错误: {status.get('error')}")
        else:
            print(f"   ✗ API 返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ✗ 无法连接到 API (http://127.0.0.1:8000)")
        print("   请确保后端 API 正在运行")
    except Exception as e:
        print(f"   ✗ 检查失败: {e}")
    
    print()
    
    # 3. 检查 trades.jsonl
    print("[3] 检查交易记录")
    trades_file = logs_dir / "trades.jsonl"
    if trades_file.exists():
        with trades_file.open("r", encoding="utf-8") as f:
            trades = [json.loads(line) for line in f if line.strip()]
        print(f"   ✓ 找到 {len(trades)} 笔交易")
        if trades:
            print(f"   最新交易: {trades[-1].get('symbol', 'N/A')} {trades[-1].get('action', 'N/A')} @ ${trades[-1].get('price', 0):.2f}")
    else:
        print("   ⚠ 交易记录文件不存在或为空")
    
    print()
    
    # 4. 检查 portfolio_state.json
    print("[4] 检查投资组合状态")
    portfolio_file = logs_dir / "portfolio_state.json"
    if portfolio_file.exists():
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        cash = state.get("cash", 0)
        positions = state.get("positions", {})
        print(f"   现金: ${cash:.2f}")
        print(f"   持仓: {len(positions)} 个")
        if positions:
            print("   持仓详情:")
            for symbol, pos in list(positions.items())[:3]:
                qty = pos.get("quantity", 0)
                avg_cost = pos.get("avg_cost", 0)
                print(f"     - {symbol}: {qty} shares @ ${avg_cost:.2f}")
    else:
        print("   ⚠ 投资组合状态文件不存在")
    
    print()
    print("=" * 80)
    print("诊断完成")
    print("=" * 80)
    print()
    print("建议:")
    print("1. 如果模拟未运行，检查后端 API 日志")
    print("2. 如果对话文件为空，可能是模拟线程崩溃或 execute_daily_trade 未执行")
    print("3. 检查后端终端是否有错误信息")
    print("4. 尝试重启 API 并重新运行模拟")

if __name__ == "__main__":
    check_simulation_status()

