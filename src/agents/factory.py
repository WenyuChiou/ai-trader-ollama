# src/agents/factory.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import yaml

from src.agents.base import AgentSpec, BaseAgent
from src.llm.ollama_client import get_llm
from langchain_ollama import ChatOllama


class AgentFactory:
    def __init__(self, config_path: Optional[str|Path]=None, llm_client=None):
        # 預設讀 config/agents.yaml
        self.config_path = Path(config_path) if config_path else Path("config/agents.yaml")
        if not self.config_path.exists():
            raise FileNotFoundError(f"agents config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 支持扁平结构（agents直接在根级别）和嵌套结构（有agents键）
        self._agents = data.get("agents", data)  # 如果没有agents键，直接使用整个data
        self._llm_client = llm_client

    def _load_prompts(self, prompt_file: str) -> Tuple[str, str]:
        # 支援 agents.yaml 內寫 ../prompts/xxx.yml 或 prompts/xxx.yml
        p = (self.config_path.parent / prompt_file).resolve()
        if not p.exists():
            # 也尝试相对于项目根目录的 prompts 目录
            prompts_dir = self.config_path.parent.parent / "prompts"
            p = (prompts_dir / Path(prompt_file).name).resolve()
        if not p.exists():
            raise FileNotFoundError(f"prompt file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
        return (y.get("system", "") or "").strip(), (y.get("user", "") or "").strip()

    def create(self, agent_key: str) -> BaseAgent:
        if agent_key not in self._agents:
            raise KeyError(f"Agent key not found in config: {agent_key}")

        conf = self._agents[agent_key]
        system, user = self._load_prompts(conf["prompt_file"])
        
        model = conf.get("model", "llama3.1")
        temperature = float(conf.get("temperature", 0.2))
        prompt_file = conf.get("prompt_file", "")

        # 使用正确的 AgentSpec 字段名（name, model, prompt_file, temperature, system, user）
        spec = AgentSpec(
            name=agent_key,
            model=model,
            prompt_file=prompt_file,
            temperature=temperature,
            system=system,
            user=user,
        )
        
        # 如果没有提供 llm_client，使用 get_llm 创建
        llm = self._llm_client
        if llm is None:
            llm = get_llm(model=model, temperature=temperature)
        
        return BaseAgent(spec, llm)
