#!/usr/bin/env python3
"""
系统功能检查脚本
检查前后端的关键功能，确认 agent 交流、memory 记录等是否正常
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

def check_backend_api():
    """检查后端 API 功能"""
    print("\n" + "="*80)
    print("🔍 检查后端 API 功能")
    print("="*80)
    
    api_base = "http://127.0.0.1:8000"
    checks = []
    
    # 1. Health check
    try:
        response = requests.get(f"{api_base}/api/health", timeout=5)
        if response.status_code == 200:
            print_success("API Health Check: 正常")
            checks.append(True)
        else:
            print_error(f"API Health Check: 状态码 {response.status_code}")
            checks.append(False)
    except Exception as e:
        print_error(f"API Health Check: 无法连接 ({e})")
        checks.append(False)
        return False
    
    # 2. System Info
    try:
        response = requests.get(f"{api_base}/api/system/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print_success("System Info API: 正常")
                print_info(f"  - Position Limit Mode: {data.get('position_limits', {}).get('mode', 'N/A')}")
                print_info(f"  - Position Limits Enabled: {data.get('position_limits', {}).get('enabled', False)}")
                checks.append(True)
            else:
                print_error("System Info API: 返回错误")
                checks.append(False)
        else:
            print_error(f"System Info API: 状态码 {response.status_code}")
            checks.append(False)
    except Exception as e:
        print_error(f"System Info API: 错误 ({e})")
        checks.append(False)
    
    # 3. Conversations API
    try:
        response = requests.get(f"{api_base}/api/agents/conversations?limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                conversations = data.get("conversations", [])
                print_success(f"Conversations API: 正常 (找到 {len(conversations)} 条记录)")
                checks.append(True)
            else:
                print_warning("Conversations API: 返回错误（可能没有对话记录）")
                checks.append(True)  # 不算错误，可能只是没有数据
        else:
            print_error(f"Conversations API: 状态码 {response.status_code}")
            checks.append(False)
    except Exception as e:
        print_error(f"Conversations API: 错误 ({e})")
        checks.append(False)
    
    # 4. Portfolio API
    try:
        response = requests.get(f"{api_base}/api/portfolio/real-time", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print_success("Portfolio API: 正常")
                checks.append(True)
            else:
                print_error("Portfolio API: 返回错误")
                checks.append(False)
        else:
            print_error(f"Portfolio API: 状态码 {response.status_code}")
            checks.append(False)
    except Exception as e:
        print_error(f"Portfolio API: 错误 ({e})")
        checks.append(False)
    
    return all(checks)

def check_agent_communication():
    """检查 Agent 交流机制"""
    print("\n" + "="*80)
    print("🤖 检查 Agent 交流机制")
    print("="*80)
    
    logs_dir = Path("data/logs")
    discussion_file = logs_dir / "discussion_actions.jsonl"
    
    checks = []
    
    # 1. 检查 discussion_actions.jsonl 文件
    if discussion_file.exists():
        print_success(f"Discussion Actions 文件存在: {discussion_file}")
        
        # 读取最近几条记录
        try:
            with open(discussion_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-10:] if len(lines) > 10 else lines
            
            print_info(f"  总记录数: {len(lines)}")
            print_info(f"  最近 {len(recent_lines)} 条记录:")
            
            # 分析记录类型
            agent_types = {}
            for line in recent_lines:
                try:
                    entry = json.loads(line.strip())
                    agent = entry.get("analyst", entry.get("agent", "Unknown"))
                    agent_types[agent] = agent_types.get(agent, 0) + 1
                except:
                    pass
            
            if agent_types:
                print_info("  Agent 类型分布:")
                for agent, count in agent_types.items():
                    print_info(f"    - {agent}: {count} 条")
            
            # 检查是否有 discussion_history
            has_discussion_history = False
            for line in recent_lines:
                try:
                    entry = json.loads(line.strip())
                    if "discussion_history" in entry or "previous_discussion" in entry.get("metadata", {}):
                        has_discussion_history = True
                        break
                except:
                    pass
            
            if has_discussion_history:
                print_success("  Discussion History 传递: 正常")
            else:
                print_warning("  Discussion History 传递: 未找到（可能记录格式不同）")
            
            checks.append(True)
        except Exception as e:
            print_error(f"读取 Discussion Actions 文件失败: {e}")
            checks.append(False)
    else:
        print_warning(f"Discussion Actions 文件不存在: {discussion_file}")
        print_info("  （如果还没有运行过交易周期，这是正常的）")
        checks.append(True)  # 不算错误
    
    # 2. 检查 multi_analyst_system.py 中的 discussion_history 机制
    multi_analyst_file = Path("backend/src/agents/multi_analyst_system.py")
    if multi_analyst_file.exists():
        try:
            content = multi_analyst_file.read_text(encoding='utf-8')
            if "discussion_history" in content and "_format_discussion_history" in content:
                print_success("Multi-Analyst System: discussion_history 机制存在")
                checks.append(True)
            else:
                print_error("Multi-Analyst System: 缺少 discussion_history 机制")
                checks.append(False)
        except Exception as e:
            print_error(f"检查 Multi-Analyst System 失败: {e}")
            checks.append(False)
    else:
        print_error(f"Multi-Analyst System 文件不存在: {multi_analyst_file}")
        checks.append(False)
    
    return all(checks)

def check_memory_system():
    """检查 Memory 系统"""
    print("\n" + "="*80)
    print("💾 检查 Memory 系统")
    print("="*80)
    
    logs_dir = Path("data/logs")
    memory_dir = logs_dir / "memory"
    daily_dir = memory_dir / "daily"
    index_dir = memory_dir / "index"
    
    checks = []
    
    # 1. 检查 memory 目录结构
    if memory_dir.exists():
        print_success(f"Memory 目录存在: {memory_dir}")
        checks.append(True)
    else:
        print_warning(f"Memory 目录不存在: {memory_dir}")
        print_info("  （如果还没有运行过交易周期，这是正常的）")
        checks.append(True)  # 不算错误
    
    # 2. 检查 daily memory 文件
    if daily_dir.exists():
        daily_files = list(daily_dir.glob("*.json"))
        if daily_files:
            print_success(f"Daily Memory 文件: 找到 {len(daily_files)} 个文件")
            
            # 检查最近的文件
            daily_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            recent_file = daily_files[0]
            print_info(f"  最近的文件: {recent_file.name}")
            
            # 读取并检查内容
            try:
                with open(recent_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                required_fields = ["date", "market_view", "market_analysis", "discussion", "risk_report", "decision", "portfolio_snapshot"]
                missing_fields = [f for f in required_fields if f not in memory_data]
                
                if not missing_fields:
                    print_success("  Memory 文件结构: 完整")
                    checks.append(True)
                else:
                    print_warning(f"  Memory 文件缺少字段: {', '.join(missing_fields)}")
                    checks.append(True)  # 不算严重错误
            except Exception as e:
                print_error(f"读取 Memory 文件失败: {e}")
                checks.append(False)
        else:
            print_warning("Daily Memory 文件: 没有找到文件")
            checks.append(True)  # 不算错误
    else:
        print_warning(f"Daily Memory 目录不存在: {daily_dir}")
        checks.append(True)  # 不算错误
    
    # 3. 检查 memory_manager.py
    memory_manager_file = Path("backend/src/data/memory_manager.py")
    if memory_manager_file.exists():
        try:
            content = memory_manager_file.read_text(encoding='utf-8')
            if "save_daily_memory" in content and "load_recent_memories" in content:
                print_success("Memory Manager: 核心功能存在")
                checks.append(True)
            else:
                print_error("Memory Manager: 缺少核心功能")
                checks.append(False)
        except Exception as e:
            print_error(f"检查 Memory Manager 失败: {e}")
            checks.append(False)
    else:
        print_error(f"Memory Manager 文件不存在: {memory_manager_file}")
        checks.append(False)
    
    # 4. 检查 trading_cycle.py 中的 memory 调用
    trading_cycle_file = Path("backend/src/orchestrator/trading_cycle.py")
    if trading_cycle_file.exists():
        try:
            content = trading_cycle_file.read_text(encoding='utf-8')
            if "MemoryManager" in content and "load_recent_memories" in content and "save_daily_memory" in content:
                print_success("Trading Cycle: Memory 集成正常")
                checks.append(True)
            else:
                print_error("Trading Cycle: 缺少 Memory 集成")
                checks.append(False)
        except Exception as e:
            print_error(f"检查 Trading Cycle 失败: {e}")
            checks.append(False)
    else:
        print_error(f"Trading Cycle 文件不存在: {trading_cycle_file}")
        checks.append(False)
    
    return all(checks)

def check_config():
    """检查配置文件"""
    print("\n" + "="*80)
    print("⚙️  检查配置文件")
    print("="*80)
    
    config_file = Path("backend/config/config.json")
    checks = []
    
    if config_file.exists():
        print_success(f"Config 文件存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查 position_limit_mode
            position_limit_mode = config.get("position_limit_mode", "auto")
            print_info(f"  Position Limit Mode: {position_limit_mode}")
            
            if position_limit_mode == "auto":
                print_success("  Position Limit Mode: 'auto' (LLM 自主决策)")
            elif position_limit_mode == "configured":
                print_info("  Position Limit Mode: 'configured' (使用硬限制)")
            else:
                print_warning(f"  Position Limit Mode: 未知值 '{position_limit_mode}'")
            
            # 检查 min_cash_reserve_ratio
            min_cash_reserve = config.get("min_cash_reserve_ratio")
            if min_cash_reserve is None:
                print_success("  Min Cash Reserve Ratio: null (LLM 自主决策)")
            else:
                print_info(f"  Min Cash Reserve Ratio: {min_cash_reserve}")
            
            checks.append(True)
        except Exception as e:
            print_error(f"读取 Config 文件失败: {e}")
            checks.append(False)
    else:
        print_error(f"Config 文件不存在: {config_file}")
        checks.append(False)
    
    return all(checks)

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🔬 AI-Trader Ollama 系统功能检查")
    print("="*80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 检查配置文件
    results.append(("配置文件", check_config()))
    
    # 2. 检查后端 API
    results.append(("后端 API", check_backend_api()))
    
    # 3. 检查 Agent 交流机制
    results.append(("Agent 交流机制", check_agent_communication()))
    
    # 4. 检查 Memory 系统
    results.append(("Memory 系统", check_memory_system()))
    
    # 总结
    print("\n" + "="*80)
    print("📊 检查结果总结")
    print("="*80)
    
    all_passed = True
    for name, result in results:
        if result:
            print_success(f"{name}: 通过")
        else:
            print_error(f"{name}: 失败")
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print_success("所有检查通过！系统功能正常。")
    else:
        print_error("部分检查失败，请查看上面的详细信息。")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

