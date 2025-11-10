"""
基本面分析工具：业绩、财报、估值指标
"""
from typing import Dict, Any, Optional
import yfinance as yf
import pandas as pd
from datetime import datetime


def get_company_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    获取公司基本面数据
    
    Args:
        symbol: 股票代码
    
    Returns:
        Dict包含业绩、估值、财务指标
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        result = {
            "symbol": symbol,
            "company_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "fundamentals": {}
        }
        
        # 估值指标
        result["fundamentals"]["valuation"] = {
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_revenue": info.get("enterpriseToRevenue"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
        }
        
        # 盈利能力
        result["fundamentals"]["profitability"] = {
            "profit_margins": info.get("profitMargins"),
            "operating_margins": info.get("operatingMargins"),
            "return_on_assets": info.get("returnOnAssets"),
            "return_on_equity": info.get("returnOnEquity"),
            "revenue": info.get("totalRevenue"),
            "revenue_per_share": info.get("revenuePerShare"),
            "gross_profits": info.get("grossProfits"),
            "ebitda": info.get("ebitda"),
            "net_income": info.get("netIncomeToCommon"),
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
        }
        
        # 增长指标
        result["fundamentals"]["growth"] = {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
        }
        
        # 财务健康
        result["fundamentals"]["financial_health"] = {
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "free_cashflow": info.get("freeCashflow"),
            "operating_cashflow": info.get("operatingCashflow"),
        }
        
        # 股息信息
        result["fundamentals"]["dividend"] = {
            "dividend_rate": info.get("dividendRate"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield"),
        }
        
        # 分析师评级
        result["fundamentals"]["analyst_ratings"] = {
            "target_price": info.get("targetMeanPrice"),
            "target_high": info.get("targetHighPrice"),
            "target_low": info.get("targetLowPrice"),
            "recommendation": info.get("recommendationKey"),
            "number_of_analysts": info.get("numberOfAnalystOpinions"),
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_earnings_history(symbol: str) -> Dict[str, Any]:
    """
    获取业绩历史
    
    Args:
        symbol: 股票代码
    
    Returns:
        最近的业绩数据
    """
    try:
        ticker = yf.Ticker(symbol)
        
        result = {
            "symbol": symbol,
            "earnings_dates": [],
            "quarterly_earnings": [],
            "annual_earnings": []
        }
        
        # 获取业绩日历
        try:
            earnings_dates = ticker.earnings_dates
            if earnings_dates is not None and not earnings_dates.empty:
                result["earnings_dates"] = [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "eps_estimate": float(row.get("EPS Estimate", 0)) if pd.notna(row.get("EPS Estimate")) else None,
                        "reported_eps": float(row.get("Reported EPS", 0)) if pd.notna(row.get("Reported EPS")) else None,
                        "surprise": float(row.get("Surprise(%)", 0)) if pd.notna(row.get("Surprise(%)")) else None,
                    }
                    for date, row in earnings_dates.head(4).iterrows()
                ]
        except:
            pass
        
        # 获取季度业绩（使用 income_stmt 替代已弃用的 quarterly_earnings）
        try:
            # 尝试使用 income_stmt 获取季度数据
            income_stmt = ticker.quarterly_income_stmt
            if income_stmt is not None and not income_stmt.empty:
                # income_stmt 的列是日期，行是指标名称
                # 获取最近4个季度的数据（列）
                for i, date_col in enumerate(income_stmt.columns[:4]):
                    # 格式化季度：计算季度数
                    if hasattr(date_col, 'quarter'):
                        quarter_str = f"{date_col.year}-Q{date_col.quarter}"
                    elif hasattr(date_col, 'year') and hasattr(date_col, 'month'):
                        quarter_num = (date_col.month - 1) // 3 + 1
                        quarter_str = f"{date_col.year}-Q{quarter_num}"
                    else:
                        quarter_str = str(date_col)
                    quarter_data = {
                        "quarter": quarter_str,
                        "revenue": None,
                        "earnings": None,
                    }
                    # 从行索引中查找 Revenue 和 Net Income
                    if "Total Revenue" in income_stmt.index:
                        val = income_stmt.loc["Total Revenue", date_col]
                        quarter_data["revenue"] = float(val) if pd.notna(val) else None
                    elif "Revenue" in income_stmt.index:
                        val = income_stmt.loc["Revenue", date_col]
                        quarter_data["revenue"] = float(val) if pd.notna(val) else None
                    if "Net Income" in income_stmt.index:
                        val = income_stmt.loc["Net Income", date_col]
                        quarter_data["earnings"] = float(val) if pd.notna(val) else None
                    elif "Net Income Common Stockholders" in income_stmt.index:
                        val = income_stmt.loc["Net Income Common Stockholders", date_col]
                        quarter_data["earnings"] = float(val) if pd.notna(val) else None
                    elif "Net Income From Continuing Operation Net Minority Interest" in income_stmt.index:
                        val = income_stmt.loc["Net Income From Continuing Operation Net Minority Interest", date_col]
                        quarter_data["earnings"] = float(val) if pd.notna(val) else None
                    if quarter_data["revenue"] is not None or quarter_data["earnings"] is not None:
                        result["quarterly_earnings"].append(quarter_data)
        except Exception as e:
            # 如果新方法失败，尝试旧方法（已弃用但可能仍可用）
            try:
                quarterly_earnings = ticker.quarterly_earnings
                if quarterly_earnings is not None and not quarterly_earnings.empty:
                    result["quarterly_earnings"] = [
                        {
                            "quarter": date.strftime("%Y-Q%q") if hasattr(date, 'quarter') else str(date),
                            "revenue": float(row.get("Revenue", 0)) if pd.notna(row.get("Revenue")) else None,
                            "earnings": float(row.get("Earnings", 0)) if pd.notna(row.get("Earnings")) else None,
                        }
                        for date, row in quarterly_earnings.head(4).iterrows()
                    ]
            except:
                pass
        
        # 获取年度业绩（使用 income_stmt 替代已弃用的 earnings）
        try:
            # 尝试使用 income_stmt 获取年度数据
            income_stmt = ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                # income_stmt 的列是日期，行是指标名称
                # 获取最近3年的数据（列）
                for i, date_col in enumerate(income_stmt.columns[:3]):
                    year_data = {
                        "year": int(date_col.year) if hasattr(date_col, 'year') else None,
                        "revenue": None,
                        "earnings": None,
                    }
                    # 从行索引中查找 Revenue 和 Net Income
                    if "Total Revenue" in income_stmt.index:
                        val = income_stmt.loc["Total Revenue", date_col]
                        year_data["revenue"] = float(val) if pd.notna(val) else None
                    elif "Revenue" in income_stmt.index:
                        val = income_stmt.loc["Revenue", date_col]
                        year_data["revenue"] = float(val) if pd.notna(val) else None
                    if "Net Income" in income_stmt.index:
                        val = income_stmt.loc["Net Income", date_col]
                        year_data["earnings"] = float(val) if pd.notna(val) else None
                    elif "Net Income Common Stockholders" in income_stmt.index:
                        val = income_stmt.loc["Net Income Common Stockholders", date_col]
                        year_data["earnings"] = float(val) if pd.notna(val) else None
                    elif "Net Income From Continuing Operation Net Minority Interest" in income_stmt.index:
                        val = income_stmt.loc["Net Income From Continuing Operation Net Minority Interest", date_col]
                        year_data["earnings"] = float(val) if pd.notna(val) else None
                    if year_data["revenue"] is not None or year_data["earnings"] is not None:
                        result["annual_earnings"].append(year_data)
        except Exception as e:
            # 如果新方法失败，尝试旧方法（已弃用但可能仍可用）
            try:
                annual_earnings = ticker.earnings
                if annual_earnings is not None and not annual_earnings.empty:
                    result["annual_earnings"] = [
                        {
                            "year": int(row.get("Year", 0)) if pd.notna(row.get("Year")) else None,
                            "revenue": float(row.get("Revenue", 0)) if pd.notna(row.get("Revenue")) else None,
                            "earnings": float(row.get("Earnings", 0)) if pd.notna(row.get("Earnings")) else None,
                        }
                        for idx, row in annual_earnings.tail(3).iterrows()
                    ]
            except:
                pass
        
        return result
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_financial_statements(symbol: str) -> Dict[str, Any]:
    """
    获取财务报表摘要
    
    Args:
        symbol: 股票代码
    
    Returns:
        资产负债表、现金流量表摘要
    """
    try:
        ticker = yf.Ticker(symbol)
        
        result = {
            "symbol": symbol,
            "balance_sheet": {},
            "cashflow": {},
        }
        
        # 资产负债表
        try:
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                latest = bs.iloc[:, 0]  # 最新一期
                result["balance_sheet"] = {
                    "total_assets": float(latest.get("Total Assets", 0)) if "Total Assets" in latest.index else None,
                    "total_liabilities": float(latest.get("Total Liabilities Net Minority Interest", 0)) if "Total Liabilities Net Minority Interest" in latest.index else None,
                    "stockholders_equity": float(latest.get("Stockholders Equity", 0)) if "Stockholders Equity" in latest.index else None,
                    "cash_and_equivalents": float(latest.get("Cash And Cash Equivalents", 0)) if "Cash And Cash Equivalents" in latest.index else None,
                }
        except:
            pass
        
        # 现金流量表
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                latest = cf.iloc[:, 0]  # 最新一期
                result["cashflow"] = {
                    "operating_cashflow": float(latest.get("Operating Cash Flow", 0)) if "Operating Cash Flow" in latest.index else None,
                    "investing_cashflow": float(latest.get("Investing Cash Flow", 0)) if "Investing Cash Flow" in latest.index else None,
                    "financing_cashflow": float(latest.get("Financing Cash Flow", 0)) if "Financing Cash Flow" in latest.index else None,
                    "free_cashflow": float(latest.get("Free Cash Flow", 0)) if "Free Cash Flow" in latest.index else None,
                }
        except:
            pass
        
        return result
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

