from __future__ import annotations
from typing import Dict, Any, Optional
import re
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

CNN_FNG_URLS = [
    "https://www.cnn.com/markets/fear-and-greed",
    "https://money.cnn.com/data/fear-and-greed/",  # 備用
]

def _clean_text(x: str) -> str:
    if not x:
        return ""
    return " ".join(x.replace("\n", " ").replace("\r", " ").split())

def fetch_fear_greed(timeout: int = 10) -> Dict[str, Any]:
    """
    嘗試抓取 CNN Fear & Greed Index（整體分數與可能的子指標文字）。
    回傳格式：
    {
      "value": 0~100 或 None,
      "label": "Extreme Fear/Fear/Neutral/Greed/Extreme Greed" (若能解析),
      "source_url": "...",
      "raw_excerpt": "..."  # 擷取的文字片段，debug 用
    }
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in CNN_FNG_URLS:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = _clean_text(soup.get_text(" "))
            # 嘗試從頁面文字找出 0-100 數值
            # 常見片段如 "Fear & Greed Index: 56 (Greed)"
            m = re.search(r"(Fear\s*&\s*Greed\s*Index[:\s]+)?(\d{1,3})\s*\(?([A-Za-z ]+)?\)?", text)
            val = None
            label = None
            if m:
                try:
                    v = int(m.group(2))
                    if 0 <= v <= 100:
                        val = v
                except Exception:
                    pass
                if m.group(3):
                    label = m.group(3).strip()
            # 再嘗試另一種樣式：e.g. "Index now: 34 – Fear"
            if val is None:
                m2 = re.search(r"Index\s+now[:\s]+(\d{1,3}).{0,30}?(Extreme\s+Greed|Greed|Neutral|Fear|Extreme\s+Fear)", text, re.IGNORECASE)
                if m2:
                    try:
                        v = int(m2.group(1))
                        if 0 <= v <= 100:
                            val = v
                        label = m2.group(2).title()
                    except Exception:
                        pass
            return {
                "value": val,
                "label": label,
                "source_url": url,
                "raw_excerpt": text[:800]
            }
        except Exception:
            continue
    return {"value": None, "label": None, "source_url": None, "raw_excerpt": ""}

def _last_float(series: pd.Series) -> float:
    """
    Robustly get the last numeric value from a Series as float
    without calling float() on the Series itself (avoids FutureWarning).
    """
    try:
        s = series.dropna()
        if s.empty:
            return float("nan")
        # prefer fast scalar access; both lines avoid Series->float deprecation
        return float(s.to_numpy()[-1])  # or: float(s.iat[-1])
    except Exception:
        return float("nan")

def vix_term_structure(start: str | None = None, end: str | None = None) -> dict:
    """
    以 yfinance 取得 ^VIX 與 ^VIX3M 近收，計算 term structure。
    回傳：
      { "vix": float, "vix3m": float, "ratio": float, "state": "contango|backwardation|flat|unknown" }
    """
    kwargs = dict(start=start, end=end, progress=False, auto_adjust=False)
    try:
        vix = yf.download("^VIX", **kwargs)
        vix3m = yf.download("^VIX3M", **kwargs)
    except Exception:
        return {"vix": None, "vix3m": None, "ratio": None, "state": "unknown"}

    if vix is None or vix.empty or vix3m is None or vix3m.empty:
        return {"vix": None, "vix3m": None, "ratio": None, "state": "unknown"}

    v = _last_float(vix["Close"])
    v3 = _last_float(vix3m["Close"])

    if pd.isna(v) or pd.isna(v3) or v <= 0:
        return {"vix": v if pd.notna(v) else None,
                "vix3m": v3 if pd.notna(v3) else None,
                "ratio": None, "state": "unknown"}

    ratio = v3 / v
    state = "contango" if ratio > 1.0 else "backwardation" if ratio < 1.0 else "flat"
    return {"vix": v, "vix3m": v3, "ratio": ratio, "state": state}

