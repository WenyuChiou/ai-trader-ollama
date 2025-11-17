#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端功能是否正常工作
逐步验证各个改进点
"""
import sys
import io
import json
import requests
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

API_BASE = "http://127.0.0.1:8000"

def test_api_connection():
    """测试 1: API 连接"""
    print("=" * 60)
    print("测试 1: API 连接")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API 连接正常")
            return True
        else:
            print(f"❌ API 返回状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到 API: {e}")
        print("   提示: 请确保后端服务器正在运行")
        return False

def test_conversations_endpoint():
    """测试 2: 对话端点"""
    print("\n" + "=" * 60)
    print("测试 2: 对话端点")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE}/api/agents/conversations?limit=50", timeout=10)
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])
            print(f"✅ 成功获取 {len(conversations)} 条对话")
            return conversations
        else:
            print(f"❌ 端点返回状态码: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 错误: {e}")
        return []

def test_discussion_rounds(conversations):
    """测试 3: 多轮讨论 (Round 1, 2, 3)"""
    print("\n" + "=" * 60)
    print("测试 3: 多轮讨论 (Round 1, 2, 3)")
    print("=" * 60)
    
    rounds = {}
    for conv in conversations:
        if conv.get("type") == "discussion" and conv.get("round", 0) > 0:
            round_num = conv.get("round")
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(conv)
    
    if rounds:
        print(f"✅ 找到 {len(rounds)} 个轮次:")
        for round_num in sorted(rounds.keys()):
            print(f"   - Round {round_num}: {len(rounds[round_num])} 条对话")
        return True
    else:
        print("❌ 未找到多轮讨论数据")
        print("   提示: 需要执行一次完整的交易循环来生成多轮讨论")
        return False

def test_risk_analyst(conversations):
    """测试 4: RiskAnalyst 风险报告"""
    print("\n" + "=" * 60)
    print("测试 4: RiskAnalyst 风险报告")
    print("=" * 60)
    
    risk_entries = []
    for conv in conversations:
        agent = conv.get("agent", "")
        if agent == "RiskAnalyst" or "risk" in agent.lower():
            risk_entries.append(conv)
    
    if risk_entries:
        print(f"✅ 找到 {len(risk_entries)} 条 RiskAnalyst 记录")
        for i, entry in enumerate(risk_entries[:3], 1):  # 只显示前3条
            risk_report = entry.get("risk_report", {})
            risk_level = risk_report.get("overall_risk_level", "unknown")
            risk_score = risk_report.get("risk_score", 0)
            print(f"   记录 {i}:")
            print(f"      - 风险等级: {risk_level}")
            print(f"      - 风险评分: {risk_score}/10")
            print(f"      - 有 risk_report: {'是' if risk_report else '否'}")
        return True
    else:
        print("❌ 未找到 RiskAnalyst 记录")
        print("   提示: 需要执行一次完整的交易循环来生成风险报告")
        return False

def test_trader_agent(conversations):
    """测试 5: TraderAgent 决策（只显示 summary）"""
    print("\n" + "=" * 60)
    print("测试 5: TraderAgent 决策（只显示 summary）")
    print("=" * 60)
    
    trader_entries = []
    for conv in conversations:
        agent = conv.get("agent", "")
        if agent == "TraderAgent" or "trader" in agent.lower():
            trader_entries.append(conv)
    
    if trader_entries:
        print(f"✅ 找到 {len(trader_entries)} 条 TraderAgent 记录")
        for i, entry in enumerate(trader_entries[:3], 1):  # 只显示前3条
            content = entry.get("content", "")
            decision = entry.get("decision", {})
            summary = decision.get("summary", "") if decision else ""
            
            print(f"   记录 {i}:")
            print(f"      - content 长度: {len(content)} 字符")
            print(f"      - 有 decision 对象: {'是' if decision else '否'}")
            if decision:
                buy_orders = decision.get("buy_orders", [])
                sell_orders = decision.get("sell_orders", [])
                print(f"      - 买入订单数: {len(buy_orders)}")
                print(f"      - 卖出订单数: {len(sell_orders)}")
            
            # 检查 content 是否只包含 summary（不包含详细订单信息）
            has_order_details = "buy_orders" in content or "sell_orders" in content or "quantity" in content.lower()
            if has_order_details:
                print(f"      ⚠️  content 包含订单详情（应该只显示 summary）")
            else:
                print(f"      ✅ content 只包含摘要（符合要求）")
            
            # 显示 content 的前 200 字符
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"      - content 预览: {preview}")
        return True
    else:
        print("❌ 未找到 TraderAgent 记录")
        print("   提示: 需要执行一次完整的交易循环来生成交易决策")
        return False

def test_data_file():
    """测试 6: 检查数据文件"""
    print("\n" + "=" * 60)
    print("测试 6: 检查数据文件")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent.parent / "backend"
    project_root = backend_dir.parent
    logs_dir = project_root / "data" / "logs"
    jsonl_file = logs_dir / "discussion_actions.jsonl"
    
    if jsonl_file.exists():
        print(f"✅ 数据文件存在: {jsonl_file}")
        
        # 读取最后几行
        with jsonl_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"   总行数: {len(lines)}")
        
        # 分析最后 20 行
        stats = {
            "RiskAnalyst": 0,
            "TraderAgent": 0,
            "DiscussionRound": 0,
            "total": 0
        }
        
        for line in lines[-20:]:
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", "")
                round_num = entry.get("round", 0)
                
                if agent == "RiskAnalyst":
                    stats["RiskAnalyst"] += 1
                elif agent == "TraderAgent":
                    stats["TraderAgent"] += 1
                elif round_num > 0:
                    stats["DiscussionRound"] += 1
                stats["total"] += 1
            except:
                pass
        
        print(f"   最后 20 行统计:")
        print(f"      - RiskAnalyst: {stats['RiskAnalyst']}")
        print(f"      - TraderAgent: {stats['TraderAgent']}")
        print(f"      - DiscussionRound: {stats['DiscussionRound']}")
        print(f"      - 总计: {stats['total']}")
        
        return True
    else:
        print(f"❌ 数据文件不存在: {jsonl_file}")
        return False

def main():
    print("\n" + "=" * 60)
    print("前端功能测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 测试 1: API 连接
    if not test_api_connection():
        print("\n❌ API 连接失败，无法继续测试")
        print("   请先启动后端服务器:")
        print("   cd backend")
        print("   uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    # 测试 2: 对话端点
    conversations = test_conversations_endpoint()
    if not conversations:
        print("\n❌ 无法获取对话数据，无法继续测试")
        sys.exit(1)
    
    # 测试 3-5: 功能测试
    results.append(("多轮讨论", test_discussion_rounds(conversations)))
    results.append(("RiskAnalyst", test_risk_analyst(conversations)))
    results.append(("TraderAgent", test_trader_agent(conversations)))
    
    # 测试 6: 数据文件
    results.append(("数据文件", test_data_file()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ 所有功能测试通过！")
        print("   前端应该能正确显示所有改进功能。")
    else:
        print("\n⚠️  部分功能测试失败。")
        print("   如果某些功能未通过，可能需要:")
        print("   1. 执行一次完整的交易循环")
        print("   2. 检查后端是否正确写入数据")
        print("   3. 刷新前端页面")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

