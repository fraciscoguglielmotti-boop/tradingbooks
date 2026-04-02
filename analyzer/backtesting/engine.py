"""
Backtesting engine powered by vectorbt.
Simulates trades as if live — no lookahead bias (signals shift(1) in strategies).
Supports: single strategy, multi-strategy comparison, parameter optimization.
"""
import pandas as pd
import numpy as np
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from analyzer.backtesting.strategies.base import BaseStrategy, BacktestResult, STRATEGIES
from analyzer.config.settings import BACKTEST_INITIAL_CASH, BACKTEST_FEES


def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    symbol: str = "ASSET",
    timeframe: str = "1d",
    initial_cash: float = BACKTEST_INITIAL_CASH,
    fees: float = BACKTEST_FEES,
) -> BacktestResult:
    """
    Run a single strategy backtest on OHLCV data.

    Args:
        df: OHLCV DataFrame (must have close, high, low, volume columns)
        strategy: BaseStrategy instance
        symbol: asset name
        timeframe: for display purposes
        initial_cash: starting capital
        fees: fee per trade (0.001 = 0.1%)
    """
    try:
        import vectorbt as vbt
    except ImportError:
        raise ImportError("Install vectorbt: pip install vectorbt")

    df = df.copy().dropna(subset=["close"])
    entries, exits = strategy.generate_signals(df)

    # Align index
    entries = entries.reindex(df.index).fillna(False)
    exits = exits.reindex(df.index).fillna(False)

    # Run portfolio simulation
    portfolio = vbt.Portfolio.from_signals(
        df["close"],
        entries=entries,
        exits=exits,
        init_cash=initial_cash,
        fees=fees,
        freq="D",
    )

    stats = portfolio.stats()
    trades = portfolio.trades.records_readable if hasattr(portfolio.trades, "records_readable") else pd.DataFrame()

    # Extract metrics
    total_return = float(stats.get("Total Return [%]", 0))
    sharpe = float(stats.get("Sharpe Ratio", 0)) if "Sharpe Ratio" in stats else None
    max_dd = float(stats.get("Max Drawdown [%]", 0))
    win_rate = float(stats.get("Win Rate [%]", 0))
    total_trades = int(stats.get("Total Trades", 0))
    profit_factor = float(stats.get("Profit Factor", 0)) if "Profit Factor" in stats else None
    avg_trade = float(stats.get("Avg Winning Trade [%]", 0))

    # Best/worst trade
    best_trade = 0.0
    worst_trade = 0.0
    if not trades.empty and "Return [%]" in trades.columns:
        best_trade = float(trades["Return [%]"].max())
        worst_trade = float(trades["Return [%]"].min())

    period_str = f"{df.index[0].date()} → {df.index[-1].date()}"
    equity_curve = portfolio.value()

    return BacktestResult(
        strategy_name=strategy.name,
        symbol=symbol,
        timeframe=timeframe,
        period=period_str,
        initial_cash=initial_cash,
        final_value=float(portfolio.final_value()),
        total_return_pct=total_return,
        sharpe_ratio=sharpe,
        max_drawdown_pct=max_dd,
        win_rate_pct=win_rate,
        total_trades=total_trades,
        profit_factor=profit_factor,
        avg_trade_return_pct=avg_trade,
        best_trade_pct=best_trade,
        worst_trade_pct=worst_trade,
        equity_curve=equity_curve,
        trades=trades,
    )


def compare_strategies(
    df: pd.DataFrame,
    symbol: str = "ASSET",
    timeframe: str = "1d",
    strategy_names: Optional[list[str]] = None,
    initial_cash: float = BACKTEST_INITIAL_CASH,
    fees: float = BACKTEST_FEES,
) -> list[BacktestResult]:
    """
    Run multiple strategies on the same data and return sorted results.
    Sorted by Sharpe ratio descending.
    """
    names = strategy_names or list(STRATEGIES.keys())
    results = []

    for name in names:
        if name not in STRATEGIES:
            print(f"[backtest] Unknown strategy: {name}")
            continue
        try:
            strategy = STRATEGIES[name]()
            result = run_backtest(df, strategy, symbol=symbol, timeframe=timeframe,
                                  initial_cash=initial_cash, fees=fees)
            results.append(result)
            print(f"[backtest] {name}: {result.total_return_pct:+.2f}% | Sharpe={result.sharpe_ratio:.2f if result.sharpe_ratio else 'N/A'} | DD={result.max_drawdown_pct:.1f}%")
        except Exception as e:
            print(f"[backtest] Error running {name}: {e}")

    results.sort(key=lambda r: r.sharpe_ratio or -99, reverse=True)
    return results


def optimize_ema_cross(
    df: pd.DataFrame,
    symbol: str = "ASSET",
    fast_range: range = range(5, 30, 5),
    slow_range: range = range(20, 100, 10),
) -> pd.DataFrame:
    """
    Grid search for optimal EMA cross parameters.
    Returns DataFrame with all combinations ranked by Sharpe.
    """
    from analyzer.backtesting.strategies.base import EMACrossStrategy
    results = []

    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue
            try:
                strat = EMACrossStrategy(fast=fast, slow=slow)
                result = run_backtest(df, strat, symbol=symbol)
                results.append({
                    "fast": fast,
                    "slow": slow,
                    "return_pct": result.total_return_pct,
                    "sharpe": result.sharpe_ratio,
                    "max_dd": result.max_drawdown_pct,
                    "win_rate": result.win_rate_pct,
                    "trades": result.total_trades,
                })
            except Exception:
                pass

    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values("sharpe", ascending=False)
    return df_results
