#!/usr/bin/env python3
"""
验证生成的summary长度：
检查discussion_actions.jsonl中的analysis字段是否达到500字
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
    log_file = current_dir.parent / 'backend' / 'data' / 'logs' / 'discussion_actions.jsonl'
else:
    log_file = Path(__file__).parent / 'backend' / 'data' / 'logs' / 'discussion_actions.jsonl'

print("=" * 80)
print("验证Summary长度")
print("=" * 80)
print(f"日志文件: {log_file}")
print()

if not log_file.exists():
    print(f"❌ 日志文件不存在: {log_file}")
    print("   提示: 请先运行交易周期生成日志")
    sys.exit(1)

# 读取日志文件
print("【读取日志文件】")
print("-" * 80)
entries = []
try:
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    
    print(f"✅ 成功读取 {len(entries)} 条记录")
    print()
except Exception as e:
    print(f"❌ 读取日志文件失败: {e}")
    sys.exit(1)

# 分析discussion类型的entry
print("【分析Discussion条目】")
print("-" * 80)
discussion_entries = [e for e in entries if e.get('type') == 'discussion']
print(f"找到 {len(discussion_entries)} 条discussion记录")
print()

if len(discussion_entries) == 0:
    print("⚠️  没有找到discussion记录")
    print("   提示: 请先运行交易周期")
    sys.exit(0)

# 检查每条记录的analysis长度
print("【检查Analysis长度】")
print("-" * 80)
results = []
for entry in discussion_entries:
    agent = entry.get('agent', 'Unknown')
    date = entry.get('date', 'N/A')
    analysis = entry.get('analysis', '')
    content = entry.get('content', '')
    
    # 使用analysis字段，如果没有则使用content
    text = analysis if analysis else content
    
    # 计算字符数和字数（英文单词数）
    char_count = len(text)
    word_count = len(text.split()) if text else 0
    
    # 估算中文字数（中文字符数）
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    estimated_words = word_count + chinese_chars  # 英文单词数 + 中文字符数
    
    results.append({
        'agent': agent,
        'date': date,
        'char_count': char_count,
        'word_count': word_count,
        'chinese_chars': chinese_chars,
        'estimated_words': estimated_words,
        'text_preview': text[:100] + '...' if len(text) > 100 else text,
    })
    
    # 判断是否达到500字
    status = "✅" if estimated_words >= 450 else "⚠️"
    print(f"{status} {agent} ({date}):")
    print(f"   字符数: {char_count}")
    print(f"   英文单词数: {word_count}")
    print(f"   中文字符数: {chinese_chars}")
    print(f"   估算总字数: {estimated_words}")
    print(f"   预览: {results[-1]['text_preview']}")
    print()

# 统计
print("【统计】")
print("-" * 80)
total_entries = len(results)
meets_requirement = sum(1 for r in results if r['estimated_words'] >= 450)
avg_words = sum(r['estimated_words'] for r in results) / total_entries if total_entries > 0 else 0
avg_chars = sum(r['char_count'] for r in results) / total_entries if total_entries > 0 else 0

print(f"总记录数: {total_entries}")
print(f"达到450字要求: {meets_requirement} ({meets_requirement/total_entries*100:.1f}%)")
print(f"平均字数: {avg_words:.1f}")
print(f"平均字符数: {avg_chars:.1f}")
print()

# 按agent分组统计
print("【按Agent分组】")
print("-" * 80)
agent_stats = {}
for r in results:
    agent = r['agent']
    if agent not in agent_stats:
        agent_stats[agent] = {
            'count': 0,
            'total_words': 0,
            'total_chars': 0,
            'meets_requirement': 0,
        }
    agent_stats[agent]['count'] += 1
    agent_stats[agent]['total_words'] += r['estimated_words']
    agent_stats[agent]['total_chars'] += r['char_count']
    if r['estimated_words'] >= 450:
        agent_stats[agent]['meets_requirement'] += 1

for agent, stats in agent_stats.items():
    avg_w = stats['total_words'] / stats['count'] if stats['count'] > 0 else 0
    avg_c = stats['total_chars'] / stats['count'] if stats['count'] > 0 else 0
    meets_pct = stats['meets_requirement'] / stats['count'] * 100 if stats['count'] > 0 else 0
    status = "✅" if avg_w >= 450 else "⚠️"
    print(f"{status} {agent}:")
    print(f"   记录数: {stats['count']}")
    print(f"   平均字数: {avg_w:.1f}")
    print(f"   平均字符数: {avg_c:.1f}")
    print(f"   达到要求: {stats['meets_requirement']}/{stats['count']} ({meets_pct:.1f}%)")
    print()

print("=" * 80)
print("验证完成")
print("=" * 80)
print("目标: 所有analysis应该达到约500字（450-550字）")
print(f"当前: {meets_requirement}/{total_entries} 条记录达到要求")
print()

if meets_requirement == total_entries:
    print("✅ 所有记录都达到500字要求！")
elif meets_requirement >= total_entries * 0.8:
    print("⚠️  大部分记录达到要求，但仍有改进空间")
else:
    print("❌ 大部分记录未达到要求，需要检查prompt和生成逻辑")
print()


