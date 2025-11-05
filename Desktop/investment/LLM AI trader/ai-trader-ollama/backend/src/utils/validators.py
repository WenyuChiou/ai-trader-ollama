# src/utils/validators.py
from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional, Tuple


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _strip_code_fences(text: str) -> Optional[str]:
    """
    若文字中包含 ```json ... ``` 或 ``` ... ```，回傳第一個區塊的內容；否則 None。
    """
    m = _FENCE_RE.search(text or "")
    if m:
        return m.group(1)
    return None


def _find_json_object_span(text: str) -> Optional[Tuple[int, int]]:
    """
    在輸出裡用簡單括號計數法找出第一個 { ... } 物件的範圍（允許前後雜訊）。
    回傳 (start, end_exclusive) 或 None。
    """
    s = text or ""
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return (start, i + 1)
    return None


def try_parse_json(text: str, fallback: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    嘗試從文字中解析出 JSON 物件。
    解析順序：
      1) 取 ```json ... ``` 或 ``` ... ``` 內文嘗試 json.loads
      2) 直接對整段 text 做 json.loads
      3) 以括號配對找到第一個 { ... } 物件子字串再 json.loads
    成功則回傳 dict；全部失敗回傳 fallback（預設 None）。
    """
    if text is None:
        return fallback

    # 1) fenced block
    fenced = _strip_code_fences(text)
    if fenced:
        try:
            obj = json.loads(fenced)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # 2) raw
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 3) first {...} span
    span = _find_json_object_span(text)
    if span:
        start, end = span
        candidate = text[start:end]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    return fallback


def ensure_valid_json(
    text_or_obj: Any,
    required_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    解析並驗證 JSON 物件。
    - text_or_obj 是字串：會呼叫 try_parse_json（失敗拋出 ValueError）
    - text_or_obj 已是 dict：直接使用
    - required_keys：若缺少任何鍵，拋出 ValueError
    """
    if isinstance(text_or_obj, dict):
        obj = text_or_obj
    elif isinstance(text_or_obj, str):
        obj = try_parse_json(text_or_obj)
        if obj is None:
            raise ValueError("Model output is not valid JSON or no JSON object found.")
    else:
        raise TypeError("ensure_valid_json expects str or dict.")

    if required_keys:
        missing = [k for k in required_keys if k not in obj]
        if missing:
            raise ValueError(f"Missing keys: {missing}")

    return obj
