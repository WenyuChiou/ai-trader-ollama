#!/usr/bin/env python3
"""
测试所有 Agent 是否可以正常创建和运行
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.factory import AgentFactory
from src.agents.base import BaseAgent


def test_agent_creation(agent_key: str, fac: AgentFactory) -> tuple[bool, str]:
    """测试单个 agent 的创建"""
    try:
        agent = fac.create(agent_key)
        if agent is None:
            return False, f"Agent '{agent_key}' creation returned None"
        if not isinstance(agent, BaseAgent):
            return False, f"Agent '{agent_key}' is not a BaseAgent instance"
        return True, f"Agent '{agent_key}' created successfully"
    except FileNotFoundError as e:
        return False, f"Agent '{agent_key}' - Missing file: {e}"
    except Exception as e:
        return False, f"Agent '{agent_key}' - Error: {type(e).__name__}: {e}"


def test_agent_run(agent_key: str, agent: BaseAgent, test_vars: dict) -> tuple[bool, str]:
    """测试单个 agent 的运行"""
    try:
        # 测试基本运行（不期望 JSON）
        result = agent.run(test_vars, expect_json=False)
        if result is None:
            return False, f"Agent '{agent_key}' run returned None"
        if not isinstance(result, str):
            return False, f"Agent '{agent_key}' run returned non-string: {type(result).__name__}"
        return True, f"Agent '{agent_key}' run successful (output length: {len(result)} chars)"
    except Exception as e:
        return False, f"Agent '{agent_key}' run error: {type(e).__name__}: {e}"


def main():
    print("\n" + "="*80)
    print(" ALL AGENTS VALIDATION TEST")
    print("="*80)
    
    # 读取 agents.yaml 获取所有 agent keys
    config_path = ROOT / "config" / "agents.yaml"
    if not config_path.exists():
        print(f"\n[FAIL] Config file not found: {config_path}")
        return False
    
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    # 获取所有 agent keys
    agent_keys = list(data.keys())
    print(f"\nFound {len(agent_keys)} agents in config:")
    for key in agent_keys:
        agent_info = data[key]
        name = agent_info.get("name", "Unknown")
        prompt_file = agent_info.get("prompt_file", "Unknown")
        print(f"  - {key}: {name} (prompt: {prompt_file})")
    
    # 创建 AgentFactory
    try:
        fac = AgentFactory(config_path=str(config_path))
        print(f"\n[OK] AgentFactory created successfully")
    except Exception as e:
        print(f"\n[FAIL] AgentFactory creation failed: {type(e).__name__}: {e}")
        return False
    
    # 准备测试变量
    test_vars = {
        "symbols": ["NVDA", "MSFT", "AAPL"],
        "start": "2024-01-01",
        "end": "2024-01-31",
        "market_view": {
            "stocks": {
                "NVDA": {"price": 150.0, "rsi14": 65.0, "macd": 2.5, "signal_score": 5.0},
                "MSFT": {"price": 380.0, "rsi14": 55.0, "macd": 1.2, "signal_score": 4.0},
                "AAPL": {"price": 180.0, "rsi14": 60.0, "macd": 0.8, "signal_score": 3.0},
            },
            "vix": {"level": 16.5, "chg_1d": 0.5, "zscore": 0.2},
        },
        "tools": ["news_scan", "vix_term", "fear_greed"],
        "tool_budget": 2,
        "preferred_domains": ["www.reuters.com", "www.ft.com"],
    }
    
    # 测试每个 agent
    print("\n" + "-"*80)
    print(" Testing Agent Creation and Run")
    print("-"*80)
    
    results = []
    for agent_key in agent_keys:
        print(f"\n[{agent_key}]")
        
        # 测试创建
        create_ok, create_msg = test_agent_creation(agent_key, fac)
        print(f"  Creation: {'[OK]' if create_ok else '[FAIL]'} {create_msg}")
        
        if not create_ok:
            results.append((agent_key, False, create_msg, None))
            continue
        
        # 测试运行
        try:
            agent = fac.create(agent_key)
            run_ok, run_msg = test_agent_run(agent_key, agent, test_vars)
            print(f"  Run:     {'[OK]' if run_ok else '[FAIL]'} {run_msg}")
            results.append((agent_key, create_ok and run_ok, create_msg, run_msg))
        except Exception as e:
            print(f"  Run:     [FAIL] Could not get agent instance: {e}")
            results.append((agent_key, False, create_msg, f"Could not get agent: {e}"))
    
    # 总结
    print("\n" + "="*80)
    print(" TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results if r[1])
    failed = total - passed
    
    print(f"\nTotal Agents: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print(f"\n[FAIL] Failed Agents:")
        for agent_key, passed, create_msg, run_msg in results:
            if not passed:
                print(f"  - {agent_key}")
                print(f"    Creation: {create_msg}")
                if run_msg:
                    print(f"    Run: {run_msg}")
    
    # 检查 prompt 文件
    print("\n" + "-"*80)
    print(" Checking Prompt Files")
    print("-"*80)
    
    prompts_dir = ROOT / "prompts"
    missing_prompts = []
    
    for agent_key in agent_keys:
        agent_info = data[agent_key]
        prompt_file = agent_info.get("prompt_file", "")
        
        # 处理相对路径（按照 factory._load_prompts 的逻辑）
        # factory 会先尝试 config_path.parent / prompt_file，如果不存在再尝试 prompts_dir / Path(prompt_file).name
        if prompt_file.startswith("../"):
            # ../prompts/xxx.yml -> prompts/xxx.yml
            prompt_path = prompts_dir / Path(prompt_file).name
        elif prompt_file.startswith("prompts/"):
            prompt_path = prompts_dir / prompt_file.replace("prompts/", "")
        else:
            prompt_path = prompts_dir / prompt_file
        
        if not prompt_path.exists():
            missing_prompts.append((agent_key, prompt_file, prompt_path))
            print(f"  [MISSING] {agent_key}: {prompt_file} -> {prompt_path}")
        else:
            print(f"  [OK] {agent_key}: {prompt_path}")
    
    if missing_prompts:
        print(f"\n[FAIL] Missing {len(missing_prompts)} prompt files")
        return False
    
    print(f"\n[OK] All prompt files exist")
    
    # 最终结果
    all_ok = passed == total and len(missing_prompts) == 0
    
    print("\n" + "="*80)
    if all_ok:
        print("[SUCCESS] All agents validated successfully!")
    else:
        print("[FAIL] Some agents failed validation")
    print("="*80 + "\n")
    
    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

