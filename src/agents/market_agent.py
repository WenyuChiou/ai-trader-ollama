from __future__ import annotations
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from ..llm.ollama_client import get_llm
from ..tools.market_tools import fetch_market_batch

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a data specialist. Only gather and format market data clearly into JSON. No analysis."),
    ("user", "Symbols: {symbols}\nDate range: {start} ~ {end}\nUse the tool to fetch data and return JSON with key 'stocks'."),
])

def run_market_agent(symbols: List[str], start: str, end: str) -> Dict[str, Any]:
    llm = get_llm()
    # We call the tool directly for determinism
    data = fetch_market_batch.invoke({"symbols": symbols, "start": start, "end": end})
    return {"stocks": data}
