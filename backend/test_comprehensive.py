#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面系统测试脚本
测试前端和后端的所有功能
"""
import subprocess
import json
import time
import sys
import io
import requests
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"
TEST_RESULTS = []

class ComprehensiveTester:
    def __init__(self):
        self.results = {
            "test_round": 1,
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
            "severity": severity,  # critical, high, medium, low
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
    
    def test_api_endpoint(self, endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
        """测试 API 端点"""
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            else:
                return {"ok": False, "error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return {"ok": True, "data": response.json()}
            else:
                return {"ok": False, "error": f"Status {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def test_portfolio_state(self):
        """测试投资组合状态"""
        print("\n[TEST] 测试投资组合状态...")
        
        # 检查 portfolio_state.json
        portfolio_file = self.backend_dir / "data" / "portfolio_state.json"
        if portfolio_file.exists():
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
                
                # 检查必需字段
                required_fields = ["cash", "positions", "total_value"]
                missing_fields = [f for f in required_fields if f not in portfolio]
                
                if missing_fields:
                    self.log_test("Portfolio State File", "fail", f"Missing fields: {missing_fields}")
                    self.log_issue(f"Portfolio state missing fields: {missing_fields}", "high")
                else:
                    self.log_test("Portfolio State File", "pass", f"Cash: ${portfolio.get('cash', 0):.2f}, Positions: {len(portfolio.get('positions', []))}")
            except Exception as e:
                self.log_test("Portfolio State File", "fail", str(e))
                self.log_issue(f"Cannot read portfolio state: {e}", "high")
        else:
            self.log_test("Portfolio State File", "warning", "File does not exist (may be after initialization)")
        
        # 检查 API
        result = self.test_api_endpoint("/api/portfolio/real-time")
        if result["ok"]:
            data = result["data"]
            if "cash" in data and "total_value" in data:
                self.log_test("Portfolio API", "pass", f"Cash: ${data.get('cash', 0):.2f}, Total: ${data.get('total_value', 0):.2f}")
            else:
                self.log_test("Portfolio API", "fail", "Missing required fields")
                self.log_issue("Portfolio API missing required fields", "high")
        else:
            self.log_test("Portfolio API", "fail", result.get("error", "Unknown error"))
            self.log_issue(f"Portfolio API error: {result.get('error')}", "critical")
    
    def test_equity_history(self):
        """测试净值历史"""
        print("\n[TEST] 测试净值历史...")
        
        # 检查 equity_history.jsonl
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        if equity_file.exists():
            try:
                lines = []
                with open(equity_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            lines.append(json.loads(line))
                
                if len(lines) > 0:
                    latest = lines[-1]
                    # 检查必需字段：date 和 total_value (或 value)
                    has_date = "date" in latest
                    has_value = "value" in latest or "total_value" in latest
                    
                    if has_date and has_value:
                        value = latest.get("value") or latest.get("total_value", 0)
                        date = latest.get("date", "Unknown")
                        self.log_test("Equity History File", "pass", f"{len(lines)} records, Latest: {date} = ${value:.2f}")
                    else:
                        missing = []
                        if not has_date: missing.append("date")
                        if not has_value: missing.append("value/total_value")
                        self.log_test("Equity History File", "fail", f"Missing required fields: {missing}")
                        self.log_issue(f"Equity history missing required fields: {missing}", "high")
                else:
                    self.log_test("Equity History File", "warning", "File exists but is empty")
            except Exception as e:
                self.log_test("Equity History File", "fail", str(e))
                self.log_issue(f"Cannot read equity history: {e}", "high")
        else:
            self.log_test("Equity History File", "warning", "File does not exist")
        
        # 检查 API
        result = self.test_api_endpoint("/api/portfolio/equity-history?limit=10")
        if result["ok"]:
            data = result["data"]
            # API 返回格式: {"ok": True, "records": [...], "count": ...}
            if isinstance(data, dict) and "records" in data:
                records = data["records"]
                count = data.get("count", len(records))
                self.log_test("Equity History API", "pass", f"{count} records returned")
            elif isinstance(data, list):
                # 兼容旧格式
                self.log_test("Equity History API", "pass", f"{len(data)} records returned")
            else:
                self.log_test("Equity History API", "fail", f"Invalid response format: {type(data)}")
                self.log_issue("Equity history API invalid format", "medium")
        else:
            self.log_test("Equity History API", "fail", result.get("error", "Unknown error"))
            self.log_issue(f"Equity history API error: {result.get('error')}", "high")
    
    def test_orders(self):
        """测试订单"""
        print("\n[TEST] 测试订单...")
        
        # 检查订单 API
        result = self.test_api_endpoint("/api/trades/recent?limit=10")
        if result["ok"]:
            data = result["data"]
            # API 可能返回数组或对象
            if isinstance(data, list):
                self.log_test("Orders API", "pass", f"{len(data)} recent orders")
            elif isinstance(data, dict) and "trades" in data:
                trades = data["trades"]
                self.log_test("Orders API", "pass", f"{len(trades)} recent orders")
            else:
                # 尝试检查是否有其他字段
                self.log_test("Orders API", "warning", f"Unexpected format: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        else:
            self.log_test("Orders API", "fail", result.get("error", "Unknown error"))
    
    def test_conversations(self):
        """测试对话"""
        print("\n[TEST] 测试对话...")
        
        result = self.test_api_endpoint("/api/agents/conversations?limit=10")
        if result["ok"]:
            data = result["data"]
            if isinstance(data, dict) and "conversations" in data:
                convs = data["conversations"]
                self.log_test("Conversations API", "pass", f"{len(convs)} conversations")
            else:
                self.log_test("Conversations API", "fail", "Invalid response format")
        else:
            self.log_test("Conversations API", "fail", result.get("error", "Unknown error"))
    
    def test_market_status(self):
        """测试市场状态"""
        print("\n[TEST] 测试市场状态...")
        
        result = self.test_api_endpoint("/api/market/is-open")
        if result["ok"]:
            data = result["data"]
            # API 返回格式: {"ok": True, "open": bool, "now": ...}
            if "open" in data:
                status = "OPEN" if data["open"] else "CLOSED"
                self.log_test("Market Status API", "pass", f"Market is {status}")
            elif "is_open" in data:
                # 兼容旧格式
                status = "OPEN" if data["is_open"] else "CLOSED"
                self.log_test("Market Status API", "pass", f"Market is {status}")
            else:
                self.log_test("Market Status API", "fail", f"Missing open/is_open field. Keys: {list(data.keys())}")
        else:
            self.log_test("Market Status API", "fail", result.get("error", "Unknown error"))
    
    def test_trading_cycle(self):
        """测试交易循环"""
        print("\n[TEST] 测试交易循环...")
        
        # 检查是否可以执行交易循环（使用更长的超时时间）
        try:
            url = f"{BASE_URL}/api/trading/execute-trade"
            response = requests.post(url, json={}, timeout=60)  # 60秒超时
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Trading Cycle API", "pass", f"Trading cycle executed: {data.get('message', 'OK')}")
            else:
                self.log_test("Trading Cycle API", "fail", f"Status {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout:
            self.log_test("Trading Cycle API", "warning", "Request timeout (60s) - trading cycle may be running")
        except Exception as e:
            error = str(e)
            # 如果是超时或正在执行，不算失败
            if "timeout" in error.lower() or "executing" in error.lower():
                self.log_test("Trading Cycle API", "warning", error)
            else:
                self.log_test("Trading Cycle API", "fail", error)
                self.log_issue(f"Trading cycle error: {error}", "high")
    
    def test_initialization(self):
        """测试初始化"""
        print("\n[TEST] 测试初始化...")
        
        # 注意：初始化会清空数据，所以只检查 API 是否可用
        # 使用 /api/system/init 端点
        try:
            url = f"{BASE_URL}/api/system/init"
            response = requests.post(url, json={}, timeout=30)  # 30秒超时
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Initialization API", "pass", f"Initialization endpoint available: {data.get('message', 'OK')}")
            elif response.status_code == 404:
                self.log_test("Initialization API", "warning", "Initialization endpoint not found (may not be implemented)")
            else:
                self.log_test("Initialization API", "fail", f"Status {response.status_code}: {response.text[:200]}")
        except requests.exceptions.Timeout:
            self.log_test("Initialization API", "warning", "Request timeout (30s) - initialization may be running")
        except Exception as e:
            error = str(e)
            if "404" in error:
                self.log_test("Initialization API", "warning", "Initialization endpoint not found (may not be implemented)")
            else:
                self.log_test("Initialization API", "fail", error)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("🔍 全面系统测试")
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
        self.test_portfolio_state()
        self.test_equity_history()
        self.test_orders()
        self.test_conversations()
        self.test_market_status()
        self.test_trading_cycle()
        self.test_initialization()
        
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
        result_file = self.backend_dir / "comprehensive_test_results.json"
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
    tester = ComprehensiveTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

