"""
Signal engine — combines technical, macro, and news signals
into a unified opportunity score for each asset.
"""
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@dataclass
class Opportunity:
    symbol: str
    asset_type: str          # "stock" or "crypto"
    price: float
    bias: str                # STRONG BUY / BUY / NEUTRAL / SELL / STRONG SELL
    score: float             # combined score (-10 to +10)
    technical_score: float
    macro_score: float
    news_score: float
    signals: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    news_summary: str = ""
    macro_notes: list = field(default_factory=list)
    timeframe: str = "1d"
    rsi: Optional[float] = None
    atr: Optional[float] = None
    risk_reward: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    def to_dict(self):
        return asdict(self)


def analyze_asset(
    symbol: str,
    asset_type: str,
    df: pd.DataFrame,
    news_data: Optional[dict] = None,
    macro_data: Optional[dict] = None,
    timeframe: str = "1d",
) -> Opportunity:
    """
    Full analysis pipeline for one asset.
    Combines technical + news AI + macro into a single Opportunity object.
    """
    from analyzer.analysis.technical import get_current_signals, detect_chart_patterns, add_all_indicators

    # Add indicators if not already present
    if "rsi" not in df.columns:
        df = add_all_indicators(df)

    tech = get_current_signals(df)
    patterns = detect_chart_patterns(df)

    technical_score = tech.get("score", 0)

    # News score
    news_score = 0.0
    news_summary = ""
    if news_data and not news_data.get("error"):
        sentiment = news_data.get("overall_sentiment", "neutral")
        confidence = news_data.get("confidence", 50) / 100
        if sentiment == "bullish":
            news_score = confidence * 2
        elif sentiment == "bearish":
            news_score = -confidence * 2
        news_summary = news_data.get("summary", "")

    # Macro score
    macro_score = 0.0
    macro_notes = []
    if macro_data and not macro_data.get("error"):
        interpretation = macro_data.get("interpretation", {})
        macro_bias = interpretation.get("bias", "neutral")
        macro_notes = interpretation.get("signals", [])
        if macro_bias == "bullish":
            macro_score = 1.0
        elif macro_bias == "bearish":
            macro_score = -1.0

    # Weighted combined score
    # Technical: 60%, News: 30%, Macro: 10%
    combined_score = (technical_score * 0.6) + (news_score * 0.3) + (macro_score * 0.1)
    combined_score = round(combined_score, 2)

    # Bias from combined score
    if combined_score >= 2.5:
        bias = "STRONG BUY"
    elif combined_score >= 0.8:
        bias = "BUY"
    elif combined_score <= -2.5:
        bias = "STRONG SELL"
    elif combined_score <= -0.8:
        bias = "SELL"
    else:
        bias = "NEUTRAL"

    # Risk/reward via ATR
    price = tech.get("price", df["close"].iloc[-1])
    atr = tech.get("atr")
    stop_loss = None
    take_profit = None
    risk_reward = None

    if atr:
        stop_loss = round(price - 1.5 * atr, 4)
        take_profit = round(price + 3.0 * atr, 4)
        risk = price - stop_loss
        reward = take_profit - price
        risk_reward = round(reward / risk, 2) if risk > 0 else None

    return Opportunity(
        symbol=symbol,
        asset_type=asset_type,
        price=float(price),
        bias=bias,
        score=combined_score,
        technical_score=float(technical_score),
        macro_score=float(macro_score),
        news_score=float(news_score),
        signals=tech.get("signals", []),
        patterns=patterns,
        news_summary=news_summary,
        macro_notes=macro_notes,
        timeframe=timeframe,
        rsi=tech.get("rsi"),
        atr=float(atr) if atr else None,
        risk_reward=risk_reward,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )


def scan_watchlist(
    stocks: list[str] = None,
    crypto: list[str] = None,
    timeframe: str = "1d",
    with_news: bool = False,
    with_macro: bool = False,
) -> list[Opportunity]:
    """
    Scan a full watchlist and return ranked opportunities.
    Sorts by abs(score) descending — strongest signals first.
    """
    from analyzer.data.fetchers.stocks import get_ohlcv as get_stock_ohlcv
    from analyzer.data.fetchers.crypto import get_ohlcv as get_crypto_ohlcv
    from analyzer.config.settings import DEFAULT_STOCKS, DEFAULT_CRYPTO

    stocks = stocks or DEFAULT_STOCKS
    crypto = crypto or DEFAULT_CRYPTO
    opportunities = []

    # Fetch macro once for all assets
    macro_data = None
    if with_macro:
        try:
            from analyzer.data.fetchers.macro import get_macro_dashboard
            macro_data = get_macro_dashboard()
        except Exception as e:
            print(f"[signals] Macro fetch failed: {e}")

    for symbol in stocks:
        try:
            df = get_stock_ohlcv(symbol, period="6mo", interval=timeframe if timeframe in ["1d", "1wk"] else "1d")
            news = None
            if with_news:
                from analyzer.data.fetchers.news import get_news_for_symbol, analyze_news_with_ai
                articles = get_news_for_symbol(symbol)
                news = analyze_news_with_ai(symbol, articles) if articles else None
            opp = analyze_asset(symbol, "stock", df, news_data=news, macro_data=macro_data, timeframe=timeframe)
            opportunities.append(opp)
        except Exception as e:
            print(f"[signals] Error analyzing {symbol}: {e}")

    for symbol in crypto:
        try:
            tf_map = {"1d": "1d", "1h": "1h", "4h": "4h", "1wk": "1w"}
            tf = tf_map.get(timeframe, "1d")
            df = get_crypto_ohlcv(symbol, timeframe=tf, limit=300)
            news = None
            if with_news:
                from analyzer.data.fetchers.news import get_news_for_symbol, analyze_news_with_ai
                base = symbol.split("/")[0]
                articles = get_news_for_symbol(base)
                news = analyze_news_with_ai(base, articles) if articles else None
            opp = analyze_asset(symbol, "crypto", df, news_data=news, macro_data=macro_data, timeframe=timeframe)
            opportunities.append(opp)
        except Exception as e:
            print(f"[signals] Error analyzing {symbol}: {e}")

    opportunities.sort(key=lambda x: abs(x.score), reverse=True)
    return opportunities
