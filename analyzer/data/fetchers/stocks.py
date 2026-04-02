"""
Stock data fetcher — uses yfinance (free, no key) as primary,
Alpaca as secondary (needed for live/paper trading).
"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from analyzer.config.settings import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL


def get_ohlcv(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a stock symbol via yfinance.

    Args:
        symbol: e.g. "AAPL", "SPY"
        period: "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        interval: "1m","2m","5m","15m","30m","60m","90m","1h","1d","5d","1wk","1mo","3mo"
        start/end: override period with date range "YYYY-MM-DD"
    """
    ticker = yf.Ticker(symbol)
    if start and end:
        df = ticker.history(start=start, end=end, interval=interval)
    else:
        df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df.index = pd.to_datetime(df.index)
    df.index.name = "datetime"
    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close", "volume"]].dropna()
    return df


def get_multiple_ohlcv(
    symbols: list[str],
    period: str = "6mo",
    interval: str = "1d",
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV for multiple symbols. Returns dict symbol -> DataFrame."""
    result = {}
    for symbol in symbols:
        try:
            result[symbol] = get_ohlcv(symbol, period=period, interval=interval)
        except Exception as e:
            print(f"[stocks] Error fetching {symbol}: {e}")
    return result


def get_fundamentals(symbol: str) -> dict:
    """Fetch key fundamental data: P/E, EPS, market cap, earnings dates, etc."""
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    return {
        "symbol": symbol,
        "name": info.get("longName", ""),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "dividend_yield": info.get("dividendYield"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "beta": info.get("beta"),
        "short_ratio": info.get("shortRatio"),
        "next_earnings": info.get("earningsTimestamp"),
    }


def get_earnings_calendar(symbol: str) -> pd.DataFrame:
    """Fetch upcoming/recent earnings dates."""
    ticker = yf.Ticker(symbol)
    try:
        cal = ticker.calendar
        if cal is not None and not cal.empty:
            return cal
    except Exception:
        pass
    return pd.DataFrame()


def search_symbol(query: str) -> list[dict]:
    """Quick symbol search via yfinance."""
    try:
        results = yf.Search(query).quotes
        return [
            {"symbol": r.get("symbol"), "name": r.get("longname", r.get("shortname", ""))}
            for r in results[:10]
        ]
    except Exception:
        return []
