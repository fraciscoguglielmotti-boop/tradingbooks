"""
Macro data fetcher — FRED (Federal Reserve Economic Data).
Free API. Key at: https://fred.stlouisfed.org/docs/api/api_key.html

Key series tracked:
- DFF: Fed Funds Rate
- CPIAUCSL: CPI (inflation)
- UNRATE: Unemployment rate
- GDP: GDP growth
- T10Y2Y: Yield curve (10Y-2Y spread, recession indicator)
- VIXCLS: VIX fear index
- DGS10: 10-year Treasury yield
- DTWEXBGS: USD Index
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from analyzer.config.settings import FRED_API_KEY

MACRO_SERIES = {
    "fed_funds_rate": "DFF",
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "yield_curve_10y2y": "T10Y2Y",
    "vix": "VIXCLS",
    "treasury_10y": "DGS10",
    "usd_index": "DTWEXBGS",
    "pce_inflation": "PCE",
    "retail_sales": "RSXFS",
}


def get_fred_series(series_id: str, start: Optional[str] = None) -> pd.Series:
    """Fetch a single FRED series."""
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set in .env")
    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_API_KEY)
        start = start or (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        data = fred.get_series(series_id, observation_start=start)
        return data.dropna()
    except ImportError:
        raise ImportError("Install fredapi: pip install fredapi")


def get_macro_dashboard() -> dict:
    """
    Fetch all key macro indicators. Returns dict with latest values + trends.
    Falls back gracefully if FRED key not available.
    """
    if not FRED_API_KEY:
        return {"error": "FRED_API_KEY not configured"}

    result = {}
    for name, series_id in MACRO_SERIES.items():
        try:
            data = get_fred_series(series_id)
            latest = float(data.iloc[-1])
            prev = float(data.iloc[-2]) if len(data) > 1 else latest
            result[name] = {
                "value": round(latest, 4),
                "prev": round(prev, 4),
                "change": round(latest - prev, 4),
                "trend": "up" if latest > prev else "down" if latest < prev else "flat",
                "series_id": series_id,
            }
        except Exception as e:
            result[name] = {"error": str(e)}

    # Interpret key signals
    result["interpretation"] = _interpret_macro(result)
    return result


def _interpret_macro(data: dict) -> dict:
    """Rule-based macro interpretation for market bias."""
    signals = []
    bias = "neutral"

    fed = data.get("fed_funds_rate", {})
    vix = data.get("vix", {})
    yc = data.get("yield_curve_10y2y", {})
    cpi = data.get("cpi", {})

    if fed and not fed.get("error"):
        if fed["trend"] == "up":
            signals.append("Fed hiking rates — bearish for growth stocks")
        elif fed["trend"] == "down":
            signals.append("Fed cutting rates — bullish signal")

    if vix and not vix.get("error"):
        v = vix["value"]
        if v > 30:
            signals.append(f"VIX={v:.1f} — extreme fear, potential reversal zone")
        elif v < 15:
            signals.append(f"VIX={v:.1f} — complacency, watch for spikes")

    if yc and not yc.get("error"):
        y = yc["value"]
        if y < 0:
            signals.append(f"Yield curve inverted ({y:.2f}%) — recession risk elevated")
        else:
            signals.append(f"Yield curve positive ({y:.2f}%) — expansion signal")

    bearish_count = sum(1 for s in signals if "bearish" in s.lower() or "risk" in s.lower() or "fear" in s.lower())
    bullish_count = sum(1 for s in signals if "bullish" in s.lower() or "cutting" in s.lower())

    if bullish_count > bearish_count:
        bias = "bullish"
    elif bearish_count > bullish_count:
        bias = "bearish"

    return {"bias": bias, "signals": signals}
