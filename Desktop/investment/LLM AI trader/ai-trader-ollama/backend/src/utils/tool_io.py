# src/utils/tool_io.py
from __future__ import annotations
import json
from typing import Any, Dict, Tuple

TOOL_REQ_KEYS = {"tool", "args"}

def extract_json_block(text: str) -> Dict[str, Any] | None:
    if not text:
        return None
    fence_start = text.find("```json")
    if fence_start != -1:
        fence_end = text.find("```", fence_start + 7)
        if fence_end != -1:
            payload = text[fence_start + 7:fence_end].strip()
            try:
                return json.loads(payload)
            except Exception:
                pass
    l = text.find("{")
    r = text.rfind("}")
    if l != -1 and r != -1 and r > l:
        candidate = text[l:r+1]
        try:
            return json.loads(candidate)
        except Exception:
            return None
    return None

def parse_tool_request(text: str) -> Tuple[str, Dict[str, Any]] | Tuple[None, None]:
    obj = extract_json_block(text)
    if not obj or not TOOL_REQ_KEYS.issubset(obj.keys()):
        return (None, None)
    name = str(obj.get("tool", "")).strip()
    args = obj.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    return (name, args)

def make_tool_result_message(name: str, ok: bool, result: Any = None, error: str | None = None) -> str:
    obj: Dict[str, Any] = {
        "tool_result": {
            "tool": name,
            "ok": ok,
            "result": result if ok else None,
            "error": None if ok else (error or "unknown error")
        }
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
