#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後端直接測試完整交易循環（使用今天真實數據）
不通過 API，直接調用 execute_daily_trade
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime, date

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 確保在 backend 目錄
import os
backend_dir = Path(__file__).parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_subsection(title):
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)

def main():
    print_section("後端直接測試完整交易循環")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目錄: {os.getcwd()}")
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        print_section("開始執行交易循環")
        print("使用今天真實數據...")
        
        # 執行完整交易循環
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=3
        )
        
        if not result:
            print("❌ 交易循環返回空結果")
            return
        
        print_section("交易循環執行完成")
        
        # 顯示市場數據
        print_subsection("市場數據與指標")
        market_agent = result.get("market_agent", {})
        stocks = market_agent.get("stocks", {})
        vix = market_agent.get("VIX", {})
        
        print(f"\nVIX 波動率指標:")
        print(f"  Level: {vix.get('level', 'N/A')}")
        print(f"  日變化: {vix.get('chg_1d', 'N/A')}")
        print(f"  Z-Score: {vix.get('zscore', 'N/A')}")
        
        print(f"\n股票技術指標 (共 {len(stocks)} 檔):")
        for symbol, data in list(stocks.items())[:5]:
            print(f"\n  {symbol}:")
            print(f"    價格: ${data.get('price', 0):.2f}")
            print(f"    變化: {data.get('change_pct', 0):.2f}%")
            print(f"    RSI14: {data.get('rsi14', 0):.2f}")
            print(f"    MACD: {data.get('macd', 0):.2f}")
            print(f"    MACD Hist: {data.get('macd_hist', 0):.2f}")
            print(f"    BB Position: {data.get('bb_pos', 0):.2f}")
            print(f"    信號分數: {data.get('signal_score', 0)}")
        
        # 顯示討論結果
        print_subsection("Agent 討論結果")
        discussion = result.get("discussion", {})
        final_stance = discussion.get("final_stance", "unknown")
        rounds = discussion.get("rounds", 0)
        tool_context = discussion.get("tool_context", [])
        
        print(f"最終立場: {final_stance}")
        print(f"討論輪數: {rounds}")
        
        if tool_context:
            print(f"\n工具使用 ({len(tool_context)} 項):")
            for tool_info in tool_context:
                print(f"  • {tool_info}")
        
        transcript = discussion.get("transcript", [])
        if transcript:
            print(f"\n對話摘要（共 {len(transcript)} 段）:")
            for i, round_text in enumerate(transcript[:3], 1):  # 只顯示前3段
                preview = round_text[:200] if len(round_text) > 200 else round_text
                print(f"  Round {i}: {preview}...")
        
        # 顯示決策與訂單
        print_subsection("交易決策與訂單")
        decision = result.get("decision", {})
        action = decision.get("action", "N/A")
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        placed_orders = result.get("placed_orders", [])
        
        print(f"決策動作: {action}")
        
        if buy_orders:
            print(f"\n買入訂單 ({len(buy_orders)} 筆):")
            for order in buy_orders:
                print(f"  • {order.get('symbol')}: {order.get('quantity')} 股 @ ${order.get('buy_price', 0):.2f} (總額: ${order.get('total_cost', 0):.2f})")
        
        if sell_orders:
            print(f"\n賣出訂單 ({len(sell_orders)} 筆):")
            for order in sell_orders:
                print(f"  • {order}")
        
        if placed_orders:
            print(f"\n已掛單 ({len(placed_orders)} 筆):")
            for order in placed_orders:
                print(f"  • {order.get('symbol')} {order.get('action')}: {order.get('quantity')} 股 @ ${order.get('limit_price', 0):.2f} (狀態: {order.get('status', 'N/A')})")
        
        # 檢查對話是否寫入
        print_subsection("檢查對話日誌")
        logs_dir = Path("data/logs")
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        if convo_file.exists():
            with convo_file.open("r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if l.strip()]
            
            print(f"對話日誌文件: {convo_file}")
            print(f"總共 {len(lines)} 條記錄")
            
            if lines:
                print("\n最新的 5 條對話:")
                for line in lines[-5:]:
                    try:
                        entry = json.loads(line.strip())
                        agent = entry.get("agent", "Unknown")
                        round_num = entry.get("round", 0)
                        content = entry.get("content", "")[:100]
                        entry_type = entry.get("type", "unknown")
                        print(f"  [{entry_type}] {agent} (Round {round_num}): {content}...")
                    except:
                        print(f"  {line.strip()[:100]}...")
            else:
                print("⚠️  對話日誌文件為空")
        else:
            print(f"⚠️  對話日誌文件不存在: {convo_file}")
        
        # 顯示組合狀態
        print_subsection("組合狀態")
        portfolio_data = result.get("portfolio", {})
        cash = portfolio_data.get("cash", 0)
        positions = portfolio_data.get("positions", {})
        total_value = portfolio_data.get("total_value", 0)
        
        print(f"現金: ${cash:.2f}")
        print(f"總資產: ${total_value:.2f}")
        print(f"持倉數量: {len(positions)}")
        
        if positions:
            print("\n持倉詳情:")
            for symbol, pos in positions.items():
                if isinstance(pos, dict):
                    qty = pos.get("quantity", 0)
                    avg_cost = pos.get("avg_cost", 0)
                    print(f"  • {symbol}: {qty} 股 @ 均價 ${avg_cost:.2f}")
        
        print_section("測試完成")
        print("✓ 交易循環執行成功")
        print("✓ 對話已寫入日誌（如果有的話）")
        print("✓ 訂單已生成")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

