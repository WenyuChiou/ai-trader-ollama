# src/utils/io.py
from __future__ import annotations
from pathlib import Path
import json

def append_jsonl(path: str | Path, obj) -> None:
    """
    Append one JSON object as a line into a .jsonl file.
    Creates parent directories if they don't exist.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
