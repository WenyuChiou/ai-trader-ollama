# scripts/monitoring_system.py
"""
交易系统监控模块
- 监控每日执行状态
- 追踪错误和异常
- 记录性能指标
- 生成监控报告
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


class TradingMonitor:
    """交易系统监控器"""
    
    def __init__(self, root: str | Path = "data/logs"):
        try:
            print(f"[MONITOR] Step 1: Setting root path to: {root}", flush=True)
            self.root = Path(root)
            self.monitoring_file = self.root / "monitoring.jsonl"
            
            print(f"[MONITOR] Step 2: Creating directories...", flush=True)
            # 确保目录存在
            self.root.mkdir(parents=True, exist_ok=True)
            print(f"[MONITOR] ✓ Directories created", flush=True)
            
            print(f"[MONITOR] Step 3: Initializing MemoryManager...", flush=True)
            self.memory_manager = MemoryManager(root=root)
            print(f"[MONITOR] ✓ MemoryManager initialized", flush=True)
            
            print(f"[MONITOR] Step 4: Initializing EquityTracker...", flush=True)
            self.equity_tracker = EquityTracker(root=root)
            print(f"[MONITOR] ✓ EquityTracker initialized", flush=True)
            
            print(f"[MONITOR] Step 5: Initializing OrderManager...", flush=True)
            self.order_manager = OrderManager(root=root)
            print(f"[MONITOR] ✓ OrderManager initialized", flush=True)
            
            print(f"[MONITOR] ✓ TradingMonitor initialized successfully", flush=True)
        except Exception as e:
            print(f"[MONITOR] ✗ ERROR during initialization: {e}", flush=True)
            raise
    
    def log_execution(
        self,
        date_str: str,
        status: str,
        execution_time: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录每日执行日志
        
        参数:
        - date_str: 执行日期
        - status: SUCCESS / ERROR / SKIPPED
        - execution_time: 执行时间（秒）
        - error: 错误信息（如果有）
        - metadata: 额外元数据
        """
        record = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "execution_time_seconds": execution_time,
            "error": error,
            "metadata": metadata or {},
        }
        
        # 追加到 JSONL 文件
        with self.monitoring_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def get_daily_status(self, date_str: str) -> Dict[str, Any]:
        """获取指定日期的执行状态"""
        if not self.monitoring_file.exists():
            return {"status": "NO_DATA", "date": date_str}
        
        try:
            with self.monitoring_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get("date") == date_str:
                            return record
        except Exception:
            pass
        
        return {"status": "NO_DATA", "date": date_str}
    
    def get_recent_status(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近几天的执行状态"""
        if not self.monitoring_file.exists():
            return []
        
        records = []
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        
        try:
            with self.monitoring_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            if record.get("date", "") >= cutoff_date:
                                records.append(record)
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
        except Exception as e:
            print(f"[WARN] Error reading monitoring file: {e}")
            return []
        
        # 按日期排序（最新的在前）
        records.sort(key=lambda x: x.get("date", ""), reverse=True)
        return records
    
    def generate_monitoring_report(self, days: int = 7) -> Dict[str, Any]:
        """生成监控报告"""
        if not self.monitoring_file.exists():
            return {
                "report_date": date.today().isoformat(),
                "period_days": days,
                "execution_summary": {
                    "total_runs": 0,
                    "success": 0,
                    "errors": 0,
                    "skipped": 0,
                    "success_rate": 0,
                    "avg_execution_time_seconds": 0,
                },
                "trading_stats": {"total_orders": 0, "filled": 0, "rejected": 0, "fill_rate": 0},
                "equity_stats": {
                    "initial_value": 0,
                    "final_value": 0,
                    "total_return": 0,
                    "total_return_pct": 0,
                    "max_drawdown": 0,
                    "records_count": 0,
                },
                "recent_status": [],
            }
        
        recent_status = self.get_recent_status(days)
        
        total_runs = len(recent_status)
        success_count = len([r for r in recent_status if r.get("status") == "SUCCESS"])
        error_count = len([r for r in recent_status if r.get("status") == "ERROR"])
        skipped_count = len([r for r in recent_status if r.get("status") == "SKIPPED"])
        
        avg_execution_time = 0.0
        if recent_status:
            times = [r.get("execution_time_seconds", 0) for r in recent_status]
            avg_execution_time = sum(times) / len(times) if times else 0.0
        
        # 获取最近的交易统计
        try:
            trading_stats = self._get_trading_stats(days)
        except Exception as e:
            print(f"[WARN] Failed to get trading stats: {e}")
            trading_stats = {
                "total_orders": 0,
                "filled": 0,
                "rejected": 0,
                "fill_rate": 0,
            }
        
        # 获取最近的净值变化
        try:
            equity_stats = self._get_equity_stats(days)
        except Exception as e:
            print(f"[WARN] Failed to get equity stats: {e}")
            equity_stats = {
                "initial_value": 0,
                "final_value": 0,
                "total_return": 0,
                "total_return_pct": 0,
                "max_drawdown": 0,
                "records_count": 0,
            }
        
        return {
            "report_date": date.today().isoformat(),
            "period_days": days,
            "execution_summary": {
                "total_runs": total_runs,
                "success": success_count,
                "errors": error_count,
                "skipped": skipped_count,
                "success_rate": (success_count / total_runs * 100) if total_runs > 0 else 0,
                "avg_execution_time_seconds": avg_execution_time,
            },
            "trading_stats": trading_stats,
            "equity_stats": equity_stats,
            "recent_status": recent_status[:5],  # 最近5条记录
        }
    
    def _get_trading_stats(self, days: int) -> Dict[str, Any]:
        """获取交易统计"""
        print(f"[MONITOR] Calculating trading stats for {days} days...", flush=True)
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        
        total_orders = 0
        total_filled = 0
        total_rejected = 0
        
        # 从每日记忆中获取交易数据
        print(f"[MONITOR] Scanning {days} days of memory files...", flush=True)
        memory_dir = self.memory_manager.daily_dir if hasattr(self.memory_manager, 'daily_dir') else Path(self.root) / "memory" / "daily"
        
        if not memory_dir.exists():
            print(f"[MONITOR] Memory directory not found: {memory_dir}", flush=True)
            return {
                "total_orders": 0,
                "filled": 0,
                "rejected": 0,
                "fill_rate": 0,
            }
        
        print(f"[MONITOR] Memory directory: {memory_dir}", flush=True)
        for i in range(days):
            if i % 5 == 0 or i == days - 1:  # 每5天或最后一天打印进度
                print(f"[MONITOR] Processing day {i+1}/{days}...", flush=True)
            check_date = (date.today() - timedelta(days=i)).isoformat()
            try:
                daily_memory = self.memory_manager.load_daily_memory(check_date)
                if daily_memory:
                    executed_trades = daily_memory.get("executed_trades", [])
                    total_orders += len(executed_trades)
                    total_filled += len([t for t in executed_trades if t.get("status") == "FILLED"])
                    total_rejected += len([t for t in executed_trades if t.get("status") == "REJECTED"])
            except Exception as e:
                # 跳过加载失败的文件，继续处理
                if i % 10 == 0:  # 每10天打印一次错误
                    print(f"[MONITOR] Warning: Failed to load memory for {check_date}: {e}", flush=True)
                continue
        
        print(f"[MONITOR] Stats calculated: {total_orders} orders, {total_filled} filled, {total_rejected} rejected", flush=True)
        return {
            "total_orders": total_orders,
            "filled": total_filled,
            "rejected": total_rejected,
            "fill_rate": (total_filled / total_orders * 100) if total_orders > 0 else 0,
        }
    
    def _get_equity_stats(self, days: int) -> Dict[str, Any]:
        """获取净值统计"""
        print(f"[MONITOR] Loading equity history for {days} days...", flush=True)
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()
        
        equity_history = self.equity_tracker.load_equity_history(
            start_date=cutoff_date,
            limit=days,
        )
        print(f"[MONITOR] Loaded {len(equity_history)} equity records", flush=True)
        
        if not equity_history:
            return {
                "initial_value": 0,
                "final_value": 0,
                "total_return": 0,
                "total_return_pct": 0,
                "max_drawdown": 0,
                "records_count": 0,
            }
        
        initial_value = equity_history[0].get("total_value", 0)
        final_value = equity_history[-1].get("total_value", 0)
        total_return = final_value - initial_value
        total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0
        
        # 计算最大回撤
        values = [r.get("total_value", 0) for r in equity_history]
        max_value = max(values) if values else 0
        max_drawdown = 0
        for val in values:
            if max_value > 0:
                drawdown = (max_value - val) / max_value * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        return {
            "initial_value": initial_value,
            "final_value": final_value,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "max_drawdown": max_drawdown,
            "records_count": len(equity_history),
        }
    
    def print_monitoring_report(self, days: int = 7) -> None:
        """打印监控报告"""
        print(f"[MONITOR] Generating report for last {days} days...", flush=True)
        report = self.generate_monitoring_report(days)
        print(f"[MONITOR] Report generated, printing...", flush=True)
        
        print("", flush=True)
        print("="*80, flush=True)
        print(f" TRADING SYSTEM MONITORING REPORT", flush=True)
        print(f" Period: Last {days} days", flush=True)
        print("="*80, flush=True)
        
        # 执行摘要
        exec_summary = report["execution_summary"]
        print("\n【执行摘要】", flush=True)
        print(f"  总运行次数: {exec_summary['total_runs']}", flush=True)
        print(f"  成功: {exec_summary['success']} ({exec_summary['success_rate']:.1f}%)", flush=True)
        print(f"  错误: {exec_summary['errors']}", flush=True)
        print(f"  跳过: {exec_summary['skipped']}", flush=True)
        print(f"  平均执行时间: {exec_summary['avg_execution_time_seconds']:.1f} 秒", flush=True)
        
        # 交易统计
        trading_stats = report["trading_stats"]
        print("\n【交易统计】", flush=True)
        print(f"  总订单数: {trading_stats['total_orders']}", flush=True)
        print(f"  成交: {trading_stats['filled']} ({trading_stats['fill_rate']:.1f}%)", flush=True)
        print(f"  拒绝: {trading_stats['rejected']}", flush=True)
        
        # 净值统计
        equity_stats = report["equity_stats"]
        print("\n【净值统计】", flush=True)
        print(f"  初始净值: ${equity_stats['initial_value']:.2f}", flush=True)
        print(f"  最终净值: ${equity_stats['final_value']:.2f}", flush=True)
        print(f"  总收益: ${equity_stats['total_return']:.2f} ({equity_stats['total_return_pct']:.2f}%)", flush=True)
        print(f"  最大回撤: {equity_stats['max_drawdown']:.2f}%", flush=True)
        
        # 最近状态
        if report["recent_status"]:
            print("\n【最近执行记录】", flush=True)
            for status in report["recent_status"][:5]:
                date_str = status.get("date", "N/A")
                stat = status.get("status", "N/A")
                time = status.get("execution_time_seconds", 0)
                print(f"  {date_str}: {stat} ({time:.1f}s)", flush=True)
        
        print("\n" + "="*80, flush=True)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading System Monitor")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--date", type=str, help="Check specific date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    monitor = TradingMonitor()
    
    if args.date:
        status = monitor.get_daily_status(args.date)
        print(f"\nDaily Status for {args.date}:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        monitor.print_monitoring_report(days=args.days)

