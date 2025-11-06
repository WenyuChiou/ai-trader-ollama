from __future__ import annotations
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timezone
import json


class TradeHistoryTracker:
    """
    Lightweight trade history tracker used for cooldown checks.

    It reads from the same JSONL trade log used by TradeLogger (trades.jsonl)
    under the provided root (default: data/logs). If there is a recent trade
    for a given symbol, it returns whether the cooldown window has elapsed.
    """

    def __init__(self, root: str | Path = "data/logs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.trade_log_file = self.root / "trades.jsonl"

    def _last_trade_ts(self, symbol: str) -> Optional[datetime]:
        if not self.trade_log_file.exists():
            return None
        last_ts: Optional[datetime] = None
        try:
            with self.trade_log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    if rec.get("symbol") != symbol:
                        continue
                    ts_str = rec.get("ts")
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        if last_ts is None or ts > last_ts:
                            last_ts = ts
                    except Exception:
                        # Ignore malformed timestamps
                        continue
        except Exception:
            # If reading fails, behave as if no prior trades exist
            return None
        return last_ts

    def can_trade(self, symbol: str, cooldown_hours: float) -> Tuple[bool, float]:
        """
        Return (can_trade_now, hours_remaining_in_cooldown).
        If no prior trade is found, returns (True, 0.0).
        """
        last_ts = self._last_trade_ts(symbol)
        if last_ts is None:
            return True, 0.0

        now = datetime.now(timezone.utc)
        elapsed_hours = (now - last_ts).total_seconds() / 3600.0
        if elapsed_hours >= cooldown_hours:
            return True, 0.0
        return False, max(0.0, cooldown_hours - elapsed_hours)


