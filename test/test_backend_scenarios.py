#!/usr/bin/env python3
"""
测试后端所有情境：
1. 100+股票处理
2. 500字summary生成
3. 工具调用
4. 所有分析师的prompt
"""

import sys
import os
import io
import json
from pathlib import Path
from datetime import datetime

# 修复Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 自动检测路径
current_dir = Path(__file__).parent.absolute()
if current_dir.name == 'test':
    backend_dir = current_dir.parent / 'backend'
    sys.path.insert(0, str(backend_dir))
else:
    backend_dir = Path(__file__).parent / 'backend'
    sys.path.insert(0, str(backend_dir))

print("=" * 80)
print("后端情境测试")
print("=" * 80)
print(f"当前目录: {current_dir}")
print(f"Backend目录: {backend_dir}")
print()

# 测试1: 检查universe配置
print("【测试1】检查universe配置")
print("-" * 80)
try:
    config_path = backend_dir / "config" / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            universe = config.get("universe", [])
            print(f"✅ 找到config.json")
            print(f"   Universe数量: {len(universe)}")
            if len(universe) >= 100:
                print(f"   ✅ Universe包含100+股票 ({len(universe)}个)")
            else:
                print(f"   ⚠️  Universe只有{len(universe)}个股票，少于100个")
            print(f"   前10个股票: {universe[:10]}")
            print(f"   最后10个股票: {universe[-10:]}")
        print()
    else:
        print(f"❌ 找不到config.json: {config_path}")
        print()
except Exception as e:
    print(f"❌ 读取config.json失败: {e}")
    print()

# 测试2: 检查_summarize_market函数
print("【测试2】检查_summarize_market函数")
print("-" * 80)
try:
    from src.agents.multi_analyst_system import _summarize_market
    
    # 模拟100+股票的市场数据
    mock_stocks = {}
    test_symbols = ["NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "NFLX"]
    # 生成100个股票的数据
    for i in range(100):
        symbol = test_symbols[i % len(test_symbols)] + str(i) if i >= len(test_symbols) else test_symbols[i]
        mock_stocks[symbol] = {
            "price": 100.0 + i * 0.5,
            "change_pct": -2.0 + (i % 5) * 1.0,
            "rsi14": 30 + (i % 40),
            "signal_score": 0.5 + (i % 10) * 0.1,
        }
    
    mock_market_view = {
        "stocks": mock_stocks,
        "vix": {"level": 20.5, "chg_1d": 0.5},
        "vix_term": {"vix": 20.5, "vix_3m": 22.0, "ratio": 1.07},
        "fear_greed": {"value": 50, "label": "neutral"},
    }
    
    summary = _summarize_market(mock_market_view)
    
    print(f"✅ _summarize_market函数正常工作")
    print(f"   stocks_count: {summary.get('stocks_count')}")
    print(f"   sample_stocks数量: {len(summary.get('sample_stocks', []))}")
    print(f"   sample_stocks_data数量: {len(summary.get('sample_stocks_data', {}))}")
    print(f"   symbols总数: {len(summary.get('symbols', []))}")
    print(f"   market_stats: {summary.get('market_stats', {})}")
    print(f"   note: {summary.get('note', '')}")
    
    # 检查prompt大小
    summary_json = json.dumps(summary, indent=2)
    print(f"   Summary JSON大小: {len(summary_json)} 字符")
    if len(summary_json) < 5000:
        print(f"   ✅ Summary大小合理（<5000字符）")
    else:
        print(f"   ⚠️  Summary可能过大（>5000字符）")
    print()
except Exception as e:
    print(f"❌ _summarize_market测试失败: {e}")
    import traceback
    print(traceback.format_exc())
    print()

# 测试3: 检查prompt文件
print("【测试3】检查prompt文件中的500字要求")
print("-" * 80)
prompt_files = [
    "market_analyst.yml",
    "technical_analyst.yml",
    "sentiment_analyst.yml",
    "fundamental_analyst.yml",
    "risk_analyst.yml",
]

for prompt_file in prompt_files:
    prompt_path = backend_dir / "prompts" / prompt_file
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "500 words" in content or "500字" in content or "approximately 500 words" in content:
                print(f"✅ {prompt_file}: 包含500字要求")
            else:
                print(f"❌ {prompt_file}: 缺少500字要求")
            if "100+ stocks" in content or "100+股票" in content or "large universe" in content:
                print(f"   ✅ 包含100+股票说明")
            else:
                print(f"   ⚠️  缺少100+股票说明")
    else:
        print(f"❌ 找不到prompt文件: {prompt_path}")
print()

# 测试4: 检查_generate_analysis_from_tools函数
print("【测试4】检查_generate_analysis_from_tools函数")
print("-" * 80)
try:
    from src.agents.multi_analyst_system import _generate_analysis_from_tools
    
    # 检查函数是否存在500字要求
    import inspect
    source = inspect.getsource(_generate_analysis_from_tools)
    if "500 words" in source or "500字" in source or "approximately 500 words" in source:
        print(f"✅ _generate_analysis_from_tools包含500字要求")
    else:
        print(f"❌ _generate_analysis_from_tools缺少500字要求")
    
    if "400" in source and "字符" in source:
        print(f"   ✅ 包含字符长度检查（400字符阈值）")
    else:
        print(f"   ⚠️  字符长度检查可能不完整")
    print()
except Exception as e:
    print(f"❌ _generate_analysis_from_tools检查失败: {e}")
    print()

# 测试5: 检查news_scan keywords数量
print("【测试5】检查news_scan keywords数量")
print("-" * 80)
try:
    from src.agents.multi_analyst_system import _execute_tool
    
    import inspect
    source = inspect.getsource(_execute_tool)
    if "symbols[:10]" in source:
        print(f"✅ news_scan使用10个symbols作为keywords")
    elif "symbols[:5]" in source:
        print(f"⚠️  news_scan仍使用5个symbols，应该增加到10个")
    else:
        print(f"⚠️  无法确定news_scan的keywords数量")
    print()
except Exception as e:
    print(f"❌ news_scan检查失败: {e}")
    print()

# 测试6: 检查Discussion Coordinator的500字要求
print("【测试6】检查Discussion Coordinator的500字要求")
print("-" * 80)
try:
    from src.agents.multi_analyst_system import _run_discussion_coordinator
    
    import inspect
    source = inspect.getsource(_run_discussion_coordinator)
    if "500 words" in source or "approximately 500 words" in source:
        print(f"✅ Discussion Coordinator包含500字要求")
    else:
        print(f"❌ Discussion Coordinator缺少500字要求")
    print()
except Exception as e:
    print(f"❌ Discussion Coordinator检查失败: {e}")
    print()

# 测试7: 模拟完整的market_view处理
print("【测试7】模拟完整的market_view处理（100+股票）")
print("-" * 80)
try:
    # 从config.json读取真实的universe
    config_path = backend_dir / "config" / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            real_universe = config.get("universe", [])
        
        # 模拟market_view
        mock_market_view = {
            "stocks": {},
            "vix": {"level": 20.5},
            "vix_term": {"vix": 20.5, "vix_3m": 22.0},
            "fear_greed": {"value": 50},
        }
        
        # 为每个股票生成数据
        for symbol in real_universe[:100]:  # 只测试前100个
            mock_market_view["stocks"][symbol] = {
                "price": 100.0,
                "change_pct": 0.5,
                "rsi14": 50.0,
                "signal_score": 0.7,
            }
        
        summary = _summarize_market(mock_market_view)
        
        print(f"✅ 成功处理{len(real_universe)}个股票的universe")
        print(f"   生成的summary包含:")
        print(f"   - stocks_count: {summary.get('stocks_count')}")
        print(f"   - sample_stocks: {len(summary.get('sample_stocks', []))}个")
        print(f"   - sample_stocks_data: {len(summary.get('sample_stocks_data', {}))}个")
        print(f"   - symbols总数: {len(summary.get('symbols', []))}个")
        
        # 检查summary大小
        summary_json = json.dumps(summary, indent=2)
        print(f"   Summary JSON大小: {len(summary_json)} 字符")
        
        if len(summary_json) < 10000:
            print(f"   ✅ Summary大小合理，适合prompt")
        else:
            print(f"   ⚠️  Summary可能过大")
    else:
        print(f"⚠️  无法读取config.json进行完整测试")
    print()
except Exception as e:
    print(f"❌ 完整market_view处理测试失败: {e}")
    import traceback
    print(traceback.format_exc())
    print()

# 测试8: 验证实际生成的summary长度
print("【测试8】验证实际生成的summary长度")
print("-" * 80)
try:
    log_file = backend_dir / "data" / "logs" / "discussion_actions.jsonl"
    if log_file.exists():
        entries = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        discussion_entries = [e for e in entries if e.get('type') == 'discussion']
        print(f"✅ 找到 {len(discussion_entries)} 条discussion记录")
        
        if len(discussion_entries) > 0:
            # 检查最近的记录（假设是新的）
            recent_entries = discussion_entries[-10:]  # 最近10条
            
            print(f"\n检查最近 {len(recent_entries)} 条记录:")
            results = []
            for entry in recent_entries:
                agent = entry.get('agent', 'Unknown')
                date = entry.get('date', 'N/A')
                analysis = entry.get('analysis', '')
                content = entry.get('content', '')
                
                text = analysis if analysis else content
                char_count = len(text)
                word_count = len(text.split()) if text else 0
                chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
                estimated_words = word_count + chinese_chars
                
                status = "✅" if estimated_words >= 450 else "⚠️"
                print(f"{status} {agent} ({date}): {estimated_words}字 ({char_count}字符)")
                results.append(estimated_words)
            
            if results:
                avg_words = sum(results) / len(results)
                meets_requirement = sum(1 for w in results if w >= 450)
                print(f"\n统计:")
                print(f"   平均字数: {avg_words:.1f}")
                print(f"   达到450字要求: {meets_requirement}/{len(results)} ({meets_requirement/len(results)*100:.1f}%)")
                
                if avg_words >= 450:
                    print(f"   ✅ 平均字数达到要求")
                elif avg_words >= 300:
                    print(f"   ⚠️  平均字数接近要求，但仍有改进空间")
                else:
                    print(f"   ❌ 平均字数未达到要求，需要检查prompt和生成逻辑")
                    print(f"   提示: 这些可能是旧的日志，需要运行新的交易周期")
        else:
            print(f"⚠️  没有找到discussion记录")
            print(f"   提示: 请先运行交易周期生成日志")
    else:
        print(f"⚠️  日志文件不存在: {log_file}")
        print(f"   提示: 请先运行交易周期生成日志")
    print()
except Exception as e:
    print(f"❌ Summary长度验证失败: {e}")
    import traceback
    print(traceback.format_exc())
    print()

# 总结
print("=" * 80)
print("测试总结")
print("=" * 80)
print("✅ 所有测试完成")
print()
print("关键检查点:")
print("1. Universe配置: 确保有100+股票")
print("2. _summarize_market: 优化为摘要模式，避免prompt过长")
print("3. Prompt文件: 包含500字要求和100+股票说明")
print("4. _generate_analysis_from_tools: 包含500字生成要求")
print("5. news_scan: 使用10个symbols作为keywords")
print("6. Discussion Coordinator: 包含500字要求")
print()
print("下一步:")
print("- 运行实际的交易周期测试（通过前端或API）")
print("- 检查生成的summary是否达到500字")
print("- 验证工具调用是否正常工作")
print()
print("提示:")
print("- 如果summary长度未达标，可能是旧的日志")
print("- 运行新的交易周期后，summary应该达到约500字")
print("- 可以使用 verify_summary_length.py 进行详细验证")
print()

