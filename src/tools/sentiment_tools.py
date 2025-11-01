# src/tools/sentiment_tools.py
from __future__ import annotations
from typing import Dict, Any, Optional
import time
import json
import re
import requests
from datetime import datetime, timezone

# ---------------- Fear & Greed (CNN) ----------------
# 策略：依序嘗試 3 個來源（任何一個成功就回值；都失敗回 stub）
# A) JSON API（新版 CNN dataviz）
# B) JSON API（備用路徑/拼寫）
# C) HTML 頁面抓值（fallback）

_CNN_JSON_ENDPOINTS = [
    # A. 常見 JSON 端點（新版 CNN Business dataviz）
    "https://production.dataviz.cnn.io/markets/fearandgreed/",
    # B. 備用：有些部署寫法不同（容錯）
    "https://production.dataviz.cnn.io/markets/fear-and-greed/",
]

_CNN_HTML_PAGES = [
    # C. HTML 頁面（新版）
    "https://www.cnn.com/markets/fear-and-greed",
    # 舊版（偶爾會 redirect）
    "https://money.cnn.com/data/fear-and-greed/"
]

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _parse_cnn_json(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    解析 CNN dataviz JSON 結構；不同環境可能鍵名略有差異，故作寬鬆解析。
    期望回傳：
      {
        "value": 0-100,
        "label": "Extreme Fear/Fear/Neutral/Greed/Extreme Greed",
        "previous_close": int|None,
        "one_week_ago": int|None,
        "one_month_ago": int|None,
        "one_year_ago": int|None,
        "asof": ISO8601
      }
    """
    if not isinstance(payload, dict):
        return None

    # 常見鍵位於 payload["fear_and_greed"] 或頂層
    node = payload.get("fear_and_greed") or payload
    value = node.get("score") or node.get("value") or node.get("index") or None
    label = node.get("rating") or node.get("label") or None

    # 歷史值常見在 node["previous_close"], node["one_week_ago"], ...
    prev = node.get("previous_close")
    wk = node.get("one_week_ago")
    mo = node.get("one_month_ago")
    yr = node.get("one_year_ago")

    # 有些版本把歷史放在 node["historical"]（list or dict）
    hist = node.get("historical")
    if isinstance(hist, dict):
        prev = prev or hist.get("previous_close")
        wk = wk or hist.get("one_week_ago")
        mo = mo or hist.get("one_month_ago")
        yr = yr or hist.get("one_year_ago")

    # 清洗為 int
    def _toi(x):
        try:
            return int(float(x))
        except Exception:
            return None

    value = _toi(value)
    prev = _toi(prev)
    wk = _toi(wk)
    mo = _toi(mo)
    yr = _toi(yr)

    if value is None and label is None:
        return None

    return {
        "value": value,
        "label": label,
        "previous_close": prev,
        "one_week_ago": wk,
        "one_month_ago": mo,
        "one_year_ago": yr,
        "asof": _now_iso(),
        "source": "cnn_json"
    }

def _scrape_cnn_html(url: str) -> Optional[Dict[str, Any]]:
    """
    從 CNN HTML 頁面抓 FGI 文字/數字。此為最後手段（DOM 可能改版）。
    """
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200 or not resp.text:
            return None
        html = resp.text

        # 嘗試找 “Fear & Greed Index” 附近的數字（0-100）
        m = re.search(r'Fear\s*&\s*Greed\s*Index[^0-9]+(\d{1,3})', html, flags=re.IGNORECASE)
        val = int(m.group(1)) if m else None

        # 嘗試找文字標籤（Extreme Fear / Fear / Neutral / Greed / Extreme Greed）
        label_pat = r'(Extreme\s+Fear|Fear|Neutral|Greed|Extreme\s+Greed)'
        ml = re.search(label_pat, html, flags=re.IGNORECASE)
        label = ml.group(1).title().replace("  ", " ") if ml else None

        if val is None and label is None:
            return None

        return {
            "value": val,
            "label": label,
            "previous_close": None,
            "one_week_ago": None,
            "one_month_ago": None,
            "one_year_ago": None,
            "asof": _now_iso(),
            "source": "cnn_html"
        }
    except Exception:
        return None

def fetch_fear_greed(timeout: float = 8.0) -> Dict[str, Any]:
    """
    抓 CNN Fear & Greed Index（多來源策略）：
      1) JSON 端點（1~2 個）
      2) HTML 頁面 fallback
      都失敗 → 回 stub 結構（不阻塞主流程）。
    """
    # A/B: JSON 端點
    for ep in _CNN_JSON_ENDPOINTS:
        try:
            r = requests.get(ep, timeout=timeout, headers={"Accept": "application/json"})
            if r.status_code == 200:
                data = r.json()
                parsed = _parse_cnn_json(data)
                if parsed:
                    return parsed
        except Exception:
            pass

    # C: HTML fallback
    for url in _CNN_HTML_PAGES:
        parsed = _scrape_cnn_html(url)
        if parsed:
            return parsed

    # 全部失敗 → stub
    return {
        "value": None,
        "label": None,
        "previous_close": None,
        "one_week_ago": None,
        "one_month_ago": None,
        "one_year_ago": None,
        "asof": _now_iso(),
        "source": "stub"
    }


# ---------------- VIX term structure（你既有的即可保留） ----------------
import yfinance as yf
import pandas as pd

def vix_term_structure() -> Dict[str, Any]:
    """
    回傳 VIX 與 VIX3M 的最新值與 term ratio（>1 通常視為 contango）。
    """
    try:
        vix = yf.download("^VIX", period="3mo", interval="1d", progress=False, auto_adjust=False)
        vix3m = yf.download("^VIX3M", period="3mo", interval="1d", progress=False, auto_adjust=False)

        def _last_close(df):
            if df is None or df.empty or "Close" not in df:
                return None
            s = df["Close"].dropna()
            if s.empty:
                return None
            # 用 numpy 取值可避免 "single element Series" 的 FutureWarning
            return float(s.to_numpy()[-1])

        v = _last_close(vix)
        v3 = _last_close(vix3m)
        ratio = (v3 / v) if (v and v3) else None

        return {
            "vix": v, "vix3m": v3, "ratio": ratio,
            "asof": _now_iso(), "source": "yfinance"
        }
    except Exception:
        return {"vix": None, "vix3m": None, "ratio": None, "asof": _now_iso(), "source": "error"}




# ---------------- （可選）VIX 風險分數 helper ----------------
def vix_risk_score(v: Optional[Dict[str, Any]] = None) -> float:
    """
    簡單將 VIX 值映射到 0~10 的風險分數。
    """
    if not v:
        return 4.0
    val = v.get("vix") or v.get("value") or v.get("level")
    try:
        val = float(val)
    except Exception:
        return 4.0
    # 粗略分段
    if val < 13: return 2.0
    if val < 18: return 4.0
    if val < 24: return 6.0
    if val < 30: return 7.5
    return 9.0
