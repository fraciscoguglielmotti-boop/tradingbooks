"""
Base strategy interface + built-in strategies for backtesting.
Uses vectorbt for simulation — NO lookahead bias (uses .shift(1) on all signals).
"""
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    timeframe: str
    period: str
    initial_cash: float
    final_value: float
    total_return_pct: float
    sharpe_ratio: Optional[float]
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    profit_factor: Optional[float]
    avg_trade_return_pct: float
    best_trade_pct: float
    worst_trade_pct: float
    equity_curve: pd.Series = None
    trades: pd.DataFrame = None

    def summary(self) -> str:
        return (
            f"=== {self.strategy_name} | {self.symbol} ({self.timeframe}) ===\n"
            f"Period: {self.period}\n"
            f"Return: {self.total_return_pct:+.2f}%\n"
            f"Sharpe: {self.sharpe_ratio:.2f if self.sharpe_ratio else 'N/A'}\n"
            f"Max DD: {self.max_drawdown_pct:.2f}%\n"
            f"Win Rate: {self.win_rate_pct:.1f}%\n"
            f"Trades: {self.total_trades}\n"
            f"Profit Factor: {self.profit_factor:.2f if self.profit_factor else 'N/A'}"
        )


class BaseStrategy(ABC):
    name: str = "BaseStrategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """
        Return (entries, exits) as boolean Series.
        IMPORTANT: Always shift signals by 1 to avoid lookahead bias.
        Entry on next candle's open after signal fires.
        """
        pass


class RSIMACDStrategy(BaseStrategy):
    """
    Classic momentum strategy:
    BUY when RSI < 40 AND MACD bullish crossover
    SELL when RSI > 60 OR MACD bearish crossover
    """
    name = "RSI + MACD"

    def __init__(self, rsi_buy=40, rsi_sell=60):
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell

    def generate_signals(self, df: pd.DataFrame):
        import pandas_ta as ta
        df = df.copy()
        df["rsi"] = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df["macd_hist"] = macd.iloc[:, 2] if macd is not None else 0

        entries = (df["rsi"] < self.rsi_buy) & (df["macd_hist"] > 0) & (df["macd_hist"].shift(1) <= 0)
        exits = (df["rsi"] > self.rsi_sell) | ((df["macd_hist"] < 0) & (df["macd_hist"].shift(1) >= 0))

        # Shift to avoid lookahead: execute on next candle
        return entries.shift(1).fillna(False), exits.shift(1).fillna(False)


class EMACrossStrategy(BaseStrategy):
    """
    EMA crossover: fast EMA crosses above slow EMA = BUY, below = SELL.
    Classic trend-following.
    """
    name = "EMA Cross"

    def __init__(self, fast=9, slow=21):
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame):
        import pandas_ta as ta
        df = df.copy()
        df["ema_fast"] = ta.ema(df["close"], length=self.fast)
        df["ema_slow"] = ta.ema(df["close"], length=self.slow)

        cross_up = (df["ema_fast"] > df["ema_slow"]) & (df["ema_fast"].shift(1) <= df["ema_slow"].shift(1))
        cross_down = (df["ema_fast"] < df["ema_slow"]) & (df["ema_fast"].shift(1) >= df["ema_slow"].shift(1))

        return cross_up.shift(1).fillna(False), cross_down.shift(1).fillna(False)


class BollingerMeanReversionStrategy(BaseStrategy):
    """
    Mean reversion: buy when price touches lower BB, sell at middle BB.
    Best in ranging/sideways markets.
    """
    name = "BB Mean Reversion"

    def __init__(self, bb_period=20, bb_std=2.0):
        self.bb_period = bb_period
        self.bb_std = bb_std

    def generate_signals(self, df: pd.DataFrame):
        import pandas_ta as ta
        df = df.copy()
        bb = ta.bbands(df["close"], length=self.bb_period, std=self.bb_std)
        if bb is None:
            return pd.Series(False, index=df.index), pd.Series(False, index=df.index)

        df["bb_lower"] = bb.iloc[:, 2]
        df["bb_mid"] = bb.iloc[:, 1]
        df["bb_upper"] = bb.iloc[:, 0]

        entries = df["close"] <= df["bb_lower"]
        exits = df["close"] >= df["bb_mid"]

        return entries.shift(1).fillna(False), exits.shift(1).fillna(False)


class DualMomentumStrategy(BaseStrategy):
    """
    Inspired by Gary Antonacci's Dual Momentum:
    Absolute momentum (asset > risk-free) + relative momentum (best performer).
    Simplified for single-asset: buy when 12-month return > 0 and recent trend up.
    """
    name = "Dual Momentum"

    def generate_signals(self, df: pd.DataFrame):
        import pandas_ta as ta
        df = df.copy()
        # 12-month momentum
        df["mom_12m"] = df["close"].pct_change(periods=252)
        df["mom_1m"] = df["close"].pct_change(periods=21)
        df["ema_50"] = ta.ema(df["close"], length=50)
        df["ema_200"] = ta.ema(df["close"], length=200)

        entries = (df["mom_12m"] > 0) & (df["mom_1m"] > 0) & (df["ema_50"] > df["ema_200"])
        exits = (df["mom_12m"] < 0) | (df["ema_50"] < df["ema_200"])

        return entries.shift(1).fillna(False), exits.shift(1).fillna(False)


class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku cloud breakout:
    BUY when price breaks above the cloud (kumo)
    SELL when price breaks below the cloud
    """
    name = "Ichimoku Cloud"

    def generate_signals(self, df: pd.DataFrame):
        import pandas_ta as ta
        df = df.copy()
        ichimoku = ta.ichimoku(df["high"], df["low"], df["close"])
        if ichimoku is None or len(ichimoku) == 0:
            return pd.Series(False, index=df.index), pd.Series(False, index=df.index)

        ichi_df = ichimoku[0]
        cols = ichi_df.columns.tolist()

        # Span A and B form the cloud
        span_a_col = [c for c in cols if "ISA" in c]
        span_b_col = [c for c in cols if "ISB" in c]

        if not span_a_col or not span_b_col:
            return pd.Series(False, index=df.index), pd.Series(False, index=df.index)

        df["span_a"] = ichi_df[span_a_col[0]]
        df["span_b"] = ichi_df[span_b_col[0]]
        df["cloud_top"] = df[["span_a", "span_b"]].max(axis=1)
        df["cloud_bot"] = df[["span_a", "span_b"]].min(axis=1)

        entries = (df["close"] > df["cloud_top"]) & (df["close"].shift(1) <= df["cloud_top"].shift(1))
        exits = (df["close"] < df["cloud_bot"]) & (df["close"].shift(1) >= df["cloud_bot"].shift(1))

        return entries.shift(1).fillna(False), exits.shift(1).fillna(False)


# Registry of all available strategies
STRATEGIES = {
    "RSI + MACD": RSIMACDStrategy,
    "EMA Cross": EMACrossStrategy,
    "BB Mean Reversion": BollingerMeanReversionStrategy,
    "Dual Momentum": DualMomentumStrategy,
    "Ichimoku Cloud": IchimokuStrategy,
}
