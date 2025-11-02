#!/usr/bin/env python3
"""
依赖关系分析脚本
分析项目的导入依赖，生成依赖图
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def parse_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """解析 Python 文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        imports = []
        from_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    from_imports.append(node.module)
        
        return imports, from_imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], []


def analyze_dependencies(root_dir: Path = Path("src")) -> Dict[str, Set[str]]:
    """分析目录中的所有依赖关系"""
    dependencies: Dict[str, Set[str]] = defaultdict(set)
    
    for py_file in root_dir.rglob("*.py"):
        rel_path = py_file.relative_to(root_dir)
        module_name = str(rel_path.with_suffix("")).replace(os.sep, ".")
        
        imports, from_imports = parse_imports(py_file)
        
        # 只关注内部导入（src.*）
        for imp in imports:
            if imp.startswith("src."):
                dependencies[module_name].add(imp)
        
        for imp in from_imports:
            if imp.startswith("src."):
                dependencies[module_name].add(imp)
    
    return dict(dependencies)


def generate_dependency_report(deps: Dict[str, Set[str]]) -> str:
    """生成依赖关系报告"""
    report = ["# 依赖关系分析报告\n"]
    report.append("## 模块依赖图\n\n")
    
    # 按模块分组
    modules = sorted(deps.keys())
    
    report.append("### 依赖统计\n\n")
    report.append(f"- 总模块数: {len(modules)}\n")
    report.append(f"- 总依赖数: {sum(len(v) for v in deps.values())}\n\n")
    
    report.append("### 详细依赖\n\n")
    for module in modules:
        if deps[module]:
            report.append(f"#### {module}\n\n")
            for dep in sorted(deps[module]):
                report.append(f"- `{dep}`\n")
            report.append("\n")
    
    # 反向依赖（哪些模块依赖某个模块）
    report.append("### 反向依赖（被依赖关系）\n\n")
    reverse_deps: Dict[str, Set[str]] = defaultdict(set)
    for module, deps_set in deps.items():
        for dep in deps_set:
            # 提取被依赖的模块名（简化）
            dep_module = dep.replace("src.", "")
            reverse_deps[dep_module].add(module)
    
    for dep_module in sorted(reverse_deps.keys()):
        if reverse_deps[dep_module]:
            report.append(f"#### {dep_module}\n\n")
            report.append("被以下模块依赖:\n")
            for module in sorted(reverse_deps[dep_module]):
                report.append(f"- `{module}`\n")
            report.append("\n")
    
    return "".join(report)


def main():
    """主函数"""
    root = Path("src")
    if not root.exists():
        print(f"Error: {root} directory not found")
        return
    
    print("分析依赖关系...")
    deps = analyze_dependencies(root)
    
    print(f"找到 {len(deps)} 个模块")
    print(f"总依赖数: {sum(len(v) for v in deps.values())}")
    
    # 生成报告
    report = generate_dependency_report(deps)
    
    # 保存报告
    output_file = Path("DEPENDENCY_ANALYSIS.md")
    output_file.write_text(report, encoding="utf-8")
    print(f"\n报告已保存到: {output_file}")
    
    # 输出关键依赖
    print("\n=== 关键入口点 ===")
    entry_points = [
        "orchestrator.trading_cycle",
        "agents.factory",
        "agents.toolbox",
        "agents.base",
    ]
    for ep in entry_points:
        if ep in deps:
            print(f"\n{ep}:")
            for dep in sorted(deps[ep]):
                print(f"  -> {dep}")


if __name__ == "__main__":
    main()

