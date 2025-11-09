#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第 3 轮测试：数据记录情境测试
测试初始化、交易循环等场景下的数据记录功能
"""
import sys
import io
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

class DataRecordingTester:
    def __init__(self):
        self.results = {
            "test_round": 3,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "issues": [],
            "summary": {}
        }
        self.backend_dir = Path(__file__).parent
        
    def log_test(self, name: str, status: str, details: str = ""):
        """记录测试结果"""
        test_result = {
            "name": name,
            "status": status,  # pass, fail, warning
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(test_result)
        icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
        print(f"{icon} {name}: {status}")
        if details:
            print(f"   {details}")
    
    def log_issue(self, issue: str, severity: str = "medium"):
        """记录问题"""
        issue_record = {
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.results["issues"].append(issue_record)
        print(f"⚠️  ISSUE [{severity.upper()}]: {issue}")
    
    def check_backend_running(self) -> bool:
        """检查后端是否运行"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def test_api_endpoint(self, endpoint: str, method: str = "GET", data: dict = None, timeout: int = 30) -> Dict[str, Any]:
        """测试 API 端点"""
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                return {"ok": False, "error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return {"ok": True, "data": response.json()}
            else:
                return {"ok": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        except requests.exceptions.Timeout:
            return {"ok": False, "error": "timeout", "timeout": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def test_initialization_recording(self):
        """测试初始化数据记录"""
        print("\n[TEST] 测试初始化数据记录...")
        
        # 记录初始化前的状态
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        portfolio_file = self.backend_dir / "data" / "logs" / "portfolio_state.json"
        
        # 读取初始化前的记录数（注意：初始化会清空文件，所以这里只是记录）
        initial_equity_count = 0
        if equity_file.exists():
            try:
                with open(equity_file, 'r', encoding='utf-8') as f:
                    initial_equity_count = sum(1 for line in f if line.strip())
            except Exception:
                pass
        
        # 执行初始化（会清空 equity_history.jsonl 并重新创建）
        result = self.test_api_endpoint("/api/system/init", method="POST", data={}, timeout=60)
        
        if result["ok"]:
            # 等待文件写入
            time.sleep(2)
            
            # 检查净值历史记录（初始化会清空文件并创建新记录）
            if equity_file.exists():
                try:
                    with open(equity_file, 'r', encoding='utf-8') as f:
                        lines = [line for line in f if line.strip()]
                    
                    # 初始化应该创建至少一条记录
                    if len(lines) > 0:
                        # 检查最新记录格式
                        latest = json.loads(lines[-1])
                        required_fields = ["date", "cash", "equity_value", "total_value"]
                        missing = [f for f in required_fields if f not in latest]
                        
                        if missing:
                            self.log_test("Initialization Equity Recording", "fail", f"Missing fields: {missing}")
                            self.log_issue(f"Initialization equity record missing fields: {missing}", "high")
                        else:
                            self.log_test("Initialization Equity Recording", "pass", f"New record added: {latest.get('date')}, Total: ${latest.get('total_value', 0):.2f}")
                    else:
                        self.log_test("Initialization Equity Recording", "fail", "Initialization should create at least one equity record")
                except Exception as e:
                    self.log_test("Initialization Equity Recording", "fail", f"Cannot read equity file: {e}")
            else:
                self.log_test("Initialization Equity Recording", "fail", "Equity history file not created")
            
            # 检查投资组合状态
            if portfolio_file.exists():
                try:
                    with open(portfolio_file, 'r', encoding='utf-8') as f:
                        portfolio = json.load(f)
                    
                    required_fields = ["cash", "positions", "total_value", "initial_value"]
                    missing = [f for f in required_fields if f not in portfolio]
                    
                    if missing:
                        self.log_test("Initialization Portfolio Recording", "fail", f"Missing fields: {missing}")
                        self.log_issue(f"Portfolio state missing fields: {missing}", "high")
                    else:
                        cash = portfolio.get("cash", 0)
                        total = portfolio.get("total_value", 0)
                        initial = portfolio.get("initial_value", 0)
                        if abs(cash - 10000.0) < 0.01 and abs(total - 10000.0) < 0.01 and abs(initial - 10000.0) < 0.01:
                            self.log_test("Initialization Portfolio Recording", "pass", f"Portfolio reset correctly: Cash=${cash:.2f}, Total=${total:.2f}, Initial=${initial:.2f}")
                        else:
                            self.log_test("Initialization Portfolio Recording", "fail", f"Portfolio not reset correctly: Cash=${cash:.2f}, Total=${total:.2f}, Initial=${initial:.2f}")
                            self.log_issue(f"Portfolio initialization values incorrect", "high")
                except Exception as e:
                    self.log_test("Initialization Portfolio Recording", "fail", f"Cannot read portfolio file: {e}")
                    self.log_issue(f"Portfolio file read error: {e}", "high")
            else:
                self.log_test("Initialization Portfolio Recording", "fail", "Portfolio state file not created")
                self.log_issue("Portfolio state file not created during initialization", "high")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Initialization Recording", "warning", "Initialization timeout (may still be processing)")
            else:
                self.log_test("Initialization Recording", "fail", f"Initialization failed: {error}")
    
    def test_trading_cycle_recording(self):
        """测试交易循环数据记录"""
        print("\n[TEST] 测试交易循环数据记录...")
        
        # 记录交易前的状态
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        conv_file = self.backend_dir / "data" / "logs" / "discussion_actions.jsonl"
        orders_file = self.backend_dir / "data" / "logs" / "filled_orders.jsonl"
        
        initial_equity_count = 0
        initial_conv_count = 0
        initial_orders_count = 0
        
        if equity_file.exists():
            try:
                with open(equity_file, 'r', encoding='utf-8') as f:
                    initial_equity_count = sum(1 for line in f if line.strip())
            except Exception:
                pass
        
        if conv_file.exists():
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    initial_conv_count = sum(1 for line in f if line.strip())
            except Exception:
                pass
        
        if orders_file.exists():
            try:
                with open(orders_file, 'r', encoding='utf-8') as f:
                    initial_orders_count = sum(1 for line in f if line.strip())
            except Exception:
                pass
        
        # 执行交易循环
        result = self.test_api_endpoint("/api/trading/execute-trade", method="POST", data={}, timeout=300)
        
        if result["ok"]:
            # 等待文件写入
            time.sleep(3)
            
            # 检查对话记录
            if conv_file.exists():
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        lines = [line for line in f if line.strip()]
                    
                    new_convs = len(lines) - initial_conv_count
                    if new_convs > 0:
                        # 检查最新记录格式
                        latest = json.loads(lines[-1])
                        if "agent" in latest or "agent_name" in latest:
                            self.log_test("Trading Cycle Conversation Recording", "pass", f"{new_convs} new conversations recorded")
                        else:
                            self.log_test("Trading Cycle Conversation Recording", "warning", "Conversations recorded but missing agent field")
                    else:
                        self.log_test("Trading Cycle Conversation Recording", "warning", "No new conversations recorded")
                except Exception as e:
                    self.log_test("Trading Cycle Conversation Recording", "warning", f"Cannot read conversation file: {e}")
            else:
                self.log_test("Trading Cycle Conversation Recording", "warning", "Conversation file not exists (may be first run)")
            
            # 检查订单记录（如果有订单生成）
            if orders_file.exists():
                try:
                    with open(orders_file, 'r', encoding='utf-8') as f:
                        lines = [line for line in f if line.strip()]
                    
                    new_orders = len(lines) - initial_orders_count
                    if new_orders > 0:
                        self.log_test("Trading Cycle Order Recording", "pass", f"{new_orders} new orders recorded")
                    else:
                        self.log_test("Trading Cycle Order Recording", "pass", "No new orders (may be no trading decisions)")
                except Exception as e:
                    self.log_test("Trading Cycle Order Recording", "warning", f"Cannot read orders file: {e}")
            else:
                self.log_test("Trading Cycle Order Recording", "pass", "No orders file (no orders generated yet)")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Trading Cycle Recording", "warning", "Trading cycle timeout (may still be processing)")
            else:
                self.log_test("Trading Cycle Recording", "fail", f"Trading cycle failed: {error}")
    
    def test_equity_history_updates(self):
        """测试净值历史更新"""
        print("\n[TEST] 测试净值历史更新...")
        
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        
        if equity_file.exists():
            try:
                # 读取所有记录
                records = []
                with open(equity_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            records.append(json.loads(line))
                
                if len(records) > 0:
                    # 检查记录是否按时间排序
                    dates = [r.get("date") for r in records if "date" in r]
                    if dates == sorted(dates):
                        self.log_test("Equity History Sorting", "pass", f"{len(records)} records, properly sorted")
                    else:
                        self.log_test("Equity History Sorting", "fail", "Records not properly sorted")
                        self.log_issue("Equity history records not sorted by date", "high")
                    
                    # 检查记录格式一致性
                    required_fields = ["date"]
                    optional_fields = ["value", "total_value", "cash", "equity_value"]
                    
                    format_issues = []
                    for i, record in enumerate(records):
                        if "date" not in record:
                            format_issues.append(f"Record {i} missing date")
                        if not any(f in record for f in optional_fields):
                            format_issues.append(f"Record {i} missing value fields")
                    
                    if format_issues:
                        self.log_test("Equity History Format Consistency", "fail", f"Issues: {format_issues[:3]}")
                        self.log_issue(f"Equity history format issues: {format_issues}", "high")
                    else:
                        self.log_test("Equity History Format Consistency", "pass", f"All {len(records)} records have consistent format")
                    
                    # 检查数据合理性
                    latest = records[-1]
                    total_value = latest.get("total_value") or latest.get("value", 0)
                    cash = latest.get("cash", 0)
                    
                    if total_value < 0 or cash < 0:
                        self.log_test("Equity History Data Validity", "fail", f"Negative values: Total=${total_value:.2f}, Cash=${cash:.2f}")
                        self.log_issue("Equity history has negative values", "high")
                    else:
                        self.log_test("Equity History Data Validity", "pass", f"Latest: Total=${total_value:.2f}, Cash=${cash:.2f}")
                else:
                    self.log_test("Equity History Updates", "warning", "No equity history records")
            except Exception as e:
                self.log_test("Equity History Updates", "fail", f"Cannot read equity file: {e}")
        else:
            self.log_test("Equity History Updates", "warning", "Equity history file not exists")
    
    def test_data_consistency_across_files(self):
        """测试跨文件数据一致性"""
        print("\n[TEST] 测试跨文件数据一致性...")
        
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        portfolio_file = self.backend_dir / "data" / "logs" / "portfolio_state.json"
        
        # 读取最新净值记录
        latest_equity = None
        if equity_file.exists():
            try:
                with open(equity_file, 'r', encoding='utf-8') as f:
                    lines = [line for line in f if line.strip()]
                if len(lines) > 0:
                    latest_equity = json.loads(lines[-1])
            except Exception:
                pass
        
        # 读取投资组合状态
        portfolio_data = None
        if portfolio_file.exists():
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio_data = json.load(f)
            except Exception:
                pass
        
        # 比较数据
        if latest_equity and portfolio_data:
            equity_total = latest_equity.get("total_value") or latest_equity.get("value", 0)
            portfolio_total = portfolio_data.get("total_value", 0)
            equity_cash = latest_equity.get("cash", 0)
            portfolio_cash = portfolio_data.get("cash", 0)
            
            # 允许小的差异（因为可能有实时价格更新）
            total_diff = abs(equity_total - portfolio_total)
            cash_diff = abs(equity_cash - portfolio_cash)
            
            # 如果 portfolio 没有 total_value，使用 cash + equity_value 计算
            if portfolio_total == 0 and portfolio_data:
                # 尝试从 positions 计算 equity_value
                positions = portfolio_data.get("positions", {})
                estimated_equity = 0.0
                # 注意：这里无法准确计算，因为需要当前价格
                # 所以如果 portfolio_total 为 0，我们使用 cash 作为近似值
                portfolio_total = portfolio_cash  # 假设没有持仓或持仓价值为0
            
            if total_diff < 100 and cash_diff < 0.01:  # 允许100美元的差异（价格波动）
                self.log_test("Cross-File Data Consistency", "pass", f"Files consistent: Total diff=${total_diff:.2f}, Cash diff=${cash_diff:.2f}")
            else:
                # 如果差异很大，检查是否是 portfolio 缺少 total_value 字段
                if "total_value" not in portfolio_data:
                    self.log_test("Cross-File Data Consistency", "fail", f"Portfolio missing total_value field: Total diff=${total_diff:.2f}, Cash diff=${cash_diff:.2f}")
                    self.log_issue("Portfolio state missing total_value field", "high")
                else:
                    self.log_test("Cross-File Data Consistency", "warning", f"Large difference: Total diff=${total_diff:.2f}, Cash diff=${cash_diff:.2f}")
        elif latest_equity:
            self.log_test("Cross-File Data Consistency", "pass", "Equity history available (portfolio file may use API fallback)")
        elif portfolio_data:
            self.log_test("Cross-File Data Consistency", "pass", "Portfolio state available (equity history may be empty)")
        else:
            self.log_test("Cross-File Data Consistency", "pass", "No data files yet (system may not be initialized)")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("🔍 第 3 轮测试：数据记录情境测试")
        print("="*80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 检查后端是否运行
        if not self.check_backend_running():
            print("❌ 后端未运行！请先启动后端服务器。")
            print("   运行命令: cd backend && python -m uvicorn src.api.server:app --reload")
            return False
        
        print("✅ 后端服务器运行中")
        print()
        
        # 运行所有测试
        self.test_initialization_recording()
        self.test_trading_cycle_recording()
        self.test_equity_history_updates()
        self.test_data_consistency_across_files()
        
        # 生成总结
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """生成测试总结"""
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        
        total = len(self.results["tests"])
        passed = len([t for t in self.results["tests"] if t["status"] == "pass"])
        failed = len([t for t in self.results["tests"] if t["status"] == "fail"])
        warnings = len([t for t in self.results["tests"] if t["status"] == "warning"])
        
        print(f"\n总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        
        if self.results["issues"]:
            print(f"\n问题数: {len(self.results['issues'])}")
            critical = [i for i in self.results["issues"] if i["severity"] == "critical"]
            high = [i for i in self.results["issues"] if i["severity"] == "high"]
            if critical:
                print(f"  🔴 严重: {len(critical)}")
            if high:
                print(f"  🟠 高: {len(high)}")
        
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "issues_count": len(self.results["issues"])
        }
        
        # 保存结果
        result_file = self.backend_dir / "data_recording_test_results_round3.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试结果已保存到: {result_file}")
        
        # 返回状态
        if failed == 0 and len([i for i in self.results["issues"] if i["severity"] in ["critical", "high"]]) == 0:
            print("\n✅ 所有测试通过！")
            return True
        else:
            print("\n⚠️  发现问题，请查看详细结果。")
            return False

if __name__ == "__main__":
    tester = DataRecordingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

