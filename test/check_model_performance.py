#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查模型性能的脚本
测试 deepseek-r1 模型的响应时间
"""
import time
import requests
import json
import sys
import os
from datetime import datetime

# 设置 Windows 终端编码
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def check_ollama_status():
    """检查 Ollama 服务状态"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"[OK] Ollama 服务运行中")
            print(f"   已安装的模型:")
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_gb = size / (1024**3) if size > 0 else 0
                print(f"   - {name} ({size_gb:.2f} GB)")
            return True
        else:
            print(f"[FAIL] Ollama 服务响应异常: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] 无法连接到 Ollama 服务 (http://localhost:11434)")
        print("   请确保 Ollama 正在运行")
        return False
    except Exception as e:
        print(f"[FAIL] 检查 Ollama 状态时出错: {e}")
        return False

def test_model_speed(model_name="deepseek-r1", test_prompt="Hello, how are you?"):
    """测试模型响应速度"""
    print(f"\n测试模型响应速度: {model_name}")
    print(f"测试提示: {test_prompt[:50]}...")
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": test_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 100,  # 限制生成长度以加快测试
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            tokens_per_second = result.get("eval_count", 0) / elapsed if elapsed > 0 else 0
            
            print(f"[OK] 响应时间: {elapsed:.2f} 秒")
            print(f"   生成 tokens: {result.get('eval_count', 0)}")
            print(f"   速度: {tokens_per_second:.2f} tokens/秒")
            print(f"   响应长度: {len(response_text)} 字符")
            
            if elapsed > 10:
                print(f"[WARNING] 响应时间较长 ({elapsed:.2f}秒)，可能影响 planning 速度")
            
            return elapsed
        else:
            print(f"[FAIL] 模型调用失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print(f"[FAIL] 模型调用超时（>30秒）")
        print("   这可能是 planning 慢的主要原因！")
        return None
    except Exception as e:
        print(f"[FAIL] 模型调用出错: {e}")
        return None

def estimate_planning_time():
    """估算 planning 所需时间"""
    print("\n估算 Planning 所需时间:")
    print("="*60)
    
    # Planning 流程中的 LLM 调用次数
    agents = [
        ("Market Analyst", 1),
        ("Technical Analyst", 1),
        ("Fundamental Analyst", 1),
        ("Sentiment Analyst", 1),
        ("Discussion Coordinator", 1),
        ("Risk Analyst", 1),
        ("Trader Agent", 1),
    ]
    
    # 假设每次调用需要 5-15 秒（取决于模型速度）
    avg_call_time = 10  # 秒
    tool_calls = 15  # tool_budget
    tool_call_time = 2  # 每个工具调用约 2 秒
    
    total_llm_time = sum(count * avg_call_time for _, count in agents)
    total_tool_time = tool_calls * tool_call_time
    market_data_time = 5  # 市场数据获取
    
    total_time = total_llm_time + total_tool_time + market_data_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"LLM 调用: {len(agents)} 个 agents × {avg_call_time}秒 = {total_llm_time}秒")
    print(f"工具调用: {tool_calls} 个 × {tool_call_time}秒 = {total_tool_time}秒")
    print(f"市场数据: {market_data_time}秒")
    print(f"总计: {total_time}秒 ({minutes}分{seconds}秒)")
    
    if total_time > 300:  # 5分钟
        print(f"\n[WARNING] Planning 预计需要 {minutes} 分钟，这是正常的")
        print("   如果实际时间远超此估算，可能是:")
        print("   1. 模型响应速度慢（检查 Ollama 配置）")
        print("   2. 网络延迟（工具调用）")
        print("   3. 模型超时设置过短（当前 8 秒）")

def main():
    print("="*60)
    print("  模型性能检查")
    print("="*60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查 Ollama 状态
    if not check_ollama_status():
        print("\n[ERROR] Ollama 服务未运行，无法继续测试")
        print("   请先启动 Ollama 服务")
        return 1
    
    # 2. 测试模型速度
    test_times = []
    for i in range(2):  # 测试 2 次取平均
        elapsed = test_model_speed("deepseek-r1", "分析一下当前市场趋势，用一句话回答。")
        if elapsed:
            test_times.append(elapsed)
        time.sleep(1)  # 等待 1 秒再测试
    
    if test_times:
        avg_time = sum(test_times) / len(test_times)
        print(f"\n平均响应时间: {avg_time:.2f} 秒")
        
        if avg_time > 15:
            print("\n[WARNING] 模型响应时间较长，这可能是 planning 慢的主要原因")
            print("   建议:")
            print("   1. 检查 Ollama 是否使用 GPU（GPU 会快很多）")
            print("   2. 检查系统资源（CPU/内存）是否充足")
            print("   3. 考虑使用更快的模型或减少 tool_budget")
        elif avg_time > 8:
            print("\n[INFO] 模型响应时间正常，但接近 timeout (8秒)")
            print("   建议: 考虑将 timeout_seconds 增加到 15-20 秒")
        else:
            print("\n[OK] 模型响应时间正常")
    
    # 3. 估算 planning 时间
    estimate_planning_time()
    
    return 0

if __name__ == "__main__":
    try:
        import sys
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

