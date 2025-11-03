# scripts/optimization_system.py
"""
交易系统优化模块
- 分析历史交易表现
- 识别优化机会
- 建议参数调整
- 策略改进建议
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# Ensure stdout is flushed immediately
import sys
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.memory_manager import MemoryManager
from src.data.equity_tracker import EquityTracker
from src.data.order_manager import OrderManager


class TradingOptimizer:
    """交易系统优化器"""
    
    def __init__(self, root: str | Path = "data/logs"):
        try:
            print(f"[OPTIMIZE] Step 1: Setting root path to: {root}", flush=True)
            self.root = Path(root)
            
            print(f"[OPTIMIZE] Step 2: Initializing MemoryManager...", flush=True)
            self.memory_manager = MemoryManager(root=root)
            print(f"[OPTIMIZE] ✓ MemoryManager initialized", flush=True)
            
            print(f"[OPTIMIZE] Step 3: Initializing EquityTracker...", flush=True)
            self.equity_tracker = EquityTracker(root=root)
            print(f"[OPTIMIZE] ✓ EquityTracker initialized", flush=True)
            
            print(f"[OPTIMIZE] Step 4: Initializing OrderManager...", flush=True)
            self.order_manager = OrderManager(root=root)
            print(f"[OPTIMIZE] ✓ OrderManager initialized", flush=True)
            
            print(f"[OPTIMIZE] ✓ TradingOptimizer initialized successfully", flush=True)
        except Exception as e:
            print(f"[OPTIMIZE] ✗ ERROR during initialization: {e}", flush=True)
            raise
    
    def analyze_performance(self, days: int = 30) -> Dict[str, Any]:
        """分析交易表现"""
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        
        # 获取净值历史
        try:
            equity_history = self.equity_tracker.load_equity_history(start_date=cutoff_date)
        except Exception as e:
            return {"error": f"Failed to load equity history: {e}"}
        
        if not equity_history or len(equity_history) < 2:
            return {"error": f"Insufficient data for analysis (found {len(equity_history) if equity_history else 0} records, need at least 2)"}
        
        # 计算收益指标
        initial_value = equity_history[0].get("total_value", 0)
        final_value = equity_history[-1].get("total_value", 0)
        total_return = final_value - initial_value
        total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0
        
        # 计算日收益率序列
        daily_returns = []
        for i in range(1, len(equity_history)):
            prev_value = equity_history[i-1].get("total_value", 0)
            curr_value = equity_history[i].get("total_value", 0)
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value * 100
                daily_returns.append(daily_return)
        
        # 计算波动率和夏普比率（简化版）
        avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        variance = sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns) if daily_returns else 0
        volatility = variance ** 0.5
        
        # 计算最大回撤
        values = [r.get("total_value", 0) for r in equity_history]
        peak = values[0]
        max_drawdown = 0
        max_drawdown_duration = 0
        drawdown_start = None
        
        for i, val in enumerate(values):
            if val > peak:
                peak = val
                drawdown_start = None
            else:
                drawdown = (peak - val) / peak * 100 if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                if drawdown_start is None:
                    drawdown_start = i
                max_drawdown_duration = max(max_drawdown_duration, i - drawdown_start)
        
        # 分析订单成交率
        order_stats = self._analyze_order_fill_rate(days)
        
        # 分析持仓集中度
        position_stats = self._analyze_position_concentration(days)
        
        return {
            "period_days": days,
            "performance_metrics": {
                "total_return": total_return,
                "total_return_pct": total_return_pct,
                "avg_daily_return": avg_daily_return,
                "volatility": volatility,
                "max_drawdown": max_drawdown,
                "max_drawdown_duration_days": max_drawdown_duration,
            },
            "order_stats": order_stats,
            "position_stats": position_stats,
            "recommendations": self._generate_recommendations(
                total_return_pct,
                max_drawdown,
                order_stats,
                position_stats,
            ),
        }
    
    def _analyze_order_fill_rate(self, days: int) -> Dict[str, Any]:
        """分析订单成交率"""
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        
        total_orders = 0
        filled_orders = 0
        rejected_orders = 0
        daily_fill_rates = []
        
        for i in range(days):
            check_date = (date.today() - timedelta(days=i)).isoformat()
            try:
                daily_memory = self.memory_manager.load_daily_memory(check_date)
            except Exception as e:
                # 跳过加载失败的文件
                continue
            if daily_memory:
                executed_trades = daily_memory.get("executed_trades", [])
                if executed_trades:
                    total_orders += len(executed_trades)
                    filled = len([t for t in executed_trades if t.get("status") == "FILLED"])
                    rejected = len([t for t in executed_trades if t.get("status") == "REJECTED"])
                    filled_orders += filled
                    rejected_orders += rejected
                    
                    fill_rate = (filled / len(executed_trades) * 100) if executed_trades else 0
                    daily_fill_rates.append(fill_rate)
        
        avg_fill_rate = sum(daily_fill_rates) / len(daily_fill_rates) if daily_fill_rates else 0
        
        return {
            "total_orders": total_orders,
            "filled": filled_orders,
            "rejected": rejected_orders,
            "fill_rate": (filled_orders / total_orders * 100) if total_orders > 0 else 0,
            "avg_daily_fill_rate": avg_fill_rate,
            "days_with_trades": len(daily_fill_rates),
        }
    
    def _analyze_position_concentration(self, days: int) -> Dict[str, Any]:
        """分析持仓集中度"""
        # 获取最新的 Portfolio 快照
        latest_date = date.today().isoformat()
        daily_memory = self.memory_manager.load_daily_memory(latest_date)
        
        if not daily_memory:
            # 尝试获取最近有数据的日期
            for i in range(days):
                check_date = (date.today() - timedelta(days=i)).isoformat()
                daily_memory = self.memory_manager.load_daily_memory(check_date)
                if daily_memory:
                    break
        
        if not daily_memory:
            return {
                "position_count": 0,
                "concentration_score": 0,
                "top_positions": [],
            }
        
        portfolio_snapshot = daily_memory.get("portfolio_snapshot", {})
        positions_detail = portfolio_snapshot.get("positions_detail", {})
        total_value = portfolio_snapshot.get("total_value", 0)
        
        if not positions_detail or total_value == 0:
            return {
                "position_count": 0,
                "concentration_score": 0,
                "top_positions": [],
            }
        
        # 计算每个持仓的权重
        position_weights = []
        for symbol, pos in positions_detail.items():
            market_value = pos.get("market_value", 0)
            weight = (market_value / total_value * 100) if total_value > 0 else 0
            position_weights.append({
                "symbol": symbol,
                "weight": weight,
                "market_value": market_value,
            })
        
        position_weights.sort(key=lambda x: x["weight"], reverse=True)
        
        # 计算集中度（前5只股票的权重和）
        top5_weight = sum(p["weight"] for p in position_weights[:5])
        
        return {
            "position_count": len(position_weights),
            "concentration_score": top5_weight,  # 前5只股票权重和
            "top_positions": position_weights[:10],  # 前10只
        }
    
    def _generate_recommendations(
        self,
        total_return_pct: float,
        max_drawdown: float,
        order_stats: Dict[str, Any],
        position_stats: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        
        # 成交率建议
        fill_rate = order_stats.get("fill_rate", 0)
        if fill_rate < 50:
            recommendations.append({
                "type": "ORDER_FILL_RATE",
                "priority": "HIGH",
                "issue": f"订单成交率过低 ({fill_rate:.1f}%)",
                "suggestion": "考虑调整限价策略：将买入限价从 99.5% 提高到 99.8% 当前价格，以提高成交率",
                "impact": "提高成交率可以增加实际交易次数，提高资金利用率",
            })
        elif fill_rate > 90:
            recommendations.append({
                "type": "ORDER_FILL_RATE",
                "priority": "LOW",
                "issue": f"订单成交率很高 ({fill_rate:.1f}%)",
                "suggestion": "考虑更激进的限价策略：将买入限价降至 99.0%，以获取更好的买入价格",
                "impact": "可能降低平均买入成本，但会降低成交率",
            })
        
        # 持仓集中度建议
        concentration = position_stats.get("concentration_score", 0)
        position_count = position_stats.get("position_count", 0)
        
        if concentration > 60:
            recommendations.append({
                "type": "POSITION_CONCENTRATION",
                "priority": "MEDIUM",
                "issue": f"持仓过于集中 (前5只股票占 {concentration:.1f}%)",
                "suggestion": "考虑分散持仓：降低单只股票的最大仓位限制（position_limit_per_stock），增加持仓数量",
                "impact": "降低单一股票风险，提高组合稳定性",
            })
        elif position_count > 40:
            recommendations.append({
                "type": "POSITION_CONCENTRATION",
                "priority": "LOW",
                "issue": f"持仓数量过多 ({position_count} 只股票)",
                "suggestion": "考虑提高选股标准：提高 signal_score 阈值，减少同时持仓数量，提高每只股票的仓位",
                "impact": "提高资金集中度，可能提高收益，但也会增加风险",
            })
        
        # 收益表现建议
        if total_return_pct < -5:
            recommendations.append({
                "type": "PERFORMANCE",
                "priority": "HIGH",
                "issue": f"收益表现不佳 (总收益 {total_return_pct:.2f}%)",
                "suggestion": "检查市场环境、策略参数，考虑暂停交易或调整策略",
                "impact": "避免进一步亏损",
            })
        elif max_drawdown > 20:
            recommendations.append({
                "type": "RISK_MANAGEMENT",
                "priority": "HIGH",
                "issue": f"最大回撤过大 ({max_drawdown:.2f}%)",
                "suggestion": "加强风险管理：降低总仓位上限（position_limit_total），增加止损机制",
                "impact": "降低组合波动性，保护本金",
            })
        
        # 交易频率建议
        days_with_trades = order_stats.get("days_with_trades", 0)
        if days_with_trades == 0:
            recommendations.append({
                "type": "TRADING_FREQUENCY",
                "priority": "MEDIUM",
                "issue": "近期没有交易活动",
                "suggestion": "检查 Trader Agent 的决策逻辑，可能需要降低 VIX 风险阈值或调整选股标准",
                "impact": "恢复正常交易活动",
            })
        
        return recommendations
    
    def print_optimization_report(self, days: int = 30) -> None:
        """打印优化报告"""
        print(f"[OPTIMIZE] Analyzing performance for last {days} days...", flush=True)
        try:
            analysis = self.analyze_performance(days)
        except Exception as e:
            print(f"[ERROR] Failed to analyze performance: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return
        
        if "error" in analysis:
            print()
            print("="*80)
            print(f" OPTIMIZATION REPORT - No Data Available")
            print("="*80)
            print(f"Error: {analysis['error']}")
            print()
            print("This usually means:")
            print("  1. System hasn't run for enough days yet")
            print("  2. Equity history file is missing or empty")
            print("  3. Data files are in a different location")
            print()
            print("To fix:")
            print("  1. Run daily trading for at least 7-30 days")
            print("  2. Check if data/logs/equity_history.jsonl exists")
            print("  3. Verify data/logs/memory/daily/ has memory files")
            print("="*80)
            return
        
        print("\n" + "="*80)
        print(f" TRADING SYSTEM OPTIMIZATION REPORT")
        print(f" Analysis Period: Last {days} days")
        print("="*80)
        
        # 表现指标
        metrics = analysis["performance_metrics"]
        print("\n【表现指标】", flush=True)
        print(f"  总收益率: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)", flush=True)
        print(f"  平均日收益率: {metrics['avg_daily_return']:.3f}%", flush=True)
        print(f"  波动率: {metrics['volatility']:.2f}%", flush=True)
        print(f"  最大回撤: {metrics['max_drawdown']:.2f}%", flush=True)
        print(f"  最大回撤持续天数: {metrics['max_drawdown_duration_days']}", flush=True)
        
        # 订单统计
        order_stats = analysis["order_stats"]
        print("\n【订单统计】", flush=True)
        print(f"  总订单数: {order_stats['total_orders']}", flush=True)
        print(f"  成交率: {order_stats['fill_rate']:.1f}%", flush=True)
        print(f"  平均每日成交率: {order_stats['avg_daily_fill_rate']:.1f}%", flush=True)
        print(f"  有交易的天数: {order_stats['days_with_trades']}", flush=True)
        
        # 持仓统计
        position_stats = analysis["position_stats"]
        print("\n【持仓统计】", flush=True)
        print(f"  持仓数量: {position_stats['position_count']} 只", flush=True)
        print(f"  集中度 (前5只): {position_stats['concentration_score']:.1f}%", flush=True)
        if position_stats['top_positions']:
            print("\n  前10大持仓:", flush=True)
            for i, pos in enumerate(position_stats['top_positions'][:10], 1):
                print(f"    {i}. {pos['symbol']}: {pos['weight']:.2f}% (${pos['market_value']:.2f})", flush=True)
        
        # 优化建议
        recommendations = analysis["recommendations"]
        print("\n【优化建议】", flush=True)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                priority_color = {
                    "HIGH": "🔴",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                }.get(rec["priority"], "⚪")
                
                print(f"\n  {i}. [{priority_color} {rec['priority']}] {rec['type']}", flush=True)
                print(f"     问题: {rec['issue']}", flush=True)
                print(f"     建议: {rec['suggestion']}", flush=True)
                print(f"     影响: {rec['impact']}", flush=True)
        else:
            print("  ✓ 暂无优化建议，系统运行正常", flush=True)
        
        print("\n" + "="*80, flush=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading System Optimizer")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    
    args = parser.parse_args()
    
    optimizer = TradingOptimizer()
    optimizer.print_optimization_report(days=args.days)

