# src/agents/factory.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import yaml

from src.agents.base import AgentSpec, BaseAgent
from src.llm.ollama_client import get_llm
from langchain_ollama import ChatOllama


def _load_llm_config_from_json() -> dict:
    """Load LLM config from config.json"""
    try:
        # Path 已经在文件顶部导入，不需要重复导入
        import json
        config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("llm", {})
    except Exception:
        pass
    return {}


class AgentFactory:
    def __init__(self, config_path: Optional[str|Path]=None, llm_client=None):
        # 預設讀 config/agents.yaml
        if config_path:
            self.config_path = Path(config_path)
            if not self.config_path.is_absolute():
                # 如果是相对路径，尝试多个可能的基础路径
                possible_bases = [
                    Path.cwd(),  # 当前工作目录
                    Path(__file__).parent.parent.parent,  # backend/ 目录
                ]
                for base in possible_bases:
                    candidate = (base / self.config_path).resolve()
                    if candidate.exists():
                        self.config_path = candidate
                        break
        else:
            # 尝试多个可能的路径
            possible_paths = [
                Path(__file__).parent.parent.parent / "config" / "agents.yaml",  # backend/config/agents.yaml（优先）
                Path.cwd() / "config" / "agents.yaml",  # 相对于当前工作目录
                Path("config/agents.yaml"),  # 相对于当前工作目录（备用）
            ]
            self.config_path = None
            for path in possible_paths:
                abs_path = path.resolve() if path.is_absolute() or path.exists() else Path.cwd() / path
                if abs_path.exists():
                    self.config_path = abs_path
                    break
            if self.config_path is None:
                # 如果都找不到，使用默认路径（但可能会失败）
                self.config_path = possible_paths[0]
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"agents config not found: {self.config_path}. Tried: {possible_paths}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 支持扁平结构（agents直接在根级别）和嵌套结构（有agents键）
        self._agents = data.get("agents", data)  # 如果没有agents键，直接使用整个data
        self._llm_client = llm_client

    def _load_prompts(self, prompt_file: str) -> Tuple[str, str]:
        # 统一使用项目根目录的 prompts/ 文件夹
        # 支持 agents.yaml 内写 ../prompts/xxx.yml 或 prompts/xxx.yml
        # 统一解析到项目根目录的 prompts/ 文件夹
        
        # 提取文件名（去掉路径前缀）
        prompt_filename = Path(prompt_file).name
        
        # 优先使用项目根目录的 prompts/ 文件夹
        # config_path 通常是 backend/config/agents.yaml
        # 所以 parent.parent.parent 是项目根目录
        root_prompts_dir = self.config_path.parent.parent.parent / "prompts"
        p = (root_prompts_dir / prompt_filename).resolve()
        
        if not p.exists():
            # 备用：尝试相对于 config 文件的路径（向后兼容）
            if prompt_file.startswith("../"):
                # 处理 ../prompts/xxx.yml
                p = (self.config_path.parent.parent / prompt_file[3:]).resolve()
            else:
                # 处理 prompts/xxx.yml 或相对路径
                p = (self.config_path.parent / prompt_file).resolve()
        
        if not p.exists():
            # 最后尝试：相对于当前工作目录
            p = Path(prompt_file).resolve()
        
        if not p.exists():
            raise FileNotFoundError(
                f"prompt file not found: {prompt_file}. "
                f"Tried: {root_prompts_dir / prompt_filename}, {p}. "
                f"Please ensure the file exists in the root prompts/ folder."
            )
        
        with open(p, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
        return (y.get("system", "") or "").strip(), (y.get("user", "") or "").strip()

    def create(self, agent_key: str) -> BaseAgent:
        if agent_key not in self._agents:
            raise KeyError(f"Agent key not found in config: {agent_key}")

        conf = self._agents[agent_key]
        system, user = self._load_prompts(conf["prompt_file"])
        
        # Load LLM config from config.json for defaults
        llm_config = _load_llm_config_from_json()
        
        # Model priority: agents.yaml > config.json llm.default_model > "llama3.1"
        model = conf.get("model") or llm_config.get("default_model") or "llama3.1"
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
        # get_llm will automatically use config.json settings for base_url and default_model
        llm = self._llm_client
        if llm is None:
            llm = get_llm(model=model, temperature=temperature)
        
        return BaseAgent(spec, llm)
