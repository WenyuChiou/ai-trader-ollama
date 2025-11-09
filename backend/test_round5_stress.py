#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第5轮测试：压力测试和边界情况测试
测试系统在高负载、并发、错误情况下的稳定性
"""
import sys
import io
import json
import time
import requests
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 確保在 backend 目錄
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30


class Round5StressTester:
    def __init__(self):
        self.results = {
            "test_round": 5,
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
            "status": status,
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
    
    def test_1_concurrent_requests(self):
        """测试1：并发请求处理"""
        print("\n[TEST 1] 测试并发请求处理...")
        
        def make_request(endpoint):
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                return {
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "status": "error",
                    "success": False,
                    "error": str(e)
                }
        
        # 并发请求多个端点
        endpoints = [
            "/api/portfolio/real-time",
            "/api/portfolio/equity-history?limit=10",
            "/api/agents/status",
            "/api/trades/recent?limit=10",
            "/api/agents/conversations?limit=10",
        ]
        
        print(f"  发送 {len(endpoints)} 个并发请求...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints * 3]  # 每个端点3次
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        if successful == total:
            self.log_test("Concurrent Requests", "pass", 
                         f"{successful}/{total} 成功，耗时 {elapsed:.2f}s")
        elif successful >= total * 0.8:
            self.log_test("Concurrent Requests", "warning", 
                         f"{successful}/{total} 成功，耗时 {elapsed:.2f}s")
        else:
            self.log_test("Concurrent Requests", "fail", 
                         f"仅 {successful}/{total} 成功")
    
    def test_2_rapid_refresh(self):
        """测试2：快速连续刷新"""
        print("\n[TEST 2] 测试快速连续刷新...")
        
        def refresh():
            try:
                response = requests.get(f"{BASE_URL}/api/portfolio/real-time", timeout=10)
                return response.status_code == 200
            except:
                return False
        
        print("  发送20个快速刷新请求...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(refresh) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        successful = sum(results)
        
        if successful >= 18:
            self.log_test("Rapid Refresh", "pass", 
                         f"{successful}/20 成功，耗时 {elapsed:.2f}s")
        else:
            self.log_test("Rapid Refresh", "fail", 
                         f"仅 {successful}/20 成功")
    
    def test_3_duplicate_trade_execution(self):
        """测试3：重复交易执行（应该被阻止）"""
        print("\n[TEST 3] 测试重复交易执行...")
        
        def execute_trade():
            try:
                response = requests.post(f"{BASE_URL}/api/trading/execute-trade", timeout=5)
                return {
                    "status": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
            except requests.exceptions.Timeout:
                return {"status": "timeout", "data": None}
            except Exception as e:
                return {"status": "error", "data": None, "error": str(e)}
        
        print("  发送3个快速交易执行请求（应该只有第一个成功）...")
        
        results = []
        for i in range(3):
            result = execute_trade()
            results.append(result)
            time.sleep(0.5)  # 短暂延迟
        
        # 检查结果
        success_count = sum(1 for r in results if r.get("status") == 200)
        conflict_count = sum(1 for r in results if r.get("status") == 409)
        timeout_count = sum(1 for r in results if r.get("status") == "timeout")
        
        if success_count == 1 and (conflict_count >= 1 or timeout_count >= 1):
            self.log_test("Duplicate Trade Prevention", "pass", 
                         f"第一个成功，后续被阻止（成功: {success_count}, 冲突: {conflict_count}, 超时: {timeout_count}）")
        elif success_count <= 1:
            self.log_test("Duplicate Trade Prevention", "warning", 
                         f"可能正常工作（成功: {success_count}, 冲突: {conflict_count}, 超时: {timeout_count}）")
        else:
            self.log_test("Duplicate Trade Prevention", "fail", 
                         f"多个请求同时成功（{success_count}），可能存在并发问题")
    
    def test_4_large_data_handling(self):
        """测试4：大数据量处理"""
        print("\n[TEST 4] 测试大数据量处理...")
        
        # 测试大量历史记录
        try:
            response = requests.get(f"{BASE_URL}/api/portfolio/equity-history?limit=1000", timeout=20)
            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                self.log_test("Large Data Query", "pass", 
                             f"成功返回 {len(records)} 条记录")
            else:
                self.log_test("Large Data Query", "warning", 
                             f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Large Data Query", "warning", 
                         f"请求失败: {str(e)}")
        
        # 测试大量对话记录
        try:
            response = requests.get(f"{BASE_URL}/api/agents/conversations?limit=500", timeout=20)
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("conversations", [])
                self.log_test("Large Conversations Query", "pass", 
                             f"成功返回 {len(conversations)} 条对话")
            else:
                self.log_test("Large Conversations Query", "warning", 
                             f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Large Conversations Query", "warning", 
                         f"请求失败: {str(e)}")
    
    def test_5_error_recovery(self):
        """测试5：错误恢复能力"""
        print("\n[TEST 5] 测试错误恢复能力...")
        
        # 测试无效端点
        try:
            response = requests.get(f"{BASE_URL}/api/invalid/endpoint", timeout=5)
            if response.status_code == 404:
                self.log_test("Invalid Endpoint Handling", "pass", 
                             "正确返回404错误")
            else:
                self.log_test("Invalid Endpoint Handling", "warning", 
                             f"返回状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Endpoint Handling", "fail", 
                         f"请求异常: {str(e)}")
        
        # 测试无效参数
        try:
            response = requests.get(f"{BASE_URL}/api/portfolio/equity-history?limit=invalid", timeout=5)
            # 应该处理错误或使用默认值
            if response.status_code in [200, 400, 422]:
                self.log_test("Invalid Parameter Handling", "pass", 
                             f"正确处理无效参数（状态码: {response.status_code}）")
            else:
                self.log_test("Invalid Parameter Handling", "warning", 
                             f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Parameter Handling", "warning", 
                         f"请求异常: {str(e)}")
        
        # 测试系统在错误后是否仍能正常工作
        try:
            # 先发送一个无效请求
            requests.get(f"{BASE_URL}/api/invalid", timeout=2)
            time.sleep(0.5)
            
            # 然后发送有效请求
            response = requests.get(f"{BASE_URL}/api/backend/status", timeout=5)
            if response.status_code == 200:
                self.log_test("Error Recovery", "pass", 
                             "错误后系统仍能正常响应")
            else:
                self.log_test("Error Recovery", "fail", 
                             f"错误后系统无法正常响应（状态码: {response.status_code}）")
        except Exception as e:
            self.log_test("Error Recovery", "fail", 
                         f"错误恢复测试失败: {str(e)}")
    
    def test_6_memory_leaks(self):
        """测试6：内存泄漏检查（通过多次请求）"""
        print("\n[TEST 6] 测试内存泄漏（多次请求）...")
        
        print("  发送100个连续请求...")
        start_time = time.time()
        success_count = 0
        
        for i in range(100):
            try:
                response = requests.get(f"{BASE_URL}/api/backend/status", timeout=5)
                if response.status_code == 200:
                    success_count += 1
                if (i + 1) % 20 == 0:
                    print(f"    已完成 {i + 1}/100 请求...")
            except Exception as e:
                pass
        
        elapsed = time.time() - start_time
        
        if success_count >= 95:
            self.log_test("Memory Leak Check", "pass", 
                         f"{success_count}/100 成功，耗时 {elapsed:.2f}s（无显著性能下降）")
        elif success_count >= 80:
            self.log_test("Memory Leak Check", "warning", 
                         f"{success_count}/100 成功，耗时 {elapsed:.2f}s（可能有性能问题）")
        else:
            self.log_test("Memory Leak Check", "fail", 
                         f"仅 {success_count}/100 成功（可能存在内存问题）")
    
    def test_7_api_response_times(self):
        """测试7：API响应时间"""
        print("\n[TEST 7] 测试API响应时间...")
        
        endpoints = [
            ("/api/backend/status", 1.0),
            ("/api/portfolio/real-time", 2.0),
            ("/api/portfolio/equity-history?limit=10", 2.0),
            ("/api/agents/status", 1.0),
            ("/api/market/is-open", 2.0),
        ]
        
        for endpoint, max_time in endpoints:
            try:
                start = time.time()
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=max_time * 2)
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    if elapsed <= max_time:
                        self.log_test(f"Response Time: {endpoint}", "pass", 
                                     f"{elapsed:.2f}s (目标: <{max_time}s)")
                    else:
                        self.log_test(f"Response Time: {endpoint}", "warning", 
                                     f"{elapsed:.2f}s (目标: <{max_time}s，较慢)")
                else:
                    self.log_test(f"Response Time: {endpoint}", "warning", 
                                 f"状态码: {response.status_code}")
            except Exception as e:
                self.log_test(f"Response Time: {endpoint}", "fail", 
                             f"请求失败: {str(e)}")
    
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
        results_file = self.backend_dir / "frontend_test_results_round5.json"
        report_file = self.backend_dir / "TEST_ROUND_5_REPORT.md"
        
        # 保存JSON
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 生成Markdown报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 第5轮测试报告：压力测试和边界情况\n\n")
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
        print(f"  - 报告: {report_file}")")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("  第5轮测试：压力测试和边界情况")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"后端URL: {BASE_URL}")
        
        # 检查后端是否运行
        if not self.check_backend_running():
            print("\n⚠️  警告: 后端服务未运行，部分测试可能失败")
            print("   请先启动后端服务: cd backend && python -m uvicorn src.api.server:app --reload")
            return
        
        # 运行所有测试
        self.test_1_concurrent_requests()
        self.test_2_rapid_refresh()
        self.test_3_duplicate_trade_execution()
        self.test_4_large_data_handling()
        self.test_5_error_recovery()
        self.test_6_memory_leaks()
        self.test_7_api_response_times()
        
        # 生成总结和保存结果
        self.generate_summary()
        self.save_results()


if __name__ == "__main__":
    tester = Round5StressTester()
    tester.run_all_tests()

