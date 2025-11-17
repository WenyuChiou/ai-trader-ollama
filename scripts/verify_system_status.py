#!/usr/bin/env python3
"""
系统状态验证脚本
检查交易周期、订单执行、数据记录等是否正常
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import requests
from pathlib import Path
from datetime import datetime

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def check_trading_cycle_execution():
    """检查交易周期执行情况"""
    print("\n" + "="*80)
    print("📊 检查交易周期执行")
    print("="*80)
    
    logs_dir = Path("data/logs")
    discussion_file = logs_dir / "discussion_actions.jsonl"
    
    if not discussion_file.exists():
        print_warning("Discussion actions 文件不存在")
        return False
    
    # 读取今天的记录
    today = datetime.now().strftime("%Y-%m-%d")
    today_entries = []
    
    try:
        with open(discussion_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line.strip())
                        timestamp = entry.get("timestamp", "")
                        if today in timestamp:
                            today_entries.append(entry)
                    except:
                        pass
    except Exception as e:
        print_error(f"读取文件失败: {e}")
        return False
    
    if not today_entries:
        print_warning(f"今天 ({today}) 没有交易周期记录")
        return False
    
    print_success(f"找到 {len(today_entries)} 条今天的记录")
    
    # 检查关键组件（支持多种字段名）
    components = {
        "MarketAnalyst": False,
        "Market Analyst": False,
        "TechnicalAnalyst": False,
        "Technical Analyst": False,
        "FundamentalAnalyst": False,
        "Fundamental Analyst": False,
        "SentimentAnalyst": False,
        "Sentiment Analyst": False,
        "DiscussionCoordinator": False,
        "Discussion Coordinator": False,
        "RiskAnalyst": False,
        "Risk Analyst": False,
        "TraderAgent": False,
        "Trader Agent": False,
    }
    
    for entry in today_entries:
        analyst = entry.get("analyst", "")
        entry_type = entry.get("type", "")
        
        # 检查 analyst 字段
        if analyst in components:
            components[analyst] = True
        
        # 检查 type 字段（有些记录可能用 type）
        if entry_type in ["market", "technical", "fundamental", "sentiment", "discussion", "risk", "trader"]:
            if entry_type == "market":
                components["MarketAnalyst"] = True
            elif entry_type == "technical":
                components["TechnicalAnalyst"] = True
            elif entry_type == "fundamental":
                components["FundamentalAnalyst"] = True
            elif entry_type == "sentiment":
                components["SentimentAnalyst"] = True
            elif entry_type == "discussion":
                components["DiscussionCoordinator"] = True
            elif entry_type == "risk":
                components["RiskAnalyst"] = True
            elif entry_type == "trader":
                components["TraderAgent"] = True
    
    print_info("组件执行情况:")
    all_ok = True
    
    # 合并相同组件的多个名称
    component_status = {
        "Market Analyst": components.get("MarketAnalyst") or components.get("Market Analyst"),
        "Technical Analyst": components.get("TechnicalAnalyst") or components.get("Technical Analyst"),
        "Fundamental Analyst": components.get("FundamentalAnalyst") or components.get("Fundamental Analyst"),
        "Sentiment Analyst": components.get("SentimentAnalyst") or components.get("Sentiment Analyst"),
        "Discussion Coordinator": components.get("DiscussionCoordinator") or components.get("Discussion Coordinator"),
        "Risk Analyst": components.get("RiskAnalyst") or components.get("Risk Analyst"),
        "Trader Agent": components.get("TraderAgent") or components.get("Trader Agent"),
    }
    
    for component, executed in component_status.items():
        if executed:
            print_success(f"  {component}: 已执行")
        else:
            print_warning(f"  {component}: 未执行")
            all_ok = False
    
    return all_ok

def check_orders_execution():
    """检查订单执行情况"""
    print("\n" + "="*80)
    print("📝 检查订单执行")
    print("="*80)
    
    logs_dir = Path("data/logs")
    filled_file = logs_dir / "filled_orders.jsonl"
    
    if not filled_file.exists():
        print_warning("Filled orders 文件不存在")
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = []
    
    try:
        with open(filled_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line.strip())
                        order_date = order.get("placed_at", "").split("T")[0] if order.get("placed_at") else ""
                        if today in order_date or today in str(order):
                            today_orders.append(order)
                    except:
                        pass
    except Exception as e:
        print_error(f"读取文件失败: {e}")
        return False
    
    if today_orders:
        print_success(f"找到 {len(today_orders)} 个今天的订单")
        buy_count = sum(1 for o in today_orders if o.get("action") == "BUY")
        sell_count = sum(1 for o in today_orders if o.get("action") == "SELL")
        print_info(f"  BUY: {buy_count}, SELL: {sell_count}")
        return True
    else:
        print_warning(f"今天 ({today}) 没有订单记录")
        return False

def check_portfolio_state():
    """检查组合状态"""
    print("\n" + "="*80)
    print("💼 检查组合状态")
    print("="*80)
    
    logs_dir = Path("data/logs")
    portfolio_file = logs_dir / "portfolio_state.json"
    
    if not portfolio_file.exists():
        print_warning("Portfolio state 文件不存在")
        return False
    
    try:
        with open(portfolio_file, 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
        
        cash = portfolio.get("cash", 0)
        positions = portfolio.get("positions", {})
        total_value = portfolio.get("total_value", cash)
        
        print_success(f"组合状态:")
        print_info(f"  现金: ${cash:,.2f}")
        print_info(f"  持仓数量: {len(positions)}")
        print_info(f"  总价值: ${total_value:,.2f}")
        
        if positions:
            print_info("  持仓详情:")
            for symbol, pos in list(positions.items())[:5]:
                qty = pos.get("quantity", 0)
                avg_cost = pos.get("avg_cost", 0)
                print_info(f"    {symbol}: {qty} shares @ ${avg_cost:.2f}")
        
        return True
    except Exception as e:
        print_error(f"读取文件失败: {e}")
        return False

def check_memory_records():
    """检查 Memory 记录"""
    print("\n" + "="*80)
    print("💾 检查 Memory 记录")
    print("="*80)
    
    logs_dir = Path("data/logs")
    memory_dir = logs_dir / "memory" / "daily"
    
    if not memory_dir.exists():
        print_warning("Memory 目录不存在")
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = memory_dir / f"{today}.json"
    
    if not memory_file.exists():
        print_warning(f"今天的 Memory 文件不存在: {memory_file}")
        return False
    
    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
        
        required_fields = ["date", "market_view", "market_analysis", "discussion", "risk_report", "decision", "portfolio_snapshot"]
        missing_fields = [f for f in required_fields if f not in memory]
        
        if not missing_fields:
            print_success("Memory 文件结构完整")
            print_info(f"  日期: {memory.get('date', 'N/A')}")
            print_info(f"  决策: {memory.get('decision', {}).get('action', 'N/A')}")
            return True
        else:
            print_warning(f"Memory 文件缺少字段: {', '.join(missing_fields)}")
            return False
    except Exception as e:
        print_error(f"读取文件失败: {e}")
        return False

def check_api_status():
    """检查 API 状态"""
    print("\n" + "="*80)
    print("🌐 检查 API 状态")
    print("="*80)
    
    api_base = "http://127.0.0.1:8000"
    
    try:
        response = requests.get(f"{api_base}/api/health", timeout=5)
        if response.status_code == 200:
            print_success("API 服务器运行正常")
            return True
        else:
            print_error(f"API 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"无法连接到 API: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔬 AI-Trader Ollama 系统状态验证")
    print("="*80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 检查 API 状态
    results.append(("API 状态", check_api_status()))
    
    # 2. 检查交易周期执行
    results.append(("交易周期执行", check_trading_cycle_execution()))
    
    # 3. 检查订单执行
    results.append(("订单执行", check_orders_execution()))
    
    # 4. 检查组合状态
    results.append(("组合状态", check_portfolio_state()))
    
    # 5. 检查 Memory 记录
    results.append(("Memory 记录", check_memory_records()))
    
    # 总结
    print("\n" + "="*80)
    print("📊 验证结果总结")
    print("="*80)
    
    all_passed = True
    for name, result in results:
        if result:
            print_success(f"{name}: 正常")
        else:
            print_error(f"{name}: 异常")
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print_success("所有检查通过！系统运行正常。")
    else:
        print_warning("部分检查未通过，请查看上面的详细信息。")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

