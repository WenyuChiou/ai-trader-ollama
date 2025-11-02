# src/agents/multi_agent_discussion.py
"""
真正的多 Agent 讨论系统
多个独立的 Analyst Agents 进行多轮讨论，最终形成共识

注意：此文件已迁移到 backend/src/agents/multi_agent_discussion.py
这里保留作为备份或向后兼容使用
"""
from __future__ import annotations
import sys
from pathlib import Path

# 尝试从 backend 目录导入
try:
    backend_path = Path(__file__).resolve().parent.parent.parent / "backend" / "src"
    if backend_path.exists() and str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    from agents.multi_agent_discussion import (
        run_multi_agent_discussion as _run_multi_agent_discussion,
    )
    
    # 重新导出主要函数
    def run_multi_agent_discussion(*args, **kwargs):
        """调用 backend 目录中的多 Agent 讨论系统"""
        return _run_multi_agent_discussion(*args, **kwargs)
except ImportError:
    # 如果无法导入，创建一个占位符函数
    def run_multi_agent_discussion(*args, **kwargs):
        """多 Agent 讨论系统未在此目录实现，请使用 backend/src/agents/multi_agent_discussion.py"""
        raise ImportError(
            "Multi-agent discussion system not available in src directory. "
            "Please use backend/src/agents/multi_agent_discussion.py instead."
        )

