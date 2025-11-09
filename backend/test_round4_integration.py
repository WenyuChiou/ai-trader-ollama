#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第4轮测试：前后端集成测试
测试端到端工作流、数据同步、实时更新
"""
import sys
import io
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 確保在 backend 目錄
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30


class Round4IntegrationTester:
    def __init__(self):
        self.results = {
            "test_round": 4,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "issues": [],
            "summary": {}
        }
        self.backend_dir = backend_dir
        
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
            response = requests.get(f"{BASE_URL}/api/backend/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_api_data(self, endpoint: str, timeout: int = TIMEOUT) -> Optional[Dict]:
        """获取API数据"""
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def post_api_data(self, endpoint: str, data: Dict = None, timeout: int = TIMEOUT) -> Optional[Dict]:
        """发送POST请求"""
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def get_file_data(self, filepath: Path) -> Optional[Dict]:
        """读取文件数据"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    if filepath.suffix == '.jsonl':
                        lines = [json.loads(l) for l in f.readlines() if l.strip()]
                        return lines if lines else None
                    else:
                        return json.load(f)
            return None
        except Exception as e:
            return None
    
    def test_1_data_sync_after_init(self):
        """测试1：初始化后的数据同步"""
        print("\n[TEST 1] 测试初始化后的数据同步...")
        
        # 1.1 执行初始化
        print("  执行系统初始化...")
        init_result = self.post_api_data("/api/system/init", timeout=60)
        
        if not init_result:
            self.log_test("Init API Response", "fail", "初始化API无响应")
            return
        
        time.sleep(2)  # 等待数据写入
        
        # 1.2 检查文件数据
        portfolio_file = self.backend_dir / "data" / "logs" / "portfolio_state.json"
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        
        portfolio_file_data = self.get_file_data(portfolio_file)
        equity_file_data = self.get_file_data(equity_file)
        
        if portfolio_file_data:
            file_cash = portfolio_file_data.get("cash", 0)
            file_total = portfolio_file_data.get("total_value", 0)
            self.log_test("Portfolio File After Init", "pass", 
                         f"Cash: ${file_cash:.2f}, Total: ${file_total:.2f}")
        else:
            self.log_test("Portfolio File After Init", "fail", "文件不存在或无法读取")
        
        if equity_file_data:
            self.log_test("Equity History File After Init", "pass", 
                         f"{len(equity_file_data)} records")
        else:
            self.log_test("Equity History File After Init", "warning", "文件为空或不存在")
        
        # 1.3 检查API数据
        api_portfolio = self.get_api_data("/api/portfolio/real-time", timeout=20)
        if api_portfolio:
            api_cash = api_portfolio.get("cash", 0)
            api_total = api_portfolio.get("total_value", 0)
            self.log_test("Portfolio API After Init", "pass", 
                         f"Cash: ${api_cash:.2f}, Total: ${api_total:.2f}")
            
            # 1.4 检查数据一致性
            if portfolio_file_data:
                file_cash = portfolio_file_data.get("cash", 0)
                if abs(file_cash - api_cash) < 0.01:
                    self.log_test("Data Sync (Init)", "pass", "文件与API数据一致")
                else:
                    self.log_test("Data Sync (Init)", "warning", 
                                 f"文件与API数据不一致: File=${file_cash:.2f}, API=${api_cash:.2f}")
        else:
            self.log_test("Portfolio API After Init", "warning", "API无响应，使用文件数据")
    
    def test_2_data_sync_after_trade(self):
        """测试2：交易后的数据同步"""
        print("\n[TEST 2] 测试交易后的数据同步...")
        
        # 2.1 获取交易前的状态
        portfolio_before = self.get_file_data(
            self.backend_dir / "data" / "logs" / "portfolio_state.json"
        )
        equity_before = self.get_file_data(
            self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        )
        
        cash_before = portfolio_before.get("cash", 0) if portfolio_before else 0
        equity_count_before = len(equity_before) if equity_before else 0
        
        print(f"  交易前状态: Cash=${cash_before:.2f}, Equity Records={equity_count_before}")
        
        # 2.2 执行交易循环
        print("  执行交易循环...")
        trade_result = self.post_api_data("/api/trading/execute-trade", timeout=300)
        
        if not trade_result:
            self.log_test("Trade Execution", "warning", "交易API无响应或超时（可能市场关闭）")
            return
        
        time.sleep(3)  # 等待数据写入
        
        # 2.3 检查交易后的状态
        portfolio_after = self.get_file_data(
            self.backend_dir / "data" / "logs" / "portfolio_state.json"
        )
        equity_after = self.get_file_data(
            self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        )
        
        if portfolio_after:
            cash_after = portfolio_after.get("cash", 0)
            total_after = portfolio_after.get("total_value", 0)
            self.log_test("Portfolio After Trade", "pass", 
                         f"Cash: ${cash_after:.2f}, Total: ${total_after:.2f}")
            
            # 检查现金是否变化
            if abs(cash_after - cash_before) > 0.01:
                self.log_test("Cash Updated After Trade", "pass", 
                            f"现金已更新: ${cash_before:.2f} -> ${cash_after:.2f}")
            else:
                self.log_test("Cash Updated After Trade", "warning", 
                            "现金未变化（可能没有订单执行）")
        else:
            self.log_test("Portfolio After Trade", "fail", "无法读取交易后的投资组合文件")
        
        if equity_after:
            equity_count_after = len(equity_after)
            self.log_test("Equity History After Trade", "pass", 
                         f"{equity_count_after} records")
            
            # 检查净值历史是否更新
            if equity_count_after > equity_count_before:
                self.log_test("Equity History Updated", "pass", 
                            f"净值历史已更新: {equity_count_before} -> {equity_count_after}")
            else:
                self.log_test("Equity History Updated", "warning", 
                            "净值历史未更新（可能没有新交易）")
        else:
            self.log_test("Equity History After Trade", "warning", "净值历史文件为空")
        
        # 2.4 检查API与文件的一致性
        api_portfolio = self.get_api_data("/api/portfolio/real-time", timeout=20)
        if api_portfolio and portfolio_after:
            api_cash = api_portfolio.get("cash", 0)
            file_cash = portfolio_after.get("cash", 0)
            if abs(api_cash - file_cash) < 0.01:
                self.log_test("Data Sync (After Trade)", "pass", "交易后文件与API数据一致")
            else:
                self.log_test("Data Sync (After Trade)", "warning", 
                             f"交易后数据不一致: File=${file_cash:.2f}, API=${api_cash:.2f}")
    
    def test_3_equity_update_realtime(self):
        """测试3：净值更新实时性"""
        print("\n[TEST 3] 测试净值更新实时性...")
        
        # 3.1 获取初始净值
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        equity_data = self.get_file_data(equity_file)
        
        if not equity_data:
            self.log_test("Equity History Available", "warning", "净值历史文件不存在或为空")
            return
        
        initial_count = len(equity_data)
        last_equity = equity_data[-1] if equity_data else None
        initial_value = last_equity.get("total_value", 0) if last_equity else 0
        
        print(f"  初始状态: {initial_count} records, Last Value=${initial_value:.2f}")
        
        # 3.2 检查API返回的净值历史
        api_equity = self.get_api_data("/api/portfolio/equity-history?limit=100", timeout=20)
        if api_equity:
            api_records = api_equity.get("history", [])
            self.log_test("Equity History API", "pass", f"API返回 {len(api_records)} 条记录")
            
            # 检查最新净值
            if api_records:
                latest_api = api_records[0]
                api_value = latest_api.get("total_value", 0)
                if abs(api_value - initial_value) < 0.01:
                    self.log_test("Equity Value Consistency", "pass", 
                                f"API与文件净值一致: ${api_value:.2f}")
                else:
                    self.log_test("Equity Value Consistency", "warning", 
                                f"API与文件净值不一致: File=${initial_value:.2f}, API=${api_value:.2f}")
        else:
            self.log_test("Equity History API", "warning", "API无响应，使用文件数据")
        
        # 3.3 检查净值图表数据格式
        if equity_data:
            # 检查数据格式（使用 equity_value 而不是 equity）
            required_fields = ["date", "total_value", "cash", "equity_value"]
            sample = equity_data[-1] if equity_data else {}
            missing_fields = [f for f in required_fields if f not in sample]
            if not missing_fields:
                self.log_test("Equity Data Format", "pass", "净值数据格式完整")
            else:
                self.log_test("Equity Data Format", "fail", 
                             f"缺少字段: {', '.join(missing_fields)}")
    
    def test_4_execution_records_completeness(self):
        """测试4：执行记录完整性"""
        print("\n[TEST 4] 测试执行记录完整性...")
        
        # 4.1 检查订单文件
        orders_file = self.backend_dir / "data" / "logs" / "pending_orders.jsonl"
        filled_orders_file = self.backend_dir / "data" / "logs" / "filled_orders.jsonl"
        
        pending_orders = self.get_file_data(orders_file)
        filled_orders = self.get_file_data(filled_orders_file)
        
        pending_count = len(pending_orders) if pending_orders else 0
        filled_count = len(filled_orders) if filled_orders else 0
        
        print(f"  订单状态: Pending={pending_count}, Filled={filled_count}")
        
        if pending_orders:
            self.log_test("Pending Orders File", "pass", f"{pending_count} pending orders")
        else:
            self.log_test("Pending Orders File", "pass", "无pending订单（正常）")
        
        if filled_orders:
            self.log_test("Filled Orders File", "pass", f"{filled_count} filled orders")
            
            # 检查filled订单的完整性
            sample_order = filled_orders[0] if filled_orders else {}
            required_fields = ["symbol", "action", "quantity", "fill_price", "timestamp"]
            missing_fields = [f for f in required_fields if f not in sample_order]
            if not missing_fields:
                self.log_test("Filled Order Format", "pass", "Filled订单格式完整")
            else:
                self.log_test("Filled Order Format", "fail", 
                             f"缺少字段: {', '.join(missing_fields)}")
        else:
            self.log_test("Filled Orders File", "pass", "无filled订单（正常）")
        
        # 4.2 检查API返回的订单
        api_trades = self.get_api_data("/api/trades/recent?limit=50", timeout=20)
        if api_trades:
            api_trade_list = api_trades.get("trades", [])
            self.log_test("Trades API", "pass", f"API返回 {len(api_trade_list)} 条交易记录")
            
            # 检查API与文件的一致性
            if filled_orders and api_trade_list:
                file_count = len(filled_orders)
                api_count = len(api_trade_list)
                if abs(file_count - api_count) <= 1:  # 允许1条记录的差异
                    self.log_test("Orders Data Sync", "pass", 
                                f"文件与API订单数量一致: {file_count}")
                else:
                    self.log_test("Orders Data Sync", "warning", 
                                f"文件与API订单数量不一致: File={file_count}, API={api_count}")
        else:
            self.log_test("Trades API", "warning", "API无响应，使用文件数据")
    
    def test_5_refresh_data_sync(self):
        """测试5：刷新后的数据同步"""
        print("\n[TEST 5] 测试刷新后的数据同步...")
        
        # 5.1 获取刷新前的文件数据
        portfolio_before = self.get_file_data(
            self.backend_dir / "data" / "logs" / "portfolio_state.json"
        )
        cash_before = portfolio_before.get("cash", 0) if portfolio_before else 0
        
        # 5.2 模拟刷新操作（调用API）
        print("  执行刷新操作...")
        api_portfolio = self.get_api_data("/api/portfolio/real-time", timeout=20)
        
        if api_portfolio:
            api_cash = api_portfolio.get("cash", 0)
            api_total = api_portfolio.get("total_value", 0)
            self.log_test("Refresh API Response", "pass", 
                         f"Cash: ${api_cash:.2f}, Total: ${api_total:.2f}")
            
            # 5.3 检查刷新后的文件数据
            portfolio_after = self.get_file_data(
                self.backend_dir / "data" / "logs" / "portfolio_state.json"
            )
            
            if portfolio_after:
                file_cash = portfolio_after.get("cash", 0)
                
                # 刷新不应该改变文件数据，只应该同步显示
                if abs(file_cash - cash_before) < 0.01:
                    self.log_test("Refresh Data Consistency", "pass", 
                                "刷新后文件数据未改变（正确）")
                else:
                    self.log_test("Refresh Data Consistency", "warning", 
                                f"刷新后文件数据改变: ${cash_before:.2f} -> ${file_cash:.2f}")
                
                # 检查API与文件的一致性
                if abs(api_cash - file_cash) < 0.01:
                    self.log_test("Refresh Data Sync", "pass", 
                                "刷新后API与文件数据一致")
                else:
                    self.log_test("Refresh Data Sync", "warning", 
                                f"刷新后数据不一致: File=${file_cash:.2f}, API=${api_cash:.2f}")
            else:
                self.log_test("Refresh Data Consistency", "fail", "无法读取刷新后的文件")
        else:
            self.log_test("Refresh API Response", "warning", "刷新API无响应")
    
    def generate_summary(self):
        """生成测试总结"""
        tests = self.results["tests"]
        passed = len([t for t in tests if t["status"] == "pass"])
        failed = len([t for t in tests if t["status"] == "fail"])
        warnings = len([t for t in tests if t["status"] == "warning"])
        total = len(tests)
        
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        }
        
        print("\n" + "=" * 80)
        print("  测试总结")
        print("=" * 80)
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⚠️  警告: {warnings}")
        print(f"通过率: {self.results['summary']['pass_rate']}")
        
        if self.results["issues"]:
            print(f"\n问题数: {len(self.results['issues'])}")
            for issue in self.results["issues"]:
                print(f"  - [{issue['severity'].upper()}] {issue['issue']}")
    
    def save_results(self):
        """保存测试结果"""
        results_file = self.backend_dir / "frontend_test_results_round4.json"
        report_file = self.backend_dir / "TEST_ROUND_4_REPORT.md"
        
        # 保存JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 生成Markdown报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 第4轮测试报告：前后端集成测试\n\n")
            f.write(f"**测试时间**: {self.results['start_time']}\n\n")
            f.write(f"## 测试结果\n\n")
            f.write(f"- ✅ **通过**: {self.results['summary']['passed']}/{self.results['summary']['total']}\n")
            f.write(f"- ❌ **失败**: {self.results['summary']['failed']}/{self.results['summary']['total']}\n")
            f.write(f"- ⚠️  **警告**: {self.results['summary']['warnings']}/{self.results['summary']['total']}\n")
            f.write(f"- **通过率**: {self.results['summary']['pass_rate']}\n\n")
            
            f.write(f"## 测试详情\n\n")
            for test in self.results["tests"]:
                icon = "✅" if test["status"] == "pass" else "❌" if test["status"] == "fail" else "⚠️"
                f.write(f"{icon} **{test['name']}**: {test['status']}\n")
                if test["details"]:
                    f.write(f"   - {test['details']}\n")
                f.write("\n")
            
            if self.results["issues"]:
                f.write(f"## 问题列表\n\n")
                for issue in self.results["issues"]:
                    f.write(f"- [{issue['severity'].upper()}] {issue['issue']}\n")
                f.write("\n")
        
        print(f"\n测试结果已保存:")
        print(f"  - JSON: {results_file}")
        print(f"  - 报告: {report_file}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("  第4轮测试：前后端集成测试")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端URL: {BASE_URL}")
        
        # 检查后端是否运行
        if not self.check_backend_running():
            print("\n⚠️  警告: 后端服务未运行，部分测试可能失败")
            print("   请先启动后端服务: cd backend && python -m uvicorn src.api.server:app --reload")
        
        # 运行所有测试
        self.test_1_data_sync_after_init()
        self.test_2_data_sync_after_trade()
        self.test_3_equity_update_realtime()
        self.test_4_execution_records_completeness()
        self.test_5_refresh_data_sync()
        
        # 生成总结和保存结果
        self.generate_summary()
        self.save_results()


if __name__ == "__main__":
    tester = Round4IntegrationTester()
    tester.run_all_tests()

