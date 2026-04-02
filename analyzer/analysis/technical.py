"""
Technical analysis engine.
Computes indicators and detects patterns using pandas-ta.
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from analyzer.config.settings import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, ATR_PERIOD, EMA_PERIODS,
    RSI_OVERSOLD, RSI_OVERBOUGHT
)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a comprehensive set of technical indicators to OHLCV DataFrame.
    Returns enriched DataFrame.
    """
    df = df.copy()

    # === TREND ===
    for period in EMA_PERIODS:
        df[f"ema_{period}"] = ta.ema(df["close"], length=period)
    df["sma_50"] = ta.sma(df["close"], length=50)
    df["sma_200"] = ta.sma(df["close"], length=200)

    # MACD
    macd = ta.macd(df["close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
    if macd is not None:
        df["macd"] = macd.iloc[:, 0]
        df["macd_signal"] = macd.iloc[:, 1]
        df["macd_hist"] = macd.iloc[:, 2]

    # Ichimoku
    ichimoku = ta.ichimoku(df["high"], df["low"], df["close"])
    if ichimoku is not None and len(ichimoku) > 0:
        ichi_df = ichimoku[0]
        for col in ichi_df.columns:
            df[col.lower().replace(" ", "_")] = ichi_df[col]

    # === MOMENTUM ===
    df["rsi"] = ta.rsi(df["close"], length=RSI_PERIOD)
    df["rsi_14"] = df["rsi"]

    stoch = ta.stoch(df["high"], df["low"], df["close"])
    if stoch is not None:
        df["stoch_k"] = stoch.iloc[:, 0]
        df["stoch_d"] = stoch.iloc[:, 1]

    df["cci"] = ta.cci(df["high"], df["low"], df["close"], length=20)
    df["williams_r"] = ta.willr(df["high"], df["low"], df["close"], length=14)
    df["mom"] = ta.mom(df["close"], length=10)
    df["roc"] = ta.roc(df["close"], length=10)

    # === VOLATILITY ===
    bb = ta.bbands(df["close"], length=BB_PERIOD, std=BB_STD)
    if bb is not None:
        df["bb_upper"] = bb.iloc[:, 0]
        df["bb_mid"] = bb.iloc[:, 1]
        df["bb_lower"] = bb.iloc[:, 2]
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
        df["bb_pct"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=ATR_PERIOD)
    df["natr"] = ta.natr(df["high"], df["low"], df["close"], length=ATR_PERIOD)

    # === VOLUME ===
    df["obv"] = ta.obv(df["close"], df["volume"])
    df["vwap"] = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
    df["mfi"] = ta.mfi(df["high"], df["low"], df["close"], df["close"], length=14)
    df["ad"] = ta.ad(df["high"], df["low"], df["close"], df["volume"])
    df["cmf"] = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=20)

    # Volume SMA for context
    df["vol_sma_20"] = ta.sma(df["volume"], length=20)
    df["vol_ratio"] = df["volume"] / df["vol_sma_20"]

    # === SUPPORT/RESISTANCE via pivot points ===
    df = _add_pivot_points(df)

    return df


def _add_pivot_points(df: pd.DataFrame) -> pd.DataFrame:
    """Classic pivot points (daily)."""
    df["pivot"] = (df["high"].shift(1) + df["low"].shift(1) + df["close"].shift(1)) / 3
    df["r1"] = 2 * df["pivot"] - df["low"].shift(1)
    df["s1"] = 2 * df["pivot"] - df["high"].shift(1)
    df["r2"] = df["pivot"] + (df["high"].shift(1) - df["low"].shift(1))
    df["s2"] = df["pivot"] - (df["high"].shift(1) - df["low"].shift(1))
    return df


def get_current_signals(df: pd.DataFrame) -> dict:
    """
    Generate trading signals from the latest candle.
    Returns a scored signal dict: score > 0 = bullish, < 0 = bearish.
    """
    if len(df) < 50:
        return {"error": "Not enough data (need 50+ candles)"}

    row = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []
    score = 0

    # --- RSI ---
    rsi = row.get("rsi")
    if rsi is not None:
        if rsi < RSI_OVERSOLD:
            signals.append({"indicator": "RSI", "signal": "BUY", "reason": f"RSI oversold ({rsi:.1f} < {RSI_OVERSOLD})"})
            score += 1
        elif rsi > RSI_OVERBOUGHT:
            signals.append({"indicator": "RSI", "signal": "SELL", "reason": f"RSI overbought ({rsi:.1f} > {RSI_OVERBOUGHT})"})
            score -= 1
        else:
            signals.append({"indicator": "RSI", "signal": "NEUTRAL", "reason": f"RSI neutral ({rsi:.1f})"})

    # --- MACD ---
    macd = row.get("macd")
    macd_sig = row.get("macd_signal")
    macd_hist = row.get("macd_hist")
    prev_hist = prev.get("macd_hist")
    if all(v is not None for v in [macd, macd_sig, macd_hist, prev_hist]):
        if macd_hist > 0 and prev_hist <= 0:
            signals.append({"indicator": "MACD", "signal": "BUY", "reason": "MACD histogram crossed above 0 (bullish)"})
            score += 2
        elif macd_hist < 0 and prev_hist >= 0:
            signals.append({"indicator": "MACD", "signal": "SELL", "reason": "MACD histogram crossed below 0 (bearish)"})
            score -= 2
        elif macd > macd_sig:
            signals.append({"indicator": "MACD", "signal": "BUY", "reason": "MACD above signal line"})
            score += 1
        else:
            signals.append({"indicator": "MACD", "signal": "SELL", "reason": "MACD below signal line"})
            score -= 1

    # --- Bollinger Bands ---
    bb_pct = row.get("bb_pct")
    if bb_pct is not None:
        if bb_pct < 0.05:
            signals.append({"indicator": "BB", "signal": "BUY", "reason": f"Price near lower BB (BB%={bb_pct:.2f})"})
            score += 1
        elif bb_pct > 0.95:
            signals.append({"indicator": "BB", "signal": "SELL", "reason": f"Price near upper BB (BB%={bb_pct:.2f})"})
            score -= 1

    # --- EMA trend (golden/death cross style) ---
    ema_9 = row.get("ema_9")
    ema_21 = row.get("ema_21")
    ema_50 = row.get("ema_50")
    ema_200 = row.get("ema_200")
    close = row["close"]
    if ema_50 and ema_200:
        if ema_50 > ema_200:
            signals.append({"indicator": "EMA", "signal": "BUY", "reason": "EMA50 > EMA200 (golden cross zone)"})
            score += 1
        else:
            signals.append({"indicator": "EMA", "signal": "SELL", "reason": "EMA50 < EMA200 (death cross zone)"})
            score -= 1
    if ema_9 and ema_21:
        if ema_9 > ema_21 and close > ema_9:
            signals.append({"indicator": "EMA_short", "signal": "BUY", "reason": "Price > EMA9 > EMA21 (short-term bullish)"})
            score += 1
        elif ema_9 < ema_21 and close < ema_9:
            signals.append({"indicator": "EMA_short", "signal": "SELL", "reason": "Price < EMA9 < EMA21 (short-term bearish)"})
            score -= 1

    # --- Volume confirmation ---
    vol_ratio = row.get("vol_ratio")
    if vol_ratio and vol_ratio > 1.5:
        signals.append({"indicator": "Volume", "signal": "CONFIRM", "reason": f"High volume ({vol_ratio:.1f}x average) — move confirmed"})
        score = int(score * 1.2)  # boost confidence

    # --- Stochastic ---
    stoch_k = row.get("stoch_k")
    stoch_d = row.get("stoch_d")
    if stoch_k and stoch_d:
        if stoch_k < 20 and stoch_d < 20:
            signals.append({"indicator": "Stoch", "signal": "BUY", "reason": f"Stochastic oversold ({stoch_k:.1f})"})
            score += 1
        elif stoch_k > 80 and stoch_d > 80:
            signals.append({"indicator": "Stoch", "signal": "SELL", "reason": f"Stochastic overbought ({stoch_k:.1f})"})
            score -= 1

    # Overall bias
    if score >= 3:
        bias = "STRONG BUY"
    elif score >= 1:
        bias = "BUY"
    elif score <= -3:
        bias = "STRONG SELL"
    elif score <= -1:
        bias = "SELL"
    else:
        bias = "NEUTRAL"

    return {
        "bias": bias,
        "score": score,
        "signals": signals,
        "price": float(close),
        "rsi": float(rsi) if rsi else None,
        "atr": float(row["atr"]) if row.get("atr") is not None else None,
        "vol_ratio": float(vol_ratio) if vol_ratio else None,
    }


def detect_chart_patterns(df: pd.DataFrame) -> list[dict]:
    """
    Detect common chart patterns in recent price action.
    Uses candlestick patterns via pandas-ta + custom logic.
    """
    patterns_found = []
    if len(df) < 20:
        return patterns_found

    # Pandas-ta candlestick patterns
    candle_patterns = {
        "doji": ta.cdl_doji,
        "hammer": ta.cdl_hammer,
        "shooting_star": ta.cdl_shooting_star,
        "engulfing": ta.cdl_pattern,
        "morning_star": ta.cdl_pattern,
    }

    # Simpler direct pandas-ta approach
    try:
        cdl = ta.cdl_pattern(df["open"], df["high"], df["low"], df["close"], name="all")
        if cdl is not None:
            for col in cdl.columns:
                last_val = cdl[col].iloc[-1]
                if last_val != 0:
                    patterns_found.append({
                        "pattern": col.replace("CDL_", ""),
                        "signal": "BUY" if last_val > 0 else "SELL",
                        "strength": abs(last_val),
                    })
    except Exception:
        pass

    # Custom: Higher Highs / Lower Lows (trend detection)
    recent = df["close"].iloc[-10:]
    highs = df["high"].iloc[-10:]
    lows = df["low"].iloc[-10:]

    if highs.iloc[-1] > highs.iloc[-5] > highs.iloc[0] and lows.iloc[-1] > lows.iloc[-5]:
        patterns_found.append({"pattern": "HIGHER_HIGHS", "signal": "BUY", "strength": 1})

    if lows.iloc[-1] < lows.iloc[-5] < lows.iloc[0] and highs.iloc[-1] < highs.iloc[-5]:
        patterns_found.append({"pattern": "LOWER_LOWS", "signal": "SELL", "strength": 1})

    # Custom: Consolidation (BB squeeze)
    bb_width = df["bb_width"].iloc[-10:] if "bb_width" in df.columns else None
    if bb_width is not None and not bb_width.isna().all():
        if bb_width.iloc[-1] < bb_width.quantile(0.2):
            patterns_found.append({"pattern": "BB_SQUEEZE", "signal": "BREAKOUT_WATCH", "strength": 1})

    return patterns_found
