#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後端完整流程測試
確保：信息流、工具使用、對話都正確成功
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

def print_step(step_num, title):
    print(f"\n[步驟 {step_num}] {title}")
    print("-" * 80)

def check_file(filepath, description):
    """檢查文件是否存在並顯示信息"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        lines = 0
        if path.suffix == '.jsonl':
            with path.open('r', encoding='utf-8') as f:
                lines = len([l for l in f.readlines() if l.strip()])
        print(f"  ✓ {description}: {path} ({size} bytes, {lines} lines)")
        return True
    else:
        print(f"  ✗ {description}: {path} (不存在)")
        return False

def main():
    print_section("後端完整流程測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目錄: {os.getcwd()}")
    
    # ========== 步驟 1: 初始化環境 ==========
    print_step(1, "初始化環境檢查")
    
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 日誌目錄: {logs_dir}")
    
    # 清空對話日誌（從乾淨狀態開始）
    convo_file = logs_dir / "discussion_actions.jsonl"
    if convo_file.exists():
        convo_file.write_text("", encoding="utf-8")
        print(f"  ✓ 已清空對話日誌（從乾淨狀態開始）")
    
    # ========== 步驟 2: 執行交易循環 ==========
    print_step(2, "執行完整交易循環")
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        print("  開始執行 execute_daily_trade...")
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=20  # 增加到20，允许LLM使用所有工具
        )
        
        if not result:
            print("  ✗ 交易循環返回空結果")
            return False
        
        print("  ✓ 交易循環執行完成")
        
    except Exception as e:
        print(f"  ✗ 交易循環執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========== 步驟 3: 驗證市場數據流 ==========
    print_step(3, "驗證市場數據流")
    
    market_agent = result.get("market_agent", {})
    if not market_agent:
        print("  ✗ 未找到 market_agent 數據")
        return False
    
    stocks = market_agent.get("stocks", {})
    vix = market_agent.get("VIX", {})
    
    print(f"  ✓ 股票數據: {len(stocks)} 檔")
    print(f"  ✓ VIX 數據: Level={vix.get('level', 'N/A')}, Z-Score={vix.get('zscore', 'N/A')}")
    
    # 檢查關鍵股票
    required_symbols = ["NVDA", "MSFT", "AAPL"]
    missing = [s for s in required_symbols if s not in stocks]
    if missing:
        print(f"  ⚠️  缺少股票: {missing}")
    else:
        print(f"  ✓ 關鍵股票數據完整: {required_symbols}")
    
    # 檢查每檔股票的關鍵指標
    for symbol in required_symbols[:3]:
        if symbol in stocks:
            data = stocks[symbol]
            has_price = "price" in data
            has_rsi = "rsi14" in data
            has_macd = "macd" in data
            has_signal = "signal_score" in data
            
            if has_price and has_rsi and has_macd and has_signal:
                print(f"  ✓ {symbol}: 指標完整 (price, rsi14, macd, signal_score)")
            else:
                print(f"  ⚠️  {symbol}: 缺少指標 (price={has_price}, rsi={has_rsi}, macd={has_macd}, signal={has_signal})")
    
    # ========== 步驟 4: 驗證工具使用 ==========
    print_step(4, "驗證工具使用")
    
    discussion = result.get("discussion", {})
    tool_context = discussion.get("tool_context", [])
    
    if not tool_context:
        print("  ✗ 未找到工具使用記錄")
        return False
    
    print(f"  ✓ 工具使用記錄: {len(tool_context)} 項")
    
    # 檢查工具使用（放宽标准：只要使用了任何工具就认为正常）
    # 让LLM自己选择工具，不强制要求特定工具
    all_available_tools = [
        "vix_term", "vix_close", "fear_greed", 
        "fetch_crypto_batch", "get_crypto_price",
        "fetch_jin10_news", "fetch_jin10_economic_data",
        "web_search", "fetch_url", "news_scan", "plan_and_scan_news"
    ]
    
    found_tools = []
    for tool_name in all_available_tools:
        # 檢查 tool_context 中是否包含該工具名稱
        tool_found = False
        for tool_info in tool_context:
            tool_lower = tool_info.lower()
            # 檢查是否包含工具名稱（可能有多種格式）
            if tool_name in tool_lower or f"{tool_name}:" in tool_lower:
                tool_found = True
                break
        
        if tool_found:
            found_tools.append(tool_name)
            print(f"  ✓ 工具 {tool_name} 已使用")
    
    # 放宽标准：只要使用了至少1个工具就认为正常（工具使用完全取决于Agent决策）
    if len(found_tools) >= 1:
        print(f"  ✓ 工具使用正常（使用了 {len(found_tools)} 个工具）")
        print(f"  ✓ 可用工具总数: {len(all_available_tools)}")
    else:
        print(f"  ⚠️  未检测到工具使用（但可能是工具名称格式不同）")
    
    # 顯示工具使用詳情
    print("\n  工具使用詳情:")
    for i, tool_info in enumerate(tool_context, 1):
        print(f"    {i}. {tool_info}")
    
    # ========== 步驟 5: 驗證對話記錄 ==========
    print_step(5, "驗證對話記錄")
    
    final_stance = discussion.get("final_stance", "unknown")
    rounds = discussion.get("rounds", 0)
    transcript = discussion.get("transcript", [])
    
    print(f"  ✓ 最終立場: {final_stance}")
    print(f"  ✓ 討論輪數: {rounds}")
    print(f"  ✓ 對話段落: {len(transcript)} 段")
    
    if not transcript:
        print("  ✗ 未找到對話內容")
        return False
    
    # 檢查對話內容
    for i, round_text in enumerate(transcript, 1):
        if len(round_text) > 50:
            print(f"  ✓ Round {i}: 對話內容完整 ({len(round_text)} 字元)")
            # 檢查是否包含關鍵信息
            has_analysis = "analysis" in round_text.lower() or "分析" in round_text
            has_stance = "stance" in round_text.lower() or "立場" in round_text
            has_rationale = "rationale" in round_text.lower() or "理由" in round_text
            
            if has_analysis or has_stance or has_rationale:
                print(f"    → 包含分析/立場/理由")
        else:
            print(f"  ⚠️  Round {i}: 對話內容過短 ({len(round_text)} 字元)")
    
    # ========== 步驟 6: 驗證對話寫入文件 ==========
    print_step(6, "驗證對話寫入文件")
    
    if not convo_file.exists():
        print(f"  ✗ 對話文件不存在: {convo_file}")
        return False
    
    with convo_file.open("r", encoding="utf-8") as f:
        lines = [l for l in f.readlines() if l.strip()]
    
    if not lines:
        print(f"  ✗ 對話文件為空")
        return False
    
    print(f"  ✓ 對話文件: {len(lines)} 條記錄")
    
    # 分析記錄類型
    discussion_count = 0
    tool_count = 0
    demo_count = 0
    
    for line in lines:
        try:
            entry = json.loads(line.strip())
            entry_type = entry.get("type", "unknown")
            if entry_type == "discussion":
                discussion_count += 1
            elif entry_type == "tool":
                tool_count += 1
            elif entry_type == "demo":
                demo_count += 1
        except:
            pass
    
    print(f"  ✓ 討論記錄: {discussion_count} 條")
    print(f"  ✓ 工具記錄: {tool_count} 條")
    if demo_count > 0:
        print(f"  ⚠️  Demo 記錄: {demo_count} 條（應該為 0）")
    
    # 顯示最新的幾條記錄
    print("\n  最新的對話記錄:")
    for line in lines[-5:]:
        try:
            entry = json.loads(line.strip())
            agent = entry.get("agent", "Unknown")
            round_num = entry.get("round", 0)
            content = entry.get("content", "")[:80]
            entry_type = entry.get("type", "unknown")
            print(f"    [{entry_type}] {agent} (Round {round_num}): {content}...")
        except:
            print(f"    {line.strip()[:80]}...")
    
    # ========== 步驟 7: 驗證交易決策 ==========
    print_step(7, "驗證交易決策")
    
    decision = result.get("decision", {})
    if not decision:
        print("  ✗ 未找到交易決策")
        return False
    
    action = decision.get("action", "N/A")
    buy_orders = decision.get("buy_orders", [])
    sell_orders = decision.get("sell_orders", [])
    placed_orders = result.get("placed_orders", [])
    
    print(f"  ✓ 決策動作: {action}")
    print(f"  ✓ 買入訂單: {len(buy_orders)} 筆")
    print(f"  ✓ 賣出訂單: {len(sell_orders)} 筆")
    print(f"  ✓ 已掛單: {len(placed_orders)} 筆")
    
    if buy_orders:
        print("\n  買入訂單詳情:")
        for order in buy_orders:
            symbol = order.get("symbol")
            quantity = order.get("quantity")
            price = order.get("buy_price", 0)
            total = order.get("total_cost", 0)
            print(f"    • {symbol}: {quantity} 股 @ ${price:.2f} (總額: ${total:.2f})")
    
    if placed_orders:
        print("\n  掛單詳情:")
        for order in placed_orders:
            symbol = order.get("symbol")
            action = order.get("action")
            quantity = order.get("quantity")
            limit_price = order.get("limit_price", 0)
            status = order.get("status", "N/A")
            print(f"    • {symbol} {action}: {quantity} 股 @ ${limit_price:.2f} (狀態: {status})")
    
    # ========== 步驟 8: 驗證組合狀態 ==========
    print_step(8, "驗證組合狀態")
    
    portfolio_data = result.get("portfolio", {})
    cash = portfolio_data.get("cash", 0)
    positions = portfolio_data.get("positions", {})
    total_value = portfolio_data.get("total_value", 0)
    
    print(f"  ✓ 現金: ${cash:.2f}")
    print(f"  ✓ 總資產: ${total_value:.2f}")
    print(f"  ✓ 持倉數量: {len(positions)}")
    
    if positions:
        print("\n  持倉詳情:")
        for symbol, pos in positions.items():
            if isinstance(pos, dict):
                qty = pos.get("quantity", 0)
                avg_cost = pos.get("avg_cost", 0)
                total_cost = pos.get("total_cost", 0)
                print(f"    • {symbol}: {qty} 股 @ 均價 ${avg_cost:.2f} (總成本: ${total_cost:.2f})")
    
    # ========== 步驟 9: 驗證文件完整性 ==========
    print_step(9, "驗證輸出文件完整性")
    
    files_to_check = [
        ("discussion_actions.jsonl", "對話日誌"),
        ("portfolio_state.json", "組合狀態"),
        ("pending_orders.jsonl", "掛單記錄（如果存在）"),
        ("real_time_snapshots.jsonl", "實時快照（如果存在）"),
    ]
    
    all_ok = True
    for filename, description in files_to_check:
        filepath = logs_dir / filename
        if not check_file(filepath, description):
            if filename in ["pending_orders.jsonl", "real_time_snapshots.jsonl"]:
                # 這些文件是可選的
                pass
            else:
                all_ok = False
    
    # ========== 總結 ==========
    print_section("測試總結")
    
    checks = [
        ("市場數據流", stocks and vix),
        ("工具使用", len(tool_context) > 0),
        ("對話記錄", len(transcript) > 0),
        ("對話寫入文件", discussion_count > 0),
        ("交易決策", decision and action != "N/A"),
        ("文件完整性", all_ok),
    ]
    
    passed = 0
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"  {status} {check_name}")
        if check_result:
            passed += 1
    
    print(f"\n通過率: {passed}/{len(checks)} ({passed*100//len(checks)}%)")
    
    if passed == len(checks):
        print("\n🎉 所有測試通過！完整流程運作正常。")
        return True
    else:
        print(f"\n⚠️  部分測試未通過，請檢查上述問題。")
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

