from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any, Dict

class TradeLogger:
    def __init__(self, root: str | Path = "data/logs"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.fp = self.root / "trades.jsonl"

    def log(self, record: Dict[str, Any]) -> None:
        record["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
