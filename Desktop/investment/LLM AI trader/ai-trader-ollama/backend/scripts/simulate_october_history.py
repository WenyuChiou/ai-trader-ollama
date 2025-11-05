#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟10月份历史数据交易
每5分钟模拟一天，查看agent的交易决策
"""
import sys
import io
import json
import time
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 確保在 backend 目錄
import os
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def init_october_simulation():
    """初始化10月模拟"""
    print_section("初始化10月历史数据模拟")
    
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 清空對話日誌
    convo_file = logs_dir / "discussion_actions.jsonl"
    if convo_file.exists():
        convo_file.write_text("", encoding="utf-8")
        print("  ✓ 已清空對話日誌")
    
    # 清空掛單記錄
    pending_file = logs_dir / "pending_orders.jsonl"
    if pending_file.exists():
        pending_file.write_text("", encoding="utf-8")
        print("  ✓ 已清空掛單記錄")
    
    # 重置組合狀態
    portfolio_file = logs_dir / "portfolio_state.json"
    initial_state = {
        "cash": 10000.0,
        "initial_value": 10000.0,
        "positions": {},
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    portfolio_file.write_text(json.dumps(initial_state, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  ✓ 已重置組合狀態 ($10,000)")
    
    # 清空單日鎖
    last_trade_file = logs_dir / "last_trade_date.txt"
    if last_trade_file.exists():
        last_trade_file.unlink()
        print("  ✓ 已清除單日鎖")
    
    return logs_dir

def settle_orders(settle_date, logs_dir):
    """結算訂單"""
    from src.data.order_executor import get_current_or_open_price
    
    order_manager = OrderManager(root="data/logs")
    pending_orders = order_manager.load_pending_orders(order_date=settle_date)
    
    if not pending_orders:
        return 0
    
    print(f"[結算訂單] {settle_date}: {len(pending_orders)} 筆待結算")
    
    # 載入組合
    portfolio_file = logs_dir / "portfolio_state.json"
    if not portfolio_file.exists():
        return 0
    
    with portfolio_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    
    portfolio = Portfolio(
        cash=float(state.get("cash", 10000.0)),
        initial_value=float(state.get("initial_value", 10000.0)),
    )
    
    # 恢復持倉
    for symbol, pos_info in state.get("positions", {}).items():
        if isinstance(pos_info, dict):
            qty = int(pos_info.get("quantity", 0))
            avg_cost = float(pos_info.get("avg_cost", 0))
            if qty > 0:
                portfolio.positions[symbol] = {"quantity": qty, "avg_cost": avg_cost}
    
    settled_count = 0
    for order in pending_orders:
        symbol = order.get("symbol")
        action = order.get("action", "").upper()
        quantity = order.get("quantity", 0)
        limit_price = order.get("limit_price", 0)
        
        try:
            # 獲取當前價格（使用歷史日期）
            current_price = get_current_or_open_price(symbol, settle_date)
            
            if current_price is None:
                # 如果沒有價格數據，使用限價
                current_price = limit_price
            
            # 強制結算（測試模式）
            if action == "BUY":
                portfolio.buy(symbol, quantity, current_price)
                print(f"  ✓ 已結算: {symbol} BUY {quantity} 股 @ ${current_price:.2f}")
            elif action == "SELL":
                portfolio.sell(symbol, quantity, current_price)
                print(f"  ✓ 已結算: {symbol} SELL {quantity} 股 @ ${current_price:.2f}")
            
            # 標記為已結算
            order_manager.mark_order_filled(order.get("order_id"), current_price, settle_date)
            settled_count += 1
            
        except Exception as e:
            print(f"  ✗ 結算失敗 {symbol} {action}: {e}")
    
    # 保存組合狀態
    portfolio_state = {
        "cash": portfolio.cash,
        "initial_value": portfolio.initial_value,
        "positions": {},
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    
    for symbol, pos in portfolio.positions.items():
        if isinstance(pos, dict):
            portfolio_state["positions"][symbol] = {
                "quantity": pos.get("quantity", 0),
                "avg_cost": pos.get("avg_cost", 0),
            }
    
    portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return settled_count

def simulate_october():
    """模擬10月份的所有交易日"""
    print_section("10月歷史數據模擬")
    print("每5分鐘模擬一天，共22個交易日")
    print("按 Ctrl+C 可隨時停止")
    print()
    
    logs_dir = init_october_simulation()
    
    # 生成10月份的所有交易日（週一到週五）
    start_date = date(2024, 10, 1)
    end_date = date(2024, 10, 31)
    
    trading_days = []
    current = start_date
    while current <= end_date:
        # 週一到週五
        if current.weekday() < 5:
            trading_days.append(current)
        current += timedelta(days=1)
    
    print(f"共 {len(trading_days)} 個交易日")
    print()
    
    total_orders = 0
    total_conversations = 0
    
    try:
        for day_num, trade_date in enumerate(trading_days, 1):
            trade_date_str = trade_date.isoformat()
            
            print("=" * 80)
            print(f"第 {day_num}/{len(trading_days)} 天 - {trade_date_str}")
            print("=" * 80)
            print()
            
            # 結算前一天的訂單（如果不是第一天）
            if day_num > 1:
                prev_date = trading_days[day_num - 2].isoformat()
                settled = settle_orders(prev_date, logs_dir)
                if settled > 0:
                    print(f"  ✓ 已結算 {settled} 筆訂單")
            
            # 執行當天交易循環
            print(f"執行交易循環 ({trade_date_str})...")
            try:
                # 使用时间窗口来获取数据（前后各10天，确保有数据）
                # yfinance 需要足够的时间窗口来获取数据
                window_start = (trade_date - timedelta(days=10)).isoformat()
                window_end = (trade_date + timedelta(days=1)).isoformat()  # 包含当天和第二天
                
                result = execute_daily_trade(
                    start=window_start,  # 使用时间窗口获取数据
                    end=window_end,      # 使用时间窗口获取数据
                    universe=["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]
                )
                
                if result:
                    orders = result.get("orders", [])
                    if orders:
                        total_orders += len(orders)
                        print(f"  ✓ 生成 {len(orders)} 筆訂單")
                        for order in orders:
                            print(f"    • {order.get('symbol')} {order.get('action')} x{order.get('quantity')} @ ${order.get('limit_price', 0):.2f}")
                    
                    print(f"  ✓ 交易循環完成")
                else:
                    print(f"  ⚠️  未生成訂單")
                
            except Exception as e:
                print(f"  ✗ 執行失敗: {e}")
                # 如果是数据获取错误，尝试跳过这一天
                if "No data" in str(e) or "YFPricesMissingError" in str(e):
                    print(f"  ⚠️  跳過此日（數據不可用）")
                    continue
                import traceback
                traceback.print_exc()
            
            # 讀取對話數量
            convo_file = logs_dir / "discussion_actions.jsonl"
            if convo_file.exists():
                with convo_file.open("r", encoding="utf-8") as f:
                    lines = [l for l in f if l.strip()]
                    total_conversations = len(lines)
            
            # 顯示當前狀態
            portfolio_file = logs_dir / "portfolio_state.json"
            if portfolio_file.exists():
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                    cash = state.get("cash", 0)
                    positions = state.get("positions", {})
                    pos_count = len(positions)
                    print(f"\n當前狀態: 現金 ${cash:.2f}, 持倉 {pos_count} 檔")
                    if positions:
                        for sym, pos in positions.items():
                            qty = pos.get("quantity", 0)
                            avg = pos.get("avg_cost", 0)
                            print(f"  • {sym}: {qty} 股 @ ${avg:.2f}")
            
            print()
            
            # 如果不是最後一天，等待5分鐘
            if day_num < len(trading_days):
                print(f"等待5分鐘後模擬下一天...")
                print(f"(按 Ctrl+C 停止)")
                print()
                time.sleep(300)  # 5分鐘 = 300秒
            else:
                print("所有交易日模擬完成！")
        
        # 結算最後一天的訂單
        if trading_days:
            last_date = trading_days[-1].isoformat()
            settled = settle_orders(last_date, logs_dir)
            if settled > 0:
                print(f"  ✓ 已結算最後 {settled} 筆訂單")
        
    except KeyboardInterrupt:
        print("\n\n模擬被中斷")
        print(f"已模擬 {day_num}/{len(trading_days)} 天")
    
    print_section("模擬總結")
    print(f"總交易日: {day_num if 'day_num' in locals() else 0}")
    print(f"總訂單數: {total_orders}")
    print(f"總對話數: {total_conversations}")
    print()
    print("前端可查看完整交易記錄和對話")

if __name__ == "__main__":
    try:
        simulate_october()
    except Exception as e:
        print(f"\n\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

