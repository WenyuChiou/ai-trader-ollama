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

# 替代數據源
_ALTERNATIVE_SOURCES = [
    "https://feargreedmeter.com/",  # 替代數據源，顯示值和日期信息
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
    改進：使用 BeautifulSoup 和更精確的正則表達式，查找嵌入的 JSON 數據。
    """
    try:
        from bs4 import BeautifulSoup
        
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        })
        if resp.status_code != 200 or not resp.text:
            return None
        html = resp.text

        val = None
        label = None
        date_str = None
        
        # 策略1: 查找嵌入在 script 標籤中的 JSON 數據
        try:
            soup = BeautifulSoup(html, 'html.parser')
            script_tags = soup.find_all('script', type='application/json')
            
            for script in script_tags:
                try:
                    script_data = json.loads(script.string)
                    # 遞歸查找包含 fear/greed 相關的數據
                    if isinstance(script_data, dict):
                        # 查找包含 value/score/index 的結構
                        for key in ['fear_and_greed', 'fearAndGreed', 'fng', 'data']:
                            if key in script_data:
                                node = script_data[key]
                                if isinstance(node, dict):
                                    candidate_val = node.get('value') or node.get('score') or node.get('index')
                                    candidate_label = node.get('label') or node.get('rating')
                                    candidate_date = node.get('date') or node.get('asof') or node.get('timestamp')
                                    
                                    if candidate_val is not None:
                                        try:
                                            candidate_int = int(float(candidate_val))
                                            if 0 <= candidate_int <= 100:
                                                val = candidate_int
                                                if candidate_label:
                                                    label = candidate_label
                                                if candidate_date:
                                                    date_str = candidate_date
                                                break
                                        except (ValueError, TypeError):
                                            pass
                        if val is not None:
                            break
                except (json.JSONDecodeError, ValueError):
                    continue
        except Exception:
            pass
        
        # 策略2: 在 HTML 中查找特定的 JSON 數據結構（更寬鬆的匹配）
        if val is None:
            # 查找可能的 JSON 結構，包含 fear_and_greed 或相關鍵
            json_patterns = [
                r'fear[_-]?and[_-]?greed[^}]*value["\']?\s*:\s*(\d{1,3})',
                r'fear[_-]?and[_-]?greed[^}]*score["\']?\s*:\s*(\d{1,3})',
                r'fear[_-]?and[_-]?greed[^}]*index["\']?\s*:\s*(\d{1,3})',
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, html, re.IGNORECASE)
                for m in matches:
                    candidate = int(m.group(1))
                    if 0 <= candidate <= 100:
                        val = candidate
                        # 嘗試在同一匹配附近找到 label
                        context_start = max(0, m.start() - 500)
                        context_end = min(len(html), m.end() + 500)
                        context = html[context_start:context_end]
                        label_match = re.search(r'label["\']?\s*:\s*"([^"]+)"', context, re.IGNORECASE)
                        if label_match:
                            label = label_match.group(1)
                        break
                if val is not None:
                    break
        
        # 策略3: 查找頁面文本中顯示的數字（最不精確，但作為最後手段）
        if val is None:
            # 查找 "Fear & Greed Index" 後面緊跟的 0-100 範圍的數字
            pattern = r'Fear\s*&\s*Greed\s*Index[^0-9]*(\d{1,2}|100)(?=\s|"|,|\.|</|$)'
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                candidate = int(match.group(1))
                if 0 <= candidate <= 100:
                    val = candidate
        
        # 查找標籤（如果還沒有找到）
        if label is None:
            label_patterns = [
                r'"label"\s*:\s*"([^"]+)"',
                r'"rating"\s*:\s*"([^"]+)"',
                r'(Extreme\s+Fear|Extreme\s+Greed|Fear|Greed|Neutral)(?=\s|"|,|\.|$)',
            ]
            
            for pattern in label_patterns:
                ml = re.search(pattern, html, re.IGNORECASE)
                if ml:
                    label_candidate = ml.group(1) if ml.groups() else ml.group(0)
                    # 驗證是否是有效的標籤
                    if any(x.lower() in label_candidate.lower() for x in ["Fear", "Greed", "Neutral"]):
                        label = label_candidate.title().replace("  ", " ")
                        break

        # 提取日期信息（優先查找最近的日期）
        if date_str is None:
            # 優先查找最近的日期格式（今天或昨天）
            today = datetime.now(timezone.utc).date()
            date_pattern = r'(\d{4}-\d{2}-\d{2})'
            all_dates = re.findall(date_pattern, html)
            if all_dates:
                # 過濾出最近的日期（在過去 7 天內）
                for d_str in all_dates:
                    try:
                        from datetime import datetime as dt
                        d = dt.strptime(d_str, '%Y-%m-%d').date()
                        if (today - d).days <= 7 and (today - d).days >= 0:
                            date_str = d_str
                            break
                    except (ValueError, TypeError):
                        continue
                # 如果沒找到最近的，使用第一個有效的日期
                if date_str is None and all_dates:
                    date_str = all_dates[0]

        if val is None and label is None:
            return None

        # 解析日期
        asof = _now_iso()
        if date_str:
            try:
                # 嘗試使用標準庫解析日期
                from datetime import datetime as dt
                parsed_date = dt.strptime(date_str, '%Y-%m-%d')
                asof = parsed_date.replace(tzinfo=timezone.utc).replace(microsecond=0).isoformat()
            except (ValueError, TypeError):
                try:
                    # 如果標準庫失敗，嘗試 dateutil（如果可用）
                    try:
                        from dateutil import parser as date_parser
                        parsed_date = date_parser.parse(date_str)
                        asof = parsed_date.replace(tzinfo=timezone.utc).replace(microsecond=0).isoformat()
                    except ImportError:
                        pass  # dateutil 不可用
                except Exception:
                    pass  # 解析失敗，使用當前時間

        return {
            "value": val,
            "label": label,
            "previous_close": None,
            "one_week_ago": None,
            "one_month_ago": None,
            "one_year_ago": None,
            "asof": asof,
            "source": "cnn_html",
            "extracted_date": date_str,
        }
    except Exception as e:
        # 輸出錯誤以便調試
        import traceback
        traceback.print_exc()
        return None

def _scrape_feargreedmeter(url: str) -> Optional[Dict[str, Any]]:
    """
    從 feargreedmeter.com 抓取 Fear & Greed Index。
    根據網站內容，顯示格式：指數值（如 35）和 "X days ago" 日期信息。
    """
    try:
        from bs4 import BeautifulSoup
        
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        })
        if resp.status_code != 200 or not resp.text:
            return None
        
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        val = None
        label = None
        date_str = None
        days_ago = None
        
        # 策略1: 查找頁面上顯示的大數字（通常是指數值）
        # 網站上顯示 "35" 作為主要數字
        large_numbers = soup.find_all(['h1', 'h2', 'h3', 'div', 'span'], 
                                     string=re.compile(r'^\d{1,3}$'))
        for elem in large_numbers:
            text = elem.get_text(strip=True)
            try:
                candidate = int(text)
                if 0 <= candidate <= 100:
                    # 檢查上下文，確認這是指數值而非其他數字
                    parent_text = elem.parent.get_text() if elem.parent else ""
                    if 'fear' in parent_text.lower() or 'greed' in parent_text.lower():
                        val = candidate
                        break
            except (ValueError, TypeError):
                continue
        
        # 策略2: 在 HTML 文本中查找包含 "Fear" 和數字的部分
        if val is None:
            # 查找 "Fear and Greed Index" 附近的數字
            pattern = r'Fear\s+(?:and\s+)?Greed\s+(?:Index\s+)?(\d{1,3})'
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                candidate = int(match.group(1))
                if 0 <= candidate <= 100:
                    val = candidate
        
        # 策略3: 查找頁面上直接顯示的數字 35（根據搜索結果）
        if val is None:
            # 查找單獨的大數字（通常是指數值）
            matches = re.finditer(r'\b(0|[1-9]\d?|100)\b', html)
            for m in matches:
                candidate = int(m.group(1))
                # 檢查這個數字附近是否有 Fear/Greed 相關文本
                context_start = max(0, m.start() - 200)
                context_end = min(len(html), m.end() + 200)
                context = html[context_start:context_end].lower()
                if 'fear' in context or 'greed' in context:
                    val = candidate
                    break
        
        # 提取標籤（根據數值範圍推斷）
        if val is not None:
            if val <= 25:
                label = "Extreme Fear"
            elif val <= 45:
                label = "Fear"
            elif val <= 55:
                label = "Neutral"
            elif val <= 75:
                label = "Greed"
            else:
                label = "Extreme Greed"
        
        # 提取日期信息（"X days ago" 或 "X hours ago"）
        date_patterns = [
            r'(\d+)\s+days?\s+ago',
            r'(\d+)\s+hours?\s+ago',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                date_info = match.group(1) if match.groups() else match.group(0)
                if 'day' in match.group(0).lower() or 'hour' in match.group(0).lower():
                    try:
                        days_ago = int(date_info)
                        # 計算實際日期
                        from datetime import datetime, timedelta
                        actual_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
                        date_str = actual_date.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
                elif re.match(r'\d{4}-\d{2}-\d{2}', date_info):
                    date_str = date_info
                break
        
        if val is None:
            return None
        
        # 解析日期
        asof = _now_iso()
        if date_str:
            try:
                from datetime import datetime as dt
                parsed_date = dt.strptime(date_str, '%Y-%m-%d')
                asof = parsed_date.replace(tzinfo=timezone.utc).replace(microsecond=0).isoformat()
            except (ValueError, TypeError):
                pass
        
        return {
            "value": val,
            "label": label,
            "previous_close": None,
            "one_week_ago": None,
            "one_month_ago": None,
            "one_year_ago": None,
            "asof": asof,
            "source": "feargreedmeter",
            "extracted_date": date_str,
            "days_ago": days_ago,  # 添加 "X days ago" 信息
        }
    except Exception:
        return None

def fetch_fear_greed(timeout: float = 8.0) -> Dict[str, Any]:
    """
    抓 Fear & Greed Index（多來源策略）：
      1) CNN JSON 端點（1~2 個）
      2) feargreedmeter.com（替代數據源，推薦）
      3) CNN HTML 頁面 fallback
      都失敗 → 回 stub 結構（不阻塞主流程）。
    """
    # A/B: CNN JSON 端點
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

    # 新增: feargreedmeter.com（替代數據源，更可靠）
    for url in _ALTERNATIVE_SOURCES:
        parsed = _scrape_feargreedmeter(url)
        if parsed and parsed.get("value") is not None:
            return parsed

    # C: CNN HTML fallback
    for url in _CNN_HTML_PAGES:
        parsed = _scrape_cnn_html(url)
        if parsed and parsed.get("value") is not None:
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
