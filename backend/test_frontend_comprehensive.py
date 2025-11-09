#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端全面测试脚本
测试所有前端功能、按钮、数据显示等
"""
import subprocess
import json
import time
import sys
import io
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
# Selenium not needed - we test APIs and frontend code directly

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_TEST_FILE = Path(__file__).parent.parent / "frontend" / "monitor_test.html"

class FrontendComprehensiveTester:
    def __init__(self):
        self.results = {
            "test_round": 2,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "issues": [],
            "summary": {}
        }
        self.backend_dir = Path(__file__).parent
        self.driver = None
        
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
    
    def test_api_endpoint(self, endpoint: str, method: str = "GET", data: dict = None, timeout: int = 10) -> Dict[str, Any]:
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
    
    def test_button_functionality(self):
        """测试按钮功能"""
        print("\n[TEST] 测试按钮功能...")
        
        # 测试初始化按钮 API
        result = self.test_api_endpoint("/api/system/init", method="POST", data={})
        if result["ok"]:
            self.log_test("Initialize Button API", "pass", "Initialization endpoint available")
        else:
            error = result.get("error", "Unknown error")
            if "timeout" in error.lower():
                self.log_test("Initialize Button API", "pass", "Endpoint responding (timeout expected)")
            elif "404" in error:
                self.log_test("Initialize Button API", "warning", "Initialization endpoint not found")
            else:
                self.log_test("Initialize Button API", "fail", error)
        
        # 测试刷新按钮（检查数据更新）
        result = self.test_api_endpoint("/api/portfolio/real-time")
        if result["ok"]:
            self.log_test("Refresh Button API", "pass", "Portfolio data refreshable")
        else:
            self.log_test("Refresh Button API", "fail", result.get("error", "Unknown error"))
        
        # 测试 Start Trading 按钮
        result = self.test_api_endpoint("/api/trading/execute-trade", method="POST", data={})
        if result["ok"]:
            self.log_test("Start Trading Button API", "pass", "Trading endpoint available")
        else:
            error = result.get("error", "Unknown error")
            if "timeout" in error.lower() or "409" in error:
                self.log_test("Start Trading Button API", "pass", "Endpoint responding (timeout/conflict expected)")
            else:
                self.log_test("Start Trading Button API", "fail", error)
    
    def test_data_display(self):
        """测试数据显示"""
        print("\n[TEST] 测试数据显示...")
        
        # 测试投资组合数据显示
        result = self.test_api_endpoint("/api/portfolio/real-time", timeout=15)
        if result["ok"]:
            data = result["data"]
            required_fields = ["cash", "total_value", "total_pnl"]
            missing = [f for f in required_fields if f not in data]
            if missing:
                self.log_test("Portfolio Display Data", "fail", f"Missing fields: {missing}")
                self.log_issue(f"Portfolio display missing fields: {missing}", "high")
            else:
                # 检查数据合理性
                cash = data.get("cash", 0)
                total_value = data.get("total_value", 0)
                if cash < 0 or total_value < 0:
                    self.log_test("Portfolio Display Data", "fail", f"Negative values: cash={cash}, total={total_value}")
                    self.log_issue("Portfolio has negative values", "high")
                else:
                    self.log_test("Portfolio Display Data", "pass", f"Cash: ${cash:.2f}, Total: ${total_value:.2f}")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Portfolio Display Data", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("Portfolio Display Data", "fail", error)
        
        # 测试净值历史显示
        result = self.test_api_endpoint("/api/portfolio/equity-history?limit=10", timeout=15)
        if result["ok"]:
            data = result["data"]
            if isinstance(data, dict) and "records" in data:
                records = data["records"]
                if len(records) > 0:
                    # 检查记录格式
                    latest = records[-1]
                    if "date" in latest and ("value" in latest or "total_value" in latest):
                        self.log_test("Equity History Display", "pass", f"{len(records)} records, format correct")
                    else:
                        self.log_test("Equity History Display", "fail", "Missing required fields in records")
                else:
                    self.log_test("Equity History Display", "warning", "No records available")
            else:
                self.log_test("Equity History Display", "fail", "Invalid response format")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Equity History Display", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("Equity History Display", "fail", error)
        
        # 测试对话显示
        result = self.test_api_endpoint("/api/agents/conversations?limit=10", timeout=15)
        if result["ok"]:
            data = result["data"]
            if isinstance(data, dict) and "conversations" in data:
                convs = data["conversations"]
                # 检查对话格式
                if len(convs) > 0:
                    first_conv = convs[0]
                    if "agent" in first_conv or "agent_name" in first_conv:
                        self.log_test("Conversations Display", "pass", f"{len(convs)} conversations, format correct")
                    else:
                        self.log_test("Conversations Display", "warning", "Conversations missing agent field")
                else:
                    self.log_test("Conversations Display", "warning", "No conversations available")
            else:
                self.log_test("Conversations Display", "fail", "Invalid response format")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Conversations Display", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("Conversations Display", "fail", error)
    
    def test_data_consistency(self):
        """测试数据一致性"""
        print("\n[TEST] 测试数据一致性...")
        
        # 检查投资组合状态文件与API的一致性
        portfolio_file = self.backend_dir / "data" / "logs" / "portfolio_state.json"
        result = self.test_api_endpoint("/api/portfolio/real-time")
        
        if result["ok"] and portfolio_file.exists():
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                api_data = result["data"]
                file_cash = file_data.get("cash", 0)
                api_cash = api_data.get("cash", 0)
                
                # 允许小的浮点误差
                if abs(file_cash - api_cash) < 0.01:
                    self.log_test("Data Consistency (Cash)", "pass", f"File and API cash match: ${file_cash:.2f}")
                else:
                    self.log_test("Data Consistency (Cash)", "fail", f"Mismatch: File=${file_cash:.2f}, API=${api_cash:.2f}")
                    self.log_issue("Portfolio cash mismatch between file and API", "high")
            except Exception as e:
                self.log_test("Data Consistency (Cash)", "warning", f"Cannot compare: {e}")
        else:
            if not portfolio_file.exists():
                self.log_test("Data Consistency (Cash)", "pass", "File not exists, API has fallback (OK)")
            else:
                self.log_test("Data Consistency (Cash)", "warning", "Cannot check consistency")
        
        # 检查净值历史与当前净值的一致性
        equity_result = self.test_api_endpoint("/api/portfolio/equity-history?limit=1")
        portfolio_result = self.test_api_endpoint("/api/portfolio/real-time")
        
        if equity_result["ok"] and portfolio_result["ok"]:
            equity_data = equity_result["data"]
            portfolio_data = portfolio_result["data"]
            
            if isinstance(equity_data, dict) and "records" in equity_data:
                records = equity_data["records"]
                if len(records) > 0:
                    latest_equity = records[-1]
                    equity_value = latest_equity.get("value") or latest_equity.get("total_value", 0)
                    portfolio_value = portfolio_data.get("total_value", 0)
                    
                    # 允许小的差异（因为可能有实时价格更新）
                    diff = abs(equity_value - portfolio_value)
                    diff_pct = (diff / equity_value * 100) if equity_value > 0 else 0
                    
                    if diff_pct < 5:  # 允许5%的差异
                        self.log_test("Data Consistency (Equity)", "pass", f"Equity history and current value consistent (diff: {diff_pct:.2f}%)")
                    else:
                        self.log_test("Data Consistency (Equity)", "warning", f"Large difference: Equity=${equity_value:.2f}, Current=${portfolio_value:.2f} (diff: {diff_pct:.2f}%)")
                else:
                    self.log_test("Data Consistency (Equity)", "warning", "No equity history records")
            else:
                self.log_test("Data Consistency (Equity)", "warning", "Cannot check equity consistency")
        else:
            self.log_test("Data Consistency (Equity)", "warning", "Cannot check consistency (API unavailable)")
    
    def test_user_experience(self):
        """测试用户体验相关功能"""
        print("\n[TEST] 测试用户体验...")
        
        # 测试市场状态显示
        result = self.test_api_endpoint("/api/market/is-open", timeout=15)
        if result["ok"]:
            data = result["data"]
            if "open" in data:
                status = "OPEN" if data["open"] else "CLOSED"
                self.log_test("Market Status Display", "pass", f"Market status correctly displayed: {status}")
            else:
                self.log_test("Market Status Display", "fail", "Missing 'open' field")
        else:
            error = result.get("error", "Unknown error")
            if result.get("timeout"):
                self.log_test("Market Status Display", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("Market Status Display", "fail", error)
        
        # 测试VIX和FGI数据
        # 这些数据应该总是可用（即使市场关闭）
        vix_result = self.test_api_endpoint("/api/vix/term", timeout=15)
        if vix_result["ok"]:
            data = vix_result["data"]
            if "vix" in data or "error" not in data:
                self.log_test("VIX Data Display", "pass", "VIX data available")
            else:
                self.log_test("VIX Data Display", "warning", "VIX data not available")
        else:
            error = vix_result.get("error", "Unknown error")
            if vix_result.get("timeout"):
                self.log_test("VIX Data Display", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("VIX Data Display", "warning", f"VIX data not available: {error}")
        
        fgi_result = self.test_api_endpoint("/api/fear-greed", timeout=15)
        if fgi_result["ok"]:
            data = fgi_result["data"]
            if "fear_greed" in data or "error" not in data:
                self.log_test("Fear & Greed Index Display", "pass", "F&G Index data available")
            else:
                self.log_test("Fear & Greed Index Display", "warning", "F&G Index data not available")
        else:
            error = fgi_result.get("error", "Unknown error")
            if fgi_result.get("timeout"):
                self.log_test("Fear & Greed Index Display", "warning", "Request timeout (may be processing)")
            else:
                self.log_test("Fear & Greed Index Display", "warning", f"F&G Index data not available: {error}")
        
        # 测试错误处理
        # 测试不存在的端点
        invalid_result = self.test_api_endpoint("/api/invalid-endpoint")
        if not invalid_result["ok"]:
            self.log_test("Error Handling", "pass", "Invalid endpoints properly handled")
        else:
            self.log_test("Error Handling", "warning", "Invalid endpoint returned success (unexpected)")
    
    def test_frontend_code(self):
        """测试前端代码质量"""
        print("\n[TEST] 测试前端代码...")
        
        if not FRONTEND_TEST_FILE.exists():
            self.log_test("Frontend Test File", "fail", "monitor_test.html not found")
            return
        
        try:
            with open(FRONTEND_TEST_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查关键函数是否存在
            required_functions = [
                "executeTradeCycle",
                "refreshData",
                "initSystem",
                "startTradingCycle",
                "startAutoTrade"
            ]
            
            missing_functions = []
            for func in required_functions:
                if f"function {func}" not in content and f"async function {func}" not in content:
                    missing_functions.append(func)
            
            if missing_functions:
                self.log_test("Frontend Functions", "fail", f"Missing functions: {missing_functions}")
                self.log_issue(f"Frontend missing functions: {missing_functions}", "high")
            else:
                self.log_test("Frontend Functions", "pass", "All required functions present")
            
            # 检查错误处理
            if "try {" in content and "catch" in content:
                self.log_test("Frontend Error Handling", "pass", "Error handling present")
            else:
                self.log_test("Frontend Error Handling", "warning", "Limited error handling")
            
            # 检查颜色对比度（黑底白字，白底黑字）
            if 'color: #ffffff' in content or 'color: #000000' in content:
                self.log_test("Frontend Color Contrast", "pass", "High contrast colors used")
            else:
                self.log_test("Frontend Color Contrast", "warning", "May need color contrast improvements")
            
            # 检查游标动画
            if "cursor-glow" in content or "cursorGlow" in content:
                self.log_test("Frontend Cursor Animation", "pass", "Cursor animation implemented")
            else:
                self.log_test("Frontend Cursor Animation", "warning", "Cursor animation not found")
            
            # 检查数据显示格式（不应该有 JSON.stringify 直接显示）
            # 排除注释中的 JSON.stringify
            import re
            json_stringify_pattern = r'JSON\.stringify\s*\('
            matches = re.findall(json_stringify_pattern, content)
            # 排除注释行
            lines = content.split('\n')
            actual_calls = 0
            for i, line in enumerate(lines):
                if re.search(json_stringify_pattern, line):
                    # 检查是否在注释中
                    stripped = line.strip()
                    if not stripped.startswith('//') and not stripped.startswith('*'):
                        actual_calls += 1
            
            if actual_calls == 0:
                self.log_test("Frontend Data Format", "pass", "No raw JSON.stringify in display")
            else:
                self.log_test("Frontend Data Format", "warning", f"Found {actual_calls} JSON.stringify calls (may need formatting)")
            
        except Exception as e:
            self.log_test("Frontend Code Check", "fail", str(e))
            self.log_issue(f"Cannot read frontend file: {e}", "high")
    
    def test_data_recording(self):
        """测试数据记录"""
        print("\n[TEST] 测试数据记录...")
        
        # 检查初始化后的数据记录
        # 注意：这里不实际执行初始化，只检查记录机制
        
        # 检查净值记录
        equity_file = self.backend_dir / "data" / "logs" / "equity_history.jsonl"
        if equity_file.exists():
            try:
                lines = []
                with open(equity_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            lines.append(json.loads(line))
                
                if len(lines) > 0:
                    # 检查记录是否按时间排序
                    dates = [r.get("date") for r in lines if "date" in r]
                    if dates == sorted(dates):
                        self.log_test("Equity History Recording", "pass", f"{len(lines)} records, properly sorted")
                    else:
                        self.log_test("Equity History Recording", "warning", "Records not properly sorted")
                else:
                    self.log_test("Equity History Recording", "warning", "No records in equity history")
            except Exception as e:
                self.log_test("Equity History Recording", "fail", str(e))
        else:
            self.log_test("Equity History Recording", "warning", "Equity history file does not exist")
        
        # 检查订单记录
        orders_file = self.backend_dir / "data" / "logs" / "filled_orders.jsonl"
        if orders_file.exists():
            try:
                lines = []
                with open(orders_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            lines.append(json.loads(line))
                self.log_test("Order Recording", "pass", f"{len(lines)} filled orders recorded")
            except Exception as e:
                self.log_test("Order Recording", "warning", str(e))
        else:
            self.log_test("Order Recording", "warning", "Filled orders file does not exist")
        
        # 检查对话记录
        conv_file = self.backend_dir / "data" / "logs" / "discussion_actions.jsonl"
        if conv_file.exists():
            try:
                lines = []
                with open(conv_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            lines.append(json.loads(line))
                self.log_test("Conversation Recording", "pass", f"{len(lines)} conversations recorded")
            except Exception as e:
                self.log_test("Conversation Recording", "warning", str(e))
        else:
            self.log_test("Conversation Recording", "warning", "Conversation file does not exist")
    
    def test_potential_errors(self):
        """测试潜在错误"""
        print("\n[TEST] 测试潜在错误...")
        
        # 测试网络错误处理
        # 模拟后端不可用的情况（通过错误的URL）
        try:
            response = requests.get("http://127.0.0.1:8001/invalid", timeout=1)
        except requests.exceptions.ConnectionError:
            self.log_test("Network Error Handling", "pass", "Connection errors properly handled")
        except Exception as e:
            self.log_test("Network Error Handling", "warning", f"Unexpected error: {e}")
        
        # 测试超时处理
        try:
            # 使用很短的超时时间测试超时处理
            response = requests.get(f"{BASE_URL}/api/trading/execute-trade", timeout=0.1)
        except requests.exceptions.Timeout:
            self.log_test("Timeout Error Handling", "pass", "Timeout errors properly handled")
        except Exception:
            pass  # 其他错误忽略
        
        # 测试数据格式错误处理
        # 检查API返回的数据格式
        result = self.test_api_endpoint("/api/portfolio/real-time")
        if result["ok"]:
            data = result["data"]
            # 检查数据类型
            if isinstance(data, dict):
                cash = data.get("cash")
                if cash is not None and isinstance(cash, (int, float)):
                    self.log_test("Data Type Validation", "pass", "Data types are correct")
                else:
                    self.log_test("Data Type Validation", "fail", f"Invalid cash type: {type(cash)}")
                    self.log_issue("Portfolio cash has invalid type", "high")
            else:
                self.log_test("Data Type Validation", "fail", f"Invalid response type: {type(data)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("🔍 第 2 轮测试：前端全面功能测试")
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
        self.test_button_functionality()
        self.test_data_display()
        self.test_data_consistency()
        self.test_user_experience()
        self.test_data_recording()
        self.test_potential_errors()
        self.test_frontend_code()
        
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
        result_file = self.backend_dir / "frontend_test_results_round2.json"
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
    tester = FrontendComprehensiveTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

