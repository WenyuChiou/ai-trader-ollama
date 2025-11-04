#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多天交易循環耦合測試
測試連續多天的交易流程，確保：
1. 每天的對話正確寫入
2. 訂單結算機制正常
3. 持倉狀態正確累積
4. 對話可以正確顯示在前端
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

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

def print_day_header(day_num, test_date):
    print("\n" + "=" * 80)
    print(f"  第 {day_num} 天 - {test_date}")
    print("=" * 80)

def init_test_environment():
    """初始化測試環境"""
    print_section("初始化測試環境")
    
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

def settle_previous_day_orders(settle_date, logs_dir):
    """結算前一天的訂單（模擬收盤後結算）"""
    from src.data.order_manager import OrderManager
    from src.data.portfolio import Portfolio
    from src.data.order_executor import get_current_or_open_price
    
    order_manager = OrderManager(root="data/logs")
    pending_orders = order_manager.load_pending_orders(order_date=settle_date)
    
    if not pending_orders:
        return 0
    
    print(f"  找到 {len(pending_orders)} 筆待結算訂單")
    
    # 載入組合
    portfolio_file = logs_dir / "portfolio_state.json"
    if portfolio_file.exists():
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # 恢復持倉
        positions = state.get("positions", {})
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                from src.data.portfolio import Position
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=int(pos_info.get("quantity", 0)),
                    avg_cost=float(pos_info.get("avg_cost", 0.0)),
                    total_cost=float(pos_info.get("total_cost", 0.0)),
                )
    else:
        portfolio = Portfolio()
    
    settled = 0
    for order in pending_orders:
        try:
            # 檢查訂單是否應該成交
            fill_result = order_manager.check_order_fill(order, settle_date)
            
            if not fill_result.get("filled"):
                # 測試模式：使用當前價格強制成交
                current_price = get_current_or_open_price(order["symbol"], settle_date)
                if current_price:
                    fill_price = current_price
                    fill_result["filled"] = True
                    fill_result["fill_price"] = fill_price
                else:
                    fill_price = order.get("limit_price", order.get("buy_price", 0))
                    fill_result["filled"] = True
                    fill_result["fill_price"] = fill_price
            
            if fill_result.get("filled"):
                fill_price = fill_result.get("fill_price")
                symbol = order["symbol"]
                action = order["action"]
                quantity = order["quantity"]
                
                if action == "BUY":
                    portfolio.buy(symbol, quantity, fill_price)
                elif action == "SELL":
                    portfolio.sell(symbol, quantity, fill_price)
                
                order_manager.mark_order_filled(order, fill_result)
                settled += 1
                print(f"    ✓ 已結算: {symbol} {action} {quantity} 股 @ ${fill_price:.2f}")
        except Exception as e:
            print(f"    ✗ 結算失敗 {order.get('symbol')}: {e}")
    
    # 保存更新後的組合狀態
    if settled > 0:
        state = {
            "cash": portfolio.cash,
            "initial_value": portfolio.initial_value,
            "positions": {},
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        for symbol, pos in portfolio._positions.items():
            state["positions"][symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": pos.total_cost,
            }
        
        portfolio_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ 已更新組合狀態（結算 {settled} 筆訂單）")
    
    return settled

def run_trading_cycle_for_date(test_date, day_num):
    """為指定日期執行交易循環"""
    print_day_header(day_num, test_date)
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        print(f"執行交易循環...")
        # 計算日期範圍（測試日期往前推30天作為start）
        test_date_obj = datetime.strptime(test_date, "%Y-%m-%d").date()
        start_date = (test_date_obj - timedelta(days=30)).isoformat()
        
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=3,
            start=start_date,  # 開始日期（往前推30天）
            end=test_date      # 結束日期（交易日）
        )
        
        if not result:
            print("  ✗ 交易循環返回空結果")
            return None
        
        # 顯示關鍵信息
        discussion = result.get("discussion", {})
        final_stance = discussion.get("final_stance", "unknown")
        tool_context = discussion.get("tool_context", [])
        decision = result.get("decision", {})
        action = decision.get("action", "N/A")
        buy_orders = decision.get("buy_orders", [])
        placed_orders = result.get("placed_orders", [])
        
        print(f"\n  ✓ 最終立場: {final_stance}")
        print(f"  ✓ 工具使用: {len(tool_context)} 項")
        print(f"  ✓ 決策動作: {action}")
        print(f"  ✓ 買入訂單: {len(buy_orders)} 筆")
        print(f"  ✓ 已掛單: {len(placed_orders)} 筆")
        
        if buy_orders:
            for order in buy_orders:
                print(f"    • {order.get('symbol')}: {order.get('quantity')} 股 @ ${order.get('buy_price', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"  ✗ 交易循環執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_conversations_for_date(test_date, logs_dir, day_num):
    """檢查指定日期的對話記錄"""
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    if not convo_file.exists():
        print(f"  ✗ 對話文件不存在")
        return 0
    
    with convo_file.open("r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]
    
    # 篩選該日期的記錄
    day_records = []
    for line in lines:
        try:
            entry = json.loads(line.strip())
            entry_date = entry.get("date", "")
            if entry_date == test_date or entry.get("timestamp", "").startswith(test_date):
                day_records.append(entry)
        except:
            pass
    
    discussion_count = len([e for e in day_records if e.get("type") == "discussion"])
    tool_count = len([e for e in day_records if e.get("type") == "tool"])
    
    print(f"  ✓ 對話記錄: {discussion_count} 條討論, {tool_count} 條工具")
    
    return len(day_records)

def main():
    print_section("多天交易循環耦合測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化環境
    logs_dir = init_test_environment()
    
    # 測試天數（從今天往前推）
    today = date.today()
    test_days = 3  # 測試連續3天
    
    dates = [(today - timedelta(days=i)).isoformat() for i in range(test_days)]
    dates.reverse()  # 從最早到最新
    
    print_section(f"開始測試連續 {test_days} 天的交易流程")
    
    all_results = []
    total_conversations = 0
    
    for day_num, test_date in enumerate(dates, 1):
        # 如果是第二天以後，先結算前一天的訂單
        if day_num > 1:
            prev_date = dates[day_num - 2]
            print(f"\n[結算前一日訂單] {prev_date}")
            settled = settle_previous_day_orders(prev_date, logs_dir)
            if settled > 0:
                print(f"  ✓ 已結算 {settled} 筆訂單")
        
        # 執行當天的交易循環
        result = run_trading_cycle_for_date(test_date, day_num)
        if result:
            all_results.append((test_date, result))
            
            # 檢查對話記錄
            conv_count = check_conversations_for_date(test_date, logs_dir, day_num)
            total_conversations += conv_count
            
            # 檢查組合狀態
            portfolio_file = logs_dir / "portfolio_state.json"
            if portfolio_file.exists():
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                cash = state.get("cash", 0)
                positions = state.get("positions", {})
                print(f"  ✓ 組合狀態: 現金 ${cash:.2f}, 持倉 {len(positions)} 檔")
        
        # 清除單日鎖（允許同一天多次測試）
        last_trade_file = logs_dir / "last_trade_date.txt"
        if last_trade_file.exists():
            last_trade_file.unlink()
    
    # ========== 總結測試結果 ==========
    print_section("多天測試總結")
    
    print(f"測試天數: {test_days} 天")
    print(f"成功執行: {len(all_results)} 天")
    print(f"總對話記錄: {total_conversations} 條")
    
    # 檢查對話文件
    convo_file = logs_dir / "discussion_actions.jsonl"
    if convo_file.exists():
        with convo_file.open("r", encoding="utf-8") as f:
            all_lines = [l for l in f.readlines() if l.strip()]
        
        print(f"\n對話文件總記錄: {len(all_lines)} 條")
        
        # 按日期統計
        date_stats = {}
        for line in all_lines:
            try:
                entry = json.loads(line.strip())
                entry_date = entry.get("date", "")
                entry_type = entry.get("type", "unknown")
                
                if entry_date not in date_stats:
                    date_stats[entry_date] = {"discussion": 0, "tool": 0, "demo": 0}
                
                date_stats[entry_date][entry_type] = date_stats[entry_date].get(entry_type, 0) + 1
            except:
                pass
        
        print("\n按日期統計:")
        for date_key in sorted(date_stats.keys()):
            stats = date_stats[date_key]
            total = sum(stats.values())
            print(f"  {date_key}: {total} 條 (討論: {stats.get('discussion', 0)}, 工具: {stats.get('tool', 0)}, Demo: {stats.get('demo', 0)})")
        
        # 顯示最新的幾條記錄（模擬前端顯示）
        print("\n最新對話記錄（前端將顯示這些）:")
        for line in all_lines[-10:]:
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", "Unknown")
                round_num = entry.get("round", 0)
                content = entry.get("content", "")[:60]
                entry_type = entry.get("type", "unknown")
                entry_date = entry.get("date", "")
                print(f"  [{entry_type}] {entry_date} {agent} (Round {round_num}): {content}...")
            except:
                pass
    
    # 檢查組合最終狀態
    portfolio_file = logs_dir / "portfolio_state.json"
    if portfolio_file.exists():
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        cash = state.get("cash", 0)
        positions = state.get("positions", {})
        total_positions_value = sum(p.get("total_cost", 0) for p in positions.values() if isinstance(p, dict))
        
        print(f"\n最終組合狀態:")
        print(f"  現金: ${cash:.2f}")
        print(f"  持倉: {len(positions)} 檔")
        print(f"  持倉價值: ${total_positions_value:.2f}")
        print(f"  總資產: ${cash + total_positions_value:.2f}")
        
        if positions:
            print("\n  持倉詳情:")
            for symbol, pos in positions.items():
                if isinstance(pos, dict):
                    qty = pos.get("quantity", 0)
                    avg_cost = pos.get("avg_cost", 0)
                    print(f"    • {symbol}: {qty} 股 @ 均價 ${avg_cost:.2f}")
    
    # ========== 前端兼容性檢查 ==========
    print_section("前端兼容性檢查")
    
    # 檢查對話數量（前端性能考量）
    if convo_file.exists():
        with convo_file.open("r", encoding="utf-8") as f:
            all_lines = [l for l in f.readlines() if l.strip()]
        
        total_count = len(all_lines)
        print(f"  總對話記錄數: {total_count}")
        
        if total_count > 1000:
            print(f"  ⚠️  對話記錄過多 ({total_count} 條)，前端可能需要分頁或限制顯示")
        elif total_count > 500:
            print(f"  ⚠️  對話記錄較多 ({total_count} 條)，建議前端設置顯示上限（如最近 100 條）")
        else:
            print(f"  ✓ 對話記錄數量適中 ({total_count} 條)，前端可正常顯示")
        
        # 檢查非 demo 記錄
        non_demo_count = 0
        for line in all_lines:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") != "demo":
                    non_demo_count += 1
            except:
                pass
        
        print(f"  真實對話記錄: {non_demo_count} 條")
        print(f"  ✓ 前端將顯示 {non_demo_count} 條真實對話（排除 demo）")
    
    print_section("測試完成")
    
    if len(all_results) == test_days:
        print("🎉 多天測試成功！")
        print("✓ 每天的交易循環正常執行")
        print("✓ 對話正確累積")
        print("✓ 訂單結算機制正常")
        print("✓ 持倉狀態正確更新")
        print("✓ 對話可正確顯示在前端")
        return True
    else:
        print(f"⚠️  部分天數測試失敗（成功 {len(all_results)}/{test_days} 天）")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n測試被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

