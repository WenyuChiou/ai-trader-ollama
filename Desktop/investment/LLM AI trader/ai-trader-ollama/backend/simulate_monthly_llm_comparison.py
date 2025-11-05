#!/usr/bin/env python3
"""
月度交易模拟 - 测试3个不同的LLM模型

- 使用一个月的数据（30天）
- 测试3个不同的LLM模型：llama3.1, llama3, mistral
- 使用 universe 中的所有股票
- 初始资金：10000 美金
- 支持反向ETF做对冲
- 比较不同模型的表现
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def get_last_month_dates() -> List[str]:
    """
    获取上个月的所有交易日（周一到周五）
    返回日期列表（YYYY-MM-DD格式）
    """
    today = datetime.now()
    
    # 计算上个月的第一天和最后一天
    if today.month == 1:
        last_month = 12
        last_year = today.year - 1
    else:
        last_month = today.month - 1
        last_year = today.year
    
    # 上个月的第一天
    first_day = datetime(last_year, last_month, 1)
    
    # 上个月的最后一天
    if last_month == 12:
        last_day = datetime(last_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(last_year, last_month + 1, 1) - timedelta(days=1)
    
    # 生成上个月的所有交易日（周一到周五）
    dates = []
    current = first_day
    while current <= last_day:
        # weekday() 返回 0-6，0=Monday, 6=Sunday
        if current.weekday() < 5:  # 周一到周五
            dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return dates


def load_universe() -> List[str]:
    """从 config.json 加载股票 universe，并添加反向ETF"""
    config_path = ROOT / "config" / "config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            universe = config.get("universe", [])
            
            # 添加常见的反向ETF选项（用于对冲）
            inverse_etfs = [
                "SQQQ",   # 3x Short QQQ (对冲 NASDAQ)
                "SPXU",   # 3x Short S&P 500
                "SH",     # Short S&P 500
                "PSQ",    # Short QQQ
                "SDS",    # 2x Short S&P 500
                "DOG",    # Short Dow 30
            ]
            
            # 将反向ETF添加到 universe（如果不存在）
            for etf in inverse_etfs:
                if etf not in universe:
                    universe.append(etf)
            
            return universe
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        # 默认返回一些股票
        return ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "SQQQ", "SPXU"]


def create_agent_config_for_model(model_name: str) -> str:
    """为指定模型创建临时的 agent 配置文件"""
    import yaml
    
    # 读取原始配置
    original_config_path = ROOT / "config" / "agents.yaml"
    with open(original_config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    # 更新所有 agent 的模型为指定模型
    for agent_key in config:
        if isinstance(config[agent_key], dict):
            config[agent_key]["model"] = model_name
    
    # 创建临时配置文件
    temp_dir = ROOT / "data" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_config_path = temp_dir / f"agents_{model_name.replace('.', '_').replace('-', '_')}.yaml"
    
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    return str(temp_config_path)


def run_simulation_for_model(
    model_name: str,
    dates: List[str],
    universe: List[str],
    initial_cash: float = 10000.0,
) -> Dict[str, Any]:
    """为指定模型运行月度模拟"""
    print("\n" + "="*80)
    print(f" SIMULATING WITH MODEL: {model_name.upper()}")
    print("="*80)
    
    # 创建临时 agent 配置
    temp_config_path = create_agent_config_for_model(model_name)
    
    # 使用环境变量或临时配置文件来指定模型
    # 由于 AgentFactory 从配置文件读取，我们需要修改配置文件路径
    # 这里我们使用一个临时方法：修改 config/agents.yaml 的内容
    # 或者创建一个自定义的 AgentFactory 实例
    
    # 为了简化，我们暂时使用环境变量来切换模型
    import os
    original_model = os.environ.get("OLLAMA_MODEL")
    os.environ["OLLAMA_MODEL"] = model_name
    
    try:
        # 初始化 Portfolio
        portfolio = Portfolio(cash=initial_cash, initial_value=initial_cash)
        trade_logger = TradeLogger()
        
        # 存储每日结果
        daily_results: List[Dict[str, Any]] = []
        
        # 模拟每一天
        for day_num, date in enumerate(dates, 1):
            print(f"\n[{model_name}] Day {day_num}/{len(dates)}: {date}")
            
            # 计算日期范围（使用前180天作为历史数据窗口）
            start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=180)).strftime('%Y-%m-%d')
            end_date = date
            
            try:
                # 临时修改所有 agent 的模型配置
                # 由于 execute_daily_trade 内部使用 AgentFactory，我们需要在全局替换配置
                # 使用 monkey patch 替换 AgentFactory 实例的配置
                from src.agents import factory as factory_module
                from src.llm.ollama_client import get_llm
                
                # 保存原始的 get_llm
                original_get_llm = factory_module.get_llm
                
                def patched_get_llm(*args, **kwargs):
                    """强制使用指定的模型"""
                    if 'model' not in kwargs:
                        kwargs['model'] = model_name
                    elif 'model' in kwargs and kwargs['model'] != model_name:
                        kwargs['model'] = model_name
                    return original_get_llm(*args, **kwargs)
                
                # 临时替换 get_llm
                factory_module.get_llm = patched_get_llm
                
                try:
                    # 执行每日交易循环
                    result = execute_daily_trade(
                        universe=universe,
                        start=start_date,
                        end=end_date,
                        rounds=3,  # 讨论轮数
                        auto_tools=True,
                        tool_budget=2,  # 工具预算
                        portfolio=portfolio,  # 使用同一个 portfolio，保持连续状态
                        trade_logger=trade_logger,
                    )
                finally:
                    # 恢复原始的 get_llm
                    factory_module.get_llm = original_get_llm
                
                # 获取最新价格
                last_prices = {}
                buy_orders = result.get("decision", {}).get("buy_orders", [])
                sell_orders = result.get("decision", {}).get("sell_orders", [])
                
                for order in buy_orders:
                    symbol = order.get("symbol")
                    price = order.get("buy_price")
                    if symbol and price:
                        last_prices[symbol] = float(price)
                
                for order in sell_orders:
                    symbol = order.get("symbol")
                    price = order.get("sell_price")
                    if symbol and price:
                        last_prices[symbol] = float(price)
                
                # 对于已有持仓的股票，尝试从市场数据获取价格
                from src.tools.market_tools import fetch_market_batch
                try:
                    held_symbols = list(portfolio._positions.keys())
                    missing_symbols = [s for s in held_symbols if s not in last_prices]
                    if missing_symbols:
                        market_data = fetch_market_batch.invoke({
                            "symbols": missing_symbols,
                            "start": date,
                            "end": date,
                        })
                        stocks = market_data.get("stocks", {})
                        for symbol in missing_symbols:
                            if symbol in stocks:
                                try:
                                    price = float(stocks[symbol].get("price", 0))
                                    if price > 0:
                                        last_prices[symbol] = price
                                except Exception:
                                    pass
                except Exception:
                    pass
                
                # 对于仍然没有价格的持仓，使用平均成本
                for symbol, pos in portfolio._positions.items():
                    if symbol not in last_prices:
                        last_prices[symbol] = pos.avg_cost
                
                # 保存每日结果
                daily_results.append({
                    "day": day_num,
                    "date": date,
                    "result": result,
                })
                
                # 打印简要信息
                decision = result.get("decision", {})
                action = decision.get("action", "HOLD")
                executed = result.get("executed_trades", [])
                print(f"  [{model_name}] Action: {action}, Trades: {len(executed)}")
                
            except Exception as e:
                print(f"  [{model_name}] Day {day_num} failed: {type(e).__name__}: {e}")
                continue
        
        # 计算最终结果
        final_portfolio_value = portfolio.value(last_prices) if last_prices else portfolio.cash
        final_pnl = portfolio.total_pnl(last_prices) if last_prices else 0.0
        final_pnl_pct = portfolio.total_pnl_pct(last_prices) if last_prices else 0.0
        
        # 统计交易
        total_trades = 0
        total_buys = 0
        total_sells = 0
        
        for daily in daily_results:
            executed = daily.get("result", {}).get("executed_trades", [])
            total_trades += len(executed)
            total_buys += len([t for t in executed if t.get("action") == "BUY"])
            total_sells += len([t for t in executed if t.get("action") == "SELL"])
        
        return {
            "model": model_name,
            "initial_capital": initial_cash,
            "final_portfolio_value": final_portfolio_value,
            "total_pnl": final_pnl,
            "total_pnl_pct": final_pnl_pct,
            "final_cash": portfolio.cash,
            "final_positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost,
                }
                for symbol, pos in portfolio._positions.items()
            },
            "trading_stats": {
                "total_trades": total_trades,
                "total_buys": total_buys,
                "total_sells": total_sells,
                "days_with_trades": len([d for d in daily_results if d.get("result", {}).get("executed_trades")]),
            },
            "daily_results": daily_results,
        }
    
    finally:
        # 恢复原始配置
        if original_config:
            os.environ["AGENTS_CONFIG_PATH"] = original_config
        elif "AGENTS_CONFIG_PATH" in os.environ:
            del os.environ["AGENTS_CONFIG_PATH"]
        
        # 清理临时配置文件
        try:
            temp_config_path_obj = Path(temp_config_path)
            if temp_config_path_obj.exists():
                temp_config_path_obj.unlink()
        except Exception:
            pass


def compare_models():
    """比较3个不同LLM模型的交易表现"""
    print("\n" + "="*80)
    print(" MONTHLY TRADING SIMULATION - LLM COMPARISON")
    print("="*80)
    
    # 获取上个月的交易日
    dates = get_last_month_dates()
    print(f"\nSimulating trading for {len(dates)} days in last month:")
    if dates:
        print(f"  Start: {dates[0]}")
        print(f"  End: {dates[-1]}")
    
    # 加载 universe
    universe = load_universe()
    print(f"\nUniverse: {len(universe)} symbols")
    print(f"  Stocks: {[s for s in universe if s not in ['SQQQ', 'SPXU', 'SH', 'PSQ', 'SDS', 'DOG']][:10]}...")
    print(f"  Inverse ETFs: {[s for s in universe if s in ['SQQQ', 'SPXU', 'SH', 'PSQ', 'SDS', 'DOG']]}")
    
    # 测试的3个模型
    models = ["llama3.1", "llama3", "mistral"]
    initial_cash = 10000.0
    
    print(f"\nTesting {len(models)} models: {', '.join(models)}")
    print(f"Initial Capital: ${initial_cash:.2f}")
    
    # 为每个模型运行模拟
    results = {}
    
    for model in models:
        try:
            print(f"\n{'='*80}")
            print(f"Starting simulation for {model}...")
            print('='*80)
            
            result = run_simulation_for_model(
                model_name=model,
                dates=dates,
                universe=universe,
                initial_cash=initial_cash,
            )
            
            results[model] = result
            
            print(f"\n[{model}] Simulation completed!")
            print(f"  Final Value: ${result['final_portfolio_value']:.2f}")
            print(f"  Total P&L: ${result['total_pnl']:.2f} ({result['total_pnl_pct']:.2f}%)")
            print(f"  Total Trades: {result['trading_stats']['total_trades']}")
            print(f"  Buy Orders: {result['trading_stats']['total_buys']}")
            print(f"  Sell Orders: {result['trading_stats']['total_sells']}")
            
        except Exception as e:
            print(f"\n[{model}] Simulation failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results[model] = {"error": str(e)}
            continue
    
    # 打印对比结果
    print("\n" + "="*80)
    print(" MODEL COMPARISON SUMMARY")
    print("="*80)
    
    comparison_data = []
    for model, result in results.items():
        if "error" not in result:
            comparison_data.append({
                "model": model,
                "final_value": result["final_portfolio_value"],
                "pnl": result["total_pnl"],
                "pnl_pct": result["total_pnl_pct"],
                "trades": result["trading_stats"]["total_trades"],
                "positions": len(result["final_positions"]),
            })
    
    # 按 P&L 百分比排序
    comparison_data.sort(key=lambda x: x["pnl_pct"], reverse=True)
    
    print("\nRanking by P&L %:")
    for i, data in enumerate(comparison_data, 1):
        print(f"\n  {i}. {data['model']}:")
        print(f"     Final Value: ${data['final_value']:.2f}")
        print(f"     P&L: ${data['pnl']:.2f} ({data['pnl_pct']:.2f}%)")
        print(f"     Total Trades: {data['trades']}")
        print(f"     Final Positions: {data['positions']}")
    
    # 保存结果
    output_file = ROOT / "data" / "logs" / "monthly_llm_comparison.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "simulation_date": datetime.now().isoformat(),
        "month_dates": dates,
        "initial_capital": initial_cash,
        "universe_size": len(universe),
        "models_tested": models,
        "results": results,
        "comparison": comparison_data,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(" SIMULATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nResults saved to: {output_file}\n")
    
    return results


if __name__ == "__main__":
    try:
        compare_models()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Simulation stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Simulation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

