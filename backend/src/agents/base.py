# src/agents/base.py
"""
Base agent classes and utilities.
This is a stable core module used by other agent implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from src.utils.validators import ensure_valid_json, try_parse_json

@dataclass
class AgentSpec:
    """
    統一的代理規格定義。注意：接受 name 參數，與 factory.create() 對齊。
    - name         : 代理鍵名（如 market_agent / risk_analyst）
    - model        : Ollama 模型名（如 "llama3.1"）
    - prompt_file  : 對應的 prompt 檔案（僅做記錄；實際 system/user 字串在建立後灌入）
    - temperature  : LLM 溫度
    - system       : render 後的 system prompt
    - user         : render 後的 user prompt
    """
    name: str
    model: str
    prompt_file: str
    temperature: float = 0.2
    system: str = ""
    user: str = ""


class BaseAgent:
    """
    共用的 LLM 代理包裝。負責：渲染 prompt、呼叫 LLM、回傳文字或 JSON。
    """
    def __init__(self, spec: AgentSpec, llm: ChatOllama):
        self.spec = spec
        self.llm = llm

    @staticmethod
    def render(text: Optional[str], vars: Dict[str, Any]) -> str:
        if not text:
            return ""
        # 使用正则表达式只替换已知变量，保留其他大括号不变（如 JSON 示例）
        # 只匹配 {key} 格式，其中 key 紧跟在 { 后面，没有空格、引号等
        result = text
        for key, value in vars.items():
            # 匹配 {key}，要求 { 后直接是变量名，且变量名只包含字母、数字下划线
            # 使用 \b 确保匹配完整的变量名，避免部分匹配
            pattern = r'\{' + re.escape(key) + r'\}(?![\w])'
            result = re.sub(pattern, str(value), result)
        return result

    def _call_llm(self, messages: List[Any], *, temperature: Optional[float] = None) -> str:
        """
        LangChain ChatOllama .invoke(messages) 的薄封裝。
        這裡不要傳遞不支援的參數到底層 (有的版本 client.chat 不吃 temperature)，
        溫度已在建構 ChatOllama 時設定。
        """
        response = self.llm.invoke(messages)
        # ChatOllama.invoke() 返回 AIMessage，需要提取 content
        if hasattr(response, 'content'):
            return str(response.content)
        return str(response)

    def run(
        self,
        vars: Dict[str, Any],
        *,
        expect_json: bool = False,
        temperature: Optional[float] = None,
        extra_user_content: Optional[str] = None,
        user_append: Optional[str] = None,  # 兼容旧参数名
    ) -> str | Dict[str, Any]:
        # 渲染 system / user
        sys_prompt = self.render(self.spec.system, vars)
        usr_prompt = self.render(self.spec.user, vars)

        # 如果提供了额外的 user content，附加到 user prompt
        extra = extra_user_content or user_append
        if extra:
            usr_prompt = f"{usr_prompt}\n\n{extra}"

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=usr_prompt),
        ]

        output_text = self._call_llm(messages, temperature=temperature)

        if expect_json:
            # 允許模型回傳自然語言時做 best-effort JSON 擷取
            maybe = try_parse_json(output_text)
            if maybe is not None:
                ensure_valid_json(maybe)  # 若你的測試需要 schema，這裡可保留；不需要可改成軟性驗證
                return maybe
        return output_text
