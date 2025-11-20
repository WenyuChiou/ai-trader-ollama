"""
Common utilities and helper functions for all analysts.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
import json
import re

from src.agents.base import BaseAgent
from src.agents.toolbox import ToolBox


def extract_score(result: Dict[str, Any], score_key: str) -> str | float:
    """
    Extract score from analyst result, handling various formats:
    - Number: return directly
    - Dict: calculate average
    - List: calculate average
    - Not found: try generic score field, finally return default 5.0
    """
    score = result.get(score_key)
    
    if score is None:
        score = result.get('score')
    
    if score is None:
        if 'error' in result:
            return 5.0
        if result.get('analysis') or result.get('stance'):
            return 5.0
        return 'N/A'
    
    if isinstance(score, (int, float)):
        return float(score)
    
    if isinstance(score, dict):
        values = [v for v in score.values() if isinstance(v, (int, float))]
        if values:
            return round(sum(values) / len(values), 1)
        return 'N/A'
    
    if isinstance(score, list):
        values = [v for v in score if isinstance(v, (int, float))]
        if values:
            return round(sum(values) / len(values), 1)
        return 'N/A'
    
    try:
        return float(score)
    except:
        return 'N/A'


def limit_discussion_history(discussion_history: List[Dict[str, Any]], max_entries: int = 20) -> None:
    """Limit discussion history length to avoid memory accumulation"""
    if len(discussion_history) > max_entries:
        old_len = len(discussion_history)
        discussion_history[:] = discussion_history[-max_entries:]
        print(f"[MEMORY] Trimmed discussion_history: {old_len} -> {len(discussion_history)} entries")


def format_discussion_history(discussion_history: List[Dict[str, Any]]) -> str:
    """Format discussion history for next analyst to see previous discussions"""
    if not discussion_history:
        return "No previous discussion."
    
    formatted = []
    for entry in discussion_history:
        analyst_name = entry.get("analyst", "Unknown")
        stance = entry.get("stance", "N/A")
        analysis = entry.get("analysis", "No analysis provided")
        tools_used = entry.get("tools_used", [])
        key_points = entry.get("key_points", [])
        
        formatted.append(f"--- {analyst_name} ---")
        formatted.append(f"Stance: {stance}")
        formatted.append(f"Analysis: {analysis}")
        
        if tools_used:
            formatted.append(f"Tools Used: {', '.join(tools_used)}")
        
        if key_points:
            formatted.append("Key Points:")
            for point in key_points[:3]:
                formatted.append(f"  - {point}")
        
        formatted.append("")
    
    return "\n".join(formatted)


def summarize_market(market_view: Dict[str, Any]) -> Dict[str, Any]:
    """Simplify market data for prompt - optimized to support 100+ stocks"""
    stocks = market_view.get("stocks", {})
    symbols_list = list(stocks.keys())
    
    sample_stocks_data = {}
    for symbol in symbols_list[:10]:
        stock_data = stocks.get(symbol, {})
        sample_stocks_data[symbol] = {
            "price": stock_data.get("price"),
            "change_pct": stock_data.get("change_pct"),
            "rsi14": stock_data.get("rsi14"),
            "signal_score": stock_data.get("signal_score"),
        }
    
    all_prices = [float(s.get("price", 0)) for s in stocks.values() if s.get("price")]
    all_changes = [float(s.get("change_pct", 0)) for s in stocks.values() if s.get("change_pct")]
    all_scores = [float(s.get("signal_score", 0)) for s in stocks.values() if s.get("signal_score")]
    
    market_stats = {}
    if all_prices:
        market_stats["avg_price"] = sum(all_prices) / len(all_prices)
        market_stats["price_range"] = {"min": min(all_prices), "max": max(all_prices)}
    if all_changes:
        market_stats["avg_change_pct"] = sum(all_changes) / len(all_changes)
        market_stats["positive_count"] = sum(1 for c in all_changes if c > 0)
        market_stats["negative_count"] = sum(1 for c in all_changes if c < 0)
    if all_scores:
        market_stats["avg_signal_score"] = sum(all_scores) / len(all_scores)
    
    return {
        "stocks_count": len(stocks),
        "symbols": symbols_list,
        "sample_stocks": symbols_list[:10],
        "sample_stocks_data": sample_stocks_data,
        "market_stats": market_stats,
        "vix": market_view.get("vix"),
        "vix_term": market_view.get("vix_term"),
        "fear_greed": market_view.get("fear_greed"),
        "note": f"Full universe contains {len(stocks)} stocks. Use tools to get detailed data for specific stocks when needed.",
    }


def parse_analyst_response(response: str | Dict[str, Any]) -> Dict[str, Any]:
    """Parse analyst response (may be JSON dict or text)"""
    if isinstance(response, dict):
        is_single_tool_call = (
            ("name" in response and "args" in response) or 
            ("@tool" in response or ("tool" in response and "params" in response))
        ) and "stance" not in response and "analysis" not in response
        
        if is_single_tool_call:
            tool_call = response
            if "@tool" in response or ("tool" in response and "params" in response):
                tool_call = {
                    "name": response.get("@tool") or response.get("tool", ""),
                    "args": response.get("params", {}) or response.get("args", {}),
                    "why": response.get("why", "Auto-converted from @tool format")
                }
            return {
                "stance": "neutral",
                "analysis": "",
                "tool_calls": [tool_call],
            }
        
        if "stance" not in response:
            response["stance"] = "neutral"
        if "analysis" not in response:
            response["analysis"] = "No analysis provided"
        if "tool_calls" not in response:
            response["tool_calls"] = []
        if "recommended_stocks" not in response:
            response["recommended_stocks"] = []
        
        if response.get("tool_calls"):
            converted_tool_calls = []
            for tc in response["tool_calls"]:
                if isinstance(tc, dict):
                    if "@tool" in tc or ("tool" in tc and "params" in tc):
                        converted_tc = {
                            "name": tc.get("@tool") or tc.get("tool", ""),
                            "args": tc.get("params", {}) or tc.get("args", {}),
                            "why": tc.get("why", "Auto-converted from @tool format")
                        }
                        converted_tool_calls.append(converted_tc)
                    else:
                        converted_tool_calls.append(tc)
                else:
                    converted_tool_calls.append(tc)
            response["tool_calls"] = converted_tool_calls
        
        if isinstance(response.get("tool_calls"), dict):
            response["tool_calls"] = [response["tool_calls"]]
        return response
    
    try:
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
        else:
            json_str = response
        
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict):
            parsed = {}
        
        defaults = {
            "stance": parsed.get("stance", "neutral"),
            "analysis": parsed.get("analysis", str(response)[:300] if isinstance(response, str) else ""),
            "tool_calls": parsed.get("tool_calls", []),
            "recommended_stocks": parsed.get("recommended_stocks", []),
        }
        
        # CRITICAL FIX: Ensure tool_calls is always a list (handle None, missing, or invalid values)
        if not isinstance(defaults["tool_calls"], list):
            if defaults["tool_calls"] is None:
                defaults["tool_calls"] = []
            elif isinstance(defaults["tool_calls"], dict):
                defaults["tool_calls"] = [defaults["tool_calls"]]
            else:
                defaults["tool_calls"] = []
        
        if not defaults["tool_calls"] and isinstance(response, str):
            tool_patterns = [
                r'get_market_indices', r'get_sector_rotation', r'get_market_breadth',
                r'get_advanced_indicators', r'get_support_resistance',
                r'get_company_fundamentals', r'get_earnings_history',
                r'fear_greed', r'vix_term', r'news_scan',
            ]
            found_tools = []
            for pattern in tool_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    found_tools.append({
                        "name": pattern,
                        "args": {},
                        "why": f"Extracted from analysis text"
                    })
            if found_tools:
                defaults["tool_calls"] = found_tools[:3]
        
        if defaults["tool_calls"] and not isinstance(defaults["tool_calls"], list):
            if isinstance(defaults["tool_calls"], dict):
                defaults["tool_calls"] = [defaults["tool_calls"]]
            else:
                defaults["tool_calls"] = []
        
        if defaults["tool_calls"]:
            validated_tool_calls = []
            for tc in defaults["tool_calls"]:
                if isinstance(tc, dict):
                    if "@tool" in tc or "tool" in tc:
                        tool_name = tc.get("@tool") or tc.get("tool", "")
                        tool_params = tc.get("params", {}) or tc.get("args", {})
                        if tool_name:
                            converted_tc = {
                                "name": tool_name,
                                "args": tool_params,
                                "why": tc.get("why", "Auto-converted from @tool format")
                            }
                            if tool_name == "get_company_fundamentals" and "tickers" in tool_params:
                                tickers = tool_params.get("tickers", [])
                                if isinstance(tickers, list) and len(tickers) > 0:
                                    for ticker in tickers:
                                        if ticker:
                                            validated_tool_calls.append({
                                                "name": tool_name,
                                                "args": {"symbol": str(ticker).upper()},
                                                "why": f"Extracted from tickers array: {ticker}"
                                            })
                                    continue
                            validated_tool_calls.append(converted_tc)
                    elif "name" in tc:
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("args", {})
                        if tool_name == "get_company_fundamentals" and "tickers" in tool_args:
                            tickers = tool_args.get("tickers", [])
                            if isinstance(tickers, list) and len(tickers) > 0:
                                for ticker in tickers:
                                    if ticker:
                                        validated_tool_calls.append({
                                            "name": tool_name,
                                            "args": {"symbol": str(ticker).upper()},
                                            "why": f"Extracted from tickers array: {ticker}"
                                        })
                                continue
                        validated_tool_calls.append(tc)
                elif isinstance(tc, str):
                    validated_tool_calls.append({"name": tc, "args": {}, "why": "Auto-converted"})
            defaults["tool_calls"] = validated_tool_calls
        
        if "recommended_stocks" in parsed:
            defaults["recommended_stocks"] = parsed["recommended_stocks"]
        
        result = {**defaults, **parsed}
        if "recommended_stocks" in parsed:
            result["recommended_stocks"] = parsed["recommended_stocks"]
        elif "recommended_stocks" not in result:
            result["recommended_stocks"] = []
        return result
    except Exception as e:
        return {
            "stance": "neutral",
            "analysis": str(response)[:300] if isinstance(response, str) else "No analysis provided",
            "tool_calls": [],
            "recommended_stocks": [],
            "score": 5.0,
            "error": f"Failed to parse JSON: {e}"
        }


def check_tool_success(tool_result: Optional[Dict[str, Any]]) -> bool:
    """Check if tool execution was successful, handling double nesting for memory tools"""
    if not tool_result or not isinstance(tool_result, dict):
        return False
    
    if tool_result.get("ok") is False:
        return False
    
    actual_result = tool_result.get("result", tool_result)
    
    if isinstance(actual_result, dict) and actual_result.get("ok") is False:
        return False
    
    return True


def get_tool_cache_key(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Generate cache key for tool call"""
    sorted_args = tuple(sorted(tool_args.items())) if tool_args else tuple()
    return f"{tool_name}:{sorted_args}"


def execute_tool(toolbox: ToolBox, tool_call: Dict[str, Any], market_summary: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Execute tool call, ensuring tools work correctly"""
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    
    # CRITICAL FIX: Ensure tool_args is a dictionary
    if not isinstance(tool_args, dict):
        print(f"   [WARN] Tool args is not a dict (type: {type(tool_args)}), resetting to empty dict")
        tool_args = {}
    
    if not tool_name:
        print(f"   [WARN] Tool call missing name")
        return {"ok": False, "error": "Tool call missing name"}
    
    # CRITICAL FIX: Tool name mapping - map incorrect tool names to correct ones
    tool_name_mapping = {
        "vix": "vix_term",
        "get_news_scan": "plan_and_scan_news",
        "get_news": "plan_and_scan_news",
        "get_market_sentiment": "fear_greed",
        "get_volume_analysis": "get_advanced_indicators",
        "get_advanced_technical_data": "get_advanced_indicators",  # LLM may use incorrect name
        "get_market_indices_data": "get_market_indices",  # LLM may use incorrect name
        "get_support_resistance_levels": "get_support_resistance",  # LLM may use incorrect name
        "get_stock_data": "get_advanced_indicators",  # LLM may use incorrect name
        "calculate_technical_indicators": "get_advanced_indicators",  # LLM may use incorrect name
        "identify_support_resistance": "get_support_resistance",  # LLM may use incorrect name
        "analyze_market_sentiment": "fear_greed",  # LLM may use incorrect name
    }
    
    if tool_name in tool_name_mapping:
        mapped_name = tool_name_mapping[tool_name]
        print(f"   [TOOL] Mapping '{tool_name}' -> '{mapped_name}' (correct tool name)")
        tool_name = mapped_name
        tool_call["name"] = mapped_name
    
    # Check if tool exists in toolbox
    if tool_name not in toolbox.list():
        print(f"   [WARN] Tool {tool_name} not found in toolbox")
        return {"ok": False, "error": f"Tool {tool_name} not available"}
    
    # CRITICAL FIX: web_search must have query or keywords parameter
    if tool_name == "web_search":
        if "query" not in tool_args and "keywords" not in tool_args:
            # If no query or keywords, add default query or skip
            if "domains" in tool_args:
                # If domains exist, use generic market query
                tool_args["query"] = "market news stocks economy"
                print(f"   [TOOL_FIX] Added default query='market news stocks economy' to web_search (domains={tool_args.get('domains')})")
            else:
                # If no domains and no query, return error
                print(f"   [TOOL_ERR] web_search requires 'query' or 'keywords' parameter")
                return {"ok": False, "error": "web_search requires 'query' or 'keywords' parameter"}
    
    # CRITICAL FIX: plan_and_scan_news - ensure mview parameter and fetch_body_top
    if tool_name == "plan_and_scan_news":
        # If fetch_body_top is not set, default to fetching top 10 articles' content
        if "fetch_body_top" not in tool_args or tool_args.get("fetch_body_top", 0) == 0:
            tool_args["fetch_body_top"] = 10
        
        # If mview is not provided, create from market_summary
        if "mview" not in tool_args and market_summary:
            tool_args["mview"] = {
                "vix": market_summary.get("vix", {}),
                "stocks": market_summary.get("stocks", {}),
            }
        elif "mview" not in tool_args:
            # If no market_summary, create empty mview
            tool_args["mview"] = {"vix": {}, "stocks": {}}
    
    # CRITICAL FIX: fear_greed tool does not accept index or crypto parameters, remove them
    if tool_name == "fear_greed":
        # fear_greed only accepts timeout parameter, remove other unsupported parameters
        unsupported_params = ["index", "crypto", "source", "market"]
        removed = []
        for param in unsupported_params:
            if param in tool_args:
                del tool_args[param]
                removed.append(param)
        if removed:
            print(f"   [TOOL_FIX] Removed unsupported parameters from fear_greed call: {removed}")
        # Only keep timeout parameter (if exists), remove all other parameters
        allowed_params = {"timeout"}
        params_to_remove = [k for k in tool_args.keys() if k not in allowed_params]
        for param in params_to_remove:
            del tool_args[param]
            if param not in unsupported_params:  # Avoid duplicate printing
                print(f"   [TOOL_FIX] Removed unsupported '{param}' parameter from fear_greed call")
    
    # CRITICAL FIX: Auto-add full universe symbols to get_market_breadth
    if tool_name == "get_market_breadth":
        if not tool_args.get("symbols") and market_summary and market_summary.get("symbols"):
            # Use full universe symbols (not sample_stocks)
            tool_args["symbols"] = market_summary["symbols"]
    
    # CRITICAL FIX: Check tools that require symbol parameter
    symbol_required_tools = ["get_advanced_indicators", "get_support_resistance", "get_company_fundamentals", 
                             "get_earnings_history", "get_financial_statements"]
    if tool_name in symbol_required_tools:
        # Check if symbol exists and is valid
        symbol = tool_args.get("symbol", "")
        if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
            if market_summary and market_summary.get("sample_stocks"):
                # Use first sample stock as default symbol
                default_symbol = market_summary["sample_stocks"][0]
                tool_args["symbol"] = default_symbol
            else:
                # If no available symbol, return error
                return {"ok": False, "error": "symbol is required"}
    
    try:
        # CRITICAL FIX: toolbox.invoke() signature is invoke(name: str, **kwargs)
        # So we need to unpack tool_args as keyword arguments, not pass as positional
        result = toolbox.invoke(tool_name, **tool_args)
        return result
    except Exception as e:
        print(f"   [ERROR] Tool {tool_name} execution failed: {e}")
        return {"ok": False, "error": str(e)}


def format_tool_result(tool_name: str, tool_result: Dict[str, Any]) -> str:
    """Format tool result for feedback to LLM"""
    if not tool_result or isinstance(tool_result, str):
        return str(tool_result)[:200] if tool_result else "No data"
    
    if isinstance(tool_result, dict):
        if "error" in tool_result:
            return f"Error: {tool_result.get('error', 'Unknown error')}"
        
        if tool_name == "get_market_indices":
            indices = tool_result.get("indices", {})
            return f"S&P 500: {indices.get('sp500', {}).get('change_percent', 'N/A')}%, NASDAQ: {indices.get('nasdaq', {}).get('change_percent', 'N/A')}%"
        elif tool_name == "get_sector_rotation":
            sectors = tool_result.get("sectors", [])
            top = sectors[:3] if sectors else []
            return f"Top sectors: {', '.join([s.get('sector', '') for s in top])}"
        elif tool_name == "get_advanced_indicators":
            indicators = tool_result.get("indicators", {})
            return f"RSI: {indicators.get('rsi', 'N/A')}, MACD: {indicators.get('macd_signal', 'N/A')}"
        elif tool_name == "get_company_fundamentals":
            fundamentals = tool_result.get("fundamentals", {})
            return f"PE: {fundamentals.get('pe_ratio', 'N/A')}, Market Cap: {fundamentals.get('market_cap', 'N/A')}"
        elif tool_name == "fear_greed":
            fg_data = tool_result.get("fear_greed", tool_result)
            if isinstance(fg_data, dict):
                value = fg_data.get("value")
                label = fg_data.get("label")
                if value is not None:
                    return f"Index: {value} ({label or 'N/A'})"
            return f"Index: {tool_result.get('value', 'N/A')} ({tool_result.get('label', 'N/A')})"
        elif tool_name == "vix_term":
            vix = tool_result.get("vix", {})
            return f"VIX: {vix.get('vix', 'N/A')}, Term structure: {vix.get('term_structure', 'N/A')}"
        elif tool_name in ["news_scan", "plan_and_scan_news"]:
            hits = tool_result.get("hits", [])
            articles = tool_result.get("articles", [])
            
            if articles:
                news_items = []
                for article in articles[:10]:
                    title = article.get("title", "No title")
                    source = article.get("source", "Unknown")
                    url = article.get("url", "")
                    excerpt = article.get("excerpt", "")
                    summary = article.get("summary", "")
                    keywords = article.get("keywords", [])
                    
                    news_str = f"  Title: {title}\n  Source: {source}"
                    if url:
                        news_str += f"\n  Link: {url}"
                    if summary:
                        news_str += f"\n  Summary: {summary}"
                    elif excerpt:
                        news_str += f"\n  Content: {excerpt[:500]}..." if len(excerpt) > 500 else f"\n  Content: {excerpt}"
                    if keywords:
                        news_str += f"\n  Keywords: {', '.join(keywords[:5])}"
                    news_items.append(news_str)
                
                if len(hits) > len(articles):
                    remaining_hits = hits[len(articles):]
                    for hit in remaining_hits[:5]:
                        title = hit.get("title", "No title")
                        source = hit.get("source", "Unknown")
                        link = hit.get("link", "")
                        news_str = f"  Title: {title}\n  Source: {source}"
                        if link:
                            news_str += f"\n  Link: {link}"
                        news_str += "\n  Content: [Title only - no content available]"
                        news_items.append(news_str)
                
                return f"News articles ({len(articles)} with content, {len(hits)} total):\n" + "\n".join(news_items)
            elif hits:
                news_items = []
                for hit in hits[:10]:
                    title = hit.get("title", "No title")
                    source = hit.get("source", "Unknown")
                    link = hit.get("link", "")
                    published = hit.get("published", hit.get("published_timestamp", ""))
                    news_str = f"  Title: {title}\n  Source: {source}"
                    if link:
                        news_str += f"\n  Link: {link}"
                    if published:
                        news_str += f"\n  Published: {published}"
                    news_str += "\n  Content: [Title only - no content available. Consider using plan_and_scan_news with fetch_body_top to get article content.]"
                    news_items.append(news_str)
                return f"News articles ({len(hits)} total, titles only - no content):\n" + "\n".join(news_items)
            else:
                queries = tool_result.get("queries", [])
                return f"No news found. Queries used: {', '.join(queries) if queries else 'N/A'}"
        else:
            items = list(tool_result.items())[:5]
            return ", ".join([f"{k}: {str(v)[:50]}" for k, v in items])
    
    return str(tool_result)[:200]


def generate_analysis_from_tools(
    analyst: BaseAgent,
    prompt_vars: Dict[str, Any],
    tool_results_summary: List[str],
    analyst_type: str,
    result_dict: Dict[str, Any],
    all_tool_calls: List[Dict[str, Any]],
    analyst_name: str
) -> None:
    """Generate analysis based on tool results"""
    current_analysis = result_dict.get("analysis", "").strip()
    if current_analysis and not current_analysis.startswith("Requested tool:") and len(current_analysis) >= 200:
        if not current_analysis.startswith("{") and not current_analysis.startswith("```"):
            if len(current_analysis) >= 600:
                return
    
    if not tool_results_summary:
        tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
        if tools_used:
            result_dict["analysis"] = f"Analyzed using tools: {', '.join(tools_used)}. Waiting for tool results to generate detailed analysis."
        return
    
    print(f"   🔄 Generating analysis based on tool results...")
    tool_results_text = "\n".join(tool_results_summary)
    
    if analyst_type == "market":
        task_desc = """Analyze the market data above and provide:
1. Market trend assessment (bullish/bearish/neutral)
2. Key insights from the data
3. Sector rotation observations
4. Market regime identification
5. Risk factors"""
    elif analyst_type == "technical":
        task_desc = """Analyze the technical indicators above and provide:
1. Technical trend assessment (bullish/bearish/neutral)
2. Key support/resistance levels
3. Momentum indicators interpretation
4. Volume analysis
5. Trading signals"""
    elif analyst_type == "fundamental":
        task_desc = """Analyze the fundamental data above and provide:
1. Valuation assessment (overvalued/undervalued/fair)
2. Earnings quality analysis
3. Financial health assessment
4. Growth prospects
5. Investment recommendation"""
    else:  # sentiment
        task_desc = """Analyze the sentiment data above and provide:
1. Market sentiment assessment (bullish/bearish/neutral)
2. Fear & Greed interpretation
3. VIX analysis
4. News sentiment trends
5. Contrarian signals"""
    
    has_news_data = any(keyword in tool_results_text.lower() for keyword in ["plan_and_scan_news", "news", "articles", "excerpt"])
    
    news_analysis_requirement = ""
    if has_news_data:
        news_analysis_requirement = f"""

**CRITICAL: News Analysis Requirement (if news data is present in tool results):**
- You MUST explicitly mention and analyze news content in your summary
- **IMPORTANT**: If article content (excerpt) is available in tool results, you MUST analyze the actual article content, not just the title
- For each relevant news article you select (choose the most important 2-3 articles, not random ones):
  1. **Title**: State the news article title
  2. **Content Analysis**: If article excerpt/content is available, analyze the actual content. If only title is available, infer key points from title
  3. **Summary**: Provide a 50-100 word summary based on article content (if available) or title analysis
  4. **Relevance**: Explain why this news is relevant to your {analyst_type} analysis
  5. **Impact**: Assess how this news might impact market sentiment or your analysis
- Format: "News Analysis: [Title] - [50-100 word summary based on article content explaining key points and relevance to {analyst_type} analysis]"
- You must SELECT the most relevant news articles yourself, not just mention any random article
- If multiple news articles are available, prioritize those most relevant to your {analyst_type} perspective
- **IMPORTANT**: When article content/excerpt is provided, use it for analysis. Do not rely solely on titles."""

    analysis_prompt = f"""Based on the tool results below, provide a comprehensive {analyst_type} analysis in natural language format (NOT JSON, just plain text).

**Tool Results:**
{tool_results_text}

**Your Task:**
{task_desc}
{news_analysis_requirement}

**Important Requirements:**
1. Write a comprehensive analysis in natural language, approximately 100-150 words in length (aim for 100-150 words)
2. Synthesize all tool results you've gathered (technical indicators, fundamental data, sentiment metrics, news content, etc.)
3. **MANDATORY**: If news data is present in tool results, you MUST explicitly mention and analyze news content. If article content/excerpt is available, analyze the actual content. If only titles are available, provide analysis based on titles.
4. Start directly with your analysis - do NOT include "Analysis:" prefix or JSON format
5. Provide specific insights based on the actual tool data
6. Include concrete numbers and observations from the tools
7. Provide a clear, coherent narrative that explains your {analyst_type} stance based on the data
8. End with a clear conclusion about the {analyst_type} outlook
9. Write in a clear, professional style suitable for financial analysis

Now provide your comprehensive 100-150 word analysis:"""
    
    try:
        analysis_response = analyst.run(
            {**prompt_vars, "extra_user_content": analysis_prompt},
            expect_json=False
        )
        if isinstance(analysis_response, str):
            cleaned_analysis = analysis_response.strip()
            if cleaned_analysis.startswith("Analysis:"):
                cleaned_analysis = cleaned_analysis[10:].strip()
            cleaned_analysis = cleaned_analysis.replace("```json", "").replace("```", "").strip()
            if cleaned_analysis.startswith("{") and cleaned_analysis.endswith("}"):
                try:
                    parsed = json.loads(cleaned_analysis)
                    if "analysis" in parsed:
                        cleaned_analysis = parsed["analysis"]
                    elif "content" in parsed:
                        cleaned_analysis = parsed["content"]
                except:
                    pass
            
            if len(cleaned_analysis) < 200:
                tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
                cleaned_analysis += f" Based on comprehensive analysis of {', '.join(tools_used)}, the {analyst_type} outlook is assessed with detailed insights from tool results."
            
            if len(cleaned_analysis) > 5000:
                cleaned_analysis = cleaned_analysis[:5000] + "... (truncated due to extreme length)"
            result_dict["analysis"] = cleaned_analysis
        else:
            analysis_str = str(analysis_response)
            if len(analysis_str) > 5000:
                analysis_str = analysis_str[:5000] + "... (truncated due to extreme length)"
            result_dict["analysis"] = analysis_str
        print(f"   [OK] Analysis generated from tool results ({len(result_dict['analysis'])} chars)")
    except Exception as e:
        print(f"   [WARN] Failed to generate analysis from tool results: {e}")
        tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst") == analyst_name]
        if tool_results_summary:
            result_dict["analysis"] = f"Based on analysis using {', '.join(tools_used)}, the {analyst_type} perspective indicates: {tool_results_text[:500]}. Further detailed analysis is being processed."
        else:
            result_dict["analysis"] = f"Analysis using tools: {', '.join(tools_used)}. Tool results are being processed to generate comprehensive {analyst_type} insights."

