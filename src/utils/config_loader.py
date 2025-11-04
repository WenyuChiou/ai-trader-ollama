# src/utils/config_loader.py
"""
Configuration loader for centralized config management
Loads config.json and agents.yaml, merges LLM settings
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.json"
DEFAULT_AGENTS_PATH = Path(__file__).resolve().parents[2] / "config" / "agents.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load config.json
    
    Returns:
        Dict with all config values
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config


def load_agents_config(agents_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load agents.yaml
    
    Returns:
        Dict with agent configurations
    """
    if agents_path is None:
        agents_path = DEFAULT_AGENTS_PATH
    
    if not agents_path.exists():
        raise FileNotFoundError(f"Agents config file not found: {agents_path}")
    
    with agents_path.open("r", encoding="utf-8") as f:
        agents_config = yaml.safe_load(f) or {}
    
    return agents_config


def get_llm_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get LLM configuration, merging config.json and environment variables
    
    Priority:
    1. Environment variables (OLLAMA_HOST, OLLAMA_MODEL)
    2. config.json "llm" section
    3. Default values
    
    Returns:
        Dict with llm settings:
        - model: str
        - base_url: str
        - auto_pull: bool
        - timeout_seconds: float
    """
    if config is None:
        config = load_config()
    
    llm_config = config.get("llm", {})
    
    # Environment variables take highest priority
    base_url = os.getenv("OLLAMA_HOST") or llm_config.get("ollama_host") or "http://localhost:11434"
    model = os.getenv("OLLAMA_MODEL") or llm_config.get("default_model") or "llama3.1"
    auto_pull = llm_config.get("auto_pull", True)
    timeout_seconds = float(llm_config.get("timeout_seconds", 8.0))
    
    return {
        "model": model,
        "base_url": base_url,
        "auto_pull": auto_pull,
        "timeout_seconds": timeout_seconds,
    }


def get_agent_model(agent_name: str, agents_config: Optional[Dict[str, Any]] = None, 
                    default_model: Optional[str] = None) -> str:
    """
    Get model for specific agent, with fallback chain:
    1. agents.yaml [agent_name].model
    2. config.json llm.default_model
    3. default_model parameter
    4. "llama3.1"
    
    Returns:
        Model name string
    """
    if agents_config is None:
        agents_config = load_agents_config()
    
    if default_model is None:
        config = load_config()
        default_model = get_llm_config(config).get("model", "llama3.1")
    
    agent_config = agents_config.get(agent_name, {})
    return agent_config.get("model") or default_model

