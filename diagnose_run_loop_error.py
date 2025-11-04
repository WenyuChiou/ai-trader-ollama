#!/usr/bin/env python3
"""
诊断 run-loop 500 错误的工具
"""
import sys
import io
import traceback
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_imports():
    """检查必要的导入"""
    print("=" * 80)
    print("检查模块导入...")
    print("=" * 80)
    
    checks = []
    
    # 1. 检查 trading_cycle
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        print("✅ execute_daily_trade 导入成功")
        checks.append(True)
    except Exception as e:
        print(f"❌ execute_daily_trade 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    
    # 2. 检查 Portfolio
    try:
        from src.data.portfolio import Portfolio
        print("✅ Portfolio 导入成功")
        checks.append(True)
    except Exception as e:
        print(f"❌ Portfolio 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    
    # 3. 检查 TradeLogger
    try:
        from src.data.trade_log import TradeLogger
        print("✅ TradeLogger 导入成功")
        checks.append(True)
    except Exception as e:
        print(f"❌ TradeLogger 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    
    # 4. 检查 OrderManager
    try:
        from src.data.order_manager import OrderManager
        print("✅ OrderManager 导入成功")
        checks.append(True)
    except Exception as e:
        print(f"❌ OrderManager 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    
    # 5. 检查 LLM client
    try:
        from src.llm.ollama_client import OllamaClient
        print("✅ OllamaClient 导入成功")
        checks.append(True)
    except Exception as e:
        print(f"❌ OllamaClient 导入失败: {e}")
        traceback.print_exc()
        checks.append(False)
    
    return all(checks)

def check_config():
    """检查配置文件"""
    print("\n" + "=" * 80)
    print("检查配置文件...")
    print("=" * 80)
    
    config_path = Path("config/config.json")
    if not config_path.exists():
        print(f"⚠️ config.json 不存在: {config_path.absolute()}")
        return False
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ config.json 存在且格式正确")
        
        # 检查必要字段
        if "universe" in config:
            universe = config["universe"]
            if isinstance(universe, list):
                print(f"✅ universe 配置: {len(universe)} 只股票")
            else:
                print(f"⚠️ universe 不是列表: {type(universe)}")
        else:
            print("⚠️ config.json 中没有 universe 字段")
        
        if "llm" in config:
            llm_config = config["llm"]
            print(f"✅ LLM 配置: {llm_config.get('default_model', 'N/A')}")
        else:
            print("⚠️ config.json 中没有 llm 字段")
        
        return True
    except Exception as e:
        print(f"❌ 读取 config.json 失败: {e}")
        traceback.print_exc()
        return False

def check_portfolio_state():
    """检查投资组合状态"""
    print("\n" + "=" * 80)
    print("检查投资组合状态...")
    print("=" * 80)
    
    portfolio_file = Path("data/logs/portfolio_state.json")
    if not portfolio_file.exists():
        print(f"⚠️ portfolio_state.json 不存在")
        print("   运行: python scripts/init_data.py")
        return False
    
    try:
        import json
        with open(portfolio_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        print(f"✅ portfolio_state.json 存在")
        print(f"   现金: ${state.get('cash', 0):.2f}")
        print(f"   持仓: {len(state.get('positions', {}))} 个")
        return True
    except Exception as e:
        print(f"❌ 读取 portfolio_state.json 失败: {e}")
        return False

def check_ollama():
    """检查 Ollama 连接"""
    print("\n" + "=" * 80)
    print("检查 Ollama 连接...")
    print("=" * 80)
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.ok:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"✅ Ollama 连接成功")
            print(f"   可用模型: {', '.join(model_names[:5])}")
            if "llama3.1" in " ".join(model_names):
                print("✅ llama3.1 模型已安装")
            else:
                print("⚠️ llama3.1 模型未找到，运行: ollama pull llama3.1")
            return True
        else:
            print(f"❌ Ollama 返回错误: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Ollama (http://localhost:11434)")
        print("   请确保 Ollama 正在运行: ollama serve")
        return False
    except Exception as e:
        print(f"❌ 检查 Ollama 失败: {e}")
        return False

def test_execute_daily_trade():
    """尝试执行一次交易循环（使用最小参数）"""
    print("\n" + "=" * 80)
    print("测试 execute_daily_trade（最小参数）...")
    print("=" * 80)
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        print("调用 execute_daily_trade...")
        # 使用最小参数，只测试一个股票
        result = execute_daily_trade(
            universe=["AAPL"],  # 只测试一个股票，减少时间
            rounds=1,  # 只运行一轮
            auto_tools=False,  # 不使用工具
            tool_budget=0
        )
        
        print("✅ execute_daily_trade 执行成功")
        print(f"   返回结果键: {list(result.keys())}")
        return True
    except Exception as e:
        print(f"❌ execute_daily_trade 执行失败: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 80)
    print("Run Loop 500 错误诊断工具")
    print("=" * 80)
    print()
    
    results = []
    
    # 检查导入
    results.append(("模块导入", check_imports()))
    
    # 检查配置
    results.append(("配置文件", check_config()))
    
    # 检查投资组合状态
    results.append(("投资组合状态", check_portfolio_state()))
    
    # 检查 Ollama
    results.append(("Ollama 连接", check_ollama()))
    
    # 测试执行（可选，可能耗时）
    print("\n" + "=" * 80)
    print("是否测试 execute_daily_trade? (这可能需要一些时间)")
    print("=" * 80)
    test_choice = input("运行测试? (y/n): ").strip().lower()
    if test_choice == 'y':
        results.append(("执行测试", test_execute_daily_trade()))
    
    # 总结
    print("\n" + "=" * 80)
    print("诊断总结")
    print("=" * 80)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✅ 所有检查通过！")
        print("   如果 run-loop 仍然失败，请查看后端 API 日志获取详细错误信息")
    else:
        print("\n❌ 部分检查失败")
        print("   请根据上面的错误信息修复问题")
        print("   然后重启 API 并再次尝试")

if __name__ == "__main__":
    main()

