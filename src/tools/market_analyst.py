from __future__ import annotations
from typing import Dict, Any, List
from ..tools.analysis_tools import assess_trend, vix_regime, vix_risk_score
from ..agents.factory import AgentFactory

def run_market_analyst(market_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Market Analyst: 评估市场趋势并生成股票推荐列表
    现在会调用 LLM 来生成推荐，而不是只返回空列表
    """
    # --- VIX sentiment ---
    vix_info = market_json.get("VIX", {}) or {}
    regime = vix_regime.invoke({"vix": vix_info})
    vix_risk = vix_risk_score.invoke({"vix": vix_info})

    concerns = []
    if regime in ("elevated", "spike"):
        lvl = vix_info.get("level")
        zz  = vix_info.get("zscore")
        try:
            concerns.append(f"VIX {regime} (level={float(lvl):.2f}, z={float(zz):.2f})")
        except Exception:
            concerns.append(f"VIX {regime}")

    # --- Per-symbol trend assessment ---
    sentiment = []
    stocks = market_json.get("stocks", {})
    # 过滤掉指数（以^开头），只保留实际股票
    stocks_only = {k: v for k, v in stocks.items() if not k.startswith("^")}
    
    # 确保评估所有 stocks_only 中的股票（不仅仅是前几个）
    # 注意：这里只评估成功获取数据的股票，失败的数据已在 fetch_market_batch 中跳过
    for sym, sd in stocks_only.items():
        try:
            t = assess_trend.invoke({"symbol_data": sd})
            sentiment.append((sym, t))
        except Exception:
            # 如果评估失败，使用 "unknown" 作为默认值
            sentiment.append((sym, "unknown"))
    
    # 调用 Market Analyst LLM 来生成推荐
    rec_buy: List[str] = []
    try:
        from ..agents.factory import AgentFactory
        fac = AgentFactory()
        agent = fac.create("market_analyst")
        
        # 构建输入变量
        # 确保 LLM 看到所有成功获取数据的股票（stocks_only 可能包含所有72只股票，也可能因为假期/退市而减少）
        # 在 prompt 中明确告知 LLM 需要分析所有提供的股票
        vars: Dict[str, Any] = {
            "market_view": {
                "stocks": stocks_only,  # 包含所有成功获取数据的股票
                "total_stocks_analyzed": len(stocks_only),  # 明确告知 LLM 有多少只股票
                "vix": vix_info,
                "regime": regime,
                "risk_score": vix_risk,
                "sentiment_observations": [f"{s}: {t}" for s, t in sentiment],  # 所有成功获取数据的股票的趋势
            },
        }
        
        # 调用 LLM 生成推荐
        out_text = agent.run(vars, expect_json=False)
        
        # 尝试从输出中提取推荐的股票
        # LLM 可能以各种格式返回：JSON, 列表, 文本等
        import json
        import re
        
        # 尝试解析 JSON
        try:
            # 查找 JSON 对象
            json_match = re.search(r'\{[^{}]*"recommended_stocks"[^{}]*\}', out_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                rec_buy = parsed.get("recommended_stocks", [])
            else:
                # 尝试解析数组格式
                array_match = re.search(r'\[["\']?([A-Z]+)["\']?(?:,\s*["\']?([A-Z]+)["\']?)*\]', out_text)
                if array_match:
                    rec_buy = [s.strip() for s in array_match.group().strip('[]').split(',') if s.strip()]
                else:
                    # 查找股票代码（大写字母，2-5个字符）
                    symbols_found = re.findall(r'\b([A-Z]{2,5})\b', out_text)
                    # 过滤：只保留在 stocks_only 中的股票
                    rec_buy = [s for s in symbols_found if s in stocks_only and s not in ["VIX", "RSI", "MACD", "BB", "OHLC"]]
        except Exception:
            # 如果解析失败，使用简单的模式匹配
            symbols_found = re.findall(r'\b([A-Z]{2,5})\b', out_text)
            rec_buy = [s for s in symbols_found if s in stocks_only and s not in ["VIX", "RSI", "MACD", "BB", "OHLC"]]
        
        # 限制推荐数量（最多20只，确保多样性）
        rec_buy = rec_buy[:20]
        
    except Exception as e:
        # 如果 LLM 调用失败，使用基于 signal_score 的备用逻辑
        # 选择 signal_score 最高的前10只股票
        candidates = []
        for sym, sd in stocks_only.items():
            if isinstance(sd, dict):
                try:
                    score = float(sd.get("signal_score", 0))
                    if score > 0:
                        candidates.append((sym, score))
                except Exception:
                    pass
        
        # 按 signal_score 降序排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        rec_buy = [sym for sym, _ in candidates[:10]]

    # key_observations 应该包含所有成功获取数据的股票的趋势评估
    # 如果 sentiment 列表很长（超过20只），只显示前20只，避免输出过长
    max_observations = 20
    if len(sentiment) > max_observations:
        # 显示前 max_observations 只，并添加说明
        key_observations = [f"{s}: {t}" for s, t in sentiment[:max_observations]]
        key_observations.append(f"... and {len(sentiment) - max_observations} more stocks analyzed (total: {len(sentiment)})")
    else:
        key_observations = [f"{s}: {t}" for s, t in sentiment]
    
    out = {
        "market_sentiment": ("bullish" if rec_buy else "neutral") if regime in ("low", "normal") else "cautious",
        "key_observations": key_observations,
        "recommended_stocks": rec_buy,
        "concerns": concerns,
        "vix": {"regime": regime, "risk_score": vix_risk, **vix_info},
        "total_stocks_analyzed": len(stocks_only),  # 添加总股票数量信息
    }
    return out
